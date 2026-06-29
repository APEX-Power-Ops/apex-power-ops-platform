# Estimator-Takeoff Relay Family (V1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Rev 2 (operator plan review, 2026-06-29):** folded 4 patches - (1) `deriveRole` now reaches the `electromechanical` tier for legacy single-function EM/solid-state relays (+tests); (2) no-default text-render gate now calls `renderReportText` and asserts `provisional=none`; (3) `matchBreaker`/`matchTransformer` get direct type+runtime guards vs a relay signature; (4) `RELAY_ACCESSORY` exclusion so a standalone transformer-accessory pressure relay is not recognized as a priced relay.

**Goal:** Admit the RELAY apparatus family into `packages/estimator-takeoff` V1 - recognized device-first, counted per device, routed to a Gate-2 application-tier scope decision (never auto-priced), with breaker and transformer behavior byte-identical.

**Architecture:** Reuse the transformer slice's scope_pending machinery (discriminated-union signature, `scope_pending` disposition, candidate ref-GROUP, R1-provisional defaults, kind-prefixed `deviceId`, cross-family guards). Add a third signature `kind: 'relay'`, a device-first recognizer/parser, an application-tier match table, and three relay-specific guardrails: voltage optional/contextual (never gates), recognition device-first (ANSI numbers are attributes, never countable devices), and an optional provisional default (no-default scope_pending).

**Tech Stack:** TypeScript, Vitest, pnpm workspace. All build/test runs on the Olares host over `ssh olares-mesh`, in worktree `/home/olares/code/apex/apex-relay-family` (branch `estimator-takeoff/relay-family-admission`).

## Global Constraints

- ASCII-only in all authored code/comments AND engine-emitted strings (questions, findings, scope questions, notes). Verbatim source DATA may be UTF-8. No em-dashes in engine strings.
- Breaker AND transformer goldens byte-identical after every task. They are the regression guard for the third family.
- No new catalog refs, no new hours. V1 uses the 9 existing NETA-7.9 relay refs only. Gaps surfaced (`catalog_gap`), never fabricated.
- Relays never auto-price. Every recognized relay -> `scope_pending` (group + optional provisional default) or `catalog_gap`. There is no "matched" relay line in V1.
- R1 (`RELAY_R1_RATIFIED`) stays `false` (role->tier provisional) until the estimator confirms; relays never auto-price, so provisional is fail-closed.
- Gates (run on host, exact): `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (the cross-package gate; `--filter apex-operations-web` matches NOTHING - false-green trap).
- Commits authored `jasonlswenson-sys <jasonlswenson@gmail.com>`; every commit ends `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Merge operator-gated; cross-engine (Codex) IRP before merge.
- Spec: `docs/superpowers/specs/2026-06-29-estimator-takeoff-relay-family-design.md` (Rev 2). Packet: `docs/superpowers/packets/estimator-takeoff-family-relays.md`.

**Host command prefix (every test/typecheck step):** `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && <cmd>'`. The exact relay refs (string-keyed) are, VERBATIM from the seed - note the " - " in two of them:
`Protective Relay (Electromechanical)`, `Protective Relay (Overcurrent Protection)`, `Protective Relay (Feeder Protection)`, `Protective Relay (Motor Control)`, `Protective Relay - (Bus Differential)`, `Protective Relay (Differential Protection)`, `Protective Relay - (Line Protection)`, `Protective Relay (Generator Protection)`, `Protective Relay (Multi-function w Meter)`.

---

### Task 1: Relay catalog authority (data + exact-ref validation)

**Files:**
- Create: `packages/estimator-takeoff/src/catalog/relay-map.data.ts`
- Create: `packages/estimator-takeoff/test/relay-catalog.test.ts`

**Interfaces:**
- Produces: `RELAY_TIERS: readonly string[]` (9 refs verbatim), `ROLE_TO_TIER: Record<RelayRole, string>` partial (legible roles only; `unknown` absent), `ORPHAN_ANSI: ReadonlySet<string>`, `RELAY_R1_RATIFIED: boolean` (false). (`RelayRole` is defined in Task 2; this task uses plain string keys to avoid a forward dep - see Step 3.)

