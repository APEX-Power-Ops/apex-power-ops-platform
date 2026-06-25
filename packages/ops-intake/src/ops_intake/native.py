from __future__ import annotations

import dataclasses
import hashlib
import json
from decimal import Decimal, InvalidOperation

from .model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn
from .validate import Finding

NATIVE_SCHEMA_VERSION = "estimate_envelope_v1"
NATIVE_PARSER_VERSION = "estimator-core/c051c02"
_LINE_KINDS = {"catalog", "custom_equipment", "service", "cost"}
_REQUIRED_CATALOG_FIELDS = ("equipment_model_ref", "base_qty", "project_intake_qty", "resolved_ref_hours")


def _pm(msg: str) -> str:
    return msg.replace("$", "")


def _f(code, message, *, ok=False, severity="blocking", detail=None) -> Finding:
    return Finding(code=code, severity=severity, ok=ok, message=_pm(message), diagnostic_detail=detail)


def _dec(v):
    """Decimal(str(v)), or None if not numeric/non-finite. None/'' -> None. Lets 1 == 1.0, never truncates.
    Non-finite (NaN, Infinity, -Infinity) -> None so they are treated as malformed (fail-closed), never
    reaching an ordered comparison that would raise decimal.InvalidOperation."""
    if v is None or v == "":
        return None
    try:
        d = Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not d.is_finite():
        return None
    return d


def _is_integer_valued(d) -> bool:
    """Return True if Decimal d is integer-valued (d == d.to_integral_value())."""
    return d is not None and d == d.to_integral_value()


