-- ============================================================================
-- TCC v5 Complete Schema Migration
-- ============================================================================
-- All tables use tcc_ prefix with specialized prefixes for breakers, TMT, ETU
-- Proper naming: all PK = id, FKs spelled out, timestamps are timestamptz
-- 40 total tables: 38 reference + 2 user tables (UUID PKs)
-- Created 2026-03-20
-- ============================================================================

-- ============================================================================
-- SECTION 1: MANUFACTURERS & TRIP REFERENCE TABLES
-- ============================================================================

CREATE TABLE tcc_manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_manufacturers_name ON tcc_manufacturers(name);

COMMENT ON TABLE tcc_manufacturers IS 'Breaker manufacturers. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_trip_types (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(manufacturer_id, name)
);

CREATE INDEX idx_tcc_trip_types_manufacturer_id ON tcc_trip_types(manufacturer_id);
CREATE INDEX idx_tcc_trip_types_name ON tcc_trip_types(name);

COMMENT ON TABLE tcc_trip_types IS 'Trip types per manufacturer. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_trip_styles (
    id SERIAL PRIMARY KEY,
    trip_type_id INTEGER NOT NULL REFERENCES tcc_trip_types(id) ON DELETE CASCADE,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    notes TEXT,
    tcc_number VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(trip_type_id, name)
);

CREATE INDEX idx_tcc_trip_styles_trip_type_id ON tcc_trip_styles(trip_type_id);
CREATE INDEX idx_tcc_trip_styles_manufacturer_id ON tcc_trip_styles(manufacturer_id);
CREATE INDEX idx_tcc_trip_styles_name ON tcc_trip_styles(name);

COMMENT ON TABLE tcc_trip_styles IS 'Trip styles (trip units) per trip type. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 2: BREAKER TYPES & STYLES
-- ============================================================================

CREATE TABLE tcc_brk_iccb (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    standard NUMERIC(3,1),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(manufacturer_id, name)
);

CREATE INDEX idx_tcc_brk_iccb_manufacturer_id ON tcc_brk_iccb(manufacturer_id);

COMMENT ON TABLE tcc_brk_iccb IS 'ICCB (Insulated Case Circuit Breaker) models. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_brk_iccb_styles (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER NOT NULL REFERENCES tcc_brk_iccb(id) ON DELETE CASCADE,
    frame VARCHAR(100) NOT NULL,
    voltage_id INTEGER,
    kaic_480v NUMERIC(10,2),
    kaic_600v NUMERIC(10,2),
    standard NUMERIC(3,1),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(breaker_id, frame)
);

CREATE INDEX idx_tcc_brk_iccb_styles_breaker_id ON tcc_brk_iccb_styles(breaker_id);

COMMENT ON TABLE tcc_brk_iccb_styles IS 'ICCB frame/style variants. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_brk_mccb (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    standard NUMERIC(3,1),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(manufacturer_id, name)
);

CREATE INDEX idx_tcc_brk_mccb_manufacturer_id ON tcc_brk_mccb(manufacturer_id);

COMMENT ON TABLE tcc_brk_mccb IS 'MCCB (Molded Case Circuit Breaker) models. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_brk_mccb_styles (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER NOT NULL REFERENCES tcc_brk_mccb(id) ON DELETE CASCADE,
    frame VARCHAR(100) NOT NULL,
    voltage_id INTEGER,
    kaic_240v NUMERIC(10,2),
    kaic_480v NUMERIC(10,2),
    kaic_600v NUMERIC(10,2),
    poles INTEGER,
    standard NUMERIC(3,1),
    interrupt_class VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(breaker_id, frame)
);

CREATE INDEX idx_tcc_brk_mccb_styles_breaker_id ON tcc_brk_mccb_styles(breaker_id);

COMMENT ON TABLE tcc_brk_mccb_styles IS 'MCCB frame/style variants. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_brk_pcb (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    standard NUMERIC(3,1),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(manufacturer_id, name)
);

CREATE INDEX idx_tcc_brk_pcb_manufacturer_id ON tcc_brk_pcb(manufacturer_id);

