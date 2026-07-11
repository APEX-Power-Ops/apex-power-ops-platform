# IRP Audit Record — disposition checker + collector

**Mode:** Audit · **Depth:** Deep · **Subject:** `check_disposition.py` + `collect_disposition.py`
+ `disposition.schema.json`, disposition-ledger lane. **Engines:** 4 Claude grounded probes +
adversarial regression pass (Workflow `irp-grounded-audit`, run `wf_5f47622e-512`) **and** Codex
`gpt-5.5` xhigh (`codex exec review --base main`, isolated detached worktree). This tool gates a
one-shot read-only PROD census + downstream irreversible schema moves, so the review prioritized
fail-closed behavior, value-silence, and false-green resistance.

## Round-1 audit (against `651c9d20`)

**Cross-engine delta:** Codex found the single most severe issue (the destructive-delete
null-vacuity) that all Claude probes missed; the Claude probes found the most systemic issue
(`found_consumers` counts edges not consumers) plus a cluster of enumeration/robustness gaps Codex
didn't reach. Complementary — neither engine alone was sufficient.

Findings, and their resolution in the correction commit that followed:

| # | Sev | Finding (engine) | Resolution |
|---|-----|------------------|-----------|
| 1 | Critical | `retention_disposition: null` (and retain/compat) pass the gate — JSON-Schema `required`/`properties` are vacuous on a null instance (Codex) | `type:object` added to delete/retain/compat then-clauses; +4 contract negatives |
| 2 | High | `found_consumers` counts EVERY edge incl. the relation's own seq/trigger/policy + outbound FKs (Claude ×3) | SQL `is_consumer` flag per edge; `found_consumers` counts consumers only; full inventory kept in `dependent_objects`; +2 collector tests; PG16-proven |
| 3 | High | `database_deps` can be set `not_applicable` to neutralize the machine signal (Claude adversarial) | checker requires `database_deps.state==observed` for a resolved conclusion; +1 negative |
| 4 | High | `target_objects` not bound to `target_schema`; compat lacked `target_schema` (Codex) | schema requires compat `target_schema`; checker SP025 binds every target_object's prefix; SP012 scoped to canonical promotion; +2 negatives |
| 5 | High | delete `recovery_proof` accepts a scheme token (`urn:`/`ta:`/`query:`) that skips file resolution — the delete baseline itself used `query:backup` (Codex) | checker requires a delete's `recovery_proof` to be a filesystem artifact under an approved root; +1 negative |
| 6 | High | project binding `ref in labels` accepts `db.<ref>.attacker.example` / pooler-user on any host (Claude/Codex) | strict anchor to `db.<ref>.supabase.co` OR `*.pooler.supabase.com`+`postgres.<ref>`; psycopg conninfo parser (URL + libpq keyword); +anchoring tests |
| 7 | Med | `FOR ALL TABLES`/schema-level publications + inheritance/partition children uncounted (Claude) | `pubs_all`/`pubs_schema`/`inherits_children` CTEs added; PG16-proven |
| 8 | Med | `write_snapshot` outside `main`'s try/except → uncaught traceback not fail-closed `2`; wrong-kind doc crashes checker (Claude) | write wrapped → exit 2; checker validates each doc's `kind` (SP001); +2 tests |

All resolved under `uv.lock`: contract 49 / checker 43 / collector 28, plus PG16.13 catalog SQL
execution proof (`evidence/pg16-sql-validation-2026-07-11.md`).

## Outstanding — for operator decision (NOT in the ratified tranche)

**F1 (High, design): the checker trusts a self-attested, UNSIGNED snapshot.** `guard_passed`,
`transaction_read_only`, `project_ref`, and the entire `consumer_evidence` block are plain writable
JSON; `query_bundle_sha256` hashes only the SQL text; SP024 only string-compares `project_ref` to a
value the operator also supplies. So a hand-authored snapshot with `guard_passed:true` and fabricated
evidence validates and can carry a delete/archive GREEN. The offline checker fundamentally cannot
verify a snapshot was produced by a genuine read-only census without either (a) the collector SIGNING
the snapshot (HMAC/detached signature the checker verifies), or (b) an explicit pipeline-integrity
guarantee that the checker only ever ingests the collector's own immutable output. This is out of
band from the three files and was surfaced by the Round-1 re-audit; it is a design call, not silently
implemented. **Recommendation:** decide (a) vs (b) before the checker is trusted to authorize a
destructive action; it does not block the read-only census GO itself.

