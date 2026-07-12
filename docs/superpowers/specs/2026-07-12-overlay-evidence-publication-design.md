# Overlay Evidence Publication Packet — Design

**Status:** design (spec only). Phase 2 of the disposition-ledger gated roadmap. Authoring this design
authorizes NO implementation, evidence collection, signing, DB access, external access, or production
action. All downstream phases remain HELD, each behind a fresh explicit operator GO.

**Goal:** Give the disposition-ledger lane the *producer* tooling that the signed-overlay *consumer*
(`disposition_overlay.py`, merged @ `a47161fc`) already assumes exists but that was deliberately left
out of the consumer packet: a value-silent, no-clobber **overlay author/sign command**, a **standalone
committed-artifact verifier**, an **`overlay-evidence` CI gate**, a **six-dimension collection runbook**,
and **corrections to `CENSUS_RUNBOOK.md`**. Per census-runbook §"After the census", the overlay tooling
lands *before* any evidence is collected (Phase 6+).

**Architecture (one line):** three small sibling modules + one CI script + two runbook docs, all
**reusing** the frozen consumption contract in `disposition_overlay.py` so *what the author accepts and
signs is exactly what the consumer will accept* — no re-implemented, drift-prone second copy of the
overlay rules.

---

## Global Constraints (bind every task)

- **Schemas FROZEN.** `disposition.schema.json` and `overlay.schema.json` are read-only inputs. This
  design requires **no** schema change — the overlay contract already carries every field the author
  computes. (Justification in §9.) If a plan task believes a schema edit is necessary, that is an
  escalation, not a task.
- **Value-silence.** The Ed25519 private key is read **only** from `DISPOSITION_SIGNING_KEY` (env,
  Infisical-injected), never argv, never printed, never embedded in any artifact. A key-load failure
  surfaces as a generic message (the PEM never appears in output). No DSN is involved (the author is
  offline; it needs no database).
- **COMPUTED, never typed.** Every binding value — `base_snapshot_sha256`, `disposition_schema_sha256`,
  `overlay_schema_sha256`, `project_ref`, `captured_at`, `producing_repo_sha`, `source_hash` — is
  computed by the tool from the census bytes / schema bytes / git / clock / source file. The operator
  supplies only *semantics* (which objects, what values, what window, what authority).
- **No-clobber, sidecar-first, atomic, unique path.** Mirror `collect_disposition.write_signed_snapshot`:
  the `.sig` is written first, then the overlay, each via temp-file + fsync + `os.link` (atomic
  create-if-absent; `FileExistsError` if present). A signed artifact NEVER overwrites.
- **Source-pinned trust anchor.** The verifier resolves the signer through the reviewed source constant
  `disposition_trust.TRUSTED_SIGNERS` (`resolve_pinned_key`), exactly as `verify_census.py` does. A
  caller-supplied keys dir cannot substitute its own key.
- **Acyclic module DAG preserved.** `disposition_overlay.py` stays a LEAF (imports only
  `disposition_signing`). New producer modules may import `disposition_overlay` (leaf),
  `disposition_signing`, `disposition_provenance`; they MUST NOT import `check_disposition`.
- **pytest is NOT a locked dependency.** Tests are script `__main__` runners executed via
  `uv run --project . --locked python tests/<file>.py`, registered in the CI `suites` loop — same as
  every existing schema-placement suite.
- **Offline + read-only.** The author, verifier, and CI touch no database and no network. The author
  reads the census file, the schema files, the source-evidence file, and git; it writes only the overlay
  + sidecar.

---

## 1. Ground truth (what the merged consumer already fixes)

The consumer (`disposition_overlay.py`) defines the overlay contract this packet must produce *to*. The
producer tooling is correct **iff** an overlay it signs passes the consumer's own checks. The relevant
frozen facts:

- **Overlay document** (`overlay.schema.json`, `additionalProperties:false`): required `kind`
  (`"evidence_overlay"`), `overlay_version` (`"1"`), `dimension` (6-enum), `source_type` (6-enum),
  `authority`, `collection_method`, `source_locator`, `source_hash` (64-hex or null),
  `base_snapshot_sha256` (64-hex), `disposition_schema_sha256` (64-hex), `overlay_schema_sha256`
  (64-hex), `project_ref`, `captured_at` (iso), `observation_window` (`{started_at, ended_at}`),
  `producing_repo_sha` (40-hex or null), `assignments` (≥1 × `{object_id, value}`). Optional:
  `source_hash_not_applicable_reason`, `producing_repo_sha_not_applicable_reason`, `operator_identity`,
  `attestation_ref`. Per-dimension `allOf` fixes `source_type` and the `value` shape; the
  `operator_declaration` dimension additionally requires `operator_identity` + `attestation_ref`.
