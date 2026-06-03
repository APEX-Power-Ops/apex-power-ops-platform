# SST bridge scramble scope verify closeout

Dispatch: `2026-06-03-codex-sst-bridge-scramble-scope-verify`

Mode: prod Supabase Postgres, read-only transactions, aggregate counts and style/frame names only.

Verdict: scramble confirmed. The rating-consistency scan flags clear bridge rating inconsistencies across all classes: ICCB 129 low-frame-to-high-sensor styles, MCCB 300 total clear inconsistencies, and PCB 807 total clear inconsistencies by the packet's 2x/half heuristic. Eaton Power Defense PDG3/PDG4 map upward to NRX 800-4000 A sensors, while PDG5/PDG6 rows map downward to PDG2 60-225 A sensors; some PDG5 rows map correctly to PDG5 800-1600 A.

## 1. Column inventory

No real amp/rating column exists on the three `tcc.brk_*_styles` tables. The only frame/rating signal available in prod is the text `frame` column.

| table_name | column_name | data_type |
| --- | --- | --- |
| brk_iccb_styles | id | integer |
| brk_iccb_styles | breaker_id | integer |
| brk_iccb_styles | frame | character varying |
| brk_iccb_styles | voltage_id | integer |
| brk_iccb_styles | kaic_480v | numeric |
| brk_iccb_styles | kaic_600v | numeric |
| brk_iccb_styles | standard | numeric |
| brk_iccb_styles | notes | text |
| brk_iccb_styles | created_at | timestamp with time zone |
| brk_iccb_styles | source_id | integer |
| brk_iccb_styles | tmt_use_sst | boolean |
| brk_iccb_styles | tmt_sst_mfr | text |
| brk_iccb_styles | tmt_sst_type | text |
| brk_iccb_styles | tmt_sst_style | text |
| brk_mccb_styles | id | integer |
| brk_mccb_styles | breaker_id | integer |
| brk_mccb_styles | frame | character varying |
| brk_mccb_styles | voltage_id | integer |
| brk_mccb_styles | kaic_240v | numeric |
| brk_mccb_styles | kaic_480v | numeric |
| brk_mccb_styles | kaic_600v | numeric |
| brk_mccb_styles | poles | integer |
| brk_mccb_styles | standard | numeric |
| brk_mccb_styles | interrupt_class | character varying |
| brk_mccb_styles | notes | text |
| brk_mccb_styles | created_at | timestamp with time zone |
| brk_mccb_styles | source_id | integer |
| brk_mccb_styles | tmt_use_sst | boolean |
| brk_mccb_styles | tmt_sst_mfr | text |
| brk_mccb_styles | tmt_sst_type | text |
| brk_mccb_styles | tmt_sst_style | text |
| brk_pcb_styles | id | integer |
| brk_pcb_styles | breaker_id | integer |
| brk_pcb_styles | frame | character varying |
| brk_pcb_styles | voltage_id | integer |
| brk_pcb_styles | kaic_480v | numeric |
| brk_pcb_styles | kaic_600v | numeric |
| brk_pcb_styles | standard | numeric |
| brk_pcb_styles | notes | text |
| brk_pcb_styles | created_at | timestamp with time zone |
| brk_pcb_styles | source_id | integer |
| brk_pcb_styles | tmt_use_sst | boolean |
| brk_pcb_styles | tmt_sst_mfr | text |
| brk_pcb_styles | tmt_sst_type | text |
| brk_pcb_styles | tmt_sst_style | text |

Bridge view columns:

| column_name | data_type |
| --- | --- |
| breaker_class | text |
| breaker_id | integer |
| breaker_style_id | integer |
| breaker_style_frame | character varying |
| tmt_sst_mfr | text |
| tmt_sst_type | text |
| tmt_sst_style | text |
| trip_style_id | integer |
| sensor_id | integer |
| sensor_rating | integer |
| sensor_description | character varying |

## 2. Rating-consistency scope

The scan used the trailing integer in `breaker_style_frame` as `frame_amp`, because prod has no separate nameplate rating column.

