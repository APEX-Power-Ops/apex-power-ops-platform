# Standalone Ground-Fault Protection Device (LV) Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admit a narrow STANDALONE Ground-Fault Protection Device/System (LV) escape hatch into `packages/estimator-takeoff` so only a standalone GFP device is counted (per device) and routed to a one-click Gate-2 scope confirmation (never auto-priced), while an embedded ground-fault function (breaker LSIG, ATS/SPD function) stays with its parent and produces NO GFP line.

**Architecture:** Reuse the relay/transformer `scope_pending` machinery. Add a fourth signature `kind: 'gfp'`, a STANDALONE-ONLY recognizer whose load-bearing guard (`isGfpParentShape`) excludes parent-shaped rows BEFORE honoring `candidateKind`, and a trivial single-ref match (`matchGfp`). Single priced ref => no tier ambiguity, no candidate GROUP, no V1 `catalog_gap`/`null` path.

**Tech Stack:** TypeScript, Vitest, pnpm workspace. Host build over `ssh olares-mesh`. Lane worktree: `/home/olares/code/apex/apex-gfp`, branch `estimator-takeoff/gfp-family-admission` (off main `ab43c569`).

## Global Constraints

- **THREE non-negotiables (operator-pinned):**
  1. **Parent exclusion BEFORE candidateKind.** `isGfpParentShape(x) = looksLikeBreaker(x.raw) || NON_BREAKER.test(x.raw)` is checked first in `looksLikeGfp`; a parent-shaped row NEVER becomes GFP, even with `candidateKind:'gfp'`.
  2. **Bare/function text NEVER counts.** `ground fault protection` (bare/function), `ground fault test`, `per 7.14`, and ANSI `50G/51G/50N/51N/64` are NOT GFP device tokens. They are role/scope evidence only.
  3. **Standalone noun forms + tag -> scope_pending(single ref).** `GROUND FAULT RELAY`, `GROUND FAULT PROTECTION SYSTEM`, `GFP/GFPE/GFR` (with a tag, on a non-parent row) -> `scope_pending` with `candidateRefs=[GFP_REF]`, `provisionalDefaultRef=GFP_REF`.
- **STANDALONE-ONLY.** GFP is a narrow escape hatch, not a "ground fault mentioned" family. A real standalone GFP device is its OWN, non-parent-shaped row.
- **`candidateKind:'gfp'` = producer asserts a STANDALONE GFP device** (honored only on a non-parent row). `looksLikeGfp` also DEFERS to an explicit non-gfp `candidateKind` (relay/transformer/breaker) - producer authority, mirroring the existing `looksLikeTransformer` deferral to `candidateKind:'relay'`. (Plan refinement of spec Rev 2; flagged to operator.)
- **GFP never auto-prices.** Every recognized standalone GFP device -> `scope_pending`. No "matched" GFP line; no GFP `catalog_gap` in V1.
- **ASCII-only** in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **No new catalog refs, no new hours.** V1 uses the single existing NETA-7.14 ref `Ground Fault Protection Device LV`. Matched by exact STRING, never section ("7.14" is overloaded with CT refs in the firm catalog).
- **Breaker AND transformer AND relay goldens byte-identical** after every task (run `golden-e01-11.test.ts`, `transformer-golden.test.ts`, `relay-golden.test.ts` - must stay green unchanged).
- **Gates (run on host, with PATH prefix):** `export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH` then `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package gate; `--filter apex-operations-web` matches NOTHING - false-green trap).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **Commit identity:** `jasonlswenson-sys <jasonlswenson@gmail.com>`; every commit ends `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Single writer per host worktree;** implementers edit host files (compose-locally-then-scp or edit in place), run host pnpm via the PATH prefix, commit on host.

---

## File Structure

