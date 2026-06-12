-- =============================================================================
-- NETA Records Domain — Core Tables  (PowerDB replacement, Chip 1)
-- Packet: 2026-06-12-neta-records-001
-- Authority: reference/neta-records/00-MASTER-INDEX.md  §3 (data model)
-- Landing Lane: infra/database/migrations/neta/
-- Requires: 001_neta_enums.sql (schema + enums)
--
-- The eight foundation tables for the four PowerDB pillars. Cross-schema links
-- to org.* / work.* are carried as DEFERRED soft UUID columns (no hard FK) so
-- this migration can land independently of org/work seed ordering, mirroring the
-- work→org deferred-FK pattern. Hard-FK activation is a later chip (see the
-- punch list). Every row carries provenance so a PowerDB import is auditable.
-- =============================================================================

-- ===========================================================================
-- PILLAR 1 — ASSET REGISTER
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- neta.asset_classes
--   Equipment-type taxonomy (PowerDB "equipment category"): the thing a test
--   object IS. Maps to a NETA procedure category so datasheet templates and PM
--   programs can be scoped by class (e.g. "LV Power Circuit Breaker").
-- ---------------------------------------------------------------------------
CREATE TABLE neta.asset_classes (
    asset_class_id      uuid            NOT NULL DEFAULT gen_random_uuid(),
    class_code          text            NOT NULL,                    -- e.g. 'lv_pcb'
    name                text            NOT NULL,                    -- e.g. 'LV Power Circuit Breaker'
    neta_category       text            NULL,                        -- free text NETA equipment category
    parent_class_id     uuid            NULL,                        -- optional taxonomy nesting
    description         text            NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_asset_classes PRIMARY KEY (asset_class_id),
    CONSTRAINT uq_asset_classes_code UNIQUE (class_code),
    CONSTRAINT fk_asset_classes_parent
        FOREIGN KEY (parent_class_id) REFERENCES neta.asset_classes (asset_class_id)
);

COMMENT ON TABLE neta.asset_classes IS
    'Equipment-type taxonomy for the asset register. Scopes datasheet templates '
    'and PM programs by class. Self-referential for category nesting.';

-- ---------------------------------------------------------------------------
-- neta.assets
--   The equipment under test — PowerDB "test object". The keystone entity: every
--   data sheet, test result, and PM schedule anchors here. Hierarchical so a
--   substation → switchgear → breaker tree can be modeled via parent_asset_id.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.assets (
    asset_id            uuid            NOT NULL DEFAULT gen_random_uuid(),
    asset_tag           text            NOT NULL,                    -- field-unique designation (PowerDB ID)
    name                text            NOT NULL,
    asset_class_id      uuid            NULL,                        -- FK → neta.asset_classes
    parent_asset_id     uuid            NULL,                        -- hierarchy (substation/switchgear/device)
    site_ref            uuid            NULL,                        -- DEFERRED soft FK → org.sites(site_id)
    client_ref          uuid            NULL,                        -- DEFERRED soft FK → org.clients(client_id)
    location_label      text            NULL,                        -- human-readable location within site

    -- Nameplate (PowerDB equipment detail)
    manufacturer        text            NULL,
    model               text            NULL,
    serial_number       text            NULL,
    rated_voltage       text            NULL,                        -- as-marked (e.g. '480V', '15kV')
    rated_current       text            NULL,                        -- as-marked (e.g. '1600A')
    year_manufactured   int             NULL,

    status              neta.asset_status_enum    NOT NULL DEFAULT 'unknown',
    condition           neta.asset_condition_enum NOT NULL DEFAULT 'not_assessed',
    last_tested_at      timestamptz     NULL,                        -- rolled up from datasheets

    -- Optional link back to the PM/work execution domain (kept soft on purpose)
    apparatus_ref       uuid            NULL,                        -- soft link → work apparatus / seam scope

    source              neta.provenance_source_enum NOT NULL DEFAULT 'manual',
    provenance_status   neta.provenance_status_enum NOT NULL DEFAULT 'curated',
    powerdb_source_id   text            NULL,                        -- legacy PowerDB primary key, if imported
    notes               text            NULL,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_assets PRIMARY KEY (asset_id),
    CONSTRAINT uq_assets_tag UNIQUE (asset_tag),
    CONSTRAINT fk_assets_class
        FOREIGN KEY (asset_class_id) REFERENCES neta.asset_classes (asset_class_id),
    CONSTRAINT fk_assets_parent
        FOREIGN KEY (parent_asset_id) REFERENCES neta.assets (asset_id),
    CONSTRAINT ck_assets_year
        CHECK (year_manufactured IS NULL OR year_manufactured BETWEEN 1900 AND 2100)
);

