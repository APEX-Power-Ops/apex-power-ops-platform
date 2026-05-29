# ETU INST/GFPU Tolerance Helper Live Cutover - Closeout

Date: 2026-05-29
Status: PASS
Lane: TCC Runtime 017 ETU (matrix #83) - data-integrity branch 3(a), corrected
Purpose: Record the governed live application of the corrected ETU evaluate-helper migration and the resulting parity proof

---

## 1. Repo Alignment

Execution started from the pushed repo state already requested by the dispatch.

Verified:

- local branch: `main`
- `HEAD`: `ad79bc4d`
- `origin/main`: `ad79bc4d`
- `git merge --ff-only origin/main`: already up to date

Migration body confirmed before any DB action:

- `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`
- normal-mode pickup tolerance reads straight from the table columns:
  - `eff_inst_tol_lo := ctx.inst_tol_lo;`
  - `eff_inst_tol_hi := ctx.inst_tol_hi;`
  - `eff_gfpu_tol_lo := ctx.gfpu_tol_lo;`
  - `eff_gfpu_tol_hi := ctx.gfpu_tol_hi;`
- no `COALESCE(..., -10)` / `COALESCE(..., 10)` fallback remains for INST or GFPU

Credential handling note:

- the governed DSN was loaded with `dotenv_values('.env.local')`, not shell string-splitting, to avoid the stale-shadow / quoted-value parse failure seen earlier
- no secret value was printed or persisted

---

## 2. Required Dry-Run Gate

The dispatch-required PATTERN-006 dry-run was executed first in a single rollback-only transaction against the governed live DSN.

Method:

1. load the corrected `20260528_000011_reapply_etu_evaluate_function.sql` into one SQL transaction
2. call the live route at `http://127.0.0.1:8010/api/v1/neta/evaluate`
3. call `public.fn_evaluate_test_results(...)` in the same uncommitted transaction
4. compare the route-owned pickup bands and pass/fail states for all committed ETU matrix scenarios
5. roll the transaction back

Dry-run result: PASS

Scenario summary:

- `sensor-25-ge-mvt-rms9-800-normal`: matched
  - route overall pass: `false`
  - helper overall pass: `false`
  - truthful STPU-only fail preserved
- `sensor-26-ge-mvt-rms9-600-live-derived`: matched
  - route overall pass: `true`
  - helper overall pass: `true`
  - no regression
- `sensor-17892-abb-ekip-dip-lvpcb-lsi-100-live-derived`: matched
  - route overall pass: `false`
  - helper overall pass: `false`
  - INST parity repaired inside the transaction

The targeted sensor `17892` dry-run helper output was:

- `INST.limit_low = 127.5`
- `INST.limit_high = 172.5`
- `INST.pass = true`

This satisfied the cutover gate, so live apply proceeded.

---

## 3. Live Apply

Applied live:

- `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`

Method:

- governed DSN via `dotenv_values('.env.local')`
- SQLAlchemy transaction with `engine.begin()`
- migration executed as repo-tracked SQL text
- result: `LIVE_APPLY_OK`

Operational classification remained benign for deployed behavior:

- function applied was `CREATE OR REPLACE`
- helper surface is parity / maintenance only
- route-owned ETU contract remained in Python
- no route edit, no hosted deployment, no TMT/EMT widening, no schema widening beyond this one already-tracked migration

---

## 4. Post-Apply Proof

Post-apply validation command:

- `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`

Result:

- `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0`

Artifact:

- `output/dev/control-plane-live-etu-sql-parity.json`

Before -> after:

- before live apply: `2 pass / 1 warn`
- after live apply: `3 pass / 0 warn`

Artifact summary after live apply:

- `pass_count: 3`
- `scenario_count: 3`
- `warn_count: 0`
- `warning_count: 0`
- `blocked_requirements: []`

No-regression confirmation from the artifact:

- sensor `25`
  - parity status: `pass`
  - API and SQL `overall_pass`: `0.0`
  - truthful STPU-only fail preserved
- sensor `26`
  - parity status: `pass`
  - API and SQL `overall_pass`: `1.0`
  - unchanged success behavior
- sensor `17892`
  - parity status: `pass`
  - API and SQL INST band now both `127.5 / 172.5`
  - evaluate-side warning cleared

---

## 5. Advisor Sweep

Supabase advisors were rerun after live apply.

Observed result:

- no new blocker tied to this migration
- baseline remained info-level only

Representative baseline items observed:

- security: `rls_enabled_no_policy`
- performance: `unindexed_foreign_keys`

This matched the dispatch expectation.

---

## 6. Outcome

The ETU INST reconciliation lane is now closed truthfully for the admitted scope.

Closed result:

- live helper surface updated
- sensor `17892` evaluate parity warning removed
- matrix artifact moved from `2/1` to `3/0`
- sensors `25` and `26` stayed behavior-stable
- route remained untouched

Out of scope but noted by dispatch:

- the separate LTPU/STPU tolerance fallback characterization remains a later packet and was not touched here
