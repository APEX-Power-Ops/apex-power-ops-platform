# P0-A Runtime-Integrity Hardening Plan

> **For agentic workers:** negative-tests-first TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Close five runtime-integrity findings the operator raised in the post-merge review of the P0-A evidence tooling (`cf1c72f3`, PR #98), so a governed production evidence run cannot be subverted by an import shadow, a stale/ancestor checkout, a caller-chosen DB role, a secret exported into the operator shell, or an unverified closeout.

**Authorization:** operator GO `PM-OPS-P0A-RUNTIME-INTEGRITY ONLY` (design-only; no prod access/SQL/HTTP/deploy/secret change). Build → focused negative tests → governed PR → **STOP after merge**. The separate `P0-A READ-ONLY EVIDENCE` GO remains HELD.

**Architecture:** All work is in `apps/mutation-seam/scripts/pm_ops_p0/`. The security model is unchanged in intent (bind → guard → read-only snapshot → atomic custody); these are integrity corrections to the *governance envelope* around it. The gold-standard precedent is `infra/database/schema-placement/CENSUS_RUNBOOK.md` + `collect_disposition.py` (fresh-fetch HEAD-equality, child-only Infisical injection, no shell secret export).

**Tech Stack:** Python 3.12, psycopg 3.3.4 (host-run tooling only), pytest 9.0.3, ruff 0.15.15. Offline tests only — no live DB. Real `git` temp-repos (with local file remotes) exercise the git-state gate offline.

## Global Constraints

- Project ref is `fxoyniqnrlkxfligbxmg`; expected admin DB role is `postgres` (source-pinned, non-overridable).
- Value-silence absolute: no DSN / host / password / role value ever printed or logged; failures surface as stable value-free codes only.
- Deferred/lazy imports of `pm_ops_p0.binding` (and thus `psycopg`) must occur only AFTER every governance pre-flight guard has passed.
- Repo pristine = clean tracked tree AND no untracked files (`git status --porcelain`, no `--untracked-files=no`).
- Governance equality: `HEAD == origin/main == --expect-repo-sha` after a fresh `git fetch origin main`. Ancestor is insufficient.
- No new third-party dependency (the finalizer is stdlib-only).
- LF line endings, final newline, 0 CR on every file; ruff check + ruff format clean; whole existing suite stays green.

---

### Task R1: F1 — import-shadow / runtime-provenance guard

**Files:**
- Modify: `apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py`
- Test: `apps/mutation-seam/scripts/pm_ops_p0/tests/test_preserve_evidence.py`

**Vulnerability:** `sys.path.insert(0, .../scripts)` + top-level `from pm_ops_p0.binding import …` (→ `import psycopg`) means an untracked `scripts/psycopg.py` (or `pm_ops_p0/subprocess.py`) executes at module load — before any guard — and `git status --untracked-files=no` hides it.

**Fix:**
- Top of module: drop the script's own directory from `sys.path` (defense-in-depth for the module's own stdlib imports), using only `sys`+`os` (already loaded, unshadowable). Remove the manual `scripts` insert.
- Do NOT import `pm_ops_p0.binding`/`psycopg` at module top. Import them lazily inside `collect_evidence()` and in `main()`'s live-capture block — after all pre-flight guards pass. Re-add the `scripts` dir there (safe post-guard: the pristine guard proved no untracked shadow file exists).
- `_repo_git_state`: change the clean check to `git status --porcelain` (untracked INCLUDED). Any untracked file ⇒ not clean ⇒ `repo_dirty` refusal in `main()` before the deferred import.

**Steps:**
- [ ] Write negative test `test_untracked_import_shadow_rejected_before_secrets`: real temp git repo, clean, then plant an untracked `psycopg.py` whose import would set a module-global sentinel; point `_repo_root` at it; run the real `_repo_git_state`/`main` gate; assert refusal (`repo_dirty`) AND the sentinel was never set (shadow never imported) AND no connect attempted.
- [ ] Run: fails (untracked currently ignored / shadow importable).
- [ ] Implement the sys.path neutralization + deferred imports + untracked-inclusive clean check.
- [ ] Run: passes; full suite still green.
- [ ] Commit.

### Task R2: F2 — HEAD == origin/main == expect-sha (fresh fetch)

**Files:** same two.

**Fix:** `_repo_git_state` performs a fresh `git fetch origin main` and returns `(head_sha, is_clean, origin_main_sha|None)`. `main()` refuses unless: clean; `head_sha == --expect-repo-sha` (`repo_sha_mismatch`); `origin_main_sha is not None` (`origin_main_unresolvable`, fail-closed on fetch failure / missing ref); `head_sha == origin_main_sha` (`repo_head_not_origin_main`) — equality replaces the old `merge-base --is-ancestor`. Update `_patched_repo` to inject `(sha, clean, origin_main_sha)`.

**Steps:**
- [ ] Write negative test `test_historical_ancestor_of_origin_main_rejected`: real temp repo + local bare remote; HEAD is an ancestor of origin/main but not equal ⇒ `repo_head_not_origin_main`. Plus `test_head_equals_origin_main_passes_gate` (equality ⇒ gate clears to bind).
- [ ] Update the existing `_patched_repo`-based refusal tests to the new 3-tuple; rename `repo_not_on_main` → `repo_head_not_origin_main`.
- [ ] Run: fails.
- [ ] Implement fetch + equality.
- [ ] Run: passes; suite green.
- [ ] Commit.

