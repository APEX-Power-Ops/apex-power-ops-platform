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


def validate_envelope(env: dict) -> list[Finding]:
    """Catalog-only fail-closed gate (C3/C5/C7). Blocking findings, never a crash."""
    out: list[Finding] = []
    if not env.get("project_number"):
        out.append(_f("missing_project_number", "Envelope has no project number"))

    # Top-level totals: bid_cents present-but-non-numeric -> malformed_total
    totals = env.get("totals", {}) or {}
    _bid = totals.get("bid_cents")
    if _bid is not None and _dec(_bid) is None:
        out.append(_f("malformed_total", "Envelope totals contain a non-numeric value",
                      detail="field=bid_cents"))

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
        svc_cents = _dec(st.get("service_cents", 0)) or Decimal(0)
        svc_hours = _dec(st.get("service_hours", 0)) or Decimal(0)   # R1-5: scope-level service_hours too
        if svc_cents != 0 or svc_hours != 0:
            out.append(_f("nonzero_service", f"Scope #{i} carries service work (not supported in v1)",
                          detail=f"scope={sc.get('scope_id')!r}"))
        if (_dec(st.get("cost_cents", 0)) or Decimal(0)) != 0:
            out.append(_f("nonzero_cost", f"Scope #{i} carries cost lines (not supported in v1)",
                          detail=f"scope={sc.get('scope_id')!r}"))
        m4 = _dec(sc.get("replication_m4"))
        if m4 is None or m4 != Decimal(1):   # R1-5: Decimal so 1.0 passes; 1.5/2 reject
            out.append(_f("m4_unsupported", f"Scope #{i} replication is not 1 (deferred)",
                          detail=f"replication_m4={sc.get('replication_m4')!r}"))

        # Hardening A: scope_totals numeric fields strictly dereferenced by pivot
        _sc_numeric_fields = (
            ("adjustment_multiplier_n4", sc.get("adjustment_multiplier_n4")),
            ("onsite_labor_cents", st.get("onsite_labor_cents")),
            ("offsite_labor_cents", st.get("offsite_labor_cents")),
            ("quoted_app_hours", st.get("quoted_app_hours")),
        )
        for _fld, _val in _sc_numeric_fields:
            if _val is not None and _dec(_val) is None:
                out.append(_f("malformed_total", f"Scope #{i} has a non-numeric value in a totals field",
                              detail=f"field={_fld}"))

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

            for fld in _REQUIRED_CATALOG_FIELDS:
                if ln.get(fld) in (None, ""):
                    out.append(_f("missing_required_catalog_field",
                                  f"Scope #{i} catalog line is missing a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={fld}"))

            # Hardening A: numeric-type guards for fields pivot dereferences as int()/Decimal()
            for _num_fld in ("base_qty", "project_intake_qty", "resolved_ref_hours"):
                _val = ln.get(_num_fld)
                if _val not in (None, "") and _dec(_val) is None:
                    out.append(_f("malformed_catalog_field",
                                  f"Scope #{i} catalog line has a non-numeric value in a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={_num_fld}"))

            # Hardening A: qty_mismatch -- both present and numeric but not equal (M4==1 invariant)
            _bq = _dec(ln.get("base_qty"))
            _pq = _dec(ln.get("project_intake_qty"))
            if _bq is not None and _pq is not None and _bq != _pq:
                out.append(_f("qty_mismatch",
                              f"Scope #{i} catalog line has mismatched base and intake quantities",
                              detail=f"line_uid={ln.get('line_uid')!r}"))

    return out


def _cents_to_dollars(cents) -> float:
    return float((Decimal(int(cents or 0)) / Decimal(100)).quantize(Decimal("0.01")))


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
            lines.append(QuoteLineIn(
                apparatus_type=ln["equipment_model_ref"],          # model-key; resolve_models -> uuid at approve
                test_standard=sc.get("neta_standard"),             # scope -> line fan-out
                qty=int(ln["base_qty"]),                           # == project_intake_qty at M4==1
                hrs_per_unit=ln["resolved_ref_hours"],
                catalog_default_hours=ln["resolved_ref_hours"],
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
