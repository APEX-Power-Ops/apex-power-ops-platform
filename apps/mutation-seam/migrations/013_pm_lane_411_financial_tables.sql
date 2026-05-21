-- ============================================================================
-- APEX PM Lane 411 / 420 — Financial Table Schema Floor
-- Migration: 013_pm_lane_411_financial_tables.sql
-- Created:   2026-05-21
-- ============================================================================
-- Creates the four financial tables required by the Lane 420 hosted smoke.
--
-- Production adaptations from the design packet:
--   * seam.projects.id and seam.apparatus.id are TEXT in production.
--   * scopes currently lives in public.scopes with UUID ids.
--   * the current import-contract-support packet emits the snapshot kind
--     miner_temp_power_contract_support, so that admitted kind is accepted.
--
-- Scope
--   * Create seam.project_contract_snapshots.
--   * Create seam.scope_labor_details.
--   * Create seam.apparatus_financials.
--   * Create seam.apparatus_revenue_events.
--   * Create the enum types those tables require.
--   * Enable RLS and preserve anon/authenticated deny posture.
--   * Preserve insert-only mutation surfaces.
--
-- Out of scope
--   * No live PM/operations/field-role grants. Those roles do not exist in the
--     current production database and remain a later admitted grant packet.
--   * The existing smoke-only lane_420_rowcount_reader role may receive
--     conditional SELECT grants when present so hosted verification can remain
--     read-only.
--   * No route implementation, business writes, views, or backfill.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'seam' AND t.typname = 'scope_labor_category'
    ) THEN
        CREATE TYPE seam.scope_labor_category AS ENUM (
            'Onsite Labor',
            'Offsite Labor',
            'Travel',
            'Outside Services'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'seam' AND t.typname = 'apparatus_revenue_event_kind'
    ) THEN
        CREATE TYPE seam.apparatus_revenue_event_kind AS ENUM (
            'apparatus_revenue_zero_baseline',
            'apparatus_revenue_recognized',
            'apparatus_revenue_reversed'
        );
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS seam.project_contract_snapshots (
    id                                  TEXT PRIMARY KEY,
    project_id                          TEXT NOT NULL REFERENCES seam.projects(id),
    snapshot_kind                       TEXT NOT NULL,
    contract_value                      NUMERIC(14,2) NOT NULL,
    total_quoted_hours                  NUMERIC(14,2) NOT NULL,
    recognition_rate_per_hour           NUMERIC(14,6) NOT NULL,
    effective_date                      DATE NOT NULL,
    source_fingerprint                  TEXT NOT NULL,
    mutation_authority                  TEXT NOT NULL DEFAULT 'not_admitted',
    revenue_recognition_authority       TEXT NOT NULL DEFAULT 'not_admitted',
    billing_export_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    invoice_authority                   TEXT NOT NULL DEFAULT 'not_admitted',
    accounting_authority                TEXT NOT NULL DEFAULT 'not_admitted',
    external_finance_sync_authority     TEXT NOT NULL DEFAULT 'not_admitted',
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                          TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    mutation_id                         TEXT NOT NULL,
    CONSTRAINT project_contract_snapshots_contract_value_nonnegative
        CHECK (contract_value >= 0),
    CONSTRAINT project_contract_snapshots_total_quoted_hours_positive
        CHECK (total_quoted_hours > 0),
    CONSTRAINT project_contract_snapshots_recognition_rate_nonnegative
        CHECK (recognition_rate_per_hour >= 0),
    CONSTRAINT project_contract_snapshots_kind_valid
        CHECK (
            snapshot_kind = 'original'
            OR snapshot_kind = 'miner_temp_power_contract_support'
            OR snapshot_kind ~ '^change_order_[1-9][0-9]*$'
        ),
    CONSTRAINT project_contract_snapshots_rate_reconciles
        CHECK (
            ABS(recognition_rate_per_hour - (contract_value / NULLIF(total_quoted_hours, 0))) < 0.001
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_contract_snapshots_project_kind
    ON seam.project_contract_snapshots (project_id, snapshot_kind);

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_contract_snapshots_mutation_id
    ON seam.project_contract_snapshots (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_contract_snapshots_audit_event_id
    ON seam.project_contract_snapshots (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_project_contract_snapshots_project_created_at
    ON seam.project_contract_snapshots (project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seam.scope_labor_details (
    id                      TEXT PRIMARY KEY,
    scope_id                UUID NOT NULL REFERENCES public.scopes(id),
    contract_snapshot_id    TEXT NOT NULL REFERENCES seam.project_contract_snapshots(id),
    labor_category          seam.scope_labor_category NOT NULL,
    quoted_amount           NUMERIC(14,2) NOT NULL,
    actual_amount           NUMERIC(14,2) NOT NULL DEFAULT 0,
    quoted_hours            NUMERIC(14,2),
    rate                    NUMERIC(14,6),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by              TEXT NOT NULL,
    audit_event_id          TEXT NOT NULL,
    mutation_id             TEXT NOT NULL,
    CONSTRAINT scope_labor_details_quoted_amount_nonnegative
        CHECK (quoted_amount >= 0),
    CONSTRAINT scope_labor_details_actual_amount_nonnegative
        CHECK (actual_amount >= 0),
    CONSTRAINT scope_labor_details_hours_required_for_labor
        CHECK (
            (
                labor_category IN ('Onsite Labor', 'Offsite Labor')
                AND quoted_hours IS NOT NULL
                AND quoted_hours >= 0
            )
            OR (
                labor_category IN ('Travel', 'Outside Services')
                AND quoted_hours IS NULL
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_scope_labor_details_contract_snapshot
    ON seam.scope_labor_details (contract_snapshot_id);

CREATE INDEX IF NOT EXISTS idx_scope_labor_details_scope
    ON seam.scope_labor_details (scope_id);

CREATE TABLE IF NOT EXISTS seam.apparatus_financials (
    id                                  TEXT PRIMARY KEY,
    apparatus_id                        TEXT NOT NULL REFERENCES seam.apparatus(id),
    contract_snapshot_id                TEXT NOT NULL REFERENCES seam.project_contract_snapshots(id),
    quoted_hours                        NUMERIC(14,2) NOT NULL,
    quoted_revenue                      NUMERIC(14,2) NOT NULL,
    recognition_rate_per_hour_snapshot  NUMERIC(14,6) NOT NULL,
    mutation_authority                  TEXT NOT NULL DEFAULT 'not_admitted',
    revenue_recognition_authority       TEXT NOT NULL DEFAULT 'not_admitted',
    billing_export_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    invoice_authority                   TEXT NOT NULL DEFAULT 'not_admitted',
    accounting_authority                TEXT NOT NULL DEFAULT 'not_admitted',
    external_finance_sync_authority     TEXT NOT NULL DEFAULT 'not_admitted',
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                          TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    mutation_id                         TEXT NOT NULL,
    CONSTRAINT apparatus_financials_quoted_hours_nonnegative
        CHECK (quoted_hours >= 0),
    CONSTRAINT apparatus_financials_quoted_revenue_nonnegative
        CHECK (quoted_revenue >= 0),
    CONSTRAINT apparatus_financials_rate_nonnegative
        CHECK (recognition_rate_per_hour_snapshot >= 0),
    CONSTRAINT apparatus_financials_quote_reconciles
        CHECK (
            ABS(quoted_revenue - (quoted_hours * recognition_rate_per_hour_snapshot)) < 0.01
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_apparatus_financials_apparatus_snapshot
    ON seam.apparatus_financials (apparatus_id, contract_snapshot_id);

CREATE INDEX IF NOT EXISTS idx_apparatus_financials_contract_snapshot
    ON seam.apparatus_financials (contract_snapshot_id);

CREATE INDEX IF NOT EXISTS idx_apparatus_financials_mutation_id
    ON seam.apparatus_financials (mutation_id);

CREATE TABLE IF NOT EXISTS seam.apparatus_revenue_events (
    id                                  TEXT PRIMARY KEY,
    record_kind                         seam.apparatus_revenue_event_kind NOT NULL,
    apparatus_id                        TEXT NOT NULL REFERENCES seam.apparatus(id),
    scope_id                            UUID NOT NULL REFERENCES public.scopes(id),
    project_id                          TEXT NOT NULL REFERENCES seam.projects(id),
    contract_snapshot_id                TEXT NOT NULL REFERENCES seam.project_contract_snapshots(id),
    recognized_amount                   NUMERIC(14,2) NOT NULL,
    recognition_percent                 NUMERIC(5,2) NOT NULL,
    recognition_date                    DATE NOT NULL,
    reverses_event_id                   TEXT REFERENCES seam.apparatus_revenue_events(id),
    source_status_from                  TEXT,
    source_status_to                    TEXT,
    revenue_recognition_authority       TEXT NOT NULL DEFAULT 'not_admitted',
    billing_export_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    invoice_authority                   TEXT NOT NULL DEFAULT 'not_admitted',
    accounting_authority                TEXT NOT NULL DEFAULT 'not_admitted',
    external_finance_sync_authority     TEXT NOT NULL DEFAULT 'not_admitted',
    idempotency_key                     TEXT NOT NULL,
    mutation_id                         TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                          TEXT NOT NULL,
    CONSTRAINT apparatus_revenue_events_percent_range
        CHECK (recognition_percent >= 0 AND recognition_percent <= 100),
    CONSTRAINT apparatus_revenue_events_zero_baseline_valid
        CHECK (
            record_kind <> 'apparatus_revenue_zero_baseline'
            OR (
                recognized_amount = 0
                AND recognition_percent = 0
                AND reverses_event_id IS NULL
            )
        ),
    CONSTRAINT apparatus_revenue_events_recognized_valid
        CHECK (
            record_kind <> 'apparatus_revenue_recognized'
            OR (
                recognized_amount > 0
                AND recognition_percent = 100.00
                AND reverses_event_id IS NULL
            )
        ),
    CONSTRAINT apparatus_revenue_events_reversed_valid
        CHECK (
            record_kind <> 'apparatus_revenue_reversed'
            OR (
                recognized_amount < 0
                AND reverses_event_id IS NOT NULL
            )
        ),
    CONSTRAINT apparatus_revenue_events_reversal_pointer_valid
        CHECK (
            reverses_event_id IS NULL
            OR record_kind = 'apparatus_revenue_reversed'
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_apparatus_revenue_events_idempotency_key
    ON seam.apparatus_revenue_events (idempotency_key);

CREATE INDEX IF NOT EXISTS idx_apparatus_revenue_events_contract_snapshot
    ON seam.apparatus_revenue_events (contract_snapshot_id);

CREATE INDEX IF NOT EXISTS idx_apparatus_revenue_events_apparatus
    ON seam.apparatus_revenue_events (apparatus_id, recognition_date DESC);

CREATE OR REPLACE FUNCTION seam.reject_lane_411_financial_table_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '%I.%I is insert-only', TG_TABLE_SCHEMA, TG_TABLE_NAME;
END;
$$;

DROP TRIGGER IF EXISTS trg_project_contract_snapshots_insert_only_update
    ON seam.project_contract_snapshots;
CREATE TRIGGER trg_project_contract_snapshots_insert_only_update
    BEFORE UPDATE ON seam.project_contract_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_project_contract_snapshots_insert_only_delete
    ON seam.project_contract_snapshots;
CREATE TRIGGER trg_project_contract_snapshots_insert_only_delete
    BEFORE DELETE ON seam.project_contract_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_scope_labor_details_insert_only_update
    ON seam.scope_labor_details;
CREATE TRIGGER trg_scope_labor_details_insert_only_update
    BEFORE UPDATE ON seam.scope_labor_details
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_scope_labor_details_insert_only_delete
    ON seam.scope_labor_details;
CREATE TRIGGER trg_scope_labor_details_insert_only_delete
    BEFORE DELETE ON seam.scope_labor_details
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_apparatus_financials_insert_only_update
    ON seam.apparatus_financials;
CREATE TRIGGER trg_apparatus_financials_insert_only_update
    BEFORE UPDATE ON seam.apparatus_financials
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_apparatus_financials_insert_only_delete
    ON seam.apparatus_financials;
CREATE TRIGGER trg_apparatus_financials_insert_only_delete
    BEFORE DELETE ON seam.apparatus_financials
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_apparatus_revenue_events_insert_only_update
    ON seam.apparatus_revenue_events;
CREATE TRIGGER trg_apparatus_revenue_events_insert_only_update
    BEFORE UPDATE ON seam.apparatus_revenue_events
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_apparatus_revenue_events_insert_only_delete
    ON seam.apparatus_revenue_events;
CREATE TRIGGER trg_apparatus_revenue_events_insert_only_delete
    BEFORE DELETE ON seam.apparatus_revenue_events
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

ALTER TABLE seam.project_contract_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE seam.scope_labor_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE seam.apparatus_financials ENABLE ROW LEVEL SECURITY;
ALTER TABLE seam.apparatus_revenue_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE seam.project_contract_snapshots FROM anon;
REVOKE ALL ON TABLE seam.project_contract_snapshots FROM authenticated;
REVOKE ALL ON TABLE seam.scope_labor_details FROM anon;
REVOKE ALL ON TABLE seam.scope_labor_details FROM authenticated;
REVOKE ALL ON TABLE seam.apparatus_financials FROM anon;
REVOKE ALL ON TABLE seam.apparatus_financials FROM authenticated;
REVOKE ALL ON TABLE seam.apparatus_revenue_events FROM anon;
REVOKE ALL ON TABLE seam.apparatus_revenue_events FROM authenticated;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lane_420_rowcount_reader') THEN
        GRANT SELECT ON TABLE seam.project_contract_snapshots TO lane_420_rowcount_reader;
        GRANT SELECT ON TABLE seam.scope_labor_details TO lane_420_rowcount_reader;
        GRANT SELECT ON TABLE seam.apparatus_financials TO lane_420_rowcount_reader;
        GRANT SELECT ON TABLE seam.apparatus_revenue_events TO lane_420_rowcount_reader;
    END IF;
END;
$$;

COMMENT ON TABLE seam.project_contract_snapshots IS
    'Lane 411 project-level contract snapshots. Live adaptation uses TEXT seam ids and admits miner_temp_power_contract_support.';
COMMENT ON TABLE seam.scope_labor_details IS
    'Lane 411 scope-level labor pool breakdown rows keyed to project contract snapshots.';
COMMENT ON TABLE seam.apparatus_financials IS
    'Lane 411 apparatus-level frozen quote financials keyed to project contract snapshots.';
COMMENT ON TABLE seam.apparatus_revenue_events IS
    'Lane 411 apparatus revenue-recognition event ledger.';

-- ============================================================================
-- END of 013_pm_lane_411_financial_tables.sql
-- ============================================================================