COMMENT ON TABLE neta.assets IS
    'The equipment under test (PowerDB test object) — keystone of the records '
    'domain. site_ref/client_ref/apparatus_ref are deliberately soft UUID links '
    'to org.* / work.* pending the FK-activation chip.';
COMMENT ON COLUMN neta.assets.powerdb_source_id IS
    'Legacy PowerDB record id preserved for round-trip / dedupe during migration.';

-- ===========================================================================
-- PILLAR 2 — NETA DATA SHEETS
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- neta.datasheet_templates
--   The blank NETA test-form definition (PowerDB form/test-card template). The
--   field layout lives in field_schema (JSONB) so the template catalog is data,
--   not code — versioned, and scoped to a standard + asset class.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.datasheet_templates (
    template_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    template_code       text            NOT NULL,                    -- e.g. 'ats_lv_pcb_v1'
    title               text            NOT NULL,
    neta_standard       neta.neta_standard_enum NOT NULL DEFAULT 'ats',
    neta_section        text            NULL,                        -- e.g. '7.6' (NETA section number)
    asset_class_id      uuid            NULL,                        -- FK → neta.asset_classes
    version             int             NOT NULL DEFAULT 1,
    is_current          boolean         NOT NULL DEFAULT true,       -- one current version per template_code
    field_schema        jsonb           NOT NULL DEFAULT '[]'::jsonb,-- ordered field definitions
    description         text            NULL,
    source              neta.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_datasheet_templates PRIMARY KEY (template_id),
    CONSTRAINT uq_datasheet_templates_code_version UNIQUE (template_code, version),
    CONSTRAINT fk_datasheet_templates_class
        FOREIGN KEY (asset_class_id) REFERENCES neta.asset_classes (asset_class_id),
    CONSTRAINT ck_datasheet_templates_version CHECK (version >= 1)
);

COMMENT ON TABLE neta.datasheet_templates IS
    'Versioned NETA data-sheet (test-form) definitions. field_schema holds the '
    'ordered field list as JSONB so the template catalog is data, not code.';
COMMENT ON COLUMN neta.datasheet_templates.field_schema IS
    'JSONB array of field defs: [{key,label,kind,unit,min,max,expected,group,order}]. '
    'Drives both data-sheet rendering and test_results validation.';

-- ---------------------------------------------------------------------------
-- neta.datasheets
--   A filled data-sheet instance: one template applied to one asset for one job
--   visit. Holds the form-level state + rolled-up assessment; the per-field
--   readings live in neta.test_results.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.datasheets (
    datasheet_id        uuid            NOT NULL DEFAULT gen_random_uuid(),
    template_id         uuid            NOT NULL,                    -- FK → neta.datasheet_templates
    asset_id            uuid            NOT NULL,                    -- FK → neta.assets
    project_ref         uuid            NULL,                        -- DEFERRED soft FK → work.projects(project_id)
    work_package_ref    uuid            NULL,                        -- DEFERRED soft FK → work.work_packages
    pm_event_id         uuid            NULL,                        -- set if this sheet fulfilled a PM event (FK added in 004)

    status              neta.datasheet_status_enum  NOT NULL DEFAULT 'draft',
    overall_assessment  neta.assessment_result_enum NOT NULL DEFAULT 'not_tested',
    test_date           date            NULL,
    technician          text            NULL,                        -- free text until identity FK chip
    reviewed_by         text            NULL,
    ambient_temp_c      numeric(5,2)    NULL,
    relative_humidity   numeric(5,2)    NULL,
    test_equipment      text            NULL,                        -- instruments used (PowerDB "test set")
    summary_notes       text            NULL,

    source              neta.provenance_source_enum NOT NULL DEFAULT 'manual',
    provenance_status   neta.provenance_status_enum NOT NULL DEFAULT 'curated',
    powerdb_source_id   text            NULL,

    -- Offline-sync contract (device-authoritative record). See
    -- reference/neta-records/01-OFFLINE-SYNC-ARCHITECTURE.md.
    origin_device       text            NULL,       -- install/device id that captured this sheet
    client_rev          int             NOT NULL DEFAULT 1,  -- LWW guard; bumped on each device edit
    client_captured_at  timestamptz     NULL,       -- when filled on device (vs server created_at)
    synced_at           timestamptz     NULL,       -- when the upload landed server-side

    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_datasheets PRIMARY KEY (datasheet_id),
    CONSTRAINT fk_datasheets_template
        FOREIGN KEY (template_id) REFERENCES neta.datasheet_templates (template_id),
    CONSTRAINT fk_datasheets_asset
        FOREIGN KEY (asset_id) REFERENCES neta.assets (asset_id),
    CONSTRAINT ck_datasheets_humidity
        CHECK (relative_humidity IS NULL OR relative_humidity BETWEEN 0 AND 100)
);

