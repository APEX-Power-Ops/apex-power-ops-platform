# Signed Evidence Overlays — Design

> Design spec (spec only). No implementation, no evidence collection, no database access, no production write in this packet. A1–A3, migrations, the apply runner, and all production mutations remain HELD.

**Goal:** Let the six `not_observed` evidence dimensions of the immutable, signed production census be resolved by separately-signed *overlay* documents — each bound to the census by its byte-hash and verified against the same pinned Ed25519 trust anchor — so a disposition cluster can pass the `check_disposition` preapply gate without ever mutating, re-signing, or re-emitting the census.

**Architecture:** Overlays are standalone signed JSON artifacts (one detached `.sig` sidecar each). `check_disposition.py` gains an overlay loader that, at preapply, verifies each overlay's signature and bindings, rejects any conflict/duplicate/unknown-target/base-mismatch/stale-window, then builds an **in-memory effective evidence view** (a deep copy of the census with the six dimensions resolved and a *derived* consumer observation window) that the existing semantic gate validates. The census file and its signature are never altered; no "combined census" is ever serialized. The overlay contract lives in a new sibling `overlay.schema.json` that `$ref`s the frozen `disposition.schema.json` typed `$defs` through an explicit **offline** schema registry.

**Grounding (verified against the merged census `@7c9a97ca`):**
- Base census: `infra/database/schema-placement/evidence/census-prod-20260711T215509Z.json`, **118 relations** (75 tables + 43 views), all in `public`, project `fxoyniqnrlkxfligbxmg`.
- **Base snapshot SHA-256 = `5bb4191fea584f4cecf111c718382bc3f6d0d88707a7c6e9c4c5065132ac416e`** = `sha256(raw census file bytes)` = the exact bytes the census `.sig` sidecar signs.
- **31 security-definer views** (`is_security_definer_view` observed `true`): the 29 `v_*`/`vw_*` definer-view-program views plus the two Packet-01b/6b exceptions `public.mcp_job_run_summary_v` and `public.mcp_task_packet_summary_v` (full list in Appendix A).
- The six `not_observed` dimensions on every relation, in three typed shapes; `consumer_evidence.database_deps` is already `observed` and is **not** an overlay target.

---

## 1. Why overlays (problem statement)

The census collector deliberately emits six dimensions as `not_observed` because they are not knowable from a read-only SQL catalog scan (see `collect_disposition.py`):

| # | Dimension (permitted field path) | Census typed shape (`disposition.schema.json $defs`) | Evidence authority |
|---|---|---|---|
| 1 | `in_data_api_exposed_schema` | `observed_bool` | platform Data-API config |
| 2 | `advisor_findings` | `observed_advisor_array` | Supabase advisor API |
| 3 | `consumer_evidence.static_repo` | `consumer_evidence_dim` | repository scan |
| 4 | `consumer_evidence.runtime_logs` | `consumer_evidence_dim` | runtime log query |
| 5 | `consumer_evidence.external_clients` | `consumer_evidence_dim` | external-client inventory |
| 6 | `consumer_evidence.operator_declaration` | `consumer_evidence_dim` | operator attestation |

The `check_disposition` preapply gate **requires** these to be resolved before it will authorize a destructive/promote/compat/archive/harden action, and it will otherwise reject the raw census:
- `SP009` — the census-default zero-width `consumer_evidence.observation_window` (`started_at == ended_at == observed_at`) violates `started < ended`.
- `SP010` — a `cluster_manifest.required_observations` field must be freshly `observed` on each source relation.
- `SP022`/`SP013` — a resolved consumer conclusion needs every consumer dimension `observed`-or-`not_applicable`, `operator_declaration` observed, `database_deps` observed, with count agreement.
- `SP027` — destructive-evidence floor (`external_clients` `not_applicable` requires `in_data_api_exposed_schema` observed `false`).

Today `check_disposition` verifies the *snapshot* signature (SP026) but has no way to accept later-collected evidence. Overlays are that mechanism — without weakening any existing gate and without touching the signed census.

## 2. Invariants (non-negotiable)