- [ ] **Step 1: Write the failing test** (`test/relay-catalog.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { RELAY_TIERS, ROLE_TO_TIER, ORPHAN_ANSI, RELAY_R1_RATIFIED } from '../src/catalog/relay-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('relay catalog authority', () => {
  it('every relay tier ref resolves verbatim in the live seed; 9 tiers', () => {
    expect(RELAY_TIERS.length).toBe(9)
    for (const ref of RELAY_TIERS) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
  })
  it('every ROLE_TO_TIER value is a member of RELAY_TIERS and resolves in the seed', () => {
    for (const ref of Object.values(ROLE_TO_TIER)) {
      expect(RELAY_TIERS).toContain(ref)
      expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
    }
  })
  it('ORPHAN_ANSI holds the deferred device types (D1 policy)', () => {
    for (const n of ['86', '79', '25', '27', '59', '81']) expect(ORPHAN_ANSI.has(n)).toBe(true)
  })
  it.todo('R1: estimator ratifies the relay role->tier mapping -> flip RELAY_R1_RATIFIED=true')
  it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests)', () => {
    expect(RELAY_R1_RATIFIED).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-catalog'`
Expected: FAIL - cannot resolve `../src/catalog/relay-map.data`.

- [ ] **Step 3: Implement** (`src/catalog/relay-map.data.ts`)

```ts
// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED (NETA 7.9, unit_of_issue=each).
// Note the " - " in Bus Differential and Line Protection; matching is string-keyed.
export const RELAY_TIERS = [
  'Protective Relay (Electromechanical)',
  'Protective Relay (Overcurrent Protection)',
  'Protective Relay (Feeder Protection)',
  'Protective Relay (Motor Control)',
  'Protective Relay - (Bus Differential)',
  'Protective Relay (Differential Protection)',
  'Protective Relay - (Line Protection)',
  'Protective Relay (Generator Protection)',
  'Protective Relay (Multi-function w Meter)',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: legible dominant-role -> default tier. 'unknown' is absent
// (illegible relays carry NO default -> no-default scope_pending). String keys (RelayRole shape lands in Task 2).
export const ROLE_TO_TIER: Record<string, string> = {
  overcurrent:         'Protective Relay (Overcurrent Protection)',
  feeder:              'Protective Relay (Feeder Protection)',
  motor:               'Protective Relay (Motor Control)',
  bus_differential:    'Protective Relay - (Bus Differential)',
  differential:        'Protective Relay (Differential Protection)',
  line:                'Protective Relay - (Line Protection)',
  generator:           'Protective Relay (Generator Protection)',
  multifunction_meter: 'Protective Relay (Multi-function w Meter)',
  electromechanical:   'Protective Relay (Electromechanical)',
}

// D1 policy: standalone-dominant device types with no priced tier home -> catalog_gap until SME decides.
export const ORPHAN_ANSI: ReadonlySet<string> = new Set(['86', '79', '25', '27', '59', '81'])

// Operator flips to true when the estimator confirms the role->tier mapping + EM-vs-uP convention.
export const RELAY_R1_RATIFIED = false
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-catalog'`
Expected: PASS (4 pass + 1 todo).

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add packages/estimator-takeoff/src/catalog/relay-map.data.ts packages/estimator-takeoff/test/relay-catalog.test.ts && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(takeoff): relay catalog authority (9 tiers verbatim + role map + orphan set)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 2: Relay signature types + voltage-optional + candidateKind + matchRelay

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts`
- Modify: `packages/estimator-takeoff/src/extraction/types.ts`
- Modify: `packages/estimator-takeoff/src/extraction/parse.ts`
- Create: `packages/estimator-takeoff/src/catalog/relay-map.ts`
- Create: `packages/estimator-takeoff/test/relay-map.test.ts`
- Modify: `packages/estimator-takeoff/test/<existing parse test for candidateKind>` (add a relay-accept case; find with grep, see Step 1b)

**Interfaces:**
- Produces: `RelayTechnology`, `RelayRole`, `RelaySignature` (NOT yet in `ApparatusSignature` union - added in Task 3); `interface RelayScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }`; `matchRelay(sig: RelaySignature): RelayScopeMatch | null`.
- Consumes: `RELAY_TIERS`, `ROLE_TO_TIER`, `ORPHAN_ANSI` (Task 1).

- [ ] **Step 1: Write the failing tests** (`test/relay-map.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { matchRelay } from '../src/catalog/relay-map'
import { RELAY_TIERS } from '../src/catalog/relay-map.data'
import type { RelaySignature } from '../src/signature/types'

const base = (o: Partial<RelaySignature> & { role: RelaySignature['role'] }): RelaySignature => ({
  kind: 'relay', technology: 'microprocessor', voltageBasis: 'none', tag: 'R1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...o,
})

