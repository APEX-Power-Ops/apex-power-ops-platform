# estimator-takeoff Runner + Reconciliation Seam — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reconciliation seam — a runnable entry that consumes a *real* drawing-nav artifact, validates it at runtime, accounts for every input row with a structured disposition, refuses to present an envelope as clean while unresolved work exists, and asserts a positive, validator-clean priced value.

**Architecture:** Additive to `@apex/estimator-takeoff`. Engine gains row-level `dispositions` (by `inputIndex`) + structured `OperatorQuestion`; a new runtime `parseArtifact` validator; a `bin` runner (`run`/`report`/`cli`) with loud partial-preview emit discipline; a provenance manifest + drift-check; the drifted 41-row fixture replaced by a manifested real artifact. `buildNativeEnvelope` is reused unchanged.

**Tech Stack:** TypeScript (Node 20), pnpm workspace, vitest. Engine builds/tests on the Olares host over mesh SSH. The fixture regen runs drawing-nav on Windows (where the PDF + producer live).

**Spec:** `docs/superpowers/specs/2026-06-26-estimator-takeoff-runner-reconciliation-design.md` @ `8b51cca0`. Read it first.

## Global Constraints

- **Branch / location:** `estimator-takeoff/runner-reconciliation` off `main` `827c83b2`; host worktree of `apex-power-ops-platform`, package `packages/estimator-takeoff`. Merge to main is OPERATOR-GATED — stop at the final whole-branch review.
- **Build/test (host):** `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; cd <pkg> && pnpm exec vitest run [file] && pnpm exec tsc --noEmit'`. A fresh worktree needs `pnpm install --frozen-lockfile` at the repo root first (worktrees carry no node_modules). The package's tsconfig has `noUncheckedIndexedAccess`.
- **Exhaustiveness invariant (load-bearing):** `result.dispositions.length === artifact.apparatus.length` and `dispositions[i].inputIndex === i` for every `i`. A row may never vanish without a disposition.
- **`ignored` ⟺ `non_breaker_excluded` only.** Every ambiguous/unclassifiable producer row is a `question`, never silently ignored. An invariant test enforces it.
- **Error findings are an unconditional hard block.** `--allow-open-items` tolerates only `unmatchedCandidates`/`operatorQuestions`; `error_findings > 0` always fails with no envelope (the voltage-assertion fail-closed contract must not be launderable into a partial preview).
- **No new runtime dependency** — hand-rolled validator, no Zod.
- **ASCII-only** user-facing strings (messages, findings, report text). No `→`/`—`.
- **Money:** the runner only READS integer `bid_cents`; no float math.
- **Commit identity:** `jasonlswenson-sys <jasonlswenson@gmail.com>`.

## File structure

- `src/buckets/types.ts` — `ApparatusDisposition*`, `DispositionReasonCode`, `TakeoffResult.dispositions`; `OperatorQuestion.code` + `inputIndex`, `OperatorQuestionCode`; re-export `EvidenceKind`. (T2, T4)
- `src/signature/types.ts` — `ApparatusSignature.inputIndex`. (T3)
- `src/signature/normalize.ts` — `q()` carries `code` (+ `inputIndex`). (T2)
- `src/quantify/quantify.ts`, `quantify/types.ts` — `lineKey`, `memberIndices`, `associated`, index-carrying `locationOnly`. (T3)
- `src/emit/emit.ts` — `runTakeoff` builds `dispositions` (move attach-to-line earlier, thread index). (T4)
- `src/extraction/parse.ts` (new) — `parseArtifact` + `ArtifactContractError`. (T1)
- `src/runner/{report.ts,run.ts,cli.ts}` (new) + `package.json` `bin`. (T5, T6)
- `src/index.ts` — exports. (T4, T6)
- `test/fixtures/stack-phx02a-e01-11.artifact.json` + `.manifest.json` (replace `-extract.json`); `scripts/regen-fixture`. (T7)
- Tests per task.

---

### Task 1: Runtime artifact validator (`parse.ts`)

**Files:**
- Create: `packages/estimator-takeoff/src/extraction/parse.ts`
- Create: `packages/estimator-takeoff/test/parse.test.ts`

**Interfaces:**
- Produces: `class ArtifactContractError extends Error { path: string; expected: string; got: string }` and `parseArtifact(json: unknown): ExtractionArtifact` — throws `ArtifactContractError` on any structural violation; returns the (same) object typed as `ExtractionArtifact` when valid. Semantic validation of `voltageAssertions` (integer/positive/tag-existence) stays in the engine; the parser checks shape only.

