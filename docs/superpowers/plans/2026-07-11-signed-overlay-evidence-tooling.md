# Signed Evidence Overlay Tooling Implementation Plan

> **rev 5 (2026-07-12)** folds the third plan re-audit (1 High + 1 Med + 1 Low): **F1** `OverlayContract` now holds **both** validators (`disposition_validator` for raw + effective, `overlay_validator` for overlays) built from the same in-hand bytes and loaded **once** — the overlay-enabled CLI path never calls `_validator()`, so no schema stage re-reads `disposition.schema.json`; **F2** the six delete/retain/SP018 e2e cases are now **named, registered, real `cd.main` tests** (`_e2e_delete_missing_in_data_api_OV015` / `_delete_true_in_data_api_SP027` / `_delete_false_noncovering_OV022` / `_retain_no_overlay_OV018` / `_retain_green` / `_unaccepted_manifest_SP018_no_receipt`); **F3** the self-review placeholder scan corrected (no placeholders remain).
> **rev 4 (2026-07-12)** folds the second plan re-audit (1 High + 4 Med): **F1** the loader **short-circuits on any schema failure** (non-object payload + malformed `assignments` → coded OV008, no `AttributeError`); **F2** the `in_data_api` delete diagnostic is a coherent split — **OV015** (missing) / **SP027** (observed-true) / **OV022** (observed-false, inadequate window); **F3** the principal `_e2e_red_then_green` + `_e2e_ov021_via_main` are now **real `cd.main` tests** (no passing placeholder); **F4** a real `validate_overlay`-maps-unseeded-`$ref`→coded-OV008 test; **F5** `producing_repo_sha` applicability is **three categories** (required / forbidden+reason / conditional) with positive+negative tests.
> **rev 3 (2026-07-12)** folds the focused-re-audit cross-engine pass (Codex, 2 P2s): OV022 **defers** for a missing/observed-true `in_data_api` overlay (fires only when an observed-false overlay's window fails to cover [S,E]); the recency-policy `OV016` (absent/non-finite `max_consumer_evidence_age_hours`) is a **deterministic precheck at the top of `derive_windows`**, never masked by a zero-contributor `OV018`.
> **rev 2 (2026-07-12)** folds the operator's cross-engine plan audit: layering RATIFIED (unconditional loader) + all nine findings (F1 raw-input validation, F2 per-overlay OV009, F3 receipt binding, F4 read-once `OverlayContract`, F5 schema-valid fixtures, F6 governed CI, F7 OV015, F8 real unresolved-`$ref` test, F9 IFF null-reason) + contributor-map-local. See the fold table at the end.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the signed-overlay evidence loader that lets the six `not_observed` dimensions of the immutable signed production census be resolved by separately-signed overlay documents, so `check_disposition.py` preapply can reach **evidence readiness** without ever mutating, re-signing, or re-emitting the census.

**Architecture:** A new **leaf module** `disposition_overlay.py` (imports `disposition_signing`, stdlib, `jsonschema`, `referencing` — it never imports `check_disposition`, preserving the acyclic module DAG the census/SP026 work established) implements the overlay load→verify→merge pipeline (codes `OV001–OV022`) and returns an **in-memory effective evidence view** (a `copy.deepcopy` of the census with the six dimensions resolved and a checker-derived consumer window). A new sibling `overlay.schema.json` `$ref`s the frozen `disposition.schema.json` typed `$defs` through an **offline, no-retrieve** `referencing.Registry`. `check_disposition.main()` (the CLI orchestration layer) gains `--overlay`/`--max-consumer-evidence-age-hours`, runs the loader in preapply after the SP026 signature gate, and passes the effective view + an in-memory `derived_window_object_ids` provenance set into the existing `semantic_check`. `semantic_check` gains exactly one behavioral change: a **provenance-conditional** SP009 branch (default `None` ⇒ original behavior, so every existing `run()`-level baseline is unchanged).

**Tech Stack:** Python 3.11, `jsonschema==4.23` + `referencing` (both already in the schema-placement `uv` project), `cryptography` (Ed25519, already present via `disposition_signing`), stdlib `hashlib`/`copy`/`json`/`math`/`datetime`. Tests are **script `__main__` runners** (pytest is NOT a locked dep).

## Global Constraints

- **Holds (this packet authorizes NONE of them):** no evidence collection, no database access, no production write, no signing-key handling, no cluster selection, no destructive apply. A1–A3, migrations, and the apply runner remain HELD. All work is offline with throwaway fixture keys.
- **`disposition.schema.json` is NOT modified.** The census bytes, its `.sig`, and `disposition_signing.py`/`disposition_trust.py`/`disposition_provenance.py` are read-only inputs to this packet (changing any would trip `ci/verify_committed_census.sh`'s tooling-unchanged gate for the committed census).
- **Module DAG:** `disposition_overlay.py` MUST NOT import `check_disposition.py`. `check_disposition.py` imports `disposition_overlay`. The collector (`collect_disposition.py`) imports neither.
- **Census immutability + in-memory merge only.** Never write a "combined census" or any merged artifact to disk. The parsed base census object is never mutated (`copy.deepcopy` before any write into the effective view).
- **Fail closed.** Every ambiguous / missing / non-finite / unresolvable condition is a coded `OV0xx`/`SP0xx` reject — never a silent pass, never an uncaught exception (registry-unresolvable and calendar-invalid datetimes are mapped to coded `OV008`).
- **Signed bytes are the unit of integrity.** Verify the detached Ed25519 signature over the **exact raw overlay bytes** against the same pinned `TRUSTED_SIGNERS` anchor via `disposition_trust.resolve_pinned_key` + `disposition_signing.verify_sidecar_bytes_with_key`. No new key, no caller-supplied key. Parse from the **same verified buffer** (no re-read).
- **Evidence readiness ≠ authorization (§2A).** A GREEN checker attests evidence readiness only. The receipt carries `evidence_ready: true` + `execution_authorized: false` and **no** `production_eligible` field and **no** write-GO. `operator_identity`/`attestation_ref` are provenance, consumed by no authorization decision.
- **T1 (OV022 trigger scope):** `OV022` is evaluated **only** for a `delete`-conclusion cluster-source relation whose `external_clients` overlay resolves to `not_applicable` (invoking the SP027 waiver, which itself requires `in_data_api_exposed_schema` observed `false`). When `external_clients` is `observed`, `OV022` is **not** evaluated.
- **T2 (exact-assignment window lookup):** the `in_data_api_exposed_schema` window used by `OV022` comes from the overlay whose `(dimension, object_id)` assignment matches that exact relation — uniquely determined by the `OV007` `(dimension, object_id)` uniqueness guarantee — never "any exposure overlay."
- **T3 (unique derivation):** the consumer window is derived **once per unique source `object_id`** across all cluster decisions (deduplicate by `object_id`); the `derived_window_object_ids` set makes repeated markers idempotent.
- **Layering — RATIFIED (operator cross-engine plan audit, 2026-07-12):** the **unconditional loader model** stands — `OV021` runs even with zero overlays; a bare preapply against the canonical raw census is **RED**; overlay presence is required for evidence readiness; direct `run()` tests retain their authoring semantics. The unconditional `OV021` precheck + effective-view build live in `main()`/`disposition_overlay`; `semantic_check`/`run()` gain only the `derived_window_object_ids`-conditional SP009 branch. Existing `run()`-level SP0xx baselines in `tests/test_check_disposition.py` stay green untouched; only the `main()`-level e2e/receipt tests migrate to the overlay model (Task 7 & 8).
- **Raw-input validation before overlay processing (audit F1):** immediately after the SP026 signature gate and **before** the overlay loader, `main()` schema-validates + kind-pins the four raw documents (via the extracted `validate_documents` helper). A validly-signed-but-malformed census yields a coded `SP001` red **before** any overlay parse — no uncaught exception. The effective view is re-validated after merge by `run()` (already planned). The loader is additionally defensive: every datetime parse is wrapped and mapped to a coded reject (Invariant 7).
- **Per-overlay window validation (audit F2):** every overlay (all six dimensions, incl. the Data-API-exposure overlay used by `OV022`) passes `check_observation_window()` — `started_at < ended_at`, `ended_at <= captured_at`, `ended_at <= now` — as a coded `OV009` **before** its assignments are staged. This is independent of the derived-window predicate.
- **Read-once schema contract (audit F4 + round-4 F1):** one `OverlayContract` (schema bytes, their SHA-256, **and both validators** — `disposition_validator` for raw + effective-view SP001, `overlay_validator` for overlays) is built **once** immediately after SP026 and threaded through every validation stage. `disposition.schema.json` is read exactly once per run; the overlay-enabled CLI path (`main()`) never calls `_validator()`, so raw validation, OV020 drift-binding, and effective-view validation cannot see different bytes under a concurrent schema edit.
- **Receipt per-overlay binding (audit F3):** each `receipt_overlays` entry binds — absolute overlay path, raw-byte SHA-256, sidecar path + SHA-256, signer `key_id` + SPKI fingerprint, dimension + assignment `object_id`s + count, `source_hash`, and the `disposition_schema_sha256`/`overlay_schema_sha256`.
- **Contributor map is local (audit instruction #9):** the per-relation consumer-contributor windows are passed to `derive_windows` as a **separate local dict** — never stashed on the effective snapshot — so no scratch key can ever reach schema validation or serialization.
- **`OV015` implemented + tested (audit F7):** `check_cluster_completeness()` produces a coded `OV015` for a cluster relation lacking a permitted-overlay-target, base-`not_observed` gate-required dimension (already-observed `database_deps` satisfies), with a dedicated negative test. `OV015` is advisory-completeness; `SP009`/`SP022`/`SP027` on the effective view remain authoritative.
- **IFF null-reason contracts (audit F9):** `OV019` (`source_hash`) and `OV012` (`producing_repo_sha`) enforce a true biconditional — a reason is required **iff** the hash is null, so a reason supplied alongside a **non-null** hash is also rejected.
- **Governed CI (audit F6):** `test_overlay_schema` and `test_overlay_loader` are added to the `suites` job of `.github/workflows/schema-placement-ci.yml` (Tasks 1 & 8). Manual Task-9 execution is not sufficient.
- **Derived-window predicate (§3), enforced at merge:** contributors `C` = consumer-dimension overlays resolving the relation with `state = observed` over `{static_repo, runtime_logs, external_clients, operator_declaration}` (`database_deps` is anchored at `base_observed_at`, NOT a windowed contributor). `S = max(startedᵢ)`, `E = min(endedᵢ)`; reject unless: `C` non-empty (`OV018`); `S < E` (`OV011`); `E <= now` (`OV009`); `now - E <= max_consumer_evidence_age_hours` (`OV016`, required finite+positive CLI flag; absent/NaN/Inf ⇒ `OV016`); `S <= base_observed_at <= E` (`OV017`); for a `delete` conclusion `(E - S) >= 720h` is left to SP027 on the effective view.
- **Negative-test matrix (every item MUST appear as a pinned failing test, most in Tasks 3–5/8):** OV022-fires-when-window-not-covering · external_clients-observed→no-OV022 · **delete-missing-in_data_api→OV015** · **delete-observed-true-in_data_api→SP027** · **delete-observed-false-non-covering→OV022** · stale-in_data_api-overlay→OV010 · window-sourced-from-the-specific-assignment · retain-no-overlay→OV018 · retain-with-covering→green · duplicate-src-object→single-derivation-one-marker · OV021-fires-with-zero-overlays · remove-marker→original-SP009 · signed-non-object-overlay→OV008 · unseeded-$ref→coded-OV008 · producing_repo_sha-{required,forbidden,conditional}. The `in_data_api` delete diagnostic split is **OV015 (missing) / SP027 (observed-true) / OV022 (observed-false, inadequate window)** — a coherent three-way routing (audit round-3 F2).
- **Test invocation (every "run the test" step):** from `infra/database/schema-placement/`, run `uv run --project . --locked python tests/<file>.py`. A test file exits `0` iff all its `_name()` cases return truthy. NEVER invoke `pytest`.
- **Grounding constants:** base snapshot SHA-256 = `5bb4191fea584f4cecf111c718382bc3f6d0d88707a7c6e9c4c5065132ac416e`; project ref `fxoyniqnrlkxfligbxmg`; pinned signer id `prod-disposition-ed25519-2026-07`; disposition schema `$id` = `https://apex-power-ops/schema-placement/disposition.schema.json`.
- **Commit discipline:** solo-maintainer branch `schema-placement/signed-overlay`; frequent commits, exact paths only (`git add <file>` — never `git add <dir>`). Merge is operator-gated after green CI + cross-engine IRP (no admin bypass).

**Base directory for every path below:** `infra/database/schema-placement/` inside the host worktree `/home/olares/code/apex/apex-schema-overlay` (branch `schema-placement/signed-overlay`, off main `7c9a97ca`). All commands run there over `ssh olares-mesh`.

---

## File Structure

| File | Create/Modify | Responsibility |
|---|---|---|
| `overlay.schema.json` | Create | The overlay document contract; `$ref`s frozen `disposition.schema.json` `$defs` via absolute `$id`. |
| `disposition_overlay.py` | Create | Leaf module: `OV_CODES`, `OverlayContract` (read-once schema bytes+hashes+registry+validator), and the load→verify→bind→window→target→conflict→base-precheck→derive→coherence→completeness pipeline returning `MergeResult`. |
| `check_disposition.py` | Modify | `validate_documents` helper (extracted from `run()`'s preamble); `main()` CLI wiring (raw-input validation before the loader, `--overlay`, `--max-consumer-evidence-age-hours`, call the loader, print `OV`+`SP` diags); the provenance-conditional SP009 branch in `semantic_check`; and the receipt reframe in `build_receipt`. |
| `.github/workflows/schema-placement-ci.yml` | Modify | Add `test_overlay_schema` + `test_overlay_loader` to the governed `suites` job (audit F6). |
| `tests/test_overlay_schema.py` | Create | Schema + offline-registry lens (Task 1). |
| `tests/test_overlay_loader.py` | Create | Loader OV-code + time-model + coherence + integration + e2e lens (Tasks 2–8). |
| `tests/test_check_disposition.py` | Modify | Migrate the `main()`-level e2e/receipt cases to the overlay model + reframed receipt (Tasks 7–8). The `run()`-level SP0xx cases are untouched. |

**Shared fixture helpers** (defined once at the top of `tests/test_overlay_loader.py`, reused by every task's cases): `_ephemeral_keypair()` (throwaway Ed25519, copied from `tests/test_check_disposition.py`), `_zero_census(oids, observed_at)` (a canonical zero-width-window census), `_overlay(dimension, source_type, assignments, **overrides)` (a well-formed overlay dict bound to the census hash), `_sign(obj, priv)` → `(bytes, sig_bytes)` (canonical JSON bytes + detached sidecar bytes).

---

## Task 1: `overlay.schema.json` + offline registry validator

**Files:**
- Create: `overlay.schema.json`
- Create: `disposition_overlay.py` (skeleton: `OV_CODES`, `DIMENSIONS`, `OverlayContract`, `load_overlay_contract`, `OverlayRegistryError`)
- Test: `tests/test_overlay_schema.py`

**Interfaces:**
- Produces: `disposition_overlay.OverlayContract` (a `dataclass` holding `disp_bytes`, `disp_sha256`, `overlay_bytes`, `overlay_sha256`, and **both** `disposition_validator` + `overlay_validator`, all from a **single** read of the two schema files); `disposition_overlay.load_overlay_contract() -> OverlayContract` (builds both `FormatChecker` validators from the exact bytes it hashed — the census `disposition_validator` and the seeded-offline-registry `overlay_validator`); `disposition_overlay.OverlayRegistryError` (raised on registry/schema failure, mapped to `OV008` by callers); `disposition_overlay.DIMENSIONS: dict[str, tuple[str, str]]` mapping each of the six dimension paths to `(value_def_name, fixed_source_type)`; `disposition_overlay.OV_CODES: dict[str, str]`.

- [ ] **Step 1: Write the failing schema tests**

Create `tests/test_overlay_schema.py`:

```python
"""Schema + offline-registry tests for overlay.schema.json (Task 1).

Proves per-dimension shape enforcement and that remote/unseeded $ref resolution is IMPOSSIBLE
(mapped to a coded OverlayRegistryError, never an uncaught referencing.Unresolvable) and that a
calendar-invalid datetime is a coded reject via FormatChecker (not a traceback).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import disposition_overlay as ov  # noqa: E402

VALIDATOR = ov.load_overlay_contract().overlay_validator


def _base_overlay(dimension, source_type, value):
    return {
        "kind": "evidence_overlay", "overlay_version": "1",
        "dimension": dimension, "source_type": source_type,
        "authority": "test", "collection_method": "test", "source_locator": "test:x",
        "source_hash": None, "source_hash_not_applicable_reason": "live pull",
        "base_snapshot_sha256": "a" * 64,
        "disposition_schema_sha256": "b" * 64, "overlay_schema_sha256": "c" * 64,
        "project_ref": "fxoyniqnrlkxfligbxmg",
        "captured_at": "2026-07-14T18:03:00+00:00",
        "observation_window": {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-10T00:00:00Z"},
        "producing_repo_sha": None, "producing_repo_sha_not_applicable_reason": "n/a",
        "assignments": [{"object_id": "public.v_scope_financials", "value": value}],
    }


def _errs(doc):
    return [e.message for e in VALIDATOR.iter_errors(doc)]


def _valid_bool_overlay_accepted():
    doc = _base_overlay("in_data_api_exposed_schema", "platform_config", {"state": "observed", "value": False})
    doc["producing_repo_sha"] = "d" * 40  # required for this dimension
    return _errs(doc) == []


def _valid_consumer_overlay_accepted():
    doc = _base_overlay("consumer_evidence.static_repo", "repository_scan",
                        {"state": "observed", "found_consumers": 0, "ref": "scan:2026-07-14"})
    doc["source_hash"] = "e" * 64
    doc["producing_repo_sha"] = "d" * 40
    return _errs(doc) == []


def _source_type_mismatch_rejected():
    doc = _base_overlay("consumer_evidence.static_repo", "advisor_api",  # wrong source_type
                        {"state": "observed", "found_consumers": 0, "ref": "scan:x"})
    return _errs(doc) != []


def _wrong_value_shape_rejected():
    # a consumer_evidence_dim value under a bool dimension must fail
    doc = _base_overlay("in_data_api_exposed_schema", "platform_config",
                        {"state": "observed", "found_consumers": 0, "ref": "x"})
    return _errs(doc) != []


def _operator_declaration_requires_provenance():
    doc = _base_overlay("consumer_evidence.operator_declaration", "operator_declaration",
                        {"state": "observed", "found_consumers": 3, "ref": "att:2026-07-14"})
    # missing operator_identity / attestation_ref -> schema rejects
    return _errs(doc) != []


def _calendar_invalid_datetime_coded():
    doc = _base_overlay("consumer_evidence.static_repo", "repository_scan",
                        {"state": "observed", "found_consumers": 0, "ref": "scan:x"})
    doc["source_hash"] = "e" * 64
    doc["producing_repo_sha"] = "d" * 40
    doc["captured_at"] = "2026-13-40T99:99:99Z"  # pattern-plausible, calendar-invalid
    # FormatChecker must flag it as a coded schema error, NOT raise
    return _errs(doc) != []


def _unseeded_ref_raises_unresolvable_offline():
    # A registry with NO retrieve callback must FAIL CLOSED (raise referencing.Unresolvable) rather
    # than fetch when a schema $ref points at an UNSEEDED $id — proving remote resolution is impossible
    # and no network is attempted. (Task 3 additionally proves validate_overlay maps this to a coded OV008.)
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import Unresolvable
    bogus = Draft202012Validator({"$ref": "https://unseeded.example/nope.json#/$defs/x"}, registry=Registry())
    try:
        list(bogus.iter_errors({"any": 1}))
        return False  # must not silently pass
    except Unresolvable:
        return True   # fail-closed, offline, no fetch
    except Exception:
        return False  # any other exception (incl. a network error) is a failure


def _contract_hashes_match_on_disk_bytes():
    # The contract's schema SHA-256s must equal the on-disk bytes (read-once binding, audit F4).
    c = ov.load_overlay_contract()
    return (c.disp_sha256 == ov._sha256_hex(open(ov.DISPOSITION_SCHEMA_PATH, "rb").read())
            and c.overlay_sha256 == ov._sha256_hex(open(ov.OVERLAY_SCHEMA_PATH, "rb").read()))


if __name__ == "__main__":
    ok = True
    for name, fn in [
        ("valid_bool_overlay_accepted", _valid_bool_overlay_accepted),
        ("valid_consumer_overlay_accepted", _valid_consumer_overlay_accepted),
        ("source_type_mismatch_rejected", _source_type_mismatch_rejected),
        ("wrong_value_shape_rejected", _wrong_value_shape_rejected),
        ("operator_declaration_requires_provenance", _operator_declaration_requires_provenance),
        ("calendar_invalid_datetime_coded", _calendar_invalid_datetime_coded),
        ("unseeded_ref_raises_unresolvable_offline", _unseeded_ref_raises_unresolvable_offline),
        ("contract_hashes_match_on_disk_bytes", _contract_hashes_match_on_disk_bytes),
    ]:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== OVERLAY SCHEMA SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_schema.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'disposition_overlay'` (module not created yet).

- [ ] **Step 3: Create `overlay.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://apex-power-ops/schema-placement/overlay.schema.json",
  "title": "Signed Evidence Overlay — contract",
  "version": "1",
  "type": "object",
  "additionalProperties": false,
  "required": ["kind", "overlay_version", "dimension", "source_type", "authority",
               "collection_method", "source_locator", "source_hash",
               "base_snapshot_sha256", "disposition_schema_sha256", "overlay_schema_sha256",
               "project_ref", "captured_at", "observation_window", "producing_repo_sha", "assignments"],
  "properties": {
    "kind": { "const": "evidence_overlay" },
    "overlay_version": { "const": "1" },
    "dimension": { "enum": ["in_data_api_exposed_schema", "advisor_findings",
                            "consumer_evidence.static_repo", "consumer_evidence.runtime_logs",
                            "consumer_evidence.external_clients", "consumer_evidence.operator_declaration"] },
    "source_type": { "enum": ["platform_config", "advisor_api", "repository_scan",
                              "runtime_logs", "external_client_inventory", "operator_declaration"] },
    "authority": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "collection_method": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "source_locator": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "source_hash": { "type": ["string", "null"], "pattern": "^[0-9a-f]{64}$" },
    "source_hash_not_applicable_reason": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "base_snapshot_sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "disposition_schema_sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "overlay_schema_sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "project_ref": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "captured_at": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/iso_datetime" },
    "observation_window": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/observation_window" },
    "producing_repo_sha": { "type": ["string", "null"], "pattern": "^[0-9a-f]{40}$" },
    "producing_repo_sha_not_applicable_reason": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "operator_identity": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "attestation_ref": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/nonempty_string" },
    "assignments": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["object_id", "value"],
        "properties": {
          "object_id": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/object_id" },
          "value": { "type": "object" }
        }
      }
    }
  },
  "allOf": [
    { "if": { "properties": { "dimension": { "const": "in_data_api_exposed_schema" } } },
      "then": { "properties": { "source_type": { "const": "platform_config" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/observed_bool" } } } } } } },
    { "if": { "properties": { "dimension": { "const": "advisor_findings" } } },
      "then": { "properties": { "source_type": { "const": "advisor_api" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/observed_advisor_array" } } } } } } },
    { "if": { "properties": { "dimension": { "const": "consumer_evidence.static_repo" } } },
      "then": { "properties": { "source_type": { "const": "repository_scan" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/consumer_evidence_dim" } } } } } } },
    { "if": { "properties": { "dimension": { "const": "consumer_evidence.runtime_logs" } } },
      "then": { "properties": { "source_type": { "const": "runtime_logs" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/consumer_evidence_dim" } } } } } } },
    { "if": { "properties": { "dimension": { "const": "consumer_evidence.external_clients" } } },
      "then": { "properties": { "source_type": { "const": "external_client_inventory" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/consumer_evidence_dim" } } } } } } },
    { "if": { "properties": { "dimension": { "const": "consumer_evidence.operator_declaration" } } },
      "then": { "required": ["operator_identity", "attestation_ref"],
        "properties": { "source_type": { "const": "operator_declaration" },
        "assignments": { "items": { "properties": { "value": { "$ref": "https://apex-power-ops/schema-placement/disposition.schema.json#/$defs/consumer_evidence_dim" } } } } } } }
  ]
}
```

- [ ] **Step 4: Create the `disposition_overlay.py` skeleton**

```python
"""Signed evidence-overlay loader for the schema-placement disposition ledger (overlay packet).

LEAF module: imports disposition_signing (crypto mechanism), stdlib, jsonschema, referencing.
It MUST NOT import check_disposition (which imports THIS) — the acyclic module DAG the census/SP026
work established is preserved. Pure and offline: no DB, no network, no signing key. Fail-closed:
every ambiguous/missing/unresolvable condition is a coded OV0xx, never an uncaught exception.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

import disposition_signing as ds

SP_DIR = os.path.dirname(os.path.abspath(__file__))
OVERLAY_SCHEMA_PATH = os.path.join(SP_DIR, "overlay.schema.json")
DISPOSITION_SCHEMA_PATH = os.path.join(SP_DIR, "disposition.schema.json")

# dimension path -> (census typed $def, fixed source_type). Mirrors spec Appendix B.
DIMENSIONS = {
    "in_data_api_exposed_schema": ("observed_bool", "platform_config"),
    "advisor_findings": ("observed_advisor_array", "advisor_api"),
    "consumer_evidence.static_repo": ("consumer_evidence_dim", "repository_scan"),
    "consumer_evidence.runtime_logs": ("consumer_evidence_dim", "runtime_logs"),
    "consumer_evidence.external_clients": ("consumer_evidence_dim", "external_client_inventory"),
    "consumer_evidence.operator_declaration": ("consumer_evidence_dim", "operator_declaration"),
}
# consumer dimensions that contribute a windowed interval (database_deps is anchored at base_observed_at).
CONSUMER_CONTRIB_DIMS = ("static_repo", "runtime_logs", "external_clients", "operator_declaration")

OV_CODES = {
    "OV001": "overlay signature missing or fails against the pinned signer (exact raw bytes)",
    "OV002": "base_snapshot_sha256 != the supplied census file byte-hash",
    "OV003": "project_ref mismatch (overlay vs census vs --expect-project-ref)",
    "OV004": "dimension not one of the six permitted paths",
    "OV005": "assignment object_id absent from the census",
    "OV006": "target base slot is not not_observed",
    "OV007": "duplicate/conflicting (dimension, object_id) across or within overlays",
    "OV008": "value/schema violation, registry-unresolvable, or format failure (coded)",
    "OV009": "observation_window malformed, started>=ended, ended>captured, or future",
    "OV010": "overlay captured_at future or staler than the manifest max_staleness_hours",
    "OV011": "derived consumer window empty (S >= E)",
    "OV012": "producing_repo_sha required-but-absent, or null without reason",
    "OV013": "source_type does not match the dimension's fixed mapping",
    "OV014": "operator_declaration overlay missing operator_identity or attestation_ref",
    "OV015": "partial cluster coverage — a gate-required permitted-overlay-target dimension is unresolved",
    "OV016": "consumer window stale (now - E > max_consumer_evidence_age_hours; absent/non-finite also OV016)",
    "OV017": "temporal incoherence: base_observed_at not within the derived window [S, E]",
    "OV018": "zero contributing observed consumer overlays for a cluster-source relation",
    "OV019": "source_hash is null without source_hash_not_applicable_reason",
    "OV020": "overlay disposition_schema_sha256/overlay_schema_sha256 != on-disk schema bytes (drift)",
    "OV021": "base census consumer window is not the canonical zero-width {observed_at, observed_at}",
    "OV022": "delete-floor incoherence: in_data_api overlay window does not cover the derived consumer window",
}


class OverlayRegistryError(Exception):
    """Registry could not be built offline, or a schema $ref was unresolvable. Callers map to OV008."""


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_iso(value):
    """Mirror of check_disposition.parse_dt (kept local to preserve the leaf-module DAG). tz-aware UTC."""
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


@dataclass(frozen=True)
class OverlayContract:
    """Read-once schema contract (audit F4 + round-4 F1): the exact schema bytes, their SHA-256, and
    BOTH validators — the census `disposition_validator` (raw + effective snapshot) and the
    `overlay_validator` — all from a SINGLE read of the two schema files. The gate loads this once and
    uses it for every validation stage, so a concurrent schema edit cannot make raw validation, OV020
    binding, and effective-view validation see different bytes."""
    disp_bytes: bytes
    disp_sha256: str
    overlay_bytes: bytes
    overlay_sha256: str
    disposition_validator: object
    overlay_validator: object


def load_overlay_contract():
    """Build the OverlayContract: read both schema files ONCE (bytes), hash those exact bytes, parse
    them, and construct BOTH validators from the in-hand parsed content — the census
    `disposition_validator` (self-contained `#/$defs` refs; used for raw + effective-view SP001) and the
    `overlay_validator` (seeded offline `referencing.Registry`, no retrieve callback → remote/unseeded
    resolution is impossible). Raises OverlayRegistryError on any load/build failure (callers map to a
    coded OV008). The gate calls this ONCE and threads the contract to every validation stage; the
    schema files are never reopened during a run (audit round-4 F1)."""
    try:
        with open(DISPOSITION_SCHEMA_PATH, "rb") as fh:
            disp_bytes = fh.read()
        with open(OVERLAY_SCHEMA_PATH, "rb") as fh:
            overlay_bytes = fh.read()
        disp = json.loads(disp_bytes)
        overlay = json.loads(overlay_bytes)
        Draft202012Validator.check_schema(disp)
        Draft202012Validator.check_schema(overlay)
        registry = Registry().with_resources([
            (disp["$id"], Resource.from_contents(disp)),
            (overlay["$id"], Resource.from_contents(overlay)),
        ])  # no retrieve= => network/unseeded resolution raises Unresolvable, never fetches
        disposition_validator = Draft202012Validator(disp, format_checker=FormatChecker())  # census, self-contained #/$defs
        overlay_validator = Draft202012Validator(overlay, registry=registry, format_checker=FormatChecker())
        return OverlayContract(disp_bytes=disp_bytes, disp_sha256=_sha256_hex(disp_bytes),
                               overlay_bytes=overlay_bytes, overlay_sha256=_sha256_hex(overlay_bytes),
                               disposition_validator=disposition_validator, overlay_validator=overlay_validator)
    except (OSError, ValueError, KeyError, Unresolvable) as exc:
        raise OverlayRegistryError(f"cannot build offline overlay contract ({type(exc).__name__}: {exc})") from exc
```

> Implementer note: `load_overlay_contract` is the ONLY reader of the two schema files during a gate run (audit round-4 F1). `OV020` compares each overlay's declared `disposition_schema_sha256`/`overlay_schema_sha256` against `contract.disp_sha256`/`contract.overlay_sha256` — the same bytes both validators were built from — so raw validation, overlay validation, drift-binding, and effective-view validation can never diverge. `check_disposition._validator()` is retained only for the standalone `run()`-level tests; the overlay-enabled CLI path (`main()`) NEVER calls it.

- [ ] **Step 5: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_schema.py`
Expected: PASS — `=== OVERLAY SCHEMA SUITE: ALL PASS ===`.

- [ ] **Step 6: Register the suite in governed CI (audit F6)**

In `.github/workflows/schema-placement-ci.yml`, add `test_overlay_schema` to the `suites` job's loop so the gate runs it on every PR:

```yaml
          for t in test_disposition_schema test_check_disposition test_collect_disposition test_verify_census test_disposition_trust test_disposition_provenance test_overlay_schema; do
```

- [ ] **Step 7: Commit**

```bash
git add overlay.schema.json disposition_overlay.py tests/test_overlay_schema.py .github/workflows/schema-placement-ci.yml
git commit -m "feat(overlay): overlay.schema.json + read-once OverlayContract + CI (Task 1)"
```

---

## Task 2: read-once signature + binding loader

**Files:**
- Modify: `disposition_overlay.py` (add `verify_overlay`, `parse_overlay`, `check_binding`)
- Test: `tests/test_overlay_loader.py` (create with shared fixtures + Task-2 cases)

**Interfaces:**
- Consumes: `disposition_signing.verify_sidecar_bytes_with_key(message_bytes, sidecar_bytes, public_key) -> (ok, reason)`; `disposition_trust.resolve_pinned_key(...).public_key`.
- Produces: `verify_overlay(overlay_bytes: bytes, sig_bytes: bytes, public_key) -> tuple[bool, str]` (True iff the detached sig verifies over the exact bytes); `parse_overlay(overlay_bytes: bytes) -> dict` (strict dup-key + non-finite reject, raises `ValueError`); `check_binding(doc, *, census_sha256, census_project_ref, expect_project_ref, on_disk_disp_sha, on_disk_overlay_sha) -> list[tuple[str, str, str]]` returning `(code, locus, message)` diagnostics for `OV002/OV003/OV020`.

- [ ] **Step 1: Write the failing binding/signature tests**

Create `tests/test_overlay_loader.py` with the shared fixtures and the Task-2 cases:

```python
"""Loader tests for disposition_overlay.py (Tasks 2-8). Offline; throwaway fixture keys only.

Runner: uv run --project . --locked python tests/test_overlay_loader.py
"""
import copy
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ dir, to reuse the real helpers
import disposition_overlay as ov  # noqa: E402
import disposition_signing as _ds  # noqa: E402
import test_check_disposition as tcd  # noqa: E402 -- reuse the SCHEMA-VALID snapshot/rel helpers (audit F5)

# Canonical, mutually-coherent fixture clock (audit F5). base census observed_at == tcd._snapshot's;
# NOW is after it; the default overlay captured_at and window sit inside [.., NOW] with
# base_observed_at IN the default window (ended_at == base_observed_at), so the default derivation is
# valid and every timestamp is internally consistent.
CENSUS_OBSERVED_AT = "2026-07-10T20:00:00Z"    # == tcd._snapshot observed_at (base_observed_at)
NOW_ISO = "2026-07-11T00:00:00Z"
DEF_CAPTURED = "2026-07-10T21:00:00Z"          # <= NOW, >= every default window ended_at
DEF_WIN = {"started_at": "2026-06-05T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}  # ~35d; ended == base_observed_at
_CONTRACT = ov.load_overlay_contract()


def _ephemeral_keypair():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(obj, priv):
    body = _canon(obj)
    sidecar = json.dumps(_ds.build_sig_sidecar(body, priv)).encode("utf-8")
    return body, sidecar


def _no_bool():
    return {"state": "not_observed", "detail": "pending"}


def _no_ci():
    return {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "pending"}


def _zero_census(oids):
    """A fully SCHEMA-VALID census built from tcd._snapshot/_rel (all required top-level fields:
    repo_sha, collector_version, query_bundle_sha256, catalog_relation_count, collection_scope,
    target_identity, ...), forced to the canonical zero-width consumer window + all six overlay dims
    not_observed. database_deps stays observed (NOT an overlay target). Reuses the real helpers (F5)."""
    rels = []
    for oid in oids:
        schema, name = oid.split(".", 1)
        r = tcd._rel(oid, schema, name, "v")
        r["in_data_api_exposed_schema"] = _no_bool()
        r["advisor_findings"] = _no_bool()
        ce = r["consumer_evidence"]
        ce["observation_window"] = {"started_at": CENSUS_OBSERVED_AT, "ended_at": CENSUS_OBSERVED_AT}
        for dim in ("static_repo", "runtime_logs", "external_clients", "operator_declaration"):
            ce[dim] = _no_ci()
        # database_deps stays observed (tcd._rel set it observed) — not an overlay target
        rels.append(r)
    return tcd._snapshot(rels)  # sets observed_at == CENSUS_OBSERVED_AT + all required snapshot fields


def _overlay(dimension, source_type, assignments, census_bytes=None, **overrides):
    """A well-formed overlay bound to census_bytes. Default source_hash/producing_repo_sha are NON-null
    with NO *_not_applicable_reason (IFF-valid, audit F9); dimensions needing null+reason override both."""
    doc = {"kind": "evidence_overlay", "overlay_version": "1",
           "dimension": dimension, "source_type": source_type,
           "authority": "test", "collection_method": "test", "source_locator": "test:x",
           "source_hash": "e" * 64,
           "base_snapshot_sha256": hashlib.sha256(census_bytes).hexdigest() if census_bytes else "a" * 64,
           "disposition_schema_sha256": _CONTRACT.disp_sha256, "overlay_schema_sha256": _CONTRACT.overlay_sha256,
           "project_ref": "fxoyniqnrlkxfligbxmg",
           "captured_at": DEF_CAPTURED, "observation_window": dict(DEF_WIN),
           "producing_repo_sha": "d" * 40,
           "assignments": assignments}
    doc.update(overrides)
    return doc


def _codes(diags):
    return sorted({c for c, _l, _m in diags})


# ---- Task 2: signature + binding ----
def _tampered_byte_fails_OV001():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    tampered = bytearray(body); tampered[10] ^= 0x01
    ok, _r = ov.verify_overlay(bytes(tampered), sig, pub)
    return ok is False


def _good_signature_verifies():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    ok, _r = ov.verify_overlay(body, sig, pub)
    return ok is True


def _base_hash_mismatch_OV002():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    doc["base_snapshot_sha256"] = "f" * 64  # not the census hash
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV002" in _codes(diags)


def _project_mismatch_OV003():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, project_ref="other-project")
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV003" in _codes(diags)


def _schema_drift_OV020():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, disposition_schema_sha256="0" * 64)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=ov._sha256_hex(open(ov.DISPOSITION_SCHEMA_PATH, "rb").read()),
                             on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV020" in _codes(diags)


_CASES = [
    ("tampered_byte_fails_OV001", _tampered_byte_fails_OV001),
    ("good_signature_verifies", _good_signature_verifies),
    ("base_hash_mismatch_OV002", _base_hash_mismatch_OV002),
    ("project_mismatch_OV003", _project_mismatch_OV003),
    ("schema_drift_OV020", _schema_drift_OV020),
]

if __name__ == "__main__":
    ok = True
    for name, fn in _CASES:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== OVERLAY LOADER SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: module 'disposition_overlay' has no attribute 'verify_overlay'`.

- [ ] **Step 3: Implement `verify_overlay`, `parse_overlay`, `check_binding`**

Append to `disposition_overlay.py`:

```python
def _reject_dup_json_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def _reject_nonfinite(const):
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def verify_overlay(overlay_bytes: bytes, sig_bytes: bytes, public_key) -> tuple[bool, str]:
    """OV001: detached Ed25519 verify over the EXACT raw overlay bytes against the pinned key object.
    Delegates to disposition_signing (same anchor as the census). Fail-closed on any error."""
    return ds.verify_sidecar_bytes_with_key(overlay_bytes, sig_bytes, public_key)


def parse_overlay(overlay_bytes: bytes) -> dict:
    """Parse the SAME verified buffer (never a re-read). Strict: duplicate keys and non-finite JSON
    constants are rejected (parity with check_disposition.load_doc_from_text). Raises ValueError."""
    return json.loads(overlay_bytes.decode("utf-8"),
                      object_pairs_hook=_reject_dup_json_pairs, parse_constant=_reject_nonfinite)


def check_binding(doc, *, census_sha256, census_project_ref, expect_project_ref,
                  on_disk_disp_sha, on_disk_overlay_sha):
    """OV002 (base hash), OV003 (project ref, three-way), OV020 (schema drift)."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    if doc.get("base_snapshot_sha256") != census_sha256:
        out.append(("OV002", loc, f"base_snapshot_sha256 {doc.get('base_snapshot_sha256')} != census byte-hash {census_sha256}"))
    proj = doc.get("project_ref")
    if not (proj == census_project_ref == expect_project_ref):
        out.append(("OV003", loc, f"project_ref {proj!r} must equal census {census_project_ref!r} and --expect-project-ref {expect_project_ref!r}"))
    if doc.get("disposition_schema_sha256") != on_disk_disp_sha:
        out.append(("OV020", loc, "disposition_schema_sha256 != on-disk disposition.schema.json bytes (drift)"))
    if doc.get("overlay_schema_sha256") != on_disk_overlay_sha:
        out.append(("OV020", loc, "overlay_schema_sha256 != on-disk overlay.schema.json bytes (drift)"))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: PASS — `=== OVERLAY LOADER SUITE: ALL PASS ===`.

- [ ] **Step 5: Commit**

```bash
git add disposition_overlay.py tests/test_overlay_loader.py
git commit -m "feat(overlay): read-once signature verify + binding guards OV001/002/003/020 (Task 2)"
```

---

## Task 3: assignment / duplicate / base-window guards

**Files:**
- Modify: `disposition_overlay.py` (add `validate_overlay`, `check_target`, `check_conflict`, `precheck_base_window`)
- Test: `tests/test_overlay_loader.py` (append Task-3 cases)

**Interfaces:**
- Produces: `validate_overlay(doc, validator) -> list[tuple]` (`OV008`, maps schema/registry/format failures to a coded reject, incl. `Unresolvable`→coded); `check_observation_window(doc, now) -> list[tuple]` (`OV009`, per-overlay: `started_at < ended_at`, `ended_at <= captured_at`, `ended_at <= now`, well-formed; applied to ALL six dimensions incl. the Data-API overlay used by OV022, audit F2); `check_target(doc, census_rel_index: dict[str, dict]) -> list[tuple]` (`OV004/OV005/OV006/OV013/OV012/OV019/OV014`, with IFF null-reason for OV012/OV019 per audit F9); `check_conflict(assignment_keys: list[tuple[str, str]]) -> list[tuple]` (`OV007`, counts duplicates within+across overlays); `precheck_base_window(census) -> list[tuple]` (`OV021`, unconditional, string-equality to `observed_at`).
- Consumes: `DIMENSIONS`; `census_rel_index` = `{object_id: relation_dict}` built by the orchestrator; `now: datetime`.

- [ ] **Step 1: Write the failing guard tests** — append these cases and add them to `_CASES`:

```python
def _rel_index(census):
    return {r["object_id"]: r for r in census["relations"]}


# ---- Task 3: target / conflict / base-window ----
def _dimension_not_permitted_OV004():
    census = _zero_census(["public.v"])
    doc = _overlay("database_deps", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV004" in _codes(ov.check_target(doc, _rel_index(census)))


def _unknown_object_id_OV005():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.absent", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV005" in _codes(ov.check_target(doc, _rel_index(census)))


def _non_not_observed_target_OV006():
    census = _zero_census(["public.v"])
    census["relations"][0]["consumer_evidence"]["static_repo"] = {"state": "query_failed", "found_consumers": None, "ref": None, "detail": "err"}
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV006" in _codes(ov.check_target(doc, _rel_index(census)))


def _source_type_mismatch_OV013():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "runtime_logs",  # wrong source_type for dimension
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV013" in _codes(ov.check_target(doc, _rel_index(census)))


def _operator_declaration_missing_provenance_OV014():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.operator_declaration", "operator_declaration",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 1, "ref": "sha:att1"}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="operator attestation")  # forbidden dim -> null+reason (isolates OV014)
    doc.pop("operator_identity", None); doc.pop("attestation_ref", None)
    return "OV014" in _codes(ov.check_target(doc, _rel_index(census)))


def _validate_overlay_unresolvable_maps_to_OV008():
    # audit round-3 F4: an unseeded $ref hit during validation must be CAUGHT by validate_overlay and
    # mapped to a coded OV008 (never an uncaught referencing.Unresolvable, never a network fetch).
    from jsonschema import Draft202012Validator
    from referencing import Registry
    bogus = Draft202012Validator({"$ref": "https://unseeded.example/nope.json#/$defs/x"}, registry=Registry())
    return _codes(ov.validate_overlay({"dimension": "x", "any": 1}, bogus)) == ["OV008"]


def _producing_repo_sha_forbidden_nonnull_OV012():
    census = _zero_census(["public.v"])  # advisor_findings is FORBIDDEN: a non-null producing_repo_sha rejects
    doc = _overlay("advisor_findings", "advisor_api",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": ["security_definer_view"]}}])  # default producing_repo_sha="d"*40
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_forbidden_null_reason_ok():
    census = _zero_census(["public.v"])
    doc = _overlay("advisor_findings", "advisor_api",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": ["x"]}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="advisor API pull")
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_conditional_nonnull_ok():
    census = _zero_census(["public.v"])  # external_clients is CONDITIONAL: non-null (no reason) is allowed
    doc = _overlay("consumer_evidence.external_clients", "external_client_inventory",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "sha:e1"}}])
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_conditional_null_reason_ok():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.external_clients", "external_client_inventory",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "sha:e1"}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="no producing repo")
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _source_hash_null_without_reason_OV019():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   source_hash=None); doc.pop("source_hash_not_applicable_reason", None)
    return "OV019" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_absent_OV012():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",  # this dimension requires producing_repo_sha
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   producing_repo_sha=None); doc.pop("producing_repo_sha_not_applicable_reason", None)
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _duplicate_pair_within_and_across_OV007():
    # identical (dimension, object_id) twice, even with identical values, must reject
    keys = [("consumer_evidence.static_repo", "public.v"), ("consumer_evidence.static_repo", "public.v")]
    return "OV007" in _codes(ov.check_conflict(keys))


def _base_nonzero_window_OV021_with_zero_overlays():
    census = _zero_census(["public.v"])
    census["relations"][0]["consumer_evidence"]["observation_window"] = {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"}
    return "OV021" in _codes(ov.precheck_base_window(census))


def _base_canonical_window_passes_OV021():
    census = _zero_census(["public.v"])  # already {observed_at, observed_at}
    return ov.precheck_base_window(census) == []


NOW_DT = ov._parse_iso(NOW_ISO)


# ---- Task 3: per-overlay window (OV009) + IFF null-reason (F9) ----
def _window_started_after_ended_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   observation_window={"started_at": "2026-07-10T00:00:00Z", "ended_at": "2026-06-01T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _window_ended_after_captured_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   captured_at="2026-07-08T00:00:00Z", observation_window={"started_at": "2026-06-05T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _window_future_ended_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   captured_at="2026-07-20T00:00:00Z", observation_window={"started_at": "2026-06-05T00:00:00Z", "ended_at": "2026-07-15T00:00:00Z"})  # ended after NOW
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _in_data_api_overlay_window_is_checked_OV009():
    # The Data-API-exposure overlay (observed_bool, NOT a consumer contributor) still passes OV009 (F2).
    doc = _overlay("in_data_api_exposed_schema", "platform_config",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": False}}],
                   observation_window={"started_at": "2026-07-10T00:00:00Z", "ended_at": "2026-06-01T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _valid_window_passes_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return ov.check_observation_window(doc, NOW_DT) == []


def _source_hash_reason_with_nonnull_OV019():
    # IFF (F9): a reason supplied ALONGSIDE a non-null source_hash is also rejected.
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   source_hash="e" * 64, source_hash_not_applicable_reason="should not be here")
    return "OV019" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_reason_with_nonnull_OV012():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   producing_repo_sha="d" * 40, producing_repo_sha_not_applicable_reason="should not be here")
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


_CASES += [
    ("dimension_not_permitted_OV004", _dimension_not_permitted_OV004),
    ("unknown_object_id_OV005", _unknown_object_id_OV005),
    ("non_not_observed_target_OV006", _non_not_observed_target_OV006),
    ("source_type_mismatch_OV013", _source_type_mismatch_OV013),
    ("operator_declaration_missing_provenance_OV014", _operator_declaration_missing_provenance_OV014),
    ("source_hash_null_without_reason_OV019", _source_hash_null_without_reason_OV019),
    ("producing_repo_sha_absent_OV012", _producing_repo_sha_absent_OV012),
    ("source_hash_reason_with_nonnull_OV019", _source_hash_reason_with_nonnull_OV019),
    ("producing_repo_sha_reason_with_nonnull_OV012", _producing_repo_sha_reason_with_nonnull_OV012),
    ("producing_repo_sha_forbidden_nonnull_OV012", _producing_repo_sha_forbidden_nonnull_OV012),
    ("producing_repo_sha_forbidden_null_reason_ok", _producing_repo_sha_forbidden_null_reason_ok),
    ("producing_repo_sha_conditional_nonnull_ok", _producing_repo_sha_conditional_nonnull_ok),
    ("producing_repo_sha_conditional_null_reason_ok", _producing_repo_sha_conditional_null_reason_ok),
    ("validate_overlay_unresolvable_maps_to_OV008", _validate_overlay_unresolvable_maps_to_OV008),
    ("duplicate_pair_within_and_across_OV007", _duplicate_pair_within_and_across_OV007),
    ("window_started_after_ended_OV009", _window_started_after_ended_OV009),
    ("window_ended_after_captured_OV009", _window_ended_after_captured_OV009),
    ("window_future_ended_OV009", _window_future_ended_OV009),
    ("in_data_api_overlay_window_is_checked_OV009", _in_data_api_overlay_window_is_checked_OV009),
    ("valid_window_passes_OV009", _valid_window_passes_OV009),
    ("base_nonzero_window_OV021_with_zero_overlays", _base_nonzero_window_OV021_with_zero_overlays),
    ("base_canonical_window_passes_OV021", _base_canonical_window_passes_OV021),
]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: ... 'check_target'` (and the other new attrs).

- [ ] **Step 3: Implement the guards** — append to `disposition_overlay.py`:

```python
# producing_repo_sha applicability, three categories per Appendix B (audit round-3 F5):
_PRODUCING_SHA_REQUIRED = {"in_data_api_exposed_schema", "consumer_evidence.static_repo"}            # non-null, NO reason
_PRODUCING_SHA_FORBIDDEN = {"advisor_findings", "consumer_evidence.runtime_logs", "consumer_evidence.operator_declaration"}  # MUST be null + reason
# consumer_evidence.external_clients is CONDITIONAL: non-null (no reason) OR null + reason (the IFF fallthrough).


def validate_overlay(doc, validator):
    """OV008: JSON-Schema + FormatChecker validation against overlay.schema.json. Any
    referencing.Unresolvable (unseeded/remote $ref) is caught and mapped to a coded OV008."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    try:
        for err in sorted(validator.iter_errors(doc), key=lambda e: str(e.path)):
            path = "/".join(str(p) for p in err.path) or "<root>"
            out.append(("OV008", f"{loc}:{path}", err.message))
    except Unresolvable as exc:
        out.append(("OV008", loc, f"schema $ref unresolvable offline ({exc}) — no remote resolution permitted"))
    return out


def check_observation_window(doc, now):
    """OV009 (audit F2): per-overlay window guard applied to EVERY overlay (all six dimensions, incl.
    the Data-API-exposure overlay OV022 relies on): started_at < ended_at, ended_at <= captured_at,
    ended_at <= now. Fail-closed: a malformed/unparseable window is a single coded OV009, never an
    uncaught exception."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    w = doc.get("observation_window") or {}
    try:
        s = _parse_iso(w["started_at"])
        e = _parse_iso(w["ended_at"])
        cap = _parse_iso(doc["captured_at"])
    except (KeyError, ValueError, TypeError):
        return [("OV009", loc, f"observation_window/captured_at malformed or unparseable: {w!r}")]
    if not (s < e):
        out.append(("OV009", loc, f"started_at {w['started_at']} must be < ended_at {w['ended_at']}"))
    if e > cap:
        out.append(("OV009", loc, f"ended_at {w['ended_at']} is after captured_at {doc['captured_at']}"))
    if e > now:
        out.append(("OV009", loc, f"ended_at {w['ended_at']} is in the future vs now {now.isoformat()}"))
    return out


def _base_slot(rel, dimension):
    if dimension.startswith("consumer_evidence."):
        return rel.get("consumer_evidence", {}).get(dimension.split(".", 1)[1], {})
    return rel.get(dimension, {})


def check_target(doc, census_rel_index):
    """OV004/OV005/OV006/OV013/OV012/OV019/OV014. Validation, NOT execution-authorization."""
    out = []
    dimension = doc.get("dimension")
    loc = f"overlay:{dimension}"
    if dimension not in DIMENSIONS:
        out.append(("OV004", loc, f"dimension {dimension!r} is not one of the six permitted paths"))
        return out  # nothing else is meaningful for an unknown dimension
    _vdef, fixed_source = DIMENSIONS[dimension]
    if doc.get("source_type") != fixed_source:
        out.append(("OV013", loc, f"source_type {doc.get('source_type')!r} != fixed {fixed_source!r} for {dimension}"))
    # OV019 IFF (audit F9): a source_hash_not_applicable_reason is required IFF source_hash is null.
    sh = doc.get("source_hash")
    sh_reason = (doc.get("source_hash_not_applicable_reason") or "").strip()
    if sh is None and not sh_reason:
        out.append(("OV019", loc, "source_hash is null without source_hash_not_applicable_reason"))
    elif sh is not None and sh_reason:
        out.append(("OV019", loc, "source_hash is non-null but a source_hash_not_applicable_reason is also present (must be absent)"))
    # OV012 IFF: required dims need a non-null producing_repo_sha with NO reason; other dims need null+reason.
    prs = doc.get("producing_repo_sha")
    prs_reason = (doc.get("producing_repo_sha_not_applicable_reason") or "").strip()
    if dimension in _PRODUCING_SHA_REQUIRED:                 # required: non-null, no reason
        if not prs:
            out.append(("OV012", loc, f"producing_repo_sha required for {dimension} but absent/null"))
        elif prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is non-null but a not_applicable_reason is also present (must be absent)"))
    elif dimension in _PRODUCING_SHA_FORBIDDEN:              # forbidden: MUST be null + reason
        if prs is not None:
            out.append(("OV012", loc, f"producing_repo_sha is not applicable for {dimension}; it must be null with a not_applicable_reason"))
        elif not prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is null without producing_repo_sha_not_applicable_reason"))
    else:                                                    # conditional (external_clients): IFF null<->reason
        if prs is None and not prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is null without producing_repo_sha_not_applicable_reason"))
        elif prs is not None and prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is non-null but a not_applicable_reason is also present (must be absent)"))
    if dimension == "consumer_evidence.operator_declaration":
        if not (doc.get("operator_identity") or "").strip() or not (doc.get("attestation_ref") or "").strip():
            out.append(("OV014", loc, "operator_declaration overlay missing operator_identity/attestation_ref provenance"))
    for a in doc.get("assignments", []):
        oid = a.get("object_id")
        rel = census_rel_index.get(oid)
        if rel is None:
            out.append(("OV005", f"{loc}:{oid}", "assignment object_id absent from the census"))
            continue
        if _base_slot(rel, dimension).get("state") != "not_observed":
            out.append(("OV006", f"{loc}:{oid}", f"base slot state={_base_slot(rel, dimension).get('state')} (only not_observed is overlayable)"))
    return out


def check_conflict(assignment_keys):
    """OV007: reject any (dimension, object_id) pair assigned more than once, within OR across
    overlays, even if the values are identical. assignment_keys is the full flat list."""
    out = []
    counts = {}
    for key in assignment_keys:
        counts[key] = counts.get(key, 0) + 1
    for (dimension, oid), n in sorted(counts.items()):
        if n > 1:
            out.append(("OV007", f"overlay:{dimension}:{oid}", f"(dimension, object_id) assigned {n} times (across or within overlays)"))
    return out


def precheck_base_window(census):
    """OV021 (UNCONDITIONAL preapply precheck — runs even with zero overlays): every relation's base
    consumer window must be the canonical zero-width {observed_at, observed_at} the collector emits.
    String-equality to observed_at; a signed-but-hand-crafted non-zero window is caught before merge."""
    out = []
    observed_at = census.get("observed_at")
    for r in census.get("relations", []):
        w = r.get("consumer_evidence", {}).get("observation_window", {})
        if not (w.get("started_at") == observed_at and w.get("ended_at") == observed_at):
            out.append(("OV021", f"census:{r.get('object_id')}",
                        f"base consumer window {w} is not the canonical zero-width {{{observed_at}, {observed_at}}}"))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: PASS — `=== OVERLAY LOADER SUITE: ALL PASS ===`.

- [ ] **Step 5: Commit**

```bash
git add disposition_overlay.py tests/test_overlay_loader.py
git commit -m "feat(overlay): target/conflict guards + unconditional OV021 base-window precheck (Task 3)"
```

---

## Task 4: time derivation + provenance-conditional SP009

**Files:**
- Modify: `disposition_overlay.py` (add `derive_windows`)
- Modify: `check_disposition.py` (`semantic_check` gains `derived_window_object_ids=None`; SP009 branch; `run()` threads the param)
- Test: `tests/test_overlay_loader.py` (append time-model cases); `tests/test_check_disposition.py` (append the provenance-conditional SP009 unit case)

**Interfaces:**
- Produces: `derive_windows(effective, *, cluster_src_oids: set[str], now: datetime, base_observed_at: datetime, max_consumer_evidence_age_hours) -> tuple[list[tuple], set[str]]` — writes `{S, E}` ISO-8601 strings into each cluster-source relation's `consumer_evidence.observation_window` in `effective`, returns `(diagnostics, derived_window_object_ids)`; codes `OV009/OV011/OV016/OV017/OV018`. `OV010` (per-overlay `captured_at`) is applied by the orchestrator over each overlay (Task 6), not here.
- Modifies: `check_disposition.semantic_check(..., derived_window_object_ids=None)` and `check_disposition.run(..., derived_window_object_ids=None)`.

- [ ] **Step 1: Write the failing time-model tests** — append to `tests/test_overlay_loader.py` and `_CASES`:

```python
def _pdt(s):
    return ov._parse_iso(s)

BASE = _pdt(CENSUS_OBSERVED_AT)          # 2026-07-10T20:00:00Z (base_observed_at)
NOW = _pdt(NOW_ISO)                      # 2026-07-11T00:00:00Z


def _contrib_map(*entries):
    """Build a LOCAL {oid: [(started, ended, captured), ...]} contributor map (audit #9: passed as a
    separate arg to derive_windows — NEVER stashed on the effective snapshot)."""
    m = {}
    for oid, started, ended, captured in entries:
        m.setdefault(oid, []).append((_pdt(started), _pdt(ended), _pdt(captured)))
    return m


def _derive(eff, contrib, max_age=8760):
    return ov.derive_windows(eff, cluster_src_oids=set(contrib) or {"public.v"}, contrib_by_oid=contrib,
                             now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=max_age)


def _fresh_window_derives_ok():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, derived = _derive(eff, contrib)
    return diags == [] and "public.v" in derived


def _decade_old_window_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2016-06-01T00:00:00Z", "2016-07-01T00:00:00Z", "2016-07-02T00:00:00Z"))
    diags, _d = _derive(eff, contrib)
    return "OV016" in _codes(diags)


def _absent_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, _d = _derive(eff, contrib, max_age=None)
    return "OV016" in _codes(diags)


def _nonfinite_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, _d = _derive(eff, contrib, max_age=float("inf"))
    return "OV016" in _codes(diags)


def _base_outside_window_OV017():
    eff = _zero_census(["public.v"])  # base_observed_at = 07-10T20; window ends 07-05 < base
    contrib = _contrib_map(("public.v", "2026-06-01T00:00:00Z", "2026-07-05T00:00:00Z", "2026-07-06T00:00:00Z"))
    diags, _d = _derive(eff, contrib)
    return "OV017" in _codes(diags)


def _empty_contributors_OV018():
    eff = _zero_census(["public.v"])
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, contrib_by_oid={}, now=NOW,
                                  base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV018" in _codes(diags)


def _empty_intersection_OV011():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-07-08T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED),   # ended 07-10T20
                           ("public.v", "2026-06-05T00:00:00Z", "2026-07-05T00:00:00Z", "2026-07-06T00:00:00Z"))  # ended 07-05
    diags, _d = _derive(eff, contrib)  # S=max(07-08,06-05)=07-08 ; E=min(07-10T20,07-05)=07-05 ; S>E
    return "OV011" in _codes(diags)


def _duplicate_src_object_single_derivation():
    # object_id appears once in the set => derived exactly once; the derived marker is idempotent.
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, derived = _derive(eff, contrib)
    w = eff["relations"][0]["consumer_evidence"]["observation_window"]
    return diags == [] and list(derived) == ["public.v"] and w["started_at"] and w["ended_at"] and "_contrib_windows" not in eff


_CASES += [
    ("fresh_window_derives_ok", _fresh_window_derives_ok),
    ("decade_old_window_OV016", _decade_old_window_OV016),
    ("absent_maxage_is_OV016", _absent_maxage_is_OV016),
    ("nonfinite_maxage_is_OV016", _nonfinite_maxage_is_OV016),
    ("base_outside_window_OV017", _base_outside_window_OV017),
    ("empty_contributors_OV018", _empty_contributors_OV018),
    ("empty_intersection_OV011", _empty_intersection_OV011),
    ("duplicate_src_object_single_derivation", _duplicate_src_object_single_derivation),
]
```

Also append to `tests/test_check_disposition.py` (before its `__main__` list) a provenance-conditional SP009 unit case and register it:

```python
def _sp009_provenance_conditional():
    # An overlay-derived window with ended_at AFTER observed_at PASSES SP009 iff the object_id is in
    # derived_window_object_ids; with the marker removed it fails via the original bound.
    snap, dec, em, man, sp = harden_bundle()
    r = snap["relations"][0]
    r["consumer_evidence"]["observation_window"] = {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-20T00:00:00Z"}  # ended > observed_at
    oid = r["object_id"]
    with_marker = [d.code for d in cd.run(snap, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp,
                                          "fxoyniqnrlkxfligbxmg", derived_window_object_ids={oid})]
    without = [d.code for d in cd.run(snap, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp,
                                      "fxoyniqnrlkxfligbxmg", derived_window_object_ids=None)]
    return "SP009" not in with_marker and "SP009" in without
```
(register as `("sp009_provenance_conditional", _sp009_provenance_conditional)` in that file's `__main__` list.)

- [ ] **Step 2: Run to verify both fail**

Run: `uv run --project . --locked python tests/test_overlay_loader.py` → FAIL (`derive_windows` missing).
Run: `uv run --project . --locked python tests/test_check_disposition.py` → FAIL (`run()` got an unexpected keyword `derived_window_object_ids`).

- [ ] **Step 3a: Implement `derive_windows`** — append to `disposition_overlay.py`:

```python
def derive_windows(effective, *, cluster_src_oids, contrib_by_oid, now, base_observed_at, max_consumer_evidence_age_hours):
    """For each UNIQUE cluster-source object_id (T3), derive the consumer window from the relation's
    observed consumer contributors in contrib_by_oid[oid] — a LOCAL {oid: [(started, ended, captured), ...]}
    map (over CONSUMER_CONTRIB_DIMS) passed by the orchestrator, NEVER read off the effective snapshot
    (audit #9) — and write {S, E} ISO-8601 strings into the effective view. Returns
    (diagnostics, derived_window_object_ids). Fail-closed per the §3 predicate."""
    # Recency-policy precheck (Codex-P2): an absent/non-finite max_consumer_evidence_age_hours is a
    # DETERMINISTIC coded OV016 reported BEFORE any per-relation contributor check, so a missing CLI
    # flag can never be masked by an OV018 on a zero-contributor relation.
    if not (_finite(max_consumer_evidence_age_hours) and max_consumer_evidence_age_hours > 0):
        return [("OV016", "overlay-derive:policy", f"max_consumer_evidence_age_hours {max_consumer_evidence_age_hours!r} absent or non-finite (required recency floor, fail-closed)")], set()
    out = []
    derived = set()
    contrib = contrib_by_oid
    rel_by_oid = {r["object_id"]: r for r in effective.get("relations", [])}
    for oid in sorted(cluster_src_oids):  # a set => each object_id derived exactly once (T3)
        windows = contrib.get(oid, [])
        loc = f"overlay-derive:{oid}"
        if not windows:
            out.append(("OV018", loc, "zero observed consumer contributors for a cluster-source relation"))
            continue
        s = max(w[0] for w in windows)
        e = min(w[1] for w in windows)
        min_captured = min(w[2] for w in windows)
        if s >= e:
            out.append(("OV011", loc, f"derived window empty: S {s.isoformat()} >= E {e.isoformat()}"))
            continue
        if e > min_captured:
            out.append(("OV009", loc, f"E {e.isoformat()} > min captured_at {min_captured.isoformat()} (defense assert)"))
            continue
        if e > now:
            out.append(("OV009", loc, f"derived E {e.isoformat()} is in the future vs now {now.isoformat()}"))
            continue
        if (now - e).total_seconds() / 3600.0 > max_consumer_evidence_age_hours:  # per-relation recency (max_age validated above)
            out.append(("OV016", loc, f"stale: now-E {(now - e).total_seconds() / 3600.0:.1f}h > max {max_consumer_evidence_age_hours}h"))
            continue
        if not (s <= base_observed_at <= e):
            out.append(("OV017", loc, f"base_observed_at {base_observed_at.isoformat()} not within derived window [{s.isoformat()}, {e.isoformat()}]"))
            continue
        rel_by_oid[oid]["consumer_evidence"]["observation_window"] = {"started_at": s.isoformat(), "ended_at": e.isoformat()}
        derived.add(oid)
    return out, derived
```

- [ ] **Step 3b: Thread the provenance-conditional SP009 branch through `check_disposition.py`**

In `semantic_check`'s signature (`check_disposition.py:220`) add the parameter:

```python
def semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path, expect_project_ref=None, derived_window_object_ids=None):
```

Replace the SP009 window block (`check_disposition.py:333-340`) with:

```python
        # window ordering (strict) + minimum duration, scoped to this cluster's source relations (SP009).
        # Provenance-conditional upper bound: for windows the overlay checker itself derived-and-wrote
        # (object_id in derived_window_object_ids), the `<= observed_at` bound is relaxed (future/recency/
        # anchor already enforced at merge by OV009/OV016/OV017); non-derived and no-provenance windows
        # keep the original s < e <= observed_at (fail-closed on an absent marker).
        for r in src_rels:
            w = r.get("consumer_evidence", {}).get("observation_window")
            if isinstance(w, dict) and "started_at" in w and "ended_at" in w:
                s, e = parse_dt(w["started_at"]), parse_dt(w["ended_at"])
                is_derived = derived_window_object_ids is not None and r["object_id"] in derived_window_object_ids
                ordered = (s < e) if is_derived else (s < e <= observed_at)
                if not ordered:
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window {w['started_at']}..{w['ended_at']} must satisfy started<ended{'' if is_derived else '<=observed_at'} ({snapshot['observed_at']})"))
                elif (e - s).total_seconds() / 3600.0 < min_window:
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window duration {(e - s).total_seconds() / 3600.0:.2f}h < minimum_consumer_window_hours {min_window}"))
```

In `run()` (`check_disposition.py:532`) add the parameter and forward it:

```python
def run(snapshot, decisions, entity_map, manifest, now, mode, roots, validator, snapshot_path=None, expect_project_ref=None, derived_window_object_ids=None):
    ...
    diags = semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path, expect_project_ref, derived_window_object_ids)
    return sorted(diags, key=lambda x: x.key())
```

- [ ] **Step 4: Run to verify both pass**

Run: `uv run --project . --locked python tests/test_overlay_loader.py` → PASS.
Run: `uv run --project . --locked python tests/test_check_disposition.py` → PASS (the new case green; every pre-existing case still green because the default `None` preserves the original bound).

- [ ] **Step 5: Commit**

```bash
git add disposition_overlay.py check_disposition.py tests/test_overlay_loader.py tests/test_check_disposition.py
git commit -m "feat(overlay): derived-window predicate + provenance-conditional SP009 (Task 4)"
```

---

## Task 5: OV022 delete-floor coherence + all-action derivation

**Files:**
- Modify: `disposition_overlay.py` (add `check_delete_floor_coherence`)
- Test: `tests/test_overlay_loader.py` (append OV022 + all-action cases)

**Interfaces:**
- Produces: `check_delete_floor_coherence(effective, *, delete_src_oids: set[str], external_na_oids: set[str], in_data_api_windows: dict[str, tuple[datetime, datetime]], derived_windows: dict[str, tuple[datetime, datetime]]) -> list[tuple]` (`OV022`). `delete_src_oids` = source relations of `delete`-conclusion decisions; `external_na_oids` = those whose `external_clients` overlay resolves to `not_applicable` (T1 gate); `in_data_api_windows[oid]` = the observation_window of the overlay whose `(in_data_api_exposed_schema, oid)` assignment matches that relation (T2); `derived_windows[oid]` = the `(S, E)` written by `derive_windows`.

- [ ] **Step 1: Write the failing OV022 + all-action tests** — append to `tests/test_overlay_loader.py` and `_CASES`:

```python
def _ov022_fires_when_window_not_covering():
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    # in_data_api overlay window starts AFTER S -> does NOT cover [S,E]
    inapi = {"public.v": (_pdt("2026-07-05T00:00:00Z"), _pdt("2026-07-10T20:00:00Z"))}
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return "OV022" in _codes(diags)


def _ov022_ok_when_window_covers():
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-06-01T00:00:00Z"), _pdt("2026-07-15T00:00:00Z"))}  # covers [S,E]
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return diags == []


def _external_clients_observed_no_OV022():
    # external_clients OBSERVED -> the not_applicable waiver is not invoked -> OV022 not evaluated (T1)
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-07-05T00:00:00Z"), _pdt("2026-07-08T00:00:00Z"))}  # narrow, would fail if evaluated
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids=set(),  # NOT not_applicable
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return diags == []


def _missing_in_data_api_no_OV022():
    # NO observed-false in_data_api overlay backs the waiver -> check_delete_floor_coherence emits NO
    # OV022 (it defers). The OVERALL routing for a missing overlay is OV015 (cluster-completeness) and,
    # for an observed-TRUE overlay, SP027 at the semantic gate — both exercised in Task 8 (audit F2).
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows={}, derived_windows={"public.v": (S, E)})
    return "OV022" not in _codes(diags)


_CASES += [
    ("ov022_fires_when_window_not_covering", _ov022_fires_when_window_not_covering),
    ("ov022_ok_when_window_covers", _ov022_ok_when_window_covers),
    ("external_clients_observed_no_OV022", _external_clients_observed_no_OV022),
    ("missing_in_data_api_no_OV022", _missing_in_data_api_no_OV022),
]
```

> The `retain-no-overlay→OV018` and `retain-with-covering→green` all-action cases are covered end-to-end in Task 8 (they exercise the full `load_and_merge` + `main()` path where a `retain` decision's source relation is included in `cluster_src_oids`). `derive_windows` (Task 4) already derives for **every** `object_id` in `cluster_src_oids` regardless of action class, so a `retain` relation with no contributors already yields `OV018` there; Task 8 asserts the green path.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: ... 'check_delete_floor_coherence'`.

- [ ] **Step 3: Implement `check_delete_floor_coherence`** — append to `disposition_overlay.py`:

```python
def check_delete_floor_coherence(effective, *, delete_src_oids, external_na_oids,
                                 in_data_api_windows, derived_windows):
    """OV022 (T1-scoped): for a delete-conclusion source relation whose external_clients overlay
    resolves to not_applicable (invoking the SP027 waiver, which requires in_data_api observed false),
    the observed-FALSE in_data_api overlay's observation_window (looked up by the exact
    (dimension, object_id) assignment, T2) must COVER the derived consumer window [S, E]
    (started_at <= S and ended_at >= E), proving the relation was unexposed THROUGHOUT the evidence
    interval. OV022 evaluates ONLY when an observed-false in_data_api overlay backs the waiver (its
    window is in in_data_api_windows). The coherent routing for the other cases (audit round-3 F2):
    a MISSING in_data_api overlay leaves the gate-required dimension unresolved and is caught by
    **OV015** (cluster-completeness, before run()); an **observed-TRUE** overlay defers here and
    **SP027** denies the waiver at the semantic gate; only an observed-false overlay with an inadequate
    window is OV022 — none of these short-circuit their ratified diagnostic. When external_clients is
    observed (oid not in external_na_oids), OV022 is not evaluated (T1)."""
    out = []
    for oid in sorted(delete_src_oids & external_na_oids):  # T1: only not_applicable-waiver deletes
        se = derived_windows.get(oid)
        if se is None:
            continue  # no derived window (already rejected upstream by OV018/OV011/etc.)
        s, e = se
        api = in_data_api_windows.get(oid)
        if api is None:
            continue  # no observed-false in_data_api overlay backs the waiver -> SP027 denies it (defer)
        api_s, api_e = api
        if not (api_s <= s and api_e >= e):
            out.append(("OV022", f"overlay-delete:{oid}",
                        f"in_data_api window [{api_s.isoformat()}, {api_e.isoformat()}] does not cover derived consumer window [{s.isoformat()}, {e.isoformat()}]"))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: PASS — `=== OVERLAY LOADER SUITE: ALL PASS ===`.

- [ ] **Step 5: Commit**

```bash
git add disposition_overlay.py tests/test_overlay_loader.py
git commit -m "feat(overlay): OV022 delete-floor temporal coherence (T1/T2-scoped) (Task 5)"
```

---

## Task 6: `load_and_merge` orchestration + effective-view integrity

**Files:**
- Modify: `disposition_overlay.py` (add `MergeResult`, `load_and_merge`; add `OV010` freshness inside it)
- Test: `tests/test_overlay_loader.py` (append orchestration + integrity cases, incl. OV010)

**Interfaces:**
- Produces: `MergeResult` (a `dataclass` with `effective_snapshot: dict`, `derived_window_object_ids: set[str]`, `receipt_overlays: list[dict]`, `diagnostics: list[tuple[str, str, str]]`); `check_cluster_completeness(base_census, effective, manifest, decisions) -> list[tuple]` (`OV015`); `load_and_merge(*, census, census_bytes, overlay_inputs, manifest, decisions, expect_project_ref, now, max_consumer_evidence_age_hours, max_staleness_hours, resolved_signer, contract) -> MergeResult`. `overlay_inputs` = `list[tuple[str, str, bytes, bytes]]` of `(overlay_path, sig_path, overlay_bytes, sig_bytes)` read once by the caller; `contract` = the read-once `OverlayContract`. Never mutates `census`.

- [ ] **Step 1: Write the failing orchestration + integrity tests** — append to `tests/test_overlay_loader.py` and `_CASES`. These build a fake `resolved_signer` and a real `overlay_validator`:

```python
import re

class _FakeSigner:
    """Stands in for disposition_trust.ResolvedSigner (public_key + provenance for the receipt, F3)."""
    def __init__(self, pub):
        self.public_key = pub
        self.key_id = "test-signer"
        self.spki_sha256 = "f" * 64


def _decisions_manifest(oids, action="harden", conclusion="unresolved", required=None):
    # default conclusion 'unresolved' + empty required_observations => OV015 is NOT triggered, so these
    # merge-mechanics unit tests isolate the deepcopy/derivation/receipt behavior. (Full gate-required
    # coverage + OV015 are exercised in Task 8's e2e + Task 6's dedicated OV015 case below.)
    rows = [{"decision_id": "D1", "action_class": action, "decision_status": "accepted",
             "consumer_disposition": conclusion, "source_objects": list(oids)}]
    decisions = {"kind": "decisions_file", "rows": rows}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": action,
                "decision_ids": ["D1"], "evidence_snapshot": "prod.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": list(required or []),
                "technical_authority_approval": "TA-1"}
    return decisions, manifest