- Create: `src/catalog/gfp-map.data.ts` - the single GFP ref + R1 flag (Task 1).
- Create: `src/catalog/gfp-map.ts` - `matchGfp` + `GfpScopeMatch` (Task 2).
- Modify: `src/signature/types.ts` - add `GfpSignature` interface (Task 2); add it to the `ApparatusSignature` union (Task 3).
- Modify: `src/extraction/types.ts`, `src/extraction/parse.ts` - widen `candidateKind` to `'gfp'` (Task 2).
- Modify: `src/signature/normalize.ts` - `GFP_DEVICE`, `isGfpParentShape`, `looksLikeGfp`, `assessGfp`, `AssessmentCode`, `assessCore` routing (Task 3).
- Modify: `src/quantify/quantify.ts` - `specKey` gfp branch (Task 3).
- Modify: `src/emit/emit.ts` - gfp match-loop branch + `ASSESS_TO_REASON` + imports (Task 3).
- Modify: `src/buckets/types.ts` - `gfp_scope_pending` codes (Task 3).
- Create: `test/gfp-catalog.test.ts` (T1), `test/gfp-map.test.ts` (T2), `test/normalize-gfp.test.ts` + `test/gfp-pipeline.test.ts` (T3), `test/gfp-recognition.test.ts` + `test/gfp-cross-family.test.ts` (T4), `test/fixtures/gfp-mixed.extract.json` + `test/gfp-golden.test.ts` (T5).
- Modify: `test/parse.test.ts` - accept `candidateKind:'gfp'` (T2).

---

### Task 1: GFP catalog data + exact-ref seed validation

**Files:**
- Create: `packages/estimator-takeoff/src/catalog/gfp-map.data.ts`
- Test: `packages/estimator-takeoff/test/gfp-catalog.test.ts`

**Interfaces:**
- Produces: `GFP_REF: string`, `GFP_R1_RATIFIED: boolean` (consumed by Task 2 `matchGfp` and Task 3 `emit`).

- [ ] **Step 1: Write the failing test**

`test/gfp-catalog.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { GFP_REF, GFP_R1_RATIFIED } from '../src/catalog/gfp-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('GFP catalog authority', () => {
  it('the single GFP ref resolves verbatim in the live seed', () => {
    expect(GFP_REF).toBe('Ground Fault Protection Device LV')
    expect(REFS.has(GFP_REF), `seed missing ref: ${GFP_REF}`).toBe(true)
  })
  it('the GFP ref is active and unit_of_issue=each in the seed', () => {
    const m = EQUIPMENT_MODELS_SEED.find((x: { ref: string }) => x.ref === GFP_REF) as
      { lifecycle_status?: string; unit_of_issue?: string } | undefined
    expect(m).toBeDefined()
    expect(m!.lifecycle_status).toBe('active')
    expect(m!.unit_of_issue).toBe('each')
  })
  it.todo('R1: SME confirms the single-ref-covers-all convention -> flip GFP_R1_RATIFIED=true')
  it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests)', () => {
    expect(GFP_R1_RATIFIED).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-catalog`
Expected: FAIL - cannot resolve `../src/catalog/gfp-map.data`.

- [ ] **Step 3: Write minimal implementation**

`src/catalog/gfp-map.data.ts`:
```ts
// Ref VERBATIM from estimator-core EQUIPMENT_MODELS_SEED (NETA 7.14, unit_of_issue=each).
// STANDALONE ground-fault protection device/system only. Matched by exact STRING, never by the firm
// section "7.14" (the firm catalog overloads 7.14 onto Current-Transformer refs - match the string).
export const GFP_REF = 'Ground Fault Protection Device LV'

// Single-ref-covers-all convention is PROVISIONAL until the SME confirms whether a dedicated
// GFPE / ground-fault relay / sensor ever prices differently from this one device ref (D1).
// GFP never auto-prices, so provisional is fail-closed.
export const GFP_R1_RATIFIED = false
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-catalog`
Expected: PASS (3 pass, 1 todo).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/catalog/gfp-map.data.ts packages/estimator-takeoff/test/gfp-catalog.test.ts
git commit -m "feat(takeoff): GFP catalog authority - single 7.14 ref + R1 flag (Task 1)"
```

---

### Task 2: GfpSignature interface + candidateKind widen + matchGfp

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts` (add `GfpSignature` interface; do NOT touch the union yet)
- Modify: `packages/estimator-takeoff/src/extraction/types.ts` (line 15 candidateKind), `packages/estimator-takeoff/src/extraction/parse.ts` (line ~58 guard)
- Create: `packages/estimator-takeoff/src/catalog/gfp-map.ts`
- Test: `packages/estimator-takeoff/test/gfp-map.test.ts`; Modify: `packages/estimator-takeoff/test/parse.test.ts`

**Interfaces:**
- Consumes: `GFP_REF` (Task 1).
- Produces: `GfpSignature` (Task 3 adds it to the union), `matchGfp(sig: GfpSignature): GfpScopeMatch`, `GfpScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }`.

- [ ] **Step 1: Write the failing tests**

