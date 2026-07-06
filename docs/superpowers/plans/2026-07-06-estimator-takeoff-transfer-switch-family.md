# Automatic / Transfer Switch Family (V1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admit the 7th apparatus family (automatic / transfer switches, NETA 7.22.3) into `packages/estimator-takeoff` so a recognized, TAGGED transfer switch is counted per device and routed to a Gate-2 automation-class scope decision (never auto-priced), a main-tie-main breaker-pair SCHEME keeps its breakers as breakers, and all six prior families + tagless rows stay byte-identical except the intentional re-baseline of the TAGGED transfer rows.

**Architecture:** Reuse the switch/relay/GFP scope_pending machinery. Add a seventh signature `kind:'transfer_switch'`. **Do NOT edit `NON_BREAKER`** (an earlier design that removed ATS/MTS/STS from it regressed four other consumers - the GFP `isGfpParentShape` guard, the transformer kVA-fallback exclusion, the NON_BREAKER tail, and the breaker-fallback guard). Instead route a device-first transfer recognizer BETWEEN `looksLikeSwitch` (normalize.ts:485) and the `NON_BREAKER` catch (normalize.ts:489) so a TAGGED transfer row is claimed before the tail; short-circuit `candidateKind:'transfer_switch'` at the top of `assessCore`; and give the H3 conflict guard a transfer-LOCAL predicate (`NON_BREAKER` minus ATS/MTS/STS) so a plain `ATS` never self-conflicts. Per the operator T1-B ruling, a bare `AF/AT` on a transfer-anchored row is RATING EVIDENCE (scope_pending), not a conflict.

**Tech Stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- ASCII-only in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- **`NON_BREAKER` (normalize.ts:8) and `SWITCH_EXCLUDE` (normalize.ts:25) are NOT edited.** No existing token regex is modified. This preserves the four NON_BREAKER consumers (GFP `isGfpParentShape` :231; transformer kVA-fallback :106; the NON_BREAKER tail :489; the breaker-fallback guard :500). Verify by grepping `NON_BREAKER` before and after: only NEW references (in `assessTransferSwitch` via `TRANSFER_CONFLICT_NONBREAKER`) are added.
- **Byte-identical after every task EXCEPT the D4 re-baseline of TAGGED transfer rows.** Breaker + transformer + relay + GFP + instrument + switch goldens byte-identical; ALL tagless `ATS`/`MTS`/`STS` rows byte-identical; ALL `UPS`/`PDU`/... rows byte-identical. The ONLY permitted deltas (Task 5): the TAGGED `ATS`/`MTS`/`STS` disposition assertions + the `E01-11` `STS-*` rows + the SKILL.md worked-example narrative.
- No new catalog refs, no new hours. V1 uses the 3 existing priced transfer refs only, matched by EXACT ref STRING (never by section; firm `7.18` is shared by the `(Functional Testing)` transfer ref AND the DC-Battery/DC-Charger refs).
- **The 3 verbatim seed refs (V1 mapped):** `Automatic Transfer Switch - (IR/DLRO)`; `Automatic Transfer Switch - Iso Bypass (IR/DLRO)`; `Manual Transfer Switch - (IR/DLRO)`. (`Automatic Transfer Switch (Functional Testing)` is NOT routed in V1; `Infrared Scan - ATS` is not a device ref.)
- Transfer switches never auto-price: every recognized transfer device -> `scope_pending` (candidate group + optional default) or `transfer_catalog_gap`. No "matched" transfer line in V1.
- Recognition is device-first (transfer anchor) + a TAG, NEVER a bare "switch". A tagless transfer-anchored row is NOT claimed (it falls to the NON_BREAKER tail, byte-identical).
- **T1-B conflict guard (operator-ratified 2026-07-06):** `transfer_parent_conflict` fires ONLY on a trip-function (`LSI`/`LSIG`), an unambiguous breaker hint (`MCB|MCCB|ACB|VCB|breaker|draw-out|GB|FB`), or a `TRANSFER_CONFLICT_NONBREAKER` token (`PDU|UPS|SPD|PQM|METER|BUS DUCT`). A bare `AF/AT` (lone token OR full pair) with none of those -> RATING EVIDENCE (`ampRating`) -> scope_pending. `FRAME_TRIP`/`TRANSFER_FRAME_TRIP` are NOT conflict signals.
- `TRANSFER_R1_RATIFIED = false` (provisional, fail-closed; never auto-priced).
- Gates (host): `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green gate).
- Build discipline: host worktree `/home/olares/code/apex/apex-estimator-ats` (branch `estimator-takeoff/transfer-switch-family-admission`); edit via scp-down/local-Edit/scp-up; `export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH`; commit trailer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`; merge OPERATOR-GATED (admin-rebase PR).
- TDD: write the failing test, watch it fail for the right reason, implement minimal, watch it pass, commit. Cross-engine (Codex) IRP before merge.