- **Signature** (OV001): detached Ed25519 over the **exact raw overlay bytes**, via
  `disposition_signing.build_sig_sidecar` / `verify_sidecar_bytes_with_key` — same primitive and same
  anchor as the census.
- **Binding** (`check_binding`): OV002 `base_snapshot_sha256 == sha256(census file bytes)`; OV003
  `project_ref == census.project_ref == --expect-project-ref` (three-way); OV020
  `disposition_schema_sha256`/`overlay_schema_sha256 == on-disk schema bytes`.
- **Target** (`check_target`): OV004 dimension ∈ 6; OV013 `source_type == DIMENSIONS[dimension]` fixed;
  OV019 `source_hash` null ⇔ reason present; OV012 `producing_repo_sha` three categories —
  REQUIRED{`in_data_api_exposed_schema`,`consumer_evidence.static_repo`} (non-null, no reason),
  FORBIDDEN{`advisor_findings`,`consumer_evidence.runtime_logs`,`consumer_evidence.operator_declaration`}
  (null + reason), CONDITIONAL{`consumer_evidence.external_clients`} (non-null xor reason); OV014
  operator_declaration provenance; OV005 every `object_id` present in the census; OV006 the target base
  slot is `not_observed`.
- **Window** (`check_observation_window`, OV009): `started_at < ended_at ≤ captured_at ≤ now`.
- **Value shapes** (per dimension, from `disposition.schema.json $defs`):
  `in_data_api_exposed_schema` → `observed_bool` `{state:"observed", value:<bool>}`;
  `advisor_findings` → `observed_advisor_array` `{state:"observed", value:[str,…]}`;
  the four `consumer_evidence.*` → `consumer_evidence_dim` — observed ⇒
  `{state:"observed", found_consumers:<int≥0>, ref:<nonempty>}`, any other state ⇒
  `{state:…, found_consumers:null, ref:null, detail:<nonempty>}`.
- **Author/verifier patterns to mirror:** `collect_disposition._write_bytes_atomic` /
  `write_signed_snapshot` (atomic sidecar-first no-clobber; unique timestamped path; refuse to overwrite),
  its value-silent env-key handling and provenance gate (`disposition_provenance.git_head_sha` +
  `git_worktree_clean`, `--expect-repo-sha`); and `verify_census.py` (read bytes once → resolve pinned
  key → verify sig before parse → semantic checks with stable codes → exit 0 only when clean).
- **Consumer-side cluster checks NOT in scope for the artifact producer:** OV007 (cross-overlay dup),
  OV011/OV016/OV017/OV018 (window derivation), OV015 (cluster completeness), OV021/OV022 (base-window /
  delete-floor) are evaluated by `check_disposition --mode preapply` over the *whole cluster* (Phase 11).
  This packet enforces the *per-artifact* subset (OV001–OV006, OV008–OV010, OV012–OV014, OV019–OV020) at
  author and verify time, and OV007 across the *committed set* in CI (§4).

---

## 2. Components overview

| # | Unit | Responsibility | Imports (new edges) |
|---|------|----------------|---------------------|
| A | `author_overlay.py` | Assemble → validate (consumer checks) → sign (value-silent) → publish (atomic sidecar-first no-clobber, unique path) one overlay for one dimension. | `disposition_overlay`, `disposition_signing`, `disposition_provenance` |
| B | `verify_overlay_artifact.py` | Standalone: verify a committed overlay+sidecar against the pinned signer and its bound census (integrity + binding + target). | `disposition_overlay`, `disposition_signing`, `disposition_trust`, `disposition_provenance` |
| C | `ci/verify_committed_overlays.sh` + `overlay-evidence` job | Verify every overlay ADDED on a branch: sidecar present, bound to a committed census, tooling-consistent, signer-valid, and no cross-overlay OV007 duplicate. | (shell → B) |
| D | `OVERLAY_COLLECTION_RUNBOOK.md` | Per-dimension authoritative source, method, value shape, window, applicability, failure behavior, redaction, evidence-PR procedure. | (doc) |
| E | `CENSUS_RUNBOOK.md` corrections | PG17.6; `disposition_trust.py` anchor; current post-census sequence. | (doc) |

