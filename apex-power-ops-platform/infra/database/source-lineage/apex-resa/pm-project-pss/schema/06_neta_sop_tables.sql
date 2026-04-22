-- ============================================================================
-- 06_neta_sop_tables.sql
-- NETA Procedures, SOPs, Safety Documents, Datasheets, and Resource Linking
-- Version: 1.0.0
-- Deployed: December 10, 2025
-- ============================================================================

-- SECTION 1: ENUM TYPES
CREATE TYPE neta_standard_type AS ENUM ('ATS', 'MTS', 'ECS');
CREATE TYPE neta_test_type AS ENUM ('visual_mechanical', 'electrical', 'insulation_resistance', 'contact_resistance', 'timing', 'functional', 'power_factor', 'oil_analysis', 'thermographic', 'other');
CREATE TYPE sop_category AS ENUM ('testing_procedure', 'safety_protocol', 'equipment_operation', 'calibration', 'documentation', 'quality_control', 'general');
CREATE TYPE safety_document_type AS ENUM ('jsa', 'safety_bulletin', 'hazard_assessment', 'ppe_requirements', 'lockout_tagout', 'arc_flash', 'confined_space', 'hot_work', 'general');
CREATE TYPE datasheet_type AS ENUM ('manufacturer_spec', 'nameplate_template', 'test_form', 'calibration_cert', 'installation_manual', 'maintenance_guide', 'wiring_diagram', 'general');
CREATE TYPE resource_type AS ENUM ('neta_procedure', 'sop', 'safety_document', 'datasheet');

-- SECTION 2: APPARATUS_TYPES ENHANCEMENT
ALTER TABLE apparatus_types
    ADD COLUMN IF NOT EXISTS neta_section_ats VARCHAR(20),
    ADD COLUMN IF NOT EXISTS neta_section_mts VARCHAR(20),
    ADD COLUMN IF NOT EXISTS neta_section_ecs VARCHAR(20),
    ADD COLUMN IF NOT EXISTS notes TEXT;

-- SECTION 3: NETA PROCEDURES TABLE
CREATE TABLE IF NOT EXISTS neta_procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_type neta_standard_type NOT NULL,
    section_number VARCHAR(20) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    description TEXT,
    scope TEXT,
    reference_documents TEXT[],
    apparatus_category VARCHAR(100),
    voltage_class VARCHAR(50),
    typical_frequency_months INTEGER,
    neta_version VARCHAR(20),
    effective_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    UNIQUE(standard_type, section_number, neta_version)
);

-- SECTION 4: NETA TEST ITEMS TABLE
CREATE TABLE IF NOT EXISTS neta_test_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    neta_procedure_id UUID NOT NULL REFERENCES neta_procedures(id) ON DELETE CASCADE,
    item_number VARCHAR(20),
    test_type neta_test_type NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    test_description TEXT,
    acceptance_criteria TEXT,
    equipment_required TEXT[],
    estimated_hours DECIMAL(5,2),
    complexity_factor DECIMAL(3,2) DEFAULT 1.0,
    display_order INTEGER DEFAULT 0,
    is_mandatory BOOLEAN DEFAULT true,
    requires_deenergized BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SECTION 5: SOPS TABLE
CREATE TABLE IF NOT EXISTS sops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sop_number VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    category sop_category NOT NULL,
    purpose TEXT,
    scope TEXT,
    procedure_steps JSONB,
    safety_requirements TEXT[],
    equipment_required TEXT[],
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    effective_date DATE,
    review_date DATE,
    department VARCHAR(100),
    owner_id UUID REFERENCES employees(id),
    is_active BOOLEAN DEFAULT true,
    document_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- SECTION 6: SAFETY DOCUMENTS TABLE
CREATE TABLE IF NOT EXISTS safety_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_number VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    document_type safety_document_type NOT NULL,
    description TEXT,
    hazards_identified TEXT[],
    controls_required TEXT[],
    ppe_required TEXT[],
    applicable_equipment_types UUID[],
    voltage_class VARCHAR(50),
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    effective_date DATE,
    review_date DATE,
    author_id UUID REFERENCES employees(id),
    reviewer_id UUID REFERENCES employees(id),
    is_active BOOLEAN DEFAULT true,
    document_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SECTION 7: DATASHEETS TABLE
CREATE TABLE IF NOT EXISTS datasheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    datasheet_number VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    datasheet_type datasheet_type NOT NULL,
    description TEXT,
    manufacturer VARCHAR(100),
    model_series VARCHAR(100),
    applicable_equipment_types UUID[],
    voltage_class VARCHAR(50),
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    effective_date DATE,
    is_active BOOLEAN DEFAULT true,
    document_url TEXT,
    form_fields JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- SECTION 8: APPARATUS TYPE RESOURCES JUNCTION TABLE
CREATE TABLE IF NOT EXISTS apparatus_type_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apparatus_type_id UUID NOT NULL REFERENCES apparatus_types(id) ON DELETE CASCADE,
    resource_type resource_type NOT NULL,
    resource_id UUID NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    UNIQUE(apparatus_type_id, resource_type, resource_id)
);

-- SECTION 9: INDEXES
CREATE INDEX IF NOT EXISTS idx_neta_procedures_standard_type ON neta_procedures(standard_type);
CREATE INDEX IF NOT EXISTS idx_neta_procedures_section ON neta_procedures(section_number);
CREATE INDEX IF NOT EXISTS idx_neta_test_items_procedure ON neta_test_items(neta_procedure_id);
CREATE INDEX IF NOT EXISTS idx_sops_number ON sops(sop_number);
CREATE INDEX IF NOT EXISTS idx_sops_category ON sops(category);
CREATE INDEX IF NOT EXISTS idx_safety_docs_number ON safety_documents(document_number);
CREATE INDEX IF NOT EXISTS idx_safety_docs_type ON safety_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_datasheets_number ON datasheets(datasheet_number);
CREATE INDEX IF NOT EXISTS idx_atr_apparatus_type ON apparatus_type_resources(apparatus_type_id);
CREATE INDEX IF NOT EXISTS idx_atr_resource_type ON apparatus_type_resources(resource_type);

-- SECTION 10: ENABLE RLS
ALTER TABLE neta_procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE neta_test_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE sops ENABLE ROW LEVEL SECURITY;
ALTER TABLE safety_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE datasheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE apparatus_type_resources ENABLE ROW LEVEL SECURITY;

-- SECTION 11: RLS POLICIES
CREATE POLICY "Read neta_procedures" ON neta_procedures FOR SELECT USING (true);
CREATE POLICY "Manage neta_procedures" ON neta_procedures FOR ALL USING (true);
CREATE POLICY "Read neta_test_items" ON neta_test_items FOR SELECT USING (true);
CREATE POLICY "Manage neta_test_items" ON neta_test_items FOR ALL USING (true);
CREATE POLICY "Read sops" ON sops FOR SELECT USING (true);
CREATE POLICY "Manage sops" ON sops FOR ALL USING (true);
CREATE POLICY "Read safety_documents" ON safety_documents FOR SELECT USING (true);
CREATE POLICY "Manage safety_documents" ON safety_documents FOR ALL USING (true);
CREATE POLICY "Read datasheets" ON datasheets FOR SELECT USING (true);
CREATE POLICY "Manage datasheets" ON datasheets FOR ALL USING (true);
CREATE POLICY "Read apparatus_type_resources" ON apparatus_type_resources FOR SELECT USING (true);
CREATE POLICY "Manage apparatus_type_resources" ON apparatus_type_resources FOR ALL USING (true);
