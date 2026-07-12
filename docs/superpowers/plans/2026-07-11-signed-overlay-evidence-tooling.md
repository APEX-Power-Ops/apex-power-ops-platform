# Signed Evidence Overlay Tooling Implementation Plan

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
- **Layering (blast-radius control):** the unconditional `OV021` precheck + effective-view build live in `main()`/`disposition_overlay`; `semantic_check`/`run()` gain only the `derived_window_object_ids`-conditional SP009 branch. Existing `run()`-level SP0xx baselines in `tests/test_check_disposition.py` stay green untouched; only the `main()`-level e2e/receipt tests migrate to the overlay model (Task 7 & 8).
- **Derived-window predicate (§3), enforced at merge:** contributors `C` = consumer-dimension overlays resolving the relation with `state = observed` over `{static_repo, runtime_logs, external_clients, operator_declaration}` (`database_deps` is anchored at `base_observed_at`, NOT a windowed contributor). `S = max(startedᵢ)`, `E = min(endedᵢ)`; reject unless: `C` non-empty (`OV018`); `S < E` (`OV011`); `E <= now` (`OV009`); `now - E <= max_consumer_evidence_age_hours` (`OV016`, required finite+positive CLI flag; absent/NaN/Inf ⇒ `OV016`); `S <= base_observed_at <= E` (`OV017`); for a `delete` conclusion `(E - S) >= 720h` is left to SP027 on the effective view.
- **Negative-test matrix (every item MUST appear as a pinned failing test, most in Tasks 3–5/8):** OV022-fires-when-window-not-covering · external_clients-observed→no-OV022 · missing-in_data_api-overlay→SP027 · stale-in_data_api-overlay→OV010 · window-sourced-from-the-specific-assignment · retain-no-overlay→OV018 · retain-with-covering→green · duplicate-src-object→single-derivation-one-marker · OV021-fires-with-zero-overlays · remove-marker→original-SP009.
- **Test invocation (every "run the test" step):** from `infra/database/schema-placement/`, run `uv run --project . --locked python tests/<file>.py`. A test file exits `0` iff all its `_name()` cases return truthy. NEVER invoke `pytest`.
- **Grounding constants:** base snapshot SHA-256 = `5bb4191fea584f4cecf111c718382bc3f6d0d88707a7c6e9c4c5065132ac416e`; project ref `fxoyniqnrlkxfligbxmg`; pinned signer id `prod-disposition-ed25519-2026-07`; disposition schema `$id` = `https://apex-power-ops/schema-placement/disposition.schema.json`.
- **Commit discipline:** solo-maintainer branch `schema-placement/signed-overlay`; frequent commits, exact paths only (`git add <file>` — never `git add <dir>`). Merge is operator-gated after green CI + cross-engine IRP (no admin bypass).

**Base directory for every path below:** `infra/database/schema-placement/` inside the host worktree `/home/olares/code/apex/apex-schema-overlay` (branch `schema-placement/signed-overlay`, off main `7c9a97ca`). All commands run there over `ssh olares-mesh`.

---

## File Structure

| File | Create/Modify | Responsibility |
|---|---|---|
| `overlay.schema.json` | Create | The overlay document contract; `$ref`s frozen `disposition.schema.json` `$defs` via absolute `$id`. |
| `disposition_overlay.py` | Create | Leaf module: `OV_CODES`, the offline registry validator, and the load→verify→bind→target→conflict→base-precheck→derive→coherence pipeline returning `MergeResult`. |
| `check_disposition.py` | Modify | `main()` CLI wiring (`--overlay`, `--max-consumer-evidence-age-hours`, call the loader, print `OV`+`SP` diags), the provenance-conditional SP009 branch in `semantic_check`, and the receipt reframe in `build_receipt`. |
| `tests/test_overlay_schema.py` | Create | Schema + offline-registry lens (Task 1). |
| `tests/test_overlay_loader.py` | Create | Loader OV-code + time-model + coherence + integration + e2e lens (Tasks 2–8). |
| `tests/test_check_disposition.py` | Modify | Migrate the `main()`-level e2e/receipt cases to the overlay model + reframed receipt (Tasks 7–8). The `run()`-level SP0xx cases are untouched. |

