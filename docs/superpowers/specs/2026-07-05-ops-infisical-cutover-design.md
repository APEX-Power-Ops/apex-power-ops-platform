# OPS_* Infisical cutover -- design (deferred B.8 lane)

Deferred follow-up to the Part B sanitizer lane (spec section B.8). This lane
finishes the Infisical cutover of the two ops DSNs by migrating the sole host
consumer's local-dev launch to `inject.sh`, purging the DSNs from every real
host cache, hardening the drift audit against uncovered caches, and only then
arming the two NAMES in `.managed-secrets`.

**Goal:** Make `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` sourced-from-Infisical
for local-dev control-plane work, with NO copy left in any real host cache and a
drift audit that cannot false-green on an unregistered cache.

**Architecture:** One committed Infisical-backed host launcher for
control-plane-api local dev; a reconciliation of the pre-existing Windows
PowerShell launcher so it is not a silent stale raw-uvicorn path; two
`secret-audit.sh` changes (register the app cache + a new device+inode-aware
cache-coverage guard, Check 1d); an operator-applied purge of the two DSNs from
the two physical caches; and finally arming the two NAMES in `.managed-secrets`.
Sequenced so local dev never loses the ops routers and Check 1c/1d never
false-greens.

**Tech stack:** bash (launcher, `secret-audit.sh`, fixture tests), self-hosted
Infisical via `infra/infisical/inject.sh` (mesh-only), FastAPI/uvicorn
(control-plane-api), GitHub Actions (`records-ci.yml`).

**Lane:** branch `secrets/ops-infisical-cutover`, host worktree
`/home/olares/code/apex/apex-ops-infisical-cutover`, off main `ba69825f`.

---

## 1. Scope and non-goals

**In scope**
- New `apps/control-plane-api/scripts/run_platform_api_local.sh` -- an
  Infisical-backed local launcher (`inject.sh dev -- uvicorn ...`).
- Reconcile `apps/control-plane-api/scripts/run_platform_api_local.ps1` +
  `apps/control-plane-api/README.md` + `.vscode/tasks.json` so raw uvicorn is no
  longer the recommended local path for ops-router work (details in section 3).
- `infra/secret-audit.sh`: register `apps/control-plane-api/.env` in the default
  `CACHES`; add Check 1d (cache-coverage completeness, device+inode-aware).
- New `infra/database/migrations/records/test_secret_audit_cache_coverage.sh`
  fixture test, wired into `.github/workflows/records-ci.yml`.
- A launcher argv test (mock `inject.sh` on PATH) + `shellcheck`.
- Arm `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` in
  `infra/infisical/.managed-secrets` -- LAST, only after purge is verified.

**Explicit non-goals (do NOT do in this lane)**
- Do NOT migrate or verify Render/production. control-plane-api deploys to
  Render (`https://control.apexpowerops.com`); Infisical is mesh-only and
  unreachable from Render, so Render OPS_* remain dashboard-env owned and OUT of
  scope. No Render dashboard step, no cloud secret-sync. Documented as a boundary,
  not touched.
- Do NOT cut over any OTHER secret. `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`,
  `SUPABASE_PROD_DSN`, `DEV_PG_PASSWORD`, `APEX_JOBS_PGPASSWORD` are all deferred
  or out. This lane touches only the two OPS_* names.
- Do NOT have the agent edit any credential value. The purge (section 6) is
  operator-applied out of band; the agent diagnoses and hands exact line
  identifiers by NAME, never a sed-edit of a `.env`.
