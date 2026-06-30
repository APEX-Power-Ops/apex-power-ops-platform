# Instrument Transformer (CT / VT / CCVT) Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admit the INSTRUMENT TRANSFORMER family (CT / VT-PT / CCVT, NETA 7.10) into `packages/estimator-takeoff` as a scope-driven V1 slice - recognized device-first by instrument-type, routed BEFORE the power-transformer path, scope_pending (candidate ref-GROUP by type x voltage + Gate-2 packaging/count), never auto-priced - while the POWER-transformer family stays byte-identical.

**Architecture:** Reuse the transformer/relay/GFP scope_pending machinery. Add a fifth `kind: 'instrument_transformer'`, a device-first recognizer routed first in `assessCore`, an ADDITIVE instrument-token exclusion atop `looksLikeTransformer` (no kVA/coolant requirement), a type x voltage match group, parent/power conflict guards, and the packaging/count contract fields.

**Tech Stack:** TypeScript, Vitest, pnpm workspace. Host build over `ssh olares-mesh`. Lane worktree: `/home/olares/code/apex/apex-itx`, branch `estimator-takeoff/instrument-transformer-family-admission` (off main `fcbbe3c2`).

## Global Constraints

- **The recognition rules (operator-ratified, A-prime):**
  - Full device nouns (`CURRENT TRANSFORMER`/`POTENTIAL TRANSFORMER`/`VOLTAGE TRANSFORMER`/`CCVT`/`COUPLING-CAPACITOR`) recognize with ANY tag.
  - Bare abbreviations (`CT`/`PT`/`VT`) recognize ONLY when the TAG is instrument-shaped (`CT-1`, `PT-2`, `VT-A`, `CCVT-1`) OR `candidateKind:'instrument_transformer'`.
  - Bare abbreviation, no instrument-shaped tag -> NOT counted.
- **Power-transformer behavior PRESERVED.** The ONLY change to `looksLikeTransformer` is two additive early `return false` lines (explicit `candidateKind:'instrument_transformer'`; a full instrument device-noun token). NO kVA/coolant requirement. "Transformer T-1" (bare) must still -> `transformer_attrs_unparsed`.
- **Instrument routes FIRST** in `assessCore`. Conflict guards in `assessInstrumentTransformer` (checked BEFORE building a signature): a breaker/NON_BREAKER row -> `instrument_transformer_parent_conflict` (no instrument scope_pending - never suppress a real breaker); a kVA/coolant row -> `instrument_transformer_power_conflict`.
- **Never auto-price.** Every recognized instrument transformer -> `scope_pending` (candidate group + optional provisional default) or `catalog_gap`.
- **Provisional default ONLY with packaging evidence** (D2): `provisionalDefaultRef` is set only when `packagingEvidence !== 'none'`.
- **phaseCount + packagingEvidence are CONTRACT fields**: on `InstrumentTransformerSignature`, the `ScopePendingLine`, the `ApparatusDisposition` (scope_pending rows), and the reconciliation report.
- **Match by exact ref STRING, never section** (firm sections 7.1/7.6/7.14/7.15 are all drifted from canonical 7.10). No new refs, no new hours.
- **Voltage optional/contextual**: drives the candidate group when present; absent -> wider group + note, never `missing_voltage`.
- **ASCII-only** in all authored code/comments/strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **Breaker AND transformer AND relay AND GFP goldens byte-identical** after every task (`golden-e01-11`, `transformer-golden`, `relay-golden`, `gfp-golden`).
- **Gates (host, PATH-prefixed):** `export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH` then `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package; `--filter apex-operations-web` matches NOTHING - false-green trap).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **Commit identity** `jasonlswenson-sys <jasonlswenson@gmail.com>`; every commit ends `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Single writer per host worktree; edit via scp-down/local-Edit/scp-up; build + commit on host.
- **R1 PROVISIONAL** (`ITX_R1_RATIFIED=false`): the `ITX_GROUPS` defaults + the set/each counting convention await SME confirmation.

---

## File Structure

- Create: `src/catalog/instrument-transformer-map.data.ts` (T1), `src/catalog/instrument-transformer-map.ts` (T2).
- Modify: `src/signature/types.ts` (T2 interface; T3 union), `src/extraction/types.ts` + `src/extraction/parse.ts` (T2 candidateKind), `src/signature/normalize.ts` (T3), `src/quantify/quantify.ts` (T3), `src/emit/emit.ts` (T3), `src/buckets/types.ts` (T3), `src/runner/report.ts` (T3).
- Create tests: `test/itx-catalog.test.ts` (T1), `test/itx-map.test.ts` (T2), `test/normalize-itx.test.ts` + `test/itx-pipeline.test.ts` (T3), `test/itx-recognition.test.ts` + `test/itx-cross-family.test.ts` (T4), `test/fixtures/itx-mixed.extract.json` + `test/itx-golden.test.ts` (T5). Modify `test/parse.test.ts` (T2).

---

### Task 1: Catalog data + ITX_GROUPS + exact-ref/section-overload tests

**Files:** Create `packages/estimator-takeoff/src/catalog/instrument-transformer-map.data.ts`; Test `packages/estimator-takeoff/test/itx-catalog.test.ts`.

**Interfaces  -  Produces:** `ITX_REFS: string[]` (9), `ITX_GROUPS: Record<string,string[]>`, `ITX_R1_RATIFIED: boolean`.

