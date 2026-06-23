-- 4b.1 backfill: bind ops.apparatus.equipment_model_ref for ONE target project,
-- resolvable rows only; leave the rest null. Idempotent, per-run snapshot, scoped.
\if :{?project_number}
\else
  \echo 'FATAL: pass -v project_number=<target project_number>'
  \quit
\endif

-- (0) aborting preflight: ops_dev + the project exists + EXACTLY the expected population.
-- NB: psql does NOT interpolate :'project_number' inside a dollar-quoted block, so stash
-- it in a session GUC first and read it via current_setting() inside the DO block.
select set_config('apex.backfill_project_number', :'project_number', false);
do $$
declare
  target_project_number text := current_setting('apex.backfill_project_number');
  v_apparatus int; v_projects int;
begin
  if current_database() <> 'ops_dev' then
    raise exception '4b1 backfill must run on ops_dev (got %)', current_database();
  end if;
  select count(*) into v_projects from ops.projects where project_number = target_project_number;
  if v_projects <> 1 then
    raise exception 'project_number % matched % rows (want exactly 1)', target_project_number, v_projects;
  end if;
  select count(*) into v_apparatus
    from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
   where p.project_number = target_project_number;
  if v_apparatus <> 5344 then
    raise exception 'project % apparatus=% (expected 5344) -- verify population before running', target_project_number, v_apparatus;
  end if;
end $$;

select gen_random_uuid() as run_id \gset

-- (1) per-run snapshot: one row per target null-ref apparatus, tagged with this run id.
create table if not exists ops.backfill_4b1_snapshot (
  run_id uuid not null, id uuid not null, prior_ref uuid, project_number text not null,
  snapped_at timestamptz not null default now(), primary key (run_id, id)
);
insert into ops.backfill_4b1_snapshot (run_id, id, prior_ref, project_number)
  select :'run_id'::uuid, a.id, a.equipment_model_ref, :'project_number'
    from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
   where p.project_number = :'project_number' and a.equipment_model_ref is null
on conflict (run_id, id) do nothing;

-- (2) bind resolvable rows to the TERMINAL-ACTIVE id (resolver-only), SCOPED to the project.
update ops.apparatus a set equipment_model_ref = v.resolved_id, updated_at = now()
  from core.v_equipment_models_resolved v, ops.scopes s, ops.projects p
 where v.requested_model_key = a.apparatus_type and s.id = a.scope_id and p.id = s.project_id
   and p.project_number = :'project_number' and a.equipment_model_ref is null;

-- (3) post-counts (scoped).
select count(*) filter (where a.equipment_model_ref is not null) as bound,
       count(*) filter (where a.equipment_model_ref is null)     as unbound, count(*) as total
  from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
 where p.project_number = :'project_number';

-- (4) plain miss report (always): each unresolved type + row count, scoped.
select a.apparatus_type, count(*) as rows
  from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
 where p.project_number = :'project_number' and a.equipment_model_ref is null
 group by 1 order by 2 desc;

\echo 'run_id (for rollback):'
select :'run_id' as run_id;
