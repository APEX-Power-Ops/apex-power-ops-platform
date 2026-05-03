-- =============================================================================
-- TCC Relay — Shared-Infra Indexes
-- Packet: 2026-04-30-tcc-relay-tranche-1
-- Authority: TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md
-- Landing Lane: infra/database/migrations/work/
-- =============================================================================

-- Root relay catalog lookups
CREATE INDEX idx_tcc_relays_manufacturer_source_id
    ON work.tcc_relays (manufacturer_source_id);

CREATE INDEX idx_tcc_relays_relay_type
    ON work.tcc_relays (relay_type);

-- Device lookups
CREATE INDEX idx_tcc_relay_devices_relay_id
    ON work.tcc_relay_devices (relay_id);

CREATE INDEX idx_tcc_relay_devices_device_function
    ON work.tcc_relay_devices (device_function);

CREATE INDEX idx_tcc_relay_devices_curve_standard_code
    ON work.tcc_relay_devices (curve_standard_code)
    WHERE curve_standard_code IS NOT NULL;

-- Section lookups
CREATE INDEX idx_tcc_relay_line_sections_device_id
    ON work.tcc_relay_line_sections (relay_device_id);

CREATE INDEX idx_tcc_relay_line_sections_section_number
    ON work.tcc_relay_line_sections (section_number);

CREATE INDEX idx_tcc_relay_td_sections_device_id
    ON work.tcc_relay_td_sections (relay_device_id);

CREATE INDEX idx_tcc_relay_td_sections_model_code
    ON work.tcc_relay_td_sections (model_code);

-- Range and discrete-value lookups
CREATE INDEX idx_tcc_relay_ranges_parent_lookup
    ON work.tcc_relay_ranges (parent_kind, source_parent_id);

CREATE INDEX idx_tcc_relay_ranges_range_key
    ON work.tcc_relay_ranges (source_range_key);

CREATE INDEX idx_tcc_relay_discrete_values_range_id
    ON work.tcc_relay_discrete_values (relay_range_id);

CREATE INDEX idx_tcc_relay_discrete_values_range_source_id
    ON work.tcc_relay_discrete_values (relay_range_source_id);

-- Family parent lookups
CREATE INDEX idx_tcc_relay_curves_iec_td_section_id
    ON work.tcc_relay_curves_iec (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_swz_td_section_id
    ON work.tcc_relay_curves_swz (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_bsl_td_section_id
    ON work.tcc_relay_curves_bsl (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_meq_td_section_id
    ON work.tcc_relay_curves_meq (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_pcd_td_section_id
    ON work.tcc_relay_curves_pcd (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_lrm_td_section_id
    ON work.tcc_relay_curves_lrm (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_rxd_td_section_id
    ON work.tcc_relay_curves_rxd (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_egc_td_section_id
    ON work.tcc_relay_curves_egc (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_tcp_td_section_id
    ON work.tcc_relay_curves_tcp (relay_td_section_id);

CREATE INDEX idx_tcc_relay_curves_tcp_curve_name
    ON work.tcc_relay_curves_tcp (curve_name);

-- TCP normalized point lookups
CREATE INDEX idx_tcc_relay_curve_points_tcp_curve_index
    ON work.tcc_relay_curve_points_tcp (relay_curve_tcp_id, current_index);