- Do NOT mint an Infisical credential cache on Windows (that would expand the
  secret surface -- the opposite of this lane's purpose). See section 3.
- Do NOT claim `secret-audit.sh` exits 0. Success is scoped (section 10).

## 2. Ground truth (verified 2026-07-05, value-silent)

- **Caches holding OPS_* = two physical files.** `OPS_API_DSN` and
  `OPS_INTAKE_WRITER_DSN` are present (name-count 1 each) in
  `apex-power-ops-platform/infra/.env` and
  `apex-power-ops-platform/apps/control-plane-api/.env`. The two worktree caches
  named in B.8 (`apex-estimator-renderer/infra/.env`,
  `apex-learning-lane/infra/.env`) are symlinks to the canonical `infra/.env`
  (all three resolve to device+inode `<dev>:827320`). Purging the canonical file
  clears both symlinks.
- **Sole host consumer = control-plane-api.** The only non-test host readers of
  OPS_* are `apps/control-plane-api/main.py` and
  `apps/control-plane-api/services/ops/{intake_router,recognition_router}.py`.
  `main.py` mounts the ops routers only when BOTH OPS_* are present in the
  process env (the `_ops_enabled()` gate). No other host process reads them.
- **Deploy topology.** control-plane-api runs (a) local dev via uvicorn on port
  8010, (b) production on Render. Infisical (`http://100.64.0.1:8222`) is
  mesh-only, so `inject.sh` applies only to the local-dev launch.
- **config.py dotenv path.** `config.py` calls `load_dotenv` (no-override) on
  repo-root `.env.local` (absent today) then `apps/control-plane-api/.env`. Real
  env set by `inject.sh` is therefore NOT clobbered by the caches.
- **Infisical dev precondition MET.** `OPS_API_DSN`, `OPS_INTAKE_WRITER_DSN`,
  `DEV_PG_PASSWORD` are all PRESENT in Infisical `dev` (checked value-silent via
  `inject.sh dev`).
- **Audit today is rc=1 on the host** on five non-allowlisted `infra/.env` keys:
  the two OPS_* plus the three deferred keys (`TCC_BREAKER_RO_PW`,
  `TCC_BREAKER_CODEX_PW`, `SUPABASE_PROD_DSN`). The cache is gitignored and
  host-local, so these cache checks do not run in CI (no cache present there);
  they are a host-hygiene signal.
- **Coverage gap.** `secret-audit.sh` default `CACHES` =
  `{infra/.env, ~/code/apex/.env.dev-pg-offsite-backup}` plus `APEX_EXTRA_CACHES`.
  `apps/control-plane-api/.env` is NOT registered -- so arming OPS_* and purging
  only `infra/.env` would leave Check 1c green while OPS_* still lingers in the
  app cache. This is the false-green Check 1d closes.
- **`.managed-secrets` is empty** (header only); OPS_* would be the first armed
  names, activating Check 1c/1d for the first time.

## 3. Dev launcher + PowerShell reconciliation

### 3.1 New host launcher (Infisical-backed)
Create `apps/control-plane-api/scripts/run_platform_api_local.sh`, the bash
sibling of the existing `.ps1`, run on the mesh-reachable host:

```bash
#!/usr/bin/env bash
# Infisical-backed local launch for control-plane-api (ops-router work).
# OPS_* + DB creds are injected from Infisical dev at runtime -- never a cache.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
exec infra/infisical/inject.sh dev -- \
  uvicorn main:app --app-dir apps/control-plane-api \
  --host "${HOST:-127.0.0.1}" --port "${PORT:-8010}"
```

Notes: `dirname/../../..` resolves to the repo root from
`apps/control-plane-api/scripts/`. Binds `127.0.0.1` by default (the README local
smoke targets `127.0.0.1:8010`), overridable via `HOST`/`PORT`. Because
`inject.sh dev` puts OPS_* in the process env, the `main.py` gate mounts the ops
routers; because it also injects `DEV_PG_PASSWORD`, dev-DB access needs no cache.

### 3.2 PowerShell launcher reconciliation
`run_platform_api_local.ps1` is a Windows, task-backed (`.vscode/tasks.json`
"Run platform API local") raw-uvicorn launcher. Routing it through Infisical on
Windows would require a Windows Infisical credential cache -- a secret-surface
regression contrary to this lane. Chosen resolution (does NOT expand the secret
surface; flagged for operator ratification at the spec-review gate):

- Add a startup notice to the `.ps1` (a `Write-Host`/comment banner, no logic
  change to the launch) stating it runs control-plane-api WITHOUT
  Infisical-sourced OPS_*, so the ops routers will not mount unless OPS_* are
  otherwise present in the Windows environment; for ops-router work use the host
  Infisical-backed launcher `scripts/run_platform_api_local.sh` under the
  dev-residency workspace.
- The surgical purge removes only OPS_* (not the main `DATABASE_URL` vars), so
  the `.ps1` remains valid for general (non-ops) local work.

### 3.3 README + workspace guidance
Update `apps/control-plane-api/README.md` local-development section: present
`scripts/run_platform_api_local.sh` (Infisical-backed, host) as the recommended
launch for ops-router work; keep the `.ps1` documented for general Windows local
work with the same non-ops caveat; add the boundary note -- OPS_* come from
Infisical dev (mesh) locally and Render dashboard env in production. Update the
`.vscode/tasks.json` "Run platform API local" task description (or add a
sibling note) so the ops-router recommendation points at the host launcher. Do
NOT rewrite the accurate port-8010 restart guidance.

## 4. secret-audit.sh changes

### 4.1 Register the app cache
Add `apps/control-plane-api/.env` to the default `CACHES` array (mode `0`, i.e.
present-optional; it is a gitignored 0600 cache like `infra/.env`). This makes
both Check 1 (permissions) and Check 1c (drift) see the app cache.

### 4.2 Check 1d -- cache-coverage completeness (device+inode-aware)
Dormant unless `.managed-secrets` names at least one secret (same trigger as
Check 1c). Purpose: guarantee that the set of physical caches actually holding a
managed name is a SUBSET of the registered, scanned `CACHES` -- so drift-verify
cannot false-green on a cache nobody registered.

Algorithm:
1. Build the registered key set: for each `CACHES` entry that exists, compute
   `stat -L -c '%d:%i'` (device+inode, following symlinks). Device+inode (NOT
   inode alone) avoids false dedup across filesystems. Collect into a set
   `REGISTERED_DEVINO`.
2. Discover candidate caches: the union of
   (a) every `CACHES` path, and
   (b) a bounded sweep for `.env` and `.env.local` under the consumer roots
       (`$ROOT`, `$ROOT/apps/*`, `$ROOT/infra`), excluding paths matching the
       `infra/.secret-audit-allow` example/sample/template globs and any
       `node_modules`.
   For each discovered existing file compute `stat -L -c '%d:%i'`; symlinks to a
   registered target collapse to the same device+inode.
3. For each discovered cache whose device+inode is NOT in `REGISTERED_DEVINO`,
   grep it (NAMES only) for each managed name. If any managed name is found in
   an unregistered cache -> `FAIL  uncovered cache holds managed name: <name> in
   <path>` and set rc=1.
4. Emit a single `PASS  cache-coverage check ran (<n> managed name(s), <m>
   registered cache(s))` line when no uncovered hit is found.

Properties: the two worktree symlinks collapse into the registered `infra/.env`
device+inode (no double-scan, no spurious uncovered-FAIL); a brand-new physical
cache that copies a managed name FAILs until it is purged or registered; files
with no managed name never FAIL (so `apps/operations-web/.env.local`, which
holds no OPS_*, is inert). Value-silent throughout: only names/paths/PASS/FAIL.

## 5. Arm `.managed-secrets` (LAST)
After the purge is verified (section 6), append two NAMES to
`infra/infisical/.managed-secrets`:

```
OPS_API_DSN
OPS_INTAKE_WRITER_DSN
```

Arming before the purge is complete is a CORRECT failure (Check 1c/1d would flag
the lingering copy), so this step is strictly last.

## 6. Operator-applied purge (out of band)
The agent never edits a credential value. The agent hands the operator the exact
targets by NAME/path; the operator removes the two lines and confirms:
- Remove the `OPS_API_DSN=` and `OPS_INTAKE_WRITER_DSN=` lines from
  `apex-power-ops-platform/infra/.env` (this clears the two worktree symlinks too).
- Remove the `OPS_API_DSN=` and `OPS_INTAKE_WRITER_DSN=` lines from
  `apex-power-ops-platform/apps/control-plane-api/.env`.
Then the agent verifies value-silent (name-count 0 in every discovered cache).

## 7. Ordering invariant (sequence)
1. Land launcher (3.1) + PS/README/tasks reconciliation (3.2/3.3) + audit changes
   (4.1/4.2) + tests (section 8). Do NOT arm `.managed-secrets` yet.
2. Verify local dev works through `inject.sh` -- ops routers mount (section 9).
3. Operator purges OPS_* from the two physical caches (section 6).
4. Verify no lingering OPS_* in any discovered cache (value-silent).
5. THEN arm the two NAMES (section 5); run `secret-audit.sh` and confirm no OPS_*
   drift/coverage FAIL and no OPS_* in Check 1b for `infra/.env`.

Arm-before-purge = correct FAIL, so the order is load-bearing.

## 8. Tests (extend the existing fixture pattern; value-silent)

**Value-silence rule (load-bearing):** fixtures use PLACEHOLDER values only;
assertions check for PASS/FAIL-line presence by NAME, never a cache value; no
test prints a `.env` value.

### 8.1 `test_secret_audit_cache_coverage.sh` (new; sibling to the two existing
`infra/database/migrations/records/test_secret_audit_*.sh`)
Build a temp `ROOT` fixture and drive `secret-audit.sh` against it (via a test
ROOT / `APEX_EXTRA_CACHES` as the existing fixtures do). Cases:
1. Registered cache holding a managed NAME with a PLACEHOLDER value, name NOT yet
   armed -> Check 1d dormant (no FAIL). Then arm the name -> Check 1c FAIL for
   drift (registered-and-present) -- proves the drift path still fires.
