# I2X-6 prod band population check closeout

Dispatch: `2026-06-03-codex-i2x6-prod-band-population-check`

Mode: prod Supabase Postgres, read-only transaction, aggregate counts only.

Verdict: gaps found ⚠️. Route-1 band data is not cleanly populated for wiring as expected: `exp_x` is absent from both prod band tables, STD ramp/composite anchors have NULL gaps, and GFD ramp/composite exponent/anchor counts have larger gaps.

## 1. Prod column inventory

| table_name | column_name | data_type |
| --- | --- | --- |
| etu_gfd_bands | sensor_id | integer |
| etu_gfd_bands | ordinal | integer |
| etu_gfd_bands | gfd_desc | character varying |
| etu_gfd_bands | gfd_open | real |
| etu_gfd_bands | gfd_clear | real |
| etu_gfd_bands | gfd_k | real |
| etu_gfd_bands | gfd_k_hi | real |
| etu_gfd_bands | gfd_low_pu | real |
| etu_gfd_bands | gfd_sgf | smallint |
| etu_gfd_bands | gfd_x | real |
| etu_gfd_bands | i_clear | real |
| etu_gfd_bands | i_open | real |
| etu_gfd_bands | i2x | smallint |
| etu_gfd_bands | t_clear | real |
| etu_gfd_bands | t_open | real |
| etu_gfd_bands | created_at | timestamp with time zone |
| etu_std_bands | sensor_id | integer |
| etu_std_bands | ordinal | integer |
| etu_std_bands | std_desc | character varying |
| etu_std_bands | std_open | real |
| etu_std_bands | std_clear | real |
| etu_std_bands | t_open | real |
| etu_std_bands | t_clear | real |
| etu_std_bands | i_open | real |
| etu_std_bands | i_clear | real |
| etu_std_bands | i2x | smallint |
| etu_std_bands | created_at | timestamp with time zone |

## 2. STD bands by I2X shape

`exp_x` is absent on `tcc.etu_std_bands`; `has_exp_x_absent` is therefore 0 for every group.

| i2x | rows | has_exp_x_absent | has_i_open | has_t_open | has_i_clear | has_t_clear | has_std_open | has_std_clear |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| NULL | 10,704 | 0 | 0 | 0 | 0 | 0 | 10,704 | 10,704 |
| 0 | 49,916 | 0 | 1,324 | 1,324 | 1,324 | 1,324 | 49,916 | 49,916 |
| 1 | 14,181 | 0 | 14,161 | 14,161 | 14,161 | 14,161 | 4,272 | 4,272 |
| 2 | 64,840 | 0 | 64,558 | 64,558 | 64,558 | 64,558 | 64,840 | 64,840 |
| 255 | 2 | 0 | 2 | 2 | 2 | 2 | 2 | 2 |

## 3. GFD bands by I2X shape

`tcc.etu_gfd_bands` has `gfd_x` rather than `exp_x`, and `gfd_open` / `gfd_clear` rather than `std_open` / `std_clear`.

| i2x | rows | has_gfd_x | has_i_open | has_t_open | has_i_clear | has_t_clear | has_gfd_open | has_gfd_clear |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| NULL | 9,123 | 0 | 30 | 30 | 30 | 30 | 9,123 | 9,123 |
| 0 | 15,713 | 0 | 2,972 | 129 | 129 | 129 | 15,713 | 12,870 |
| 1 | 12,104 | 7,745 | 12,080 | 4,335 | 4,335 | 4,335 | 12,040 | 4,295 |
| 2 | 35,522 | 0 | 35,311 | 35,311 | 35,311 | 35,311 | 35,522 | 35,522 |
| 255 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |

## 4. Gap checks

STD gap check for ramp (`i2x=1`) and composite (`i2x=2`):

| i2x | rows | null_exp_x_absent | null_open_anchor | null_clear_anchor | composite_null_floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 14,181 | 14,181 | 20 | 20 | 0 |
| 2 | 64,840 | 64,840 | 282 | 282 | 0 |

GFD gap check for ramp (`i2x=1`) and composite (`i2x=2`), using `gfd_x` as the only real exponent-like column present:

| i2x | rows | null_gfd_x | null_open_anchor | null_clear_anchor | composite_null_floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 12,104 | 4,359 | 7,769 | 7,769 | 0 |
| 2 | 35,522 | 35,522 | 211 | 211 | 0 |

## Column-name mismatches

- Expected `exp_x` is absent from both `tcc.etu_std_bands` and `tcc.etu_gfd_bands`.
- `tcc.etu_gfd_bands` uses `gfd_x`; it is populated for 7,745 of 12,104 ramp rows and 0 of 35,522 composite rows.
- `tcc.etu_gfd_bands` uses `gfd_open` / `gfd_clear` floor columns rather than `std_open` / `std_clear`.
- Expected `i2x`, `i_open`, `t_open`, `i_clear`, and `t_clear` exist on both prod tables.
