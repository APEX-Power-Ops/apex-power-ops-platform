# Lane 500 Migration 016 Structural Supplement Verification

This directory contains the rerunnable verification surface for the PM Lane 500 migration 016 structural supplement.

Scope:

1. Verify `seam.apparatus.scope_id` exists as nullable `TEXT`.
2. Verify `seam.apparatus.scope_id` targets `seam.scopes(id)`.
3. Verify index `apparatus_scope_id_idx` exists.
4. Verify `pm` and `operations` have `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus`.
5. Verify `anon` and `authenticated` do not retain those table privileges.
6. Verify seam row counts remain unchanged at `projects=1`, `tasks=15`, `apparatus=184`, and `scopes=0`.
7. Verify all current `seam.apparatus.scope_id` values remain `NULL`.

Environment:

1. Preferred env var: `LANE_500_MIGRATION_016_ADMIN_DSN`.
2. Fallback env vars: `SEAM_DATABASE_URL`, `DATABASE_URL`.
3. Do not commit DSNs, passwords, or copied connection strings into repo files or shell history.

Run:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_500_migration_016\run_migration_016_verification.py
```

Output:

1. Verification artifacts are written under `apps/mutation-seam/scripts/lane_500_migration_016/output/` unless `--output-file` is supplied.
2. The script performs read-only verification and emits a structured JSON summary of the column, FK, index, role privileges, revokes, row counts, and all-NULL `scope_id` posture.