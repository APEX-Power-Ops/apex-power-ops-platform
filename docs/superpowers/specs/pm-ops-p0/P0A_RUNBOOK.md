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
- **Run from a clean, dedicated worktree checked out at the pinned SHA — NOT the primary checkout.** The primary worktree may carry unrelated uncommitted work (e.g. the `apex-jobs` modifications); the script refuses a non-pristine tree, and you must **never** `git stash`/`autostash`/`checkout`/discard that work to satisfy the gate. `git worktree add <path> <EXPECT_SHA>` gives a clean tree without touching it.
- **A literal, independently-sourced server SHA.** The GO carries the authoritative `main` SHA as a literal, obtained from an independent source (the GitHub API / another machine) — **not** re-derived from the same local remote the script later corroborates (a rewritten `remote.origin.url` would otherwise self-confirm; RI2 finding 5). The script enforces a **pristine** tree (clean + **no untracked** files) and `HEAD == origin/main == --expect-repo-sha` by **equality** after a fresh `git fetch origin refs/heads/main` (findings 1–2). **If `main` has advanced past the literal SHA, STOP** — re-review and obtain a new GO with the new literal SHA; do **not** silently adopt the new tip.
- **The interpreter contract is `python -I -S`.** `-I` alone does **not** imply `-S`: `site` would still run and execute an editable-install `.pth` during startup — before the script's guards, with the injected DSN present (RI2 finding 1). Both CLIs refuse (`interpreter_not_isolated_no_site`) unless invoked with **`-I -S`**.
- **A hash-pinned dependency bundle.** Because `-S` takes site-packages off `sys.path`, psycopg is loaded **only** from an operator-supplied, immutable, SHA-256-pinned dependency bundle — never the repo-local `.venv` — via `--dependency-bundle`/`--bundle-manifest`/`--expect-bundle-manifest-sha256` (the manifest's own hash attested out-of-band, like the repo SHA). See **Part A0**.
- The DSN is injected into the **child process only** via `infra/infisical/inject.sh prod` and read from an **environment variable name** (never a value on the command line, never `export`ed into the operator shell; review round-3 finding 4). The admin DB role is **source-pinned** to `postgres` (no CLI override; finding 3). Authorized read-only prod access only.
- **P6 and P7 are two SEPARATELY-GOVERNED read-only probes (RI2 finding 3).** P6 (`sslmode=verify-full` + `sslrootcert=system` cert chain) requires a **direct** `db.<ref>.supabase.co` connection; P7 (Supavisor transaction-mode `BEGIN…COMMIT`) requires the **transaction-pooler on port 6543**. The tracked session-pooler (`:5432`) `SUPABASE_PROD_DSN` proves **neither**: each probe needs its own child-only DSN input under its own GO, and any new DSN provisioning is its own authorization. Do **not** claim P6 and P7 from the single session-pooler DSN.

---

## Part A0 — Build the hash-pinned dependency bundle (one-time, per GO)

Under `-S`, psycopg is loaded only from a verified bundle (never the repo `.venv`). Build an
**immutable** bundle of psycopg + its deps and pin every file, from the clean worktree at the
pinned SHA. The manifest's own SHA-256 becomes an **out-of-band attestation** carried in the
GO (like the repo SHA), so a swapped bundle is rejected.

```bash
set +x
BUNDLE=/home/olares/custody/pm-ops-p0-deps/<UTC>        # a NEW immutable dir, outside the repo
# populate BUNDLE with psycopg + deps only (e.g. `pip install --no-compile --target "$BUNDLE" psycopg[binary]==3.3.4`
# in a throwaway env, then remove any __pycache__), then freeze it read-only:
find "$BUNDLE" -type d -exec chmod 0555 {} +; find "$BUNDLE" -type f -exec chmod 0444 {} +
# pin every file (sorted, stable) into a manifest and record ITS hash as the attestation:
( cd "$BUNDLE" && find . -type f | LC_ALL=C sort | sed 's#^\./##' \
    | while read -r f; do printf '%s  %s\n' "$(sha256sum "$f" | cut -d" " -f1)" "$f"; done ) > /tmp/bundle.sha256
BUNDLE_MANIFEST_SHA="$(sha256sum /tmp/bundle.sha256 | cut -d' ' -f1)"   # -> attest this in the GO record
```

The bootstrap refuses (value-free) any bundle whose manifest hash, any member hash, or member
shape (unlisted file, symlink, traversal, non-regular, missing) does not match — before any
bundle file is importable.

## Part A — Database evidence (script-captured)

Run from a **clean, dedicated worktree at the pinned SHA** (see Preconditions — never the
possibly-dirty primary checkout, and never stash its work). The DSN is injected into the
**child process only** via `infra/infisical/inject.sh prod` — never `export`ed into the
operator shell (matches `CENSUS_RUNBOOK.md`; review round-3 finding 4).

```bash
set +x                                             # do not echo the injected child env
EXPECT_SHA="<literal main SHA from the GO — independently sourced, NOT derived here>"
git fetch --quiet origin refs/heads/main           # refresh the branch ref (not a tag named main)
# fail closed unless HEAD IS that literal commit, origin/main IS that literal commit, and the
# tree is pristine (the script re-checks too). NOTE: a `git worktree add <path> <EXPECT_SHA>`
# checkout is DETACHED, so we gate on SHA equality (what the script enforces), NOT branch name.
# If origin/main has ADVANCED past EXPECT_SHA, STOP and get a new GO — do not adopt the new tip.
test "$(git rev-parse HEAD)" = "$EXPECT_SHA"         || { echo "refusing: HEAD != pinned SHA"; exit 1; }
test "$(git rev-parse origin/main)" = "$EXPECT_SHA"  || { echo "refusing: origin/main advanced past the pinned SHA — STOP, re-review"; exit 1; }
test -z "$(git status --porcelain)"                  || { echo "refusing: dirty/untracked tree"; exit 1; }

# secrets stay in the injected CHILD; nothing is exported into this shell.
# `-I -S` is REQUIRED: -I ignores PYTHONPATH/user-site/unsafe sys.path[0]; -S disables `site`
# so no editable-install `.pth` executes before the guards (RI2 finding 1). psycopg is loaded
# from the verified bundle (Part A0). The script refuses (interpreter_not_isolated_no_site)
# without both flags, and refuses any un-pinned bundle.
infra/infisical/inject.sh prod -- \
  "$BUNDLE/../python-runtime/bin/python" -I -S apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py \
    --expect-project-ref fxoyniqnrlkxfligbxmg \
    --dsn-env SUPABASE_PROD_DSN \
    --expect-repo-sha "$EXPECT_SHA" \
    --dependency-bundle "$BUNDLE" \
    --bundle-manifest /tmp/bundle.sha256 \
    --expect-bundle-manifest-sha256 "$BUNDLE_MANIFEST_SHA"
# -> RESULT PASS + CUSTODY /home/olares/custody/pm-ops-p0/<UTC>/  (dir 0700, files 0400, manifest.sha256)
```

> The `python` above must be a `-S`-usable interpreter whose stdlib resolves without site
> (any standard CPython); psycopg comes from `--dependency-bundle`, not from that
> interpreter's site-packages.

The script independently re-enforces the gate: a **pristine** tree (clean + **no
untracked** files), a fresh `git fetch origin refs/heads/main`, and `HEAD == origin/main ==
--expect-repo-sha` by equality; the admin DB role is **source-pinned** to `postgres`; and the
dependency bundle is hash-verified before psycopg is imported. The DSN is read from
`$SUPABASE_PROD_DSN` inside the injected child and bound to the project ref before any socket
opens.

Artifacts written (atomically published; each hashed in `manifest.sha256`):

| Artifact | Design §2 category |
| --- | --- |
| `00_provenance.json` | governance: repo SHA, `origin_main_sha` + HEAD-equality, pristine flag, source-pinned role, `dependency_bundle_manifest_sha256`, tool + query-bundle hashes, versions, timestamps |
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

These four categories are **not** produced by the script and must be captured separately and added to the closeout index.

**HTTP capture rules (RI2 finding 7 — all mandatory).** Every capture command is **HTTPS-only**, **GET-only**, **fail-on-error**, and **timeout-bounded**, against a **named** host with its **expected service identity** and **deployment identifier** recorded. **Never issue `POST /reset` (or any mutation) to create evidence** — the `/reset` route state is read from the *OpenAPI document*, never by calling it. Use, per host:

```bash
# HTTPS + GET + fail-on-error (-f) + explicit connect/total timeouts; named host only.
curl -fsS --proto '=https' --tlsv1.2 --connect-timeout 5 --max-time 20 -X GET \
  "https://<named-host>/openapi.json" -o "01_openapi_<host-label>.json"
# record alongside each capture: the resolved host, the deployed version/commit SHA (from the
# app's version endpoint or the Render/Vercel deploy record), and the capture UTC timestamp.
```

| # | Category | How to capture (HTTPS/GET/fail-fast/timeout-bounded; never POST /reset) |
| --- | --- | --- |
| (1) | Deployed OpenAPI, both hosts, + version/SHA | GET `https://<mutation-seam-host>/openapi.json` and the control-plane host with the curl form above; record each resolved host, deployed version/commit SHA, and timestamp. Hash each. |
| (2) | `/reset` route + security state | Read the `POST /reset` entry + its `security` (expected: none) **from the captured OpenAPI document** — do **not** call the route. Record as its own artifact. |
| (7) | Active backend classification | Record the inferred backend (Render service + `SEAM_STORE_BACKEND`) and the **source** of the inference (config/deploy record), not a live mutation. |
| (8) | Render `POST /reset` access logs | Operator-exported from Render for a **defined time window** (record the window start/end UTC + the service/deployment id); hash the export. |

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
# stdlib-only finalizer: any standard CPython works; -I -S required (RI2 finding 1), no bundle needed.
python -I -S apps/mutation-seam/scripts/pm_ops_p0/finalize_closeout.py \
  --spec <closeout-spec.json> \
  --custody-dir /home/olares/custody/pm-ops-p0/<UTC>
# -> RESULT PASS + CLOSEOUT .../closeout_index.json   (mode 0400; every artifact SHA-256-bound)
# (-I -S required, like preserve_evidence: the finalizer refuses interpreter_not_isolated_no_site otherwise)
```

The spec is JSON: `{"categories": [{"category": 1..9, "source": "script"|"operator",
"artifacts": ["<name under the custody dir>", ...]}, ...]}`. Script categories (3, 4, 5, 6,
9) reference the manifest-hashed artifacts above; operator categories (1, 2, 7, 8) reference
the Part-B captures. A `RESULT PASS` closeout index — not this checklist alone — is what
completes the P0-A database + evidence binding.

**Drift.** Compare against the baseline in design §2 (4 tables `rls_enabled=false`/`policies=0`; `anon`+`authenticated` writes; default ACLs from grantors `postgres`+`supabase_admin`; query (e) flags exactly the 3 apparatus RPCs `in_scope_failclosed=true` via `name_refs_targets`, `has_dynamic_sql=false`). **Any** new SECURITY DEFINER function, any `has_dynamic_sql=true` in-scope row, or unexpected default-ACL grantor is a NEW finding requiring re-review **before P0-C**.

**Stop condition.** Stop with the completed index, all hashes, and the drift call. Do **not** proceed to P0-B/C/D/E without their own separate operator GOs.
