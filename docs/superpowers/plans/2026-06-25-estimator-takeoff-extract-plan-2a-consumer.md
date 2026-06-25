# estimator-takeoff Plan 2a — Consumer engine change (extract seam) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the merged Plan-1 breaker engine honor the extractor's richer artifact — surface exotic-suffix breaker candidates as questions (`candidateKind`), refuse to price unrated LV breakers (`frameA` eligibility), and propagate `profileWarnings` to the operator — so `drawing-nav extract` (Plan 2b) lands cleanly.

**Architecture:** Three surgical, additive changes to `packages/estimator-takeoff` plus their tests. No new files; no behavior change for existing well-formed inputs (the Plan-1 55-test suite stays green). All work TDD over mesh-SSH on branch `estimator-takeoff/extract`.

**Tech Stack:** TypeScript 5.5, vitest, `@apex/estimator-core` (workspace), Node 20. No new deps.

## Global Constraints

- **Repo/branch:** `apex-power-ops-platform/packages/estimator-takeoff` on the Olares host, branch `estimator-takeoff/spec`'s successor **`estimator-takeoff/extract`** (off main `3a14e3cc`). Never commit to `main`.
- **Execution mechanic (mesh-SSH):** subagents author in the LOCAL staging mirror `C:\dev\estimator-takeoff-staging\packages\estimator-takeoff\`; transport with **per-file `scp`** (NEVER a whole-dir `tar` push — that + a concurrent writer corrupted host `index.ts` earlier); run ALL pnpm/vitest/git ON THE HOST (`export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH`; `ssh olares-mesh`). ONE writer per host worktree.
- **PULL before authoring:** each task pulls the current host package into staging first (`ssh olares-mesh "cd $REPO && tar -C packages/estimator-takeoff --exclude=node_modules -cf - ." | tar -C "$STAGE" -xf -`) so it edits committed truth.
- **`candidateKind` is SURFACING-ONLY:** it may make a row breaker-shaped (→ questions); it must NEVER imply mounting/functions/frame/voltage/catalog eligibility, never flow into `ApparatusSignature`/`matchBreaker`, and never override `NON_BREAKER`.
- **LV pricing invariant:** LV `matchBreaker` eligibility requires parsed **voltage + mounting + `frameA` + rule-specific fields** (G for LSIG, functions for LS/LSI). **MV is separate** (keys on `mvType`; no `frameA` requirement).
- **TDD:** failing test → run-red → minimal impl → run-green → commit. Full suite green at each task end: `pnpm --filter @apex/estimator-takeoff test`.
- **Host paths:** `STAGE=/c/dev/estimator-takeoff-staging/packages/estimator-takeoff`, `PKG=/home/olares/code/apex/apex-power-ops-platform/packages/estimator-takeoff`, `REPO=/home/olares/code/apex/apex-power-ops-platform`.

---

## File Structure

```
packages/estimator-takeoff/
  src/extraction/types.ts          # MODIFY: + candidateKind?:'breaker' (ExtractedApparatus), + profileWarnings?:string[] (ExtractionArtifact)
  src/signature/normalize.ts       # MODIFY: assessApparatus gate consults candidateKind
  src/catalog/breaker-map.data.ts  # MODIFY: LV rules require frameA!==undefined
  src/emit/emit.ts                 # MODIFY: runTakeoff propagates artifact.profileWarnings → operatorQuestions
  test/normalize.test.ts           # MODIFY: candidateKind surfacing case
  test/breaker-map.test.ts         # MODIFY: base gains frameA; + frameA-eligibility cases
  test/emit.test.ts                # MODIFY: MCB-leak-closed, real-rated-MCB-matches, DH110-UB orphan, profileWarnings
  test/extraction.test.ts          # MODIFY: contract — candidateKind/profileWarnings shape
