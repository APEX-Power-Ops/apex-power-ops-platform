# Signed Evidence Overlays — Design (rev 3)

> Design spec (spec only). No implementation, no evidence collection, no database access, no production write in this packet. A1–A3, migrations, the apply runner, and all production mutations remain HELD.
>
> **rev 2** folded the ratified round-1 cross-engine IRP: the checker is an **evidence-readiness** gate (not authorization); recency floor + temporal-coherence bound; fail-closed defaults; overlay/receipt binding. **rev 3 (2026-07-11)** folds the round-2 re-audit: reconciles the one residual HIGH (rev-2 pinned the derived window to `E == base_observed_at` by keeping SP009's `<= observed_at` *and* adding OV017) via a **deliberate SP009 gate change** (§3), and settles `max_consumer_evidence_age_hours` as a required CLI flag (§3). IRP record (both rounds): `evidence/irp-cross-engine-overlay-35755d69.md`.

**Goal:** Let the six `not_observed` evidence dimensions of the immutable, signed production census be resolved by separately-signed *overlay* documents — each bound to the census by its byte-hash and verified against the same pinned Ed25519 trust anchor — so a disposition cluster can reach **evidence readiness** at the `check_disposition` preapply gate without ever mutating, re-signing, or re-emitting the census. A GREEN checker attests *evidence readiness*, **not** permission to execute DDL (see §2A).

**Architecture:** Overlays are standalone signed JSON artifacts (one detached `.sig` sidecar each). `check_disposition.py` gains an overlay loader that, at preapply, verifies each overlay's signature and bindings, rejects any conflict/duplicate/unknown-target/base-mismatch/stale-or-incoherent-window, then builds an **in-memory effective evidence view** (a deep copy of the census with the six dimensions resolved and a *checker-derived* consumer observation window) that the existing semantic gate validates. The census file and its signature are never altered; no "combined census" is ever serialized. The overlay contract lives in a new sibling `overlay.schema.json` that `$ref`s the frozen `disposition.schema.json` typed `$defs` through an explicit **offline, no-retrieve** schema registry.

**Grounding (verified against the merged census `@7c9a97ca`, re-verified against `check_disposition.py` during the IRP):**
- Base census: `infra/database/schema-placement/evidence/census-prod-20260711T215509Z.json`, **118 relations** (75 tables + 43 views), all in `public`, project `fxoyniqnrlkxfligbxmg`.
- **Base snapshot SHA-256 = `5bb4191fea584f4cecf111c718382bc3f6d0d88707a7c6e9c4c5065132ac416e`** = `sha256(raw census file bytes)` = the exact bytes the census `.sig` sidecar signs.
- **31 security-definer views** (Appendix A): 29 `v_*`/`vw_*` + the two Packet-01b/6b exceptions `public.mcp_job_run_summary_v`, `public.mcp_task_packet_summary_v`.
- The six `not_observed` dimensions on every relation, in three typed shapes; `consumer_evidence.database_deps` is already `observed` and is **not** an overlay target.

---

## 1. Why overlays (problem statement)

The census collector deliberately emits six dimensions as `not_observed` (not knowable from a read-only SQL catalog scan — see `collect_disposition.py`):

| # | Dimension (permitted field path) | Census typed shape (`disposition.schema.json $defs`) | Evidence authority |
|---|---|---|---|
| 1 | `in_data_api_exposed_schema` | `observed_bool` | platform Data-API config |
| 2 | `advisor_findings` | `observed_advisor_array` | Supabase advisor API |
| 3 | `consumer_evidence.static_repo` | `consumer_evidence_dim` | repository scan |
| 4 | `consumer_evidence.runtime_logs` | `consumer_evidence_dim` | runtime log query |
| 5 | `consumer_evidence.external_clients` | `consumer_evidence_dim` | external-client inventory |
| 6 | `consumer_evidence.operator_declaration` | `consumer_evidence_dim` | operator attestation |

Until these are resolved, the `check_disposition` preapply gate **withholds evidence readiness** for a destructive/promote/compat/archive/harden action and rejects the raw census: `SP009` (zero-width `consumer_evidence.observation_window`), `SP010` (`required_observations` must be freshly `observed`), `SP022`/`SP013` (resolved consumer conclusion needs every consumer dim `observed`/`not_applicable`, `database_deps` observed, count agreement), `SP027` (delete floor). Today `check_disposition` verifies the *snapshot* signature (SP026) but has no way to accept later-collected evidence. Overlays are that mechanism — without weakening any existing gate and without touching the signed census.

## 2. Invariants (non-negotiable)

1. **Census immutability.** The census JSON bytes and its `.sig` are read-only inputs. Overlays never modify, re-sign, replace, or re-emit them.
2. **In-memory merge only.** The effective evidence view exists only for the duration of a gate run. The checker never writes a "combined census" or any merged artifact to disk; the receipt records overlay *provenance*, not merged evidence bodies.
3. **Six dimensions only.** An overlay may resolve only the six field paths in §1. Any assignment to a catalog fact, to `database_deps`, to `observation_window`, or to any other field is rejected (`OV004`). The single exception is the *checker itself* deriving-and-writing `consumer_evidence.observation_window` in the effective view (§3) — that is a checker action, never an overlay assignment.
4. **Resolve, don't overwrite.** An overlay assignment is valid only where the base census slot for `(object_id, dimension)` is currently `not_observed`. Targeting an already-`observed`/`not_applicable`/`query_failed`/`stale` slot is rejected (`OV006`). (Today all six dims are `not_observed` on all 118 relations; `query_failed`/`stale` are reserved and also non-overlayable.)
5. **Bound to this census.** Every overlay binds the base snapshot byte-hash and the project ref; a mismatch is rejected (`OV002`/`OV003`). The literal hash lives in overlay *instances*, never in the schema contract (the schema constrains a 64-hex pattern so future censuses bind their own hashes).
6. **Signed bytes are the unit of evidence integrity.** The Ed25519 detached signature is verified over the **exact raw overlay bytes** against the pinned `TRUSTED_SIGNERS` anchor and `keys/` (the `disposition_trust` / `disposition_signing` path SP026 established). A signature proves *artifact integrity* only — never authorization (see §2A).
7. **Fail closed.** Every ambiguous, missing, non-finite, or unresolvable condition is a coded reject, never a silent pass and never an uncaught exception.

## 2A. Control separation (the checker does NOT authorize execution)

A GREEN `check_disposition` result establishes **evidence readiness**, not permission to mutate production. Three distinct controls gate a destructive action, and this packet implements only the first two:

1. **Overlay signature → evidence integrity.** The overlay bytes are authentic and unmodified. (This packet.)
2. **Cluster-manifest TA approval → technical acceptance.** `cluster_manifest.status == accepted` + non-empty `technical_authority_approval` (SP018). Technical sign-off that the disposition is correct. (Existing gate.)
3. **Apply-runner per-action operator write-GO → execution authorization.** An explicit, per-action operator authorization bound to *target project + action_class + manifest hash + gate-receipt hash + exact migration-SQL hash + expiry/nonce*, issued at apply time. **Out of scope here — a future apply-runner packet.** Until it exists, **no DELETE (or any prod mutation) can execute**, regardless of a GREEN checker.

Consequences enforced by this spec:
- `operator_declaration` is an **evidence** dimension (the operator attests to observed consumer facts), **not** an authorization. Its `operator_identity` + `attestation_ref` are preserved as **provenance** in the overlay and the gate receipt, and are consumed by **no** authorization decision in the checker.
- Possession of the single census signing key confers evidence-integrity ability only. **A signer holding every valid overlay still cannot produce an execution-authorized DELETE receipt** — the receipt carries no write-GO and is not an authorization token. (§5 step 10.)
- No second signing key and no approval-registry are introduced in this packet; per-action authorization is deferred to the apply-runner design.

## 3. Time model (corrected) and the derived consumer window

Three timestamps are kept strictly separate:
- **`base_observed_at`** — the census `observed_at`. Immutable. `SP008` (base-census freshness vs `--now` / `max_staleness_hours`) continues to check *this*, unchanged. A stale base census still demands a fresh signed census before preapply.
- **`overlay.captured_at`** — when an overlay artifact was completed. Each overlay's freshness is checked independently against *its own* `captured_at` (`OV010`), never against `base_observed_at`.
- **`overlay.observation_window` `{started_at, ended_at}`** — the genuine interval the evidence source covers. Per-overlay; the four consumer sources legitimately carry *different* intervals.

**Checker-derived consumer window.** For each relation, the checker derives the effective `consumer_evidence.observation_window` from the consumer-dimension overlays that resolve that relation with `state = observed` ("contributors"), and writes it into the effective view (invariant 3's carve-out). Let `C` = the set of contributing overlays for the relation, `S = max(startedᵢ)`, `E = min(endedᵢ)`. The derivation is rejected (fail-closed) unless the full predicate holds:

```
C is non-empty                                   # else OV018 (zero contributors)
S < E                                            # else OV011 (empty intersection)
E <= min(capturedᵢ over C)                        # documented sanity/defense assert*
E <= now                                         # else OV009 (future window)
now - E <= max_consumer_evidence_age_hours        # else OV016 (stale evidence) — RECENCY FLOOR
S <= base_observed_at <= E                         # else OV017 (temporal incoherence)
```
`* E <= min(capturedᵢ)` is algebraically implied by `OV009`'s per-overlay `endedᵢ <= capturedᵢ`; it is retained as an explicit defense-in-depth assert, **not** as the recency safeguard (the real recency safeguard is `now - E <= max_consumer_evidence_age_hours`).

- `max_consumer_evidence_age_hours` is a **finite, positive** bound supplied as a **REQUIRED CLI flag** `--max-consumer-evidence-age-hours` (NOT a `cluster_manifest` field — that schema is `additionalProperties:false` and frozen here, so a new field would fail SP001). Unlike the host `max_staleness_hours`/`minimum_consumer_window_hours` skip-on-absence convention, an **absent or non-finite value is a coded reject** (`OV016` fires closed), per Invariant 7. It is recorded in the receipt so the apply-runner revalidates the identical recency policy.
- The `S <= base_observed_at <= E` clause makes the catalog-anchored `database_deps` (observed at `base_observed_at`) temporally coherent with the overlaid consumer evidence — closing the "decade-old window authorizes a delete" hole. `database_deps` stays anchored at `base_observed_at` and is *not* re-windowed; it must fall inside the derived window.
- A relation with a `not_applicable` consumer dimension: that dimension contributes no interval. A relation with **no** observed consumer contributor fails `OV018` (never a silent pass).

**Division of labor (resolves the un-plumbable-`captured_at` and silent-pass hazards):**
- **At merge (overlay loader, OV codes):** build + validate the derived window with the full predicate above (uses `capturedᵢ` + `base_observed_at`, which are available at merge but not in the effective window struct). Write `{S,E}` into the effective view.
- **At the semantic gate (`SP009` on the effective view):** ordering `S < E` and duration `(E−S)/3600 >= minimum_consumer_window_hours`, plus `SP027`'s DELETE-only `>= 720h`. **Deliberate gate change:** SP009's current upper bound `e <= observed_at` (written for the census's own zero-width self-window) is **removed for the overlaid consumer window** — a legitimate later-collected window ends *after* `base_observed_at`, so keeping `e <= observed_at` alongside `OV017` (`S <= base_observed_at <= E`) would pin `E == base_observed_at` and the gate could never go green (the round-2 residual HIGH). The census anchor instead comes from the merge-time `OV017` + recency `OV016` + `E <= min(capturedᵢ)`/`E <= now`. This is safe: a non-overlaid relation's window is the zero-width census default and still fails `S < E` closed, and a non-zero window can only arise from a merge-validated overlay or the forge-proof signed census — so removing the bound opens no bypass. The duration floor (rev-1 dropped it) is retained. Because the merge already rejects a stale/incoherent/zero-contributor window, SP009 on the effective view can never see a cleared or out-of-range window.

## 4. Overlay document contract

One overlay resolves **exactly one** dimension (§1) across one or more census object IDs.

```jsonc
{
  "kind": "evidence_overlay",
  "overlay_version": "1",
  "dimension": "consumer_evidence.static_repo",   // one of the 6 permitted field paths
  "source_type": "repository_scan",               // typed; fixed per dimension (Appendix B)
  "authority": "apex-power-ops-platform repository history",
  "collection_method": "ripgrep symbol scan over tracked sources",
  "source_locator": "git:apex-power-ops-platform@<sha>:/",
  "source_hash": "<sha256 of the evidence bundle, or null>",
  "source_hash_not_applicable_reason": "<string, required iff source_hash is null>",

  "base_snapshot_sha256": "5bb4191f…",            // == sha256(census file bytes)
  "disposition_schema_sha256": "<sha256 of the on-disk disposition.schema.json bytes>",
  "overlay_schema_sha256": "<sha256 of the on-disk overlay.schema.json bytes>",
  "project_ref": "fxoyniqnrlkxfligbxmg",
  "captured_at": "2026-07-14T18:03:00+00:00",
  "observation_window": { "started_at": "…", "ended_at": "…" },

  "producing_repo_sha": "<40-hex or null>",
  "producing_repo_sha_not_applicable_reason": "<string, required iff producing_repo_sha is null>",

  // operator_declaration dimension ONLY (PROVENANCE, not authorization — §2A):
  "operator_identity": "<string>",
  "attestation_ref": "<string>",

  "assignments": [
    { "object_id": "public.v_scope_financials",
      "value": { "state": "observed", "found_consumers": 0, "ref": "scan:2026-07-14" } }
  ]
}
```

- **`assignments[].value`** is exactly the census typed wrapper for that dimension (`observed_bool` / `observed_advisor_array` / `consumer_evidence_dim`), reused by `$ref` — so `state`/`value`/`detail` and the `observed_state_rule` are enforced identically to the census (`OV008`). Intra-file `(object_id)` uniqueness is enforced by the **`OV007` loader counter**, not JSON-Schema `uniqueItems` (which compares whole array items and would miss a same-`object_id` different-`value` pair); `OV007` counts duplicates within *and* across overlays.
- **`source_hash`** binds the evidence bundle; when a live source has no fixed bundle (e.g. an advisor-API pull), it is `null` **and** `source_hash_not_applicable_reason` is required (`OV019`).
- **`disposition_schema_sha256` / `overlay_schema_sha256`** pin the exact schema bytes the overlay was authored against (drift guard, §D5); the loader rejects a mismatch (`OV020`).
- **`operator_identity` / `attestation_ref`** (operator_declaration only) are **provenance**, echoed into the receipt; no gate consumes them as authorization (§2A).

### `overlay.schema.json` (sibling contract)

- New file `infra/database/schema-placement/overlay.schema.json` with its own `$id` and a `version`.
- It `$ref`s the frozen `disposition.schema.json` typed `$defs` (`observed_bool`, `observed_advisor_array`, `consumer_evidence_dim`, `object_id`, `iso_datetime`, `nonempty_string`) through the disposition schema's **absolute `$id`**.
- **`disposition.schema.json` is not modified in this packet.**
- Schema loading uses an explicit local `referencing.Registry` seeded with **both** schema documents by `$id`, built **without a retrieve callback** so remote/network resolution is impossible; an unresolvable/missing resource is **caught and mapped to a coded `OV008` reject** (never an uncaught `referencing.Unresolvable`). The validator uses the rfc3339 `FormatChecker` (parity with `check_disposition`/`verify_census`), and a `RefResolver`-based path is prohibited.
- Per-dimension shape is enforced by `oneOf`/`if-then` over `dimension` → allowed `source_type` + `assignments[].value` `$ref` + `producing_repo_sha`/`source_hash` applicability + (for `operator_declaration`) required `operator_identity`/`attestation_ref`.

## 5. Load → verify → merge algorithm (`check_disposition` preapply)

New repeatable input: **`--overlay PATH`** (each with a detached `PATH.sig` sidecar, resolved fail-closed). Overlays are consumed only in `preapply`. Sequence, entirely offline:

0. **SP028 checkout gate first.** The checkout-provenance gate (bound vs authoring opt-in) runs **before any census, overlay, or sidecar bytes are read** — unchanged from SP026/SP028, now explicitly *step zero* ahead of all overlay reads.
1. **Read once.** Read the census bytes and each overlay's raw bytes and each sidecar exactly once into in-hand buffers.
2. **Verify signatures over the exact in-hand bytes** — census (SP026, unchanged) and every overlay: detached Ed25519 over the exact raw overlay buffer, via `disposition_trust.resolve_pinned_key(--key-id)` + `disposition_signing.verify_sidecar_bytes_with_key` (`OV001`). Same pinned anchor, no caller-supplied key.
3. **Parse from the verified buffer.** Schema-validate and later merge each overlay by parsing the **same in-hand verified bytes** (never a re-read) — closing the verify-then-reparse TOCTOU (`OV008` on schema/registry/format failure, coded).
4. **Bind** each overlay: `base_snapshot_sha256 == sha256(census bytes)` (`OV002`); `project_ref == census.project_ref == --expect-project-ref` (`OV003`); `disposition_schema_sha256`/`overlay_schema_sha256` == the on-disk schema bytes (`OV020`).
5. **Freshness (finite-guarded).** `captured_at` not future, and no staler than the manifest's existing `max_staleness_hours` (reused as the per-overlay `captured_at` bound; `_finite()`-guarded) (`OV010`). Each `observation_window` well-formed, `started_at < ended_at`, `ended_at <= captured_at`, not future (`OV009`).
6. **Authorize the assignment target** (validation, not execution-authorization): `dimension` is one of the six (`OV004`); not `observation_window`/catalog/`database_deps` (`OV004`); `source_type` matches the dimension's fixed mapping (`OV013`); `object_id` exists in the census (`OV005`); the base slot is `not_observed` (`OV006`); `producing_repo_sha`/`source_hash` applicability satisfied (`OV012`/`OV019`); `operator_declaration` carries `operator_identity`+`attestation_ref` provenance (`OV014`).
7. **Conflict/duplicate** — no `(dimension, object_id)` pair assigned more than once across **or within** overlays, even if values are identical (`OV007`).
8. **Build the effective view** — `copy.deepcopy` the parsed census; set each resolved dimension value; for each **cluster-source relation under a resolved/delete conclusion** (the relations for which the gate requires a consumer window) derive-and-write the consumer window per the §3 predicate as **ISO-8601 strings** (`OV011`/`OV016`/`OV017`/`OV018`). `OV018` fires only for such a relation with zero observed contributors; non-cluster/non-overlaid relations keep their zero-width census default (still fail `SP009` closed) and are not over-rejected. The parsed base census object is never mutated.
9. **Run the existing semantic gate** (`semantic_check`, SP001–SP027) against the **effective** view — preceded by a re-`schema_validate` of the merged effective view against `disposition.schema.json` (the effective view is a census) **with the rfc3339 `FormatChecker`**, so a merged datetime cannot reach an unguarded `parse_dt`. SP009 runs with its upper bound relaxed per §3 (ordering + duration); SP027 (delete floor incl. 720h) unchanged; both now see a valid derived window. `observed_at` is never overwritten; the effective view is never serialized.
10. **Receipt (evidence readiness, NOT authorization).** Records, per overlay: `path`, raw-bytes `sha256`, `.sig` `sha256`, `signer`, `dimension`, covered object-id count, `captured_at`, `producing_repo_sha`, `source_hash`, and (for operator_declaration) `operator_identity`/`attestation_ref` as provenance; plus `disposition_schema_sha256`/`overlay_schema_sha256`, the recency policy `max_consumer_evidence_age_hours` (so the apply-runner revalidates the identical bound), and `effective_view: {in_memory_only: true}`, alongside the SP026 signer/`snapshot_signature_sha256`/gate fields. The receipt carries **no write-GO and is not an authorization token**; a GREEN receipt attests evidence readiness only (§2A).

The collector never imports the overlay loader; the checker never imports the collector (SP026's dependency discipline preserved).

## 6. Reject matrix (overlay codes `OV0xx`)

| Code | Rejects |
|---|---|
| OV001 | overlay signature missing or fails against the pinned signer (exact raw bytes) |
| OV002 | `base_snapshot_sha256` != the supplied census file byte-hash |
| OV003 | `project_ref` mismatch (overlay vs census vs `--expect-project-ref`) |
| OV004 | `dimension` not one of the six permitted paths (catalog / `database_deps` / `observation_window` / other) |
| OV005 | assignment `object_id` absent from the census |
| OV006 | target base slot is not `not_observed` (attempt to replace a resolved/failed/stale fact) |
| OV007 | duplicate/conflicting `(dimension, object_id)` — across **or within** overlays, even if values agree |
| OV008 | value/schema violation, incl. registry-unresolvable or format failure mapped to a coded reject (never uncaught) |
| OV009 | `observation_window` malformed, `started_at >= ended_at`, `ended_at > captured_at`, or future |
| OV010 | overlay `captured_at` future, or staler than the manifest `max_staleness_hours` (finite-guarded) |
| OV011 | derived consumer window empty (`S >= E`; non-intersecting source windows) |
| OV012 | `producing_repo_sha` required-but-absent, or null without reason |
| OV013 | `source_type` does not match the dimension's fixed mapping |
| OV014 | `operator_declaration` overlay missing `operator_identity` or `attestation_ref` provenance |
| OV015 | partial cluster coverage — a cluster relation lacks a *permitted-overlay-target, base-`not_observed`* gate-required dimension (§8; already-observed `database_deps` counts as satisfied) |
| OV016 | consumer window stale: `now - E > max_consumer_evidence_age_hours` (required CLI flag; **absent or non-finite value also `OV016`**, fail-closed) |
| OV017 | temporal incoherence: `base_observed_at` not within the derived window `[S, E]` |
| OV018 | zero contributing observed consumer overlays for a cluster-source relation that requires a consumer window (resolved/delete conclusion; fail-closed) |
| OV019 | `source_hash` is null without `source_hash_not_applicable_reason` |
| OV020 | overlay `disposition_schema_sha256`/`overlay_schema_sha256` != on-disk schema bytes (drift) |

`SP008` unchanged (base-census freshness). `SP009` retains ordering **and** duration on the effective view. All other `SP0xx` semantics unchanged and run against the effective view.

## 7. Signature & key handling (evidence integrity only)

- Overlays are signed/verified with the **same pinned Ed25519 anchor** as the census. No new key, no caller-supplied key, no new trust surface in this packet.
- This is **evidence integrity**, not authorization (§2A). Cross-type replay (an overlay's bytes passed as a census, or vice versa) is blocked structurally by the `kind` const + the base-hash/schema-hash binding; there is no cryptographic domain separation and none is added here (deferred with the apply-runner authorization design).
- The private signing key stays in operator/Infisical custody, never handled by the assistant; overlay *signing* is an operator-run, value-silent step (design only here).

## 8. Definer-view reconciliation & cluster admissibility

- **Appendix A** enumerates all **31** security-definer views (29 program views + the two `mcp_*` Packet-01b/6b exceptions, explicitly retained — not silently omitted).
- **Gate-required dimension** for a relation = the subset of `union(required_observations, SP022-forced-for-a-resolved-conclusion, SP027-delete-floor)` that is a **permitted overlay target and base `not_observed`** for that relation. Already-`observed` `database_deps` is **satisfied by the base census** and never demands an overlay (corrects the rev-1 OV015 that would have blocked every resolved-conclusion cluster).
- **First cluster gate.** The first disposition cluster (3–5 views) is admissible only when, for **every** relation, every gate-required dimension is overlaid so the effective view passes `SP009`/`SP010`/`SP013`/`SP022`/`SP027` with a valid, fresh, coherent window. A missing required dimension is `OV015`. `OV015` is advisory-completeness; `SP009`/`SP022`/`SP027` on the effective view remain authoritative.
- Cluster *selection* (which 3–5 views) is out of scope here and happens only after complete, fresh overlay coverage exists.

## 9. Testing strategy (negative-first)

TDD, contract tests first, all offline (no DB, no network, no signing key; throwaway fixture keys only). Required coverage:
- **Schema/registry:** valid per-dimension overlays accepted; `dimension`↔`source_type` mismatch rejected; wrong `value` shape rejected; **missing/unseeded registry resource → coded `OV008`, not an uncaught `Unresolvable`**; **remote `$ref` resolution impossible** (no retrieve callback); pattern-valid-but-calendar-invalid datetime → coded reject (FormatChecker), not a traceback.
- **Binding:** base-hash mismatch (`OV002`); project mismatch (`OV003`); schema-drift `sha256` mismatch (`OV020`); unknown object_id (`OV005`); non-`not_observed` target incl. `query_failed`/`stale` (`OV006`).
- **Conflict:** duplicate `(dimension, object_id)` across overlays and **within** one overlay, with identical values, still rejected (`OV007`).
- **Time model (adversarial):** overlay `captured_at` after `base_observed_at` **accepted**; **a fresh overlay carrying a decade-old window → `OV016`**; `S > base_observed_at` or `E < base_observed_at` (census instant outside the derived window) → `OV017`; **empty contributor set on a cluster-source relation → `OV018`** (fail-closed, not a silent pass); **absent or NaN/Inf `max_consumer_evidence_age_hours` → coded reject (`OV016`, fail-closed)**; future `captured_at` or staler than `max_staleness_hours` (`OV010`); `ended_at > captured_at` (`OV009`); empty intersection (`OV011`); a valid derived window with `ended_at` after `base_observed_at` **passes** SP009 (whose effective-view upper bound is relaxed per §3; `OV017` supplies the census anchor); SP009 duration floor still fires below `minimum_consumer_window_hours`.
- **Signature:** tampered overlay byte fails (`OV001`); **verify-then-file-swap** (verify buffer A, on-disk B) cannot occur — parse-from-verified-buffer proven; **replayed valid overlay against a DIFFERENT census → `OV002`**; census signature path (SP026) unaffected.
- **Authorization boundary (§2A):** a valid operator_declaration overlay **without** manifest TA approval does **not** reach evidence readiness (SP018 still fires); valid overlays + accepted manifest still produce a receipt that is **not** an execution authorization (no write-GO field; assert the receipt cannot be interpreted as a DELETE authorization); DELETE window `< 30d` → `SP027`.
- **Merge integrity:** census file byte-identical on disk before/after; no combined-census artifact; `observed_at` unchanged; **`copy.deepcopy` proven — a test asserts the parsed base census object is unmutated after merge** (catches shallow-copy aliasing); receipt carries overlay provenance + artifact hashes only.
- **End-to-end (fixtures):** a synthetic mini-census + per-dimension overlays drive a cluster from red (raw census fails `SP009`) to evidence-ready green (effective view passes) — throwaway keys, never the prod signer.

## 10. Out of scope / guardrails

- **No evidence collection.** Collecting each dimension's real evidence happens later, under separately-authorized read-only workflows.
- **No execution authorization here.** Per-action operator write-GO (target/action/manifest-hash/receipt-hash/SQL-hash/expiry) is the **apply-runner** packet (§2A). No DELETE or any prod mutation can execute until it exists.
- **No database access, no production write, no signing.** A1–A3, migrations, the apply runner, and all prod mutations remain HELD.
- **`disposition.schema.json` unchanged**; census evidence + signature unchanged; **no new census dimension** and no re-collection in this packet (a fresh census, when SP008 says stale, is a separate operator-gated run).
- **No cluster selection or destructive disposition** in this packet.
- Merge governance unchanged: solo-maintainer squash after green CI + cross-engine IRP, no admin bypass. Overlay tooling merges **before** any evidence is collected.

## 11. Ratified decisions & residual notes

**Rev-3** additionally folds the round-2 re-audit (same IRP record): the deliberate SP009 upper-bound relaxation for the overlaid consumer window (§3, reconciling the round-2 OV017-vs-SP009 `E == base_observed_at` pin), `max_consumer_evidence_age_hours` as a **required fail-closed CLI flag** (§3), OV010 reusing the manifest `max_staleness_hours` (§5.5), OV018 scoped to cluster-source relations (§5.8), ISO-8601 derived-window serialization + `disposition.schema.json`+FormatChecker re-validation of the effective view (§5.8–9), and the OV007-counter (not `uniqueItems`) intra-file uniqueness note (§4). Rev-2 folds the ratified round-1 corrections (record: `evidence/irp-cross-engine-overlay-35755d69.md`): D1 control-separation / evidence-readiness reframing (§2A); D2 the full derived-window predicate with recency floor + `S <= base_observed_at <= E` coherence, retained duration + 720h floors (§3); the fail-closed bundle (§2.7, §3, §5); overlay-artifact + schema-drift + provenance receipt binding (§4, §5.10); `source_hash_not_applicable_reason` (§4); OV015 correction (§8); the four Codex P2s (SP028 step 0, receipt binding, source_hash reason, OV015). Residual flags for the plan/apply stages:
- **R-1 (single-source external signal):** `external_clients` remains a single overlay-supplied signal for external/HTTP consumers; `database_deps` is DB-internal-blind. Coherence (`OV017`) + recency (`OV016`) bound its *timeliness*, not its *independence*. An independent external-consumer signal is a future census-dimension consideration (deliberately out of scope — would touch the collector + a fresh census).
- **R-2 (apply-runner re-bind):** the HELD apply runner must re-read + re-verify census + overlays from the receipt's pinned hashes (revalidate-everything) and enforce control 3 (§2A) before any SQL.
- **R-3 (ledger-time schema drift):** `disposition_schema_sha256`/`overlay_schema_sha256` bind a single run; long-term ledger evolution across schema edits is bounded per-run by these hashes + SP028 checkout pinning.

---

## Appendix A — the 31 security-definer views

Definer-view-program (29): `public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_apparatus_approval_queue`, `public.v_apparatus_resources`, `public.v_apparatus_testing_status`, `public.v_apparatus_type_resources`, `public.v_approval_queue_summary`, `public.v_equipment_current_status`, `public.v_equipment_movement_history`, `public.v_guide_image_completeness`, `public.v_image_production_queue`, `public.v_image_sourcing_summary`, `public.v_neta_test_details`, `public.v_pending_handoffs`, `public.v_project_equipment`, `public.v_projects_active`, `public.v_projects_full`, `public.v_pss_dashboard`, `public.v_scope_financials`, `public.v_scope_summary`, `public.v_tcc_calc_input`, `public.v_tcc_etu_catalog`, `public.v_tcc_etu_coefficients`, `public.v_tcc_tmt_catalog`, `public.v_tcc_tmt_curve_data`, `public.vw_etu_browse`, `public.vw_etu_calc_context`, `public.vw_sensor_calc_context`, `public.vw_trip_unit_cascade`.

Packet-01b/6b exceptions (2, explicitly retained): `public.mcp_job_run_summary_v`, `public.mcp_task_packet_summary_v`.

## Appendix B — per-dimension overlay type table

| # | `dimension` | `value` `$ref` | fixed `source_type` | `producing_repo_sha` | `source_hash` | extra |
|---|---|---|---|---|---|---|
| 1 | `in_data_api_exposed_schema` | `observed_bool` | `platform_config` | required (config repo SHA) | required or null+reason | — |
| 2 | `advisor_findings` | `observed_advisor_array` | `advisor_api` | n/a + reason | typically null + reason (live pull) | — |
| 3 | `consumer_evidence.static_repo` | `consumer_evidence_dim` | `repository_scan` | required (scanned repo SHA) | required | — |
| 4 | `consumer_evidence.runtime_logs` | `consumer_evidence_dim` | `runtime_logs` | n/a + reason | null + reason (or query-result hash) | — |
| 5 | `consumer_evidence.external_clients` | `consumer_evidence_dim` | `external_client_inventory` | conditional (repo-tracked → required, else n/a + reason) | conditional | — |
| 6 | `consumer_evidence.operator_declaration` | `consumer_evidence_dim` | `operator_declaration` | n/a + reason | null + reason | `operator_identity`, `attestation_ref` (provenance, not authz) |
