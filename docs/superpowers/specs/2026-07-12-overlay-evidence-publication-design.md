# Overlay Evidence Publication Packet — Design (rev 2)

**Status:** design (spec only). Phase 2 of the disposition-ledger gated roadmap. Authoring this design
authorizes NO implementation, evidence collection, signing, DB access, external access, or production
action. All downstream phases remain HELD, each behind a fresh explicit operator GO.

**rev 2** folds the round-1 cross-engine IRP (Codex + Claude grounded-audit panel + operator audit); the
review record is `evidence/irp-cross-engine-overlay-publication.md`. Operator ratifications carried here:
**D1** reuse `disposition_overlay`'s own checks; **D2** the module names below; **D3** replicate the atomic
publish helper in this packet (with equivalent adversarial tests) and leave the census collector
untouched; **D4** author provenance is a **mandatory** clean merged-main checkout + required expected SHA.

**Goal:** the *producer* tooling the merged signed-overlay *consumer* (`disposition_overlay.py` @
`a47161fc`) assumes but omits: a value-silent, no-clobber **overlay author/sign command**, a **standalone
committed-artifact verifier**, an **`overlay-evidence` CI gate**, a **committed source-evidence record**, a
**six-dimension collection runbook**, and **`CENSUS_RUNBOOK.md` corrections**. Per the census runbook, the
overlay tooling lands *before* any evidence is collected.

**Architecture (one line):** three sibling modules + one CI script + a committed source-evidence record +
two runbook docs, all **reusing** the frozen consumption contract (`disposition_overlay`) and the census
acceptance gate (`verify_census.check_census`) so *what the author signs is exactly what the consumer and
the census gate accept* — with the artifact tooling additionally enforcing evidence **immutability** and
**source rehashability** that the per-cluster consumer does not.

---

## Global Constraints (bind every task)

