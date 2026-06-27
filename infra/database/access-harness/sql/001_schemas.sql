-- 001_schemas.sql
-- Access Fidelity Harness -- schema DDL
-- HR1: structural columns only (counts/deltas/hashes/key-tuples/booleans-of-structure/load-process states).
-- No interpretive/verdict columns (is_gap, correct, expected, category, verdict).

-- ============================================================
-- Schemas
-- ============================================================
CREATE SCHEMA IF NOT EXISTS access_raw;
CREATE SCHEMA IF NOT EXISTS access_meta;
CREATE SCHEMA IF NOT EXISTS access_validation;
CREATE SCHEMA IF NOT EXISTS tcc_snapshot;

-- ============================================================
-- access_meta tables
-- ============================================================

CREATE TABLE IF NOT EXISTS access_meta.extraction_run (
    run_id              text        PRIMARY KEY,
    source_path         text,
    frozen_copy_path    text,
    source_size         bigint,
    source_mtime_utc    timestamptz,
    source_sha256       text,
    extracted_at_utc    timestamptz,
    driver_name         text,
    dbms_version        text,
    read_only           boolean,
    harness_version     text
);

CREATE TABLE IF NOT EXISTS access_meta.tcc_snapshot (
    snapshot_id     text        PRIMARY KEY,
    run_id          text        REFERENCES access_meta.extraction_run(run_id),
    host            text,
    db_name         text,
    captured_at     timestamptz,
    role            text
);