describe('matchRelay', () => {
  it('legible role -> group + provisional defaultRef (the role tier)', () => {
    const m = matchRelay(base({ role: 'differential' }))!
    expect(m.group).toEqual([...RELAY_TIERS])
    expect(m.defaultRef).toBe('Protective Relay (Differential Protection)')
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('electromechanical role -> the Electromechanical tier as default', () => {
    const m = matchRelay(base({ role: 'electromechanical', technology: 'electromechanical_solid_state' }))!
    expect(m.defaultRef).toBe('Protective Relay (Electromechanical)')
  })
  it('illegible role (unknown) -> group with NO defaultRef (no-default case)', () => {
    const m = matchRelay(base({ role: 'unknown' }))!
    expect(m.group).toEqual([...RELAY_TIERS])
    expect(m.defaultRef).toBeUndefined()
  })
  it('orphan-dominant role -> null (catalog_gap)', () => {
    const m = matchRelay(base({ role: 'unknown', ansiFunctions: ['86'] }))
    expect(m).toBeNull()
  })
})
```

- [ ] **Step 1b: Find the existing candidateKind parse test**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && grep -rln "candidateKind" packages/estimator-takeoff/test'`
Add to that file a case asserting `parseArtifact` accepts `candidateKind: 'relay'` (mirror the existing `'transformer'` accept case verbatim, swapping the value).

- [ ] **Step 2: Run tests to verify they fail**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-map'`
Expected: FAIL - `../src/catalog/relay-map` and `RelaySignature` do not exist.

- [ ] **Step 3a: Implement signature types** (`src/signature/types.ts`)

Change `BaseSignature.voltageClass` to optional and re-declare it required on the two existing kinds; add the relay types. Exact edits:

```ts
// in BaseSignature: voltageClass becomes optional
export interface BaseSignature {
  voltageClass?: VoltageClass        // optional at the base; required for breaker/transformer (re-declared), contextual for relay
  voltageV?: number
  voltageBasis: VoltageBasis
  tag?: string
  inputIndex?: number
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string; block?: string }
}

// BreakerSignature: re-declare voltageClass required
export interface BreakerSignature extends BaseSignature {
  kind: 'breaker'
  voltageClass: VoltageClass         // required for breakers (narrows the optional base)
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting
  mountingBasis: MountingBasis
  mvType?: MvType
}

// TransformerSignature: re-declare voltageClass required
export interface TransformerSignature extends BaseSignature {
  kind: 'transformer'
  voltageClass: VoltageClass         // required for transformers (narrows the optional base)
  kvaRating?: number
  coolant: Coolant
  padMount?: boolean
  ltc?: boolean
}

// New relay types
export type RelayTechnology = 'electromechanical_solid_state' | 'microprocessor' | 'unknown'
export type RelayRole =
  | 'overcurrent' | 'feeder' | 'motor' | 'bus_differential' | 'differential'
  | 'line' | 'generator' | 'multifunction_meter' | 'electromechanical' | 'unknown'

export interface RelaySignature extends BaseSignature {
  kind: 'relay'
  technology: RelayTechnology
  ansiFunctions?: string[]
  model?: string
  role?: RelayRole
  // voltageClass stays optional (inherited): relay voltage is contextual and never gates.
}

// NOTE: ApparatusSignature union is widened to include RelaySignature in Task 3 (the wire task),
// together with the emit/specKey relay branches that the union forces. Do NOT add it here.
export type ApparatusSignature = BreakerSignature | TransformerSignature
```

- [ ] **Step 3b: Widen candidateKind** (`src/extraction/types.ts` + `src/extraction/parse.ts`)

`extraction/types.ts`: change `candidateKind?: 'breaker' | 'transformer'` to `candidateKind?: 'breaker' | 'transformer' | 'relay'`.
`extraction/parse.ts`: the candidateKind validation currently rejects anything but breaker/transformer; widen it to accept `'relay'`:

```ts
  if (r['candidateKind'] !== undefined && r['candidateKind'] !== 'breaker' && r['candidateKind'] !== 'transformer' && r['candidateKind'] !== 'relay') fail(`${p}.candidateKind`, "'breaker'|'transformer'|'relay'", r['candidateKind'])
```

- [ ] **Step 3c: Implement matchRelay** (`src/catalog/relay-map.ts`)

```ts
import type { RelaySignature } from '../signature/types'
import { RELAY_TIERS, ROLE_TO_TIER, ORPHAN_ANSI } from './relay-map.data'

export interface RelayScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select relay test-scope tier (application/function): which of the priced relay tiers applies to this device?'

export function matchRelay(sig: RelaySignature): RelayScopeMatch | null {
  // Orphan device types (86/79/25/27/59/81 standalone-dominant) have no priced tier home -> catalog_gap.
  if (sig.ansiFunctions && sig.ansiFunctions.length === 1 && ORPHAN_ANSI.has(sig.ansiFunctions[0]!)) return null
  const role = sig.role ?? 'unknown'
  const defaultRef = role !== 'unknown' ? ROLE_TO_TIER[role] : undefined
  // Always offer the full tier group; provisional default only where the role is legible.
  return { group: [...RELAY_TIERS], defaultRef, scopeQuestion: SCOPE_Q }
}
```

- [ ] **Step 4: Run tests + typecheck + goldens**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck'`
Expected: PASS - relay-map tests green; ALL existing tests green (breaker + transformer goldens byte-identical: the voltage-optional change is inert because both kinds re-declare it required).

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add -A && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(takeoff): relay signature types (voltage-optional base) + candidateKind relay + matchRelay" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 3: Wire relay into the union + pipeline (emit/specKey/contract, no-default)

This is the "wire" task: adding `RelaySignature` to `ApparatusSignature` forces every `kind` consumer to handle relay. No `assessRelay` exists yet, so no relay signatures flow through `runTakeoff` - breaker/transformer goldens stay byte-identical; the relay path is proven here by a unit test that feeds a hand-built relay signature through `quantify` + the emit match loop.

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts` (union)
- Modify: `packages/estimator-takeoff/src/quantify/quantify.ts` (specKey relay branch)
- Modify: `packages/estimator-takeoff/src/buckets/types.ts` (optional provisionalDefaultRef + relay codes)
- Modify: `packages/estimator-takeoff/src/emit/emit.ts` (relay match branch)
- Modify: `packages/estimator-takeoff/src/runner/report.ts` (ReconciliationReport optional + renderer `?? 'none'`)
- Create: `packages/estimator-takeoff/test/relay-pipeline.test.ts`

**Interfaces:**
- Consumes: `matchRelay`, `RelayScopeMatch` (Task 2), `RELAY_R1_RATIFIED` (Task 1), `RelaySignature` (Task 2).
- Produces: relay rows flow as `scope_pending` (with/without default) or `catalog_gap` through `runTakeoff`; `ScopePendingLine.provisionalDefaultRef?` optional.

- [ ] **Step 1: Write the failing test** (`test/relay-pipeline.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { RelaySignature } from '../src/signature/types'

const rsig = (o: Partial<RelaySignature> & { role: RelaySignature['role']; tag: string }): RelaySignature => ({
  kind: 'relay', technology: 'microprocessor', voltageBasis: 'none', inputIndex: 0,
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' }, ...o,
})

describe('relay flows through quantify (kind-aware specKey, no voltage required)', () => {
  it('two relays differing only in role get separate lines; no voltage needed', () => {
    const { lines } = quantify([
      rsig({ role: 'differential', tag: 'R1' }),
      rsig({ role: 'feeder', tag: 'R2', inputIndex: 1 }),
    ])
    expect(lines).toHaveLength(2)
    expect(lines.every((l) => l.signature.kind === 'relay')).toBe(true)
  })
})
```

(The end-to-end scope_pending/catalog_gap assertions arrive in Task 4 once `assessRelay` feeds `runTakeoff`; this task proves the union + quantify path compiles and groups relays.)

- [ ] **Step 2: Run test to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-pipeline'`
Expected: FAIL - `quantify` rejects relay signatures (specKey transformer branch reads `s.coolant`) / type errors.

- [ ] **Step 3a: Widen the union** (`src/signature/types.ts`)

```ts
export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature
```

- [ ] **Step 3b: Add the specKey relay branch** (`src/quantify/quantify.ts`, inside `specKey`, BEFORE the transformer `return`)

```ts
  if (s.kind === 'relay') {
    // per-device application tier; voltage optional/contextual; role+technology+model dedup
    return [s.kind, s.role ?? '-', s.technology, s.model ?? '-', s.voltageClass ?? '-', s.source.block ?? '-'].join('|')
  }
```

- [ ] **Step 3c: Contract - optional default + relay codes** (`src/buckets/types.ts`)

```ts
// ScopePendingLine: provisionalDefaultRef becomes optional (no-default relay case)
export interface ScopePendingLine {
  candidateRefs: string[]
  provisionalDefaultRef?: string     // optional: absent for an illegible-role relay (no-default scope_pending)
  r1Ratified: boolean
  scopeQuestion: string
  qty: number
  block: string
  line: QuantifiedLine
}
```

Add to `OperatorQuestionCode`: `| 'relay_scope_pending' | 'relay_catalog_gap'`.
Add to `DispositionReasonCode`: `| 'relay_scope_pending' | 'relay_catalog_gap'`.
Add to `TakeoffFinding.code` union: `| 'relay_catalog_gap'`.
(`relay_breaker_conflict` is added in Task 4 with the AssessmentCode.)

- [ ] **Step 3d: Add the emit relay match branch** (`src/emit/emit.ts`)

Add imports at top: `import { matchRelay } from '../catalog/relay-map'`; `import { RELAY_R1_RATIFIED } from '../catalog/relay-map.data'`; and add `RelaySignature` to the existing `import type { ApparatusSignature, BreakerSignature, TransformerSignature } from '../signature/types'`.

Insert this block in the `for (const line of lines)` loop, AFTER the `if (sig.kind === 'breaker') { ... continue }` block and BEFORE the `// kind === 'transformer'` line:

```ts
    if (sig.kind === 'relay') {
      const rsig: RelaySignature = sig
      const scope = matchRelay(rsig)
      if (scope) {
        scopePendingLines.push({
          candidateRefs: scope.group,
          provisionalDefaultRef: scope.defaultRef,   // may be undefined (no-default relay)
          r1Ratified: RELAY_R1_RATIFIED,
          scopeQuestion: scope.scopeQuestion,
          qty: line.qty,
          block: rsig.source.block ?? rsig.source.sheet,
          line,
        })
        for (const i of line.memberIndices) {
          stamp(dispositions, i, 'scope_pending', 'relay_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
          const disp = dispositions[i]!
          disp.candidateRefs = scope.group
          disp.provisionalDefaultRef = scope.defaultRef
          disp.scopeQuestion = scope.scopeQuestion
        }
        questions.push({ question: scope.scopeQuestion, context: `${rsig.tag ?? rsig.source.sheet} (candidate group: ${scope.group.join(' | ')})`, code: 'relay_scope_pending' })
      } else {
        const reason = `recognized relay (role ${rsig.role ?? 'unknown'}) - no applicable priced ref-group`
        unmatchedCandidates.push({ reason, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'relay_catalog_gap', reason, undefined, line.lineKey)
        findings.push({ code: 'relay_catalog_gap', severity: 'warning', message: reason, context: rsig.tag ?? rsig.source.sheet })
        questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: rsig.tag ?? rsig.source.sheet, code: 'relay_catalog_gap' })
      }
      continue
    }
```

- [ ] **Step 3e: Report no-default rendering** (`src/runner/report.ts`)

In `ReconciliationReport.scopePending[]` make the field optional: `provisionalDefaultRef?: string`.
In the text renderer (the `provisional=` line), render `none` when absent:

```ts
      out.push('    [' + (sp.tag ?? sp.lineKey) + '] qty=' + sp.qty + ' provisional=' + (sp.provisionalDefaultRef ?? 'none') + ' r1Ratified=' + sp.r1Ratified)
```

(The reconcile builder already passes `provisionalDefaultRef: sp.provisionalDefaultRef`; now optional, it carries `undefined` cleanly into JSON.)

- [ ] **Step 4: Run tests + both typechecks (incl cross-package)**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: PASS - relay-pipeline test green; ALL existing tests green; estimator-takeoff typecheck clean; operations-web typecheck CLEAN (the cross-package gate - the optional-field change must not break it). Breaker + transformer goldens byte-identical.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add -A && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(takeoff): wire relay into the signature union + pipeline (emit/specKey/contract; no-default scope_pending)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 4: Device-first recognition + parsers + assessRelay (+ codes/ASSESS_TO_REASON)

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts`
- Modify: `packages/estimator-takeoff/src/buckets/types.ts` (`relay_breaker_conflict` into the three unions)
- Modify: `packages/estimator-takeoff/src/emit/emit.ts` (ASSESS_TO_REASON entries)
- Create: `packages/estimator-takeoff/test/normalize-relay.test.ts`

**Interfaces:**
- Consumes: `RelaySignature`, `RelayTechnology`, `RelayRole` (Task 2); the wired pipeline (Task 3).
- Produces: `assessRelay` routed in `assessCore`; `AssessmentCode` += `'relay_recognized' | 'relay_breaker_conflict'`; recognized relays flow end-to-end to `scope_pending`/`catalog_gap`.

- [ ] **Step 1: Write the failing tests** (`test/normalize-relay.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('relay recognition - device-first', () => {
  it('bare 87T text with NO anchor is NOT a relay (unrecognized)', () => {
    const a = assessApparatus(row({ raw: '87T', tag: undefined }))
    expect(a.signature).toBeNull()
    expect(a.assessmentCode).toBe('unrecognized_apparatus_row')
  })
  it('candidateKind:relay + 87T -> relay device, differential role', () => {
    const a = assessApparatus(row({ raw: '87T', tag: 'R-1', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature?.kind).toBe('relay')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.role : null).toBe('differential')
  })
  it('a relay with NO bus voltage never emits missing_voltage', () => {
    const a = assessApparatus(row({ raw: 'SEL-751 FEEDER RELAY', tag: 'R-2' }))   // no busVoltageV
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature?.kind).toBe('relay')
  })
  it('a relay carrying a breaker frame/trip -> relay_breaker_conflict (null signature)', () => {
    const a = assessApparatus(row({ raw: 'RELAY 800AF/600AT', tag: 'R-3', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_breaker_conflict')
    expect(a.signature).toBeNull()
  })
  it('a legacy single-function EM/solid-state relay -> electromechanical role', () => {
    const a = assessApparatus(row({ raw: 'EM OVERCURRENT RELAY 51', tag: 'R-4', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.technology : null).toBe('electromechanical_solid_state')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.role : null).toBe('electromechanical')
  })
  it('a standalone transformer-accessory pressure relay is NOT a protective relay device', () => {
    const a = assessApparatus(row({ raw: 'FAULT PRESSURE RELAY', tag: 'X63' }))   // no candidateKind anchor
    expect(a.signature).toBeNull()
    expect(a.assessmentCode).toBe('unrecognized_apparatus_row')
  })
})

describe('relay end-to-end through runTakeoff', () => {
  it('anchored 87T -> scope_pending differential (with provisional default)', () => {
    const r = runTakeoff(art([row({ raw: '87T', tag: 'R-1', candidateKind: 'relay' })]))
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines ?? []).toHaveLength(1)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.provisionalDefaultRef).toBe('Protective Relay (Differential Protection)')
    expect(sp.r1Ratified).toBe(false)
    expect(r.dispositions[0]!.reasonCode).toBe('relay_scope_pending')
  })
  it('illegible relay -> no-default scope_pending (provisionalDefaultRef undefined)', () => {
    const r = runTakeoff(art([row({ raw: 'PROTECTIVE RELAY', tag: 'R-9', candidateKind: 'relay' })]))
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs.length).toBe(9)
    expect(sp.provisionalDefaultRef).toBeUndefined()
  })
  it('relay-only extraction is not "nothing to price" (no missing_voltage row)', () => {
    const r = runTakeoff(art([row({ raw: 'SEL-787 87T XFMR DIFF RELAY', tag: 'R-1', candidateKind: 'relay' })]))
    expect(r.dispositions.every((d) => d.reasonCode !== 'missing_voltage')).toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test normalize-relay'`
Expected: FAIL - relays not recognized (assessmentCode `unrecognized_apparatus_row` for the anchored cases).

- [ ] **Step 3a: Add relay codes + AssessmentCode + ASSESS_TO_REASON**

`src/buckets/types.ts`: add `| 'relay_breaker_conflict'` to BOTH `OperatorQuestionCode` and `DispositionReasonCode`.
`src/signature/normalize.ts`: add to `AssessmentCode`: `| 'relay_recognized' | 'relay_breaker_conflict'`.
`src/emit/emit.ts` `ASSESS_TO_REASON`: add the two entries (this is the NAMED safety-seam task):

```ts
  relay_recognized:       'relay_scope_pending',   // unreachable (has signature); present for exhaustiveness
  relay_breaker_conflict: 'relay_breaker_conflict',
```

- [ ] **Step 3b: Implement recognition + parsers + assessRelay** (`src/signature/normalize.ts`)

Add near the other token regexes:

```ts
const RELAY_DEVICE = /\b(protective\s+relay|relay|SEL-?\d|multilin|beckwith|basler|micom)\b/i
const ANSI_FN = /\b(2[1-7]|32|37|38|40|46N?|47|49[RT]?|50N?|51N?|55|59|60|63|64|67|79|81|86|87[TBGN]?)\b/g
// Transformer-protection accessory relays (pressure/temperature/Buchholz/gas) are NOT standalone
// protective-relay DEVICES the firm prices. Exclude them from token-based recognition so a plain
// "FAULT PRESSURE RELAY" does not become a priced relay (an explicit candidateKind:'relay' still wins).
const RELAY_ACCESSORY = /\b((sudden|fault)\s*pressure|pressure|buchholz|gas\s*accumulator)\s*relay\b/i
```

Device-first recognizer (a RELAY token alone is not enough without a tag, mirroring the kVA-breaker guard discipline; the accessory exclusion makes the transformer-first claim true even for a STANDALONE pressure relay that carries no transformer token):

```ts
function looksLikeRelay(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'relay') return true                  // explicit producer signal wins
  if (RELAY_ACCESSORY.test(x.raw)) return false                 // transformer accessory, not a priced relay device
  return RELAY_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}

function parseRelayTechnology(raw: string): RelayTechnology {
  if (/\b(SEL-?\d|multilin|beckwith|basler|micom|microprocessor|uP)\b/i.test(raw)) return 'microprocessor'
  if (/\b(electromechanical|EM|solid.?state)\b/i.test(raw)) return 'electromechanical_solid_state'
  return 'unknown'
}

function parseAnsiFunctions(raw: string): string[] {
  const out = new Set<string>()
  for (const m of raw.matchAll(ANSI_FN)) out.add(m[1]!.toUpperCase())
  return [...out]
}

function parseRelayModel(raw: string): string | undefined {
  const m = raw.match(/\b(SEL-?\d{2,4}[A-Z]?|multilin\s*\w+|beckwith\s*\w+|basler\s*\w+|micom\s*\w+)\b/i)
  return m ? m[0] : undefined
}

function deriveRole(ansi: string[], raw: string, tech: RelayTechnology): RelayRole {
  const has = (n: string) => ansi.includes(n)
  // Complex / multi-element roles first (these take their tier even on legacy technology).
  if (has('87T') || /transformer\s+diff/i.test(raw)) return 'differential'
  if (has('87B') || /\bbus\b/i.test(raw)) return 'bus_differential'
  if (has('87')) return 'differential'
  if (/generator/i.test(raw) || (has('40') && (has('32') || has('46')))) return 'generator'
  if (has('21') || /\b(line|distance)\b/i.test(raw)) return 'line'
  if (/motor/i.test(raw) || (has('49') && has('50') && has('51'))) return 'motor'
  if (/multi.?function/i.test(raw) && /meter/i.test(raw)) return 'multifunction_meter'
  // Legacy single-function EM/solid-state -> the cheap electromechanical tier (spec line 62).
  // Placed BEFORE the generic feeder/overcurrent roles so a simple EM relay does not fall into the uP tier.
  if (tech === 'electromechanical_solid_state' && ansi.length <= 1) return 'electromechanical'
  if (/feeder/i.test(raw)) return 'feeder'
  if (has('50') || has('51') || /overcurrent/i.test(raw)) return 'overcurrent'
  return 'unknown'
}

function assessRelay(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  if (FRAME_TRIP.test(x.raw)) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'relay_breaker_conflict',
      questions: [q(x, 'Label names a relay but carries a breaker frame/trip rating - confirm device type before counting.', 'relay_breaker_conflict')],
    }
  }
  const ansiFunctions = parseAnsiFunctions(x.raw)
  const technology = parseRelayTechnology(x.raw)
  const role = deriveRole(ansiFunctions, x.raw, technology)
  const voltageClass = classifyVoltage(x.busVoltageV)   // MAY be undefined - relay voltage is contextual, NOT gated
  const sig: RelaySignature = {
    kind: 'relay', technology, ansiFunctions, role,
    model: parseRelayModel(x.raw),
    voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'relay_recognized', questions: [] }
}
```

Add the imports for `RelaySignature`, `RelayTechnology`, `RelayRole` to the existing `import type ... from './types'`.

Route in `assessCore` - relay AFTER transformer, BEFORE NON_BREAKER (so a `Multi-function (w Meter)` relay's METER token is not swallowed by NON_BREAKER). A transformer-accessory pressure relay on a row that ALSO carries a transformer token stays with the transformer because transformer is checked first; a STANDALONE pressure relay (no transformer token) is excluded by `RELAY_ACCESSORY` in `looksLikeRelay` and falls through to `unrecognized_apparatus_row`:

```ts
  if (looksLikeTransformer(x)) {
    // ... existing transformer block unchanged ...
  }

  if (looksLikeRelay(x)) {
    return assessRelay(x, voltageBasis)
  }

  if (NON_BREAKER.test(x.raw)) {
    // ... existing unchanged ...
```

- [ ] **Step 4: Run tests + both typechecks + goldens**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: PASS - normalize-relay tests green (device-first + no-voltage + conflict + end-to-end scope_pending); ALL existing tests green; breaker + transformer goldens byte-identical.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add -A && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "feat(takeoff): device-first relay recognition + parsers + assessRelay (+ASSESS_TO_REASON, never missing_voltage)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 5: Cross-family guards + quantify dedup

**Files:**
- Create: `packages/estimator-takeoff/test/relay-cross-family.test.ts`

**Interfaces:**
- Consumes: the full relay pipeline (Tasks 2-4). No production code expected; if a guard test fails, fix the smallest seam and note it.

- [ ] **Step 1: Write the tests** (`test/relay-cross-family.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { RelaySignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const relaySig: RelaySignature = {
  kind: 'relay', technology: 'microprocessor', role: 'feeder', voltageBasis: 'none', tag: 'R1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}

describe('relay cross-family guards', () => {
  it('a relay and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: '87T', tag: 'X1', candidateKind: 'relay' }),
      row({ raw: 'X1 800AF/600AT LSIG', tag: 'X1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).length).toBe(1)   // the relay
    expect(r.matchedLines.length).toBe(1)                 // the breaker
  })
  it('matchBreaker is type- AND runtime-defended against a relay signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error relay is not a BreakerSignature - the family-dispatch boundary is type-defended
      forced = matchBreaker(relaySig)
    }).not.toThrow()
    expect(forced).toBeFalsy()                            // even force-passed, no breaker rule matches a relay
  })
  it('matchTransformer is type- AND runtime-defended against a relay signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error relay is not a TransformerSignature
      forced = matchTransformer(relaySig)
    }).not.toThrow()
    expect(forced).toBeNull()                             // coolant undefined -> no group -> null
  })
  it('two relays differing only in technology get separate lines', () => {
    const r = runTakeoff(art([
      row({ raw: 'OVERCURRENT RELAY 50/51', tag: 'R1', candidateKind: 'relay' }),                 // microprocessor-unknown
      row({ raw: 'ELECTROMECHANICAL OVERCURRENT RELAY 50/51', tag: 'R2', candidateKind: 'relay' }), // em
    ]))
    expect((r.scopePendingLines ?? []).length).toBe(2)
  })
})
```

- [ ] **Step 2: Run + verify**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-cross-family'`
Expected: PASS. If a guard fails, fix the smallest seam (e.g. specKey) and re-run; record the fix in the commit message.

- [ ] **Step 3: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add -A && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "test(takeoff): relay cross-family guards + technology/role dedup" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 6: Real golden fixture + Gate-2 stand-in (coexistence)

**Files:**
- Create: `packages/estimator-takeoff/test/fixtures/relay-mixed.extract.json`
- Create: `packages/estimator-takeoff/test/relay-golden.test.ts`

**Interfaces:**
- Consumes: the full pipeline. Proves breaker + transformer + relay coexist; a Gate-2 stand-in resolves a relay tier and prices via estimator-core.

- [ ] **Step 1: Create the fixture** (`test/fixtures/relay-mixed.extract.json`)

A mixed one-line: a priced breaker, a scope_pending transformer, an 87T differential relay (anchored `candidateKind:'relay'`), a feeder microprocessor relay, and a bare illegible relay. Example:

```json
{
  "pdf": "relay-mixed.pdf",
  "apparatus": [
    { "raw": "MSB-1 800AF/600AT LSIG DRAW-OUT", "tag": "MSB-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 480, "candidateKind": "breaker" },
    { "raw": "T-1 1500KVA 480V DRY-TYPE XFMR", "tag": "T-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "busVoltageV": 480 },
    { "raw": "87T XFMR DIFFERENTIAL RELAY SEL-787", "tag": "R-1", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "candidateKind": "relay" },
    { "raw": "SEL-751 FEEDER PROTECTION RELAY", "tag": "R-2", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "candidateKind": "relay" },
    { "raw": "PROTECTIVE RELAY", "tag": "R-3", "sheet": "E01-11", "page": 1, "bbox": [0,0,1,1], "evidence": "one-line", "candidateKind": "relay" }
  ]
}
```

- [ ] **Step 2: Write the golden test** (`test/relay-golden.test.ts`)

```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { runTakeoff } from '../src/emit/emit'
import { reconcile, renderReportText } from '../src/runner/report'
import type { ExtractionArtifact } from '../src/extraction/types'

const artifact = JSON.parse(readFileSync(new URL('./fixtures/relay-mixed.extract.json', import.meta.url), 'utf8')) as ExtractionArtifact

describe('relay golden - breaker + transformer + relay coexist', () => {
  const r = runTakeoff(artifact)
  it('breaker prices; transformer + 3 relays scope_pending; nothing mis-priced', () => {
    expect(r.matchedLines).toHaveLength(1)                       // the breaker
    expect((r.scopePendingLines ?? []).length).toBe(4)          // transformer + 3 relays
  })
  it('the 87T relay has differential provisional default; the bare relay has none', () => {
    const sp = (r.scopePendingLines ?? [])
    const diff = sp.find((s) => s.line.signature.kind === 'relay' && (s.line.signature as any).role === 'differential')!
    const bare = sp.find((s) => s.line.signature.kind === 'relay' && (s.line.signature as any).role === 'unknown')!
    expect(diff.provisionalDefaultRef).toBe('Protective Relay (Differential Protection)')
    expect(bare.provisionalDefaultRef).toBeUndefined()
  })
  it('no-default relay renders provisional=none in BOTH JSON and text', () => {
    const report = reconcile(artifact, r, { bid_cents: 0 })
    // JSON: at least one scope-pending entry carries no provisional default
    expect(report.scopePending.some((s) => s.provisionalDefaultRef === undefined)).toBe(true)
    // TEXT (human report): the renderer must print provisional=none, never provisional=undefined
    const text = renderReportText(report)
    expect(text).toContain('provisional=none')
    expect(text).not.toContain('provisional=undefined')
  })
})
```

- [ ] **Step 3: Run + verify**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test relay-golden'`
Expected: PASS.

- [ ] **Step 4: Full suite + both typechecks (final per-task gate)**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: PASS - full suite green; both typechecks clean; breaker + transformer goldens byte-identical.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-relay-family && git add -A && git -c user.name="jasonlswenson-sys" -c user.email="jasonlswenson@gmail.com" commit -m "test(takeoff): relay golden - breaker+transformer+relay coexistence + no-default render" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

## Hard-gate tests (operator-pinned + Rev 2 review; the final review verifies all present + green)

1. bare `87T` is NOT counted (Task 4).
2. `candidateKind:'relay'` + `87T` -> scope_pending differential (Task 4).
3. relay without voltage never emits `missing_voltage` (Task 4).
4. no-default scope_pending cleanly represented in JSON AND text - `renderReportText` prints `provisional=none`, never `provisional=undefined` (Tasks 3, 6).
5. exact relay refs resolve in the live seed (Task 1).
6. breaker AND transformer goldens byte-identical (every task).
7. operations-web typecheck stays green (Tasks 3, 4, 6 - the cross-package gate).
8. legacy single-function EM/solid-state relay -> electromechanical role/tier (Tasks 2, 4) - the EM tier is reachable, not dead.
9. standalone transformer-accessory pressure relay is NOT a priced relay device (Task 4 - `RELAY_ACCESSORY` exclusion).
10. `matchBreaker` AND `matchTransformer` are type- (`@ts-expect-error`) AND runtime-defended against a relay signature (Task 5).

## Self-Review notes

- Spec coverage: extraction widen (T2), signature union + optional voltage (T2/T3), device-first recognition + parsers (T4), matchRelay optional default (T2), quantify branch (T3), scope_pending/catalog_gap threading + no-default contract + report renderer (T3), ASSESS_TO_REASON named task (T4), cross-family guards (T5), golden + Gate-2 stand-in (T6). All spec sections mapped.
- Type consistency: `RelayScopeMatch.defaultRef?` (T2) <-> `ScopePendingLine.provisionalDefaultRef?` (T3) <-> emit stamping `scope.defaultRef` (T3) <-> `ReconciliationReport.scopePending[].provisionalDefaultRef?` + renderer `?? 'none'` (T3) - consistent. `RelayRole` values (T2) == `ROLE_TO_TIER` keys (T1) == `deriveRole` returns (T4) - consistent. `AssessmentCode` additions (T4) == `ASSESS_TO_REASON` entries (T4) - consistent.
- Sequencing: each task compiles + is green. T3 is the only task that widens the union; it carries every `kind`-exhaustive consumer change (emit, specKey) so typecheck never breaks. No relay signatures flow until T4, so breaker/transformer goldens are inert through T1-T3.