2. Unregistered PHYSICAL cache holding an armed managed NAME -> Check 1d
   `FAIL uncovered cache holds managed name`.
3. A SYMLINK to a registered cache -> collapses by device+inode: no double-FAIL
   and no spurious uncovered-FAIL.
4. Clean state (armed name absent from every cache) -> Check 1d PASS line.
Assert on presence/absence of the specific FAIL/PASS lines by name; assert the
audit rc for the clean case.

### 8.2 Wire into CI
Add a `run: bash infra/database/migrations/records/test_secret_audit_cache_coverage.sh`
step to `.github/workflows/records-ci.yml` beside the existing two audit fixture
steps (the workflow already triggers on `infra/secret-audit.sh`).

### 8.3 Launcher argv test + shellcheck
A deterministic test: put a mock `inject.sh` on PATH that echoes its argv, run
`run_platform_api_local.sh`, assert it invokes
`inject.sh dev -- uvicorn main:app --app-dir apps/control-plane-api --host
127.0.0.1 --port 8010` (defaults). No network/secret needed. Run `shellcheck` on
both new/edited bash files.

## 9. Verification / smoke (host, manual, value-silent)
- Run `scripts/run_platform_api_local.sh`; confirm the ops routers are mounted
  (the FastAPI OpenAPI/health surface advertises the ops intake/recognition
  routes) -- proves OPS_* arrived via Infisical, not a cache.
