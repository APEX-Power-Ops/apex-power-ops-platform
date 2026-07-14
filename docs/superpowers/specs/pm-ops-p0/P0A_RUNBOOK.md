# P0-A Read-Only Evidence — Runbook & Closeout Index

**Scope.** P0-A of the PM/Ops emergency-containment lane: capture approved pre-change
evidence, read-only, before any P0-B..E action. This runbook binds **all nine** design
§2 evidence categories into one closeout.

> **Hard rule (review finding 4).** `preserve_evidence.py` captures only the **database
> subset** of P0-A. Running it alone does **NOT** complete P0-A. P0-A is complete only
> when every one of the nine categories below has an artifact + hash in the closeout
> index and the operator has reviewed the drift call.

**Preconditions.**
- A live, in-your-own-voice **`P0-A READ-ONLY EVIDENCE`** operator GO (this runbook does not grant it).
- Run **only from clean, merged `main`** — the script enforces a **pristine** tree (clean + **no untracked** files) and `HEAD == origin/main == --expect-repo-sha` by **equality** after a fresh `git fetch origin main` (not a mere ancestor test; review round-3 findings 1–2).
- The DSN is injected into the **child process only** via `infra/infisical/inject.sh prod` and read from an **environment variable name** (never a value on the command line, never `export`ed into the operator shell; review round-3 finding 4). The admin DB role is **source-pinned** to `postgres` (no CLI override; finding 3). Authorized read-only prod access only.
- P6 / P7 remain fail-closed **live confirmations** at run time: `sslmode=verify-full` cert chain for the direct host (P6); Supavisor transaction-mode `BEGIN…COMMIT` behavior on the pooler (P7).

---

## Part A — Database evidence (script-captured)

Run from the **merged-main worktree** (it holds `infra/infisical/.env.agent`). The DSN is
injected into the **child process only** via `infra/infisical/inject.sh prod` — never
`export`ed into the operator shell (matches `CENSUS_RUNBOOK.md`; review round-3 finding 4).

```bash
set +x                                             # do not echo the injected child env
git fetch --quiet origin main                      # refresh the remote ref first
MAIN_SHA="$(git rev-parse origin/main)"            # pin to the MERGED tip, not local HEAD
# fail closed unless we ARE that commit, on main, and pristine (the script re-checks too)
test "$(git rev-parse --abbrev-ref HEAD)" = "main" || { echo "refusing: not on main"; exit 1; }
test "$(git rev-parse HEAD)" = "$MAIN_SHA"         || { echo "refusing: HEAD != origin/main"; exit 1; }
test -z "$(git status --porcelain)"                || { echo "refusing: dirty/untracked tree"; exit 1; }

# secrets stay in the injected CHILD; nothing is exported into this shell.
# `-I` (isolated) is REQUIRED: it makes Python ignore PYTHONPATH / user-site / the unsafe
# sys.path[0], closing the import-shadow class at the interpreter level; the script refuses
# (interpreter_not_isolated) if invoked without it (review round-3 Codex-c14).
infra/infisical/inject.sh prod -- \
  "<repo>/.venv/bin/python" -I apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py \
    --expect-project-ref fxoyniqnrlkxfligbxmg \
    --dsn-env SUPABASE_PROD_DSN \
    --expect-repo-sha "$MAIN_SHA"
# -> RESULT PASS + CUSTODY /home/olares/custody/pm-ops-p0/<UTC>/  (dir 0700, files 0400, manifest.sha256)
```

The script independently re-enforces the gate: a **pristine** tree (clean + **no
untracked** files), a fresh `git fetch origin main`, and `HEAD == origin/main ==
--expect-repo-sha` by equality; the admin DB role is **source-pinned** to `postgres`. The
DSN is read from `$SUPABASE_PROD_DSN` inside the injected child and bound to the project
ref before any socket opens.

Artifacts written (atomically published; each hashed in `manifest.sha256`):

| Artifact | Design §2 category |
| --- | --- |
| `00_provenance.json` | governance: repo SHA, `origin_main_sha` + HEAD-equality, pristine flag, source-pinned role, tool + query-bundle hashes, versions, timestamps |
| `00_p0a_snapshot.sql` | the exact guarded read-only SQL block (record) |
| `01_markers.txt` | in-band markers (corroborating only) |
| `02_table_acl.txt` | (9) rollback input — exact per-grantee table ACL + RLS |
| `03_effective_privilege.txt` | (3) effective privileges, fixed principal set |
| `04_role_membership_closure.txt` | (3) anon/authenticated membership closure |
| `05_counts.txt` | (5) counts only |
| `06_default_acl.txt` | (6) `pg_default_acl` tables + functions, per grantor / (9) rollback input |
| `07_secdef_discovery.txt` | (4) SECURITY DEFINER discovery (fail-closed) |
| `08_secdef_function_acl.txt` | (4)/(9) **exact** function ACL (raw `proacl` + `aclexplode`) — the P0-C RPC-grant rollback source (review finding 1) |

