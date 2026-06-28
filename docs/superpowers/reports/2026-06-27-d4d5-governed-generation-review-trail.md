# D4/D5 Governed Generation (Phase 2 / D-C) -- Review Trail

Lane: `lvbreaker/tcc-79-d4d5-governed-generation` (off main `6e288120`). Build-only; NO prod apply.
This record makes the review history auditable from the repo (the live SDD ledger is gitignored scratch).

## Artifacts
- Spec: `docs/superpowers/specs/2026-06-27-d4d5-governed-generation-design.md` (Rev 1 `a5a073e7` -> Rev 2
  `2d4f85a8` [operator review folds] -> Rev 2.1 `25be94fb`/this commit [count partition, determinism,
  030 extra-row guard, ASCII-data scope]).
- Plan: `docs/superpowers/plans/2026-06-27-d4d5-governed-generation.md` (`df034c0c`, + Rev 2.1 patches).
- Phase 1 evidence (the governed mirror this generator reads from):
  `docs/superpowers/reports/2026-06-27-access-harness-governed-run.md` (`e27abdb8`).
- Code: `access_harness/d4d5_governed_generation.py` + `access_harness/cli.py` +
  `tests/test_d4d5_governed_generation.py`. Generated SQL artifacts (after the dry-run) land under
  `infra/database/sandbox/breaker/d4d5-governed-generation/`.

## Build (subagent-driven, fresh implementer + independent opus review per task)
| Task | Commit | Per-task opus review |
|---|---|---|
| 1 -- manifest + six fail-closed pre-emit gates | `d82ee320` | SPEC PASS + QUALITY APPROVED |
| 2 -- governed reader + verbatim transform + report + parity regression | `85a3116b` | SPEC PASS + QUALITY APPROVED |
| 3 -- temp-stage row-level SQL emitter + generate-d4d5 CLI | `be8f9552` | SPEC PASS + QUALITY APPROVED |
| 4 -- corrective: ORDER BY determinism + 030 extra-row guard + cosmetics | `a0caba89` | folded |
| 5 -- cross-engine corrective wave (4 patches, below) | `1f738b55` | SPEC PASS + QUALITY APPROVED |
| 5b -- blocker-proof regression test (stale tmt_* -> NULL on source-NULL) | `497ed365` | -- |
| 6 -- prod-executable SQL: remove psql meta-command + raw-artifact proof | `71ce1a12` | SPEC PASS + QUALITY APPROVED |

## Whole-slice opus review (`be8f9552`) -- MERGE READY (code-level)
0 Critical / 0 Important. Cross-task seams verified: single validated `run_id` threaded through
gates -> reads -> provenance -> emit (no latest-extraction leak; the ORDER BY latest pattern is test-only);
emitted SQL matches the queued 029/030 DDL exactly; fence precedes every read on library + CLI paths;
policy (a) holds end-to-end; transform fidelity proven by the live governed-vs-direct parity test.
NOTE: "MERGE READY" was the code-review verdict, not a merge gate -- controller validation (real
generation + host-clone dry-run + cross-engine) was still owed.

## Cross-engine (Codex) review of `be8f9552` -- 6 findings, all dispositioned
1. IMPORTANT (merge blocker): all-null D4 rows were skipped (MCCB staged 10236/10335), so a rerun /
   polluted target would not clear stale D4 to source NULL. FIXED (Task 5): stage every ICCB/MCCB style;
   `d4_update_count == total_styles` (608/10335); UPDATE sets all 6 cols incl. NULL. PROVEN by `497ed365`
   (stale value -> NULL on source-NULL apply).
2. MEDIUM: provenance omitted source row_count. FIXED (Task 5): row_count in the report + both SQL headers.
3. MEDIUM: 030 post-write proved row presence, not value parity. FIXED (Task 5): a `$vp$` post-write
   guard, `IS NOT DISTINCT FROM` across the 5 jsonb blocks + `ovr_curves IS NULL`.
4. LOW/MED: 030 emit PK guard was not exact-2. FIXED (Task 5): exact-count + membership, mirroring the DDL.
5. LOW: generated 029 SQL carries non-ASCII source text (TMT_Notes). DISPOSITION: correct + intentional --
   source data is carried VERBATIM as UTF-8 (client_encoding=UTF8); ASCII-only governs authored code only.
   Docs clarified (Rev 2.1); NO data escaping (that would break fidelity).
6. PROCESS: review trail not in the repo. ADDRESSED by this file.

## Cross-engine (Codex) round 2 -- of `e5b21e62`
1. HIGH (blocker): both emitters embedded `\set ON_ERROR_STOP on`, a psql meta-command that is INVALID
   server SQL for the apply_migration / psycopg path; the live tests stripped backslash lines before
   executing, so they proved a CLEANED script, not the artifact (false-green). FIXED (Task 6 `71ce1a12`):
   removed `\set` from emit_029 + emit_030 (fail-closed is preserved by the in-tx DO-block RAISEs +
   BEGIN/COMMIT, matching the queued 029/030 DDL which carry no `\set`).
2. MEDIUM: `_exec_sql_script` no longer strips backslash lines; added prod-executor tests that run the
   EXACT emit_029/emit_030 output raw through psycopg (commit + data landing) + a structural no-backslash
   assert -- closing the false-green class.
3. LOW: the parity test now resolves the gate-selected run_id's `frozen_copy_path` (via select_run_id),
   not `ORDER BY extracted_at_utc DESC LIMIT 1` (multi-run safe).
Boundary note (reviewer): the prod-executor coverage proves the artifact is valid pure server SQL that
psycopg accepts unmodified (the apply_migration path); if apply_migration ever re-wraps/splits the SQL,
that envelope is outside this test's scope.

## Test posture
Single-process full suite green (the implementer's Task 5 run: 227 passed / 1 skipped / 0 regressions).
A pre-existing order-/concurrency-fragility exists in `test_validate.py` (shared single `tcc_fidelity_test`
DB; cluster-level DROP/CREATE SCHEMA in the `pg` fixture) -- it surfaces only when multiple pytest
processes run at once; it is untouched by this slice and passes in a clean single-process run. Out of
scope for this lane (follow-up: harden test_validate / the f79_03 acceptance test against shared-DB
ordering). Live tests (governed DB + frozen Access) are `live`-marked and excluded by `-m "not live"`.

## Remaining (controller phase; still NO prod apply)
Run `generate-d4d5` against governed access_raw -> the real 029/030 data SQL + report; host-clone dry-run
off `tcc_breaker_baseline_20260625` (apply 029/030 DDL + generated data; verify the partition
687 real + 13533 rating_only + 2 neither = 14222, d4_update 608/10335, all guards, idempotency); commit
the validated artifacts + a dry-run README; final Codex `review-run` + opus IRP; STOP. Prod apply stays
gated: separate operator gos for 029 DDL -> 029 data -> 030 DDL -> 030 data -> 031.
