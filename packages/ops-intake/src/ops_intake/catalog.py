from __future__ import annotations

"""Catalog resolution + the M4 gate for the 4b.1 approve precheck.

resolve_models() turns estimator apparatus_type strings (= core.equipment_models
model_key) into their TERMINAL ACTIVE identity uuid via the merge-chasing resolver
view core.v_equipment_models_resolved. A key that is absent / deprecated /
merged-dead / on a cycle yields NO row -> it is 'unresolved'.
"""

from decimal import Decimal, InvalidOperation


def resolve_models(cur, model_keys: list[str]) -> dict[str, str]:
    """Return {model_key: resolved_id} for the RESOLVABLE subset. Resolver-only read."""
    keys = sorted({k for k in model_keys if isinstance(k, str) and k})
    if not keys:
        return {}
    rows = cur.execute(
        "select requested_model_key, resolved_id"
        "  from core.v_equipment_models_resolved"
        " where requested_model_key = any(%s)",
        (keys,),
    ).fetchall()
    return {k: str(rid) for (k, rid) in rows}


def m4_ok(quote: dict) -> bool:
    """True IFF unit_multiplier is present and exactly Decimal('1').

    Strict: missing, '', 0, negative, non-1, or unparseable all return False (M4 != 1
    is deferred to 4b.2). Never coerce a falsey value to 1.
    """
    raw = quote.get("unit_multiplier")
    if raw is None:
        return False
    try:
        return Decimal(str(raw)) == Decimal("1")
    except (InvalidOperation, TypeError, ValueError):
        return False
