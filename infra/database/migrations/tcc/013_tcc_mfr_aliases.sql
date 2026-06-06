-- 013_tcc_mfr_aliases.sql
-- =============================================================================
-- applied to prod via MCP 2026-06-06; recorded here for version control
--
-- Manufacturer display aliases from the EP -> ETAP Star Library List crosswalk.
-- The application joins this table by EP manufacturer name and falls back to the
-- raw EP name when no alias row exists.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS tcc.mfr_aliases (
  ep_mfr_id integer PRIMARY KEY REFERENCES tcc.manufacturers(id),
  ep_mfr_name text NOT NULL UNIQUE,
  etap_mfr_name text NOT NULL,
  tier text NOT NULL,
  match_basis text,
  provenance text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO tcc.mfr_aliases (
  ep_mfr_id,
  ep_mfr_name,
  etap_mfr_name,
  tier,
  match_basis,
  provenance,
  created_at
) VALUES
  (1, 'ABB', 'ABB', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (2, 'Allis Chalmer', 'Allis-Chalmers', 'typo', 'operator map: Allis Chalmer -> Allis-Chalmers', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (4, 'Brown Boveri', 'ITE (BBC)', 'label', 'operator map: Brown Boveri -> ITE (BBC)', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (8, 'Fed Pacific', 'Federal Pacific', 'conditional', 'operator map: use Federal Pacific only if Star page lists it', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (9, 'GE', 'General Electric', 'expand', 'operator map: GE -> General Electric', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (11, 'ITE', 'ITE (BBC)', 'label', 'operator map: ITE -> ITE (BBC)', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (15, 'Siemens', 'Siemens', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (16, 'Siemens Allis', 'Siemens-Allis', 'punctuation', 'operator map: Siemens Allis -> Siemens-Allis', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (17, 'SQD', 'Square-D', 'shorthand', 'operator map: SQD -> Square-D', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (18, 'West', 'Westinghouse', 'expand', 'operator map: West -> Westinghouse', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (21, 'Joslyn', 'Joslyn', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (28, 'Cutler-Hammer', 'Cutler-Hammer', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (33, 'Siemens-Allis', 'Siemens-Allis', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (35, 'Square D', 'Square-D', 'punctuation', 'operator map: Square D -> Square-D', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (36, 'Westinghouse', 'Westinghouse', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (40, 'Merlin Gerin', 'Merlin Gerin', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (41, 'Cutler Hammer', 'Cutler-Hammer', 'punctuation', 'operator map: Cutler Hammer -> Cutler-Hammer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (42, 'Heinemann', 'Heinemann', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (43, 'SACE', 'ABB', 'lineage', 'operator-approved: SACE = ABB SACE breaker division', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (45, 'Federal Pioneer', 'Federal Pioneer', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (46, 'Fuji', 'Fuji', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (48, 'Roller Smith', 'Roller Smith', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (49, 'Multilin', 'Multilin', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (50, 'Utility Relay', 'Utility Relay', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (51, 'Carriere', 'Carriere', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (52, 'Satin American', 'satinAMERICAN', 'spelling', 'operator map: Satin American -> satinAMERICAN', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (61, 'Toshiba', 'TOSHIBA', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (68, 'Westrip', 'WESTRIP', 'case', 'operator map: Westrip -> WESTRIP', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (79, 'Moeller', 'Moeller', 'identity', 'operator map: Moeller -> Moeller', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (82, 'Sytek', 'Sytek', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (84, 'Schneider', 'Schneider Electric', 'expand', 'operator map: Schneider -> Schneider Electric', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (85, 'Allis-Chalmers', 'Allis-Chalmers', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (96, 'Hyundai', 'Hyundai', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (101, 'Allen-Bradley', 'Allen-Bradley', 'identity', 'operator correction: Allen-Bradley is identity', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (102, 'Fuji America', 'Fuji', 'variant', 'operator-approved: Fuji America -> Fuji', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (104, 'Sure-Trip', 'SURE-TRIP', 'case', 'operator map: Sure-Trip -> SURE-TRIP', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (118, 'Federal Pacific', 'Federal Pacific', 'conditional', 'operator map: use Federal Pacific only if Star page lists it', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (121, 'Challenger', 'Challenger', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (122, 'Mitsubishi', 'Mitsubishi', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (124, 'Telemecanique', 'Telemecanique', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (125, 'BBC', 'ITE (BBC)', 'label', 'operator map: BBC -> ITE (BBC)', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (131, 'Eaton', 'Eaton', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (144, 'Hitachi', 'Hitachi', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (149, 'Sylvania', 'SYLVANIA', 'case', 'operator map: Sylvania -> SYLVANIA', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (151, 'Terasaki', 'Terasaki', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (173, 'Gould', 'ITE (BBC)', 'lineage', 'operator-approved: Gould-ITE lineage -> ITE (BBC)', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (192, 'LS Industrial', 'LSIS', 'rebrand', 'operator map: LS Industrial -> LSIS', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (203, 'AEG', 'AEG', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (235, 'SquareD', 'Square-D', 'punctuation', 'operator map: SquareD -> Square-D', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (240, 'Milbank', 'Milbank', 'identity', 'case-insensitive exact Star Library manufacturer', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (253, 'Larsen & Toubro', 'L&T', 'contract', 'operator map: Larsen & Toubro -> L&T', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (304, 'LG Industrial', 'LSIS', 'rebrand', 'operator map: LG Industrial -> LSIS', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00'),
  (395, 'GTE/Sylvania', 'SYLVANIA', 'lineage', 'operator-approved: GTE/Sylvania -> SYLVANIA', '[ETAP Star Library List - published help docs] names-only crosswalk', '2026-06-06 22:45:28.61908+00')
ON CONFLICT (ep_mfr_id) DO UPDATE SET
  ep_mfr_name = EXCLUDED.ep_mfr_name,
  etap_mfr_name = EXCLUDED.etap_mfr_name,
  tier = EXCLUDED.tier,
  match_basis = EXCLUDED.match_basis,
  provenance = EXCLUDED.provenance,
  created_at = EXCLUDED.created_at;

COMMIT;
