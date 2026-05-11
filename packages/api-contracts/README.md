# API Contracts

Status: Deferred placeholder package lane

Purpose:
- reserved shared-contract package for platform API schemas, request and response models, and cross-surface integration contracts
- intended extraction target when app-local contracts are ready to move into a shared package boundary

Current decision:
- defer package activation in this cycle
- keep contracts in the owning app until more than one active surface needs the same stable contract boundary

Current rules:
1. do not populate this package by bulk-copying app-local code
2. extract only bounded shared contracts that are already stable enough to serve more than one surface
3. keep runtime-only implementation details in the owning app until the boundary is ready
4. activate this package only when real second-surface reuse exists, not merely because the folder is present

Activation trigger:
1. activate this package only when more than one active platform surface depends on the same stable contract boundary
2. require that the first extracted contract slice already has a clear owner and validation path
3. until then, keep contracts in the owning active surface rather than scaffolding this package speculatively

Authority order:
1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/README.md`
2. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `C:/APEX Platform/apex-power-ops-platform/README.md`

This folder existed as an approved target lane at audit time but was empty. This README marks it as intentional rather than accidental.