COMMENT ON TABLE neta.datasheets IS
    'A filled NETA data sheet: one template × one asset × one job visit. '
    'Form-level state + rolled-up assessment; readings live in neta.test_results.';

-- ===========================================================================
-- PILLAR 3 — TEST RESULTS
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- neta.test_results
--   One captured reading per row, keyed to a data sheet and the template field
--   it answers. value_kind selects which value column is authoritative. The
--   expected/min/max acceptance window + assessment make pass/fail self-contained.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.test_results (
    result_id           uuid            NOT NULL DEFAULT gen_random_uuid(),
    datasheet_id        uuid            NOT NULL,                    -- FK → neta.datasheets
    field_key           text            NOT NULL,                    -- matches a template field_schema[].key
    field_label         text            NULL,                        -- denormalized for stable history
    test_group          text            NULL,                        -- e.g. 'insulation_resistance', 'contact_resistance'
    sequence_no         int             NULL,                        -- ordering within the sheet

    value_kind          neta.result_value_kind_enum NOT NULL DEFAULT 'numeric',
    value_numeric       numeric         NULL,
    value_text          text            NULL,
    value_boolean       boolean         NULL,
    unit                text            NULL,                        -- e.g. 'MΩ', 'µΩ', 'A', 's'

    -- Acceptance window (PowerDB tolerance band)
    expected_value      numeric         NULL,
    min_acceptable      numeric         NULL,
    max_acceptable      numeric         NULL,
    assessment          neta.assessment_result_enum NOT NULL DEFAULT 'not_tested',

    measured_at         timestamptz     NULL,
    notes               text            NULL,

    -- Offline-sync contract (device-authoritative record).
    origin_device       text            NULL,
    client_rev          int             NOT NULL DEFAULT 1,
    client_captured_at  timestamptz     NULL,
    synced_at           timestamptz     NULL,

    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_test_results PRIMARY KEY (result_id),
    CONSTRAINT fk_test_results_datasheet
        FOREIGN KEY (datasheet_id) REFERENCES neta.datasheets (datasheet_id) ON DELETE CASCADE,
    CONSTRAINT uq_test_results_field UNIQUE (datasheet_id, field_key),
    CONSTRAINT ck_test_results_window
        CHECK (min_acceptable IS NULL OR max_acceptable IS NULL OR max_acceptable >= min_acceptable)
);

COMMENT ON TABLE neta.test_results IS
    'One captured reading per (datasheet, field_key). value_kind selects the '
    'authoritative value column; the acceptance window + assessment make pass/fail '
    'self-contained. Cascades on data-sheet delete.';

-- ===========================================================================
-- PILLAR 4 — PM TRACKING
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- neta.pm_programs
--   A preventive-maintenance program: a recurrence rule (interval + unit) for a
--   class of equipment or a specific asset, typically driven by a NETA MTS
--   maintenance interval. The "what cadence" definition.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.pm_programs (
    pm_program_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    program_code        text            NOT NULL,
    name                text            NOT NULL,
    asset_class_id      uuid            NULL,                        -- FK → neta.asset_classes (class-scoped)
    template_id         uuid            NULL,                        -- FK → datasheet_templates (form to run)
    interval_value      int             NOT NULL,
    interval_unit       neta.pm_interval_unit_enum NOT NULL DEFAULT 'years',
    neta_standard       neta.neta_standard_enum NOT NULL DEFAULT 'mts',
    description         text            NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_pm_programs PRIMARY KEY (pm_program_id),
    CONSTRAINT uq_pm_programs_code UNIQUE (program_code),
    CONSTRAINT fk_pm_programs_class
        FOREIGN KEY (asset_class_id) REFERENCES neta.asset_classes (asset_class_id),
    CONSTRAINT fk_pm_programs_template
        FOREIGN KEY (template_id) REFERENCES neta.datasheet_templates (template_id),
    CONSTRAINT ck_pm_programs_interval CHECK (interval_value > 0)
);

