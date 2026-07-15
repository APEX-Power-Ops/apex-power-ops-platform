# Overlay evidence collection runbook (disposition ledger)

> **DO NOT RUN until the operator gives an explicit per-dimension collection GO (roadmap Phase 9).**
> Prepared procedure only. Each of the six dimensions gets its OWN source-specific GO, so one
> source failure cannot contaminate the others. Every overlay binds to the CURRENT fresh signed
> census (Phase 6/7); never author against a stale census.

## 0. Preconditions

1. Clean merged-main checkout; record `GATE_SHA=$(git rev-parse origin/main)` after
   `git fetch origin main`, and confirm `git rev-parse HEAD` equals it with a clean
   `git status --porcelain`. The author refuses otherwise (AO010).
2. The fresh signed census + sidecar (committed under `evidence/`), its merged `repo_sha`
   (`CENSUS_SHA`), and the reviewed query-bundle hash
   (`QB=$(cd infra/database/schema-placement && uv run --project . --locked python -c "import collect_disposition as c; print(c.query_bundle_sha256())")`).
3. `DISPOSITION_SIGNING_KEY` in Infisical (operator custody — the key never enters the repo,
   argv, logs, or this runbook). Injection via `infra/infisical/inject.sh prod`.
4. An out-of-repo output dir: `OUT="$HOME/overlay-evidence/$(date -u +%Y%m%dT%H%M%SZ)"`.

## 1. Value-silence discipline (MANDATORY)

- Signing key from env ONLY; `set +x`; never echo it.
- **Raw source evidence is secret-bearing** (runtime logs and advisor output may embed DSN
  fragments): never `cat` it into a transcript. The committed source record for logs is a
  NORMALIZED, REDACTED extract; raw un-redacted material stays in separate custody (Vault),
  referenced from the record.
- Secret-scan and redact any transcript before committing evidence.

## 2. The six dimensions

| Dimension (`source_type`) | Authoritative source | assignment `value` shape | `producing_repo_sha` | source record → `source_hash` |
|---|---|---|---|---|
| `in_data_api_exposed_schema` (`platform_config`) | Data-API **exposed-schemas platform config** (declared config, NOT the runtime `pgrst.db_schemas` GUC) | `{"state":"observed","value":<bool>}` | REQUIRED = author HEAD (`GATE_SHA`) | committed config export |
| `advisor_findings` (`advisor_api`) | Supabase **advisor API** (security + performance) | `{"state":"observed","value":["<finding>",...]}` | FORBIDDEN → null + reason | committed advisor JSON |
| `consumer_evidence.static_repo` (`repository_scan`) | **Static scan** of platform repos for references to each object | consumer_evidence_dim: observed → `{"state":"observed","found_consumers":<int>,"ref":"<scan ref>"}` | REQUIRED = author HEAD | scan output **+ an enumeration of EVERY scanned {repo_root, commit_sha}** (one `producing_repo_sha` never stands in for multiple external repos) |
| `consumer_evidence.runtime_logs` (`runtime_logs`) | Production **query/pg logs** over the window | consumer_evidence_dim | FORBIDDEN → null + reason | **redacted** log extract + raw-custody note |
| `consumer_evidence.external_clients` (`external_client_inventory`) | External API-client / integration inventory | consumer_evidence_dim | CONDITIONAL (author HEAD if repo-committed inventory; else null + reason) | committed inventory |
| `consumer_evidence.operator_declaration` (`operator_declaration`) | Signed **operator attestation** (core carries `operator_identity` + `attestation_ref`) | consumer_evidence_dim | FORBIDDEN → null + reason | committed attestation, or null + reason with `--source-custody-locator` |

Non-observed consumer states use `{"state":"...","found_consumers":null,"ref":null,"detail":"..."}`.

## 3. Window + freshness discipline (make preapply SATISFIABLE)

