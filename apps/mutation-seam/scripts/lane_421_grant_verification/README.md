# Lane 421 Grant Verification

This directory contains the rerunnable operator scripts for PM Lane 421.

Scope:

1. `run_lane_421_grant_verification.py` verifies the executable Lane 411 Revision C grant contract after migration `014_pm_lane_411_revision_c_role_contract_grants.sql` is applied.
2. `run_lane_421_atomic_transaction_probe.py` proves the five-target write contract can stage one row in each target and then leave zero residue after rollback.

Environment:

1. Both scripts require an administrative Postgres DSN because they query `pg_roles`, inspect financial-table grants, and, for the atomic probe, open one rollback-only transaction.
2. Preferred env var: `LANE_421_ADMIN_DSN`.
3. Fallback env vars supported by the scripts: `SEAM_DATABASE_URL`, `DATABASE_URL`.
4. Do not commit DSNs, passwords, or copied SQL-editor connection strings into repo files or shell history.

Suggested sequence:

1. Apply `apps/mutation-seam/migrations/014_pm_lane_411_revision_c_role_contract_grants.sql` in the governed privileged surface.
2. Apply `apps/mutation-seam/migrations/015_seam_scopes_addition_and_fk_retarget.sql` in the governed privileged surface before attempting the atomic probe.
3. Run grant verification:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_421_grant_verification\run_lane_421_grant_verification.py
```

4. Discover one existing `seam.scopes.id` and one existing `seam.apparatus.id` tied to the imported Temp Power project.
5. Run the rollback-only atomic probe:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_421_grant_verification\run_lane_421_atomic_transaction_probe.py --scope-id <uuid> --apparatus-id <text-id>
```

Notes:

1. The atomic probe now expects the operational `seam.scopes.id` anchor introduced by migration `015_seam_scopes_addition_and_fk_retarget.sql`.
2. The atomic probe uses a generated `change_order_<digits>` snapshot kind so it does not collide with the existing `(project_id, snapshot_kind)` uniqueness rule on `seam.project_contract_snapshots`.
3. The probe intentionally inserts into `seam.idempotency_keys` as the fifth atomic target and always rolls back.
4. Output artifacts are written under `apps/mutation-seam/scripts/lane_421_grant_verification/output/` unless `--output-file` is supplied.