**Task ordering rationale (the discriminated-union coupling):** `TransferSwitchSignature` is defined as a standalone interface in Task 1 but is NOT added to the `ApparatusSignature` union until Task 3. Widening the union breaks `quantify.specKey` (its transformer fall-through) and `emit.ts` (`const tsig: TransformerSignature = sig`), so the union widening + the `quantify`/`emit` transfer branches + the `buckets` codes MUST land together in Task 3 to keep the build green at every commit. Task 1 (catalog) and Task 2 (recognition predicates) are pure additions that compile green without touching the union. Task 3 also wires `assessCore`; the byte-identical re-baseline of the tagged transfer rows is deferred to Task 5 (documented before/after).

---

### Task 1: Catalog - the 3 refs, TRANSFER_GROUPS, matchTransferSwitch

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts` (add the `TransferAutomationClass` type + the `TransferSwitchSignature` interface; do NOT touch the `ApparatusSignature` union yet)
- Create: `packages/estimator-takeoff/src/catalog/transfer-switch-map.data.ts`
- Create: `packages/estimator-takeoff/src/catalog/transfer-switch-map.ts`
- Test: `packages/estimator-takeoff/test/transfer-map.test.ts`

**Interfaces:**
- Consumes: `VoltageClass`, `BaseSignature` from `signature/types`.
- Produces: `TransferAutomationClass`, `TransferSwitchSignature` (interface, not yet in the union); `TRANSFER_REFS`, `TRANSFER_GROUPS`, `TRANSFER_R1_RATIFIED` from `catalog/transfer-switch-map.data`; `TransferScopeMatch`, `matchTransferSwitch(sig: TransferSwitchSignature): TransferScopeMatch | null` from `catalog/transfer-switch-map`.

- [ ] **Step 1: Add the types to `signature/types.ts`** (after the `SwitchSignature` block, before the `ApparatusSignature` union line). Do NOT add to the union yet.

```ts
export type TransferAutomationClass = 'automatic' | 'manual' | 'static' | 'unknown'
export interface TransferSwitchSignature extends BaseSignature {
  kind: 'transfer_switch'
  automationClass: TransferAutomationClass
  bypassIsolation?: boolean   // 'iso'/'bypass' present -> picks the Iso-Bypass ref
  ampRating?: number          // evidence/display only (continuous A OR the AF/AT frame value; T1-B)
  // voltageClass stays optional (inherited): contextual; never gates.
}
```

- [ ] **Step 2: Write the failing test `test/transfer-map.test.ts`** (matchTransferSwitch: automatic default IR/DLRO, automatic+bypass -> Iso-Bypass, manual default, unknown -> group no default, static -> null gap, manual+bypass -> null gap, exact-ref verbatim + 7.18 overload).

```ts
import { describe, it, expect } from 'vitest'
import { matchTransferSwitch, TransferScopeMatch } from '../src/catalog/transfer-switch-map'
import { TRANSFER_REFS } from '../src/catalog/transfer-switch-map.data'
import type { TransferSwitchSignature } from '../src/signature/types'
import seed from '../../estimator-core/src/catalog/equipment-models.seed.json'

const sig = (o: Partial<TransferSwitchSignature>): TransferSwitchSignature => ({
  kind: 'transfer_switch', automationClass: 'automatic', source: { block: null }, ...o,
} as TransferSwitchSignature)

