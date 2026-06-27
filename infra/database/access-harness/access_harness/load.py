"""access_harness.load -- load Access data rows into access_raw staging tables.

Public API
----------
create_access_raw_table(conn, table, col_types)
    Drop-and-recreate access_raw."<table>" with typed columns.
    Identifiers are ALWAYS quoted via psycopg.sql.Identifier (never f-string).

single_writer(conn)
    Context manager: takes pg_advisory_xact_lock(ADVISORY_LOCK_KEY) so that
    only one harness process may load concurrently.  The lock is released when
    the transaction ends.  A second concurrent pg_try_advisory_xact_lock returns
    False while the first holder's transaction is open.

load_table(conn, table, col_types, rows, run_id, continue_on_error=False)
    In ONE transaction:
      1. Upsert access_meta.tables row with load_state='extracting'.
      2. Drop-and-recreate access_raw."<table>" (via create_access_raw_table).
      3. TRUNCATE access_raw."<table>".
      4. Bulk-insert all rows via cursor.executemany.
      5. Update access_meta.tables: load_state='loaded', staging_row_count=count.
      6. COMMIT and return count.
    On ANY error: roll back, then record load_state='failed' in a separate
    committed statement.  Re-raises by default; swallows when
    continue_on_error=True.

IMPORTANT: conn must be opened with autocommit=False (the default for psycopg
connections created without autocommit=True).  load_table manages commits
explicitly via conn.commit() / conn.rollback().
"""
from __future__ import annotations

import contextlib
from typing import Iterable

import psycopg
from psycopg import sql

from access_harness.typemap import ColumnType, pg_ddl_type

# ---------------------------------------------------------------------------
# Advisory lock key -- fixed constant; identifies the access-harness loader.
# Chosen to be memorable and unlikely to collide with application locks.
# ---------------------------------------------------------------------------
ADVISORY_LOCK_KEY: int = 0x41505843484152  # "APXCHAR" in ASCII hex


# ---------------------------------------------------------------------------
# Materialised-owner stamping (multi-run isolation guard, fixes 5+6)
# ---------------------------------------------------------------------------

