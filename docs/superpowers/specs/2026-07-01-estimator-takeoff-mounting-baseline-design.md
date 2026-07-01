# Estimator-Takeoff Mounting Baseline (LV Breaker Pricing Unlock) - Design

**Status:** Ratified design (operator, 2026-07-01), Option A-prime. Ready for writing-plans -> SDD -> Codex/opus IRP -> operator-gated merge.
**Lane:** host worktree `/home/olares/code/apex/apex-mounting`, branch `estimator-takeoff/mounting-baseline` off main `194864d4`.
**Package:** `packages/estimator-takeoff`.

## Goal

Turn the ~106 (Building A) / ~331 (Building B) LV breakers that currently resolve to `mounting: 'unknown'` -> unmatched (unpriced) into priced NETA test-scope lines, by broadening the estimating-baseline mounting inference AND hardening the trip-function parser so real decorated descriptors (LSIGM) are not silently dropped. Today only 4 (A) / 3 (B) breakers price; the block is graphical mounting, which the text extractor cannot supply, so the engine assumes it from frame + trip functions under a loud `estimating_baseline` provenance.

## Context / current behavior (grounded against main 194864d4)

`resolveMounting` (src/signature/normalize.ts:140-151) precedence, UNCHANGED by this lane:
1. `x.mountingHint` (basis `hint`) wins first.
2. `parseMounting(x.raw)` explicit text (MCB/panelboard/MCCB/ICCB/EO/draw-out) (basis `text`) wins next.
3. Estimating baseline (basis `estimating_baseline`) - the only branch this lane changes.
4. else `unknown` (basis `none`).

The baseline branch today is a single rule: `frameA >= 800 && functions.includes('G') -> draw_out`; everything else -> `unknown`. That is why only breakers with a >=800A frame AND an explicit G function price.

`MountingBasis = 'hint' | 'text' | 'estimating_baseline' | 'none'` already exists (types.ts:12). Provenance is already loud and never laundered as detected geometry - operator caution #2 is already structural.

`Mounting = 'draw_out' | 'electrically_operated' | 'insulated_case' | 'molded_case' | 'panelboard' | 'unknown'`.
`TripFunction = 'L' | 'S' | 'I' | 'G'` (only four; no `E`, no `M`).

### The parser defect (operator finding 1, verified)

`parseFunctions` (normalize.ts) uses `/\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i`. The trailing `\b` requires a word boundary immediately after the `E?` group. For `LSIGM`, the position after `G` is `G->M` (both letters, NOT a boundary), so the whole token fails to match and returns `[]`. Verified empirically: `1200AF/1200AT LSIGM -> functions: [] -> mounting: unknown`.

Real decorated-function vocabulary censused from the live A/B extraction artifacts (/tmp/{A2,B2}.artifact.json):

| token | A count | B count | current parse | correct parse |
|-------|---------|---------|---------------|---------------|
| LSI   | 114     | 93      | [L,S,I] OK    | [L,S,I]       |
| LSIGM | **95**  | **69**  | **[] WRONG**  | [L,S,I,G]     |
| LI    | 19      | 16      | [L,I] OK      | [L,I]         |
| LSIG  | 6       | 4       | [L,S,I,G] OK  | [L,S,I,G]     |
| LSIM  | 2       | 6       | **[] WRONG**  | [L,S,I]       |

`LSIGM` (164 rows total) is the dominant decorated form. Left unfixed, those become `molded_case + missing_power_functions` under the new baseline instead of `draw_out`/`insulated_case` (LSIG) - bid-significant. The extractor preserves the decoration (drawing-nav `discover_miner` captures `LSIGM`); the engine must stop discarding it.

## Scope: three coordinated changes (NOT one branch)

### Change 1 - parseFunctions decoration hardening (prerequisite)

Parse the leading `L[S][I][G|E]` core from the descriptor, tolerating trailing modifier characters (`M`, `N`, and punctuation decorations such as `,N.C.`) WITHOUT discarding the core. `E` still folds to `G`. `M` is a modifier / evidence, never a new catalog tier.

Required input -> output (test cases, real forms):
- `LSIGM` -> `['L','S','I','G']`
- `LSIM`  -> `['L','S','I']`
- `LSIG`  -> `['L','S','I','G']` (unchanged)
- `LSIGE` -> `['L','S','I','G']` (unchanged; existing test normalize.test.ts:22-23)
- `LSI`   -> `['L','S','I']` (unchanged)
- `LI`    -> `['L','I']` (unchanged)
- `LSIGM,N.C.` -> `['L','S','I','G']` (decoration tolerance)
- Guard against over-capture across token boundaries: a synthetic `LSIGMAIN` (no delimiter) must NOT match as `[L,S,I,G]`. Bound the trailing consumption to the modifier/punctuation set (e.g. `[MN.,C]*`), not all letters, so it cannot swallow an adjacent word.

