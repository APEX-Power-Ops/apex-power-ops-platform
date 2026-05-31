---
dispatch_id: 2026-05-31-codex-tcc-tol-b11-tmt-mfr-filter
target: CODEX
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-31-tcc-tol-b11-tmt-mfr-filter-closeout.md
---

# B1.1 — Fix the TMT `/tmt/frames` manufacturer filter (Axis-1 dropdown is inert for TMT)

**Lane:** TCC Field Tolerances MVP. **Spec of record:** `apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`. **CODE-ONLY backend; parity-gated; reversible.** Follow the inbox lifecycle (claim-push before editing). This is independent of B0.1 (different files) — a dual-executor lane.

## The bug (independently verified)
The frontend sends `manufacturer_id` to `/tmt/frames`, but the backend route signature accepts **`manufacturer_name` only** and FastAPI silently drops the unknown `manufacturer_id` param → TMT frames are NOT manufacturer-filtered. Live proof: `GET /api/v1/neta/tmt/frames?manufacturer_id=9` (GE) returned ABB + Cutler Hammer frames. The route signature is around `apps/control-plane-api/services/neta/router.py:3503-3512` (grep for the `/tmt/frames` handler — line may have drifted). Contrast with ETU, where manufacturer filtering already works.

## Do
1. **Claim** (git mv pending→claimed, push) before editing.
2. **Add `manufacturer_id`** (Optional) to the `/tmt/frames` route signature + the WHERE clause, filtering TMT frames by manufacturer the way ETU does. For symmetry/forward use, also accept `breaker_id` and `breaker_style_id` if the underlying TMT frame view/table exposes those keys (only wire what exists — do not invent joins). Keep the route backward-compatible (all new params optional; `manufacturer_name` still works).
3. **Characterize the orthogonal finding** (do not necessarily fix in this dispatch): `GET /tmt/frames?manufacturer_name=GE` reportedly returns count=0 — determine whether GE TMT frames are simply absent from the catalog (a data gap) or whether it's a name-matching/normalization issue (e.g., "GE" vs "GEIS" vs "General Electric"). Record the finding; if it's a trivial matching fix in the same handler, fold it in; if it's a data gap, flag it for a separate item. **Do not declare the id-filter "done" while silently assuming the name filter is healthy.**

## Acceptance (post-deploy, hosted)
- `GET /api/v1/neta/tmt/frames?manufacturer_id=<id>` returns ONLY that manufacturer's TMT frames (verify with 2 distinct manufacturer_ids).
- `manufacturer_name` filtering still works; no params → unfiltered (unchanged).
- The `manufacturer_name=GE`→0 question is answered (data gap vs matching) in the closeout.
- No regression: ETU SQL parity 3/0; relay parity 6/6; `catalog/status` 63/17831; `GET /tmt/facets` 200; `GET /emt/facets` 200.

## Guardrails
- Backend code-only (`router.py` + the TMT frame query; a focused route test). No DDL/migration. No frontend in this dispatch (the "0 MATCHES" fix is B1.2). Scoped `git add`. DSN out-of-band; no `.env*` contents. PUBLIC repo — no client/job identifiers.

## Closeout
Record: the route diff (params + WHERE), local test result, the manufacturer_name=0 finding (data vs matching), commit hash, Render deploy confirmation, and the post-deploy gate (2 manufacturer_ids filtered + no-regression probes). Then `git mv` claimed→done, commit, push.
