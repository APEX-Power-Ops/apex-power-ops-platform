# Estimator-Takeoff Transformer Family V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Admit the POWER transformer family (dry-type + pad-mount oil) into `packages/estimator-takeoff` as a bounded V1 slice that recognizes transformers positively, attributes them, and routes each to a `scope_pending` operator decision carrying a candidate priced-ref GROUP - never auto-pricing from drawing labels.

**Architecture:** `ApparatusSignature` becomes a discriminated union on `kind`; a `match(sig)` family-dispatch routes breaker vs transformer; transformers resolve to a new `scope_pending` disposition (candidate ref-group + default tier, Gate-2 resolves later) or a `catalog_gap` finding. Breaker path behaviorally untouched + regression-guarded.

**Tech Stack:** TypeScript, `packages/estimator-takeoff` (pnpm workspace, vitest, Node 20, host build over mesh-SSH). Imports `@apex/estimator-core` for the priced catalog. Spec: `docs/superpowers/specs/2026-06-28-estimator-takeoff-transformer-family-design.md` (Rev 2).

## Global Constraints

- FAIL-CLOSED: unknown / ambiguous -> operator question; never a fabricated priced line.
- NEVER auto-price a transformer from drawing signature alone. A recognized transformer is `scope_pending` (or `catalog_gap`); V1 emits NO priced transformer line absent an explicit resolved-scope input (no such input path ships in V1).
- EXISTING catalog refs only. No new authored hours. A recognized transformer no ref-group covers -> `catalog_gap` (question + warning finding), never a fabricated `custom_equipment` line.
- BREAKER behavior untouched: the existing breaker golden envelope is byte-identical before/after (regression test).
- A `transformer` signature can NEVER reach `matchBreaker` or a priced breaker `MatchedLine` (compiler `kind`-narrowing + explicit test).
- ASCII-only in engine-emitted strings (questions / findings / notes).
- accounting-before-pricing: takeoff emits `ref + qty` only; estimator-core resolves hours/price.
- Build/test on the host: `ssh olares-mesh 'cd /home/olares/code/apex/apex-family-admission/packages/estimator-takeoff && pnpm vitest run <file> && pnpm tsc --noEmit'`. Lane `estimator-takeoff/family-admission` (rebased on main `6231f2b4`). Merge operator-gated; Codex IRP before merge.

---

## File Structure

- Modify `src/signature/types.ts` - discriminated union `BreakerSignature | TransformerSignature`.
- Modify `src/signature/normalize.ts` - transformer recognition branch + `assessTransformer` + new `AssessmentCode`s.
- Create `src/catalog/transformer-map.ts` + `src/catalog/transformer-map.data.ts` - `matchTransformer` + the R1 tier constants. (Family dispatch is the inline `sig.kind` switch in `runTakeoff`, not a separate module.)
- Modify `src/quantify/quantify.ts` - `specKey` / `pickAuthoritative` narrow on `kind`.
- Modify `src/buckets/types.ts` - `scope_pending` status, new reason/question codes, `ScopePendingLine`, `TakeoffResult.scopePendingLines`, generalize `TakeoffFinding.code`.
- Modify `src/emit/emit.ts` - `runTakeoff` match step dispatches on `kind`; `MatchedLine` build narrows; scope_pending + catalog_gap threading.
- Modify `src/runner/report.ts` - `isClean` / `unresolved_rows` count `scope_pending`.
- Modify `src/runner/run.ts` - zero-matched guard allows `scope_pending` -> open-items/partial_preview.
- Modify `src/extraction/types.ts` - `candidateKind?: 'breaker' | 'transformer'`.
- Tests: `test/transformer-catalog.test.ts`, `test/normalize-transformer.test.ts`, `test/transformer-map.test.ts`, `test/family-dispatch.test.ts`, `test/transformer-golden.test.ts`, fixture `test/fixtures/transformer-mixed.extract.json`.

---

## Task 1: Catalog authority - tier constants + live-seed validation

**R1 GATE:** the two `defaultRef` tiers are an estimating-authority call. This task pins them as RATIFIED constants if the operator has confirmed, else as a fail-closed placeholder that FAILS the validation test until ratified. Operator lean: dry `(TTR/WR/IR)`, oil `(TTR/WR/IR)`.

