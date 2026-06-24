"""
Task 13 -- API route tests for the ops intake router.

Covers:
  - route-guard (Task 12, kept here)
  - upload (POST /api/v1/ops/intake)
  - get run (GET /api/v1/ops/intake/{run_id})
  - review (POST /api/v1/ops/intake/{run_id}/review)
  - approve (POST /api/v1/ops/intake/{run_id}/approve)
  - reject (POST /api/v1/ops/intake/{run_id}/reject)
  - finance-redaction: no diagnostic_detail field anywhere, no $ in finding messages

OPS_DEV_DSN must target ops_test (enforced by the migration fixture).
"""
from __future__ import annotations

import os
import pathlib
import sys
import uuid

# Set DATABASE_URL before config.py is imported so it doesn't raise at collection time.
# The TestClient overrides the actual DB via OPS_DEV_DSN; this placeholder satisfies config.py.
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/ops_test")

import psycopg
import pytest

# ---------------------------------------------------------------------------
# Locate fixture builder (mirror the package conftest pattern)
# ---------------------------------------------------------------------------
_FIXTURE_DIR = (
    pathlib.Path(__file__).resolve().parents[3]
    / "packages/ops-intake/tests/fixtures"
)
sys.path.insert(0, str(_FIXTURE_DIR))
from build_fixture import build  # noqa: E402

# ---------------------------------------------------------------------------
# Migration setup -- mirrors packages/ops-intake/tests/conftest.py exactly
# ---------------------------------------------------------------------------
_MIGRATIONS_DIR = (
    pathlib.Path(__file__).resolve().parents[3]
    / "infra/database/migrations/ops"
)

_OPS_TRUNCATE = (
    "truncate ops.apparatus, ops.scope_quote_line, ops.scope_quote, "
    "ops.scopes, ops.standard_hours, ops.projects, ops.tasks, "
    "ops.intake_validation_findings, ops.intake_source_files, ops.intake_runs cascade;"
)


def _require_ops_test(dsn: str) -> None:
    from psycopg.conninfo import conninfo_to_dict

    db = conninfo_to_dict(dsn).get("dbname")
    assert db == "ops_test", (
        "Safety guard: DSN must target dbname=ops_test, got " + repr(db)
    )


def _dsn() -> str:
    return os.environ["OPS_DEV_DSN"]  # set by the test runner command