1. **Census immutability.** The census JSON bytes and its `.sig` are read-only inputs. Overlays never modify, re-sign, replace, or re-emit them.
2. **In-memory merge only.** The effective evidence view exists only for the duration of a gate run. The checker never writes a "combined census" or any merged artifact to disk; the receipt records overlay *provenance*, not merged evidence bodies.
3. **Six dimensions only.** An overlay may resolve only the six field paths in §1. Any assignment to a catalog fact, to `database_deps`, or to any other field is rejected (`OV004`).
4. **Resolve, don't overwrite.** An overlay assignment is valid only where the base census slot for `(object_id, dimension)` is currently `not_observed`. Targeting an already-`observed`/`not_applicable` slot is rejected (`OV006`).
5. **Bound to this census.** Every overlay binds the base snapshot byte-hash and the project ref; a mismatch is rejected (`OV002`/`OV003`). The literal hash lives in overlay *instances*, never in the schema contract (the schema constrains a 64-hex pattern so future censuses bind their own hashes).
6. **Signed bytes are the unit of trust.** The Ed25519 detached signature is verified over the **exact raw overlay bytes** against the pinned `TRUSTED_SIGNERS` anchor and `keys/` (the same `disposition_trust` / `disposition_signing` path SP026 established). A signature proves *artifact integrity*, not human authorization.

## 3. Three time concepts (corrected model)

The design keeps three timestamps strictly separate. Conflating them is the central hazard the cross-engine review must scrutinize.

- **`base_observed_at`** — the census `observed_at`. Immutable. When the catalog was read. `SP008` (base-census freshness vs `--now` / `max_staleness_hours`) continues to check *this* and is unchanged.
- **`overlay.captured_at`** — when an overlay artifact was completed. Each overlay's freshness is checked independently against *its own* `captured_at` (`OV010`) — never against `base_observed_at`.
- **`overlay.observation_window` `{started_at, ended_at}`** — the genuine interval the evidence source actually covers (e.g. a 90-day repo-history scan). Per-overlay; the four consumer sources legitimately carry *different* intervals.

**Consumer window derivation.** For each relation, the effective `consumer_evidence.observation_window` is the **non-empty intersection** of the windows of the consumer-dimension overlays that resolve that relation with `state = observed`:

```
started_at = max(started_at of contributing observed consumer overlays for this relation)
ended_at   = min(ended_at   of contributing observed consumer overlays for this relation)
```

- Empty intersection (`started_at >= ended_at`) → reject (`OV011`).
- Overlays are **never** required to claim identical windows.
- A consumer dimension resolved as `not_applicable` contributes no interval (it has no observation).

**`SP009` under overlays (revised success condition).** After the effective view is built, `SP009` validates the *derived* consumer window with:
`started_at < ended_at` **and** `ended_at <= min(captured_at of the contributing overlays)` **and** neither bound is after `--now`.
It is validated against the contributing overlays' `captured_at`, **not** against the older `base_observed_at`. A relation whose consumer window is *not* overlaid still fails `SP009` exactly as before (the census default must be overlaid). `database_deps` retains its base-census provenance (`observed` at `base_observed_at`) and is not re-windowed; the derived window governs the four workflow dimensions. (Open item O-1 in §11: whether `database_deps` must fall inside the derived window.)

## 4. Overlay document contract

One overlay resolves **exactly one** dimension (§1) across one or more census object IDs. Fields:

```jsonc
{
  "kind": "evidence_overlay",
  "overlay_version": "1",
  "dimension": "consumer_evidence.static_repo",   // one of the 6 permitted field paths
  "source_type": "repository_scan",               // typed; fixed per dimension (Appendix B)
  "authority": "apex-power-ops-platform repository history",   // who/what vouches
  "collection_method": "ripgrep symbol scan over tracked sources", // how it was gathered
  "source_locator": "git:apex-power-ops-platform@<sha>:/",         // where (URI/path/query id)
  "source_hash": "<sha256 of the evidence bundle, or null with reason>",

  "base_snapshot_sha256": "5bb4191f…",            // == sha256(census file bytes)
  "project_ref": "fxoyniqnrlkxfligbxmg",          // == census project_ref
  "captured_at": "2026-07-14T18:03:00+00:00",     // when this artifact was completed
  "observation_window": { "started_at": "…", "ended_at": "…" },

  "producing_repo_sha": "<40-hex or null>",       // conditional (Appendix B)
  "producing_repo_sha_not_applicable_reason": "<string, required iff producing_repo_sha null>",

  // operator_declaration dimension ONLY:
  "operator_identity": "<string>",
  "approval_ref": "<string>",

  "assignments": [
    { "object_id": "public.v_scope_financials",
      "value": { "state": "observed", "found_consumers": 0, "ref": "scan:2026-07-14" } }
    // value conforms to the dimension's census typed shape via $ref (Appendix B)
  ]
}
```

