---
dispatch_id: 2026-06-04-prodwrite-eaton-pdg5-sst-correction
status: DONE
applied_by: CC
applied_at: 2026-06-04
mechanism: Supabase apply_migration (tcc_009_eaton_pdg5_sst_correction), governed prod fxoyniqnrlkxfligbxmg
---

# CLOSEOUT — Eaton PDG5 SST correction (migration 009) APPLIED + verified

Operator-authorized 2026-06-04 ("they gotta be done … proceed with best practice"). Applied the reviewed
migration `009_eaton_pdg5_sst_correction.sql` via `apply_migration` (read MCP read-only for verification).
`{"success":true}`; the in-migration assert passed.

## Pre-flight (read-only, matched the packet)
PDG5: **10** rows `(PXR 10, PDG2-LSI)` [60–225 A] (the wrong triple) + 5 already-correct `(PXR20, PDG5-LSI)`
[800–1600] siblings.

## Result (read-only post-verify)
- All 10 defective rows re-pointed `(PXR 10, PDG2-LSI)` → `(PXR20, PDG5-LSI)`; **0 remaining bad**.
- PDG5 now **15** rows `(PXR20, PDG5-LSI)` (10 corrected + 5 sibling).
- **End-to-end:** PDG5 frames now resolve through the bridge to **800–1600 A** sensors (style 2439) — was
  60–225 A (~5× too small). Clears the §118 amber mismatch warning for PDG5.

Idempotent (re-run matches 0 rows); reversible via `009_eaton_pdg5_sst_correction_down.sql`.
