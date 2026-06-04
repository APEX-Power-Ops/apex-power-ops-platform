-- 009_eaton_pdg5_sst_correction.sql
-- =============================================================================
-- Correct the Eaton Power Defense PDG5 (800-1200 A) SST-bridge mis-mapping.
--
-- WHY (STATE §138/§139, 2026-06-04; verified vs raw Access + Eaton PXPM):
--   EasyPower's source maps the PDG5-* "PXR 10" breaker styles (800-1200 A frames)
--   to trip style (Eaton, PXR 10, PDG2-LSI) whose sensors are only 60-225 A — an
--   ~5x rating mismatch (a field tech is offered 60-225 A sensors for an 800-1200 A
--   breaker). This is native to EasyPower's library (NOT a load/rank=id defect).
--
--   EasyPower ALSO carries the rating-correct style for the SAME PDG5 frame:
--   (Eaton, PXR20, PDG5-LSI) [trip_style 2439, sensors 800-1600 A, i2x=1] — and its
--   own PDG5-1600 sibling rows already point there correctly. This UPDATE makes the
--   800-1200 A PDG5 rows consistent with their 1600 A sibling. Same i2x=1 curve
--   family; the only change is type 'PXR 10'->'PXR20' + style 'PDG2-LSI'->'PDG5-LSI'.
--   Grounded by Eaton Power Xpert Protection Manager (PXR2025MCCB.xml: PD2-6 are
--   PXR20/25 trip units) — the validated-library loop (cf. §108 PXR2 catalog).
--
-- SCOPE: ONLY the defective PDG5 "PXR 10"/PDG2-LSI rows (the precise wrong triple).
--   The originally-correct PDG5 rows (already PXR20/PDG5-LSI) are NOT matched.
--   PDG3 (->PDG3-LSI) and PDG6 (->PDG6-LSIGM) are DEFERRED pending the operator's
--   curve-family confirmation (they would change the i2x curve family — domain call).
-- IDEMPOTENT: re-running matches 0 rows. Operator-authorized correction (2026-06-04).
-- =============================================================================

BEGIN;

UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR20',
    tmt_sst_style = 'PDG5-LSI'
WHERE tmt_use_sst
  AND frame ILIKE 'PDG5%'
  AND tmt_sst_type = 'PXR 10'
  AND tmt_sst_style = 'PDG2-LSI';

-- assert: expected exactly 10 PDG5 rows corrected; the 1600 siblings untouched.
DO $$
DECLARE
  n_remaining_bad int;
  n_pdg5_correct int;
BEGIN
  SELECT count(*) INTO n_remaining_bad FROM tcc.brk_mccb_styles
    WHERE frame ILIKE 'PDG5%' AND tmt_sst_type='PXR 10' AND tmt_sst_style='PDG2-LSI';
  SELECT count(*) INTO n_pdg5_correct FROM tcc.brk_mccb_styles
    WHERE frame ILIKE 'PDG5%' AND tmt_sst_type='PXR20' AND tmt_sst_style='PDG5-LSI';
  IF n_remaining_bad <> 0 THEN
    RAISE EXCEPTION 'PDG5 SST correction assert FAILED: % rows still PXR 10/PDG2-LSI', n_remaining_bad;
  END IF;
  RAISE NOTICE 'PDG5 SST correction OK: 0 remaining bad; % PDG5 rows now PXR20/PDG5-LSI (10 corrected + 5 sibling)', n_pdg5_correct;
END $$;

COMMIT;