- [ ] **Step 1: Write the failing test** — `test/parse.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { parseArtifact, ArtifactContractError } from '../src/extraction/parse'

const ok = () => ({
  pdf: 'x.pdf',
  apparatus: [{ raw: 'MSB 4000AF/4000AT LSIG', tag: 'MSB-1', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480 }],
})

function err(mut: (a: any) => void): ArtifactContractError {
  const a = ok(); mut(a)
  try { parseArtifact(a); throw new Error('did not throw') }
  catch (e) { if (e instanceof ArtifactContractError) return e; throw e }
}

describe('parseArtifact', () => {
  it('accepts a valid artifact and returns it', () => {
    const a = ok(); expect(parseArtifact(a)).toBe(a)
  })
  it('rejects a non-array apparatus', () => { expect(err((a) => (a.apparatus = {})).path).toBe('apparatus') })
  it('rejects a missing pdf', () => { expect(err((a) => delete a.pdf).path).toBe('pdf') })
  it('rejects a bad bbox arity', () => { expect(err((a) => (a.apparatus[0].bbox = [0, 0, 1])).path).toBe('apparatus[0].bbox') })
  it('rejects a non-finite bbox value', () => { expect(err((a) => (a.apparatus[0].bbox = [0, 0, 1, Infinity])).path).toBe('apparatus[0].bbox') })
  it('rejects an unknown evidence enum', () => { expect(err((a) => (a.apparatus[0].evidence = 'guess')).path).toBe('apparatus[0].evidence') })
  it('rejects a non-integer page', () => { expect(err((a) => (a.apparatus[0].page = 1.5)).path).toBe('apparatus[0].page') })
  it('rejects a non-integer busVoltageV', () => { expect(err((a) => (a.apparatus[0].busVoltageV = 480.5)).path).toBe('apparatus[0].busVoltageV') })
  it('rejects a non-positive busVoltageV', () => { expect(err((a) => (a.apparatus[0].busVoltageV = 0)).path).toBe('apparatus[0].busVoltageV') })
  it('rejects an oversized payload', () => { expect(err((a) => (a.apparatus = Array.from({ length: 5001 }, () => ok().apparatus[0]))).path).toBe('apparatus') })
  it('rejects a malformed voltageAssertions shape', () => { expect(err((a) => (a.voltageAssertions = [{ voltageV: 480 }])).path).toBe('voltageAssertions[0].tags') })
})
```

- [ ] **Step 2: Run it red** — `pnpm exec vitest run test/parse.test.ts` → FAIL (module missing).

- [ ] **Step 3: Implement** `src/extraction/parse.ts`:

```ts
import type { ExtractionArtifact, ExtractedApparatus, EvidenceKind } from './types'
import type { Mounting } from '../signature/types'

const EVIDENCE: ReadonlySet<string> = new Set(['one-line', 'panel-schedule', 'switchgear-schedule', 'power-plan'])
const MOUNTING: ReadonlySet<string> = new Set(['draw_out', 'electrically_operated', 'insulated_case', 'molded_case', 'panelboard', 'unknown'])
const MAX_APPARATUS = 5000

export class ArtifactContractError extends Error {
  constructor(public path: string, public expected: string, public got: string) {
    super(`artifact contract violation at ${path}: expected ${expected}, got ${got}`)
    this.name = 'ArtifactContractError'
  }
}

function fail(path: string, expected: string, v: unknown): never {
  throw new ArtifactContractError(path, expected, v === undefined ? 'undefined' : JSON.stringify(v)?.slice(0, 60) ?? String(v))
}
const isStr = (v: unknown) => typeof v === 'string'
const nonEmptyStr = (v: unknown) => isStr(v) && v.length > 0
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)

export function parseArtifact(json: unknown): ExtractionArtifact {
  if (!isObj(json)) fail('', 'object', json)
  const a = json as Record<string, unknown>
  if (!nonEmptyStr(a.pdf)) fail('pdf', 'non-empty string', a.pdf)
  if (a.extractedAt !== undefined && !isStr(a.extractedAt)) fail('extractedAt', 'string', a.extractedAt)
  if (a.profileWarnings !== undefined && (!Array.isArray(a.profileWarnings) || !a.profileWarnings.every(isStr))) fail('profileWarnings', 'string[]', a.profileWarnings)
  if (!Array.isArray(a.apparatus)) fail('apparatus', 'array', a.apparatus)
  if (a.apparatus.length > MAX_APPARATUS) fail('apparatus', `<= ${MAX_APPARATUS} rows`, a.apparatus.length)
  a.apparatus.forEach((row, i) => validateRow(row, `apparatus[${i}]`))
  if (a.voltageAssertions !== undefined) {
    if (!Array.isArray(a.voltageAssertions)) fail('voltageAssertions', 'array', a.voltageAssertions)
    a.voltageAssertions.forEach((va, i) => validateAssertionShape(va, `voltageAssertions[${i}]`))
  }
  return json as ExtractionArtifact
}

function validateRow(row: unknown, p: string): void {
  if (!isObj(row)) fail(p, 'object', row)
  const r = row as Record<string, unknown>
  if (!nonEmptyStr(r.raw)) fail(`${p}.raw`, 'non-empty string', r.raw)
  if (!nonEmptyStr(r.sheet)) fail(`${p}.sheet`, 'non-empty string', r.sheet)
  if (!(typeof r.page === 'number' && Number.isInteger(r.page) && r.page >= 0)) fail(`${p}.page`, 'integer >= 0', r.page)
  if (!Array.isArray(r.bbox) || r.bbox.length !== 4 || !r.bbox.every((n) => typeof n === 'number' && Number.isFinite(n))) fail(`${p}.bbox`, '[number,number,number,number]', r.bbox)
  if (!EVIDENCE.has(r.evidence as string)) fail(`${p}.evidence`, [...EVIDENCE].join('|'), r.evidence)
  if (r.tag !== undefined && !isStr(r.tag)) fail(`${p}.tag`, 'string', r.tag)
  if (r.block !== undefined && !isStr(r.block)) fail(`${p}.block`, 'string', r.block)
  if (r.busVoltageV !== undefined && !(typeof r.busVoltageV === 'number' && Number.isInteger(r.busVoltageV) && r.busVoltageV > 0)) fail(`${p}.busVoltageV`, 'positive integer', r.busVoltageV)
  if (r.mountingHint !== undefined && !MOUNTING.has(r.mountingHint as string)) fail(`${p}.mountingHint`, [...MOUNTING].join('|'), r.mountingHint)
  if (r.candidateKind !== undefined && r.candidateKind !== 'breaker') fail(`${p}.candidateKind`, "'breaker'", r.candidateKind)
}

function validateAssertionShape(va: unknown, p: string): void {
  if (!isObj(va)) fail(p, 'object', va)
  const v = va as Record<string, unknown>
  if (typeof v.voltageV !== 'number') fail(`${p}.voltageV`, 'number', v.voltageV)
  if (!Array.isArray(v.tags) || v.tags.length === 0 || !v.tags.every(isStr)) fail(`${p}.tags`, 'non-empty string[]', v.tags)
}
```

