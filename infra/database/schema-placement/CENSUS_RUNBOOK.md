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
3. Add **only** the **public** key + a fingerprint/rotation id to the branch. Committed for this cycle
   (through your own governed keypair commit, NOT the tooling commit):
   - public key: `infra/database/schema-placement/keys/prod-disposition-ed25519-2026-07.pub.pem`
   - fingerprint (rotation id): `infra/database/schema-placement/keys/prod-disposition-ed25519-2026-07.spki-sha256`
     = the SPKI SHA-256 `c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca`
     (verified to match the committed public key).
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

## 2. Inject secrets (value-silent) + set the timestamp

```sh
set +x
# from Infisical (adapt to your CLI); values never printed:
export DISPOSITION_DSN="$(infisical secrets get SUPABASE_PROD_DSN --plain)"
export DISPOSITION_SIGNING_KEY="$(infisical secrets get DISPOSITION_SIGNING_KEY --plain)"
TS=$(date -u +%Y%m%dT%H%M%SZ)          # unique UTC stamp (no overwrite)
OUT=infra/database/schema-placement/evidence/prod-$TS.json
```

## 3. Run the read-only census  →  unique `prod-<UTC>.json` + `.sig`

```sh
uv run --project infra/database/schema-placement --locked \
  python infra/database/schema-placement/collect_disposition.py \
    --dsn-env DISPOSITION_DSN \
    --signing-key-env DISPOSITION_SIGNING_KEY \
    --project-ref fxoyniqnrlkxfligbxmg \
    --expect-database postgres \
    --require-role-markers anon,authenticated,service_role \
    --schemas public \
    --out "$OUT"
```

The collector: binds the DSN to the project ref (refuses an unbound DSN / any `hostaddr`); opens a
read-only session; asserts current_database / read-only / role markers **in-band** (raises before any
snapshot); records `observed_at` from the DB clock and `repo_sha` from `git HEAD` (= `MAIN_SHA`); bakes
`collection_scope` (schemas / db / role markers / repo_sha / query-bundle hash) into the document; then
**signs the exact snapshot bytes** and publishes `$OUT` + `$OUT.sig` no-clobber (unique path). It never
overwrites.

## 4. Census acceptance  (offline; the gate that makes the census authoritative)

```sh
uv run --project infra/database/schema-placement --locked \
  python infra/database/schema-placement/verify_census.py \
    --snapshot "$OUT" \
    --snapshot-sig "$OUT.sig" \
    --verify-key infra/database/schema-placement/keys/prod-disposition-ed25519-2026-07.pub.pem \
    --expect-project-ref fxoyniqnrlkxfligbxmg \
    --expect-database postgres \
    --expect-schemas public \
    --expect-repo-sha "$MAIN_SHA" \
    --require-role-markers anon,authenticated,service_role
```

Exit 0 = `=== CENSUS ACCEPTANCE: GREEN ===`. It verifies the detached signature against the pinned
public key **before parsing**; asserts project ref / database / schema scope / query-bundle hash /
merged repo SHA / role markers; validates structure + relation-count + object-id integrity; rejects any
`query_failed` catalog group; confirms every relation is within the requested scope; and permits the
expected zero-width windows + `not_observed` overlays. It requires **no** decisions / entity-map /
manifest (a raw census legitimately has none — it must NOT be run through `check_disposition --mode
preapply`).

## 5. Commit the evidence (governed PR)

Commit `prod-$TS.json`, `prod-$TS.json.sig`, and a **redacted** transcript through an evidence PR.
`unset DISPOSITION_DSN DISPOSITION_SIGNING_KEY` when done.

---

**After the census:** build the signed-overlay packet (the `not_observed` overlays become
separately-signed docs bound to the base snapshot SHA-256 — the census stays immutable), then the
apply runner (revalidate-everything: read-once, verify snapshot+overlay sigs vs the pinned key, re-run
schema/semantic/target/SP014, verify receipt hashes, bind+hash the exact migration SQL, restore-test
the backup in disposable PostgreSQL, recheck identity+drift immediately before the SQL). The apply gate
remains HELD until then.
