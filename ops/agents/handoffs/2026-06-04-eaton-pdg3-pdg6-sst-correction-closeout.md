---
dispatch_id: 2026-06-04-prodwrite-eaton-pdg3-pdg6-sst-correction
status: DONE
applied_by: CC
applied_at: 2026-06-04
predecessor: 2026-06-04-prodwrite-eaton-pdg5-sst-correction
mechanism: Supabase apply_migration (tcc_010_eaton_pdg3_pdg6_sst_correction), governed prod fxoyniqnrlkxfligbxmg
---

# CLOSEOUT — Eaton PDG3 + PDG6 SST correction (migration 010) APPLIED + verified

Operator-authorized 2026-06-04 ("they gotta be done … proceed with best practice"). Applied the reviewed
migration `010_eaton_pdg3_pdg6_sst_correction.sql` via `apply_migration` after 009 (its predecessor).
`{"success":true}`; the in-migration assert passed. Vendor-grounded (TD012065EN PD3 + TD012068EN PD6 + PXPM,
encoded in `services/neta/pxr_curves.py` + `reference/tcc/EATON-POWER-DEFENSE-PXR.md`).

## Pre-flight (read-only, matched the packet)
- PDG3: **12** rows `(PXR20/25, NRX-LSI (RF))` [800–4000 A] (wrong triple).
- PDG6: **9** rows `(PXR 10, PDG2-LSI)` [60–225 A] (wrong triple, ~11× too small).

## Result (read-only post-verify)
- PDG3: 12 → `(PXR20, PDG3-LSI)`; **0 remaining bad**. Bridge now resolves to **125–600 A** sensors (style 2466).
- PDG6: 9 → `(PXR20, PDG6-LSIGM)`; **0 remaining bad**. Bridge now resolves to **1600–2500 A** sensors (style 2377/2376).

With 009 (PDG5), **all 31 defective Eaton Power Defense rows are corrected**; zero bad triples remain across
PDG3/PDG5/PDG6.

## Documented caveats (rating fix is the gross correction; refinements only)
- PDG3 target SD slope verified faithful per STATE §142 (EasyPower carries both the flat `i2x=0` and the
  I²t-ramp `i2x=1` selectable SD bands, both served `db`) — the earlier "i2x=1 approximation" concern was
  overturned; no curve issue.
- PDG6 target is LSIGM (ground) while PD6 also ships an LSI (no-ground) config → it over-offers a GF element
  (the tech leaves GFPU off for an LSI breaker). A selection nuance, not a rating/curve error.

Idempotent (re-run matches 0 rows); reversible via `010_eaton_pdg3_pdg6_sst_correction_down.sql`.