| breaker_class | styles | frame_gt_2x_sensor_max | frame_lt_half_sensor_min | frame_amp_parse_null | clear_inconsistent_total |
| --- | ---: | ---: | ---: | ---: | ---: |
| iccb | 515 | 0 | 129 | 264 | 129 |
| mccb | 1,576 | 22 | 278 | 936 | 300 |
| pcb | 2,162 | 2 | 805 | 715 | 807 |

## 3. Eaton PDG worst-offender samples

| frame | tmt_mfr | tmt_type | tmt_style | min_sensor | max_sensor |
| --- | --- | --- | --- | ---: | ---: |
| PDG3-F PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-F PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-G PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-G PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-K PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-K PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-M PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-M PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-N PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-N PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-P PXR 400A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG3-P PXR 600A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG4-G PXR 800A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG4-K PXR 800A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG4-M PXR 800A | Eaton | PXR20/25 | NRX-LSI (RF) | 800 | 4000 |
| PDG5-K PXR 1200 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-K PXR 1600 | Eaton | PXR20 | PDG5-LSI | 800 | 1600 |
| PDG5-K PXR 800A | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-M PXR 1200 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-M PXR 1600 | Eaton | PXR20 | PDG5-LSI | 800 | 1600 |
| PDG5-M PXR 800A | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-N PXR 1200 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-N PXR 1600 | Eaton | PXR20 | PDG5-LSI | 800 | 1600 |
| PDG5-N PXR 800A | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-P PXR 1200 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-P PXR 1600 | Eaton | PXR20 | PDG5-LSI | 800 | 1600 |
| PDG5-P PXR 800A | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-T PXR 1200 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG5-T PXR 1600 | Eaton | PXR20 | PDG5-LSI | 800 | 1600 |
| PDG5-T PXR 800A | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-M PXR 1600 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-M PXR 2000 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-M PXR 2500 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-N PXR 1600 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-N PXR 2000 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-N PXR 2500 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-P PXR 1600 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-P PXR 2000 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |
| PDG6-P PXR 2500 | Eaton | PXR 10 | PDG2-LSI | 60 | 225 |

## 4. Eaton Power Defense family map

| frame_family | tmt_style | min_sensor | max_sensor | styles |
| --- | --- | ---: | ---: | ---: |
| PDG2 | PXR2 20D/25 LSI | 60 | 225 | 6 |
| PDG3 | NRX-LSI (RF) | 800 | 4000 | 12 |
| PDG4 | NRX-LSI (RF) | 800 | 4000 | 3 |
| PDG5 | PDG2-LSI | 60 | 225 | 10 |
| PDG5 | PDG5-LSI | 800 | 1600 | 5 |
| PDG6 | PDG2-LSI | 60 | 225 | 9 |

## Optional load-vs-source note

The live EasyPower Access DB and sibling `source-domains` tree were not reachable from this host, so a raw Access row read was not performed.

The checked-in D1 source-generated loader artifact was reachable: `infra/database/migrations/tcc/_d1_loader/RUN_ORDER.md` says the D1 SQL was generated from read-only Access `D:\TCC_NEW.accdb`, with a proven rank-to-id mapping and integrity hashes. Comparing three prod PDG6 sample rows to that generated artifact:

| prod_style_id | prod_source_id | frame | prod_tmt_sst | D1 artifact triple_id | D1 artifact tmt_sst |
| ---: | ---: | --- | --- | ---: | --- |
| 8783 | 99022 | PDG6-M PXR 1600 | Eaton / PXR 10 / PDG2-LSI | 258 | Eaton / PXR 10 / PDG2-LSI |
| 8784 | 99032 | PDG6-M PXR 2000 | Eaton / PXR 10 / PDG2-LSI | 258 | Eaton / PXR 10 / PDG2-LSI |
| 8785 | 99042 | PDG6-M PXR 2500 | Eaton / PXR 10 / PDG2-LSI | 258 | Eaton / PXR 10 / PDG2-LSI |

Interpretation: prod matches the D1 generated load artifact for those PDG6 samples. This host cannot distinguish whether the raw Access rows themselves are odd or whether the generated D1 re-carry artifact encoded the misalignment before load; it does show the current prod bridge/view is not introducing a later mismatch for these samples.