`test/gfp-map.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { matchGfp } from '../src/catalog/gfp-map'
import { GFP_REF } from '../src/catalog/gfp-map.data'
import type { GfpSignature } from '../src/signature/types'

const gsig = (o: Partial<GfpSignature> = {}): GfpSignature => ({
  kind: 'gfp', voltageBasis: 'none', tag: 'GFP-1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...o,
})

describe('matchGfp - single ref, never null in V1', () => {
  it('returns the single GFP ref as the only candidate AND the provisional default', () => {
    const m = matchGfp(gsig())
    expect(m.group).toEqual([GFP_REF])
    expect(m.defaultRef).toBe(GFP_REF)
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('is voltage-agnostic (no busVoltage -> still the single-ref match)', () => {
    const m = matchGfp(gsig({ voltageClass: undefined, voltageV: undefined }))
    expect(m.group).toEqual([GFP_REF])
  })
})
```

Append to `test/parse.test.ts` (inside the candidateKind describe block, after the relay case at line ~52):
```ts
  it('accepts candidateKind:gfp and the row parses without error', () => {
    const a = ok({
      pdf: 'x.pdf',
      apparatus: [{ raw: 'GFP-1 GROUND FAULT PROTECTION SYSTEM', tag: 'GFP-1', sheet: 'E1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', candidateKind: 'gfp' }],
    })
    expect(a.apparatus[0]!.candidateKind).toBe('gfp')
  })
```
(Use the same `ok(...)` helper the existing parse.test.ts uses for the relay/transformer cases; mirror its exact call form.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-map parse`
Expected: `gfp-map` FAILs (no `../src/catalog/gfp-map`); `parse` FAILs (candidateKind:'gfp' rejected as unknown).

- [ ] **Step 3: Write minimal implementation**

In `src/signature/types.ts`, ADD the interface (immediately after `RelaySignature`, BEFORE the `ApparatusSignature` type alias; do NOT modify the union in this task):
```ts
export interface GfpSignature extends BaseSignature {
  kind: 'gfp'
  ansiFunctions?: string[]   // evidence/display only (e.g. 64, 50G); never used to match or to count
  // voltageClass stays optional (inherited): GFP voltage is contextual and never gates.
}
```

In `src/extraction/types.ts` line 15, widen:
```ts
  candidateKind?: 'breaker' | 'transformer' | 'relay' | 'gfp'   // 'gfp' = producer asserts a STANDALONE ground-fault protection device (honored only on a non-parent-shaped row)
```

In `src/extraction/parse.ts` (~line 58), widen the guard + message:
```ts
  // candidateKind: 'breaker' | 'transformer' | 'relay' | 'gfp'
  if (r['candidateKind'] !== undefined && r['candidateKind'] !== 'breaker' && r['candidateKind'] !== 'transformer' && r['candidateKind'] !== 'relay' && r['candidateKind'] !== 'gfp') fail(`${p}.candidateKind`, "'breaker'|'transformer'|'relay'|'gfp'", r['candidateKind'])
```

Create `src/catalog/gfp-map.ts`:
```ts
import type { GfpSignature } from '../signature/types'
import { GFP_REF } from './gfp-map.data'

export interface GfpScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }

const SCOPE_Q =
  'Confirm this standalone ground-fault protection device/system is in test scope (NETA 7.14); it is priced per device, separate from any breaker/ATS ground-fault trip function (which is carried by the parent ref).'

