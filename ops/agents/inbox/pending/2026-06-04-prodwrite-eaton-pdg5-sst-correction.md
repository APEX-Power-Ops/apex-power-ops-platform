---
dispatch_id: 2026-06-04-prodwrite-eaton-pdg5-sst-correction
target: PRODWRITE
priority: 1
from: CC
created_at: 2026-06-04
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-04-eaton-pdg5-sst-correction-closeout.md
---

# PROD-WRITE — correct Eaton Power Defense PDG5 SST-bridge mis-mapping (clean subset)

**Lane:** lvbreakertcc · SST bridge (`tcc.brk_mccb_styles.tmt_sst_*`).
**Type:** DATA correction (UPDATE 10 rows; no DDL, no code). **Operator-authorized 2026-06-04.**
**Migration:** `infra/database/migrations/tcc/009_eaton_pdg5_sst_correction.sql` (+ `_down`).

## Why
EasyPower's own library maps the PDG5-* "PXR 10" breaker styles (800-1200 A frames) to
`(Eaton, PXR 10, PDG2-LSI)` → 60-225 A sensors (~5× too small; the field tech is offered the wrong
sensor set → wrong NETA settings). EasyPower also carries the rating-correct `(Eaton, PXR20, PDG5-LSI)`
[800-1600 A, same i2x=1 curve family], and its own PDG5-**1600** sibling rows already point there. This
makes the 800-1200 A rows consistent with the 1600 A sibling. Grounded by Eaton PXPM (`PXR2025MCCB.xml`:
PD2-6 are PXR20/25 trip units — the "PXR 10" attribution is the source data error). Diagnosis: STATE §138/§139
(rank=id is bit-exact; this is native to EasyPower, not a load defect).

## Apply (governed service-role)
Run `009_eaton_pdg5_sst_correction.sql` verbatim (transactional, asserted: 0 rows may remain PXR 10/PDG2-LSI;
idempotent — re-run matches 0).

## Pre-flight (verified read-only by CC 2026-06-04)
- 10 PDG5 styles match `frame ILIKE 'PDG5%' AND tmt_sst_type='PXR 10' AND tmt_sst_style='PDG2-LSI'`
  (e.g. `PDG5-K PXR 1200`, `PDG5-T PXR 800A`).
- The 5 correct PDG5-1600 rows (already PXR20/PDG5-LSI) are NOT matched.

## Verify (after apply)
```sql
SELECT tmt_sst_type, tmt_sst_style, count(*)
FROM tcc.brk_mccb_styles WHERE tmt_use_sst AND frame ILIKE 'PDG5%' AND tmt_sst_style LIKE 'PDG%'
GROUP BY 1,2 ORDER BY 1,2;
-- expect: PXR20 / PDG5-LSI = 15  (10 corrected + 5 sibling); PXR 10 / PDG2-LSI = 0
```
Then live-spot-check `PDG5-K PXR 1200` on prod (`/etu/bridge-sensors`): now resolves to 800-1600 A sensors,
and the §118 amber rating-warning no longer fires.

## Boundaries
- UPDATE only `tcc.brk_mccb_styles.tmt_sst_type/tmt_sst_style` for the 10 PDG5 rows; no DDL, no other rows, no code.
- Reversible via `009_..._down.sql`. PUBLIC repo + no secrets (style/frame names only).
- **DEFERRED (separate, pending operator domain confirm):** PDG3 (12 rows → PDG3-LSI) and PDG6 (9 rows →
  PDG6-LSIGM) — both would change the i2x curve family (PXR20/25 i2x=2 → PXR20 i2x=1), a protection-engineering
  call. See STATE §139.

## Acceptance / closeout
Closeout at the `closeout:` path with the verify result (PXR20/PDG5-LSI=15, PXR 10/PDG2-LSI=0).
