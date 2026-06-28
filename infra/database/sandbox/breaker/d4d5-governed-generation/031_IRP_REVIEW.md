# 031 TMT Contract-View Transition -- IRP Review Record

> Audit mode, Deep depth (schema, prod-bound, irreversible-class view change). 2026-06-28.
> Subject: `tcc/031-tmt-contract-view-transition` @ `a582f1a2` vs main `9a2ba40a`.
> Engines: Codex (gpt-5.5 via apex-jobs review-run) + 4 adversarial Claude lenses (opus). Operator ratifies.

## Verdict

**Ship after the applied fixes.** The cross-engine IRP found two guard-honesty gaps -- a D4 fail-open
(Important, Claude) and a D5 partial-coverage gap (P2, Codex) -- both closed by hardening the guard to
its exact per-frame coverage invariant (`841ca3a8`) and re-validated. The view body, value-parity, and
scope were clean from the first pass. No remaining blocker; prod apply is operator-gated.

## Cross-engine passes

- **Codex (head 56cc2d25):** clean -- "No actionable correctness issues ... relative to the existing
  028 view contract and the documented 029/030 carry sequence."
- **Codex (head a582f1a2, post per-class fix):** no new SQL defect; one P2 process finding -- the
  committed validation evidence was pinned to `56cc2d25` and stale vs the guard-fixed bytes. RESOLVED:
  evidence amended.
- **Codex (head 28a794d5, evidence-refresh):** raised the **D5 coverage P2** (below) -- the guard only
  checked the side table non-empty, so a partial 030 would mislabel uncovered frames. RESOLVED at
  `841ca3a8` (per-frame coverage anti-join).
- **Claude 4 lenses (head a582f1a2):** value-parity = ship; guard-fail-closed = fix-first (the
  Important below); down+lock-safety = ship; spec-conformance = ship.

## Findings

### Guard honesty -- FIXED (two findings, one terminal fix)
- **D4 fail-open to an asymmetric per-class partial 029 recarry (Important, Claude).** The leading guard
  summed ICCB+MCCB `tmt_breaker_type` non-null into one `>0` check. All 30809 d4-flagged frames are MCCB
  (ICCB has 0 `tmt_frames`), so an ICCB-only carry (608) would mask a skipped MCCB recarry while 031
  strips the d4 flag from every MCCB frame -- labels flipping ahead of the data.
- **D5 partial-coverage gap (P2, Codex).** The d5 flag is relabeled `carried_reference_only`
  UNCONDITIONALLY for every frame, but the guard only checked the side table non-empty -- a partially
  populated 030 would mislabel frames whose style has no side-table row as carried.
- **Terminal fix (841ca3a8):** gate each relabel claim at its exact PER-FRAME grain -- anti-joins
  asserting (a) 0 ICCB/MCCB frames have an uncarried backing style (`tmt_breaker_type` NULL) and (b) 0
  frames have a backing style without a side-table row. This is the precise honesty invariant: it subsumes
  the per-class fix, rejects a skipped per-class recarry AND a partial side table, vacuously passes a class
  with 0 frames, and does not false-positive on the 99 unreferenced NULL-`tmt_breaker_type` MCCB styles
  (verified: 0 referenced by any frame). **Re-validated:** D4-coverage negative (skip MCCB) raises
  `30809 ... uncarried backing style`; D5-coverage negative (PARTIAL side table) raises `30809
  frame-backing style(s) lack a ... row`; positive applies with `0 D4-uncarried, 0 D5-uncovered`;
  value-parity hash `58cc15fe` + the 6-combo distribution unchanged (every guard change is precondition-only).

### Minor -- addressed / accepted
- **Trailing d4/d5 survivor checks are an authoring tripwire, not a data gate** (they read the
  just-replaced view, so they are structurally 0 regardless of data). Comment reworded to say so; the
  leading guard is the real data gate. Kept as a cheap tripwire (catches a stale literal left by a bad edit).
- **File ships outer BEGIN/COMMIT vs the apply_migration "strip it" convention.** Not a defect: the
  028/029/030 prod applies all carried inner BEGIN/COMMIT through apply_migration (nested BEGIN = WARNING,
  not ERROR; the guard RAISE still aborts the runner tx). Apply procedure: strip the outer BEGIN/COMMIT
  for cleanliness, or accept the harmless warning consistent with precedent.

### Refuted / non-issues (raised then self-cleared by the lenses)
- Per-child `count(*)` vs 028 `count(DISTINCT id)` -- equivalent, guaranteed by child-table `id` PK +
  NOT NULL; empirically 0 divergence over all 42069 frames (full-outer-join diff = 0), with orphan
  child rows (484 curve, 16 setting), multi-class frames (39509), and max 4-child fan (7200) all exercised.
- `trip_class_count = count(DISTINCT class)` unaffected by Cartesian fan or NULL class.
- `tmt_breaker_type` is a sound "row carried" sentinel (NULL-`tmt_breaker_type` MCCB rows have zero other
  D4 cols; never empty-string-non-null like the text cols).
- CREATE OR REPLACE column-list invariance holds both directions (21 cols, `projection_hazards text[]`).
- Down restores the 028 base view + COMMENT byte-identically; dependents untouched (correct minimal change).
- Lock safety: ACCESS EXCLUSIVE on the base view only, no current readers/grants, no deadlock path.
- Scope: exactly drop-d4 + relabel-d5 + perf-fix; no served flips; ASCII clean; COMMENT accurate.

## Operator decision -- GO (applied 2026-06-28)

Operator ratified the record and gave GO conditional on prod MCP reconnection + a live pre-apply baseline
check. Both met: preflight on live prod confirmed pre-031 state (d4_absent_old=30809, d5_old=42069,
d5_carried_new=0), hash `58cc15fe`, 029/030 data present, and 0 D4-uncarried / 0 D5-uncovered frames.
**031 DDL applied** via MCP `apply_migration` (`tcc_031_lvbreakertcc_tmt_contract_view_transition`, outer
BEGIN/COMMIT stripped) -> `{"success":true}` (both guards passed). Post-apply on live prod: hash
`58cc15fe` IDENTICAL, aggregates unchanged, 0 stale survivors, d5_carried=42069, exact 6-combo
distribution. Evidence: `PROD_APPLY_EVIDENCE.md` Step 5. Down available (`031_..._down.sql`). Clone
`tcc_breaker_d4d5_031val_20260628` disposable (DROP hook-blocked -> manual housekeeping).