def _static_overlay(cb, oid="public.v", **overrides):
    return _overlay("consumer_evidence.static_repo", "repository_scan",
                    [{"object_id": oid, "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                    census_bytes=cb, **overrides)


def _merge(census, cb, overlays, decisions, manifest, signer, max_stale=8760):
    inputs = []
    for i, ov_doc in enumerate(overlays):
        ob, sig = _sign(ov_doc, signer[0])
        inputs.append((f"o{i}.json", f"o{i}.json.sig", ob, sig))
    return ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=inputs, manifest=manifest,
                             decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                             max_consumer_evidence_age_hours=8760, max_staleness_hours=max_stale,
                             resolved_signer=signer[1], contract=_CONTRACT)


def _merge_deepcopy_unmutated():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    before = copy.deepcopy(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    # base census object is unmutated; the effective view got a derived window (started_at moved off the
    # zero-width base); and no scratch contributor map leaked onto the effective snapshot (audit #9).
    w = res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]
    return (census == before and res.diagnostics == [] and w["started_at"] != CENSUS_OBSERVED_AT
            and "_contrib_windows" not in res.effective_snapshot)


def _stale_overlay_captured_at_OV010():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    # coherent window (ended <= captured, no OV009) but captured_at far older than max_staleness_hours
    o = _static_overlay(cb, captured_at="2020-01-05T00:00:00Z",
                        observation_window={"started_at": "2019-12-01T00:00:00Z", "ended_at": "2020-01-01T00:00:00Z"})
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [o], decisions, manifest, (priv, _FakeSigner(pub)), max_stale=24)
    return "OV010" in _codes(res.diagnostics)


def _effective_view_datetimes_are_iso():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    w = res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]
    pat = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
    return res.diagnostics == [] and re.match(pat, w["started_at"]) and re.match(pat, w["ended_at"])