- [ ] **Step 4: Run it green** — `pnpm exec vitest run test/parse.test.ts` + `pnpm exec tsc --noEmit`.
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): runtime artifact contract validator (parseArtifact, fail-closed)`.

---

### Task 2: Structured operator questions

**Files:**
- Modify: `packages/estimator-takeoff/src/buckets/types.ts`
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts`
- Modify: `packages/estimator-takeoff/test/normalize.test.ts`

**Interfaces:**
- Produces: `OperatorQuestion { question, context, code: OperatorQuestionCode, inputIndex? }`; `q(x, question, code, inputIndex?)` in normalize.ts. Every question site supplies a `code`.

- [ ] **Step 1: Failing test** — append to `test/normalize.test.ts`:

```ts
it('every operator question carries a structured code', () => {
  const a = assessApparatus({ raw: 'breaker', sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' })
  expect(a.questions.length).toBeGreaterThan(0)
  expect(a.questions[0]!.code).toBe('missing_voltage')
})
```
(A breaker-hint row with no voltage yields the `missing_voltage` question.)

- [ ] **Step 2: Run red** — `pnpm exec vitest run test/normalize.test.ts` → FAIL (`code` undefined).

- [ ] **Step 3: Implement.** In `src/buckets/types.ts`, extend `OperatorQuestion` and add the code union:

```ts
export type OperatorQuestionCode =
  | 'missing_voltage' | 'lv_frame_trip_unparsed' | 'missing_power_functions'
  | 'mounting_hint_conflict' | 'non_breaker_carries_rating' | 'location_only'
  | 'unrecognized_apparatus_row' | 'profile_warning'

export interface OperatorQuestion { question: string; context: string; code: OperatorQuestionCode; inputIndex?: number }
```
In `src/signature/normalize.ts`, change `q` and every call site to pass a code (inputIndex is supplied later by runTakeoff, so `q` here sets only `code`):

```ts
function q(x: ExtractedApparatus, question: string, code: OperatorQuestionCode): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})`, code }
}
```
Code map at each site (verbatim): NON_BREAKER+rating L77 -> `'non_breaker_carries_rating'`; missing-voltage L86 -> `'missing_voltage'`; LV frame/trip unparsed L96 -> `'lv_frame_trip_unparsed'`; mounting-hint conflict L106 -> `'mounting_hint_conflict'`; missing power functions L109 -> `'missing_power_functions'`. Import `OperatorQuestionCode`.

- [ ] **Step 4: Run green** — `pnpm exec vitest run test/normalize.test.ts && pnpm exec tsc --noEmit` (tsc will flag any question site missing a code — fix until clean).
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): structured operator-question codes`.

