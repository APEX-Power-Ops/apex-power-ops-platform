-- ============================================================================
-- Auth Ownership Transition Preparation
-- ============================================================================
-- Purpose:
--   Make the current demo-only anonymous write relaxation explicit so the live
--   schema no longer carries silent drift before Phase 5 auth wiring begins.
--
-- Current accepted posture:
--   - authenticated ownership is the target steady state
--   - anonymous rows are still temporarily allowed only for the internal
--     `project = 'neta-demo'` path
--   - future auth-phase migration will backfill or retire anonymous demo rows,
--     then tighten `user_id` back to NOT NULL
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.tcc_test_plans
        WHERE user_id IS NULL
          AND COALESCE(project, '') <> 'neta-demo'
    ) THEN
        RAISE EXCEPTION
            'Anonymous plans exist outside the allowed demo project boundary; resolve data before applying auth prep constraint';
    END IF;
END $$;

ALTER TABLE public.tcc_test_plans
    DROP CONSTRAINT IF EXISTS tcc_test_plans_demo_or_owned_ck;

ALTER TABLE public.tcc_test_plans
    ADD CONSTRAINT tcc_test_plans_demo_or_owned_ck
    CHECK (user_id IS NOT NULL OR project = 'neta-demo');

COMMENT ON COLUMN public.tcc_test_plans.user_id IS
    'Supabase auth.users ownership. Temporarily nullable only for internal demo rows where project = ''neta-demo'' until auth-phase enforcement lands.';

COMMENT ON TABLE public.tcc_test_plans IS
    'User test plans for breaker trip unit validation. Anonymous rows are temporarily permitted only for the internal demo project until auth-phase migration closes ownership enforcement.';