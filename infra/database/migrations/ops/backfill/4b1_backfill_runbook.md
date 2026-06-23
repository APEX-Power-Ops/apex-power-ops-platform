# 4b.1 Backfill Runbook — `ops.apparatus.equipment_model_ref` (Miner-scoped)

> **Operator-gated.** Do NOT run until the 4b.1 PR is merged and operator has given explicit approval.
> The script is hard-scoped to `project_number='MINER-PHX-AB-MV'` and aborts if `current_database() <> 'ops_dev'` or the apparatus count ≠ 5344.

---

## Preconditions

1. **Migration 008 live:** `ops_dev` must have `core.equipment_models`, the merge-chasing resolver view `core.v_equipment_models_resolved`, and the nullable FK `ops.apparatus.equipment_model_ref` — all landed by mig 008.
2. **Safety dump first:** `docker exec apex-dev-pg pg_dump -U postgres -Fc ops_dev > ops_dev_pre_4b1_backfill_$(date +%Y%m%d).dump` — take this before running the script.
3. **Target:** `project_number = 'MINER-PHX-AB-MV'` ("Project Miner — PHX Bldg A & B MV"), 5344 apparatus, all frozen, all `provenance_status='approved'`.
4. **pg_trgm (optional triage only):** the steward triage query in the "Triage" section requires the `pg_trgm` extension. The apply role can run `create extension if not exists pg_trgm;` on `ops_dev` before the triage step. The main backfill script does NOT require pg_trgm.

---

## Apply

Run from the Olares host (or any host with `ssh olares-mesh` access):

```bash
cat infra/database/migrations/ops/backfill/4b1_bind_equipment_model_ref.sql \
  | ssh olares-mesh "docker exec -i apex-dev-pg psql -U postgres -d ops_dev \
      -v ON_ERROR_STOP=1 --single-transaction \
      -v project_number=MINER-PHX-AB-MV -f -"
```

The script aborts (`\quit` / `raise exception`) if:
- `-v project_number=...` is not passed
- `current_database()` is not `ops_dev`
- The project does not exist (matched rows ≠ 1)
- Apparatus count ≠ 5344

Because it runs `--single-transaction`, any abort rolls back the entire transaction.

**Expected post-count (re-derive at run time):**
```
 bound | unbound | total
-------+---------+-------
  4199 |    1145 |  5344
```
*(≈79% resolved — derived from live `ops_dev` characterization 2026-06-23. Preflight aborts if total ≠ 5344 so the count is verified before the bind.)*

The script prints a **run_id** at the end — record it for the rollback step.

---

## Miss Report

The script automatically emits a miss report (step 4): each `apparatus_type` with null `equipment_model_ref` after the bind, ordered by row count descending. Expected unresolved types (~1145 rows across 5 types):

| apparatus_type | rows |
|---|---|
| Conductors MV - Set of 3 (VLF & TD) | 983 |
| Vaccum Frequency Interrupter - VFI | 132 |
| Protective Relay - (Transfer Control) | 15 |
| Ground Resistance Test - Two-Point (One Day) | 12 |
| (Half Day) | 3 |

These feed the deferred 4b.4 catalog governance lane (alias/typo/service/true-new classification).

---

## Optional Steward Triage (requires pg_trgm)

Run separately after the backfill. Sources active keys from the resolver view only (no direct `core.equipment_models` read):

```sql
create extension if not exists pg_trgm;
with active_keys as (select distinct resolved_model_key as k from core.v_equipment_models_resolved)
select a.apparatus_type, count(*) as rows,
       (select k from active_keys order by similarity(k, a.apparatus_type) desc limit 1) as nearest_active_key,
       round((select max(similarity(k, a.apparatus_type)) from active_keys)::numeric, 3) as best_sim,
       case when a.apparatus_type ilike '%test%' or a.apparatus_type ilike '%resistance%' then 'service/non-catalog?'
            when (select max(similarity(k, a.apparatus_type)) from active_keys) > 0.6 then 'alias/typo-candidate (VERIFY hours)'
            else 'true-new-canonical?' end as classification
  from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
 where p.project_number = 'MINER-PHX-AB-MV' and a.equipment_model_ref is null
 group by a.apparatus_type order by rows desc;
```

**Important:** `Conductors MV - Set of 3 (...)` has six seed variants with hours 4.0–6.0h ATS — NOT a safe auto-alias. Classify, do not alias without steward review of the hours conflict. This is a 4b.4 decision, not a 4b.1 action.

---

## Verify Post-Run

```sql
-- Scoped post-counts (re-run to confirm):
select count(*) filter (where a.equipment_model_ref is not null) as bound,
       count(*) filter (where a.equipment_model_ref is null)     as unbound, count(*) as total
  from ops.apparatus a join ops.scopes s on s.id=a.scope_id join ops.projects p on p.id=s.project_id
 where p.project_number = 'MINER-PHX-AB-MV';

-- Snapshot row count (one per target null-ref apparatus per run):
select count(*) from ops.backfill_4b1_snapshot where project_number = 'MINER-PHX-AB-MV';
-- Expected: 5344 on the INITIAL run (all apparatus snapped before bind; prior_ref=null for every row).
--           A re-run snapshots only the still-null rows under a new run_id, so expect fewer.
```

---

## Rollback (run-id-bound)

Replace `<printed run_id>` with the UUID printed by the script at the end:

```sql
update ops.apparatus a set equipment_model_ref = sn.prior_ref, updated_at=now()
  from ops.backfill_4b1_snapshot sn where sn.id = a.id and sn.run_id = '<printed run_id>';
```

This restores each apparatus to its `prior_ref` (null for all Miner rows in the initial run). The snapshot persists in `ops.backfill_4b1_snapshot` — do not drop it until the 4b.4 governance lane is closed.

---

## Idempotency

The script is safe to re-run:
- The snapshot uses `on conflict (run_id, id) do nothing` — a second run gets a new `run_id` and snapshots only the still-null rows.
- The bind predicate `a.equipment_model_ref is null` is a no-op for already-bound rows.
- A second run with all rows already bound will produce `bound=4199, unbound=1145, total=5344` (same counts; the 1145 remain unresolved until 4b.4 governance adds aliases).
