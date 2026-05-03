-- =============================================================================
-- TCC Relay — Shared-Infra Schema Substrate
-- Packet: 2026-04-30-tcc-relay-tranche-1
-- Authority: TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md
-- Landing Lane: infra/database/migrations/work/
--
-- Scope invariants preserved by this migration:
--   * Creates only the Packet 003-admitted relay substrate tables.
--   * No data loads, no runtime views, no trigger/function surface, no UI/API.
--   * No deferred enrichment tables such as relay interlocks, impedance,
--     directional, frequency, or voltage-setting overlays.
--   * Source-faithful columns are preserved alongside bounded derived metadata
--     needed by later staging and runtime packets.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Relay-local enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.relay_range_parent_kind_enum AS ENUM (
    'td_section',
    'line_section',
    'iec_curve',
    'swz_curve',
    'bsl_curve',
    'meq_curve',
    'pcd_curve',
    'lrm_curve',
    'rxd_curve',
    'egc_curve',
    'tcp_curve'
);

COMMENT ON TYPE work.relay_range_parent_kind_enum IS
    'Typed discriminator for RelayRanges.ParentID targets, sourced from RangeKey semantics.';

CREATE TYPE work.relay_voltage_restraint_kind_enum AS ENUM (
    'none',
    'multiplier',
    'discrete_curve_set'
);

COMMENT ON TYPE work.relay_voltage_restraint_kind_enum IS
    'Bounded derived metadata describing how voltage restraint modifies relay curve evaluation.';

-- ---------------------------------------------------------------------------
-- tcc_relays
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relays (
    relay_id                 uuid            NOT NULL DEFAULT gen_random_uuid(),
    source_row_id            integer         NOT NULL,
    manufacturer_source_id   integer         NOT NULL,
    relay_type               text            NOT NULL,
    relay_note               text            NULL,
    is_multifunction         boolean         NOT NULL DEFAULT false,
    dc_offset_filter_enabled boolean         NOT NULL DEFAULT false,
    relay_class_code         integer         NOT NULL,
    relay_construction_code  integer         NOT NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'Relays',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relays PRIMARY KEY (relay_id),
    CONSTRAINT uq_tcc_relays_source_row_id UNIQUE (source_row_id)
);

COMMENT ON TABLE work.tcc_relays IS
    'Canonical relay catalog root. Source-faithful row mirror of Relays.csv with shared-infra keys and provenance.';
COMMENT ON COLUMN work.tcc_relays.manufacturer_source_id IS
    'Source Manufacturers.ID value preserved verbatim until a later shared reference surface is formally wired.';

-- ---------------------------------------------------------------------------
-- tcc_relay_devices
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_devices (
    relay_device_id          uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_id                 uuid            NOT NULL,
    relay_source_id          integer         NOT NULL,
    source_row_id            integer         NOT NULL,
    device_function          text            NOT NULL,
    ordinal                  integer         NOT NULL,
    standard_code            integer         NOT NULL,
    dftype_code              integer         NOT NULL,
    use_sst                  boolean         NOT NULL DEFAULT false,
    sst_manufacturer         text            NULL,
    sst_type                 text            NULL,
    sst_style                text            NULL,
    element_codes            text[]          NULL,
    curve_standard_code      text            NULL,
    parse_status             text            NULL,
    stage_count              integer         NULL,
    device_annotation        text            NULL,
    pickup_unit              text            NULL,
    voltage_restraint_kind   work.relay_voltage_restraint_kind_enum NOT NULL DEFAULT 'none',
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelayDevices',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_devices PRIMARY KEY (relay_device_id),
    CONSTRAINT fk_tcc_relay_devices_relay
        FOREIGN KEY (relay_id) REFERENCES work.tcc_relays (relay_id),
    CONSTRAINT uq_tcc_relay_devices_source_row_id UNIQUE (source_row_id),
    CONSTRAINT ck_tcc_relay_devices_stage_count
        CHECK (stage_count IS NULL OR stage_count >= 0)
);

