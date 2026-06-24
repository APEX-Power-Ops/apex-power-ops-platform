from __future__ import annotations

from decimal import Decimal, InvalidOperation

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
    for i, sc in enumerate(env.get("scopes", []) or [], start=1):
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
            for fld in _REQUIRED_CATALOG_FIELDS:
                if ln.get(fld) in (None, ""):
                    out.append(_f("missing_required_catalog_field",
                                  f"Scope #{i} catalog line is missing a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={fld}"))
    return out