def validate_envelope(env: dict) -> list[Finding]:
    """Catalog-only fail-closed gate (C3/C5/C7). Blocking findings, never a crash."""
    out: list[Finding] = []

    # Hardening D3: schema_version / source_kind contract (top-level, fail-closed at the boundary).
    # Must match the pinned contract before any other structural checks.
    if env.get("schema_version") != NATIVE_SCHEMA_VERSION:
        out.append(_f("invalid_schema_version",
                      "Envelope schema_version does not match the expected contract version",
                      detail=f"expected={NATIVE_SCHEMA_VERSION!r}; got={env.get('schema_version')!r}"))
    if env.get("source_kind") != "native":
        out.append(_f("invalid_source_kind",
                      "Envelope source_kind is not 'native'",
                      detail=f"got={env.get('source_kind')!r}"))

    if not env.get("project_number"):
        out.append(_f("missing_project_number", "Envelope has no project number"))

    # Hardening D1: quote_version REQUIRED non-null integer (idempotency anchor).
    # Accepted: Python int (not bool), or float that is integer-valued (e.g. 1.0).
    # Rejected: absent, null, bool, string (even "1"), non-numeric, fractional (1.5).
    # Rationale: strings are JSON strings not integers; the client must send a JSON number.
    _qv = env.get("quote_version")  # returns None for both absent and present-null
    _qv_present = "quote_version" in env
    if not _qv_present or _qv is None:
        # absent or explicit null
        out.append(_f("missing_quote_version", "Envelope has no valid quote_version (must be a non-null integer)"))
    elif isinstance(_qv, bool):
        # bool is a subtype of int in Python; reject it
        out.append(_f("missing_quote_version", "Envelope has no valid quote_version (must be a non-null integer)"))
    elif isinstance(_qv, str):
        # strings rejected even if they look like integers (e.g. "1")
        out.append(_f("missing_quote_version", "Envelope has no valid quote_version (must be a non-null integer)"))
    elif isinstance(_qv, int):
        # pure integer: OK
        pass
    else:
        # float or other numeric: check integer-valued via Decimal
        _qv_dec = _dec(_qv)
        if _qv_dec is None or not _is_integer_valued(_qv_dec):
            out.append(_f("missing_quote_version", "Envelope has no valid quote_version (must be a non-null integer)"))
        # else: float with integer-valued (e.g. 1.0) -> OK

    # Hardening D3 FIX-2: top-level container shape checks (fail-closed before any dereference).
    # totals: if present and NOT a dict -> malformed_shape (the pivot does .get("bid_cents") on it).
    _raw_totals = env.get("totals")
    if _raw_totals is not None and not isinstance(_raw_totals, dict):
        out.append(_f("malformed_shape", "Envelope 'totals' is not an object",
                      detail=f"type={type(_raw_totals).__name__!r}"))
    # scopes: if present and NOT a list -> malformed_shape (can't iterate safely).
    _raw_scopes = env.get("scopes")
    if _raw_scopes is not None and not isinstance(_raw_scopes, list):
        out.append(_f("malformed_shape", "Envelope 'scopes' is not an array",
                      detail=f"type={type(_raw_scopes).__name__!r}"))

    # Top-level totals: bid_cents present-but-non-numeric OR present-but-fractional OR negative -> malformed_total
    # Safe: only inspect as dict when it IS a dict (non-dict already flagged above as malformed_shape).
    _raw_totals_val = env.get("totals")
    totals = (_raw_totals_val or {}) if isinstance(_raw_totals_val, dict) else {}
    _bid_dec = None
    _bid_ok = False
    if "bid_cents" in totals:
        _bid = totals["bid_cents"]
        _bid_dec = _dec(_bid)
        if _bid_dec is None:
            out.append(_f("malformed_total", "Envelope totals contain a non-numeric value",
                          detail="field=bid_cents"))
        elif not _is_integer_valued(_bid_dec):
            out.append(_f("malformed_total", "Envelope totals contain a fractional (non-integer) value",
                          detail="field=bid_cents"))
        elif _bid_dec < 0:
            out.append(_f("malformed_total", "Envelope totals contain a negative value",
                          detail="field=bid_cents"))
        else:
            _bid_ok = True

    # Hardening D3 gap 4: collect all included catalog line_uids for global uniqueness check.
    _all_line_uids: list[str] = []

    # Safe iteration: only iterate scopes when it is actually a list (non-list already flagged above).
    _scopes_iter = env.get("scopes", []) if isinstance(env.get("scopes"), list) else []
    for i, sc in enumerate(_scopes_iter or [], start=1):
        # Hardening D3 FIX-2: per-scope shape check — MUST run BEFORE any sc.get() call.
        # A non-dict scope element (e.g. None, a string) -> malformed_shape + skip this scope.
        if not isinstance(sc, dict):
            out.append(_f("malformed_shape", f"Scope #{i} is not an object (must be a JSON object)",
                          detail=f"type={type(sc).__name__!r}"))
            continue

        # Hardening A: scope identity / lineage fields required by the pivot
        if not sc.get("name"):
            out.append(_f("missing_scope_name", f"Scope #{i} has no name",
                          detail=f"scope_id={sc.get('scope_id')!r}"))
        if not sc.get("scope_id"):
            out.append(_f("missing_scope_id", f"Scope #{i} has no scope_id",
                          detail=f"name={sc.get('name')!r}"))
        if not sc.get("neta_standard"):
            out.append(_f("missing_neta_standard", f"Scope #{i} has no neta_standard",
                          detail=f"scope_id={sc.get('scope_id')!r}"))

        # Hardening D3 FIX-2: scope_totals shape check — if present and NOT a dict -> malformed_shape.
        # The code below does st.get(...) on scope_totals; a non-dict would cause AttributeError.
        _raw_st = sc.get("scope_totals")
        if _raw_st is not None and not isinstance(_raw_st, dict):
            out.append(_f("malformed_shape", f"Scope #{i} 'scope_totals' is not an object",
                          detail=f"type={type(_raw_st).__name__!r}"))
            continue

        st = sc.get("scope_totals", {}) or {}

        # Hardening D1: service_cents/cost_cents — if present-and-non-numeric -> malformed_total
        # (previously `_dec(...) or Decimal(0)` silently zeroed non-numeric, bypassing nonzero check)
        _svc_cents_raw = st["service_cents"] if "service_cents" in st else 0
        _svc_cents_dec = _dec(_svc_cents_raw)
        if "service_cents" in st and _svc_cents_dec is None:
            out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                          detail=f"field=service_cents"))
        else:
            svc_cents = _svc_cents_dec if _svc_cents_dec is not None else Decimal(0)
            # Hardening D3 gap 2: service_hours present-null/non-numeric -> malformed_total (never silently zero).
            # Mirror the D1 fix for service_cents: if present and _dec is None -> blocking malformed_total.
            if "service_hours" in st and _dec(st["service_hours"]) is None:
                out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                              detail=f"field=service_hours"))
            else:
                svc_hours = _dec(st.get("service_hours", 0)) or Decimal(0)
                if svc_cents != 0 or svc_hours != 0:
                    out.append(_f("nonzero_service", f"Scope #{i} carries service work (not supported in v1)",
                                  detail=f"scope={sc.get('scope_id')!r}"))

        _cost_cents_raw = st["cost_cents"] if "cost_cents" in st else 0
        _cost_cents_dec = _dec(_cost_cents_raw)
        if "cost_cents" in st and _cost_cents_dec is None:
            out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                          detail=f"field=cost_cents"))
        else:
            if (_cost_cents_dec if _cost_cents_dec is not None else Decimal(0)) != 0:
                out.append(_f("nonzero_cost", f"Scope #{i} carries cost lines (not supported in v1)",
                              detail=f"scope={sc.get('scope_id')!r}"))
        m4 = _dec(sc.get("replication_m4"))
        if m4 is None or m4 != Decimal(1):   # R1-5: Decimal so 1.0 passes; 1.5/2 reject
            out.append(_f("m4_unsupported", f"Scope #{i} replication is not 1 (deferred)",
                          detail=f"replication_m4={sc.get('replication_m4')!r}"))

        # Hardening D1: scope_totals/scope fields with present-null detection and type guards.
        # Integer-cents fields (onsite_labor_cents, offsite_labor_cents): absent->default 0 OK;
        #   present-null/non-numeric/fractional/negative -> malformed_total.
        # Numeric (fractional-OK) fields (adjustment_multiplier_n4, quoted_app_hours): absent->default OK;
        #   present-null/non-numeric -> malformed_total.
        for _fld, _container, _key in (
            ("adjustment_multiplier_n4", sc, "adjustment_multiplier_n4"),
            ("quoted_app_hours", st, "quoted_app_hours"),
        ):
            if _key in _container:
                _val = _container[_key]
                _d = _dec(_val)
                if _d is None:
                    out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                                  detail=f"field={_fld}"))

        for _fld, _key in (("onsite_labor_cents", "onsite_labor_cents"), ("offsite_labor_cents", "offsite_labor_cents")):
            if _key in st:
                _val = st[_key]
                _d = _dec(_val)
                if _d is None:
                    out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                                  detail=f"field={_fld}"))
                elif not _is_integer_valued(_d):
                    out.append(_f("malformed_total", f"Scope #{i} has a fractional (non-integer) value in an integer-cents field",
                                  detail=f"field={_fld}"))
                elif _d < 0:
                    out.append(_f("malformed_total", f"Scope #{i} has a negative value in an integer-cents field",
                                  detail=f"field={_fld}"))

        # Hardening D2/D3: per-scope adjusted-cents reconciliation.
        # D3 gap 3: adjusted_cents is now REQUIRED (not optional-silent-skip).
        # When all the other required numeric inputs are present/valid, adjusted_cents MUST
        # also be present and numeric; absent/non-numeric -> blocking missing_adjusted_cents.
        # (The ±1-cent mismatch check only runs when adjusted_cents is present and numeric.)
        _onsite_d  = _dec(st.get("onsite_labor_cents", 0))
        _offsite_d = _dec(st.get("offsite_labor_cents", 0))
        _m4_d      = _dec(sc.get("replication_m4"))
        _n4_d      = _dec(sc.get("adjustment_multiplier_n4"))
        _adj_raw   = st.get("adjusted_cents")  # None if key absent
        _adj_present = "adjusted_cents" in st
        _adj_d     = _dec(_adj_raw)  # None if non-numeric OR if key absent
        if (
            _onsite_d is not None and _offsite_d is not None
            and _m4_d is not None and _n4_d is not None
        ):
            # D3: adjusted_cents must be present and numeric at this stage
            if not _adj_present or _adj_d is None:
                out.append(_f(
                    "missing_adjusted_cents",
                    f"Scope #{i} adjusted_cents is absent or non-numeric (required for reconciliation)",
                    detail=f"scope_id={sc.get('scope_id')!r}; adjusted_cents={_adj_raw!r}",
                ))
            else:
                _derived = (_onsite_d + _offsite_d) * _m4_d * _n4_d
                if abs(_derived - _adj_d) > Decimal(1):
                    out.append(_f(
                        "scope_adjusted_mismatch",
                        f"Scope #{i} adjusted cents do not reconcile with derived component economics",
                        detail=f"scope_id={sc.get('scope_id')!r}; derived={int(_derived)}; adjusted_cents={int(_adj_d)}",
                    ))

        # Hardening D3 FIX-2: lines shape check — if present and NOT a list -> malformed_shape.
        _raw_lines = sc.get("lines")
        if _raw_lines is not None and not isinstance(_raw_lines, list):
            out.append(_f("malformed_shape", f"Scope #{i} 'lines' is not an array",
                          detail=f"type={type(_raw_lines).__name__!r}"))
            continue

        for j, ln in enumerate(sc.get("lines", []) or [], start=1):
            # Hardening D3 FIX-2: per-line shape check — MUST run BEFORE any ln.get() call.
            if not isinstance(ln, dict):
                out.append(_f("malformed_shape", f"Scope #{i} line #{j} is not an object (must be a JSON object)",
                              detail=f"type={type(ln).__name__!r}"))
                continue

            if not ln.get("included", True):
                continue
            kind = ln.get("line_kind")
            if kind not in _LINE_KINDS:
                out.append(_f("invalid_line_state", f"Scope #{i} has a line with an unknown kind",
                              detail=f"line_uid={ln.get('line_uid')!r}; line_kind={kind!r}"))
                continue
            if kind != "catalog":
                out.append(_f("non_catalog_line", f"Scope #{i} has a non-catalog line (not supported in v1)",
                              detail=f"line_uid={ln.get('line_uid')!r}; line_kind={kind!r}"))
                continue

            # Hardening A + D3 fix-3: line identity must be a non-empty STRING (pivot idempotency +
            # the duplicate-uid check below uses set membership, which a list/dict line_uid would crash).
            _luid = ln.get("line_uid")
            if not isinstance(_luid, str) or not _luid:
                out.append(_f("missing_line_uid", f"Scope #{i} catalog line has a missing or non-string line_uid",
                              detail=f"line_uid={_luid!r}; type={type(_luid).__name__}; "
                                     f"equipment_model_ref={ln.get('equipment_model_ref')!r}"))
            else:
                _all_line_uids.append(_luid)

            for fld in _REQUIRED_CATALOG_FIELDS:
                if ln.get(fld) in (None, ""):
                    out.append(_f("missing_required_catalog_field",
                                  f"Scope #{i} catalog line is missing a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={fld}"))

            # Hardening D1: integer-qty fields (base_qty, project_intake_qty) — must be non-negative integers.
            # resolved_ref_hours — REQUIRED numeric (fractional OK); present-null/non-numeric -> malformed_catalog_field.
            # Keep Hardening A non-numeric check for all three first; then add integer/negative for qty.
            _qty_ok = {}  # track per-field validity for qty_mismatch gate below
            for _num_fld in ("base_qty", "project_intake_qty", "resolved_ref_hours"):
                _val = ln.get(_num_fld)
                if _val in (None, ""):
                    # missing/null — already caught by missing_required_catalog_field above; skip here
                    _qty_ok[_num_fld] = False
                    continue
                _d = _dec(_val)
                if _d is None:
                    out.append(_f("malformed_catalog_field",
                                  f"Scope #{i} catalog line has a non-numeric value in a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))
                    _qty_ok[_num_fld] = False
                elif _num_fld in ("base_qty", "project_intake_qty"):
                    # D1/D3-fix: integer-qty: must be a POSITIVE integer (>= 1).
                    # An included catalog line means "test >= 1 of these"; zero-qty is malformed
                    # and would otherwise silently materialize 1 apparatus via the `0 or 1` fallback
                    # in the shared materialize helper (wrong materialization at the financial boundary).
                    if not _is_integer_valued(_d):
                        out.append(_f("malformed_catalog_field",
                                      f"Scope #{i} catalog line has a fractional (non-integer) quantity",
                                      detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))
                        _qty_ok[_num_fld] = False
                    elif _d < 1:
                        out.append(_f("malformed_catalog_field",
                                      f"Scope #{i} catalog line quantity must be >= 1 (zero or negative not allowed for an included line)",
                                      detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}; value={int(_d)}"))
                        _qty_ok[_num_fld] = False
                    else:
                        _qty_ok[_num_fld] = True
                elif _num_fld == "resolved_ref_hours":
                    # D3 gap 5: resolved_ref_hours must be non-negative (fractional OK; sign check only)
                    if _d < 0:
                        out.append(_f("malformed_catalog_field",
                                      f"Scope #{i} catalog line has negative resolved_ref_hours",
                                      detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))
                        _qty_ok[_num_fld] = False
                    else:
                        _qty_ok[_num_fld] = True
                else:
                    _qty_ok[_num_fld] = True

            # Hardening A: qty_mismatch -- both present and numeric integer but not equal (M4==1 invariant)
            # Only fires when both are valid integers (D1: prevents firing on fractional values)
            if _qty_ok.get("base_qty") and _qty_ok.get("project_intake_qty"):
                _bq = _dec(ln.get("base_qty"))
                _pq = _dec(ln.get("project_intake_qty"))
                if _bq != _pq:
                    out.append(_f("qty_mismatch",
                                  f"Scope #{i} catalog line has mismatched base and intake quantities",
                                  detail=f"line_uid={ln.get('line_uid')!r}"))

    # Hardening D3 gap 4: global duplicate line_uid check.
    # Duplicate line_uids across all included catalog lines -> approve-time DB collision
    # (uq_ops_apparatus_intake). Reject BEFORE storing as parsed.
    _seen_uids: set[str] = set()
    for _uid in _all_line_uids:
        if _uid in _seen_uids:
            out.append(_f("duplicate_line_uid",
                          "Envelope contains duplicate catalog line identifiers (line_uid must be globally unique)",
                          detail=f"duplicate line_uid={_uid!r}"))
            break  # one finding is sufficient; PM-safe
        _seen_uids.add(_uid)

    # Hardening D3 fix-3 (c): native project-level bid reconciliation at the PACKET tolerance (±1 cent).
    # The shared validate_payload.contract_total uses a ±$1.00 tolerance; the native packet requires
    # bid_cents to reconcile with the sum of per-scope adjusted_cents within 1 cent. Native-side ONLY
    # (do NOT change the shared validator). Only runs on an otherwise-clean envelope so the sum is over
    # validated, present+numeric scope economics.
    if _bid_ok and not out:
        _scopes_iter = env.get("scopes") if isinstance(env.get("scopes"), list) else []
        _sum_derived = Decimal(0)
        _derivable = True
        for _sc in _scopes_iter:
            _st = _sc.get("scope_totals", {}) or {}
            _on = _dec(_st.get("onsite_labor_cents", 0))
            _off = _dec(_st.get("offsite_labor_cents", 0))
            _m4 = _dec(_sc.get("replication_m4"))
            _n4 = _dec(_sc.get("adjustment_multiplier_n4"))
            if _on is None or _off is None or _m4 is None or _n4 is None:
                # Any derivation input absent/non-numeric -> cannot derive the project total here.
                # (Consistent with the per-scope D2 check, which also skips when these are None.)
                _derivable = False
                break
            _sum_derived += (_on + _off) * _m4 * _n4
        if _derivable and abs(_bid_dec - _sum_derived) > Decimal(1):
            out.append(_f(
                "native_bid_mismatch",
                "Envelope bid total does not reconcile with the sum of derived scope economics (native +/- 1 cent)",
                detail=f"bid_cents={int(_bid_dec)}; sum_derived_cents={int(_sum_derived)}",
            ))

    return out


def _cents_to_dollars(cents) -> float:
    # Use _dec so integer-valued string/float forms (e.g. "100000.0", "1e5", 100000.0) coerce
    # cleanly via Decimal — the guard guarantees integer-valued, so int(d) is exact.
    d = _dec(cents)
    return float((Decimal(int(d) if d is not None else 0) / Decimal(100)).quantize(Decimal("0.01")))


def pivot_to_intake_payload(env: dict) -> dict:
    """Catalog-only pivot. Callers MUST validate_envelope() first (this is strict: it dereferences
    required catalog fields). Money: integer cents -> float dollars (numeric, matches workbook contract)."""
    pn = env.get("project_number")
    project = ProjectIn(
        project_number=pn,
        project_name=pn or "",                     # Q-2: envelope has no name; fall back to project_number
        contract_value=_cents_to_dollars((env.get("totals", {}) or {}).get("bid_cents", 0)),
    )
    scopes = []
    for sc in env.get("scopes", []) or []:
        st = sc.get("scope_totals", {}) or {}
        quote = ScopeQuoteIn(
            onsite_labor=_cents_to_dollars(st.get("onsite_labor_cents", 0)),
            offsite_labor=_cents_to_dollars(st.get("offsite_labor_cents", 0)),
            travel=0.0,
            outside_services=0.0,
            unit_multiplier=float(Decimal(str(sc.get("replication_m4", 1)))),
            pct_adjust=float(Decimal(str(sc.get("adjustment_multiplier_n4", 1)))),
            # D3 FIX-2: coerce quoted_app_hours via _dec so numeric-string forms (e.g. "18")
            # don't survive as a str into validate_payload's J3 float arithmetic (-> TypeError/500).
            total_quoted_hours=float(_dec(st.get("quoted_app_hours", 0)) or 0),
        )
        lines = []
        for ln in sc.get("lines", []) or []:
            if not ln.get("included", True) or ln.get("line_kind") != "catalog":
                continue
            # D3 gap 5: coerce resolved_ref_hours through _dec (like cents/qty) so string "10.0"
            # becomes float 10.0 in the payload rather than crashing downstream arithmetic.
            _rrh = float(_dec(ln["resolved_ref_hours"]))
            lines.append(QuoteLineIn(
                apparatus_type=ln["equipment_model_ref"],          # model-key; resolve_models -> uuid at approve
                test_standard=sc.get("neta_standard"),             # scope -> line fan-out
                qty=int(_dec(ln["base_qty"])),                     # == project_intake_qty at M4==1; _dec handles "3.0"/"3"/3
                hrs_per_unit=_rrh,
                catalog_default_hours=_rrh,
                line_uid=ln.get("line_uid"),
                section=None,                                      # envelope has no section -> __ungrouped__ task
                designation=ln.get("designation"),
                notes=ln.get("notes"),
                description=ln.get("description"),
            ))
        scopes.append(ScopeIn(scope_name=sc["name"], scope_type="OTHER", sort_order=0, quote=quote, lines=lines))
    return json.loads(json.dumps(dataclasses.asdict(IntakePayload(project=project, scopes=scopes)), default=str))


def recompute_content_hash(env: dict) -> str:
    """Server-side idempotency hash over the pivoted economic payload (C6: never trust the client hash).
    Deterministic (sort_keys). Free-text metadata fields (designation/notes/description) are excluded
    so that two envelopes identical in economics hash identically regardless of field-label differences
    (economic-neutral invariant). The stored payload and scope_quote_line rows retain all metadata."""
    payload = pivot_to_intake_payload(env)
    for sc in payload.get("scopes") or []:
        for ln in sc.get("lines") or []:
            ln.pop("designation", None)
            ln.pop("notes", None)
            ln.pop("description", None)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