All three modules are **peers of the collector**, invoked as CLIs; none is imported by the consumer, so
the leaf DAG is preserved.

---

## 3. Component A — `author_overlay.py` (author + sign)

**One overlay, one dimension, per invocation** (Phase 9 issues source-specific GOs per dimension). The
command is a mechanical *binder + validator + signer + publisher* — it does not collect evidence; the
operator/collection-runbook supplies the raw evidence and the semantic core.

### 3.1 Inputs

- `--census <path>` + `--census-sig <path>` — the fresh signed census the overlay binds to.
- `--key-id <id>` + `--keys-dir <dir>` (default `keys/`) — the pinned signer (for verifying the census
  before authoring against it; the *public* anchor, not the signing key).
- `--input <overlay-core.json>` — operator-supplied **semantics only**:
  `{dimension, assignments:[{object_id, value}…], observation_window:{started_at, ended_at},
  authority, collection_method, source_locator, [operator_identity], [attestation_ref]}`.
- `--source-file <path>` **xor** `--source-hash-na-reason <str>` — source evidence bytes (→
  `source_hash = sha256(bytes)`) or the not-applicable reason.
- `--producing-repo-sha-na-reason <str>` — required for the FORBIDDEN dims and the CONDITIONAL dim when
  no repo produced the evidence; ignored (must be absent) for REQUIRED dims.
- `--expect-project-ref <ref>` — asserted `== census.project_ref` (fail-closed).
- `--out <path>` (+ `--sig-out`, default `<out>.sig`) — unique publish path (§3.5).
- `--signing-key-env DISPOSITION_SIGNING_KEY` — env var holding the PEM (value-silent).

### 3.2 Computed binding (never typed)

`base_snapshot_sha256 = sha256(census file bytes)`; `disposition_schema_sha256` /
`overlay_schema_sha256 = OverlayContract.disp_sha256 / .overlay_sha256`; `project_ref = census.project_ref`;
`captured_at = now (UTC, tool clock)`; `source_type = disposition_overlay.DIMENSIONS[dimension][1]`
(fixed — so OV013 cannot fire); `kind="evidence_overlay"`, `overlay_version="1"`;
`producing_repo_sha` per the OV012 category table —
REQUIRED dims: `disposition_provenance.git_head_sha(repo)` (and a **clean-worktree assertion** so the SHA
identifies a real commit; `--expect-repo-sha` optional but recommended, mirroring the collector);
FORBIDDEN dims: `null` + `--producing-repo-sha-na-reason`; CONDITIONAL (`external_clients`): git HEAD if
a repo produced it, else `null` + reason.

### 3.3 Validate-before-sign (the correctness guarantee)

After assembly, the author runs the consumer's **own** per-artifact checks against the census —
`load_overlay_contract()` → `validate_overlay` (OV008) → `check_binding` (OV002/003/020) →
`check_observation_window` (OV009) → `check_target` (OV004/005/006/012/013/014/019) with the census
`rel_index` — plus an **intra-overlay duplicate `object_id`** check (a single overlay assigning the same
object twice). If ANY check yields an `OV0xx`/`AO0xx`, the author prints the codes and **refuses to
sign or publish**. Because these are the *identical functions* the consumer enforces, an authored-and-
published overlay is guaranteed to pass the consumer's per-artifact gate (the cluster-level checks remain
the preapply gate's job).

### 3.4 Census verification first

Before anything else the author `resolve_pinned_key(keys_dir, key_id)` and
`verify_detached_with_key(census_bytes, census_sig, signer.public_key)` — you cannot author an overlay
against a forged/tampered/foreign-signed census. Fail-closed with a coded message.

### 3.5 Publish (mirror the collector)

Serialize canonically (`json.dumps(doc, indent=2, sort_keys=True).encode()`) → the **signed message**.
`build_sig_sidecar(message, private_key)` → sidecar bytes. Publish **sidecar first**, then the overlay,
each atomic + no-clobber (temp+fsync+`os.link`). Refuse up front if either path exists. Reuse the
collector's atomic helper (imported, or a ~15-line replica to keep the frozen collector untouched — a
build-detail, not an interface).