describe('matchTransferSwitch', () => {
  it('automatic -> default base IR/DLRO ref, group of 2', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'automatic' })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Automatic Transfer Switch - (IR/DLRO)')
    expect(m.group).toContain('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')
  })
  it('automatic + bypass -> Iso-Bypass default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'automatic', bypassIsolation: true })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')
  })
  it('manual -> Manual default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'manual' })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Manual Transfer Switch - (IR/DLRO)')
  })
  it('unknown -> group [auto base, manual base], NO default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'unknown' })) as TransferScopeMatch
    expect(m.defaultRef).toBeUndefined()
    expect(m.group).toEqual(['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)'])
  })
  it('static -> null (catalog gap)', () => {
    expect(matchTransferSwitch(sig({ automationClass: 'static' }))).toBeNull()
  })
  it('manual + bypass -> null (no manual-iso-bypass ref; D6)', () => {
    expect(matchTransferSwitch(sig({ automationClass: 'manual', bypassIsolation: true }))).toBeNull()
  })
  it('never routes to the Functional-Testing ref in V1', () => {
    for (const ac of ['automatic', 'manual', 'unknown'] as const) {
      const m = matchTransferSwitch(sig({ automationClass: ac }))
      const refs = m ? [...m.group, m.defaultRef] : []
      expect(refs).not.toContain('Automatic Transfer Switch (Functional Testing)')
    }
  })
  it('the 3 V1 refs resolve verbatim in the live seed', () => {
    const names = new Set((seed as any[]).map((r) => r.ref))
    for (const r of TRANSFER_REFS) expect(names.has(r)).toBe(true)
  })
  it('7.18 overload: the Functional-Testing transfer ref + DC-Battery + DC-Charger all sit at firm 7.18 -> match by STRING', () => {
    const at718 = (seed as any[]).filter((r) => r.neta_section?.ATS === '7.18').map((r) => r.ref)
    expect(at718).toContain('Automatic Transfer Switch (Functional Testing)')
    expect(at718.some((r: string) => /Direct-Current Systems - Batteries/.test(r))).toBe(true)
    expect(at718.some((r: string) => /Direct-Current Systems - Chargers/.test(r))).toBe(true)
  })
})
```

- [ ] **Step 3: Run it; expect FAIL** (`transfer-switch-map` does not exist).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-estimator-ats && pnpm --filter @apex/estimator-takeoff test -- transfer-map'`
Expected: FAIL (module not found).

- [ ] **Step 4: Implement `catalog/transfer-switch-map.data.ts`.**

```ts
export const TRANSFER_REFS = [
  'Automatic Transfer Switch - (IR/DLRO)',
  'Automatic Transfer Switch - Iso Bypass (IR/DLRO)',
  'Manual Transfer Switch - (IR/DLRO)',
] as const

// R1 PROVISIONAL until the estimating authority confirms (TRANSFER_R1_RATIFIED=false).
export const TRANSFER_GROUPS: Record<'automatic' | 'manual' | 'unknown', string[]> = {
  automatic: ['Automatic Transfer Switch - (IR/DLRO)', 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)'],
  manual: ['Manual Transfer Switch - (IR/DLRO)'],
  unknown: ['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)'],
  // ABSENT (deliberate gaps): 'static'; manual+bypassIsolation; MV transfer
}
export const TRANSFER_R1_RATIFIED = false
```

- [ ] **Step 5: Implement `catalog/transfer-switch-map.ts`.**

```ts
import type { TransferSwitchSignature } from '../signature/types'
import { TRANSFER_GROUPS } from './transfer-switch-map.data'

export interface TransferScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }
const SCOPE_Q =
  'Confirm the transfer-switch ref (automatic vs manual; base vs iso-bypass; IR/DLRO scope) at Gate-2.'

export function matchTransferSwitch(sig: TransferSwitchSignature): TransferScopeMatch | null {
  if (sig.automationClass === 'static') return null                                   // D5 gap (FIRST)
  if (sig.automationClass === 'manual' && sig.bypassIsolation === true) return null    // D6 gap
  const key = sig.automationClass === 'unknown' ? 'unknown' : sig.automationClass
  const group = TRANSFER_GROUPS[key as 'automatic' | 'manual' | 'unknown']
  if (!group || group.length === 0) return null
  let defaultRef: string | undefined
  if (sig.automationClass === 'automatic') {
    defaultRef = sig.bypassIsolation === true
      ? 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)'
      : 'Automatic Transfer Switch - (IR/DLRO)'
  } else if (sig.automationClass === 'manual') {
    defaultRef = 'Manual Transfer Switch - (IR/DLRO)'
  } // 'unknown' -> no default (D2)
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
```

- [ ] **Step 6: Run it; expect PASS. Commit.**

Run: `... pnpm --filter @apex/estimator-takeoff test -- transfer-map && pnpm --filter @apex/estimator-takeoff typecheck`
Expected: PASS. Then:
```bash
git add packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/catalog/transfer-switch-map.data.ts packages/estimator-takeoff/src/catalog/transfer-switch-map.ts packages/estimator-takeoff/test/transfer-map.test.ts
git commit -m "feat(transfer): catalog - 3 V1 refs + matchTransferSwitch + gaps (Task 1)"
```

---

