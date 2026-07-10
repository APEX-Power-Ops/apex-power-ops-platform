-- fingerprint.sql -- deterministic, sorted text fingerprint of the surface that
-- A1/A2/A3 mutate. Run with:  psql -tA -d <db> < fingerprint.sql
-- Covers: anon+authenticated table privileges (8 mcp objects always in public;
-- the guarded 7th + 2 scratch tables resolved by pg_class OID so schema moves are
-- tracked), the scratch tables' schema, policy-name set on the mcp tables, and the
-- 6 table comments. Identical output at baseline and after up->down proves reversal.
SELECT line FROM (
    -- 8 mcp objects (always public): anon+authenticated x SELECT/INSERT/UPDATE/DELETE
    SELECT format('PRIV|%s|%s|%s|%s', r.role, o.obj, v.verb,
                  has_table_privilege(r.role, o.obj, v.verb)::text) AS line
    FROM (VALUES ('anon'),('authenticated')) r(role)
    CROSS JOIN (VALUES
        ('public.mcp_job_runs'),('public.mcp_lane_priorities'),('public.mcp_local_action_queue'),
        ('public.mcp_review_decisions'),('public.mcp_task_packets'),('public.mcp_validation_artifacts'),
        ('public.mcp_job_run_summary_v'),('public.mcp_task_packet_summary_v')) o(obj)
    CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb)

    UNION ALL
    -- conditional tables (guarded 7th + 2 scratch): privileges via OID (schema-agnostic)
    SELECT format('XPRIV|%s|%s|%s|%s', r.role, c.relname, v.verb,
                  has_table_privilege(r.role, c.oid, v.verb)::text) AS line
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN (VALUES ('anon'),('authenticated')) r(role)
    CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')) v(verb)
    WHERE c.relkind='r'
      AND c.relname IN ('mcp_external_action_audits','_009_rollback_snapshot','_phase3_load_manifest')

    UNION ALL
    -- scratch-table schema location
    SELECT format('SCHEMA|%s|%s', c.relname, n.nspname) AS line
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind='r'
      AND c.relname IN ('_009_rollback_snapshot','_phase3_load_manifest')

    UNION ALL
    -- policy-name set on the mcp tables (6 core + guarded 7th)
    SELECT format('POLICY|%s|%s', c.relname, p.polname) AS line
    FROM pg_policy p
    JOIN pg_class c ON c.oid = p.polrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname='public'
      AND c.relname IN ('mcp_job_runs','mcp_lane_priorities','mcp_local_action_queue',
                        'mcp_review_decisions','mcp_task_packets','mcp_validation_artifacts',
                        'mcp_external_action_audits')

    UNION ALL
    -- the 6 table comments
    SELECT format('COMMENT|%s|%s', c.relname, COALESCE(obj_description(c.oid,'pg_class'),'<null>')) AS line
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname='public' AND c.relkind='r'
      AND c.relname IN ('mcp_job_runs','mcp_lane_priorities','mcp_local_action_queue',
                        'mcp_review_decisions','mcp_task_packets','mcp_validation_artifacts')
) t
ORDER BY line;