- [ ] **Step 1: Write the failing test**  -  `test/itx-catalog.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { ITX_REFS, ITX_GROUPS, ITX_R1_RATIFIED } from '../src/catalog/instrument-transformer-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('instrument-transformer catalog authority', () => {
  it('all 9 instrument-transformer refs resolve verbatim in the live seed', () => {
    expect(ITX_REFS.length).toBe(9)
    for (const ref of ITX_REFS) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
  })
  it('every ITX_GROUPS member is one of ITX_REFS and resolves in the seed', () => {
    for (const group of Object.values(ITX_GROUPS)) for (const ref of group) {
      expect(ITX_REFS).toContain(ref)
      expect(REFS.has(ref)).toBe(true)
    }
  })
  it('section is OVERLOADED/DRIFTED: the 9 refs scatter across 7.1/7.6/7.14/7.15, NONE at canonical 7.10 -> match by STRING', () => {
    const secs = new Set(ITX_REFS.map((ref) => {
      const m = EQUIPMENT_MODELS_SEED.find((x: { ref: string }) => x.ref === ref) as { neta_section?: { ATS?: string | null } } | undefined
      return m?.neta_section?.ATS ?? null
    }))
    expect(secs.has('7.10')).toBe(false)                 // NONE at canonical 7.10
    expect(secs.size).toBeGreaterThan(1)                 // scattered
    for (const s of secs) expect(['7.1', '7.6', '7.14', '7.15']).toContain(s)
  })
  it.todo('R1: SME confirms ITX_GROUPS defaults + set/each convention -> flip ITX_R1_RATIFIED=true')
  it('R1 provisional', () => { expect(ITX_R1_RATIFIED).toBe(false) })
})
```

- [ ] **Step 2: Run to verify it fails**  -  `pnpm --filter @apex/estimator-takeoff test itx-catalog` -> FAIL (module missing).

- [ ] **Step 3: Implement**  -  `src/catalog/instrument-transformer-map.data.ts`:
```ts
// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED. Instrument transformers (CT/VT/CCVT, NETA 7.10).
// Matched by exact STRING ONLY: the firm neta_section for these scatters across 7.1/7.6/7.14/7.15 (NONE at
// canonical 7.10) and is overloaded with unrelated refs - section is NOISE here.
export const ITX_REFS = [
  'Current Transformer - Bushing HV/MV',
  'Current Transformer - Bushing, HV/MV (Set)',
  'Current Transformer LV - Set of 3',
  'Current Transformer MV - Set of 3',
  'Potential Transformer - MV',
  'Potential Transformer - MV Set',
  'Potential Transformer (set)',
  'CCVT Voltage Transformer - Individual',
  'CCVT Voltage Transformer - Set of 3',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: candidate ref-GROUP keyed by `${itxType}:${voltageClass|'unknown'}`.
// Individual + set variants are BOTH offered (the operator picks packaging at Gate-2). The Bushing HV/MV refs
// cover HV and MV CT. PT is MV-specific; there is NO priced LV/HV PT ref, so vt:LV / vt:HV are INTENTIONALLY
// EMPTY -> instrument_transformer_catalog_gap (a bounded V1 gap per spec R1). The generic "Potential Transformer
// (set)" is offered ONLY for vt:unknown (voltage absent -> wider group). CCVT is voltage-agnostic.
// CRITICAL: an EMPTY group ([]) is NOT the same as a MISSING key. matchInstrumentTransformer falls back to the
// `:unknown` group ONLY on a missing (undefined) key; an explicit [] yields null -> catalog_gap. Keep vt:LV / vt:HV
// present-and-empty so a KNOWN non-MV voltage fails closed instead of silently borrowing the vt:unknown set.
export const ITX_GROUPS: Record<string, string[]> = {
  'ct:LV': ['Current Transformer LV - Set of 3'],
  'ct:MV': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)', 'Current Transformer MV - Set of 3'],
  'ct:HV': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)'],
  'ct:unknown': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)', 'Current Transformer LV - Set of 3', 'Current Transformer MV - Set of 3'],
  'vt:MV': ['Potential Transformer - MV', 'Potential Transformer - MV Set'],
  'vt:LV': [],   // bounded catalog gap: no priced LV PT ref (spec R1) - present-and-empty -> catalog_gap, never vt:unknown fallback
  'vt:HV': [],   // bounded catalog gap: no priced HV PT ref (spec R1) - present-and-empty -> catalog_gap, never vt:unknown fallback
  'vt:unknown': ['Potential Transformer - MV', 'Potential Transformer - MV Set', 'Potential Transformer (set)'],
  'ccvt:LV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:MV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:HV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:unknown': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
}

// Operator flips when the SME confirms the type x voltage -> default-ref table + the set/each counting convention.
export const ITX_R1_RATIFIED = false
```

- [ ] **Step 4: Run to verify it passes**  -  `pnpm --filter @apex/estimator-takeoff test itx-catalog` -> PASS.
- [ ] **Step 5: Commit**  -  `feat(takeoff): instrument-transformer catalog authority - 9 refs + type x voltage groups (Task 1)`.

---

### Task 2: Signature interface + candidateKind widen + matchInstrumentTransformer

**Files:** Modify `src/signature/types.ts` (add interface; NOT the union), `src/extraction/types.ts` + `src/extraction/parse.ts`; Create `src/catalog/instrument-transformer-map.ts`; Test `test/itx-map.test.ts` + modify `test/parse.test.ts`.

**Interfaces  -  Consumes:** `ITX_REFS`/`ITX_GROUPS` (T1). **Produces:** `InstrumentTransformerSignature` (+ `ItxType`/`ItxPackaging`/`ItxPackagingEvidence`), `matchInstrumentTransformer(sig): ItxScopeMatch | null`, `ItxScopeMatch { group; defaultRef?; scopeQuestion }`.