### Task 2: Recognition predicates - regexes, looksLikeTransferSwitch, parse functions

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts` (add the transfer regexes + `looksLikeTransferSwitch` + `parseAutomationClass` + `parseBypassIsolation` + `parseTransferAmp`; do NOT wire `assessCore` yet)
- Test: `packages/estimator-takeoff/test/normalize-transfer.test.ts`

**Interfaces:**
- Consumes: `ExtractedApparatus` from `extraction/types`.
- Produces: `looksLikeTransferSwitch`, `parseAutomationClass`, `parseBypassIsolation`, `parseTransferAmp` (exported for the test + Task 3's assessor).

- [ ] **Step 1: Write the failing test `test/normalize-transfer.test.ts`.**

```ts
import { describe, it, expect } from 'vitest'
import { looksLikeTransferSwitch, parseAutomationClass, parseBypassIsolation, parseTransferAmp } from '../src/signature/normalize'

const mk = (raw: string, tag?: string, candidateKind?: any) =>
  ({ raw, tag, sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', candidateKind } as any)

describe('looksLikeTransferSwitch', () => {
  it('claims tagged ATS/MTS/STS/transfer-switch', () => {
    for (const r of ['ATS', 'MTS', 'STS', 'Automatic Transfer Switch', 'Transfer Switch'])
      expect(looksLikeTransferSwitch(mk(r, 'X'))).toBe(true)
  })
  it('requires a tag (tagless -> false, stays on the NON_BREAKER tail)', () => {
    expect(looksLikeTransferSwitch(mk('ATS 800AF/800AT'))).toBe(false)
  })
  it('candidateKind:transfer_switch wins; other producer kinds defer', () => {
    expect(looksLikeTransferSwitch(mk('anything', 'X', 'transfer_switch'))).toBe(true)
    expect(looksLikeTransferSwitch(mk('ATS', 'X', 'breaker'))).toBe(false)
  })
  it('a bare "switch" is NOT a transfer anchor', () => {
    expect(looksLikeTransferSwitch(mk('Switch', 'X'))).toBe(false)
  })
})
describe('parse', () => {
  it('automation class', () => {
    expect(parseAutomationClass('ATS-1')).toBe('automatic')
    expect(parseAutomationClass('MTS-2')).toBe('manual')
    expect(parseAutomationClass('STS-1 static')).toBe('static')
    expect(parseAutomationClass('Transfer Switch')).toBe('unknown')
  })
  it('bypass isolation', () => {
    expect(parseBypassIsolation('ATS-1 Iso Bypass')).toBe(true)
    expect(parseBypassIsolation('ATS-1')).toBeUndefined()
  })
  it('amp evidence: plain amps OR the AF/AT frame value (T1-B)', () => {
    expect(parseTransferAmp('ATS-1 800A')).toBe(800)
    expect(parseTransferAmp('ATS-1 800AF/800AT')).toBe(800)
    expect(parseTransferAmp('ATS-1')).toBeUndefined()
  })
})
```

- [ ] **Step 2: Run it; expect FAIL** (functions not exported). Run: `... test -- normalize-transfer`.

- [ ] **Step 3: Implement in `normalize.ts`** (add near the switch regexes; do NOT touch `NON_BREAKER`/`SWITCH_EXCLUDE`).

```ts
const TRANSFER_DEVICE = /\b(automatic\s+transfer\s+switch|manual\s+transfer\s+switch|transfer\s+switch|ATS|MTS|STS)\b/i
// NON_BREAKER MINUS the transfer tokens - used ONLY in the transfer conflict guard so a plain ATS/MTS/STS does not self-conflict:
const TRANSFER_CONFLICT_NONBREAKER = /\b(PDU|UPS|SPD|PQM|METER|BUS\s*DUCT)\b/i
const TRANSFER_BYPASS = /\b(iso(lation)?[\s-]?bypass|bypass[\s-]?iso(lation)?|\biso\b|\bbypass\b)\b/i
const TRANSFER_TRIP_FN = /\bL(?=[SIGE]{2})(S?)(I?)(G?)(E?)\b/i           // LSI/LSIG (reuse switch shape)
const TRANSFER_BREAKER_CONFLICT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i
const TRANSFER_FRAME = /\b(\d{2,6})\s*A[FT]\b/i                          // frame/trip amp value (evidence, T1-B)
const TRANSFER_PLAIN_AMP = /(?<!\d)(\d{2,6})\s*A\b/i

export function looksLikeTransferSwitch(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'transfer_switch') return true
  if (x.candidateKind !== undefined && x.candidateKind !== 'transfer_switch') return false
  return TRANSFER_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}
export function parseAutomationClass(raw: string): 'automatic' | 'manual' | 'static' | 'unknown' {
  if (/\bautomatic\s+transfer\s+switch\b|\bATS\b/i.test(raw)) return 'automatic'
  if (/\bmanual\s+transfer\s+switch\b|\bMTS\b/i.test(raw)) return 'manual'
  if (/\bstatic\b|\bsolid[\s-]?state\b|\bSTS\b/i.test(raw)) return 'static'
  return 'unknown'
}
export function parseBypassIsolation(raw: string): boolean | undefined {
  return TRANSFER_BYPASS.test(raw) ? true : undefined
}
export function parseTransferAmp(raw: string): number | undefined {
  const p = TRANSFER_PLAIN_AMP.exec(raw); if (p) return parseInt(p[1], 10)
  const f = TRANSFER_FRAME.exec(raw); if (f) return parseInt(f[1], 10)
  return undefined
}
// Exposed for Task 3's assessor:
export const _transferGuards = { TRANSFER_TRIP_FN, TRANSFER_BREAKER_CONFLICT, TRANSFER_CONFLICT_NONBREAKER }
```
Note the precedence in `parseAutomationClass`: `automatic` (`ATS`) and `manual` (`MTS`) are checked before `static` so a plain `ATS`/`MTS` never falls to `static`; `STS`/`static`/`solid-state` -> `static`.

- [ ] **Step 4: Run it; expect PASS. Commit.**
```bash
git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/normalize-transfer.test.ts
git commit -m "feat(transfer): recognition predicates + parse (Task 2)"
```

---

### Task 3: Assessor + union widening + pipeline wiring (the coupled core)

**Files (all land together to keep the build green):**
- Modify: `packages/estimator-takeoff/src/extraction/types.ts` (candidateKind), `extraction/parse.ts` (validator)
- Modify: `signature/types.ts` (widen `ApparatusSignature`)
- Modify: `signature/normalize.ts` (`assessTransferSwitch` + `assessCore` routing + `AssessmentCode`)
- Modify: `quantify/quantify.ts` (`specKey` branch + `pickAuthoritative`)
- Modify: `buckets/types.ts` (code unions)
- Modify: `emit/emit.ts` (transfer branch + `ASSESS_TO_REASON`)
- Test: `test/transfer-assess.test.ts`, `test/quantify-transfer.test.ts`

**Interfaces:**
- Consumes: Task 1 (`matchTransferSwitch`, `TRANSFER_R1_RATIFIED`, `TransferSwitchSignature`) + Task 2 (predicates/parse/`_transferGuards`).
- Produces: `assessTransferSwitch`; the widened union; `transfer_recognized`/`transfer_parent_conflict` assessment codes; `transfer_scope_pending`/`transfer_catalog_gap`/`transfer_parent_conflict` disposition/question codes.

- [ ] **Step 1: Write the failing tests** `test/transfer-assess.test.ts` (the T1-B guard + routing) + `test/quantify-transfer.test.ts` (specKey + pickAuthoritative). Assert:
  - `ATS-1` (tagged) -> `assessmentCode 'transfer_recognized'`, `automationClass 'automatic'`.
  - `ATS-1 800AF/800AT` (bare AF/AT, no LSIG/hint, tagged) -> `transfer_recognized` (NOT conflict), `ampRating 800` (T1-B).
  - `ATS-1 800AF/800AT LSIG` -> `transfer_parent_conflict`, signature null.
  - `ATS-1 VCB` -> `transfer_parent_conflict`; `ATS-1 UPS` (co-located) -> `transfer_parent_conflict`.
  - `STS-1` clean AND `STS-1 800AF/800AT` (no LSIG) -> `transfer_recognized` (static) -> [Task 4 emit turns this into a gap]; `STS-1 800AF/800AT LSIG` -> conflict.
  - `candidateKind:'transfer_switch'` on a raw containing `SEL-751 relay` -> `transfer_recognized` (top-of-assessCore short-circuit beats `looksLikeRelay`).
  - `specKey` for two same-tag automatic-base transfers aggregates; a `transfer_switch` deviceId is kind-prefixed.

```ts
// test/transfer-assess.test.ts (excerpt)
import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
const at = (raw: string, tag = 'X', kind?: any, v?: number) =>
  assessApparatus({ raw, tag, sheet: 'E', page: 1, bbox: [0,0,1,1], evidence: 'one-line', candidateKind: kind, busVoltageV: v } as any)
describe('assessTransferSwitch T1-B', () => {
  it('bare AF/AT is rating evidence, not a conflict', () => {
    const a = at('ATS-1 800AF/800AT')
    expect(a.assessmentCode).toBe('transfer_recognized')
    expect((a.signature as any).ampRating).toBe(800)
  })
  it('LSIG on a transfer row -> conflict', () => {
    expect(at('ATS-1 800AF/800AT LSIG').assessmentCode).toBe('transfer_parent_conflict')
  })
  it('co-located UPS -> conflict', () => { expect(at('ATS-1 UPS').assessmentCode).toBe('transfer_parent_conflict') })
  it('candidateKind hard-win beats relay wording', () => {
    expect(at('ATS-1 SEL-751', 'X', 'transfer_switch').assessmentCode).toBe('transfer_recognized')
  })
})
```

- [ ] **Step 2: Run; expect FAIL** (assessor + union not present). Run: `... test -- transfer-assess quantify-transfer`.

- [ ] **Step 3: Implement (all together).**
  1. `extraction/types.ts:15`: widen `candidateKind` to `... | 'transfer_switch'`. `extraction/parse.ts:58`: accept `'transfer_switch'` + update the message.
  2. `signature/types.ts:91`: `export type ApparatusSignature = ... | SwitchSignature | TransferSwitchSignature`.
  3. `signature/normalize.ts`: add the assessor + new `AssessmentCode` members `'transfer_recognized' | 'transfer_parent_conflict'`:
     ```ts
     function assessTransferSwitch(x: ExtractedApparatus, voltageBasis?: number): ApparatusAssessment {
       const { TRANSFER_TRIP_FN, TRANSFER_BREAKER_CONFLICT, TRANSFER_CONFLICT_NONBREAKER } = _transferGuards
       if (TRANSFER_TRIP_FN.test(x.raw) || TRANSFER_BREAKER_CONFLICT.test(x.raw) || TRANSFER_CONFLICT_NONBREAKER.test(x.raw)) {
         return { assessmentCode: 'transfer_parent_conflict', signature: null,
           question: 'Transfer-anchored row carries a breaker/trip or a co-located non-transfer device signal; confirm whether it is a transfer switch or a breaker/parent.' }
       }
       const sig: TransferSwitchSignature = {
         kind: 'transfer_switch',
         automationClass: parseAutomationClass(x.raw),
         bypassIsolation: parseBypassIsolation(x.raw),
         ampRating: parseTransferAmp(x.raw),
         voltageClass: classifyVoltage(x.busVoltageV ?? voltageBasis),
         source: { block: x.block ?? null }, tag: x.tag,
       }
       return { assessmentCode: 'transfer_recognized', signature: sig }
     }
     ```
     `assessCore`: (i) at the TOP add `if (x.candidateKind === 'transfer_switch') return assessTransferSwitch(x, voltageBasis)`; (ii) AFTER the `looksLikeSwitch` block (normalize.ts:485) and BEFORE the `NON_BREAKER` catch (normalize.ts:489) add `if (looksLikeTransferSwitch(x)) return assessTransferSwitch(x, voltageBasis)`. Do NOT edit `NON_BREAKER`, `isGfpParentShape`, `looksLikeTransformer`, or the tail.
  4. `quantify/quantify.ts` `specKey`: BEFORE the transformer fall-through add
     ```ts
     if (s.kind === 'transfer_switch')
       return [s.kind, s.automationClass, s.bypassIsolation ? 'BYP' : '-', s.voltageClass ?? '-', s.source.block ?? '-'].join('|')
     ```
     and in `pickAuthoritative` add a `richTransfer = auths.find((o) => o.kind === 'transfer_switch' && (o.automationClass !== 'unknown' || o.bypassIsolation !== undefined))` preference (return it when present).
  5. `buckets/types.ts`: `OperatorQuestionCode` += `'transfer_scope_pending' | 'transfer_catalog_gap' | 'transfer_parent_conflict'`; `DispositionReasonCode` += the same three; `TakeoffFinding.code` += `'transfer_catalog_gap'`; add `automationClass?: string` + `bypassIsolation?: boolean` to `ScopePendingLine` + `ApparatusDisposition`.
  6. `emit/emit.ts`: import `matchTransferSwitch` + `TRANSFER_R1_RATIFIED` + `TransferSwitchSignature`; add a `sig.kind === 'transfer_switch'` branch BEFORE the transformer fall-through (with `continue`): a scope match -> `scope_pending` (candidateRefs=group, provisionalDefaultRef, r1Ratified=TRANSFER_R1_RATIFIED, automationClass, bypassIsolation, scopeQuestion) + stamp the evidence on each member; a `null` match -> `transfer_catalog_gap` finding (warning) + `unmatched` disposition + question. Update `ASSESS_TO_REASON`: `transfer_recognized -> transfer_scope_pending`, `transfer_parent_conflict -> transfer_parent_conflict`.

- [ ] **Step 4: Run the FULL suite + typechecks; expect PASS (build green at this commit). Commit.**

Run (NO `| tail`): `... pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck`
Expected: green. **Any assertion that goes RED is a TAGGED-transfer behavior change** (a tagged `ATS`/`MTS`/`STS` that now routes to the transfer family) - re-baseline it IN THIS COMMIT with a documented before/after (the reason-code deltas: a tagged `ATS 800AF/800AT LSIG` -> `transfer_parent_conflict` [was `non_breaker_carries_rating`]; a tagged bare `ATS-1` -> transfer scope_pending), so the build stays green at every commit (NO xfail). Do NOT touch any TAGLESS assertion (`at('ATS 800AF/800AT')` stays `non_breaker_carries_rating`), any `UPS-*` row, any `drift-check`/`golden-e01-11` value-loose assertion that still passes, or any prior-family assertion. Coarse assertions that stay green but no longer positively prove the route fired (the vacuous `MTS`/`STS` null-shape checks) are TIGHTENED in Task 5, not here. Commit:
```bash
git add -A && git commit -m "feat(transfer): assessor + union widen + quantify/emit/buckets wiring (Task 3, coupled core)"
```

---

### Task 4: Report projection + end-to-end pipeline tests (the crux cases)

**Files:**
- Modify: `packages/estimator-takeoff/src/runner/report.ts` (scopePending projection gains `automationClass` + `bypassIsolation`)
- Test: `packages/estimator-takeoff/test/transfer-pipeline.test.ts`

**Interfaces:**
- Consumes: `runTakeoff` (the full pipeline, Tasks 1-3).
- Produces: the end-to-end crux-case coverage + the report projection.

- [ ] **Step 1: Write the failing pipeline test** covering spec crux #1-#8, #10 (cross-family byte-identical), #14 (producer hard-win): a tagged `ATS-1` -> transfer scope_pending (automatic, default IR/DLRO); `MTS-2` -> manual; `ATS ... bypass` -> Iso-Bypass default; bare `transfer switch` -> unknown group no default; `MTS ... bypass` -> `transfer_catalog_gap`; `STS-1` -> gap; a `UPS-*-MIB 1600AF/1600AT` -> `non_breaker_carries_rating` (UNCHANGED); `ATS-1 500kVA` -> transfer (NOT transformer); a tagged `ATS-1 GROUND FAULT` candidateKind:'gfp' -> NOT a priced GFP line. Assert the report carries `automationClass`/`bypassIsolation`.

- [ ] **Step 2: Run; expect FAIL** (report projection missing the fields). Run: `... test -- transfer-pipeline`.

- [ ] **Step 3: Implement the `runner/report.ts` projection** (add `automationClass`/`bypassIsolation` to the `scopePending` projection + `renderReportText` Gate-2 block, mirroring the switch `switchType`/`fused` projection).

- [ ] **Step 4: Run; expect PASS. Commit.**
```bash
git add packages/estimator-takeoff/src/runner/report.ts packages/estimator-takeoff/test/transfer-pipeline.test.ts
git commit -m "feat(transfer): report projection + end-to-end pipeline crux tests (Task 4)"
```

---

### Task 5: Golden re-baseline (E01-11) + SKILL.md + byte-identical regression + full gates

**Files:**
- Test: `packages/estimator-takeoff/test/transfer-golden.test.ts` (a new coexistence golden)
- Modify (intentional re-baseline, documented): `test/golden-e01-11.test.ts` (if it asserts STS reason codes), `test/normalize.test.ts` (the tagged ATS/MTS/STS assertions), `test/dispositions.test.ts` (tagged ATS/STS), `test/runner.test.ts` (comment refresh) - EXACTLY the tagged-transfer deltas, nothing else
- Modify (doc re-baseline): `packages/estimator-takeoff/SKILL.md` (line ~104 worked-example narrative)
- (Read-only verification of the six prior golden tests + all tagless/UPS rows)

**Interfaces:**
- Consumes: the full pipeline (Tasks 1-4).
- Produces: the transfer coexistence golden + the documented re-baseline + the byte-identical confirmation.

- [ ] **Step 1: Enumerate the exact tagged-transfer assertions that change (the D4 before/after).** Grep `ATS|MTS|STS` in `test/*.test.ts`; for each TAGGED occurrence assert its old vs new disposition. Expected deltas: tagged `ATS/MTS/STS 800AF/800AT LSIG` -> `transfer_parent_conflict` (was `non_breaker_carries_rating`); tagged `ATS-1` bare -> transfer scope_pending; the E01-11 `STS-*` rows (8, all `1200AF/1200AT LSI`, tagged) -> `transfer_parent_conflict`. Confirm NO tagless row and NO `UPS-*` row changes (grep `at('ATS 800AF/800AT')` and the `UPS-*-MIB` fixture rows stay their current codes). Write the before/after into a comment block in `transfer-golden.test.ts`.

- [ ] **Step 2: Write the failing coexistence golden `test/transfer-golden.test.ts`** (a real one-line: a tagged `ATS-1` + `ATS-2 Iso Bypass` + `MTS-3` + `STS-4` + a `Main-Tie-Main` pair of REAL breakers + a `UPS-5-MIB 1600AF/1600AT` main coexist). Expect: ATS-1 -> automatic scope_pending; ATS-2 -> Iso-Bypass; MTS-3 -> manual; STS-4 -> `transfer_catalog_gap`; the two MAIN/TIE breakers -> priced breakers; UPS-5 -> `non_breaker_carries_rating` question; `partial_preview`; `accounted true`.

- [ ] **Step 3: TIGHTEN the re-baselined normalize tests to be NON-VACUOUS.** In `test/normalize.test.ts`, change the tagged `MTS-2 800AF/800AT LSIG` / `STS-1 800AF/800AT LSIG` assertions from the coarse `signature===null + questions>0` to `assessmentCode === 'transfer_parent_conflict'` (positively proving the route fired - a build that skipped the route would now RED). Update `dispositions.test.ts` tagged-ATS reasonCode -> `transfer_parent_conflict`; refresh the stale `runner.test.ts:59` comment.

- [ ] **Step 4: Update `SKILL.md` line ~104** worked-example: split the STS rows (now `transfer_parent_conflict`) from the UPS rows (still `non_breaker_carries_rating`); re-verify the `39 operator questions / bid_cents 198000 / 0 findings` figures still hold verbatim (they must - `transfer_parent_conflict` is still an unpriced question).

- [ ] **Step 5: Run the FULL suite + both typechecks; confirm the six prior goldens + all tagless/UPS rows byte-identical.**

Run (NO `| tail` - let the test exit code propagate): `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-estimator-ats && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: ALL green; `breaker/transformer/relay/gfp/itx/switch` goldens byte-identical; the E01-11 `bid_cents 198000` unchanged; ONLY the tagged-transfer + SKILL.md deltas present. **Build-time watch:** if any NON-transfer row or any tagless ATS/MTS/STS row moved, STOP and investigate.

- [ ] **Step 6: Commit.**
```bash
git add -A && git commit -m "feat(transfer): coexistence golden + E01-11/SKILL.md re-baseline + byte-identical gates (Task 5)"
```

- [ ] **Step 7: Cross-engine (Codex) IRP on the whole branch, then finish (operator-gated PR).** Run the Codex whole-branch review (`codex exec review --dangerously-bypass-approvals-and-sandbox -c model_reasoning_effort=high --base main` from the lane worktree); fold any must-fixes; then `superpowers:finishing-a-development-branch` (push + open PR; operator-gated squash/admin-rebase merge).

---

## Self-Review (completed by the plan author)

**1. Spec coverage:** Every spec (rev 3) section maps to a task. Component 1 (extraction) + 2 (signature types) -> Tasks 1+3; Component 3 (recognition + the T1-B guard + the no-NON_BREAKER-edit routing) -> Tasks 2+3; Component 4 (match) -> Task 1; Component 5 (quantify) -> Task 3; Component 6 (disposition+emit+report) -> Tasks 3+4. Spec tests #1-#20 distributed: match/#11 -> Task 1; recognition/#3/#4/#7/#9/#14/#20 -> Tasks 2+3; cross-family byte-identical #10 -> Tasks 3+4; pipeline #5/#6/#12/#13/#16 -> Task 4; golden re-baseline #17/#18/#19 -> Task 5. The T1-B ruling, the STS gap-vs-conflict split, and the main-tie-main safety are pinned in Tasks 3 (guard) + 5 (golden). No gaps.

**2. Placeholder scan:** No TBD/TODO. All source is complete code; all regexes literal; the 3 refs verbatim; the tests concrete. The one "enumerate the exact deltas" step (Task 5 Step 1) is a grounding action against the live tree, not a placeholder - it produces the documented before/after D4 requires.

**3. Type consistency:** `TransferAutomationClass`/`TransferSwitchSignature` (Task 1) used identically in `matchTransferSwitch` (Task 1), `assessTransferSwitch`/`specKey`/emit (Task 3). `TransferScopeMatch {group, defaultRef?, scopeQuestion}` consistent with the emit consumer. `transfer_recognized`/`transfer_parent_conflict` (AssessmentCode) map to `transfer_scope_pending`/`transfer_parent_conflict` (DispositionReasonCode) via `ASSESS_TO_REASON`. `automationClass?`/`bypassIsolation?` consistent across `ScopePendingLine`/`ApparatusDisposition`/report. `NON_BREAKER` is verified UNCHANGED (a grep invariant), preserving GFP/transformer/tagless/breaker-fallback.
