# TCC_BREAKER_* Infisical Cutover + Retire Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, single-writer over mesh). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Cut `TCC_BREAKER_RO_PW` over to Infisical `dev` (docs + arm) and retire `TCC_BREAKER_CODEX_PW`; no code change (the access-harness already reads `os.environ`). OOB steps (Infisical load + cache removal) are DONE + verified.

**Architecture:** Docs (2 READMEs) + a one-line `.managed-secrets` arm + value-silent verification. The OOB gated steps are complete: RO_PW is in Infisical `dev`, both keys are out of host `infra/.env`, and the injected host round-trip is green.

**Spec:** `docs/superpowers/specs/2026-07-07-tcc-breaker-infisical-cutover-design.md`

## Global Constraints

- Host-canonical single-writer over mesh (author local -> scp -> commit host-side); lane branch in the MAIN worktree `/home/olares/code/apex/apex-power-ops-platform` (caches present for injection + `secret-audit`); restore `main` after merge.
- Value-silent: names/booleans only, never a secret value or DSN.
- ASCII-only added lines.
- `secret-audit.sh` `ENV_ALLOWED_KEYS` UNCHANGED; `TCC_BREAKER_CODEX_PW` is NOT armed; sandbox DB/role DROP is OUT of scope (separate packet).
- Merge governance: squash, author self-merge after green CI + Codex, NO admin-bypass.
- Mesh conventions: `SSH`=`ssh olares-mesh`; `REPO`=`/home/olares/code/apex/apex-power-ops-platform`; `PATHX`=`export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH`.

---

## Task 1: docs -- access-harness injected runbook + sandbox CODEX retirement

**Files:**
- Modify: `infra/database/access-harness/README.md`
- Modify: `infra/database/sandbox/breaker/README.md`

- [ ] **Step 1: access-harness README.** In the Environment table row for `TCC_BREAKER_RO_PW` and/or a nearby "Running on the host" note, record: the value is injected from Infisical `dev` (`infra/infisical/inject.sh dev -- <cmd>`) for host-side `snapshot-tcc`/tests; `host_tcc_conn` targets the sandbox viewer clone `tcc_breaker_viewer_20260625` on `100.64.0.1:5432`; the Windows full-Access pipeline reads `TCC_BREAKER_RO_PW` as a Windows env var (a separate machine cache, not the host `infra/.env`). Exact hunk pinned at execution after reading the current bytes.
- [ ] **Step 2: sandbox/breaker README.** Add a "Status / credential retirement" note: the breaker sandbox is a completed 2026-06-25 one-off; `TCC_BREAKER_CODEX_PW` is retired (removed from host `infra/.env`, NOT loaded into Infisical, NOT armed in `.managed-secrets`); the codex-harness + `_20260625` DBs/roles are leftover residue for a separate destructive-cleanup packet; re-running the sandbox requires re-seeding the vars. Exact hunk pinned at execution.
- [ ] **Step 3: scp both, ASCII-check (diff-scoped).**

Run: `SSH 'cd REPO && git --no-pager diff -- infra/database/access-harness/README.md infra/database/sandbox/breaker/README.md | grep "^+" | grep -v "^+++" | LC_ALL=C grep -nP "[^\x00-\x7F]" && echo NON_ASCII_ADDED || echo ADDED_LINES_ASCII_CLEAN'`. Any line the diff touches must be ASCII on its added (`+`) form -- normalize a legacy em dash to `--` if a changed line carries one. Untouched legacy non-ASCII elsewhere in the file is out of scope.
- [ ] **Step 4: Commit.**

`SSH 'cd REPO && git add infra/database/access-harness/README.md infra/database/sandbox/breaker/README.md && git commit -m "docs(secrets): TCC_BREAKER_RO_PW injected runbook + TCC_BREAKER_CODEX_PW retirement" ...'`

---

## Task 2: arm TCC_BREAKER_RO_PW + no-regression audit