def _receipt_binds_sidecar_and_signer():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    e = res.receipt_overlays[0]
    return (res.diagnostics == [] and e["path"] == "o0.json" and e["sig_path"] == "o0.json.sig"
            and len(e["raw_sha256"]) == 64 and len(e["sig_sha256"]) == 64
            and e["signer"]["key_id"] == "test-signer" and e["signer"]["spki_sha256"] == "f" * 64
            and e["object_ids"] == ["public.v"] and e["dimension"] == "consumer_evidence.static_repo"
            and e["disposition_schema_sha256"] == _CONTRACT.disp_sha256)


def _ov015_missing_gate_required_dimension():
    # A resolved (no_consumer) conclusion forces every consumer contributor dim; supplying only
    # static_repo leaves runtime_logs/external_clients/operator_declaration unresolved -> OV015 (F7).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"], conclusion="no_consumer")
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    return "OV015" in _codes(res.diagnostics)


def _signed_non_object_overlay_OV008():
    # a SIGNED JSON array (not an object) must be a coded OV008, never an uncaught AttributeError (F1).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    body, sig = _sign(["not", "an", "object"], priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("bad.json", "bad.json.sig", body, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                            max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), contract=_CONTRACT)
    return "OV008" in _codes(res.diagnostics)  # reached here => no uncaught exception


