# PM Lane 421 Schema Architecture Correction Closeout Handoff

Date: 2026-05-21

## Scope

Bounded live schema correction for the Dataverse-era `public.scopes` assumption on the seam financial tables.

This closeout covers only:

1. creation of `seam.scopes` as the operational scope anchor
2. retargeting seam-side financial `scope_id` foreign keys from `public.scopes` to `seam.scopes`
3. live verification of the new table, the retargeted foreign keys, and the corrected column types
4. update of the rollback-only Lane 421 probe helper so future reruns target `seam.scopes`

It does not cover any business-row insert, onboarding backfill, route implementation change, or first-write admission.

## Repo Changes

1. Added `apps/mutation-seam/migrations/015_seam_scopes_addition_and_fk_retarget.sql`.
2. Added `apps/mutation-seam/scripts/lane_421_schema_correction/run_lane_421_schema_correction_verification.py`.
3. Added `apps/mutation-seam/scripts/lane_421_schema_correction/README.md`.
4. Added `apps/mutation-seam/scripts/lane_421_schema_correction/output/schema_correction_verification_20260521T023011Z.json`.
5. Updated `apps/mutation-seam/scripts/lane_421_grant_verification/run_lane_421_atomic_transaction_probe.py`.
6. Updated `apps/mutation-seam/scripts/lane_421_grant_verification/README.md`.
7. Added `docs/operations/APEX-PM-LANE-421-SCHEMA-ARCHITECTURE-CORRECTION-PUBLIC-TO-SEAM-FK-RETARGET-NO-LIVE-PACKET-2026-05-21.md`.
8. Updated `docs/operations/APEX-PM-LANE-412-REVISION-B-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md` with the Correction Note.
9. Updated `PROJECT_STATUS.md`.

## Production Facts Applied

1. `seam.scopes` did not exist before this handoff.
2. `seam.projects.id` and `seam.apparatus.id` were already `TEXT`, while the seam-side financial `scope_id` columns were still `UUID` and pointed at `public.scopes.id`.
3. All four existing financial tables were empty before the retarget.
4. Migration 015 created `seam.scopes` live with `TEXT` primary key, `project_id -> seam.projects(id)`, insert-only triggers, RLS, and PM/Operations `SELECT` plus `INSERT` grants.
5. Migration 015 retargeted `seam.scope_labor_details.scope_id` and `seam.apparatus_revenue_events.scope_id` to `seam.scopes(id)` and converted both columns from `UUID` to `TEXT`.
6. `public.*` legacy tables that still reference `public.scopes.id` were surfaced during discovery but were intentionally left untouched.

## Live Validation Commands

Migration application:

```powershell
$script = @'
from pathlib import Path
import os
import psycopg2

migration_path = Path(r'apps/mutation-seam/migrations/015_seam_scopes_addition_and_fk_retarget.sql')
sql_text = migration_path.read_text(encoding='utf-8')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
try:
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()
    print('MIGRATION_015_STATUS applied')
finally:
    conn.close()
'@; .\.venv\Scripts\python.exe -c $script
```

Verification rerun:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_421_schema_correction\run_lane_421_schema_correction_verification.py
```

## Live Validation Results

1. The live migration application returned `MIGRATION_015_STATUS applied`.
2. The verification rerun returned `overall_status = passed` and wrote `apps/mutation-seam/scripts/lane_421_schema_correction/output/schema_correction_verification_20260521T023011Z.json`.
3. The passing artifact proves:
   - `seam.scopes` exists and row count is `0`
   - `seam.scope_labor_details.scope_id` targets `seam.scopes.id`
   - `seam.apparatus_revenue_events.scope_id` targets `seam.scopes.id`
   - both seam-side `scope_id` columns are `TEXT`
   - `pm` and `operations` retain `USAGE` on schema `seam` plus `SELECT` and `INSERT` on `seam.scopes`

## Verification Nuance

1. The verifier attempted live role-session probes for `pm` and `operations` but the governed admin DSN cannot `SET ROLE` or `SET SESSION AUTHORIZATION` to those `NOLOGIN` roles.
2. The final passing artifact therefore records `probe_mode = privilege_metadata_only` for both roles and verifies their access through `pg_roles`, `has_schema_privilege`, and `has_table_privilege` metadata instead of a role-session row-count query.
3. This is a verifier limitation, not a schema failure; the FK and type retarget itself verified cleanly.

## Final Verdict

PM Lane 421 Schema Architecture Correction is closed and live.

The seam financial surface no longer depends on the legacy `public.scopes` tier for new-project scope anchors. The next blocker is no longer architectural. The next blocker is operational onboarding: a later lane must populate real Miner Temp Power rows in `seam.projects`, `seam.scopes`, and `seam.apparatus` before the corrected rollback-only Lane 421 probe can run.

## Guardrails Preserved

1. No production business-row insert or update was performed.
2. No write was made to `public.*`.
3. No route-path or persistence-module change was deployed.
4. No existing migration file was edited in place.
5. No secret value was added to repo files.
6. No Lane 422 admission phrase was minted.