# Closeout: 2026-06-01-codex-lvbreakertcc-wiring-scoping

Status: DONE

Deliverables:
- Added `apps/operations-web/app/lvbreakertcc/WIRING_SCOPING.md`.
- Scoped current frozen `page.tsx` data/state, live per-screen contracts, gap classes, curve fidelity, proposed solutions, staging, explorer consolidation, and operator decision points.

Boundaries honored:
- No edits to `apps/operations-web/app/lvbreakertcc/page.tsx`.
- No API, route, migration, or database changes.
- No live Supabase introspection.
- No secrets printed or touched.

Key conclusions:
- Stage A should wire the LV page's Specifications screen to the existing explorer-style dual-axis ETU selection and the D1 bridge foundation.
- The true compatible-sensor narrowing data exists in `tcc.vw_breaker_sst_bridge`, but a thin read-only endpoint or route mode is still needed for the LV page to consume it directly.
- Stage B should ship the field-tolerance MVP by using `/context`, `/settings`, and `/calculate`, with G4 trust labels.
- Stage C should replace fake curve points with `/plot-tcc` preview data, but field-trust curve promotion remains engine-gated.
- The generic breaker explorer should be kept temporarily as a diagnostic surface, then retired/hidden after `/lvbreakertcc` reaches Stage B parity.

Validation:
- Documentation-only diff reviewed.
- `git diff --check` passed.
