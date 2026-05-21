# Lane 421 Schema Architecture Correction Verification

This directory contains the rerunnable verification surface for the PM Lane 421 schema architecture correction.

Scope:

1. Apply `apps/mutation-seam/migrations/015_seam_scopes_addition_and_fk_retarget.sql` through the governed privileged database path.
2. Verify `seam.scopes` exists and remains empty after migration.
3. Verify `pm` and `operations` can `SELECT count(*)` from `seam.scopes` without permission errors.
4. Verify `seam.scope_labor_details.scope_id` and `seam.apparatus_revenue_events.scope_id` now target `seam.scopes(id)` and use `TEXT`, not `UUID`.

Environment:

1. Preferred env var: `LANE_421_SCHEMA_CORRECTION_ADMIN_DSN`.
2. Fallback env vars: `SEAM_DATABASE_URL`, `DATABASE_URL`.
3. Do not commit DSNs, passwords, or copied connection strings into repo files or shell history.

Run:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_421_schema_correction\run_lane_421_schema_correction_verification.py
```

Output:

1. Verification artifacts are written under `apps/mutation-seam/scripts/lane_421_schema_correction/output/` unless `--output-file` is supplied.
2. The script performs read-only verification and emits a structured JSON summary of table existence, role checks, FK targets, and column types.