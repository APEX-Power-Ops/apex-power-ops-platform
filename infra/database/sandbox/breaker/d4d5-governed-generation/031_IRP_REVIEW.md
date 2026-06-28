# 031 TMT Contract-View Transition -- IRP Review Record

> Audit mode, Deep depth (schema, prod-bound, irreversible-class view change). 2026-06-28.
> Subject: `tcc/031-tmt-contract-view-transition` @ `a582f1a2` vs main `9a2ba40a`.
> Engines: Codex (gpt-5.5 via apex-jobs review-run) + 4 adversarial Claude lenses (opus). Operator ratifies.

## Verdict

**Ship after the applied fix.** One Important defect found (guard fail-open) -- fixed at `a582f1a2`
and re-validated. Everything else converges to ship. No remaining blocker; prod apply is operator-gated.

## Cross-engine passes

- **Codex (head 56cc2d25):** clean -- "No actionable correctness issues ... relative to the existing
  028 view contract and the documented 029/030 carry sequence."
- **Codex (head a582f1a2, post-fix):** no new SQL defect; one P2 process finding -- the committed
  validation evidence was pinned to `56cc2d25` and stale vs the guard-fixed bytes. RESOLVED: evidence
  amended to cover `a582f1a2` (`031_DRYRUN_VALIDATION.md`).
- **Claude 4 lenses:** value-parity = ship; guard-fail-closed = fix-first (the Important below);
  down+lock-safety = ship; spec-conformance = ship.

## Findings

### Important -- FIXED
- **D4 guard was fail-open to an asymmetric per-class partial 029 recarry.** The leading guard summed
  ICCB+MCCB `tmt_breaker_type` non-null into one `>0` check. All 30809 d4-flagged frames are MCCB
  (ICCB has 0 `tmt_frames`), so an ICCB-only carry (608) would mask a skipped MCCB recarry while 031
  strips the d4 flag from every MCCB frame whose helper cols are NULL -- labels flipping ahead of the
  data. **Fix (a582f1a2):** gate per class -- `RAISE IF v_iccb=0 OR v_mccb=0`. **Re-validated:** the
  asymmetric negative (MCCB nulled, ICCB intact) now raises `... (iccb_nn=608, mccb_nn=0)`; value-parity
  hash `58cc15fe` and the 6-combo distribution are unchanged (guard-only change).

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

## Operator decision

Gate: apply **031 DDL** to governed prod `fxoyniqnrlkxfligbxmg` via MCP `apply_migration` (outer
BEGIN/COMMIT stripped; the runner wraps the tx; the fail-closed guard still aborts within it). Its OWN
explicit go. Apply-evidence standard: pre-apply branch SHA, post-apply live re-check (hash `58cc15fe`,
aggregates, 6-combo distribution, 0 stale survivors), transcript committed. Down available
(`031_..._down.sql`). Clone disposable (DROP hook-blocked -> manual).
