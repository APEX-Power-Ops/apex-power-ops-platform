# estimator-takeoff — Breaker Engine Implementation Plan (Plan 1 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic breaker takeoff engine: consume a drawing extraction JSON, normalize each device to a breaker signature (with voltage class), de-duplicate to project-wide counts, map to canonical `estimator-core` catalog refs (3 buckets), and emit a priced `EstimateEnvelope` via `buildNativeEnvelope` — proven end-to-end on STACK PHX02A breakers.

**Architecture:** A new TS package `packages/estimator-takeoff` in `apex-power-ops-platform`, depending on `@apex/estimator-core` via the workspace. Pure functions in a pipeline: `normalize → voltage → quantify → match → emit`. The package imports `estimator-core`'s `buildNativeEnvelope`, catalog resolver, and `NativeEnvelopeInput` types directly, so refs and the emit shape are type-checked and validated through canonical. `drawing-nav` (Python, Windows) supplies the extraction JSON; that JSON is the only cross-language artifact and is fixture-driven in this plan.

**Tech Stack:** TypeScript 5.5, vitest, `@apex/estimator-core` (workspace), Node 20. No new runtime deps.

> **Pre-execution corrections (v1.1, folded in 2026-06-25 from a cross-engine review — all reflected in the tasks below):**
> 1. **Golden assert** (Task 6): assert *no error-severity findings*, not *zero findings* — matches estimator-core's own native test.
> 2. **Quantify key consistency** (Task 4): a single `deviceId()` helper for BOTH grouping and source-retrieval (the sketch keyed grouping by `…@sheet:bbox` but retrieval by `…@sheet` — a real collision bug) + an untagged-duplicate test.
> 3. **ESM hygiene** (Task 5): top-level `import { BREAKER_MAP }`, never `require()` in this ESM package.
> 4. **Real config, not the sketch** (Task 0a): copy estimator-core's ACTUAL `tsconfig`/`package.json` — expect `module: ES2022`, `noUncheckedIndexedAccess: true`, `types: ["node"]`, Vitest `^2.1.0`. `noUncheckedIndexedAccess` types every index access as `T | undefined`, so keep the `!`/guards the code below already uses.

## Global Constraints

- **Repo / home:** `apex-power-ops-platform/packages/estimator-takeoff` on the Olares host (`/home/olares/code/apex/apex-power-ops-platform`). Canonical only; the Windows `C:\dev\estimator-ui-staging` copy is scratch.
- **Branch:** all work on `estimator-takeoff/spec` (the spec already lives there) or a child branch; never commit engine code to `main`.
- **Contract authority:** `@apex/estimator-core` is the ONLY source of catalog refs, the `NativeEnvelopeInput` shape, and validation. Never copy the catalog; import `EQUIPMENT_MODELS_SEED` / `createDefaultCatalogResolver` / `buildNativeEnvelope` from the package.
- **Emit path:** ALWAYS emit through `buildNativeEnvelope`. The engine constructs only `NativeEnvelopeInput` (catalog `{ref, qty}` lines). It never hand-builds `LineDraft`/`ScopeDraft` and never emits non-catalog lines — uncataloged equipment is fail-closed to the `unmatchedCandidates` bucket.
- **Voltage routing convention** (takeoff-local, NOT universal taxonomy): `LV < 1000 V`, `MV ≥ 1000 V and ≤ 69000 V`, `HV > 69000 V`.
- **Quantify rule:** count each physical device (by tag) once, only if it has ≥1 *authoritative* source (`one-line` or `*-schedule`); `power-plan` occurrences are locations and never add to the count.
- **TDD:** every task is failing test → run-red → minimal impl → run-green → commit. `pnpm --filter @apex/estimator-takeoff test`.
- **Tooling note:** run on the Olares host with Node 20 on PATH: `export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH`.

---

## File Structure

```
packages/estimator-takeoff/
  package.json                       # name @apex/estimator-takeoff, vitest, dep @apex/estimator-core
  tsconfig.json
  src/
    extraction/types.ts              # ExtractedApparatus, ExtractionArtifact  (drawing-nav → engine contract)
    signature/types.ts               # VoltageClass, Mounting, MvType, TripFunction, ApparatusSignature
    signature/voltage.ts             # classifyVoltage()
    signature/normalize.ts           # normalizeApparatus()
    quantify/types.ts                # QuantifiedLine
    quantify/quantify.ts             # quantify()
    catalog/breaker-map.data.ts      # BREAKER_MAP table (signature → estimator-core ref)
    catalog/breaker-map.ts           # matchBreaker()
    buckets/types.ts                 # MatchedLine, UnmatchedCandidate, OperatorQuestion, TakeoffResult
    emit/emit.ts                     # runTakeoff(), emitEnvelope()
    index.ts                         # public exports
  test/
    fixtures/stack-phx02a-breakers.json   # real extraction sample (hand-built from the ELEC one-lines)
    *.test.ts
```