**Files:** Create `src/catalog/transformer-map.data.ts`; Test `test/transformer-catalog.test.ts`.
**Interfaces - Produces:** `DRY_GROUP: string[]`, `OIL_GROUP: string[]`, `DRY_DEFAULT_REF: string`, `OIL_DEFAULT_REF: string` (all refs verbatim from the estimator-core seed).

- [ ] **Step 1: Write the failing test** (`test/transformer-catalog.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF, OIL_DEFAULT_REF } from '../src/catalog/transformer-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('transformer catalog authority', () => {
  it('every group ref resolves in the live seed; no group is empty', () => {
    for (const g of [DRY_GROUP, OIL_GROUP]) {
      expect(g.length).toBeGreaterThan(0)
      for (const ref of g) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
    }
  })
  it('each default is a member of its own group and resolves', () => {
    expect(DRY_GROUP).toContain(DRY_DEFAULT_REF)
    expect(OIL_GROUP).toContain(OIL_DEFAULT_REF)
    expect(REFS.has(DRY_DEFAULT_REF) && REFS.has(OIL_DEFAULT_REF)).toBe(true)
  })
})
```

- [ ] **Step 2: Run it - expect FAIL** (module not found).
  Run: `pnpm vitest run test/transformer-catalog.test.ts` -> FAIL.

- [ ] **Step 3: Create `src/catalog/transformer-map.data.ts` with the exact seed refs.**
  First confirm (a) the seed EXPORT NAME from `@apex/estimator-core` (`EQUIPMENT_MODELS_SEED` per the breaker-map.data.ts comment - verify it is re-exported from the package index; adjust the Step-1 import if it differs) and (b) the verbatim ref strings: `ssh olares-mesh "grep -oE '\"ref\": *\"Transformer[^\"]*\"' .../estimator-core/src/catalog/equipment-models.seed.json"`. Use those EXACT strings.

```ts
// Refs verbatim from estimator-core EQUIPMENT_MODELS_SEED. Groups = the priced scope tiers per coolant (D3: power dry + oil only).
export const DRY_GROUP = [
  'Transformer - Dry Type (TTR/IR)',
  'Transformer - Dry Type (TTR/WR/IR)',
  'Transformer - Dry Type (TTR/IR/WR/PF)',
] as const satisfies readonly string[]
export const OIL_GROUP = [
  'Transformer - Pad Mount Oil (TTR/WR/IR)',
  'Transformer - Pad Mount Oil (TTR/IR/WR/PF/Oil)',
] as const satisfies readonly string[]
// R1 (estimating authority). If NOT operator-ratified, leave the PLACEHOLDER below (fails Step-4 ratify check).
export const DRY_DEFAULT_REF: string = 'Transformer - Dry Type (TTR/WR/IR)'   // [operator lean]
export const OIL_DEFAULT_REF: string = 'Transformer - Pad Mount Oil (TTR/WR/IR)' // [operator lean]
export const R1_RATIFIED = false   // operator flips to true when the two tiers are confirmed
```

- [ ] **Step 4: Add the R1 ratification MARKER as a pending test** (visible, NON-blocking - the suite stays green for the SDD flow; the FAIL-CLOSED behavior is proven by the `scope_pending` tests in Task 7, NOT by a red flag here. Defaults = operator lean, estimator-UNRATIFIED -> a Gate-2 suggestion only, never an authoritative price).

```ts
import { R1_RATIFIED } from '../src/catalog/transformer-map.data'
it.todo('R1: estimator ratifies the dry/oil default tiers -> flip R1_RATIFIED=true')
it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests, not here)', () => {
  expect(typeof R1_RATIFIED).toBe('boolean')   // provisional defaults exist; never auto-priced (Task 7)
})
```

- [ ] **Step 5: Run - all PASS** (seed/default green; the R1 `todo` shows as a pending marker, not a failure).
  Run: `pnpm vitest run test/transformer-catalog.test.ts`. `R1_RATIFIED` stays `false` until the estimator confirms the two tiers (then flip it + convert the `todo` to a real assertion); do NOT flip it without operator/estimator confirmation.

- [ ] **Step 6: Commit.** `git commit -m "feat(takeoff): transformer tier constants + live-seed validation (R1 gate)"`

---

## Task 2: Signature discriminated union + family-dispatch + breaker regression guard

**Files:** Modify `src/signature/types.ts`, `src/extraction/types.ts`, `src/catalog/breaker-map.ts` + `breaker-map.data.ts`; Test `test/family-dispatch.test.ts`, plus the existing breaker golden as a regression guard.
**Interfaces - Produces:** `BreakerSignature`, `TransformerSignature`, `ApparatusSignature` (union); `matchBreaker` narrowed to `BreakerSignature`. The family dispatch is the inline `sig.kind` switch in `runTakeoff` (Task 7), not a separate module.

- [ ] **Step 1: Failing test** (`test/family-dispatch.test.ts`) - a transformer signature never matches a breaker rule.

```ts
import { describe, it, expect } from 'vitest'
import { matchBreaker } from '../src/catalog/breaker-map'
import type { TransformerSignature } from '../src/signature/types'

it('matchBreaker rejects a transformer signature (type + runtime)', () => {
  const tx = { kind: 'transformer', voltageClass: 'LV', voltageBasis: 'detected', coolant: 'dry',
    source: { sheet: 'E1', page: 1, bbox: [0,0,1,1], evidence: 'one-line' } } as unknown as TransformerSignature
  // @ts-expect-error matchBreaker only accepts BreakerSignature
  expect(matchBreaker(tx)).toBeNull()
})
```

- [ ] **Step 2: Run - expect FAIL** (today `matchBreaker` takes the single-member `ApparatusSignature`; no `kind` discrimination, the `@ts-expect-error` is unsatisfied).
  Run: `pnpm vitest run test/family-dispatch.test.ts` and `pnpm tsc --noEmit` -> FAIL.

- [ ] **Step 3: Refactor `src/signature/types.ts` to a discriminated union.**

```ts
export type Coolant = 'dry' | 'liquid' | 'unknown'
export interface BaseSignature {
  voltageClass: VoltageClass
  voltageV?: number
  voltageBasis: VoltageBasis
  tag?: string
  inputIndex?: number
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string; block?: string }
}
export interface BreakerSignature extends BaseSignature {
  kind: 'breaker'
  frameA?: number; tripA?: number; functions: TripFunction[]
  mounting: Mounting; mountingBasis: MountingBasis; mvType?: MvType
}
export interface TransformerSignature extends BaseSignature {
  kind: 'transformer'
  kvaRating?: number; coolant: Coolant; padMount?: boolean; ltc?: boolean
}
export type ApparatusSignature = BreakerSignature | TransformerSignature
```

- [ ] **Step 4: Narrow `matchBreaker` to `BreakerSignature`** - in `src/catalog/breaker-map.ts` change the param to `BreakerSignature`; in `breaker-map.data.ts` change `BreakerRule.when: (s: BreakerSignature) => boolean` (the rules already read only breaker fields). Widen `src/extraction/types.ts` `candidateKind?: 'breaker' | 'transformer'`. NO separate dispatch module: `runTakeoff` (Task 7) switches on `sig.kind` and calls `matchBreaker` / `matchTransformer` directly. The type narrowing here is precisely what makes a transformer signature unable to reach `matchBreaker` (the `@ts-expect-error` in Step 1).

- [ ] **Step 5: Fix every compile error from the union** (breaker-field readers in `quantify.ts`, `emit.ts` now require `kind === 'breaker'` narrowing - Tasks 6/7 own those; for THIS task add the minimal `if (sig.kind !== 'breaker') ...` guards needed to compile, leaving transformer behavior as "unmatched, no line" so the breaker path is unchanged).
  Run: `pnpm tsc --noEmit` -> clean. `pnpm vitest run test/family-dispatch.test.ts` -> PASS.

- [ ] **Step 6: Breaker regression guard.** Run the FULL existing suite incl. the breaker golden: `pnpm vitest run`. Expected: ALL existing tests green, breaker golden byte-identical. If any breaker test changed output, STOP - the union refactor regressed the breaker path.

- [ ] **Step 7: Commit.** `git commit -m "refactor(takeoff): ApparatusSignature discriminated union + matchFamily dispatch (breaker path unchanged)"`

---

## Task 3: Evidence-gated transformer recognition + NON_BREAKER carve-out + conflict guard

**Files:** Modify `src/signature/normalize.ts`; Test `test/normalize-transformer.test.ts`.
**Interfaces - Produces:** `TRANSFORMER_DEVICE` regex, `KVA_RATING` regex, recognition predicate `looksLikeTransformer(x)`; new `AssessmentCode`s `transformer_recognized | transformer_breaker_conflict`.

- [ ] **Step 1: Failing tests** - recognition precision (the operator's #2): device token OR kVA-rating+designation recognizes; bare `KVA` word does NOT; transformer+breaker-rating -> conflict question.

```ts
import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
const base = { sheet: 'E1', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const }
it('recognizes a dry-type transformer device token', () => {
  const a = assessApparatus({ ...base, raw: 'T-1 480V 1500KVA DRY-TYPE XFMR', tag: 'T-1', busVoltageV: 480 })
  expect(a.assessmentCode).toBe('transformer_recognized')
})
it('does NOT recognize a bare KVA load-summary note as a transformer', () => {
  const a = assessApparatus({ ...base, raw: 'TOTAL CONNECTED LOAD 250 KVA', evidence: 'power-plan' })
  expect(a.assessmentCode).not.toBe('transformer_recognized')   // -> unrecognized_apparatus_row (a question), not a TX candidate
})
it('flags a transformer token carrying a breaker frame/trip as a conflict', () => {
  const a = assessApparatus({ ...base, raw: 'XFMR 800AF/600AT', tag: 'X1', busVoltageV: 480 })
  expect(a.assessmentCode).toBe('transformer_breaker_conflict')
  expect(a.signature).toBeNull()
})
```

- [ ] **Step 2: Run - expect FAIL.** `pnpm vitest run test/normalize-transformer.test.ts` -> FAIL.

- [ ] **Step 3: Implement recognition in `normalize.ts`** - add BEFORE the `NON_BREAKER` branch in `assessCore`; remove `TX|XFMR|KVA` from `NON_BREAKER`.

```ts
const TRANSFORMER_DEVICE = /\b(XFMR|transformer|dry.?type|pad.?mount|oil.?filled)\b/i
const KVA_RATING = /(?<!\w)\d+(?:\.\d+)?\s*kVA\b/i
const NON_BREAKER = /\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i   // TX/XFMR/KVA removed
function looksLikeTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'transformer') return true
  if (TRANSFORMER_DEVICE.test(x.raw)) return true
  return KVA_RATING.test(x.raw) && (x.tag !== undefined && x.tag.length > 0)   // rating+designation, never bare KVA
}
// inside assessCore, FIRST branch:
if (looksLikeTransformer(x)) {
  if (FRAME_TRIP.test(x.raw)) {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'transformer_breaker_conflict',
      questions: [q(x, 'Label names a transformer but carries a breaker frame/trip rating - confirm device type before counting.', 'non_breaker_carries_rating')] }
  }
  return assessTransformer(x, voltageBasis)   // Task 4
}
```
  Add `transformer_recognized | transformer_breaker_conflict | transformer_scope_pending | transformer_catalog_gap | transformer_attrs_unparsed` to `AssessmentCode`.

- [ ] **Step 4: Stub `assessTransformer`** to return `transformer_recognized` with a minimal signature (full parsing in Task 4) so Step-1 tests pass:

```ts
function assessTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) return { signature: null, isBreakerShaped: false, assessmentCode: 'missing_voltage',
    questions: [q(x, 'Looks like a transformer but has no associated bus voltage - supply voltage to classify.', 'missing_voltage')] }
  const sig: TransformerSignature = { kind: 'transformer', voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'), coolant: 'unknown', tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block } }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'transformer_recognized', questions: [] }
}
```

- [ ] **Step 5: Run - PASS** (3/3) + `pnpm tsc --noEmit` clean + FULL suite (breaker regression) green.

- [ ] **Step 6: Commit.** `git commit -m "feat(takeoff): evidence-gated transformer recognition + conflict guard (bare KVA excluded)"`

---

## Task 4: Transformer attribute parsers + full assessTransformer

**Files:** Modify `src/signature/normalize.ts`; extend `test/normalize-transformer.test.ts`.
**Interfaces - Produces:** `parseKva`, `parseCoolant`, `parsePadMount`, `parseLtc`; `assessTransformer` populates `kvaRating/coolant/padMount/ltc`; emits `transformer_attrs_unparsed` question when kVA AND coolant are both absent.

- [ ] **Step 1: Failing tests** - kVA vs kV disambiguation (the historical bug), coolant dry/oil, pad-mount, LTC, missing-attrs question.

```ts
it('parses kVA, not kV (30KVA != 30kV)', () => {
  const a = assessApparatus({ ...base, raw: 'T-2 30KVA 480V DRY', tag: 'T-2', busVoltageV: 480 })
  expect((a.signature as any).kvaRating).toBe(30)
})
it('parses coolant dry vs pad-mount oil', () => {
  expect((assessApparatus({ ...base, raw: 'PAD MOUNT OIL XFMR', tag:'T3', busVoltageV: 480 }).signature as any).coolant).toBe('liquid')
  expect((assessApparatus({ ...base, raw: 'DRY-TYPE XFMR', tag:'T4', busVoltageV: 480 }).signature as any).coolant).toBe('dry')
})
it('asks when neither kVA nor coolant is parseable', () => {
  const a = assessApparatus({ ...base, raw: 'XFMR T-9', tag: 'T-9', busVoltageV: 480 })
  expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
})
```

- [ ] **Step 2: Run - expect FAIL.**

- [ ] **Step 3: Implement parsers (text-only, fail-closed) + wire into `assessTransformer`.**

```ts
function parseKva(raw: string): number | undefined { const m = raw.match(/(?<!\w)(\d+(?:\.\d+)?)\s*kVA\b/i); return m ? Number(m[1]) : undefined }
function parseCoolant(raw: string): Coolant {
  if (/\b(oil.?filled|pad.?mount|liquid|mineral\s*oil)\b/i.test(raw)) return 'liquid'
  if (/\b(dry.?type|\bAA\b|ventilated|cast\s*resin)\b/i.test(raw)) return 'dry'
  return 'unknown'
}
function parsePadMount(raw: string): boolean { return /\bpad.?mount\b/i.test(raw) }
function parseLtc(raw: string): boolean { return /\b(LTC|load\s*tap\s*changer|on.?load\s*tap)\b/i.test(raw) }
```
  In `assessTransformer`: set `kvaRating/coolant/padMount/ltc`; if `kvaRating === undefined && coolant === 'unknown'` -> return `transformer_attrs_unparsed` question (no fabricated attrs). Keep the missing-voltage branch.

- [ ] **Step 4: Run - PASS** + tsc clean + full suite green.
- [ ] **Step 5: Commit.** `git commit -m "feat(takeoff): transformer attribute parsers (kVA/coolant/padMount/LTC) + assessTransformer"`

---

## Task 5: transformer-map (group + default) + match dispatch

**Files:** Create `src/catalog/transformer-map.ts`; wire `src/catalog/match.ts`; Test `test/transformer-map.test.ts`.
**Interfaces - Consumes:** Task 1 constants. **Produces:** `matchTransformer(sig): ScopeMatch | null` (consumed inline by `runTakeoff` in Task 7; `null` => catalog_gap).

- [ ] **Step 1: Failing tests** - dry -> 3-tier group + dry default; oil -> 2-tier group + oil default; an uncovered coolant (`unknown`) -> `null` (catalog_gap).

```ts
import { matchTransformer } from '../src/catalog/transformer-map'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF } from '../src/catalog/transformer-map.data'
const tx = (o: Partial<TransformerSignature>): TransformerSignature => ({ kind:'transformer', voltageClass:'LV', voltageBasis:'detected', coolant:'dry', source:{sheet:'E1',page:1,bbox:[0,0,1,1],evidence:'one-line'}, ...o })
it('dry -> dry tier group + dry default', () => { const r = matchTransformer(tx({ coolant:'dry' }))!; expect(r.group).toEqual([...DRY_GROUP]); expect(r.defaultRef).toBe(DRY_DEFAULT_REF) })
it('liquid pad-mount -> oil group', () => { const r = matchTransformer(tx({ coolant:'liquid', padMount:true }))!; expect(r.group).toEqual([...OIL_GROUP]) })
it('unknown coolant -> null (catalog gap)', () => { expect(matchTransformer(tx({ coolant:'unknown' }))).toBeNull() })
```

- [ ] **Step 2: Run - expect FAIL.**
- [ ] **Step 3: Implement `transformer-map.ts`** (LTC present -> base unit only + a V2-deferral note, invariant 5; never matched to an LTC ref). Add a test that an `ltc:true` dry transformer still returns the DRY group but with the deferral note in `scopeQuestion`.

```ts
import type { TransformerSignature } from '../signature/types'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF, OIL_DEFAULT_REF } from './transformer-map.data'
export interface ScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }
export function matchTransformer(sig: TransformerSignature): ScopeMatch | null {
  const ltc = sig.ltc ? ' NOTE: LTC present - LTC test scope (Tap Changer / Power-w/-LTC) deferred to V2; covers the base unit only.' : ''
  if (sig.coolant === 'dry')    return { group: [...DRY_GROUP], defaultRef: DRY_DEFAULT_REF, scopeQuestion: 'Select dry-type test scope tier (TTR/IR vs TTR/WR/IR vs TTR/IR/WR/PF).' + ltc }
  if (sig.coolant === 'liquid') return { group: [...OIL_GROUP], defaultRef: OIL_DEFAULT_REF, scopeQuestion: 'Select pad-mount-oil test scope tier (TTR/WR/IR vs +PF/Oil).' + ltc }
  return null   // unknown coolant / out-of-V1 sub-type -> catalog_gap (surfaced, never fabricated)
}
```
  `runTakeoff` (Task 7) consumes `matchTransformer` inline: a `ScopeMatch` -> `scope_pending`; `null` -> `catalog_gap`.

- [ ] **Step 4: Run - PASS** + tsc + full suite green.
- [ ] **Step 5: Commit.** `git commit -m "feat(takeoff): matchTransformer scope ref-group + family dispatch"`

---

## Task 6: quantify / specKey narrow on kind

**Files:** Modify `src/quantify/quantify.ts`; Test `test/transformer-map.test.ts` (extend) or a quantify test.
**Interfaces - Produces:** `specKey`/`pickAuthoritative` handle both kinds; two identical transformers dedupe to one line qty 2.

- [ ] **Step 1: Failing test** - two identical dry 1500kVA 480V transformers -> one quantified line, qty 2; a transformer + a breaker never share a line.

```ts
import { quantify } from '../src/quantify/quantify'
it('dedupes identical transformers; never merges across kind', () => {
  const t = (tag: string): TransformerSignature => ({ kind:'transformer', voltageClass:'LV', voltageV:480, voltageBasis:'detected', coolant:'dry', kvaRating:1500, tag, inputIndex:0, source:{sheet:'E1',page:1,bbox:[0,0,1,1],evidence:'one-line'} })
  const { lines } = quantify([{ ...t('TA') }, { ...t('TB') }])
  expect(lines).toHaveLength(1); expect(lines[0]!.qty).toBe(2)
})
```

- [ ] **Step 2: Run - expect FAIL** (today `specKey` reads `s.mounting/functions/...` which are absent on a transformer -> tsc error / wrong key).
- [ ] **Step 3: Narrow `specKey` + `pickAuthoritative`.**

```ts
function specKey(s: ApparatusSignature): string {
  const base = [s.kind, s.voltageClass, s.voltageV ?? '-', s.voltageBasis, s.source.block ?? '-']
  if (s.kind === 'breaker') return [...base, s.mounting, s.mvType ?? '-', s.functions.join(''), s.frameA ?? '-', s.tripA ?? '-'].join('|')
  return [...base, s.coolant, s.kvaRating ?? '-', s.padMount ? 'pad' : '-', s.ltc ? 'ltc' : '-'].join('|')
}
function pickAuthoritative(occ: ApparatusSignature[]): ApparatusSignature | undefined {
  const auths = occ.filter((o) => AUTHORITATIVE(o.source.evidence))
  return auths.find((o) => o.kind === 'breaker' && o.mounting !== 'unknown') ?? auths[0]
}
```

- [ ] **Step 4: Run - PASS** + tsc + full suite (breaker dedupe unchanged) green.
- [ ] **Step 5: Commit.** `git commit -m "feat(takeoff): quantify specKey/pickAuthoritative narrow on signature kind"`

---

## Task 7: scope_pending disposition + catalog_gap finding threaded end-to-end

**Files:** Modify `src/buckets/types.ts`, `src/emit/emit.ts`, `src/runner/report.ts`, `src/runner/run.ts`; Test `test/transformer-map.test.ts` (extend) / a runner test.
**Interfaces - Produces:** `ApparatusDispositionStatus += 'scope_pending'`; `DispositionReasonCode += 'transformer_scope_pending' | 'transformer_catalog_gap'`; `ScopePendingLine`; `TakeoffResult.scopePendingLines`; `TakeoffFinding.code` generalized with `'transformer_catalog_gap'` (severity `warning`).

- [ ] **Step 1: Failing tests** (a runner-level test):
  - a recognized dry transformer -> exactly one `scope_pending` disposition + one `scopePendingLines` entry carrying `DRY_GROUP` + default; 0 matchedLines; `isClean` false; `reconcile().counts.unresolved_rows` includes it.
  - an unknown-coolant transformer -> `catalog_gap` (status `unmatched`, reasonCode `transformer_catalog_gap`) + a `warning` finding; never a priced line.
  - a transformer-only artifact through `runFromArtifact({ allowOpenItems: true })` -> `partial_preview` (NOT the "nothing to price" hard stop), surfacing the scope question.

```ts
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
const art = (raw: string) => ({ pdf:'x', apparatus:[{ raw, tag:'T-1', sheet:'E1', page:1, bbox:[0,0,1,1], evidence:'one-line', busVoltageV:480 }] })
it('dry transformer -> scope_pending, no priced line, blocks clean', () => {
  const r = runTakeoff(art('T-1 1500KVA 480V DRY-TYPE XFMR') as any)
  expect(r.matchedLines).toHaveLength(0)
  expect(r.scopePendingLines).toHaveLength(1)
  expect(r.dispositions[0]!.status).toBe('scope_pending')
})
it('transformer-only artifact runs as partial_preview, not nothing-to-price', () => {
  const res = runFromArtifact(art('T-1 1500KVA 480V DRY-TYPE XFMR'), { projectNumber:'P1', allowOpenItems:true })
  expect(res.report?.status).toBe('partial_preview'); expect(res.exitCode).toBe(0)
})
```

- [ ] **Step 2: Run - expect FAIL.**
- [ ] **Step 3: buckets/types.ts** - add `scope_pending` to `ApparatusDispositionStatus`; `transformer_scope_pending | transformer_catalog_gap` to `DispositionReasonCode`; add `ScopePendingLine { candidateRefs: string[]; defaultRef: string; scopeQuestion: string; qty: number; block: string; line: QuantifiedLine }`; add `scopePendingLines: ScopePendingLine[]` to `TakeoffResult`; generalize `TakeoffFinding.code` to `VoltageAssertionCode | 'transformer_catalog_gap'`; add `transformer_scope_pending | transformer_catalog_gap` to `OperatorQuestionCode`.

- [ ] **Step 4: emit.ts `runTakeoff`** - replace the `matchBreaker` match loop with a `matchFamily` dispatch:

```ts
const scopePendingLines: ScopePendingLine[] = []
for (const line of lines) {
  const sig = line.signature
  if (sig.kind === 'breaker') {
    const ref = matchBreaker(sig)
    if (ref) { matchedLines.push({ ref, qty: line.qty, block: sig.source.block ?? sig.source.sheet, mountingBasis: sig.mountingBasis, voltageBasis: sig.voltageBasis, line })
      for (const i of line.memberIndices) stamp(dispositions, i, 'matched', 'catalog_rule', `matched ${ref}`, ref, line.lineKey) }
    else { const reason = `no catalog rule for ${sig.mounting}/${sig.functions.join('') || '-'}`
      unmatchedCandidates.push({ reason, line }); for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'no_catalog_rule', reason, undefined, line.lineKey) }
    continue
  }
  // transformer
  const scope = matchTransformer(sig)
  if (scope) {
    scopePendingLines.push({ candidateRefs: scope.group, defaultRef: scope.defaultRef, scopeQuestion: scope.scopeQuestion, qty: line.qty, block: sig.source.block ?? sig.source.sheet, line })
    for (const i of line.memberIndices) stamp(dispositions, i, 'scope_pending', 'transformer_scope_pending', scope.scopeQuestion, scope.defaultRef, line.lineKey)
    questions.push({ question: scope.scopeQuestion, context: `${sig.tag ?? sig.source.sheet} (candidate group: ${scope.group.join(' | ')})`, code: 'transformer_scope_pending' })
  } else {
    const reason = `recognized transformer (coolant ${sig.coolant}, ${sig.kvaRating ?? '?'}kVA) - no applicable priced ref-group`
    unmatchedCandidates.push({ reason, line }); for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'transformer_catalog_gap', reason, undefined, line.lineKey)
    findings.push({ code: 'transformer_catalog_gap', severity: 'warning', message: reason, context: sig.tag ?? sig.source.sheet })
    questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: sig.tag ?? sig.source.sheet, code: 'transformer_catalog_gap' })
  }
}
// return { ..., scopePendingLines } and DROP any breaker-only assumption in MatchedLine build (already kind-guarded).
```
  NOTE: `findings` here are takeoff findings (warning, non-blocking). `emitEnvelope`'s blocking filter is `severity === 'error'` so a warning never blocks; scope_pending/catalog_gap rows are never in `matchedLines` so they never price.

- [ ] **Step 5: report.ts** - `isClean.allRowsResolved` already requires status in {matched, associated_source, ignored} so `scope_pending` blocks clean (correct, no change needed) - ADD `scope_pending` to `unresolved_rows`: `d.filter((x) => x.status === 'unmatched' || x.status === 'question' || x.status === 'scope_pending').length`. `reconcilesInternally` is unaffected (scope_pending lines are neither matched nor unmatched memberships; assert their lineKey resolves by adding scopePendingLines lineKeys to the `lineKeys` set).

- [ ] **Step 6: run.ts** - refine the zero-matched guard so scope_pending is open-items, not nothing-to-price:

```ts
// 2. Zero matched guard: nothing to price ONLY if there is also nothing scope-pending.
if (result.matchedLines.length === 0 && result.scopePendingLines.length === 0) {
  stderr.push('no matched or scope-pending lines - nothing to price; review the takeoff'); return { report: accountedReport, findings: [], exitCode: 1, stderr }
}
```
  A run with only scope_pending falls through: `isClean` false (scope_pending blocks) -> open-items path -> `--allow-open-items` -> partial_preview. (Clean-path `emitEnvelope` still throws on zero matched, but isClean is false so that path is never taken.)

- [ ] **Step 7: Run - PASS** + tsc + full suite green (breaker runner behavior unchanged).
- [ ] **Step 8: Commit.** `git commit -m "feat(takeoff): scope_pending disposition + catalog_gap finding threaded through runTakeoff/report/runner"`

---

## Task 8: Real golden - dry + oil + breaker coexist; Gate-2 stand-in priced proof

**Files:** Create `test/fixtures/transformer-mixed.extract.json`, `test/transformer-golden.test.ts`.
**Interfaces - Consumes:** the whole pipeline.

- [ ] **Step 1: Build a realistic fixture** `test/fixtures/transformer-mixed.extract.json` - a one-line artifact with: one dry-type 480V transformer, one pad-mount-oil MV transformer, and one matchable LV draw-out LSIG breaker (>=800AF+G), each with a tag + busVoltageV. (ASCII; minimal but real-shaped.)

- [ ] **Step 2: Failing golden test.**

```ts
import { describe, it, expect } from 'vitest'
import fixture from './fixtures/transformer-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { buildNativeEnvelope } from '@apex/estimator-core'
import { DRY_DEFAULT_REF } from '../src/catalog/transformer-map.data'

it('families coexist: breaker prices, transformers scope_pending, partial_preview', () => {
  const r = runTakeoff(fixture as any)
  expect(r.matchedLines.length).toBe(1)                         // the breaker
  expect(r.scopePendingLines.length).toBe(2)                    // dry + oil transformers
  const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-TX', allowOpenItems: true })
  expect(res.report?.status).toBe('partial_preview')
  expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)     // the breaker line priced
})
it('Gate-2 STAND-IN: a chosen transformer tier prices through estimator-core', () => {
  // NOT a V1 product-pricing path - the engine never auto-prices a transformer (invariant 9).
  const env = buildNativeEnvelope({ projectNumber: 'PHX-TX', scopes: [{ name: 'Block X', netaStandard: 'ATS', lines: [{ ref: DRY_DEFAULT_REF, qty: 1 }] }] })
  expect(env.totals.bid_cents).toBeGreaterThan(0)
})
```

- [ ] **Step 3: Run - expect FAIL, then make green** (fixture realistic, refs resolve). `pnpm vitest run test/transformer-golden.test.ts`.
- [ ] **Step 4: Full suite + tsc + breaker golden regression all green.** `pnpm vitest run && pnpm tsc --noEmit`.
- [ ] **Step 5: Commit.** `git commit -m "test(takeoff): transformer family golden - coexist + Gate-2 stand-in priced proof"`

---

## Post-build

- Cross-engine IRP (Codex via `apex-jobs review-run --review-head estimator-takeoff/family-admission --base-ref main` + a Claude adversarial pass) BEFORE merge. Concentrate the lens on: recognition precision (bare-KVA / tag-collision false positives), the union-narrowing completeness (no breaker-field read without a `kind` guard), scope_pending never laundering into a priced line, catalog_gap vs scope_pending correctness, and the breaker regression.
- Merge operator-gated (PR, admin-rebase pattern).
- R1: confirm `R1_RATIFIED=true` (Task 1) is set only after the operator ratifies the two default tiers.