- **Schemas FROZEN.** `disposition.schema.json` / `overlay.schema.json` are read-only inputs; this design
  needs no schema change (§10). `source_locator` (already a free string) is *defined* by this packet: when a
  source record is committed, it is the record's path **relative to the schema-placement directory**
  (`evidence/source/…`; CI resolves `$SP/<source_locator>` after `cd $(git rev-parse --show-toplevel)`,
  exactly the census gate's convention); in the null-`source_hash` case it names the out-of-band
  authority/custody locator. A semantic tightening, not a schema edit.
- **Value-silence (extended).** The Ed25519 private key is read only from `DISPOSITION_SIGNING_KEY` (env,
  Infisical-injected), never argv/printed/embedded. **The `--source-file` content is also secret-bearing**
  (runtime logs, advisor JSON may embed DSN fragments): the author only `read → sha256`s it and copies it,
  **never** prints or parses its content; a source read/hash failure is the dedicated fail-closed `AO009`
  reporting **only** the path + `type(exc).__name__` (never content, never a stack trace). No DSN is used
  (the author is offline).
- **COMPUTED, never typed.** Every binding value — `base_snapshot_sha256`, `disposition_schema_sha256`,
  `overlay_schema_sha256`, `project_ref`, `captured_at`, `producing_repo_sha`, `source_hash`, and (when a
  source record is published) `source_locator` — is computed by the tool. The operator supplies only
  *semantics* (objects, values, window, authority — and, in the null-`source_hash` case, the
  `--source-custody-locator` reference) plus the raw evidence.
- **No-clobber, sidecar-first, atomic, unique path** (mirror `collect_disposition.write_signed_snapshot`):
  temp-file + fsync + `os.link` (atomic create-if-absent; `FileExistsError` if present), with the
  collector's `finally` temp-unlink. A signed artifact NEVER overwrites.
- **Source-pinned trust anchor.** The signer resolves through `disposition_trust.TRUSTED_SIGNERS`
  (`resolve_pinned_key`), as `verify_census.py` does. A caller keys-dir cannot substitute its own key.
- **Acyclic DAG.** `disposition_overlay` stays a LEAF. New producer modules may import
  `disposition_overlay`, `verify_census` (which imports only the collector + leaves), `disposition_signing`,
  `disposition_trust`, `disposition_provenance`; they MUST NOT import `check_disposition`. (`verify_census`
  imports none of the new modules → acyclic.)
- **pytest is NOT locked.** Tests are script `__main__` runners via `uv run --project . --locked python
  tests/<file>.py`, registered in the CI `suites` loop.
- **Offline + read-only.** Author/verifier/CI touch no database and no network. The author reads census,
  schema, source-evidence, and git; it writes only the overlay + sidecar + source record.

---

## 1. Ground truth (the merged consumer + census gate this packet produces to)

Producer tooling is correct **iff** an overlay it signs passes the consumer's own per-artifact checks and
its base census passes the census gate. Frozen facts (grounded in `disposition_overlay.py` /
`verify_census.py`):

- **Overlay document** (`overlay.schema.json`, `additionalProperties:false`): `kind`(`evidence_overlay`),
  `overlay_version`(`1`), `dimension`(6-enum), `source_type`(6-enum), `authority`, `collection_method`,
  `source_locator`, `source_hash`(64-hex|null), `base_snapshot_sha256`(64-hex),
  `disposition_schema_sha256`(64-hex), `overlay_schema_sha256`(64-hex), `project_ref`, `captured_at`(iso),
  `observation_window`(`{started_at,ended_at}`), `producing_repo_sha`(40-hex|null), `assignments`(≥1 ×
  `{object_id,value}`); optional `source_hash_not_applicable_reason`,
  `producing_repo_sha_not_applicable_reason`, `operator_identity`, `attestation_ref`.
- **Per-artifact consumer checks** (the subset an artifact can be judged by, in isolation):
  OV001 signature (detached Ed25519 over exact raw bytes); OV002 `base_snapshot_sha256 == sha256(census
  bytes)`; OV003 three-way `project_ref`; OV020 schema-sha drift; OV004 dimension∈6; OV013 `source_type`
  fixed by `DIMENSIONS[dim]`; OV019 `source_hash` null⇔reason; OV012 `producing_repo_sha` three categories
  (REQUIRED{`in_data_api_exposed_schema`,`consumer_evidence.static_repo`} non-null/no-reason;
  FORBIDDEN{`advisor_findings`,`consumer_evidence.runtime_logs`,`consumer_evidence.operator_declaration`}
  null+reason; CONDITIONAL{`consumer_evidence.external_clients`} non-null xor reason); OV014
  operator_declaration provenance; OV005 object_id∈census; OV006 base slot `not_observed`; OV008 schema+
  format; **OV007** duplicate `(dimension,object_id)` *within or across* overlays (flat key list).
- **OV009 vs OV010 (corrected attribution).** `check_observation_window` (OV009) enforces
  `started_at < ended_at`, `ended_at ≤ captured_at`, and `ended_at ≤ now` — it does **not** bound
  `captured_at ≤ now`. The `captured_at > now` (future) guard and the `> max_staleness_hours` guard are
  **OV010**, wired only into the cluster `load_and_merge` (staleness needs the manifest). So the artifact
  tooling can enforce the manifest-independent half (`captured_at ≤ now`) but NOT the manifest staleness.
- **Cluster-only checks (NOT artifact-judgeable):** window derivation OV011/OV016/OV017/OV018, cluster
  completeness OV015, base-window OV021, delete-floor OV022 — all in `check_disposition --mode preapply`
  over the whole cluster (Phase 11). OV016 freshness is evaluated at preapply `now` against
  **E = min(ended)** across the observed consumer overlays (the earliest-ending window), not `captured_at`.
- **Census acceptance** (`verify_census.check_census`): the full contract — schema+`kind`, project_ref,
  database (current/scope/target), collection_scope (schemas, role markers, collector_version/repo_sha/
  query-bundle internal consistency), query-bundle hash, repo_sha, relation/catalog counts, object_id
  integrity, empty/dup rejection, `query_failed` rejection, scope containment. A signed-but-out-of-scope /
  malformed / query-failed census must NOT become an overlay base.
- **Value shapes** (`disposition.schema.json $defs`): `in_data_api_exposed_schema`→`observed_bool`
  `{state:"observed",value:<bool>}`; `advisor_findings`→`observed_advisor_array`
  `{state:"observed",value:[str,…]}`; the four `consumer_evidence.*`→`consumer_evidence_dim` (observed ⇒
  `{state:"observed",found_consumers:<int≥0>,ref:<nonempty>}`, else `{state,found_consumers:null,ref:null,
  detail:<nonempty>}`).

---

## 2. Components

| # | Unit | Responsibility | Imports (new edges) |
|---|------|----------------|---------------------|
| A | `author_overlay.py` | Publish the source record; assemble → validate (consumer checks on the exact signed bytes) → signer-parity + in-memory sidecar verify → publish (atomic sidecar-first no-clobber) one overlay for one dimension. | `disposition_overlay`, `verify_census`, `disposition_signing`, `disposition_trust`, `disposition_provenance` |
| B | `verify_overlay_artifact.py` | Standalone: verify a committed overlay+sidecar against the pinned signer, its bound census (full `verify_census` acceptance), the schema/binding/target contract, `captured_at ≤ now`, and the flat OV007. | same as A |
| C | `ci/verify_committed_overlays.sh` + `overlay-evidence` job | Immutability (reject MODIFY/DELETE of committed census+overlay pairs), canonical-path + orphan-sidecar guards, exactly-one-census binding, source rehash, committed-set OV007, per-overlay verify. | (shell → B) |
| S | committed **source-evidence record** per overlay | Durable, rehashable evidence the `overlay.source_locator` points to and CI re-hashes to `source_hash`. | (data) |
| D | `OVERLAY_COLLECTION_RUNBOOK.md` | Per-dimension source/method/value/window/applicability + freshness discipline + redaction + evidence-PR. | (doc) |
| E | `CENSUS_RUNBOOK.md` corrections | PG17.6; `disposition_trust.py` anchor; current post-census sequence. | (doc) |

---

## 3. Component A — `author_overlay.py`

One overlay, one dimension, per invocation. A mechanical *binder + validator + signer + publisher*; it
does not collect evidence.

### 3.1 Inputs
- `--census` + `--census-sig` — the fresh signed census the overlay binds to.
- **Census-acceptance params** (mirroring `verify_census`, so the base is fully accepted, not just
  signature-checked): `--expect-project-ref`, `--expect-database`, `--expect-schemas`,
  `--expect-census-repo-sha`, `--require-role-markers`, `--expect-query-bundle-sha256`.
- `--key-id` + `--keys-dir` — the pinned signer (public anchor).
- `--input <overlay-core.json>` — operator **semantics only**: `{dimension, assignments:[{object_id,
  value}…], observation_window, authority, collection_method, [operator_identity], [attestation_ref]}`.
- `--source-file <path>` **xor** `--source-hash-na-reason <str>` — the source-evidence record content (→
  published as the committed source record, §S) or the NA reason. With the NA reason,
  `--source-custody-locator <str>` is **required** (and forbidden otherwise): the operator-supplied
  out-of-band authority/custody reference the tool emits as `source_locator` — operator *semantics*, like
  `authority`, not a computed binding (`AO004` covers all three exclusivity violations).
- `--producing-repo-sha-na-reason <str>` — for FORBIDDEN dims and the null case of the CONDITIONAL dim.
- `--expect-gate-repo-sha <sha>` — **REQUIRED (D4)**: the author's own merged-main HEAD; asserted with a
  clean-worktree check before the signing key or any evidence input is read (no runtime bypass; tests patch
  `disposition_provenance`).
- `--out` / `--sig-out` / `--source-out` — unique publish paths (§3.5).
- `--signing-key-env DISPOSITION_SIGNING_KEY`.

### 3.2 Provenance gate FIRST (D4, mandatory, all dimensions)
Before reading the signing key or any evidence input: `git_head_sha(repo) == --expect-gate-repo-sha` AND
`git_worktree_clean(repo)`; else `AO010` and stop. This makes the author's `producing_repo_sha` (§3.3) an
ancestor of the eventual evidence-PR HEAD, so the CI's ancestor/tooling-diff assertion holds.

### 3.3 Computed binding
`base_snapshot_sha256 = sha256(census bytes)`; `disposition_schema_sha256`/`overlay_schema_sha256` from the
read-once `OverlayContract`; `project_ref = census.project_ref` (asserted `== --expect-project-ref`, else
`AO003`); `captured_at = now` (single UTC clock read, also used for the `<UTC>` path); `source_type =
DIMENSIONS[dim][1]`; `kind`/`overlay_version` constants; `source_hash = sha256(published source-record
bytes)` (or null+reason); `source_locator` = the published source record's path **relative to the
schema-placement directory** (the literal `evidence/source/overlay-…` value; §S — one explicit base, used
identically by author and CI).
**`producing_repo_sha` = the AUTHOR's `--expect-gate-repo-sha` (schema-pub clean merged-main HEAD)** for
REQUIRED dims — NOT the external scanned-repo commit (that lives in the source record, §S). FORBIDDEN dims:
`null` + reason. CONDITIONAL (`external_clients`): the author's HEAD if a repo-committed inventory backed it,
else `null` + reason.

### 3.4 Census acceptance (not just signature)
`resolve_pinned_key` → `verify_detached_with_key(census_bytes, census_sig, signer.public_key)` (else
`AO001`), then parse the verified bytes with **`verify_census.load_snapshot_from_bytes`** (the census
gate's own dup-key/non-finite-rejecting parse — sig-before-parse, never a bare `json.loads`) and **run the
full `verify_census.check_census`** with the §3.1 census-acceptance params. Any `CN0xx` → `AO011` (prints
the underlying `CN0xx`) and stop. You cannot author against a forged **or** out-of-scope/malformed census.

### 3.5 Assemble → validate the SIGNED BYTES → signer-parity → publish
Assemble the doc; serialize canonically (`json.dumps(doc, indent=2, sort_keys=True).encode()`) → the
**signed message**. Validate by round-tripping the *serialized bytes*: `parse_overlay(message)` (exercises
the dup-key/non-finite guard) → `validate_overlay` (OV008) → `check_binding` (OV002/003/020) →
`check_observation_window` (OV009) → **`captured_at ≤ now`** (OV010 future-half) → `check_target`
(OV004/005/006/012/013/014/019) with the census `rel_index` → **flat OV007** over this overlay's
assignments (intra-overlay dup). Any code → `AO005` (prints the underlying `OV0xx`) and refuse to sign.
**Signer-parity:** load the private key; assert `public_key_fingerprint(key.public_key()) ==
signer.spki_sha256` (else `AO007` — the env key is not the pinned signer); build the sidecar
(`sidecar_bytes = json.dumps(build_sig_sidecar(message, key), indent=2, sort_keys=True).encode()`);
**verify the sidecar in-memory** (`verify_sidecar_bytes_with_key(message, sidecar_bytes, signer.public_key)`)
before writing anything (else `AO012`). Publish **source-record first (when `--source-file` was given),
then sidecar, then overlay**, each atomic + no-clobber (temp+fsync+`os.link`, with `finally` temp-unlink).
In the `--source-hash-na-reason` case NO source record is published (a **pair**, not a triple) and
`source_locator` names the out-of-band authority/custody locator instead of a path. Refuse up front if any
target path exists. The signer-parity/fingerprint comparison is an **explicit coded check** (never a bare
Python `assert`, which `-O` strips), and an unset/invalid/unloadable key PEM is reported value-silently
(the PEM content never appears in any message — same discipline as `AO009`).

### 3.6 Naming
`evidence/overlay-<dim-slug>-<census12>-<UTC>.json` (+ `.json.sig`); source record
`evidence/source/overlay-<dim-slug>-<census12>-<UTC>.source.<ext>`. `<dim-slug>` = dimension with `.`→`_`;
`<census12>` = first 12 hex of `base_snapshot_sha256`; `<UTC>` = `captured_at` as `YYYYMMDDTHHMMSSZ` (same
clock instant as the signed `captured_at`). A same-second collision fails no-clobber (safe); a
`-NN` counter suffix is appended if needed so two legitimate same-second artifacts do not block each other.

### 3.7 Error codes (`AO0xx`)
`AO000` input unreadable; `AO001` census signature failed; `AO002` `--input` missing/typed field;
`AO003` project-ref mismatch; `AO004` source-file/NA-reason exclusivity; `AO005` assembled overlay failed a
consumer check (prints `OV0xx`); `AO006` (reserved — intra-overlay dup now surfaces via `AO005`/OV007);
`AO007` env key is a valid Ed25519 key but NOT the pinned signer (fingerprint mismatch), or unset/invalid
PEM; `AO008` publish failed / path exists; `AO009` source-file unreadable (path + type only, value-silent);
`AO010` provenance gate (dirty / HEAD ≠ `--expect-gate-repo-sha`); `AO011` base census failed
`verify_census` acceptance (prints `CN0xx`); `AO012` in-memory sidecar verify failed. Exit 0 only on a
fully published set — {source, sidecar, overlay} when a source record applies, {sidecar, overlay} in the
NA-reason case.

---

## 4. Component B — verifier + Component C — CI

### 4.1 `verify_overlay_artifact.py` (standalone)
Args: `--overlay`, `--overlay-sig`, `--census`, `--census-sig`, the census-acceptance params (§3.1),
`--key-id`, `--keys-dir`, `--expect-project-ref`. Flow: `resolve_pinned_key` → read overlay bytes once →
`verify_sidecar_bytes_with_key(overlay_bytes, sig_bytes, signer.public_key)` (OV001) → verify census sig
(same signer) → parse the census via **`verify_census.load_snapshot_from_bytes`** → **`check_census`** on
it (else `CN0xx`) → `parse_overlay` →
**`isinstance(doc, dict)` guard** (coded OV008 on a signed non-object, never a crash) → `load_overlay_contract`
→ `validate_overlay` (OV008) → **short-circuit on any schema error before binding/target** → `check_binding`
(OV002/003/020) → `check_observation_window` (OV009) → **`captured_at ≤ now`** (OV010 future-half) →
`check_target` (OV004/005/006/012/013/014/019) → **flat OV007** over the overlay's own assignments. Prints
codes; exit 0 only when clean. It is an **artifact + base-census-acceptance** gate; it does NOT run the
cluster derivation (OV011/015/016/017/018/021/022) or the manifest-staleness half of OV010 — those are
`check_disposition --mode preapply`. Stated in the docstring so a green verify is not mistaken for
evidence-readiness.

### 4.2 `ci/verify_committed_overlays.sh` + `overlay-evidence` job
`set -euo pipefail`; **`git fetch origin main` fail-closed** (a fetch failure aborts, not `|| true`);
`BASE` via **`git merge-base --all origin/main HEAD` — FAIL unless the output is exactly one line**
(empty = no base; >1 = ambiguous criss-cross; plain `merge-base` cannot detect ambiguity).

1. **Immutability (status-classification-proof).** `git diff --no-renames --name-status BASE HEAD` over
   `evidence/census-prod-*.json`, `evidence/overlay-*.json`, **`evidence/source/**`**, and every `*.sig`
   under `evidence/` → **FAIL unless every entry has status `A`** (rejects `M`, `D`, and also `T`
   (typechange), `R`/`C` (rename/copy), `U`, `B`). **`--no-renames` is REQUIRED**: git's default rename
   detection reports a rename+modify as status `R`, which a bare `--diff-filter=MD` silently ignores AND
   the step-3 `--diff-filter=A` also ignores — a git-native immutability bypass (empirically reproduced).
   With `--no-renames` a rename decomposes to `A`+`D`; the `D` fails here and the `A` side re-enters the
   step-3 added set for full re-verification. Additionally reject any **non-regular mode** anywhere under
   `evidence/` (`git ls-files -s`: mode `120000` symlink / `160000` gitlink → FAIL). *Steps 1–2 run
   UNCONDITIONALLY — before and regardless of the added-set early-exit in step 3 — so a PR that only
   tampers with existing evidence still fails.* *This also closes the same gap in the census gate (§7).*
2. **Canonical path + orphans + census uniqueness.** **Content-sniff every added file under `evidence/`
   regardless of extension or case**: attempt the strict (dup-key/non-finite-rejecting) JSON parse; skip
   bytes that don't parse; FAIL on any parsed object with `kind == "evidence_overlay"` off the canonical
   `evidence/overlay-*.json` path (no overlay hidden under `.JSON`, an extension-less name, or an "opaque"
   `evidence/source/` name). Every `evidence/overlay-*.json` must have exactly one `evidence/overlay-*.json.sig`
   and vice-versa (pairing scoped to overlay sidecars; census sidecars belong to the census gate). **FAIL
   any ADDED `evidence/census-prod-*.json` whose `sha256(bytes)` equals an already-committed census**
   (byte-identical duplicate would make every bound overlay permanently ambiguous under step 4's
   exactly-one rule while immutability forbids deleting either copy). **Source-record orphan guard
   (unconditional):** build the set of `source_locator` values from **every committed overlay at HEAD**
   with non-null `source_hash` (`git ls-files 'evidence/overlay-*.json'`); every committed regular blob
   under `evidence/source/**` must be referenced by **exactly one** such overlay — an unreferenced
   (orphan) or multiply-referenced source record FAILs. Source records exist only *per overlay* (§5), and
   because this runs before the step-3 early exit, a **source-only PR** (an added `evidence/source/**`
   record with no referencing overlay in the same HEAD) fails even when zero overlays are added.
3. **Added set.** `ADDED = git diff --no-renames --diff-filter=A --name-only BASE HEAD --
   'evidence/overlay-*.json'`; if none → exit 0 *(steps 1–2 have already run)*.
4. For each added overlay: extract `base_snapshot_sha256`; among committed `evidence/census-prod-*.json`
   find those whose `sha256(bytes)` equals it — **require exactly one** (0 → FAIL unbound; >1 → FAIL
   ambiguous). **Bind the matched census independently, mirroring `verify_committed_census.sh`:** assert
   `git merge-base --is-ancestor <census.repo_sha> HEAD` and `git diff --quiet <census.repo_sha> HEAD --
   $TOOLING`, and compute `--expect-query-bundle-sha256` from `collect_disposition.query_bundle_sha256()`
   **at HEAD** (reviewed source — never the census's self-attested value); pass pinned constants for
   `--expect-project-ref/--expect-database/--expect-schemas/--require-role-markers` (CN006/CN007 must not
   be self-referential). **Constrain then re-hash the source record:** normalize `source_locator` (reject an
   absolute path or any `..` component), require the normalized path to sit **under `evidence/source/`**
   and to be a **committed regular blob** (one of the step-1-immutability-protected files; symlink/gitlink
   modes already FAIL step 1) — a locator naming anything else (e.g. a mutable non-glob `evidence/*.md`)
   FAILs; then assert `sha256(bytes) == source_hash` (skip only if `source_hash` is null with a reason).
   Extract `producing_repo_sha` **null-safe** (JSON null → empty string): if non-empty, assert
   ancestor-of-HEAD + `git diff --quiet <sha> HEAD -- $TOOLING`; if empty, skip (safe — the
   `verify_overlay_artifact.py` run later in this step enforces OV012 at HEAD). Run
   `verify_overlay_artifact.py` against the matched
   census + its sidecar + pinned signer + the census-acceptance params above (`--expect-census-repo-sha` =
   the matched census's `repo_sha`, made non-self-referential by the ancestor + tooling-diff binding);
   must exit 0.
5. **Committed-set OV007.** Build the flat `(dimension, object_id)` list over **every** committed overlay at
   HEAD (`git ls-files 'evidence/overlay-*.json'`, not just the added set) that binds to each census, incl.
   intra-overlay repeats; FAIL on any duplicate — mirroring `check_conflict`'s whole-cluster `all_keys`.

`TOOLING = author_overlay.py verify_overlay_artifact.py disposition_overlay.py verify_census.py
collect_disposition.py disposition_signing.py disposition_trust.py disposition_provenance.py
overlay.schema.json disposition.schema.json keys`. New `overlay-evidence` job (`fetch-depth: 0`, pinned
`uv==0.11.21`); the `suites` loop gains `test_author_overlay` + `test_verify_overlay_artifact`.

---

## 5. Component S — committed source-evidence record

Every overlay's `source_locator` is the committed source-evidence record's path **relative to the
schema-placement directory** (`evidence/source/…`; CI resolves it as `$SP/<source_locator>` from the git
root, the census gate's convention); `source_hash = sha256(that record's bytes)`, which CI re-hashes
(§4.2 step 4). In the null-`source_hash` (+reason) case no record is committed and `source_locator` names
the out-of-band authority/custody locator instead. The
record carries the dimension, the (redacted where sensitive) evidence, and — for `consumer_evidence.static_repo`
scans — an explicit enumeration of **every scanned repository root + its exact commit SHA** (a single
`producing_repo_sha`, being the author's schema-pub HEAD, does NOT stand in for multiple external repos).
For `consumer_evidence.runtime_logs` and any raw-secret source, the committed record is a **normalized,
redacted extract**; the record documents that the raw un-redacted source is held in **separate custody**
(not committed) with a custody reference. The author publishes this record no-clobber alongside the overlay
(§3.5), so CI can reproduce `source_hash` and confirm `source_locator` without external access.

---

## 6. Component D — `OVERLAY_COLLECTION_RUNBOOK.md`

DO-NOT-RUN-until-GO. Per dimension: authoritative source, method, `value` shape, `producing_repo_sha` /
`source_hash` applicability, and the source-record content.

| Dimension (`source_type`) | Authoritative source | `value` shape | `producing_repo_sha` | source record → `source_hash` |
|---|---|---|---|---|
| `in_data_api_exposed_schema` (`platform_config`) | Data-API **exposed-schemas platform config** (declared, not the `pgrst.db_schemas` GUC) | `observed_bool` | REQUIRED = author schema-pub HEAD | committed config export |
| `advisor_findings` (`advisor_api`) | Supabase **advisor API** | `observed_advisor_array` | FORBIDDEN → null+reason | committed advisor JSON |
| `consumer_evidence.static_repo` (`repository_scan`) | **Static scan** of platform repos | `consumer_evidence_dim` | REQUIRED = author schema-pub HEAD | scan output **+ enumerated {repo_root, commit_sha}** |
| `consumer_evidence.runtime_logs` (`runtime_logs`) | Production **query/pg logs** | `consumer_evidence_dim` | FORBIDDEN → null+reason | **redacted** log extract (+ raw custody note) |
| `consumer_evidence.external_clients` (`external_client_inventory`) | External API-client inventory | `consumer_evidence_dim` | CONDITIONAL (author HEAD if repo-committed; else null+reason) | committed inventory |
| `consumer_evidence.operator_declaration` (`operator_declaration`) | Signed **operator attestation** (+ `operator_identity`, `attestation_ref`) | `consumer_evidence_dim` | FORBIDDEN → null+reason | committed attestation (or null+reason) |

**Window + freshness discipline (so preapply is satisfiable).** Per-overlay: `started < ended ≤ captured`
and `ended ≤ now` (OV009) + `captured ≤ now` (OV010 future-half; the verifier now enforces this). At
preapply the consumer window is `S=max(started), E=min(ended)` across the *observed* consumer overlays and
must be non-empty (OV011), bracket the fixed past `base_observed_at` i.e. `S ≤ observed_at ≤ E` (OV017), be
fresh (OV016), and — for a `not_applicable`-waiver **delete** — the observed-**false**
`in_data_api_exposed_schema` window must cover `[S,E]` (OV022). **OV016 is measured at preapply `now`
against `E = min(ended)` — the earliest-ending consumer window, not `captured_at`** — so the runbook directs
operators to collect all consumer evidence for a cluster-source relation close together, bracket the census
instant, and **run the cluster gate within `--max-consumer-evidence-age-hours` of the earliest window's
`ended_at`**, recommending the intended value up front. Redaction + evidence-PR: artifacts produced
out-of-tree, secret-scanned/redacted, then committed via a governed evidence PR whose `overlay-evidence` CI
re-verifies everything.

---

## 7. Component E — `CENSUS_RUNBOOK.md` corrections (grounded)

1. **PG16 → PG17.6** (committed census `server_version` = `PostgreSQL 17.6 … 170006`).
2. **Trust anchor**: "TRUSTED_SIGNERS in `verify_census.py`" → "the `TRUSTED_SIGNERS` source constant in
   **`disposition_trust.py`** (shared; `verify_census` and `check_disposition` both `resolve_pinned_key`)."
3. **Post-census sequence**: the signed-overlay **consumer** is merged; next is **overlay publication
   tooling → fresh census → definer-view reconciliation → collect+sign the six overlays (`author_overlay.py`
   bound to the fresh census, each with a committed source record) → formal cluster gate (`check_disposition
   --mode preapply`) → apply runner**, each operator-gated.
4. **Census immutability note**: the new `overlay-evidence` CI also rejects MODIFY/DELETE of committed
   `census-prod-*.json` / `.sig` (§4.2 step 1), closing the census gate's `--diff-filter=A`-only weakness.

---

## 8. Data flow

Fresh signed census (committed) → operator collects raw evidence per dimension (runbook) → `author_overlay.py`
(provenance gate → full census acceptance → bind → validate signed bytes → signer-parity → publish
{source, sidecar, overlay}) → operator `verify_overlay_artifact.py` locally → commit the triples on an
evidence branch → `overlay-evidence` CI (immutability, canonical-path/orphans, exactly-one-census, source
rehash, per-overlay verify, committed-set OV007) → (Phase 11) `check_disposition --mode preapply` derives
windows and runs the cluster gate.

---

## 9. Fail-closed posture

Stable codes, non-zero exits, never a stack trace: `AO0xx` (author), `OV0xx`/`CN0xx` (verifier), explicit
`FAIL:` lines (CI). The author refuses to sign a doc failing any per-artifact/census check; verifies the
sidecar in-memory before writing; and is value-silent on key **and** source content. The verifier verifies
signatures before parsing and fails-closed on non-object/schema-invalid input. CI fails on modified/deleted
evidence (**including committed source records**), an unbound/ambiguous census, a mismatched source hash,
tooling drift, an untrusted signer, an orphan sidecar, an off-path overlay, or a committed-set duplicate —
with the immutability + canonical-path steps running unconditionally, before any added-set early exit.

---

## 10. Why the schemas stay frozen

Every overlay field the contract requires is computed and injected; the contract already models the
optional NA-reasons, `operator_identity`, `attestation_ref`, and fixes `source_type`/`value` per dimension.
`source_locator` is an existing free string this packet *defines* semantically (schema-placement-relative
record path, or the operator-supplied custody locator in the NA case — see Global Constraints; not a
schema change). A schema edit would break the merged consumer's `overlay_sha256` binding (OV020) and every
downstream hash. **No schema edit.**

---

## 11. Testing strategy (negative-contract-first)

TDD, negatives first. Coverage matrix (each row → a failing test before code):

| Negative case | Enforced by | Code / mechanism |
|---|---|---|
| tampered overlay/census bytes | verifier/CI signature | OV001 |
| wrong base hash | verifier/CI binding | OV002 |
| wrong project | author/verifier | AO003/OV003 |
| schema drift | verifier/CI binding | OV020 (+OV008) |
| incoherent window (`started≥ended`, `ended>captured`, future `ended`) | author/verifier | OV009 |
| **future `captured_at`** (ended≤now) | author/verifier | **OV010 future-half (`captured_at ≤ now`)** |
| **base census out-of-scope / malformed / query-failed / count-mismatch** | author/verifier/CI | **full `verify_census.check_census` (CN0xx)** |
| **signing key ≠ pinned signer** | author | **AO007 fingerprint mismatch** |
| **in-memory sidecar fails to verify** | author | **AO012** |
| **dirty / wrong-HEAD author checkout** | author | **AO010** |
| signed **non-object** / schema-invalid committed overlay | verifier/CI | **OV008 (isinstance-guard, no crash)** |
| duplicate `(dimension,object_id)` intra-overlay | author/verifier/CI | flat OV007 |
| duplicate vs an **already-committed** overlay (same census) | CI | **committed-set OV007** |
| **modified/deleted** committed census, overlay, sidecar, **or source record** | CI | **`--no-renames --name-status`, all-`A` FAIL (unconditional, pre-early-exit)** |
| **rename+modify (status `R`) / typechange (`T`) of committed evidence** | CI | **`--no-renames` decomposition + non-`A` status FAIL (empirically pinned)** |
| **symlink/gitlink under `evidence/`** | CI | **`git ls-files -s` mode FAIL** |
| **orphan sidecar / off-canonical-path overlay (incl. `.JSON`/extension-less/under `evidence/source/`)** | CI | **content-sniff + path FAIL** |
| **byte-identical duplicate census added** | CI | **census-uniqueness FAIL** |
| **`source_locator` rehash ≠ `source_hash`** | CI | **source-record FAIL** |
| **traversal / absolute / outside-`evidence/source/` / non-regular `source_locator`** | CI | **locator-constraint FAIL** |
| **orphan / multiply-referenced source record (incl. a source-only PR)** | CI | **source-orphan guard FAIL (unconditional; test `source_record_without_overlay_fails`)** |
| **self-referential census binding** (CN006/CN007 fed from the census itself) | CI | **ancestor + tooling-diff + HEAD-computed bundle** |
| overlay bound to **0 or >1** committed census | CI | **exactly-one FAIL** |
| **null `producing_repo_sha`** on a FORBIDDEN dim | CI | **null-safe skip (no shell abort)** |
| tooling drift (SHA-bearing dims) | CI | `git diff --quiet <producing_repo_sha> HEAD -- $TOOLING` |
| source-file unreadable | author | AO009 (value-silent) |

Each suite is a script `__main__` runner with synthetic Ed25519 keys + fixtures (no prod key, no DB). The
`author_overlay`/`verify_overlay_artifact` suites join the `suites` loop; the CI script is exercised by a
shell dry-run fixture (added/modified/deleted/orphan/off-path cases).

---

## 12. What this design explicitly does NOT do (holds intact)

No evidence collected, no overlay signed with the production key, no census run, no DB touched, no schema
changed, nothing pushed, no PR opened, no cluster assembled, no production action. Tooling + runbooks +
source-record format only. Phases 4 (build), 5 (PR), 6+ (census, reconciliation, collection, cluster,
apply) each remain HELD behind their own explicit GO.
