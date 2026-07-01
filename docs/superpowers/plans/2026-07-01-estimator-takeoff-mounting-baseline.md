# Estimator-Takeoff Mounting Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, controller-executed on the host over mesh SSH) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. A mandatory Codex + opus IRP runs after Task 5, before the operator merge gate.

**Goal:** Price the ~106 (A) / ~331 (B) LV breakers that currently resolve to `mounting: 'unknown'` by broadening the estimating-baseline mounting inference AND hardening the trip-function parser so decorated descriptors (LSIGM) are not silently dropped.

**Architecture:** Three coordinated edits in `src/signature/normalize.ts` (one file): (1) `parseFunctions` regex tolerates trailing decoration; (2) `resolveMounting` baseline branch becomes a 3-way frame/function map; (3) the `missing_power_functions` question also fires for baseline-inferred large molded_case. Plus deliberate test-contract updates in three test files. No new source files, no new catalog refs.

**Tech Stack:** TypeScript, vitest 2.x, pnpm workspace. Package `@apex/estimator-takeoff`. Host worktree `/home/olares/code/apex/apex-mounting`, branch `estimator-takeoff/mounting-baseline` off main `194864d4`.

## Global Constraints

- ASCII-only in all authored code, comments, and engine-emitted strings. Source DATA stays UTF-8.
- No new catalog refs (every target mounting already priced in `breaker-map.data.ts:16-23`; all require `hasFrame`).
- The five family goldens (gfp / itx / relay / transformer / switch) MUST stay byte-identical. If any shifts, STOP and escalate - do NOT regenerate a family golden to make it pass.
- E01-11 behavioral golden invariants MUST hold: `unmatched + questions + ignored > 0` AND `findings === 0`.
- Precedence unchanged: `mountingHint` (hint) > explicit text (`parseMounting`) > estimating_baseline > none. Explicit mounting always wins.
- Every inferred mounting carries `basis: 'estimating_baseline'` (loud provenance, never presented as detected).
- `SWITCH_TRIP_FN` (normalize.ts mirror) is NOT hardened this lane; only its comment is updated to document the intentional divergence.
- The decorated-function regex must be tightly bounded: `LSIGM`, `LSIM`, `LSIGM,N.C.` parse; `LSIGMAIN` must NOT parse as `[L,S,I,G]`.
- Merge is OPERATOR-GATED.

## File Structure

- Modify `src/signature/normalize.ts`: `parseFunctions` regex (~line 113), the mirror comment (~line 45), `resolveMounting` baseline branch (~lines 149-151), `missing_power_functions` trigger (~lines 522-523).
- Modify `test/normalize.test.ts`: add parseFunctions + mounting-baseline tests; rewrite the three stale assertions.
- Modify `test/emit.test.ts`: rewrite the three shifted assertions (400AF LSI now priced).
- Modify `test/breaker-map.test.ts`: add the insulated_case-with-functions match test.

## Setup (before Task 1)

Host commands run from the worktree; prefix every node command with the PATH export.

