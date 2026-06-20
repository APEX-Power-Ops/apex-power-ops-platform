-- =============================================================================
-- Records migration 043 -- NETA acceptance-value source-link companion
--   records.neta_table_source_links: no-excerpt source lineage for records.neta_tables.
--   Schema only. No seed rows. No source-body reads. No acceptance-value import.
--
-- Requires (canonical records order):
--   001_records_enums.sql              records schema + records.neta_standard_enum
--   004_records_triggers_and_views.sql records.fn_set_updated_at()
--   005_neta_reference_tables.sql      records.neta_tables (pk neta_table_id uuid)
--   038_neta_tables_standard.sql       standard col + UNIQUE (standard, table_number)
--
-- Design notes:
--   Governed metadata ONLY -- provenance, policy posture, and review lifecycle for where
--   an acceptance-table row came from; never duplicates values or stores source excerpts.
--   Bespoke vocab (surface / use-posture / confidence / validation-status) is
--   CHECK-constrained text, not enums: single-table operational vocab, cheaper to evolve
--   (records.neta_standard_enum, a cross-table domain enum, is reused as-is).
--   NO RLS / grants: no records migration (001-042) defines any; the lane is local-PG +
--   future PowerSync, not yet on the governed Supabase API surface. RLS/grants are deferred
--   to a deliberate, lane-wide records serving/security migration.
--   Reviewed: docs/architecture/knowledge-domain/apex-resa/
--   NETA_ETT_RECORDS_SOURCE_LINK_SCHEMA_043_TECHNICAL_AUTHORITY_REVIEW_2026-06-19.md
-- =============================================================================

BEGIN;
SET client_encoding TO 'UTF8';
-- Pin scs=on so the backslash in the drive-path CHECK regex below reaches the
-- regex engine literally (it is the PG 9.1+ default; this hardens the security
-- constraint against any session that flipped it off).
SET standard_conforming_strings TO on;