- After purge: run `infra/secret-audit.sh`; confirm (a) no `OPS_*` line under
  Check 1b for `infra/.env`, (b) no OPS_* drift/coverage FAIL under Check 1c/1d.
  The audit will still be rc=1 on the three deferred keys -- expected.
- No prod/dev data mutation; nothing connects as a privileged role; the smoke
  only starts the API and reads route metadata.

## 10. Success criterion (honest scoping)
Done = `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` are absent from every real host
cache (both physical files, hence the two symlinks) AND armed in
`.managed-secrets` AND guarded by Check 1c/1d (drift + coverage), AND the
Infisical-backed local launcher mounts the ops routers. Explicitly NOT "secret-
audit exits 0": `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`, `SUPABASE_PROD_DSN`
remain deferred and keep the audit rc=1 on the host by design.

## 11. Discipline (whole lane)
Host-canonical single-writer: author locally, scp to the
`apex-ops-infisical-cutover` worktree only, commit host-side. ASCII-only added
lines (audit each file's added lines; the caches/scripts may carry pre-existing
non-ASCII). Value-silent (names/paths/booleans/counts only; never a DSN or
password value, never a pytest/bash env dump). Operator applies the credential
purge; the agent never edits a credential value. No production mutation. Commit
trailer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## 12. Decisions (ratified 2026-07-05)
1. Prod boundary: local-dev only; Render remains dashboard-env owned and out of
   scope (no Render step, no cloud sync).
2. Dev launch: committed Infisical-backed launcher artifact
   (`run_platform_api_local.sh`), testable, README/tasks repointed.
3. Check 1d: registration + realpath device+inode (`%d:%i`) equality/coverage
   guard (not inode alone -- avoids cross-filesystem false dedup).
4. Register `apps/control-plane-api/.env` in `CACHES`.
5. `test_secret_audit_cache_coverage.sh` beside the existing secret-audit fixture
   tests, wired into `records-ci.yml`.
6. Operator purges OPS_* from the two physical caches; agent never edits values.
7. Arm the two NAMES in `.managed-secrets` only after purge verification.
8. Success scoped: OPS_* gone from every real host cache and guarded by
   `.managed-secrets`/Check 1d, not full `secret-audit` rc=0 while TCC_* and
   SUPABASE_PROD_DSN remain deferred.
9. PowerShell launcher reconciliation: annotate `.ps1` + repoint README/tasks so
   it is not a silent stale raw-uvicorn path, WITHOUT minting a Windows Infisical
   credential cache (operator to ratify at spec review).
