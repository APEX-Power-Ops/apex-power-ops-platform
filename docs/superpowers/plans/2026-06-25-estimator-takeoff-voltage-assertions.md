# Estimator-Takeoff Voltage Assertions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an operator assert breaker bus voltage per device tag; the TS engine validates and applies those assertions authoritatively (fail-closed on bad input), prices each device at its own asserted voltage, and records provenance — with a thin `--assert-voltage` CLI collector in drawing-nav producing the artifact block.

**Architecture:** A pure `applyVoltageAssertions` pass runs before `assessApparatus` in `runTakeoff`, returning engine-owned `ResolvedApparatus` wrappers (carrying non-forgeable `voltageBasis`) plus coded `TakeoffFinding[]`. `emitEnvelope` refuses on any `error`-severity finding. The slice spans two repos joined only by the `ExtractionArtifact` JSON seam: **Phase A** = TS engine (`apex-power-ops-platform`, vitest), the merge-gated deliverable executed first; **Phase B** = drawing-nav Python collector (separate repo, pytest), executed after Phase A merges.

**Tech Stack:** TypeScript + vitest (Phase A, `packages/estimator-takeoff`); Python + pytest (Phase B, `C:\Users\jjswe\Tools\drawing-nav`). Host worktree `/home/olares/code/apex/apex-takeoff-voltage` over mesh SSH for Phase A.

**Source spec:** `docs/superpowers/specs/2026-06-25-estimator-takeoff-voltage-assertions-design.md` (rev 2 @ `ab623880`).

## Global Constraints

- **Engine is sole validator/applier; Python is a thin collector** — the CLI performs no semantic validation (tag existence, conflicts, voltage sanity), only its own flag syntax.
- **Provenance is non-forgeable:** public `ExtractedApparatus` gains **no** `voltageBasis` field. Basis lives only on the engine-owned `ResolvedApparatus` wrapper, recomputed from scratch every run; `applyVoltageAssertions` never reads a basis off its input.
- **Voltage validation:** an assertion is valid iff `Number.isInteger(voltageV) && voltageV > 0`. Invalid → `error` finding + taint.
- **Severity policy:** `voltage_assertion_unknown_tag`, `voltage_assertion_duplicate_tag`, `voltage_assertion_invalid_voltage` = **`error`** (block). `voltage_assertion_conflict` = **`warning`** (operator wins, device prices, non-blocking audit).
- **`emitEnvelope` refuses on any `error`-severity `TakeoffResult.finding`**, independent of `matchedLines.length`.
- **Taint:** any tag with an `error`-severity assertion issue (invalid/duplicate) has its effective `busVoltageV` cleared to `undefined` (basis `none`) so it cannot price via a detected fallback.
- **`actor`/`note`/`source`/`at` are evidence-only** — the engine never branches on them. V1 CLI omits `at`.
- **New fields are required (always present):** `ApparatusSignature.voltageBasis`, `MatchedLine.voltageBasis`, `TakeoffResult.findings`.
- **Quantify grouping (load-bearing per-tag invariant):** `specKey` includes nominal `voltageV` **and** `voltageBasis`, so two devices that differ only in asserted voltage (480 vs 208, both LV) — or only in provenance (detected vs asserted) — never collapse into one priced line.
- **Malformed-shape fail-closed:** the engine is the authoritative JSON seam — a non-array `voltageAssertions`, or an assertion with missing / empty / non-array `tags`, produces a `voltage_assertion_invalid_shape` **error** finding, never a thrown exception.
- **VoltageBasis** = `'detected' | 'asserted' | 'none'`. `classifyVoltage` routing: LV `< 1000`, MV `1000–69000`, HV `> 69000`.
- **O1:** NO fabricated real `E01-11` 480/208 golden — mixed-voltage proof uses a **synthetic** fixture only.
- **O2:** the real `E01-11` golden asserts 480 V to a **named subset** `['MSB-P1-110-GB', 'ACC-1-09-FB', 'ACC-1-10-FB']` (MSB-P1-110-GB is the confirmed draw-out LSIG main); the test name makes the scope explicit; 208 V house tags are intentionally **not** asserted.
- **Merge to `main` is OPERATOR-GATED.** Phase A is dev-only on the lane until the operator approves the merge. Phase B lands in the drawing-nav repo separately.
- All Phase A git/test ops run on the host over `ssh olares-mesh`; commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`.

---

## File Structure

**Phase A — `packages/estimator-takeoff/` (TS engine):**

- `src/signature/voltage.ts` — *(modify)* add the `<= 0 → undefined` lower-bound guard (D8).
- `src/quantify/quantify.ts` — *(modify)* add `voltageV` + `voltageBasis` to `specKey` so per-tag voltage/provenance never collapse (Task A3b).
- `src/extraction/types.ts` — *(modify)* add `VoltageAssertion` + `ExtractionArtifact.voltageAssertions`. **No** `voltageBasis` on `ExtractedApparatus`.
- `src/signature/types.ts` — *(modify)* add `VoltageBasis` + `ApparatusSignature.voltageBasis`.
- `src/buckets/types.ts` — *(modify)* add `FindingSeverity`, `VoltageAssertionCode`, `TakeoffFinding`, `MatchedLine.voltageBasis`, `TakeoffResult.findings`.
- `src/signature/voltage-assertions.ts` — *(create)* `ResolvedApparatus` + `applyVoltageAssertions` (validation, taint, apply, conflict findings). One responsibility: turn raw assertions into resolved apparatus + findings.
- `src/signature/normalize.ts` — *(modify)* `assessApparatus(x, voltageBasis?)`; set `signature.voltageBasis`.
- `src/emit/emit.ts` — *(modify)* `runTakeoff` calls `applyVoltageAssertions` and threads `findings`; `MatchedLine.voltageBasis`; notes; `emitEnvelope` error-finding refusal.
- `src/index.ts` — *(modify)* export the new public symbols.
- `test/voltage.test.ts`, `test/normalize.test.ts`, `test/quantify.test.ts`, `test/breaker-map.test.ts`, `test/emit.test.ts`, `test/golden-e01-11.test.ts` — *(modify)*.
- `test/voltage-assertions.test.ts` — *(create)*.
- `test/fixtures/synthetic-mixed-voltage.json` — *(create)*.

**Phase B — `C:\Users\jjswe\Tools\drawing-nav/` (Python collector, separate repo):**

- `drawing_nav.py` — *(modify)* add `parse_voltage_assertions` helper; `--assert-voltage`/`--assert-actor`/`--assert-note` flags; call from `cmd_extract`.
- `tests/test_assert_voltage.py` — *(create)*.

---

# PHASE A — TS engine (execute first; merge-gated)

### Task A1: `classifyVoltage` lower-bound guard (D8 defense-in-depth)

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/voltage.ts`
- Test: `packages/estimator-takeoff/test/voltage.test.ts`

**Interfaces:**
- Produces: `classifyVoltage(voltageV: number | undefined): VoltageClass | undefined` — now returns `undefined` for `voltageV <= 0` (in addition to `undefined` input).

- [ ] **Step 1: Write the failing test** — append inside the existing `describe('classifyVoltage ...')` block in `test/voltage.test.ts`:

```ts
  it('returns undefined for impossible (non-positive) voltages', () => {
    expect(classifyVoltage(0)).toBeUndefined()
    expect(classifyVoltage(-1)).toBeUndefined()
    expect(classifyVoltage(-480)).toBeUndefined()
  })
```

- [ ] **Step 2: Run test to verify it fails**

Run (on host): `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage.test.ts'`
Expected: FAIL — `classifyVoltage(0)` returns `'LV'`, not `undefined`.

- [ ] **Step 3: Add the guard** in `src/signature/voltage.ts`:

```ts
export function classifyVoltage(voltageV: number | undefined): VoltageClass | undefined {
  if (voltageV === undefined) return undefined
  if (voltageV <= 0) return undefined          // impossible voltage — never classify (D8)
  if (voltageV < 1000) return 'LV'
  if (voltageV <= 69000) return 'MV'
  return 'HV'
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage.test.ts'`
Expected: PASS (all classifyVoltage cases green).

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/signature/voltage.ts packages/estimator-takeoff/test/voltage.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(estimator-takeoff): classifyVoltage rejects non-positive voltages (D8)"'
```

---

### Task A2: contract types + `applyVoltageAssertions` (validate / taint / apply / findings)

**Files:**
- Modify: `packages/estimator-takeoff/src/extraction/types.ts`
- Modify: `packages/estimator-takeoff/src/signature/types.ts`
- Modify: `packages/estimator-takeoff/src/buckets/types.ts`
- Create: `packages/estimator-takeoff/src/signature/voltage-assertions.ts`
- Modify: `packages/estimator-takeoff/src/index.ts`
- Test: `packages/estimator-takeoff/test/voltage-assertions.test.ts` (create)

**Interfaces:**
- Consumes: `ExtractedApparatus` (existing), `classifyVoltage` (not directly).
- Produces:
  - `VoltageAssertion { voltageV: number; tags: string[]; actor?: string; note?: string; source?: 'cli'|'gate1'; at?: string }`
  - `ExtractionArtifact.voltageAssertions?: VoltageAssertion[]`
  - `VoltageBasis = 'detected' | 'asserted' | 'none'`
  - `FindingSeverity = 'error' | 'warning'`
  - `VoltageAssertionCode = 'voltage_assertion_unknown_tag' | 'voltage_assertion_duplicate_tag' | 'voltage_assertion_conflict' | 'voltage_assertion_invalid_voltage' | 'voltage_assertion_invalid_shape'`
  - `TakeoffFinding { code: VoltageAssertionCode; severity: FindingSeverity; message: string; context: string; detail?: { tag?: string; detectedV?: number; assertedV?: number; actor?: string; source?: string } }`
  - `ResolvedApparatus { apparatus: ExtractedApparatus; voltageBasis: VoltageBasis }`
  - `applyVoltageAssertions(artifact: ExtractionArtifact): { resolved: ResolvedApparatus[]; findings: TakeoffFinding[] }`

- [ ] **Step 1: Add the types.** In `src/extraction/types.ts`, add `VoltageAssertion` and extend `ExtractionArtifact` (do NOT touch `ExtractedApparatus`):

```ts
export interface VoltageAssertion {
  voltageV: number          // engine requires Number.isInteger(voltageV) && voltageV > 0
  tags: string[]            // device tags this assertion covers (>= 1)
  actor?: string            // evidence-only; engine never branches on it
  note?: string             // evidence-only
  source?: 'cli' | 'gate1'  // evidence-only
  at?: string               // untrusted metadata; engine never trusts it for ordering/authority
}
```

Extend `ExtractionArtifact`:

```ts
export interface ExtractionArtifact {
  pdf: string
  extractedAt?: string
  profileWarnings?: string[]
  apparatus: ExtractedApparatus[]
  voltageAssertions?: VoltageAssertion[]
}
```

In `src/signature/types.ts`, add (above `ApparatusSignature`):

```ts
export type VoltageBasis = 'detected' | 'asserted' | 'none'
```

In `src/buckets/types.ts`, add:

```ts
export type FindingSeverity = 'error' | 'warning'

export type VoltageAssertionCode =
  | 'voltage_assertion_unknown_tag'
  | 'voltage_assertion_duplicate_tag'
  | 'voltage_assertion_conflict'
  | 'voltage_assertion_invalid_voltage'
  | 'voltage_assertion_invalid_shape'

export interface TakeoffFinding {
  code: VoltageAssertionCode
  severity: FindingSeverity
  message: string
  context: string
  detail?: { tag?: string; detectedV?: number; assertedV?: number; actor?: string; source?: string }
}
```

- [ ] **Step 2: Write the failing tests** — create `test/voltage-assertions.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { applyVoltageAssertions } from '../src/signature/voltage-assertions'
import type { ExtractionArtifact, ExtractedApparatus } from '../src/extraction/types'

const dev = (tag: string, busVoltageV?: number): ExtractedApparatus => ({
  raw: `${tag} 4000AF/4000AT LSIG`, tag, sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1],
  evidence: 'one-line', block: 'P1-110', busVoltageV,
})
const art = (apparatus: ExtractedApparatus[], voltageAssertions?: ExtractionArtifact['voltageAssertions']): ExtractionArtifact =>
  ({ pdf: 'x', apparatus, voltageAssertions })

