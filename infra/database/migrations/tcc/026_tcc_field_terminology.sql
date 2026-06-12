-- 026_tcc_field_terminology.sql
-- =============================================================================
-- applied to prod via MCP 2026-06-11; recorded here for version control
--
-- SC3 field-facing terminology dictionary (task #129) — the "verbiage" slice of
-- ARCHITECTURE Decision 013, governed-but-narrow per the operator's 2026-06-11
-- ratification. One dictionary read by every consumer (lvbreakertcc Screen 2/3
-- + the B2.1 tolerance sheet): per-lineage element labels + faceplate dial
-- symbols, trust-badge words (RULED: db=MFR / unsupported=N/A), timing-source
-- method labels, setting labels (plug = "Rating plug (In)" — the Ir mislabel
-- fix), and honesty-note texts. Serving resolves
--   COALESCE(approved row @ lineage, approved row @ '*', hard-coded fallback)
-- and only status='approved' rows ever serve. Lineage assignment lives in
-- services/neta/terminology.py (pure, unit-tested), with two data-faithful
-- per-sensor overrides: SEC1GF_NAME='Earth Leakage Pickup' -> micrologic_7x_el
-- and inst_name='Override' (DT 310). Spec + rulings + per-row provenance:
-- reference/tcc/SC3-FIELD-TERMINOLOGY-DRAFT.md (operator red-line 2026-06-11).
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS tcc.field_terminology (
  id          serial PRIMARY KEY,
  namespace   text NOT NULL,
  lineage     text NOT NULL,
  term_key    text NOT NULL,
  label_short text NOT NULL,
  label_long  text,
  symbol      text,
  method_text text,
  basis       text NOT NULL,
  status      text NOT NULL DEFAULT 'draft',
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (namespace, lineage, term_key)
);

INSERT INTO tcc.field_terminology
  (namespace, lineage, term_key, label_short, label_long, symbol, method_text, basis, status)
VALUES
  -- ── element · '*' default (Series B captions are identical — vendor-confirmed) ──
  ('element', '*', 'ltpu', 'LTPU', 'Long-Time Pickup',  NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201 (Series B captions identical, pdftotext 2026-06-11)', 'approved'),
  ('element', '*', 'ltd',  'LTD',  'Long-Time Delay',   NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201 (Series B captions identical, pdftotext 2026-06-11)', 'approved'),
  ('element', '*', 'stpu', 'STPU', 'Short-Time Pickup', NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201 (Series B captions identical, pdftotext 2026-06-11)', 'approved'),
  ('element', '*', 'std',  'STD',  'Short-Time Delay',  NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201 (Series B captions identical, pdftotext 2026-06-11)', 'approved'),
  ('element', '*', 'inst', 'INST', 'Instantaneous',     NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201 (Series B captions identical, pdftotext 2026-06-11)', 'approved'),
  ('element', '*', 'gfpu', 'GFPU', 'Ground-Fault Pickup', NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201; Q1 RULED 2026-06-11 (EP "LG Pickup" = Local Ground, never shown)', 'approved'),
  ('element', '*', 'gfd',  'GFD',  'Ground-Fault Delay',  NULL, NULL, 'NETA-STD; VENDOR-DOC:0602CT9201R201; Q1 RULED 2026-06-11 (EP "LG Pickup" = Local Ground, never shown)', 'approved'),

  -- ── element · micrologic_iec (Masterpact NW/NT, Compact NS/NSX — Ir/tr dial faces) ──
  ('element', 'micrologic_iec', 'ltpu', 'LTPU', 'Long-Time Pickup',  'Ir',  NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'ltd',  'LTD',  'Long-Time Delay',   'tr',  'tr is the trip time at 6 x Ir.', 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'stpu', 'STPU', 'Short-Time Pickup', 'Isd', NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'std',  'STD',  'Short-Time Delay',  'tsd', NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'inst', 'INST', 'Instantaneous',     'Ii',  NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'gfpu', 'GFPU', 'Ground-Fault Pickup', 'Ig', NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),
  ('element', 'micrologic_iec', 'gfd',  'GFD',  'Ground-Fault Delay',  'tg', NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (micrologic_20_70a_eng)', 'approved'),

  -- ── element · micrologic_7x_el (Vigi earth leakage — the GFPU label CORRECTION) ──
  ('element', 'micrologic_7x_el', 'gfpu', 'EL', 'Earth-Leakage Pickup', 'IΔn', 'Earth-leakage (residual current) element — not a ground-fault overcurrent test; verify per the manufacturer Vigi test procedure.', 'DB-EP:DatSensor.SEC1GF_NAME=''Earth Leakage Pickup''; VENDOR-DOC:STATE §134 (Micrologic 7.0 Vigi)', 'approved'),
  ('element', 'micrologic_7x_el', 'gfd',  'EL', 'Earth-Leakage Delay',  'tΔ', 'Earth-leakage (residual current) element — not a ground-fault overcurrent test; verify per the manufacturer Vigi test procedure.', 'DB-EP:DatSensor.SEC1GF_NAME=''Earth Leakage Pickup''; VENDOR-DOC:STATE §134 (Micrologic 7.0 Vigi)', 'approved'),

  -- ── element · pxr (Eaton Power Defense — IEC symbols where TD-doc-confirmed) ──
  ('element', 'pxr', 'ltpu', 'LTPU', 'Long Delay Pickup', 'Ir',  NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md (TD012064-068EN)', 'approved'),
  ('element', 'pxr', 'ltd',  'LTD',  'Long Delay Time',   NULL,  NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md (TD012064-068EN)', 'approved'),
  ('element', 'pxr', 'stpu', 'STPU', 'Short Delay Pickup', 'Isd', NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md (TD012064-068EN)', 'approved'),
  ('element', 'pxr', 'std',  'STD',  'Short Delay Time',  'tsd', NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md (TD012064-068EN)', 'approved'),
  ('element', 'pxr', 'inst', 'INST', 'Instantaneous',     NULL,  NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md; symbol unconfirmed -> none (L4)', 'approved'),
  ('element', 'pxr', 'gfpu', 'GFPU', 'Ground Fault Pickup', NULL, NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md; symbol unconfirmed -> none (L4)', 'approved'),
  ('element', 'pxr', 'gfd',  'GFD',  'Ground Fault Delay',  NULL, NULL, 'VENDOR-DOC:EATON-POWER-DEFENSE-PXR.md; symbol unconfirmed -> none (L4)', 'approved'),

  -- ── element · digitrip (West/C-H/Eaton/SqD DT lineage — captions per the RMS manuals) ──
  ('element', 'digitrip', 'ltpu', 'LTPU', 'Long Delay Setting', NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'digitrip', 'ltd',  'LTD',  'Long Delay Time (s)', NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units; DB-EP:ltd_name ''LT Delay (s)''', 'approved'),
  ('element', 'digitrip', 'stpu', 'STPU', 'Short Delay Pickup', NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'digitrip', 'std',  'STD',  'Short Delay Time',   NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'digitrip', 'inst', 'INST', 'Instantaneous',      NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'digitrip', 'gfpu', 'GFPU', 'Ground Fault Pickup', NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units; Q1 RULED (EP LG = Local Ground, not shown)', 'approved'),
  ('element', 'digitrip', 'gfd',  'GFD',  'Ground Fault Time',   NULL, NULL, 'VENDOR-DOC:IL70C1037H05 + Digitrip RMS Units (captions confirmed pdftotext 2026-06-11)', 'approved'),

  -- ── element · ge_mvt_eg (MVT/VersaTrip/RMS-9/Power+/EntelliGuard TU) ──
  ('element', 'ge_mvt_eg', 'ltpu', 'LTPU', 'Long Time Pickup',  NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'ge_mvt_eg', 'ltd',  'LTD',  'Long Time Delay',   NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'ge_mvt_eg', 'stpu', 'STPU', 'Short Time Pickup', NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'ge_mvt_eg', 'std',  'STD',  'Short Time Delay',  NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'ge_mvt_eg', 'inst', 'INST', 'Instantaneous',     NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'ge_mvt_eg', 'gfpu', 'GFPU', 'Ground Fault Pickup', NULL, NULL, 'VENDOR-DOC:GEH-5369; Q1 RULED (EP LG = Local Ground, not shown)', 'approved'),
  ('element', 'ge_mvt_eg', 'gfd',  'GFD',  'Ground Fault Delay',  NULL, NULL, 'VENDOR-DOC:GEH-5369 (captions confirmed pdftotext 2026-06-11)', 'approved'),

  -- ── element · ekip_pr (ABB SACE — L/S/I/G function thresholds I1–I4, times t1/t2/t4) ──
  ('element', 'ekip_pr', 'ltpu', 'LTPU', 'L threshold', 'I1', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip; DB-EP:ltpu_name I1/Ir1', 'approved'),
  ('element', 'ekip_pr', 'ltd',  'LTD',  'L time',      't1', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip', 'approved'),
  ('element', 'ekip_pr', 'stpu', 'STPU', 'S threshold', 'I2', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip; DB-EP:stpu_name I2/Ir2', 'approved'),
  ('element', 'ekip_pr', 'std',  'STD',  'S time',      't2', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip', 'approved'),
  ('element', 'ekip_pr', 'inst', 'INST', 'I threshold', 'I3', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip; DB-EP:inst_name I3/Ir3', 'approved'),
  ('element', 'ekip_pr', 'gfpu', 'GFPU', 'G threshold', 'I4', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip', 'approved'),
  ('element', 'ekip_pr', 'gfd',  'GFD',  'G time',      't4', NULL, 'VENDOR-DOC:1SXU210266G0201 + 860995673-Ekip-Dip', 'approved'),

  -- ── element · siemens_etu (Sentron WL/3WA/3VA ETU — symbols per the WL guide) ──
  ('element', 'siemens_etu', 'ltpu', 'LTPU', 'Long-Time Pickup',  'IR',  NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'siemens_etu', 'ltd',  'LTD',  'Long-Time Delay',   'tR',  NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide; DB-EP:ltd_name ''tr'' (ETU 350/560)', 'approved'),
  ('element', 'siemens_etu', 'stpu', 'STPU', 'Short-Time Pickup', 'Isd', NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'siemens_etu', 'std',  'STD',  'Short-Time Delay',  'tsd', NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'siemens_etu', 'inst', 'INST', 'Instantaneous',     'Ii',  NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'siemens_etu', 'gfpu', 'GFPU', 'Ground-Fault Pickup', 'Ig', NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),
  ('element', 'siemens_etu', 'gfd',  'GFD',  'Ground-Fault Delay',  'tg', NULL, 'VENDOR-DOC:sie-sa-wl-selection-guide (symbols confirmed pdftotext 2026-06-11)', 'approved'),

  -- ── trust badges + field phrasing (Q2 = MFR, Q3 = N/A; gates unchanged, L5) ──
  ('trust', '*', 'pickup.db', 'MFR', 'Manufacturer per-device tolerance (device library)', NULL, 'Manufacturer per-device tolerance (device library).', 'RULED 2026-06-11 (Q2); G4 pickup tier', 'approved'),
  ('trust', '*', 'delay.db', 'MFR', 'Manufacturer time band for this sensor + setting (validated)', NULL, 'Manufacturer time band for this sensor + setting (validated).', 'RULED 2026-06-11 (Q2); G4 db tier', 'approved'),
  ('trust', '*', 'delay.verify', 'VERIFY', 'Reference only — confirm against the manufacturer TCC before acceptance', NULL, 'Reference only — confirm against the manufacturer TCC before acceptance.', 'RULED 2026-06-11; G4 verify tier (currently empty, §214)', 'approved'),
  ('trust', '*', 'delay.unsupported', 'N/A', 'No certified trip time — record measured; accept per manufacturer TCC', NULL, 'No certified trip time — record the measured value; acceptance per the manufacturer TCC.', 'RULED 2026-06-11 (Q3); G4 unsupported tier', 'approved'),

  -- ── timing-source / Method labels (Part II 2b, approved) ──
  ('method', '*', 'timing_source.ltd_reference_window', 'Manufacturer LTD tolerance (device library)', 'Manufacturer LTD tolerance (device library)', NULL, 'Manufacturer LTD tolerance (device library).', 'RULED 2026-06-11 (Part II 2b)', 'approved'),
  ('method', '*', 'timing_source.ltd_reference_window_generic', 'Estimated band −30%/+0% — no manufacturer tolerance on file (flagged)', 'Estimated band −30%/+0% — no manufacturer tolerance on file (flagged)', NULL, 'Estimated −30%/+0% band; no manufacturer tolerance on file (flagged).', 'RULED 2026-06-11 (Part II 2b)', 'approved'),
  ('method', '*', 'timing_source.band_table', 'Manufacturer delay band (per-sensor)', 'Manufacturer delay band (per-sensor)', NULL, 'Manufacturer delay band (per-sensor).', 'RULED 2026-06-11 (Part II 2b)', 'approved'),
  ('method', '*', 'timing_source.i2x', 'Manufacturer I²t characteristic (validated)', 'Manufacturer I²t characteristic (validated)', NULL, 'Manufacturer I²t characteristic (validated).', 'RULED 2026-06-11 (Part II 2b)', 'approved'),
  ('method', '*', 'timing_source.curve_interpolation', 'Manufacturer curve band (open/clear)', 'Manufacturer curve band (open/clear)', NULL, 'Manufacturer curve band (open/clear).', 'RULED 2026-06-11 (Part II 2b)', 'approved'),
  ('method', '*', 'timing_source.maint_profile', 'Maintenance-mode (ARMS) profile', 'Maintenance-mode (ARMS) profile', NULL, 'Maintenance-mode (ARMS) profile.', 'RULED 2026-06-11 (Part II 2b)', 'approved'),

  -- ── setting labels (the Plug (Ir) -> Rating plug (In) fix + Q5) ──
  ('setting', '*', 'plug', 'Rating plug (In)', 'Rating plug (In)', 'In', NULL, 'VENDOR-DOC:MICROLOGIC-6.0A.md (plug sets In; Ir = LTPU dial x In — live 3833); RULED 2026-06-11 (Part III 3a)', 'approved'),
  ('setting', '*', 'test_current', 'Test Current', 'Test Current (x pickup)', NULL, NULL, 'RULED 2026-06-11 (Q5)', 'approved'),

  -- ── honesty notes (Part II 2c/2d, approved) ──
  ('note', '*', 'withheld', 'withheld', 'No certified expected time for this element; record the measured value; acceptance per the manufacturer TCC.', NULL, 'No certified expected time for this element; record the measured value; acceptance per the manufacturer TCC.', 'RULED 2026-06-11 (Part II 2c)', 'approved'),
  ('note', '*', 'est', 'est*', 'Estimated −30/+0% band; no manufacturer tolerance on file.', NULL, 'Estimated −30/+0% band; no manufacturer tolerance on file.', 'RULED 2026-06-11 (Part II 2c)', 'approved'),
  ('note', '*', 'plot_caveat', 'nominal', 'Published curve (nominal) — acceptance is the envelope/table values.', NULL, 'Published curve (nominal) — acceptance is the envelope/table values.', 'RULED 2026-06-11 (Part II 2c)', 'approved'),
  ('note', '*', 'sheet_footer', 'footer', 'Acceptance values are manufacturer tolerances per the device library; NETA ATS table values are used only where labeled as fallback. Pickup tolerances are per-device. Withheld times are deliberate: no certified basis exists — use the manufacturer TCC.', NULL, 'Acceptance values are manufacturer tolerances per the device library; NETA ATS table values are used only where labeled as fallback. Pickup tolerances are per-device. Withheld times are deliberate: no certified basis exists — use the manufacturer TCC.', 'RULED 2026-06-11 (Part II 2d); feedback_neta_acceptance_equals_mfr_tolerances', 'approved');

-- fail-closed verification
DO $$
DECLARE
  n integer;
  v text;
BEGIN
  SELECT count(*) INTO n FROM tcc.field_terminology;
  IF n <> 67 THEN
    RAISE EXCEPTION 'field_terminology seed count % <> 67', n;
  END IF;
  SELECT count(*) INTO n FROM tcc.field_terminology WHERE status <> 'approved';
  IF n <> 0 THEN
    RAISE EXCEPTION 'field_terminology has % non-approved seed rows (expected 0)', n;
  END IF;
  SELECT symbol INTO v FROM tcc.field_terminology
   WHERE namespace='element' AND lineage='micrologic_iec' AND term_key='ltpu';
  IF v IS DISTINCT FROM 'Ir' THEN
    RAISE EXCEPTION 'micrologic_iec ltpu symbol % <> Ir', v;
  END IF;
  SELECT label_short INTO v FROM tcc.field_terminology
   WHERE namespace='trust' AND lineage='*' AND term_key='delay.unsupported';
  IF v IS DISTINCT FROM 'N/A' THEN
    RAISE EXCEPTION 'trust delay.unsupported badge % <> N/A', v;
  END IF;
  SELECT label_short INTO v FROM tcc.field_terminology
   WHERE namespace='element' AND lineage='micrologic_7x_el' AND term_key='gfpu';
  IF v IS DISTINCT FROM 'EL' THEN
    RAISE EXCEPTION 'micrologic_7x_el gfpu code % <> EL', v;
  END IF;
END $$;

COMMIT;
