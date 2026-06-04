-- 010_eaton_pdg3_pdg6_sst_correction.sql
-- =============================================================================
-- Correct the Eaton Power Defense PDG3 + PDG6 SST-bridge mis-mappings (rating fix).
-- Vendor-confirmed by Eaton TCC docs TD012065EN (PD3) + TD012068EN (PD6) and PXPM;
-- encoded in services/neta/pxr_curves.py + reference/tcc/EATON-POWER-DEFENSE-PXR.md.
-- STATE §138/§139/§140. Operator-directed (2026-06-04). Follows migration 009 (PDG5).
--
-- PDG3 (400-600 A): currently (PXR20/25, NRX-LSI (RF)) -> 800-4000 A sensors (a 400 A
--   breaker is offered 800-4000 A pickups). TD012065EN: PD3 = 125/250/400/600 A, which
--   matches (PXR20, PDG3-LSI) [125-600 A] exactly. -> re-point.
-- PDG6 (1600-2600 A): currently (PXR 10, PDG2-LSI) -> 60-225 A sensors (~11x too small).
--   TD012068EN: PD6 = 1600/2000/2500 A, matching (PXR20, PDG6-LSIGM) [1600-2500 A]. -> re-point.
--
-- CAVEATS (documented; the rating fix is the gross correction, a large net improvement):
--   * PDG3 target SD slope encodes as i2x=1 vs the prior i2x=2 (the authoritative PXR SD is
--     selectable flat/I2t; EasyPower's PXR20 PDG-LSI i2x=1 is an approximation — a fidelity
--     refinement for the curve-serving layer, NOT a rating issue).
--   * PDG6 target is LSIGM (ground) while PD6 also ships LSI (no ground) -> it over-offers a
--     GF element. Minor (the tech leaves GFPU off for an LSI breaker).
-- IDEMPOTENT (NOT EXISTS via the exact wrong triple); transactional; asserted; reversible.
-- =============================================================================

BEGIN;

-- PDG3: (PXR20/25, NRX-LSI (RF)) -> (PXR20, PDG3-LSI)
UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR20', tmt_sst_style = 'PDG3-LSI'
WHERE tmt_use_sst AND frame ILIKE 'PDG3%'
  AND tmt_sst_type = 'PXR20/25' AND tmt_sst_style = 'NRX-LSI (RF)';

-- PDG6: (PXR 10, PDG2-LSI) -> (PXR20, PDG6-LSIGM)
UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR20', tmt_sst_style = 'PDG6-LSIGM'
WHERE tmt_use_sst AND frame ILIKE 'PDG6%'
  AND tmt_sst_type = 'PXR 10' AND tmt_sst_style = 'PDG2-LSI';

DO $$
DECLARE bad3 int; bad6 int;
BEGIN
  SELECT count(*) INTO bad3 FROM tcc.brk_mccb_styles
    WHERE frame ILIKE 'PDG3%' AND tmt_sst_type='PXR20/25' AND tmt_sst_style='NRX-LSI (RF)';
  SELECT count(*) INTO bad6 FROM tcc.brk_mccb_styles
    WHERE frame ILIKE 'PDG6%' AND tmt_sst_type='PXR 10' AND tmt_sst_style='PDG2-LSI';
  IF bad3 <> 0 OR bad6 <> 0 THEN
    RAISE EXCEPTION 'PDG3/PDG6 SST correction assert FAILED: bad_pdg3=%, bad_pdg6=%', bad3, bad6;
  END IF;
  RAISE NOTICE 'PDG3/PDG6 SST correction OK (expected 12 PDG3 + 9 PDG6 corrected)';
END $$;

COMMIT;
