"""access_harness.inventory -- populate access_meta tables from extraction metadata.

populate_meta() writes one row per table (access_meta.tables), one row per column
(access_meta.columns), one row per PK (access_meta.primary_keys), one row per index
(access_meta.indexes), one row per FK relationship (access_meta.relationships), and
one row per saved query (access_meta.queries) for the given run_id.

Idempotency: all rows for run_id are deleted then re-inserted each call.

Row counts: access_row_count is populated cheaply with a COUNT(*) query via the
data_conn ODBC connection for loaded tables; NULL for inventoried_only tables.
"""
from __future__ import annotations

from typing import Optional

from access_harness import extract


def _count_rows(data_conn, table: str) -> Optional[int]:
    """Return COUNT(*) for a table via ODBC, or None on any error."""
    try:
        cur = data_conn.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) FROM [{table}]")
            row = cur.fetchone()
            return int(row[0]) if row is not None else None
        finally:
            cur.close()
    except Exception:
        return None


def populate_meta(
    pg_conn,
    data_conn,
    ace_conn,
    run_id: str,
    all_tables: list,
    loaded_tables: set,
    count_only_tables: Optional[set] = None,
) -> None:
    """Populate all access_meta tables for one extraction run.

    Parameters
    ----------
    pg_conn           : open psycopg connection (autocommit=True).
    data_conn         : open pyodbc connection to the .accdb (READ-ONLY).
    ace_conn          : open ACE OLE DB ADODB.Connection (READ-ONLY).
    run_id            : run identifier (must already exist in extraction_run).
    all_tables        : ordered list of all table names to inventory.
    loaded_tables     : set of table names that were successfully loaded into access_raw.
    count_only_tables : OPTIONAL set of table names that were NOT data-loaded but
                        whose access_row_count should still be recorded (a cheap
                        ODBC COUNT(*)).  Used for the curves table -- it is too
                        large to data-load locally, but its access-side count is
                        needed for the access-vs-tcc count reconciliation.  These
                        stay load_state='inventoried_only' (NOT 'loaded').
    """
    count_only_tables = count_only_tables or set()
    # ------------------------------------------------------------------
    # Delete existing rows for this run_id (idempotency).
    # ------------------------------------------------------------------
    # FIRST preserve any staging_row_count / checksum already written by an
    # earlier load step (load_table writes those before inventory runs in the
    # pipeline).  Re-inserting access_meta.tables without them would silently
    # WIPE the load-fidelity counts, so we carry them forward per table.
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT table_name, staging_row_count, checksum "
            "FROM access_meta.tables WHERE run_id = %s",
            (run_id,),
        )
        _preserved = {
            r[0]: {"staging_row_count": r[1], "checksum": r[2]}
            for r in cur.fetchall()
        }

    # Order matters for FK references: delete child tables before parents.
    # access_meta.tables is the logical parent; others carry (run_id, table_name).
    with pg_conn.cursor() as cur:
        cur.execute(
            "DELETE FROM access_meta.queries WHERE run_id = %s", (run_id,)
        )
        cur.execute(
            "DELETE FROM access_meta.relationships WHERE run_id = %s", (run_id,)
        )
        cur.execute(
            "DELETE FROM access_meta.indexes WHERE run_id = %s", (run_id,)
        )
        cur.execute(
            "DELETE FROM access_meta.primary_keys WHERE run_id = %s", (run_id,)
        )
        cur.execute(
            "DELETE FROM access_meta.columns WHERE run_id = %s", (run_id,)
        )
        cur.execute(
            "DELETE FROM access_meta.tables WHERE run_id = %s", (run_id,)
        )

    # ------------------------------------------------------------------
    # Pre-fetch all saved queries once (database-level, not per-table).
    # ------------------------------------------------------------------
    all_saved_queries = extract.saved_queries(ace_conn)

    # ------------------------------------------------------------------
    # Per-table metadata.
    # ------------------------------------------------------------------
    for table in all_tables:
        is_loaded = table in loaded_tables
        load_state = "loaded" if is_loaded else "inventoried_only"

        # Row count: cheap COUNT(*) for loaded tables AND for explicitly
        # count-only tables (e.g. curves -- not data-loaded but its access count
        # is needed for the access-vs-tcc count reconciliation); NULL otherwise.
        access_row_count: Optional[int] = None
        if is_loaded or table in count_only_tables:
            access_row_count = _count_rows(data_conn, table)

        # access_meta.tables -- carry forward any preserved load-fidelity values.
        preserved = _preserved.get(table, {})
        staging_row_count = preserved.get("staging_row_count")
        checksum = preserved.get("checksum")
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_meta.tables (
                    run_id,
                    table_name,
                    object_type,
                    load_state,
                    access_row_count,
                    staging_row_count,
                    checksum,
                    tcc_build_kind
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id,
                    table,
                    "TABLE",
                    load_state,
                    access_row_count,
                    staging_row_count,
                    checksum,
                    None,
                ),
            )

        # Column metadata (via cursor.description probe -- never cursor.columns()).
        cols = extract.column_meta(data_conn, table)
        for ordinal, ct in enumerate(cols, start=1):
            with pg_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO access_meta.columns (
                        run_id,
                        table_name,
                        column_name,
                        ordinal,
                        access_type,
                        mapped_pg_type,
                        nullable,
                        round_trip_verified
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        table,
                        ct.name,
                        ordinal,
                        ct.access_type,
                        ct.pg_type,
                        ct.nullable,
                        None,
                    ),
                )

        # Primary key (cursor.statistics()).
        pk_columns = extract.primary_key(data_conn, table)
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_meta.primary_keys (
                    run_id,
                    table_name,
                    key_columns,
                    coverage_source
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    run_id,
                    table,
                    pk_columns,
                    "cursor.statistics",
                ),
            )

        # Indexes (ACE OpenSchema adSchemaIndexes).
        table_indexes = extract.indexes(ace_conn, table)
        for idx in table_indexes:
            with pg_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO access_meta.indexes (
                        run_id,
                        table_name,
                        index_name,
                        key_columns,
                        is_unique,
                        coverage_source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        table,
                        idx["name"],
                        idx["columns"],
                        idx["is_unique"],
                        "ace.adSchemaIndexes",
                    ),
                )

        # Foreign keys (ACE OpenSchema adSchemaForeignKeys) -- child side.
        fks = extract.foreign_keys(ace_conn, table)
        # Group by fk_name so each relationship is one row with arrays.
        fk_by_name: dict = {}
        for fk in fks:
            name = fk["fk_name"] or "__unnamed__"
            entry = fk_by_name.setdefault(
                name,
                {
                    "fk_columns": [],
                    "pk_table": fk["pk_table"],
                    "pk_columns": [],
                },
            )
            entry["fk_columns"].append(fk["fk_column"])
            entry["pk_columns"].append(fk["pk_column"])

        for rel in fk_by_name.values():
            with pg_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO access_meta.relationships (
                        run_id,
                        fk_table,
                        fk_columns,
                        pk_table,
                        pk_columns,
                        coverage_source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        table,
                        rel["fk_columns"],
                        rel["pk_table"],
                        rel["pk_columns"],
                        "ace.adSchemaForeignKeys",
                    ),
                )

    # ------------------------------------------------------------------
    # Saved queries (database-level, not per-table).
    # ------------------------------------------------------------------
    for q in all_saved_queries:
        sql_text = q.get("sql_text")
        sql_text_complete = bool(sql_text) if sql_text is not None else False
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_meta.queries (
                    run_id,
                    query_name,
                    query_type,
                    sql_text,
                    sql_text_complete,
                    inventory_source
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, query_name) DO NOTHING
                """,
                (
                    run_id,
                    q.get("name"),
                    q.get("type"),
                    sql_text,
                    sql_text_complete,
                    "ace.adSchemaProcedures+adSchemaViews",
                ),
            )
