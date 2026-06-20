-- =============================================================================
-- Records migration 044 -- person anchor (records.persons) + technician spine FK.
--   Phase-5 additive identity slice. Authority:
--   .claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md (C1, C3, D2, D4, D5).
--   Lane: integration/person-identity-slice.  Dev DB: records_dev (local PG). NOT applied to prod.
--
-- Per-lane LOCAL ANCHOR for the person spine -- parity with the apparatus anchor
-- (records.assets): the canonical person key is prod public.employees.id, reachable
-- ONLY across databases, so employee_ref is the single dangling contract-FK
-- (validated by the C8 reconciliation job, NEVER a DB foreign key). Every records
-- "who" column becomes a real in-DB FK to THIS table (not a bare per-row uuid -- the
-- soft-uuid pattern that rotted the ops "Law 2").
--
-- Requires (canonical records order):
--   001_records_enums.sql              records schema
--   002_records_tables.sql             records.form_submissions (free-text technician varchar)
--   004_records_triggers_and_views.sql records.fn_set_updated_at()
--
-- NO RLS / grants -- consistent with records 001-043 (lane is local-PG + future
-- PowerSync, not yet on the governed Supabase API surface).
-- =============================================================================

BEGIN;
SET client_encoding TO 'UTF8';

CREATE TABLE IF NOT EXISTS records.persons (
    person_id       uuid        NOT NULL DEFAULT gen_random_uuid(),

    -- The ONE cross-DB pointer: prod public.employees.id. NOT a DB FK (employees
    -- lives in a separate database). NULL until human-adjudicated.
    employee_ref    uuid        NULL,

    display_name    text        NOT NULL,

    -- D4: represent W-2 / 1099 / partner / legacy (non-login) workers in the model.
    worker_class    text        NOT NULL DEFAULT 'w2',

    -- C3: matching is human-adjudicated, NEVER fuzzy. Provenance of the match.
    match_adjudicated_by    uuid        NULL,
    match_adjudicated_at    timestamptz NULL,
    match_confidence        text        NULL,

    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT pk_persons PRIMARY KEY (person_id),

    CONSTRAINT ck_persons_display_name_nonempty
        CHECK (display_name <> ''),

    CONSTRAINT ck_persons_worker_class
        CHECK (worker_class IN ('w2', '1099', 'partner', 'legacy')),

    CONSTRAINT ck_persons_match_confidence
        CHECK (match_confidence IS NULL OR match_confidence IN ('exact', 'high', 'manual')),

    -- An adjudicated match must name who AND when (audit completeness); both NULL = unadjudicated.
    CONSTRAINT ck_persons_match_adjudication_paired
        CHECK (
            (match_adjudicated_by IS NULL AND match_adjudicated_at IS NULL)
            OR (match_adjudicated_by IS NOT NULL AND match_adjudicated_at IS NOT NULL)
        )
);

COMMENT ON TABLE records.persons IS
    'Local person anchor for the records lane (identity contract C1/D2). Canonical person spine '
    'is prod public.employees.id; employee_ref is the single cross-DB contract-FK (reconciliation-'
    'validated, not a DB FK). Every records "who" column FKs THIS table.';
COMMENT ON COLUMN records.persons.employee_ref IS
    'Contract-FK to prod public.employees.id. NULL = MATCHABLE-PENDING / PERMANENTLY-UNMATCHED. '
    'Never auto-joined by email or fuzzy match (contract C2/C3) -- only human adjudication sets it.';
COMMENT ON COLUMN records.persons.worker_class IS
    'w2 | 1099 | partner | legacy (contract D4). Non-w2 classes need no login account.';

-- At most one anchor row per real employee (partial: many NULL employee_ref allowed).
CREATE UNIQUE INDEX IF NOT EXISTS uq_persons_employee_ref
    ON records.persons (employee_ref)
    WHERE employee_ref IS NOT NULL;

DROP TRIGGER IF EXISTS trg_persons_updated_at ON records.persons;
CREATE TRIGGER trg_persons_updated_at
    BEFORE UPDATE ON records.persons
    FOR EACH ROW EXECUTE FUNCTION records.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- records.form_submissions adopts the spine (contract C3).
--   technician_person_id: real in-DB FK to the local anchor (nullable; legacy rows
--     keep free text only). ON DELETE SET NULL -- removing an anchor row must never
--     delete a test record (the evidence outlives the identity bookkeeping).
--   Free-text technician is RETAINED as immutable provenance (never overwritten).
--   Forward-only capture discipline is app-enforced now; a CHECK/trigger lands once
--   the column is populated (contract D5).
-- ---------------------------------------------------------------------------

ALTER TABLE records.form_submissions
    ADD COLUMN IF NOT EXISTS technician_person_id uuid NULL;

ALTER TABLE records.form_submissions
    DROP CONSTRAINT IF EXISTS fk_form_submissions_technician_person;
ALTER TABLE records.form_submissions
    ADD CONSTRAINT fk_form_submissions_technician_person
        FOREIGN KEY (technician_person_id)
        REFERENCES records.persons (person_id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_form_submissions_technician_person
    ON records.form_submissions (technician_person_id);

COMMENT ON COLUMN records.form_submissions.technician_person_id IS
    'Person-spine FK (records.persons). NULL for legacy/unadjudicated rows. The free-text '
    '"technician" column is retained as immutable provenance and never overwritten (contract C3).';

COMMIT;