## Round-2 re-audit (against `212fca7b`)

Same engines (Claude workflow `wf_4420a233-e48` + Codex `gpt-5.5` xhigh). Found **9 more** real
defects — several were narrow variations of the null-vacuity class, and one (over-broad compat SP012
exemption) was introduced BY the Round-1 correction. Codex proved the promote gap by executing a test.
All resolved on `212fca7b`'s successor commit:

| Finding (engine) | Resolution |
|------------------|-----------|
| promote + `has_consumers` + `compatibility_contract:null` false-greens (Codex, EXECUTED) | schema requires a real (type:object, required=true) compat for has_consumers promote; +neg |
| promote allows `exposure_policy:null` (Claude adversarial) | promote requires a non-null exposure posture; +neg |
| compat SP012-skip too broad — `target_schema:'evil'` passes (Codex + Claude, my Round-1 regression) | compat `target_schema` must equal `public`; +neg |
| manifest `required_observations: consumer_evidence` silently dropped (Codex) | enforced: every consumer dim observed/N-A when required; +neg |
| non-finite `max_staleness_hours`/`minimum_consumer_window_hours` (NaN/Inf) defeat SP008/SP009 (Codex) | SP015 rejects non-finite gate numbers; JSON loader rejects NaN/Inf; +neg |
| delete `recovery_proof` = empty file passes (Claude) | checker requires a NON-EMPTY resolved artifact; +neg |
| DSN `hostaddr` bypasses the host bind (Claude) | reject any DSN carrying `hostaddr`; +test |
| `FOR ALL TABLES` publications over-count views/matviews/foreign tables (Claude) | `pubs_all`/`pubs_schema` filtered to relkind r/p; PG16-proven (v_foo → 0 pub edges) |
| empty `--schemas` emits misleading empty census (Claude) | fail closed (exit 2) before any DB work; +test |
| stale committed bundle hash in the dev transcript (Codex) | dev transcript marked superseded; PG16 transcript records current bundle `065d49e0…` |

Regression-green under `uv.lock`: contract 51 / checker 47 / collector 29; PG16.13 re-validated.

## Outstanding — OPERATOR DECISIONS (design; not unilaterally changed)

1. **F1 — unsigned snapshot** (dominant residual): the offline checker cannot bind a snapshot to a
   genuine read-only census without a collector SIGNATURE or an explicit pipeline-integrity guarantee.
2. **Destructive-delete evidence floor:** SP022 lets the three compensating consumer dimensions
   (static_repo / runtime_logs / external_clients) each be waived via `not_applicable`, so a delete
   can green on database_deps(0) + operator_declaration alone. Decide how many dims must be *genuinely
   observed* for an irreversible delete.
3. **Evidence-file TOCTOU:** the gate validates `recovery_proof`/evidence files at CHECK time; the
   later apply reads them. Binding the validated bytes (a pinned checksum) ties into the F1 signing
   decision.
4. **compat consumer gate:** compat does not require a `consumer_disposition`, so SP022/SP013 never
   run for it (unlike archive, which forces `no_consumer`, and promote, which runs SP013). compat is
   additive (a public compat view) and now destination-pinned to `public`, so risk is low — but
   decide whether compat should require consumer evidence or at least an explicit conclusion.

## Round-3 correction tranche (operator-ratified decisions on the 4 residuals + 2 new Mediums)

The operator RATIFIED Round-1 and Round-2 and returned decisions on the four outstanding design
items, plus two further Medium findings from their own re-audit. Implemented in one bounded
correction tranche (TDD; all suites regression-green under `uv.lock`: **contract 57 / checker 58 /
collector 35**). The catalog SQL is UNCHANGED — `query_bundle_sha256` remains
`065d49e08c0ba8458aed25fc24bdacbfd8c3c69e2759a348b797fc496f3aa568`, byte-identical to the committed
PG16.13 transcript, so no PG16 re-run was required.