def _signed_malformed_assignments_OV008():
    # a SIGNED object whose assignments is the wrong TYPE (not an array) -> schema OV008, no crash: the
    # short-circuit skips the assignment iteration that would otherwise iterate a string (F1).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _static_overlay(cb)
    doc["assignments"] = "not-an-array"
    body, sig = _sign(doc, priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("m.json", "m.json.sig", body, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                            max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), contract=_CONTRACT)
    return "OV008" in _codes(res.diagnostics)


_CASES += [
    ("merge_deepcopy_unmutated", _merge_deepcopy_unmutated),
    ("stale_overlay_captured_at_OV010", _stale_overlay_captured_at_OV010),
    ("effective_view_datetimes_are_iso", _effective_view_datetimes_are_iso),
    ("receipt_binds_sidecar_and_signer", _receipt_binds_sidecar_and_signer),
    ("ov015_missing_gate_required_dimension", _ov015_missing_gate_required_dimension),
    ("signed_non_object_overlay_OV008", _signed_non_object_overlay_OV008),
    ("signed_malformed_assignments_OV008", _signed_malformed_assignments_OV008),
]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: ... 'load_and_merge'`.

- [ ] **Step 3: Implement `MergeResult` + `load_and_merge`** — append to `disposition_overlay.py`:

```python
# ---- OV015 cluster-completeness (advisory; audit F7) ----
_PERMITTED_OVERLAY_TARGETS = set(DIMENSIONS)  # the six permitted overlay paths
_CONSUMER_REQUIRED_EXPANSION = tuple(f"consumer_evidence.{d}" for d in CONSUMER_CONTRIB_DIMS)


