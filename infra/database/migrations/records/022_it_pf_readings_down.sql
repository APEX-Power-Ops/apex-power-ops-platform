-- =============================================================================
-- Records reconcile slice 2 / D-R1 generalized - DOWN: strip the IT PF/DF additions.
-- (1) remove current_ma + pf_corrected_pct from every IT PF/DF section (handles both
--     fields-kind (ct/vt power_factor) and table-kind (cvt capacitance_pf)).
-- (2) remove ONLY the cap_pf that 022 added to vt.power_factor - CT's native cap_pf
--     must survive, so that strip is scoped to ats_vt_v1.
-- Surgical + idempotent (NOT IN / <> safe whether or not the tags are present);
-- leaves the 015 capture-mode/import wiring + the rest of the field_schema intact.
-- =============================================================================
BEGIN;

-- (1) current_ma + pf_corrected_pct, all three IT templates, fields OR table.columns
UPDATE records.form_templates t
SET field_schema = jsonb_set(
        t.field_schema, '{sections}',
        (SELECT jsonb_agg(
                  CASE WHEN s->>'key' IN ('power_factor', 'capacitance_pf') THEN (
                         CASE WHEN s ? 'fields'
                              THEN jsonb_set(s, '{fields}',
                                     (SELECT COALESCE(jsonb_agg(f), '[]'::jsonb)
                                      FROM jsonb_array_elements(s->'fields') f
                                      WHERE f->>'tag' NOT IN ('current_ma', 'pf_corrected_pct')))
                              ELSE jsonb_set(s, '{table,columns}',
                                     (SELECT COALESCE(jsonb_agg(c), '[]'::jsonb)
                                      FROM jsonb_array_elements(s->'table'->'columns') c
                                      WHERE c->>'tag' NOT IN ('current_ma', 'pf_corrected_pct')))
                         END)
                       ELSE s END)
         FROM jsonb_array_elements(t.field_schema->'sections') s)),
    updated_at = now()
WHERE t.template_code IN ('ats_ct_v1', 'ats_vt_v1', 'ats_cvt_v1') AND t.is_current;

-- (2) the cap_pf 022 added to VT only (CT had cap_pf natively - leave it)
UPDATE records.form_templates t
SET field_schema = jsonb_set(
        t.field_schema, '{sections}',
        (SELECT jsonb_agg(
                  CASE WHEN s->>'key' = 'power_factor'
                       THEN jsonb_set(s, '{fields}',
                              (SELECT COALESCE(jsonb_agg(f), '[]'::jsonb)
                               FROM jsonb_array_elements(s->'fields') f
                               WHERE f->>'tag' <> 'cap_pf'))
                       ELSE s END)
         FROM jsonb_array_elements(t.field_schema->'sections') s)),
    updated_at = now()
WHERE t.template_code = 'ats_vt_v1' AND t.is_current;

COMMIT;
