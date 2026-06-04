---
dispatch_id: 2026-06-04-prodwrite-eaton-pdg3-pdg6-sst-correction
target: PRODWRITE
priority: 1
from: CC
created_at: 2026-06-04
authority: gated
predecessor: 2026-06-04-prodwrite-eaton-pdg5-sst-correction
closeout: ops/agents/handoffs/2026-06-04-eaton-pdg3-pdg6-sst-correction-closeout.md
---

# PROD-WRITE — correct Eaton Power Defense PDG3 + PDG6 SST mis-mappings (rating fix)

**Lane:** lvbreakertcc · SST bridge (`tcc.brk_mccb_styles.tmt_sst_*`). **Type:** DATA correction (21 rows).
**Operator-directed 2026-06-04** (build the proper Eaton PD curve catalog from the authoritative docs).
**Migration:** `infra/database/migrations/tcc/010_eaton_pdg3_pdg6_sst_correction.sql` (+ `_down`).
**Vendor-grounded:** TD012065EN (PD3) + TD012068EN (PD6) + PXPM; encoded in `services/neta/pxr_curves.py`
(cited) + `reference/tcc/EATON-POWER-DEFENSE-PXR.md`.

## Why
- **PDG3** (400-600 A) currently maps to `(PXR20/25, NRX-LSI(RF))` → **800-4000 A** sensors (a 400 A breaker
  offered 800 A+ pickups — useless for coordination). TD012065EN: PD3 = 125/250/400/600 A → matches
  `(PXR20, PDG3-LSI)` [125-600 A].
- **PDG6** (1600-2600 A) currently maps to `(PXR 10, PDG2-LSI)` → **60-225 A** (~11× too small). TD012068EN:
  PD6 = 1600/2000/2500 A → matches `(PXR20, PDG6-LSIGM)` [1600-2500 A].
The gross rating error is fixed; see migration header for the two documented fidelity caveats (PDG3 SD-slope
encoding; PDG6 LSIGM over-offers G) — refinements for the curve-serving layer, not rating issues.

## Apply (governed service-role)
Run `010_eaton_pdg3_pdg6_sst_correction.sql` (transactional, asserted, idempotent).

## Pre-flight (verified read-only by CC 2026-06-04)
- PDG3 rows to fix: **12** (`PDG3-* PXR 400A/600A`). Target `(Eaton, PXR20, PDG3-LSI)` covers **125-600 A**.
- PDG6 rows to fix: **9** (`PDG6-* PXR 1600..2500`). Target `(Eaton, PXR20, PDG6-LSIGM)` covers **1600-2500 A**.

## Verify (after apply)
```sql
SELECT left(frame,4) AS fam, tmt_sst_type, tmt_sst_style, count(*)
FROM tcc.brk_mccb_styles
WHERE tmt_use_sst AND (frame ILIKE 'PDG3%' OR frame ILIKE 'PDG6%') AND tmt_sst_style LIKE 'PDG%' OR
      (frame ILIKE 'PDG3%' AND tmt_sst_style='NRX-LSI (RF)')
GROUP BY 1,2,3 ORDER BY 1,2,3;
-- expect 0 rows of PDG3->NRX-LSI(RF) and PDG6->PDG2-LSI; PDG3->PDG3-LSI=12, PDG6->PDG6-LSIGM=9
```
Live-spot-check `PDG3-F PXR 400A` + `PDG6-P PXR 2500` (`/etu/bridge-sensors`): now 125-600 A / 1600-2500 A
sensors; §118 amber warning no longer fires.

## Boundaries
- UPDATE only `tmt_sst_type/tmt_sst_style` for the 21 rows; no DDL, no other rows, no code. Reversible via `_down`.
- PUBLIC repo + no secrets (style/frame names only).

## Acceptance / closeout
Closeout with the verify result (PDG3-LSI=12, PDG6-LSIGM=9, 0 remaining bad).