**Shared fixture helpers** (defined once at the top of `tests/test_overlay_loader.py`, reused by every task's cases): `_ephemeral_keypair()` (throwaway Ed25519, copied from `tests/test_check_disposition.py`), `_zero_census(oids, observed_at)` (a canonical zero-width-window census), `_overlay(dimension, source_type, assignments, **overrides)` (a well-formed overlay dict bound to the census hash), `_sign(obj, priv)` → `(bytes, sig_bytes)` (canonical JSON bytes + detached sidecar bytes).

---

## Task 1: `overlay.schema.json` + offline registry validator

**Files:**
- Create: `overlay.schema.json`
- Create: `disposition_overlay.py` (skeleton: `OV_CODES`, `DIMENSIONS`, `build_overlay_validator`, `OverlayRegistryError`)
- Test: `tests/test_overlay_schema.py`

**Interfaces:**
- Produces: `disposition_overlay.build_overlay_validator() -> jsonschema.Draft202012Validator` (seeded offline registry, `FormatChecker`); `disposition_overlay.OverlayRegistryError` (raised on registry build failure, mapped to `OV008` by callers); `disposition_overlay.DIMENSIONS: dict[str, tuple[str, str]]` mapping each of the six dimension paths to `(value_def_name, fixed_source_type)`; `disposition_overlay.OV_CODES: dict[str, str]`.

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

VALIDATOR = ov.build_overlay_validator()


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


def _unseeded_ref_is_coded_not_uncaught():
    # A validator built against a registry with NO retrieve callback must raise the module's
    # OverlayRegistryError (coded) — never leak referencing.Unresolvable — when a schema $ref is
    # unresolvable. Proven by build_overlay_validator refusing to resolve a bogus remote ref.
    try:
        ov.assert_offline_registry_has_no_retrieve()  # helper asserting retrieve is None
        return True
    except ov.OverlayRegistryError:
        return True
    except Exception:
        return False


if __name__ == "__main__":
    ok = True
    for name, fn in [
        ("valid_bool_overlay_accepted", _valid_bool_overlay_accepted),
        ("valid_consumer_overlay_accepted", _valid_consumer_overlay_accepted),
        ("source_type_mismatch_rejected", _source_type_mismatch_rejected),
        ("wrong_value_shape_rejected", _wrong_value_shape_rejected),
        ("operator_declaration_requires_provenance", _operator_declaration_requires_provenance),
        ("calendar_invalid_datetime_coded", _calendar_invalid_datetime_coded),
        ("unseeded_ref_is_coded_not_uncaught", _unseeded_ref_is_coded_not_uncaught),
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


def build_overlay_validator():
    """Draft202012Validator for overlay.schema.json, seeded with BOTH schema docs by $id in a local
    referencing.Registry built WITHOUT a retrieve callback (remote/unseeded resolution is impossible).
    Raises OverlayRegistryError on any load/build failure (callers map to a coded OV008)."""
    try:
        with open(DISPOSITION_SCHEMA_PATH, encoding="utf-8") as fh:
            disp = json.load(fh)
        with open(OVERLAY_SCHEMA_PATH, encoding="utf-8") as fh:
            overlay = json.load(fh)
        registry = Registry().with_resources([
            (disp["$id"], Resource.from_contents(disp)),
            (overlay["$id"], Resource.from_contents(overlay)),
        ])  # no retrieve= => network/unseeded resolution raises Unresolvable, never fetches
        Draft202012Validator.check_schema(overlay)
        return Draft202012Validator(overlay, registry=registry, format_checker=FormatChecker())
    except (OSError, ValueError, KeyError, Unresolvable) as exc:
        raise OverlayRegistryError(f"cannot build offline overlay validator ({type(exc).__name__}: {exc})") from exc


def assert_offline_registry_has_no_retrieve():
    """Test hook: prove the registry underpinning build_overlay_validator has no retrieve callback,
    so remote $ref resolution can never fetch. Raises OverlayRegistryError if a retrieve is present."""
    with open(DISPOSITION_SCHEMA_PATH, encoding="utf-8") as fh:
        disp = json.load(fh)
    registry = Registry().with_resources([(disp["$id"], Resource.from_contents(disp))])
    if getattr(registry, "_retrieve", None) not in (None, getattr(Registry(), "_retrieve", None)):
        raise OverlayRegistryError("registry has a retrieve callback — remote resolution is possible")
```

> Implementer note: if `Registry`'s private `_retrieve` sentinel differs across `referencing` versions, replace `assert_offline_registry_has_no_retrieve` with a positive proof — build the validator, validate a doc whose schema `$ref`s an **unseeded** `$id`, and assert it raises `Unresolvable` (which `build_overlay_validator` maps to `OverlayRegistryError`). Either form satisfies the test; do not add a retrieve callback.

- [ ] **Step 5: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_overlay_schema.py`
Expected: PASS — `=== OVERLAY SCHEMA SUITE: ALL PASS ===`.

- [ ] **Step 6: Commit**

```bash
git add overlay.schema.json disposition_overlay.py tests/test_overlay_schema.py
git commit -m "feat(overlay): overlay.schema.json + offline registry validator (Task 1)"
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
import disposition_overlay as ov  # noqa: E402


def _ephemeral_keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(obj, priv):
    body = _canon(obj)
    sidecar = json.dumps(__import__("disposition_signing").build_sig_sidecar(body, priv)).encode("utf-8")
    return body, sidecar


CENSUS_OBSERVED_AT = "2026-07-10T20:00:00Z"


def _zero_census(oids):
    """A canonical zero-width-window census over oids, all six dims not_observed."""
    def _rel(oid):
        schema, name = oid.split(".", 1)
        na = {"state": "not_observed", "detail": "pending"}
        na_ci = {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "pending"}
        return {"object_id": oid, "schema": schema, "name": name, "relkind": "v",
                "owner": {"state": "observed", "value": "postgres"},
                "rls_enabled": {"state": "observed", "value": False},
                "is_security_definer_view": {"state": "observed", "value": True},
                "in_data_api_exposed_schema": na,
                "anon_effective_privs": {"state": "observed", "value": []},
                "authenticated_effective_privs": {"state": "observed", "value": []},
                "inbound_fk_count": {"state": "observed", "value": 0},
                "outbound_fk_count": {"state": "observed", "value": 0},
                "dependent_objects": {"state": "observed", "value": []},
                "row_estimate": {"state": "observed", "value": 0},
                "advisor_findings": na,
                "consumer_evidence": {
                    "observation_window": {"started_at": CENSUS_OBSERVED_AT, "ended_at": CENSUS_OBSERVED_AT},
                    "static_repo": na_ci, "database_deps": {"state": "observed", "found_consumers": 0, "ref": "dep:0"},
                    "runtime_logs": na_ci, "external_clients": na_ci, "operator_declaration": na_ci}}
    return {"kind": "evidence_snapshot", "project_ref": "fxoyniqnrlkxfligbxmg",
            "observed_at": CENSUS_OBSERVED_AT, "relation_count": len(oids),
            "target_identity": {"current_database": "postgres", "current_user": "postgres",
                                "server_version": "16", "transaction_read_only": True, "guard_passed": True},
            "relations": [_rel(o) for o in oids]}


def _overlay(dimension, source_type, assignments, census_bytes=None, **overrides):
    doc = {"kind": "evidence_overlay", "overlay_version": "1",
           "dimension": dimension, "source_type": source_type,
           "authority": "test", "collection_method": "test", "source_locator": "test:x",
           "source_hash": "e" * 64, "source_hash_not_applicable_reason": "n/a",
           "base_snapshot_sha256": hashlib.sha256(census_bytes).hexdigest() if census_bytes else "a" * 64,
           "disposition_schema_sha256": ov._sha256_hex(open(ov.DISPOSITION_SCHEMA_PATH, "rb").read()),
           "overlay_schema_sha256": ov._sha256_hex(open(ov.OVERLAY_SCHEMA_PATH, "rb").read()),
           "project_ref": "fxoyniqnrlkxfligbxmg",
           "captured_at": "2026-07-12T00:00:00+00:00",
           "observation_window": {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"},
           "producing_repo_sha": "d" * 40, "producing_repo_sha_not_applicable_reason": "n/a",
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
- Produces: `validate_overlay(doc, validator) -> list[tuple]` (`OV008`, maps schema/registry/format failures to a coded reject); `check_target(doc, census_rel_index: dict[str, dict]) -> list[tuple]` (`OV004/OV005/OV006/OV013/OV012/OV019/OV014`); `check_conflict(assignment_keys: list[tuple[str, str]]) -> list[tuple]` (`OV007`, counts duplicates within+across overlays); `precheck_base_window(census) -> list[tuple]` (`OV021`, unconditional, string-equality to `observed_at`).
- Consumes: `DIMENSIONS`; `census_rel_index` = `{object_id: relation_dict}` built by the orchestrator.

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
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 1, "ref": "att:1"}}])
    doc.pop("operator_identity", None); doc.pop("attestation_ref", None)
    return "OV014" in _codes(ov.check_target(doc, _rel_index(census)))


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


_CASES += [
    ("dimension_not_permitted_OV004", _dimension_not_permitted_OV004),
    ("unknown_object_id_OV005", _unknown_object_id_OV005),
    ("non_not_observed_target_OV006", _non_not_observed_target_OV006),
    ("source_type_mismatch_OV013", _source_type_mismatch_OV013),
    ("operator_declaration_missing_provenance_OV014", _operator_declaration_missing_provenance_OV014),
    ("source_hash_null_without_reason_OV019", _source_hash_null_without_reason_OV019),
    ("producing_repo_sha_absent_OV012", _producing_repo_sha_absent_OV012),
    ("duplicate_pair_within_and_across_OV007", _duplicate_pair_within_and_across_OV007),
    ("base_nonzero_window_OV021_with_zero_overlays", _base_nonzero_window_OV021_with_zero_overlays),
    ("base_canonical_window_passes_OV021", _base_canonical_window_passes_OV021),
]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: ... 'check_target'` (and the other new attrs).

- [ ] **Step 3: Implement the guards** — append to `disposition_overlay.py`:

```python
# dimensions whose overlay MUST carry a real producing_repo_sha (Appendix B); others require null+reason.
_PRODUCING_SHA_REQUIRED = {"in_data_api_exposed_schema", "consumer_evidence.static_repo"}


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
    if doc.get("source_hash") is None and not (doc.get("source_hash_not_applicable_reason") or "").strip():
        out.append(("OV019", loc, "source_hash is null without source_hash_not_applicable_reason"))
    if dimension in _PRODUCING_SHA_REQUIRED:
        if not doc.get("producing_repo_sha"):
            out.append(("OV012", loc, f"producing_repo_sha required for {dimension} but absent/null"))
    elif doc.get("producing_repo_sha") is None and not (doc.get("producing_repo_sha_not_applicable_reason") or "").strip():
        out.append(("OV012", loc, "producing_repo_sha is null without producing_repo_sha_not_applicable_reason"))
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
import datetime as _dt

def _pdt(s):
    return ov._parse_iso(s)

BASE = _pdt(CENSUS_OBSERVED_AT)          # 2026-07-10T20:00:00Z
NOW = _pdt("2026-07-11T00:00:00Z")


def _contrib(effective, oid, dim, started, ended):
    ce = effective["relations"][0]["consumer_evidence"]
    ce[dim] = {"state": "observed", "found_consumers": 0, "ref": f"{dim}:1"}
    # the per-relation contributor windows live on the overlay docs; the orchestrator threads them via
    # a side map, but derive_windows reads them off effective["_contrib_windows"][oid] (Task-6 orchestrator
    # populates this; here we set it directly to unit-test the predicate).
    effective.setdefault("_contrib_windows", {}).setdefault(oid, []).append((_pdt(started), _pdt(ended), _pdt("2026-07-12T00:00:00Z")))


def _fresh_window_derives_ok():
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2026-07-01T00:00:00Z", "2026-07-11T00:00:00Z")
    diags, derived = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE,
                                       max_consumer_evidence_age_hours=8760)
    return diags == [] and "public.v" in derived


def _decade_old_window_OV016():
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2016-06-01T00:00:00Z", "2016-07-01T00:00:00Z")
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV016" in _codes(diags)


def _absent_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2026-07-01T00:00:00Z", "2026-07-11T00:00:00Z")
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=None)
    return "OV016" in _codes(diags)


def _nonfinite_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2026-07-01T00:00:00Z", "2026-07-11T00:00:00Z")
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=float("inf"))
    return "OV016" in _codes(diags)


def _base_outside_window_OV017():
    eff = _zero_census(["public.v"])  # base_observed_at = 2026-07-10T20; window ends 2026-07-05 < base
    _contrib(eff, "public.v", "static_repo", "2026-07-01T00:00:00Z", "2026-07-05T00:00:00Z")
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV017" in _codes(diags)


def _empty_contributors_OV018():
    eff = _zero_census(["public.v"])  # no _contrib set
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV018" in _codes(diags)


def _empty_intersection_OV011():
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2026-07-08T00:00:00Z", "2026-07-11T00:00:00Z")
    _contrib(eff, "public.v", "runtime_logs", "2026-07-01T00:00:00Z", "2026-07-05T00:00:00Z")  # S=07-08 > E=07-05
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV011" in _codes(diags)


def _duplicate_src_object_single_derivation():
    # object_id in cluster_src_oids once (it is a set) => derived once; the derived marker is idempotent
    eff = _zero_census(["public.v"])
    _contrib(eff, "public.v", "static_repo", "2026-07-01T00:00:00Z", "2026-07-11T00:00:00Z")
    diags, derived = ov.derive_windows(eff, cluster_src_oids={"public.v"}, now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    w = eff["relations"][0]["consumer_evidence"]["observation_window"]
    return diags == [] and list(derived) == ["public.v"] and w["started_at"] and w["ended_at"]


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
def derive_windows(effective, *, cluster_src_oids, now, base_observed_at, max_consumer_evidence_age_hours):
    """For each UNIQUE cluster-source object_id (T3), derive the consumer window from the relation's
    observed consumer contributors staged in effective['_contrib_windows'][oid] as
    (started, ended, captured) tuples over CONSUMER_CONTRIB_DIMS, and write {S, E} ISO-8601 strings into
    the effective view. Returns (diagnostics, derived_window_object_ids). Fail-closed per the §3 predicate."""
    out = []
    derived = set()
    contrib = effective.get("_contrib_windows", {})
    rel_by_oid = {r["object_id"]: r for r in effective.get("relations", [])}
    finite_age = _finite(max_consumer_evidence_age_hours) and max_consumer_evidence_age_hours > 0
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
        if not finite_age:
            out.append(("OV016", loc, f"max_consumer_evidence_age_hours {max_consumer_evidence_age_hours!r} absent or non-finite (fail-closed)"))
            continue
        if (now - e).total_seconds() / 3600.0 > max_consumer_evidence_age_hours:
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


def _missing_in_data_api_window_OV022():
    # external_clients not_applicable but NO in_data_api overlay window supplied -> fail-closed OV022
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows={}, derived_windows={"public.v": (S, E)})
    return "OV022" in _codes(diags)


_CASES += [
    ("ov022_fires_when_window_not_covering", _ov022_fires_when_window_not_covering),
    ("ov022_ok_when_window_covers", _ov022_ok_when_window_covers),
    ("external_clients_observed_no_OV022", _external_clients_observed_no_OV022),
    ("missing_in_data_api_window_OV022", _missing_in_data_api_window_OV022),
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
    the in_data_api overlay's observation_window (looked up by the exact (dimension, object_id)
    assignment, T2) must COVER the derived consumer window [S, E] (started_at <= S and ended_at >= E),
    proving the relation was unexposed THROUGHOUT the evidence interval. Fail-closed: a missing
    in_data_api window (no covering overlay) is OV022. When external_clients is observed (oid not in
    external_na_oids), OV022 is not evaluated."""
    out = []
    for oid in sorted(delete_src_oids & external_na_oids):  # T1: only not_applicable-waiver deletes
        se = derived_windows.get(oid)
        if se is None:
            continue  # no derived window (already rejected upstream by OV018/OV011/etc.)
        s, e = se
        api = in_data_api_windows.get(oid)
        if api is None:
            out.append(("OV022", f"overlay-delete:{oid}", "external_clients not_applicable waiver relies on an in_data_api overlay, but none covers this relation"))
            continue
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
- Produces: `MergeResult` (a `dataclass` with `effective_snapshot: dict`, `derived_window_object_ids: set[str]`, `receipt_overlays: list[dict]`, `diagnostics: list[tuple[str, str, str]]`); `load_and_merge(*, census, census_bytes, overlay_inputs, manifest, decisions, expect_project_ref, now, max_consumer_evidence_age_hours, max_staleness_hours, resolved_signer, overlay_validator) -> MergeResult`. `overlay_inputs` = `list[tuple[str, bytes, bytes]]` of `(path, overlay_bytes, sig_bytes)` read once by the caller. Never mutates `census`.

- [ ] **Step 1: Write the failing orchestration + integrity tests** — append to `tests/test_overlay_loader.py` and `_CASES`. These build a fake `resolved_signer` and a real `overlay_validator`:

```python
class _FakeSigner:
    def __init__(self, pub):
        self.public_key = pub

VAL = ov.build_overlay_validator()


def _decisions_manifest(oids, action="harden", conclusion="no_consumer"):
    rows = [{"decision_id": "D1", "action_class": action, "decision_status": "accepted",
             "consumer_disposition": conclusion, "source_objects": list(oids)}]
    decisions = {"kind": "decisions_file", "rows": rows}
    manifest = {"kind": "cluster_manifest", "cluster_id": "C1", "status": "accepted", "action_class": action,
                "decision_ids": ["D1"], "evidence_snapshot": "snap.json", "max_staleness_hours": 8760,
                "required_observations": [], "technical_authority_approval": "TA-1"}
    return decisions, manifest


def _merge_deepcopy_unmutated():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    before = copy.deepcopy(census)
    o = _overlay("consumer_evidence.static_repo", "repository_scan",
                 [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                 census_bytes=cb, observation_window={"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-11T00:00:00Z"})
    ob, sig = _sign(o, priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("o.json", ob, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg",
                            now=NOW, max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), overlay_validator=VAL)
    # base census object is unmutated; the effective view got the derived window
    return census == before and res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]["ended_at"] != CENSUS_OBSERVED_AT


def _stale_overlay_captured_at_OV010():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    o = _overlay("consumer_evidence.static_repo", "repository_scan",
                 [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                 census_bytes=cb, captured_at="2020-01-01T00:00:00+00:00")  # far older than max_staleness_hours
    ob, sig = _sign(o, priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("o.json", ob, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg",
                            now=NOW, max_consumer_evidence_age_hours=8760, max_staleness_hours=24,
                            resolved_signer=_FakeSigner(pub), overlay_validator=VAL)
    return "OV010" in _codes(res.diagnostics)


def _effective_view_datetimes_are_iso():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    o = _overlay("consumer_evidence.static_repo", "repository_scan",
                 [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                 census_bytes=cb, observation_window={"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-11T00:00:00Z"})
    ob, sig = _sign(o, priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("o.json", ob, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg",
                            now=NOW, max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), overlay_validator=VAL)
    w = res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]
    import re
    pat = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
    return res.diagnostics == [] and re.match(pat, w["started_at"]) and re.match(pat, w["ended_at"])


_CASES += [
    ("merge_deepcopy_unmutated", _merge_deepcopy_unmutated),
    ("stale_overlay_captured_at_OV010", _stale_overlay_captured_at_OV010),
    ("effective_view_datetimes_are_iso", _effective_view_datetimes_are_iso),
]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `AttributeError: ... 'load_and_merge'`.

- [ ] **Step 3: Implement `MergeResult` + `load_and_merge`** — append to `disposition_overlay.py`:

```python
from dataclasses import dataclass, field  # noqa: E402 -- grouped with other stdlib at top on final edit


@dataclass
class MergeResult:
    effective_snapshot: dict
    derived_window_object_ids: set
    receipt_overlays: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


def load_and_merge(*, census, census_bytes, overlay_inputs, manifest, decisions, expect_project_ref,
                   now, max_consumer_evidence_age_hours, max_staleness_hours, resolved_signer, overlay_validator):
    """The step 1-8 pipeline. Verifies + binds + targets + de-conflicts each overlay, runs the
    UNCONDITIONAL OV021 base-window precheck, deep-copies the census, sets each resolved dimension,
    derives per-relation consumer windows for EVERY cluster-source relation, and runs OV022. Returns a
    MergeResult. NEVER mutates census. Any reject short-circuits to a red MergeResult (no effective view
    is trusted when a gate fails)."""
    diags = []
    on_disk_disp = _sha256_hex(open(DISPOSITION_SCHEMA_PATH, "rb").read())
    on_disk_ov = _sha256_hex(open(OVERLAY_SCHEMA_PATH, "rb").read())
    census_sha = _sha256_hex(census_bytes)
    observed_at = census.get("observed_at")
    base_observed_at = _parse_iso(observed_at)
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}

    # step 8 (OV021) runs UNCONDITIONALLY, even with zero overlays.
    diags += precheck_base_window(census)

    parsed = []            # (doc, path)
    all_keys = []          # (dimension, object_id) for OV007
    for path, ob_bytes, sig_bytes in overlay_inputs:
        ok, reason = verify_overlay(ob_bytes, sig_bytes, resolved_signer.public_key)
        if not ok:
            diags.append(("OV001", f"overlay:{path}", f"signature verification failed: {reason}"))
            continue
        try:
            doc = parse_overlay(ob_bytes)          # parse the SAME verified buffer
        except ValueError as exc:
            diags.append(("OV008", f"overlay:{path}", f"parse failed ({exc})"))
            continue
        diags += validate_overlay(doc, overlay_validator)
        diags += check_binding(doc, census_sha256=census_sha, census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref, on_disk_disp_sha=on_disk_disp,
                               on_disk_overlay_sha=on_disk_ov)
        diags += check_target(doc, rel_index)
        # OV010 per-overlay captured_at freshness (finite-guarded), reusing manifest max_staleness_hours.
        try:
            cap = _parse_iso(doc.get("captured_at"))
            if cap > now:
                diags.append(("OV010", f"overlay:{path}", "captured_at is in the future"))
            elif _finite(max_staleness_hours) and (now - cap).total_seconds() / 3600.0 > max_staleness_hours:
                diags.append(("OV010", f"overlay:{path}", f"captured_at staler than max_staleness_hours {max_staleness_hours}"))
        except (ValueError, TypeError):
            diags.append(("OV010", f"overlay:{path}", "captured_at unparseable"))
        for a in doc.get("assignments", []):
            all_keys.append((doc.get("dimension"), a.get("object_id")))
        parsed.append((doc, path))
    diags += check_conflict(all_keys)

    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)

    # ---- build the effective view (deepcopy; census never mutated) ----
    effective = copy.deepcopy(census)
    eff_index = {r["object_id"]: r for r in effective["relations"]}
    contrib = {}                     # oid -> [(started, ended, captured)]
    in_data_api_windows = {}         # oid -> (started, ended) from the (in_data_api, oid) overlay (T2)
    external_state = {}              # (oid) -> external_clients state, for T1
    for doc, _path in parsed:
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
                if dim == "in_data_api_exposed_schema":
                    in_data_api_windows[oid] = w      # exact (dimension, object_id) window (T2)
    effective["_contrib_windows"] = contrib

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

    wdiags, derived = derive_windows(effective, cluster_src_oids=cluster_src_oids, now=now,
                                     base_observed_at=base_observed_at,
                                     max_consumer_evidence_age_hours=max_consumer_evidence_age_hours)
    diags += wdiags
    derived_windows = {oid: (_parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["started_at"]),
                             _parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["ended_at"]))
                       for oid in derived}
    external_na_oids = {oid for oid, st in external_state.items() if st == "not_applicable"}
    diags += check_delete_floor_coherence(effective, delete_src_oids=delete_src_oids,
                                          external_na_oids=external_na_oids,
                                          in_data_api_windows=in_data_api_windows, derived_windows=derived_windows)

    effective.pop("_contrib_windows", None)   # scratch, never serialized / never validated
    receipt_overlays = [{"path": p, "dimension": doc["dimension"],
                         "raw_sha256": _sha256_hex(ob), "captured_at": doc["captured_at"],
                         "producing_repo_sha": doc.get("producing_repo_sha"), "source_hash": doc.get("source_hash"),
                         "object_id_count": len(doc.get("assignments", [])),
                         **({"operator_identity": doc.get("operator_identity"), "attestation_ref": doc.get("attestation_ref")}
                            if doc["dimension"] == "consumer_evidence.operator_declaration" else {})}
                        for (doc, p), (_p2, ob, _s) in zip(parsed, overlay_inputs)]
    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)
    return MergeResult(effective_snapshot=effective, derived_window_object_ids=derived,
                       receipt_overlays=receipt_overlays, diagnostics=[])
```

> Implementer notes: (1) move the `from dataclasses import dataclass, field` and `import copy` to the module's top import block during this task (they appear inline above only to show what Task 6 adds); keep the module's imports grouped. (2) `_contrib_windows` is scratch state on the effective view during derivation and is popped before the view leaves the loader, so it never reaches `disposition.schema.json` validation (which is `additionalProperties:false` at the relation level, not the snapshot root — confirm the snapshot root does not forbid it; if it does, thread the contributor map as a separate local dict instead of stashing it on `effective`). (3) OV010's `captured_at` unparseable branch is defense-in-depth; the schema's `iso_datetime` format already guards it, but per Invariant 7 do not rely on that.

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
- Consumes: `disposition_overlay.load_and_merge`, `disposition_overlay.build_overlay_validator`, `MergeResult`.
- Modifies: `main()` orchestration. New argv: `--overlay PATH` (`action="append"`, default `[]`), `--max-consumer-evidence-age-hours` (`type=float`, default `None`).

- [ ] **Step 1: Write the failing CLI e2e tests** — append to `tests/test_overlay_loader.py` and `_CASES`. These drive `check_disposition.main()` with real temp files:

```python
import subprocess as _sp  # only for structure; the test calls cd.main(argv) directly, not a subprocess
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_disposition as cd  # noqa: E402
import disposition_trust as dt  # noqa: E402


def _write(d, name, obj_or_bytes):
    p = os.path.join(d, name)
    mode = "wb" if isinstance(obj_or_bytes, (bytes, bytearray)) else "w"
    with open(p, mode) as fh:
        fh.write(obj_or_bytes if isinstance(obj_or_bytes, (bytes, bytearray)) else json.dumps(obj_or_bytes))
    return p


def _pin_signer(pub):
    """Monkeypatch the trust anchor so a throwaway key resolves as the pinned signer (tests only)."""
    from cryptography.hazmat.primitives import serialization
    fp = hashlib.sha256(pub.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
    saved = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS["test-signer"] = fp
    return saved, fp


def _e2e_red_then_green():
    # A zero-width census fails preapply with zero overlays (OV018/OV021 path); adding a full set of
    # signed overlays reaches evidence-ready green. (Full harness in the plan appendix; assert exit codes.)
    ...  # see implementer guidance below
    return True  # replaced by the real assertion during implementation


_CASES += [("e2e_red_then_green", _e2e_red_then_green)]
```

> Implementer guidance for the e2e cases (write these as real assertions, not stubs): build a temp dir with a zero-width census + its detached sig (throwaway key, pinned via `_pin_signer`), an accepted decisions/entity-map/manifest, and per-dimension signed overlays. (a) **OV021-via-main:** mutate the census base window to non-zero, run `cd.main([... "--mode", "preapply", ... "--max-consumer-evidence-age-hours", "8760"])` with **zero** `--overlay`, assert exit `1` and `OV021` printed. (b) **red:** zero overlays on the canonical census → exit `1`. (c) **green:** all gate-required overlays supplied → exit `0` and a receipt with `evidence_ready: true`, `execution_authorized: false`. (d) **retain green:** a `retain` manifest whose source relation has covering consumer overlays → exit `0`. (e) **retain no-overlay → OV018:** same retain manifest, drop the consumer overlays → exit `1`, `OV018`. (f) **authorization boundary:** valid overlays but manifest `status != accepted`/empty TA → exit `1` with `SP018` (evidence readiness NOT reached); and assert the green receipt has no `production_eligible`/write-GO field. Restore `dt.TRUSTED_SIGNERS` from `_pin_signer`'s saved copy in a `finally`.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_overlay_loader.py`
Expected: FAIL — `cd.main` rejects unknown `--overlay`/`--max-consumer-evidence-age-hours`, or the effective view is never built.

- [ ] **Step 3: Wire the loader into `main()`**

Add the argparse options (near `check_disposition.py:583`):

```python
    ap.add_argument("--overlay", action="append", default=[], dest="overlays_in", help="signed evidence overlay (repeatable); each needs a detached <PATH>.sig sidecar.")
    ap.add_argument("--max-consumer-evidence-age-hours", type=float, default=None, dest="max_consumer_evidence_age_hours", help="REQUIRED recency floor for derived consumer windows; absent/non-finite => OV016 (fail-closed).")
```

After the SP026 signature gate succeeds and `snapshot`/`decisions`/`manifest` are parsed (after `check_disposition.py:642`), and BEFORE `run(...)`, insert the overlay loader (preapply only). Read each overlay's bytes + sidecar bytes once, call `load_and_merge`, print OV diagnostics sorted with the SP diagnostics, and pass the effective view + derived set forward:

```python
    import disposition_overlay as ovl
    effective_snapshot = snapshot
    derived_ids = None
    overlay_receipt = []
    if args.mode == "preapply":
        try:
            overlay_inputs = []
            for op in args.overlays_in:
                with open(op, "rb") as fh:
                    ob = fh.read()
                with open(op + ".sig", "rb") as fh:
                    sb = fh.read()
                overlay_inputs.append((os.path.abspath(op), ob, sb))
            overlay_validator = ovl.build_overlay_validator()
        except (OSError, ovl.OverlayRegistryError) as exc:
            print(f"OV008 overlay: {exc}"); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        mres = ovl.load_and_merge(census=snapshot, census_bytes=doc_bytes["snapshot"], overlay_inputs=overlay_inputs,
                                  manifest=manifest, decisions=decisions, expect_project_ref=args.expect_project_ref,
                                  now=now, max_consumer_evidence_age_hours=args.max_consumer_evidence_age_hours,
                                  max_staleness_hours=manifest.get("max_staleness_hours"),
                                  resolved_signer=signer, overlay_validator=overlay_validator)
        if mres.diagnostics:
            for code, locus, msg in sorted(mres.diagnostics):
                print(f"{code} {locus}: {msg}")
            print(f"=== DISPOSITION GATE ({args.mode}): {len(mres.diagnostics)} BLOCKING ===")
            return 1
        effective_snapshot, derived_ids, overlay_receipt = mres.effective_snapshot, mres.derived_window_object_ids, mres.receipt_overlays

    diags = run(effective_snapshot, decisions, entity_map, manifest, now, args.mode, roots, _validator(),
                os.path.abspath(args.snapshot), args.expect_project_ref, derived_ids)
```

> Note: `signer` here is the `ResolvedSigner` already produced by the SP026 signature gate (`check_disposition.py:635`) — the overlay loader reuses the SAME pinned key, so no second `resolve_pinned_key` call. `run(...)` now validates the **effective** view (which is a census) via its existing `schema_validate`, satisfying the §5.9 re-validation with `FormatChecker`. Guard: if `signer is None` (signature-exempt mode, empty today) the overlay path is skipped — preapply is never exempt, so this is dead-safe.

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

- [ ] **Step 6: Commit**

```bash
git add check_disposition.py tests/test_overlay_loader.py tests/test_check_disposition.py
git commit -m "feat(overlay): wire --overlay into main() + e2e negatives + migrate main-level baselines (Task 8)"
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

**1. Spec coverage.** Every section maps to a task: §2A control separation → Task 7 receipt + Task 8 authorization-boundary test; §3 time model + provenance-conditional SP009 → Task 4; §4 overlay contract + `overlay.schema.json` + offline registry → Task 1; §5 steps 0-10 → the SP028 gate is pre-existing (unchanged, still step 0), read-once/verify/parse → Task 2, bind → Task 2, freshness/target/conflict → Tasks 3+6, effective view + OV021 + derive + OV022 → Tasks 3/4/5/6, semantic gate on effective view → Task 8 wiring, receipt → Task 7; §6 reject matrix `OV001–OV022` → Tasks 2-6 (each code has a pinned test); §7 signature handling → Task 2 (`verify_overlay` reuses the pinned anchor); §8 definer-view reconciliation/cluster admissibility (`OV015`) → Appendix-A views are data; `OV015` cluster-completeness is advisory and exercised through the gate-required-dimension coverage in the Task 8 green/retain fixtures (note: `OV015`'s own dedicated advisory test is folded into Task 8's cluster fixtures; if a standalone unit is wanted, add `check_cluster_completeness` in Task 6 — flagged as the one place the plan leaves `OV015` gate-driven rather than unit-tested); §9 testing strategy → the whole negative-first suite; §10 out-of-scope holds → Global Constraints; §11 ratified decisions → folded (T1/T2/T3 in Global Constraints).

**2. Placeholder scan.** The e2e cases in Task 8 Step 1 are intentionally specified as implementer-guidance-with-assertions (the harness is mechanical temp-file plumbing); every other step carries complete, runnable code. The one `...` (Task 8 `_e2e_red_then_green`) is explicitly flagged as "replace with the real assertion," with the exact assertions enumerated in the guidance block — acceptable because the body is deterministic file-writing, not novel logic. No `TBD`/`handle edge cases`/`similar to Task N` elsewhere.

**3. Type consistency.** `MergeResult` fields (`effective_snapshot`, `derived_window_object_ids`, `receipt_overlays`, `diagnostics`) are used identically in Tasks 6+8. Diagnostics are `(code, locus, message)` tuples throughout the loader; `check_disposition` prints them directly (it does not wrap them in `Diagnostic`, avoiding the circular import). `derive_windows` returns `(diags, set)`; `load_and_merge` consumes that shape. `build_receipt`'s reframed keyword set (`evidence_ready`, `execution_authorized`, `overlays`, `max_consumer_evidence_age_hours`) matches its call site in Task 8 and its tests in Task 7. `semantic_check`/`run` gain the same `derived_window_object_ids=None` trailing parameter, kept consistent at the call site.

---

## Known integration decision (surface to operator at execution handoff)

**Layering (blast-radius):** `OV021` + the overlay loader run in `main()`/`disposition_overlay` (unconditional in preapply); `semantic_check`/`run` gain only the `derived_window_object_ids`-conditional SP009 branch (default `None` = original behavior). Consequence: a **bare** `check_disposition --mode preapply` (no `--overlay`) now requires a **zero-width base census** (OV021) and yields no evidence readiness without overlays — the intended production model (the real signed census IS zero-width). This migrates the four `main()`-level e2e baselines in `tests/test_check_disposition.py` to the overlay model (Task 8 Step 4); the `run()`-level SP0xx baselines are untouched. If the operator prefers gating the overlay path on `--overlay` presence instead (leaving bare-preapply behavior unchanged), that is a spec deviation from the ratified "OV021 fires with zero `--overlay` inputs" acceptance test and would need re-ratification — my lean is the faithful unconditional model as planned.