```

---

## Task 1: `candidateKind` surfacing marker

**Files:**
- Modify: `src/extraction/types.ts`
- Modify: `src/signature/normalize.ts` (the `assessApparatus` gate)
- Test: `test/normalize.test.ts`

**Interfaces:**
- Consumes: existing `assessApparatus(x: ExtractedApparatus): ApparatusAssessment`.
- Produces: `ExtractedApparatus.candidateKind?: 'breaker'`; an exotic-suffix candidate with no AF/AT and no voltage now returns `{signature:null, isBreakerShaped:true, questions:[<missing voltage>]}`.

- [ ] **Step 1: Write the failing test** — append to `test/normalize.test.ts`'s `describe('assessApparatus — first-class questions / non-breaker handling', …)` block:

```ts
  it('surfaces an exotic-suffix breaker candidate (no GB/FB hint, no AF/AT, no voltage) via candidateKind', () => {
    const a = assessApparatus({
      raw: 'DH110-UB', tag: 'DH110-UB', sheet: 'E01-30', page: 18, bbox: [1200, 800, 1280, 812],
      evidence: 'one-line', candidateKind: 'breaker',
    })
    expect(a.isBreakerShaped).toBe(true)
    expect(a.signature).toBeNull()                 // no voltage → not classifiable
    expect(a.questions.length).toBeGreaterThan(0)  // surfaced, not dropped
  })
  it('without candidateKind, the same exotic-suffix row is not breaker-shaped (drops, pre-fix behavior)', () => {
    const a = assessApparatus({ raw: 'DH110-UB', tag: 'DH110-UB', sheet: 'E01-30', page: 18, bbox: [0, 0, 1, 1], evidence: 'one-line' })
    expect(a.isBreakerShaped).toBe(false)
  })
```

- [ ] **Step 2: Run test to verify it fails** — Run on host: `pnpm --filter @apex/estimator-takeoff test normalize`. Expected: FAIL — `candidateKind` not on `ExtractedApparatus` (type error) / first test false (row drops as not-breaker-shaped).

- [ ] **Step 3: Add the contract field** — in `src/extraction/types.ts`, add to `ExtractedApparatus` (after `mountingHint?: Mounting`):

```ts
  candidateKind?: 'breaker'                       // surfacing-only marker for a breaker-suffix token with no AF/AT (see Plan 2a)
```

- [ ] **Step 4: Wire the gate** — in `src/signature/normalize.ts`, change the single gate line in `assessApparatus`. Find:

```ts
  if (!looksLikeBreaker(x.raw)) return { signature: null, questions: [], isBreakerShaped: false }
```
Replace with:
```ts
  if (x.candidateKind !== 'breaker' && !looksLikeBreaker(x.raw)) return { signature: null, questions: [], isBreakerShaped: false }
```
(Do NOT add a separate early branch — this single edit keeps the downstream voltage/frame/mounting flow intact. The `NON_BREAKER` check above it is unchanged, so a mis-marked SPD/ATS still excludes.)

- [ ] **Step 5: Run tests to verify they pass** — Run on host: `pnpm --filter @apex/estimator-takeoff test normalize`. Expected: PASS.

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh "cd $REPO && git add packages/estimator-takeoff && git commit -m 'feat(estimator-takeoff): candidateKind surfacing marker for exotic-suffix breaker candidates'"
```

---

## Task 2: LV pricing eligibility requires `frameA`

**Files:**
- Modify: `src/catalog/breaker-map.data.ts`
- Test: `test/breaker-map.test.ts`, `test/emit.test.ts`

**Interfaces:**
- Consumes: `matchBreaker(sig)` / `BREAKER_MAP` (unchanged signature).
- Produces: LV catalog rules now require `s.frameA !== undefined`; an unrated LV candidate → `matchBreaker` returns null.

- [ ] **Step 1: Write the failing tests** — (a) in `test/breaker-map.test.ts`, add to the `describe('matchBreaker', …)` block:

```ts
  it('does NOT price an LV breaker with no parsed frame rating (frameA undefined)', () => {
    expect(matchBreaker({ ...base, mounting: 'panelboard', functions: [], frameA: undefined })).toBeNull()
    expect(matchBreaker({ ...base, mounting: 'molded_case', functions: [], frameA: undefined })).toBeNull()
    expect(matchBreaker({ ...base, mounting: 'draw_out', functions: ['L', 'S', 'I', 'G'], frameA: undefined })).toBeNull()
  })
  it('prices a rated LV panelboard MCB (frameA present, no functions needed)', () => {
    expect(matchBreaker({ ...base, mounting: 'panelboard', functions: [], frameA: 400 })).toBe('Circuit Breaker LV - Panelboard MCB')
  })
```
   (b) in `test/emit.test.ts`, add a new `describe`:

```ts
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('LV frameA eligibility (the MCB pricing leak)', () => {
  it('an unrated MCB candidate (candidateKind, 480V, no AF/AT) is never priced — surfaced instead', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'LP-1-MCB', tag: 'LP-1-MCB', sheet: 'E01-50', page: 20, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'HOUSE_NON_CRITICAL', candidateKind: 'breaker' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(0)                  // never priced
    expect(r.unmatchedCandidates.length + r.operatorQuestions.length).toBeGreaterThan(0)  // surfaced
  })
  it('a real rated MCB (400AF/400AT, 480V) is matched', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'LP-2-MCB 400AF/400AT', tag: 'LP-2-MCB', sheet: 'E01-50', page: 20, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'HOUSE_NON_CRITICAL' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(1)
    expect(r.matchedLines[0]!.ref).toBe('Circuit Breaker LV - Panelboard MCB')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail** — Run on host: `pnpm --filter @apex/estimator-takeoff test`. Expected: the new breaker-map cases FAIL (rules don't yet require frameA; `base` has no frameA so the first new case may pass spuriously while existing base-matching cases now need frameA) — see Step 3 note; the emit MCB-leak case FAILS (currently priced).

- [ ] **Step 3: Add the frame guard + fix the synthetic base** — in `src/catalog/breaker-map.data.ts`, add the helper and append `&& hasFrame(s)` to **every LV rule** (the 6 power-breaker rules and the 2 panelboard/molded rules); leave the 4 MV rules unchanged:

```ts
const hasFrame = (s: ApparatusSignature) => s.frameA !== undefined
```
Each LV rule becomes e.g.:
```ts
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out' && hasG(s) && hasFrame(s),  ref: 'Circuit Breaker LV - Draw-Out (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out' && hasFns(s) && hasFrame(s), ref: 'Circuit Breaker LV - Draw-Out (LS/LSI)' },
  // …electrically_operated (LSIG/LS-LSI), insulated_case (LSIG/LS-LSI): add `&& hasFrame(s)` likewise…
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'panelboard' && hasFrame(s),            ref: 'Circuit Breaker LV - Panelboard MCB' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'molded_case' && hasFrame(s),           ref: 'Circuit Breaker LV - Molded Case Thermal/Mag' },
```
Then in `test/breaker-map.test.ts`, give the shared `base` a frame so the existing matching cases stay valid — change the `base` literal to include:
```ts
  frameA: 800, tripA: 800,
```

- [ ] **Step 4: Run the full suite to verify green** — Run on host: `pnpm --filter @apex/estimator-takeoff test`. Expected: PASS (all suites, incl. the existing 55). Confirm the `BREAKER_MAP` length stays 12 and all refs still resolve.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh "cd $REPO && git add packages/estimator-takeoff && git commit -m 'feat(estimator-takeoff): LV catalog eligibility requires parsed frameA (close unrated-MCB pricing leak)'"
```

---

## Task 3: `profileWarnings` propagation

**Files:**
- Modify: `src/extraction/types.ts`
- Modify: `src/emit/emit.ts` (`runTakeoff`)
- Test: `test/emit.test.ts`, `test/extraction.test.ts`

**Interfaces:**
- Consumes: `runTakeoff(artifact: ExtractionArtifact): TakeoffResult`.
- Produces: `ExtractionArtifact.profileWarnings?: string[]`; each warning surfaces as an `operatorQuestion` with `context: 'legend/profile'`.

- [ ] **Step 1: Write the failing tests** — (a) in `test/emit.test.ts`:

```ts
describe('profileWarnings propagation', () => {
  it('surfaces artifact.profileWarnings as operator questions', () => {
    const art: ExtractionArtifact = { pdf: 'x', profileWarnings: ['legend E00-01 unparsed — default profile assumed'], apparatus: [] }
    const r = runTakeoff(art)
    expect(r.operatorQuestions.some((q) => /default profile assumed/.test(q.question) && q.context === 'legend/profile')).toBe(true)
  })
})
```
   (b) in `test/extraction.test.ts`, add a contract assertion:

```ts
  it('the contract carries optional profileWarnings (string[]) and candidateKind (breaker)', () => {
    const a: ExtractionArtifact = { pdf: 'x', profileWarnings: ['w'], apparatus: [
      { raw: 'X-UB', tag: 'X-UB', sheet: 'E01-30', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', candidateKind: 'breaker' },
    ] }
    expect(Array.isArray(a.profileWarnings)).toBe(true)
    expect(a.apparatus[0]!.candidateKind).toBe('breaker')
  })
```

- [ ] **Step 2: Run tests to verify they fail** — Run on host: `pnpm --filter @apex/estimator-takeoff test emit extraction`. Expected: FAIL — `profileWarnings` not on `ExtractionArtifact` (type error) / not surfaced.

- [ ] **Step 3: Add the field + propagation** — in `src/extraction/types.ts`, add to `ExtractionArtifact`:

```ts
  profileWarnings?: string[]                      // legend-fallback / unknown-title notices from the extractor (see Plan 2a)
```
In `src/emit/emit.ts`, inside `runTakeoff`, after the existing `operatorQuestions`/`questions` array is populated and before assembling the return (just before the `matchBreaker` loop is fine; pick the spot where `questions` exists), append:

```ts
  for (const w of artifact.profileWarnings ?? []) {
    questions.push({ question: w, context: 'legend/profile' })
  }
```
(Use the actual local variable name for the questions array in `runTakeoff` — it is `operatorQuestions` or `questions`; match the existing code.)

- [ ] **Step 4: Run the full suite to verify green** — Run on host: `pnpm --filter @apex/estimator-takeoff test`. Expected: PASS (all suites).

- [ ] **Step 5: Typecheck + commit**

```bash
ssh olares-mesh "cd $REPO && export PATH=\$HOME/.nvm/versions/node/v20.20.2/bin:\$PATH && pnpm --filter @apex/estimator-takeoff typecheck"
ssh olares-mesh "cd $REPO && git add packages/estimator-takeoff && git commit -m 'feat(estimator-takeoff): propagate artifact profileWarnings into operator questions'"
```

---

## Self-Review

- **Spec coverage:** §3.2(a) candidateKind → Task 1 ✓; §3.2(b) LV frameA eligibility → Task 2 ✓; §3.2(c) profileWarnings → Task 3 ✓; the min rev4 engine test set (§7: MCB-leak-closed, real-rated-MCB-matches, DH110-UB surfaces, profileWarnings surfaced, no regression, frameA eligibility units, contract shape) is covered across Tasks 1–3.
- **Placeholders:** none — every step has the exact edit/test. (Step 3 of Task 3 says "match the existing variable name" because the implementer pulls the real `emit.ts`; the runTakeoff questions array is a single obvious local — not a placeholder.)
- **Type consistency:** `candidateKind?: 'breaker'`, `profileWarnings?: string[]`, `frameA`, `OperatorQuestion {question, context}`, `runTakeoff`/`matchBreaker`/`assessApparatus` names all match the existing engine exactly.
- **No regression:** Tasks are additive; existing 55 tests + the Plan-1 golden stay green (fixture devices carry `frameA`; the gate edit is a no-op when `candidateKind` is undefined).

## Execution Handoff

Plan 2a is the small, de-risking contract change; **Plan 2b (the `drawing-nav extract` producer + golden e2e)** follows and depends on this. Recommended execution: **Subagent-Driven** over mesh-SSH (fresh implementer + reviewer per task, per-file scp, host pnpm/vitest/git), same as Plan 1.
