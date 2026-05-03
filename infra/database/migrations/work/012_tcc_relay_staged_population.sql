-- =============================================================================
-- TCC Relay — Staged Population And Provenance Replay
-- Packet: 2026-04-30-tcc-relay-tranche-2
-- Authority: TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md
-- Landing Lane: infra/database/migrations/work/
--
-- Scope invariants preserved by this migration:
--   * Replays one immutable relay snapshot into the existing shared-infra relay substrate.
--   * Preserves source snapshot ids, source row ids, and family-specific TCP provenance.
--   * Rejects orphan RelayDevices rows instead of silently synthesizing parent relays.
--   * Keeps calc-engine, API, browser, triggers, views, and deferred enrichments closed.
--
-- Execution note:
--   Run this file from infra/database/migrations/work/ so the relative snapshot
--   paths below resolve correctly.
-- =============================================================================

\set ON_ERROR_STOP on
\set relay_snapshot_id 'stdlib-relay-snapshot-001'

-- ---------------------------------------------------------------------------
-- Compatibility correction for already-applied Tranche 1 databases
-- ---------------------------------------------------------------------------

ALTER TYPE work.relay_range_parent_kind_enum ADD VALUE IF NOT EXISTS 'td_section';

ALTER TABLE work.tcc_relay_ranges
    ADD COLUMN IF NOT EXISTS td_section_source_id integer NULL;

COMMENT ON TABLE work.tcc_relay_ranges IS
    'Polymorphic setting ranges. Parent kind is derived from RangeKey while preserving the original parent source id and relative unit code, including the post-2000 td_section branch.';

ALTER TABLE work.tcc_relay_curves_tcp
    ALTER COLUMN horizontal_amps_code DROP NOT NULL;

DO $$
DECLARE
    relay_column record;
BEGIN
    FOR relay_column IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'work'
          AND table_name LIKE 'tcc_relay%'
          AND data_type = 'numeric'
          AND numeric_precision = 14
          AND numeric_scale = 6
    LOOP
        EXECUTE format(
            'ALTER TABLE work.%I ALTER COLUMN %I TYPE numeric(20,6)',
            relay_column.table_name,
            relay_column.column_name
        );
    END LOOP;
END $$;

ALTER TABLE work.tcc_relay_ranges
    DROP CONSTRAINT IF EXISTS ck_tcc_relay_ranges_parent_source_alignment;

ALTER TABLE work.tcc_relay_ranges
    ADD CONSTRAINT ck_tcc_relay_ranges_parent_source_alignment
    CHECK (
        (parent_kind = 'line_section' AND line_section_source_id IS NOT NULL AND td_section_source_id IS NULL AND curve_parent_source_id IS NULL AND source_parent_id = line_section_source_id)
        OR
        (parent_kind = 'td_section' AND td_section_source_id IS NOT NULL AND line_section_source_id IS NULL AND curve_parent_source_id IS NULL AND source_parent_id = td_section_source_id)
        OR
        (parent_kind NOT IN ('line_section', 'td_section') AND curve_parent_source_id IS NOT NULL AND line_section_source_id IS NULL AND td_section_source_id IS NULL AND source_parent_id = curve_parent_source_id)
    );

ALTER TABLE work.tcc_relay_curve_points_tcp
    DROP CONSTRAINT IF EXISTS uq_tcc_relay_curve_points_tcp_parent_dial_index;

ALTER TABLE work.tcc_relay_curve_points_tcp
    DROP CONSTRAINT IF EXISTS uq_tcc_relay_curve_points_tcp_parent_ordinal_index;

ALTER TABLE work.tcc_relay_curve_points_tcp
    ADD CONSTRAINT uq_tcc_relay_curve_points_tcp_parent_ordinal_index
    UNIQUE (relay_curve_tcp_id, source_ordinal, current_index);

-- ---------------------------------------------------------------------------
-- Replay reset: this file is intentionally rerunnable from the same immutable
-- snapshot, so it truncates only the relay slice before reloading.
-- ---------------------------------------------------------------------------