## Part B — Non-database evidence (operator / HTTP-captured)

These four categories are **not** produced by the script and must be captured separately and added to the closeout index:

| # | Category | How to capture |
| --- | --- | --- |
| (1) | Deployed OpenAPI, both hosts, + version/SHA | `curl -s https://<mutation-seam-host>/openapi.json` and the control-plane host; record the deployed version/commit SHA. Hash each. |
| (2) | `/reset` route + security state | From the captured OpenAPI: record the `POST /reset` entry + its `security` (expected: none) as its own artifact. |
| (7) | Active backend classification | Record the inferred backend (Render service + `SEAM_STORE_BACKEND`) and the **source** of the inference (config/deploy), not a live mutation. |
| (8) | Render `POST /reset` access logs | Operator-exported from Render; hash the export. |

---

## Part C — Closeout evidence index (fill in, then hash this file too)

P0-A is complete only when every row has an artifact + SHA-256 and the drift call is recorded.

| # | Category | Artifact / source | SHA-256 | Captured by | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Deployed OpenAPI + version/SHA (both hosts) | | | operator/HTTP | ☐ |
| 2 | `/reset` route + security state | | | operator/HTTP | ☐ |
| 3 | Effective privileges + membership closure + RLS | `03_…`, `04_…` | (manifest) | script | ☐ |
| 4 | SECURITY DEFINER discovery + **exact function ACL** | `07_…`, `08_…` | (manifest) | script | ☐ |
| 5 | Counts | `05_counts.txt` | (manifest) | script | ☐ |
| 6 | `pg_default_acl` (tables + functions) per grantor | `06_default_acl.txt` | (manifest) | script | ☐ |
| 7 | Active backend classification (+ source) | | | operator | ☐ |
| 8 | Render `POST /reset` access logs | | | operator | ☐ |
| 9 | Rollback inputs (per-grantee ACL + per-grantor default ACL + RPC grants) | `02_…`, `06_…`, `08_…` | (manifest) | script | ☐ |
| — | Provenance (repo SHA, `origin_main_sha` + HEAD-equality, pristine flag, tool + query hashes) | `00_provenance.json` | (manifest) | script | ☐ |

**Finalize (fail-closed).** After Parts A + B, place the operator/HTTP artifacts (categories
1, 2, 7, 8) into the **same** custody dir, write a closeout spec mapping each of the nine
categories to its artifact filenames, then run the finalizer. It refuses on any missing or
duplicated category, path traversal, non-regular artifact, unhashed or hash-mismatched
script artifact, or failed-HTTP capture, and publishes a **no-clobber** `closeout_index.json`
binding every artifact by SHA-256 (review round-3 finding 5):

```bash
"<repo>/.venv/bin/python" -I apps/mutation-seam/scripts/pm_ops_p0/finalize_closeout.py \
  --spec <closeout-spec.json> \
  --custody-dir /home/olares/custody/pm-ops-p0/<UTC>
# -> RESULT PASS + CLOSEOUT .../closeout_index.json   (mode 0400; every artifact SHA-256-bound)
# (-I required, like preserve_evidence: the finalizer refuses interpreter_not_isolated otherwise)
```

The spec is JSON: `{"categories": [{"category": 1..9, "source": "script"|"operator",
"artifacts": ["<name under the custody dir>", ...]}, ...]}`. Script categories (3, 4, 5, 6,
9) reference the manifest-hashed artifacts above; operator categories (1, 2, 7, 8) reference
the Part-B captures. A `RESULT PASS` closeout index — not this checklist alone — is what
completes the P0-A database + evidence binding.

**Drift.** Compare against the baseline in design §2 (4 tables `rls_enabled=false`/`policies=0`; `anon`+`authenticated` writes; default ACLs from grantors `postgres`+`supabase_admin`; query (e) flags exactly the 3 apparatus RPCs `in_scope_failclosed=true` via `name_refs_targets`, `has_dynamic_sql=false`). **Any** new SECURITY DEFINER function, any `has_dynamic_sql=true` in-scope row, or unexpected default-ACL grantor is a NEW finding requiring re-review **before P0-C**.

**Stop condition.** Stop with the completed index, all hashes, and the drift call. Do **not** proceed to P0-B/C/D/E without their own separate operator GOs.