**Naming / unique path:** `evidence/overlay-<dim-slug>-<census12>-<UTC>.json` (+ `.json.sig`), where
`<dim-slug>` replaces `.` with `_` (`consumer_evidence.static_repo` → `consumer_evidence_static_repo`),
`<census12>` is the first 12 hex of `base_snapshot_sha256` (groups overlays by the census they bind to),
`<UTC>` = `YYYYMMDDTHHMMSSZ`. The CI glob is `evidence/overlay-*.json`.

### 3.6 Error codes (`AO0xx`, stable)

`AO000` input unreadable/invalid; `AO001` census signature failed (untrusted/forged base); `AO002`
`--input` missing a required field / wrong type; `AO003` `--expect-project-ref != census.project_ref`;
`AO004` source-file/NA-reason mutually-exclusive violation; `AO005` assembled overlay failed a consumer
check (prints the underlying `OV0xx`); `AO006` intra-overlay duplicate `object_id`; `AO007`
`DISPOSITION_SIGNING_KEY` unset / not a valid Ed25519 PEM; `AO008` publish failed / path exists
(no-clobber). Exit 0 only on a signed, published pair.

---

## 4. Component B — `verify_overlay_artifact.py` (standalone verifier) + Component C (CI)

### 4.1 Verifier

Mirrors `verify_census.py`, at overlay granularity. Args: `--overlay`, `--overlay-sig`, `--census`,
`--census-sig`, `--key-id`, `--keys-dir`, `--expect-project-ref`. Flow: `resolve_pinned_key` →
read overlay bytes once → `verify_sidecar_bytes_with_key(overlay_bytes, sig_bytes, signer.public_key)`
(OV001) → **also** verify the census sig against the same signer (so the base it binds to is itself
genuine) → `parse_overlay` (dup-key/non-finite reject) → `load_overlay_contract` → `validate_overlay`
(OV008) → `check_binding` vs `sha256(census bytes)` + schema shas (OV002/003/020) →
`check_observation_window` (OV009) → `check_target` vs census `rel_index` (OV004/005/006/012/013/014/019).
Prints `OV0xx`; exit 0 only when clean. It is an **artifact integrity + binding** gate; it does **not**
run cluster derivation (OV011/015/016/017/018/021/022) — those are `check_disposition --mode preapply`.
This scoping is stated in the module docstring so no one mistakes a green artifact verify for
evidence-readiness.

### 4.2 CI — `ci/verify_committed_overlays.sh` + `overlay-evidence` job

Mirrors `ci/verify_committed_census.sh`. `set -euo pipefail`; `git fetch origin main`;
`BASE=merge-base`; `ADDED = git diff --diff-filter=A --name-only BASE HEAD -- '$SP/evidence/overlay-*.json'`
(excluding `.sig`); if none → exit 0. `TOOLING = author_overlay.py verify_overlay_artifact.py
disposition_overlay.py disposition_signing.py disposition_trust.py disposition_provenance.py
overlay.schema.json disposition.schema.json keys`. For each added overlay:
1. **missing sidecar** → FAIL.
2. Extract `base_snapshot_sha256`; find the committed `evidence/census-prod-*.json` whose
   `sha256(bytes)` equals it; **no match → FAIL** (overlay binds to a census not present in the tree).
3. If `producing_repo_sha` is non-null: assert it is an **ancestor of HEAD** and TOOLING is **unchanged**
   since it (`git diff --quiet <producing_repo_sha> HEAD -- $TOOLING`) — the same tooling-drift assertion
   the census gate makes.
4. Run `verify_overlay_artifact.py` against the matched census + its sidecar + the pinned signer + the
   expected project ref; must exit 0.

After the per-overlay loop, a **cross-overlay OV007** check: across all added overlays binding to the
same census, no `(dimension, object_id)` pair may repeat → FAIL if it does. New job `overlay-evidence`
(`fetch-depth: 0`, pinned `uv==0.11.21`) runs the script; the existing `suites` loop gains
`test_author_overlay` and `test_verify_overlay_artifact`.

---

## 5. Component D — `OVERLAY_COLLECTION_RUNBOOK.md` (six dimensions)

A **DO-NOT-RUN-until-GO** procedure (like the census runbook) covering, per dimension: authoritative
source, collection method, `value` shape, `observation_window` semantics, `producing_repo_sha` /
`source_hash` applicability, failure behavior, redaction, and the evidence-PR procedure.