- [ ] **Step 1: Write the failing tests**  -  `test/itx-map.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { matchInstrumentTransformer } from '../src/catalog/instrument-transformer-map'
import type { InstrumentTransformerSignature } from '../src/signature/types'

const sig = (o: Partial<InstrumentTransformerSignature> & { itxType: InstrumentTransformerSignature['itxType'] }): InstrumentTransformerSignature => ({
  kind: 'instrument_transformer', packaging: 'unknown', packagingEvidence: 'none', voltageBasis: 'none', tag: 'CT-1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' }, ...o,
})

describe('matchInstrumentTransformer', () => {
  it('CT + MV -> the MV CT candidate group', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV' }))!
    expect(m.group).toContain('Current Transformer MV - Set of 3')
    expect(m.group.length).toBeGreaterThan(1)
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('packaging evidence present -> provisional default set (a set variant)', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'set_of_3' }))!
    expect(m.defaultRef).toBe('Current Transformer MV - Set of 3')
  })
  it('NO packaging evidence -> NO provisional default (D2)', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'unknown', packagingEvidence: 'none' }))!
    expect(m.defaultRef).toBeUndefined()
  })
  it('absent voltage -> wider (unknown) group, no default without packaging', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'vt' }))!
    expect(m.group.length).toBeGreaterThanOrEqual(2)
    expect(m.defaultRef).toBeUndefined()
  })
  it('set_of_3 / three_phase ranks the EXPLICIT Set-of-3 ref above a broader bushing (Set)', () => {
    const a = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'set_of_3' }))!
    expect(a.defaultRef).toBe('Current Transformer MV - Set of 3')          // NOT 'Current Transformer - Bushing, HV/MV (Set)'
    const b = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'three_phase' }))!
    expect(b.defaultRef).toBe('Current Transformer MV - Set of 3')
  })
  it('LV/HV PT has NO priced home -> null (catalog_gap), never the generic "(set)" ref (bounded V1 gap)', () => {
    expect(matchInstrumentTransformer(sig({ itxType: 'vt', voltageClass: 'LV' }))).toBeNull()
    expect(matchInstrumentTransformer(sig({ itxType: 'vt', voltageClass: 'HV' }))).toBeNull()
  })
})
```
Append to `test/parse.test.ts` (mirror the existing relay/gfp candidateKind cases):
```ts
  it('accepts candidateKind:instrument_transformer', () => {
    const a = ok({ pdf: 'x.pdf', apparatus: [{ raw: 'CT-1 600:5', tag: 'CT-1', sheet: 'E1', page: 1, bbox: [0,0,1,1], evidence: 'one-line', candidateKind: 'instrument_transformer' }] })
    expect(a.apparatus[0]!.candidateKind).toBe('instrument_transformer')
  })
```

- [ ] **Step 2: Run to verify they fail**  -  `pnpm --filter @apex/estimator-takeoff test itx-map parse` -> FAIL.

- [ ] **Step 3: Implement.**
In `src/signature/types.ts`, add (after `GfpSignature`, BEFORE the `ApparatusSignature` alias - do NOT touch the union this task):
```ts
export type ItxType = 'ct' | 'vt' | 'ccvt'
export type ItxPackaging = 'individual' | 'set' | 'unknown'
export type ItxPackagingEvidence = 'set_token' | 'set_of_3' | 'three_phase' | 'symbol_group' | 'none'
export interface InstrumentTransformerSignature extends BaseSignature {
  kind: 'instrument_transformer'
  itxType: ItxType
  packaging: ItxPackaging
  packagingEvidence: ItxPackagingEvidence   // CONTRACT: why packaging was inferred (drives the Gate-2 default gate)
  phaseCount?: number                         // CONTRACT: observed phase/count evidence (e.g. 3)
  ratio?: string                              // evidence/display only (e.g. "600:5")
  // voltageClass stays optional (inherited): contextual; drives the group when present, never gates.
}
```
In `src/extraction/types.ts`: widen `candidateKind` to `... | 'gfp' | 'instrument_transformer'` (note: producer asserts an instrument transformer).
In `src/extraction/parse.ts`: widen the guard to accept `'instrument_transformer'`; update the expected-string message.
Create `src/catalog/instrument-transformer-map.ts`:
```ts
import type { InstrumentTransformerSignature, VoltageClass } from '../signature/types'
import { ITX_GROUPS } from './instrument-transformer-map.data'

export interface ItxScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select instrument-transformer packaging/count (individual vs 3-phase set) and confirm the priced ref; instrument transformers are priced per device or per set and are never auto-priced.'

// RANKED set selection. A "set" packaging prefers a set-variant ref; individual prefers a non-set ref. A KNOWN
// 3-phase set (set_of_3 / three_phase) must pick the EXPLICIT "Set of 3" ref, NOT merely the first set-named ref -
// e.g. ct:MV is ['...Bushing HV/MV', '...Bushing, HV/MV (Set)', '...MV - Set of 3'] and a naive `find(isSetRef)`
// returns the broad bushing "(Set)" at index 1, not the MV "Set of 3" the Gate-2 evidence implies. group[0] is the
// last-resort fallback so a default (when evidence exists) is never empty.
const matchesSetOf3 = (ref: string): boolean => /set\s+of\s+3/i.test(ref)
const matchesAnySet = (ref: string): boolean => /\bset\b/i.test(ref)

export function matchInstrumentTransformer(sig: InstrumentTransformerSignature): ItxScopeMatch | null {
  const vc: VoltageClass | 'unknown' = sig.voltageClass ?? 'unknown'
  const group = ITX_GROUPS[`${sig.itxType}:${vc}`] ?? ITX_GROUPS[`${sig.itxType}:unknown`]
  if (!group || group.length === 0) return null                     // no priced home (missing OR empty group) -> catalog_gap
  // D2: provisional default ONLY with explicit packaging evidence, ranked within the group.
  let defaultRef: string | undefined
  if (sig.packagingEvidence !== 'none') {
    if (sig.packaging === 'set') {
      defaultRef = (sig.packagingEvidence === 'set_of_3' || sig.packagingEvidence === 'three_phase')
        ? (group.find(matchesSetOf3) ?? group.find(matchesAnySet) ?? group[0])   // explicit Set of 3 wins
        : (group.find(matchesAnySet) ?? group[0])                                 // weaker set signal -> any set ref
    } else if (sig.packaging === 'individual') {
      defaultRef = group.find((r) => !matchesAnySet(r)) ?? group[0]               // individual -> a non-set ref
    } else {
      defaultRef = group[0]
    }
  }
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
```

