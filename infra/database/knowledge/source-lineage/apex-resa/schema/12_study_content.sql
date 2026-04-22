-- ============================================================================
-- NETA STUDY CONTENT SCHEMA EXTENSION
-- Integrates learning content into existing Resource Linking architecture
-- Version: 1.0.0 | December 26, 2025
-- ============================================================================
-- 
-- VISION: One platform. Everything connected. Always available when it matters.
-- 
-- Study content is a RESOURCE TYPE, not a separate system. Field techs see
-- study guides alongside NETA procedures, SOPs, safety docs - all linked to
-- the apparatus they're testing. Same query pattern, same UI component.
--
-- INTEGRATION POINT:
-- apparatus → apparatus_type → apparatus_type_resources → study_content
-- (Same junction pattern as SOPs, safety docs, datasheets)
-- ============================================================================

-- ============================================================================
-- ENUM EXTENSIONS
-- ============================================================================

-- Extend existing resource_type enum with study content types
ALTER TYPE resource_type ADD VALUE IF NOT EXISTS 'study_guide';
ALTER TYPE resource_type ADD VALUE IF NOT EXISTS 'reference_sheet';
ALTER TYPE resource_type ADD VALUE IF NOT EXISTS 'practice_questions';

-- Certification levels (matches existing neta_level concept)
CREATE TYPE certification_level AS ENUM ('I', 'II', 'III', 'IV');

-- Content quality tiers (aligns with GOVERNANCE-FRAMEWORK quality dimensions)
CREATE TYPE content_quality_tier AS ENUM (
    'gold',           -- 1000+ lines, all dimensions, enhancement-exhausted
    'high_quality',   -- Meets all specs, minor enhancement opportunities
    'complete',       -- Meets minimum specs
    'draft',          -- Work in progress
    'needs_review'    -- Flagged for quality review
);

-- Question types for practice content
CREATE TYPE question_type AS ENUM (
    'multiple_choice',
    'true_false', 
    'calculation',
    'scenario',
    'fill_blank',
    'matching'
);

-- ============================================================================
-- CORE STUDY CONTENT TABLE
-- ============================================================================
-- Holds study guides, reference sheets - links via apparatus_type_resources

CREATE TABLE study_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- ========== IDENTITY ==========
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,      -- URL-friendly: 'transformer-testing-protocol'
    resource_type resource_type NOT NULL,   -- study_guide, reference_sheet, practice_questions
    
    -- ========== CLASSIFICATION ==========
    certification_level certification_level NOT NULL,
    domain VARCHAR(100) NOT NULL,           -- 'transformers', 'circuit-breakers', 'grounding'
    
    -- Progressive content: same topic, different depth per level
    level_ii_section TEXT,                  -- Foundational content for this topic
    level_iii_section TEXT,                 -- Advanced content for this topic  
    level_iv_section TEXT,                  -- Expert/system-level content
    
    -- ========== CONTENT ==========
    body_markdown TEXT NOT NULL,            -- Primary content (markdown)
    body_html TEXT,                         -- Rendered HTML for web display
    summary TEXT,                           -- 1-2 sentence description
    
    -- ========== METADATA ==========
    estimated_minutes INT,                  -- Reading/study time
    word_count INT,
    line_count INT,                         -- Migration tracking from HTML
    
    -- ========== QUALITY TRACKING ==========
    quality_tier content_quality_tier DEFAULT 'draft',
    quality_score NUMERIC(5,2),             -- 0-100 (6 dimensions assessment)
    enhancement_status VARCHAR(50) DEFAULT 'active',
    deferred_enhancements JSONB,            -- [{opportunity, rationale, priority}]
    
    -- ========== SOURCE REFERENCES ==========
    sources JSONB,                          -- [{standard, section, page}]
    original_file VARCHAR(255),             -- Migration reference: '11-Transformer-Oil-Analysis.html'
    
    -- ========== AI/RAG ==========
    embedding VECTOR(1536),                 -- Semantic search (pgvector)
    
    -- ========== RELATIONSHIPS ==========
    prerequisite_ids UUID[],                -- Must understand these first
    related_content_ids UUID[],             -- See also
    ksa_mappings VARCHAR[],                 -- ['ETT-III-2.4', 'ETT-IV-1.3']
    neta_sections VARCHAR[],                -- ['ATS-7.2.1', 'MTS-7.2.1'] direct NETA links
    
    -- ========== TIMESTAMPS ==========
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    published_at TIMESTAMPTZ,               -- NULL = draft, set = live
    
    -- ========== CONSTRAINTS ==========
    CONSTRAINT valid_study_resource_type CHECK (
        resource_type IN ('study_guide', 'reference_sheet', 'practice_questions')
    )
);

