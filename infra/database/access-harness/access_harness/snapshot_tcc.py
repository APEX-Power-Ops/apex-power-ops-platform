"""access_harness.snapshot_tcc -- cross-instance bridge for the governed tcc.* schema.

The Access Fidelity Harness writes to a LOCAL Postgres (access_raw, access_meta,
tcc_snapshot) on tcc_fidelity_*.  The governed tcc.* schema lives on a SEPARATE
host Postgres reachable only over the LarePass mesh:

    host   = 100.64.0.1
    port   = 5432
    db     = tcc_breaker_viewer_20260625
    role   = tcc_breaker_ro   (SELECT-only on tcc.*)

A Postgres EXCEPT / anti-join cannot cross two server instances.  So before the
local-to-local anti-join can run, this module pulls the tcc.* key-sets / counts
read-only over the mesh into a LOCAL tcc_snapshot.* schema.

Public API
----------
host_tcc_conn() -> psycopg.Connection
    Open a READ-ONLY psycopg connection to the host tcc Postgres.  Built from
    kwargs (NEVER a URI -- the password contains characters that break URL
    parsing).  The session is opened read-only (default_transaction_read_only=on
    via connect options) AND the role is SELECT-only, so writes are doubly
    refused.  Raises RuntimeError if TCC_BREAKER_RO_PW is unset.

snapshot_tcc(pg_conn, run_id, table_specs) -> str
    Pull the requested tcc.* tables read-only over the mesh and record one
    snapshot.  Returns the snapshot_id.

    table_specs maps tcc_table_name -> list[str] columns | None:
      * None        -> COUNT-ONLY.  Run SELECT count(*) on the host; record the
                       count.  Do NOT create a local table (used for large
                       computed/derived tables such as tmt_curves / tmt_thermal_adj
                       so we never pull 1.14M rows).
      * list[str]   -> Materialise that column subset from tcc.<table> on the
                       host into tcc_snapshot."<table>" locally, then record the
                       row count.

    Provenance: one access_meta.tcc_snapshot row + one
    access_meta.tcc_snapshot_table row per table.

All identifiers are quoted via psycopg.sql.Identifier.  The password is never
printed or logged.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import psycopg
from psycopg import sql

# ---------------------------------------------------------------------------
# Host connection constants (the governed tcc breaker viewer over the mesh).
# ---------------------------------------------------------------------------
HOST = "100.64.0.1"
PORT = 5432
USER = "tcc_breaker_ro"
DB_NAME = "tcc_breaker_viewer_20260625"
_PW_ENV = "TCC_BREAKER_RO_PW"


# ---------------------------------------------------------------------------
# host_tcc_conn
# ---------------------------------------------------------------------------

def host_tcc_conn() -> psycopg.Connection:
    """Open a read-only psycopg connection to the host tcc Postgres.

    Connection is built from kwargs (never a URI) because the password may
    contain characters (%, @, /, :) that break URL parsing.

    Read-only is enforced two ways (defense in depth):
      1. The role tcc_breaker_ro is SELECT-only on tcc.* (no INSERT/UPDATE).
      2. The SESSION is opened with default_transaction_read_only=on via
         connect `options`, which persists across every transaction (so even
         a CREATE TEMP TABLE is rejected with ReadOnlySqlTransaction).

    Returns
    -------
    psycopg.Connection -- autocommit, read-only.

    Raises
    ------
    RuntimeError -- if TCC_BREAKER_RO_PW is not set in the environment.
    """
    pw = os.environ.get(_PW_ENV)
    if not pw:
        raise RuntimeError(
            f"{_PW_ENV} is not set. Export the tcc_breaker_ro password "
            "(a Windows environment variable) before running the snapshot bridge."
        )

    return psycopg.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=pw,
        dbname=DB_NAME,
        sslmode="disable",
        connect_timeout=10,
        autocommit=True,
        # Session-level read-only: persists across all transactions, unlike a
        # standalone `SET` in autocommit mode (which only affects its own txn).
        options="-c default_transaction_read_only=on",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _host_count(host_conn, tcc_table: str) -> int:
    """SELECT count(*) FROM tcc.<table> on the host."""
    stmt = sql.SQL("SELECT count(*) FROM {schema}.{table}").format(
        schema=sql.Identifier("tcc"),
        table=sql.Identifier(tcc_table),
    )
    with host_conn.cursor() as cur:
        cur.execute(stmt)
        (n,) = cur.fetchone()
    return int(n)


def _materialise_table(
    host_conn,
    pg_conn,
    tcc_table: str,
    columns: list,
) -> int:
    """Copy a column subset of tcc.<table> from the host into tcc_snapshot.<table>.

    Uses server-side COPY (binary) host->client->local so 42k+ rows stream
    without being materialised as Python tuples in RAM, and types round-trip
    exactly.  Returns the number of rows copied.

    The local table is created with all-text columns is AVOIDED: instead the
    local table mirrors the host column types so binary COPY round-trips
    losslessly (a key-set snapshot must preserve the host's typed values for a
    later local-to-local anti-join).
    """
    schema_tcc = sql.Identifier("tcc")
    schema_snap = sql.Identifier("tcc_snapshot")
    table_id = sql.Identifier(tcc_table)
    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in columns)

    # --- 1. Read host column types for the requested subset, in order. ------
    type_stmt = sql.SQL(
        "SELECT column_name, data_type, udt_name "
        "FROM information_schema.columns "
        "WHERE table_schema = 'tcc' AND table_name = %s "
        "AND column_name = ANY(%s)"
    )
    with host_conn.cursor() as cur:
        cur.execute(type_stmt, (tcc_table, list(columns)))
        type_rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    missing = [c for c in columns if c not in type_rows]
    if missing:
        raise ValueError(
            f"tcc.{tcc_table} is missing requested column(s): {missing}"
        )

    # Build local column DDL preserving host types (fall back to udt_name when
    # data_type is 'USER-DEFINED' or 'ARRAY'; for the common scalar tcc cases
    # data_type is the canonical SQL name and is correct).
    col_defs = []
    for c in columns:
        data_type, udt_name = type_rows[c]
        if data_type in ("USER-DEFINED", "ARRAY"):
            pg_type = udt_name
        else:
            pg_type = data_type
        col_defs.append(
            sql.SQL("{col} {type}").format(
                col=sql.Identifier(c),
                type=sql.SQL(pg_type),
            )
        )

    drop_stmt = sql.SQL("DROP TABLE IF EXISTS {schema}.{table}").format(
        schema=schema_snap, table=table_id
    )
    create_stmt = sql.SQL("CREATE TABLE {schema}.{table} ({cols})").format(
        schema=schema_snap,
        table=table_id,
        cols=sql.SQL(", ").join(col_defs),
    )
    with pg_conn.cursor() as cur:
        cur.execute(drop_stmt)
        cur.execute(create_stmt)

    # --- 2. Stream rows host -> local via binary COPY. ----------------------
    copy_out = sql.SQL(
        "COPY (SELECT {cols} FROM {schema}.{table}) TO STDOUT (FORMAT binary)"
    ).format(cols=col_ids, schema=schema_tcc, table=table_id)
    copy_in = sql.SQL(
        "COPY {schema}.{table} ({cols}) FROM STDIN (FORMAT binary)"
    ).format(schema=schema_snap, table=table_id, cols=col_ids)

    with host_conn.cursor() as src, pg_conn.cursor() as dst:
        with src.copy(copy_out) as src_copy, dst.copy(copy_in) as dst_copy:
            for data in src_copy:
                dst_copy.write(data)

    # --- 3. Count what landed locally. --------------------------------------
    count_stmt = sql.SQL("SELECT count(*) FROM {schema}.{table}").format(
        schema=schema_snap, table=table_id
    )
    with pg_conn.cursor() as cur:
        cur.execute(count_stmt)
        (n,) = cur.fetchone()
    return int(n)


# ---------------------------------------------------------------------------
# snapshot_tcc
# ---------------------------------------------------------------------------

def snapshot_tcc(pg_conn, run_id: str, table_specs: dict) -> str:
    """Pull tcc.* key-sets / counts read-only into local tcc_snapshot.* + record.

    Parameters
    ----------
    pg_conn     : open LOCAL psycopg connection (tcc_fidelity_*).  The pg
                  fixture provides autocommit=True; this function works under
                  either commit mode (it commits explicitly at the end).
    run_id      : FK into access_meta.extraction_run.
    table_specs : dict tcc_table_name -> list[str] columns | None.
                  None means COUNT-ONLY (no local table created).

    Returns
    -------
    str -- the snapshot_id.
    """
    snapshot_id = f"{run_id}-tcc-{uuid.uuid4().hex[:8]}"
    captured_at = datetime.now(tz=timezone.utc)

    host_conn = host_tcc_conn()
    try:
        # Compute counts / materialise tables BEFORE writing provenance so a
        # host failure does not leave a dangling snapshot row.
        per_table_counts: dict = {}
        for tcc_table, columns in table_specs.items():
            if columns is None:
                per_table_counts[tcc_table] = _host_count(host_conn, tcc_table)
            else:
                per_table_counts[tcc_table] = _materialise_table(
                    host_conn, pg_conn, tcc_table, list(columns)
                )
    finally:
        host_conn.close()

    # --- Record provenance: one tcc_snapshot row + one row per table. -------
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tcc_snapshot
                (snapshot_id, run_id, host, db_name, captured_at, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (snapshot_id, run_id, HOST, DB_NAME, captured_at, USER),
        )
        for tcc_table, count in per_table_counts.items():
            cur.execute(
                """
                INSERT INTO access_meta.tcc_snapshot_table
                    (snapshot_id, table_name, tcc_row_count)
                VALUES (%s, %s, %s)
                """,
                (snapshot_id, tcc_table, count),
            )

        # Stamp this snapshot_id as the CURRENT owner of the materialised
        # tcc_snapshot layer (multi-run isolation guard, fixes 5+6).  Because
        # _materialise_table drops+recreates tcc_snapshot.<table> GLOBALLY
        # (latest-only), validate must fail closed when a stale snapshot_id is
        # asked to read it.
        cur.execute(
            """
            INSERT INTO access_meta.materialized_owner
                (layer, run_id, snapshot_id, updated_at)
            VALUES ('tcc_snapshot', %s, %s, %s)
            ON CONFLICT (layer) DO UPDATE SET
                run_id = EXCLUDED.run_id,
                snapshot_id = EXCLUDED.snapshot_id,
                updated_at = EXCLUDED.updated_at
            """,
            (run_id, snapshot_id, captured_at),
        )

    # Commit explicitly so the snapshot is durable even if pg_conn was opened
    # with autocommit=False.  (No-op when autocommit=True.)
    try:
        pg_conn.commit()
    except Exception:
        # Autocommit connections raise nothing meaningful here; ignore.
        pass

    return snapshot_id