---

### Task 3: `inputIndex` on signatures + richer `quantify`

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts`
- Modify: `packages/estimator-takeoff/src/quantify/types.ts`
- Modify: `packages/estimator-takeoff/src/quantify/quantify.ts`
- Modify: `packages/estimator-takeoff/test/quantify.test.ts`

**Interfaces:**
- Consumes: `ApparatusSignature` (T-existing).
- Produces: `ApparatusSignature.inputIndex: number`; `QuantifiedLine.lineKey: string` + `memberIndices: number[]`; `quantify(sigs): { lines; associated: { inputIndex: number; lineKey: string }[]; locationOnly: { inputIndex: number; sig: ApparatusSignature }[] }`.

- [ ] **Step 1: Failing test** — append to `test/quantify.test.ts` (use the file's existing sig builder; set `inputIndex` on each):

```ts
it('exposes lineKey, memberIndices, and associated non-representative occurrences', () => {
  // two occurrences of the SAME device (same tag): a one-line (authoritative) and a power-plan (not)
  const oneLine = mk({ tag: 'B1', evidence: 'one-line', inputIndex: 0 })
  const powerPlan = mk({ tag: 'B1', evidence: 'power-plan', inputIndex: 1 })
  const r = quantify([oneLine, powerPlan])
  expect(r.lines).toHaveLength(1)
  expect(r.lines[0]!.memberIndices).toEqual([0])           // the authoritative representative
  expect(r.lines[0]!.lineKey).toBe(r.lines[0]!.signature ? specKeyOf(r.lines[0]!) : '')  // present + stable
  expect(r.associated).toContainEqual({ inputIndex: 1, lineKey: r.lines[0]!.lineKey })
})
```
(`mk`/`specKeyOf` are local helpers in the test; if absent, add a minimal `mk` that builds an `ApparatusSignature` with the given fields and a default LV/draw_out/LSIG spec so it matches a catalog rule, and read `lineKey` straight off the line for the comparison.)

- [ ] **Step 2: Run red** — FAIL (`memberIndices`/`associated` missing).

- [ ] **Step 3: Implement.** `signature/types.ts`: add `inputIndex: number` to `ApparatusSignature`. `quantify/types.ts`: add `lineKey: string` and `memberIndices: number[]` to `QuantifiedLine`. `quantify/quantify.ts`: track non-representative occurrences and indices:

```ts
export function quantify(sigs: ApparatusSignature[]): {
  lines: QuantifiedLine[]
  associated: { inputIndex: number; lineKey: string }[]
  locationOnly: { inputIndex: number; sig: ApparatusSignature }[]
} {
  const byDevice = new Map<string, ApparatusSignature[]>()
  for (const s of sigs) { const id = deviceId(s); (byDevice.get(id) ?? byDevice.set(id, []).get(id)!).push(s) }

  const counted: ApparatusSignature[] = []
  const locationOnly: { inputIndex: number; sig: ApparatusSignature }[] = []
  const nonRep: ApparatusSignature[] = []            // signature-built occurrences that are NOT the representative
  const sourcesByDevice = new Map<string, ApparatusSignature['source'][]>()
  for (const [id, occ] of byDevice) {
    const auth = pickAuthoritative(occ)
    if (!auth) { for (const o of occ) locationOnly.push({ inputIndex: o.inputIndex, sig: o }); continue }
    counted.push(auth)
    for (const o of occ) if (o !== auth) nonRep.push(o)
    sourcesByDevice.set(id, occ.map((o) => o.source))
  }

  const bySpec = new Map<string, ApparatusSignature[]>()
  for (const s of counted) { const k = specKey(s); (bySpec.get(k) ?? bySpec.set(k, []).get(k)!).push(s) }
  const lines: QuantifiedLine[] = [...bySpec.entries()].map(([k, group]) => ({
    signature: group[0]!, qty: group.length,
    sources: group.flatMap((s) => sourcesByDevice.get(deviceId(s)) ?? [s.source]),
    memberTags: group.map((s) => s.tag).filter((t): t is string => !!t),
    memberIndices: group.map((s) => s.inputIndex),
    lineKey: k,
    countedFromAuthoritative: true as const,
  }))
  const lineKeyOfDevice = (id: string): string => specKey(byDevice.get(id)!.find((o) => counted.includes(o))!)
  const associated = nonRep.map((o) => ({ inputIndex: o.inputIndex, lineKey: specKey(o) }))
  return { lines, associated, locationOnly }
}
```
(Note: a non-representative occurrence shares its device's specKey by construction, so `specKey(o)` is the line's key. If `locationOnly` previously took the whole device, it now emits one entry per occurrence index.)

- [ ] **Step 4: Run green** — `pnpm exec vitest run test/quantify.test.ts && pnpm exec tsc --noEmit`. Fix the existing quantify tests for the new `locationOnly` shape (`{inputIndex, sig}` not bare sig).
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): inputIndex + memberIndices/lineKey/associated in quantify`.