COMMENT ON TABLE study_content IS 'Study guides, reference sheets linked to apparatus types via apparatus_type_resources';
COMMENT ON COLUMN study_content.slug IS 'URL-friendly identifier, e.g., transformer-oil-analysis';
COMMENT ON COLUMN study_content.domain IS 'Equipment/topic domain for filtering, e.g., transformers, circuit-breakers';
COMMENT ON COLUMN study_content.ksa_mappings IS 'NETA ETT KSA codes this content addresses';

-- ============================================================================
-- QUESTIONS TABLE (for practice tests)
-- ============================================================================
-- Separate from study_content for flexible question bank management

CREATE TABLE study_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- ========== IDENTITY ==========
    question_number VARCHAR(20),            -- 'Q-TRF-001' for organization
    question_type question_type NOT NULL,
    certification_level certification_level NOT NULL,
    domain VARCHAR(100) NOT NULL,
    
    -- ========== QUESTION CONTENT ==========
    stem TEXT NOT NULL,                     -- The question itself
    choices JSONB,                          -- [{id, text, is_correct}] for MC
    correct_answer TEXT,                    -- For non-MC questions
    explanation TEXT NOT NULL,              -- Why the answer is correct
    distractor_explanations JSONB,          -- [{choice_id, why_wrong}]
    
    -- ========== CLASSIFICATION ==========
    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),  -- 1=easy, 5=expert
    ksa_mappings VARCHAR[],                 -- KSAs this question tests
    neta_sections VARCHAR[],                -- Related NETA sections
    
    -- ========== SOURCE ==========
    source_content_id UUID REFERENCES study_content(id),
    sources JSONB,                          -- External references
    original_file VARCHAR(255),             -- Migration tracking
    
    -- ========== ANALYTICS ==========
    times_shown INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    discrimination_index NUMERIC(3,2),      -- How well it separates knowing/not knowing
    
    -- ========== TIMESTAMPS ==========
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- ========== EMBEDDING ==========
    embedding VECTOR(1536)                  -- For semantic question search
);

COMMENT ON TABLE study_questions IS 'Question bank for practice tests, linked to study content and apparatus types';

-- ============================================================================
-- LINKING: Questions ↔ Apparatus Types  
-- ============================================================================
-- Granular question-level linking (study_content links via apparatus_type_resources)

CREATE TABLE apparatus_type_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apparatus_type_id UUID NOT NULL REFERENCES apparatus_types(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES study_questions(id) ON DELETE CASCADE,
    relevance_score NUMERIC(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(apparatus_type_id, question_id)
);

COMMENT ON TABLE apparatus_type_questions IS 'Links individual questions to apparatus types for targeted practice';

-- ============================================================================
-- USER PROGRESS TRACKING
-- ============================================================================
-- Ready for auth integration (Phase 2.0)

CREATE TABLE user_study_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                  -- References auth.users when ready
    content_id UUID REFERENCES study_content(id),
    question_id UUID REFERENCES study_questions(id),
    
    -- Progress metrics
    completed BOOLEAN DEFAULT false,
    time_spent_seconds INT DEFAULT 0,
    last_accessed TIMESTAMPTZ DEFAULT now(),
    
    -- For questions
    attempts INT DEFAULT 0,
    correct_attempts INT DEFAULT 0,
    last_answer TEXT,
    
    -- Mastery tracking
    mastery_level NUMERIC(5,2) DEFAULT 0,   -- 0-100
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT one_target CHECK (
        (content_id IS NOT NULL AND question_id IS NULL) OR
        (content_id IS NULL AND question_id IS NOT NULL)
    )
);

COMMENT ON TABLE user_study_progress IS 'Tracks user progress through study content and questions';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_study_content_domain ON study_content(domain);
CREATE INDEX idx_study_content_level ON study_content(certification_level);
CREATE INDEX idx_study_content_type ON study_content(resource_type);
CREATE INDEX idx_study_content_slug ON study_content(slug);
CREATE INDEX idx_study_content_published ON study_content(published_at) WHERE published_at IS NOT NULL;