COMMENT ON TABLE tcc_brk_pcb IS 'PCB (Power Circuit Breaker) models. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_brk_pcb_styles (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER NOT NULL REFERENCES tcc_brk_pcb(id) ON DELETE CASCADE,
    frame VARCHAR(100) NOT NULL,
    voltage_id INTEGER,
    kaic_480v NUMERIC(10,2),
    kaic_600v NUMERIC(10,2),
    standard NUMERIC(3,1),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(breaker_id, frame)
);

CREATE INDEX idx_tcc_brk_pcb_styles_breaker_id ON tcc_brk_pcb_styles(breaker_id);

COMMENT ON TABLE tcc_brk_pcb_styles IS 'PCB frame/style variants. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 3: TMT (TRIP MEMORY TABLE) TABLES
-- ============================================================================

CREATE TABLE tcc_tmt_frames (
    id SERIAL PRIMARY KEY,
    breaker_style_id INTEGER NOT NULL,
    breaker_class VARCHAR(4) NOT NULL CHECK (breaker_class IN ('iccb', 'mccb', 'pcb')),
    size VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_tmt_frames_breaker_style_id ON tcc_tmt_frames(breaker_style_id);
CREATE INDEX idx_tcc_tmt_frames_breaker_class ON tcc_tmt_frames(breaker_class);

COMMENT ON TABLE tcc_tmt_frames IS 'TMT frame sizes (discriminated by breaker_class). Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_tmt_amps (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_tmt_frames(id) ON DELETE CASCADE,
    rating NUMERIC(10,2) NOT NULL,
    max_override NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(frame_id, rating)
);

CREATE INDEX idx_tcc_tmt_amps_frame_id ON tcc_tmt_amps(frame_id);

COMMENT ON TABLE tcc_tmt_amps IS 'TMT amperage ratings per frame. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_tmt_curves (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_tmt_frames(id) ON DELETE CASCADE,
    class INTEGER NOT NULL,
    time_sec NUMERIC(10,4) NOT NULL,
    current_amp NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_tmt_curves_frame_id ON tcc_tmt_curves(frame_id);
CREATE INDEX idx_tcc_tmt_curves_frame_id_class ON tcc_tmt_curves(frame_id, class);

COMMENT ON TABLE tcc_tmt_curves IS 'TMT trip curves (1.1M+ rows). Frame/class composite for performance. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_tmt_settings (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_tmt_frames(id) ON DELETE CASCADE,
    value NUMERIC(10,4) NOT NULL,
    label VARCHAR(100),
    tol_lo NUMERIC(10,4),
    tol_hi NUMERIC(10,4),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_tmt_settings_frame_id ON tcc_tmt_settings(frame_id);

COMMENT ON TABLE tcc_tmt_settings IS 'TMT settings with tolerances per frame. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_tmt_thermal_adj (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_tmt_frames(id) ON DELETE CASCADE,
    adjustment NUMERIC(7,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(frame_id)
);

CREATE INDEX idx_tcc_tmt_thermal_adj_frame_id ON tcc_tmt_thermal_adj(frame_id);

COMMENT ON TABLE tcc_tmt_thermal_adj IS 'TMT thermal adjustment per frame. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 4: EMT (ELECTRO-MECHANICAL TRIP) TABLES
-- ============================================================================

CREATE TABLE tcc_emt (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL REFERENCES tcc_manufacturers(id) ON DELETE CASCADE,
    type_name VARCHAR(100),
    style_name VARCHAR(100),
    tcc_number VARCHAR(50),
    notes TEXT,
    trip_char INTEGER,
    trip_plug INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(manufacturer_id, type_name, style_name)
);

CREATE INDEX idx_tcc_emt_manufacturer_id ON tcc_emt(manufacturer_id);
CREATE INDEX idx_tcc_emt_type_name ON tcc_emt(type_name);
CREATE INDEX idx_tcc_emt_style_name ON tcc_emt(style_name);

COMMENT ON TABLE tcc_emt IS 'EMT family master catalog. Source: EMT';

-- ============================================================================

CREATE TABLE tcc_emt_frames (
    id SERIAL PRIMARY KEY,
    emt_id INTEGER NOT NULL REFERENCES tcc_emt(id) ON DELETE CASCADE,
    frame_size NUMERIC(10,2),
    frame_desc VARCHAR(100),
    ordinal INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(emt_id, frame_desc)
);