COMMENT ON TABLE work.tcc_relay_devices IS
    'Relay device-function rows with source DeviceFunction preserved and bounded derived metadata added per Packet 003 D-D.';
COMMENT ON COLUMN work.tcc_relay_devices.device_function IS
    'Source fidelity surface from RelayDevices.DeviceFunction. Never normalize this away in the base table.';

-- ---------------------------------------------------------------------------
-- tcc_relay_line_sections
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_line_sections (
    relay_line_section_id    uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_device_id          uuid            NOT NULL,
    relay_device_source_id   integer         NOT NULL,
    source_row_id            integer         NOT NULL,
    section_number           integer         NOT NULL,
    section_name             text            NOT NULL,
    pickup                   numeric(20,6)   NULL,
    secondary_i_code         integer         NOT NULL,
    amps_calc_mode           integer         NOT NULL,
    use_toc_multiplier       boolean         NOT NULL DEFAULT false,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelayLineSection',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_line_sections PRIMARY KEY (relay_line_section_id),
    CONSTRAINT fk_tcc_relay_line_sections_device
        FOREIGN KEY (relay_device_id) REFERENCES work.tcc_relay_devices (relay_device_id),
    CONSTRAINT uq_tcc_relay_line_sections_source_row_id UNIQUE (source_row_id)
);

COMMENT ON TABLE work.tcc_relay_line_sections IS
    'Relay pickup and line-setting sections. RelayLineSection.Amps is preserved as amps_calc_mode semantics, not collapsed to boolean.';
COMMENT ON COLUMN work.tcc_relay_line_sections.amps_calc_mode IS
    'Verbatim RelayLineSection.Amps code preserved for later runtime interpretation.';

-- ---------------------------------------------------------------------------
-- tcc_relay_td_sections
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_td_sections (
    relay_td_section_id      uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_device_id          uuid            NOT NULL,
    relay_device_source_id   integer         NOT NULL,
    source_row_id            integer         NOT NULL,
    section_name             text            NOT NULL,
    model_code               integer         NOT NULL,
    type_code                integer         NOT NULL,
    allow_trip_lt_st_delay   boolean         NOT NULL DEFAULT false,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelayTDSection',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_td_sections PRIMARY KEY (relay_td_section_id),
    CONSTRAINT fk_tcc_relay_td_sections_device
        FOREIGN KEY (relay_device_id) REFERENCES work.tcc_relay_devices (relay_device_id),
    CONSTRAINT uq_tcc_relay_td_sections_source_row_id UNIQUE (source_row_id)
);

COMMENT ON TABLE work.tcc_relay_td_sections IS
    'Time-dial section rows. Model code is the canonical family-code authority for later curve dispatch.';

-- ---------------------------------------------------------------------------
-- tcc_relay_ranges
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_ranges (
    relay_range_id           uuid            NOT NULL DEFAULT gen_random_uuid(),
    source_row_id            integer         NOT NULL,
    source_parent_id         integer         NOT NULL,
    parent_kind              work.relay_range_parent_kind_enum NOT NULL,
    line_section_source_id   integer         NULL,
    td_section_source_id     integer         NULL,
    curve_parent_source_id   integer         NULL,
    aux_key                  integer         NOT NULL,
    ordinal                  integer         NOT NULL,
    min_value                numeric(20,6)   NULL,
    max_value                numeric(20,6)   NULL,
    step_value               numeric(20,6)   NULL,
    relative_unit_code       integer         NOT NULL,
    use_range                boolean         NOT NULL DEFAULT false,
    source_range_key         integer         NOT NULL,
    scales_with_time_multiplier boolean      NOT NULL DEFAULT false,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelayRanges',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_ranges PRIMARY KEY (relay_range_id),
    CONSTRAINT uq_tcc_relay_ranges_source_row_id UNIQUE (source_row_id),
    CONSTRAINT ck_tcc_relay_ranges_parent_source_alignment
        CHECK (
            (parent_kind = 'line_section' AND line_section_source_id IS NOT NULL AND td_section_source_id IS NULL AND curve_parent_source_id IS NULL AND source_parent_id = line_section_source_id)
            OR
            (parent_kind = 'td_section' AND td_section_source_id IS NOT NULL AND line_section_source_id IS NULL AND curve_parent_source_id IS NULL AND source_parent_id = td_section_source_id)
            OR
            (parent_kind NOT IN ('line_section', 'td_section') AND curve_parent_source_id IS NOT NULL AND line_section_source_id IS NULL AND td_section_source_id IS NULL AND source_parent_id = curve_parent_source_id)
        )
);

