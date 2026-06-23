-- ============================================================================
-- ops Step 4a APPLY PREFLIGHT — ops_dev only. Run in the SAME -1 txn as 008.
-- Any failed precondition raises -> full rollback -> zero writes. Not in the test gate.
-- ============================================================================
do $$
begin
  if current_database() <> 'ops_dev' then
    raise exception 'preflight: refusing apply, current_database()=% (expected ops_dev)', current_database();
  end if;
  if exists (select 1 from information_schema.schemata where schema_name='core') then
    raise exception 'preflight: core schema already exists (008 already applied?)';
  end if;
  if (select count(equipment_model_ref) from ops.apparatus) <> 0 then
    raise exception 'preflight: ops.apparatus has % non-null equipment_model_ref rows -- FK not additive, STOP',
      (select count(equipment_model_ref) from ops.apparatus);
  end if;
  raise notice 'preflight ok: ops_dev / no core schema / 0 non-null equipment_model_ref';
end $$;
