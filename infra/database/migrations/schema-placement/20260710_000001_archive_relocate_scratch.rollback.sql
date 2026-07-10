-- ROLLBACK for A3 (01a). OPERATOR-GATED. Run as postgres (grantor fidelity). Never auto-runs.
-- Moves the 2 scratch tables back to public and restores anon+authenticated grants (ALL / arwdDxtm).
-- Does NOT drop schema `archive` (drop only if intentionally abandoning it AND it is empty).
BEGIN;
DO $$ BEGIN IF current_user <> 'postgres' THEN RAISE EXCEPTION 'run rollback as postgres (grantor fidelity)'; END IF; END $$;

DO $$
BEGIN
    IF to_regclass('archive._009_rollback_snapshot') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE archive._009_rollback_snapshot SET SCHEMA public';
    END IF;
    IF to_regclass('archive._phase3_load_manifest') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE archive._phase3_load_manifest SET SCHEMA public';
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public._009_rollback_snapshot') IS NOT NULL THEN
        EXECUTE 'GRANT ALL ON public._009_rollback_snapshot TO anon, authenticated';
    END IF;
    IF to_regclass('public._phase3_load_manifest') IS NOT NULL THEN
        EXECUTE 'GRANT ALL ON public._phase3_load_manifest TO anon, authenticated';
    END IF;
END $$;

-- DROP SCHEMA archive;  -- uncomment ONLY to intentionally abandon `archive` (must be empty)
COMMIT;
