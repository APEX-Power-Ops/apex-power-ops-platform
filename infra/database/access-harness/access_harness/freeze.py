"""access_harness.freeze -- freeze an Access source file + record the extraction run.

FrozenSource captures the provenance of a source .accdb file at the moment it was
copied so downstream tasks always work against a stable, content-addressed snapshot.

freeze() contract:
  * Streams the source file through hashlib.sha256 (never slurps 239 MB into RAM).
  * Derives a deterministic frozen filename:
      <stem>_<mtimecompact>_<sha8>.accdb
    where <mtimecompact> = mtime formatted %Y%m%dT%H%M%S (UTC)
          <sha8>         = first 8 hex chars of the sha256 digest
  * Creates dest_dir if it does not exist.
  * SKIPS the copy (idempotent) if the destination file already exists.
  * Uses shutil.copy2 so file metadata is preserved.

record_extraction_run() contract:
  * Inserts one row into access_meta.extraction_run.
  * run_id is deterministic: f"{sha8}-{mtimecompact}" -- unique per frozen source.
  * Sets read_only=True, extracted_at_utc=now(UTC).
  * Returns run_id.
"""
import hashlib
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class FrozenSource:
    """Provenance record for a frozen (content-addressed) copy of a source file."""

    source_path: str
    frozen_path: str
    source_sha256: str
    source_size: int
    source_mtime_utc: datetime  # tz-aware UTC


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sha256_and_size(path: Path) -> tuple:
    """Stream-hash a file; return (hex_digest, byte_count)."""
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):  # 1 MiB chunks
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _mtime_utc(path: Path) -> datetime:
    """Return the file mtime as a tz-aware UTC datetime."""
    mtime_ts = path.stat().st_mtime
    return datetime.fromtimestamp(mtime_ts, tz=timezone.utc)


def _compact(dt: datetime) -> str:
    """Format a datetime as a compact UTC string, e.g. '20260626T153045'."""
    return dt.strftime("%Y%m%dT%H%M%S")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def freeze(source, dest_dir) -> FrozenSource:
    """Copy *source* into *dest_dir* as a content-addressed frozen snapshot.

    Parameters
    ----------
    source   : str or Path -- the .accdb / .mdb source file to freeze.
    dest_dir : str or Path -- directory to write the frozen copy into.

    Returns
    -------
    FrozenSource -- provenance record (frozen_path may point to a pre-existing
                    copy if the same content was already frozen).
    """
    src = Path(source)
    dest = Path(dest_dir)

    sha256, size = _sha256_and_size(src)
    mtime = _mtime_utc(src)
    sha8 = sha256[:8]
    compact = _compact(mtime)

    frozen_name = f"{src.stem}_{compact}_{sha8}{src.suffix}"
    dest_path = dest / frozen_name

    dest.mkdir(parents=True, exist_ok=True)

    if not dest_path.exists():
        shutil.copy2(str(src), str(dest_path))

    return FrozenSource(
        source_path=str(src),
        frozen_path=str(dest_path),
        source_sha256=sha256,
        source_size=size,
        source_mtime_utc=mtime,
    )


def record_extraction_run(
    conn,
    frozen: FrozenSource,
    driver_name: str,
    dbms_version: str,
    harness_version: str = "0.1.0",
) -> str:
    """Insert one row into access_meta.extraction_run and return run_id.

    run_id is deterministic: f"{sha8}-{mtimecompact}", so re-running the same
    frozen source returns a predictable ID.  Callers that need strict uniqueness
    per calendar-run should append a uuid4 fragment; for this harness the
    deterministic form is acceptable because each distinct frozen file has a
    unique (sha8, mtime) pair.

    Parameters
    ----------
    conn            : open psycopg connection (autocommit=True).
    frozen          : FrozenSource returned by freeze().
    driver_name     : ODBC driver name string (from driver_info(conn)[0]).
    dbms_version    : DBMS version string (from driver_info(conn)[1]).
    harness_version : harness release tag; defaults to '0.1.0'.

    Returns
    -------
    str -- the run_id inserted.
    """
    sha8 = frozen.source_sha256[:8]
    compact = _compact(frozen.source_mtime_utc)
    run_id = f"{sha8}-{compact}"

    now_utc = datetime.now(tz=timezone.utc)

    sql = """
        INSERT INTO access_meta.extraction_run (
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
        ) VALUES (
            %(run_id)s,
            %(source_path)s,
            %(frozen_copy_path)s,
            %(source_size)s,
            %(source_mtime_utc)s,
            %(source_sha256)s,
            %(extracted_at_utc)s,
            %(driver_name)s,
            %(dbms_version)s,
            %(read_only)s,
            %(harness_version)s
        )
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "run_id": run_id,
                "source_path": frozen.source_path,
                "frozen_copy_path": frozen.frozen_path,
                "source_size": frozen.source_size,
                "source_mtime_utc": frozen.source_mtime_utc,
                "source_sha256": frozen.source_sha256,
                "extracted_at_utc": now_utc,
                "driver_name": driver_name,
                "dbms_version": dbms_version,
                "read_only": True,
                "harness_version": harness_version,
            },
        )

    return run_id
