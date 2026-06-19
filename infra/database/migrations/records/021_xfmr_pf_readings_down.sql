-- =============================================================================
-- Records reconcile slice 1 / D-R1 - DOWN: strip the Doble raw-reading columns.
-- Removes test_kv / current_ma / watts / pf_corrected_pct from the power_factor
-- section's table.columns on both xfmr templates. Surgical (jsonb rebuild) and
-- idempotent (NOT IN filter is safe whether or not the columns are present);
-- leaves the 020 capture-mode wiring + the rest of the field_schema intact.
-- =============================================================================
BEGIN;
UPDATE records.form_templates t
SET field_schema = jsonb_set(
        t.field_schema,
        '{sections}',
        (SELECT jsonb_agg(
                  CASE WHEN s->>'key' = 'power_factor'
                       THEN jsonb_set(
                              s, '{table,columns}',
                              (SELECT COALESCE(jsonb_agg(col), '[]'::jsonb)
                               FROM jsonb_array_elements(s->'table'->'columns') col
                               WHERE col->>'tag' NOT IN
                                     ('test_kv', 'current_ma', 'watts', 'pf_corrected_pct')))
                       ELSE s END)
         FROM jsonb_array_elements(t.field_schema->'sections') s)),
    updated_at = now()
WHERE t.template_code IN ('ats_liquid_xfmr_v1', 'ats_dry_xfmr_v1') AND t.is_current;
COMMIT;