Candidate implementation (TDD finalizes exact class): `/\bL(?=[SIGE])(S?)(I?)(G?)(E?)[MN.,C]*\b/i`, keeping the existing group-based L/S/I/G assembly (`E||G -> push 'G'`).

### Change 2 - resolveMounting estimating-baseline broadening

Replace the baseline branch only (hint/text precedence unchanged). When there is no hint and no text mount:

| frame | trip functions | mounting | basis |
|-------|----------------|----------|-------|
| present, >= 800A | any (`functions.length > 0`) | `draw_out` | `estimating_baseline` |
| present, < 800A  | any (`functions.length > 0`) | `insulated_case` | `estimating_baseline` |
| present (any)    | none (`functions.length === 0`) | `molded_case` | `estimating_baseline` |
| absent           | (n/a) | `unknown` | `none` |

- The old `hasG` special case is removed: `draw_out` is now `frame>=800 + any functions`; the `LSIG` vs `LS/LSI` catalog split happens in breaker-map.data.ts (lines 16 vs 17), not in the resolver.
- `panelboard` and `electrically_operated` are NEVER emitted by the baseline - they remain text/hint-only (operator caution: do not infer panelboard from frame alone).
- `frame absent -> unknown/none` is intentional fail-closed: every LV catalog ref requires `hasFrame`, so a frameless breaker cannot price regardless of mounting.

Every target mounting has an existing priced catalog ref (breaker-map.data.ts):
- `draw_out` -> `Circuit Breaker LV - Draw-Out (LSIG)` (hasG) or `(LS/LSI)` (hasFns)
- `insulated_case` -> `Insulated Case (LSIG)` / `(LS/LSI)`
- `molded_case` -> `Molded Case Thermal/Mag` (frame only)
No new catalog refs are introduced.

### Change 3 - missing_power_functions trigger (Option A-prime)

A breaker with a frame but no parsed functions -> `molded_case` (cheapest LV tier). For frame >= 800A with no function evidence, that is more likely an extraction miss than a genuine large thermal-mag breaker, so it must be PRICED (partial preview) BUT flagged, so it can never be a clean bid silently.

Amend the existing trigger (normalize.ts:522-523) from:
```
if (functions.length === 0 && (mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case'))
```
to additionally fire for baseline-inferred large molded_case:
```
if (functions.length === 0 && (
      mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case'
   || (mounting === 'molded_case' && mountingBasis === 'estimating_baseline' && frameA !== undefined && frameA >= 800)
))
```
The `mountingBasis === 'estimating_baseline'` guard is load-bearing: a TEXT-resolved MCCB (explicit molded_case, no functions - normal for molded-case) must NOT be flagged; only the ASSUMED large molded_case is suspicious. Small-frame (<800) baseline molded_case is a genuine small MCCB-style device and is not flagged.

## Deliberate test-contract updates (operator finding 2)

These existing non-golden assertions intentionally become stale and MUST be updated as part of the lane (call them out so the suite does not "surprise fail"):
- `test/normalize.test.ts:70-72` - "stays unknown ... for a 400AF LSI breaker" -> now `insulated_case` / `estimating_baseline`.
- `test/normalize.test.ts:74-75` - "does NOT apply the baseline for a large frame without ground-fault (LS/LSI)" (`1600AF/1600AT LSI`) -> now `draw_out` / `estimating_baseline`. (This test encodes the removed "requires G" rule; rewrite it to assert the new draw_out behavior.)
- `test/normalize.test.ts:78` - `PANEL-DO-3 200AF/200AT LSI` -> now `insulated_case` (no explicit draw-out text token; "DO-3" is not `(DO)`/`D/O`).
- `test/emit.test.ts:26-28` - the 400AF LSI `HF-P1-110-01-FB` flips from `unmatchedCandidates` length 1 to MATCHED (priced Insulated Case LS/LSI). Rewrite to assert it is matched with the expected ref, and keep an unmatched/question example elsewhere so the "never silently lost" invariant still has a subject.

## Golden posture

