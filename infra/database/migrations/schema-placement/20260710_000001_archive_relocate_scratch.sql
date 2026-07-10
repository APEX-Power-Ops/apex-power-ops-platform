-- 20260710_000001_archive_relocate_scratch.sql   (lane: infra/database/migrations/schema-placement/)
-- Schema-Placement Packet 01 / ACTION A3 (01a): create/harden `archive`; relocate 2 inert scratch tables.
-- APPLY: raw `psql -v ON_ERROR_STOP=1 -f <this file>` ONLY, one action per invocation.
-- retain-and-relocate ONLY (retention is a SEPARATE open decision). `archive` stays OFF the PostgREST exposed list.
-- Idempotent; re-run safe (guarded SET SCHEMA). Rollback: 20260710_000001_archive_relocate_scratch.rollback.sql.
BEGIN;

CREATE SCHEMA IF NOT EXISTS archive AUTHORIZATION postgres;

COMMENT ON SCHEMA archive IS 'Non-authoritative holding for superseded/inert artifacts. Schema-role (OPERATING-ARCHITECTURE 2.8): NOT part of the canonical apparatus/equipment identity graph; no identity FK required. NOT exposed on the PostgREST Data API. schema-placement packet 01a, 2026-07-10.';

REVOKE ALL ON SCHEMA archive FROM PUBLIC;
REVOKE ALL ON SCHEMA archive FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA archive REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;

DO $$
BEGIN
    IF to_regclass('public._009_rollback_snapshot') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public._009_rollback_snapshot SET SCHEMA archive';
    END IF;
    IF to_regclass('public._phase3_load_manifest') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public._phase3_load_manifest SET SCHEMA archive';
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('archive._009_rollback_snapshot') IS NOT NULL THEN
        EXECUTE 'REVOKE ALL ON archive._009_rollback_snapshot FROM PUBLIC, anon, authenticated';
    END IF;
    IF to_regclass('archive._phase3_load_manifest') IS NOT NULL THEN
        EXECUTE 'REVOKE ALL ON archive._phase3_load_manifest FROM PUBLIC, anon, authenticated';
    END IF;
END $$;

-- Assert: both objects in archive (not public); anon+authenticated hold no effective privilege (all verbs).
DO $$
DECLARE
    obj  text;
    objs text[];
    role text;
    priv text;
    bad  text[] := '{}';
BEGIN
    IF to_regclass('public._009_rollback_snapshot') IS NOT NULL THEN bad := bad || 'still-in-public:_009_rollback_snapshot'::text; END IF;
    IF to_regclass('public._phase3_load_manifest')  IS NOT NULL THEN bad := bad || 'still-in-public:_phase3_load_manifest'::text; END IF;
    IF to_regclass('archive._009_rollback_snapshot') IS NULL THEN bad := bad || 'missing-in-archive:_009_rollback_snapshot'::text; END IF;
    IF to_regclass('archive._phase3_load_manifest')  IS NULL THEN bad := bad || 'missing-in-archive:_phase3_load_manifest'::text; END IF;
    objs := ARRAY[]::text[];
    IF to_regclass('archive._009_rollback_snapshot') IS NOT NULL THEN objs := objs || 'archive._009_rollback_snapshot'::text; END IF;
    IF to_regclass('archive._phase3_load_manifest')  IS NOT NULL THEN objs := objs || 'archive._phase3_load_manifest'::text; END IF;
    FOREACH obj IN ARRAY objs LOOP
        FOREACH role IN ARRAY ARRAY['anon','authenticated'] LOOP
            FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE'] LOOP
                IF has_table_privilege(role, obj, priv) THEN bad := bad || (role||':'||obj||':'||priv); END IF;
            END LOOP;
        END LOOP;
    END LOOP;
    IF array_length(bad,1) IS NOT NULL THEN
        RAISE EXCEPTION '01a FAILED: %', bad;
    END IF;
END $$;

COMMIT;
