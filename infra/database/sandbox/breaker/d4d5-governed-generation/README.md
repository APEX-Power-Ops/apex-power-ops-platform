# D4/D5 Governed Generation (Phase 2 / D-C) -- Artifacts + Host-Clone Validation Evidence

Lane: `lvbreaker/tcc-79-d4d5-governed-generation`. Build-only; **NOT applied to prod.**
These are the PROD-BOUND data SQL artifacts generated FROM the governed `access_raw` mirror, plus the
fresh host-clone validation that proved them. Prod apply is operator-gated (separate gos, below).

## Artifacts (this directory root -- the anchored default `--out-dir`, SHA-pinned)
| File | sha256 |
|---|---|
| `029_d4_data.sql` | `911cc4db8727b27e1abc8a7da64be390bc7979825c58e2bd8f293ae943a41dd6` |
| `030_d5_data.sql` | `95be4dd8c03f36b2701a153bd4082eb3ca373d4302ebb37057e2823e4b6e3d48` |
| `generation_report.json` | `c5fa1b6a6dcb01ac277973b525caeeb40dc660d2de33f29091331c35a51900c7` |

These are **byte-reproducible**: two back-to-back `generate-d4d5` runs (and runs from different working
dirs) produce identical SHAs. Generation is deterministic because Task 9 removed the wall-clock
`generated_at` (now omitted unless an explicit value is passed); provenance is carried by `run_id`
(embeds the extraction timestamp), `source_sha256`, `snapshot_id`, and per-table checksums instead.

### SUPERSEDES the 2026-06-27 dry-run set (commit `4c00d2a0`, in `_generated/`)
The earlier `_generated/` artifacts are SUPERSEDED and removed from the tree (recoverable from git history
at `4c00d2a0`). They differed in two ways, both now folded:
- Codex round-4 **P2b**: the 030 extra-row guard now anti-joins the FULL class domain {ICCB, MCCB, PCB}
  (no staged-class filter), so a zero-staged class's stale prior-apply rows are caught.
- Task 9 determinism: the wall-clock `generated_at` is gone, so the SHA is a true content fingerprint.

Superseded SHAs (for audit): 029 `15f3a2a2...`, 030 `9415729a...`, report `2248971e...`.

## Provenance (from the artifact headers / report)
- run_id: `c15adaef-20260608T210440`
- snapshot_id: `c15adaef-20260608T210440-tcc-40067d1d` (deterministically selected -- the sole snapshot
  for this run; T8 P3 fail-closes if a run ever has zero or more than one)
- governed_source_db: `tcc_fidelity_governed` (the actual D4/D5 source -- governed `access_raw`)
- tcc_snapshot_db: `tcc_breaker_viewer_20260625` (Phase-1 host TCC bridge, informational)
- source_sha256: `c15adaefa57ed1bbc10d82c24842c5d9fc89e5d2b6992f50c0aeba764a59a16a`
- frozen_copy_path: `D:\_access_frozen\TCC_NEW_20260608T210440_c15adaef.accdb`
- driver: ACEODBC.DLL ; per-table checksum matches=True ; row_count 608/10335/3279

## Generation counts
- ICCB: d4_update_count=608, d5_insert_count=608
- MCCB: d4_update_count=10335, d5_insert_count=10335
- PCB: d4_update_count=0 (no D4 for PCB), d5_insert_count=3279
- D5 total = 14222 ; D4 full-coverage recarry stages every ICCB+MCCB style (608 + 10335).

## Host-clone validation (2026-06-28 UTC) -- the re-validation of the regenerated set
- Clone: `tcc_breaker_d4d5_gen_20260628` = `CREATE DATABASE ... TEMPLATE tcc_breaker_baseline_20260625`
  (fresh dated clone off the frozen baseline on `apex-dev-pg`; NOT the prior hook-blocked clone).
- **Transfer fidelity:** the 029/030 data files were scp'd to the host and their sha256 confirmed
  IDENTICAL to the Windows-side SHAs above -- the validated files ARE the committed artifacts.
- Apply path: `docker exec -i apex-dev-pg psql -U postgres -d <clone> -v ON_ERROR_STOP=1 < <file>` --
  the artifacts are PURE server SQL (no psql meta-commands), the same server-protocol path as the
  eventual gated apply. `ON_ERROR_STOP=1` is passed EXTERNALLY (not embedded).
- Apply order: `029_d4_tmt_helper_recarry.sql` (DDL) -> `030_d5_native_overrides_sidetable.sql` (DDL) ->
  `029_d4_data.sql` -> `030_d5_data.sql`.

### First apply -- all committed (exit 0)
- 029 DDL: `029 shape OK: 6 D4 cols x 2 tables, types match` ; COMMIT.
- 030 DDL: `030 shape OK: table + key types + 6 jsonb + PK + 2 CHECKs` ; COMMIT.
- 029 data: stage_029_iccb + stage_029_mccb, full-coverage `UPDATE 10335` recarry, guards passed, COMMIT.
- 030 data: stage_030_d5, `INSERT 0 14222`, all guards passed, COMMIT.

### Idempotent double-apply -- stable
`029_d4_data.sql` and `030_d5_data.sql` re-applied: exit=0, COMMIT (ON CONFLICT upsert + the full-coverage
UPDATE are idempotent; all in-tx guards passed again).

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
  all passed.
- **P2b full-domain extra-row guard ACTIVELY FIRED:** a bogus `('PCB', 88888888)` row was seeded into the
  side table, then `030_d5_data.sql` was re-applied; the guard RAISED
  `030 extra-row guard: 1 stale (breaker_class, source_id) row(s) in target outside the staged keyset --
  polluted prior apply detected` and the transaction rolled back (psql exit 3). This proves the guard
  catches a stale row in ANY class, not just staged classes.
- Idempotency: clean double-apply stable; the polluted re-apply fail-closed (rolled back).

## Cleanup
Host `/tmp/d4d5_gen_20260628` removed. The clones `tcc_breaker_d4d5_gen_20260627` (prior dry-run) and
`tcc_breaker_d4d5_gen_20260628` (this run; intentionally left polluted by the guard test) are harmless
throwaway copies on the dev host; `DROP DATABASE` is blocked by a safety hook, so dispose of them manually
(operator-side) when convenient.

## Status / next (operator-gated)
Validation PASSED. NOT applied to prod. Prod apply stays gated, in order, each on an explicit go:
029 DDL -> governed 029 data -> 030 DDL -> governed 030 data -> author 031 (view-transition, carries the
028 frame_counts perf-fix). Apply via the governed Supabase `fxoyniqnrlkxfligbxmg` (apply_migration), the
027/028 discipline.