TRUNCATE TABLE
    work.tcc_relay_curve_points_tcp,
    work.tcc_relay_curve_rows_pcd,
    work.tcc_relay_curve_rows_meq,
    work.tcc_relay_curve_rows_bsl,
    work.tcc_relay_curve_rows_swz,
    work.tcc_relay_curve_rows_iec,
    work.tcc_relay_discrete_values,
    work.tcc_relay_ranges,
    work.tcc_relay_curves_tcp,
    work.tcc_relay_curves_egc,
    work.tcc_relay_curves_rxd,
    work.tcc_relay_curves_lrm,
    work.tcc_relay_curves_pcd,
    work.tcc_relay_curves_meq,
    work.tcc_relay_curves_bsl,
    work.tcc_relay_curves_swz,
    work.tcc_relay_curves_iec,
    work.tcc_relay_td_sections,
    work.tcc_relay_line_sections,
    work.tcc_relay_devices,
    work.tcc_relays;

-- ---------------------------------------------------------------------------
-- Snapshot staging tables
-- ---------------------------------------------------------------------------

CREATE TEMP TABLE relay_stage_manufacturers (
    source_row_id          integer,
    manufacturer_name      text
);

CREATE TEMP TABLE relay_stage_relays (
    source_row_id              integer,
    manufacturer_source_id     integer,
    relay_type                 text,
    relay_note                 text,
    is_multifunction_flag      integer,
    dc_offset_filter_flag      integer,
    relay_class_code           integer,
    relay_construction_code    integer
);

CREATE TEMP TABLE relay_stage_devices (
    source_row_id              integer,
    relay_source_id            integer,
    device_function            text,
    ordinal                    integer,
    standard_code              integer,
    dftype_code                integer,
    use_sst_flag               integer,
    sst_manufacturer           text,
    sst_type                   text,
    sst_style                  text
);

CREATE TEMP TABLE relay_stage_line_sections (
    source_row_id              integer,
    relay_device_source_id     integer,
    section_number             integer,
    section_name               text,
    pickup                     numeric(20,6),
    secondary_i_code           integer,
    amps_calc_mode             integer,
    use_toc_multiplier_flag    integer
);

CREATE TEMP TABLE relay_stage_td_sections (
    source_row_id                  integer,
    relay_device_source_id         integer,
    section_name                   text,
    model_code                     integer,
    type_code                      integer,
    allow_trip_lt_st_delay_flag    integer
);

CREATE TEMP TABLE relay_stage_ranges (
    source_row_id                  integer,
    source_parent_id               integer,
    aux_key                        integer,
    ordinal                        integer,
    min_value                      numeric(20,6),
    max_value                      numeric(20,6),
    step_value                     numeric(20,6),
    relative_unit_code             integer,
    use_range_flag                 integer,
    source_range_key               integer,
    scales_with_time_multiplier_flag integer
);

CREATE TEMP TABLE relay_stage_discrete_values (
    relay_range_source_id      integer,
    discrete_value             numeric(20,6),
    discrete_description       text
);