CREATE TABLE IF NOT EXISTS access_meta.tcc_snapshot_table (
    snapshot_id     text        REFERENCES access_meta.tcc_snapshot(snapshot_id),
    table_name      text,
    tcc_row_count   bigint,
    PRIMARY KEY (snapshot_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_meta.tables (
    run_id              text        REFERENCES access_meta.extraction_run(run_id),
    table_name          text,
    object_type         text,
    load_state          text        NOT NULL
                                    CHECK (load_state IN (
                                        'inventoried_only',
                                        'extracting',
                                        'loaded',
                                        'checksummed',
                                        'failed'
                                    )),
    access_row_count    bigint,
    staging_row_count   bigint,
    checksum            text,
    has_usable_unique_key   boolean,
    tcc_build_kind      text        CHECK (tcc_build_kind IN (
                                        '1:1_load',
                                        'computed',
                                        'derived',
                                        'none'
                                    )),
    started_at          timestamptz,
    completed_at        timestamptz,
    PRIMARY KEY (run_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_meta.columns (
    run_id              text,
    table_name          text,
    column_name         text,
    ordinal             int,
    access_type         text,
    mapped_pg_type      text,
    nullable            boolean,
    size                int,
    precision           int,
    round_trip_verified boolean,
    PRIMARY KEY (run_id, table_name, column_name)
);

CREATE TABLE IF NOT EXISTS access_meta.primary_keys (
    run_id              text,
    table_name          text,
    key_columns         text[],
    coverage_source     text,
    PRIMARY KEY (run_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_meta.indexes (
    run_id              text,
    table_name          text,
    index_name          text,
    key_columns         text[],
    is_unique           boolean,
    coverage_source     text,
    PRIMARY KEY (run_id, table_name, index_name)
);

CREATE TABLE IF NOT EXISTS access_meta.relationships (
    run_id          text,
    fk_table        text,
    fk_columns      text[],
    pk_table        text,
    pk_columns      text[],
    coverage_source text
);

CREATE TABLE IF NOT EXISTS access_meta.queries (
    run_id              text,
    query_name          text,
    query_type          text,
    sql_text            text,
    sql_text_complete   boolean,
    inventory_source    text,
    is_parameterless    boolean,
    PRIMARY KEY (run_id, query_name)
);

CREATE TABLE IF NOT EXISTS access_meta.golden_allowlist (
    query_name  text    PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS access_meta.projection_map (
    access_table    text,
    access_column   text,
    tcc_table       text,
    tcc_column      text,
    type_alignment  text,
    PRIMARY KEY (access_table, access_column)
);

-- ============================================================
-- access_validation tables
-- ============================================================

CREATE TABLE IF NOT EXISTS access_validation.row_count_reconciliation (
    run_id              text,
    table_name          text,
    access_row_count    bigint,
    staging_row_count   bigint,
    delta               bigint,
    PRIMARY KEY (run_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_validation.checksum_reconciliation (
    run_id              text,
    table_name          text,
    access_checksum     text,
    staging_checksum    text,
    matches             boolean,
    PRIMARY KEY (run_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_validation.type_drift (
    run_id              text,
    table_name          text,
    column_name         text,
    access_type         text,
    mapped_pg_type      text,
    coercion            text,
    not_comparable_coerced  boolean,
    PRIMARY KEY (run_id, table_name, column_name)
);

CREATE TABLE IF NOT EXISTS access_validation.key_quality (
    run_id              text,
    table_name          text,
    candidate_key       text[],
    is_unique           boolean,
    distinct_count      bigint,
    total_count         bigint,
    PRIMARY KEY (run_id, table_name)
);

CREATE TABLE IF NOT EXISTS access_validation.antijoin_vs_tcc (
    run_id                      text,
    snapshot_id                 text,
    access_table                text,
    tcc_table                   text,
    method                      text,
    missing_in_tcc_count        bigint,
    extra_in_tcc_count          bigint,
    frames_with_deficit         bigint,
    enumerated_missing          jsonb,
    row_antijoin_not_applicable boolean,
    PRIMARY KEY (run_id, access_table)
);

CREATE TABLE IF NOT EXISTS access_validation.golden_capture (
    run_id          text,
    query_name      text,
    captured_at     timestamptz,
    row_count       bigint,
    result_snapshot jsonb,
    PRIMARY KEY (run_id, query_name)
);

-- Access-raw vs tcc-snapshot count reconciliation (the access-vs-governed-tcc
-- count delta; distinct from row_count_reconciliation which is access-vs-staging
-- load fidelity).  delta = access_row_count - tcc_row_count.  Purely structural.
CREATE TABLE IF NOT EXISTS access_validation.tcc_count_reconciliation (
    run_id              text,
    access_table        text,
    tcc_table           text,
    snapshot_id         text,
    access_row_count    bigint,
    tcc_row_count       bigint,
    delta               bigint,
    PRIMARY KEY (run_id, access_table)
);

-- Style-mediated frame-resolution structural evidence.  The Access frame's
-- breaker class is IMPLICIT: only Breaker_TMTFrameSizes.StyleID is recorded, and
-- a StyleID can appear in MORE THAN ONE Access style-table ID space (the per-class
-- (class,id) overlap).  This table records, per run, how many distinct Access
-- StyleIDs resolve to exactly one class, to two-or-more classes (AMBIGUOUS -- the
-- class cannot be picked without fabricating it), and to no class.  These are
-- COUNTS ONLY -- the harness records the ambiguity; it never resolves it.
CREATE TABLE IF NOT EXISTS access_validation.style_resolution (
    run_id                          text,
    access_frame_table              text,
    distinct_styleid_count          bigint,
    resolved_single_class_count     bigint,
    ambiguous_multi_class_count     bigint,
    unresolved_no_class_count       bigint,
    mccb_only_count                 bigint,
    iccb_only_count                 bigint,
    pcb_only_count                  bigint,
    PRIMARY KEY (run_id, access_frame_table)
);

-- Clean style-provenance anti-join: Access BreakerXXXStyles.ID -> tcc
-- brk_xxx_styles.source_id.  This is the ONE cross-instance key that is provably
-- 1:1 (it does not route through the re-sequenced tmt_frames.id surrogate), so it
-- is the cleanly-keyable child anti-join.  missing_in_tcc / extra_in_tcc are the
-- set-diff cardinalities (purely structural; cast to text symmetrically so an
-- int-vs-numeric storage difference cannot fabricate a spurious delta).
CREATE TABLE IF NOT EXISTS access_validation.style_provenance_antijoin (
    run_id              text,
    breaker_class       text,
    access_style_table  text,
    tcc_style_table     text,
    access_id_count     bigint,
    tcc_source_id_count bigint,
    missing_in_tcc_count    bigint,
    extra_in_tcc_count      bigint,
    enumerated_missing  jsonb,
    PRIMARY KEY (run_id, breaker_class)
);

-- ============================================================
-- Convenience views
-- ============================================================

CREATE OR REPLACE VIEW access_meta.latest_run AS
SELECT *
FROM access_meta.extraction_run
WHERE extracted_at_utc = (
    SELECT MAX(extracted_at_utc) FROM access_meta.extraction_run
);