- [ ] **Step 4: Run to verify pass + typecheck**  -  `pnpm --filter @apex/estimator-takeoff test itx-map parse` then `... typecheck` -> PASS/clean (union untouched).
- [ ] **Step 5: Commit**  -  `feat(takeoff): InstrumentTransformerSignature + candidateKind + matchInstrumentTransformer (Task 2)`.

---

### Task 3: Recognition + union wire (the integration task)

**Files:** Modify `src/signature/types.ts` (union), `src/signature/normalize.ts`, `src/quantify/quantify.ts`, `src/emit/emit.ts`, `src/buckets/types.ts`, `src/runner/report.ts`; Test `test/normalize-itx.test.ts` + `test/itx-pipeline.test.ts`.

**Why one task:** the union widen compiler-forces the `specKey` + emit branches together, and the emit branch is only exercisable once recognition produces signatures. Cohesive, end-to-end-testable deliverable.

- [ ] **Step 1: Write the failing tests**  -  `test/normalize-itx.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const itx = (a: ReturnType<typeof assessApparatus>) => (a.signature && a.signature.kind === 'instrument_transformer' ? a.signature : null)

describe('instrument-transformer recognition', () => {
  it('Current Transformer + tag -> instrument (itxType ct)', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_recognized')
    expect(itx(a)?.itxType).toBe('ct')
  })
  it('Potential / Voltage Transformer -> itxType vt', () => {
    expect(itx(assessApparatus(row({ raw: 'POTENTIAL TRANSFORMER', tag: 'PT-1' })))?.itxType).toBe('vt')
    expect(itx(assessApparatus(row({ raw: 'VOLTAGE TRANSFORMER', tag: 'VT-1' })))?.itxType).toBe('vt')
  })
  it('CCVT -> itxType ccvt (not vt)', () => {
    expect(itx(assessApparatus(row({ raw: 'CCVT', tag: 'CCVT-1' })))?.itxType).toBe('ccvt')
  })
  it('bare CT with instrument-shaped tag -> instrument (A-prime)', () => {
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'CT-1' })).assessmentCode).toBe('instrument_transformer_recognized')
  })
  it('bare CT in a non-instrument-tag row -> NOT instrument (A-prime)', () => {
    const a = assessApparatus(row({ raw: 'FEEDER WITH CT METERING', tag: 'F-1' }))
    expect(a.signature?.kind).not.toBe('instrument_transformer')
  })
  it('3-phase notation -> packagingEvidence three_phase + phaseCount 3', () => {
    const s = itx(assessApparatus(row({ raw: 'CURRENT TRANSFORMER (3) MV', tag: 'CT-1' })))
    expect(s?.packagingEvidence).toBe('three_phase'); expect(s?.phaseCount).toBe(3)
  })
  it('parent conflict: candidateKind itx + AF/AT -> parent_conflict, null sig', () => {
    const a = assessApparatus(row({ raw: '800AF/800AT LSIG', tag: 'MSB-1', candidateKind: 'instrument_transformer' }))
    expect(a.assessmentCode).toBe('instrument_transformer_parent_conflict')
    expect(a.signature).toBeNull()
  })
  it('power conflict: instrument noun + kVA -> power_conflict', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 500KVA', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_power_conflict')
  })
  it('type unparsed: instrument flagged (candidateKind) but no CT/PT/VT/CCVT token -> type_unparsed, null sig (no fabricated CT)', () => {
    const a = assessApparatus(row({ raw: '600:5', tag: 'X9', candidateKind: 'instrument_transformer' }))
    expect(a.assessmentCode).toBe('instrument_transformer_type_unparsed')
    expect(a.signature).toBeNull()
  })
  it('generic INSTRUMENT TRANSFORMER noun with no CT/PT/VT type -> type_unparsed (not a fabricated ct)', () => {
    const a = assessApparatus(row({ raw: 'INSTRUMENT TRANSFORMER', tag: 'IT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_type_unparsed')
    expect(a.signature).toBeNull()
  })
  it('a bare instrument transformer with no voltage never emits missing_voltage', () => {
    expect(assessApparatus(row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-1' })).assessmentCode).toBe('instrument_transformer_recognized')
  })
})

describe('power-transformer behavior PRESERVED (additive exclusion)', () => {
  it('Transformer T-1 500kVA dry-type -> power transformer (NOT instrument)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1 500KVA DRY-TYPE', tag: 'T-1', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
  it('Transformer T-1 (bare) -> transformer_attrs_unparsed (existing fail-closed behavior, unchanged)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1', tag: 'T-1', busVoltageV: 480 }))
    expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
  })
})
```
`test/itx-pipeline.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('instrument-transformer end-to-end', () => {
  it('CT set of 3 MV -> scope_pending with a provisional default + carried evidence', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER MV SET OF 3', tag: 'CT-1', busVoltageV: 4160 })]))
    expect(r.matchedLines).toHaveLength(0)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs.length).toBeGreaterThan(1)
    expect(sp.provisionalDefaultRef).toBe('Current Transformer MV - Set of 3')
    expect(sp.packagingEvidence).toBe('set_of_3')
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_scope_pending')
    expect(r.dispositions[0]!.packagingEvidence).toBe('set_of_3')
  })
  it('CT MV with NO packaging evidence -> scope_pending, no default', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-2', busVoltageV: 4160 })]))
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.provisionalDefaultRef).toBeUndefined()
  })
  it('LV PT (480V) has no priced home -> catalog_gap disposition, NO scope_pending (bounded V1 gap)', () => {
    const r = runTakeoff(art([row({ raw: 'POTENTIAL TRANSFORMER', tag: 'PT-9', busVoltageV: 480 })]))
    expect((r.scopePendingLines ?? []).length).toBe(0)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_catalog_gap')
  })
})
```