---

### Task 4: Row-level `dispositions` on `TakeoffResult`

**Files:**
- Modify: `packages/estimator-takeoff/src/buckets/types.ts`
- Modify: `packages/estimator-takeoff/src/emit/emit.ts`
- Modify: `packages/estimator-takeoff/src/index.ts`
- Create: `packages/estimator-takeoff/test/dispositions.test.ts`

**Interfaces:**
- Consumes: T1-T3 outputs (`OperatorQuestion.code/inputIndex`, `inputIndex`, quantify `associated`/`memberIndices`/`locationOnly`).
- Produces: `ApparatusDisposition`, `ApparatusDispositionStatus`, `DispositionReasonCode` (spec §3.1, verbatim); `TakeoffResult.dispositions: ApparatusDisposition[]`; re-export `EvidenceKind` from buckets. `runTakeoff` populates `dispositions` (one per `artifact.apparatus` row) and stamps `inputIndex` on signatures + `inputIndex` on each per-row question.

- [ ] **Step 1: Failing test** — `test/dispositions.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[], voltageAssertions?: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus, voltageAssertions })

describe('dispositions', () => {
  it('is exhaustive and index-aligned (one per input row)', () => {
    const a = art([row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480 }), row({ raw: 'XFMR 1000KVA', tag: 'T' }), row({ raw: 'SPARE', tag: 'S' })])
    const d = runTakeoff(a).dispositions
    expect(d).toHaveLength(3)
    d.forEach((x, i) => expect(x.inputIndex).toBe(i))
  })
  it('classifies non-breaker as ignored/non_breaker_excluded', () => {
    const d = runTakeoff(art([row({ raw: 'XFMR 1000KVA', tag: 'T' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'ignored', reasonCode: 'non_breaker_excluded' })
  })
  it('classifies an unclassifiable producer row as a question, never ignored', () => {
    const d = runTakeoff(art([row({ raw: 'SPARE', tag: 'S' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'unrecognized_apparatus_row' })
  })
  it('classifies a missing-voltage breaker as a question', () => {
    const d = runTakeoff(art([row({ raw: 'MCB 100AF/100AT', tag: 'B' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'missing_voltage' })
  })
  it('classifies a matched breaker with a ref', () => {
    const d = runTakeoff(art([row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' })])).dispositions
    expect(d[0]!.status).toBe('matched'); expect(d[0]!.ref).toBeTruthy(); expect(d[0]!.lineKey).toBeTruthy()
  })
  it('marks a non-representative occurrence as associated_source', () => {
    const a = art([
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'one-line' }),
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'power-plan' }),
    ])
    const d = runTakeoff(a).dispositions
    expect(d[1]!).toMatchObject({ status: 'associated_source', reasonCode: 'occurrence_of_counted_device' })
  })
  it('INVARIANT: no ignored row has any reasonCode other than non_breaker_excluded', () => {
    const a = art([row({ raw: 'XFMR' }), row({ raw: 'SPARE' }), row({ raw: 'ATS', tag: 'x' }), row({ raw: 'STS 800AF/800AT' })])
    for (const x of runTakeoff(a).dispositions) if (x.status === 'ignored') expect(x.reasonCode).toBe('non_breaker_excluded')
  })
})
```

- [ ] **Step 2: Run red** — FAIL (`dispositions` missing).

- [ ] **Step 3: Implement.** Add the spec §3.1 types to `src/buckets/types.ts` verbatim (status union, reasonCode union, `ApparatusDisposition`, `TakeoffResult.dispositions`); `export type { EvidenceKind } from '../extraction/types'`. Rewrite `runTakeoff` in `src/emit/emit.ts` to build a `dispositions` array of length `apparatus.length`, stamping each index per the spec §3.5 table. Skeleton:

```ts
export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const apparatus = artifact.apparatus
  const dispositions: ApparatusDisposition[] = apparatus.map((x, i) => baseDisp(x, i))   // status filled below
  const { resolved, findings } = applyVoltageAssertions(artifact)
  const questions: OperatorQuestion[] = []
  const sigs: ApparatusSignature[] = []
  const unresolved: { i: number; x: ExtractedApparatus; questions: OperatorQuestion[] }[] = []

  resolved.forEach(({ apparatus: x, voltageBasis }, i) => {
    const a = assessResolvedApparatus(x, voltageBasis)
    if (a.signature) {                                  // counted candidate — push its advisory questions, linked to the row
      sigs.push({ ...a.signature, inputIndex: i })
      for (const qq of a.questions) questions.push({ ...qq, inputIndex: i })
      return
    }
    if (a.questions.length === 0) { stamp(dispositions, i, 'ignored', 'non_breaker_excluded', 'non-breaker device token'); return }  // FINAL — not attach-eligible
    const rc = a.questions.some((qq) => qq.code === 'non_breaker_carries_rating') ? 'non_breaker_carries_rating'
             : a.questions.some((qq) => qq.code === 'missing_voltage') ? 'missing_voltage'
             : 'unrecognized_apparatus_row'
    stamp(dispositions, i, 'question', rc, a.questions[0]!.question)
    unresolved.push({ i, x, questions: a.questions })   // question rows only; DEFER pushing their questions until attach is decided
  })

  const { lines, associated, locationOnly } = quantify(sigs)
  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) for (const t of l.memberTags) byTag.set(t, l)

  // unresolved rows whose tag matches a counted line become associated_source; their (spurious) questions
  // are SUPPRESSED (preserves emit.ts L29-33 `continue`). Genuinely-unresolved rows surface their questions
  // and KEEP their 'question' disposition.
  for (const { i, x, questions: qs } of unresolved) {
    const l = x.tag ? byTag.get(x.tag) : undefined
    if (l) { l.sources.push({ sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block }); stamp(dispositions, i, 'associated_source', 'unresolved_tag_attached', `source for ${l.lineKey}`, undefined, l.lineKey) }
    else { for (const qq of qs) questions.push({ ...qq, inputIndex: i }) }
  }
  for (const { inputIndex, lineKey } of associated) stamp(dispositions, inputIndex, 'associated_source', 'occurrence_of_counted_device', `occurrence of ${lineKey}`, undefined, lineKey)
  for (const { inputIndex } of locationOnly) { stamp(dispositions, inputIndex, 'question', 'location_only_non_authoritative', 'device only on a non-authoritative sheet'); questions.push({ question: 'Device appears only on a non-authoritative sheet - include it?', context: `${apparatus[inputIndex]!.sheet}`, code: 'location_only', inputIndex }) }

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) { matchedLines.push({ ref, qty: line.qty, block: line.signature.source.block ?? line.signature.source.sheet, mountingBasis: line.signature.mountingBasis, voltageBasis: line.signature.voltageBasis, line }); for (const i of line.memberIndices) stamp(dispositions, i, 'matched', 'catalog_rule', `matched ${ref}`, ref, line.lineKey) }
    else { const reason = `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('') || '-'}`; unmatchedCandidates.push({ reason, line }); for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'no_catalog_rule', reason, undefined, line.lineKey) }
  }

  for (const w of artifact.profileWarnings ?? []) questions.push({ question: w, context: 'legend/profile', code: 'profile_warning' })

  assertExhaustive(dispositions, apparatus.length)
  return { matchedLines, unmatchedCandidates, operatorQuestions: questions, findings, dispositions }
}
```
Helpers (`baseDisp` copies the row's `inputIndex/tag/raw/sheet/page/bbox/evidence` and a sentinel `status:'question'`/`reasonCode:'unrecognized_apparatus_row'` so an unstamped row is loud, not silent; `stamp(d,i,status,reasonCode,reason,ref?,lineKey?)` overwrites; `assertExhaustive` throws if any row kept the sentinel or length mismatches). Update `src/index.ts` to export the new disposition types.

- [ ] **Step 4: Run green** — `pnpm exec vitest run && pnpm exec tsc --noEmit` (FULL suite — runTakeoff is widely used; fix call sites for the `locationOnly` shape change and any test reading the old buckets).
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): row-level dispositions on TakeoffResult (exhaustive, by inputIndex)`.

---

### Task 5: Reconciliation report (`report.ts`)

**Files:**
- Create: `packages/estimator-takeoff/src/runner/report.ts`
- Create: `packages/estimator-takeoff/test/report.test.ts`

**Interfaces:**
- Produces: `ReconciliationReport` (spec §6, verbatim) and `reconcile(artifact, result, envelopeTotals?): ReconciliationReport` — pure; computes counts, `accounted`, and carries `dispositions`. `renderReportText(report): string` for stdout (ASCII table).

- [ ] **Step 1: Failing test** — `test/report.test.ts`: build an artifact with 1 matched + 1 non-breaker + 1 missing-voltage; assert `counts.apparatus_in === 3`, `matched_lines === 1`, `ignored === 1`, `operator_questions >= 1`, `accounted === true`, and that `status` is `'partial_preview'` when open items exist.

- [ ] **Step 2: Run red.**

- [ ] **Step 3: Implement** `reconcile()`: `apparatus_in = artifact.apparatus.length`; tally from `result.dispositions` (status counts) and `result.matchedLines` (`matched_qty = Σ qty`), `findings` by severity. `accounted = dispositions.length === apparatus_in && dispositions.every((d,i)=>d.inputIndex===i)`. `status` = `'clean'` iff zero unmatched + zero questions + zero error findings, else `'partial_preview'`. `renderReportText` prints the counts block + a per-row table (`inputIndex  status  reasonCode  tag  ref`). ASCII only.

- [ ] **Step 4: Run green** + tsc.
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): reconciliation report`.