describe('applyVoltageAssertions', () => {
  it('no assertions → passthrough with recomputed basis (back-compat)', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A', 480), dev('B')]))
    expect(findings).toEqual([])
    expect(resolved.map((r) => r.voltageBasis)).toEqual(['detected', 'none'])
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('applies an asserted voltage and labels basis asserted', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: ['A'], source: 'cli' }]))
    expect(findings).toEqual([])
    expect(resolved[0]!.voltageBasis).toBe('asserted')
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('unknown tag → error finding, no device touched', () => {
    const { findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: ['NOPE'], source: 'cli' }]))
    expect(findings).toHaveLength(1)
    expect(findings[0]!.code).toBe('voltage_assertion_unknown_tag')
    expect(findings[0]!.severity).toBe('error')
  })

  it('duplicate tag → error finding and the device is tainted (basis none, voltage cleared)', () => {
    const { resolved, findings } = applyVoltageAssertions(
      art([dev('A')], [{ voltageV: 480, tags: ['A'] }, { voltageV: 208, tags: ['A'] }]),
    )
    expect(findings.some((f) => f.code === 'voltage_assertion_duplicate_tag' && f.severity === 'error')).toBe(true)
    expect(resolved[0]!.voltageBasis).toBe('none')
    expect(resolved[0]!.apparatus.busVoltageV).toBeUndefined()
  })

  it('duplicate tag WITH a detected voltage is still tainted (no detected fallback)', () => {
    const { resolved } = applyVoltageAssertions(
      art([dev('A', 480)], [{ voltageV: 480, tags: ['A'] }, { voltageV: 480, tags: ['A'] }]),
    )
    expect(resolved[0]!.voltageBasis).toBe('none')              // NOT 'detected'
    expect(resolved[0]!.apparatus.busVoltageV).toBeUndefined()  // detected 480 cleared
  })

  it('invalid voltages (0, -1, 12.5, NaN) → error finding + taint', () => {
    for (const bad of [0, -1, 12.5, NaN]) {
      const { resolved, findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: bad, tags: ['A'] }]))
      expect(findings.some((f) => f.code === 'voltage_assertion_invalid_voltage' && f.severity === 'error')).toBe(true)
      expect(resolved[0]!.voltageBasis).toBe('none')
    }
  })

  it('conflict (detected != asserted) → warning, operator wins, device keeps asserted voltage', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A', 240)], [{ voltageV: 480, tags: ['A'], actor: 'jls' }]))
    const conflict = findings.find((f) => f.code === 'voltage_assertion_conflict')!
    expect(conflict.severity).toBe('warning')
    expect(conflict.detail).toMatchObject({ tag: 'A', detectedV: 240, assertedV: 480, actor: 'jls' })
    expect(resolved[0]!.voltageBasis).toBe('asserted')
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('agreeing detected + asserted → no conflict finding', () => {
    const { findings } = applyVoltageAssertions(art([dev('A', 480)], [{ voltageV: 480, tags: ['A'] }]))
    expect(findings).toEqual([])
  })

  it('per-tag: two tags asserted at different voltages each keep their own voltage', () => {
    const { resolved } = applyVoltageAssertions(
      art([dev('A'), dev('B')], [{ voltageV: 480, tags: ['A'] }, { voltageV: 208, tags: ['B'] }]),
    )
    expect(resolved.find((r) => r.apparatus.tag === 'A')!.apparatus.busVoltageV).toBe(480)
    expect(resolved.find((r) => r.apparatus.tag === 'B')!.apparatus.busVoltageV).toBe(208)
  })

  it('provenance is non-forgeable: a stray voltageBasis on the artifact JSON is ignored', () => {
    const sneaky = { ...dev('A', 480), voltageBasis: 'asserted' } as unknown as ExtractedApparatus
    const { resolved } = applyVoltageAssertions(art([sneaky]))     // NO real assertion
    expect(resolved[0]!.voltageBasis).toBe('detected')             // recomputed, never 'asserted'
  })

  it('non-array voltageAssertions → invalid_shape error, nothing applied (no throw)', () => {
    const bad = { pdf: 'x', apparatus: [dev('A', 480)], voltageAssertions: {} } as unknown as ExtractionArtifact
    const { resolved, findings } = applyVoltageAssertions(bad)
    expect(findings.some((f) => f.code === 'voltage_assertion_invalid_shape' && f.severity === 'error')).toBe(true)
    expect(resolved[0]!.voltageBasis).toBe('detected')            // device untouched
  })

  it('assertion missing tags → invalid_shape error', () => {
    const bad = { pdf: 'x', apparatus: [dev('A')], voltageAssertions: [{ voltageV: 480 }] } as unknown as ExtractionArtifact
    expect(applyVoltageAssertions(bad).findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })

  it('assertion with non-array tags → invalid_shape error', () => {
    const bad = { pdf: 'x', apparatus: [dev('A')], voltageAssertions: [{ voltageV: 480, tags: 'A' }] } as unknown as ExtractionArtifact
    expect(applyVoltageAssertions(bad).findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })

  it('assertion with empty tags → invalid_shape error', () => {
    const { findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: [] }]))
    expect(findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })
})
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage-assertions.test.ts'`
Expected: FAIL — `Cannot find module '../src/signature/voltage-assertions'`.

- [ ] **Step 4: Implement** `src/signature/voltage-assertions.ts`:

```ts
import type { ExtractedApparatus, ExtractionArtifact } from '../extraction/types'
import type { VoltageBasis } from './types'
import type { TakeoffFinding } from '../buckets/types'

export interface ResolvedApparatus {
  apparatus: ExtractedApparatus     // effective busVoltageV already applied/cleared
  voltageBasis: VoltageBasis        // authoritative — recomputed here, never read from input
}

function detectedOrNone(busVoltageV: number | undefined): VoltageBasis {
  return busVoltageV !== undefined ? 'detected' : 'none'
}

interface ValidPair { tag: string; voltageV: number; actor?: string; source?: string }

export function applyVoltageAssertions(
  artifact: ExtractionArtifact,
): { resolved: ResolvedApparatus[]; findings: TakeoffFinding[] } {
  const rawAssertions: unknown = artifact.voltageAssertions
  const findings: TakeoffFinding[] = []
  const passthrough = (): ResolvedApparatus[] =>
    artifact.apparatus.map((apparatus) => ({ apparatus, voltageBasis: detectedOrNone(apparatus.busVoltageV) }))

  // Container shape guard — the engine is the authoritative JSON seam; never throw on malformed input.
  if (rawAssertions === undefined) return { resolved: passthrough(), findings }
  if (!Array.isArray(rawAssertions)) {
    findings.push({
      code: 'voltage_assertion_invalid_shape', severity: 'error',
      message: 'voltageAssertions must be an array — all assertions ignored.',
      context: 'voltageAssertions (not an array)',
    })
    return { resolved: passthrough(), findings }
  }
  if (rawAssertions.length === 0) return { resolved: passthrough(), findings }

  const tainted = new Set<string>()
  const validPairs: ValidPair[] = []

  // Per-assertion shape guard FIRST (missing/empty/non-array tags → coded error, never a throw),
  // then voltage validation; taint tags of invalid entries (Global: invalid → error + taint).
  for (const item of rawAssertions as unknown[]) {
    const a = item as { voltageV?: unknown; tags?: unknown; actor?: string; source?: string }
    if (a == null || typeof a !== 'object' || !Array.isArray(a.tags) || a.tags.length === 0) {
      findings.push({
        code: 'voltage_assertion_invalid_shape', severity: 'error',
        message: 'Malformed voltage assertion (missing, empty, or non-array tags) — rejected.',
        context: `assertion ${(JSON.stringify(a) ?? String(a)).slice(0, 80)}`,
      })
      continue
    }
    const tags = a.tags as string[]
    if (!(typeof a.voltageV === 'number' && Number.isInteger(a.voltageV) && a.voltageV > 0)) {
      for (const tag of tags) {
        tainted.add(tag)
        findings.push({
          code: 'voltage_assertion_invalid_voltage', severity: 'error',
          message: `Voltage assertion ${String(a.voltageV)} for ${tag} is not a positive integer — rejected.`,
          context: `${tag} (assert ${String(a.voltageV)}V)`,
          detail: { tag, assertedV: typeof a.voltageV === 'number' ? a.voltageV : undefined, actor: a.actor, source: a.source },
        })
      }
      continue
    }
    for (const tag of tags) validPairs.push({ tag, voltageV: a.voltageV, actor: a.actor, source: a.source })
  }

  // Group valid pairs by tag; duplicate tag → error + taint (Global: duplicate strict, even same voltage).
  const byTag = new Map<string, ValidPair[]>()
  for (const p of validPairs) (byTag.get(p.tag) ?? byTag.set(p.tag, []).get(p.tag)!).push(p)
  for (const [tag, ps] of byTag) {
    if (ps.length > 1) {
      tainted.add(tag)
      const volts = [...new Set(ps.map((p) => p.voltageV))].join('/')
      findings.push({
        code: 'voltage_assertion_duplicate_tag', severity: 'error',
        message: `Tag ${tag} is asserted ${ps.length} times (${volts}V) — ambiguous, rejected.`,
        context: `${tag} (${ps.length} assertions)`,
        detail: { tag },
      })
    }
  }

  // Unknown tag → error (no device to taint).
  const presentTags = new Set(artifact.apparatus.map((x) => x.tag).filter((t): t is string => !!t))
  for (const tag of byTag.keys()) {
    if (!presentTags.has(tag)) {
      findings.push({
        code: 'voltage_assertion_unknown_tag', severity: 'error',
        message: `Asserted tag ${tag} does not match any extracted device — check the tag/sheet.`,
        context: `${tag} (unknown)`,
        detail: { tag },
      })
    }
  }

  // Effective single-assertion map for non-tainted, present tags.
  const effective = new Map<string, ValidPair>()
  for (const [tag, ps] of byTag) {
    if (tainted.has(tag) || !presentTags.has(tag)) continue
    if (ps.length === 1) effective.set(tag, ps[0]!)
  }

  const resolved: ResolvedApparatus[] = artifact.apparatus.map((apparatus) => {
    const tag = apparatus.tag
    if (tag && tainted.has(tag)) {
      // Taint: clear effective voltage so no detected fallback can price it.
      return { apparatus: { ...apparatus, busVoltageV: undefined }, voltageBasis: 'none' }
    }
    const eff = tag ? effective.get(tag) : undefined
    if (eff) {
      const detectedV = apparatus.busVoltageV
      if (detectedV !== undefined && detectedV !== eff.voltageV) {
        findings.push({
          code: 'voltage_assertion_conflict', severity: 'warning',
          message: `Asserted ${eff.voltageV}V overrides detected ${detectedV}V for ${tag} — operator wins.`,
          context: `${tag} (detected ${detectedV}V → asserted ${eff.voltageV}V)`,
          detail: { tag, detectedV, assertedV: eff.voltageV, actor: eff.actor, source: eff.source },
        })
      }
      return { apparatus: { ...apparatus, busVoltageV: eff.voltageV }, voltageBasis: 'asserted' }
    }
    return { apparatus, voltageBasis: detectedOrNone(apparatus.busVoltageV) }
  })

  return { resolved, findings }
}
```

