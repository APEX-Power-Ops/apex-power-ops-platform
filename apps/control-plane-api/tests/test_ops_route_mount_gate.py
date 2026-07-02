# test_ops_route_mount_gate.py -- NO-DB module for the ops-route mount/host gating tests.
# Deliberately carries NO apply_migrations autouse fixture, so it runs at Task 8 (before the
# Task-10 route-harness cutover). It only imports main/_ops_intake_enabled and spawns a
# subprocess; config.py requires DATABASE_URL at import, so set a placeholder first.
import os, pathlib, subprocess, sys
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/ops_test")


def test_ops_intake_enabled_requires_both_role_dsns(monkeypatch):
    from main import _ops_intake_enabled
    monkeypatch.delenv("OPS_INTAKE_WRITER_DSN", raising=False)
    monkeypatch.delenv("OPS_API_DSN", raising=False)
    monkeypatch.delenv("OPS_DEV_DSN", raising=False)
    assert _ops_intake_enabled() is False
    monkeypatch.setenv("OPS_INTAKE_WRITER_DSN", "x")
    assert _ops_intake_enabled() is False, "writer DSN alone must not mount"
    monkeypatch.setenv("OPS_API_DSN", "y")
    assert _ops_intake_enabled() is True
    monkeypatch.delenv("OPS_INTAKE_WRITER_DSN")
    assert _ops_intake_enabled() is False, "api DSN alone must not mount"
    monkeypatch.setenv("OPS_DEV_DSN", "z")
    assert _ops_intake_enabled() is False, "OPS_DEV_DSN must be inert"


def test_recognition_router_host_gated_subprocess():
    """With the role DSNs unset, the recognition routes are NOT mounted (404)."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("OPS_INTAKE_WRITER_DSN", "OPS_API_DSN", "OPS_DEV_DSN")}
    env["DATABASE_URL"] = "postgresql://localhost/ops_test"
    code = ("import os;"
            "[os.environ.pop(k, None) for k in ('OPS_INTAKE_WRITER_DSN','OPS_API_DSN','OPS_DEV_DSN')];"
            "from fastapi.testclient import TestClient; from main import app;"
            "c=TestClient(app);"
            "import sys; sys.exit(0 if c.post('/api/v1/ops/recognition/completion/attest',json={}).status_code==404 else 1)")
    r = subprocess.run([sys.executable, "-c", code],
                       cwd=str(pathlib.Path(__file__).resolve().parents[1]), env=env)
    assert r.returncode == 0, "recognition routes must be absent when the role DSNs are unset"