def _gate_required_dims(row, manifest):
    """Permitted-overlay-target dimensions a decision's source relations must have resolved: the
    permitted-target subset of manifest.required_observations (consumer_evidence expands to the four
    contributor dims) UNION the consumer dims for a resolved consumer_disposition (SP022) UNION the
    delete-floor dims + in_data_api for a delete (SP027 external_clients waiver)."""
    req = set()
    for f in manifest.get("required_observations", []):
        if f == "consumer_evidence":
            req.update(_CONSUMER_REQUIRED_EXPANSION)
        elif f in _PERMITTED_OVERLAY_TARGETS:
            req.add(f)
    if row.get("consumer_disposition") in ("no_consumer", "has_consumers"):
        req.update(_CONSUMER_REQUIRED_EXPANSION)
    if row.get("action_class") == "delete":
        req.update(_CONSUMER_REQUIRED_EXPANSION)
        req.add("in_data_api_exposed_schema")
    return req & _PERMITTED_OVERLAY_TARGETS


def check_cluster_completeness(base_census, effective, manifest, decisions):
    """OV015 (advisory, audit F7): every cluster-source relation must have each gate-required
    permitted-overlay-target dimension resolved (state != not_observed) in the effective view — unless
    it was already observed in the BASE census (e.g. database_deps, which is not an overlay target).
    SP009/SP022/SP027 on the effective view remain authoritative; OV015 names the missing overlay early."""
    out = []
    dec_by_id = {row["decision_id"]: row for row in decisions.get("rows", [])}
    base_index = {r["object_id"]: r for r in base_census.get("relations", [])}
    eff_index = {r["object_id"]: r for r in effective.get("relations", [])}
    for did in manifest.get("decision_ids", []):
        row = dec_by_id.get(did)
        if not row:
            continue
        for oid in row.get("source_objects", []):
            base_rel, eff_rel = base_index.get(oid), eff_index.get(oid)
            if base_rel is None or eff_rel is None:
                continue
            for dim in sorted(_gate_required_dims(row, manifest)):
                if _base_slot(base_rel, dim).get("state") == "not_observed" and _base_slot(eff_rel, dim).get("state") == "not_observed":
                    out.append(("OV015", f"cluster:{did}:{oid}:{dim}", f"gate-required dimension {dim} is unresolved (no permitted overlay)"))
    return out


