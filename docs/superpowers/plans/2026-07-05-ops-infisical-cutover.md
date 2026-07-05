# OPS_* Infisical Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` sourced-from-Infisical for
local-dev control-plane work, with no copy left in any real host cache and a drift
audit (Check 1d) that cannot false-green on an unregistered cache within its
bounded discovery set.

**Architecture:** Three code changes -- an Infisical-backed host launcher for
control-plane-api local dev, a reconciliation of the pre-existing Windows
PowerShell launcher so it is not a silent stale raw-uvicorn path, and two
`secret-audit.sh` changes (register the app cache + a new device+inode-aware
cache-coverage guard, Check 1d) proven by a value-silent fixture test wired into
CI -- followed by an operator-gated post-merge cutover runbook (precondition ->
purge -> post-purge proof -> arm `.managed-secrets`).

**Tech Stack:** bash (launcher, `secret-audit.sh`, fixture tests), self-hosted
Infisical via `infra/infisical/inject.sh` (mesh-only), FastAPI/uvicorn
(control-plane-api), GitHub Actions (`records-ci.yml`).

**Spec:** `docs/superpowers/specs/2026-07-05-ops-infisical-cutover-design.md`
(rev 4, committed `bebcdfdf`). The spec is the single source of truth; read it in
full before starting.

## Global Constraints

Every task's requirements implicitly include this section.

- **Host-canonical single-writer:** author locally on Windows -> scp per-file to
  the host worktree `/home/olares/code/apex/apex-ops-infisical-cutover` -> run and
  commit host-side over `ssh olares-mesh`. Never a stale-mirror tar-push.
- **ASCII-only ADDED lines.** Audit added lines only:
  `git diff --cached | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]'` (must be empty).
- **Value-silent:** names/paths/booleans/counts only; NEVER a DSN or password
  value; no pytest/bash env dump; fixture tests assert on PASS/FAIL lines by NAME
  and use synthetic PLACEHOLDER values that must be absent from output.
- **Operator applies the credential-file purge.** The implementer NEVER edits or
  sed-edits a credential value / `.env` line; it only hands the operator exact
  NAME/path targets (see the Operator Cutover Runbook).
- **No production mutation.** Render is OUT of scope (mesh-only Infisical cannot
  reach it; Render OPS_* stay dashboard-env owned).
- **Success is scoped:** done = OPS_* gone from every real host cache + guarded by
  `.managed-secrets`/Check 1c/1d, NOT `secret-audit` rc=0 (`TCC_BREAKER_RO_PW`,
  `TCC_BREAKER_CODEX_PW`, `SUPABASE_PROD_DSN` remain deferred and keep the audit
  rc=1 on the host by design).
- **Commit trailer:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Branch/worktree:** `secrets/ops-infisical-cutover` off main `ba69825f`; the
  spec + plan are already committed on it.

---

## File Structure

| File | Task | Responsibility |
|---|---|---|
| `apps/control-plane-api/scripts/run_platform_api_local.sh` | 0 | new: Infisical-backed host launcher |
| `apps/control-plane-api/scripts/test_run_platform_api_local.sh` | 0 | new: argv-contract test (temp-fixture stub) |
| `apps/control-plane-api/scripts/run_platform_api_local.ps1` | 1 | modify: add NON-OPS startup banner |
| `apps/control-plane-api/README.md` | 1 | modify: recommend host `.sh` for ops work + boundary note |
| `.vscode/tasks.json` | 1 | modify: relabel both Windows tasks NON-OPS + ops-host instruction |
| `infra/secret-audit.sh` | 2 | modify: register app cache in CACHES + add Check 1d |
| `infra/database/migrations/records/test_secret_audit_cache_coverage.sh` | 2 | new: 5-case value-silent Check 1d fixture |
| `.github/workflows/records-ci.yml` | 0, 2 | modify: wire the two new tests |

Task order: **0 -> 1 -> 2**. T1's README/tasks reference the T0 launcher path.
T2 is independent but sequenced last. The post-merge Operator Cutover Runbook is
documentation, not a code task.

---

## Task 0: Infisical-backed host launcher + argv-contract test

**Files:**
- Create: `apps/control-plane-api/scripts/run_platform_api_local.sh`
- Create: `apps/control-plane-api/scripts/test_run_platform_api_local.sh`
- Modify: `.github/workflows/records-ci.yml` (add a shell-test step)

