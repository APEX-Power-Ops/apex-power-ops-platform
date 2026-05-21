# Lane 502 Temp Power Scope Backfill

This directory holds the bounded Lane 502 runner for the Miner Temp Power scope backfill.

The runner enforces the frozen Lane 501 admission gate before any transaction opens:

1. Recompute the canonical reconciliation report hash.
2. Validate the intermediate JSON against the Lane 501 schema.
3. Re-verify the live Migration 016 floor.
4. Re-check the live baseline row counts and `seam.apparatus.scope_id` posture.
5. Validate the admission phrase from an environment variable.
6. Refuse the write if the frozen contract is not insertable into `seam.scopes`.

Run:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_502_temp_power_scope_backfill\run_lane_502_temp_power_scope_backfill.py
```

Prerequisites:

1. `DATABASE_URL`, `SEAM_DATABASE_URL`, or `LANE_502_TEMP_POWER_SCOPE_BACKFILL_ADMIN_DSN` must point at the governed production database.
2. `LANE_502_ADMISSION_PHRASE` must be set at execution time.
3. The frozen Lane 501 sample files must remain byte-stable.

Admission phrase format:

```text
LANE_502_TEMP_POWER_SCOPE_BACKFILL_ADMITTED
  RECONCILIATION_REPORT_HASH=1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130
  INTERMEDIATE_JSON_PATH=apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_intermediate_20260521T103643Z.json
  OPERATOR=<operator_name>
  TIMESTAMP=<iso8601_utc>
```

Outputs:

1. `output/scope_backfill_<timestamp>.json`
2. `output/scope_backfill_<timestamp>_idempotency_proof.json` for a successful second run only

Expected success criteria:

1. First run inserts 7 `seam.scopes` rows and updates 184 `seam.apparatus.scope_id` rows.
2. Second run inserts 0 scopes and updates 0 apparatus rows.
3. Financial tables, `seam.tasks`, and `public.*` row counts remain unchanged.

Current known blocker:

The frozen Lane 501 sample keeps `quoted_amount: null` for every proposed scope, while the live `seam.scopes` table created by Migration 015 requires `quoted_amount NUMERIC NOT NULL` and is insert-only. The runner therefore aborts pre-transaction against the current frozen sample instead of inventing irreversible values.

Safe rerun procedure:

1. Keep the same admitted phrase only when rerunning the same frozen Lane 501 artifacts.
2. If the first run aborts pre-transaction, inspect the emitted output artifact and resolve the blocking design/schema mismatch before retrying.
3. If a future run commits successfully, rerun immediately with `--idempotency-proof` to capture the zero-net-change proof artifact.