"""TDD - records Chip 2c FOLLOW-ON: Network Protector datasheet (NETA 7.8), v2 standard-aware.

The last genuine missing apparatus-family leaf. The Chip-2-shell (007) created the
`network_protectors` parent INACTIVE with no leaf. This migration (042):
  (a) INSERTs the `network_protector` leaf + activates the parent (post-foundation
      leaf-add, mirroring the surge 017 pattern),
  (b) links the leaf to the 7.8 procedure (primary),
  (c) INSERTs `ats_network_protector_v1` -- born v2 standard-aware (post-244): it covers
      BOTH ATS (29 items: 17 VM + 12 electrical) and MTS (27 items: 16 VM + 11 electrical)
      via per-standard `neta_covers` {ats,mts} maps on shared physical sections.

R-A: IR -> 100.1 (neta_table); connection/contact/control-IR/power-fuse/relay-pickup -> mfr;
CT-ratio xref 7.10 + master/phasing-relay calibration xref 7.9; NEVER tcc (a network protector
has no integral trip curve -- protection is the external network-protector relay, 7.9).

RED until gen_network_protector_template.py emits 042_network_protector_template.sql. Run PER-CHIP:
  RECORDS_DEV_PGPASSWORD=TCC_v5_2025 uv run --no-project --with "psycopg[binary]" --with pytest \
    pytest test_042_network_protector_template.py -q
"""
import json
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)
CODE = "ats_network_protector_v1"
LEAF = "network_protector"
PARENT = "network_protectors"
SEC = "7.8"
UP = "042_network_protector_template.sql"
DOWN = "042_network_protector_template_down.sql"


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


@pytest.fixture(scope="module")
def conn():
    _psql(DOWN)   # idempotent clean (safe before up)
    _psql(UP)
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn):
    row = conn.execute(
        "select neta_section, neta_standard, field_schema, "
        "(select class_code from records.asset_classes a where a.asset_class_id = t.asset_class_id) "
        "from records.form_templates t where template_code = %s and is_current", (CODE,)
    ).fetchone()
    assert row, f"{CODE} not found"
    sec, std, fs, leaf = row
    return sec, str(std), (json.loads(fs) if isinstance(fs, str) else fs), leaf


def _required(conn, std):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = %s and ti.standard = %s "
        "and ti.category in ('visual_mechanical','electrical')", (SEC, std)
    ).fetchall()
    return {f"{SEC}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}" for cat, num in rows}


def _covered(fs, std):
    cov = set()
    for s in fs["sections"]:
        nc = s.get("neta_covers") or {}
        if isinstance(nc, dict):
            cov |= set(nc.get(std, []))
    return cov


def test_leaf_created_and_parent_active(conn):
    row = conn.execute(
        "select a.is_active, p.class_code, p.is_active from records.asset_classes a "
        "join records.asset_classes p on a.parent_class_id = p.asset_class_id "
        "where a.class_code = %s", (LEAF,)
    ).fetchone()
    assert row, "leaf not created"
    leaf_active, parent_code, parent_active = row
    assert leaf_active is True, "leaf must be active"
    assert parent_code == PARENT, f"wrong parent: {parent_code}"
    assert parent_active is True, "parent network_protectors must be activated"


def test_acnp_link_primary(conn):
    row = conn.execute(
        "select acnp.is_primary from records.asset_class_neta_procedure acnp "
        "join records.asset_classes a using (asset_class_id) "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where a.class_code = %s and p.section = %s", (LEAF, SEC)
    ).fetchone()
    assert row, "no leaf -> 7.8 link"
    assert row[0] is True, "leaf -> 7.8 link must be primary"


def test_template_bound(conn):
    sec, std, _, leaf = _schema(conn)
    assert sec == SEC and leaf == LEAF and std == "ats", f"{sec}/{leaf}/{std}"


def test_standard_aware_v2(conn):
    _, _, fs, _ = _schema(conn)
    assert fs.get("neta_standards") == ["ats", "mts"], fs.get("neta_standards")
    # every section (incl. non-NETA: test_equipment/comments/attachments) carries a per-standard
    # neta_covers map -- matches the 040 herd convention (test_040 enforces this across all sheets).
    for s in fs["sections"]:
        assert isinstance(s.get("neta_covers"), dict), f"{s['key']}: neta_covers must be a map"


def test_per_standard_coverage_invariant(conn):
    _, _, fs, _ = _schema(conn)
    for std, n in (("ats", 29), ("mts", 27)):
        req = _required(conn, std)
        cov = _covered(fs, std)
        assert len(req) == n, f"{std} required={len(req)} != {n}"
        drops = req - cov
        phantom = {r for r in cov if r.startswith(SEC + ".")} - req
        assert not drops, f"{std} SILENT DROPS {sorted(drops)}"
        assert not phantom, f"{std} PHANTOM {sorted(phantom)}"


def test_ir_acceptance_is_neta_table(conn):
    _, _, fs, _ = _schema(conn)
    ir = next(s for s in fs["sections"] if s["key"] == "insulation_resistance")
    col = next(c for c in ir["table"]["columns"] if c["tag"] == "one_min_mohm")
    assert col.get("tolerance_source", {}).get("table") == "100.1"


def test_never_tcc(conn):
    _, _, fs, _ = _schema(conn)
    blob = json.dumps(fs).replace(" ", "")
    assert '"engine":"tcc"' not in blob, "network protector must never use the tcc engine"


def test_capture_modes(conn):
    _, _, fs, _ = _schema(conn)
    cap = fs.get("capture", {})
    assert cap.get("default") == "field" and "cover_attach" in cap.get("modes", [])


def test_ascii_only(conn):
    _, _, fs, _ = _schema(conn)
    assert json.dumps(fs, ensure_ascii=False).isascii(), "field_schema must be ASCII-only"


def test_reversibility(conn):
    _psql(DOWN)
    with psycopg.connect(DSN) as c:
        assert c.execute(
            "select 1 from records.form_templates where template_code=%s and is_current", (CODE,)
        ).fetchone() is None, "down must remove the template"
        assert c.execute(
            "select 1 from records.asset_classes where class_code=%s", (LEAF,)
        ).fetchone() is None, "down must remove the leaf"
        pa = c.execute(
            "select is_active from records.asset_classes where class_code=%s", (PARENT,)
        ).fetchone()
        assert pa and pa[0] is False, "down must restore parent inactive"
    _psql(DOWN)
    _psql(UP)
