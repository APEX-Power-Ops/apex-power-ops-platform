# Read-only census runbook (schema-placement disposition ledger)

> **DO NOT RUN until the operator gives an explicit read-only census GO.** This is a prepared
> procedure only. The census produces AUTHORITATIVE production evidence, so it runs from a **merged
> `main` checkout**, never from an unpushed branch.

Prod project: `fxoyniqnrlkxfligbxmg` (Supabase, managed non-super `postgres`, PG16). The census is a
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
   The trust anchor is the `TRUSTED_SIGNERS` constant in `verify_census.py` (reviewed verifier source),
   which pins this signer id to SPKI SHA-256
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
MAIN_SHA=$(git -C . rev-parse HEAD)          # MUST be the merged-main commit; worktree MUST be clean
TS=$(date -u +%Y%m%dT%H%M%SZ)                # unique UTC stamp
OUT="$HOME/census-evidence/prod-$TS.json"; mkdir -p "$HOME/census-evidence"
```

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
`QUERY_BUNDLE` changes (re-derive with `python -c "import collect_disposition as c; print(c.query_bundle_sha256())"`).

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

**After the census:** build the signed-overlay packet (the `not_observed` overlays become
separately-signed docs bound to the base snapshot SHA-256 — the census stays immutable), then the
apply runner (revalidate-everything: read-once, verify snapshot+overlay sigs vs the pinned key, re-run
schema/semantic/target/SP014, verify receipt hashes, bind+hash the exact migration SQL, restore-test
the backup in disposable PostgreSQL, recheck identity+drift immediately before the SQL). The apply gate
remains HELD until then.