- [ ] **Step 2: Run to verify they fail**  -  `pnpm --filter @apex/estimator-takeoff test normalize-itx itx-pipeline` -> FAIL.

- [ ] **Step 3: Implement.**
(a) `src/signature/types.ts` union: `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature | InstrumentTransformerSignature`.
(b) `src/signature/normalize.ts`:
  - Add the type to the `./types` import: `... GfpSignature, InstrumentTransformerSignature, ItxPackaging, ItxPackagingEvidence, ItxType, ...`.
  - Add regexes (near the other device regexes):
```ts
const INSTRUMENT_TX_DEVICE = /\b(current\s+transformer|potential\s+transformer|voltage\s+transformer|coupling[\s-]?capacitor(\s+voltage\s+transformer)?|CCVT|instrument\s+transformer)\b/i
const INSTRUMENT_TX_ABBR = /\b(CT|PT|VT)\b/i
const INSTRUMENT_TAG = /^(CT|PT|VT|CCVT)[-_ ]?\w*$/i
```
  - Recognition + parsers + assessor:
```ts
function looksLikeInstrumentTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'instrument_transformer') return true
  if (INSTRUMENT_TX_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0) return true   // full noun + any tag
  if (INSTRUMENT_TX_ABBR.test(x.raw) && x.tag !== undefined && INSTRUMENT_TAG.test(x.tag)) return true  // bare abbr needs instrument-shaped tag (A-prime)
  return false
}

function parseItxType(raw: string, tag?: string): ItxType | undefined {
  if (/\b(CCVT|coupling[\s-]?capacitor)\b/i.test(raw) || (tag !== undefined && /^CCVT/i.test(tag))) return 'ccvt'
  if (/\b(potential\s+transformer|voltage\s+transformer|PT|VT)\b/i.test(raw) || (tag !== undefined && /^(PT|VT)/i.test(tag))) return 'vt'
  if (/\b(current\s+transformer|CT)\b/i.test(raw) || (tag !== undefined && /^CT/i.test(tag))) return 'ct'
  return undefined   // NO CT/PT/VT/CCVT type token (e.g. candidateKind-only row with an opaque tag/ratio) -> fail closed; NEVER fabricate 'ct'
}

function parsePackaging(raw: string): { packaging: ItxPackaging; packagingEvidence: ItxPackagingEvidence; phaseCount?: number } {
  if (/\bset\s+of\s+3\b/i.test(raw)) return { packaging: 'set', packagingEvidence: 'set_of_3', phaseCount: 3 }
  if (/\b3\s*(?:phase|ph|-phase)\b/i.test(raw) || /\b3\s*x\b/i.test(raw) || /\(3\)/.test(raw)) return { packaging: 'set', packagingEvidence: 'three_phase', phaseCount: 3 }
  if (/\bset\b/i.test(raw)) return { packaging: 'set', packagingEvidence: 'set_token' }
  return { packaging: 'unknown', packagingEvidence: 'none' }
}

function parseRatio(raw: string): string | undefined {
  const m = raw.match(/\b\d+\s*:\s*\d+\b/)
  return m ? m[0].replace(/\s+/g, '') : undefined
}

function assessInstrumentTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // Conflict guards FIRST (instrument routes before breaker/NON_BREAKER): a misrouted parent surfaces a
  // question, never a silent instrument scope_pending.
  if (looksLikeBreaker(x.raw) || NON_BREAKER.test(x.raw)) {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_parent_conflict',
      questions: [q(x, 'Label names an instrument transformer but the row is breaker/parent-shaped (frame/trip or a parent-device token) - confirm device type before counting.', 'instrument_transformer_parent_conflict')] }
  }
  if (KVA_RATING.test(x.raw) || parseCoolant(x.raw) !== 'unknown') {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_power_conflict',
      questions: [q(x, 'Label names an instrument transformer but carries a power-transformer signal (kVA/coolant) - confirm device type before counting.', 'instrument_transformer_power_conflict')] }
  }
  const itxType = parseItxType(x.raw, x.tag)
  if (itxType === undefined) {
    // Flagged as an instrument transformer (candidateKind or context) but no CT/PT/VT/CCVT type token -> fail closed.
    return { signature: null, isBreakerShaped: false, assessmentCode: 'instrument_transformer_type_unparsed',
      questions: [q(x, 'Row is flagged as an instrument transformer but names no CT/PT/VT/CCVT type - confirm the instrument-transformer type before counting.', 'instrument_transformer_type_unparsed')] }
  }
  const pk = parsePackaging(x.raw)
  const sig: InstrumentTransformerSignature = {
    kind: 'instrument_transformer', itxType,
    packaging: pk.packaging, packagingEvidence: pk.packagingEvidence, phaseCount: pk.phaseCount,
    ratio: parseRatio(x.raw),
    voltageClass: classifyVoltage(x.busVoltageV), voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag, source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'instrument_transformer_recognized', questions: [] }
}
```
  - `looksLikeTransformer` ADDITIVE exclusion (insert immediately after the `if (x.candidateKind === 'relay') return false` line):