| # | Item (source) | Resolution |
|---|---------------|-----------|
| 1 | New Medium: non-finite compat exit window (Codex) — `exit_condition.window_hours` = +inf slips past the schema's exclusiveMinimum:0 | checker SP015 now rejects non-finite `window_hours` as well as `threshold`; +neg |
| 2 | New Medium: consumer classification discarded from the durable snapshot (Codex) | collector emits a required `dependency_role` per stored edge (external_consumer \| outbound_dependency \| attached_object), computed after the consumer-OR; schema adds the enum + requires it; +3 tests. No SQL change |
| 3 | Decision F1 — signed evidence (Ed25519) | new `disposition_signing.py`; collector signs the exact snapshot bytes with an env-injected key (value-silent) → detached `.sig`; checker SP026 verifies before trusting (preapply REQUIRES `--snapshot-sig` + `--verify-key`; missing/invalid ⇒ block, semantics never run); `cryptography==49.0.0` pinned + relocked; ephemeral-key tests. Production key = operator custody (Infisical), never handled here |
| 4 | Decision — destructive-delete evidence floor | new SP027: for an accepted delete, database_deps/static_repo/runtime_logs/operator_declaration must be OBSERVED (no `not_applicable` waiver); external_clients OBSERVED, or `not_applicable` ONLY when `in_data_api_exposed_schema` is OBSERVED false; observation window ≥ 30 days. Structured `recovery_artifact` {artifact_path, sha256, captured_at, restore_validation_ref}: checker resolves the path, verifies the backup bytes hash to the declared sha256, resolves the restore-validation proof, and confirms capture predates the census (SP014). +7 negs, +1 positive (the one allowed external waiver) |
| 5 | Decision — gate receipt (TOCTOU) | checker `--receipt-out` emits, on a GREEN gate, a `disposition_gate_receipt` pinning the SHA-256 of the four CLI docs (+ signature/verify-key) and every resolved decision-referenced evidence file (recovery artifact, restore proof, evidence_refs, transform report, telemetry). Apply-runner contract = rehash-before-SQL, fail on mismatch. +2 tests |
| 6 | Decision — mandatory compat consumer evidence | accepted compat now REQUIRES `consumer_disposition: has_consumers` (schema); the checker's consumer-evidence resolution (SP022/SP013) then runs for compat INDEPENDENT of the manifest's `required_observations`; no consumer ⇒ the decision cannot be accepted (stays proposed). +2 schema negs, +1 checker neg |

An adversarial negative accompanies every reproduced bypass. `disposition_signing.py` lazy-imports
`cryptography` so `import collect_disposition` stays cheap and the offline core keeps its
no-heavy-deps-on-import property.

## Round-3 cross-engine re-audit (of the correction commit `53507c0f`)

Codex `gpt-5.5` xhigh (`review --base a5bed80d`, detached worktree) found **3 real defects — all in the
NEW tranche code**, and all the same class: a control meant to CLOSE a TOCTOU re-read the artifact at
a different time than it was parsed/validated. (The Claude grounded-audit's first invocation
`wf_c8d73f2a-f1f` was mis-shaped — `probes` passed as strings, and this workflow's probe agents don't
receive `subject` — so it was stopped and re-run correctly as `wf_9bf40060-b7a`; see the Claude section.)