Each file has one responsibility; files that change together (a stage + its types) live together.

---

## Task 0: Scaffold the package

**Files:**
- Create: `packages/estimator-takeoff/package.json`
- Create: `packages/estimator-takeoff/tsconfig.json`
- Create: `packages/estimator-takeoff/src/index.ts`
- Test: `packages/estimator-takeoff/test/smoke.test.ts`

**Interfaces:**
- Consumes: `@apex/estimator-core` exports `createDefaultCatalogResolver`, `EQUIPMENT_MODELS_SEED`.
- Produces: a buildable, testable workspace package.

- [ ] **Step 1: Write the failing smoke test**

```ts
// packages/estimator-takeoff/test/smoke.test.ts
import { describe, it, expect } from 'vitest'
import { createDefaultCatalogResolver, EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'

describe('estimator-takeoff wiring', () => {
  it('can reach the canonical estimator-core catalog', () => {
    expect(EQUIPMENT_MODELS_SEED.length).toBeGreaterThan(100)
    const r = createDefaultCatalogResolver()
    expect(r.tryResolve('Circuit Breaker LV - Draw-Out (LSIG)')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH && cd /home/olares/code/apex/apex-power-ops-platform && pnpm --filter @apex/estimator-takeoff test`
Expected: FAIL — package does not exist / cannot resolve `@apex/estimator-takeoff`.

- [ ] **Step 3: Create package.json, tsconfig.json, index.ts**

```jsonc
// packages/estimator-takeoff/package.json
{
  "name": "@apex/estimator-takeoff",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": { "test": "vitest run", "test:watch": "vitest", "typecheck": "tsc --noEmit" },
  "dependencies": { "@apex/estimator-core": "workspace:*" },
  "devDependencies": { "@types/node": "^20.14.0", "typescript": "^5.5.4", "vitest": "^2.0.0" }
}
```

```jsonc
// packages/estimator-takeoff/tsconfig.json  (mirror estimator-core's tsconfig; confirm in Step 0a)
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler",
    "strict": true, "esModuleInterop": true, "skipLibCheck": true,
    "resolveJsonModule": true, "noEmit": true
  },
  "include": ["src", "test"]
}
```

```ts
// packages/estimator-takeoff/src/index.ts
export {}
```

> **Step 0a (do FIRST — load-bearing, not optional):** `cat packages/estimator-core/tsconfig.json packages/estimator-core/package.json` and the root `pnpm-workspace.yaml`. **Copy estimator-core's ACTUAL config — the JSON above is a sketch and is known to differ.** Expect at least: `module: "ES2022"`, `moduleResolution` per the repo, **`noUncheckedIndexedAccess: true`**, `types: ["node"]`, and **Vitest `^2.1.0`** (match the repo's exact version + the workspace glob). Replace the two files above with what you find before running anything. With `noUncheckedIndexedAccess`, every array/index access is `T | undefined` — the code in later tasks already uses `!`/guards at those points; keep them.

- [ ] **Step 4: Install + run test to verify it passes**

