-- 028_lvbreakertcc_tmt_serving_contract_views_down.sql
-- =============================================================================
-- DOWN for 028 — drop the three additive TMT serving-contract views.
-- Drop the dependents first (they SELECT * from the contract view).
-- =============================================================================

BEGIN;

DROP VIEW IF EXISTS tcc.vw_lvbreakertcc_tmt_projection_hazards;
DROP VIEW IF EXISTS tcc.vw_lvbreakertcc_tmt_serving_frames;
DROP VIEW IF EXISTS tcc.vw_lvbreakertcc_tmt_frame_contract;

COMMIT;
