"""access_harness.cli -- the Access Fidelity Harness command-line entry point.

Wires the harness modules (freeze / extract / load / inventory / snapshot_tcc /
validate / golden) into argparse subcommands and the `run-all` pipeline that
runs the breaker/TMT slice END-TO-END:

    freeze -> extract(record run) -> load(slice) -> inventory(all 79) ->
    snapshot-tcc(TMT + style tables) -> validate(reconcile + anti-joins +
    style-resolution) -> [golden-capture optional]

producing the F-79-03 STRUCTURAL evidence with ZERO behavioral interpretation
(HR1).  The CLI takes connections/paths from the environment:

  ACCESS_HARNESS_SUPERUSER_DSN  -- local Postgres superuser DSN (target db is in
                                   the DSN; run-all defaults to that db).
  TCC_BREAKER_RO_PW             -- host tcc SELECT-only password (mesh).
  ACCESS_HARNESS_FROZEN_DIR     -- dir for frozen .accdb copies (default D:\\_access_frozen).
  --accdb / ACCESS_HARNESS_ACCDB-- the source .accdb path (default D:\\TCC_NEW.accdb).

Build/run on WINDOWS (the ACE / pyodbc Access path is Windows-only).

IMPORTANT: the host tcc connection is built from psycopg KWARGS, never a URI
(snapshot_tcc.host_tcc_conn already does this -- the password has URL-breaking
characters).  This module never prints or logs any password.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

from access_harness import config
from access_harness import extract, freeze as freeze_mod, inventory, load, validate
from access_harness.config import frozen_dir
from access_harness.projection import ProjectionMap
from access_harness.snapshot_tcc import snapshot_tcc

# ---------------------------------------------------------------------------
# Slice definition -- the breaker/TMT tables data-loaded into access_raw.
# ---------------------------------------------------------------------------
DEFAULT_ACCDB = r"D:\TCC_NEW.accdb"

# 5 TMT frame/child tables (have ProjectionMap entries) + 3 style tables.
SLICE_TMT_TABLES = [
    "Breaker_TMTFrameSizes",
    "Breaker_TMTFrameAmps",
    "Breaker_TMTFrameSettings",
    "Breaker_TMTFrameCurves",
    "Breaker_TMTThermalTripAdj",
]
SLICE_STYLE_TABLES = [
    "BreakerMCCBStyles",
    "BreakerICCBStyles",
    "BreakerPCBStyles",
]
SLICE_TABLES = SLICE_TMT_TABLES + SLICE_STYLE_TABLES

# Curves is ~1.14M rows.  Loading it into access_raw is NOT required to produce
# the F-79-03 evidence (the count-only path produces the curves count delta).
# By default the slice SKIPS the curves DATA-load; --with-curves re-enables it.
CURVES_TABLE = "Breaker_TMTFrameCurves"

# tcc snapshot spec: key columns to materialise locally, None == COUNT-ONLY.
TCC_SNAPSHOT_SPEC = {
    "tmt_frames": ["id", "breaker_style_id", "breaker_class", "size"],
    "tmt_amps": ["frame_id", "rating"],
    "tmt_settings": ["frame_id", "value"],
    "tmt_curves": None,        # count-only -- never pull 1.14M rows
    "tmt_thermal_adj": None,   # count-only
    "brk_mccb_styles": ["id", "source_id", "breaker_id"],
    "brk_iccb_styles": ["id", "source_id", "breaker_id"],
    "brk_pcb_styles": ["id", "source_id", "breaker_id"],
}

BREAKER_CLASSES = ["MCCB", "ICCB", "PCB"]


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def _pg_dsn_from_env() -> str:
    # Obtain the local DSN via config.pg_dsn(), which strips a SQLAlchemy-style
    # driver prefix (postgresql+psycopg:// / +asyncpg://) that psycopg.connect
    # does NOT understand.  Routing through config keeps the CLI's connection
    # path byte-identical to the tests' (config.pg_dsn()/test_pg_dsn()), so a
    # +driver DSN no longer breaks every CLI subcommand.
    return config.pg_dsn()


def _pg_dsn_for(args) -> str:
    """Return the governed DSN when --governed is set, else the base DSN.

    Both go through config so the SQLAlchemy-style +driver prefix is stripped
    identically to the tests' connection path.
    """
    if getattr(args, "governed", False):
        return config.governed_pg_dsn()
    return config.pg_dsn()


def _fence_governed(conn, args) -> None:
    """Fail closed: when --governed is set, assert conn is on tcc_fidelity_governed.

    Called immediately after each connection is opened and BEFORE any load /
    schema action, so a governed command can never write into postgres / _test /
    any other DB. No-op when --governed is not set.
    """
    if getattr(args, "governed", False):
        config.assert_current_database(conn, config.GOVERNED_DB)


def _connect_pg(dsn: str, *, autocommit: bool) -> psycopg.Connection:
    return psycopg.connect(dsn, autocommit=autocommit)


def _accdb_path(args) -> str:
    return (
        getattr(args, "accdb", None)
        or os.environ.get("ACCESS_HARNESS_ACCDB")
        or DEFAULT_ACCDB
    )


# ---------------------------------------------------------------------------
# Driver-capability preflight
# ---------------------------------------------------------------------------

def driver_preflight(accdb_path: str) -> tuple:
    """Assert the metadata path returns rows on the (frozen) file.

    Opens a read-only ODBC + ACE connection, lists the user tables, and probes
    column_meta on the first slice table that exists.  Returns
    (driver_name, dbms_version, table_count).  Raises RuntimeError if the
    metadata path yields nothing -- so we never trust a file the driver cannot
    actually read.
    """
    data_conn = extract.connect_data(accdb_path)
    ace_conn = extract.connect_ace(accdb_path)
    try:
        tables = extract.list_user_tables(ace_conn)
        if not tables:
            raise RuntimeError(
                f"Driver preflight FAILED: no user tables returned from {accdb_path}"
            )
        # Probe column metadata on a known slice table.
        probe = next((t for t in SLICE_TABLES if t in tables), tables[0])
        cols = extract.column_meta(data_conn, probe)
        if not cols:
            raise RuntimeError(
                f"Driver preflight FAILED: column_meta returned no columns for "
                f"{probe!r} in {accdb_path}"
            )
        driver_name, dbms_version = extract.driver_info(data_conn)
        return driver_name, dbms_version, len(tables)
    finally:
        try:
            ace_conn.Close()
        except Exception:
            pass
        data_conn.close()


# ---------------------------------------------------------------------------
# Subcommand: freeze
# ---------------------------------------------------------------------------

def cmd_freeze(args) -> int:
    accdb = _accdb_path(args)
    dest = Path(args.frozen_dir) if args.frozen_dir else frozen_dir()
    fs = freeze_mod.freeze(accdb, dest)
    print(f"frozen: {fs.frozen_path}")
    print(f"sha256: {fs.source_sha256}")
    print(f"size:   {fs.source_size}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: extract (records the extraction_run against the frozen file)
# ---------------------------------------------------------------------------

def cmd_extract(args) -> int:
    accdb = _accdb_path(args)
    dest = Path(args.frozen_dir) if args.frozen_dir else frozen_dir()
    fs = freeze_mod.freeze(accdb, dest)

    driver_name, dbms_version, n_tables = driver_preflight(fs.frozen_path)

    dsn = _pg_dsn_from_env()
    pg = _connect_pg(dsn, autocommit=True)
    try:
        run_id = freeze_mod.record_extraction_run(
            pg, fs, driver_name, dbms_version
        )
    finally:
        pg.close()
    print(f"run_id: {run_id}")
    print(f"driver: {driver_name} ({dbms_version}); tables seen: {n_tables}")
    return 0


# ---------------------------------------------------------------------------
# Shared slice runner used by `load`, `inventory`, and `run-all`.
# ---------------------------------------------------------------------------

def _frozen_for(args) -> "freeze_mod.FrozenSource":
    accdb = _accdb_path(args)
    dest = Path(args.frozen_dir) if args.frozen_dir else frozen_dir()
    return freeze_mod.freeze(accdb, dest)


def _load_slice(pg_conn, data_conn, run_id: str, *, with_curves: bool) -> tuple:
    """Data-load the breaker/TMT slice into access_raw.

    Returns (loaded_table_set, col_types_by_table) so the caller can checksum the
    loaded tables with the SAME col_types used to load them.
    """
    loaded = set()
    col_types_by_table = {}
    for table in SLICE_TABLES:
        if table == CURVES_TABLE and not with_curves:
            # Skip the 1.14M-row curves DATA load; the count-only path produces
            # the curves evidence (documented decision).
            continue
        col_types = extract.column_meta(data_conn, table)
        rows = extract.read_rows(data_conn, table)
        count = load.load_table(pg_conn, table, col_types, rows, run_id)
        loaded.add(table)
        col_types_by_table[table] = col_types
        print(f"loaded access_raw.{table}: {count} rows")
    return loaded, col_types_by_table


# ---------------------------------------------------------------------------
# Subcommand: load
# ---------------------------------------------------------------------------

def cmd_load(args) -> int:
    fs = _frozen_for(args)
    driver_name, dbms_version, _ = driver_preflight(fs.frozen_path)
    dsn = _pg_dsn_for(args)

    pg_auto = _connect_pg(dsn, autocommit=True)
    try:
        _fence_governed(pg_auto, args)   # fail closed before ANY work
        run_id = freeze_mod.record_extraction_run(
            pg_auto, fs, driver_name, dbms_version
        )
        data_conn = extract.connect_data(fs.frozen_path)
        pg_tx = _connect_pg(dsn, autocommit=False)
        try:
            _fence_governed(pg_tx, args)
            loaded, col_types_by_table = _load_slice(
                pg_tx, data_conn, run_id, with_curves=args.with_curves
            )
            validate.reconcile_checksums(
                pg_auto, run_id, sorted(loaded), col_types_by_table,
                access_rows_for=lambda t: extract.read_rows(data_conn, t),
            )
        finally:
            pg_tx.close()
            data_conn.close()
        validate.assert_style_parents_faithful(pg_auto, run_id)
    finally:
        pg_auto.close()
    print(f"run_id: {run_id}; loaded {len(loaded)} slice tables")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: inventory (ALL 79 tables; data-load only the slice)
# ---------------------------------------------------------------------------

def cmd_inventory(args) -> int:
    fs = _frozen_for(args)
    driver_name, dbms_version, _ = driver_preflight(fs.frozen_path)
    dsn = _pg_dsn_for(args)

    pg_auto = _connect_pg(dsn, autocommit=True)
    pg_tx = _connect_pg(dsn, autocommit=False)
    try:
        _fence_governed(pg_auto, args)   # fail closed before ANY work
        _fence_governed(pg_tx, args)
        run_id = freeze_mod.record_extraction_run(
            pg_auto, fs, driver_name, dbms_version
        )
        data_conn = extract.connect_data(fs.frozen_path)
        ace_conn = extract.connect_ace(fs.frozen_path)
        try:
            loaded, col_types_by_table = _load_slice(
                pg_tx, data_conn, run_id, with_curves=args.with_curves
            )
            all_tables = extract.list_user_tables(ace_conn)
            count_only = set() if args.with_curves else {CURVES_TABLE}
            inventory.populate_meta(
                pg_auto, data_conn, ace_conn, run_id, all_tables, loaded,
                count_only_tables=count_only,
            )
            validate.reconcile_checksums(
                pg_auto, run_id, sorted(loaded), col_types_by_table,
                access_rows_for=lambda t: extract.read_rows(data_conn, t),
            )
            print(f"inventoried {len(all_tables)} tables; loaded {len(loaded)}")
        finally:
            pg_tx.close()
            try:
                ace_conn.Close()
            except Exception:
                pass
            data_conn.close()
        validate.assert_style_parents_faithful(pg_auto, run_id)
    finally:
        pg_auto.close()
    print(f"run_id: {run_id}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: snapshot-tcc
# ---------------------------------------------------------------------------

def cmd_snapshot_tcc(args) -> int:
    if not args.run_id:
        raise RuntimeError("snapshot-tcc requires --run-id")
    dsn = _pg_dsn_from_env()
    pg = _connect_pg(dsn, autocommit=True)
    try:
        sid = snapshot_tcc(pg, args.run_id, TCC_SNAPSHOT_SPEC)
    finally:
        pg.close()
    print(f"snapshot_id: {sid}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: validate
# ---------------------------------------------------------------------------

def _run_validation(pg_conn, run_id: str, snapshot_id: str) -> None:
    """Run the full F-79-03 validation suite (reconcile + anti-joins + style)."""
    # (1) access-vs-staging load reconciliation (existing) + (1') access-vs-tcc.
    validate.reconcile_counts(pg_conn, run_id)
    validate.reconcile_vs_tcc(pg_conn, run_id, snapshot_id)

    # (2/3) per-table anti-join vs tcc.
    #   * computed/derived (curves, thermal_adj) -> COUNT-ONLY (no 1.14M EXCEPT).
    #   * amps (1:1 load) -> anti-join on the NATURAL-attribute key TripAmp
    #     (Access) -> rating (tcc), with numeric_keys=True so the Access float
    #     and the tcc numeric compare symmetrically (brief item 2).  This is a
    #     frame-FREE rating-value key: the row-level frame-resolved amps key is
    #     DEFERRED (the tcc tmt_frames.id is re-sequenced and `size` is computed,
    #     so the frame correspondence cannot be honestly built -- see report).
    # NOTE: the surrogate FrameSizeID is NEVER used as a key here -- routing it
    # to tmt_frames.id would (correctly) raise ForbiddenKeyError.
    validate.antijoin_vs_tcc(
        pg_conn, run_id, snapshot_id, "Breaker_TMTFrameAmps", ["TripAmp"],
        numeric_keys=True,
    )
    # Curves / thermal_adj: count-only (the key arg is unused on that branch, but
    # a natural-attribute placeholder is passed so no surrogate guard trips).
    validate.antijoin_vs_tcc(
        pg_conn, run_id, snapshot_id, "Breaker_TMTFrameCurves", ["Class"],
    )
    validate.antijoin_vs_tcc(
        pg_conn, run_id, snapshot_id, "Breaker_TMTThermalTripAdj", ["Setting"],
    )

    # (4) style-mediated frame resolution: record the ambiguity as counts.
    validate.resolve_style_classes(pg_conn, run_id)

    # (4') the cleanly-keyable style-provenance anti-join (one row per class).
    for bc in BREAKER_CLASSES:
        validate.style_provenance_antijoin(pg_conn, run_id, bc)


def cmd_validate(args) -> int:
    if not args.run_id or not args.snapshot_id:
        raise RuntimeError("validate requires --run-id and --snapshot-id")
    dsn = _pg_dsn_from_env()
    pg = _connect_pg(dsn, autocommit=True)
    try:
        _run_validation(pg, args.run_id, args.snapshot_id)
    finally:
        pg.close()
    print(f"validated run_id={args.run_id} snapshot_id={args.snapshot_id}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: golden-capture (Phase-1 capture only; fail-closed)
# ---------------------------------------------------------------------------

def cmd_golden_capture(args) -> int:
    # Phase 1 only CAPTURES; the diff is deferred to Phase 2.  The fail-closed
    # multi-factor gate (access_harness.golden) is the load-bearing safety, and
    # is exercised by tests/test_golden.py.  Here we simply note that no goldens
    # are auto-captured unless an allow-list is provided (opt-in).
    print(
        "golden-capture: no goldens captured (opt-in; provide an explicit "
        "allow-list per access_harness.golden -- Phase-1 capture is fail-closed)."
    )
    return 0


# ---------------------------------------------------------------------------
# Subcommand: provision-governed
# ---------------------------------------------------------------------------

def cmd_provision_governed(args) -> int:
    """Create tcc_fidelity_governed if absent and apply the harness DDL to it.

    Operator-run only (never the test suite). Connects to the BASE db to create
    the governed db, then connects to the governed db, FENCES, and applies the
    idempotent schema DDL (CREATE SCHEMA/TABLE IF NOT EXISTS).
    """
    base_dsn = config.pg_dsn()
    admin = _connect_pg(base_dsn, autocommit=True)
    try:
        created = config.ensure_database(admin, config.GOVERNED_DB)
    finally:
        admin.close()
    print(f"governed db {config.GOVERNED_DB}: "
          f"{'created' if created else 'already present'}")

    gov = _connect_pg(config.governed_pg_dsn(), autocommit=True)
    try:
        config.assert_current_database(gov, config.GOVERNED_DB)  # fail closed
        schema_sql = Path(__file__).parent.parent / "sql" / "001_schemas.sql"
        config.apply_sql(gov, schema_sql)
    finally:
        gov.close()
    print(f"applied 001_schemas.sql to {config.GOVERNED_DB}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: run-all (the full slice pipeline)
# ---------------------------------------------------------------------------

def run_all(
    pg_auto: psycopg.Connection,
    pg_tx: psycopg.Connection,
    accdb_path: str,
    frozen_dest: Path,
    *,
    with_curves: bool = False,
) -> dict:
    """Run the breaker/TMT slice end to end and return the run identifiers.

    Steps: freeze -> preflight -> record run -> load slice -> inventory all ->
    snapshot tcc -> validate.  Connections are supplied by the caller so the
    acceptance test can target tcc_fidelity_test explicitly.

    pg_auto : autocommit psycopg connection (record-run, inventory, snapshot,
              validate).
    pg_tx   : NON-autocommit psycopg connection (load_table transactions).

    Returns {'run_id', 'snapshot_id', 'loaded', 'all_tables'}.
    """
    fs = freeze_mod.freeze(accdb_path, frozen_dest)
    driver_name, dbms_version, _ = driver_preflight(fs.frozen_path)
    run_id = freeze_mod.record_extraction_run(
        pg_auto, fs, driver_name, dbms_version
    )

    data_conn = extract.connect_data(fs.frozen_path)
    ace_conn = extract.connect_ace(fs.frozen_path)
    try:
        loaded, col_types_by_table = _load_slice(
            pg_tx, data_conn, run_id, with_curves=with_curves
        )
        all_tables = extract.list_user_tables(ace_conn)
        count_only = set() if with_curves else {CURVES_TABLE}
        inventory.populate_meta(
            pg_auto, data_conn, ace_conn, run_id, all_tables, loaded,
            count_only_tables=count_only,
        )
        # Per-table checksum + access-vs-staging reconciliation (after inventory,
        # which re-inserts load_state='loaded'; this upgrades it to 'checksummed').
        validate.reconcile_checksums(
            pg_auto, run_id, sorted(loaded), col_types_by_table,
            access_rows_for=lambda t: extract.read_rows(data_conn, t),
        )
    finally:
        try:
            ace_conn.Close()
        except Exception:
            pass
        data_conn.close()

    snapshot_id = snapshot_tcc(pg_auto, run_id, TCC_SNAPSHOT_SPEC)
    _run_validation(pg_auto, run_id, snapshot_id)
    validate.assert_style_parents_faithful(pg_auto, run_id)

    return {
        "run_id": run_id,
        "snapshot_id": snapshot_id,
        "loaded": sorted(loaded),
        "all_tables": all_tables,
    }


def cmd_run_all(args) -> int:
    accdb = _accdb_path(args)
    dest = Path(args.frozen_dir) if args.frozen_dir else frozen_dir()
    dsn = _pg_dsn_for(args)
    pg_auto = _connect_pg(dsn, autocommit=True)
    pg_tx = _connect_pg(dsn, autocommit=False)
    try:
        _fence_governed(pg_auto, args)   # fail closed before ANY work
        _fence_governed(pg_tx, args)
        result = run_all(
            pg_auto, pg_tx, accdb, dest, with_curves=args.with_curves
        )
    finally:
        pg_tx.close()
        pg_auto.close()
    print(f"run_id:     {result['run_id']}")
    print(f"snapshot_id:{result['snapshot_id']}")
    print(f"loaded:     {len(result['loaded'])} tables")
    print(f"inventoried:{len(result['all_tables'])} tables")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="access-harness",
        description="Access Fidelity Harness -- mirror MS Access into Postgres "
                    "and produce structural fidelity evidence (HR1: no "
                    "behavioral interpretation).",
    )
    p.add_argument("--accdb", default=None, help="source .accdb path")
    p.add_argument("--frozen-dir", default=None, help="frozen-copy directory")
    p.add_argument(
        "--with-curves",
        action="store_true",
        help="also DATA-load the 1.14M-row curves table (default: count-only)",
    )
    p.add_argument(
        "--governed",
        action="store_true",
        help="target the durable governed DB (tcc_fidelity_governed) and FENCE "
             "every connection to it (fail closed); off = the base DSN's db",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("freeze", help="freeze the .accdb (content-addressed copy)").set_defaults(func=cmd_freeze)
    sub.add_parser("extract", help="freeze + preflight + record extraction_run").set_defaults(func=cmd_extract)
    sub.add_parser("load", help="data-load the breaker/TMT slice into access_raw").set_defaults(func=cmd_load)
    sub.add_parser("inventory", help="inventory ALL tables; data-load only the slice").set_defaults(func=cmd_inventory)

    sp = sub.add_parser("snapshot-tcc", help="pull TMT + style tables into tcc_snapshot")
    sp.add_argument("--run-id", required=True)
    sp.set_defaults(func=cmd_snapshot_tcc)

    vp = sub.add_parser("validate", help="reconcile + anti-join + style-resolution")
    vp.add_argument("--run-id", required=True)
    vp.add_argument("--snapshot-id", required=True)
    vp.set_defaults(func=cmd_validate)

    sub.add_parser("golden-capture", help="Phase-1 golden capture (fail-closed, opt-in)").set_defaults(func=cmd_golden_capture)
    sub.add_parser(
        "provision-governed",
        help="create tcc_fidelity_governed (if absent) + apply harness DDL",
    ).set_defaults(func=cmd_provision_governed)
    sub.add_parser("run-all", help="the full breaker/TMT slice pipeline").set_defaults(func=cmd_run_all)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
