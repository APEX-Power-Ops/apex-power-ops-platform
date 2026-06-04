-- 010_eaton_pdg3_pdg6_sst_correction_down.sql
-- Reverse 010: restore PDG3 + PDG6 to EasyPower's original (defective) triples.
BEGIN;
UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR20/25', tmt_sst_style = 'NRX-LSI (RF)'
WHERE tmt_use_sst AND frame ILIKE 'PDG3%'
  AND tmt_sst_type = 'PXR20' AND tmt_sst_style = 'PDG3-LSI';
UPDATE tcc.brk_mccb_styles
SET tmt_sst_type = 'PXR 10', tmt_sst_style = 'PDG2-LSI'
WHERE tmt_use_sst AND frame ILIKE 'PDG6%'
  AND tmt_sst_type = 'PXR20' AND tmt_sst_style = 'PDG6-LSIGM';
COMMIT;