---

### Task 6: The runner + emit discipline (`run.ts`, `cli.ts`, `bin`)

**Files:**
- Create: `packages/estimator-takeoff/src/runner/run.ts`, `src/runner/cli.ts`
- Modify: `packages/estimator-takeoff/package.json` (`bin`), `src/index.ts`
- Create: `packages/estimator-takeoff/test/runner.test.ts`

**Interfaces:**
- Produces: `runFromArtifact(json: unknown, opts: { projectNumber: string; allowOpenItems: boolean }): { report: ReconciliationReport; envelope?: EstimateEnvelope; exitCode: number; stderr: string[] }` — pure/testable core; `cli.ts` is the thin argv+process wrapper. `package.json` `bin: { "estimator-takeoff": "dist/runner/cli.js" }` (or a ts entry per the package's run convention).

- [ ] **Step 1: Failing test** — `test/runner.test.ts`:

```ts
// clean: a single matched breaker, no open items -> status clean, exitCode 0, envelope present
// open items without flag -> exitCode != 0, no clean envelope
// open items WITH --allow-open-items -> status partial_preview, stderr warning, exitCode 0
// CRITICAL: an error-severity finding (e.g. unknown asserted tag) -> exitCode != 0 and NO envelope EVEN WITH allowOpenItems
// invalid JSON / contract error -> exitCode != 0
```
Concretely include: `runFromArtifact(<artifact with voltageAssertions:[{voltageV:480,tags:['NOPE']}]>, { projectNumber:'P', allowOpenItems:true })` -> `exitCode !== 0 && envelope === undefined` (the unknown-tag error finding is NOT launderable).

- [ ] **Step 2: Run red.**

- [ ] **Step 3: Implement** `runFromArtifact`: `parseArtifact` (catch -> exit 2, contract error) -> `runTakeoff` -> assert exhaustiveness -> compute `errorFindings = findings.filter(f=>f.severity==='error')`. **If `errorFindings.length > 0`: exit non-zero, NO envelope, regardless of `allowOpenItems`** (build the report with `status` reflecting the block; stderr the codes). Else if `unmatched>0 || questions>0`: if `!allowOpenItems` -> exit non-zero, no envelope; else -> call `emitEnvelope` (matched lines), `status='partial_preview'`, push the `WARNING: partial preview ...` to stderr, exit 0. Else (all clean): `emitEnvelope`, `status='clean'`, exit 0. `cli.ts` parses argv (`run <file> --project <N> [--out f] [--allow-open-items]`), reads the file, calls the core, writes `--out` JSON / prints `renderReportText`, prints stderr lines, `process.exit(exitCode)`. `package.json` gains `bin`.

- [ ] **Step 4: Run green** + tsc + (if a build step is needed for the bin) the package build.
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): runner CLI with fail-closed emit discipline (error findings never bypassable)`.

---

### Task 7: Provenance manifest + canonical fixture + drift-check

**Files:**
- Create: `packages/estimator-takeoff/scripts/regen-fixture` (documented command + sha/manifest writer)
- Create: `packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11.artifact.json` (regenerated) + `.manifest.json`
- Delete: `packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11-extract.json`
- Create: `packages/estimator-takeoff/test/drift-check.test.ts`

> **Cross-host step.** The artifact is regenerated by running drawing-nav on **Windows** (the PDF + producer live there); the resulting JSON + manifest are committed to the apex repo. The drift-check test runs on the host and is a sha256 compare (it cannot re-extract — the proprietary PDF is not in the repo).

- [ ] **Step 1: Regenerate the artifact (Windows).** Run, in `C:\Users\jjswe\Tools\drawing-nav` on drawing-nav `e7a3fb4`:
  `.venv/Scripts/python.exe drawing_nav.py extract "C:\Users\jjswe\Resa Power, LLC\...\20260616 – PHX02A – ADDENDUM 4 – ELEC.pdf" --no-timestamp --assert-voltage 480:MSB-P1-110-GB,ACC-1-09-FB,ACC-1-10-FB --out stack-phx02a-e01-11.artifact.json`
  (PDF path verified present via `index_elec.json`.) Verify the 3 asserted tags are present (they are) so no `unknown_tag` error is produced.
- [ ] **Step 2: Write the manifest** (spec §7 shape) with `producerCommit=e7a3fb4`, the exact `command`, `sha256` of the artifact bytes, `apparatusCount`. Transport both files into the package's `test/fixtures/` and `git rm` the old `-extract.json`.
- [ ] **Step 3: Failing test** — `test/drift-check.test.ts`: read the committed artifact + manifest, recompute `createHash('sha256').update(bytes).digest('hex')` and `JSON.parse(bytes).apparatus.length`, assert both equal the manifest. (Red until the manifest is correct.)
- [ ] **Step 4: Run green** + tsc.
- [ ] **Step 5: Commit** — `feat(estimator-takeoff): canonical real artifact + provenance manifest + drift-check (retire 41-row fixture)`.

---

### Task 8: Golden E2E re-baseline (real artifact -> priced, reconciled)

**Files:**
- Modify/replace: `packages/estimator-takeoff/test/golden-e01-11.test.ts`

**Interfaces:** consumes Task 6 `runFromArtifact` + Task 7 canonical fixture.

- [ ] **Step 1: Write the E2E** against the canonical artifact (with embedded voltageAssertions):

```ts
import { describe, it, expect } from 'vitest'
import artifact from './fixtures/stack-phx02a-e01-11.artifact.json'
import { runFromArtifact } from '../src/runner/run'

