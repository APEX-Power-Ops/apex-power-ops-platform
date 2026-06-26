# Gate-1 Voltage UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A browser-only, ephemeral Gate-1 page in `operations-web` that loads a drawing-nav artifact, lets a PM resolve `missing_voltage` questions by asserting voltage per tag, shows the full reconciliation (clean vs partial_preview), and exports the runner's durable JSON shapes with deterministic content hashes — no backend, no persistence.

**Architecture:** The estimator-takeoff TS engine runs **client-side** (operations-web is a pure browser shell; `/estimator` already runs estimator-core in the browser). The page composes `parseArtifact` → `runTakeoff` → `reconcile` (so `TakeoffResult.findings` is visible) and `emitEnvelope` (clean-only) entirely in the browser. Pure helpers live in `lib/gate1*.ts` (unit-tested, no fetch); the page is a `'use client'` component tested by a Playwright smoke.

**Tech Stack:** Next.js 16 App Router (client components only), React 19, `@apex/estimator-takeoff` (workspace), `crypto.subtle` (SHA-256), Playwright + Vitest.

## Global Constraints

- **Spec is the contract:** `docs/superpowers/specs/2026-06-26-estimator-takeoff-gate1-voltage-ui-design.md` (Rev 2). The four Rev-2 corrections are binding.
- **Ephemeral, browser-only:** NO `app/api` route, NO control-plane route, NO DB, NO migration, NO object storage. Artifact lives in React state; output is downloaded.
- **THE SEAM (operator-mandated, load-bearing):** the interactive surface uses the thin helper `evaluate` = `runTakeoff` + `reconcile`, built and unit-tested BEFORE any UI. The page MUST NOT import `runFromArtifact` (its `RunResult.findings` drops the voltage-assertion findings — every non-emit return path sets `findings: []`). `runFromArtifact` is reserved for CLI parity only. `emitEnvelope(result, {projectNumber})` is called only when `isClean(result) && result.matchedLines.length > 0`.
- **Untagged rows are read-only**, never assertable (engine `VoltageAssertion` is tag-keyed; no `inputIndex` path).
- **Assertions merge by tag (replace, last-write-wins)** — never blind-append; duplicate tags are a hard engine error.
- **UI shows ALL open items** (two panels) — `isClean` blocks on error findings, any unresolved disposition, and any operator question.
- **Deterministic canonical hash:** `sha256(canonicalJson(value))` where `canonicalJson` recursively sorts keys + emits compact JSON; reproducible from the parsed object (survives a future JSONB round-trip).
- **Operator name/initials = evidence metadata, explicitly `authoritative: false`.** Not auth.
- **ASCII-only** user-facing strings. Identity actor from `process.env.NEXT_PUBLIC_OPS_DEV_PM_ID` (the existing dev pattern).
- **Lane:** `estimator-takeoff/gate1-voltage-ui` (host worktree `apex-gate1`); build/test on the Olares host (pnpm, Node 20). Merge OPERATOR-GATED.

## File Structure

- `apps/operations-web/package.json` — add `@apex/estimator-takeoff` dep (modify).
- `apps/operations-web/next.config.ts` — add the package to `transpilePackages` (modify).
- `apps/operations-web/lib/gate1.ts` — `evaluate`, `resolvableVoltageGroups`, `otherOpenItems`, `buildAssertions`, `mergeAssertionsByTag`, `buildExport`, types, `Gate1Error` (create).
- `apps/operations-web/lib/gate1-canonical.ts` — `canonicalJson`, `sha256Hex` (create).
- `apps/operations-web/app/takeoff/page.tsx` — the page (create).
- `apps/operations-web/app/takeoff/loading.tsx` — skeleton (create).
- `apps/operations-web/tests/gate1.unit.spec.ts` — helper tests (create).
- `apps/operations-web/tests/gate1-canonical.unit.spec.ts` — canonical/hash tests (create).
- `apps/operations-web/tests/browser-shell.takeoff.smoke.spec.ts` — Playwright smoke (create).
- `apps/operations-web/scripts/smoke-hosted-routes.mjs` — add `/takeoff` route entry (modify).
- `apps/operations-web/app/pm-review/page.tsx` (or the existing top-level nav) — add a `/takeoff` link (modify).

