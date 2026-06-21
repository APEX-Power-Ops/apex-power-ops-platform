"""
Route-guard test for the ops intake router.

Mirrors tests/test_learning_resources.py::test_learning_routes_guarded_by_env.
Asserts that _ops_intake_enabled() is gated on OPS_DEV_DSN only — it does NOT
start a subprocess or touch the database; it just tests the guard function.
"""


def test_ops_intake_routes_guarded_by_env(monkeypatch):
    from main import _ops_intake_enabled
    monkeypatch.delenv("OPS_DEV_DSN", raising=False)
    assert _ops_intake_enabled() is False
    monkeypatch.setenv("OPS_DEV_DSN", "host=127.0.0.1 dbname=ops_test")
    assert _ops_intake_enabled() is True