describe('golden E01-11 (real artifact -> reconciled priced envelope)', () => {
  const out = runFromArtifact(artifact, { projectNumber: 'PHX02A-DEMO', allowOpenItems: true })
  it('accounts for every input row', () => {
    expect(out.report.counts.apparatus_in).toBe((artifact as any).apparatus.length)
    expect(out.report.accounted).toBe(true)
  })
  it('matches the 480V draw-out mains with a catalog ref', () => {
    const matched = out.report.dispositions.filter((d) => d.status === 'matched')
    expect(matched.length).toBeGreaterThan(0)
    expect(matched.every((d) => !!d.ref)).toBe(true)
  })
  it('surfaces the real producer noise as unmatched/ignored/question (not lost)', () => {
    const tally = out.report.counts
    expect(tally.unmatched_candidates + tally.operator_questions + tally.ignored).toBeGreaterThan(0)
  })
  it('is a partial_preview (open items present) and prices positive AND clean', () => {
    expect(out.report.status).toBe('partial_preview')
    expect(out.envelope!.totals.bid_cents).toBeGreaterThan(0)
    // pricing seam is positive AND validator-clean
    const { findings } = out as any  // run carries the emit findings
    expect((findings ?? []).length).toBe(0)
  })
})
```
(If `runFromArtifact` does not already surface the emit `findings`, add them to its return so the clean-pricing assertion can read them. The exact matched count is asserted as `> 0`, not a magic number, to stay robust to producer revisions — the manifest+drift-check pins the bytes.)

- [ ] **Step 2: Run red -> implement any wiring (surface emit findings on the run result) -> green.**
- [ ] **Step 3: Full suite + tsc** — `pnpm exec vitest run && pnpm exec tsc --noEmit`.
- [ ] **Step 4: Commit** — `test(estimator-takeoff): golden E2E - real artifact to reconciled priced envelope (bid_cents>0, findings clean)`.

---

## Self-Review

**Spec coverage:** §3.1 dispositions -> T4; §3.4 quantify -> T3; §3.6 structured questions -> T2; §4 validator -> T1; §5 runner+gate -> T6; §6 report -> T5; §7 manifest/drift -> T7; §8 fixture replace + §9 pricing -> T7/T8. All covered.

**Placeholder scan:** types + tests are verbatim; the runTakeoff body is a complete skeleton with named helpers (`baseDisp`/`stamp`/`assertExhaustive`) whose contracts are stated. No TBD.

**Type consistency:** `inputIndex`, `lineKey`, `memberIndices`, `ApparatusDisposition`, `DispositionReasonCode`, `OperatorQuestionCode`, `reconcile`, `runFromArtifact`, `envelope.totals.bid_cents`, `{envelope, findings}` are spelled identically across tasks and match the grounded source.

**Ordering:** T1 (independent) -> T2 (questions) -> T3 (index+quantify) -> T4 (dispositions, depends T2/T3) -> T5 (report, depends T4) -> T6 (runner, depends T5/T1) -> T7 (fixture) -> T8 (E2E, depends T6/T7). Each ends green + tsc clean.

**Risk:** T4 rewrites `runTakeoff` (widely used) — its Step 4 runs the FULL suite, and the exhaustiveness assert is the safety net. The cross-host T7 is the only non-host step; flagged.