COMMENT ON TABLE work.tcc_relay_ranges IS
    'Polymorphic setting ranges. Parent kind is derived from RangeKey while preserving the original parent source id and relative unit code, including the post-2000 td_section branch.';
COMMENT ON COLUMN work.tcc_relay_ranges.relative_unit_code IS
    'Verbatim RelUnit code preserved even where current runtime use is binary.';

-- ---------------------------------------------------------------------------
-- tcc_relay_discrete_values
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_discrete_values (
    relay_discrete_value_id  uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_range_id           uuid            NOT NULL,
    relay_range_source_id    integer         NOT NULL,
    discrete_value           numeric(20,6)   NULL,
    discrete_description     text            NOT NULL DEFAULT '',
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelayDiscreteValues',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_discrete_values PRIMARY KEY (relay_discrete_value_id),
    CONSTRAINT fk_tcc_relay_discrete_values_range
        FOREIGN KEY (relay_range_id) REFERENCES work.tcc_relay_ranges (relay_range_id)
);

COMMENT ON TABLE work.tcc_relay_discrete_values IS
    'Discrete setting-value expansions per range. Source table has no row id, so the natural key is preserved instead.';

-- ---------------------------------------------------------------------------
-- Typed family parent surfaces
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_curves_iec (
    relay_curve_iec_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2IEC',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_iec PRIMARY KEY (relay_curve_iec_id),
    CONSTRAINT fk_tcc_relay_curves_iec_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_iec_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_swz (
    relay_curve_swz_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2SWZ',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_swz PRIMARY KEY (relay_curve_swz_id),
    CONSTRAINT fk_tcc_relay_curves_swz_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_swz_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_bsl (
    relay_curve_bsl_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2BSL',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_bsl PRIMARY KEY (relay_curve_bsl_id),
    CONSTRAINT fk_tcc_relay_curves_bsl_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_bsl_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_meq (
    relay_curve_meq_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2MEQ',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_meq PRIMARY KEY (relay_curve_meq_id),
    CONSTRAINT fk_tcc_relay_curves_meq_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_meq_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_pcd (
    relay_curve_pcd_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2PCD',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_pcd PRIMARY KEY (relay_curve_pcd_id),
    CONSTRAINT fk_tcc_relay_curves_pcd_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_pcd_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_lrm (
    relay_curve_lrm_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    lr_unit_code             integer         NOT NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2LRM',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_lrm PRIMARY KEY (relay_curve_lrm_id),
    CONSTRAINT fk_tcc_relay_curves_lrm_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_lrm_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_rxd (
    relay_curve_rxd_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2RXD',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_rxd PRIMARY KEY (relay_curve_rxd_id),
    CONSTRAINT fk_tcc_relay_curves_rxd_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_rxd_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_egc (
    relay_curve_egc_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    min_pickup               numeric(20,6)   NULL,
    max_pickup               numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2EGC',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_egc PRIMARY KEY (relay_curve_egc_id),
    CONSTRAINT fk_tcc_relay_curves_egc_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_egc_source_row_id UNIQUE (source_row_id)
);

CREATE TABLE work.tcc_relay_curves_tcp (
    relay_curve_tcp_id       uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_td_section_id      uuid            NOT NULL,
    relay_td_section_source_id integer       NOT NULL,
    source_row_id            integer         NOT NULL,
    curve_name               text            NOT NULL,
    tcc_number               text            NULL,
    ordinal                  integer         NOT NULL,
    is_discrete              boolean         NOT NULL DEFAULT false,
    step_size                numeric(20,6)   NULL,
    horizontal_amps_code     integer         NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2TCP',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curves_tcp PRIMARY KEY (relay_curve_tcp_id),
    CONSTRAINT fk_tcc_relay_curves_tcp_td_section
        FOREIGN KEY (relay_td_section_id) REFERENCES work.tcc_relay_td_sections (relay_td_section_id),
    CONSTRAINT uq_tcc_relay_curves_tcp_source_row_id UNIQUE (source_row_id)
);

COMMENT ON TABLE work.tcc_relay_curves_tcp IS
    'TCP family parent rows preserve the structurally distinct discrete matrix metadata before normalization into point rows.';

-- ---------------------------------------------------------------------------
-- Typed family row surfaces
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_curve_rows_iec (
    relay_curve_row_iec_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_iec_id       uuid            NOT NULL,
    relay_curve_iec_source_id integer        NOT NULL,
    curve_name               text            NOT NULL,
    ordinal                  integer         NOT NULL,
    v_k                      numeric(20,6)   NULL,
    v_e                      numeric(20,6)   NULL,
    dt_after                 numeric(20,6)   NULL,
    dt_min_time              numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2IECCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_rows_iec PRIMARY KEY (relay_curve_row_iec_id),
    CONSTRAINT fk_tcc_relay_curve_rows_iec_parent
        FOREIGN KEY (relay_curve_iec_id) REFERENCES work.tcc_relay_curves_iec (relay_curve_iec_id),
    CONSTRAINT uq_tcc_relay_curve_rows_iec_parent_ordinal
        UNIQUE (relay_curve_iec_id, ordinal)
);

CREATE TABLE work.tcc_relay_curve_rows_swz (
    relay_curve_row_swz_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_swz_id       uuid            NOT NULL,
    relay_curve_swz_source_id integer        NOT NULL,
    curve_name               text            NOT NULL,
    ordinal                  integer         NOT NULL,
    v_a                      numeric(20,6)   NULL,
    v_b                      numeric(20,6)   NULL,
    v_e                      numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2SWZCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_rows_swz PRIMARY KEY (relay_curve_row_swz_id),
    CONSTRAINT fk_tcc_relay_curve_rows_swz_parent
        FOREIGN KEY (relay_curve_swz_id) REFERENCES work.tcc_relay_curves_swz (relay_curve_swz_id),
    CONSTRAINT uq_tcc_relay_curve_rows_swz_parent_ordinal
        UNIQUE (relay_curve_swz_id, ordinal)
);

CREATE TABLE work.tcc_relay_curve_rows_bsl (
    relay_curve_row_bsl_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_bsl_id       uuid            NOT NULL,
    relay_curve_bsl_source_id integer        NOT NULL,
    curve_name               text            NOT NULL,
    ordinal                  integer         NOT NULL,
    v_a                      numeric(20,6)   NULL,
    v_b                      numeric(20,6)   NULL,
    v_c                      numeric(20,6)   NULL,
    v_d                      numeric(20,6)   NULL,
    v_n                      numeric(20,6)   NULL,
    v_k                      numeric(20,6)   NULL,
    v_r                      numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2BSLCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_rows_bsl PRIMARY KEY (relay_curve_row_bsl_id),
    CONSTRAINT fk_tcc_relay_curve_rows_bsl_parent
        FOREIGN KEY (relay_curve_bsl_id) REFERENCES work.tcc_relay_curves_bsl (relay_curve_bsl_id),
    CONSTRAINT uq_tcc_relay_curve_rows_bsl_parent_ordinal
        UNIQUE (relay_curve_bsl_id, ordinal)
);

CREATE TABLE work.tcc_relay_curve_rows_meq (
    relay_curve_row_meq_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_meq_id       uuid            NOT NULL,
    relay_curve_meq_source_id integer        NOT NULL,
    curve_name               text            NOT NULL,
    ordinal                  integer         NOT NULL,
    v_a                      numeric(20,6)   NULL,
    v_b                      numeric(20,6)   NULL,
    v_c                      numeric(20,6)   NULL,
    v_d                      numeric(20,6)   NULL,
    v_e                      numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2MEQCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_rows_meq PRIMARY KEY (relay_curve_row_meq_id),
    CONSTRAINT fk_tcc_relay_curve_rows_meq_parent
        FOREIGN KEY (relay_curve_meq_id) REFERENCES work.tcc_relay_curves_meq (relay_curve_meq_id),
    CONSTRAINT uq_tcc_relay_curve_rows_meq_parent_ordinal
        UNIQUE (relay_curve_meq_id, ordinal)
);

CREATE TABLE work.tcc_relay_curve_rows_pcd (
    relay_curve_row_pcd_id   uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_pcd_id       uuid            NOT NULL,
    relay_curve_pcd_source_id integer        NOT NULL,
    curve_name               text            NOT NULL,
    ordinal                  integer         NOT NULL,
    v_a                      numeric(20,6)   NULL,
    v_b                      numeric(20,6)   NULL,
    v_c                      numeric(20,6)   NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2PCDCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_rows_pcd PRIMARY KEY (relay_curve_row_pcd_id),
    CONSTRAINT fk_tcc_relay_curve_rows_pcd_parent
        FOREIGN KEY (relay_curve_pcd_id) REFERENCES work.tcc_relay_curves_pcd (relay_curve_pcd_id),
    CONSTRAINT uq_tcc_relay_curve_rows_pcd_parent_ordinal
        UNIQUE (relay_curve_pcd_id, ordinal)
);

-- ---------------------------------------------------------------------------
-- Normalized TCP points
-- ---------------------------------------------------------------------------

CREATE TABLE work.tcc_relay_curve_points_tcp (
    relay_curve_point_tcp_id uuid            NOT NULL DEFAULT gen_random_uuid(),
    relay_curve_tcp_id       uuid            NOT NULL,
    relay_curve_tcp_source_id integer        NOT NULL,
    time_dial                numeric(20,6)   NOT NULL,
    td_desc                  text            NULL,
    current_index            integer         NOT NULL,
    current_value            numeric(20,6)   NOT NULL,
    trip_time_seconds        numeric(20,6)   NOT NULL,
    source_time_dial         numeric(20,6)   NOT NULL,
    source_ordinal           integer         NOT NULL,
    source_current_index     integer         NOT NULL,
    source_snapshot_id       text            NULL,
    source_table_name        text            NOT NULL DEFAULT 'RelaySec2TCPCurves',
    created_from_source      work.provenance_source_enum NOT NULL DEFAULT 'migration',
    provenance_status        work.provenance_status_enum NOT NULL DEFAULT 'provisional',
    created_at               timestamptz     NOT NULL DEFAULT now(),
    updated_at               timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tcc_relay_curve_points_tcp PRIMARY KEY (relay_curve_point_tcp_id),
    CONSTRAINT fk_tcc_relay_curve_points_tcp_parent
        FOREIGN KEY (relay_curve_tcp_id) REFERENCES work.tcc_relay_curves_tcp (relay_curve_tcp_id),
    CONSTRAINT uq_tcc_relay_curve_points_tcp_parent_ordinal_index
        UNIQUE (relay_curve_tcp_id, source_ordinal, current_index),
    CONSTRAINT ck_tcc_relay_curve_points_tcp_current_index
        CHECK (current_index BETWEEN 1 AND 25),
    CONSTRAINT ck_tcc_relay_curve_points_tcp_source_current_index
        CHECK (source_current_index BETWEEN 1 AND 25)
);

COMMENT ON TABLE work.tcc_relay_curve_points_tcp IS
    'Normalized TCP points keyed by (tcp parent, time dial, current index). The source -100 current-axis sentinel does not survive here.';