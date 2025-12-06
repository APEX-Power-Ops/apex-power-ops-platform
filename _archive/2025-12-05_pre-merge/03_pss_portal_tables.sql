-- =============================================================================
-- RESA Power Platform - PSS Portal Tables
-- =============================================================================
-- Run this AFTER 01_supabase_schema.sql
-- Adds Power System Studies Portal tables
-- =============================================================================

-- =============================================================================
-- PSS PORTAL TABLES
-- =============================================================================

-- 1. Engineers (PSS Engineering Vendors like Shaw)
CREATE TABLE IF NOT EXISTS pss_engineers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(200) NOT NULL,
    primary_contact_id UUID,  -- Will reference pss_contacts
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(255),
    dropbox_share_link TEXT,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PSS Contacts (People at Clients or Engineers)
CREATE TABLE IF NOT EXISTS pss_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role_title VARCHAR(100),
    contact_type VARCHAR(50) NOT NULL,  -- 'Client', 'Engineer', 'RESA'
    client_id UUID REFERENCES clients(id),  -- If client contact
    engineer_id UUID REFERENCES pss_engineers(id),  -- If engineer contact
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_contact_type CHECK (contact_type IN ('Client', 'Engineer', 'RESA'))
);

-- Add foreign key for primary contact now that pss_contacts exists
ALTER TABLE pss_engineers 
ADD CONSTRAINT fk_engineer_primary_contact 
FOREIGN KEY (primary_contact_id) REFERENCES pss_contacts(id);

-- 3. PSS Projects (Power System Study Projects)
CREATE TABLE IF NOT EXISTS pss_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resa_job_number VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    client_id UUID REFERENCES clients(id),
    engineer_id UUID REFERENCES pss_engineers(id),
    
    -- Study Details
    service_type VARCHAR(50) NOT NULL,  -- PSS, Arc Flash, PSS + Arc Flash, Coordination
    status VARCHAR(50) NOT NULL DEFAULT 'New Request',
    stage VARCHAR(50),  -- Auto-calculated from status
    
    -- Key Dates
    order_date DATE,
    target_report_date DATE,
    report_sent_date DATE,
    report_approved_date DATE,
    stickers_applied_date DATE,
    
    -- Responsibility
    data_collection_by VARCHAR(50),  -- RESA, Client, Shaw
    stickers_settings_by VARCHAR(50),  -- RESA, Client, Shaw
    
    -- Financial
    po_number VARCHAR(100),
    po_date DATE,
    po_amount DECIMAL(12, 2),
    invoice_date DATE,
    
    -- Tracking
    status_changed_at TIMESTAMPTZ DEFAULT NOW(),
    days_in_current_status INTEGER DEFAULT 0,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_service_type CHECK (service_type IN ('PSS', 'Arc Flash', 'PSS + Arc Flash', 'Coordination')),
    CONSTRAINT valid_status CHECK (status IN (
        'New Request', 'Awaiting Documents', 'Partial Documents', 
        'Ready for Engineer', 'In Progress', 'RFI Pending',
        'Draft Submitted', 'Revisions Requested', 'Report Approved',
        'Stickers Pending', 'Closed'
    ))
);

-- 4. Document Templates (Master checklist of required documents)
CREATE TABLE IF NOT EXISTS pss_document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_name VARCHAR(200) NOT NULL,
    study_types TEXT[] NOT NULL,  -- Array: ['PSS', 'Arc Flash', 'Coordination']
    is_required BOOLEAN DEFAULT true,
    description TEXT,
    example_notes TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Documents (Individual documents for each project)
CREATE TABLE IF NOT EXISTS pss_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES pss_projects(id) ON DELETE CASCADE,
    template_id UUID REFERENCES pss_document_templates(id),
    document_name VARCHAR(200),
    
    status VARCHAR(50) NOT NULL DEFAULT 'Not Requested',
    requested_date DATE,
    received_date DATE,
    reviewed_date DATE,
    
    uploaded_by_id UUID REFERENCES pss_contacts(id),
    reviewed_by_id UUID REFERENCES pss_contacts(id),
    
    file_url TEXT,  -- Supabase Storage URL
    file_name VARCHAR(255),
    file_size INTEGER,
    
    days_outstanding INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_doc_status CHECK (status IN (
        'Not Requested', 'Requested', 'Received', 
        'Under Review', 'Rejected', 'Accepted', 'N/A'
    ))
);

-- 6. RFIs (Requests for Information)
CREATE TABLE IF NOT EXISTS pss_rfis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES pss_projects(id) ON DELETE CASCADE,
    rfi_number VARCHAR(50),  -- Format: RFI-{JobNumber}-{Seq}
    sequence_number INTEGER DEFAULT 1,
    
    subject VARCHAR(200) NOT NULL,
    question TEXT NOT NULL,
    related_document_id UUID REFERENCES pss_documents(id),
    
    priority VARCHAR(20) NOT NULL DEFAULT 'Medium',
    status VARCHAR(20) NOT NULL DEFAULT 'Open',
    
    submitted_by_id UUID REFERENCES pss_contacts(id),
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    
    response TEXT,
    response_by_id UUID REFERENCES pss_contacts(id),
    response_date TIMESTAMPTZ,
    response_file_url TEXT,
    
    days_open INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_priority CHECK (priority IN ('Low', 'Medium', 'High', 'Urgent')),
    CONSTRAINT valid_rfi_status CHECK (status IN ('Open', 'Responded', 'Closed'))
);