COMMENT ON TABLE neta.pm_programs IS
    'Preventive-maintenance recurrence definition (interval + unit), typically a '
    'NETA MTS cadence, scoped to an asset class and the data-sheet template to run.';

-- ---------------------------------------------------------------------------
-- neta.pm_schedules
--   Enrollment of one asset into one PM program, with the rolling next-due state.
--   The "who is on what cadence and when next" record (one per asset×program).
-- ---------------------------------------------------------------------------
CREATE TABLE neta.pm_schedules (
    pm_schedule_id      uuid            NOT NULL DEFAULT gen_random_uuid(),
    pm_program_id       uuid            NOT NULL,                    -- FK → neta.pm_programs
    asset_id            uuid            NOT NULL,                    -- FK → neta.assets
    last_performed_at   date            NULL,
    next_due_at         date            NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    notes               text            NULL,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_pm_schedules PRIMARY KEY (pm_schedule_id),
    CONSTRAINT fk_pm_schedules_program
        FOREIGN KEY (pm_program_id) REFERENCES neta.pm_programs (pm_program_id),
    CONSTRAINT fk_pm_schedules_asset
        FOREIGN KEY (asset_id) REFERENCES neta.assets (asset_id) ON DELETE CASCADE,
    CONSTRAINT uq_pm_schedules_asset_program UNIQUE (asset_id, pm_program_id)
);

COMMENT ON TABLE neta.pm_schedules IS
    'One asset enrolled in one PM program with rolling next-due state. '
    'next_due_at is recomputed on PM-event completion (later chip).';

-- ---------------------------------------------------------------------------
-- neta.pm_events
--   A single maintenance occurrence against a schedule: planned, due, performed,
--   or skipped. When performed, it links to the data sheet that fulfilled it.
-- ---------------------------------------------------------------------------
CREATE TABLE neta.pm_events (
    pm_event_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    pm_schedule_id      uuid            NOT NULL,                    -- FK → neta.pm_schedules
    asset_id            uuid            NOT NULL,                    -- denormalized FK → neta.assets
    status              neta.pm_event_status_enum NOT NULL DEFAULT 'scheduled',
    scheduled_for       date            NULL,
    performed_at        date            NULL,
    datasheet_id        uuid            NULL,                        -- FK → neta.datasheets (the fulfilling sheet)
    project_ref         uuid            NULL,                        -- DEFERRED soft FK → work.projects
    outcome             neta.assessment_result_enum NULL,
    notes               text            NULL,

    -- Offline-sync contract (device-authoritative when closed in the field).
    origin_device       text            NULL,
    client_rev          int             NOT NULL DEFAULT 1,
    client_captured_at  timestamptz     NULL,
    synced_at           timestamptz     NULL,

    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_pm_events PRIMARY KEY (pm_event_id),
    CONSTRAINT fk_pm_events_schedule
        FOREIGN KEY (pm_schedule_id) REFERENCES neta.pm_schedules (pm_schedule_id) ON DELETE CASCADE,
    CONSTRAINT fk_pm_events_asset
        FOREIGN KEY (asset_id) REFERENCES neta.assets (asset_id),
    CONSTRAINT fk_pm_events_datasheet
        FOREIGN KEY (datasheet_id) REFERENCES neta.datasheets (datasheet_id)
);

COMMENT ON TABLE neta.pm_events IS
    'A single preventive-maintenance occurrence against a schedule. Links to the '
    'data sheet that fulfilled it, closing the asset → PM → datasheet → results loop.';

-- ---------------------------------------------------------------------------
-- Deferred reciprocal FK: neta.datasheets.pm_event_id → neta.pm_events
-- Added now that pm_events exists (datasheets was created first).
-- ---------------------------------------------------------------------------
ALTER TABLE neta.datasheets
    ADD CONSTRAINT fk_datasheets_pm_event
        FOREIGN KEY (pm_event_id) REFERENCES neta.pm_events (pm_event_id);
