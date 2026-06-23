import psycopg
from ops_intake.catalog import resolve_models, m4_ok

def test_resolve_models_returns_resolvable_subset(clean_ops):
    with psycopg.connect(clean_ops) as c:
        out = resolve_models(c.cursor(), ["Capcitors - Per Unit", "NOPE", "Capcitors - Per Unit", ""])
    assert out["Capcitors - Per Unit"]      # resolvable -> non-empty uuid string, deduped
    assert "NOPE" not in out and "" not in out   # unresolved / empty dropped

def test_m4_ok_is_strict():
    assert m4_ok({"unit_multiplier": 1}) and m4_ok({"unit_multiplier": "1"}) and m4_ok({"unit_multiplier": 1.0})
    for bad in [{}, {"unit_multiplier": None}, {"unit_multiplier": ""}, {"unit_multiplier": 0},
                {"unit_multiplier": -1}, {"unit_multiplier": 2}, {"unit_multiplier": "abc"}]:
        assert not m4_ok(bad), bad     # missing / falsey / invalid / non-1 all rejected
