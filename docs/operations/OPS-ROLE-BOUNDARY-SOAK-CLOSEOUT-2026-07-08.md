# ops_app role-boundary -- STRUCTURAL SOAK CLOSEOUT (2026-07-08)

**Lane:** ops_app role boundary (migration `infra/database/migrations/ops/012_ops_app_role_boundary.sql`).
**Soak opened:** 2026-07-02 (012 applied to ops_dev; PR #55/#56 merged). **Operator direction
2026-07-08:** "mark it structurally closed now, then run one functional role pass to close it fully."
This record is that pass + the disposition. **Companion apply-time record:**
`docs/operations/OPS-ROLE-BOUNDARY-012-OPS-DEV-APPLY-RECORD-2026-07-02.md` (Sections 3/4/5/8 cited below).
**Reproducible harness (committed with this record):** `docs/operations/ops-role-pass-2026-07-08.py`.

## What this IS / is NOT
- IS: a point-in-time STRUCTURAL re-confirmation that the 012 boundary still holds on ops_dev, by a
  two-oracle harness, ~6 days after apply. Plus the app mount-gate and the chip5 retire fixture-gate.
- IS NOT a load-soak: **no serving-path role DSN exists for a persistent ops DB** (see Finding, Sec 6);
  **zero live role/serving traffic hit ops_dev in the interval.** The roles reach ops_dev only because
  this harness overrides the DSN dbname in-process (roles are cluster-global). This is the SAME static
  proof as apply-time, re-run once at day 6 -- day-0 and day-6 postures are identical.

## Substrate (frames the D8 gap)
ops_dev = the `apex-dev-pg` PostgreSQL 17 container. Tables in schema `ops` are owned by `postgres`
(a **superuser** on dev). The tested principals `ops_api` / `ops_intake_writer` are **non-superuser**
login roles. Prod (D8) differs on exactly these axes (managed `postgres` is NOT superuser; tables not
super-owned) -- so this dev proof does not transfer to prod for ownership/RI/RLS/pooler behavior.

## 1. Method
Value-silent psycopg harness. Each role DSN is retargeted to ops_dev by parsing it to a params mapping
(`conninfo_to_dict`) and replacing only the `dbname` key (the URL is never re-formatted with the
secret; the password is never printed). Every write runs in an always-rolled-back txn. TWO independent
oracles per claim so neither a broad error code nor a stale grant yields a false green:
- **behavioral** -- attempt in a rolled-back txn; classify SQLSTATE: `ACL_DENY`=42501,
  `MISSING`=42P01/3F000/42883/42704, `REACHED`=ok or a downstream data/business error.
- **catalog-exact** -- `has_schema_privilege` / `has_table_privilege` / `has_function_privilege` as the
  connected role (an exact privilege, not a collapsed error).
**Value-silence on failure:** connect / probe / catalog / assertion failures emit ONLY a SQLSTATE class
or a precomputed boolean; no `str(e)`, DSN, or env dict is ever printed.

## 2. Results -- ops_dev, 18/18 (2 identity + 7 behavioral + 9 catalog; oracles agree on every one)
Identity binds: **I0** `ops_intake_writer@ops_dev`, **I1** `ops_api@ops_dev`.

| # | assertion | behavioral | catalog-exact |
|---|-----------|-----------|---------------|
| W1 / C2 | writer CAN write intake surface (ops.intake_runs) | REACHED | INSERT=true |
| W2 / C3 | writer CANNOT write recognition table directly | ACL_DENY | INSERT=false |
| W3 / C4 | writer CANNOT invoke recognition SECDEF fn | ACL_DENY | EXECUTE=false |
| C1 | writer USAGE on schema ops | (n/a) | USAGE=true |
| A1 / C6 | api CAN read its recognition view | REACHED | SELECT=true |
| A2 / C7 | api CANNOT read out-of-scope table (ops.projects) | ACL_DENY | SELECT=false |
| A3 / C8 | api CANNOT write recognition table directly | ACL_DENY | INSERT=false |
| A4 / C9 | api CAN invoke recognition SECDEF fn | REACHED | EXECUTE=true |
| C5 | api USAGE on schema ops | (n/a) | USAGE=true |

Behavioral count = 7 (W1-W3, A1-A4); catalog count = 9 (C1-C9); identity = 2 (I0-I1). Total 18, all PASS.
RESIDUE: **zero committed rows from THIS pass** (all writes rolled back). See Sec 5 on pre-existing residue.

## 3. Which artifact ran against which target
| artifact | target | note |
|----------|--------|------|
| boundary matrix (18 checks) | **ops_dev** (via in-process dbname override) | where 012 is applied |
| mount-gate `test_ops_route_mount_gate.py` | **no DB** (unit; monkeypatched env + subprocess) | pure enable/route logic |
| chip5 fixture parity | **no DB** (git compare of test fixtures) | retire gate |

**Mount-gate:** 2 tests, passed. (a) `_ops_intake_enabled()` returns False unless BOTH
`OPS_INTAKE_WRITER_DSN` and `OPS_API_DSN` are set, and False when only `OPS_DEV_DSN` is set
(**OPS_DEV_DSN inert**); (b) a subprocess with the role DSNs unset gets 404 on the recognition route
(routes absent). Run with the repo-root `.venv` (the earlier red was a wrong-venv `learning_capture`
import, not a gate failure).

## 4. Drift enumeration (bounds "no drift")
ops_dev schema `ops`: **17 tables / 11 views / 9 SECURITY DEFINER fns** -- identical to the 2026-07-02
apply record (Sec 3). **0 PUBLIC table grants, 0 PUBLIC routine grants.** No object escaped the boundary
in the interval. The disposition is bounded to this enumerated object set.

## 5. Residue (precise)
This pass committed nothing. Independently, ops_dev is **not pristine**: the 2026-07-02 apply (Sec 5)
left a permanent, **non-zero-ROW-COUNT** but **net-zero-BALANCE** RB012-SMOKE recognition ledger
(attest -> approve_and_recognize +1500.00 -> reverse -1500.00 -> revoke). Those rows are append-only by
design (immutability triggers) and are **visible in the recognition worklist/rollup views** -- filter
`RB012-SMOKE-*` on any soak dashboard. This residue predates and is unrelated to this pass.

## 6. Finding -- armed dev role DSNs target the test DB, not a serving DB
`OPS_API_DSN` / `OPS_INTAKE_WRITER_DSN` in Infisical dev bind the correct roles but target
`dbname=ops_test` -- the app pytest suite's DB, guarded by `_require_ops_test` (asserts dbname==ops_test)
and provisioned (001->012 ladder) + torn down per test session (empty at rest, which is why an
out-of-fixture probe finds no ops schema there). Correct for the test suite. **There is NO armed serving
role DSN pointing at a persistent ops DB;** ops_dev holds the boundary but nothing connects to it as the
roles in normal operation. Not a dev defect -- a D8 prerequisite.

## 7. Scope honesty (what these probes do and do NOT prove)
- **A4/C9 prove invocability, not a live elevated write.** With random UUIDs the SECDEF fn raises a
  business error before the elevated write. The elevated write path was proven at APPLY TIME
  (2026-07-02 Sec 5, real +1500/-1500 recognition cycle as ops_api).
- **W1 proves table-level INSERT**, not the full app write path; the full path (11-column load.py shape,
  `_freeze`) AND a mounted HTTP product-path smoke on the role DSNs were exercised at apply time (Sec 5,
  Sec 8: worklist/rollup 200, intake 404, no permission-denied).
- Apply-time evidence is **end-to-end** (real write cycle + 7/7 denial smoke + HTTP smoke), not exhaustive.

## 8. Cross-engine review folded
- **Codex (xhigh):** A4-not-a-write-proof -> reframed (Sec 7); "42501 too broad" -> **closed** by the
  catalog oracle (C1-C9); residue over-claim -> corrected (Sec 5); D8-unproven / served-app-not-armed ->
  the forward gate (Sec 9). 
- **Claude 2-lens critic:** count corrected 18 (not 20); "6-day soak" reframed to static re-confirmation;
  ops_dev-vs-ops_test split (Sec 3); substrate stated; drift enumeration added (Sec 4); value-silence-on-
  failure affirmed (Sec 1); branch base SHA pinned (Sec 10).

## 9. Disposition + D8 forward gate
**SOAK: STRUCTURALLY CLOSED** (per operator direction 2026-07-08). Basis: apply-time end-to-end proof
(2026-07-02) + a clean two-oracle re-confirmation (18/18) + mount-gate green + object-set/PUBLIC drift
enumeration clean. All residual open items are prod (D8), not dev. *This closes the STRUCTURAL obligation
only; observed-serving proof is deferred to D8.*

**D8 (prod) forward gate -- do NOT start cold.** The prod packet must establish, on managed
non-superuser Postgres (tables NOT postgres-owned), what dev cannot: role creation without superuser;
table ownership + non-`postgres`-owner trigger/RI behavior; the ownership/GRANT choreography; pooler
behavior; RLS / default-ACL posture; view owner (`security_invoker`) semantics; AND **armed serving role
DSNs** (writer + api) for the prod ops DB. **First D8 task = re-run this same two-oracle harness against
the prod substrate.**

## 10. Branch retirement (ratified by operator, NOT executed)
Base for the "unique commits" claims = `origin/main @ f83db72c` (fetched 2026-07-08).
- `ops/recognition-bridge` (local `c73258a7`, worktree `apex-ops-recognition`): 446 behind / 0 ahead,
  `git cherry` empty -> zero unique commits.
- `ops/chip5-miner-intake` (local `8d5d99c1`, worktree `apex-ops-lane`): 641 behind / 16 ahead, but the
  16 are superseded -- ops migs 001/002/003 byte-identical to main; main's `packages/ops-intake` is a
  re-architected SUPERSET (extract.py 132->263 superset with 14 stale chip5-only lines; load.py rewritten
  cursor-injection for the role boundary; adds approve/catalog/classify/envelope/native/recognition).
  Retirement rests on this structural-superset + fixture-parity JUDGMENT, not a mechanical zero-unique.
- **Fixture parity:** main `packages/ops-intake/tests/test_model.py` carries the identical Miner identity
  (`MINER-PHX-AB-MV` / `Rev10` / `4692078.98` / "Project Jupiter") + the real `MINER_WORKBOOK` fixture;
  chip5's only unique fixture content is a marketing description string main replaced with real-workbook
  extraction. Nothing of value lost.

**Guard:** delete the local branches + worktrees ONLY after explicit operator deletion approval, and
re-confirm each branch's disposition vs `origin/main` at its then-current pinned SHA immediately before
deletion.
