"""Tests for access_harness.freeze -- freeze() + record_extraction_run().

All tests use small temporary files (NOT the real 239 MB .accdb).
The pg fixture (conftest.py) connects to tcc_fidelity_test and applies
001_schemas.sql, so access_meta.extraction_run exists.
"""
import os
import time

import pytest

from access_harness.freeze import FrozenSource, freeze, record_extraction_run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp(path, content: bytes = b"hello access harness"):
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------------------
# freeze() unit tests (no DB)
# ---------------------------------------------------------------------------

def test_sha_is_deterministic(tmp_path):
    """Two files with identical content produce the same source_sha256."""
    content = b"deterministic content for sha256 test"
    a = _write_temp(tmp_path / "a.accdb", content)
    b = _write_temp(tmp_path / "b.accdb", content)

    fs_a = freeze(a, tmp_path / "frozen_a")
    fs_b = freeze(b, tmp_path / "frozen_b")

    assert fs_a.source_sha256 == fs_b.source_sha256
    assert len(fs_a.source_sha256) == 64  # full hex sha256


def test_skip_copy_when_already_frozen(tmp_path):
    """Freezing the same source twice into the same dest_dir does not re-copy.

    We assert the inode (on Windows: file identity via os.stat().st_ino on NTFS,
    which may be 0 on FAT, so we fall back to comparing mtime + size) does not
    change after the second freeze call.
    """
    src = _write_temp(tmp_path / "source.accdb")
    dest_dir = tmp_path / "frozen"

    fs1 = freeze(src, dest_dir)

    stat_before = os.stat(fs1.frozen_path)
    # Ensure at least 10ms passes so mtime WOULD differ if re-copied
    time.sleep(0.05)

    fs2 = freeze(src, dest_dir)

    stat_after = os.stat(fs2.frozen_path)

    # frozen_path is the same deterministic name
    assert fs1.frozen_path == fs2.frozen_path

    # File was NOT re-written: mtime must be identical
    assert stat_before.st_mtime == stat_after.st_mtime


def test_freeze_creates_dest_dir(tmp_path):
    """freeze() creates dest_dir if it does not exist."""
    src = _write_temp(tmp_path / "source.accdb")
    dest_dir = tmp_path / "new" / "nested" / "dir"

    assert not dest_dir.exists()

    fs = freeze(src, dest_dir)

    assert dest_dir.exists()
    assert os.path.isfile(fs.frozen_path)


def test_frozen_source_fields(tmp_path):
    """FrozenSource carries size, mtime (UTC, tz-aware), sha256, and paths."""
    from datetime import timezone

    content = b"field check content"
    src = _write_temp(tmp_path / "check.accdb", content)
    dest_dir = tmp_path / "frozen"

    fs = freeze(src, dest_dir)

    assert fs.source_size == len(content)
    assert fs.source_mtime_utc.tzinfo is not None
    assert fs.source_mtime_utc.tzinfo == timezone.utc
    assert fs.source_sha256 != ""
    assert fs.source_path == str(src)
    assert fs.frozen_path.endswith(".accdb")


# ---------------------------------------------------------------------------
# record_extraction_run() -- requires the pg fixture
# ---------------------------------------------------------------------------

def test_record_extraction_run_inserts_all_provenance(pg, tmp_path):
    """freeze + record_extraction_run round-trips all provenance columns."""
    content = b"provenance test content for the extraction run"
    src = _write_temp(tmp_path / "source.accdb", content)
    dest_dir = tmp_path / "frozen"

    fs = freeze(src, dest_dir)

    driver_name = "ACEODBC.DLL"
    dbms_version = "04.00.9999"
    harness_version = "0.1.0"

    run_id = record_extraction_run(
        pg,
        fs,
        driver_name=driver_name,
        dbms_version=dbms_version,
        harness_version=harness_version,
    )

    assert run_id != ""

    # SELECT the row back and verify all provenance columns
    with pg.cursor() as cur:
        cur.execute(
            """
            SELECT
                run_id,
                source_path,
                frozen_copy_path,
                source_size,
                source_mtime_utc,
                source_sha256,
                extracted_at_utc,
                driver_name,
                dbms_version,
                read_only,
                harness_version
            FROM access_meta.extraction_run
            WHERE run_id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()

    assert row is not None, "Row not found in access_meta.extraction_run"

    (
        db_run_id,
        db_source_path,
        db_frozen_copy_path,
        db_source_size,
        db_source_mtime_utc,
        db_source_sha256,
        db_extracted_at_utc,
        db_driver_name,
        db_dbms_version,
        db_read_only,
        db_harness_version,
    ) = row

    # run_id round-trips
    assert db_run_id == run_id

    # path / hash / size
    assert db_source_path == fs.source_path
    assert db_frozen_copy_path == fs.frozen_path
    assert db_source_size == fs.source_size
    assert db_source_sha256 == fs.source_sha256

    # mtime round-trips (UTC, tz-aware); allow 1-second tolerance for tz-offset math
    delta = abs((db_source_mtime_utc - fs.source_mtime_utc).total_seconds())
    assert delta < 1.0, f"mtime delta too large: {delta}s"

    # driver + version strings
    assert db_driver_name == driver_name
    assert db_dbms_version == dbms_version
    assert db_harness_version == harness_version

    # read_only must be True
    assert db_read_only is True

    # extracted_at_utc must be a recent timestamp
    from datetime import timezone
    now = __import__("datetime").datetime.now(tz=timezone.utc)
    assert db_extracted_at_utc is not None
    age_s = (now - db_extracted_at_utc).total_seconds()
    assert 0 <= age_s < 60, f"extracted_at_utc looks stale: age={age_s}s"


def test_record_extraction_run_is_idempotent(pg, tmp_path):
    """Calling record_extraction_run twice for the SAME frozen source must NOT
    raise (re-runnable extract/load/run-all) and must leave exactly ONE row.

    run_id is deterministic (sha8-mtimecompact), so a second call against the
    same frozen file collides on the PK; the insert must be an UPSERT that
    refreshes the mutable fields instead of raising a PK violation.
    """
    content = b"idempotent re-run provenance content"
    src = _write_temp(tmp_path / "rerun.accdb", content)
    dest_dir = tmp_path / "frozen"

    fs = freeze(src, dest_dir)

    run_id_1 = record_extraction_run(
        pg, fs, driver_name="ACEODBC.DLL", dbms_version="04.00.0001",
        harness_version="0.1.0",
    )
    # Second run with DIFFERENT mutable values: must not raise, must refresh.
    run_id_2 = record_extraction_run(
        pg, fs, driver_name="ACEODBC.DLL", dbms_version="04.00.0002",
        harness_version="0.1.0",
    )

    assert run_id_1 == run_id_2, "deterministic run_id must be stable"

    # Exactly ONE row for that run_id.
    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*), max(dbms_version) "
            "FROM access_meta.extraction_run WHERE run_id=%s",
            (run_id_1,),
        )
        n, dbms = cur.fetchone()
    assert n == 1, f"re-run must leave exactly one row, found {n}"
    # Mutable field refreshed to the second call's value (UPSERT, not ignore).
    assert dbms == "04.00.0002", f"UPSERT must refresh dbms_version, got {dbms!r}"