-- 7. Activity Log (Communication & action history)
CREATE TABLE IF NOT EXISTS pss_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES pss_projects(id) ON DELETE CASCADE,
    
    activity_datetime TIMESTAMPTZ DEFAULT NOW(),
    activity_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    
    performed_by_id UUID REFERENCES pss_contacts(id),
    related_rfi_id UUID REFERENCES pss_rfis(id),
    related_document_id UUID REFERENCES pss_documents(id),
    
    attachment_url TEXT,
    visible_to_client BOOLEAN DEFAULT true,
    visible_to_engineer BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_activity_type CHECK (activity_type IN (
        'Status Change', 'Document Uploaded', 'Document Reviewed',
        'RFI Submitted', 'RFI Responded', 'Email Sent', 'Email Received',
        'Phone Call', 'Note Added', 'Reminder Sent'
    ))
);

-- 8. PSS Users (Portal user accounts)
CREATE TABLE IF NOT EXISTS pss_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    contact_id UUID REFERENCES pss_contacts(id),
    
    role VARCHAR(50) NOT NULL DEFAULT 'Client',
    is_active BOOLEAN DEFAULT true,
    
    last_login TIMESTAMPTZ,
    created_by_id UUID REFERENCES pss_users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('RESA Admin', 'RESA Staff', 'Client', 'Engineer'))
);

-- =============================================================================
-- INDEXES FOR PSS TABLES
-- =============================================================================

CREATE INDEX idx_pss_contacts_client ON pss_contacts(client_id);
CREATE INDEX idx_pss_contacts_engineer ON pss_contacts(engineer_id);
CREATE INDEX idx_pss_projects_client ON pss_projects(client_id);
CREATE INDEX idx_pss_projects_engineer ON pss_projects(engineer_id);
CREATE INDEX idx_pss_projects_status ON pss_projects(status);
CREATE INDEX idx_pss_projects_job_number ON pss_projects(resa_job_number);
CREATE INDEX idx_pss_documents_project ON pss_documents(project_id);
CREATE INDEX idx_pss_documents_status ON pss_documents(status);
CREATE INDEX idx_pss_rfis_project ON pss_rfis(project_id);
CREATE INDEX idx_pss_rfis_status ON pss_rfis(status);
CREATE INDEX idx_pss_activity_project ON pss_activity_log(project_id);

-- =============================================================================
-- TRIGGERS FOR PSS TABLES
-- =============================================================================

-- Apply updated_at triggers
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name IN (
            'pss_engineers', 'pss_contacts', 'pss_projects', 
            'pss_document_templates', 'pss_documents', 'pss_rfis', 'pss_users'
        )
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%s_updated_at ON %s;
            CREATE TRIGGER update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- FUNCTION: Auto-calculate stage from status
-- =============================================================================

CREATE OR REPLACE FUNCTION calculate_pss_stage()
RETURNS TRIGGER AS $$
BEGIN
    NEW.stage := CASE NEW.status
        WHEN 'New Request' THEN '1. Intake'
        WHEN 'Awaiting Documents' THEN '2. Data Collection'
        WHEN 'Partial Documents' THEN '2. Data Collection'
        WHEN 'Ready for Engineer' THEN '3. Engineer Handoff'
        WHEN 'In Progress' THEN '4. Study In Progress'
        WHEN 'RFI Pending' THEN '4. Study In Progress'
        WHEN 'Draft Submitted' THEN '5. Review'
        WHEN 'Revisions Requested' THEN '5. Review'
        WHEN 'Report Approved' THEN '6. Final Delivery'
        WHEN 'Stickers Pending' THEN '6. Final Delivery'
        WHEN 'Closed' THEN '7. Complete'
        ELSE '1. Intake'
    END;
    
    -- Track status change time
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        NEW.status_changed_at := NOW();
        NEW.days_in_current_status := 0;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_pss_stage
BEFORE INSERT OR UPDATE ON pss_projects
FOR EACH ROW
EXECUTE FUNCTION calculate_pss_stage();

-- =============================================================================
-- FUNCTION: Auto-generate RFI number
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_rfi_number()
RETURNS TRIGGER AS $$
DECLARE
    job_number VARCHAR(50);
    next_seq INTEGER;
BEGIN
    -- Get job number from project
    SELECT resa_job_number INTO job_number 
    FROM pss_projects WHERE id = NEW.project_id;
    
    -- Get next sequence for this project
    SELECT COALESCE(MAX(sequence_number), 0) + 1 INTO next_seq
    FROM pss_rfis WHERE project_id = NEW.project_id;
    
    NEW.sequence_number := next_seq;
    NEW.rfi_number := 'RFI-' || job_number || '-' || LPAD(next_seq::TEXT, 3, '0');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_rfi_number
BEFORE INSERT ON pss_rfis
FOR EACH ROW
EXECUTE FUNCTION generate_rfi_number();

-- =============================================================================
-- SUCCESS MESSAGE
-- =============================================================================
SELECT 'PSS Portal tables created successfully!' as message;