def _ops_schema_exists(conn) -> bool:
    """Return True if the ops schema exists in the database (copied from package conftest)."""
    row = conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone()
    return row is not None


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply full migration ladder 001→010 (incl. 009) to ops_test, yield, then teardown.
    Reset blocks guard native+009 teardown with _ops_schema_exists so a fresh ops_test is safe.
    Exercises 010_down and 009_down each session (matching the package conftest ladder)."""
    d = _dsn()
    _require_ops_test(d)

    def _run_sql(conn, path):
        sql = path.read_text(encoding="utf-8")
        conn.execute(sql)

    mig_dir = _MIGRATIONS_DIR
    # pre-up reset: guarded native+009 teardown THEN 008+001 teardown.
    # 009/010 down require the ops schema to exist; guard so a fresh ops_test is safe.
    with psycopg.connect(d, autocommit=True) as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010_down's data-loss guard passes
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
        _run_sql(c, mig_dir / "008_core_equipment_models_down.sql")
        _run_sql(c, mig_dir / "001_identity_skeleton_down.sql")

    up_migrations = [
        "001_identity_skeleton.sql",
        "002_quote_model.sql",
        "003_intake_unique_keys.sql",
        "004_person_anchor.sql",
        "005_recognition_ledger.sql",
        "006_progress_billing.sql",
        "007_intake_envelope.sql",
        "008_core_equipment_models.sql",
        "009_recognition_bridge.sql",
        "010_native_envelope_intake.sql",
    ]
    with psycopg.connect(d, autocommit=True) as c:
        for name in up_migrations:
            _run_sql(c, mig_dir / name)

    yield

    with psycopg.connect(d, autocommit=True) as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010_down's data-loss guard passes
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
        _run_sql(c, mig_dir / "008_core_equipment_models_down.sql")
        _run_sql(c, mig_dir / "001_identity_skeleton_down.sql")


@pytest.fixture(scope="session")
def mini_wb_bytes(tmp_path_factory) -> bytes:
    """Build mini estimator workbook once per session; return raw bytes."""
    path = build(tmp_path_factory.mktemp("wb") / "mini_estimator.xlsx")
    return path.read_bytes()


@pytest.fixture(scope="session")
def person_id(apply_migrations) -> str:
    """Insert one ops.persons row; return the person_id UUID (as str)."""
    d = _dsn()
    with psycopg.connect(d, autocommit=True) as c:
        row = c.execute(
            "insert into ops.persons (display_name) values (%s) returning person_id",
            ("Test PM",),
        ).fetchone()
    return str(row[0])


@pytest.fixture(autouse=True)
def clean_ops_between_tests(apply_migrations):
    """Truncate envelope tables before each test to keep tests independent."""
    d = _dsn()
    _require_ops_test(d)
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(_OPS_TRUNCATE)
    yield


# ---------------------------------------------------------------------------
# App client -- OPS_DEV_DSN is already in os.environ from the shell command
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def client(apply_migrations):
    from fastapi.testclient import TestClient
    from main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper: recursively scan JSON value for substring presence
# ---------------------------------------------------------------------------
def _contains_substring(obj, sub: str) -> bool:
    """Return True if any string value anywhere in the JSON tree contains sub."""
    if isinstance(obj, str):
        return sub in obj
    if isinstance(obj, dict):
        return any(_contains_substring(v, sub) for v in obj.values()) or any(
            _contains_substring(k, sub) for k in obj.keys()
        )
    if isinstance(obj, (list, tuple)):
        return any(_contains_substring(item, sub) for item in obj)
    return False


# ---------------------------------------------------------------------------
# Task 12 route-guard test (kept here per brief)
# ---------------------------------------------------------------------------
def test_ops_intake_routes_guarded_by_env(monkeypatch):
    from main import _ops_intake_enabled

    monkeypatch.delenv("OPS_DEV_DSN", raising=False)
    assert _ops_intake_enabled() is False
    monkeypatch.setenv("OPS_DEV_DSN", "host=127.0.0.1 dbname=ops_test")
    assert _ops_intake_enabled() is True


# ---------------------------------------------------------------------------
# Task 13 tests
# ---------------------------------------------------------------------------


class TestUpload:
    """POST /api/v1/ops/intake"""

    def test_upload_mini_workbook_returns_200_parsed(
        self, client, mini_wb_bytes, person_id
    ):
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "parsed"

    def test_upload_response_has_no_diagnostic_detail(
        self, client, mini_wb_bytes, person_id
    ):
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert not _contains_substring(body, "diagnostic_detail"), (
            "diagnostic_detail must not appear anywhere in the upload response"
        )

    def test_upload_findings_have_no_dollar_sign(
        self, client, mini_wb_bytes, person_id
    ):
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        for finding in body.get("findings", []):
            msg = finding.get("message", "")
            assert "$" not in msg, f"Finding message must not contain $: {msg!r}"

    def test_upload_response_has_expected_fields(
        self, client, mini_wb_bytes, person_id
    ):
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        body = resp.json()
        for field in (
            "run_id",
            "status",
            "conflict_kind",
            "source_format",
            "review_payload",
            "findings",
        ):
            assert field in body, f"Missing field {field!r} in upload response"

    def test_upload_over_25mb_returns_413(self, client, person_id):
        big = b"X" * (25 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={"file": ("huge.xlsm", big, "application/octet-stream")},
        )
        assert resp.status_code == 413, resp.text


class TestGetRun:
    """GET /api/v1/ops/intake/{run_id}"""

    def test_get_run_returns_run(self, client, mini_wb_bytes, person_id):
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        run_id = up.json()["run_id"]
        resp = client.get(f"/api/v1/ops/intake/{run_id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["run_id"] == run_id
        assert body["status"] == "parsed"

    def test_get_run_no_diagnostic_detail(self, client, mini_wb_bytes, person_id):
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        run_id = up.json()["run_id"]
        body = client.get(f"/api/v1/ops/intake/{run_id}").json()
        assert not _contains_substring(body, "diagnostic_detail")

    def test_get_run_unknown_id_returns_404(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/ops/intake/{fake_id}")
        assert resp.status_code == 404


class TestApprove:
    """POST /api/v1/ops/intake/{run_id}/approve"""

    def test_approve_clean_upload_returns_approved(
        self, client, mini_wb_bytes, person_id
    ):
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        assert up.status_code == 200, up.text
        run_id = up.json()["run_id"]
        resp = client.post(
            f"/api/v1/ops/intake/{run_id}/approve",
            json={"approved_by": person_id},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "approved"

    def test_approve_unknown_id_returns_404(self, client):
        resp = client.post(
            f"/api/v1/ops/intake/{uuid.uuid4()}/approve",
            json={"approved_by": "someone"},
        )
        assert resp.status_code == 404

    def test_approve_uncatalogued_returns_422_and_findings_visible(
        self, client, person_id
    ):
        """Precheck-reject (uncatalogued apparatus) surfaces its findings via GET run.

        Contract under test:
          1. POST /approve → 422 with outcome=blocked_findings (body has run_id only)
          2. GET /intake/{run_id} → 200 with at least one blocking uncatalogued_apparatus
             finding whose message mentions the uncatalogued type.
          3. PM-safety: no diagnostic_detail key, no $ in any finding message.
        """
        import json as _json

        # Seed a run in 'reviewing' status with an uncatalogued apparatus_type directly
        # via psycopg (mirrors packages/ops-intake/tests/test_catalog_binding._seed_run).
        d = _dsn()
        payload = {
            "project": {
                "project_number": "UC-ROUTE-1",
                "project_name": "Route Test",
                "contract_value": 1.0,
            },
            "scopes": [
                {
                    "scope_name": "S",
                    "legacy_source_id": "S",
                    "quote": {
                        "onsite_labor": 100,
                        "unit_multiplier": 1,
                        "pct_adjust": 1,
                        "total_quoted_hours": 2,
                    },
                    "lines": [
                        {
                            "apparatus_type": "Not In Catalog",
                            "test_standard": "ATS",
                            "qty": 1,
                            "hrs_per_unit": 2.0,
                            "section": "S1",
                            "line_number": 1,
                            "line_uid": "S:r1",
                        }
                    ],
                }
            ],
        }
        with psycopg.connect(d, autocommit=True) as c:
            row = c.execute(
                "insert into ops.intake_runs"
                " (project_number, source_format, status, payload_schema_version,"
                "  parser_version, canonical_payload_json, review_payload_json, uploaded_by)"
                " values (%s,'decomposed_scope_sheet','reviewing','1','t',%s,%s,%s)"
                " returning id",
                (
                    "UC-ROUTE-1",
                    _json.dumps(payload),
                    _json.dumps(payload),
                    person_id,
                ),
            ).fetchone()
        run_id = str(row[0])

        # 1. POST approve → expect 422 blocked_findings
        resp = client.post(
            f"/api/v1/ops/intake/{run_id}/approve",
            json={"approved_by": person_id},
        )
        assert resp.status_code == 422, resp.text
        body422 = resp.json()
        assert body422.get("detail", {}).get("outcome") == "blocked_findings", body422

        # 2. GET run → findings contain the blocking uncatalogued_apparatus finding
        resp2 = client.get(f"/api/v1/ops/intake/{run_id}")
        assert resp2.status_code == 200, resp2.text
        body_get = resp2.json()
        findings = body_get.get("findings", [])
        blocking = [
            f
            for f in findings
            if f.get("severity") == "blocking"
            and f.get("ok") is False
            and f.get("code") == "uncatalogued_apparatus"
        ]
        assert blocking, (
            f"Expected at least one blocking uncatalogued_apparatus finding; got: {findings}"
        )
        assert any("Not In Catalog" in f.get("message", "") for f in blocking), (
            f"Expected 'Not In Catalog' in a blocking finding message; got: {blocking}"
        )

        # 3. PM-safety: no diagnostic_detail anywhere, no $ in finding messages
        assert not _contains_substring(body_get, "diagnostic_detail"), (
            "diagnostic_detail must not appear anywhere in GET run response"
        )
        for f in findings:
            msg = f.get("message", "")
            assert "$" not in msg, f"Finding message must not contain $: {msg!r}"


class TestReject:
    """POST /api/v1/ops/intake/{run_id}/reject"""

    def test_reject_returns_rejected_status(self, client, mini_wb_bytes, person_id):
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        run_id = up.json()["run_id"]
        resp = client.post(
            f"/api/v1/ops/intake/{run_id}/reject",
            json={"reason": "duplicate submission"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected"

    def test_reject_unknown_id_returns_404(self, client):
        resp = client.post(
            f"/api/v1/ops/intake/{uuid.uuid4()}/reject",
            json={"reason": "no"},
        )
        assert resp.status_code == 404

    def test_reject_already_approved_returns_409(
        self, client, mini_wb_bytes, person_id
    ):
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={
                "file": (
                    "mini_estimator.xlsm",
                    mini_wb_bytes,
                    "application/vnd.ms-excel.sheet.macroEnabled.12",
                )
            },
        )
        run_id = up.json()["run_id"]
        client.post(
            f"/api/v1/ops/intake/{run_id}/approve",
            json={"approved_by": person_id},
        )
        resp = client.post(
            f"/api/v1/ops/intake/{run_id}/reject",
            json={"reason": "too late"},
        )
        assert resp.status_code == 409


class TestCodexAuditHardening:
    """Post-audit boundary hardening from the Codex review (content_type validation, unknown-actor
    4xx, generic value-free review-guard detail)."""

    _MIME = "application/vnd.ms-excel.sheet.macroEnabled.12"

    def test_invalid_content_type_returns_422(self, client, mini_wb_bytes, person_id):
        # finding 3: a content_type outside {xlsm,json} is a 422 at the boundary, never a DB CHECK 500.
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "application/octet-stream"},
            files={"file": ("x.bin", mini_wb_bytes, "application/octet-stream")},
        )
        assert resp.status_code == 422, resp.text

    def test_unknown_actor_returns_400_not_500(self, client, mini_wb_bytes):
        # finding 6: an uploaded_by UUID not in ops.persons is a clean 400, not an uncaught FK 500.
        import uuid
        resp = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": str(uuid.uuid4()), "content_type": "xlsm"},
            files={"file": ("mini.xlsm", mini_wb_bytes, self._MIME)},
        )
        assert resp.status_code == 400, resp.text

    def test_review_guard_rejection_is_generic_and_dollar_free(self, client, mini_wb_bytes, person_id):
        # finding 1: a review tamper that trips the allowlist returns a GENERIC 400 with NO dollar
        # value -- never the raw canonical=/review= leak.
        up = client.post(
            "/api/v1/ops/intake",
            data={"uploaded_by": person_id, "content_type": "xlsm"},
            files={"file": ("mini.xlsm", mini_wb_bytes, self._MIME)},
        )
        assert up.status_code == 200, up.text
        run = up.json()
        rp = run["review_payload"]
        rp["scopes"][0]["quote"]["onsite_labor"] = 999999  # tamper a pinned dollar field
        resp = client.post(
            f"/api/v1/ops/intake/{run['run_id']}/review",
            json={"review_payload": rp},
        )
        assert resp.status_code == 400, resp.text
        assert not _contains_substring(resp.json(), "999999")
        assert not _contains_substring(resp.json(), "$")


# ---------------------------------------------------------------------------
# Task 7 -- POST /api/v1/ops/intake/native
# ---------------------------------------------------------------------------


def _catalog_envelope():
    return {
        "schema_version": "estimate_envelope_v1", "source_kind": "native",
        "project_number": "API-1", "envelope_id": "api-env-1", "quote_version": 1,
        "source_draft_id": "d", "source_revision_id": "r",
        "totals": {"bid_cents": 165000, "service_hours": 0},
        "scopes": [{
            "scope_id": "S1", "name": "A1", "neta_standard": "ATS",
            "replication_m4": 1, "adjustment_multiplier_n4": 1,
            "scope_totals": {"onsite_labor_cents": 165000, "offsite_labor_cents": 0,
                             "cost_cents": 0, "service_cents": 0, "service_hours": 0,
                             "quoted_app_hours": 10, "adjusted_cents": 165000},
            "lines": [{"line_uid": "S1:r1", "line_kind": "catalog", "included": True,
                       "equipment_model_ref": "Capcitors - Per Unit", "base_qty": 1,
                       "project_intake_qty": 1, "resolved_ref_hours": 10.0}],
        }],
    }


class TestNativeIntake:
    """POST /api/v1/ops/intake/native"""

    def test_native_returns_200_pm_safe(self, client, person_id):
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": _catalog_envelope()})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source_format"] == "native" and body["status"] == "parsed"
        assert not _contains_substring(body, "$")               # finance redaction
        for f in body["findings"]:
            assert set(f) == {"code", "severity", "ok", "message"}   # no diagnostic_detail

    def test_native_non_catalog_rejected(self, client, person_id):
        env = _catalog_envelope(); env["scopes"][0]["lines"][0]["line_kind"] = "service"
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": env})
        assert resp.status_code == 200, resp.text          # a governed reject is 200 with status='rejected'
        assert resp.json()["status"] == "rejected"

    def test_native_malformed_numeric_is_governed_reject(self, client, person_id):
        """Hardening A: base_qty="abc" -> HTTP 200 status=rejected (never 500), findings have malformed_catalog_field."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "HARDEN-A-1"
        env["scopes"][0]["lines"][0]["base_qty"] = "abc"
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": env})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "malformed_catalog_field" in codes, f"Expected malformed_catalog_field in {codes}"
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")

    def test_native_missing_scope_name_is_governed_reject(self, client, person_id):
        """Hardening A: scope missing name -> HTTP 200 status=rejected (never 500)."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "HARDEN-A-2"
        env["envelope_id"] = "api-env-harden-a-2"
        del env["scopes"][0]["name"]
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": env})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "missing_scope_name" in codes, f"Expected missing_scope_name in {codes}"


# ---------------------------------------------------------------------------
# Hardening D1 route tests
# ---------------------------------------------------------------------------


class TestNativeIntakeD1:
    """D1 hardening: explicit-null and quote_version route-level tests."""

    def test_native_explicit_null_total_is_governed_reject(self, client, person_id):
        """adjustment_multiplier_n4=null (JSON null -> Python None) -> HTTP 200 status=rejected (NOT 500).
        The present-null path was crashing the pivot before D1."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "D1-ROUTE-NULL-TOTAL"
        env["envelope_id"] = "d1-route-env-1"
        env["scopes"][0]["adjustment_multiplier_n4"] = None  # explicit null
        resp = client.post(
            "/api/v1/ops/intake/native",
            json={"uploaded_by": person_id, "envelope": env},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "malformed_total" in codes, f"Expected malformed_total in {codes}"
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")

    def test_native_missing_quote_version_is_governed_reject(self, client, person_id):
        """quote_version=null -> HTTP 200 status=rejected (not 500 or 4xx)."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "D1-ROUTE-NO-QV"
        env["envelope_id"] = "d1-route-env-2"
        env["quote_version"] = None  # explicit null -> missing_quote_version
        resp = client.post(
            "/api/v1/ops/intake/native",
            json={"uploaded_by": person_id, "envelope": env},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "missing_quote_version" in codes, f"Expected missing_quote_version in {codes}"
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")

    def test_native_integer_valued_string_cents_is_accepted_not_500(self, client, person_id):
        """D1 FIX: bid_cents='100000.0' (integer-valued string) -> HTTP 200 status='parsed' (NOT 500, NOT rejected).
        The pivot must coerce via Decimal so int('100000.0') path is avoided."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "D1-ROUTE-INT-STR"
        env["envelope_id"] = "d1-route-env-int-str"
        env["quote_version"] = 2  # distinct quote_version to avoid collision
        env["totals"]["bid_cents"] = "100000.0"
        # scope_totals consistent at integer form
        env["scopes"][0]["scope_totals"]["onsite_labor_cents"] = "100000.0"
        env["scopes"][0]["scope_totals"]["adjusted_cents"] = 100000
        resp = client.post(
            "/api/v1/ops/intake/native",
            json={"uploaded_by": person_id, "envelope": env},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "parsed", (
            f"Expected status='parsed' for integer-valued string cents; got {body['status']}; findings={body.get('findings')}"
        )
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")


# ---------------------------------------------------------------------------
# Hardening D3 route tests
# ---------------------------------------------------------------------------


class TestNativeIntakeD3:
    """D3 hardening: schema/source contract + duplicate line_uid route-level tests."""

    def test_native_source_kind_workbook_intake_is_governed_reject(self, client, person_id):
        """source_kind='workbook_intake' -> HTTP 200 status='rejected' (not 500, not 422)."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "D3-ROUTE-SK"
        env["envelope_id"] = "d3-route-env-sk"
        env["source_kind"] = "workbook_intake"
        resp = client.post(
            "/api/v1/ops/intake/native",
            json={"uploaded_by": person_id, "envelope": env},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "invalid_source_kind" in codes, f"Expected invalid_source_kind in {codes}"
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")

    def test_native_duplicate_line_uid_is_governed_reject_not_500(self, client, person_id):
        """Duplicate line_uid -> HTTP 200 status='rejected' (not a DB 500 from uq_ops_apparatus_intake)."""
        import copy
        env = copy.deepcopy(_catalog_envelope())
        env["project_number"] = "D3-ROUTE-DUP-UID"
        env["envelope_id"] = "d3-route-env-dup-uid"
        # Add a second line with the same line_uid (duplicating "S1:r1")
        line2 = copy.deepcopy(env["scopes"][0]["lines"][0])
        env["scopes"][0]["lines"].append(line2)
        resp = client.post(
            "/api/v1/ops/intake/native",
            json={"uploaded_by": person_id, "envelope": env},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected", body
        codes = {f["code"] for f in body.get("findings", [])}
        assert "duplicate_line_uid" in codes, f"Expected duplicate_line_uid in {codes}"
        assert not _contains_substring(body, "$")
        assert not _contains_substring(body, "diagnostic_detail")