- [ ] **S1: Install + baseline green**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm install --frozen-lockfile >/dev/null 2>&1 && cd packages/estimator-takeoff && pnpm exec vitest run 2>&1 | tail -8'
```
Expected: the full package suite passes (this is the pre-change baseline; note the counts). If it does not pass on a clean worktree, STOP - do not build on a red baseline.

---

### Task 1: parseFunctions decoration hardening + mirror comment

**Files:**
- Modify: `src/signature/normalize.ts` (`parseFunctions` regex; mirror comment ~line 45)
- Test: `test/normalize.test.ts`

**Interfaces:**
- Consumes: `normalizeApparatus(x)`, `mk(raw, v?)`, `asBreaker(...)` (existing helpers).
- Produces: `parseFunctions` now returns the L/S/I/G core for decorated descriptors; downstream `resolveMounting` (Task 2) relies on `functions.length > 0` being TRUE for LSIGM/LSIM breakers.

- [ ] **Step 1: Write failing tests** (append to the `describe('normalizeApparatus - parse', ...)` block in `test/normalize.test.ts`)

```ts
  it('parses LSIGM decorated descriptor as LSIG (M is a modifier, not dropped)', () => {
    expect(asBreaker(normalizeApparatus(mk('BKR-1 1200AF/1200AT LSIGM', 480))).functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('parses LSIM as LSI (M modifier, no ground fault)', () => {
    expect(asBreaker(normalizeApparatus(mk('BKR-2 800AF/800AT LSIM', 480))).functions).toEqual(['L', 'S', 'I'])
  })
  it('tolerates trailing N.C. decoration on LSIGM', () => {
    expect(asBreaker(normalizeApparatus(mk('BKR-3 1600AF/1600AT LSIGM,N.C.', 480))).functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('does NOT over-capture a run-together suffix word (LSIGMAIN is not LSIG)', () => {
    expect(asBreaker(normalizeApparatus(mk('BKR-4 800AF/800AT LSIGMAIN', 480))).functions).not.toEqual(['L', 'S', 'I', 'G'])
  })
  it('preserves plain LSI / LI / LSIG / LSIGE (regression)', () => {
    expect(asBreaker(normalizeApparatus(mk('B 400AF/400AT LSI', 480))).functions).toEqual(['L', 'S', 'I'])
    expect(asBreaker(normalizeApparatus(mk('B 400AF/400AT LI', 480))).functions).toEqual(['L', 'I'])
    expect(asBreaker(normalizeApparatus(mk('B 4000AF/4000AT LSIG', 480))).functions).toEqual(['L', 'S', 'I', 'G'])
    expect(asBreaker(normalizeApparatus(mk('B 800AF/800AT LSIGE', 480))).functions).toEqual(['L', 'S', 'I', 'G'])
  })
```

- [ ] **Step 2: Run tests, verify the LSIGM/LSIM/N.C. cases FAIL**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -30'
```
Expected: the LSIGM, LSIM, and `LSIGM,N.C.` tests FAIL (`functions` is `[]`); the preserve/over-capture tests PASS.

- [ ] **Step 3: Harden the regex.** In `parseFunctions` (the line `const m = region.match(/\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i)`), replace the regex with:

```ts
  const m = region.match(/\bL(?=[SIGE])(S?)(I?)(G?)(E?)[MN.,C]*\b/i)
```

The `[MN.,C]*` consumes trailing modifier/decoration characters (M, N, `.`, `,`, C) before the word boundary; the `(S?)(I?)(G?)(E?)` capture groups and the existing `tok.includes(...)` assembly are unchanged, so `M`/`N`/`C` never add a function (none of them is S/I/G/E) and the bound prevents swallowing an adjacent word.

- [ ] **Step 4: Update the mirror comment** at `SWITCH_TRIP_FN` (~line 45-51). Replace the line `// A breaker trip-function descriptor on a switch row = conflict (mirrors parseFunctions' L(SIGE) shape).` with:

```ts
// A breaker trip-function descriptor on a switch row = conflict. NOTE: this DELIBERATELY diverges from
// parseFunctions - parseFunctions tolerates trailing decoration (LSIGM/LSIM) for breaker pricing, but this
// mirror keeps the strict `[SIGE]{2}` + trailing-\b shape ON PURPOSE, to preserve the false-positive guard
// that stops tag prefixes (LS-1/LG-2) mis-flagging a legitimate disconnect as switch_parent_conflict.
```

- [ ] **Step 5: Run tests, verify all PASS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -12'
```
Expected: all normalize.test.ts cases pass. (Some mounting assertions still reflect OLD behavior - they are updated in Task 2. If any mounting test FAILS here, it is one of the four stale ones; leave it for Task 2 only if it is 70-72/74-75/78, otherwise investigate.)

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting && git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize.test.ts && git commit -q -m "feat(normalize): harden parseFunctions for decorated descriptors (LSIGM/LSIM)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" && git log --oneline -1'
```

---

### Task 2: resolveMounting baseline broadening + normalize mounting contract

**Files:**
- Modify: `src/signature/normalize.ts` (`resolveMounting` baseline branch ~lines 149-151)
- Test: `test/normalize.test.ts` (add new cells; rewrite stale 70-72 / 74-75 / 78)

**Interfaces:**
- Consumes: `resolveMounting(x, frameA, functions)` returning `{ mounting, basis, conflict }`; `functions` from Task 1.
- Produces: baseline mountings `draw_out` (>=800 + fns), `insulated_case` (<800 + fns), `molded_case` (frame + no fns), all `basis: 'estimating_baseline'`; `unknown/none` when no frame. Task 3 keys the question on `mounting === 'molded_case' && mountingBasis === 'estimating_baseline'`.

- [ ] **Step 1: Write failing tests** (append to the `describe('normalizeApparatus - construction (mounting) + provenance', ...)` block)

```ts
  it('baseline: large frame (>=800) with functions -> draw_out / estimating_baseline', () => {
    const s = asBreaker(normalizeApparatus(mk('BIG-FB 1600AF/1600AT LSIG', 480)))
    expect(s.mounting).toBe('draw_out'); expect(s.mountingBasis).toBe('estimating_baseline')
  })
  it('baseline: large frame with LS/LSI (no G) -> draw_out (removes the old requires-G rule)', () => {
    const s = asBreaker(normalizeApparatus(mk('BIG-FB 1600AF/1600AT LSI', 480)))
    expect(s.mounting).toBe('draw_out'); expect(s.mountingBasis).toBe('estimating_baseline')
  })
  it('baseline: small frame (<800) with functions -> insulated_case / estimating_baseline', () => {
    const s = asBreaker(normalizeApparatus(mk('HF-P1-110-01-FB 400AF/300AT LSI', 480)))
    expect(s.mounting).toBe('insulated_case'); expect(s.mountingBasis).toBe('estimating_baseline')
  })
  it('baseline: frame present, no functions -> molded_case / estimating_baseline', () => {
    const s = asBreaker(normalizeApparatus(mk('MC-1 250AF/250AT', 480)))
    expect(s.mounting).toBe('molded_case'); expect(s.mountingBasis).toBe('estimating_baseline')
  })
  it('baseline: no frame -> unknown / none (fail-closed; catalog requires frame)', () => {
    const s = asBreaker(normalizeApparatus(mk('NOFRAME-FB LSIG', 480)))
    expect(s.mounting).toBe('unknown'); expect(s.mountingBasis).toBe('none')
  })
  it('precedence: explicit text mount (MCCB) still wins over baseline', () => {
    const s = asBreaker(normalizeApparatus(mk('PNL MCCB 250AF/250AT LSI', 480)))
    expect(s.mounting).toBe('molded_case'); expect(s.mountingBasis).toBe('text')
  })
```

- [ ] **Step 2: Rewrite the three stale assertions** in `test/normalize.test.ts` to the new contract:
  - The test "stays unknown (fail-closed) for a 400AF LSI breaker with no evidence" (`400AF/300AT LSI` -> was `unknown`): change to expect `insulated_case` / `estimating_baseline` (or delete it - the new insulated_case test above covers it).
  - The test "does NOT apply the baseline for a large frame without ground-fault (LS/LSI)" (`1600AF/1600AT LSI` -> was `unknown`): change to expect `draw_out` / `estimating_baseline` (the new draw_out-LS/LSI test above covers it).
  - The `PANEL-DO-3 200AF/200AT LSI` -> was `unknown`: change to expect `insulated_case` (frame 200 < 800 + functions; "DO-3" is not an explicit draw-out token).

- [ ] **Step 3: Run tests, verify new cells FAIL** (old baseline still active)

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -30'
```
Expected: the new insulated_case / molded_case / draw_out-LS-LSI cells FAIL (old rule returns `unknown`).

- [ ] **Step 4: Rewrite the baseline branch** in `resolveMounting`. Replace the tail (the `const hasG = functions.includes('G')` line and the two `return` lines that follow it):

```ts
  if (frameA === undefined) return { mounting: 'unknown', basis: 'none', conflict: false }
  if (functions.length > 0) {
    return { mounting: frameA >= 800 ? 'draw_out' : 'insulated_case', basis: 'estimating_baseline', conflict: false }
  }
  return { mounting: 'molded_case', basis: 'estimating_baseline', conflict: false }
```

- [ ] **Step 5: Run tests, verify all normalize.test.ts PASS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -12'
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting && git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize.test.ts && git commit -q -m "feat(normalize): broaden estimating-baseline mounting to draw_out/insulated/molded" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" && git log --oneline -1'
```

---

### Task 3: missing_power_functions A-prime trigger

**Files:**
- Modify: `src/signature/normalize.ts` (the `missing_power_functions` `if` ~lines 522-523)
- Test: `test/normalize.test.ts`

**Interfaces:**
- Consumes: `assessApparatus(x)` returning `{ signature, questions, ... }`; `questions[i].code`.
- Produces: `missing_power_functions` question also present for baseline large molded_case.

- [ ] **Step 1: Write failing tests**

```ts
  it('flags a baseline large-frame (>=800) molded_case with no functions (missing_power_functions)', () => {
    const a = assessApparatus(mk('BIG-MC 1000AF/1000AT', 480))
    expect(asBreaker(a.signature).mounting).toBe('molded_case')
    expect(a.questions.some((qq) => qq.code === 'missing_power_functions')).toBe(true)
  })
  it('does NOT flag a small-frame (<800) baseline molded_case (genuine MCCB-scale)', () => {
    const a = assessApparatus(mk('SM-MC 250AF/250AT', 480))
    expect(a.questions.some((qq) => qq.code === 'missing_power_functions')).toBe(false)
  })
  it('does NOT flag a text-resolved molded_case (explicit MCCB, no functions)', () => {
    const a = assessApparatus(mk('PNL MCCB 1000AF/1000AT', 480))
    expect(a.questions.some((qq) => qq.code === 'missing_power_functions')).toBe(false)
  })
```
Note: `assessApparatus` returns `signature` possibly null for non-breakers; these inputs are breaker-shaped so `asBreaker(a.signature)` is safe.

- [ ] **Step 2: Run, verify the large-molded_case flag test FAILS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -20'
```
Expected: the first new test FAILS (no question today for molded_case); the two negative tests PASS.

- [ ] **Step 3: Amend the trigger.** Replace the `if` condition:

```ts
    if (functions.length === 0 && (
          mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case'
       || (mounting === 'molded_case' && mountingBasis === 'estimating_baseline' && frameA !== undefined && frameA >= 800)
    )) {
      questions.push(q(x, 'Power-breaker trip-function descriptor (e.g. LSIG) missing - confirm functions (affects LSIG vs LS/LSI vs unmatched).', 'missing_power_functions'))
    }
```

- [ ] **Step 4: Run, verify all PASS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/normalize.test.ts 2>&1 | tail -12'
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting && git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize.test.ts && git commit -q -m "feat(normalize): flag baseline large-frame molded_case missing functions (A-prime)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" && git log --oneline -1'
```

---

### Task 4: emit + breaker-map pricing contract

**Files:**
- Test: `test/emit.test.ts` (three shifted assertions), `test/breaker-map.test.ts` (add one match test)

**Interfaces:**
- Consumes: `runTakeoff(fixture)` -> `{ matchedLines, unmatchedCandidates, operatorQuestions }`; `matchBreaker(sig)`; `createDefaultCatalogResolver()`.
- Produces: no code change - this task verifies the pricing effect and updates the stale contract. The `stack-phx02a-breakers.json` fixture has exactly 4 rows; only `HF-P1-110-01-FB` (400AF LSI) moves (unmatched -> insulated_case matched), so matchedLines goes 2 -> 3 and unmatchedCandidates 1 -> 0.

- [ ] **Step 1: Add the insulated_case-with-functions match test** to `test/breaker-map.test.ts` (this path is the new baseline pricing route and is currently untested):

```ts
  it('maps LV insulated_case with LS/LSI functions to the insulated-case ref', () => {
    const ref = matchBreaker({ ...base, mounting: 'insulated_case', functions: ['L', 'S', 'I'], frameA: 400 })!
    expect(ref).toBe('Circuit Breaker LV - Insulated Case (LS/LSI)')
    expect(resolver.tryResolve(ref)).not.toBeNull()
  })
```

- [ ] **Step 2: Rewrite the three shifted emit.test.ts assertions.**
  - The assertion `expect(result.matchedLines).toHaveLength(2)`: change `2` to `3`.
  - The assertion `expect(refs.every((r) => r === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)`: replace with:

```ts
    expect(refs.filter((r) => r === 'Circuit Breaker LV - Draw-Out (LSIG)')).toHaveLength(2)
    expect(refs).toContain('Circuit Breaker LV - Insulated Case (LS/LSI)')
```

  - The test `it('fails closed: the 400AF LSI breaker with no evidence is unmatched, not guessed', ...)`: rewrite to the assume-with-provenance contract:

```ts
  it('assumes-with-provenance: the 400AF LSI breaker prices as Insulated Case (LS/LSI), basis estimating_baseline', () => {
    const hf = result.matchedLines.find((m) => m.line.signature.tag === 'HF-P1-110-01-FB')!
    expect(hf.ref).toBe('Circuit Breaker LV - Insulated Case (LS/LSI)')
    expect(hf.mountingBasis).toBe('estimating_baseline')
    expect(result.unmatchedCandidates).toHaveLength(0)
  })
```
Fail-closed coverage is not lost: the E01-11 golden still proves "no assertion -> nothing priced", and Task 2 proves "no frame -> unknown/none".

- [ ] **Step 3: Run emit + breaker-map tests, verify PASS**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run test/emit.test.ts test/breaker-map.test.ts 2>&1 | tail -20'
```
Expected: all pass. If `matchedLines` length is not 3, STOP - characterize which extra row moved before changing the number.

- [ ] **Step 4: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting && git add packages/estimator-takeoff/test/emit.test.ts packages/estimator-takeoff/test/breaker-map.test.ts && git commit -q -m "test(takeoff): update emit/breaker-map contract for baseline-priced LV breakers" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" && git log --oneline -1'
```

---

### Task 5: whole-package verification + golden integrity

**Files:** none modified (verification only, unless a shift is found).

- [ ] **Step 1: Run the full package suite**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm exec vitest run 2>&1 | tail -20'
```
Expected: ALL tests green, including the six golden suites and `family-dispatch` / `cross-family-guards`.

- [ ] **Step 2: Confirm no family golden shifted.** The five family golden suites (gfp/itx/relay/transformer/switch) must pass without edits. If any FAILED in Step 1, STOP and escalate - a non-breaker fixture carried a decorated token whose functions were being dropped; investigate, do NOT regenerate the golden.

- [ ] **Step 3: Confirm parseFunctions blast radius unchanged**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-mounting/packages/estimator-takeoff && grep -rn "parseFunctions" src/'
```
Expected: exactly two hits (the definition ~line 110 and the single caller ~line 507) plus the divergence comment - no new callers.

- [ ] **Step 4: Commit any nothing / record green.** No commit if no files changed. Record the final suite counts in the report.

---

## Post-plan (controller, not a task)

1. **Mandatory Codex + opus IRP** (Audit mode, Deep depth) on the branch diff `main..estimator-takeoff/mounting-baseline` via Workflow, per the independent-review skill: Codex cross-engine via apex-jobs review-run + opus adversarial lenses (correctness of the regex bound, the mounting map completeness, the trigger guard, golden integrity, the emit contract). Fold findings; fix; re-verify.
2. **Operator merge gate.** Present the IRP record + the priced-delta preview. Do NOT merge without the operator go.
3. **A/B LV preview (post-merge).** Re-run `run-artifact ... --allow-open-items` on `/tmp/{A2,B2}.artifact.json`; record the priced jump from 4/3 to bulk, still labeled `partial_preview` (MV non-breaker families deferred).

## Self-Review

- **Spec coverage:** Change 1 -> Task 1; Change 2 -> Task 2; Change 3 -> Task 3; stale-test updates -> Tasks 2 (normalize) + 4 (emit); no-new-catalog-refs + pricing -> Task 4; golden integrity + blast radius -> Task 5; mirror divergence -> Task 1 Step 4. All spec sections mapped.
- **Placeholder scan:** none (every code step shows the exact code/regex/command).
- **Type consistency:** `mounting` values match the `Mounting` union; `basis` matches `MountingBasis`; `functions` is `TripFunction[]`; question code `missing_power_functions` is an existing `OperatorQuestionCode`; ref strings copied verbatim from `breaker-map.data.ts`.