| Dimension (`source_type`) | Authoritative source | `value` shape | `producing_repo_sha` | `source_hash` |
|---|---|---|---|---|
| `in_data_api_exposed_schema` (`platform_config`) | Supabase Data-API **exposed-schemas platform config** (declared, not the runtime `pgrst.db_schemas` GUC) | `observed_bool` `{state:"observed", value:<bool>}` | REQUIRED (repo-committed config export → git HEAD) | sha256(config export) |
| `advisor_findings` (`advisor_api`) | Supabase **advisor API** (security/performance) | `observed_advisor_array` `{state:"observed", value:[str,…]}` | FORBIDDEN (API snapshot) → null+reason | sha256(saved advisor JSON) |
| `consumer_evidence.static_repo` (`repository_scan`) | **Static scan** of platform repos for references to each object | `consumer_evidence_dim` | REQUIRED (scanned repo commit → git HEAD) | sha256(scan output) |
| `consumer_evidence.runtime_logs` (`runtime_logs`) | Production **query/pg logs** over the window | `consumer_evidence_dim` | FORBIDDEN (logs) → null+reason | sha256(log extract) |
| `consumer_evidence.external_clients` (`external_client_inventory`) | Inventory of **external API clients / integrations** | `consumer_evidence_dim` | CONDITIONAL (repo inventory → git HEAD; else null+reason) | sha256(inventory) |
| `consumer_evidence.operator_declaration` (`operator_declaration`) | Signed **operator attestation** (+ `operator_identity`, `attestation_ref`) | `consumer_evidence_dim` | FORBIDDEN → null+reason | sha256(attestation) or null+reason |

**Window discipline (so the eventual cluster preapply is satisfiable):** every overlay window must obey
`started < ended ≤ captured ≤ now` (OV009). At preapply the *consumer* window is derived as
`S=max(started), E=min(ended)` across the observed consumer overlays for each cluster-source relation and
must be non-empty (OV011), must bracket `base_observed_at` i.e. `S ≤ observed_at ≤ E` (OV017), must be
fresh vs `--max-consumer-evidence-age-hours` (OV016), and — for a **delete** whose `external_clients`
resolves `not_applicable` — the observed-**false** `in_data_api_exposed_schema` overlay window must
**cover** `[S, E]` (OV022). The runbook therefore directs operators to choose, per cluster-source
relation, consumer windows that overlap and bracket the census instant, and (for deletes) an
`in_data_api` window at least as wide. This is guidance for *satisfiability at preapply*; the artifact
tooling enforces only the per-overlay OV009.

Redaction + evidence-PR: overlays and sidecars are produced out-of-tree, secret-scanned/redacted (no
DSN, key, or `env` dump in any transcript), then copied into `evidence/` and committed through a governed
evidence PR (Phase 10) whose `overlay-evidence` CI independently re-verifies every artifact.

---

## 6. Component E — `CENSUS_RUNBOOK.md` corrections (grounded)

1. **PG16 → PG17.6.** The committed census `target_identity.server_version` is
   `PostgreSQL 17.6 … (server_version_num 170006)`. Correct the "PG16" statement (§preamble).
2. **Trust-anchor location.** "TRUSTED_SIGNERS constant in `verify_census.py`" → "the `TRUSTED_SIGNERS`
   source constant in **`disposition_trust.py`** (the shared anchor; `verify_census` *and*
   `check_disposition` both resolve through `resolve_pinned_key`)." (SP026 moved the anchor.)
3. **Post-census sequence.** Replace "build the signed-overlay packet … then the apply runner" (which
   framed the overlay tooling as future work) with the current sequence: the signed-overlay **consumer**
   is merged; next is **(this) overlay publication tooling → fresh census → definer-view reconciliation →
   collect+sign the six overlays with `author_overlay.py` bound to the fresh census → formal cluster gate
   (`check_disposition --mode preapply`) → apply runner**, each operator-gated.

---

## 7. Data flow (end to end)

Fresh signed census (Phase 6/7, committed) → operator collects raw evidence per dimension (collection
runbook) → `author_overlay.py` binds+validates+signs each overlay against that census → operator
`verify_overlay_artifact.py` locally → commit overlays+sidecars on an evidence branch → `overlay-evidence`
CI re-verifies every added artifact → (Phase 11) `check_disposition --mode preapply` derives windows and
runs the cluster gate over census + all overlays.

---

## 8. Error handling & fail-closed posture