- [ ] **Step 5: Add exports** to `src/index.ts`:

```ts
export { applyVoltageAssertions } from './signature/voltage-assertions'
export type { ResolvedApparatus } from './signature/voltage-assertions'
export type { VoltageAssertion } from './extraction/types'
export type { VoltageBasis } from './signature/types'
export type { TakeoffFinding, FindingSeverity, VoltageAssertionCode } from './buckets/types'
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage-assertions.test.ts && pnpm tsc --noEmit'`
Expected: PASS (all 10 cases) and typecheck clean.

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/extraction/types.ts packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/buckets/types.ts packages/estimator-takeoff/src/signature/voltage-assertions.ts packages/estimator-takeoff/src/index.ts packages/estimator-takeoff/test/voltage-assertions.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(estimator-takeoff): applyVoltageAssertions — validate/taint/apply per-tag voltage with coded findings"'
```

---

### Task A3: `assessApparatus` voltage-basis parameter + `ApparatusSignature.voltageBasis`

> **⚠ SUPERSEDED SHAPE — see spec Rev 3 (2026-06-25).** The single public
> `assessApparatus(x, voltageBasis?)` shown in this task was forgeable and was
> NOT shipped. The implemented form splits it: private `assessCore(x, basis?)`,
> public **one-arg** `assessApparatus(x)`, and engine-internal
> `assessResolvedApparatus(x, basis)` (used by `runTakeoff`/`emit`, NOT
> re-exported from `src/index.ts`). The 2-arg signature below is retained for
> task-history only — build to the Rev-3 shape.

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts`
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts`
- Modify: `packages/estimator-takeoff/test/normalize.test.ts`
- Modify: `packages/estimator-takeoff/test/quantify.test.ts`
- Modify: `packages/estimator-takeoff/test/breaker-map.test.ts`

**Interfaces:**
- Consumes: `VoltageBasis` (A2).
- Produces (Rev-3 shipped shape): private `assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment` + public **one-arg** `assessApparatus(x): ApparatusAssessment` + engine-internal `assessResolvedApparatus(x, voltageBasis): ApparatusAssessment` (not re-exported from index.ts). The signature it builds carries `voltageBasis: VoltageBasis`, defaulting to `x.busVoltageV !== undefined ? 'detected' : 'none'`; `'asserted'` can arrive only via the controlled parameter on the internal entry. *(The 2-arg public form below is superseded — see the banner.)*

- [ ] **Step 1: Add the required field** to `ApparatusSignature` in `src/signature/types.ts`:

```ts
export interface ApparatusSignature {
  kind: 'breaker'
  voltageClass: VoltageClass
  voltageV?: number
  voltageBasis: VoltageBasis   // NEW — always present, parallel to mountingBasis
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting
  mountingBasis: MountingBasis
  mvType?: MvType
  tag?: string
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string; block?: string }
}
```

- [ ] **Step 2: Write the failing test** — append to `test/normalize.test.ts` a new describe block (and import `VoltageBasis` is not needed; the literal strings suffice):

```ts
describe('assessApparatus — voltage provenance (voltageBasis)', () => {
  it('labels asserted when the controlled basis arg says so', () => {
    const a = assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480), 'asserted')
    expect(a.signature!.voltageBasis).toBe('asserted')
  })
  it('derives detected from busVoltageV when no basis arg is given', () => {
    expect(assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)).signature!.voltageBasis).toBe('detected')
  })
  it('never yields asserted from a raw apparatus call (no basis arg)', () => {
    expect(assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)).signature!.voltageBasis).not.toBe('asserted')
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/normalize.test.ts'`
Expected: FAIL — `assessApparatus` does not accept a 2nd arg / signature lacks `voltageBasis` (also a typecheck error on the new field).

- [ ] **Step 4: Implement** in `src/signature/normalize.ts`. Add the import and the parameter; compute and set the basis. Change the import line and the `assessApparatus` signature, and the signature-construction block:

```ts
import type { ApparatusSignature, Mounting, MountingBasis, MvType, TripFunction, VoltageBasis } from './types'
```

```ts
// SHIPPED (Rev 3): the body below is the PRIVATE core; do not export it 2-arg.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // ...unchanged NON_BREAKER / candidateKind / voltageClass guard logic...
// public wrapper: export function assessApparatus(x) { return assessCore(x) }
// engine entry:   export function assessResolvedApparatus(x, b) { return assessCore(x, b) }
```

Within the function, where the signature is constructed, add the basis:

```ts
  const basis: VoltageBasis = voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')

  const signature: ApparatusSignature = {
    kind: 'breaker', voltageClass, voltageV: x.busVoltageV, voltageBasis: basis, frameA, tripA, functions,
    mounting, mountingBasis, mvType, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature, questions, isBreakerShaped: true }
```

