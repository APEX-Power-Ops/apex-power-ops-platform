-- 009_eaton_pdg5_sst_correction_down.sql
-- Reverse 009: restore the 10 corrected PDG5 (800-1200 A) rows to EasyPower's
-- original (defective) triple. The originally-correct PDG5-1600 siblings carry
-- '1600' in their frame name and are EXCLUDED so they stay PXR20/PDG5-LSI.
BEGIN;
UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR 10',
    tmt_sst_style = 'PDG2-LSI'
WHERE tmt_use_sst
  AND frame ILIKE 'PDG5%'
  AND tmt_sst_type = 'PXR20'
  AND tmt_sst_style = 'PDG5-LSI'
  AND frame NOT ILIKE '%1600%';   -- exclude the legitimately-correct 1600 A siblings
COMMIT;
