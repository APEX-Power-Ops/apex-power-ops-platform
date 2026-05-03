# TCC Relay StdLib Snapshot 001 Validation Checklist

Date: 2026-04-30
Replay target: local staging database `apex_pm_stage`
Replay file: `infra/database/migrations/work/012_tcc_relay_staged_population.sql`
Replayability proof: same file executed twice with stable counts

## Snapshot integrity

1. ✅ One immutable snapshot id fixed: `stdlib-relay-snapshot-001`.
2. ✅ Admitted file set preserved in repo-native source-lineage.
3. ✅ Row counts and SHA-256 hashes recorded in `00_snapshot_manifest.md`.
4. ✅ Replay reads only repo-native snapshot files, not live MDB/ACCDB exports.

## Source-to-target load summary

| Target table | Loaded rows |
| --- | ---: |
| `tcc_relays` | 1442 |
| `tcc_relay_devices` | 6850 |
| `tcc_relay_line_sections` | 23387 |
| `tcc_relay_td_sections` | 6635 |
| `tcc_relay_ranges` | 34213 |
| `tcc_relay_discrete_values` | 38679 |
| `tcc_relay_curves_iec` | 981 |
| `tcc_relay_curves_swz` | 950 |
| `tcc_relay_curves_bsl` | 491 |
| `tcc_relay_curves_meq` | 333 |
| `tcc_relay_curves_pcd` | 52 |
| `tcc_relay_curves_lrm` | 13 |
| `tcc_relay_curves_rxd` | 26 |
| `tcc_relay_curves_egc` | 0 |
| `tcc_relay_curves_tcp` | 16183 |
| `tcc_relay_curve_rows_iec` | 4114 |
| `tcc_relay_curve_rows_swz` | 5688 |
| `tcc_relay_curve_rows_bsl` | 3695 |
| `tcc_relay_curve_rows_meq` | 1600 |
| `tcc_relay_curve_rows_pcd` | 424 |
| `tcc_relay_curve_points_tcp` | 1570700 |

## Governed rejection and admissible-parent proof

1. ✅ `RelayDevices -> Relays` orphan rejection executed as designed: **342** source device rows rejected.
2. ✅ `RelayRanges` loaded counts match admissible-parent expectations exactly:

| RangeKey | Expected for loaded parents | Loaded rows |
| ---: | ---: | ---: |
| 101 | 1078 | 1078 |
| 102 | 30200 | 30200 |
| 202 | 1028 | 1028 |
| 203 | 365 | 365 |
| 204 | 491 | 491 |
| 205 | 947 | 947 |
| 206 | 52 | 52 |
| 207 | 26 | 26 |
| 208 | 26 | 26 |

3. ✅ TCP normalization loaded every point for admitted TCP parents:
   raw snapshot expected points = **1611617**,
   admitted-parent expected points = **1570700**,
   loaded points = **1570700**.
4. ✅ `RangeKey 101 -> td_section` branch now replays truthfully into `tcc_relay_ranges.parent_kind = 'td_section'` with **1078** loaded rows.

## Policy gates

1. ✅ Deferred relay enrichment tables present: **0**.
2. ✅ No calc-engine, API, or browser surface opened in this tranche.
3. ✅ Replay rerun from clean state reproduced the same counts.

## Notes

1. The lower loaded counts relative to raw source totals are explained by governed upstream exclusions, not silent data loss in the replay itself.
2. The replay implementation required source-backed substrate corrections discovered during execution:
   `RelayRanges.RangeKey 101 -> RelayTDSection`, wider numeric precision (`numeric(20,6)`), nullable `horizontal_amps_code`, and TCP point uniqueness keyed by `source_ordinal`.