## Pre-Flight Plan Review (run before Task 1)

Scan for these before dispatching: (a) **the seam guard** — confirm `evaluate` (Task 2) is built and tested before the page (Task 6), and that no task imports `runFromArtifact` into the page; (b) no task asserts a hardcoded `bid_cents` beyond `> 0`; (c) untagged rows never appear in the resolvable panel. If clean, proceed.

---

### Task 1: Scaffold — wire the engine into operations-web

**Files:**
- Modify: `apps/operations-web/package.json`
- Modify: `apps/operations-web/next.config.ts`
- Create: `apps/operations-web/tests/gate1-engine.unit.spec.ts`

**Interfaces:**
- Consumes: `@apex/estimator-takeoff` exports `parseArtifact`, `runTakeoff` (verified in `src/index.ts`).
- Produces: a proven browser-safe import path for the engine.

- [ ] **Step 1: Write the failing test** (`tests/gate1-engine.unit.spec.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { parseArtifact, runTakeoff } from '@apex/estimator-takeoff'

describe('estimator-takeoff engine is importable + browser-safe', () => {
  it('parses a minimal artifact and runs without Node-only deps', () => {
    const artifact = parseArtifact({
      pdf: 't.pdf',
      apparatus: [{ raw: 'MSB 800AF/800AT', tag: 'MSB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line' }],
      voltageAssertions: [],
    })
    const result = runTakeoff(artifact)
    expect(result.dispositions).toHaveLength(1)
  })
})
```

- [ ] **Step 2: Run it; expect FAIL** (module not found — dep not added yet)

Run: `pnpm --filter operations-web exec vitest run tests/gate1-engine.unit.spec.ts`
Expected: FAIL — cannot resolve `@apex/estimator-takeoff`.

- [ ] **Step 3: Add the dependency + transpile**

In `apps/operations-web/package.json` `dependencies`, add (alongside `@apex/estimator-core`):
```json
"@apex/estimator-takeoff": "workspace:*",
```
In `apps/operations-web/next.config.ts`, extend `transpilePackages`:
```ts
transpilePackages: ['@apex/estimator-core', '@apex/estimator-takeoff'],
```
Then install: `pnpm install` (from repo root).

- [ ] **Step 4: Run it; expect PASS**

Run: `pnpm --filter operations-web exec vitest run tests/gate1-engine.unit.spec.ts`
Expected: PASS (1 disposition).

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/package.json apps/operations-web/next.config.ts apps/operations-web/tests/gate1-engine.unit.spec.ts pnpm-lock.yaml
git commit -m "feat(takeoff-ui): wire @apex/estimator-takeoff into operations-web (browser-safe)"
```

---

### Task 2: The thin helper — evaluate (runTakeoff + reconcile) + open-item helpers (`lib/gate1.ts` part 1)

> **This is THE SEAM. It is built and tested BEFORE any UI so the page cannot drift back to `runFromArtifact` and lose `TakeoffResult.findings`.**

**Files:**
- Create: `apps/operations-web/lib/gate1.ts`
- Create: `apps/operations-web/tests/gate1.unit.spec.ts`

**Interfaces:**
- Consumes: `runTakeoff`, `reconcile` and types `TakeoffResult`, `ReconciliationReport`, `ExtractionArtifact` from `@apex/estimator-takeoff`.
- Produces:
  - `evaluate(artifact: ExtractionArtifact): { result: TakeoffResult; report: ReconciliationReport }`
  - `resolvableVoltageGroups(result, artifact): SheetGroup[]` where `SheetGroup = { sheet: string; blocks: { block: string; tags: TagRow[] }[] }` and `TagRow = { tag: string; inputIndexes: number[]; raw: string; evidence: string; reason: string }`
  - `otherOpenItems(result, artifact): OpenItem[]` where `OpenItem = { kind: 'untagged_missing_voltage' | 'unmatched_candidate' | 'question'; label: string; sheet?: string; reasonCode?: string }`

- [ ] **Step 1: Write the failing tests** (inline synthetic artifact: one tagged missing-voltage, one untagged missing-voltage)

```ts
import { describe, it, expect } from 'vitest'
import { parseArtifact } from '@apex/estimator-takeoff'
import { evaluate, resolvableVoltageGroups, otherOpenItems } from '../lib/gate1'

const ARTIFACT = parseArtifact({
  pdf: 't.pdf',
  apparatus: [
    { raw: 'FB-1 400AF/400AT', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' },
    { raw: 'UNLABELED 225AF', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' },
  ],
  voltageAssertions: [],
})

describe('evaluate (the thin helper = runTakeoff + reconcile)', () => {
  it('returns both result and report', () => {
    const { result, report } = evaluate(ARTIFACT)
    expect(result.dispositions.length).toBe(2)
    expect(report.status).toBe('partial_preview')
  })
})

describe('resolvableVoltageGroups', () => {
  it('includes the TAGGED missing-voltage row grouped by sheet/block/tag', () => {
    const { result } = evaluate(ARTIFACT)
    const tags = resolvableVoltageGroups(result, ARTIFACT).flatMap((g) => g.blocks.flatMap((b) => b.tags.map((t) => t.tag)))
    expect(tags).toContain('FB-1')
  })
  it('EXCLUDES untagged rows (engine is tag-keyed)', () => {
    const { result } = evaluate(ARTIFACT)
    const raws = resolvableVoltageGroups(result, ARTIFACT).flatMap((g) => g.blocks.flatMap((b) => b.tags.map((t) => t.raw)))
    expect(raws).not.toContain('UNLABELED 225AF')
  })
})

describe('otherOpenItems', () => {
  it('includes the untagged missing-voltage row as read-only', () => {
    const { result } = evaluate(ARTIFACT)
    expect(otherOpenItems(result, ARTIFACT).some((i) => i.kind === 'untagged_missing_voltage')).toBe(true)
  })
})
```

> Implementer note: confirm against the engine that a tagged sub-800AF feeder with no voltage yields a `missing_voltage` disposition with `status: 'question'`. If the synthetic rows produce a different `reasonCode`, adjust the fixture (e.g. give FB-1 a clearly LV-eligible frame) so the test exercises a real `missing_voltage` row — do NOT weaken the assertion.

- [ ] **Step 2: Run; expect FAIL** (module missing)

Run: `pnpm --filter operations-web exec vitest run tests/gate1.unit.spec.ts`

- [ ] **Step 3: Implement** `lib/gate1.ts` part 1

```ts
// apps/operations-web/lib/gate1.ts
import {
  runTakeoff, reconcile,
  type ExtractionArtifact, type TakeoffResult, type ReconciliationReport,
} from '@apex/estimator-takeoff'

export class Gate1Error extends Error {
  constructor(message: string, readonly path?: string) { super(message); this.name = 'Gate1Error' }
}

export interface TagRow { tag: string; inputIndexes: number[]; raw: string; evidence: string; reason: string }
export interface SheetGroup { sheet: string; blocks: { block: string; tags: TagRow[] }[] }
export type OpenItemKind = 'untagged_missing_voltage' | 'unmatched_candidate' | 'question'
export interface OpenItem { kind: OpenItemKind; label: string; sheet?: string; reasonCode?: string }

// THE SEAM: runTakeoff + reconcile, returning BOTH so the UI can read TakeoffResult.findings.
// Never use runFromArtifact for the interactive surface — it drops voltage findings.
export function evaluate(artifact: ExtractionArtifact): { result: TakeoffResult; report: ReconciliationReport } {
  const result = runTakeoff(artifact)
  const report = reconcile(artifact, result)
  return { result, report }
}

export function resolvableVoltageGroups(result: TakeoffResult, artifact: ExtractionArtifact): SheetGroup[] {
  const sheets = new Map<string, Map<string, Map<string, TagRow>>>()
  for (const d of result.dispositions) {
    if (d.reasonCode !== 'missing_voltage' || !d.tag) continue       // tagged only
    const row = artifact.apparatus[d.inputIndex]
    const block = row?.block ?? '(no block)'
    const byBlock = sheets.get(d.sheet) ?? sheets.set(d.sheet, new Map()).get(d.sheet)!
    const byTag = byBlock.get(block) ?? byBlock.set(block, new Map()).get(block)!
    const existing = byTag.get(d.tag)
    if (existing) existing.inputIndexes.push(d.inputIndex)
    else byTag.set(d.tag, { tag: d.tag, inputIndexes: [d.inputIndex], raw: row?.raw ?? '', evidence: d.evidence, reason: d.reason })
  }
  return [...sheets.entries()].map(([sheet, byBlock]) => ({
    sheet,
    blocks: [...byBlock.entries()].map(([block, byTag]) => ({ block, tags: [...byTag.values()] })),
  }))
}

export function otherOpenItems(result: TakeoffResult, artifact: ExtractionArtifact): OpenItem[] {
  const items: OpenItem[] = []
  for (const d of result.dispositions) {
    if (d.status !== 'question' && d.status !== 'unmatched') continue
    if (d.reasonCode === 'missing_voltage' && d.tag) continue        // resolvable elsewhere
    const row = artifact.apparatus[d.inputIndex]
    if (d.reasonCode === 'missing_voltage') {
      items.push({ kind: 'untagged_missing_voltage', label: row?.raw ?? `row ${d.inputIndex}`, sheet: d.sheet, reasonCode: d.reasonCode })
    } else if (d.status === 'unmatched') {
      items.push({ kind: 'unmatched_candidate', label: `${d.tag ?? row?.raw ?? `row ${d.inputIndex}`}`, sheet: d.sheet, reasonCode: d.reasonCode })
    } else {
      items.push({ kind: 'question', label: `${d.tag ?? row?.raw ?? `row ${d.inputIndex}`}: ${d.reason}`, sheet: d.sheet, reasonCode: d.reasonCode })
    }
  }
  for (const q of result.operatorQuestions) {
    if (q.inputIndex === undefined) items.push({ kind: 'question', label: q.question })  // profile warnings carry no inputIndex
  }
  return items
}
```

- [ ] **Step 4: Run; expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/lib/gate1.ts apps/operations-web/tests/gate1.unit.spec.ts
git commit -m "feat(takeoff-ui): thin evaluate helper (runTakeoff+reconcile) + two-panel open-item helpers"
```

---

### Task 3: Canonical serialization + SHA-256 (`lib/gate1-canonical.ts`)

**Files:**
- Create: `apps/operations-web/lib/gate1-canonical.ts`
- Create: `apps/operations-web/tests/gate1-canonical.unit.spec.ts`

**Interfaces:**
- Produces: `canonicalJson(value: unknown): string`, `sha256Hex(text: string): Promise<string>`.

- [ ] **Step 1: Write the failing tests**

```ts
import { describe, it, expect } from 'vitest'
import { canonicalJson, sha256Hex } from '../lib/gate1-canonical'

describe('canonicalJson', () => {
  it('is key-order independent', () => {
    expect(canonicalJson({ b: 1, a: 2 })).toBe(canonicalJson({ a: 2, b: 1 }))
  })
  it('sorts nested object keys and preserves array order', () => {
    expect(canonicalJson({ z: [3, { y: 1, x: 2 }], a: 1 })).toBe('{"a":1,"z":[3,{"x":2,"y":1}]}')
  })
  it('preserves number and string fidelity', () => {
    expect(canonicalJson({ n: 480, s: 'MSB-1' })).toBe('{"n":480,"s":"MSB-1"}')
  })
})

describe('sha256Hex', () => {
  it('is reproducible and 64 hex chars', async () => {
    const a = await sha256Hex('{"a":1}')
    expect(a).toBe(await sha256Hex('{"a":1}'))
    expect(a).toMatch(/^[0-9a-f]{64}$/)
  })
  it('matches a known vector', async () => {
    expect(await sha256Hex('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
  })
})
```

- [ ] **Step 2: Run; expect FAIL** (module missing)

Run: `pnpm --filter operations-web exec vitest run tests/gate1-canonical.unit.spec.ts`

- [ ] **Step 3: Implement**

```ts
// apps/operations-web/lib/gate1-canonical.ts
// Deterministic, reproducible-from-object JSON + SHA-256. The hash basis is a canonical
// serialization (sorted keys, compact) so it survives a future JSONB round-trip — distinct
// from drawing-nav's raw-byte drift hash. See the Gate-1 spec, "Determinism & hashing".

export function canonicalJson(value: unknown): string {
  return JSON.stringify(sortDeep(value))
}

function sortDeep(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortDeep)
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const k of Object.keys(value as Record<string, unknown>).sort()) {
      out[k] = sortDeep((value as Record<string, unknown>)[k])
    }
    return out
  }
  return value
}

export async function sha256Hex(text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
```

- [ ] **Step 4: Run; expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/lib/gate1-canonical.ts apps/operations-web/tests/gate1-canonical.unit.spec.ts
git commit -m "feat(takeoff-ui): canonical JSON + SHA-256 (deterministic, JSONB-stable)"
```

---

### Task 4: Assertions — build + merge-by-tag (`lib/gate1.ts` part 2)

**Files:**
- Modify: `apps/operations-web/lib/gate1.ts`
- Modify: `apps/operations-web/tests/gate1.unit.spec.ts`

**Interfaces:**
- Consumes: type `VoltageAssertion` from `@apex/estimator-takeoff`.
- Produces:
  - `buildAssertions(entries: { tag: string; voltageV: number }[], actor: string): VoltageAssertion[]`
  - `mergeAssertionsByTag(existing: VoltageAssertion[] | undefined, gate1: VoltageAssertion[]): VoltageAssertion[]`

- [ ] **Step 1: Write the failing tests** (the adversarial case: a CLI assertion already present for a tag the operator re-asserts)

```ts
import { buildAssertions, mergeAssertionsByTag } from '../lib/gate1'

describe('buildAssertions', () => {
  it('stamps source gate1 + actor, one tag per entry', () => {
    expect(buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
      .toEqual([{ voltageV: 480, tags: ['FB-1'], source: 'gate1', actor: 'JLS' }])
  })
})

describe('mergeAssertionsByTag', () => {
  it('REPLACES a same-tag existing/CLI assertion (no duplicate-tag)', () => {
    const existing = [{ voltageV: 208, tags: ['FB-1'], source: 'cli' as const }]
    const merged = mergeAssertionsByTag(existing, buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
    const fb1 = merged.filter((m) => m.tags.includes('FB-1'))
    expect(fb1).toHaveLength(1)
    expect(fb1[0].voltageV).toBe(480)
    expect(fb1[0].source).toBe('gate1')
  })
  it('keeps unrelated existing tags', () => {
    const merged = mergeAssertionsByTag([{ voltageV: 208, tags: ['OTHER'], source: 'cli' as const }],
      buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
    expect(merged.some((m) => m.tags.includes('OTHER') && m.voltageV === 208)).toBe(true)
    expect(merged.some((m) => m.tags.includes('FB-1') && m.voltageV === 480)).toBe(true)
  })
})
```

- [ ] **Step 2: Run; expect FAIL**

- [ ] **Step 3: Implement** (append to `lib/gate1.ts`; extend the import to add `VoltageAssertion`)

```ts
import { /* existing + */ type VoltageAssertion } from '@apex/estimator-takeoff'

export function buildAssertions(entries: { tag: string; voltageV: number }[], actor: string): VoltageAssertion[] {
  return entries.map((e) => ({ voltageV: e.voltageV, tags: [e.tag], source: 'gate1' as const, actor }))
}

// Replace-by-tag (last-write-wins). Gate-1 entries override any existing same-tag assertion
// (CLI or prior edit). Guarantees <= 1 assertion per tag -> never trips the engine's hard
// duplicate-tag error. Each output assertion carries exactly one tag.
export function mergeAssertionsByTag(existing: VoltageAssertion[] | undefined, gate1: VoltageAssertion[]): VoltageAssertion[] {
  const byTag = new Map<string, VoltageAssertion>()
  for (const a of existing ?? []) for (const tag of a.tags) byTag.set(tag, { ...a, tags: [tag] })
  for (const a of gate1) for (const tag of a.tags) byTag.set(tag, { ...a, tags: [tag] })   // gate1 overrides
  return [...byTag.values()]
}
```

- [ ] **Step 4: Run; expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/lib/gate1.ts apps/operations-web/tests/gate1.unit.spec.ts
git commit -m "feat(takeoff-ui): build + merge-by-tag assertions (replace, no duplicate-tag)"
```

---

### Task 5: Export builder (`lib/gate1.ts` part 3)

**Files:**
- Modify: `apps/operations-web/lib/gate1.ts`
- Modify: `apps/operations-web/tests/gate1.unit.spec.ts`

**Interfaces:**
- Consumes: `isClean`, `emitEnvelope` from `@apex/estimator-takeoff`; `canonicalJson`, `sha256Hex` from `./gate1-canonical` (Task 3).
- Produces: `buildExport(input): Promise<Gate1Export>` where
  `input = { artifact: ExtractionArtifact; result: TakeoffResult; report: ReconciliationReport; projectCtx: { projectNumber: string; packageName?: string; operatorName: string }; nowIso: string }`
  and `Gate1Export = { combined: Record<string, unknown>; runnerArtifact: ExtractionArtifact }`.

- [ ] **Step 1: Write the failing tests**

```ts
import { evaluate, buildExport } from '../lib/gate1'
import { parseArtifact } from '@apex/estimator-takeoff'

it('omits envelope and labels partial_preview when not clean', async () => {
  const art = parseArtifact({ pdf: 't.pdf', apparatus: [
    { raw: 'FB-1 400AF/400AT', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0,0,1,1], evidence: 'one-line' }], voltageAssertions: [] })
  const { result, report } = evaluate(art)
  const { combined } = await buildExport({ artifact: art, result, report,
    projectCtx: { projectNumber: 'P1', operatorName: 'JLS' }, nowIso: '2026-06-26T00:00:00Z' })
  expect((combined as any).manifest.status).toBe('partial_preview')
  expect((combined as any).envelope).toBeUndefined()
  expect((combined as any).manifest.operatorEvidence.authoritative).toBe(false)
  expect((combined as any).manifest.artifactContentHash).toMatch(/^[0-9a-f]{64}$/)
})
```

> Implementer note: also add a CLEAN-path test using a real matchable main with `voltageAssertions` injected so `isClean` holds and `emitEnvelope` succeeds (assert `manifest.status === 'clean'` and `envelope.totals.bid_cents > 0`). Build it from the package's E01-11 fixture or a minimal ≥800AF draw-out main + a 480 assertion; do not assert a hardcoded bid value beyond `> 0`.

- [ ] **Step 2: Run; expect FAIL**

- [ ] **Step 3: Implement** (append to `lib/gate1.ts`)

```ts
import { /* + */ isClean, emitEnvelope } from '@apex/estimator-takeoff'
import { canonicalJson, sha256Hex } from './gate1-canonical'

export interface Gate1Export { combined: Record<string, unknown>; runnerArtifact: ExtractionArtifact }

export async function buildExport(input: {
  artifact: ExtractionArtifact; result: TakeoffResult; report: ReconciliationReport
  projectCtx: { projectNumber: string; packageName?: string; operatorName: string }; nowIso: string
}): Promise<Gate1Export> {
  const { artifact, result, report, projectCtx, nowIso } = input
  const clean = isClean(result) && result.matchedLines.length > 0
  const envelope = clean ? emitEnvelope(result, { projectNumber: projectCtx.projectNumber }).envelope : undefined
  const artifactContentHash = await sha256Hex(canonicalJson(artifact))
  const reportContentHash = await sha256Hex(canonicalJson(report))
  const manifest = {
    projectNumber: projectCtx.projectNumber,
    packageName: projectCtx.packageName ?? null,
    sheet: artifact.apparatus[0]?.sheet ?? null,
    pdf: artifact.pdf,
    status: report.status,
    apparatusCount: artifact.apparatus.length,
    unresolvedRows: report.counts.unresolved_rows,
    gate1AssertionTags: (artifact.voltageAssertions ?? []).flatMap((a) => a.tags),
    operatorEvidence: { name: projectCtx.operatorName, assertedAtClient: nowIso, authoritative: false },
    artifactContentHash, reportContentHash,
  }
  const combined: Record<string, unknown> = { schemaVersion: 1, manifest, artifact, report }
  if (envelope) combined.envelope = envelope
  return { combined, runnerArtifact: artifact }
}
```

- [ ] **Step 4: Run; expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/lib/gate1.ts apps/operations-web/tests/gate1.unit.spec.ts
git commit -m "feat(takeoff-ui): export builder (combined JSON + hashes; envelope clean-only)"
```

---

### Task 6: The page + loading skeleton (`app/takeoff/`)

**Files:**
- Create: `apps/operations-web/app/takeoff/page.tsx`
- Create: `apps/operations-web/app/takeoff/loading.tsx`

**Interfaces:**
- Consumes: all of `lib/gate1.ts` + `parseArtifact`/`ArtifactContractError`. **MUST NOT import `runFromArtifact`** (seam guard — verify in review). `mergeAssertionsByTag` is applied to a **cloned** artifact before `evaluate`.
- Produces: the `/takeoff` route. (Behavior verified by the Task 7 smoke.)

- [ ] **Step 1: Implement `loading.tsx`** (mirror `app/pm-review/loading.tsx`)

```tsx
export default function Loading() {
  return <main className="shell-page"><div className="hero-card"><p className="lede">Loading takeoff review...</p></div></main>
}
```

- [ ] **Step 2: Implement `page.tsx`** — `'use client'`. Structure (authored here; verified by the smoke, not transcribed line-for-line):
  - **Imports from `lib/gate1` only** for engine work (`evaluate`, `resolvableVoltageGroups`, `otherOpenItems`, `buildAssertions`, `mergeAssertionsByTag`, `buildExport`, `Gate1Error`) + `parseArtifact`/`ArtifactContractError` for load. NEVER `runFromArtifact`.
  - State: `artifact` (pristine `ExtractionArtifact | null`), `evald` (`{result, report} | null`), `entries` (`Map<tag, voltageV>`), `projectCtx`, `err: string | null`, `busy`.
  - **Load:** `<input type="file" accept="application/json">` → `FileReader.readAsText` → `JSON.parse` → `parseArtifact`; on `ArtifactContractError` set a red `role="alert"` message `artifact contract error at <path>`; else `setArtifact(artifact); setEvald(evaluate(artifact))`, clear entries.
  - **Project-context form:** required `projectNumber`, optional `packageName`, `operatorName` (initials). Export buttons disabled until `projectNumber` non-empty.
  - **Panel 1 "Voltage questions I can resolve":** `resolvableVoltageGroups(evald.result, artifact)` grouped table; per tag a numeric `<input>` bound into `entries`. **Apply** button: `clone = structuredClone(artifact); clone.voltageAssertions = mergeAssertionsByTag(clone.voltageAssertions, buildAssertions([...entries].map(([tag, voltageV]) => ({ tag, voltageV })), projectCtx.operatorName)); setEvald(evaluate(clone)); setArtifact(clone)`.
  - **Panel 2 "Other open items blocking clean output":** `otherOpenItems(evald.result, artifact)` rendered read-only.
  - **Findings strip:** `evald.result.findings` — errors red; `voltage_assertion_conflict` amber, showing `detail.detectedV` vs `detail.assertedV`.
  - **Status banner:** `evald.report.status` — green "clean" or amber "partial_preview - N unresolved row(s); NOT a complete bid" (`counts.unresolved_rows`).
  - **Export:** two buttons — "Download export JSON" (`(await buildExport({ artifact, ...evald, projectCtx, nowIso: new Date().toISOString() })).combined`) and "Download runner artifact" (the bare `artifact`); each `JSON.stringify(x, null, 2)` → Blob download.
  - Styling: `shell-page` / `hero-card` / `status-pill` + the estimator-intake utility class strings. ASCII-only copy.
  - The page `<h1>` MUST read exactly `Gate-1 Voltage Takeoff Review` (the smoke + route marker).

- [ ] **Step 3: Typecheck**

Run: `pnpm --filter operations-web exec tsc --noEmit`
Expected: clean. (Also grep the page for `runFromArtifact` — must be absent.)

- [ ] **Step 4: Commit**

```bash
git add apps/operations-web/app/takeoff/page.tsx apps/operations-web/app/takeoff/loading.tsx
git commit -m "feat(takeoff-ui): /takeoff page - load, two panels, assert+reevaluate, export"
```

---

### Task 7: Browser smoke + route registry + nav link

**Files:**
- Create: `apps/operations-web/tests/browser-shell.takeoff.smoke.spec.ts`
- Modify: `apps/operations-web/scripts/smoke-hosted-routes.mjs`
- Modify: the top-level nav (`apps/operations-web/app/pm-review/page.tsx` link list, or the home nav)

**Interfaces:**
- Consumes: the committed E01-11 fixture `packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11.artifact.json` (read into the test, uploaded via the file input).

- [ ] **Step 1: Write the smoke** (mirror `tests/browser-shell.pm-recognition.smoke.spec.ts`; NO API mocks — ephemeral has none)

```ts
import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const FIXTURE = fileURLToPath(new URL(
  '../../../packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11.artifact.json', import.meta.url))

test('takeoff gate-1 loads, surfaces voltage worklist, reaches partial_preview', async ({ page }) => {
  await page.goto('/takeoff', { waitUntil: 'networkidle' })
  await expect(page.getByRole('heading', { name: /Gate-1 Voltage Takeoff Review/i })).toBeVisible()
  await page.setInputFiles('input[type=file]', FIXTURE)
  await expect(page.getByText(/Voltage questions I can resolve/i)).toBeVisible()
  await expect(page.getByText(/Other open items blocking clean output/i)).toBeVisible()
  await expect(page.getByText(/partial_preview/i)).toBeVisible()
})
```

- [ ] **Step 2: Run; expect PASS once the page renders the markers** (if it passes immediately, confirm it is exercising the real page — the fixture upload must drive the worklist, not a static string).

Run: `pnpm --filter operations-web exec playwright test tests/browser-shell.takeoff.smoke.spec.ts`

- [ ] **Step 3: Register the route + nav link**

In `apps/operations-web/scripts/smoke-hosted-routes.mjs` `routeChecks`, add:
```js
{ path: '/takeoff', marker: 'Gate-1 Voltage Takeoff Review' },
```
Add `<Link href="/takeoff">Gate-1 Voltage Takeoff</Link>` in the existing nav link list (match the surrounding pattern).

- [ ] **Step 4: Run the full operations-web check; expect PASS**

Run: `pnpm --filter operations-web exec tsc --noEmit && pnpm --filter operations-web exec vitest run && pnpm --filter operations-web exec playwright test tests/browser-shell.takeoff.smoke.spec.ts`

- [ ] **Step 5: Commit**

```bash
git add apps/operations-web/tests/browser-shell.takeoff.smoke.spec.ts apps/operations-web/scripts/smoke-hosted-routes.mjs apps/operations-web/app/pm-review/page.tsx
git commit -m "test(takeoff-ui): browser smoke + route registry + nav link"
```

---

## Self-Review (author checklist run against the spec)

1. **The seam (operator guard):** the thin helper `evaluate` (`runTakeoff`+`reconcile`) is **Task 2 — the first implementation task after scaffold, before ALL UI (Task 6)**. The page (Task 6) imports only `lib/gate1` + `parseArtifact`; it MUST NOT import `runFromArtifact` (Global Constraint + Task 6 Interfaces + a grep check in Task 6 Step 3 + the Pre-Flight guard). This prevents drift back to `RunResult.findings`.
2. **Spec coverage:** load+parse (T6), evaluate seam (T2), tagged worklist grouped sheet→block→tag (T2), untagged read-only (T2/T6), per-tag assert + merge-by-tag replace (T4/T6), re-evaluate on clone (T6), findings from result.findings (T6), clean vs partial_preview (T6), two panels (T2/T6), export combined+runner with hashes + envelope-clean-only + non-authoritative evidence (T5), determinism (T3), scaffold (T1), smoke+registry (T7).
3. **Placeholders:** none — lib code is complete; the page (T6) is specified field-by-field with the load-bearing logic inline, verified by the smoke.
4. **Type consistency:** `evaluate` returns `{result, report}` consumed by `resolvableVoltageGroups`/`otherOpenItems`/`buildExport`; `buildAssertions`→`mergeAssertionsByTag`→`clone.voltageAssertions`→`evaluate`; `VoltageAssertion`/`TakeoffResult`/`ReconciliationReport`/`ExtractionArtifact` names match `src/index.ts`.
5. **Scope:** ephemeral/browser-only; no backend/DB/migration; Model-2 persistence deferred.

## Out of scope (deferred)

Persistence (`ops.takeoff_runs` + control-plane routes), Gate-2 line review, apparatus-family expansion, multi-sheet composition, real auth.
