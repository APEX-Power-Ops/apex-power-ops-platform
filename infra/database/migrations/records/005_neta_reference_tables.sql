-- =============================================================================
-- Records Domain — NETA Reference Layer  (Chip 2a)
-- Packet: 2026-06-15-records-2a
-- Authority: reference/records/00-MASTER-INDEX.md §5 (NETA seed for field_schema),
--            02-LEGACY-BASELINE.md §2 (NETA-aligned equipment categories)
-- Landing Lane: infra/database/migrations/records/
-- Requires: 001_records_enums.sql (records schema + records.neta_standard_enum
--           + records.provenance_source_enum)
--
-- The authoritative NETA equipment / procedure / test-item / acceptance-table
-- reference, loaded accurately from the NETA Master Equipment Table
-- (ANSI/NETA ATS-2025 + MTS-2023). Pure reference data — reusable across every
-- equipment class, and the acceptance-value BASIS for the field-trust law.
--
-- Datasheets (records.form_templates) REFERENCE and FILTER this layer (Chip 2b):
-- a form field carries a neta_ref to its item; the item text + acceptance live
-- here, once, and are never copied onto a sheet. The NETA-vs-common-datasheet
-- divergence is then a query (neta_test_items LEFT JOIN field refs), not a manual
-- matrix.
-- =============================================================================

-- The four parallel NETA structures published per procedure.
CREATE TYPE records.neta_test_category_enum AS ENUM (
    'visual_mechanical',      -- A. Visual and Mechanical Inspection (numbered steps)
    'electrical',             -- B. Electrical Tests (numbered steps)
    'test_value_visual',      -- C.1 Test Values — Visual (acceptance criteria)
    'test_value_electrical'   -- C.2 Test Values — Electrical (acceptance criteria)
);

COMMENT ON TYPE records.neta_test_category_enum IS
    'Which of the four parallel NETA item structures a test item belongs to '
    '(the A/B inspection+test steps and the C test-value acceptance criteria).';

-- ---------------------------------------------------------------------------
-- records.neta_procedures
--   One row per NETA section (e.g. 7.6.1.2). The equipment test procedure with
--   its ATS/MTS coverage flags and the acceptance tables it references.
-- ---------------------------------------------------------------------------
CREATE TABLE records.neta_procedures (
    neta_procedure_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    section             text            NOT NULL,            -- e.g. '7.6.1.2'
    name                text            NOT NULL,            -- e.g. 'Circuit Breakers, Low-Voltage, Power'
    category            text            NULL,                -- e.g. 'circuit_breakers'
    category_name       text            NULL,
    status              text            NULL,                -- master-table status (e.g. 'complete')
    has_ats             boolean         NOT NULL DEFAULT false,
    has_mts             boolean         NOT NULL DEFAULT false,
    ats_table_refs      jsonb           NOT NULL DEFAULT '[]'::jsonb,  -- table_numbers the ATS procedure cites
    mts_table_refs      jsonb           NOT NULL DEFAULT '[]'::jsonb,  -- table_numbers the MTS procedure cites
    notes               jsonb           NULL,
    source              records.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_neta_procedures PRIMARY KEY (neta_procedure_id),
    CONSTRAINT uq_neta_procedures_section UNIQUE (section)
);

COMMENT ON TABLE records.neta_procedures IS
    'NETA equipment test procedures (ANSI/NETA ATS-2025 + MTS-2023), one row per '
    'section. The authoritative reference that datasheets filter against (Chip 2b).';

-- ---------------------------------------------------------------------------
-- records.neta_test_items
--   The numbered NETA items under each procedure, split by standard (ATS/MTS)
--   and category (inspection / electrical / test-values).
-- ---------------------------------------------------------------------------
CREATE TABLE records.neta_test_items (
    neta_test_item_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    neta_procedure_id   uuid            NOT NULL,
    standard            records.neta_standard_enum NOT NULL,           -- ats | mts
    category            records.neta_test_category_enum NOT NULL,
    item_number         text            NOT NULL,            -- NETA item number, e.g. '1', '10'
    description         text            NOT NULL,
    is_optional         boolean         NOT NULL DEFAULT false,
    sort_order          int             NOT NULL DEFAULT 0,
    created_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_neta_test_items PRIMARY KEY (neta_test_item_id),
    CONSTRAINT fk_neta_test_items_procedure
        FOREIGN KEY (neta_procedure_id) REFERENCES records.neta_procedures (neta_procedure_id) ON DELETE CASCADE,
    CONSTRAINT uq_neta_test_items UNIQUE (neta_procedure_id, standard, category, item_number)
);

COMMENT ON TABLE records.neta_test_items IS
    'Individual NETA test items per procedure × standard × category — the numbered '
    'inspection/electrical steps and their acceptance-criteria test values.';

-- ---------------------------------------------------------------------------
-- records.neta_tables
--   The NETA standard acceptance/reference tables (Table 100.x), deduped
--   globally. headers + rows carry the published acceptance values.
-- ---------------------------------------------------------------------------
CREATE TABLE records.neta_tables (
    neta_table_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    table_number        text            NOT NULL,            -- e.g. '100.1', '100.12.1'
    title               text            NULL,
    status              text            NULL,
    parent_table_number text            NULL,                -- e.g. '100.12.1' -> '100.12'
    headers             jsonb           NOT NULL DEFAULT '[]'::jsonb,
    rows                jsonb           NOT NULL DEFAULT '[]'::jsonb,
    created_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_neta_tables PRIMARY KEY (neta_table_id),
    CONSTRAINT uq_neta_tables_number UNIQUE (table_number)
);

COMMENT ON TABLE records.neta_tables IS
    'NETA standard acceptance/reference tables (Table 100.x), deduped globally. '
    'The acceptance-value source for seeding datasheet field acceptance windows '
    '(field-trust basis — never fabricated).';

CREATE INDEX ix_neta_test_items_procedure ON records.neta_test_items (neta_procedure_id);
CREATE INDEX ix_neta_test_items_lookup    ON records.neta_test_items (standard, category);
CREATE INDEX ix_neta_tables_parent        ON records.neta_tables (parent_table_number);