// Single ref: a recognized standalone GFP device always maps to the one priced ref (no tier choice,
// no V1 catalog_gap). The single ref is BOTH the only candidate and the provisional default (a one-click
// Gate-2 confirm). _sig is unused in V1 - the match does not depend on device attributes.
export function matchGfp(_sig: GfpSignature): GfpScopeMatch {
  return { group: [GFP_REF], defaultRef: GFP_REF, scopeQuestion: SCOPE_Q }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-map parse` then `pnpm --filter @apex/estimator-takeoff typecheck`
Expected: PASS. Typecheck clean (union untouched -> specKey/emit unaffected).

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/extraction/types.ts packages/estimator-takeoff/src/extraction/parse.ts packages/estimator-takeoff/src/catalog/gfp-map.ts packages/estimator-takeoff/test/gfp-map.test.ts packages/estimator-takeoff/test/parse.test.ts
git commit -m "feat(takeoff): GfpSignature + candidateKind:'gfp' + single-ref matchGfp (Task 2)"
```

---

### Task 3: Recognition + union wire (the integration task)

**Files:**
- Modify: `src/signature/types.ts` (add `GfpSignature` to the `ApparatusSignature` union)
- Modify: `src/signature/normalize.ts` (`GFP_DEVICE`, `isGfpParentShape`, `looksLikeGfp`, `assessGfp`, `AssessmentCode`, `assessCore` routing)
- Modify: `src/quantify/quantify.ts` (`specKey` gfp branch)
- Modify: `src/emit/emit.ts` (gfp match-loop branch + `ASSESS_TO_REASON` + imports)
- Modify: `src/buckets/types.ts` (`gfp_scope_pending` codes)
- Test: `test/normalize-gfp.test.ts`, `test/gfp-pipeline.test.ts`

**Interfaces:**
- Consumes: `GfpSignature` (T2), `matchGfp`/`GfpScopeMatch` (T2), `GFP_R1_RATIFIED` (T1), existing `looksLikeBreaker`/`NON_BREAKER`/`classifyVoltage`/`parseAnsiFunctions`.
- Produces: `isGfpParentShape(x): boolean` (exported, directly tested in T4); a live recognition->scope_pending pipeline for standalone GFP devices.

**Why one task:** widening the union breaks `specKey` and the emit `const tsig: TransformerSignature = sig` narrowing simultaneously (compile errors), and the emit branch can only be exercised end-to-end once recognition produces `GfpSignature`s. These are one cohesive, end-to-end-testable deliverable.

- [ ] **Step 1: Write the failing tests**

`test/normalize-gfp.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { assessApparatus, isGfpParentShape } from '../src/signature/normalize'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })

describe('GFP recognition - standalone-only', () => {
  it('standalone GROUND FAULT RELAY + tag -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT RELAY', tag: 'GFR-1' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
    expect(a.signature?.kind).toBe('gfp')
  })
  it('GROUND FAULT PROTECTION SYSTEM + tag -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT PROTECTION SYSTEM', tag: 'GFP-1' }))
    expect(a.signature?.kind).toBe('gfp')
  })
  it('candidateKind:gfp on a non-parent row -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GFP-2', tag: 'GFP-2', candidateKind: 'gfp' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
  })
  it('a GFP device with NO bus voltage never emits missing_voltage', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT MONITOR', tag: 'GFM-1' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
  })
})

describe('isGfpParentShape - the load-bearing guard (direct)', () => {
  it('a breaker frame row is parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: '800AF/800AT LSIG', tag: 'B1' }))).toBe(true)
  })
  it('a NON_BREAKER row (ATS) is parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: 'ATS 800A GROUND FAULT PROTECTION', tag: 'ATS-1' }))).toBe(true)
  })
  it('a standalone GFP device row is NOT parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: 'GROUND FAULT RELAY', tag: 'GFR-1' }))).toBe(false)
  })
})
```

`test/gfp-pipeline.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { GFP_REF } from '../src/catalog/gfp-map.data'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('GFP end-to-end through runTakeoff', () => {
  it('standalone GFP -> scope_pending(single ref) with the ref as provisional default', () => {
    const r = runTakeoff(art([row({ raw: 'GROUND FAULT PROTECTION SYSTEM', tag: 'GFP-1' })]))
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines ?? []).toHaveLength(1)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs).toEqual([GFP_REF])
    expect(sp.provisionalDefaultRef).toBe(GFP_REF)
    expect(sp.r1Ratified).toBe(false)
    expect(r.dispositions[0]!.reasonCode).toBe('gfp_scope_pending')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pnpm --filter @apex/estimator-takeoff test normalize-gfp gfp-pipeline`
Expected: FAIL - `isGfpParentShape` not exported; GFP rows assessed as `unrecognized_apparatus_row`.

- [ ] **Step 3: Write the implementation**

In `src/signature/types.ts`, widen the union:
```ts
export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature
```

In `src/signature/normalize.ts`:
(a) Add the type to the existing `./types` import: `... RelaySignature, RelayTechnology, GfpSignature, TransformerSignature ...`.
(b) Add the device regex near `RELAY_DEVICE` (device NOUNS only - not function/scope phrasings):
```ts
// STANDALONE GFP device NOUNS only. Deliberately does NOT match a bare ANSI ground function (50G/51G/64),
// the trip-function letter G, bare "ground fault protection" (function name), "ground fault test", or "per 7.14".
const GFP_DEVICE = /\b(GFPE?|GFR|ground[\s-]?fault\s+(relay|sensor|monitor|module|system|device|unit)|ground[\s-]?fault\s+protection\s+(system|device|unit|relay|module|panel))\b/i
```
(c) Add the helpers (place near `looksLikeRelay`):
```ts
// LOAD-BEARING standalone guard: a parent-shaped row (a breaker by frame/hint, or a NON_BREAKER device)
// carries its ground-fault burden in the PARENT ref, so it can NEVER become a GFP device - even with
// candidateKind:'gfp'. Exported for a direct unit test (the rule that prevents drift).
export function isGfpParentShape(x: ExtractedApparatus): boolean {
  return looksLikeBreaker(x.raw) || NON_BREAKER.test(x.raw)
}

function looksLikeGfp(x: ExtractedApparatus): boolean {
  if (isGfpParentShape(x)) return false                 // parent exclusion BEFORE candidateKind (non-negotiable #1)
  if (x.candidateKind === 'gfp') return true            // producer asserts a STANDALONE GFP device
  if (x.candidateKind !== undefined) return false       // defer to an explicit other-family producer signal (producer authority)
  return GFP_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}

function assessGfp(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // No FRAME_TRIP/conflict guard: looksLikeGfp (isGfpParentShape) already excludes any breaker-shaped row,
  // so assessGfp is only reached for a clean standalone device. The invariant is pinned by a test.
  const voltageClass = classifyVoltage(x.busVoltageV)   // MAY be undefined - GFP voltage contextual, NOT gated
  const sig: GfpSignature = {
    kind: 'gfp',
    ansiFunctions: parseAnsiFunctions(x.raw),
    voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'gfp_recognized', questions: [] }
}
```
(d) Add `'gfp_recognized'` to the `AssessmentCode` union (after `'relay_breaker_conflict'`).
(e) In `assessCore`, insert the GFP route BETWEEN the `looksLikeTransformer` block and the `looksLikeRelay` block:
```ts
  if (looksLikeGfp(x)) {
    return assessGfp(x, voltageBasis)
  }

  if (looksLikeRelay(x)) {
    return assessRelay(x, voltageBasis)
  }
```

In `src/quantify/quantify.ts`, add the gfp branch in `specKey` BEFORE the transformer fall-through (after the `s.kind === 'relay'` block):
```ts
  if (s.kind === 'gfp') {
    // single-ref family: per device; voltage optional/contextual; ANSI evidence NOT in the key.
    return [s.kind, s.voltageClass ?? '-', s.source.block ?? '-'].join('|')
  }
```

In `src/buckets/types.ts`, extend both unions:
```ts
// OperatorQuestionCode: add after 'relay_breaker_conflict'
  | 'gfp_scope_pending'
// DispositionReasonCode: add after 'relay_breaker_conflict'
  | 'gfp_scope_pending'
```

In `src/emit/emit.ts`:
(a) Imports - add the type to the `../signature/types` import and the two GFP modules:
```ts
import type { ApparatusSignature, BreakerSignature, TransformerSignature, RelaySignature, GfpSignature } from '../signature/types'
import { matchGfp } from '../catalog/gfp-map'
import { GFP_R1_RATIFIED } from '../catalog/gfp-map.data'
```
(b) `ASSESS_TO_REASON` - add the member (forced by the new AssessmentCode):
```ts
  gfp_recognized:                'gfp_scope_pending',   // unreachable (has signature); present for exhaustiveness
```
(c) Add the gfp match-loop branch BEFORE the `// kind === 'transformer'` fall-through (after the `if (sig.kind === 'relay') { ... continue }` block):
```ts
    if (sig.kind === 'gfp') {
      const gsig: GfpSignature = sig
      const scope = matchGfp(gsig)
      scopePendingLines.push({
        candidateRefs: scope.group,
        provisionalDefaultRef: scope.defaultRef,
        r1Ratified: GFP_R1_RATIFIED,
        scopeQuestion: scope.scopeQuestion,
        qty: line.qty,
        block: gsig.source.block ?? gsig.source.sheet,
        line,
      })
      for (const i of line.memberIndices) {
        stamp(dispositions, i, 'scope_pending', 'gfp_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
        const disp = dispositions[i]!
        disp.candidateRefs = scope.group
        disp.provisionalDefaultRef = scope.defaultRef
        disp.scopeQuestion = scope.scopeQuestion
      }
      questions.push({ question: scope.scopeQuestion, context: `${gsig.tag ?? gsig.source.sheet} (standalone GFP; priced per device; NETA 7.14)`, code: 'gfp_scope_pending' })
      continue
    }
```

- [ ] **Step 4: Run tests + typecheck to verify they pass**

Run: `pnpm --filter @apex/estimator-takeoff test normalize-gfp gfp-pipeline` then `pnpm --filter @apex/estimator-takeoff test` then `pnpm --filter @apex/estimator-takeoff typecheck` then `pnpm --filter './apps/operations-web' typecheck`
Expected: new tests PASS; full suite PASS (breaker/transformer/relay goldens unchanged); both typechecks clean.

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/src packages/estimator-takeoff/test/normalize-gfp.test.ts packages/estimator-takeoff/test/gfp-pipeline.test.ts
git commit -m "feat(takeoff): wire GFP into union + recognition pipeline (Task 3)"
```

---

### Task 4: Recognition guards + cross-family + operator-pinned invariants

**Files:**
- Test: `packages/estimator-takeoff/test/gfp-recognition.test.ts`, `packages/estimator-takeoff/test/gfp-cross-family.test.ts`
- (Modify `src/signature/normalize.ts` ONLY if a pinned case fails - fail-closed fixes.)

**Interfaces:**
- Consumes: everything from Task 3. No new production interfaces; this task is the operator-pinned regression net.

- [ ] **Step 1: Write the failing/guard tests**

`test/gfp-recognition.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { assessApparatus } from '../src/signature/normalize'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const noGfp = (r: ReturnType<typeof runTakeoff>) =>
  r.dispositions.every((d) => d.reasonCode !== 'gfp_scope_pending')

describe('operator-pinned GFP recognition invariants', () => {
  // #1 - breaker with GF function stays breaker; NEVER a GFP line
  it('800AF/800AT LSIG (+ ground fault protection text) -> breaker only, no GFP', () => {
    const r = runTakeoff(art([row({ raw: '800AF/800AT LSIG DRAW-OUT GROUND FAULT PROTECTION', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'breaker' })]))
    expect(r.matchedLines.length).toBe(1)
    expect(noGfp(r)).toBe(true)
  })

  // #2 - dedicated standalone GFP -> GFP
  it('GROUND FAULT RELAY / GROUND FAULT PROTECTION SYSTEM + tag -> GFP scope_pending', () => {
    for (const raw of ['GROUND FAULT RELAY', 'GROUND FAULT PROTECTION SYSTEM']) {
      const r = runTakeoff(art([row({ raw, tag: 'G1' })]))
      expect((r.scopePendingLines ?? []).length).toBe(1)
      expect(r.dispositions[0]!.reasonCode).toBe('gfp_scope_pending')
    }
  })

  // #3 - a relay element stays relay; only an explicit standalone GFP device becomes GFP
  it('SEL-751 50G 51G (candidateKind relay) stays relay, not GFP', () => {
    const r = runTakeoff(art([row({ raw: 'SEL-751 50G 51G', tag: 'R-1', candidateKind: 'relay' })]))
    expect(noGfp(r)).toBe(true)
    expect((r.scopePendingLines ?? []).some((s) => s.line.signature.kind === 'relay')).toBe(true)
  })
  it('an UNCLASSIFIED dedicated GROUND FAULT RELAY row -> GFP', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT RELAY 64', tag: 'G2' }))
    expect(a.signature?.kind).toBe('gfp')
  })

  // #4 - bare ANSI / function text never counts
  it('bare 50G / 64 / function text -> not a GFP device (unrecognized)', () => {
    for (const raw of ['50G', '64', 'PERFORM GROUND FAULT TEST PER 7.14', 'GROUND FAULT PROTECTION']) {
      const a = assessApparatus(row({ raw, tag: undefined }))
      expect(a.signature, `raw=${raw}`).toBeNull()
    }
  })

  // parent exclusion overrides candidateKind - assert the INVARIANT (never GFP), not the downstream family
  it('candidateKind:gfp + 400AF/400AT -> NEVER a GFP line (parent exclusion wins)', () => {
    const r = runTakeoff(art([row({ raw: '400AF/400AT', tag: 'B-9', busVoltageV: 480, candidateKind: 'gfp' })]))
    expect(noGfp(r)).toBe(true)
  })
  it('candidateKind:gfp on an ATS (NON_BREAKER) row -> NEVER a GFP line', () => {
    const r = runTakeoff(art([row({ raw: 'ATS 800A GROUND FAULT PROTECTION', tag: 'ATS-1', candidateKind: 'gfp' })]))
    expect(noGfp(r)).toBe(true)
  })
})