CREATE TEMP TABLE relay_stage_curves_iec (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curve_rows_iec (
    parent_source_id           integer,
    curve_name                 text,
    ordinal                    integer,
    v_k                        numeric(20,6),
    v_e                        numeric(20,6),
    dt_after                   numeric(20,6),
    dt_min_time                numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_swz (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curve_rows_swz (
    parent_source_id           integer,
    curve_name                 text,
    ordinal                    integer,
    v_a                        numeric(20,6),
    v_b                        numeric(20,6),
    v_e                        numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_bsl (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curve_rows_bsl (
    parent_source_id           integer,
    curve_name                 text,
    ordinal                    integer,
    v_a                        numeric(20,6),
    v_b                        numeric(20,6),
    v_c                        numeric(20,6),
    v_d                        numeric(20,6),
    v_n                        numeric(20,6),
    v_k                        numeric(20,6),
    v_r                        numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_meq (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curve_rows_meq (
    parent_source_id           integer,
    curve_name                 text,
    ordinal                    integer,
    v_a                        numeric(20,6),
    v_b                        numeric(20,6),
    v_c                        numeric(20,6),
    v_d                        numeric(20,6),
    v_e                        numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_pcd (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curve_rows_pcd (
    parent_source_id           integer,
    curve_name                 text,
    ordinal                    integer,
    v_a                        numeric(20,6),
    v_b                        numeric(20,6),
    v_c                        numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_lrm (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6),
    lr_unit_code               integer
);

CREATE TEMP TABLE relay_stage_curves_rxd (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_egc (
    source_row_id              integer,
    relay_td_section_source_id integer,
    min_pickup                 numeric(20,6),
    max_pickup                 numeric(20,6)
);

CREATE TEMP TABLE relay_stage_curves_tcp (
    source_row_id              integer,
    relay_td_section_source_id integer,
    curve_name                 text,
    tcc_number                 text,
    ordinal                    integer,
    is_discrete_flag           integer,
    step_size                  numeric(20,6),
    horizontal_amps_code       integer
);

CREATE TEMP TABLE relay_stage_curve_rows_tcp (
    parent_source_id           integer,
    time_dial                  numeric(20,6),
    td_desc                    text,
    source_ordinal             integer,
    v1                         numeric(20,6),
    v2                         numeric(20,6),
    v3                         numeric(20,6),
    v4                         numeric(20,6),
    v5                         numeric(20,6),
    v6                         numeric(20,6),
    v7                         numeric(20,6),
    v8                         numeric(20,6),
    v9                         numeric(20,6),
    v10                        numeric(20,6),
    v11                        numeric(20,6),
    v12                        numeric(20,6),
    v13                        numeric(20,6),
    v14                        numeric(20,6),
    v15                        numeric(20,6),
    v16                        numeric(20,6),
    v17                        numeric(20,6),
    v18                        numeric(20,6),
    v19                        numeric(20,6),
    v20                        numeric(20,6),
    v21                        numeric(20,6),
    v22                        numeric(20,6),
    v23                        numeric(20,6),
    v24                        numeric(20,6),
    v25                        numeric(20,6)
);

-- ---------------------------------------------------------------------------
-- Snapshot copy-in
-- ---------------------------------------------------------------------------

\copy relay_stage_manufacturers FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/Manufacturers.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_relays FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/Relays.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_devices FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelayDevices.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_line_sections FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelayLineSection.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_td_sections FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelayTDSection.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_ranges FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelayRanges.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_discrete_values FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelayDiscreteValues.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_iec FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2IEC.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_iec FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2IECCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_swz FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2SWZ.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_swz FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2SWZCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_bsl FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2BSL.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_bsl FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2BSLCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_meq FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2MEQ.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_meq FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2MEQCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_pcd FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2PCD.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_pcd FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2PCDCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_lrm FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2LRM.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_rxd FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2RXD.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_egc FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2EGC.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curves_tcp FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2TCP.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy relay_stage_curve_rows_tcp FROM '../../source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/RelaySec2TCPCurves.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- ---------------------------------------------------------------------------
-- Core root and section replay
-- ---------------------------------------------------------------------------

INSERT INTO work.tcc_relays (
    source_row_id,
    manufacturer_source_id,
    relay_type,
    relay_note,
    is_multifunction,
    dc_offset_filter_enabled,
    relay_class_code,
    relay_construction_code,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    source_row_id,
    manufacturer_source_id,
    relay_type,
    relay_note,
    COALESCE(is_multifunction_flag, 0) <> 0,
    COALESCE(dc_offset_filter_flag, 0) <> 0,
    relay_class_code,
    relay_construction_code,
    :'relay_snapshot_id',
    'Relays',
    'bulk_upload',
    'imported'
FROM relay_stage_relays;

INSERT INTO work.tcc_relay_devices (
    relay_id,
    relay_source_id,
    source_row_id,
    device_function,
    ordinal,
    standard_code,
    dftype_code,
    use_sst,
    sst_manufacturer,
    sst_type,
    sst_style,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    relay.relay_id,
    stage.relay_source_id,
    stage.source_row_id,
    stage.device_function,
    stage.ordinal,
    stage.standard_code,
    stage.dftype_code,
    COALESCE(stage.use_sst_flag, 0) <> 0,
    NULLIF(stage.sst_manufacturer, ''),
    NULLIF(stage.sst_type, ''),
    NULLIF(stage.sst_style, ''),
    :'relay_snapshot_id',
    'RelayDevices',
    'bulk_upload',
    'imported'
FROM relay_stage_devices stage
JOIN work.tcc_relays relay
  ON relay.source_row_id = stage.relay_source_id;

INSERT INTO work.tcc_relay_line_sections (
    relay_device_id,
    relay_device_source_id,
    source_row_id,
    section_number,
    section_name,
    pickup,
    secondary_i_code,
    amps_calc_mode,
    use_toc_multiplier,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    device.relay_device_id,
    stage.relay_device_source_id,
    stage.source_row_id,
    stage.section_number,
    stage.section_name,
    stage.pickup,
    stage.secondary_i_code,
    stage.amps_calc_mode,
    COALESCE(stage.use_toc_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayLineSection',
    'bulk_upload',
    'imported'
FROM relay_stage_line_sections stage
JOIN work.tcc_relay_devices device
  ON device.source_row_id = stage.relay_device_source_id;

INSERT INTO work.tcc_relay_td_sections (
    relay_device_id,
    relay_device_source_id,
    source_row_id,
    section_name,
    model_code,
    type_code,
    allow_trip_lt_st_delay,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    device.relay_device_id,
    stage.relay_device_source_id,
    stage.source_row_id,
    stage.section_name,
    stage.model_code,
    stage.type_code,
    COALESCE(stage.allow_trip_lt_st_delay_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayTDSection',
    'bulk_upload',
    'imported'
FROM relay_stage_td_sections stage
JOIN work.tcc_relay_devices device
  ON device.source_row_id = stage.relay_device_source_id;

-- ---------------------------------------------------------------------------
-- Family parent replay
-- ---------------------------------------------------------------------------

INSERT INTO work.tcc_relay_curves_iec (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2IEC', 'bulk_upload', 'imported'
FROM relay_stage_curves_iec stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_swz (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2SWZ', 'bulk_upload', 'imported'
FROM relay_stage_curves_swz stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_bsl (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2BSL', 'bulk_upload', 'imported'
FROM relay_stage_curves_bsl stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_meq (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2MEQ', 'bulk_upload', 'imported'
FROM relay_stage_curves_meq stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_pcd (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2PCD', 'bulk_upload', 'imported'
FROM relay_stage_curves_pcd stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_lrm (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    lr_unit_code,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       stage.lr_unit_code, :'relay_snapshot_id', 'RelaySec2LRM', 'bulk_upload', 'imported'
FROM relay_stage_curves_lrm stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_rxd (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2RXD', 'bulk_upload', 'imported'
FROM relay_stage_curves_rxd stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_egc (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    min_pickup,
    max_pickup,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT td.relay_td_section_id, stage.relay_td_section_source_id, stage.source_row_id, stage.min_pickup, stage.max_pickup,
       :'relay_snapshot_id', 'RelaySec2EGC', 'bulk_upload', 'imported'
FROM relay_stage_curves_egc stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

INSERT INTO work.tcc_relay_curves_tcp (
    relay_td_section_id,
    relay_td_section_source_id,
    source_row_id,
    curve_name,
    tcc_number,
    ordinal,
    is_discrete,
    step_size,
    horizontal_amps_code,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    td.relay_td_section_id,
    stage.relay_td_section_source_id,
    stage.source_row_id,
    stage.curve_name,
    NULLIF(stage.tcc_number, ''),
    stage.ordinal,
    COALESCE(stage.is_discrete_flag, 0) <> 0,
    stage.step_size,
    stage.horizontal_amps_code,
    :'relay_snapshot_id',
    'RelaySec2TCP',
    'bulk_upload',
    'imported'
FROM relay_stage_curves_tcp stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.relay_td_section_source_id;

-- ---------------------------------------------------------------------------
-- Range and discrete replay
-- ---------------------------------------------------------------------------

INSERT INTO work.tcc_relay_ranges (
    source_row_id,
    source_parent_id,
    parent_kind,
    line_section_source_id,
    td_section_source_id,
    curve_parent_source_id,
    aux_key,
    ordinal,
    min_value,
    max_value,
    step_value,
    relative_unit_code,
    use_range,
    source_range_key,
    scales_with_time_multiplier,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'td_section'::work.relay_range_parent_kind_enum,
    NULL::integer,
    td.source_row_id,
    NULL::integer,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_td_sections td
  ON td.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 101

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'line_section'::work.relay_range_parent_kind_enum,
    line_section.source_row_id,
    NULL::integer,
    NULL::integer,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_line_sections line_section
  ON line_section.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 102

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'iec_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_iec curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 202

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'meq_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_meq curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 203

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'bsl_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_bsl curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 204

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'swz_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_swz curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 205

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'pcd_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_pcd curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 206

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'rxd_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_rxd curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 207

UNION ALL

SELECT
    stage.source_row_id,
    stage.source_parent_id,
    'lrm_curve'::work.relay_range_parent_kind_enum,
    NULL::integer,
    NULL::integer,
    curve_parent.source_row_id,
    stage.aux_key,
    stage.ordinal,
    stage.min_value,
    stage.max_value,
    stage.step_value,
    stage.relative_unit_code,
    COALESCE(stage.use_range_flag, 0) <> 0,
    stage.source_range_key,
    COALESCE(stage.scales_with_time_multiplier_flag, 0) <> 0,
    :'relay_snapshot_id',
    'RelayRanges'::text,
    'bulk_upload'::work.provenance_source_enum,
    'imported'::work.provenance_status_enum
FROM relay_stage_ranges stage
JOIN work.tcc_relay_curves_lrm curve_parent
  ON curve_parent.source_row_id = stage.source_parent_id
WHERE stage.source_range_key = 208;

INSERT INTO work.tcc_relay_discrete_values (
    relay_range_id,
    relay_range_source_id,
    discrete_value,
    discrete_description,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    relay_range.relay_range_id,
    stage.relay_range_source_id,
    stage.discrete_value,
    COALESCE(stage.discrete_description, ''),
    :'relay_snapshot_id',
    'RelayDiscreteValues',
    'bulk_upload',
    'imported'
FROM relay_stage_discrete_values stage
JOIN work.tcc_relay_ranges relay_range
  ON relay_range.source_row_id = stage.relay_range_source_id;

-- ---------------------------------------------------------------------------
-- Family row replay
-- ---------------------------------------------------------------------------

INSERT INTO work.tcc_relay_curve_rows_iec (
    relay_curve_iec_id,
    relay_curve_iec_source_id,
    curve_name,
    ordinal,
    v_k,
    v_e,
    dt_after,
    dt_min_time,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT parent.relay_curve_iec_id, stage.parent_source_id, stage.curve_name, stage.ordinal, stage.v_k, stage.v_e, stage.dt_after, stage.dt_min_time,
       :'relay_snapshot_id', 'RelaySec2IECCurves', 'bulk_upload', 'imported'
FROM relay_stage_curve_rows_iec stage
JOIN work.tcc_relay_curves_iec parent
  ON parent.source_row_id = stage.parent_source_id;

INSERT INTO work.tcc_relay_curve_rows_swz (
    relay_curve_swz_id,
    relay_curve_swz_source_id,
    curve_name,
    ordinal,
    v_a,
    v_b,
    v_e,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT parent.relay_curve_swz_id, stage.parent_source_id, stage.curve_name, stage.ordinal, stage.v_a, stage.v_b, stage.v_e,
       :'relay_snapshot_id', 'RelaySec2SWZCurves', 'bulk_upload', 'imported'
FROM relay_stage_curve_rows_swz stage
JOIN work.tcc_relay_curves_swz parent
  ON parent.source_row_id = stage.parent_source_id;

INSERT INTO work.tcc_relay_curve_rows_bsl (
    relay_curve_bsl_id,
    relay_curve_bsl_source_id,
    curve_name,
    ordinal,
    v_a,
    v_b,
    v_c,
    v_d,
    v_n,
    v_k,
    v_r,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT parent.relay_curve_bsl_id, stage.parent_source_id, stage.curve_name, stage.ordinal, stage.v_a, stage.v_b, stage.v_c, stage.v_d, stage.v_n, stage.v_k, stage.v_r,
       :'relay_snapshot_id', 'RelaySec2BSLCurves', 'bulk_upload', 'imported'
FROM relay_stage_curve_rows_bsl stage
JOIN work.tcc_relay_curves_bsl parent
  ON parent.source_row_id = stage.parent_source_id;

INSERT INTO work.tcc_relay_curve_rows_meq (
    relay_curve_meq_id,
    relay_curve_meq_source_id,
    curve_name,
    ordinal,
    v_a,
    v_b,
    v_c,
    v_d,
    v_e,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT parent.relay_curve_meq_id, stage.parent_source_id, stage.curve_name, stage.ordinal, stage.v_a, stage.v_b, stage.v_c, stage.v_d, stage.v_e,
       :'relay_snapshot_id', 'RelaySec2MEQCurves', 'bulk_upload', 'imported'
FROM relay_stage_curve_rows_meq stage
JOIN work.tcc_relay_curves_meq parent
  ON parent.source_row_id = stage.parent_source_id;

INSERT INTO work.tcc_relay_curve_rows_pcd (
    relay_curve_pcd_id,
    relay_curve_pcd_source_id,
    curve_name,
    ordinal,
    v_a,
    v_b,
    v_c,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT parent.relay_curve_pcd_id, stage.parent_source_id, stage.curve_name, stage.ordinal, stage.v_a, stage.v_b, stage.v_c,
       :'relay_snapshot_id', 'RelaySec2PCDCurves', 'bulk_upload', 'imported'
FROM relay_stage_curve_rows_pcd stage
JOIN work.tcc_relay_curves_pcd parent
  ON parent.source_row_id = stage.parent_source_id;

INSERT INTO work.tcc_relay_curve_points_tcp (
    relay_curve_tcp_id,
    relay_curve_tcp_source_id,
    time_dial,
    td_desc,
    current_index,
    current_value,
    trip_time_seconds,
    source_time_dial,
    source_ordinal,
    source_current_index,
    source_snapshot_id,
    source_table_name,
    created_from_source,
    provenance_status
)
SELECT
    parent.relay_curve_tcp_id,
    dial_rows.parent_source_id,
    dial_rows.time_dial,
    NULLIF(dial_rows.td_desc, ''),
    normalized_points.current_index,
    normalized_points.current_value,
    normalized_points.trip_time_seconds,
    dial_rows.time_dial,
    dial_rows.source_ordinal,
    normalized_points.current_index,
    :'relay_snapshot_id',
    'RelaySec2TCPCurves',
    'bulk_upload',
    'imported'
FROM relay_stage_curve_rows_tcp dial_rows
JOIN relay_stage_curve_rows_tcp header_rows
  ON header_rows.parent_source_id = dial_rows.parent_source_id
 AND header_rows.time_dial = -100
JOIN work.tcc_relay_curves_tcp parent
  ON parent.source_row_id = dial_rows.parent_source_id
CROSS JOIN LATERAL (
    VALUES
        (1,  header_rows.v1,  dial_rows.v1),
        (2,  header_rows.v2,  dial_rows.v2),
        (3,  header_rows.v3,  dial_rows.v3),
        (4,  header_rows.v4,  dial_rows.v4),
        (5,  header_rows.v5,  dial_rows.v5),
        (6,  header_rows.v6,  dial_rows.v6),
        (7,  header_rows.v7,  dial_rows.v7),
        (8,  header_rows.v8,  dial_rows.v8),
        (9,  header_rows.v9,  dial_rows.v9),
        (10, header_rows.v10, dial_rows.v10),
        (11, header_rows.v11, dial_rows.v11),
        (12, header_rows.v12, dial_rows.v12),
        (13, header_rows.v13, dial_rows.v13),
        (14, header_rows.v14, dial_rows.v14),
        (15, header_rows.v15, dial_rows.v15),
        (16, header_rows.v16, dial_rows.v16),
        (17, header_rows.v17, dial_rows.v17),
        (18, header_rows.v18, dial_rows.v18),
        (19, header_rows.v19, dial_rows.v19),
        (20, header_rows.v20, dial_rows.v20),
        (21, header_rows.v21, dial_rows.v21),
        (22, header_rows.v22, dial_rows.v22),
        (23, header_rows.v23, dial_rows.v23),
        (24, header_rows.v24, dial_rows.v24),
        (25, header_rows.v25, dial_rows.v25)
) AS normalized_points(current_index, current_value, trip_time_seconds)
WHERE dial_rows.time_dial <> -100
  AND normalized_points.current_value IS NOT NULL
  AND normalized_points.trip_time_seconds IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Focused validation output
-- ---------------------------------------------------------------------------

\echo Relay source/target counts
SELECT *
FROM (
    VALUES
        ('source_manufacturers',      (SELECT count(*)::bigint FROM relay_stage_manufacturers)),
        ('source_relays',             (SELECT count(*)::bigint FROM relay_stage_relays)),
        ('loaded_relays',             (SELECT count(*)::bigint FROM work.tcc_relays WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('source_devices',            (SELECT count(*)::bigint FROM relay_stage_devices)),
        ('loaded_devices',            (SELECT count(*)::bigint FROM work.tcc_relay_devices WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('source_line_sections',      (SELECT count(*)::bigint FROM relay_stage_line_sections)),
        ('loaded_line_sections',      (SELECT count(*)::bigint FROM work.tcc_relay_line_sections WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('source_td_sections',        (SELECT count(*)::bigint FROM relay_stage_td_sections)),
        ('loaded_td_sections',        (SELECT count(*)::bigint FROM work.tcc_relay_td_sections WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('source_ranges',             (SELECT count(*)::bigint FROM relay_stage_ranges)),
        ('loaded_ranges',             (SELECT count(*)::bigint FROM work.tcc_relay_ranges WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('source_discrete_values',    (SELECT count(*)::bigint FROM relay_stage_discrete_values)),
        ('loaded_discrete_values',    (SELECT count(*)::bigint FROM work.tcc_relay_discrete_values WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('loaded_tcp_points',         (SELECT count(*)::bigint FROM work.tcc_relay_curve_points_tcp WHERE source_snapshot_id = :'relay_snapshot_id')),
        ('orphan_relay_devices_rejected', (SELECT count(*)::bigint FROM relay_stage_devices stage LEFT JOIN relay_stage_relays relay ON relay.source_row_id = stage.relay_source_id WHERE relay.source_row_id IS NULL))
) AS counts(metric, row_count)
ORDER BY metric;

\echo Relay range resolution by RangeKey
SELECT
    stage.source_range_key,
    count(*) AS source_rows,
    count(loaded.relay_range_id) AS loaded_rows
FROM relay_stage_ranges stage
LEFT JOIN work.tcc_relay_ranges loaded
  ON loaded.source_row_id = stage.source_row_id
GROUP BY stage.source_range_key
ORDER BY stage.source_range_key;

\echo TCP normalization expected vs loaded points
WITH expected AS (
    SELECT count(*) AS expected_points
    FROM relay_stage_curve_rows_tcp dial_rows
    JOIN relay_stage_curve_rows_tcp header_rows
      ON header_rows.parent_source_id = dial_rows.parent_source_id
     AND header_rows.time_dial = -100
    CROSS JOIN LATERAL (
        VALUES
            (header_rows.v1,  dial_rows.v1),
            (header_rows.v2,  dial_rows.v2),
            (header_rows.v3,  dial_rows.v3),
            (header_rows.v4,  dial_rows.v4),
            (header_rows.v5,  dial_rows.v5),
            (header_rows.v6,  dial_rows.v6),
            (header_rows.v7,  dial_rows.v7),
            (header_rows.v8,  dial_rows.v8),
            (header_rows.v9,  dial_rows.v9),
            (header_rows.v10, dial_rows.v10),
            (header_rows.v11, dial_rows.v11),
            (header_rows.v12, dial_rows.v12),
            (header_rows.v13, dial_rows.v13),
            (header_rows.v14, dial_rows.v14),
            (header_rows.v15, dial_rows.v15),
            (header_rows.v16, dial_rows.v16),
            (header_rows.v17, dial_rows.v17),
            (header_rows.v18, dial_rows.v18),
            (header_rows.v19, dial_rows.v19),
            (header_rows.v20, dial_rows.v20),
            (header_rows.v21, dial_rows.v21),
            (header_rows.v22, dial_rows.v22),
            (header_rows.v23, dial_rows.v23),
            (header_rows.v24, dial_rows.v24),
            (header_rows.v25, dial_rows.v25)
    ) AS points(current_value, trip_time_seconds)
    WHERE dial_rows.time_dial <> -100
      AND points.current_value IS NOT NULL
      AND points.trip_time_seconds IS NOT NULL
)
SELECT
    expected.expected_points,
    actual.loaded_points
FROM expected
CROSS JOIN (
    SELECT count(*) AS loaded_points
    FROM work.tcc_relay_curve_points_tcp
    WHERE source_snapshot_id = :'relay_snapshot_id'
) AS actual;