(`normalizeApparatus` is unchanged — it delegates with no basis arg.)

- [ ] **Step 5: Fix the compile cascade** — every test that builds an `ApparatusSignature` literal must add `voltageBasis`. In `test/quantify.test.ts`, the `sig` helper (line ~6), the `untagged` helper (line ~31), and the two inline literals (lines ~51, ~60): add `voltageBasis: 'detected',` to each object. Example for the `sig` helper:

```ts
const sig = (tag: string, evidence: string, sheet = 'E01-11'): ApparatusSignature => ({
  kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'],
  mounting: 'draw_out', mountingBasis: 'text',
  tag, source: { sheet, page: 1, bbox: [0, 0, 1, 1], evidence },
})
```

Apply the same `voltageBasis: 'detected',` insertion to the `untagged` helper and the two inline `{ kind: 'breaker', ... }` literals in `test/quantify.test.ts`, and to the `base` literal (line ~8) in `test/breaker-map.test.ts`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/normalize.test.ts test/quantify.test.ts test/breaker-map.test.ts && pnpm tsc --noEmit'`
Expected: PASS and typecheck clean.

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize.test.ts packages/estimator-takeoff/test/quantify.test.ts packages/estimator-takeoff/test/breaker-map.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(estimator-takeoff): ApparatusSignature.voltageBasis + assessApparatus controlled basis param"'
```

---

### Task A3b: per-tag invariant — include `voltageV` + `voltageBasis` in the quantify spec key

**Files:**
- Modify: `packages/estimator-takeoff/src/quantify/quantify.ts`
- Test: `packages/estimator-takeoff/test/quantify.test.ts`

**Interfaces:**
- Consumes: `ApparatusSignature.voltageV`, `ApparatusSignature.voltageBasis` (A3).
- Produces: `specKey` now distinguishes devices by nominal `voltageV` and `voltageBasis`. **Why this task exists:** the current `specKey` keys on `voltageClass` only, so two same-frame/same-function breakers in one block asserted at 480 V and 208 V (both LV) collapse into one `QuantifiedLine` and the second device silently inherits the representative's voltage — breaking the slice's core "price each device at its own asserted voltage" promise.

- [ ] **Step 1: Write the failing tests** — append to `test/quantify.test.ts` (the existing `sig` helper builds an `ApparatusSignature`; mutate `voltageV`/`voltageBasis` per case):

```ts
describe('quantify — per-tag voltage + provenance never collapse (the slice invariant)', () => {
  it('keeps two same-spec breakers in one block on separate lines when voltage differs', () => {
    const a = sig('A-480', 'one-line'); a.voltageV = 480
    const b = sig('B-208', 'one-line'); b.voltageV = 208
    const { lines } = quantify([a, b])
    expect(lines).toHaveLength(2)
    expect(lines.map((l) => l.signature.voltageV).sort((x, y) => (x ?? 0) - (y ?? 0))).toEqual([208, 480])
  })
  it('keeps same-spec same-voltage breakers separate when provenance differs (detected vs asserted)', () => {
    const det = sig('A', 'one-line'); det.voltageV = 480                       // basis detected (helper default)
    const asr = sig('B', 'one-line'); asr.voltageV = 480; asr.voltageBasis = 'asserted'
    expect(quantify([det, asr]).lines).toHaveLength(2)
  })
  it('still aggregates two identical-spec identical-voltage devices into one line (qty 2)', () => {
    const a = sig('A', 'one-line'); a.voltageV = 480
    const b = sig('B', 'one-line'); b.voltageV = 480
    const { lines } = quantify([a, b])
    expect(lines).toHaveLength(1); expect(lines[0]!.qty).toBe(2)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/quantify.test.ts'`
Expected: FAIL — the first two cases collapse to 1 line under the current `specKey` (voltageClass only).

- [ ] **Step 3: Implement** the spec-key change in `src/quantify/quantify.ts`:

```ts
function specKey(s: ApparatusSignature): string {
  return [
    s.voltageClass, s.voltageV ?? '-', s.voltageBasis, s.mounting, s.mvType ?? '-', s.functions.join(''),
    s.frameA ?? '-', s.tripA ?? '-', s.source.block ?? '-',   // voltageV + voltageBasis → per-tag voltage/provenance preserved
  ].join('|')
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/quantify.test.ts test/emit.test.ts && pnpm tsc --noEmit'`
Expected: PASS — the new cases green; existing quantify/emit tests unaffected (each of their tests uses a single uniform voltage + basis, and `deviceId` for untagged devices derives the same key as before).

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/quantify/quantify.ts packages/estimator-takeoff/test/quantify.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "fix(estimator-takeoff): specKey includes voltageV + voltageBasis (per-tag voltage never collapses)"'
```

---

### Task A4: wire `applyVoltageAssertions` into `runTakeoff` + `TakeoffResult.findings`

**Files:**
- Modify: `packages/estimator-takeoff/src/buckets/types.ts`
- Modify: `packages/estimator-takeoff/src/emit/emit.ts`
- Modify: `packages/estimator-takeoff/test/emit.test.ts`
- Test: `packages/estimator-takeoff/test/voltage-assertions.test.ts` (add an integration case)

**Interfaces:**
- Consumes: `applyVoltageAssertions` (A2), `assessApparatus(x, voltageBasis?)` (A3), `TakeoffFinding` (A2).
- Produces: `TakeoffResult.findings: TakeoffFinding[]` (required); `runTakeoff(artifact)` now resolves assertions and threads findings end-to-end.

- [ ] **Step 1: Add the required field** to `TakeoffResult` in `src/buckets/types.ts`:

```ts
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]
  findings: TakeoffFinding[]   // NEW — coded, severity-tagged assertion findings
}
```

- [ ] **Step 2: Write the failing integration test** — append to `test/voltage-assertions.test.ts`:

```ts
import { runTakeoff } from '../src/emit/emit'

describe('runTakeoff threads voltage assertions + findings', () => {
  const breaker = (tag: string, busVoltageV?: number): ExtractedApparatus => ({
    raw: `${tag} 4000AF/4000AT LSIG`, tag, sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1],
    evidence: 'one-line', block: 'P1-110', busVoltageV,
  })

  it('asserted voltage produces a matched line with voltageBasis asserted', () => {
    const r = runTakeoff({ pdf: 'x', apparatus: [breaker('M1-GB')], voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'], source: 'cli' }] })
    expect(r.findings).toEqual([])
    expect(r.matchedLines).toHaveLength(1)
    expect(r.matchedLines[0]!.voltageBasis).toBe('asserted')
  })

  it('an unknown-tag assertion surfaces an error finding even when another line matches', () => {
    const r = runTakeoff({
      pdf: 'x', apparatus: [breaker('M1-GB')],
      voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'] }, { voltageV: 480, tags: ['GHOST'] }],
    })
    expect(r.matchedLines.length).toBeGreaterThan(0)
    expect(r.findings.some((f) => f.code === 'voltage_assertion_unknown_tag' && f.severity === 'error')).toBe(true)
  })

  it('non-forgeable end to end: stray voltageBasis on JSON does not yield asserted', () => {
    const sneaky = { ...breaker('M1-GB', 480), voltageBasis: 'asserted' } as unknown as ExtractedApparatus
    const r = runTakeoff({ pdf: 'x', apparatus: [sneaky] })   // no assertion
    expect(r.matchedLines[0]!.voltageBasis).toBe('detected')
  })
})
```

(`MatchedLine.voltageBasis` is added in Task A5 — these assertions on `voltageBasis` will fail to typecheck until A5; that is expected. To keep A4 self-contained, the `voltageBasis` field on `MatchedLine` is added here as part of Step 4 so this test compiles. See Step 4.)

- [ ] **Step 3: Run test to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage-assertions.test.ts'`
Expected: FAIL — `runTakeoff` does not populate `findings`; `MatchedLine.voltageBasis` undefined.

- [ ] **Step 4: Implement** the wiring + the `MatchedLine.voltageBasis` field (added here so this task compiles; emit notes + refusal come in A5). In `src/buckets/types.ts`:

```ts
export interface MatchedLine { ref: string; qty: number; block: string; mountingBasis: MountingBasis; voltageBasis: VoltageBasis; line: QuantifiedLine }
```

Add the import at the top of `src/buckets/types.ts`:

```ts
import type { MountingBasis, VoltageBasis } from '../signature/types'
```

In `src/emit/emit.ts`, update imports and `runTakeoff`:

```ts
import { applyVoltageAssertions } from '../signature/voltage-assertions'
import type { MatchedLine, OperatorQuestion, TakeoffResult, UnmatchedCandidate, TakeoffFinding } from '../buckets/types'
```

```ts
export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const { resolved, findings } = applyVoltageAssertions(artifact)
  const sigs: ApparatusSignature[] = []
  const questions: OperatorQuestion[] = []
  const unresolved: { x: ExtractedApparatus; questions: OperatorQuestion[] }[] = []

  for (const { apparatus, voltageBasis } of resolved) {
    const a = assessApparatus(apparatus, voltageBasis)
    if (a.signature) { sigs.push(a.signature); questions.push(...a.questions); continue }
    unresolved.push({ x: apparatus, questions: a.questions })
  }

  const { lines, locationOnly } = quantify(sigs)

  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) for (const t of l.memberTags) byTag.set(t, l)

  for (const { x, questions: qs } of unresolved) {
    const l = x.tag ? byTag.get(x.tag) : undefined
    if (l) { l.sources.push({ sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block }); continue }
    questions.push(...qs)
  }

  for (const s of locationOnly) {
    questions.push({ question: `Device ${s.tag ?? '(untagged)'} appears only on a non-authoritative sheet — include it?`, context: `${s.source.sheet} (${s.source.evidence})` })
  }

  for (const w of artifact.profileWarnings ?? []) {
    questions.push({ question: w, context: 'legend/profile' })
  }

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) matchedLines.push({ ref, qty: line.qty, block: line.signature.source.block ?? line.signature.source.sheet, mountingBasis: line.signature.mountingBasis, voltageBasis: line.signature.voltageBasis, line })
    else unmatchedCandidates.push({ reason: `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('') || '—'}`, line })
  }
  return { matchedLines, unmatchedCandidates, operatorQuestions: questions, findings }
}
```

- [ ] **Step 5: Fix the compile cascade** in `test/emit.test.ts` — the hand-built `TakeoffResult` literal at the zero-lines test must add `findings: []`:

```ts
  it('emitEnvelope fails closed (throws) when there are zero matched lines', () => {
    expect(() => emitEnvelope({ matchedLines: [], unmatchedCandidates: [], operatorQuestions: [], findings: [] }, { projectNumber: 'X' }))
      .toThrow(/zero matched lines/)
  })
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/voltage-assertions.test.ts test/emit.test.ts && pnpm tsc --noEmit'`
Expected: PASS and typecheck clean.

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/buckets/types.ts packages/estimator-takeoff/src/emit/emit.ts packages/estimator-takeoff/test/emit.test.ts packages/estimator-takeoff/test/voltage-assertions.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(estimator-takeoff): runTakeoff applies voltage assertions + threads TakeoffResult.findings"'
```

---

### Task A5: `emitEnvelope` refuses on blocking findings + voltage provenance in notes

**Files:**
- Modify: `packages/estimator-takeoff/src/emit/emit.ts`
- Modify: `packages/estimator-takeoff/test/emit.test.ts`

**Interfaces:**
- Consumes: `TakeoffResult.findings` (A4), `MatchedLine.voltageBasis` (A4).
- Produces: `emitEnvelope` throws `/blocking voltage-assertion/` when any finding has `severity === 'error'`, before the zero-lines check; per-line `notes` include voltage + basis.

- [ ] **Step 1: Write the failing tests** — append to `test/emit.test.ts`:

```ts
import type { ExtractedApparatus } from '../src/extraction/types'

describe('emitEnvelope — blocking voltage-assertion findings', () => {
  const brk = (tag: string, busVoltageV?: number): ExtractedApparatus => ({
    raw: `${tag} 4000AF/4000AT LSIG`, tag, sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1],
    evidence: 'one-line', block: 'P1-110', busVoltageV,
  })

  it('refuses to emit when an error finding is present even though a line matched', () => {
    const r = runTakeoff({
      pdf: 'x', apparatus: [brk('M1-GB')],
      voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'] }, { voltageV: 480, tags: ['GHOST'] }],
    })
    expect(r.matchedLines.length).toBeGreaterThan(0)
    expect(() => emitEnvelope(r, { projectNumber: 'X' })).toThrow(/blocking voltage-assertion/)
  })

  it('a conflict (warning) does NOT block emission — operator wins, device prices', () => {
    const r = runTakeoff({ pdf: 'x', apparatus: [brk('M1-GB', 240)], voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'] }] })
    expect(r.findings.some((f) => f.code === 'voltage_assertion_conflict' && f.severity === 'warning')).toBe(true)
    expect(r.matchedLines[0]!.voltageBasis).toBe('asserted')
    expect(() => emitEnvelope(r, { projectNumber: 'X' })).not.toThrow()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/emit.test.ts'`
Expected: FAIL — the first case does not throw (emit only gates on zero lines today).

- [ ] **Step 3: Implement** the refusal + notes in `src/emit/emit.ts`. At the top of `emitEnvelope`:

```ts
export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  const blocking = result.findings.filter((f) => f.severity === 'error')
  if (blocking.length > 0) {
    const codes = [...new Set(blocking.map((f) => f.code))].join(', ')
    throw new Error(
      `estimator-takeoff: refusing to emit — ${blocking.length} blocking voltage-assertion finding(s) [${codes}]. ` +
      `Resolve the operator voltage assertions before emitting.`,
    )
  }
  if (result.matchedLines.length === 0) {
    throw new Error('estimator-takeoff: refusing to emit an envelope with zero matched lines — all candidates are unmatched/uncertain; resolve construction/catalog evidence or review the takeoff.')
  }
  // ...existing scope build...
```

And update the per-line `notes` (in the `for (const m of result.matchedLines)` loop):

```ts
    scope.lines.push({ ref: m.ref, qty: m.qty, designation: m.line.signature.tag, notes: `from ${src?.sheet ?? '?'}; construction basis: ${m.mountingBasis}; voltage ${m.line.signature.voltageV}V (${m.voltageBasis})` })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/emit.test.ts && pnpm tsc --noEmit'`
Expected: PASS and typecheck clean.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/src/emit/emit.ts packages/estimator-takeoff/test/emit.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(estimator-takeoff): emitEnvelope refuses on blocking findings + voltage provenance in notes"'
```

---

### Task A6: golden rewrite (named 480 subset) + synthetic mixed-voltage proof

**Files:**
- Modify: `packages/estimator-takeoff/test/golden-e01-11.test.ts`
- Create: `packages/estimator-takeoff/test/fixtures/synthetic-mixed-voltage.json`
- Test: `packages/estimator-takeoff/test/voltage-assertions.test.ts` (add the synthetic per-tag case)

**Interfaces:**
- Consumes: `runTakeoff`, `emitEnvelope` (final form), the real `stack-phx02a-e01-11-extract.json` fixture (all `busVoltageV` undefined).

- [ ] **Step 1: Create the synthetic fixture** `test/fixtures/synthetic-mixed-voltage.json` (explicitly synthetic — no real-sheet claim). **Both devices share frame/trip/functions/mounting/block** and differ ONLY in asserted voltage, so the per-tag test genuinely exercises the quantify-collapse path that Task A3b fixes:

```json
{
  "pdf": "synthetic-mixed-voltage",
  "apparatus": [
    { "raw": "MAIN-480-GB 1600AF/1600AT LSIG", "tag": "MAIN-480-GB", "sheet": "SYN-01", "page": 1, "bbox": [0, 0, 1, 1], "evidence": "one-line", "block": "SYN" },
    { "raw": "HOUSE-208-GB 1600AF/1600AT LSIG", "tag": "HOUSE-208-GB", "sheet": "SYN-01", "page": 1, "bbox": [2, 2, 3, 3], "evidence": "one-line", "block": "SYN" }
  ]
}
```

- [ ] **Step 2: Write the failing synthetic per-tag test** — append to `test/voltage-assertions.test.ts`:

```ts
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

describe('synthetic mixed-voltage: per-tag, not block-scoped', () => {
  const syn = JSON.parse(
    readFileSync(fileURLToPath(new URL('./fixtures/synthetic-mixed-voltage.json', import.meta.url)), 'utf8'),
  ) as ExtractionArtifact

  it('synthetic_mixed_voltage_prices_each_tag_at_its_own_asserted_voltage', () => {
    const r = runTakeoff({
      ...syn,
      voltageAssertions: [{ voltageV: 480, tags: ['MAIN-480-GB'] }, { voltageV: 208, tags: ['HOUSE-208-GB'] }],
    })
    expect(r.findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(r.matchedLines).toHaveLength(2)                          // NOT collapsed — the A3b invariant
    const main = r.matchedLines.find((m) => m.line.signature.tag === 'MAIN-480-GB')!
    const house = r.matchedLines.find((m) => m.line.signature.tag === 'HOUSE-208-GB')!
    expect(main.line.signature.voltageV).toBe(480)
    expect(house.line.signature.voltageV).toBe(208)
    expect(main.voltageBasis).toBe('asserted')
    expect(house.voltageBasis).toBe('asserted')
  })
})
```

- [ ] **Step 3: Rewrite the golden positive case** — replace the second `it(...)` in `test/golden-e01-11.test.ts` (the `e01_11_with_operator_voltage_assertion_emits_drawout_lsig` case) with the named-subset version. Leave the first (negative) case unchanged:

```ts
  it('e01_11_named_480_subset_emits_drawout_lsig (per-tag operator assertion; 208V house bus intentionally NOT asserted)', () => {
    // Operator asserts 480V for a NAMED SUBSET of confirmed-480 tags (MSB-P1-110-GB is the draw-out LSIG main).
    // The mixed-bus 208/120 house tags are deliberately left unasserted (their voltage is an unresolved operator input).
    const NAMED_480 = ['MSB-P1-110-GB', 'ACC-1-09-FB', 'ACC-1-10-FB']
    const asserted: ExtractionArtifact = {
      ...fixture,
      voltageAssertions: [{ voltageV: 480, tags: NAMED_480, source: 'cli' }],
    }
    const r = runTakeoff(asserted)
    expect(r.findings.filter((f) => f.severity === 'error')).toEqual([])      // no blocking findings
    const lsig = r.matchedLines.find((m) => m.ref === 'Circuit Breaker LV - Draw-Out (LSIG)')
    expect(lsig).toBeDefined()
    expect(lsig!.mountingBasis).toBe('estimating_baseline')                   // construction is an estimating assumption
    expect(lsig!.voltageBasis).toBe('asserted')                              // voltage is operator-supplied
    const { envelope, findings } = emitEnvelope(r, { projectNumber: 'GOLDEN' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(envelope.scopes.length).toBeGreaterThan(0)
  })
```

- [ ] **Step 4: Run the golden + synthetic tests to verify they fail then pass**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run test/golden-e01-11.test.ts test/voltage-assertions.test.ts'`
Expected: PASS — the named subset produces draw-out LSIG lines with `voltageBasis: 'asserted'`; the synthetic case prices 480 and 208 per tag. (If a fresh run was red before the edits compiled, that confirms the TDD red→green.)

- [ ] **Step 5: Full suite + typecheck**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage/packages/estimator-takeoff && pnpm vitest run && pnpm tsc --noEmit'`
Expected: PASS — entire estimator-takeoff suite green, typecheck clean.

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-takeoff-voltage && git add packages/estimator-takeoff/test/golden-e01-11.test.ts packages/estimator-takeoff/test/fixtures/synthetic-mixed-voltage.json packages/estimator-takeoff/test/voltage-assertions.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "test(estimator-takeoff): named-480-subset golden + synthetic per-tag mixed-voltage proof"'
```

---

# PHASE B — drawing-nav `--assert-voltage` thin collector (after Phase A merges)

> **Repo:** `C:\Users\jjswe\Tools\drawing-nav` (separate git, `master`). Runs locally on Windows; tests via `pytest` in the repo's `.venv`. This phase has **no** dependency on the host — it only produces the JSON shape Phase A consumes.

### Task B1: `--assert-voltage` parse + embed

**Files:**
- Modify: `C:\Users\jjswe\Tools\drawing-nav\drawing_nav.py`
- Create: `C:\Users\jjswe\Tools\drawing-nav\tests\test_assert_voltage.py`

**Interfaces:**
- Produces: `parse_voltage_assertions(specs: list[str], actor: str | None = None, note: str | None = None) -> list[dict]` — pure helper, no PDF, no semantic validation; raises `SystemExit` on malformed flag syntax. `cmd_extract` calls it and sets `art["voltageAssertions"]` when non-empty.

- [ ] **Step 1: Write the failing test** — create `tests/test_assert_voltage.py`:

```python
import pytest
from drawing_nav import parse_voltage_assertions


def test_parses_multiple_assertions():
    out = parse_voltage_assertions(["480:A,B", "208:C"])
    assert out == [
        {"voltageV": 480, "tags": ["A", "B"], "source": "cli"},
        {"voltageV": 208, "tags": ["C"], "source": "cli"},
    ]


def test_carries_actor_and_note():
    out = parse_voltage_assertions(["480:A"], actor="jls", note="from RFI 12")
    assert out[0]["actor"] == "jls"
    assert out[0]["note"] == "from RFI 12"


def test_strips_whitespace_in_tags():
    out = parse_voltage_assertions(["480: A , B "])
    assert out[0]["tags"] == ["A", "B"]


def test_rejects_missing_colon():
    with pytest.raises(SystemExit):
        parse_voltage_assertions(["foo"])


def test_rejects_empty_tag_list():
    with pytest.raises(SystemExit):
        parse_voltage_assertions(["480:"])


def test_rejects_non_integer_voltage():
    with pytest.raises(SystemExit):
        parse_voltage_assertions(["4.8:A"])


def test_empty_returns_empty():
    assert parse_voltage_assertions([]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/c/Users/jjswe/Tools/drawing-nav" && .venv/Scripts/python.exe -m pytest tests/test_assert_voltage.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_voltage_assertions'`.

- [ ] **Step 3: Implement** in `drawing_nav.py`. Add the pure helper just above `cmd_extract` (near the `# ---- extract` banner):

```python
def parse_voltage_assertions(specs, actor=None, note=None):
    """Thin collector: parse repeatable --assert-voltage 'V:TAG[,TAG...]' into VoltageAssertion dicts.

    No semantic validation (tag existence / conflicts / voltage sanity) — the engine owns that.
    Only the flag's own syntax is checked here."""
    assertions = []
    for spec in specs:
        v, sep, tags = spec.partition(":")
        if not sep or not tags.strip():
            raise SystemExit(f"--assert-voltage: expected V:TAG[,TAG...], got {spec!r}")
        try:
            voltage = int(v)
        except ValueError:
            raise SystemExit(f"--assert-voltage: voltage must be an integer, got {v!r}")
        tag_list = [t.strip() for t in tags.split(",")]
        if any(not t for t in tag_list):                       # fail closed on an empty tag slot (e.g. "480:A,,B")
            raise SystemExit(f"--assert-voltage: empty tag in {spec!r}")
        entry = {"voltageV": voltage, "tags": tag_list, "source": "cli"}
        if actor:
            entry["actor"] = actor
        if note:
            entry["note"] = note
        assertions.append(entry)
    return assertions
```

Wire it into `cmd_extract` — insert immediately after `art = extract_artifact(d, pages=pages, now=now)`:

```python
    art = extract_artifact(d, pages=pages, now=now)
    assertions = parse_voltage_assertions(a.assert_voltage, a.assert_actor, a.assert_note)
    if assertions:
        art["voltageAssertions"] = assertions
    payload = json.dumps(art, indent=2, ensure_ascii=False)
```

Add the flags to the `extract` subparser (after the `--no-timestamp` line):

```python
    s = sub.add_parser("extract"); s.add_argument("pdf")
    s.add_argument("--page", type=int)
    s.add_argument("--out")
    s.add_argument("--no-timestamp", action="store_true")
    s.add_argument("--assert-voltage", action="append", default=[], metavar="V:TAG[,TAG...]",
                   help="operator voltage assertion, repeatable (e.g. 480:MSB-A,MSB-B)")
    s.add_argument("--assert-actor")
    s.add_argument("--assert-note")
    s.set_defaults(func=cmd_extract)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/c/Users/jjswe/Tools/drawing-nav" && .venv/Scripts/python.exe -m pytest tests/test_assert_voltage.py -v`
Expected: PASS (7 cases).

- [ ] **Step 5: Run the full drawing-nav suite (no regressions)**

Run: `cd "/c/Users/jjswe/Tools/drawing-nav" && .venv/Scripts/python.exe -m pytest -q`
Expected: PASS — existing extract/assemble/pipeline tests still green.

- [ ] **Step 6: Commit**

```bash
cd "/c/Users/jjswe/Tools/drawing-nav" && git add drawing_nav.py tests/test_assert_voltage.py && git commit -m "feat(extract): --assert-voltage thin collector → artifact voltageAssertions"
```

---

## Self-Review

**1. Spec coverage** (rev-2 §-by-§):
- §3.1 `VoltageAssertion` → A2 Step 1. ✓
- §3.2 `voltageAssertions` on artifact → A2 Step 1. ✓
- §3.3 non-forgeable `ResolvedApparatus`, no `voltageBasis` on `ExtractedApparatus` → A2 (type + recompute) + A2/A4 non-forgeable tests. ✓
- §3.4 `ApparatusSignature.voltageBasis` → A3. ✓
- §3.5 `MatchedLine.voltageBasis` + `TakeoffFinding` + `TakeoffResult.findings` → A4 (field) + A2 (TakeoffFinding type). ✓
- §3.6 severity policy → A2 (codes/severity) + A5 (emit refusal) + tests. ✓
- §4 algorithm (validate/taint/apply/conflict) → A2; plus malformed-shape fail-closed guard (`voltage_assertion_invalid_shape`) → A2. ✓
- **Per-tag quantify invariant** (`specKey` += `voltageV` + `voltageBasis` so distinct-voltage/provenance devices never collapse) → A3b. ✓
- §4.1 `assessApparatus(x, basis?)` → A3. ✓
- §4.2 runTakeoff wiring → A4. ✓
- §4.3 notes surfacing → A5. ✓
- §4.4 emitEnvelope refusal → A5. ✓
- §5 Python collector → B1. ✓
- §6 tests (every listed case) → A2/A4/A5/A6 + B1. ✓
- D8 classifyVoltage guard → A1. ✓
- O1 synthetic-only mixed proof → A6 Step 1-2. ✓
- O2 named-480 subset golden, explicit test name → A6 Step 3. ✓

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; test names concrete; the only bracketed token is the deliberate `NAMED_480` constant (a real value). ✓

**3. Type consistency:** `VoltageBasis`, `VoltageAssertion`, `TakeoffFinding`, `VoltageAssertionCode`, `FindingSeverity`, `ResolvedApparatus`, `applyVoltageAssertions`, `assessApparatus(x, voltageBasis?)`, `MatchedLine.voltageBasis`, `TakeoffResult.findings` are spelled identically across A2→A6. The five codes (the four §3.6 codes + `voltage_assertion_invalid_shape`) are spelled identically in the union (A2 Step 1) and every `findings.push`. `MatchedLine.voltageBasis` is introduced in A4 (so A4's test compiles) and consumed in A5 — noted explicitly in A4 Step 2/4. ✓

**Note on task ordering:** A1→A2→A3→A3b→A4→A5→A6 then B1. Each Phase-A task ends green and typechecks. A3b (specKey) lands after A3 — which adds the `signature.voltageBasis`/`voltageV` it reads — and before A6, whose synthetic per-tag test (`toHaveLength(2)`) depends on it. `MatchedLine.voltageBasis` lands in A4 (not A5) deliberately so A4's integration test compiles; A5 only adds the emit-time *behavior* (refusal + notes).
