# Calc Engine Compatibility Boundary

This folder is no longer the primary implementation home of shared TCC calculation logic.

Current ownership split:

1. `router.py` remains the app-local FastAPI surface for `/api/v1/calculate/*` routes.
2. `etu_curves.py`, `etu_ltd.py`, `etu_merge.py`, `etu_pickup.py`, and `tmt_curves.py` are compatibility shims that re-export logic from `packages/calc-engine`.
3. New shared calc-domain behavior should land in `C:/APEX Platform/apex-power-ops-platform/packages/calc-engine/` unless the change is specifically about the control-plane HTTP contract.

Interpret the spec files here as lineage and implementation handoff material, not as the governing source of package ownership.