```ts
  if (x.candidateKind === 'instrument_transformer') return false   // explicit instrument producer signal yields
  if (INSTRUMENT_TX_DEVICE.test(x.raw)) return false               // instrument device noun is NOT a power transformer (additive; no kVA/coolant requirement)
```
  - `assessCore`: insert the instrument route FIRST (before the `looksLikeTransformer` block):
```ts
  if (looksLikeInstrumentTransformer(x)) {
    return assessInstrumentTransformer(x, voltageBasis)
  }
```
  - `AssessmentCode` += `instrument_transformer_recognized`, `instrument_transformer_parent_conflict`, `instrument_transformer_power_conflict`, `instrument_transformer_type_unparsed`.
(c) `src/quantify/quantify.ts` specKey (before the transformer fall-through):
```ts
  if (s.kind === 'instrument_transformer') {
    return [s.kind, s.itxType, s.voltageClass ?? '-', s.packaging, s.source.block ?? '-'].join('|')   // phaseCount/ratio are evidence, not key
  }
```
(d) `src/buckets/types.ts`:
  - `OperatorQuestionCode` += `'instrument_transformer_scope_pending' | 'instrument_transformer_catalog_gap' | 'instrument_transformer_parent_conflict' | 'instrument_transformer_power_conflict' | 'instrument_transformer_type_unparsed'`.
  - `DispositionReasonCode` += the same five.
  - `TakeoffFinding.code` union += `'instrument_transformer_catalog_gap'`.
  - `ScopePendingLine` += `packagingEvidence?: string` + `phaseCount?: number`.
  - `ApparatusDisposition` += `packagingEvidence?: string` + `phaseCount?: number`.
(e) `src/emit/emit.ts`:
  - Imports: add `InstrumentTransformerSignature` to the `../signature/types` import; `import { matchInstrumentTransformer } from '../catalog/instrument-transformer-map'`; `import { ITX_R1_RATIFIED } from '../catalog/instrument-transformer-map.data'`.
  - `ASSESS_TO_REASON` += `instrument_transformer_recognized: 'instrument_transformer_scope_pending'`, `instrument_transformer_parent_conflict: 'instrument_transformer_parent_conflict'`, `instrument_transformer_power_conflict: 'instrument_transformer_power_conflict'`, `instrument_transformer_type_unparsed: 'instrument_transformer_type_unparsed'`.
  - Match-loop branch BEFORE the transformer fall-through:
```ts
    if (sig.kind === 'instrument_transformer') {
      const isig: InstrumentTransformerSignature = sig
      const scope = matchInstrumentTransformer(isig)
      if (scope) {
        scopePendingLines.push({
          candidateRefs: scope.group, provisionalDefaultRef: scope.defaultRef, r1Ratified: ITX_R1_RATIFIED,
          scopeQuestion: scope.scopeQuestion, qty: line.qty, block: isig.source.block ?? isig.source.sheet, line,
          packagingEvidence: isig.packagingEvidence, phaseCount: isig.phaseCount,
        })
        for (const i of line.memberIndices) {
          stamp(dispositions, i, 'scope_pending', 'instrument_transformer_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
          const disp = dispositions[i]!
          disp.candidateRefs = scope.group; disp.provisionalDefaultRef = scope.defaultRef; disp.scopeQuestion = scope.scopeQuestion
          disp.packagingEvidence = isig.packagingEvidence; disp.phaseCount = isig.phaseCount
        }
        questions.push({ question: scope.scopeQuestion, context: `${isig.tag ?? isig.source.sheet} (${isig.itxType}; candidate group: ${scope.group.join(' | ')})`, code: 'instrument_transformer_scope_pending' })
      } else {
        const reason = `recognized instrument transformer (${isig.itxType}, ${isig.voltageClass ?? 'unknown'}V) - no applicable priced ref-group`
        unmatchedCandidates.push({ reason, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'instrument_transformer_catalog_gap', reason, undefined, line.lineKey)
        findings.push({ code: 'instrument_transformer_catalog_gap', severity: 'warning', message: reason, context: isig.tag ?? isig.source.sheet })
        questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: isig.tag ?? isig.source.sheet, code: 'instrument_transformer_catalog_gap' })
      }
      continue
    }
```
(f) `src/runner/report.ts`: the `scopePending` projection gains `packagingEvidence: sp.packagingEvidence` + `phaseCount: sp.phaseCount`; add them to the `ReconciliationReport.scopePending[]` type; `renderReportText` appends `` + (sp.packagingEvidence ? ` packaging=${sp.packagingEvidence}` : '') + (sp.phaseCount ? ` phases=${sp.phaseCount}` : '')`` to the Gate-2 line.

- [ ] **Step 4: Run tests + typechecks**  -  `pnpm --filter @apex/estimator-takeoff test normalize-itx itx-pipeline`, then full `... test`, then `... typecheck`, then `pnpm --filter './apps/operations-web' typecheck`. Expected: new tests PASS; full suite PASS (all 4 goldens unchanged); both typechecks clean.
- [ ] **Step 5: Commit**  -  `feat(takeoff): wire instrument transformers into union + recognition pipeline (Task 3)`.

---

### Task 4: Operator must-pin invariants + cross-family guards

**Files:** Test `test/itx-recognition.test.ts`, `test/itx-cross-family.test.ts`. (Modify `normalize.ts` ONLY if a pinned case fails - fail-closed fixes.)