@dataclass
class MergeResult:
    effective_snapshot: dict
    derived_window_object_ids: set
    receipt_overlays: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


def load_and_merge(*, census, census_bytes, overlay_inputs, manifest, decisions, expect_project_ref,
                   now, max_consumer_evidence_age_hours, max_staleness_hours, resolved_signer, contract):
    """The step 1-8 pipeline. `contract` is the read-once OverlayContract (schema bytes+hashes+validator,
    audit F4 — schemas are NEVER reopened here). `overlay_inputs` = list of
    (overlay_path, sig_path, overlay_bytes, sig_bytes) read once by the caller. Verifies + binds +
    window-checks (OV009, per-overlay) + targets + de-conflicts each overlay; runs the UNCONDITIONAL
    OV021 precheck; deep-copies the census; sets each resolved dimension; derives per-relation consumer
    windows for EVERY cluster-source relation (contributor map kept LOCAL, audit #9); runs OV022 + OV015.
    Returns a MergeResult. NEVER mutates census. Any reject short-circuits to a red MergeResult."""
    diags = []
    census_sha = _sha256_hex(census_bytes)
    base_observed_at = _parse_iso(census.get("observed_at"))
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}

    # step 8 (OV021) runs UNCONDITIONALLY, even with zero overlays.
    diags += precheck_base_window(census)

    parsed = []            # (doc, overlay_path, sig_path, overlay_bytes, sig_bytes)
    all_keys = []          # (dimension, object_id) for OV007
    for overlay_path, sig_path, ob_bytes, sig_bytes in overlay_inputs:
        ok, reason = verify_overlay(ob_bytes, sig_bytes, resolved_signer.public_key)
        if not ok:
            diags.append(("OV001", f"overlay:{overlay_path}", f"signature verification failed: {reason}"))
            continue
        try:
            doc = parse_overlay(ob_bytes)          # parse the SAME verified buffer
        except ValueError as exc:
            diags.append(("OV008", f"overlay:{overlay_path}", f"parse failed ({exc})"))
            continue
        # A signed-but-non-object payload (JSON array/scalar) has no .get/.assignments — reject it as a
        # coded OV008 before any dict-shaped access, never an uncaught AttributeError (audit round-3 F1).
        if not isinstance(doc, dict):
            diags.append(("OV008", f"overlay:{overlay_path}", f"overlay is not a JSON object (got {type(doc).__name__})"))
            continue
        # SHORT-CIRCUIT on any schema/format/registry failure: a schema-invalid overlay is not safe to
        # bind / window-check / target / iterate (its assignments may be malformed). OV008 then continue.
        schema_diags = validate_overlay(doc, contract.overlay_validator)
        if schema_diags:
            diags.extend(schema_diags)
            continue
        diags += check_binding(doc, census_sha256=census_sha, census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref, on_disk_disp_sha=contract.disp_sha256,
                               on_disk_overlay_sha=contract.overlay_sha256)
        diags += check_observation_window(doc, now)   # OV009 per-overlay (audit F2), on a schema-valid doc
        diags += check_target(doc, rel_index)
        # OV010 per-overlay captured_at freshness (finite-guarded), reusing manifest max_staleness_hours.
        try:
            cap = _parse_iso(doc.get("captured_at"))
            if cap > now:
                diags.append(("OV010", f"overlay:{overlay_path}", "captured_at is in the future"))
            elif _finite(max_staleness_hours) and (now - cap).total_seconds() / 3600.0 > max_staleness_hours:
                diags.append(("OV010", f"overlay:{overlay_path}", f"captured_at staler than max_staleness_hours {max_staleness_hours}"))
        except (ValueError, TypeError):
            diags.append(("OV010", f"overlay:{overlay_path}", "captured_at unparseable"))
        for a in doc.get("assignments", []):
            all_keys.append((doc.get("dimension"), a.get("object_id")))
        parsed.append((doc, overlay_path, sig_path, ob_bytes, sig_bytes))
    diags += check_conflict(all_keys)

    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)

    # ---- build the effective view (deepcopy; census never mutated) ----
    effective = copy.deepcopy(census)
    eff_index = {r["object_id"]: r for r in effective["relations"]}
    contrib = {}                     # LOCAL: oid -> [(started, ended, captured)] (audit #9; NOT stashed on effective)
    in_data_api_windows = {}         # oid -> (started, ended) from the (in_data_api, oid) overlay (T2)
    external_state = {}              # oid -> external_clients state, for T1
    for doc, _op, _sp, _ob, _sb in parsed:
        dim = doc["dimension"]
        win = doc["observation_window"]
        w = (_parse_iso(win["started_at"]), _parse_iso(win["ended_at"]))
        cap = _parse_iso(doc["captured_at"])
        for a in doc["assignments"]:
            oid = a["object_id"]
            rel = eff_index[oid]
            if dim.startswith("consumer_evidence."):
                sub = dim.split(".", 1)[1]
                rel["consumer_evidence"][sub] = a["value"]
                if sub in CONSUMER_CONTRIB_DIMS and a["value"].get("state") == "observed":
                    contrib.setdefault(oid, []).append((w[0], w[1], cap))
                if sub == "external_clients":
                    external_state[oid] = a["value"].get("state")
            else:
                rel[dim] = a["value"]
                # Record the in_data_api window ONLY for an observed-FALSE overlay — the only shape that
                # backs the SP027 external_clients not_applicable waiver. A missing overlay leaves the
                # gate-required dim unresolved (-> OV015); an observed-true overlay leaves this unset so
                # OV022 defers and SP027 denies the waiver at the semantic gate (audit F2; T2).
                if dim == "in_data_api_exposed_schema" and a["value"].get("state") == "observed" and a["value"].get("value") is False:
                    in_data_api_windows[oid] = w

    # cluster-source object_ids across ALL decisions (deduped by object_id, T3), incl. retain.
    dec_by_id = {row["decision_id"]: row for row in decisions.get("rows", [])}
    cluster_src_oids = set()
    delete_src_oids = set()
    for did in manifest.get("decision_ids", []):
        row = dec_by_id.get(did)
        if not row:
            continue
        for oid in row.get("source_objects", []):
            if oid in eff_index:
                cluster_src_oids.add(oid)
                if row.get("action_class") == "delete":
                    delete_src_oids.add(oid)

    wdiags, derived = derive_windows(effective, cluster_src_oids=cluster_src_oids, contrib_by_oid=contrib,
                                     now=now, base_observed_at=base_observed_at,
                                     max_consumer_evidence_age_hours=max_consumer_evidence_age_hours)
    diags += wdiags
    derived_windows = {oid: (_parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["started_at"]),
                             _parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["ended_at"]))
                       for oid in derived}
    external_na_oids = {oid for oid, st in external_state.items() if st == "not_applicable"}
    diags += check_delete_floor_coherence(effective, delete_src_oids=delete_src_oids,
                                          external_na_oids=external_na_oids,
                                          in_data_api_windows=in_data_api_windows, derived_windows=derived_windows)
    diags += check_cluster_completeness(census, effective, manifest, decisions)   # OV015 (audit F7)

    receipt_overlays = []
    for doc, op, sp, ob, sb in parsed:
        entry = {"path": op, "raw_sha256": _sha256_hex(ob), "sig_path": sp, "sig_sha256": _sha256_hex(sb),
                 "signer": {"key_id": resolved_signer.key_id, "spki_sha256": resolved_signer.spki_sha256},
                 "dimension": doc["dimension"], "object_ids": [a["object_id"] for a in doc.get("assignments", [])],
                 "object_id_count": len(doc.get("assignments", [])), "captured_at": doc["captured_at"],
                 "producing_repo_sha": doc.get("producing_repo_sha"), "source_hash": doc.get("source_hash"),
                 "disposition_schema_sha256": doc.get("disposition_schema_sha256"),
                 "overlay_schema_sha256": doc.get("overlay_schema_sha256")}
        if doc["dimension"] == "consumer_evidence.operator_declaration":
            entry["operator_identity"] = doc.get("operator_identity")
            entry["attestation_ref"] = doc.get("attestation_ref")
        receipt_overlays.append(entry)
    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)
    return MergeResult(effective_snapshot=effective, derived_window_object_ids=derived,
                       receipt_overlays=receipt_overlays, diagnostics=[])
```

> Implementer notes: (1) the contributor windows are a **local** `contrib` dict passed to `derive_windows` (audit #9) — it is never written onto `effective`, so no scratch key can reach schema validation or serialization. (2) `check_cluster_completeness` compares the BASE slot (was it `not_observed`?) against the EFFECTIVE slot (did an overlay resolve it?); an already-observed `database_deps` (not an overlay target) never triggers OV015. (3) OV010's `captured_at`-unparseable branch is defense-in-depth (the schema's `iso_datetime` format already guards it, but per Invariant 7 do not rely on that). (4) `dataclass`/`field`/`copy` are imported at the module top (Task 1); do not re-import here.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: PASS — `=== OVERLAY LOADER SUITE: ALL PASS ===`.

- [ ] **Step 5: Commit**

```bash
git add disposition_overlay.py tests/test_overlay_loader.py
git commit -m "feat(overlay): load_and_merge orchestration + effective-view integrity + OV010 (Task 6)"
```

---

## Task 7: evidence-readiness receipt

**Files:**
- Modify: `check_disposition.py` (`build_receipt`: replace `production_eligible` with `evidence_ready`/`execution_authorized`; add overlay provenance, recency policy, `effective_view` flag)
- Test: `tests/test_check_disposition.py` (update the three existing receipt cases to the reframed fields)

**Interfaces:**
- Modifies: `build_receipt(..., production_eligible=...)` → `build_receipt(..., evidence_ready, execution_authorized=False, overlays=None, max_consumer_evidence_age_hours=None)`. The receipt dict drops `production_eligible` and adds `evidence_ready`, `execution_authorized: False`, `overlays` (provenance list from `MergeResult.receipt_overlays`), `max_consumer_evidence_age_hours`, and `effective_view: {"in_memory_only": True}`.

- [ ] **Step 1: Update the receipt tests to the reframed contract (RED)**

In `tests/test_check_disposition.py`, update `_receipt_pure`, `_bound_green_receipt`, and `_authoring_banner_and_receipt` to assert the new fields. Representative body for `_receipt_pure`:

```python
def _receipt_pure():
    dec = _decs([_decision("harden", "D-h1")])
    rec = cd.build_receipt(mode="preapply", now_iso="2026-07-10T21:00:00Z", expect_project_ref="fxoyniqnrlkxfligbxmg",
                           doc_bytes={"snapshot": b"{}"}, doc_paths={"snapshot": "/x"}, signer={"key_id": "k"},
                           snapshot_signature_sha256="00", gate_repo_sha="abc", checkout_bound=True,
                           evidence_ready=True, execution_authorized=False, overlays=[{"path": "o.json", "dimension": "consumer_evidence.static_repo", "raw_sha256": "aa"}],
                           max_consumer_evidence_age_hours=8760, roots=ROOTS, decisions=dec)
    return (rec.get("evidence_ready") is True and rec.get("execution_authorized") is False
            and "production_eligible" not in rec and rec["overlays"][0]["dimension"] == "consumer_evidence.static_repo"
            and rec["effective_view"] == {"in_memory_only": True})
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: FAIL — `build_receipt() got an unexpected keyword argument 'evidence_ready'`.

- [ ] **Step 3: Reframe `build_receipt`** in `check_disposition.py`:

```python
def build_receipt(*, mode, now_iso, expect_project_ref, doc_bytes, doc_paths, signer, snapshot_signature_sha256,
                  gate_repo_sha, checkout_bound, evidence_ready, execution_authorized=False, overlays=None,
                  max_consumer_evidence_age_hours=None, roots, decisions):
    """Evidence-readiness receipt (§2A): attests evidence readiness ONLY. It carries NO write-GO and is
    NOT an authorization token. `production_eligible` is replaced by `evidence_ready` +
    `execution_authorized: false` so no apply runner can read a receipt field as write authorization."""
    receipt = {"kind": "disposition_gate_receipt", "gate": "green", "mode": mode, "now": now_iso,
               "expect_project_ref": expect_project_ref, "inputs": {}, "evidence": [],
               "signer": signer, "snapshot_signature_sha256": snapshot_signature_sha256,
               "gate_repo_sha": gate_repo_sha, "checkout_bound": checkout_bound,
               "evidence_ready": evidence_ready, "execution_authorized": execution_authorized,
               "overlays": overlays or [], "max_consumer_evidence_age_hours": max_consumer_evidence_age_hours,
               "effective_view": {"in_memory_only": True}}
    # ... (unchanged from here: inputs hashing + evidence-ref resolution loop + sort) ...
```

Keep the rest of `build_receipt`'s body (the `for name, data in doc_bytes.items()` block through `receipt["evidence"].sort(...)`) exactly as-is.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: PASS (the three receipt cases green under the reframed fields; every other case unchanged).