-- ---------------------------------------------------------------------------
-- records.neta_table_source_links
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS records.neta_table_source_links (
    neta_table_source_link_id   uuid        NOT NULL DEFAULT gen_random_uuid(),

    -- Nullable so metadata candidates can be reviewed before an exact row match.
    neta_table_id               uuid        NULL,

    -- Current acceptance-value target is ATS/MTS records.neta_tables.
    standard                    records.neta_standard_enum NOT NULL,
    table_number                text        NULL,

    source_repo_id              text        NOT NULL,
    source_repo_head            text        NOT NULL,
    source_repo_dirty_count     integer     NOT NULL,

    source_surface              text        NOT NULL,
    source_family               text        NOT NULL,
    canonical_family            text        NOT NULL,
    source_path                 text        NOT NULL,
    source_file                 text        NOT NULL,
    source_owner                text        NOT NULL,
    source_use_posture          text        NOT NULL DEFAULT 'metadata_only',

    locator_kind                text        NOT NULL,
    locator_value               text        NULL,

    lineage_confidence          text        NOT NULL DEFAULT 'medium',
    restricted_review_required  boolean     NOT NULL DEFAULT true,
    validation_status           text        NOT NULL DEFAULT 'candidate',

    -- Operator/review prose only. Never source excerpts or acceptance values.
    review_notes                text        NULL,

    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT pk_neta_table_source_links
        PRIMARY KEY (neta_table_source_link_id),

    CONSTRAINT fk_neta_table_source_links_table
        FOREIGN KEY (neta_table_id)
        REFERENCES records.neta_tables (neta_table_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_neta_table_source_links_dirty_count
        CHECK (source_repo_dirty_count >= 0),

    -- Git HEAD must be a full SHA-1 (40) or SHA-256 (64) lowercase hex hash.
    CONSTRAINT ck_neta_table_source_links_source_head
        CHECK (source_repo_head ~ '^([0-9a-f]{40}|[0-9a-f]{64})$'),

    -- Acceptance-value links resolve only against ATS/MTS records.neta_tables.
    CONSTRAINT ck_neta_table_source_links_standard
        CHECK (standard IN ('ats', 'mts')),

    CONSTRAINT ck_neta_table_source_links_source_surface
        CHECK (source_surface IN (
            'resources_references',
            'resources_catalog',
            'resources_extractions'
        )),

    CONSTRAINT ck_neta_table_source_links_use_posture
        CHECK (source_use_posture IN (
            'metadata_only',
            'cite_only',
            'public_domain',
            'operator_authored',
            'extract_with_permission',
            'unknown'
        )),

    CONSTRAINT ck_neta_table_source_links_lineage_confidence
        CHECK (lineage_confidence IN ('high', 'medium', 'low', 'blocked')),

    CONSTRAINT ck_neta_table_source_links_validation_status
        CHECK (validation_status IN (
            'candidate',
            'valid_metadata',
            'matched_record',
            'blocked_policy',
            'blocked_missing_source',
            'blocked_content_review',
            'excluded'
        )),

    -- Repo-relative path only: block drive roots, absolute roots, traversal, and
    -- credential/control surfaces.
    CONSTRAINT ck_neta_table_source_links_source_path_relative
        CHECK (
            source_path <> ''
            AND source_path !~ '^[A-Za-z]:[\\/]'
            AND source_path !~ '^/'
            AND source_path !~ '(^|/)[.][.](/|$)'
            AND source_path !~ '(^|/)([.]env|[.]secrets|[.]claude|[.]git)(/|$)'
        ),

    CONSTRAINT ck_neta_table_source_links_source_file_name_only
        CHECK (
            source_file <> ''
            AND source_file !~ '[\\/]'
        ),

    CONSTRAINT ck_neta_table_source_links_text_nonempty
        CHECK (
            source_repo_id <> ''
            AND source_family <> ''
            AND canonical_family <> ''
            AND source_owner <> ''
            AND locator_kind <> ''
        ),

    CONSTRAINT ck_neta_table_source_links_review_notes_length
        CHECK (review_notes IS NULL OR char_length(review_notes) <= 2000)
);

COMMENT ON TABLE records.neta_table_source_links IS
    'No-excerpt source lineage companion for records.neta_tables. Governed metadata only; never source-body excerpts or duplicated acceptance values.';

COMMENT ON COLUMN records.neta_table_source_links.neta_table_id IS
    'Nullable FK to records.neta_tables while candidate rows are unresolved.';
COMMENT ON COLUMN records.neta_table_source_links.source_repo_head IS
    'Git HEAD (SHA-1 or SHA-256) of the source checkout used for metadata validation.';
COMMENT ON COLUMN records.neta_table_source_links.source_path IS
    'Repo-relative source path only. Absolute paths, traversal, .env, .secrets, .claude, .git are blocked by CHECK.';
COMMENT ON COLUMN records.neta_table_source_links.review_notes IS
    'Operator/review prose only. Never store source excerpts or acceptance values here.';

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_neta_table_source_links_table
    ON records.neta_table_source_links (neta_table_id);

CREATE INDEX IF NOT EXISTS ix_neta_table_source_links_standard_number
    ON records.neta_table_source_links (standard, table_number);

CREATE INDEX IF NOT EXISTS ix_neta_table_source_links_source_family
    ON records.neta_table_source_links (source_family, source_surface);

CREATE INDEX IF NOT EXISTS ix_neta_table_source_links_policy_queue
    ON records.neta_table_source_links (restricted_review_required, validation_status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_neta_table_source_links_source_locator
    ON records.neta_table_source_links (
        source_repo_id,
        source_repo_head,
        source_path,
        standard,
        COALESCE(table_number, ''),
        locator_kind,
        COALESCE(locator_value, '')
    );

-- ---------------------------------------------------------------------------
-- updated_at trigger (reuses the records-lane shared function from 004)
-- ---------------------------------------------------------------------------

DROP TRIGGER IF EXISTS trg_neta_table_source_links_updated_at
    ON records.neta_table_source_links;

CREATE TRIGGER trg_neta_table_source_links_updated_at
    BEFORE UPDATE ON records.neta_table_source_links
    FOR EACH ROW EXECUTE FUNCTION records.fn_set_updated_at();

-- RLS / grants intentionally omitted -- deferred to a lane-wide records
-- serving/security migration (no records migration 001-042 defines any).

COMMIT;