- [ ] **Step 1: Write the tests**  -  `test/itx-recognition.test.ts` (the 7 operator must-pin + the Rev-2.1 cases):
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { assessApparatus } from '../src/signature/normalize'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const noItx = (r: ReturnType<typeof runTakeoff>) =>
  r.dispositions.every((d) => d.reasonCode !== 'instrument_transformer_scope_pending') &&
  (r.scopePendingLines ?? []).every((s) => s.line.signature.kind !== 'instrument_transformer')

describe('operator must-pin: instrument vs power transformer', () => {
  it('#1 Current Transformer + tag -> instrument scope_pending', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' })]))
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_scope_pending')
  })
  it('#2 Potential / Voltage Transformer -> instrument', () => {
    for (const raw of ['POTENTIAL TRANSFORMER', 'VOLTAGE TRANSFORMER']) {
      const a = assessApparatus(row({ raw, tag: 'PT-1' }))
      expect(a.signature?.kind).toBe('instrument_transformer')
    }
  })
  it('#3 Transformer T-1 500kVA dry-type -> POWER transformer', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1 500KVA DRY-TYPE', tag: 'T-1', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
  it('#4 Transformer T-1 (bare) -> transformer_attrs_unparsed (unchanged behavior)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1', tag: 'T-1', busVoltageV: 480 }))
    expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
  })
  it('#5 bare CT without instrument-shaped tag -> NOT counted; CT-1 tag + candidateKind -> instrument', () => {
    expect(noItx(runTakeoff(art([row({ raw: 'FEEDER WITH CT METERING', tag: 'F-1' })])))).toBe(true)
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'CT-1' })).signature?.kind).toBe('instrument_transformer')
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'X9', candidateKind: 'instrument_transformer' })).signature?.kind).toBe('instrument_transformer')
  })
  it('#6 type+voltage, no packaging -> scope_pending, no default', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-1', busVoltageV: 4160 })]))
    expect((r.scopePendingLines ?? [])[0]!.provisionalDefaultRef).toBeUndefined()
  })
  it('parent conflict: candidateKind itx + AF/AT -> conflict, NO instrument line, breaker not suppressed', () => {
    const r = runTakeoff(art([row({ raw: '800AF/800AT LSIG DRAW-OUT', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'instrument_transformer' })]))
    expect(noItx(r)).toBe(true)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_parent_conflict')
  })
  it('power conflict: instrument noun + kVA -> power_conflict', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 500KVA', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_power_conflict')
  })
  it('phase/default-gate: (3) notation drives the default; no packaging -> no default', () => {
    const withPhase = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER (3) MV', tag: 'CT-1', busVoltageV: 4160 })]))
    expect((withPhase.scopePendingLines ?? [])[0]!.provisionalDefaultRef).toBeDefined()
    expect((withPhase.scopePendingLines ?? [])[0]!.phaseCount).toBe(3)
  })
  it('type unparsed: candidateKind itx + opaque ratio/tag (no type token) -> type_unparsed, NO instrument line', () => {
    const r = runTakeoff(art([row({ raw: '600:5', tag: 'X9', candidateKind: 'instrument_transformer' })]))
    expect(noItx(r)).toBe(true)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_type_unparsed')
  })
})
```
`test/itx-cross-family.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { InstrumentTransformerSignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const itxSig: InstrumentTransformerSignature = {
  kind: 'instrument_transformer', itxType: 'ct', packaging: 'unknown', packagingEvidence: 'none', voltageBasis: 'none', tag: 'CT-1',
  source: { sheet: 'E01', page: 1, bbox: [0,0,1,1], evidence: 'one-line' },
}

describe('instrument-transformer cross-family guards', () => {
  it('an instrument transformer and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' }),
      row({ raw: 'MSB-1 800AF/600AT LSIG', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'instrument_transformer').length).toBe(1)
    expect(r.matchedLines.length).toBe(1)
  })
  it('matchBreaker is type- AND runtime-defended against an instrument-transformer signature', () => {
    let forced: unknown
    // @ts-expect-error itx is not a BreakerSignature
    expect(() => { forced = matchBreaker(itxSig) }).not.toThrow()
    expect(forced).toBeFalsy()
  })
  it('matchTransformer is type- AND runtime-defended against an instrument-transformer signature', () => {
    let forced: unknown
    // @ts-expect-error itx is not a TransformerSignature
    expect(() => { forced = matchTransformer(itxSig) }).not.toThrow()
    expect(forced).toBeNull()
  })
})
```

- [ ] **Step 2: Run**  -  `pnpm --filter @apex/estimator-takeoff test itx-recognition itx-cross-family`. Most PASS against Task 3 code; a FAIL reveals a real gap.
- [ ] **Step 3: Fix only genuine gaps** in `normalize.ts` (fail-closed; do NOT relax a non-negotiable). Re-run.
- [ ] **Step 4: Full suite + both typechecks**  -  all pass; the 4 prior goldens unchanged.
- [ ] **Step 5: Commit**  -  `test(takeoff): instrument-transformer operator-pinned invariants + cross-family guards (Task 4)`.

---

### Task 5: Real golden + Gate-2 stand-in

**Files:** Create `test/fixtures/itx-mixed.extract.json`, `test/itx-golden.test.ts`.

- [ ] **Step 1: Fixture + failing test**  -  `test/fixtures/itx-mixed.extract.json`:
```json
{
  "pdf": "itx-mixed.pdf",
  "apparatus": [
    { "raw": "MSB-1 1600AF/1600AT LSIG DRAW-OUT", "tag": "MSB-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 480, "candidateKind": "breaker" },
    { "raw": "T-1 1500KVA 480V DRY-TYPE XFMR", "tag": "T-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 480 },
    { "raw": "CURRENT TRANSFORMER MV SET OF 3 600:5", "tag": "CT-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 4160 },
    { "raw": "POTENTIAL TRANSFORMER - MV", "tag": "PT-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 4160 }
  ]
}
```
`test/itx-golden.test.ts`:
```ts
import { describe, it, expect } from 'vitest'
import fixture from './fixtures/itx-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { reconcile, renderReportText } from '../src/runner/report'
import { buildNativeEnvelope } from '@apex/estimator-core'

describe('instrument-transformer golden - breaker + power transformer + CT + PT coexist', () => {
  const r = runTakeoff(fixture as any)
  it('breaker prices; power transformer + CT + PT scope_pending; partial_preview', () => {
    expect(r.matchedLines.length).toBe(1)                         // MSB-1
    expect((r.scopePendingLines ?? []).length).toBe(3)            // T-1 (power) + CT-1 + PT-1
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-ITX', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)
  })
  it('the power transformer stayed power (NOT instrument); CT/PT are instrument', () => {
    const sp = r.scopePendingLines ?? []
    expect(sp.some((s) => s.line.signature.kind === 'transformer')).toBe(true)
    expect(sp.filter((s) => s.line.signature.kind === 'instrument_transformer').length).toBe(2)
    const ct = sp.find((s) => s.line.signature.kind === 'instrument_transformer' && (s.line.signature as any).itxType === 'ct')!
    expect(ct.provisionalDefaultRef).toBe('Current Transformer MV - Set of 3')
    expect(renderReportText(reconcile(fixture as any, r, { bid_cents: 0 }))).toContain('packaging=set_of_3')
  })
  it('Gate-2 STAND-IN: a chosen instrument-transformer ref prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({ projectNumber: 'PHX-ITX', scopes: [{ name: 'Block ITX', netaStandard: 'ATS', lines: [{ ref: 'Current Transformer MV - Set of 3', qty: 1 }] }] })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
```

- [ ] **Step 2: Run**  -  `pnpm --filter @apex/estimator-takeoff test itx-golden` -> PASS if T1-T4 correct (do NOT relax guards on a surprise).
- [ ] **Step 3: Full suite + both typechecks (final gate)**  -  all pass; breaker/transformer/relay/GFP goldens byte-identical.
- [ ] **Step 4: Commit**  -  `test(takeoff): instrument-transformer family golden + Gate-2 stand-in (Task 5)`.

---

## Self-Review

**Spec coverage:** catalog+groups (T1) ;  signature+candidateKind+match (T2) ;  recognition+union-wire+power-exclusion+conflicts+specKey+emit+contract-fields+report (T3) ;  7 must-pin + Rev-2.1 cases + cross-family (T4) ;  real golden + power-stays-power + Gate-2 (T5). All Global Constraints tested.

**Type-forced safety:** the union widen (T3) forces the `gfp`-style branches in `specKey` AND emit (transformer narrowing breaks otherwise); the new `AssessmentCode` members force `ASSESS_TO_REASON`.

**Placeholder scan:** none  -  complete code in every step.

**Type consistency:** `InstrumentTransformerSignature`/`ItxType`/`ItxPackaging`/`ItxPackagingEvidence` (T2) -> union (T3); `matchInstrumentTransformer`/`ItxScopeMatch` (T2) used in emit (T3); `ITX_REFS`/`ITX_GROUPS`/`ITX_R1_RATIFIED` (T1) used in T2/T3; the FOUR `AssessmentCode` members (recognized, parent_conflict, power_conflict, type_unparsed) and the FIVE disposition/question codes (scope_pending, catalog_gap, parent_conflict, power_conflict, type_unparsed) added once (T3) and asserted in T3/T4/T5; `parseItxType` returns `ItxType | undefined` (T3) and the undefined branch is consumed by the type_unparsed guard; `packagingEvidence`/`phaseCount` added to `ScopePendingLine` + `ApparatusDisposition` + report (T3) and asserted end-to-end (T3/T4/T5). Power-exclusion is additive (no kVA/coolant requirement)  -  pinned by T3/T4 #3/#4.

**Plan-review patches (Codex/IRP, applied before SDD):**
- **P1 ranked set selector (T2):** `matchInstrumentTransformer` ranks within the candidate group - a `set_of_3`/`three_phase` signal picks the EXPLICIT "Set of 3" ref, not the first set-named ref (the broad bushing "(Set)" at index 1 of ct:MV). Pinned by `itx-map` ("set_of_3 / three_phase ranks the EXPLICIT Set-of-3 ref...") + the T3 pipeline + the T5 golden, which all assert `Current Transformer MV - Set of 3`.
- **P2 type-unparsed fail-closed (T3):** `parseItxType` no longer defaults to `ct`; a row flagged instrument with no CT/PT/VT/CCVT token -> `instrument_transformer_type_unparsed` (null signature, question, NO scope_pending), mirroring the parent/power conflict guards. Pinned by `normalize-itx` (candidateKind+opaque, generic INSTRUMENT TRANSFORMER) + the T4 disposition must-pin.
- **P3 LV/HV PT catalog-gap (T1):** `vt:LV` / `vt:HV` are present-and-EMPTY (`[]`) -> `catalog_gap`, NOT mapped to the generic "(set)" ref (a bounded V1 gap per spec R1). An empty group != a missing key (the `?? :unknown` fallback fires only on a MISSING key). Pinned by `itx-map` (LV/HV PT -> null) + the T3 pipeline catalog_gap test.
- **Minor abbr case (T3):** `INSTRUMENT_TX_ABBR` is `/i` (tags already are).
