# Read-only census runbook (schema-placement disposition ledger)

> **DO NOT RUN until the operator gives an explicit read-only census GO.** This is a prepared
> procedure only. The census produces AUTHORITATIVE production evidence, so it runs from a **merged
> `main` checkout**, never from an unpushed branch.

Prod project: `fxoyniqnrlkxfligbxmg` (Supabase, managed non-super `postgres`, PG17.6 — per the committed census `target_identity.server_version`, `server_version_num` 170006). The census is a
**read-only** catalog SELECT sweep — no writes. It emits an immutable, Ed25519-signed
`evidence_snapshot`; a separate acceptance gate then proves it is genuine and in-scope.

## 0. Preconditions (operator, out of band)

1. Generate an Ed25519 keypair **outside the repo**, restrictive perms:
   `openssl genpkey -algorithm ed25519 -out census.key && chmod 600 census.key`
   `openssl pkey -in census.key -pubout -out census.pub`
2. Store the **private** key in Infisical as `DISPOSITION_SIGNING_KEY` (PKCS8 PEM). It never enters the
   repo, argv, logs, or this runbook.
3. Add **only** the **public** key to the branch (through your own governed keypair commit, NOT the
   tooling commit): `infra/database/schema-placement/keys/prod-disposition-ed25519-2026-07.pub.pem`.
   The trust anchor is the `TRUSTED_SIGNERS` source constant in `disposition_trust.py` (the SHARED
   reviewed anchor — `verify_census` AND `check_disposition` both resolve signers through
   `disposition_trust.resolve_pinned_key`), which pins this signer id to SPKI SHA-256
   `c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca`. The committed public key MUST
   have exactly that SPKI fingerprint or `verify_census` fails closed (CN013). (An optional
   `.spki-sha256` sidecar may accompany the key for humans, but it is NOT the anchor — the verifier
   ignores it and reads the fingerprint from source.)
4. Open the governed PR (collector + verify_census + the public key), pass CI, **merge to `main`**.
5. Refresh a **clean `main`** checkout and record its commit: `MAIN_SHA=$(git rev-parse HEAD)`. The
   census must run from this checkout so the snapshot's `repo_sha` == `MAIN_SHA`.
6. The prod DSN is in Infisical as `SUPABASE_PROD_DSN`. It must carry the project ref in host/user
   (`db.fxoyniqnrlkxfligbxmg.supabase.co` or pooler `postgres.fxoyniqnrlkxfligbxmg`) and **no**
   `hostaddr`.

## 1. Value-silence discipline (MANDATORY)

- The DSN and signing key are read from **env vars only** — never argv, never echoed, never logged.
- `set +x` in the shell; do not `echo "$DISPOSITION_DSN"` / `"$DISPOSITION_SIGNING_KEY"`.
- The collector prints only host/user/db identity and the bundle-hash prefix — never secret values;
  driver errors surface the exception **type** only.
- Redact any transcript before committing it (no DSN, no key, no `env` dumps).

## 2. Set the provenance + a unique OUT path OUTSIDE the repo

```sh
set +x
git fetch --quiet origin main                          # refresh the remote ref first
MAIN_SHA=$(git rev-parse origin/main)                  # expected SHA = the MERGED main tip, NOT the local checkout
# Fail closed unless we are ON main, our HEAD *is* origin/main, and the worktree is clean — so a clean but
# UNMERGED (or stale) feature branch cannot be censused (self-attestation gap, operator finding).
test "$(git rev-parse --abbrev-ref HEAD)" = "main" || { echo "refusing: not on the main branch"; exit 1; }
test "$(git rev-parse HEAD)" = "$MAIN_SHA"         || { echo "refusing: local HEAD != origin/main (unmerged or stale)"; exit 1; }
test -z "$(git status --porcelain)"                || { echo "refusing: dirty worktree"; exit 1; }
TS=$(date -u +%Y%m%dT%H%M%SZ)                          # unique UTC stamp
OUT="$HOME/census-evidence/prod-$TS.json"; mkdir -p "$HOME/census-evidence"
```

`MAIN_SHA` is the **merged** main tip (`origin/main`), and the census is refused unless the local checkout
is exactly that commit on `main` and clean — the collector's `--expect-repo-sha` and the verifier's
`--require-clean-checkout` then bind to a genuinely merged SHA, not a self-attested branch head.

Write the census OUTSIDE the repo: the collector refuses to census a DIRTY worktree, and provenance is
only meaningful against a clean tree — so the evidence is produced out-of-tree and committed later via an
evidence PR (step 5). Do NOT `export` any secret into this shell.

## 3. Run the read-only census under the injection wrapper  →  `prod-<UTC>.json` + `.sig`

Secrets stay in the CHILD process only. `infra/infisical/inject.sh prod` injects apex-platform/prod
secrets (`SUPABASE_PROD_DSN`, `DISPOSITION_SIGNING_KEY`) into the census command; nothing lands in the
operator shell. Run from the merged-main worktree (it holds `infra/infisical/.env.agent`).

```sh
infra/infisical/inject.sh prod -- \
  uv run --project infra/database/schema-placement --locked \
    python infra/database/schema-placement/collect_disposition.py \
      --dsn-env SUPABASE_PROD_DSN \
      --signing-key-env DISPOSITION_SIGNING_KEY \
      --project-ref fxoyniqnrlkxfligbxmg \
      --expect-database postgres \
      --expect-repo-sha "$MAIN_SHA" \
      --require-role-markers anon,authenticated,service_role \
      --schemas public \
      --out "$OUT"
```