**Files:**
- Modify: `infra/infisical/.managed-secrets` (append `TCC_BREAKER_RO_PW`)

- [ ] **Step 1: Re-verify injected round-trip (clean shell, injection-only).**

Run: `SSH 'cd REPO && PATHX && infra/infisical/inject.sh dev -- bash -c "cd infra/database/access-harness && uv run python - <<PY
from access_harness.snapshot_tcc import host_tcc_conn
c=host_tcc_conn(); c.execute(\"select 1\").fetchone(); c.close(); print(\"RO_ROUNDTRIP_OK\")
PY"' 2>&1 | grep -viE "release of infisical|To update|Injecting" | tail -3`
Expected: `RO_ROUNDTRIP_OK`.

- [ ] **Step 2: Arm RO_PW.** Append `TCC_BREAKER_RO_PW` as a new line to `infra/infisical/.managed-secrets` (after `APEX_JOBS_PGPASSWORD`). Do NOT add `TCC_BREAKER_CODEX_PW`.

- [ ] **Step 3: scp + no-regression audit (value-silent).**

`scp .managed-secrets`; then
Run: `SSH 'cd REPO && bash infra/secret-audit.sh > /tmp/a.out 2>&1; echo AUDIT_RC=$?; grep -iE "FAIL|allowed:|drift|managed name" /tmp/a.out; grep -i "TCC_BREAKER" /tmp/a.out; rm -f /tmp/a.out' 2>&1 | grep -viE "password=|dsn=[a-z]"`
Expected: `AUDIT_RC=1`; Check-1b FAILs ONLY `SUPABASE_PROD_DSN` (TCC_BREAKER_RO_PW + TCC_BREAKER_CODEX_PW no longer flagged); Check 1c drift check PASS including `TCC_BREAKER_RO_PW` (armed, not in any cache); no `TCC_BREAKER_CODEX_PW` finding anywhere.

- [ ] **Step 4: ASCII-check + commit.**

`SSH 'cd REPO && LC_ALL=C grep -qP "[^\x00-\x7F]" infra/infisical/.managed-secrets && { echo NON_ASCII; exit 1; } || echo ASCII_CLEAN; git add infra/infisical/.managed-secrets && git commit -m "secrets: arm TCC_BREAKER_RO_PW in .managed-secrets (Infisical dev cutover)" ...'`

---

## Task 3: Codex whole-branch review + finish

- [ ] **Step 1: Whole-branch Codex via the front door (through injection).**

Run: `SSH 'cd REPO && PATHX && infra/infisical/apex-jobs.sh review-run --review-head secrets/tcc-breaker-infisical-cutover --base-ref main --json' 2>&1 | grep -viE "release of infisical|To update|Injecting"`
Adjudicate any finding value-silently; fix on the branch; re-run. Fold into the review record.

- [ ] **Step 2: Push + open PR (host gh).** PR body leads with: RO_PW cut over to Infisical dev (injected; armed), CODEX_PW retired (no load/arm; dead one-off), sandbox DB/role DROP deferred to a separate packet, verified OOB (cache absence + Infisical presence + RO_ROUNDTRIP_OK), no-regression audit (Check-1b down to SUPABASE_PROD_DSN only), Codex clean.

- [ ] **Step 3: STOP for CI.** Do not merge until checks green (governance). On green: squash-merge (no admin-bypass), restore main worktree to main, doc reconcile (platform-hygiene note, .remember, memory; next parked key = SUPABASE_PROD_DSN, prod-path/gated).

## Self-Review (authoring)

- Spec coverage: RO cutover docs (T1) + arm (T2) / CODEX retirement doc (T1) + not-armed (T2) / no-regression audit (T2) / Codex + finish (T3) / sandbox-DROP out of scope (Global) / KEEP sanitizer batteries (Global) / host-scope + Windows-env-var-separate (T1 doc). Mapped.
- No code change (harness reads env); no placeholders (exact hunks pinned at execution after reading current bytes -- deliberate, since READMEs weren't fully re-read yet).