CREATE INDEX idx_tcc_emt_frames_emt_id ON tcc_emt_frames(emt_id);
CREATE INDEX idx_tcc_emt_frames_frame_size ON tcc_emt_frames(frame_size);

COMMENT ON TABLE tcc_emt_frames IS 'EMT frame records per EMT style. Source: EMT_Frames';

-- ============================================================================

CREATE TABLE tcc_emt_frame_amps (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_emt_frames(id) ON DELETE CASCADE,
    rating NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(frame_id, rating)
);

CREATE INDEX idx_tcc_emt_frame_amps_frame_id ON tcc_emt_frame_amps(frame_id);

COMMENT ON TABLE tcc_emt_frame_amps IS 'EMT amp ratings per frame. Source: EMT_FrameAmps';

-- ============================================================================

CREATE TABLE tcc_emt_sections (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_emt_frames(id) ON DELETE CASCADE,
    name VARCHAR(100),
    sec_char INTEGER,
    curve_type INTEGER,
    pickup_calc INTEGER,
    pickup_tol_lo NUMERIC(10,4),
    pickup_tol_hi NUMERIC(10,4),
    pickup_setting INTEGER,
    step_size NUMERIC(10,4),
    current_calc INTEGER,
    delay_clr_curve INTEGER,
    delay_open_time NUMERIC(10,4),
    delay_clear_time NUMERIC(10,4),
    open_curve_radius NUMERIC(10,4),
    clear_curve_radius NUMERIC(10,4),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_emt_sections_frame_id ON tcc_emt_sections(frame_id);
CREATE INDEX idx_tcc_emt_sections_sec_char ON tcc_emt_sections(sec_char);

COMMENT ON TABLE tcc_emt_sections IS 'EMT section metadata and selection semantics. Source: EMT_Sections';

-- ============================================================================

CREATE TABLE tcc_emt_pickups (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES tcc_emt_sections(id) ON DELETE CASCADE,
    setting NUMERIC(10,4),
    description VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(section_id, setting, description)
);

CREATE INDEX idx_tcc_emt_pickups_section_id ON tcc_emt_pickups(section_id);

COMMENT ON TABLE tcc_emt_pickups IS 'EMT pickup setting rows per section. Source: EMT_Pickups';

-- ============================================================================

CREATE TABLE tcc_emt_band_names (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES tcc_emt_sections(id) ON DELETE CASCADE,
    band_name VARCHAR(100),
    ordinal INTEGER,
    current_at NUMERIC(10,4),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(section_id, band_name, ordinal)
);

CREATE INDEX idx_tcc_emt_band_names_section_id ON tcc_emt_band_names(section_id);

COMMENT ON TABLE tcc_emt_band_names IS 'EMT named curve bands per section. Source: EMT_BandNames';

-- ============================================================================

CREATE TABLE tcc_emt_curves (
    id SERIAL PRIMARY KEY,
    band_id INTEGER NOT NULL REFERENCES tcc_emt_band_names(id) ON DELETE CASCADE,
    class INTEGER,
    time_sec NUMERIC(14,4) NOT NULL,
    current_amp NUMERIC(10,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_emt_curves_band_id ON tcc_emt_curves(band_id);
CREATE INDEX idx_tcc_emt_curves_band_id_class ON tcc_emt_curves(band_id, class);

COMMENT ON TABLE tcc_emt_curves IS 'EMT opening and clearing point-data curves. Source: EMT_Curves';

-- ============================================================================
-- SECTION 5: ETU (ELECTRONIC TRIP UNIT) CORE TABLES
-- ============================================================================

CREATE TABLE tcc_etu_plugs (
    id SERIAL PRIMARY KEY,
    trip_style_id INTEGER NOT NULL REFERENCES tcc_trip_styles(id) ON DELETE CASCADE,
    value INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(trip_style_id, value)
);

CREATE INDEX idx_tcc_etu_plugs_trip_style_id ON tcc_etu_plugs(trip_style_id);

COMMENT ON TABLE tcc_etu_plugs IS 'ETU plug ratings per trip style. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_sensors (
    id SERIAL PRIMARY KEY,
    trip_style_id INTEGER NOT NULL REFERENCES tcc_trip_styles(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    description VARCHAR(200),
    ltpu_name VARCHAR(50),
    ltpu_calc INTEGER,
    ltpu_tol_hi NUMERIC(5,2),
    ltpu_tol_lo NUMERIC(5,2),
    ltpu_step NUMERIC(10,4),
    ltd_name VARCHAR(50),
    stpu_name VARCHAR(50),
    stpu_calc INTEGER,
    stpu_tol_hi NUMERIC(5,2),
    stpu_tol_lo NUMERIC(5,2),
    stpu_step NUMERIC(10,4),
    inst_name VARCHAR(50),
    inst_calc INTEGER,
    inst_tol_hi NUMERIC(5,2),
    inst_tol_lo NUMERIC(5,2),
    gfpu_name VARCHAR(50),
    gfpu_calc INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(trip_style_id, rating)
);

CREATE INDEX idx_tcc_etu_sensors_trip_style_id ON tcc_etu_sensors(trip_style_id);

COMMENT ON TABLE tcc_etu_sensors IS 'ETU sensors (trip units) with pickup/delay config metadata. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 5: ETU PICKUP SETTING TABLES
-- ============================================================================

CREATE TABLE tcc_etu_ltpu_pickups (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    value NUMERIC(10,4) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_ltpu_pickups_sensor_id ON tcc_etu_ltpu_pickups(sensor_id);

COMMENT ON TABLE tcc_etu_ltpu_pickups IS 'LTPU (Long-Time Pickup) settings per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_ltpu_multipliers (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    c_value NUMERIC(10,4) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_ltpu_multipliers_sensor_id ON tcc_etu_ltpu_multipliers(sensor_id);

COMMENT ON TABLE tcc_etu_ltpu_multipliers IS 'LTPU multiplier settings per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_stpu_pickups (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    label VARCHAR(50),
    value NUMERIC(10,4) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_stpu_pickups_sensor_id ON tcc_etu_stpu_pickups(sensor_id);

COMMENT ON TABLE tcc_etu_stpu_pickups IS 'STPU (Short-Time Pickup) settings per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_inst_pickups (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    label VARCHAR(50),
    value NUMERIC(10,4) NOT NULL,
    mode INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_inst_pickups_sensor_id ON tcc_etu_inst_pickups(sensor_id);

COMMENT ON TABLE tcc_etu_inst_pickups IS 'Instantaneous (INST) settings per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_gfpu_pickups (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    label VARCHAR(50),
    value NUMERIC(10,4) NOT NULL,
    mode INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_gfpu_pickups_sensor_id ON tcc_etu_gfpu_pickups(sensor_id);

COMMENT ON TABLE tcc_etu_gfpu_pickups IS 'Ground Fault Pickup (GFPU) settings per sensor. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 6: ETU DELAY BAND TABLES
-- ============================================================================

CREATE TABLE tcc_etu_ltd_bands (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    band VARCHAR(20),
    band_label VARCHAR(50),
    open_time NUMERIC(10,4),
    clear_time NUMERIC(10,4),
    i_open NUMERIC(10,4),
    i_clear NUMERIC(10,4),
    t_open NUMERIC(10,4),
    t_clear NUMERIC(10,4),
    i2x NUMERIC(10,4),
    exp_x NUMERIC(10,4),
    const_k NUMERIC(10,4),
    sgf NUMERIC(10,4),
    low_pickup NUMERIC(10,4),
    const_k_hi NUMERIC(10,4),
    curve_id INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_ltd_bands_sensor_id ON tcc_etu_ltd_bands(sensor_id);

COMMENT ON TABLE tcc_etu_ltd_bands IS 'LTD (Long-Time Delay) bands per sensor with curve data. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_std_bands (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    band VARCHAR(20),
    band_label VARCHAR(50),
    open_time NUMERIC(10,4),
    clear_time NUMERIC(10,4),
    i_open NUMERIC(10,4),
    i_clear NUMERIC(10,4),
    t_open NUMERIC(10,4),
    t_clear NUMERIC(10,4),
    i2x NUMERIC(10,4),
    exp_x NUMERIC(10,4),
    const_k NUMERIC(10,4),
    sgf NUMERIC(10,4),
    low_pickup NUMERIC(10,4),
    const_k_hi NUMERIC(10,4),
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_std_bands_sensor_id ON tcc_etu_std_bands(sensor_id);

COMMENT ON TABLE tcc_etu_std_bands IS 'STD (Short-Time Delay) bands per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_gfd_bands (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    band VARCHAR(20),
    band_label VARCHAR(50),
    open_time NUMERIC(10,4),
    clear_time NUMERIC(10,4),
    i_open NUMERIC(10,4),
    i_clear NUMERIC(10,4),
    t_open NUMERIC(10,4),
    t_clear NUMERIC(10,4),
    i2x NUMERIC(10,4),
    exp_x NUMERIC(10,4),
    const_k NUMERIC(10,4),
    sgf NUMERIC(10,4),
    low_pickup NUMERIC(10,4),
    const_k_hi NUMERIC(10,4),
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_gfd_bands_sensor_id ON tcc_etu_gfd_bands(sensor_id);

COMMENT ON TABLE tcc_etu_gfd_bands IS 'GFD (Ground Fault Delay) bands per sensor. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 7: ETU EQUATION TABLES
-- ============================================================================

CREATE TABLE tcc_etu_std_equations (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    label VARCHAR(50),
    in_out INTEGER,
    fd_open_eq INTEGER,
    fd_open_1 NUMERIC(12,6),
    fd_open_2 NUMERIC(12,6),
    fd_open_3 NUMERIC(12,6),
    fd_open_4 NUMERIC(12,6),
    fd_open_5 NUMERIC(12,6),
    fd_open_6 NUMERIC(12,6),
    fd_open_i_calc INTEGER,
    fd_clear_eq INTEGER,
    fd_clear_1 NUMERIC(12,6),
    fd_clear_2 NUMERIC(12,6),
    fd_clear_3 NUMERIC(12,6),
    fd_clear_4 NUMERIC(12,6),
    fd_clear_5 NUMERIC(12,6),
    fd_clear_6 NUMERIC(12,6),
    fd_clear_i_calc INTEGER,
    id_open_eq INTEGER,
    id_open_1 NUMERIC(12,6),
    id_open_2 NUMERIC(12,6),
    id_open_3 NUMERIC(12,6),
    id_open_4 NUMERIC(12,6),
    id_open_5 NUMERIC(12,6),
    id_open_6 NUMERIC(12,6),
    id_open_i_calc INTEGER,
    id_clear_eq INTEGER,
    id_clear_1 NUMERIC(12,6),
    id_clear_2 NUMERIC(12,6),
    id_clear_3 NUMERIC(12,6),
    id_clear_4 NUMERIC(12,6),
    id_clear_5 NUMERIC(12,6),
    id_clear_6 NUMERIC(12,6),
    id_clear_i_calc INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_std_equations_sensor_id ON tcc_etu_std_equations(sensor_id);

COMMENT ON TABLE tcc_etu_std_equations IS 'STD inverse time equations with 4 equation sets (fd_open, fd_clear, id_open, id_clear). Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_gfd_equations (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    label VARCHAR(50),
    in_out INTEGER,
    fd_open_eq INTEGER,
    fd_open_1 NUMERIC(12,6),
    fd_open_2 NUMERIC(12,6),
    fd_open_3 NUMERIC(12,6),
    fd_open_4 NUMERIC(12,6),
    fd_open_5 NUMERIC(12,6),
    fd_open_6 NUMERIC(12,6),
    fd_open_i_calc INTEGER,
    fd_clear_eq INTEGER,
    fd_clear_1 NUMERIC(12,6),
    fd_clear_2 NUMERIC(12,6),
    fd_clear_3 NUMERIC(12,6),
    fd_clear_4 NUMERIC(12,6),
    fd_clear_5 NUMERIC(12,6),
    fd_clear_6 NUMERIC(12,6),
    fd_clear_i_calc INTEGER,
    id_open_eq INTEGER,
    id_open_1 NUMERIC(12,6),
    id_open_2 NUMERIC(12,6),
    id_open_3 NUMERIC(12,6),
    id_open_4 NUMERIC(12,6),
    id_open_5 NUMERIC(12,6),
    id_open_6 NUMERIC(12,6),
    id_open_i_calc INTEGER,
    id_clear_eq INTEGER,
    id_clear_1 NUMERIC(12,6),
    id_clear_2 NUMERIC(12,6),
    id_clear_3 NUMERIC(12,6),
    id_clear_4 NUMERIC(12,6),
    id_clear_5 NUMERIC(12,6),
    id_clear_6 NUMERIC(12,6),
    id_clear_i_calc INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_gfd_equations_sensor_id ON tcc_etu_gfd_equations(sensor_id);

COMMENT ON TABLE tcc_etu_gfd_equations IS 'GFD inverse time equations with 4 equation sets (fd_open, fd_clear, id_open, id_clear). Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 8: ETU CURVE & PARAMETER TABLES
-- ============================================================================

CREATE TABLE tcc_etu_inst_curves (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    ordinal INTEGER,
    class VARCHAR(50),
    current_amp NUMERIC(10,2),
    time_sec NUMERIC(10,4),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_inst_curves_sensor_id ON tcc_etu_inst_curves(sensor_id);

COMMENT ON TABLE tcc_etu_inst_curves IS 'Instantaneous trip curves per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_sensor_params (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    section INTEGER,
    idx INTEGER,
    value NUMERIC(12,6),
    curve_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_sensor_params_sensor_id ON tcc_etu_sensor_params(sensor_id);

COMMENT ON TABLE tcc_etu_sensor_params IS 'ETU sensor parameters by section/index. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_ltd_params (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    curve_id INTEGER,
    curve_name VARCHAR(50),
    ordinal INTEGER,
    method INTEGER,
    ltf INTEGER,
    tol_hi NUMERIC(5,2),
    tol_lo NUMERIC(5,2),
    value NUMERIC(10,4),
    type INTEGER,
    slope NUMERIC(10,4),
    step NUMERIC(10,4),
    delay_priority INTEGER,
    force_i2x_out INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_ltd_params_sensor_id ON tcc_etu_ltd_params(sensor_id);

COMMENT ON TABLE tcc_etu_ltd_params IS 'LTD curve parameters (formerly sst_sensor_sec2_params). Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_stpu_overrides (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    type VARCHAR(50),
    value NUMERIC(10,4),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_etu_stpu_overrides_sensor_id ON tcc_etu_stpu_overrides(sensor_id);

COMMENT ON TABLE tcc_etu_stpu_overrides IS 'STPU override settings per sensor. Source: circuit_breaker_database';

-- ============================================================================

CREATE TABLE tcc_etu_sensor_maint (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES tcc_etu_sensors(id) ON DELETE CASCADE,
    alarm_type VARCHAR(50),
    alarm_threshold NUMERIC(10,2),
    alarm_enabled BOOLEAN DEFAULT FALSE,
    maint_available BOOLEAN DEFAULT FALSE,
    maint_ltpu_reduction NUMERIC(5,2),
    maint_stpu_reduction NUMERIC(5,2),
    maint_inst_reduction NUMERIC(5,2),
    params_json JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sensor_id, alarm_type)
);

CREATE INDEX idx_tcc_etu_sensor_maint_sensor_id ON tcc_etu_sensor_maint(sensor_id);

COMMENT ON TABLE tcc_etu_sensor_maint IS 'ETU sensor maintenance mode settings with JSON params. Source: circuit_breaker_database';

-- ============================================================================
-- SECTION 9: USER TEST TABLES (UUID PKs)
-- ============================================================================

CREATE TABLE tcc_test_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(200),
    project VARCHAR(200),
    equipment_tag VARCHAR(100),
    location VARCHAR(200),
    sensor_id INTEGER REFERENCES tcc_etu_sensors(id),
    ltpu_pickup_id INTEGER REFERENCES tcc_etu_ltpu_pickups(id),
    ltd_band_id INTEGER REFERENCES tcc_etu_ltd_bands(id),
    stpu_pickup_id INTEGER REFERENCES tcc_etu_stpu_pickups(id),
    std_band_id INTEGER REFERENCES tcc_etu_std_bands(id),
    inst_pickup_id INTEGER REFERENCES tcc_etu_inst_pickups(id),
    gfpu_pickup_id INTEGER REFERENCES tcc_etu_gfpu_pickups(id),
    gfd_band_id INTEGER REFERENCES tcc_etu_gfd_bands(id),
    ltpu_test_amps NUMERIC(10,2),
    ltpu_min_sec NUMERIC(10,2),
    ltpu_max_sec NUMERIC(10,2),
    std_test_amps NUMERIC(10,2),
    std_min_sec NUMERIC(10,2),
    std_max_sec NUMERIC(10,2),
    inst_test_amps NUMERIC(10,2),
    inst_min_sec NUMERIC(10,2),
    inst_max_sec NUMERIC(10,2),
    gfpu_test_amps NUMERIC(10,2),
    gfpu_min_sec NUMERIC(10,2),
    gfpu_max_sec NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tcc_test_plans_user_id ON tcc_test_plans(user_id);
CREATE INDEX idx_tcc_test_plans_sensor_id ON tcc_test_plans(sensor_id);

COMMENT ON TABLE tcc_test_plans IS 'User test plans for breaker trip unit validation. Source: user data';

-- ============================================================================

CREATE TABLE tcc_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES tcc_test_plans(id) ON DELETE CASCADE,
    test_type VARCHAR(20),
    element VARCHAR(20),
    expected NUMERIC(12,4),
    actual NUMERIC(12,4),
    min_accept NUMERIC(12,4),
    max_accept NUMERIC(12,4),
    passed BOOLEAN,
    tested_at TIMESTAMPTZ DEFAULT now(),
    technician VARCHAR(100),
    notes TEXT
);

CREATE INDEX idx_tcc_test_results_plan_id ON tcc_test_results(plan_id);

COMMENT ON TABLE tcc_test_results IS 'Test results from breaker trip unit validation runs. Source: user data';

-- ============================================================================
-- SECTION 10: ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Tier 1: Reference Tables (31 tables)
-- Authenticated users: SELECT only
-- Service role: ALL (bypass)

ALTER TABLE tcc_manufacturers ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_manufacturers_select ON tcc_manufacturers FOR SELECT USING (TRUE);
CREATE POLICY tcc_manufacturers_service ON tcc_manufacturers USING (auth.role() = 'service_role');

ALTER TABLE tcc_trip_types ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_trip_types_select ON tcc_trip_types FOR SELECT USING (TRUE);
CREATE POLICY tcc_trip_types_service ON tcc_trip_types USING (auth.role() = 'service_role');

ALTER TABLE tcc_trip_styles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_trip_styles_select ON tcc_trip_styles FOR SELECT USING (TRUE);
CREATE POLICY tcc_trip_styles_service ON tcc_trip_styles USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_iccb ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_iccb_select ON tcc_brk_iccb FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_iccb_service ON tcc_brk_iccb USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_iccb_styles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_iccb_styles_select ON tcc_brk_iccb_styles FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_iccb_styles_service ON tcc_brk_iccb_styles USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_mccb ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_mccb_select ON tcc_brk_mccb FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_mccb_service ON tcc_brk_mccb USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_mccb_styles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_mccb_styles_select ON tcc_brk_mccb_styles FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_mccb_styles_service ON tcc_brk_mccb_styles USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_pcb ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_pcb_select ON tcc_brk_pcb FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_pcb_service ON tcc_brk_pcb USING (auth.role() = 'service_role');

ALTER TABLE tcc_brk_pcb_styles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_brk_pcb_styles_select ON tcc_brk_pcb_styles FOR SELECT USING (TRUE);
CREATE POLICY tcc_brk_pcb_styles_service ON tcc_brk_pcb_styles USING (auth.role() = 'service_role');

ALTER TABLE tcc_tmt_frames ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_tmt_frames_select ON tcc_tmt_frames FOR SELECT USING (TRUE);
CREATE POLICY tcc_tmt_frames_service ON tcc_tmt_frames USING (auth.role() = 'service_role');

ALTER TABLE tcc_tmt_amps ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_tmt_amps_select ON tcc_tmt_amps FOR SELECT USING (TRUE);
CREATE POLICY tcc_tmt_amps_service ON tcc_tmt_amps USING (auth.role() = 'service_role');

ALTER TABLE tcc_tmt_curves ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_tmt_curves_select ON tcc_tmt_curves FOR SELECT USING (TRUE);
CREATE POLICY tcc_tmt_curves_service ON tcc_tmt_curves USING (auth.role() = 'service_role');

ALTER TABLE tcc_tmt_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_tmt_settings_select ON tcc_tmt_settings FOR SELECT USING (TRUE);
CREATE POLICY tcc_tmt_settings_service ON tcc_tmt_settings USING (auth.role() = 'service_role');

ALTER TABLE tcc_tmt_thermal_adj ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_tmt_thermal_adj_select ON tcc_tmt_thermal_adj FOR SELECT USING (TRUE);
CREATE POLICY tcc_tmt_thermal_adj_service ON tcc_tmt_thermal_adj USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_plugs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_plugs_select ON tcc_etu_plugs FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_plugs_service ON tcc_etu_plugs USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_sensors ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_sensors_select ON tcc_etu_sensors FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_sensors_service ON tcc_etu_sensors USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_ltpu_pickups ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_ltpu_pickups_select ON tcc_etu_ltpu_pickups FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_ltpu_pickups_service ON tcc_etu_ltpu_pickups USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_ltpu_multipliers ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_ltpu_multipliers_select ON tcc_etu_ltpu_multipliers FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_ltpu_multipliers_service ON tcc_etu_ltpu_multipliers USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_stpu_pickups ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_stpu_pickups_select ON tcc_etu_stpu_pickups FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_stpu_pickups_service ON tcc_etu_stpu_pickups USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_inst_pickups ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_inst_pickups_select ON tcc_etu_inst_pickups FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_inst_pickups_service ON tcc_etu_inst_pickups USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_gfpu_pickups ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_gfpu_pickups_select ON tcc_etu_gfpu_pickups FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_gfpu_pickups_service ON tcc_etu_gfpu_pickups USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_ltd_bands ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_ltd_bands_select ON tcc_etu_ltd_bands FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_ltd_bands_service ON tcc_etu_ltd_bands USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_std_bands ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_std_bands_select ON tcc_etu_std_bands FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_std_bands_service ON tcc_etu_std_bands USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_gfd_bands ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_gfd_bands_select ON tcc_etu_gfd_bands FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_gfd_bands_service ON tcc_etu_gfd_bands USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_std_equations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_std_equations_select ON tcc_etu_std_equations FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_std_equations_service ON tcc_etu_std_equations USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_gfd_equations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_gfd_equations_select ON tcc_etu_gfd_equations FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_gfd_equations_service ON tcc_etu_gfd_equations USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_inst_curves ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_inst_curves_select ON tcc_etu_inst_curves FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_inst_curves_service ON tcc_etu_inst_curves USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_sensor_params ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_sensor_params_select ON tcc_etu_sensor_params FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_sensor_params_service ON tcc_etu_sensor_params USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_ltd_params ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_ltd_params_select ON tcc_etu_ltd_params FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_ltd_params_service ON tcc_etu_ltd_params USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_stpu_overrides ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_stpu_overrides_select ON tcc_etu_stpu_overrides FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_stpu_overrides_service ON tcc_etu_stpu_overrides USING (auth.role() = 'service_role');

ALTER TABLE tcc_etu_sensor_maint ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_etu_sensor_maint_select ON tcc_etu_sensor_maint FOR SELECT USING (TRUE);
CREATE POLICY tcc_etu_sensor_maint_service ON tcc_etu_sensor_maint USING (auth.role() = 'service_role');

-- Tier 2: User Tables (2 tables)
-- Authenticated users: ALL where user_id = auth.uid()
-- Service role: ALL (bypass)

ALTER TABLE tcc_test_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_test_plans_auth ON tcc_test_plans FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY tcc_test_plans_service ON tcc_test_plans USING (auth.role() = 'service_role');

ALTER TABLE tcc_test_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY tcc_test_results_auth ON tcc_test_results FOR ALL USING (
    EXISTS (SELECT 1 FROM tcc_test_plans p WHERE p.id = plan_id AND p.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM tcc_test_plans p WHERE p.id = plan_id AND p.user_id = auth.uid())
);
CREATE POLICY tcc_test_results_service ON tcc_test_results USING (auth.role() = 'service_role');

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