> **WARNING — a valid derived consumer window does NOT imply resolved consumer evidence.** The window is
> derived only across the OBSERVED consumer overlays; a resolved `consumer_disposition` additionally
> requires EVERY consumer dimension itself to be OBSERVED (#102 `runtime_logs`; #103 `static_repo` and
> `external_clients`). Unavailable telemetry, an unscanned repo, OR API-non-exposure must be recorded
> `not_observed`, **never** `not_applicable` — an N/A on any of these dims for a resolved conclusion is
> rejected by the semantic checker (`SP022`) and, on non-delete rows, early-flagged by the signed-overlay
> loader (`OV015`); no receipt is written. The SINGLE surviving N/A: `external_clients=not_applicable` on
> an ACCEPTED delete, governed by the SP027 floor's ratified exposure-false waiver. (delete additionally
> floors on `SP027`.)

- Per overlay (enforced at author time): `started_at < ended_at <= captured_at` and `ended_at <=
  now` (OV009); `captured_at` is set by the tool clock (its future-half is OV010).
- At the cluster gate the consumer window derives as `S = max(started_at)`, `E = min(ended_at)`
  across the OBSERVED consumer overlays per relation. It must be non-empty (OV011), bracket the
  census instant `S <= observed_at <= E` (OV017), and — for a delete whose `external_clients` is
  `not_applicable` — the observed-FALSE `in_data_api_exposed_schema` window must COVER `[S, E]`
  (OV022). So: choose consumer windows that OVERLAP and BRACKET `observed_at`, and give the
  `in_data_api` overlay a window at least as wide as the intersection.
- **OV016 freshness is measured at PREAPPLY time against `E = min(ended_at)` — the
  earliest-ending consumer window, not `captured_at`.** Collect all consumer evidence for a
  cluster close together, and run `check_disposition --mode preapply` within
  `--max-consumer-evidence-age-hours` (planned value: 720) of the earliest `ended_at`.

## 4. Author one overlay (per-dimension GO)

Write the semantics core (`core.json`): `dimension`, `assignments`, `observation_window`,
`authority`, `collection_method` (+ `operator_identity`/`attestation_ref` for the declaration
dimension). Then:

    infra/infisical/inject.sh prod -- \
      uv run --project infra/database/schema-placement --locked \
        python infra/database/schema-placement/author_overlay.py \
          --census <committed census path> --census-sig <committed census .sig> \
          --key-id prod-disposition-ed25519-2026-07 \
          --input core.json \
          --source-file <raw-or-redacted evidence file> \
          --expect-gate-repo-sha "$GATE_SHA" \
          --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres \
          --expect-schemas public --expect-census-repo-sha "$CENSUS_SHA" \
          --require-role-markers anon,authenticated,service_role \
          --expect-query-bundle-sha256 "$QB" \
          --out-dir "$OUT"

For a no-artifact dimension replace `--source-file` with
`--source-hash-na-reason "<why>" --source-custody-locator "<vault ref>"`. The custody locator
must use an approved scheme — `vault:` or `infisical:` (`APPROVED_CUSTODY_SCHEMES`, pinned
identically in `author_overlay.py` and `ci/overlay_ci_checks.py`); adding a scheme requires a
governed tooling change (a reviewed source change to `APPROVED_CUSTODY_SCHEMES`).
For FORBIDDEN/`external_clients`-null dimensions add `--producing-repo-sha-na-reason "<why>"`.
The tool validates BEFORE signing (AO005 prints the exact OV codes), enforces signer parity
(AO007), verifies the sidecar in memory (AO012), and publishes
`$OUT/{overlay,overlay.sig,source/record}` no-clobber with canonical names.

## 5. Verify + commit (evidence PR, Phase 10 GO)

Verify locally: `verify_overlay_artifact.py --overlay ... --overlay-sig ... --census ...
--census-sig ... --key-id prod-disposition-ed25519-2026-07 --expect-project-ref
fxoyniqnrlkxfligbxmg --expect-database postgres --expect-schemas public
--expect-census-repo-sha "$CENSUS_SHA" --expect-query-bundle-sha256 "$QB"` → GREEN. Copy the
triple into `infra/database/schema-placement/evidence/` PRESERVING NAMES (the overlay's
`source_locator` is the schema-placement-relative destination `evidence/source/<name>`), commit
via a governed evidence PR, and let the `overlay-evidence` CI independently re-verify every
artifact (immutability, orphan guard, census binding, source rehash, committed-set OV007).
