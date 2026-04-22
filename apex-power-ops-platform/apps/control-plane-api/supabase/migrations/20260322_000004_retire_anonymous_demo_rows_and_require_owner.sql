-- Retire legacy anonymous demo plans now that backend write routes require
-- authenticated identity, then restore user_id as a required ownership field.

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM tcc_test_results r
    JOIN tcc_test_plans p ON p.id = r.plan_id
    WHERE p.user_id IS NULL
  ) THEN
    RAISE EXCEPTION 'Cannot retire anonymous demo rows while anonymous results still exist';
  END IF;

  DELETE FROM tcc_test_plans
  WHERE user_id IS NULL
    AND project = 'neta-demo';

  IF EXISTS (
    SELECT 1
    FROM tcc_test_plans
    WHERE user_id IS NULL
  ) THEN
    RAISE EXCEPTION 'Cannot restore NOT NULL on tcc_test_plans.user_id while null owners remain';
  END IF;
END $$;

ALTER TABLE public.tcc_test_plans
  ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE public.tcc_test_plans
  DROP CONSTRAINT IF EXISTS tcc_test_plans_demo_or_owned_ck;

COMMENT ON COLUMN public.tcc_test_plans.user_id IS
  'Supabase auth ownership. Required for all steady-state plan writes.';

COMMENT ON TABLE public.tcc_test_plans IS
  'User-created test plans with authenticated Supabase ownership.';