Every ambiguous/missing/malformed condition is a **stable code** and a non-zero exit, never a stack
trace: `AO0xx` (author), `OV0xx`/`CN0xx`-analog (verifier), explicit `FAIL:` lines (CI). The author
never signs a doc that fails a consumer check; the verifier verifies the signature **before** parsing;
the CI fails on a missing sidecar, an unbound census, tooling drift, an untrusted signer, or a duplicate
assignment. Key/DSN values never appear in any output.

---

## 9. Why the schemas stay frozen

The author computes and injects every overlay field the contract requires; the contract already models
`source_hash_not_applicable_reason`, `producing_repo_sha_not_applicable_reason`, `operator_identity`, and
`attestation_ref`; the per-dimension `allOf` already fixes `source_type` and `value`. No new field, enum,
or constraint is needed to *produce* a conformant overlay — the producer is purely additive tooling over
a sufficient contract. A schema change would also break the already-merged consumer's `overlay_sha256`
binding (OV020) and every downstream hash. Therefore: **no schema edit.**

---

## 10. Testing strategy (negative-contract-first)

TDD, negatives first (each maps to a failing test before the code exists). Coverage matrix for the
operator's negative acceptance cases:

| Negative case | Enforced by | Code |
|---|---|---|
| tampering (bytes altered post-sign) | verifier / CI signature verify | OV001 |
| wrong base hash | verifier / CI binding | OV002 |
| wrong project | author + verifier | AO003 / OV003 |
| stale / incoherent window (per-overlay) | author + verifier | OV009 (+ OV010 captured_at) |
| schema drift | verifier / CI binding | OV020 (+ OV008) |
| missing sidecar | CI (and verifier fail-closed) | `FAIL: missing sidecar` |
| duplicate assignment (intra-overlay) | author | AO006 |
| duplicate assignment (cross-overlay, same census) | CI | OV007 |
| untrusted signer — foreign-signed artifact/census | author + verifier (sig fails vs pinned key) | AO001 / OV001 |
| untrusted signer — unpinned `--key-id` / substituted key material | author + verifier (`resolve_pinned_key` returns None) | key-resolution block (`CN013`-analog) |
| tooling drift | CI | `git diff --quiet <producing_repo_sha> HEAD -- $TOOLING` |
| overlay bound to a census not in the tree | CI | `FAIL: no matching committed census` |

Each `author_overlay`/`verify_overlay_artifact` suite is a script `__main__` runner using synthetic
Ed25519 keys + fixtures (no prod key, no DB). Both suites join the CI `suites` loop; the
`overlay-evidence` job is exercised by the artifact-verify suite plus a shell dry-run fixture.

---

## 11. Open decisions for operator ratification (with leans)

- **D1 — Reuse vs re-implement (architectural).** *Lean: reuse.* The author and the standalone verifier
  both **import `disposition_overlay`** and call its `validate_overlay` / `check_binding` /
  `check_observation_window` / `check_target`, so "what the author signs" ≡ "what the consumer accepts"
  with zero drift. Independence is preserved by *layering* — the standalone artifact verifier, the CI
  gate, and (ultimately) `check_disposition --mode preapply` are separate confirmations — rather than by
  a duplicate copy of the rules. Alternative: a fully independent re-implementation (belt-and-suspenders,
  but duplication + drift risk). Recommend **reuse**.
- **D2 — Module names.** *Lean:* `author_overlay.py`, `verify_overlay_artifact.py`,
  `ci/verify_committed_overlays.sh`, `OVERLAY_COLLECTION_RUNBOOK.md`. Trivial; rename on request.
- **D3 — Atomic-publish helper.** *Lean:* replicate the ~15-line `_write_bytes_atomic` sidecar-first
  helper inside `author_overlay.py` to keep the frozen collector untouched (minimal blast radius).
  Alternative: extract a shared `disposition_publish.py` used by both (cleaner factoring, touches the
  collector). Recommend **replicate**.
- **D4 — `producing_repo_sha` clean-worktree assertion in the author.** *Lean: yes* — for the REQUIRED
  dims, assert `git_worktree_clean` (and optionally `--expect-repo-sha`) so the producing SHA identifies
  a real committed scan, mirroring the collector. Recommend **yes**.

---

## 12. What this design explicitly does NOT do (holds intact)

No evidence is collected, no overlay is signed with the production key, no census is run, no DB is
touched, no schema is changed, nothing is pushed, no PR is opened, no cluster is assembled, and no
production action is taken. This packet is **tooling + runbooks only**. Phases 4 (build), 5 (PR), 6+
(census, reconciliation, collection, cluster, apply) each remain HELD behind their own explicit GO.