| Sev | Finding (Codex) | Resolution |
|-----|-----------------|-----------|
| P1 | SP026 verified the snapshot file RE-READ at verify time, not the bytes `load_doc()` already parsed — a file swapped between parse and verify lets a signed benign file satisfy SP026 while the gate trusts a different in-memory doc | checker main() reads each input's bytes ONCE, parses from that buffer, and verifies the sidecar against the in-hand snapshot bytes via new `verify_detached()`; +e2e already covers tamper |
| P1 | `build_receipt` RE-READ the CLI inputs after `run()` validated the in-memory docs, so with `--receipt-out` it could pin hashes of unvalidated bytes | `build_receipt` now hashes the in-hand `doc_bytes` (the parsed+gated bytes), not a second read; `_receipt_pure` strengthened to corrupt the on-disk file after capture and assert the receipt follows the validated bytes |
| P2 | `write_signed_snapshot` under `--overwrite` deleted the just-written snapshot on a sidecar-write failure — after `os.replace` had already destroyed the prior snapshot, leaving NO valid pair | sidecar is published FIRST, snapshot SECOND, and no destination is ever deleted on failure; a failed snapshot replace leaves the prior snapshot intact (the new sidecar simply won't verify → fail-closed). +collector regression test |

All three Codex defects resolved on commit `84eb2411`; the cross-engine pass earned its keep — three
genuine TOCTOU/data-safety defects in the very controls added to close TOCTOU, none caught by the
per-item TDD.

### Claude grounded-audit (`wf_9bf40060-b7a`, Deep, 5 self-contained probes + adversarial + memo)

**Verdict: SHIP-WITH-CONDITIONS — no FATAL, no primary-gate destructive false-green.** It VERIFIED
sound: the three R3 TOCTOU repairs; manifest-independent compat consumer evidence; SP015 reachable for
compat+promote; dependency_role↔found_consumers on the live path; a receipt cannot emit on a non-green
gate. It found **F1 (IMPORTANT, missed by BOTH engines' probes)** plus a MEDIUM/LOW hardening tail.
FIXED in commit `<this>` (contract 58 / checker 62 / collector 37; bundle hash unchanged; no PG16 re-run):

| Finding | Sev | Resolution |
|---------|-----|-----------|
| F1 — `format: date-time` was INERT (rfc3339-validator not installed → jsonschema silently skips the format), so every timestamp check degraded to a regex that admits calendar-invalid values (month 13, hour 25). Consequences: a calendar-invalid future `captured_at` bypassed the SP014 ordering check (swallowed `except`); `observed_at`/window `parse_dt` crashed as a traceback not a clean SP0xx. **Execution-confirmed.** | IMPORTANT | Pinned `rfc3339-validator==0.1.4` → `date-time` now validates (calendar-invalid ⇒ SP001 at the schema layer, both checker + collector); `captured_at` parse failure now emits SP014 (never a silent pass); +schema negative with a real calendar-invalid value |
| F2 — the recovery floor proved self-consistency, not recoverability: `restore_validation_ref` was existence-only (empty file / arbitrary file / `rvr==artifact_path` all passed); comments overstated the guarantee | MEDIUM | `restore_validation_ref` now must be non-empty AND distinct from `artifact_path`; schema + checker comments corrected to state the gate binds STRUCTURE not recoverability (real restore-success is an operator/apply-time attestation). Recency floor + deeper attestation SURFACED (D-below) |
| F5 — SP026 keyed on `mode=='preapply'` (fail-OPEN for a future mode) | LOW | default-deny: gated for EVERY mode except an explicit (empty) exempt set |
| F6 — `dependency_role` IFF `found_consumers` not enforced: an outbound edge flagged `_is_consumer` would be counted yet labeled `outbound_dependency` (unreachable on the live SQL, reachable via a future source/manual overlay) | LOW | `consumer_keys` now excludes outbound edges → `found_consumers == #external_consumer` by construction; +collector test |
| F7 — `build_receipt` silently omitted a sig/verify-key entry if the file vanished before hashing | LOW | hard-error (FileNotFoundError) on a missing verification input; `main()` refuses to emit an incomplete receipt (returns 1) |
| F8 — SP015 finiteness skipped for `required=false` contracts (inert today; forward risk) | LOW | finiteness checked whenever an `exit_condition` is present; +checker negative |

**SURFACED as operator decisions (NOT unilaterally implemented — see the operator-decisions block):**
F2 `captured_at` recency floor (needs a policy value); F3 threading `semantic_check`'s already-computed
recovery-artifact hash into the receipt; F4 labeling receipt evidence entries + carrying the declared
sha; the DEEPER recovery-recoverability attestation (inherently apply-time); the apply-runner
re-validation contract (must re-run SP014 + `verify_detached`, not merely rehash the receipt — this
single fact sets the residual severity of F3/F4/F5); the unsigned governance-doc asymmetry
(decisions/manifest/entity_map are plain JSON, pinned by the receipt but not signed like the snapshot).

## Verdict
Cross-engine adversarial review drove **8 + 9** findings on earlier commits, **6** operator-ratified
items in the correction tranche, **3** from the Codex re-audit (TOCTOU in the new controls), and **6**
from the Claude re-audit (F1 IMPORTANT + a hardening tail) — each with a negative test, no SQL change,
PG16 proof still valid. Both re-audits agree there is **no FATAL and no primary-gate destructive
false-green**; the F1 timestamp gap is closed. The remaining items are apply-time/policy design calls
surfaced for the operator, not code defects. Per the fail-closed convergence rule, further code-only
rounds show diminishing returns — the lane is at a **decision point, not a defect point**.
**Census GO, push, and PR remain HELD** pending operator ratification, the production keypair custody,
and the surfaced apply-time decisions (which gate the first DESTRUCTIVE apply, not the read-only census).

## Operator adversarial audit of `382dec9a` — CONDITIONAL census ratification

The operator ran an independent adversarial pass on `382dec9a` and **conditionally ratified the
collector/signature path for the first UNIQUE, no-overwrite, read-only census**, gated on four
pre-census fixes; the apply gate stays HELD, and the signed-overlay contract + apply-runner become the
NEXT PACKET (not another checker-only round). Two findings were real bugs in the immediately-preceding
fixes. Independently verified by the operator: suites 58/62/37, RFC3339 active, SP015 on inf windows,
in-hand-bytes verify + receipt, fail-closed key disappearance, bundle `065d49e0`, branch clean, no prod
access. Pre-census fixes applied in the pre-census commit (suites 58/63/37; bundle hash unchanged):

| # | Sev | Finding | Resolution |
|---|-----|---------|-----------|
| 1 | High | the "distinct restore proof" check compared declared path STRINGS, so a symlink `restore-alias.log`→`recovery.tar` false-greened (same inode) | compare the RESOLVED files with `os.path.samefile`, not strings; +symlink-alias negative |
| 2 | Medium | signed-pair `--overwrite` is not atomic AS A PAIR — a failed snapshot replace left the old snapshot beside a new, non-verifying sidecar | removed `--overwrite` from the signed path entirely; a signed census writes a UNIQUE path, no-clobber (os.link) for both files; the overwrite test became a no-clobber test |
| 4 | Medium | the receipt was described as "closing TOCTOU"/authorizing SQL, but it re-reads sig/key/evidence after validation | `build_receipt` docstring corrected: the receipt is ADVISORY and records validated hashes; the apply runner is the authority and MUST independently re-read/re-verify/re-check/rehash/restore-test |
| 5 | Low | committed evidence memo had trailing whitespace (`git diff --check`) | stripped trailing whitespace from `evidence/*.md` |

**Ratified for the NEXT PACKET (apply-runner + signed overlays), NOT implemented now:**
- **Recovery recency:** a dedicated manifest `max_recovery_age_hours` (recommend 24h at checker time), NOT `max_staleness_hours` (different fact); the apply runner must create + restore-test a FRESH backup immediately before the destructive SQL.
- **Apply-runner = revalidate everything** (7 steps): read each input once; verify snapshot + overlay signatures vs the repo-pinned key; re-run schema/semantic/target/SP014; verify receipt hashes; bind + hash the exact migration SQL; restore-test the backup in disposable PostgreSQL; recheck target identity + drift immediately before executing that exact SQL.
- **Receipt hardening (F3/F4):** build WITH the apply runner (interface known there) — thread validated evidence bytes/hashes forward in memory, label each evidence role, record the verified key fingerprint, include the migration hash. No standalone receipt revision first.
- **Signed overlays (design gap #3):** the collector signs the WHOLE raw snapshot, but static_repo/runtime/external_clients/operator/exposure/advisor ship as `not_observed` and are meant to be filled later — editing them invalidates the signature. Keep the census IMMUTABLE; define separately-signed overlay documents bound to the base snapshot SHA-256.
- **Unsigned governance docs:** acceptable only if the runner requires a clean, reviewed Git commit and verifies each doc against its Git blob/hash; reject arbitrary working-tree files.

**Pre-census GO checklist (operator):** (1) restore-proof alias detection ✅; (2) remove signed `--overwrite` ✅; (3) clean the evidence memo ✅; (4) generate the production Ed25519 keypair out-of-band (private → Infisical, commit the public key) — OPERATOR. Then: the read-only census GO for a unique `evidence/prod-<ts>.json`. The apply gate remains HELD.

## Census-enablement packet (operator-directed; final packet before the census)

The operator's three remaining gaps (tooling local-only; `preapply` is the wrong post-census
verifier; the signature doesn't bind `--schemas`) are closed. Suites green: schema 59 / checker 63 /
collector 38 / **census-acceptance 14**; bundle hash unchanged (`065d49e0`).

- **Gap 3 — signed `collection_scope`:** the collector now bakes `collection_scope`
  {schemas(sorted), expected_database, required_role_markers(sorted), repo_sha, query_bundle_sha256,
  collector_version} into the signed snapshot (schema-required), so the signature binds the query
  PARAMETERS, not just the SQL text. +schema negative +collector test.
- **Gap 2 — `verify_census.py` (census-acceptance gate), distinct from preapply:** verifies the
  detached signature vs the repo-pinned public key BEFORE parsing (CN001); asserts project_ref /
  database / schema-scope / query-bundle hash / **merged repo SHA** / role markers; validates
  structure + relation_count + object_id; rejects any `query_failed` group (CN011); confirms every
  relation is in the requested scope (CN012); PERMITS the expected zero-width windows + `not_observed`
  overlays; requires NO decisions/entity-map/manifest. Codes CN0xx. +14 tests incl. the operator's
  adversarial set (wrong scope, wrong bundle hash, wrong repo SHA, mixed-schema, query failure,
  missing signature, wrong key).
- **Gap 1 — local-only tooling:** addressed by process — `CENSUS_RUNBOOK.md` mandates running from a
  **merged `main`** checkout so `repo_sha` == the merged commit, which `verify_census --expect-repo-sha`
  asserts. The collector + verify_census + public key go through a governed PR + merge BEFORE the census.
- **Runbook:** `CENSUS_RUNBOOK.md` — the exact value-silent census + acceptance procedure (secrets
  from env only, unique `prod-<UTC>.json` + `.sig`, no-overwrite, redacted transcript, evidence PR).
  **Prepared only — not run.**

**Ratified-for-later (unchanged):** signed-overlay contract, apply-runner (revalidate-everything incl.
restore-test), recovery-recency (`max_recovery_age_hours` 24h), receipt hardening — all after the census.

## Census-hardening tranche (operator audit of `588da50b` — 5 false-green paths)

The operator's adversarial pass found 5 acceptance-gate false-greens; HELD census GO + PR. All fixed;
suites green (schema 59 / checker 63 / collector 40 / census-acceptance 21); catalog SQL RE-VALIDATED on
PG16.13 (bundle `217ff3ad…`, census_count added).

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| 1 | High | merged-main provenance not enforced — the collector records `git HEAD` even from a DIRTY tree, so modified tooling could stamp the clean commit | collector refuses a DIRTY worktree (`_git_worktree_clean`) and `--expect-repo-sha` asserts HEAD==expected BEFORE any secret injection / DB access; runbook writes evidence OUTSIDE the repo so the tree stays clean; +2 collector tests |
| 2 | High | trust anchor is caller-selected — `verify_census --verify-key` accepts any matching key; the fingerprint file is never consumed | replaced with `--key-id` (+`--keys-dir`): resolves the pinned `keys/<id>.pub.pem` + `.spki-sha256`, requires the pubkey's SPKI sha256 to equal the committed fingerprint (CN013), THEN verifies; +fingerprint-mismatch + unknown-key-id tests |
| 3 | Med | an EMPTY census and two DIFFERING records sharing an object_id both passed (`uniqueItems` only catches identical JSON) | verify_census rejects empty (CN014) + duplicate object_ids (CN015); collector adds an INDEPENDENT DB `census_count` → `catalog_relation_count` (schema-required); CN009 now requires emitted-list == relation_count == catalog count; +tests + PG16 re-validation |
| 4 | Med | mismatched top-level vs scope `collector_version`, and a mismatched `target_identity.expected_database`, both passed | verify_census asserts internal consistency of collector_version/repo_sha/query_bundle_sha256 (CN016) and `target_identity.expected_database == --expect-database` (CN004); +tests |
| 5 | Med | the runbook exported secrets into the operator shell, bypassing the injection contract | runbook uses `infra/infisical/inject.sh prod -- <collector>` (`--dsn-env SUPABASE_PROD_DSN`, secrets in child only); run from the merged-main worktree; evidence written out-of-tree |

Independently confirmed by the operator: the two public artifacts are valid, contain no private key, the
SPKI fingerprint matches, and the Infisical private key was verified against that public key without
exposing either. Trust-anchor keys committed separately (dedicated, exact-path commit; no broad add).
One focused cross-engine review runs on this tranche before the census GO.
**Census GO, push, and PR remain HELD** — a fresh cross-engine IRP re-audit runs on the correction
commit before any read-only census, and the production signing keypair (Infisical custody) is a
census precondition, not handled in this tranche.
