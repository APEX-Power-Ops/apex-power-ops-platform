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
    """Decimal(str(v)), or None if not numeric (None/'' -> None). Lets 1 == 1.0 and never truncates."""
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


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

    # Top-level totals: bid_cents present-but-non-numeric OR present-but-fractional OR negative -> malformed_total
    totals = env.get("totals", {}) or {}
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

    # Hardening D3 gap 4: collect all included catalog line_uids for global uniqueness check.
    _all_line_uids: list[str] = []

    for i, sc in enumerate(env.get("scopes", []) or [], start=1):
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

        for ln in sc.get("lines", []) or []:
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

            # Hardening A: line identity field required by pivot idempotency
            if not ln.get("line_uid"):
                out.append(_f("missing_line_uid", f"Scope #{i} catalog line has no line_uid",
                              detail=f"equipment_model_ref={ln.get('equipment_model_ref')!r}"))
            else:
                # D3 gap 4: collect for global duplicate check (only when line_uid is present)
                _all_line_uids.append(ln["line_uid"])

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
                    # D1: integer-qty: must be non-negative integer
                    if not _is_integer_valued(_d):
                        out.append(_f("malformed_catalog_field",
                                      f"Scope #{i} catalog line has a fractional (non-integer) quantity",
                                      detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))
                        _qty_ok[_num_fld] = False
                    elif _d < 0:
                        out.append(_f("malformed_catalog_field",
                                      f"Scope #{i} catalog line has a negative quantity",
                                      detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))
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
            total_quoted_hours=st.get("quoted_app_hours", 0),
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
            ))
        scopes.append(ScopeIn(scope_name=sc["name"], scope_type="OTHER", sort_order=0, quote=quote, lines=lines))
    return json.loads(json.dumps(dataclasses.asdict(IntakePayload(project=project, scopes=scopes)), default=str))


def recompute_content_hash(env: dict) -> str:
    """Server-side idempotency hash over the pivoted economic payload (C6: never trust the client hash).
    Deterministic (sort_keys). Call only on a validated envelope (the pivot is strict)."""
    blob = json.dumps(pivot_to_intake_payload(env), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