All six golden tests are mounting-agnostic (0 mounting assertions each). The five family goldens (gfp / itx / relay / transformer / switch) cover NON-breaker devices and MUST stay byte-identical. E01-11 is a BEHAVIORAL golden asserting (a) `unmatched + questions + ignored > 0` (producer noise never silently lost) and (b) `findings === 0` (priced seam validates against estimator-core). This lane moves breakers unmatched->priced, which reduces unmatched but keeps noise > 0 (tagless / frameless / non-breaker rows remain) and keeps findings === 0 (newly-priced refs are the same already-validated LV refs). The plan re-verifies both invariants; no golden is regenerated.

## Integration risk + the mirror-regex divergence decision (grounded)

`parseFunctions` (normalize.ts:110) has exactly ONE functional caller - normalize.ts:507, the breaker normalize path - so the blast radius of the function itself is contained to `BreakerSignature.functions`.

However there is a DELIBERATE MIRROR: `SWITCH_TRIP_FN = /\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i` (normalize.ts:51), used by the switch-family conflict guard (assessCore switch branch, ~line 437-441 -> `switch_parent_conflict`). The line-45 comment states it "mirrors parseFunctions' L(SIGE) shape." It shares the SAME trailing-`\b` decoration blind spot (`LSIGM` will not match it either) BUT it also carries a tuned false-positive guard (`[SIGE]{2}` lookahead + `\b`) with a documented regression history: it was tightened specifically to stop mis-flagging a legitimate disconnect (tag prefixes like `LS-1`/`LG-2`/`LI-7`) as `switch_parent_conflict`.

DECISION (this lane): harden `parseFunctions` ONLY. Leave `SWITCH_TRIP_FN` unchanged, because (a) it keeps the switch family golden byte-identical (switch classification is untouched), and (b) hardening it risks re-triggering the disconnect false-positive it was tuned to prevent. The line-45 comment MUST be updated to record the intentional divergence (parseFunctions now tolerates trailing decoration; SWITCH_TRIP_FN deliberately does not, to preserve its false-positive guard). Known, DOCUMENTED gap (pre-existing, not worsened by this lane): a MISLABELED switch row carrying a decorated `LSIGM`/`LSIM` breaker descriptor will not trip `switch_parent_conflict`. It is a rare case, still catchable downstream (coverage audit / voltage-assertion gate), and a candidate follow-on only if it appears in real data. Operator may override at the spec-review gate to harden the mirror too.

The plan MUST still: run `family-dispatch`, `cross-family-guards`, and all six golden suites. If a family golden shifts, STOP and escalate - it would mean a non-breaker fixture carried a decorated token whose functions were being silently dropped; investigate before touching the golden (do NOT regenerate a family golden to make it pass).

## Verification plan

1. Unit (TDD) on `parseFunctions` for every row in the vocabulary table + the over-capture guard.
2. Unit (TDD) on `resolveMounting` for each cell: draw_out (>=800 + fns, both LSIG and LS/LSI), insulated_case (<800 + fns), molded_case (frame + no fns), unknown (no frame), and precedence preserved (hint > text > baseline), basis correctness.
3. Unit on the `missing_power_functions` trigger: fires for baseline molded_case frame>=800 no-fn; does NOT fire for text molded_case or small-frame baseline molded_case.
4. breaker-map match tests: each inferred mounting reaches its expected ref.
5. Update the four stale assertions (above) to the new contract.
6. Full `pnpm --filter @apex/estimator-takeoff test` green, including all six goldens (5 byte-identical; E01-11 invariants hold).
7. Post-merge (separate step): re-run the A/B LV-breaker preview (`run-artifact ... --allow-open-items`) and record the priced jump from 4/3 to bulk, still labeled `partial_preview` (MV non-breaker families deferred).

## Global constraints

- ASCII-only in all authored code, comments, and engine-emitted strings. Verbatim source DATA stays UTF-8.
- No new catalog refs (all target mountings already priced).
- Five family goldens byte-identical; E01-11 behavioral invariants hold.
- Additive/precedence-preserving: hint and explicit text mounting always win over the baseline (operator caution #1).
- Provenance loud: every inferred mounting carries `basis: 'estimating_baseline'`, never presented as detected (operator caution #2).
- Merge is OPERATOR-GATED. Codex + opus IRP mandatory before the merge gate.

## Out of scope (explicit)

- Panelboard-context inference (panelboard stays text/hint-only this lane).
- MV non-breaker lane (transformers / 50-51 relays / L.I. switches / CTs / PQMs) - deferred, coverage-audited.
- B tag coverage (287 tagless breakers) - separate drawing-nav lane.
- Block / data-hall quantity multipliers - config layer, needs operator inventory.
- Promoting `M` into the `TripFunction` vocabulary - `M` is a modifier with no catalog tier; not added.
