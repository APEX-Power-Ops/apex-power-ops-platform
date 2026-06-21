-- Slice 2d NON-DESTRUCTIVE reversal: deactivate the rehearsal cohort. NEVER delete (FK cascade into
-- the immutable learning_events ledger trips the append-only trigger -- evidence is immutable).
do $$ begin
  if current_database() not in ('learning_dev','learning_test') then
    raise exception 'Slice 2d retire refuses to run on %; expected learning_dev/learning_test', current_database();
  end if;
end $$;
update public.user_profiles set is_active = false
where id = 'a0000000-2d00-4000-8000-000000000001';