The collector: refuses a DIRTY worktree and asserts `git HEAD == $MAIN_SHA` BEFORE connecting; binds the
DSN to the project ref (refuses an unbound DSN / any `hostaddr`); opens a read-only session; asserts
current_database / read-only / role markers **in-band** (raises before any snapshot); records
`observed_at` from the DB clock and `repo_sha` from HEAD; runs an INDEPENDENT catalog count; bakes
`collection_scope` (schemas / db / role markers / repo_sha / query-bundle hash) into the document; then
**signs the exact snapshot bytes** and publishes `$OUT` + `$OUT.sig` no-clobber. It never overwrites.

## 4. Census acceptance  (offline; the gate that makes the census authoritative)

```sh
uv run --project infra/database/schema-placement --locked \
  python infra/database/schema-placement/verify_census.py \
    --snapshot "$OUT" \
    --snapshot-sig "$OUT.sig" \
    --key-id prod-disposition-ed25519-2026-07 \
    --expect-project-ref fxoyniqnrlkxfligbxmg \
    --expect-database postgres \
    --expect-schemas public \
    --expect-repo-sha "$MAIN_SHA" \
    --require-role-markers anon,authenticated,service_role \
    --expect-query-bundle-sha256 217ff3add2abdaca2fafa108f68e10490ee687ac9899b7762f1411d45e2de9db \
    --require-clean-checkout
```

`--require-clean-checkout` is a preflight: it asserts the verifier's own git checkout is clean AND at
`$MAIN_SHA` before it trusts `TRUSTED_SIGNERS` + `keys/` — binding the acceptance gate to reviewed source
(a dirty or wrong-commit checkout fails CN017, no bypass). Run this step from the same clean merged-main
worktree as the census.

`--expect-query-bundle-sha256` is now REQUIRED (D4/RR-2): it binds CN006 to a **reviewed** hash
rather than silently trusting the verifier's own checkout. The value MUST equal
`collect_disposition.query_bundle_sha256()` at the census commit; update it in lockstep whenever the
`QUERY_BUNDLE` changes. Re-derive it from the package directory (the bare `python -c` fails from repo root):
`(cd infra/database/schema-placement && uv run --project . --locked python -c "import collect_disposition as c; print(c.query_bundle_sha256())")`.

Exit 0 = `=== CENSUS ACCEPTANCE: GREEN ===`. `--key-id` must name a signer pinned in the
`TRUSTED_SIGNERS` source constant; `keys/<key-id>.pub.pem` (`--keys-dir` defaults to `keys/`) is loaded
as public key MATERIAL and accepted only if its SPKI SHA-256 equals the pinned value — the trust anchor
is REVIEWED VERIFIER SOURCE, not a caller-supplied path or keys-dir (`--key-id` is sanitized and the
resolved key path is contained within `--keys-dir`). It then verifies
the detached signature **before parsing**; asserts project ref / database (incl. `target_identity`
expected_database) / schema scope / query-bundle hash / merged repo SHA / role markers; validates
structure + internal consistency + relation-count (emitted list == relation_count == INDEPENDENT catalog
count) + object-id integrity; rejects an EMPTY census, DUPLICATE object_ids, and any `query_failed`
catalog group; confirms every relation is within the requested scope; and permits the expected zero-width
windows + `not_observed` overlays. It requires **no** decisions / entity-map / manifest (a raw census
legitimately has none — it must NOT be run through `check_disposition --mode preapply`).

## 5. Commit the evidence (governed PR)

Copy `$OUT` + `$OUT.sig` from `$HOME/census-evidence/` into
`infra/database/schema-placement/evidence/`, add a **redacted** transcript, and commit through a governed
evidence PR (this is the first time the worktree gains untracked evidence — the census run itself kept it
clean). No secret ever entered the operator shell, so there is nothing to `unset`.

---

**After the census (current sequence — each step operator-gated):** the signed-overlay CONSUMER
(`disposition_overlay.py`, OV001–OV022) and the overlay PUBLICATION tooling (`author_overlay.py`,
`verify_overlay_artifact.py`, the `overlay-evidence` CI gate, `OVERLAY_COLLECTION_RUNBOOK.md`) are
merged. Next: **fresh census → definer-view reconciliation → collect and sign the six per-dimension
overlays, each bound to the fresh census byte hash and publishing either (a) a committed source
record whose bytes match its non-null `source_hash`, or (b), only where the contract permits
`source_hash:null`, a non-empty NA reason and approved out-of-band custody locator → formal cluster
gate (`check_disposition --mode preapply` over census + all overlays) → apply runner**
(revalidate-everything: read-once, verify snapshot+overlay sigs vs the pinned key, re-run
schema/semantic/target gates, bind+hash the exact migration SQL, restore-test the backup in
disposable PostgreSQL, recheck identity+drift immediately before SQL). The apply gate remains HELD.

**Evidence immutability:** the `overlay-evidence` CI job also rejects any MODIFY/DELETE/RENAME/
TYPECHANGE of committed `census-prod-*.json`, `overlay-*.json`, `evidence/source/**`, or `*.sig`
artifacts (`git diff --no-renames --name-status`, all-`A` required) — closing the census gate's
added-only blind spot. Committed evidence is immutable; supersede with a fresh artifact, never an
edit.
