"""Deterministic, guarded seed generator for core.equipment_models (estimator step 4a).
Source of truth: 008_equipment_models.seed.json (estimator-core catalog, pinned).
4a seeds the ACTIVE dimension only; merge edges (merged_into_ref) are a 4b concern and
this generator REFUSES to emit them (it does not resolve the self-FK uuid). Same input
-> byte-identical SQL. Never hand-edit the emitted seed block."""
from __future__ import annotations
import hashlib, json, pathlib

HERE = pathlib.Path(__file__).parent
SEED = HERE / "008_equipment_models.seed.json"
SHA256 = "dfe59bc3c35a6d74388ca9b703fa276bc7ef9d184c973dfb9c0cc4e288a8c8d1"
EXPECTED_ROWS = 120

def load_models() -> list[dict]:
    raw = SEED.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    assert got == SHA256, f"seed sha256 drift: {got} != {SHA256}"
    models = json.loads(raw)
    assert len(models) == EXPECTED_ROWS, f"row count {len(models)} != {EXPECTED_ROWS}"
    bad = [m["ref"] for m in models
           if m.get("lifecycle_status") != "active" or m.get("merged_into_ref") is not None]
    assert not bad, (f"4a seed must be active-only; merge data is deferred to 4b "
                     f"(generator does not emit merged_into_id). Offending refs: {bad}")
    return models

def _sql(v) -> str:
    if v is None: return "null"
    if isinstance(v, bool): raise TypeError("unexpected bool")
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return repr(v)
    return "'" + str(v).replace("'", "''") + "'"

def emit_inserts() -> str:
    rows = sorted(load_models(), key=lambda m: m["ref"])  # 120 distinct refs -> total order
    out = []
    for m in rows:
        ns, rh = m["neta_section"], m["ref_hours"]
        out.append(
            "insert into core.equipment_models "
            "(model_key, apparatus, neta_section_ats, neta_section_mts, "
            "ref_hours_ats, ref_hours_mts, unit_of_issue, lifecycle_status) values ("
            f"{_sql(m['ref'])}, {_sql(m['apparatus'])}, {_sql(ns.get('ATS'))}, {_sql(ns.get('MTS'))}, "
            f"{_sql(rh.get('ATS'))}, {_sql(rh.get('MTS'))}, {_sql(m['unit_of_issue'])}::core.unit_of_issue, "
            f"{_sql(m['lifecycle_status'])}::core.equipment_lifecycle);"
        )
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    a, b = emit_inserts(), emit_inserts()
    assert a == b, "emit_inserts() not byte-stable across runs"
    models = load_models()
    lines = a.strip().splitlines()
    assert len(lines) == len(models) == EXPECTED_ROWS, "emitted line count != source row count"
    # robust coverage: each ref's EXACT escaped literal appears as the model_key (1st VALUES arg).
    for m in models:                       # refs can contain ', ' -> never comma-split
        assert ("values (" + _sql(m["ref"]) + ", ") in a, f"missing seeded model_key {m['ref']!r}"
    print(a, end="")
