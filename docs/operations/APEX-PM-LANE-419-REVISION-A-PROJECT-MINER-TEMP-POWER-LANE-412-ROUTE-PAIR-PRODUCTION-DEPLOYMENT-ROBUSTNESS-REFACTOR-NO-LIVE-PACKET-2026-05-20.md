# APEX PM Lane 419 Revision A - Project Miner Temp Power Lane 412 Route Pair Production Deployment Robustness Refactor No-Live Packet

Date: 2026-05-20

Status: Additive hardening revision layered on top of the closed Lane 419 implementation packet to remove runtime fixture-file dependency, replace router hardcoded dev-actor detection with a jwt sentinel, and carry forward explicit Phase 0 discovery documentation without changing the route contract

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_ROUTE_PAIR_PRODUCTION_DEPLOYMENT_ROBUSTNESS_REFACTOR_NO_LIVE_REVISION_A`

## Purpose

PM Lane 419 Revision A hardens the already-implemented Lane 412 route pair before PM Lane 420 Hosted Dual-Route Smoke Readiness builds on it.

This revision is restorative and additive only. The route paths, request and response envelopes, role contract, dry-run flag behavior, runtime role rejection, digest construction, and no-live boundary all remain unchanged.

## Selected Outcome

Selected outcome:

`LANE_412_ROUTE_PAIR_PRODUCTION_DEPLOYMENT_ROBUSTNESS_REFACTOR_READY_NO_LIVE_REVISION_A`

Meaning:

1. Production code no longer reads Lane 415 JSON files from `apps/mutation-seam/scripts/lane_415_envelope_export/` at request time.
2. The strict auth wrapper no longer hardcodes the dev fallback actor identity.
3. The Lane 419 Phase 0 findings are now carried forward explicitly in the revision packet body.
4. The route contract remains byte-identical to Lane 415 frozen exports, now proven by `17 passed` in the focused route test file.

## Phase 0 Discovery

### 1. Lane 419 packet state

Discovery result:

1. `PROJECT_STATUS.md` records PM Lane 419 as closed clean with the route pair implemented locally.
2. The focused Lane 419 validation before this revision was `15 passed` on `apps/mutation-seam/tests/test_project_import_contract_support.py`.
3. No route-contract defect or test regression was open at the start of this revision.

Conclusion:

Revision A is a hardening follow-on, not a contract-correction or bug-fix packet.

### 2. Lane 415 frozen export file inventory

Discovery result:

The current Lane 419 persistence module depended on these 12 response exports at runtime:

1. `response_success_first_write.json` - success first write
2. `response_success_idempotent_hit.json` - idempotent replay
3. `response_conflict_duplicate_business_payload.json` - duplicate business payload conflict
4. `response_rollback_scope_detail_conflict.json` - rollback variant `scope_detail_conflict`
5. `response_rollback_apparatus_financial_validation_failed.json` - rollback variant `apparatus_financial_validation_failed`
6. `response_rollback_audit_write_unavailable.json` - rollback variant `audit_write_unavailable`
7. `response_rollback_idempotency_write_unavailable.json` - rollback variant `idempotency_write_unavailable`
8. `response_readback_missing.json` - readback `missing`
9. `response_readback_ready.json` - readback `ready`
10. `response_readback_stale_candidate.json` - readback `stale_candidate`
11. `response_readback_counts_mismatch.json` - readback `counts_mismatch`
12. `response_readback_unavailable.json` - readback `unavailable`

Additional finding:

No pre-existing `CONTRACT_SUPPORT_RESPONSE_*` constants existed anywhere under `apps/mutation-seam/app/**` before this revision.

Conclusion:

Revision A must embed all 12 frozen response shapes as Python constants and leave the scripts directory as a test-only source-of-truth surface.

### 3. Existing dev fallback actor identity in `jwt.py`

Discovery result:

1. The pre-revision `get_current_actor(...)` fallback produced `Actor(actor_id="tech-001", actor_role="field_tech", project_scope=["proj-001"])` when authorization was absent.
2. `jwt.py` did not previously export a sentinel constant or predicate for that fallback identity.
3. The Lane 419 router wrapper therefore hardcoded those same three identity values locally.

Conclusion:

Revision A must expose the dev fallback identity from `jwt.py` itself and make the router wrapper consume that exported sentinel instead of repeating literals.

### 4. `__file__`-based path resolution risk

Discovery result:

1. `apps/mutation-seam/app/project_import_contract_support_persistence.py` previously resolved `Path(__file__).resolve().parents[1] / "scripts" / "lane_415_envelope_export"` at runtime.
2. The current app-local Render blueprint starts `uvicorn app.main:app` from `apps/mutation-seam` and therefore may include the scripts directory when the full app folder is deployed from the repo.
3. The mutation-seam package metadata declares `[tool.setuptools] packages = ["app"]`, which does not express the scripts directory as packaged application data.
4. The app-local deployment guide's future container example copies only `app/` into the image, which would break any runtime dependency on `apps/mutation-seam/scripts/**` immediately.

Conclusion:

Even if the current hosted bundle happens to include `scripts/`, the runtime `Path(__file__)` dependency is brittle and non-portable. Revision A removes it unconditionally.

### Original Lane 419 Phase 0 Findings Carried Forward

The original Lane 419 Phase 0 findings remain canonical and are now recorded explicitly in this revision packet:

1. Router module convention - resolved through `apps/mutation-seam/app/routers/project_import_approvals.py`.
2. Actor dependency pattern - resolved through `get_current_actor(...)` in `apps/mutation-seam/app/auth/jwt.py`.
3. Persistence delegation pattern - resolved through route-to-persistence delegation with unauthorized actors rejected before write logic.
4. Lane 411 Revision C role contract - resolved post-hot-fix as symmetric PM plus Operations peer write authority.
5. Env-flag convention - resolved as `LANE_412_DRY_RUN_ENABLED` checked through `os.getenv(...).strip().lower() in {"1", "true", "yes", "on"}`.
6. Pydantic model location - resolved as flat models under `apps/mutation-seam/app/`.
7. Route registration pattern - resolved through `app.include_router(...)` in `apps/mutation-seam/app/main.py`.
8. Test infrastructure - resolved through `pytest` and the FastAPI `client` fixture in `apps/mutation-seam/tests/`.
9. Lane 414 mock plus Lane 415 frozen exports - resolved as the response-shape source-of-truth at `apps/mutation-seam/scripts/lane_415_envelope_export/`; Revision A removes only the runtime dependency.
10. Runtime role vocabulary - resolved as `task_lead` for the field-role rejection surface.
11. Auth dependency fallback behavior - resolved as dev fallback actor return from `get_current_actor(...)`, requiring a strict wrapper for this route family.

## Inherited Lane 419 Baseline

Revision A inherits unchanged from Lane 419:

1. `POST /api/v1/mutations/project-import-contract-support`
2. `GET /api/v1/reads/project-import-contract-support-status`
3. the request and response envelope shapes
4. the PM+Operations symmetric role contract
5. `task_lead` runtime rejection
6. the `LANE_412_DRY_RUN_ENABLED` gate semantics
7. the sha256 business-payload digest construction
8. the flat model layout in `project_import_contract_support_models.py`
9. the module-global `_STATE` plus per-test reset pattern
10. the no-live boundary

## Refactor Surface 1 - Embedded Lane 415 Response Constants

Implemented surface:

1. added `apps/mutation-seam/app/contract_support_response_fixtures.py`
2. embedded all 12 Lane 415 response exports as Python constants named `CONTRACT_SUPPORT_RESPONSE_<SCENARIO>`
3. removed `_FIXTURE_DIR` and `_fixture(...)` from `app/project_import_contract_support_persistence.py`
4. replaced runtime file reads with imports plus `deepcopy(...)`
5. left the Lane 415 JSON files in place as canonical frozen exports used only by the verification test

## Refactor Surface 2 - Sentinel-Based Dev Actor Detection

Implemented surface:

1. added `DEV_FALLBACK_ACTOR_IDENTITY` to `apps/mutation-seam/app/auth/jwt.py`
2. added `is_dev_fallback_actor(actor: Actor) -> bool` to `apps/mutation-seam/app/auth/jwt.py`
3. kept `get_current_actor(...)` behavior unchanged while sourcing the fallback actor from the same identity tuple
4. updated `app/routers/project_import_contract_support.py` to call `is_dev_fallback_actor(actor)` instead of repeating identity literals

## Refactor Surface 3 - Phase 0 Documentation Completeness

Implemented surface:

1. this Revision A packet now records the mandatory pre-implementation discovery answers explicitly
2. this Revision A packet also carries forward the 11 original Lane 419 Phase 0 findings as the new canonical discovery record for the route family

## Validation

Focused executable validation passed:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_import_contract_support.py -q
```

Result:

`17 passed`

What the new two tests add:

1. byte-equivalence verification between each embedded response constant and the corresponding Lane 415 JSON export using canonical JSON serialization
2. regression proof that the strict auth wrapper now uses the jwt sentinel rather than hardcoded router literals

## Boundary

This revision does not admit:

1. any route-path or HTTP-method change
2. any request-envelope or response-envelope change
3. any role-contract change
4. any env-flag behavior change
5. hosted deployment
6. live business writes
7. schema migration execution
8. any behavior change to `get_current_actor(...)`
9. any drift on Lane 411, Lane 412, Lane 413, or Lane 414 through Lane 418 surfaces

## Next Truth

The next truthful follow-on is PM Lane 420 Hosted Dual-Route Smoke Readiness, because the route family is now locally implemented without runtime fixture-file dependence and the next unanswered question is hosted no-write deployment parity.