- [ ] **Step 5: Commit**

```bash
git add check_disposition.py tests/test_check_disposition.py
git commit -m "feat(overlay): reframe gate receipt to evidence_ready + execution_authorized:false (Task 7)"
```

---

## Task 8: CLI wiring + end-to-end negatives + migrate main()-level baselines

**Files:**
- Modify: `check_disposition.py` (`main()`: `--overlay`, `--max-consumer-evidence-age-hours`; call `load_and_merge`; merge OV+SP diags; pass effective view + derived set to `run()`; wire the reframed receipt)
- Test: `tests/test_overlay_loader.py` (append e2e red→green + authorization-boundary + retain green + OV021-via-main cases); `tests/test_check_disposition.py` (migrate the `main()`-level e2e cases to the overlay model)

**Interfaces:**
- Consumes: `disposition_overlay.load_and_merge`, `disposition_overlay.load_overlay_contract`, `MergeResult`.
- Modifies: `main()` orchestration. New argv: `--overlay PATH` (`action="append"`, default `[]`), `--max-consumer-evidence-age-hours` (`type=float`, default `None`).

- [ ] **Step 1: Write the failing CLI e2e tests** — append to `tests/test_overlay_loader.py` and `_CASES`. These drive `check_disposition.main()` with real temp files:

```python
import contextlib
import io
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_disposition as cd  # noqa: E402
import disposition_trust as dt  # noqa: E402


def _wb(path, b):
    with open(path, "wb") as fh:
        fh.write(b if isinstance(b, (bytes, bytearray)) else json.dumps(b).encode("utf-8"))
    return path


def _pin_signer(pub):
    """Monkeypatch the trust anchor so the throwaway key resolves as the pinned 'test-signer' (tests
    only). Returns the saved TRUSTED_SIGNERS to restore in a finally."""
    from cryptography.hazmat.primitives import serialization
    fp = hashlib.sha256(pub.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
    saved = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS["test-signer"] = fp
    return saved


def _keys_dir(tmp, pub):
    from cryptography.hazmat.primitives import serialization
    kd = os.path.join(tmp, "keys"); os.makedirs(kd, exist_ok=True)
    _wb(os.path.join(kd, "test-signer.pub.pem"),
        pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return kd


def _capture_main(argv):
    # Catch SystemExit so these tests start RED cleanly BEFORE implementation: an unknown --overlay /
    # --max-consumer-evidence-age-hours makes argparse call sys.exit(2) (a BaseException the runner's
    # `except Exception` would NOT catch), which would otherwise crash the whole suite instead of
    # reporting a per-test FAIL. After the CLI flags exist, cd.main returns an int normally.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = cd.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 2
    return rc, buf.getvalue()


def _harden_docs(oid):
    # consumer_disposition 'unresolved' => SP022 does not force the consumer dims; required_observations
    # names in_data_api (a permitted-overlay target, base not_observed) as the sole gate-required dim.
    d = {"decision_id": "D-h1", "source_objects": [oid], "meaning_disposition": "preserve",
         "action_class": "harden", "decision_status": "accepted", "exposure_policy": "service_only",
         "consumer_disposition": "unresolved", "evidence_refs": ["query:x"], "technical_authority_approval": "TA-1"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "harden",
                "decision_ids": ["D-h1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-1"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _base_argv(tmp, cpath, dpath, epath, mpath, pub):
    return ["--snapshot", cpath, "--snapshot-sig", cpath + ".sig", "--decisions", dpath,
            "--entity-map", epath, "--manifest", mpath, "--now", NOW_ISO, "--mode", "preapply",
            "--expect-project-ref", "fxoyniqnrlkxfligbxmg", "--key-id", "test-signer",
            "--keys-dir", _keys_dir(tmp, pub), "--allow-unbound-checkout",
            "--max-consumer-evidence-age-hours", "8760", "--root", tmp]


def _write_harden_case(priv, pub, census):
    tmp = tempfile.mkdtemp(prefix="ov_e2e_")
    cb = _canon(census)
    cpath = _wb(os.path.join(tmp, "census.json"), cb); _wb(cpath + ".sig", _sign(census, priv)[1])
    decisions, manifest, em = _harden_docs("public.v")
    dpath = _wb(os.path.join(tmp, "dec.json"), _canon(decisions))
    epath = _wb(os.path.join(tmp, "ent.json"), _canon(em))
    mpath = _wb(os.path.join(tmp, "man.json"), _canon(manifest))
    return tmp, cb, _base_argv(tmp, cpath, dpath, epath, mpath, pub)


def _e2e_red_then_green():
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        tmp, cb, base = _write_harden_case(priv, pub, _zero_census([oid]))
        rc_red, _o = _capture_main(base)                          # RED: zero overlays -> OV018/OV015
        # GREEN: in_data_api observed-false (gate-required) + static_repo observed (a windowed contributor).
        # Consumer refs use the 'sha:' scheme so SP014 treats them as non-path (a bare id would be a path ref).
        ov_api = _overlay("in_data_api_exposed_schema", "platform_config",
                          [{"object_id": oid, "value": {"state": "observed", "value": False}}], census_bytes=cb)
        ov_static = _overlay("consumer_evidence.static_repo", "repository_scan",
                             [{"object_id": oid, "value": {"state": "observed", "found_consumers": 0, "ref": "sha:s1"}}], census_bytes=cb)
        opts = []
        for i, o in enumerate((ov_api, ov_static)):
            p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig); opts += ["--overlay", p]
        rpath = os.path.join(tmp, "receipt.json")
        rc_green, _o2 = _capture_main(base + opts + ["--receipt-out", rpath])
        receipt = json.load(open(rpath)) if os.path.exists(rpath) else {}
        return (rc_red == 1 and rc_green == 0 and receipt.get("evidence_ready") is True
                and receipt.get("execution_authorized") is False and "production_eligible" not in receipt)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


def _e2e_ov021_via_main():
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        census = _zero_census([oid])
        census["relations"][0]["consumer_evidence"]["observation_window"] = {"started_at": "2026-06-05T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}
        _tmp, _cb, base = _write_harden_case(priv, pub, census)   # non-zero base window, zero overlays
        rc, out = _capture_main(base)
        return rc == 1 and "OV021" in out
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


# ---- delete/retain/SP018 e2e helpers + the six named tests (audit round-4 F2) ----
def _write_case(priv, pub, census, docs, extra_roots=()):
    """Generalizes _write_harden_case to any (decisions, manifest, entity_map) + extra --root dirs."""
    tmp = tempfile.mkdtemp(prefix="ov_e2e_")
    cb = _canon(census)
    cpath = _wb(os.path.join(tmp, "census.json"), cb); _wb(cpath + ".sig", _sign(census, priv)[1])
    decisions, manifest, em = docs
    dpath = _wb(os.path.join(tmp, "dec.json"), _canon(decisions))
    epath = _wb(os.path.join(tmp, "ent.json"), _canon(em))
    mpath = _wb(os.path.join(tmp, "man.json"), _canon(manifest))
    argv = _base_argv(tmp, cpath, dpath, epath, mpath, pub)
    for r in extra_roots:
        argv += ["--root", r]
    return tmp, cb, argv


def _add_overlays(tmp, priv, overlays):
    opts = []
    for i, o in enumerate(overlays):
        p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig)
        opts += ["--overlay", p]
    return opts


def _consumer_overlay(dim, cb, ref, state="observed", **overrides):
    src = {"static_repo": "repository_scan", "runtime_logs": "runtime_logs",
           "external_clients": "external_client_inventory", "operator_declaration": "operator_declaration"}[dim]
    value = ({"state": "observed", "found_consumers": 0, "ref": ref} if state == "observed"
             else {"state": state, "found_consumers": None, "ref": None, "detail": "n/a"})
    return _overlay(f"consumer_evidence.{dim}", src, [{"object_id": "public.v", "value": value}], census_bytes=cb, **overrides)


def _in_data_api_overlay(cb, value, window=None):
    extra = {"observation_window": window} if window else {}
    return _overlay("in_data_api_exposed_schema", "platform_config",
                    [{"object_id": "public.v", "value": {"state": "observed", "value": value}}], census_bytes=cb, **extra)


def _delete_consumer_overlays(cb):
    """The SP027/SP022 consumer set for a no_consumer delete: static_repo/runtime_logs/operator_declaration
    observed (windowed contributors) + external_clients not_applicable (invokes the SP027 waiver)."""
    return [
        _consumer_overlay("static_repo", cb, "sha:s1"),  # producing_repo_sha default "d"*40 (required category)
        _consumer_overlay("runtime_logs", cb, "sha:r1", producing_repo_sha=None, producing_repo_sha_not_applicable_reason="runtime query"),
        _consumer_overlay("operator_declaration", cb, "sha:o1", producing_repo_sha=None,
                          producing_repo_sha_not_applicable_reason="operator", operator_identity="op-1", attestation_ref="att-1"),
        _consumer_overlay("external_clients", cb, None, state="not_applicable",
                          producing_repo_sha=None, producing_repo_sha_not_applicable_reason="no external clients"),
    ]


def _delete_docs(oid):
    d = {"decision_id": "D-d1", "source_objects": [oid], "meaning_disposition": "retire",
         "action_class": "delete", "decision_status": "accepted", "consumer_disposition": "no_consumer",
         "retention_disposition": {"policy": "delete_after", "recovery_proof": tcd._recovery_artifact()},
         "evidence_refs": ["query:x"], "technical_authority_approval": "TA-5"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "delete",
                "decision_ids": ["D-d1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-5"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _retain_docs(oid):
    d = {"decision_id": "D-r1", "source_objects": [oid], "meaning_disposition": "preserve",
         "action_class": "retain", "decision_status": "accepted", "consumer_disposition": "unresolved",
         "retention_disposition": {"policy": "retain", "recovery_proof": None},
         "evidence_refs": ["query:x"], "technical_authority_approval": "TA-r"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "retain",
                "decision_ids": ["D-r1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-r"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _run_case(docs, build_overlays, receipt=False, extra_roots=()):
    """Write a case, sign the overlays build_overlays(cb) produces, run cd.main, return (rc, out, receipt_path_or_None)."""
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub)
    try:
        tmp, cb, base = _write_case(priv, pub, _zero_census(["public.v"]), docs, extra_roots=extra_roots)
        argv = base + _add_overlays(tmp, priv, build_overlays(cb))
        rpath = None
        if receipt:
            rpath = os.path.join(tmp, "receipt.json"); argv += ["--receipt-out", rpath]
        rc, out = _capture_main(argv)
        return rc, out, (rpath if rpath and os.path.exists(rpath) else None)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


def _e2e_delete_missing_in_data_api_OV015():
    rc, out, _r = _run_case(_delete_docs("public.v"), _delete_consumer_overlays, extra_roots=[tcd._ROOT])
    return rc == 1 and "OV015" in out


def _e2e_delete_true_in_data_api_SP027():
    rc, out, _r = _run_case(_delete_docs("public.v"),
                            lambda cb: _delete_consumer_overlays(cb) + [_in_data_api_overlay(cb, True)], extra_roots=[tcd._ROOT])
    return rc == 1 and "SP027" in out


def _e2e_delete_false_noncovering_OV022():
    narrow = {"started_at": "2026-06-20T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}  # starts after S=06-05 -> not covering
    rc, out, _r = _run_case(_delete_docs("public.v"),
                            lambda cb: _delete_consumer_overlays(cb) + [_in_data_api_overlay(cb, False, window=narrow)], extra_roots=[tcd._ROOT])
    return rc == 1 and "OV022" in out


def _e2e_retain_no_overlay_OV018():
    rc, out, _r = _run_case(_retain_docs("public.v"), lambda cb: [])   # retain source relation has no contributor
    return rc == 1 and "OV018" in out


def _e2e_retain_green():
    rc, out, _r = _run_case(_retain_docs("public.v"),
                            lambda cb: [_in_data_api_overlay(cb, False), _consumer_overlay("static_repo", cb, "sha:s1")])
    return rc == 0


def _e2e_unaccepted_manifest_SP018_no_receipt():
    decisions, manifest, em = _harden_docs("public.v")
    manifest["status"] = "proposed"; manifest["technical_authority_approval"] = None   # not accepted -> SP018
    rc, out, receipt = _run_case((decisions, manifest, em),
                                 lambda cb: [_in_data_api_overlay(cb, False), _consumer_overlay("static_repo", cb, "sha:s1")], receipt=True)
    return rc == 1 and "SP018" in out and receipt is None   # no receipt is written on a RED gate


_CASES += [
    ("e2e_red_then_green", _e2e_red_then_green),
    ("e2e_ov021_via_main", _e2e_ov021_via_main),
    ("e2e_delete_missing_in_data_api_OV015", _e2e_delete_missing_in_data_api_OV015),
    ("e2e_delete_true_in_data_api_SP027", _e2e_delete_true_in_data_api_SP027),
    ("e2e_delete_false_noncovering_OV022", _e2e_delete_false_noncovering_OV022),
    ("e2e_retain_no_overlay_OV018", _e2e_retain_no_overlay_OV018),
    ("e2e_retain_green", _e2e_retain_green),
    ("e2e_unaccepted_manifest_SP018_no_receipt", _e2e_unaccepted_manifest_SP018_no_receipt),
]
```

> All e2e matrix items are now **pinned tests above** (audit round-4 F2): the OV015/SP027/OV022 delete split, retain green + OV018, and SP018-with-no-receipt. The delete cases reuse `tcd._recovery_artifact()` + `tcd._ROOT` for the SP014 recovery proof (`extra_roots=[tcd._ROOT]`) and the full SP027/SP022 consumer set; they vary only the `in_data_api` overlay (absent / observed-true / observed-false-non-covering) to exercise each of the three coherent diagnostics.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `cd.main` rejects unknown `--overlay`/`--max-consumer-evidence-age-hours`, or the effective view is never built.

- [ ] **Step 3: Wire the loader into `main()`**

Add the argparse options (near `check_disposition.py:583`):

```python
    ap.add_argument("--overlay", action="append", default=[], dest="overlays_in", help="signed evidence overlay (repeatable); each needs a detached <PATH>.sig sidecar.")
    ap.add_argument("--max-consumer-evidence-age-hours", type=float, default=None, dest="max_consumer_evidence_age_hours", help="REQUIRED recency floor for derived consumer windows; absent/non-finite => OV016 (fail-closed).")
```

**First, extract the raw-validation preamble (audit F1).** Refactor `run()`'s schema-validate + kind-pin preamble (`check_disposition.py:533-540`) into a shared helper, so `main()` can run it on the RAW documents before the overlay loader:

```python
def validate_documents(docs, validator):
    """SP001 schema-validation + per-input kind-pin. Shared by run() (on the effective view, post-merge)
    and main() (on the RAW documents, BEFORE the overlay loader, audit F1) so a validly-signed but
    malformed census is a coded SP001 red rather than an uncaught raise inside load_and_merge."""
    diags = schema_validate(docs, validator)
    for expected, doc in docs.items():
        if isinstance(doc, dict) and doc.get("kind") != expected:
            diags.append(Diagnostic("SP001", f"{expected}:kind", f"expected kind={expected!r}, got {doc.get('kind')!r}"))
    return diags
```

and make `run()` call it (behavior-preserving):

```python
def run(snapshot, decisions, entity_map, manifest, now, mode, roots, validator, snapshot_path=None, expect_project_ref=None, derived_window_object_ids=None):
    docs = {"evidence_snapshot": snapshot, "decisions_file": decisions, "entity_map": entity_map, "cluster_manifest": manifest}
    diags = validate_documents(docs, validator)
    if diags:
        return sorted(diags, key=lambda x: x.key())
    diags = semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path, expect_project_ref, derived_window_object_ids)
    return sorted(diags, key=lambda x: x.key())
```

**Then**, after the SP026 signature gate succeeds and `snapshot`/`decisions`/`manifest` are parsed (after `check_disposition.py:642`) and BEFORE `run(...)`, insert the raw-validation stage and the overlay loader (preapply only):

