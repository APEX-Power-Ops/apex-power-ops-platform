-- ============================================================================
-- EMT Target Schema Expansion
-- ============================================================================
-- Adds the EMT family target tables that were left out of the initial v5 schema.
-- Created 2026-03-22
-- ============================================================================

CREATE TABLE IF NOT EXISTS tcc_emt (
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

CREATE INDEX IF NOT EXISTS idx_tcc_emt_manufacturer_id ON tcc_emt(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_tcc_emt_type_name ON tcc_emt(type_name);
CREATE INDEX IF NOT EXISTS idx_tcc_emt_style_name ON tcc_emt(style_name);

COMMENT ON TABLE tcc_emt IS 'EMT family master catalog. Source: EMT';

CREATE TABLE IF NOT EXISTS tcc_emt_frames (
    id SERIAL PRIMARY KEY,
    emt_id INTEGER NOT NULL REFERENCES tcc_emt(id) ON DELETE CASCADE,
    frame_size NUMERIC(10,2),
    frame_desc VARCHAR(100),
    ordinal INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(emt_id, frame_desc)
);

CREATE INDEX IF NOT EXISTS idx_tcc_emt_frames_emt_id ON tcc_emt_frames(emt_id);
CREATE INDEX IF NOT EXISTS idx_tcc_emt_frames_frame_size ON tcc_emt_frames(frame_size);

COMMENT ON TABLE tcc_emt_frames IS 'EMT frame records per EMT style. Source: EMT_Frames';

CREATE TABLE IF NOT EXISTS tcc_emt_frame_amps (
    id SERIAL PRIMARY KEY,
    frame_id INTEGER NOT NULL REFERENCES tcc_emt_frames(id) ON DELETE CASCADE,
    rating NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(frame_id, rating)
);

CREATE INDEX IF NOT EXISTS idx_tcc_emt_frame_amps_frame_id ON tcc_emt_frame_amps(frame_id);

COMMENT ON TABLE tcc_emt_frame_amps IS 'EMT amp ratings per frame. Source: EMT_FrameAmps';

CREATE TABLE IF NOT EXISTS tcc_emt_sections (
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

CREATE INDEX IF NOT EXISTS idx_tcc_emt_sections_frame_id ON tcc_emt_sections(frame_id);
CREATE INDEX IF NOT EXISTS idx_tcc_emt_sections_sec_char ON tcc_emt_sections(sec_char);

COMMENT ON TABLE tcc_emt_sections IS 'EMT section metadata and selection semantics. Source: EMT_Sections';

CREATE TABLE IF NOT EXISTS tcc_emt_pickups (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES tcc_emt_sections(id) ON DELETE CASCADE,
    setting NUMERIC(10,4),
    description VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(section_id, setting, description)
);

CREATE INDEX IF NOT EXISTS idx_tcc_emt_pickups_section_id ON tcc_emt_pickups(section_id);

COMMENT ON TABLE tcc_emt_pickups IS 'EMT pickup setting rows per section. Source: EMT_Pickups';

CREATE TABLE IF NOT EXISTS tcc_emt_band_names (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES tcc_emt_sections(id) ON DELETE CASCADE,
    band_name VARCHAR(100),
    ordinal INTEGER,
    current_at NUMERIC(10,4),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(section_id, band_name, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_tcc_emt_band_names_section_id ON tcc_emt_band_names(section_id);

COMMENT ON TABLE tcc_emt_band_names IS 'EMT named curve bands per section. Source: EMT_BandNames';

CREATE TABLE IF NOT EXISTS tcc_emt_curves (
    id SERIAL PRIMARY KEY,
    band_id INTEGER NOT NULL REFERENCES tcc_emt_band_names(id) ON DELETE CASCADE,
    class INTEGER,
    time_sec NUMERIC(14,4) NOT NULL,
    current_amp NUMERIC(10,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tcc_emt_curves_band_id ON tcc_emt_curves(band_id);
CREATE INDEX IF NOT EXISTS idx_tcc_emt_curves_band_id_class ON tcc_emt_curves(band_id, class);

COMMENT ON TABLE tcc_emt_curves IS 'EMT opening and clearing point-data curves. Source: EMT_Curves';