- **`assignments[].value`** is exactly the census typed wrapper for that dimension (`observed_bool` / `observed_advisor_array` / `consumer_evidence_dim`), reused by `$ref` — so `state`/`value`/`detail` and the `observed_state_rule` are enforced identically to the census (`OV008`).
- **`source_hash`** binds the evidence bundle the overlay was derived from (nullable with a stated reason for authorities that have no fixed bundle, e.g. a live advisor API pull).
- **`producing_repo_sha`** — Appendix B fixes, per dimension, whether it is required (repository/config-derived evidence) or explicitly not-applicable with a reason.

### `overlay.schema.json` (sibling contract)

- New file `infra/database/schema-placement/overlay.schema.json` with its own `$id` (e.g. `https://apex-power-ops/schema-placement/overlay.schema.json`) and a `version`.
- It `$ref`s the frozen `disposition.schema.json` typed `$defs` (`observed_bool`, `observed_advisor_array`, `consumer_evidence_dim`, `observation_window`, `object_id`, `iso_datetime`, `nonempty_string`) through the disposition schema's **absolute `$id`**.
- **`disposition.schema.json` is not modified in this packet.**
- Schema loading uses an explicit local `referencing.Registry` seeded with both schema documents by `$id`; **network/remote resolution is impossible** and a missing registry resource **fails closed**. Negative tests assert both (§9).
- Per-dimension shape is enforced by a `oneOf`/`if-then` over `dimension` → allowed `source_type` + `assignments[].value` `$ref` + `producing_repo_sha` applicability + (for `operator_declaration`) required `operator_identity`/`approval_ref`.

## 5. Load → verify → merge algorithm (`check_disposition` preapply)

New repeatable input: **`--overlay PATH`** (each with a detached `PATH.sig` sidecar, resolved fail-closed). Overlays are consumed only in `preapply`. Sequence, entirely offline:

1. **Read** the census bytes and each overlay's raw bytes once (in-hand bytes are the unit of trust, per SP026's pattern).
2. **Verify signatures** — census (SP026, unchanged) and every overlay: detached Ed25519 over the exact raw overlay bytes, resolved through `disposition_trust.resolve_pinned_key(--key-id)` and `disposition_signing.verify_sidecar_bytes_with_key` (`OV001`). Same pinned anchor, no caller-supplied key.
3. **Schema-validate** each overlay against `overlay.schema.json` via the offline registry (`OV008`).
4. **Bind** each overlay: `base_snapshot_sha256 == sha256(census bytes)` (`OV002`); `project_ref == census.project_ref` and `== --expect-project-ref` (`OV003`).
5. **Freshness** — each overlay's `captured_at` within `--now` and an overlay max-staleness bound; not in the future (`OV010`). Each `observation_window` well-formed and `ended_at <= captured_at`, not future (`OV009`).
6. **Authorize the target** of every assignment: `dimension` is one of the six (`OV004`); `source_type` matches the dimension's fixed authority mapping (`OV013`); `object_id` exists in the census (`OV005`); the base slot is currently `not_observed` (`OV006`); `producing_repo_sha` applicability satisfied (`OV012`); `operator_declaration` carries `operator_identity`+`approval_ref` (`OV014`).
7. **Conflict/duplicate** — no `(dimension, object_id)` pair is assigned more than once across all overlays, **even if the values are identical** (`OV007`).
8. **Build the effective view** — deep-copy the census; for each assignment set the resolved dimension value; for each relation compute the derived consumer window (§3, `OV011`). Record provenance (per overlay: raw-bytes sha256, dimension, signer, `captured_at`, covered object-id count, `producing_repo_sha`).
9. **Run the existing semantic gate** (`semantic_check`, SP001–SP027) against the **effective** snapshot — unchanged except `SP009`'s revised success condition (§3). The SP028 checkout gate and SP026 snapshot-signature check are unchanged and run as today (SP028 before any document is read). `observed_at` is never overwritten; the effective view is never serialized.
10. **Receipt** records the overlay provenance list and `effective_view: {in_memory_only: true}` alongside the SP026 signer/`snapshot_signature_sha256`/gate fields. No merged evidence bodies, no combined census.