```python
    # Load the read-once schema contract ONCE (both validators + schema hashes) — used for raw
    # validation, overlay validation/OV020, and effective-view validation (audit round-4 F1). No stage
    # reopens the schemas; the overlay-enabled CLI path NEVER calls _validator().
    import disposition_overlay as ovl
    try:
        contract = ovl.load_overlay_contract()
    except ovl.OverlayRegistryError as exc:
        print(f"OV008 overlay: {exc}"); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1

    # Raw-document SP001 + kind validation (audit F1): BEFORE the overlay loader, using the contract's
    # census validator, so a validly-signed but malformed census is a coded SP001 red — never an
    # uncaught raise inside load_and_merge.
    raw_docs = {"evidence_snapshot": snapshot, "decisions_file": decisions, "entity_map": entity_map, "cluster_manifest": manifest}
    raw_diags = validate_documents(raw_docs, contract.disposition_validator)
    if raw_diags:
        for dg in sorted(raw_diags, key=lambda x: x.key()):
            print(dg.render())
        print(f"=== DISPOSITION GATE ({args.mode}): {len(raw_diags)} BLOCKING ===")
        return 1

    effective_snapshot = snapshot
    derived_ids = None
    overlay_receipt = []
    if args.mode == "preapply":
        try:
            overlay_inputs = []
            for op in args.overlays_in:
                abspath = os.path.abspath(op)
                with open(abspath, "rb") as fh:
                    ob = fh.read()
                with open(abspath + ".sig", "rb") as fh:
                    sb = fh.read()
                overlay_inputs.append((abspath, abspath + ".sig", ob, sb))
        except OSError as exc:
            print(f"OV008 overlay: {exc}"); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        mres = ovl.load_and_merge(census=snapshot, census_bytes=doc_bytes["snapshot"], overlay_inputs=overlay_inputs,
                                  manifest=manifest, decisions=decisions, expect_project_ref=args.expect_project_ref,
                                  now=now, max_consumer_evidence_age_hours=args.max_consumer_evidence_age_hours,
                                  max_staleness_hours=manifest.get("max_staleness_hours"),
                                  resolved_signer=signer, contract=contract)
        if mres.diagnostics:
            for code, locus, msg in sorted(mres.diagnostics):
                print(f"{code} {locus}: {msg}")
            print(f"=== DISPOSITION GATE ({args.mode}): {len(mres.diagnostics)} BLOCKING ===")
            return 1
        effective_snapshot, derived_ids, overlay_receipt = mres.effective_snapshot, mres.derived_window_object_ids, mres.receipt_overlays

    # Effective-view SP001 + semantic gate, using the SAME contract census validator (not _validator()).
    diags = run(effective_snapshot, decisions, entity_map, manifest, now, args.mode, roots, contract.disposition_validator,
                os.path.abspath(args.snapshot), args.expect_project_ref, derived_ids)
```

> Note: `signer` here is the `ResolvedSigner` already produced by the SP026 signature gate (`check_disposition.py:635`) — the overlay loader reuses the SAME pinned key (no second `resolve_pinned_key`) and reads its `key_id`/`spki_sha256` into the receipt (F3). Both the raw-doc validation and the effective-view `run(...)` use `contract.disposition_validator` (built from the same in-hand `disp_bytes` as the overlay validator + the OV020 hashes), so **no schema stage re-reads `disposition.schema.json`** and `_validator()` is never called on this path (audit round-4 F1). Guard: preapply is never signature-exempt, so `signer` is always set here.

Update the receipt call (`check_disposition.py:660`) to the reframed signature:

```python
            receipt = build_receipt(mode=args.mode, now_iso=args.now, expect_project_ref=args.expect_project_ref,
                                    doc_bytes=doc_bytes, doc_paths=doc_paths, signer=signer_meta,
                                    snapshot_signature_sha256=snapshot_signature_sha256,
                                    gate_repo_sha=gate_repo_sha, checkout_bound=checkout_bound,
                                    evidence_ready=True, execution_authorized=False, overlays=overlay_receipt,
                                    max_consumer_evidence_age_hours=args.max_consumer_evidence_age_hours,
                                    roots=roots, decisions=decisions)
```

- [ ] **Step 4: Migrate the `main()`-level baselines in `tests/test_check_disposition.py`**

The `run()`-level SP0xx cases are untouched. Only the cases that drive `cd.main()` end-to-end in preapply (`_sig_gate_e2e`, `_preapply_anchor_green`, `_bound_green_receipt`, `_authoring_banner_and_receipt`) now hit the unconditional overlay path. Migrate each to a **zero-width-window census + a full set of signed overlays** (reuse the `_zero_census`/`_overlay`/`_sign`/`_pin_signer` helpers, importing them or duplicating the minimal set into this file), passing `--max-consumer-evidence-age-hours 8760` and the `--overlay` files. Assert the same green outcomes (exit 0, banner, receipt) they asserted before, now with `evidence_ready`.

- [ ] **Step 5: Run both suites to verify they pass**

Run: `uv run --project . --locked python tests/test_overlay_loader.py` → PASS.
Run: `uv run --project . --locked python tests/test_check_disposition.py` → PASS.

- [ ] **Step 6: Register the loader suite in governed CI (audit F6)**

In `.github/workflows/schema-placement-ci.yml`, add `test_overlay_loader` to the `suites` job's loop (it now lists both new suites):

```yaml
          for t in test_disposition_schema test_check_disposition test_collect_disposition test_verify_census test_disposition_trust test_disposition_provenance test_overlay_schema test_overlay_loader; do
```

- [ ] **Step 7: Commit**

```bash
git add check_disposition.py tests/test_overlay_loader.py tests/test_check_disposition.py .github/workflows/schema-placement-ci.yml
git commit -m "feat(overlay): raw-input validation + wire --overlay into main() + e2e + migrate baselines + CI (Task 8)"
```

---

## Task 9: full regression + finish

**Files:** none (verification + branch finish).

- [ ] **Step 1: Run the full schema-placement suite**

Run each script-runner test (they are the CI runners; pytest is not a locked dep):

```bash
for t in tests/test_overlay_schema.py tests/test_overlay_loader.py tests/test_check_disposition.py \
         tests/test_collect_disposition.py tests/test_disposition_schema.py \
         tests/test_disposition_trust.py tests/test_verify_census.py tests/test_disposition_provenance.py; do
  echo "=== $t ==="; uv run --project . --locked python "$t" || exit 1
done
```
Expected: every suite prints its `ALL PASS` banner and exits 0.

- [ ] **Step 2: Confirm the committed-census CI gate is unaffected**

Run: `bash ci/verify_committed_census.sh`
Expected: `no census artifacts added on this branch ... nothing to verify` (this packet adds no census) OR `ALL COMMITTED CENSUS ARTIFACTS VERIFIED`. It must NOT fail — the overlay packet does not touch `disposition.schema.json`, the collector, the trust anchor, or `keys/`.

- [ ] **Step 3: Spec-coverage self-check**

Confirm every OV code `OV001–OV022` has at least one pinned failing test, every Global-Constraints negative-test-matrix item is present, and the three ratified acceptance tests are green: `OV021-fires-with-zero-overlays` (Task 8a), `remove-marker→original-SP009` (Task 4 `_sp009_provenance_conditional`), and `duplicate-src-object→single-derivation` (Task 4). List any gap and add the test.

- [ ] **Step 4: Cross-engine IRP + finish the branch**

Per the mandatory Independent Review Protocol, run the cross-engine Codex pass over the branch (`apex-jobs review-run --review-head schema-placement/signed-overlay --base-ref main`, or the direct `codex exec review --base main` fallback) plus a Claude grounded review, and fold any findings. Then use `superpowers:finishing-a-development-branch` — verify the full suite green, present the operator the merge options, and (operator-gated) open the squash PR. **No production apply, no evidence collection, no DB access** happens here — merging the overlay tooling PRECEDES any evidence collection (spec §10).

---

## Self-Review

**1. Spec coverage.** Every section maps to a task: §2A control separation → Task 7 receipt + Task 8 authorization-boundary test; §3 time model + provenance-conditional SP009 → Task 4; §4 overlay contract + `overlay.schema.json` + read-once `OverlayContract` offline registry → Task 1; §5 steps 0-10 → SP028 gate pre-existing (unchanged, still step 0), raw-input SP001/kind validation before the loader → Task 8 (audit F1), read-once/verify/parse → Task 2, bind → Task 2, per-overlay window OV009 → Task 3 (audit F2), freshness/target/conflict → Tasks 3+6, effective view + OV021 + derive + OV022 + OV015 → Tasks 3/4/5/6, semantic gate on effective view → Task 8 wiring, receipt → Task 7; §6 reject matrix `OV001–OV022` → **every code has a pinned failing test** (OV001/002/003/020 T2; OV004/005/006/007/009/012/013/014/019/021 T3; OV011/016/017/018 T4; OV022 T5; OV008 T1; OV010/OV015 T6); §7 signature handling → Task 2 (`verify_overlay` reuses the pinned anchor); §8 definer-view reconciliation/cluster admissibility → Appendix-A views are data; `OV015` cluster-completeness is implemented as `check_cluster_completeness` in Task 6 with a dedicated negative test `ov015_missing_gate_required_dimension` (audit F7); §9 testing strategy → the whole negative-first suite (registered in CI, audit F6); §10 out-of-scope holds → Global Constraints; §11 ratified decisions → folded (T1/T2/T3 in Global Constraints). Cross-engine plan-audit findings F1–F9 + contributor-map instruction are all folded (see the fold table below).

**2. Placeholder scan.** No placeholders remain. Every step carries complete, runnable code, including the Task 8 e2e suite: `_e2e_red_then_green`, `_e2e_ov021_via_main`, and the six named delete/retain/SP018 tests (`_e2e_delete_missing_in_data_api_OV015`, `_e2e_delete_true_in_data_api_SP027`, `_e2e_delete_false_noncovering_OV022`, `_e2e_retain_no_overlay_OV018`, `_e2e_retain_green`, `_e2e_unaccepted_manifest_SP018_no_receipt`) are all real `cd.main` tests with concrete assertions, registered in `_CASES` (audit round-4 F2 + F3). No `TBD`/`handle edge cases`/`similar to Task N`/`... return True` anywhere.

**3. Type consistency.** `MergeResult` fields (`effective_snapshot`, `derived_window_object_ids`, `receipt_overlays`, `diagnostics`) are used identically in Tasks 6+8. Diagnostics are `(code, locus, message)` tuples throughout the loader; `check_disposition` prints them directly (it does not wrap them in `Diagnostic`, avoiding the circular import). `derive_windows` returns `(diags, set)`; `load_and_merge` consumes that shape. `build_receipt`'s reframed keyword set (`evidence_ready`, `execution_authorized`, `overlays`, `max_consumer_evidence_age_hours`) matches its call site in Task 8 and its tests in Task 7. `semantic_check`/`run` gain the same `derived_window_object_ids=None` trailing parameter, kept consistent at the call site.

---

## Ratified layering + cross-engine plan-audit fold (rev 2, 2026-07-12)

**Layering — RATIFIED by the operator's cross-engine plan audit.** The unconditional loader model stands: `OV021` + the overlay loader run in `main()`/`disposition_overlay` (unconditional in preapply); `semantic_check`/`run` gain only the `derived_window_object_ids`-conditional SP009 branch (default `None` = original behavior). A bare `check_disposition --mode preapply` (no `--overlay`) requires a zero-width base census (OV021) and yields no evidence readiness without overlays — the production model. The four `main()`-level e2e baselines migrate to the overlay model (Task 8 Step 4); the `run()`-level SP0xx baselines are untouched.

**Audit findings folded (all nine + the contributor-map instruction):**

| Finding | Fold |
|---|---|
| F1 (High) raw docs consumed before SP001 | `validate_documents` extracted; `main()` runs SP001+kind on the raw docs **before** the loader; effective view re-validated by `run()` (Task 8). |
| F2 (High) OV009 not per-overlay | `check_observation_window()` (started<ended, ended≤captured, ended≤now) applied to ALL six dimensions before assignments (Tasks 3, 6). |
| F3 (High) receipt binding incomplete | `receipt_overlays` binds path, raw+sidecar SHA-256, sidecar path, signer key_id+SPKI, dimension+object_ids+count, source_hash, schema hashes (Tasks 6, 7). |
| F4 (Med) schema validate vs hash read different bytes | read-once `OverlayContract` (bytes+hashes+registry+validator); schemas never reopened during a run (Tasks 1, 6). |
| F5 (Med) fixtures not schema-valid / incoherent times | `_zero_census` reuses `tcd._snapshot`/`_rel` (all required fields); one canonical, coherent fixture clock (Task 2). |
| F6 (Med) new suites absent from CI | `test_overlay_schema` + `test_overlay_loader` added to the governed `suites` job (Tasks 1, 8). |
| F7 (Med) OV015 unimplemented/untested | `check_cluster_completeness()` + dedicated `ov015_missing_gate_required_dimension` test (Task 6). |
| F8 (Med) offline-registry test false proof | replaced with a real unseeded-`$ref` → `Unresolvable`/coded-OV008 test (Tasks 1, 3); no network. |
| F9 (Low) null-reason not IFF | OV019/OV012 reject reason-with-non-null-hash too (Task 3). |
| #9 contributor map on effective | contributor windows passed as a separate local `contrib_by_oid` dict; never stashed on `effective` (Tasks 4, 6). |

**Focused plan re-audit (instruction #10) — DONE, cross-engine.** Claude focused self-review: folds real + internally consistent. Codex (`codex exec review --base main`, `-m gpt-5.5`, sandbox-bypassed) found **2 NEW P2s** (neither re-raising F1–F9), both folded → **rev 3**:

| Codex P2 | Fix |
|---|---|
| OV022 emitted for a *missing* in_data_api overlay → short-circuits before `run()` can fire SP027 | OV022 records the window only for an **observed-false** overlay and **defers**. The **rev-4 refinement** (audit F2) then routes the deferred cases coherently: **OV015** (missing) / **SP027** (observed-true) / **OV022** (observed-false, inadequate window). Task-5 unit + Task-8 e2e assert all three. |
| Absent/non-finite `max_consumer_evidence_age_hours` checked after the OV018 short-circuit → a zero-contributor relation masks the missing flag | Recency-policy `OV016` is a **deterministic precheck at the top of `derive_windows`**, before any per-relation contributor check. |

**Second plan re-audit (2026-07-12) → rev 4 (1 High + 4 Med, all folded):** F1 loader short-circuits on any schema failure (non-object/malformed-`assignments` → OV008, no `AttributeError`); F2 the coherent `in_data_api` delete split OV015(missing)/SP027(observed-true)/OV022(observed-false,bad-window) — matrix + Task-5 unit + Task-8 e2e updated; F3 `_e2e_red_then_green` + `_e2e_ov021_via_main` are real `cd.main` tests; F4 real `validate_overlay`→coded-OV008 unseeded-`$ref` test; F5 three `producing_repo_sha` categories (required/forbidden/conditional) with pos+neg tests.

**Third plan re-audit (2026-07-12) → rev 5 (1 High + 1 Med + 1 Low, folded):** F1 read-once completeness — `OverlayContract` holds both validators, loaded once; the overlay-enabled CLI path never calls `_validator()` (no `disposition.schema.json` re-read across the raw / OV020 / effective stages); F2 six named, registered, real `cd.main` e2e tests for the delete/retain/SP018 matrix items; F3 corrected self-review placeholder scan.

Convergence: the design converged 3→1→0 HIGH over the spec's 3 IRP rounds; the plan converged 9 → 2 → 5 → 3 → 0 over four plan-audit rounds (each round's findings were newly-surfaced correctness/coverage gaps, not regressions). A final **narrow diff review** should prove no `_validator()` call remains in the overlay-enabled CLI path and all six new e2e tests start RED (per the operator's instruction); if clean, the build GO is authorized without another broad plan audit. Implementation, evidence collection, DB access, production, A1–A3, and the apply runner remain HELD.
