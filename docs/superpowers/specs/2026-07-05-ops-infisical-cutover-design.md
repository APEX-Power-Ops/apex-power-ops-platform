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
- A launcher argv test (temp repo fixture with a stub `infra/infisical/inject.sh`
  at the real relative path) + `shellcheck`.
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
- Do NOT fix `inject.sh` passing the Infisical client secret on argv (a
  pre-existing exposure this lane merely leans on more; hardening it to env/stdin
  instead of `--client-secret=` is a separate follow-up).

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
  process env (the `_ops_intake_enabled()` gate). No other host process reads them.
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
`inject.sh dev` puts OPS_* in the process env, the `_ops_intake_enabled()` gate
mounts the ops routers. The main `DATABASE_URL` is unaffected by this lane:
`config.py` resolves it from `APEX_OLARES_LIVE_DSN` / `SEAM_DATABASE_URL` /
`APEX_DB_CONNECTION_STRING` / `DATABASE_URL` (none of them OPS_* names), which keep
coming from the app `.env` cache (their migration is out of scope). `inject.sh dev`
also injects `DEV_PG_PASSWORD`, but that feeds dev-DB tooling (e.g. `dev-psql.sh`),
NOT `config.py`'s `DATABASE_URL` -- the launcher is not claimed cache-free for the
main DSN.

### 3.2 PowerShell launcher reconciliation
`run_platform_api_local.ps1` is a Windows, task-backed (`.vscode/tasks.json`
"Run platform API local") raw-uvicorn launcher. Routing it through Infisical on
Windows would require a Windows Infisical credential cache -- a secret-surface
regression contrary to this lane. Chosen resolution (operator-ratified; does NOT
expand the secret surface):

- Add a startup notice to the `.ps1` (a `Write-Host`/comment banner, no logic
  change to the launch) stating it runs control-plane-api WITHOUT
  Infisical-sourced OPS_*, so the ops routers will not mount unless OPS_* are
  otherwise present in the Windows environment; for ops-router work use the host
  Infisical-backed launcher
  `apps/control-plane-api/scripts/run_platform_api_local.sh` under the
  dev-residency workspace.
- The surgical purge removes only OPS_* (not the main `DATABASE_URL` vars), so
  the `.ps1` remains valid for general (non-ops) local work.

### 3.3 README + workspace guidance
Update `apps/control-plane-api/README.md` local-development section: present
`apps/control-plane-api/scripts/run_platform_api_local.sh` (host, Infisical-backed)
as the recommended launch for ops-router work; keep the `.ps1` documented for
general Windows local work with the same non-ops caveat; add the boundary note --
OPS_* come from Infisical dev (mesh) locally and Render dashboard env in
production.

Reconcile `.vscode/tasks.json` unambiguously -- a note is NOT sufficient, because
the existing "Run platform API local" and "Restart platform API local" tasks
literally invoke the raw `run_platform_api_local.ps1` via pwsh. Required: (a)
relabel BOTH tasks NON-OPS (label + `detail` stating they run without Infisical
OPS_*, so the ops routers do not mount), and (b) add a distinct ops-host launcher
instruction routing ops-router work to
`apps/control-plane-api/scripts/run_platform_api_local.sh` (run in the
dev-residency / Remote-SSH host terminal, where the integrated shell is host
bash). A committed cross-platform VS Code bash task is OPTIONAL (it only works in
the Remote-SSH context); the relabel + the ops instruction are MANDATORY. Do NOT
rewrite the accurate port-8010 restart guidance.

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
1. Build the registered device+inode set: for each existing `CACHES` entry compute
   `stat -L -c '%d:%i'` (device+inode, following symlinks -- NOT inode alone, which
   would false-dedup across filesystems). Collect into `REGISTERED_DEVINO`.
2. Discover candidate caches as the union of:
   (a) every `CACHES` path (covers registered caches wherever they live, incl. the
       out-of-`$ROOT` offsite-backup cache), and
   (b) a RECURSIVE sweep `find -L "$ROOT" -name '.env*'` (all depths; `find -L`
       follows symlinks so a symlinked cache is emitted, not skipped), and
   (c) a DEPTH-1 `find -L <dir> -maxdepth 1 -name '.env*'` over the containing
       directory of every registered `CACHES` entry that lies OUTSIDE `$ROOT`
       (depth-1, NOT recursive: the offsite-backup cache's dir is the parent of
       ALL worktrees, so a recursive sweep there would be catastrophic) -- this
       catches a stray sibling like `~/code/apex/.env` without descending.
   Exclusions use a PURPOSE-BUILT set -- `node_modules` and the literal basenames
   `*.example` / `*.sample` / `*.template` -- NOT `infra/.secret-audit-allow`
   (whose `*/tests/*` and `.vscode/*` globs would wrongly suppress a real runtime
   cache). For each discovered existing file compute `stat -L -c '%d:%i'`; symlinks
   and hardlinks to a registered target collapse onto its device+inode.
