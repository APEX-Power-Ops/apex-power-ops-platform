"""Task 0 TDD test: verify schemas and core tables exist after applying 001_schemas.sql."""

import psycopg


def test_schemas_and_core_tables_exist(pg):
    """After applying 001_schemas.sql, 4 schemas and key tables must exist."""
    with pg.cursor() as cur:
        # Check all 4 schemas exist
        cur.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = ANY(%s)
            ORDER BY schema_name
            """,
            (["access_meta", "access_raw", "access_validation", "tcc_snapshot"],),
        )
        found_schemas = [row[0] for row in cur.fetchall()]

    assert "access_meta" in found_schemas, "Schema access_meta not found"
    assert "access_raw" in found_schemas, "Schema access_raw not found"
    assert "access_validation" in found_schemas, "Schema access_validation not found"
    assert "tcc_snapshot" in found_schemas, "Schema tcc_snapshot not found"

    with pg.cursor() as cur:
        # Check access_meta.extraction_run exists
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'access_meta'
              AND table_name = 'extraction_run'
            """
        )
        (count,) = cur.fetchone()

    assert count == 1, "Table access_meta.extraction_run not found"

    with pg.cursor() as cur:
        # Check access_validation.antijoin_vs_tcc exists
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'access_validation'
              AND table_name = 'antijoin_vs_tcc'
            """
        )
        (count,) = cur.fetchone()

    assert count == 1, "Table access_validation.antijoin_vs_tcc not found"
