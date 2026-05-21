# PM Lane 500 Migration 016 Structural Supplement Closeout Handoff

Date: 2026-05-21

## Scope

Bounded live schema and privilege supplement for the blocked Lane 500 onboarding family.

This closeout covers only:

1. adding `seam.apparatus.scope_id`
2. adding the `seam.apparatus -> seam.scopes` foreign key and index
3. extending `pm` and `operations` grant posture on `seam.projects`, `seam.tasks`, and `seam.apparatus`
4. revoking `anon` and `authenticated` on those same tables
5. live verification of column shape, FK, index, grants, revokes, unchanged counts, and all-NULL `scope_id`

It does not cover any business-row write, scope backfill, JSONB normalization, route change, or first-write admission.

## Repo Changes

1. Added [016_seam_apparatus_scope_id_and_operational_grants.sql](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/migrations/016_seam_apparatus_scope_id_and_operational_grants.sql).
2. Added [run_migration_016_verification.py](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_500_migration_016/run_migration_016_verification.py).
3. Added [README.md](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_500_migration_016/README.md).
4. Added [migration_016_verification_20260521T040158Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_500_migration_016/output/migration_016_verification_20260521T040158Z.json).
5. Added [APEX-PM-LANE-500-MIGRATION-016-STRUCTURAL-SUPPLEMENT-NO-LIVE-PACKET-2026-05-21.md](c:/APEX%20Platform/apex-power-ops-platform/docs/operations/APEX-PM-LANE-500-MIGRATION-016-STRUCTURAL-SUPPLEMENT-NO-LIVE-PACKET-2026-05-21.md).
6. Added [2026-05-21-pm-lane-500-migration-016-structural-supplement-no-live-packet.json](c:/APEX%20Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-21-pm-lane-500-migration-016-structural-supplement-no-live-packet.json).
7. Updated [PROJECT_STATUS.md](c:/APEX%20Platform/apex-power-ops-platform/PROJECT_STATUS.md).

## Live Validation Commands

Migration application:

```powershell
$script = @'
from pathlib import Path
import os
import psycopg2

migration_path = Path(r'apps/mutation-seam/migrations/016_seam_apparatus_scope_id_and_operational_grants.sql')
sql_text = migration_path.read_text(encoding='utf-8')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
try:
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()
    print('MIGRATION_016_STATUS applied')
finally:
    conn.close()
'@; .\.venv\Scripts\python.exe -c $script
```

Verification rerun:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_500_migration_016\run_migration_016_verification.py
```

## Live Validation Results

1. The live migration application returned `MIGRATION_016_STATUS applied`.
2. The verification rerun returned `overall_status = passed` and wrote `apps/mutation-seam/scripts/lane_500_migration_016/output/migration_016_verification_20260521T040158Z.json`.
3. The passing artifact proves:
   - `seam.apparatus.scope_id` exists as nullable `TEXT`
   - `apparatus_scope_id_fkey` targets `seam.scopes(id)`
   - `apparatus_scope_id_idx` exists
   - `pm` and `operations` each have `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus`
   - `anon` and `authenticated` do not retain those privileges
   - seam totals remain `projects=1`, `tasks=15`, `apparatus=184`, and `scopes=0`
   - all `184` current `seam.apparatus.scope_id` values remain `NULL`

## Final Verdict

PM Lane 500 migration 016 structural supplement is closed and live.

The minimum relational and grant floor is now present for later onboarding redesign work, but the broader Lane 500 onboarding lane remains separately blocked and no-live.

## Guardrails Preserved

1. No production business-row insert or update was performed.
2. No `scope_id` backfill was performed.
3. No JSONB payload was normalized or rewritten.
4. No route-path or persistence-module change was deployed.
5. No first-write admission phrase was minted.