Run: `pnpm install && pnpm --filter @apex/estimator-takeoff test`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff
git commit -m "feat(estimator-takeoff): scaffold package wired to estimator-core"
```

---

## Task 1: Extraction contract + a real fixture

**Files:**
- Create: `packages/estimator-takeoff/src/extraction/types.ts`
- Create: `packages/estimator-takeoff/test/fixtures/stack-phx02a-breakers.json`
- Test: `packages/estimator-takeoff/test/extraction.test.ts`

**Interfaces:**
- Produces: `ExtractedApparatus`, `ExtractionArtifact` — the drawing-nav → engine JSON contract; `loadArtifact()`.

- [ ] **Step 1: Write the failing test**

```ts
// test/extraction.test.ts
import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('extraction contract', () => {
  it('the STACK fixture conforms to ExtractionArtifact', () => {
    const a = fixture as ExtractionArtifact
    expect(a.apparatus.length).toBeGreaterThan(0)
    const first = a.apparatus[0]!
    expect(typeof first.raw).toBe('string')
    expect(typeof first.sheet).toBe('string')
    expect(first.bbox).toHaveLength(4)
    expect(['one-line', 'panel-schedule', 'switchgear-schedule', 'power-plan']).toContain(first.evidence)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test extraction`
Expected: FAIL — `extraction/types` and the fixture do not exist.

- [ ] **Step 3: Create the types and the fixture**

```ts
// src/extraction/types.ts
export type EvidenceKind = 'one-line' | 'panel-schedule' | 'switchgear-schedule' | 'power-plan'

export interface ExtractedApparatus {
  raw: string                                   // raw label/spec text near the device
  tag?: string                                  // device identity, e.g. "MSB-P1-110-GB"
  sheet: string                                 // e.g. "E01-11"
  page: number
  bbox: [number, number, number, number]
  evidence: EvidenceKind
  busVoltageV?: number                          // nominal bus voltage if drawing-nav associated one
  block?: string                                // electrical block, e.g. "P1-110"
}

export interface ExtractionArtifact {
  pdf: string
  extractedAt?: string                          // ISO string stamped by drawing-nav (string, not Date)
  apparatus: ExtractedApparatus[]
}
```

```jsonc
// test/fixtures/stack-phx02a-breakers.json  (hand-built from the real E01-11 one-line; expand as needed)
{
  "pdf": "20260616 - PHX02A - ADDENDUM 4 - ELEC.pdf",
  "apparatus": [
    { "raw": "MSB-P1-110-GB 4000AF/4000AT LSIG", "tag": "MSB-P1-110-GB", "sheet": "E01-11",
      "page": 11, "bbox": [60, 30, 180, 45], "evidence": "one-line", "busVoltageV": 480, "block": "P1-110" },
    { "raw": "HF-P1-110-01-FB 400AF/300AT LSI", "tag": "HF-P1-110-01-FB", "sheet": "E01-11",
      "page": 11, "bbox": [300, 60, 360, 75], "evidence": "one-line", "busVoltageV": 480, "block": "P1-110" },
    { "raw": "ACC-1-09-FB 800AF/800AT LSIGE", "tag": "ACC-1-09-FB", "sheet": "E01-11",
      "page": 11, "bbox": [886, 491, 944, 501], "evidence": "one-line", "busVoltageV": 480, "block": "P1-110" },
    { "raw": "ACC-1-09 (location)", "tag": "ACC-1-09-FB", "sheet": "E02-03D",
      "page": 38, "bbox": [644, 1668, 686, 1678], "evidence": "power-plan", "block": "P1-110" }
  ]
}
```

> The two `ACC-1-09-FB` rows are the same device on the one-line and a power plan — Task 3 must count it once.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test extraction`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/extraction packages/estimator-takeoff/test/extraction.test.ts packages/estimator-takeoff/test/fixtures
git commit -m "feat(estimator-takeoff): drawing-nav extraction contract + STACK breaker fixture"
```

---

## Task 2: Voltage classification

**Files:**
- Create: `packages/estimator-takeoff/src/signature/types.ts`
- Create: `packages/estimator-takeoff/src/signature/voltage.ts`
- Test: `packages/estimator-takeoff/test/voltage.test.ts`

**Interfaces:**
- Produces: `VoltageClass`, `Mounting`, `MvType`, `TripFunction`, `ApparatusSignature`; `classifyVoltage(voltageV?: number): VoltageClass | undefined`.

- [ ] **Step 1: Write the failing test**

```ts
// test/voltage.test.ts
import { describe, it, expect } from 'vitest'
import { classifyVoltage } from '../src/signature/voltage'

describe('classifyVoltage (takeoff routing convention)', () => {
  it.each([
    [480, 'LV'], [600, 'LV'], [999, 'LV'],
    [1000, 'MV'], [4160, 'MV'], [13800, 'MV'], [69000, 'MV'],
    [69001, 'HV'], [115000, 'HV'], [230000, 'HV'],
  ])('classifies %iV as %s', (v, cls) => {
    expect(classifyVoltage(v)).toBe(cls)
  })
  it('returns undefined when voltage is unknown', () => {
    expect(classifyVoltage(undefined)).toBeUndefined()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test voltage`
Expected: FAIL — `classifyVoltage` not defined.

- [ ] **Step 3: Write the types + implementation**

```ts
// src/signature/types.ts
export type VoltageClass = 'LV' | 'MV' | 'HV'
export type Mounting =
  | 'draw_out' | 'electrically_operated' | 'insulated_case'
  | 'molded_case' | 'panelboard' | 'unknown'
export type MvType = 'air_frame' | 'vacuum' | 'sf6' | 'oil' | 'unknown'
export type TripFunction = 'L' | 'S' | 'I' | 'G'

export interface ApparatusSignature {
  kind: 'breaker'
  voltageClass: VoltageClass
  voltageV?: number
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting
  mvType?: MvType
  tag?: string
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string }
}
```

```ts
// src/signature/voltage.ts
import type { VoltageClass } from './types'

// Takeoff routing convention (NOT a universal taxonomy):
// LV < 1000 V ; MV >= 1000 V and <= 69000 V ; HV > 69000 V
export function classifyVoltage(voltageV: number | undefined): VoltageClass | undefined {
  if (voltageV === undefined) return undefined
  if (voltageV < 1000) return 'LV'
  if (voltageV <= 69000) return 'MV'
  return 'HV'
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test voltage`
Expected: PASS (10 cases).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/signature packages/estimator-takeoff/test/voltage.test.ts
git commit -m "feat(estimator-takeoff): signature types + voltage routing classification"
```

---

## Task 3: Normalize raw apparatus → breaker signature

**Files:**
- Create: `packages/estimator-takeoff/src/signature/normalize.ts`
- Test: `packages/estimator-takeoff/test/normalize.test.ts`

**Interfaces:**
- Consumes: `ExtractedApparatus` (Task 1), `classifyVoltage` (Task 2), signature types (Task 2).
- Produces: `normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null` (null = not a breaker / unparseable).

- [ ] **Step 1: Write the failing test**

```ts
// test/normalize.test.ts
import { describe, it, expect } from 'vitest'
import { normalizeApparatus } from '../src/signature/normalize'
import type { ExtractedApparatus } from '../src/extraction/types'

const mk = (raw: string, v?: number): ExtractedApparatus => ({
  raw, tag: 'X', sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: v,
})

describe('normalizeApparatus', () => {
  it('parses frame/trip and LSIG functions on a 480V draw-out breaker', () => {
    const s = normalizeApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480))!
    expect(s.voltageClass).toBe('LV')
    expect(s.frameA).toBe(4000)
    expect(s.tripA).toBe(4000)
    expect(s.functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('parses LS/LSI subset and trailing E (ground-fault sensing) as G', () => {
    const s = normalizeApparatus(mk('ACC-1-09-FB 800AF/800AT LSIGE', 480))!
    expect(s.functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('classifies molded-case from the MCB/molded keyword', () => {
    expect(normalizeApparatus(mk('LP-1 MCB 100AF/20AT', 480))!.mounting).toBe('panelboard')
  })
  it('classifies an MV vacuum breaker', () => {
    const s = normalizeApparatus(mk('MV-SWGR-1 VACUUM 1200A', 13800)!)!
    expect(s.voltageClass).toBe('MV')
    expect(s.mvType).toBe('vacuum')
  })
  it('returns null for a non-breaker label', () => {
    expect(normalizeApparatus(mk('TX-P1-110 535KVA', 480))).toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test normalize`
Expected: FAIL — `normalizeApparatus` not defined.

- [ ] **Step 3: Write the implementation**

```ts
// src/signature/normalize.ts
import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, Mounting, MvType, TripFunction } from './types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(\d{2,4})\s*AF\s*\/\s*(\d{2,4})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(AF\s*\/|MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
// device tags that are clearly NOT breakers
const NON_BREAKER = /\b(TX|XFMR|KVA|PDU|UPS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

function parseFunctions(raw: string): TripFunction[] {
  const m = raw.match(/\bL?S?I?G?E?\b/g)?.find((t) => /^L?S?I?G?E?$/.test(t) && t.length >= 2 && /[LSIG]/.test(t))
  if (!m) return []
  const out: TripFunction[] = []
  if (m.includes('L')) out.push('L')
  if (m.includes('S')) out.push('S')
  if (m.includes('I')) out.push('I')
  if (m.includes('G') || m.includes('E')) out.push('G') // trailing E = ground-fault sensing → G
  return out
}

function parseMounting(raw: string): Mounting {
  if (/\bMCB\b|panelboard/i.test(raw)) return 'panelboard'
  if (/molded\s*case|MCCB/i.test(raw)) return 'molded_case'
  if (/insulated\s*case|\bICCB\b/i.test(raw)) return 'insulated_case'
  if (/electrically\s*operated|\bEO\b/i.test(raw)) return 'electrically_operated'
  if (/draw.?out|\bDO\b/i.test(raw)) return 'draw_out'
  return 'unknown'
}

function parseMvType(raw: string): MvType {
  if (/vacuum|\bVCB\b/i.test(raw)) return 'vacuum'
  if (/SF6/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/air\s*frame/i.test(raw)) return 'air_frame'
  return 'unknown'
}

export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  if (NON_BREAKER.test(x.raw) && !/AF\s*\//i.test(x.raw)) return null
  if (!BREAKER_HINT.test(x.raw)) return null
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) return null
  const ft = x.raw.match(FRAME_TRIP)
  const mounting = voltageClass === 'LV' ? parseMounting(x.raw) : 'unknown'
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined
  return {
    kind: 'breaker',
    voltageClass,
    voltageV: x.busVoltageV,
    frameA: ft ? Number(ft[1]) : undefined,
    tripA: ft ? Number(ft[2]) : undefined,
    functions: parseFunctions(x.raw),
    mounting,
    mvType,
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence },
  }
}
```

> Note for the implementer: the regexes above are a v1 starting point sized to the STACK fixture. Treat any normalize miss surfaced by the golden test (Task 6) as a new failing test case first, then widen the regex — never loosen it blindly.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test normalize`
Expected: PASS (5 cases).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize.test.ts
git commit -m "feat(estimator-takeoff): normalize raw apparatus to breaker signature"
```

---

## Task 4: Quantify — de-dup by device, authoritative-source rule

**Files:**
- Create: `packages/estimator-takeoff/src/quantify/types.ts`
- Create: `packages/estimator-takeoff/src/quantify/quantify.ts`
- Test: `packages/estimator-takeoff/test/quantify.test.ts`

**Interfaces:**
- Consumes: `ApparatusSignature` (Task 2).
- Produces: `QuantifiedLine { signature, qty, sources, countedFromAuthoritative }`; `quantify(sigs: ApparatusSignature[]): { lines: QuantifiedLine[]; locationOnly: ApparatusSignature[] }`.

- [ ] **Step 1: Write the failing test**

```ts
// test/quantify.test.ts
import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { ApparatusSignature } from '../src/signature/types'

const sig = (tag: string, evidence: string, sheet = 'E01-11'): ApparatusSignature => ({
  kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out',
  tag, source: { sheet, page: 1, bbox: [0, 0, 1, 1], evidence },
})

describe('quantify', () => {
  it('counts the same device once across one-line + power-plan, keeping both sources', () => {
    const { lines } = quantify([sig('ACC-1-09-FB', 'one-line'), sig('ACC-1-09-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(1)
    expect(lines[0]!.sources).toHaveLength(2)
  })
  it('counts two distinct devices of the same spec as qty 2', () => {
    const { lines } = quantify([sig('HF-01-FB', 'one-line'), sig('HF-02-FB', 'one-line')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
  })
  it('does NOT count a device seen only on a power-plan; reports it location-only', () => {
    const { lines, locationOnly } = quantify([sig('GHOST-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(0)
    expect(locationOnly).toHaveLength(1)
    expect(locationOnly[0]!.tag).toBe('GHOST-FB')
  })
  it('keeps two UNTAGGED same-spec devices distinct by bbox (no source collision)', () => {
    const untagged = (bbox: [number, number, number, number]): ApparatusSignature => ({
      kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I'], mounting: 'molded_case',
      source: { sheet: 'E05-20', page: 1, bbox, evidence: 'panel-schedule' },
    })
    const { lines } = quantify([untagged([0, 0, 1, 1]), untagged([2, 2, 3, 3])])
    expect(lines).toHaveLength(1)               // same spec → one line
    expect(lines[0]!.qty).toBe(2)               // two distinct devices (distinct bbox)
    expect(lines[0]!.sources).toHaveLength(2)   // both sources retained — the deviceId() fix prevents collision
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test quantify`
Expected: FAIL — `quantify` not defined.

- [ ] **Step 3: Write the implementation**

```ts
// src/quantify/types.ts
import type { ApparatusSignature } from '../signature/types'
export interface QuantifiedLine {
  signature: ApparatusSignature                 // representative signature (authoritative occurrence)
  qty: number                                   // distinct devices counted
  sources: ApparatusSignature['source'][]       // every contributing occurrence (incl. power-plan locations)
  countedFromAuthoritative: true
}
```

```ts
// src/quantify/quantify.ts
import type { ApparatusSignature } from '../signature/types'
import type { QuantifiedLine } from './types'

const AUTHORITATIVE = (e: string) => e === 'one-line' || e.endsWith('-schedule')

function specKey(s: ApparatusSignature): string {
  return [s.voltageClass, s.mounting, s.mvType ?? '-', s.functions.join(''), s.frameA ?? '-', s.tripA ?? '-'].join('|')
}

// Stable device identity used for BOTH grouping AND source-retrieval. These MUST be identical in
// both places — keying grouping by `…@sheet:bbox` but retrieval by `…@sheet` collides untagged
// devices and drops their sources. Tagged → the tag; untagged → spec + sheet + bbox.
function deviceId(s: ApparatusSignature): string {
  return s.tag ?? `${specKey(s)}@${s.source.sheet}:${s.source.bbox.join(',')}`
}

export function quantify(sigs: ApparatusSignature[]): {
  lines: QuantifiedLine[]
  locationOnly: ApparatusSignature[]
} {
  // 1) group every occurrence by device identity
  const byDevice = new Map<string, ApparatusSignature[]>()
  for (const s of sigs) {
    const id = deviceId(s)
    ;(byDevice.get(id) ?? byDevice.set(id, []).get(id)!).push(s)
  }

  // 2) a device counts only if it has >=1 authoritative occurrence; store sources under the SAME id
  const counted: ApparatusSignature[] = []
  const locationOnly: ApparatusSignature[] = []
  const sourcesByDevice = new Map<string, ApparatusSignature['source'][]>()
  for (const [id, occ] of byDevice) {
    const auth = occ.find((o) => AUTHORITATIVE(o.source.evidence))
    if (!auth) { locationOnly.push(occ[0]!); continue }
    counted.push(auth)
    sourcesByDevice.set(id, occ.map((o) => o.source))
  }

  // 3) aggregate counted devices by spec into quantified lines; retrieve sources by the SAME deviceId
  const bySpec = new Map<string, ApparatusSignature[]>()
  for (const s of counted) {
    const k = specKey(s)
    ;(bySpec.get(k) ?? bySpec.set(k, []).get(k)!).push(s)
  }
  const lines: QuantifiedLine[] = [...bySpec.values()].map((group) => ({
    signature: group[0]!,
    qty: group.length,
    sources: group.flatMap((s) => sourcesByDevice.get(deviceId(s)) ?? [s.source]),
    countedFromAuthoritative: true as const,
  }))
  return { lines, locationOnly }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test quantify`
Expected: PASS (3 cases).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/quantify packages/estimator-takeoff/test/quantify.test.ts
git commit -m "feat(estimator-takeoff): quantify with device de-dup + authoritative-source rule"
```

---

## Task 5: Catalog match — signature → estimator-core ref (3 buckets)

**Files:**
- Create: `packages/estimator-takeoff/src/catalog/breaker-map.data.ts`
- Create: `packages/estimator-takeoff/src/catalog/breaker-map.ts`
- Create: `packages/estimator-takeoff/src/buckets/types.ts`
- Test: `packages/estimator-takeoff/test/breaker-map.test.ts`

**Interfaces:**
- Consumes: `ApparatusSignature` (Task 2), `QuantifiedLine` (Task 4), `createDefaultCatalogResolver` (`@apex/estimator-core`).
- Produces: `matchBreaker(sig: ApparatusSignature): string | null` (returns a catalog `ref` or null); `MatchedLine`, `UnmatchedCandidate`, `OperatorQuestion`.

- [ ] **Step 1: Write the failing test**

```ts
// test/breaker-map.test.ts
import { describe, it, expect } from 'vitest'
import { matchBreaker } from '../src/catalog/breaker-map'
import { BREAKER_MAP } from '../src/catalog/breaker-map.data'
import { createDefaultCatalogResolver } from '@apex/estimator-core'
import type { ApparatusSignature } from '../src/signature/types'

const base: ApparatusSignature = {
  kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out',
  source: { sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}
const resolver = createDefaultCatalogResolver()

describe('matchBreaker', () => {
  it('maps LV draw-out LSIG to a ref that exists in the canonical catalog', () => {
    const ref = matchBreaker(base)!
    expect(ref).toBe('Circuit Breaker LV - Draw-Out (LSIG)')
    expect(resolver.tryResolve(ref)).not.toBeNull()      // every mapped ref MUST resolve
  })
  it('maps LV draw-out LS/LSI (no G) to the LS/LSI ref', () => {
    expect(matchBreaker({ ...base, functions: ['L', 'S', 'I'] })).toBe('Circuit Breaker LV - Draw-Out (LS/LSI)')
  })
  it('maps an MV vacuum breaker', () => {
    expect(matchBreaker({ ...base, voltageClass: 'MV', mounting: 'unknown', mvType: 'vacuum' }))
      .toBe('Circuit Breaker MV - Vacuum Bkr')
  })
  it('returns null for an unmappable signature (HV, no type)', () => {
    expect(matchBreaker({ ...base, voltageClass: 'HV', mounting: 'unknown' })).toBeNull()
  })
  it('every ref in the map resolves in the canonical catalog', () => {
    for (const rule of BREAKER_MAP) expect(resolver.tryResolve(rule.ref)).not.toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test breaker-map`
Expected: FAIL — `matchBreaker` not defined.

- [ ] **Step 3: Write the mapping table + matcher**

```ts
// src/catalog/breaker-map.data.ts
import type { ApparatusSignature } from '../signature/types'

export interface BreakerRule {
  when: (s: ApparatusSignature) => boolean
  ref: string                                    // MUST exist in estimator-core EQUIPMENT_MODELS_SEED
}

const hasG = (s: ApparatusSignature) => s.functions.includes('G')

// Refs are verbatim from the canonical catalog (packages/estimator-core/src/catalog/equipment-models.seed.json).
export const BREAKER_MAP: BreakerRule[] = [
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out' && hasG(s),  ref: 'Circuit Breaker LV - Draw-Out (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out',             ref: 'Circuit Breaker LV - Draw-Out (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'electrically_operated' && hasG(s), ref: 'Circuit Breaker LV - Electrically Operated (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'electrically_operated', ref: 'Circuit Breaker LV - Electrically Operated (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'insulated_case' && hasG(s),  ref: 'Circuit Breaker LV - Insulated Case (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'insulated_case',        ref: 'Circuit Breaker LV - Insulated Case (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'panelboard',            ref: 'Circuit Breaker LV - Panelboard MCB' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'molded_case',           ref: 'Circuit Breaker LV - Molded Case Thermal/Mag' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'vacuum',                  ref: 'Circuit Breaker MV - Vacuum Bkr' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'air_frame',               ref: 'Circuit Breaker MV - Air Frame' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'oil',                     ref: 'Circuit Breaker MV - Oil Insluated' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'sf6',                     ref: 'Circuit Breaker MV - SF6 (230kV & Under)' },
]
```

```ts
// src/catalog/breaker-map.ts
import type { ApparatusSignature } from '../signature/types'
import { BREAKER_MAP } from './breaker-map.data'

export function matchBreaker(sig: ApparatusSignature): string | null {
  return BREAKER_MAP.find((rule) => rule.when(sig))?.ref ?? null
}
```

```ts
// src/buckets/types.ts
import type { ApparatusSignature } from '../signature/types'
import type { QuantifiedLine } from '../quantify/types'

export interface MatchedLine { ref: string; qty: number; block: string; line: QuantifiedLine }
export interface UnmatchedCandidate { reason: string; line: QuantifiedLine }
export interface OperatorQuestion { question: string; context: string }
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test breaker-map`
Expected: PASS (5 cases) — including that EVERY ref in the map resolves in the canonical catalog.

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/catalog packages/estimator-takeoff/src/buckets
git add packages/estimator-takeoff/test/breaker-map.test.ts
git commit -m "feat(estimator-takeoff): breaker catalog mapping validated against canonical refs"
```

---

## Task 6: Pipeline + emit via buildNativeEnvelope (golden end-to-end)

**Files:**
- Create: `packages/estimator-takeoff/src/emit/emit.ts`
- Modify: `packages/estimator-takeoff/src/index.ts` (export the public surface)
- Test: `packages/estimator-takeoff/test/emit.test.ts`

**Interfaces:**
- Consumes: everything above + `buildNativeEnvelope`, `NativeEnvelopeInput` (`@apex/estimator-core`).
- Produces: `runTakeoff(artifact: ExtractionArtifact): TakeoffResult`; `emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }): { envelope; findings }`.

- [ ] **Step 1: Write the failing test**

```ts
// test/emit.test.ts
import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('runTakeoff + emitEnvelope (golden)', () => {
  const result = runTakeoff(fixture as ExtractionArtifact)

  it('matches the three breakers and de-dups ACC-1-09-FB to qty 1', () => {
    const acc = result.matchedLines.find((m) => m.line.signature.tag === 'ACC-1-09-FB')!
    expect(acc.qty).toBe(1)                         // counted once despite the power-plan duplicate
    expect(result.matchedLines.map((m) => m.ref)).toContain('Circuit Breaker LV - Draw-Out (LSIG)')
  })

  it('emits a valid envelope with no error-severity findings', () => {
    const { envelope, findings } = emitEnvelope(result, { projectNumber: 'STACK-PHX02A' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])  // estimator-core's own native test asserts no ERROR findings (not zero findings)
    expect(envelope.scopes.length).toBeGreaterThan(0)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test emit`
Expected: FAIL — `runTakeoff` / `emitEnvelope` not defined.

- [ ] **Step 3: Write the implementation**

```ts
// src/emit/emit.ts
import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact } from '../extraction/types'
import { normalizeApparatus } from '../signature/normalize'
import { quantify } from '../quantify/quantify'
import { matchBreaker } from '../catalog/breaker-map'
import type { MatchedLine, TakeoffResult, UnmatchedCandidate } from '../buckets/types'

export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const sigs = artifact.apparatus.map(normalizeApparatus).filter((s): s is NonNullable<typeof s> => s !== null)
  const { lines, locationOnly } = quantify(sigs)

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) matchedLines.push({ ref, qty: line.qty, block: line.signature.source.sheet, line })
    else unmatchedCandidates.push({ reason: `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('')}`, line })
  }
  const operatorQuestions = locationOnly.map((s) => ({
    question: `Device ${s.tag ?? '(untagged)'} appears only on a non-authoritative sheet — include it?`,
    context: `${s.source.sheet} (${s.source.evidence})`,
  }))
  return { matchedLines, unmatchedCandidates, operatorQuestions }
}

export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  // group matched lines into scopes by block; emit ONLY catalog {ref, qty} lines (fail-closed)
  const byScope = new Map<string, NativeEnvelopeInput['scopes'][number]>()
  for (const m of result.matchedLines) {
    const name = `Block ${m.block}`
    const scope = byScope.get(name) ?? { name, netaStandard: 'ATS' as NetaStandard, lines: [] }
    scope.lines.push({ ref: m.ref, qty: m.qty, designation: m.line.signature.tag, notes: `from ${m.line.sources[0]?.sheet}` })
    byScope.set(name, scope)
  }
  const input: NativeEnvelopeInput = { projectNumber: opts.projectNumber, scopes: [...byScope.values()] }
  return buildNativeEnvelope(input)
}
```

```ts
// src/index.ts
export { runTakeoff, emitEnvelope } from './emit/emit'
export type { ExtractedApparatus, ExtractionArtifact } from './extraction/types'
export type { ApparatusSignature, VoltageClass } from './signature/types'
export type { TakeoffResult, MatchedLine, UnmatchedCandidate, OperatorQuestion } from './buckets/types'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test`
Expected: PASS (all suites). The golden test proves drawings JSON → de-duped inventory → valid priced envelope with zero findings.

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/emit packages/estimator-takeoff/src/index.ts packages/estimator-takeoff/test/emit.test.ts
git commit -m "feat(estimator-takeoff): full breaker pipeline emitting via buildNativeEnvelope (golden e2e)"
```

---

## Out of scope — Plan 2 (the human + tuning layer)

These ride on this engine and get their own plan once it lands:
- **drawing-nav export command** (Windows): add a `drawing-nav extract <pdf>` that emits the `ExtractionArtifact` JSON this engine consumes (today the fixture is hand-built).
- **Gate 1 presentation:** render the inventory table + `unmatchedCandidates` + `operatorQuestions` + `find --render` crop-on-dispute; freeze `inventory.json`.
- **Spec-parser + Gate 2:** parse the project testing spec → `ScopeProfile` overrides (in-scope, ATS/MTS) with clause citations; resolve `default ⊕ spec ⊕ human`.
- **ScopeProfile application:** in-scope / out-of-scope filtering before emit (default profile = all breaker classes in-scope, ATS).
- **Pattern flags** (advisory) attached to lines and carried into `notes`.
- **SKILL.md** orchestration tying drawing-nav (Windows) ↔ this engine (Olares) ↔ the two gates.
- **Codex implementation constraints to honor in Plan 2:** integer quantities; if any `custom_equipment` path is ever added, `provisional_token` must be unique across lines (V1 avoids this entirely by emitting catalog-only).

## Self-review

- **Spec coverage:** normalize/voltage (Tasks 2-3) ✓ · quantify de-dup rule (Task 4) ✓ · catalog match + 3 buckets + fail-closed (Tasks 5-6) ✓ · emit via `buildNativeEnvelope` (Task 6) ✓ · scope-per-block (Task 6) ✓. Gates, spec-parser, patterns, voltage-from-drawing extraction → Plan 2 (explicitly deferred).
- **Placeholders:** none — every step has runnable code/commands. (Step 0a is a real verification action, not a placeholder.)
- **Type consistency:** `ApparatusSignature`, `QuantifiedLine`, `MatchedLine`, `TakeoffResult`, `runTakeoff`, `emitEnvelope`, `matchBreaker`, `classifyVoltage`, `normalizeApparatus`, `quantify` are defined once and referenced with the same signatures across Tasks 1-6. `NativeEnvelopeInput`/`buildNativeEnvelope`/`NetaStandard` are imported from `@apex/estimator-core` verbatim.
