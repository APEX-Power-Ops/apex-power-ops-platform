import psycopg
from ops_intake.envelope import create_run_native   # NOTE: create_run_native is in envelope.py, NOT native.py
from ops_intake.approve import approve_run
from ops_intake.native import recompute_content_hash
from test_native_envelope import _catalog_env        # sibling tests module; if import fails, copy the small factory in

_MODEL_KEY = "Capcitors - Per Unit"  # resolvable mig-008 seed key on ops_test (matches test_approve_envelope.py)

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]

def test_native_metadata_lands_in_scope_quote_line(clean_ops):
    dsn = clean_ops
    who = _person(dsn)
    env = _catalog_env()
    line = env["scopes"][0]["lines"][0]
    line["equipment_model_ref"] = _MODEL_KEY
    line["designation"] = "CB-12"
    line["notes"] = "torque verified"
    line["description"] = "Medium-voltage breaker, primary injection"
    r = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert r["status"] == "parsed", r["findings"]
    res = approve_run(dsn, r["run_id"], approved_by=who)
    assert res["outcome"] == "approved", res
    with psycopg.connect(dsn) as c:
        row = c.execute(
            "select designation, notes, description from ops.scope_quote_line "
            "where source='ops-intake' and legacy_source_id=%s",
            (line["line_uid"],),
        ).fetchone()
    assert row == ("CB-12", "torque verified", "Medium-voltage breaker, primary injection")


def test_recompute_content_hash_is_metadata_neutral():
    """Two envelopes identical in economics but differing only in free-text metadata
    (designation / notes / description) must yield the SAME server content hash.
    Economic-neutral invariant: designation/notes/description are excluded from the hash."""
    env_a = _catalog_env()
    env_b = _catalog_env()
    # Set metadata on env_a's line
    env_a["scopes"][0]["lines"][0]["designation"] = "CB-12"
    env_a["scopes"][0]["lines"][0]["notes"] = "torque verified"
    env_a["scopes"][0]["lines"][0]["description"] = "Medium-voltage breaker, primary injection"
    # Different metadata on env_b's line — economics are identical
    env_b["scopes"][0]["lines"][0]["designation"] = "CB-99"
    env_b["scopes"][0]["lines"][0]["notes"] = "different notes"
    env_b["scopes"][0]["lines"][0]["description"] = "A completely different description"
    assert recompute_content_hash(env_a) == recompute_content_hash(env_b), (
        "recompute_content_hash must be metadata-neutral: "
        "designation/notes/description must not affect the hash"
    )