The collector never imports the overlay loader; the checker never imports the collector (SP026's dependency discipline is preserved).

## 6. Reject matrix (overlay codes `OV0xx`)

| Code | Rejects |
|---|---|
| OV001 | overlay signature missing or fails against the pinned signer (exact raw bytes) |
| OV002 | `base_snapshot_sha256` != the supplied census file byte-hash (base mismatch) |
| OV003 | `project_ref` mismatch (overlay vs census vs `--expect-project-ref`) |
| OV004 | `dimension` not one of the six permitted paths (catalog fact / `database_deps` / other) |
| OV005 | assignment `object_id` absent from the census (unknown relation ID) |
| OV006 | target base slot is not `not_observed` (attempt to replace a resolved fact) |
| OV007 | duplicate/conflicting `(dimension, object_id)` assignment — rejected even when values agree |
| OV008 | value violates the dimension's typed shape / `observed_state_rule` / schema |
| OV009 | `observation_window` malformed, `started_at >= ended_at`, `ended_at > captured_at`, or future |
| OV010 | overlay `captured_at` stale or in the future vs `--now` |
| OV011 | derived consumer window empty (non-intersecting source windows) |
| OV012 | `producing_repo_sha` required-but-absent, or null-without-reason where applicable |
| OV013 | `source_type` does not match the dimension's fixed authority mapping |
| OV014 | `operator_declaration` overlay missing `operator_identity` or `approval_ref` |
| OV015 | partial cluster coverage — a cluster relation lacks a gate-required dimension overlay (raised at cluster admissibility, §8) |

`SP008` unchanged (base-census freshness). `SP009` success condition revised for overlaid consumer windows (§3). All other `SP0xx` semantics unchanged and run against the effective view.

## 7. Signature & key handling

- Overlays are signed and verified with the **same pinned Ed25519 trust anchor** as the census (`disposition_trust.TRUSTED_SIGNERS` + `keys/<key-id>.pub.pem`, SPKI-pinned). No new key, no caller-supplied key, no new trust surface.
- The private signing key stays in operator/Infisical custody and is never handled by the assistant; overlay *signing* is an operator-run, value-silent step (design only here — no signing performed in this packet).
- Verification is over exact raw overlay bytes (`verify_sidecar_bytes_with_key`), matching SP026's in-hand-bytes binding.

## 8. Definer-view reconciliation & cluster admissibility

- **Appendix A** enumerates all **31** security-definer views: the 29 definer-view-program views plus `public.mcp_job_run_summary_v` and `public.mcp_task_packet_summary_v`, the two exceptions recorded (not silently omitted) in Packets 01b/6b.
- **First cluster gate.** The first disposition cluster (3–5 views) is admissible only when, for **every** relation in the cluster, **every gate-required dimension** is fully overlaid — i.e. the effective view passes `SP009`/`SP010`/`SP013`/`SP022`/`SP027` for those relations with valid, fresh windows. Any relation missing a required dimension is `OV015` (partial coverage) — no cluster proceeds on partial evidence.
- "Gate-required dimension" for a relation = the union of the cluster manifest's `required_observations` and whatever a resolved `consumer_disposition` forces (`SP022`), for that relation. Overlays that resolve *more* than the minimum are permitted; overlays that resolve *less* than required block the cluster.
- Cluster *selection* (which 3–5 views) is out of scope here and happens only after complete, fresh overlay coverage exists for the chosen views.

## 9. Testing strategy (negative-first)

TDD, contract tests first, all offline (no DB, no network, no signing key). The implementation plan (separate packet) will detail tasks; the spec fixes the required coverage:
- **Schema (offline registry):** valid per-dimension overlays accepted; `dimension`↔`source_type` mismatch rejected; wrong `value` shape rejected; **missing registry resource fails closed**; **attempted remote `$ref` resolution fails** (no network).
- **Binding:** base-hash mismatch (`OV002`), project mismatch (`OV003`), unknown object_id (`OV005`), non-`not_observed` target (`OV006`).
- **Conflict:** duplicate `(dimension, object_id)` with **identical** values still rejected (`OV007`).
- **Time model:** overlay `captured_at` after the base census `observed_at` is **accepted** (proves decoupling); future `captured_at` rejected (`OV010`); `ended_at > captured_at` rejected (`OV009`); empty consumer-window intersection rejected (`OV011`); a valid derived window with `ended_at` after `base_observed_at` **passes** `SP009` (proves the revised success condition).
- **Signature:** tampered overlay byte fails (`OV001`); correct signature over exact bytes passes; the census signature path (SP026) is unaffected.
- **Merge integrity:** the census file on disk is byte-identical before/after a gate run; no combined-census artifact is produced; `observed_at` unchanged in output; receipt carries overlay provenance only.
- **End-to-end (fixtures):** a synthetic mini-census + per-dimension overlays drive a cluster from red (raw census fails `SP009`/`SP010`) to green (effective view passes) — using throwaway fixture keys, never the prod signer.

## 10. Out of scope / guardrails

- **No evidence collection.** This packet designs the contract and the checker mechanism only. Collecting each dimension's real evidence happens later, under separately-authorized read-only workflows.
- **No database access, no production write, no signing.** A1–A3, migrations, the apply runner, and all prod mutations remain HELD.
- **`disposition.schema.json` unchanged**; the census evidence and its signature unchanged.
- **No cluster selection or destructive disposition** in this packet.
- Merge governance unchanged: solo-maintainer squash after green CI + cross-engine IRP, no admin bypass. Overlay tooling merges **before** any evidence is collected.

## 11. Open items for cross-engine review

- **O-1 (time):** Should `database_deps`'s base observation (`base_observed_at`) be required to fall within the derived consumer window, or is recording it as separate provenance sufficient? The spec currently does the latter.
- **O-2 (registry):** Confirm the offline `referencing.Registry` seeding pattern and that both validators (`verify_census`-style and the overlay loader) fail closed identically on a missing resource.
- **O-3 (conflict rule):** Is per-`(dimension, object_id)` single-assignment the right granularity, or should a single overlay be allowed to supersede another by explicit version (rejected here in favor of no-supersede)?
- **O-4 (signature binding):** Confirm the `--overlay PATH` + `PATH.sig` sidecar convention (vs explicit `--overlay-sig`) and that raw-bytes verification matches SP026 exactly.
- **O-5 (producing_repo_sha):** Validate the per-dimension applicability table (Appendix B), especially `external_clients` (repo-tracked inventory vs live).

---

## Appendix A — the 31 security-definer views

Definer-view-program (29): `public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_apparatus_approval_queue`, `public.v_apparatus_resources`, `public.v_apparatus_testing_status`, `public.v_apparatus_type_resources`, `public.v_approval_queue_summary`, `public.v_equipment_current_status`, `public.v_equipment_movement_history`, `public.v_guide_image_completeness`, `public.v_image_production_queue`, `public.v_image_sourcing_summary`, `public.v_neta_test_details`, `public.v_pending_handoffs`, `public.v_project_equipment`, `public.v_projects_active`, `public.v_projects_full`, `public.v_pss_dashboard`, `public.v_scope_financials`, `public.v_scope_summary`, `public.v_tcc_calc_input`, `public.v_tcc_etu_catalog`, `public.v_tcc_etu_coefficients`, `public.v_tcc_tmt_catalog`, `public.v_tcc_tmt_curve_data`, `public.vw_etu_browse`, `public.vw_etu_calc_context`, `public.vw_sensor_calc_context`, `public.vw_trip_unit_cascade`.

Packet-01b/6b exceptions (2, explicitly retained): `public.mcp_job_run_summary_v`, `public.mcp_task_packet_summary_v`.

## Appendix B — per-dimension overlay type table

| # | `dimension` | `value` `$ref` | fixed `source_type` | `producing_repo_sha` | extra required |
|---|---|---|---|---|---|
| 1 | `in_data_api_exposed_schema` | `observed_bool` | `platform_config` | required (config repo SHA) | — |
| 2 | `advisor_findings` | `observed_advisor_array` | `advisor_api` | n/a + reason | — |
| 3 | `consumer_evidence.static_repo` | `consumer_evidence_dim` | `repository_scan` | required (scanned repo SHA) | — |
| 4 | `consumer_evidence.runtime_logs` | `consumer_evidence_dim` | `runtime_logs` | n/a + reason | — |
| 5 | `consumer_evidence.external_clients` | `consumer_evidence_dim` | `external_client_inventory` | conditional: required iff inventory is repo-tracked, else n/a + reason | — |
| 6 | `consumer_evidence.operator_declaration` | `consumer_evidence_dim` | `operator_declaration` | n/a + reason | `operator_identity`, `approval_ref` |