### Task R3: F3 — source-pin the `postgres` DB role

**Files:** same two.

**Fix:** remove the `--expect-db-role` CLI option; hardcode `EXPECTED_DB_ROLE`. `collect_evidence` drops the `expect_role` parameter (uses the constant); `_ROLE_CHECK_SQL` compares `current_user` to the pinned role; provenance records the pinned role.

**Steps:**
- [ ] Write negative test `test_expect_db_role_flag_is_rejected` (`--expect-db-role x` ⇒ argparse SystemExit≠0) and keep `test_collect_evidence_refuses_wrong_db_role_before_evidence` (current_user≠postgres ⇒ `db_role_mismatch`) with the updated signature.
- [ ] Run: fails.
- [ ] Implement removal + pin.
- [ ] Run: passes; suite green.
- [ ] Commit.

### Task R4: F4 — runbook child-only Infisical injection

**Files:**
- Modify: `docs/superpowers/specs/pm-ops-p0/P0A_RUNBOOK.md`
- Test: `apps/mutation-seam/scripts/pm_ops_p0/tests/test_preserve_evidence.py`

**Fix:** Part A run block becomes (matching CENSUS_RUNBOOK):
```
git fetch --quiet origin main
MAIN_SHA=$(git rev-parse origin/main)
infra/infisical/inject.sh prod -- \
  <repo>/.venv/bin/python apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py \
    --expect-project-ref fxoyniqnrlkxfligbxmg --dsn-env SUPABASE_PROD_DSN \
    --expect-repo-sha "$MAIN_SHA"
```
No `export SUPABASE_PROD_DSN`; no `--expect-db-role` (removed). Add a "Do NOT export any secret into this shell" note.

**Steps:**
- [ ] Write doc-lint test `test_runbook_uses_child_only_injection`: reads `P0A_RUNBOOK.md`; asserts it contains `infra/infisical/inject.sh prod --` and `--dsn-env`; asserts it contains NO literal `export SUPABASE_PROD_DSN=` (and no `--expect-db-role`).
- [ ] Run: fails.
- [ ] Rewrite the runbook Part A + preconditions.
- [ ] Run: passes.
- [ ] Commit.

### Task R5: F5 — fail-closed nine-category closeout finalizer

**Files:**
- Create: `apps/mutation-seam/scripts/pm_ops_p0/finalize_closeout.py` (stdlib only)
- Create: `apps/mutation-seam/scripts/pm_ops_p0/tests/test_finalize_closeout.py`

**Interface (Produces):**
- `load_spec(path) -> list[Category]` — parse the closeout spec JSON (`{category:int, source:str, artifacts:[path]}`).
- `finalize(spec_path, custody_dir, out_path) -> Path` — validate + write `closeout_index.json` no-clobber; raises `CloseoutError(code)` (value-free) on any failure.
- Validation, fail-closed: all categories 1..9 present exactly once (`missing_category` / `duplicate_category`); each artifact path resolves inside `custody_dir` (reject `..`/absolute traversal → `artifact_path_escape`); each artifact is a regular file (`artifact_not_regular`); HTTP categories (1,2) parse as JSON with an expected marker (`failed_http`); every artifact hashed (`unhashed_artifact` if a listed script artifact is absent from `manifest.sha256` or its hash disagrees). Output binds every artifact by SHA-256; `O_EXCL` no-clobber.

**Steps (each: write failing test → run fail → implement → run pass → commit):**
- [ ] `test_finalize_missing_category_fails`
- [ ] `test_finalize_duplicate_category_fails`
- [ ] `test_finalize_failed_http_artifact_fails` (category-1 artifact is an HTML error page, not OpenAPI JSON)
- [ ] `test_finalize_unhashed_artifact_fails` (script artifact missing from manifest / hash mismatch)
- [ ] `test_finalize_path_traversal_rejected` and `test_finalize_non_regular_artifact_rejected`
- [ ] `test_finalize_index_binds_every_artifact_by_sha256`
- [ ] `test_finalize_no_clobber` (second finalize ⇒ `FileExistsError`/`CloseoutError`)
- [ ] Implement `finalize_closeout.py`; wire into runbook Part C as the closeout step.

### Task R6: Regression + ruff + LF verify + review record

- [ ] Full offline suite green on host `.venv` (all existing + new); `ruff check .` + `ruff format --check .` clean.
- [ ] LF byte-verify every edited/new file (0 CR, final LF).
- [ ] Append **Round 3** to `docs/superpowers/specs/pm-ops-p0/2026-07-14-p0a-tooling-review-record.md` (the five findings + dispositions).
- [ ] Commit.

### Task R7: Cross-engine IRP review (mandatory)

- [ ] Deep audit IRP vs `main`: Codex `gpt-5.5` via `apex-jobs review-run --review-head pm-ops/p0a-runtime-integrity --base-ref main` + two adversarial Claude lenses (A: F1 shadow-bypass + value-silence; B: F5 fail-closed completeness + no-clobber + F2 equality logic). Fold every finding; converge.

### Task R8: Governed PR + squash merge; STOP

- [ ] Push branch; open governed PR; green CI; squash merge; **no admin bypass**.
- [ ] Reconcile durable memory. STOP. Surface operator post-merge steps (fast-forward primary worktree at stale `270ca6e1`; rederive merge SHA; issue the separate `P0-A READ-ONLY EVIDENCE` GO) and re-flag P0-E-must-adopt-`connect_bound`. No production access at any point.