describe('GFP quantify aggregation', () => {
  it('two standalone GFP devices (same block) aggregate to one line qty=2', () => {
    const r = runTakeoff(art([
      row({ raw: 'GROUND FAULT RELAY', tag: 'G1' }),
      row({ raw: 'GROUND FAULT RELAY', tag: 'G2' }),
    ]))
    const sp = (r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'gfp')
    expect(sp.length).toBe(1)
    expect(sp[0]!.qty).toBe(2)
  })
})
```

`test/gfp-cross-family.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import { matchRelay } from '../src/catalog/relay-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { GfpSignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const gfpSig: GfpSignature = {
  kind: 'gfp', voltageBasis: 'none', tag: 'G1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}

describe('GFP cross-family guards', () => {
  it('a GFP and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: 'GROUND FAULT RELAY', tag: 'X1' }),
      row({ raw: 'X1 800AF/600AT LSIG', tag: 'X1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'gfp').length).toBe(1)
    expect(r.matchedLines.length).toBe(1)   // the breaker
  })
  it('matchBreaker is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a BreakerSignature
      forced = matchBreaker(gfpSig)
    }).not.toThrow()
    expect(forced).toBeFalsy()
  })
  it('matchTransformer is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a TransformerSignature
      forced = matchTransformer(gfpSig)
    }).not.toThrow()
    expect(forced).toBeNull()
  })
  it('matchRelay is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a RelaySignature
      forced = matchRelay(gfpSig)
    }).not.toThrow()
    // matchRelay reads sig.role/ansiFunctions; a gfp sig has neither -> role 'unknown' -> group, no default.
    // The guard that matters: no THROW and a GFP signature never reaches matchRelay in the real pipeline
    // (the family-dispatch in emit routes kind==='gfp' to matchGfp). This forced call only proves no crash.
    expect(forced === null || typeof forced === 'object').toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to verify status**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-recognition gfp-cross-family`
Expected: most PASS against Task 3 code. Any FAIL reveals a real recognition gap.

- [ ] **Step 3: Fix only genuine gaps (fail-closed)**

If a pinned case fails, fix the minimal recognition logic in `src/signature/normalize.ts` (e.g. tighten `GFP_DEVICE`, adjust `looksLikeGfp` ordering). Do NOT relax any non-negotiable. Re-run until green.

- [ ] **Step 4: Run the full suite + typechecks**

Run: `pnpm --filter @apex/estimator-takeoff test` then both typechecks.
Expected: ALL pass; breaker/transformer/relay goldens unchanged.

- [ ] **Step 5: Commit**

```bash
git add packages/estimator-takeoff/test/gfp-recognition.test.ts packages/estimator-takeoff/test/gfp-cross-family.test.ts packages/estimator-takeoff/src
git commit -m "test(takeoff): GFP operator-pinned invariants + cross-family guards (Task 4)"
```

---

### Task 5: Real golden fixture (standalone GFP + breaker-LSIG + relay coexist)

**Files:**
- Create: `packages/estimator-takeoff/test/fixtures/gfp-mixed.extract.json`
- Test: `packages/estimator-takeoff/test/gfp-golden.test.ts`

**Interfaces:**
- Consumes: the full pipeline (T1-T4), `runFromArtifact`, `reconcile`/`renderReportText`, `buildNativeEnvelope`, `GFP_REF`.

- [ ] **Step 1: Write the fixture + failing test**

`test/fixtures/gfp-mixed.extract.json`:
```json
{
  "pdf": "gfp-mixed.pdf",
  "apparatus": [
    { "raw": "MSB-1 1600AF/1600AT LSIG DRAW-OUT", "tag": "MSB-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 480, "candidateKind": "breaker" },
    { "raw": "SEL-751 FEEDER PROTECTION RELAY", "tag": "R-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "candidateKind": "relay" },
    { "raw": "GROUND FAULT PROTECTION SYSTEM (NEC 230.95)", "tag": "GFP-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line" }
  ]
}
```

`test/gfp-golden.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import fixture from './fixtures/gfp-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { reconcile, renderReportText } from '../src/runner/report'
import { buildNativeEnvelope } from '@apex/estimator-core'
import { GFP_REF } from '../src/catalog/gfp-map.data'

describe('GFP family golden - breaker + relay + standalone GFP coexist', () => {
  const r = runTakeoff(fixture as any)

  it('breaker prices; relay + standalone GFP scope_pending; partial_preview', () => {
    expect(r.matchedLines.length).toBe(1)                        // MSB-1 breaker
    expect((r.scopePendingLines ?? []).length).toBe(2)          // R-1 + GFP-1
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-GFP', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)    // the breaker line priced
  })

  it('the embedded-GFP-stays-parent rule holds end-to-end: the LSIG breaker has NO gfp disposition', () => {
    expect(r.dispositions.every((d) => d.reasonCode !== 'gfp_scope_pending' || d.tag === 'GFP-1')).toBe(true)
    const msb = r.dispositions.find((d) => d.tag === 'MSB-1')!
    expect(msb.status).toBe('matched')
  })

  it('the standalone GFP -> scope_pending with the single ref as provisional default', () => {
    const sp = (r.scopePendingLines ?? []).find((s) => s.line.signature.kind === 'gfp')!
    expect(sp.candidateRefs).toEqual([GFP_REF])
    expect(sp.provisionalDefaultRef).toBe(GFP_REF)
    const report = reconcile(fixture as any, r, { bid_cents: 0 })
    expect(renderReportText(report)).toContain('provisional=Ground Fault Protection Device LV')
  })

  // Gate-2 STAND-IN: an operator-confirmed GFP device prices through estimator-core directly.
  // NOT a V1 auto-price path - GFP is never auto-priced (the engine only scope_pends it).
  it('Gate-2 STAND-IN: the confirmed GFP ref prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({
      projectNumber: 'PHX-GFP',
      scopes: [{ name: 'Block GFP', netaStandard: 'ATS', lines: [{ ref: GFP_REF, qty: 1 }] }],
    })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
```

- [ ] **Step 2: Run test to verify it fails (then passes)**

Run: `pnpm --filter @apex/estimator-takeoff test gfp-golden`
Expected: PASS if T1-T4 are correct (the fixture exercises the integrated pipeline). If the relay row count or breaker match differs, investigate (do NOT relax guards).

- [ ] **Step 3: Run the full suite + both typechecks (final gate)**

Run: `pnpm --filter @apex/estimator-takeoff test` then `pnpm --filter @apex/estimator-takeoff typecheck` then `pnpm --filter './apps/operations-web' typecheck`
Expected: ALL pass; breaker (`golden-e01-11`), transformer (`transformer-golden`), relay (`relay-golden`) goldens byte-identical/unchanged.

- [ ] **Step 4: Commit**

```bash
git add packages/estimator-takeoff/test/fixtures/gfp-mixed.extract.json packages/estimator-takeoff/test/gfp-golden.test.ts
git commit -m "test(takeoff): GFP family golden - standalone GFP + breaker + relay coexist (Task 5)"
```

---

## Self-Review

**Spec coverage:** Every spec Rev 2 contract item maps to a task - catalog (T1), signature+candidateKind+match (T2), recognition+union-wire+specKey+emit+codes (T3), the 6 operator-pinned recognition cases + cross-family + quantify (T4), real golden + Gate-2 stand-in + embedded-stays-parent-end-to-end (T5). The three non-negotiables are in Global Constraints and tested in T3/T4.

**Plan refinement of spec (flag to operator):** `looksLikeGfp` defers to an explicit non-gfp `candidateKind` (`if (x.candidateKind !== undefined) return false` after the `=== 'gfp'` check). This preserves producer authority (a `candidateKind:'relay'` row stays relay even with GFP wording) and mirrors the existing `looksLikeTransformer` deferral to `candidateKind:'relay'`. The dedicated-text -> GFP path therefore applies to UNCLASSIFIED rows (or `candidateKind:'gfp'`). If the operator wants dedicated GFP wording to OVERRIDE `candidateKind:'relay'`, drop that line and re-test #3.

**Type-forced safety:** widening `ApparatusSignature` (T3) forces the `gfp` branch in `specKey` AND the emit match loop (the `const tsig: TransformerSignature = sig` narrowing breaks otherwise), and the new `AssessmentCode` member forces the `ASSESS_TO_REASON` update - the same compiler-driven safety the relay lane relied on.

**Placeholder scan:** none - every step carries complete code.

**Type consistency:** `GfpSignature` (T2) -> union (T3); `matchGfp`/`GfpScopeMatch` (T2) used in emit (T3); `GFP_REF`/`GFP_R1_RATIFIED` (T1) used in T2/T3/T5; `isGfpParentShape` (T3) tested in T3+T4. `gfp_scope_pending` code added once (T3), used in emit + asserted in T3/T4/T5. No naming drift.