def _stamp_access_raw_owner(conn, run_id: str) -> None:
    """Record run_id as the current owner of the materialised access_raw layer.

    Upserts the single access_meta.materialized_owner row for layer='access_raw'
    so validate can fail closed when a SUPERSEDED run_id is asked to anti-join
    against the (latest-only) access_raw.* tables.  Stamped inside the caller's
    load transaction so ownership is atomic with the load.
    """
    from datetime import datetime, timezone

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.materialized_owner
                (layer, run_id, snapshot_id, updated_at)
            VALUES ('access_raw', %s, NULL, %s)
            ON CONFLICT (layer) DO UPDATE SET
                run_id = EXCLUDED.run_id,
                snapshot_id = EXCLUDED.snapshot_id,
                updated_at = EXCLUDED.updated_at
            """,
            (run_id, datetime.now(tz=timezone.utc)),
        )


# ---------------------------------------------------------------------------
# create_access_raw_table
# ---------------------------------------------------------------------------

def create_access_raw_table(
    conn,
    table: str,
    col_types: list,
) -> None:
    """Drop and recreate access_raw."<table>" with columns from col_types.

    Identifiers (schema, table name, column names) are quoted via
    psycopg.sql.Identifier so spaces and reserved words are handled safely.
    No PK or FK constraints are added -- orphans must survive.

    Parameters
    ----------
    conn       : open psycopg connection (autocommit may be True or False;
                 called from within load_table's transaction when False).
    table      : Access table name (may contain spaces / odd characters).
    col_types  : list of ColumnType; each ct.name is the column name and
                 pg_ddl_type(ct) is the Postgres type.
    """
    schema_id = sql.Identifier("access_raw")
    table_id = sql.Identifier(table)

    # Build column definitions list: "name" type [NULL | NOT NULL]
    col_defs = []
    for ct in col_types:
        col_id = sql.Identifier(ct.name)
        # pg_ddl_type returns a plain string -- embed as SQL literal fragment
        type_frag = sql.SQL(pg_ddl_type(ct))
        null_frag = sql.SQL("NULL" if ct.nullable else "NOT NULL")
        col_defs.append(
            sql.SQL("{col} {type} {null}").format(
                col=col_id,
                type=type_frag,
                null=null_frag,
            )
        )

    drop_stmt = sql.SQL("DROP TABLE IF EXISTS {schema}.{table}").format(
        schema=schema_id,
        table=table_id,
    )

    if col_defs:
        create_stmt = sql.SQL(
            "CREATE TABLE {schema}.{table} ({cols})"
        ).format(
            schema=schema_id,
            table=table_id,
            cols=sql.SQL(", ").join(col_defs),
        )
    else:
        # Edge case: no columns (still a valid empty table)
        create_stmt = sql.SQL(
            "CREATE TABLE {schema}.{table} ()"
        ).format(
            schema=schema_id,
            table=table_id,
        )

    with conn.cursor() as cur:
        cur.execute(drop_stmt)
        cur.execute(create_stmt)


# ---------------------------------------------------------------------------
# single_writer
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def single_writer(conn):
    """Context manager: acquire pg_advisory_xact_lock(ADVISORY_LOCK_KEY).

    The lock is scoped to the current transaction on `conn` and is released
    automatically when that transaction commits or rolls back.  A second
    connection attempting pg_try_advisory_xact_lock while this lock is held
    will get False (or block until timeout with lock_timeout).

    conn must be a psycopg connection NOT in autocommit mode so the advisory
    lock lasts for the duration of the caller's transaction block.
    """
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT pg_advisory_xact_lock({key})").format(
                key=sql.Literal(ADVISORY_LOCK_KEY)
            )
        )
    yield


# ---------------------------------------------------------------------------
# load_table
# ---------------------------------------------------------------------------

def load_table(
    conn,
    table: str,
    col_types: list,
    rows: Iterable[tuple],
    run_id: str,
    continue_on_error: bool = False,
) -> int:
    """Load rows into access_raw."<table>" and update access_meta.tables.

    The entire operation runs in ONE transaction (conn must not be in
    autocommit mode).  On success, commits and returns the inserted count.
    On any error, rolls back then records load_state='failed' in a separate
    auto-committed statement.

    TRUNCATE before insert ensures idempotency: re-running load_table with
    the same rows yields the same count rather than doubling it.

    Parameters
    ----------
    conn             : psycopg connection, autocommit=False.
    table            : Access table name.
    col_types        : list of ColumnType (with .name set).
    rows             : iterable of tuples; consumed exactly once.
    run_id           : FK into access_meta.extraction_run.
    continue_on_error: if True, swallow the error after recording 'failed';
                       if False (default), re-raise.

    Returns
    -------
    int -- number of rows inserted.
    """
    schema_id = sql.Identifier("access_raw")
    table_id = sql.Identifier(table)

    try:
        # ------------------------------------------------------------------
        # 1. Upsert access_meta.tables with load_state='extracting'
        # ------------------------------------------------------------------
        upsert_sql = sql.SQL("""
            INSERT INTO access_meta.tables (run_id, table_name, load_state)
            VALUES (%s, %s, 'extracting')
            ON CONFLICT (run_id, table_name)
            DO UPDATE SET load_state = 'extracting'
        """)
        with conn.cursor() as cur:
            cur.execute(upsert_sql, (run_id, table))

        # ------------------------------------------------------------------
        # 2. Drop-and-recreate the staging table
        # ------------------------------------------------------------------
        create_access_raw_table(conn, table, col_types)

        # ------------------------------------------------------------------
        # 3. TRUNCATE (idempotency guard -- no-op on a fresh table)
        # ------------------------------------------------------------------
        trunc_stmt = sql.SQL("TRUNCATE {schema}.{table}").format(
            schema=schema_id, table=table_id
        )
        with conn.cursor() as cur:
            cur.execute(trunc_stmt)

        # ------------------------------------------------------------------
        # 4. Bulk insert all rows
        # ------------------------------------------------------------------
        row_count = 0
        if col_types:
            col_ids = sql.SQL(", ").join(
                sql.Identifier(ct.name) for ct in col_types
            )
            placeholders = sql.SQL(", ").join(
                sql.SQL("%s") for _ in col_types
            )
            insert_stmt = sql.SQL(
                "INSERT INTO {schema}.{table} ({cols}) VALUES ({vals})"
            ).format(
                schema=schema_id,
                table=table_id,
                cols=col_ids,
                vals=placeholders,
            )
            with conn.cursor() as cur:
                # executemany is efficient for batch inserts in psycopg v3
                data_list = list(rows)  # materialise to get the count
                row_count = len(data_list)
                if data_list:
                    cur.executemany(insert_stmt, data_list)
        else:
            # No columns -- consume the iterator to detect errors, count rows
            data_list = list(rows)
            row_count = len(data_list)

        # ------------------------------------------------------------------
        # 5. Update load_state='loaded' + staging_row_count
        # ------------------------------------------------------------------
        update_sql = sql.SQL("""
            UPDATE access_meta.tables
               SET load_state = 'loaded',
                   staging_row_count = %s
             WHERE run_id = %s
               AND table_name = %s
        """)
        with conn.cursor() as cur:
            cur.execute(update_sql, (row_count, run_id, table))

        # ------------------------------------------------------------------
        # 5'. Stamp this run_id as the CURRENT owner of the materialised
        #     access_raw layer (multi-run isolation guard, fixes 5+6).  Because
        #     create_access_raw_table drops+recreates access_raw.<table>
        #     GLOBALLY (latest-only), validate must fail closed when a stale
        #     run_id is asked to read it.  Stamped inside this txn so it is
        #     atomic with the load.
        # ------------------------------------------------------------------
        _stamp_access_raw_owner(conn, run_id)

        # ------------------------------------------------------------------
        # 6. COMMIT
        # ------------------------------------------------------------------
        conn.commit()
        return row_count

    except Exception:
        # Roll back the failed transaction
        conn.rollback()

        # Record load_state='failed' in its own committed statement so the
        # failure is visible even though the main transaction was rolled back.
        try:
            fail_sql = sql.SQL("""
                INSERT INTO access_meta.tables (run_id, table_name, load_state)
                VALUES (%s, %s, 'failed')
                ON CONFLICT (run_id, table_name)
                DO UPDATE SET load_state = 'failed'
            """)
            with conn.cursor() as cur:
                cur.execute(fail_sql, (run_id, table))
            conn.commit()
        except Exception:
            # Best-effort -- if we cannot write the failure record, ignore
            try:
                conn.rollback()
            except Exception:
                pass

        if not continue_on_error:
            raise
        return 0