CREATE INDEX idx_study_questions_domain ON study_questions(domain);
CREATE INDEX idx_study_questions_level ON study_questions(certification_level);
CREATE INDEX idx_study_questions_type ON study_questions(question_type);
CREATE INDEX idx_study_questions_source ON study_questions(source_content_id);

CREATE INDEX idx_apparatus_type_questions_type ON apparatus_type_questions(apparatus_type_id);
CREATE INDEX idx_apparatus_type_questions_question ON apparatus_type_questions(question_id);

CREATE INDEX idx_user_study_progress_user ON user_study_progress(user_id);
CREATE INDEX idx_user_study_progress_content ON user_study_progress(content_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Unified resource view for apparatus types (extends existing pattern)
CREATE OR REPLACE VIEW v_apparatus_type_all_resources AS
SELECT 
    at.id AS apparatus_type_id,
    at.name AS apparatus_type_name,
    'study_content' AS source_table,
    sc.id AS resource_id,
    sc.title AS resource_title,
    sc.resource_type,
    sc.certification_level::TEXT AS level,
    sc.summary AS description,
    sc.slug AS url_slug,
    sc.estimated_minutes
FROM apparatus_types at
JOIN apparatus_type_resources atr ON at.id = atr.apparatus_type_id
JOIN study_content sc ON atr.resource_id = sc.id
WHERE atr.resource_type IN ('study_guide', 'reference_sheet', 'practice_questions')
  AND sc.published_at IS NOT NULL

UNION ALL

SELECT 
    at.id AS apparatus_type_id,
    at.name AS apparatus_type_name,
    'neta_procedures' AS source_table,
    np.id AS resource_id,
    np.title AS resource_title,
    'neta_procedure'::resource_type,
    np.standard_type::TEXT AS level,
    np.scope AS description,
    np.section_number AS url_slug,
    NULL::INT AS estimated_minutes
FROM apparatus_types at
JOIN apparatus_type_resources atr ON at.id = atr.apparatus_type_id  
JOIN neta_procedures np ON atr.resource_id = np.id
WHERE atr.resource_type = 'neta_procedure';

COMMENT ON VIEW v_apparatus_type_all_resources IS 'Unified view of all resources linked to apparatus types';

-- Field tech view: Study content for specific apparatus
CREATE OR REPLACE VIEW v_apparatus_study_content AS
SELECT 
    a.id AS apparatus_id,
    a.apparatus_designation,
    at.name AS apparatus_type,
    sc.id AS content_id,
    sc.title,
    sc.resource_type,
    sc.certification_level,
    sc.summary,
    sc.estimated_minutes,
    sc.slug
FROM apparatus a
JOIN apparatus_types at ON a.apparatus_type_id = at.id
JOIN apparatus_type_resources atr ON at.id = atr.apparatus_type_id
JOIN study_content sc ON atr.resource_id = sc.id
WHERE sc.published_at IS NOT NULL
ORDER BY a.apparatus_designation, sc.certification_level, sc.title;

COMMENT ON VIEW v_apparatus_study_content IS 'Study content linked to specific apparatus for field tech view';

-- Content inventory dashboard
CREATE OR REPLACE VIEW v_study_content_inventory AS
SELECT 
    domain,
    certification_level,
    resource_type,
    quality_tier,
    COUNT(*) AS content_count,
    SUM(line_count) AS total_lines,
    AVG(quality_score) AS avg_quality_score,
    COUNT(*) FILTER (WHERE published_at IS NOT NULL) AS published_count
FROM study_content
GROUP BY domain, certification_level, resource_type, quality_tier
ORDER BY domain, certification_level;

COMMENT ON VIEW v_study_content_inventory IS 'Content inventory by domain, level, and quality tier';

-- Question bank statistics
CREATE OR REPLACE VIEW v_question_bank_stats AS
SELECT 
    domain,
    certification_level,
    question_type,
    COUNT(*) AS question_count,
    AVG(difficulty) AS avg_difficulty,
    AVG(CASE WHEN times_shown > 0 THEN times_correct::NUMERIC / times_shown ELSE NULL END) AS success_rate
FROM study_questions
GROUP BY domain, certification_level, question_type
ORDER BY domain, certification_level;

COMMENT ON VIEW v_question_bank_stats IS 'Question bank statistics by domain and level';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER study_content_updated 
    BEFORE UPDATE ON study_content 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER study_questions_updated
    BEFORE UPDATE ON study_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER user_study_progress_updated
    BEFORE UPDATE ON user_study_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- RPC FUNCTIONS: Content Management
-- ============================================================================

-- Register study content (migration helper)
CREATE OR REPLACE FUNCTION register_study_content(
    p_title VARCHAR,
    p_slug VARCHAR,
    p_resource_type resource_type,
    p_certification_level certification_level,
    p_domain VARCHAR,
    p_body_markdown TEXT,
    p_summary TEXT DEFAULT NULL,
    p_original_file VARCHAR DEFAULT NULL,
    p_line_count INT DEFAULT NULL,
    p_ksa_mappings VARCHAR[] DEFAULT NULL,
    p_neta_sections VARCHAR[] DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_content_id UUID;
BEGIN
    INSERT INTO study_content (
        title, slug, resource_type, certification_level, domain,
        body_markdown, summary, original_file, line_count,
        ksa_mappings, neta_sections, quality_tier
    ) VALUES (
        p_title, p_slug, p_resource_type, p_certification_level, p_domain,
        p_body_markdown, p_summary, p_original_file, p_line_count,
        p_ksa_mappings, p_neta_sections, 'draft'
    )
    ON CONFLICT (slug) DO UPDATE SET
        title = EXCLUDED.title,
        body_markdown = EXCLUDED.body_markdown,
        summary = EXCLUDED.summary,
        line_count = EXCLUDED.line_count,
        ksa_mappings = EXCLUDED.ksa_mappings,
        neta_sections = EXCLUDED.neta_sections,
        updated_at = now()
    RETURNING id INTO v_content_id;
    
    RETURN v_content_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION register_study_content IS 'Register or update study content during migration';

-- Link content to apparatus type
CREATE OR REPLACE FUNCTION link_content_to_apparatus_type(
    p_content_slug VARCHAR,
    p_apparatus_type_name VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_content_id UUID;
    v_type_id UUID;
    v_resource_type resource_type;
BEGIN
    SELECT id, resource_type INTO v_content_id, v_resource_type
    FROM study_content WHERE slug = p_content_slug;
    
    IF v_content_id IS NULL THEN
        RAISE EXCEPTION 'Content not found: %', p_content_slug;
    END IF;
    
    SELECT id INTO v_type_id
    FROM apparatus_types WHERE name = p_apparatus_type_name;
    
    IF v_type_id IS NULL THEN
        RAISE EXCEPTION 'Apparatus type not found: %', p_apparatus_type_name;
    END IF;
    
    INSERT INTO apparatus_type_resources (apparatus_type_id, resource_id, resource_type)
    VALUES (v_type_id, v_content_id, v_resource_type)
    ON CONFLICT DO NOTHING;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION link_content_to_apparatus_type IS 'Link study content to apparatus type via junction table';

-- Publish content (makes it visible)
CREATE OR REPLACE FUNCTION publish_study_content(p_slug VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE study_content 
    SET published_at = now(), updated_at = now()
    WHERE slug = p_slug AND published_at IS NULL;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION publish_study_content IS 'Publish content by setting published_at timestamp';

-- Get all resources for an apparatus (field tech query)
CREATE OR REPLACE FUNCTION get_apparatus_resources(p_apparatus_id UUID)
RETURNS TABLE (
    resource_id UUID,
    title VARCHAR,
    resource_type resource_type,
    source_table VARCHAR,
    level TEXT,
    description TEXT,
    url_slug VARCHAR,
    estimated_minutes INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.resource_id,
        r.resource_title AS title,
        r.resource_type,
        r.source_table,
        r.level,
        r.description,
        r.url_slug,
        r.estimated_minutes
    FROM apparatus a
    JOIN v_apparatus_type_all_resources r ON a.apparatus_type_id = r.apparatus_type_id
    WHERE a.id = p_apparatus_id
    ORDER BY r.resource_type, r.resource_title;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_apparatus_resources IS 'Get all resources (NETA, SOPs, study content) for an apparatus';

-- ============================================================================
-- RPC FUNCTIONS: Question Management
-- ============================================================================

-- Register a question
CREATE OR REPLACE FUNCTION register_question(
    p_question_type question_type,
    p_certification_level certification_level,
    p_domain VARCHAR,
    p_stem TEXT,
    p_choices JSONB,
    p_correct_answer TEXT,
    p_explanation TEXT,
    p_difficulty INT DEFAULT 3,
    p_ksa_mappings VARCHAR[] DEFAULT NULL,
    p_source_content_slug VARCHAR DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_question_id UUID;
    v_source_content_id UUID;
BEGIN
    -- Get source content ID if provided
    IF p_source_content_slug IS NOT NULL THEN
        SELECT id INTO v_source_content_id
        FROM study_content WHERE slug = p_source_content_slug;
    END IF;
    
    INSERT INTO study_questions (
        question_type, certification_level, domain,
        stem, choices, correct_answer, explanation,
        difficulty, ksa_mappings, source_content_id
    ) VALUES (
        p_question_type, p_certification_level, p_domain,
        p_stem, p_choices, p_correct_answer, p_explanation,
        p_difficulty, p_ksa_mappings, v_source_content_id
    )
    RETURNING id INTO v_question_id;
    
    RETURN v_question_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION register_question IS 'Register a new practice question';

-- Get questions for apparatus type
CREATE OR REPLACE FUNCTION get_apparatus_type_questions(
    p_apparatus_type_id UUID,
    p_certification_level certification_level DEFAULT NULL,
    p_limit INT DEFAULT 25
) RETURNS TABLE (
    question_id UUID,
    question_type question_type,
    certification_level certification_level,
    domain VARCHAR,
    stem TEXT,
    choices JSONB,
    difficulty INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        q.id AS question_id,
        q.question_type,
        q.certification_level,
        q.domain,
        q.stem,
        q.choices,
        q.difficulty
    FROM study_questions q
    JOIN apparatus_type_questions atq ON q.id = atq.question_id
    WHERE atq.apparatus_type_id = p_apparatus_type_id
      AND (p_certification_level IS NULL OR q.certification_level = p_certification_level)
    ORDER BY atq.relevance_score DESC, RANDOM()
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_apparatus_type_questions IS 'Get practice questions for an apparatus type';

-- ============================================================================
-- RPC FUNCTIONS: Progress Tracking
-- ============================================================================

-- Record content view/completion
CREATE OR REPLACE FUNCTION record_content_progress(
    p_user_id UUID,
    p_content_id UUID,
    p_time_spent_seconds INT,
    p_completed BOOLEAN DEFAULT false
) RETURNS UUID AS $$
DECLARE
    v_progress_id UUID;
BEGIN
    INSERT INTO user_study_progress (
        user_id, content_id, time_spent_seconds, completed, last_accessed
    ) VALUES (
        p_user_id, p_content_id, p_time_spent_seconds, p_completed, now()
    )
    ON CONFLICT (user_id, content_id) WHERE question_id IS NULL
    DO UPDATE SET
        time_spent_seconds = user_study_progress.time_spent_seconds + EXCLUDED.time_spent_seconds,
        completed = EXCLUDED.completed OR user_study_progress.completed,
        last_accessed = now(),
        updated_at = now()
    RETURNING id INTO v_progress_id;
    
    RETURN v_progress_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_content_progress IS 'Record user progress on study content';

-- Record question attempt
CREATE OR REPLACE FUNCTION record_question_attempt(
    p_user_id UUID,
    p_question_id UUID,
    p_answer TEXT,
    p_is_correct BOOLEAN
) RETURNS UUID AS $$
DECLARE
    v_progress_id UUID;
BEGIN
    -- Update question analytics
    UPDATE study_questions 
    SET times_shown = times_shown + 1,
        times_correct = times_correct + CASE WHEN p_is_correct THEN 1 ELSE 0 END
    WHERE id = p_question_id;
    
    -- Record user progress
    INSERT INTO user_study_progress (
        user_id, question_id, attempts, correct_attempts, last_answer, last_accessed
    ) VALUES (
        p_user_id, p_question_id, 1, 
        CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        p_answer, now()
    )
    ON CONFLICT (user_id, question_id) WHERE content_id IS NULL
    DO UPDATE SET
        attempts = user_study_progress.attempts + 1,
        correct_attempts = user_study_progress.correct_attempts + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        last_answer = p_answer,
        last_accessed = now(),
        updated_at = now()
    RETURNING id INTO v_progress_id;
    
    RETURN v_progress_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_question_attempt IS 'Record user question attempt with analytics';