3. For each discovered cache whose device+inode is NOT in `REGISTERED_DEVINO`, scan
   it for each managed name using the SAME anchored assignment regex Check 1c uses
   -- `^[[:space:]]*(export[[:space:]]+)?<name>[[:space:]]*=` -- so a commented
   `# OPS_API_DSN=` does not FAIL and a superset name (`OPS_API_DSN_BACKUP`) does
   not misfire. Any match -> `FAIL  uncovered cache holds managed name: <name> in
   <path>` and set rc=1.
4. Emit a summary line `PASS  cache-coverage check ran (<n> managed name(s),
   <d> caches discovered, <r> registered)` when no uncovered hit is found. The
   `<d>` discovered count (names/paths/counts only) lets the fixture assert a
   planted cache was actually enumerated (not silently skipped).

Properties: the two worktree symlinks collapse onto the registered `infra/.env`
device+inode (no double-scan, no spurious uncovered-FAIL); a copy in any `.env*`
file recursively under `$ROOT` -- or beside a registered out-of-`$ROOT` cache --
FAILs until purged or registered; a commented or superset-name line does not
misfire; a file with no managed name never FAILs (so `apps/operations-web/.env.local`
is inert). Coverage is honestly bounded (see section 10): a cache entirely OUTSIDE
`$ROOT` that is not registered is NOT discovered -- it must be added via
`APEX_EXTRA_CACHES` to be covered. Value-silent throughout: names/paths/counts only.

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
- If a Windows-local checkout of the repo exists (a separate machine, OUTSIDE the
  mesh audit's reach), check its `apps/control-plane-api/.env` for `OPS_API_DSN` /
  `OPS_INTAKE_WRITER_DSN`; if present, the operator purges those two names there
  too; if absent, record "not present." No Windows Infisical credential cache is
  created and the `.ps1` stays non-ops (section 3.2).
Then the agent verifies value-silent (name-count 0 in every discovered cache),
running the authoritative audit from the canonical `apex-power-ops-platform`
checkout (see section 9), not the lane worktree.

## 7. Ordering invariant (sequence)
1. Land launcher (3.1) + PS/README/tasks reconciliation (3.2/3.3) + audit changes
   (4.1/4.2) + tests (section 8). Do NOT arm `.managed-secrets` yet.
2. Pre-purge PRECONDITION (value-silent): confirm Infisical dev resolves BOTH
   OPS_* names via `inject.sh dev` name-presence. Do NOT use a pre-purge
   router-mount smoke as proof -- with the caches still populated it would mount
   the routers from the cache regardless of whether Infisical delivered anything
   (a false-green).
3. Operator purges OPS_* from the two host caches -- and the Windows checkout if
   present (section 6).
4. Post-purge DEFINITIVE proof (section 9): the launcher (via `inject.sh`) mounts
   BOTH ops routes; the NEGATIVE control (raw `uvicorn`, no `inject.sh`) mounts
   NEITHER -- together proving the routers now come from Infisical and the caches
   are truly gone.
5. Verify no lingering OPS_* in any discovered cache (value-silent).
6. THEN arm the two NAMES (section 5); run `secret-audit.sh` FROM THE CANONICAL
   `apex-power-ops-platform` checkout (a worktree has no gitignored caches and
   would false-green) and confirm no OPS_* drift/coverage FAIL and no OPS_* in
   Check 1b for `infra/.env`.

Arm-before-purge = correct FAIL, so the order is load-bearing.

## 8. Tests (extend the existing fixture pattern; value-silent)

**Value-silence rule (load-bearing):** fixtures use PLACEHOLDER values only;
assertions check for PASS/FAIL-line presence by NAME, never a cache value; no
test prints a `.env` value.

### 8.1 `test_secret_audit_cache_coverage.sh` (new; sibling to the two existing
`infra/database/migrations/records/test_secret_audit_*.sh`)
HARNESS (load-bearing): `secret-audit.sh` derives `ROOT` from its own
`BASH_SOURCE`, NOT cwd/env, and Check 1d's registered set, `.managed-secrets`
path, and sweep ALL key off `$ROOT`. So the fixture MUST replicate the
`test_secret_audit_env_allowlist.sh` pattern: `cp` the audit into a temp
`fixture/infra/secret-audit.sh`, write a fixture `infra/infisical/.managed-secrets`,
and plant every cache UNDER the fixture ROOT -- so the BASH_SOURCE-derived ROOT (and
1d's sweep) lands on the temp fixture, never the real `$HOME/code/apex` tree.
`APEX_EXTRA_CACHES` alone does NOT relocate ROOT and must not be relied on for
hermeticity.

Cases (value-silent -- PLACEHOLDER values; assert on PASS/FAIL lines + counts + rc
by NAME, never a value):
1. Registered cache holds a managed NAME, name NOT yet armed -> Check 1d dormant
   (no FAIL). Arm the name -> Check 1c FAIL for drift (registered-and-present) --
   proves the drift path still fires.
2. Unregistered PHYSICAL cache at a NESTED/other-tree path (e.g.
   `apps/control-plane-api/scripts/.env`) holds an armed managed NAME -> assert ALL
   of: the specific `FAIL  uncovered cache holds managed name: <name>` line,
   `rc == 1`, that the name is armed (guard against a dormant-by-accident no-op),
   and that the summary `discovered` count proves the planted cache was actually
   enumerated (so a mis-built fixture fails loudly instead of passing).
3. Unregistered SYMLINK pointing to an OUTSIDE physical cache that holds an armed
   NAME -> `find -L` follows it and Check 1d FAILs (proves symlink DISCOVERY, not
   just `stat -L` dedup).
4. SYMLINK to a REGISTERED cache -> collapses by device+inode: no double-FAIL and
   no spurious uncovered-FAIL.
5. Clean state (armed name absent from every cache) -> Check 1d PASS summary with a
   non-zero `discovered` count; assert `rc == 0` for this isolated case.

### 8.2 Wire into CI
Add a `run: bash infra/database/migrations/records/test_secret_audit_cache_coverage.sh`
step to `.github/workflows/records-ci.yml` beside the existing two audit fixture
steps (the workflow already triggers on `infra/secret-audit.sh`).

### 8.3 Launcher argv test + shellcheck
The launcher calls `infra/infisical/inject.sh` by RELATIVE path (after `cd
"$ROOT"`), so a mock on `PATH` would NOT intercept it. Instead build a temp repo
fixture that exercises the real path contract: a temp `ROOT` containing
`apps/control-plane-api/scripts/run_platform_api_local.sh` (a copy of the real
launcher) and a stub `infra/infisical/inject.sh` at that relative path which
echoes its argv. Run the copied launcher; its `$ROOT` resolves to the temp
fixture, so it invokes the stub. Assert the stub captured
`dev -- uvicorn main:app --app-dir apps/control-plane-api --host 127.0.0.1 --port
8010` (defaults). No network/secret, and no test-only hook in the production
launcher. Run `shellcheck` on both new/edited bash files. This is an ARGV-CONTRACT
test only -- it does NOT prove `main.py` imports, that Infisical dev holds both
OPS_* names, or that the routers mount; that is the post-purge host smoke
(section 9).

## 9. Verification / smoke (host, manual, value-silent)
The router-mount proof is meaningful only POST-purge (pre-purge the cache supplies
OPS_* regardless of Infisical). After the purge (section 6):
- POSITIVE: run `apps/control-plane-api/scripts/run_platform_api_local.sh`; assert
  the OpenAPI surface advertises BOTH ops routes (intake AND recognition) -- FAIL
  the smoke if either is missing (do not eyeball a generic "mounted"). This proves
  OPS_* arrived via Infisical, since the caches no longer hold them.
- NEGATIVE control: run raw `uvicorn main:app --app-dir apps/control-plane-api`
  WITHOUT `inject.sh`; assert NEITHER ops route is advertised -- proving the caches
  are truly purged (not silently re-supplying OPS_*).
- AUDIT (authoritative): run `infra/secret-audit.sh` FROM THE CANONICAL
  `apex-power-ops-platform` checkout (a worktree has no gitignored caches and would
  false-green); confirm (a) no `OPS_*` under Check 1b for `infra/.env`, (b) no OPS_*
  drift/coverage FAIL under Check 1c/1d. Audit stays rc=1 on the three deferred keys
  -- expected. (The lane-worktree audit run exercises only the fixture, not the real
  caches.)
- No prod/dev data mutation; nothing connects as a privileged role; the smoke only
  starts the API and reads route metadata.

## 10. Success criterion (honest scoping)
Done = `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` are absent from every real host
cache (the two physical files, hence the two symlinks; plus the Windows checkout's
app `.env` if one exists, section 6) AND armed in `.managed-secrets` AND guarded by
Check 1c/1d, AND the post-purge smoke proves the launcher mounts BOTH ops routes via
Infisical (with the raw-uvicorn negative control mounting neither).

Coverage of Check 1d is HONESTLY BOUNDED, not universal: it covers every `.env*`
file recursively under `$ROOT` PLUS every registered `CACHES` entry (wherever it
lives). A cache entirely OUTSIDE `$ROOT` that is not registered is a documented
residual -- it must be added via `APEX_EXTRA_CACHES` to be covered. The
authoritative audit runs from the canonical `apex-power-ops-platform` checkout.

Explicitly NOT "secret-audit exits 0": `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`,
`SUPABASE_PROD_DSN` remain deferred and keep the audit rc=1 on the host by design.

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
2. Dev launch: committed Infisical-backed host launcher artifact
   (`apps/control-plane-api/scripts/run_platform_api_local.sh`), testable; README
   updated and the two Windows VS Code tasks relabeled NON-OPS + a distinct
   ops-host launcher instruction added.
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
9. PowerShell launcher reconciliation (operator-ratified): annotate the `.ps1`
   startup as NON-OPS, relabel the two Windows VS Code tasks NON-OPS, add a
   distinct ops-host launcher instruction, and update the README -- so it is not a
   silent stale raw-uvicorn path -- WITHOUT minting a Windows Infisical credential
   cache.
10. Check 1d coverage (IRP F1): widen discovery to recursive `find -L "$ROOT"
    -name '.env*'` + registered cache paths (depth-1 sibling scan for out-of-`$ROOT`
    ones), `%d:%i` dedup, Check 1c's anchored regex, purpose-built excludes; scope
    section 10 honestly (under-`$ROOT` + registered; out-of-`$ROOT` unregistered
    must use `APEX_EXTRA_CACHES`).
11. Windows checkout (IRP F6): operator purges OPS_* from a Windows-local
    `apps/control-plane-api/.env` if present, records "not present" if absent; no
    Windows Infisical cache; `.ps1` stays non-ops.
12. Authoritative audit (IRP F2) runs from the canonical `apex-power-ops-platform`
    checkout, never the lane worktree (BASH_SOURCE-derived ROOT).
13. Cutover proof (IRP F3) is POST-purge: launcher -> BOTH ops routes; raw-uvicorn
    negative control -> neither. Pre-purge is only the Infisical name-presence
    precondition.
14. Coverage fixture (IRP F4) is self-validating: Check 1d emits a discovered
    count; Case 2 asserts FAIL line + rc=1 + name-armed + planted-cache-enumerated;
    the fixture cp's the audit into the fixture ROOT (env_allowlist harness) and
    adds an outside-symlink-to-physical case.

## 13. Revisions
- rev 2 (2026-07-05): folded operator spec-review findings P1-P3 before the IRP
  pass. P1 -- `.vscode/tasks.json` reconciliation made mandatory and unambiguous
  (relabel both Windows tasks NON-OPS + a distinct ops-host instruction; a note
  is not sufficient, since the tasks literally run the raw `.ps1`). P2 -- the
  launcher argv test uses a temp repo fixture with a stub
  `infra/infisical/inject.sh` at the real relative path (a `PATH` mock cannot
  intercept a relative-path call). P3 -- exactness: real gate is
  `_ops_intake_enabled()` (main.py:109); the launcher is referenced by full
  repo-root path `apps/control-plane-api/scripts/run_platform_api_local.sh`.
- rev 3 (2026-07-05): folded the lean IRP + Codex cross-engine audit of rev 2
  (verdict REVISE). F1 (both engines, HIGH) -- widened Check 1d discovery to a
  recursive `find -L` + registered-dir union with an anchored regex and
  purpose-built excludes, and honestly bounded the section-10 coverage claim.
  F2 (Codex, HIGH) -- authoritative audit runs from the canonical checkout, not
  the lane worktree. F3 (Codex, HIGH) -- moved the definitive Infisical-delivery
  proof post-purge with a raw-uvicorn negative control and a both-routes assertion.
  F4 (Claude, MED) -- self-validating coverage fixture (discovered count, armed
  guard, outside-symlink case, env_allowlist harness). F5 (accuracy) -- corrected
  the DATABASE_URL note. F6 (both) -- Windows checkout app `.env` is an
  operator-purge target if present. F8 (Codex, LOW) -- noted `inject.sh` argv
  exposure as an out-of-scope follow-up.
