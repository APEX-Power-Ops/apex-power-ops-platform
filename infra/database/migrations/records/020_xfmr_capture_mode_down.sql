-- =============================================================================
-- Records Chip 10a (Phase 1) - DOWN: strip the capture-mode wiring from the xfmr templates.
-- Restores capture=null and removes capture_mode/import from the four PTM sections.
-- Reversible; leaves the rest of the 012 transformer field_schema intact.
-- =============================================================================
BEGIN;
-- 1. drop the template-level capture block
UPDATE records.form_templates
SET field_schema = (field_schema - 'capture'),
    updated_at = now()
WHERE template_code IN ('ats_liquid_xfmr_v1', 'ats_dry_xfmr_v1') AND is_current;

-- 2. strip capture_mode + import from the four PTM sections (rebuild the sections array)
UPDATE records.form_templates t
SET field_schema = jsonb_set(
        t.field_schema,
        '{sections}',
        (SELECT jsonb_agg(
                  CASE WHEN s->>'key' IN ('turns_ratio', 'winding_resistance', 'power_factor', 'excitation_current')
                       THEN (s - 'capture_mode' - 'import')
                       ELSE s END)
         FROM jsonb_array_elements(t.field_schema->'sections') s)),
    updated_at = now()
WHERE t.template_code IN ('ats_liquid_xfmr_v1', 'ats_dry_xfmr_v1') AND t.is_current;
COMMIT;
