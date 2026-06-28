# D4/D5 Governed Generation (Phase 2 / D-C) -- Artifacts + Host-Clone Dry-Run Evidence

Lane: `lvbreaker/tcc-79-d4d5-governed-generation`. Build-only; **NOT applied to prod.**
These are the PROD-BOUND data SQL artifacts generated FROM the governed `access_raw` mirror, plus the
host-clone dry-run that validated them. Prod apply is operator-gated (separate gos, below).

## Artifacts (in `_generated/`, SHA-pinned -- identical before AND after the dry-run)
| File | sha256 |
|---|---|
| `029_d4_data.sql` | `15f3a2a258a03971434f1ee0679c4c020b8f3b54b501b0d88387fe3cc18a145c` |
| `030_d5_data.sql` | `9415729a5401b3cb0c0dbaa12b2834a66ec1586309e86810c15132d3effd74aa` |
| `generation_report.json` | `2248971e50bbfcc737c64fdb960807f1d5b8276beaf88c482cc348e0c809dace` |

The before/after SHAs were captured around the dry-run and are identical, so the committed files are
provably the exact files that passed.

## Provenance (from the artifact headers)
- run_id: `c15adaef-20260608T210440`
- snapshot_id: `c15adaef-20260608T210440-tcc-40067d1d`
- governed_source_db: `tcc_fidelity_governed` (the actual D4/D5 source -- governed `access_raw`)
- tcc_snapshot_db: `tcc_breaker_viewer_20260625` (Phase-1 host TCC bridge, informational)
- source_sha256: `c15adaefa57ed1bbc10d82c24842c5d9fc89e5d2b6992f50c0aeba764a59a16a`
- frozen_copy_path: `D:\_access_frozen\TCC_NEW_20260608T210440_c15adaef.accdb`
- driver: ACEODBC.DLL ; per-table checksum matches=True ; row_count 608/10335/3279

## Host-clone dry-run (2026-06-27/28 UTC)
- Clone: `tcc_breaker_d4d5_gen_20260627` = `CREATE DATABASE ... TEMPLATE tcc_breaker_baseline_20260625`
  (fresh dated clone off the frozen baseline on `apex-dev-pg`; NOT the 79audit clone).
- Apply path: `docker exec apex-dev-pg psql -U postgres -d <clone> -v ON_ERROR_STOP=1 -f <file>` --
  the artifacts are PURE server SQL (no psql meta-commands), so this is the same server-protocol path as
  the eventual gated apply. `ON_ERROR_STOP=1` is passed EXTERNALLY (not embedded).
- Apply order: `029_d4_tmt_helper_recarry.sql` (DDL) -> `030_d5_native_overrides_sidetable.sql` (DDL) ->
  `029_d4_data.sql` -> `030_d5_data.sql`.

### First apply -- all committed (exit 0)
- 029 DDL: `029 shape OK: 6 D4 cols x 2 tables, types match` ; COMMIT.
- 030 DDL: `030 shape OK: table + key types + 6 jsonb + PK + 2 CHECKs` ; COMMIT.
- 029 data: stage_029_iccb + stage_029_mccb, per-class guards passed, COMMIT.
- 030 data: stage_030_d5, all guards passed, COMMIT.
- The coverage anti-join guards PASSED against real prod-shaped `brk_*_styles` -- every generated
  source_id aligns with the clone's style tables (0 orphans).

### Idempotent double-apply -- stable
`029_d4_data.sql` and `030_d5_data.sql` re-applied: exit=0, 0 errors, COMMIT (ON CONFLICT upsert + the
full-coverage UPDATE are idempotent; all in-tx guards passed again).

### Verification (post double-apply)
| Check | Result | Expected |
|---|---|---|
| style tables | iccb 608 / mccb 10335 / pcb 3279 | match |
| D4 non-null coverage | iccb 608 / mccb 10236 | mccb 10335 total, 99 all-NULL source-faithful |
| D5 per-class | 608 / 10335 / 3279 | match |
| D5 total | 14222 | 14222 |
| partition | real 687 / rating_only 13533 / neither 2 | 687 / 13533 / 2 |
| extra-row orphans | 0 | 0 |
| ovr_curves non-null | 0 | 0 (reserved) |
| value-parity spot | ICCB sid 11: InstOvrAmps=46000.0, 16-key inst block | full block carried |

### Guard proofs demonstrated on the clone
- DDL exact-shape guards (029/030) -- passed.
- 029: stage-count, no-dup, DDL-present, coverage anti-join, post-write count -- all passed on real data.
- 030: stage-count, no-dup, PK-exact-2, coverage anti-join, post-write count, VALUE-parity, EXTRA-row --
  all passed; 0 orphans confirms the extra-row guard's invariant holds.
- Idempotency: double-apply stable, guards re-passed.
- (Stale-D4 -> NULL clearing is proven by the unit regression `test_emit_029_source_null_clears_stale_tmt_value`;
  the baseline clone had no pre-existing D4 to clear, so the full-coverage UPDATE set all rows from source.)

## Cleanup
Host `/tmp/d4d5_dryrun` (+ container copy) removed. **The clone `tcc_breaker_d4d5_gen_20260627` was NOT
dropped** -- the `DROP DATABASE` was blocked by a safety hook. It is a harmless throwaway copy on the dev
host; dispose of it manually (operator-side) when convenient.

## Status / next (operator-gated)
Dry-run PASSED. NOT applied to prod. Prod apply stays gated, in order, each on an explicit go:
029 DDL -> governed 029 data -> 030 DDL -> governed 030 data -> author 031 (view-transition, carries the
028 frame_counts perf-fix). Apply via the governed Supabase `fxoyniqnrlkxfligbxmg` (apply_migration), the
027/028 discipline.