**Interfaces:**
- Produces: the launcher invokes `infra/infisical/inject.sh dev -- uvicorn
  main:app --app-dir apps/control-plane-api --host 127.0.0.1 --port 8010`
  (HOST/PORT overridable). T1's README points at this path.

- [ ] **Step 1: Write the failing argv-contract test**

Create `apps/control-plane-api/scripts/test_run_platform_api_local.sh`. It builds
a temp repo fixture exercising the REAL relative-path contract (a `PATH` mock
cannot intercept the launcher's relative `infra/infisical/inject.sh` call), stubs
`inject.sh` to capture argv WITHOUT running uvicorn, and asserts the exact argv.

```bash
#!/usr/bin/env bash
# Argv-contract test for run_platform_api_local.sh. Proves the launcher invokes
# inject.sh with the exact `dev -- uvicorn ...` argv. This is NOT a cutover proof:
# it does not run uvicorn, import main.py, or touch Infisical. Value-silent (no
# secret values are involved).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
LAUNCHER="$HERE/run_platform_api_local.sh"
fail=0; say() { printf '%s\n' "$*"; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

if [[ ! -f "$LAUNCHER" ]]; then
  say "FAIL  launcher missing: $LAUNCHER"; exit 1
fi

# Temp repo fixture: launcher three levels under root; stub inject.sh at the real
# relative path apps/control-plane-api/scripts -> ../../.. = fixture root.
mkdir -p "$tmp/apps/control-plane-api/scripts" "$tmp/infra/infisical"
cp "$LAUNCHER" "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
chmod +x "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
cat > "$tmp/infra/infisical/inject.sh" <<'STUB'
#!/usr/bin/env bash
# Stub: capture argv, do NOT exec uvicorn.
printf '%s\n' "$*" > "$CAPTURE"
STUB
chmod +x "$tmp/infra/infisical/inject.sh"

CAPTURE="$tmp/argv.txt" bash "$tmp/apps/control-plane-api/scripts/run_platform_api_local.sh"
got="$(cat "$tmp/argv.txt" 2>/dev/null || echo '<none>')"
expected='dev -- uvicorn main:app --app-dir apps/control-plane-api --host 127.0.0.1 --port 8010'
if [[ "$got" == "$expected" ]]; then
  say "PASS  launcher argv contract"
else
  say "FAIL  launcher argv contract"; say "  expected: $expected"; say "  got:      $got"; fail=1
fi

if [[ "$fail" == "0" ]]; then say "RESULT: launcher argv fixture PASSED"; else say "RESULT: launcher argv fixture FAILED"; fi
exit "$fail"
```

- [ ] **Step 2: Run the test to verify it fails**

Author locally, scp to the worktree, run host-side:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  bash apps/control-plane-api/scripts/test_run_platform_api_local.sh; echo "rc=$?"'
```
Expected: `FAIL  launcher missing: .../run_platform_api_local.sh` and `rc=1`
(the launcher does not exist yet).

- [ ] **Step 3: Write the launcher**

Create `apps/control-plane-api/scripts/run_platform_api_local.sh`:
```bash
#!/usr/bin/env bash
# Infisical-backed local launch for control-plane-api (ops-router work).
# OPS_* are injected from Infisical dev at runtime -- never a cache. The main
# DATABASE_URL still resolves in config.py from the app .env cache (its migration
# is out of scope for this lane); DEV_PG_PASSWORD is also injected but feeds
# dev-DB tooling (dev-psql.sh), not config.py's DATABASE_URL.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
exec infra/infisical/inject.sh dev -- \
  uvicorn main:app --app-dir apps/control-plane-api \
  --host "${HOST:-127.0.0.1}" --port "${PORT:-8010}"
```
`chmod +x` it host-side after scp: `chmod +x apps/control-plane-api/scripts/run_platform_api_local.sh`.

- [ ] **Step 4: Run the test to verify it passes + shellcheck**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  bash apps/control-plane-api/scripts/test_run_platform_api_local.sh; echo "rc=$?"; \
  shellcheck apps/control-plane-api/scripts/run_platform_api_local.sh \
             apps/control-plane-api/scripts/test_run_platform_api_local.sh; echo "shellcheck_rc=$?"'
```
Expected: `PASS  launcher argv contract`, `RESULT: launcher argv fixture PASSED`,
`rc=0`, and `shellcheck_rc=0`.

- [ ] **Step 5: Wire the test into CI**

In `.github/workflows/records-ci.yml`, beside the existing
`test_secret_audit_ac8.sh` / `test_secret_audit_env_allowlist.sh` steps, add:
```yaml
      - name: control-plane-api launcher argv contract test
        run: bash apps/control-plane-api/scripts/test_run_platform_api_local.sh
```
Add `apps/control-plane-api/scripts/run_platform_api_local.sh` to the workflow's
`paths:` trigger list if it gates on changed paths (mirror how
`infra/secret-audit.sh` is listed).

- [ ] **Step 6: ASCII-check and commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  git add apps/control-plane-api/scripts/run_platform_api_local.sh \
          apps/control-plane-api/scripts/test_run_platform_api_local.sh \
          .github/workflows/records-ci.yml && \
  git diff --cached | grep "^+" | LC_ALL=C grep -P "[^\x00-\x7F]" && echo "NON-ASCII" || echo "ASCII-CLEAN"'
# then commit (only if ASCII-CLEAN):
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && git commit -m "feat(control-plane-api): Infisical-backed local launcher + argv-contract test

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

## Task 1: Reconcile the Windows launcher (non-ops) + README + tasks.json

**Files:**
- Modify: `apps/control-plane-api/scripts/run_platform_api_local.ps1`
- Modify: `apps/control-plane-api/README.md`
- Modify: `.vscode/tasks.json`

**Interfaces:**
- Consumes: the Task 0 launcher path
  `apps/control-plane-api/scripts/run_platform_api_local.sh`.
- Produces: no code interface; a documentation/config reconciliation so the raw
  `.ps1` is not a silent stale ops path.

**Note:** This task is doc/config; its "test" is grep-assertions plus a
PowerShell parse check. A note alone is NOT sufficient -- both Windows tasks must
be relabeled NON-OPS AND a distinct ops-host instruction added.

- [ ] **Step 1: Add the NON-OPS banner to the `.ps1` (no launch-logic change)**

Insert, immediately after the `param(...)` block and before the port logic, in
`apps/control-plane-api/scripts/run_platform_api_local.ps1`:
```powershell
Write-Host "[NON-OPS] This Windows launcher runs control-plane-api WITHOUT Infisical-sourced OPS_*." -ForegroundColor Yellow
Write-Host "[NON-OPS] The ops intake/recognition routers will NOT mount unless OPS_* are already in this Windows environment." -ForegroundColor Yellow
Write-Host "[NON-OPS] For ops-router work use the host launcher apps/control-plane-api/scripts/run_platform_api_local.sh (Infisical-backed) under the dev-residency workspace." -ForegroundColor Yellow
```
Do NOT change the existing `Get-NetTCPConnection` / `Stop-Process` / uvicorn
invocation.

- [ ] **Step 2: Verify the `.ps1` still parses**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  pwsh -NoProfile -Command "[void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path apps/control-plane-api/scripts/run_platform_api_local.ps1), [ref]\$null, [ref]\$errs); if (\$errs) { \$errs; exit 1 } else { \"PS-PARSE-OK\" }"' 2>&1 || echo "pwsh unavailable on host -- verify parse on Windows instead"
```
Expected: `PS-PARSE-OK` (or, if `pwsh` is not on the host, parse-check on Windows).

- [ ] **Step 3: Update the README local-development section**

In `apps/control-plane-api/README.md` (the block around the current
`run_platform_api_local.ps1` / `uvicorn` local-run instructions, ~lines 220-234
and the numbered helper note ~line 290):
- Present `apps/control-plane-api/scripts/run_platform_api_local.sh` (host,
  Infisical-backed) as the RECOMMENDED launch for ops-router work.
- Keep the `.ps1` documented for general Windows local (NON-OPS) work with the
  caveat that it does not mount the ops routers.
- Add the boundary note verbatim: "OPS_* come from Infisical dev (mesh) locally
  and from Render's dashboard env in production."
Do NOT rewrite the accurate port-8010 restart guidance.

- [ ] **Step 4: Relabel the two `.vscode/tasks.json` tasks NON-OPS + add the ops instruction**

In `.vscode/tasks.json`, for BOTH `"label": "Run platform API local"` and
`"label": "Restart platform API local"` (each runs the raw `.ps1` via `pwsh`):
- Change the label to include `(non-ops, Windows)`, e.g.
  `"Run platform API local (non-ops, Windows)"`.
- Add/extend a `"detail"` field: `"Runs WITHOUT Infisical OPS_*; the ops routers
  do NOT mount. For ops-router work use apps/control-plane-api/scripts/run_platform_api_local.sh on the dev-residency host."`
A committed cross-platform VS Code bash task for the host launcher is OPTIONAL
(it only works in the Remote-SSH context); the relabel + the README/detail ops
instruction are MANDATORY. Keep the JSON valid.

- [ ] **Step 5: Verify the reconciliation (grep asserts + JSON validity)**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  echo "=== .ps1 banner present ===" && grep -c "NON-OPS" apps/control-plane-api/scripts/run_platform_api_local.ps1 && \
  echo "=== tasks relabeled non-ops ===" && grep -c "non-ops" .vscode/tasks.json && \
  echo "=== README points at host launcher ===" && grep -c "run_platform_api_local.sh" apps/control-plane-api/README.md && \
  echo "=== tasks.json valid JSON ===" && python3 -c "import json,sys; json.load(open(\".vscode/tasks.json\")); print(\"JSON-OK\")"'
```
Expected: `NON-OPS` count >= 3, `non-ops` count >= 2 (both tasks), README count
>= 1, `JSON-OK`.

- [ ] **Step 6: ASCII-check and commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  git add apps/control-plane-api/scripts/run_platform_api_local.ps1 apps/control-plane-api/README.md .vscode/tasks.json && \
  git diff --cached | grep "^+" | LC_ALL=C grep -P "[^\x00-\x7F]" && echo "NON-ASCII" || echo "ASCII-CLEAN"'
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && git commit -m "docs(control-plane-api): reconcile Windows launcher as non-ops; recommend host Infisical launcher

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

## Task 2: secret-audit.sh -- register app cache + Check 1d (TDD via fixture)

**Files:**
- Create: `infra/database/migrations/records/test_secret_audit_cache_coverage.sh`
- Modify: `infra/secret-audit.sh` (default `CACHES` array; new Check 1d after 1c)
- Modify: `.github/workflows/records-ci.yml` (add the fixture step)

**Interfaces:**
- Consumes: existing `secret-audit.sh` globals -- `ROOT`, `rc`, `CACHES`,
  `ENV_ALLOWED_KEYS`, `MANAGED`, `MNAMES[]`, `say()` -- and Check 1c's anchored
  regex `^[[:space:]]*(export[[:space:]]+)?${nm}[[:space:]]*=`.
- Produces: Check 1d emits `FAIL  uncovered cache holds managed name: <name> in
  <path>` per uncovered hit and ALWAYS a `PASS|FAIL  cache-coverage check ran
  (<n> managed name(s), <d> caches discovered, <r> registered)` summary line.

- [ ] **Step 1: Write the failing fixture test (5 cases)**

Create `infra/database/migrations/records/test_secret_audit_cache_coverage.sh`,
replicating the `test_secret_audit_env_allowlist.sh` harness (cp the real audit
into the fixture repo so its `BASH_SOURCE`-derived `ROOT` lands on the fixture;
override `HOME` so the out-of-`$ROOT` depth-1 sweep stays in the temp home).

```bash
#!/usr/bin/env bash
# Check 1d (cache-coverage completeness) fixture for infra/secret-audit.sh.
# Proves an armed managed name in an UNREGISTERED cache FAILs, that symlinks are
# discovered/deduped by device+inode, and that the coverage summary is emitted on
# both pass and fail. All planted values are synthetic PLACEHOLDERs and must be
# absent from audit output.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../../../.." && pwd)"
AUDIT="$ROOT/infra/secret-audit.sh"
[[ -f "$AUDIT" ]] || { echo "FATAL: cannot locate infra/secret-audit.sh (ROOT=$ROOT)" >&2; exit 2; }

fail=0; say() { printf '%s\n' "$*"; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
PLACEHOLDER='PLACEHOLDER-TEST-VALUE-000000'
MNAME='OPS_API_DSN'

# Build a fixture repo whose copied audit resolves ROOT onto the fixture and
# registers infra/.env + apps/control-plane-api/.env (Check 1d/1c CACHES).
make_repo() {
  local repo="$1"
  mkdir -p "$repo/infra/infisical" "$repo/apps/control-plane-api"
  cp "$AUDIT" "$repo/infra/secret-audit.sh"; chmod +x "$repo/infra/secret-audit.sh"
  printf 'infra/.env\napps/control-plane-api/.env\n' > "$repo/.gitignore"
  git -C "$repo" init -q
  git -C "$repo" add .gitignore infra/secret-audit.sh
  : > "$repo/infra/infisical/.managed-secrets"   # empty = dormant by default
}
arm() { printf '%s\n' "$MNAME" >> "$1/infra/infisical/.managed-secrets"; }
run_audit() { HOME="$tmp/home" bash "$1/infra/secret-audit.sh" 2>&1; }
mkdir -p "$tmp/home"

# --- Case 1: registered cache holds an armed name -> Check 1c drift FAIL -------
r1="$tmp/c1"; make_repo "$r1"
printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$r1/apps/control-plane-api/.env"; chmod 600 "$r1/apps/control-plane-api/.env"
out="$(run_audit "$r1")"                 # dormant: not armed yet
if printf '%s' "$out" | grep -qF "drift: '$MNAME'"; then say "FAIL  case1 fired while dormant"; fail=1; else say "PASS  case1 dormant before arming"; fi
arm "$r1"; out="$(run_audit "$r1")"
if printf '%s' "$out" | grep -qF "drift: '$MNAME' is Infisical-managed but still copied"; then say "PASS  case1 Check 1c drift FAIL after arm"; else say "FAIL  case1 drift not raised"; fail=1; fi

# --- Case 2: unregistered NESTED physical cache holds armed name -> Check 1d ---
r2="$tmp/c2"; make_repo "$r2"; arm "$r2"
mkdir -p "$r2/apps/control-plane-api/scripts"
printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$r2/apps/control-plane-api/scripts/.env"
out="$(run_audit "$r2")"; rc2=$?
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name: $MNAME"; then say "PASS  case2 uncovered-cache FAIL line"; else say "FAIL  case2 missing uncovered FAIL"; fail=1; fi
[[ "$rc2" == "1" ]] && say "PASS  case2 rc=1" || { say "FAIL  case2 rc=$rc2 (want 1)"; fail=1; }
# name-armed guard: the drift/coverage machinery ran (managed-name count in summary >= 1)
if printf '%s' "$out" | grep -qE "cache-coverage check ran \([1-9][0-9]* managed name"; then say "PASS  case2 name-armed (managed>=1)"; else say "FAIL  case2 not armed"; fail=1; fi
# discovered-count proves enumeration (the planted nested cache was swept)
if printf '%s' "$out" | grep -qE "cache-coverage check ran \([0-9]+ managed name\(s\), [1-9][0-9]* caches discovered"; then say "PASS  case2 discovered>=1 (planted cache enumerated)"; else say "FAIL  case2 discovered count 0"; fail=1; fi

# --- Case 3: unregistered SYMLINK to an OUTSIDE physical cache -> Check 1d -----
r3="$tmp/c3"; make_repo "$r3"; arm "$r3"
outside="$tmp/outside-cache.env"; printf '%s=%s\n' "$MNAME" "$PLACEHOLDER" > "$outside"
ln -s "$outside" "$r3/.env.linked"       # symlink under ROOT, name matches .env*
out="$(run_audit "$r3")"
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name: $MNAME"; then say "PASS  case3 symlink-to-outside FAIL"; else say "FAIL  case3 symlink not discovered"; fail=1; fi

# --- Case 4: symlink to a REGISTERED cache -> %d:%i collapse, no spurious FAIL -
r4="$tmp/c4"; make_repo "$r4"; arm "$r4"
printf 'DEV_PG_PASSWORD=%s\n' "$PLACEHOLDER" > "$r4/infra/.env"; chmod 600 "$r4/infra/.env"  # registered, no managed name
ln -s "$r4/infra/.env" "$r4/apps/.env.mirror"   # symlink to the registered infra/.env
out="$(run_audit "$r4")"
if printf '%s' "$out" | grep -qF "uncovered cache holds managed name"; then say "FAIL  case4 spurious uncovered-FAIL on registered-target symlink"; fail=1; else say "PASS  case4 registered-target symlink collapsed (no spurious FAIL)"; fi

# --- Case 5: clean -> PASS summary with non-zero discovered count, rc=0 --------
r5="$tmp/c5"; make_repo "$r5"; arm "$r5"
printf 'DEV_PG_PASSWORD=%s\n' "$PLACEHOLDER" > "$r5/infra/.env"; chmod 600 "$r5/infra/.env"
out="$(run_audit "$r5")"; rc5=$?
if printf '%s' "$out" | grep -qE "PASS  cache-coverage check ran \([0-9]+ managed name\(s\), [1-9][0-9]* caches discovered"; then say "PASS  case5 clean PASS summary w/ discovered>=1"; else say "FAIL  case5 no clean PASS summary"; fail=1; fi
[[ "$rc5" == "0" ]] && say "PASS  case5 rc=0" || { say "FAIL  case5 rc=$rc5 (want 0)"; fail=1; }

# --- Value-silence: the PLACEHOLDER must never appear in any output ------------
for r in "$r1" "$r2" "$r3" "$r4" "$r5"; do
  if run_audit "$r" | grep -qF -- "$PLACEHOLDER"; then say "FAIL  value-silent violation: placeholder leaked"; fail=1; fi
done
say "PASS  value-silent: placeholder absent from all output"

if [[ "$fail" == "0" ]]; then say "RESULT: cache-coverage fixture PASSED"; else say "RESULT: cache-coverage fixture FAILED"; fi
exit "$fail"
```

- [ ] **Step 2: Run the fixture to verify it fails (no Check 1d yet)**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  bash infra/database/migrations/records/test_secret_audit_cache_coverage.sh; echo "rc=$?"'
```
Expected: FAIL -- Case 2/3/5 have no `uncovered cache holds managed name` /
`cache-coverage check ran` lines yet (Check 1d absent), and Case 2 also fails
because `apps/control-plane-api/.env` is not registered so its drift is not seen;
`rc=1`.

- [ ] **Step 3a: Register the app cache in the default CACHES**

In `infra/secret-audit.sh`, the `CACHES` array (currently):
```bash
declare -a CACHES=(
  "$ROOT/infra/.env:0"
  "$HOME/code/apex/.env.dev-pg-offsite-backup:0"
)
```
Add the app cache line:
```bash
declare -a CACHES=(
  "$ROOT/infra/.env:0"
  "$ROOT/apps/control-plane-api/.env:0"
  "$HOME/code/apex/.env.dev-pg-offsite-backup:0"
)
```

- [ ] **Step 3b: Add Check 1d after Check 1c**

Insert immediately after the Check 1c block (after its closing `fi`), in
`infra/secret-audit.sh`:
```bash
# ---- Check 1d: cache-coverage completeness (device+inode-aware) -----------
# Guarantees the physical caches actually holding a managed name are a SUBSET of
# the registered, scanned CACHES -- so drift-verify cannot false-green on a cache
# nobody registered, within a bounded discovery set (every .env* under $ROOT plus
# registered caches plus depth-1 siblings of out-of-$ROOT registered dirs).
# Dormant unless .managed-secrets names >= 1 secret (same trigger as Check 1c).
if [[ -f "$MANAGED" && "${#MNAMES[@]}" -gt 0 ]]; then
  # 1. Registered device+inode set (follow symlinks; %d:%i is cross-fs safe).
  declare -A REGISTERED_DEVINO=()
  for entry in "${CACHES[@]}"; do
    rf="${entry%:*}"; [[ -e "$rf" ]] || continue
    di="$(stat -L -c '%d:%i' "$rf" 2>/dev/null)" || continue
    [[ -n "$di" ]] && REGISTERED_DEVINO["$di"]=1
  done
  # 2. Discover candidates: registered paths + recursive find -P under $ROOT +
  #    depth-1 siblings of out-of-$ROOT registered dirs. -P does not descend
  #    directory symlinks (no escape from $ROOT) but matches .env* symlink files.
  declare -a CANDIDATES=()
  for entry in "${CACHES[@]}"; do rf="${entry%:*}"; [[ -e "$rf" ]] && CANDIDATES+=("$rf"); done
  while IFS= read -r f; do [[ -n "$f" ]] && CANDIDATES+=("$f"); done < <(
    find -P "$ROOT" -name '.env*' \( -type f -o -type l \) \
      -not -path '*/node_modules/*' -not -path '*/.git/*' \
      -not -name '*.example' -not -name '*.sample' -not -name '*.template' 2>/dev/null
  )
  for entry in "${CACHES[@]}"; do
    rf="${entry%:*}"; case "$rf" in "$ROOT"/*) continue;; esac
    rdir="$(dirname "$rf")"; [[ -d "$rdir" ]] || continue
    while IFS= read -r f; do [[ -n "$f" ]] && CANDIDATES+=("$f"); done < <(
      find -P "$rdir" -maxdepth 1 -name '.env*' \( -type f -o -type l \) \
        -not -name '*.example' -not -name '*.sample' -not -name '*.template' 2>/dev/null
    )
  done
  # 3. FAIL any managed name in an UNREGISTERED candidate; dedup + count by devino.
  declare -A SEEN_DEVINO=()
  d_count=0; cov_fail=0
  for f in "${CANDIDATES[@]}"; do
    di="$(stat -L -c '%d:%i' "$f" 2>/dev/null)" || continue
    [[ -n "$di" && -z "${SEEN_DEVINO[$di]:-}" ]] || continue
    SEEN_DEVINO["$di"]=1; d_count=$((d_count+1))
    [[ -n "${REGISTERED_DEVINO[$di]:-}" ]] && continue   # registered -> Check 1c's domain
    for nm in "${MNAMES[@]}"; do
      if grep -qE "^[[:space:]]*(export[[:space:]]+)?${nm}[[:space:]]*=" "$f" 2>/dev/null; then
        say "  FAIL  uncovered cache holds managed name: $nm in $f"; rc=1; cov_fail=1
      fi
    done
  done
  prefix="PASS"; [[ "$cov_fail" == "1" ]] && prefix="FAIL"
  say "  $prefix  cache-coverage check ran (${#MNAMES[@]} managed name(s), $d_count caches discovered, ${#REGISTERED_DEVINO[@]} registered)"
fi
```

- [ ] **Step 4: Run the fixture to verify it passes**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  bash infra/database/migrations/records/test_secret_audit_cache_coverage.sh; echo "rc=$?"; \
  shellcheck infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_cache_coverage.sh; echo "shellcheck_rc=$?"'
```
Expected: every `PASS ...` line present, `RESULT: cache-coverage fixture PASSED`,
`rc=0`. (shellcheck: pre-existing `secret-audit.sh` style warnings may exist;
ensure NO new error-level findings in the added Check 1d block or the fixture.)

- [ ] **Step 5: Re-run the two existing audit fixtures (no regression)**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  bash infra/database/migrations/records/test_secret_audit_env_allowlist.sh; echo "allowlist_rc=$?"; \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh; echo "ac8_rc=$?"'
```
Expected: both `*_rc=0` (Check 1d is dormant when `.managed-secrets` is empty, so
neither existing fixture changes behavior).

- [ ] **Step 6: Wire the new fixture into CI**

In `.github/workflows/records-ci.yml`, beside the existing audit fixture steps:
```yaml
      - name: cache-coverage fixture test (Check 1d)
        run: bash infra/database/migrations/records/test_secret_audit_cache_coverage.sh
```

- [ ] **Step 7: ASCII-check and commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && \
  git add infra/secret-audit.sh infra/database/migrations/records/test_secret_audit_cache_coverage.sh .github/workflows/records-ci.yml && \
  git diff --cached | grep "^+" | LC_ALL=C grep -P "[^\x00-\x7F]" && echo "NON-ASCII" || echo "ASCII-CLEAN"'
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-infisical-cutover && git commit -m "feat(secret-audit): register app cache + Check 1d cache-coverage guard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'
```

---

## Task 3 (cross-engine review before finishing)

After Tasks 0-2 are green, run the Codex whole-branch review via the wired
apex-jobs front door against `origin/main` (per the Independent Review Protocol),
fold any findings, then use superpowers:finishing-a-development-branch. The
operator lean is push + open a PR (independent merge timing, no admin bypass,
review-count=0 self-merge after green CI + IRP/Codex). Do NOT run the Operator
Cutover Runbook until after the PR merges.

---

## Operator Cutover Runbook (post-merge, operator-gated -- NOT a code task)

Runs on the host AFTER the PR merges to main and the canonical
`apex-power-ops-platform` checkout has the new launcher + Check 1d. Strict order;
the agent assists value-silent but NEVER edits a credential value.

1. **Pre-purge precondition (value-silent).** Confirm Infisical dev resolves BOTH
   names -- do NOT use a pre-purge router-mount smoke (it false-greens from the
   still-populated cache):
   ```bash
   cd /home/olares/code/apex/apex-power-ops-platform
   infra/infisical/inject.sh dev -- bash -c 'for n in OPS_API_DSN OPS_INTAKE_WRITER_DSN; do [ -n "${!n:-}" ] && echo "$n PRESENT" || echo "$n ABSENT"; done'
   ```
   Require both `PRESENT` before continuing.
2. **Operator purge (out of band).** The agent hands these exact NAME/path
   targets; the OPERATOR removes the two lines from each and confirms. The agent
   never sed-edits a credential file.
   - `apex-power-ops-platform/infra/.env`: remove `OPS_API_DSN=` and
     `OPS_INTAKE_WRITER_DSN=` (the two worktree symlinks auto-clear).
   - `apex-power-ops-platform/apps/control-plane-api/.env`: remove the same two.
   - If a Windows-local checkout exists: remove the same two from BOTH its
     `apps/control-plane-api/.env` AND its `infra/.env`; else record "not present."
3. **Post-purge proof.**
   - POSITIVE: `apps/control-plane-api/scripts/run_platform_api_local.sh`; assert
     the OpenAPI surface advertises BOTH ops routes (intake AND recognition) --
     fail if either is missing.
   - NEGATIVE control: `env -u OPS_API_DSN -u OPS_INTAKE_WRITER_DSN uvicorn
     main:app --app-dir apps/control-plane-api` (no inject.sh); assert NEITHER ops
     route is advertised.
4. **Verify no lingering copy (value-silent, names only):**
   ```bash
   cd /home/olares/code/apex/apex-power-ops-platform
   for f in infra/.env apps/control-plane-api/.env; do
     for n in OPS_API_DSN OPS_INTAKE_WRITER_DSN; do
       c=$(grep -cE "^[[:space:]]*(export[[:space:]]+)?$n[[:space:]]*=" "$f" 2>/dev/null || echo 0)
       echo "$f $n=$c"
     done
   done
   ```
   Require all counts `=0`.
5. **Arm `.managed-secrets` (LAST).** Append the two NAMES to
   `apex-power-ops-platform/infra/infisical/.managed-secrets`:
   ```
   OPS_API_DSN
   OPS_INTAKE_WRITER_DSN
   ```
6. **Authoritative audit.** Invoke the canonical checkout's own script path
   (ROOT is script-location-derived):
   ```bash
   bash /home/olares/code/apex/apex-power-ops-platform/infra/secret-audit.sh
   ```
   Confirm: no `OPS_*` under Check 1b for `infra/.env`; no OPS_* drift/coverage
   FAIL under Check 1c/1d. The audit stays rc=1 on the three deferred keys
   (`TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`, `SUPABASE_PROD_DSN`) -- expected;
   that is the scoped success criterion, not audit rc=0.

---

## Self-Review notes

- **Spec coverage:** launcher (spec 3.1) -> Task 0; `.ps1`/README/tasks
  reconciliation (3.2/3.3) -> Task 1; CACHES registration (4.1) + Check 1d (4.2)
  -> Task 2 steps 3a/3b; fixture with 5 cases incl outside-symlink + self-
  validating Case 2 (8.1) -> Task 2 step 1; CI wire (8.2) -> Task 2 step 6;
  launcher argv test (8.3) -> Task 0; verification/smoke (9) + sequence (7) +
  purge (6) + arm (5) -> Operator Cutover Runbook; honest success (10) -> Global
  Constraints. All spec sections mapped.
- **No placeholders:** every code step carries complete bash/powershell/yaml.
- **Type/name consistency:** Check 1d reuses the exact Check 1c regex and the
  audit globals (`ROOT`, `rc`, `CACHES`, `MANAGED`, `MNAMES`, `say`); the fixture
  asserts the exact `uncovered cache holds managed name` / `cache-coverage check
  ran` strings the impl emits; the launcher argv string matches between Task 0
  step 1 (expected) and step 3 (launcher).
