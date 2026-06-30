# Switch / Disconnect Family (V1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admit the 6th apparatus family (switches / disconnects, NETA 7.5) into `packages/estimator-takeoff` so a recognized non-automatic switch is counted per device and routed to a Gate-2 voltage-x-type scope decision (never auto-priced), while the breaker recognizer and all five prior families stay byte-identical.

**Architecture:** Reuse the relay/GFP/instrument scope_pending machinery. Add a sixth signature `kind:'switch'`, a device-first switch recognizer routed AFTER the five prior families whose first actions are an EXCLUSION pass + a switch-local breaker-conflict guard, a voltage-x-type match group, and catalog-gap handling. The hard part is recognition: "switch" is the most overloaded device word in the catalog, and switches share the SF6/vacuum/air medium tokens with the existing `BREAKER_HINT`, so the switch route must intercept anchored switch rows before the breaker fallback WITHOUT touching breaker behavior.

**Tech Stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- ASCII-only in all authored code/comments AND engine-emitted strings (no em-dashes). Verbatim source DATA may be UTF-8.
- Breaker AND transformer AND relay AND GFP AND instrument-transformer goldens BYTE-IDENTICAL after every task. Five prior families regression-guard the sixth.
- No new catalog refs, no new hours. V1 uses the 11 existing switch refs only, matched by EXACT ref STRING (never by section; `PDU (Power Distribution Unit)` also sits at firm 7.5).
- The 11 verbatim seed refs: `Switch LV - Fused Disconnect`; `Switch LV - Fused Disconnect (Open)`; `Switch MV - Fused Disconnect`; `Switch MV - Open`; `Switch MV - Cutout`; `Switch MV - Oil Insulated`; `Switch MV - Motor Operated`; `Switch (SF6) - Medium Voltage`; `Switch (Pad Mount Vista) - Medium Voltage`; `Switch HV - Open`; `Switch HV - Motor Operated`.
- Switches never auto-price: every recognized switch -> `scope_pending` (candidate group + optional default) or `switch_catalog_gap`. No "matched" switch line in V1.
- Recognition is device-first (compound anchor), NEVER the bare token "switch". `NF` is an attribute, never a standalone anchor.
- The breaker-conflict guard keys on the UNAMBIGUOUS subset + frame/trip + trip functions + NON_BREAKER, NOT the shared SF6/vacuum/air medium. `BREAKER_HINT`/`FRAME_TRIP`/`NON_BREAKER` are NOT modified.
- Conservative default: `provisionalDefaultRef` set ONLY with a voltage class AND a specific type token; generic anchor or absent voltage -> group, no default.
- `SWITCH_R1_RATIFIED = false` (provisional, fail-closed; never auto-priced).
- Gates (host): `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (cross-package false-green gate).
- Build discipline: host worktree `/home/olares/code/apex/apex-switch` (branch `estimator-takeoff/switch-family-admission`); edit via scp-down/local-Edit/scp-up; `export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH`; commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>` + the `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer; merge OPERATOR-GATED.
- TDD: write the failing test, watch it fail for the right reason, implement minimal, watch it pass, commit. Cross-engine (Codex) IRP before merge.

**Task ordering rationale (the discriminated-union coupling):** `SwitchSignature` is defined as a standalone interface in Task 1 but is NOT added to the `ApparatusSignature` union until Task 3. Widening the union breaks `quantify.specKey` (its transformer fall-through would treat a switch as a transformer) and `emit.ts` (`const tsig: TransformerSignature = sig`), so the union widening + the `quantify`/`emit` switch branches + the `buckets` codes MUST land together in Task 3 to keep the build green at every commit. Task 1 (catalog) and Task 2 (recognition predicates) are pure additions that compile green without touching the union.

---

### Task 1: Catalog - the 11 refs, SWITCH_GROUPS, matchSwitch

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/types.ts` (add `SwitchType` + the `SwitchSignature` interface; do NOT touch the `ApparatusSignature` union yet)
- Create: `packages/estimator-takeoff/src/catalog/switch-map.data.ts`
- Create: `packages/estimator-takeoff/src/catalog/switch-map.ts`
- Test: `packages/estimator-takeoff/test/switch-map.test.ts`

**Interfaces:**
- Consumes: `VoltageClass` from `signature/types`.
- Produces: `SwitchType`, `SwitchSignature` (interface, not yet in the union); `SWITCH_REFS`, `SWITCH_GROUPS`, `SWITCH_R1_RATIFIED` from `catalog/switch-map.data`; `SwitchScopeMatch`, `matchSwitch(sig: SwitchSignature): SwitchScopeMatch | null` from `catalog/switch-map`.

- [ ] **Step 1: Add the SwitchType + SwitchSignature interface to `signature/types.ts`** (after the `InstrumentTransformerSignature` block, before the `ApparatusSignature` union line). Do NOT add it to the union yet.

```ts
export type SwitchType =
  | 'fused_disconnect' | 'open' | 'oil' | 'sf6' | 'cutout'
  | 'motor_operated' | 'vista' | 'vacuum' | 'unknown'
export interface SwitchSignature extends BaseSignature {
  kind: 'switch'
  switchType: SwitchType
  fused?: boolean        // CONTRACT: NF -> false; fused/fusible -> true; undefined when unstated. Disambiguates the LV non-fused gap.
  ampRating?: number     // evidence/display only (continuous A; NOT a frame/trip pair)
  // voltageClass stays optional (inherited): contextual; drives the group when present, never gates.
}
```

- [ ] **Step 2: Write the failing test `test/switch-map.test.ts`** (matchSwitch: groups, conservative default, LV non-fused gap, missing-key gap, air-via-open switchType, exact-ref + PDU overload).

```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { matchSwitch } from '../src/catalog/switch-map'
import { SWITCH_REFS, SWITCH_GROUPS, SWITCH_R1_RATIFIED } from '../src/catalog/switch-map.data'
import type { SwitchSignature } from '../src/signature/types'

const base = { voltageBasis: 'detected' as const, source: { sheet: 's', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' } }
const sig = (o: Partial<SwitchSignature>): SwitchSignature => ({ kind: 'switch', switchType: 'unknown', ...base, ...o })

describe('matchSwitch', () => {
  it('MV fused disconnect -> the MV fused-disconnect ref + default', () => {
    const m = matchSwitch(sig({ switchType: 'fused_disconnect', voltageClass: 'MV' }))
    expect(m).not.toBeNull()
    expect(m!.group).toEqual(['Switch MV - Fused Disconnect'])
    expect(m!.defaultRef).toBe('Switch MV - Fused Disconnect')
  })
  it('LV fused disconnect default is the ENCLOSED tier, not the (Open) variant', () => {
    const m = matchSwitch(sig({ switchType: 'fused_disconnect', voltageClass: 'LV' }))
    expect(m!.group).toEqual(['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)'])
    expect(m!.defaultRef).toBe('Switch LV - Fused Disconnect')
  })
  it('SF6 / cutout / oil / motor_operated / vista MV map to their exact refs', () => {
    expect(matchSwitch(sig({ switchType: 'sf6', voltageClass: 'MV' }))!.defaultRef).toBe('Switch (SF6) - Medium Voltage')
    expect(matchSwitch(sig({ switchType: 'cutout', voltageClass: 'MV' }))!.defaultRef).toBe('Switch MV - Cutout')
    expect(matchSwitch(sig({ switchType: 'oil', voltageClass: 'MV' }))!.defaultRef).toBe('Switch MV - Oil Insulated')
    expect(matchSwitch(sig({ switchType: 'motor_operated', voltageClass: 'MV' }))!.defaultRef).toBe('Switch MV - Motor Operated')
    expect(matchSwitch(sig({ switchType: 'vista', voltageClass: 'MV' }))!.defaultRef).toBe('Switch (Pad Mount Vista) - Medium Voltage')
  })
  it('air switch maps via switchType open: MV/HV -> Open default; LV -> gap', () => {
    expect(matchSwitch(sig({ switchType: 'open', voltageClass: 'MV' }))!.defaultRef).toBe('Switch MV - Open')
    expect(matchSwitch(sig({ switchType: 'open', voltageClass: 'HV' }))!.defaultRef).toBe('Switch HV - Open')
    expect(matchSwitch(sig({ switchType: 'open', voltageClass: 'LV' }))).toBeNull()  // open:LV absent -> gap
  })
  it('generic anchor (switchType unknown) + voltage -> group with NO default (D2)', () => {
    const m = matchSwitch(sig({ switchType: 'unknown', voltageClass: 'MV' }))
    expect(m!.group.length).toBeGreaterThan(1)
    expect(m!.defaultRef).toBeUndefined()
  })
  it('absent voltage -> wider group, NO default', () => {
    const m = matchSwitch(sig({ switchType: 'sf6' }))   // no voltageClass
    expect(m!.defaultRef).toBeUndefined()
    expect(m!.group.length).toBeGreaterThan(0)
  })
  it('LV non-fused disconnect -> catalog_gap (LV is fused-only)', () => {
    expect(matchSwitch(sig({ switchType: 'unknown', fused: false, voltageClass: 'LV' }))).toBeNull()
  })
  it('vacuum / HV fused/cutout/oil/sf6 -> catalog_gap (missing key)', () => {
    expect(matchSwitch(sig({ switchType: 'vacuum', voltageClass: 'MV' }))).toBeNull()
    expect(matchSwitch(sig({ switchType: 'fused_disconnect', voltageClass: 'HV' }))).toBeNull()
    expect(matchSwitch(sig({ switchType: 'cutout', voltageClass: 'HV' }))).toBeNull()
  })
  it('all 11 SWITCH_REFS resolve verbatim in the live seed; PDU also sits at firm 7.5 (string-match proof)', () => {
    const seedPath = require.resolve('@apex/estimator-core/src/catalog/equipment-models.seed.json')
    const seed = JSON.parse(readFileSync(seedPath, 'utf8'))
    const rows: any[] = Array.isArray(seed) ? seed : (seed.models ?? seed.equipmentModels ?? Object.values(seed).find((v) => Array.isArray(v)))
    const names = new Set(rows.map((r) => r.ref ?? r.name ?? r.apparatus ?? r.model))
    for (const ref of SWITCH_REFS) expect(names.has(ref), `seed missing ${ref}`).toBe(true)
    expect(names.has('PDU (Power Distribution Unit)')).toBe(true)  // the 12th ref at 7.5 -> must match by STRING, not section
  })
  it('SWITCH_R1_RATIFIED is false (provisional, fail-closed)', () => {
    expect(SWITCH_R1_RATIFIED).toBe(false)
  })
})
```

- [ ] **Step 3: Run the test, verify it FAILS** (modules not found).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test -- switch-map'`
Expected: FAIL - cannot resolve `../src/catalog/switch-map`.

- [ ] **Step 4: Create `catalog/switch-map.data.ts`** (mirrors `instrument-transformer-map.data.ts`).

```ts
// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED. Switches / disconnects (NETA 7.5).
// Matched by exact STRING ONLY: a 12th ref, 'PDU (Power Distribution Unit)', also sits at firm 7.5, so a
// section match would sweep PDU. Section is NOISE here; only the ref string is authoritative.
export const SWITCH_REFS = [
  'Switch LV - Fused Disconnect',
  'Switch LV - Fused Disconnect (Open)',
  'Switch MV - Fused Disconnect',
  'Switch MV - Open',
  'Switch MV - Cutout',
  'Switch MV - Oil Insulated',
  'Switch MV - Motor Operated',
  'Switch (SF6) - Medium Voltage',
  'Switch (Pad Mount Vista) - Medium Voltage',
  'Switch HV - Open',
  'Switch HV - Motor Operated',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: candidate ref-GROUP keyed by `${SwitchType}:${VoltageClass}` plus
// generic `any:${VoltageClass}` (generic anchor, no type token) and `any:unknown` (no voltage). The conservative
// default (Task 3 matchSwitch) is the FIRST ref in a type-x-voltage group; generic/no-voltage -> no default.
// GAPS are encoded as ABSENT keys -> matchSwitch returns null -> switch_catalog_gap:
//   vacuum:* (no vacuum ref); fused_disconnect:HV / cutout:HV / oil:HV / sf6:HV (HV has only Open + Motor-Operated);
//   open:LV (LV has only the fused refs). The LV non-fused gap (fused:false at LV) is handled in matchSwitch.
export const SWITCH_GROUPS: Record<string, string[]> = {
  'fused_disconnect:LV': ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)'],
  'fused_disconnect:MV': ['Switch MV - Fused Disconnect'],
  'open:MV': ['Switch MV - Open'],
  'open:HV': ['Switch HV - Open'],
  'cutout:MV': ['Switch MV - Cutout'],
  'oil:MV': ['Switch MV - Oil Insulated'],
  'motor_operated:MV': ['Switch MV - Motor Operated'],
  'motor_operated:HV': ['Switch HV - Motor Operated'],
  'sf6:MV': ['Switch (SF6) - Medium Voltage'],
  'vista:MV': ['Switch (Pad Mount Vista) - Medium Voltage'],
  'any:LV': ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)'],
  'any:MV': ['Switch MV - Fused Disconnect', 'Switch MV - Open', 'Switch MV - Cutout', 'Switch MV - Oil Insulated', 'Switch MV - Motor Operated', 'Switch (SF6) - Medium Voltage', 'Switch (Pad Mount Vista) - Medium Voltage'],
  'any:HV': ['Switch HV - Open', 'Switch HV - Motor Operated'],
  'any:unknown': [
    'Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)', 'Switch MV - Fused Disconnect',
    'Switch MV - Open', 'Switch MV - Cutout', 'Switch MV - Oil Insulated', 'Switch MV - Motor Operated',
    'Switch (SF6) - Medium Voltage', 'Switch (Pad Mount Vista) - Medium Voltage', 'Switch HV - Open', 'Switch HV - Motor Operated',
  ],
}

// Operator flips when the SME confirms the voltage-x-type -> default-ref table + the open-vs-enclosed convention + the bounded gaps.
export const SWITCH_R1_RATIFIED = false
```

- [ ] **Step 5: Create `catalog/switch-map.ts`** (matchSwitch; conservative default + LV non-fused gap + missing/empty-key gap).

```ts
import type { SwitchSignature, SwitchType, VoltageClass } from '../signature/types'
import { SWITCH_GROUPS } from './switch-map.data'

export interface SwitchScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select switch/disconnect voltage class and construction type (fused/open/oil/SF6/cutout/motor-operated/Vista) and confirm the priced ref; switches are priced per device and are never auto-priced.'

// LV is fused-only (both LV refs are "Fused Disconnect"), so a definitively non-fused LV disconnect has no priced
// home. MV/HV are NOT gated here: "Switch MV - Open" / "Switch HV - Open" are plausible non-fused homes.
function isNonFusedLvGap(sig: SwitchSignature): boolean {
  return sig.fused === false && sig.voltageClass === 'LV'
    && (sig.switchType === 'unknown' || sig.switchType === 'fused_disconnect')
}

export function matchSwitch(sig: SwitchSignature): SwitchScopeMatch | null {
  if (isNonFusedLvGap(sig)) return null                         // D1: non-fused LV -> catalog_gap
  const vc: VoltageClass | 'unknown' = sig.voltageClass ?? 'unknown'
  const typeKey: SwitchType | 'any' = sig.switchType === 'unknown' ? 'any' : sig.switchType
  const group = SWITCH_GROUPS[`${typeKey}:${vc}`]
  if (!group || group.length === 0) return null                 // missing OR empty key -> catalog_gap (vacuum, HV fused/cutout/oil/sf6, open:LV)
  // D2 conservative default: ONLY with a voltage class AND a specific type token. The FIRST group ref is the
  // conservative tier (e.g. LV fused-disconnect default is the ENCLOSED ref, not the "(Open)" variant).
  const defaultRef = (sig.voltageClass !== undefined && sig.switchType !== 'unknown') ? group[0] : undefined
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
```

- [ ] **Step 6: Run the test, verify it PASSES; run the full estimator-takeoff suite (all five prior goldens still green).**

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck'`
Expected: PASS (new switch-map tests green; all prior tests unchanged; typecheck clean - the union is NOT yet widened).

- [ ] **Step 7: Commit.**

```bash
git add packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/catalog/switch-map.data.ts packages/estimator-takeoff/src/catalog/switch-map.ts packages/estimator-takeoff/test/switch-map.test.ts
git commit -m "feat(switch): catalog - 11 refs, SWITCH_GROUPS, matchSwitch (Task 1)"
```

---

### Task 2: Recognition predicates - regexes, looksLikeSwitch, parse functions

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts` (add the SWITCH_* regexes + `looksLikeSwitch` + `parseSwitchType` + `parseFused` + `parseAmpRating` as standalone exported functions; do NOT add `assessSwitch` or the `assessCore` route yet)
- Test: `packages/estimator-takeoff/test/switch-recognition.test.ts`

**Interfaces:**
- Consumes: `ExtractedApparatus` from `extraction/types`; `SwitchType` from `signature/types`.
- Produces (exported from `normalize.ts`): `looksLikeSwitch(x: ExtractedApparatus): boolean`; `parseSwitchType(raw: string): SwitchType`; `parseFused(raw: string): boolean | undefined`; `parseAmpRating(raw: string): number | undefined`. (Exported so Task 2 can unit-test them; consumed internally by `assessSwitch` in Task 3.)

- [ ] **Step 1: Write the failing test `test/switch-recognition.test.ts`.**

```ts
import { describe, it, expect } from 'vitest'
import { looksLikeSwitch, parseSwitchType, parseFused, parseAmpRating } from '../src/signature/normalize'
import type { ExtractedApparatus } from '../src/extraction/types'

const row = (raw: string, o: Partial<ExtractedApparatus> = {}): ExtractedApparatus =>
  ({ raw, tag: o.tag ?? 'D-1', sheet: 's', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })

describe('looksLikeSwitch - device-first, never the bare token', () => {
  it('compound anchors + tag -> true', () => {
    for (const r of ['Fused Disconnect', 'Safety Switch', 'Load Break Switch', 'LBS', 'Disconnect Switch', 'SF6 Switch', 'Air Switch', 'Cutout', 'Oil Switch', 'Non-Fused Disconnect'])
      expect(looksLikeSwitch(row(r)), r).toBe(true)
  })
  it('candidateKind switch -> true', () => {
    expect(looksLikeSwitch(row('opaque', { candidateKind: 'switch' }))).toBe(true)
  })
  it('bare "switch" with no qualifier -> false', () => {
    expect(looksLikeSwitch(row('switch'))).toBe(false)
  })
  it('T1 NF is not a standalone anchor', () => {
    expect(looksLikeSwitch(row('NF', { tag: 'NF-1' }))).toBe(false)       // bare NF tag
    expect(looksLikeSwitch(row('feeder NF 400'))).toBe(false)             // raw merely contains NF
    expect(looksLikeSwitch(row('NF Disconnect'))).toBe(true)              // NF + a real anchor -> switch
  })
  it('T3 overload families excluded FIRST', () => {
    for (const r of ['Circuit Switcher MV', 'Automatic Transfer Switch', 'Manual Transfer Switch', 'Switchgear - Medium Voltage', 'Switchboard - Low Voltage'])
      expect(looksLikeSwitch(row(r)), r).toBe(false)
  })
  it('anchor without a tag -> false', () => {
    expect(looksLikeSwitch(row('Fused Disconnect', { tag: undefined }))).toBe(false)
  })
  it('another producer signal -> false (defers)', () => {
    expect(looksLikeSwitch(row('Disconnect Switch', { candidateKind: 'breaker' }))).toBe(false)
  })
})

describe('parseSwitchType - precedence (R1 provisional)', () => {
  it('maps the construction tokens', () => {
    expect(parseSwitchType('Pad Mount Vista MV')).toBe('vista')
    expect(parseSwitchType('Motor Operated Disconnect')).toBe('motor_operated')
    expect(parseSwitchType('M.O. switch')).toBe('motor_operated')
    expect(parseSwitchType('SF6 Switch')).toBe('sf6')
    expect(parseSwitchType('Oil Switch')).toBe('oil')
    expect(parseSwitchType('Cutout')).toBe('cutout')
    expect(parseSwitchType('Vacuum Switch')).toBe('vacuum')
    expect(parseSwitchType('Fused Disconnect')).toBe('fused_disconnect')
    expect(parseSwitchType('Air Switch')).toBe('open')          // air switch -> open
    expect(parseSwitchType('Open Switch')).toBe('open')
    expect(parseSwitchType('Disconnect')).toBe('unknown')       // generic anchor
  })
  it('actuation outranks medium (motor-operated SF6 -> motor_operated)', () => {
    expect(parseSwitchType('Motor Operated SF6 Switch MV')).toBe('motor_operated')
  })
})

describe('parseFused / parseAmpRating', () => {
  it('NF -> false; fused/fusible -> true; else undefined', () => {
    expect(parseFused('NF Disconnect')).toBe(false)
    expect(parseFused('Non-Fused Disconnect')).toBe(false)
    expect(parseFused('Fused Disconnect')).toBe(true)
    expect(parseFused('Fusible Switch')).toBe(true)
    expect(parseFused('Disconnect Switch')).toBeUndefined()
  })
  it('parseAmpRating reads PLAIN amps only - AF/AT are NOT amps', () => {
    expect(parseAmpRating('Fused Disconnect 400A')).toBe(400)
    expect(parseAmpRating('Disconnect 800 A')).toBe(800)
    expect(parseAmpRating('switch 800AF')).toBeUndefined()
    expect(parseAmpRating('switch 800AT')).toBeUndefined()
  })
})
```

- [ ] **Step 2: Run the test, verify it FAILS** (functions not exported).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test -- switch-recognition'`
Expected: FAIL - `looksLikeSwitch` is not exported from normalize.

- [ ] **Step 3: Add the regexes + predicates to `normalize.ts`** (place the regexes after `INSTRUMENT_TAG` at line ~20; place the functions near the other `looksLike*`/`parse*` helpers). Import `SwitchType` in the existing type-import line from `./types`.

```ts
// --- Switch / disconnect family (NETA 7.5) ---
// Overload families EXCLUDED FIRST (T3): "switch" appears in switchboard/switchgear (7.1 assemblies),
// transfer switch (7.18/22), circuit switcher (7.3). None are 7.5 switches.
const SWITCH_EXCLUDE = /\b(circuit\s+switcher|transfer\s+switch|switchgear|switchboard)\b/i
// COMPOUND switch-device anchors - NEVER the bare token "switch".
const SWITCH_DEVICE = /\b(disconnect(\s+switch)?|fus(ed|ible)\s+switch|safety\s+switch|load[\s-]?break\s+switch|LBS|isolat(ion|ing)\s+switch|knife\s+switch|air\s+switch|oil\s+switch|SF6\s+switch|cutout|non[\s-]?fused\s+disconnect)\b/i
// The UNAMBIGUOUS breaker subset for the switch-local conflict guard - DELIBERATELY excludes the shared
// vacuum/SF6/air-frame medium tokens (those are switch construction evidence, not conflict signals).
const SWITCH_BREAKER_CONFLICT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|GB|FB)\b/i
// A single numbered frame/trip token (catches 800AF or 800AT even WITHOUT the full FRAME_TRIP pair).
const SWITCH_FRAME_TRIP = /\b\d{2,6}\s*A[FT]\b/i
// A breaker trip-function descriptor on a switch row = conflict (mirrors parseFunctions' L(SIGE) shape;
// the lookahead + \b spare anchors like "LBS" and English words like "LIGHT").
const SWITCH_TRIP_FN = /\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i
// The non-fused attribute - consumed ONLY when a real anchor is present (looksLikeSwitch gates it).
const SWITCH_NF = /\bN\.?F\.?\b|\bnon[\s-]?fused\b/i
// PLAIN continuous amps ONLY: the \bA\b boundary means 800AF / 800AT do NOT match (AF/AT can never be amps).
const SWITCH_AMP = /(?<!\d)(\d{2,6})\s*A\b/i

export function looksLikeSwitch(x: ExtractedApparatus): boolean {
  if (SWITCH_EXCLUDE.test(x.raw)) return false                          // T3: overload families excluded FIRST
  if (x.candidateKind === 'switch') return true                         // explicit producer signal wins
  if (x.candidateKind !== undefined && x.candidateKind !== 'switch') return false  // defer to other producers
  return SWITCH_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0       // compound anchor + tag
}

export function parseSwitchType(raw: string): SwitchType {
  if (/pad[\s-]?mount\s+vista|\bvista\b/i.test(raw)) return 'vista'
  if (/motor[\s-]?operated|\bM\.?O\.?\b/i.test(raw)) return 'motor_operated'
  if (/\bSF6\b/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/\bcutout\b/i.test(raw)) return 'cutout'
  if (/\bvacuum\b/i.test(raw)) return 'vacuum'                          // recognized; no priced ref -> gap
  if (/fus(ed|ible)/i.test(raw)) return 'fused_disconnect'
  if (/air\s+switch|\bopen\b/i.test(raw)) return 'open'                 // air-open switches ARE the firm "Open" refs
  return 'unknown'                                                       // generic disconnect/switch anchor -> group, no default
}

export function parseFused(raw: string): boolean | undefined {
  if (SWITCH_NF.test(raw)) return false
  if (/fus(ed|ible)/i.test(raw)) return true
  return undefined
}

export function parseAmpRating(raw: string): number | undefined {
  const m = raw.match(SWITCH_AMP)
  return m ? Number(m[1]) : undefined
}
```

- [ ] **Step 4: Run the test, verify it PASSES; run the full suite + typecheck.**

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck'`
Expected: PASS (switch-recognition green; prior tests unchanged; typecheck clean - the new functions are exported but unused by the pipeline yet).

- [ ] **Step 5: Commit.**

```bash
git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/test/switch-recognition.test.ts
git commit -m "feat(switch): recognition predicates - regexes, looksLikeSwitch, parse* (Task 2)"
```

---

### Task 3: Assessor + union widening + pipeline wiring (the coupled core)

**Files:**
- Modify: `packages/estimator-takeoff/src/signature/normalize.ts` (add `assessSwitch`, the `assessCore` route, the two `AssessmentCode` members)
- Modify: `packages/estimator-takeoff/src/signature/types.ts` (widen the `ApparatusSignature` union to include `SwitchSignature`)
- Modify: `packages/estimator-takeoff/src/extraction/types.ts:15` + `packages/estimator-takeoff/src/extraction/parse.ts:58` (candidateKind += `'switch'`)
- Modify: `packages/estimator-takeoff/src/quantify/quantify.ts` (specKey switch branch + pickAuthoritative richSwitch)
- Modify: `packages/estimator-takeoff/src/buckets/types.ts` (codes + ScopePendingLine/ApparatusDisposition fields)
- Modify: `packages/estimator-takeoff/src/emit/emit.ts` (imports + ASSESS_TO_REASON entries + the `kind === 'switch'` match-loop branch)
- Test: `packages/estimator-takeoff/test/normalize-switch.test.ts` (assessor + routing)
- Test: `packages/estimator-takeoff/test/quantify-switch.test.ts` (specKey + the #23 rich-switch representative)

**Interfaces:**
- Consumes: `looksLikeSwitch`, `parseSwitchType`, `parseFused`, `parseAmpRating` (Task 2); `matchSwitch`, `SWITCH_R1_RATIFIED` (Task 1); `SwitchSignature` (Task 1).
- Produces: `assessSwitch` (internal); `AssessmentCode` += `'switch_recognized' | 'switch_parent_conflict'`; the widened `ApparatusSignature` union; the emit/quantify switch handling; `OperatorQuestionCode`/`DispositionReasonCode` += `'switch_scope_pending' | 'switch_catalog_gap' | 'switch_parent_conflict'`; `TakeoffFinding.code` += `'switch_catalog_gap'`.

- [ ] **Step 1: Write the failing test `test/normalize-switch.test.ts`** (assessSwitch recognized + conflict-guard both directions including single AF/AT and trip-fn-only; assessCore routing; SF6-switch interception).

```ts
import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
import type { ExtractedApparatus } from '../src/extraction/types'

const row = (raw: string, o: Partial<ExtractedApparatus> = {}): ExtractedApparatus =>
  ({ raw, tag: o.tag ?? 'D-1', sheet: 's', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: o.busVoltageV, ...o })

describe('assessSwitch via assessApparatus', () => {
  it('fused disconnect -> switch signature (switch_recognized)', () => {
    const a = assessApparatus(row('Fused Disconnect 400A', { busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('switch')
    expect(a.assessmentCode).toBe('switch_recognized')
    if (a.signature?.kind === 'switch') {
      expect(a.signature.switchType).toBe('fused_disconnect')
      expect(a.signature.fused).toBe(true)
      expect(a.signature.ampRating).toBe(400)
      expect(a.signature.voltageClass).toBe('LV')
    }
  })
  it('SF6 switch is intercepted by the switch route (NOT the breaker fallback)', () => {
    const a = assessApparatus(row('SF6 Switch', { busVoltageV: 15000 }))
    expect(a.signature?.kind).toBe('switch')   // SF6 is in BREAKER_HINT, but the anchored switch route runs first
    if (a.signature?.kind === 'switch') expect(a.signature.switchType).toBe('sf6')
  })
  it('T2 conflict - both directions', () => {
    // switch anchor + full AF/AT pair -> parent conflict, null signature
    expect(assessApparatus(row('Fused Disconnect 800AF/800AT LSIG')).signature).toBeNull()
    expect(assessApparatus(row('Fused Disconnect 800AF/800AT LSIG')).assessmentCode).toBe('switch_parent_conflict')
    // switch anchor + SINGLE 800AF token (no pair) -> conflict
    expect(assessApparatus(row('Disconnect Switch 800AF')).assessmentCode).toBe('switch_parent_conflict')
    // switch anchor + trip-function-only (no AF/AT) -> conflict
    expect(assessApparatus(row('Disconnect Switch LSIG')).assessmentCode).toBe('switch_parent_conflict')
    // switch anchor + unambiguous breaker hint -> conflict
    expect(assessApparatus(row('Disconnect Switch VCB')).assessmentCode).toBe('switch_parent_conflict')
    // a real breaker with NO switch anchor -> NOT routed to switch (stays breaker path)
    const b = assessApparatus(row('800AF/800AT LSIG', { busVoltageV: 480 }))
    expect(b.signature?.kind).toBe('breaker')
  })
  it('generic disconnect + voltage, no type -> recognized switch, switchType unknown', () => {
    const a = assessApparatus(row('Disconnect Switch', { busVoltageV: 15000 }))
    expect(a.signature?.kind).toBe('switch')
    if (a.signature?.kind === 'switch') expect(a.signature.switchType).toBe('unknown')
  })
  it('overload families fall through (not switch, not crashed)', () => {
    expect(assessApparatus(row('Circuit Switcher MV')).signature).toBeNull()
    expect(assessApparatus(row('Switchgear - Medium Voltage')).signature).toBeNull()
  })
})
```

Also write `test/quantify-switch.test.ts` (the #23 rich-switch representative + specKey separation):

```ts
import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { SwitchSignature } from '../src/signature/types'

const sw = (o: Partial<SwitchSignature>, i: number): SwitchSignature => ({
  kind: 'switch', switchType: 'unknown', voltageBasis: 'detected', inputIndex: i, tag: 'DS-1', voltageClass: 'LV',
  source: { sheet: o.source?.evidence === 'one-line' ? 'one' : 'sch', page: 1, bbox: [i, 0, i + 1, 1], evidence: o.source?.evidence ?? 'panel-schedule' },
  ...o,
})

describe('quantify switch', () => {
  it('#23 rich-switch keeps fused:false evidence over a sparse same-tag occurrence', () => {
    // an authoritative schedule row carrying fused:false + a sparser authoritative one-line occurrence, same tag
    const rich: SwitchSignature = sw({ fused: false, source: { sheet: 'sch', page: 1, bbox: [0, 0, 1, 1], evidence: 'panel-schedule' } }, 0)
    const sparse: SwitchSignature = sw({ fused: undefined, source: { sheet: 'one', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' } }, 1)
    const { lines } = quantify([sparse, rich])
    expect(lines.length).toBe(1)
    const rep = lines[0]!.signature
    expect(rep.kind).toBe('switch')
    if (rep.kind === 'switch') expect(rep.fused).toBe(false)   // the fused:false representative wins -> LV gap proof holds
  })
  it('specKey separates by switchType / voltage / fused', () => {
    const a = sw({ switchType: 'sf6', voltageClass: 'MV', tag: 'A', source: { sheet: 'one', page: 1, bbox: [0,0,1,1], evidence: 'one-line' } }, 0)
    const b = sw({ switchType: 'open', voltageClass: 'MV', tag: 'B', source: { sheet: 'one', page: 1, bbox: [1,0,2,1], evidence: 'one-line' } }, 1)
    const { lines } = quantify([a, b])
    expect(lines.length).toBe(2)
  })
})
```

- [ ] **Step 2: Run the tests, verify they FAIL** (switch never recognized; quantify treats switch as transformer pre-union-widening, or fails to compile).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test -- normalize-switch quantify-switch'`
Expected: FAIL - `a.signature?.kind` is not `'switch'` (no route yet); quantify-switch fails (union not yet widened).

- [ ] **Step 3: Add `assessSwitch` + the two AssessmentCode members + the assessCore route to `normalize.ts`.** Add the AssessmentCode members `'switch_recognized'` and `'switch_parent_conflict'` to the `AssessmentCode` union. Add `assessSwitch` near the other `assess*` functions:

```ts
function assessSwitch(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // CONFLICT GUARD FIRST (switch routes before the breaker fallback): a misrouted parent surfaces a question,
  // never a silent switch scope_pending and never suppressing a real breaker. Keyed on the UNAMBIGUOUS breaker
  // subset + full pair + single AF/AT token + trip functions + NON_BREAKER - NOT the shared SF6/vacuum/air medium.
  if (SWITCH_BREAKER_CONFLICT.test(x.raw) || FRAME_TRIP.test(x.raw) || SWITCH_FRAME_TRIP.test(x.raw)
      || SWITCH_TRIP_FN.test(x.raw) || NON_BREAKER.test(x.raw)) {
    return { signature: null, isBreakerShaped: false, assessmentCode: 'switch_parent_conflict',
      questions: [q(x, 'Label names a switch/disconnect but the row carries a breaker signal (frame/trip, trip functions, or a breaker/parent token) - confirm device type before counting.', 'switch_parent_conflict')] }
  }
  const sig: SwitchSignature = {
    kind: 'switch',
    switchType: parseSwitchType(x.raw),
    fused: parseFused(x.raw),
    ampRating: parseAmpRating(x.raw),
    voltageClass: classifyVoltage(x.busVoltageV), voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag, source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'switch_recognized', questions: [] }
}
```

Insert the route in `assessCore` AFTER the `looksLikeRelay` block and BEFORE the `NON_BREAKER` block (currently normalize.ts ~L354-356):

```ts
  if (looksLikeSwitch(x)) {
    return assessSwitch(x, voltageBasis)
  }
```

Add `SwitchSignature` to the type-import line from `./types`.

- [ ] **Step 4: Widen the union + wire consumers (this is the coupled change that keeps the build green).**

`signature/types.ts` - widen the union:
```ts
export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature | InstrumentTransformerSignature | SwitchSignature
```

`extraction/types.ts:15` - widen candidateKind:
```ts
  candidateKind?: 'breaker' | 'transformer' | 'relay' | 'gfp' | 'instrument_transformer' | 'switch'
```

`extraction/parse.ts:58` - widen the guard:
```ts
  if (r['candidateKind'] !== undefined && r['candidateKind'] !== 'breaker' && r['candidateKind'] !== 'transformer' && r['candidateKind'] !== 'relay' && r['candidateKind'] !== 'gfp' && r['candidateKind'] !== 'instrument_transformer' && r['candidateKind'] !== 'switch') fail(`${p}.candidateKind`, "'breaker'|'transformer'|'relay'|'gfp'|'instrument_transformer'|'switch'", r['candidateKind'])
```

`quantify/quantify.ts` - add the switch `specKey` branch BEFORE the transformer fall-through (after the `instrument_transformer` branch):
```ts
  if (s.kind === 'switch') {
    return [s.kind, s.switchType, s.voltageClass ?? '-', s.fused === undefined ? '-' : (s.fused ? 'F' : 'NF'), s.source.block ?? '-'].join('|')
  }
```
and add the rich-switch preference in `pickAuthoritative` (after the `richRelay` line):
```ts
  const richSwitch = auths.find((o) => o.kind === 'switch' && (o.switchType !== 'unknown' || o.fused !== undefined || o.ampRating !== undefined))
  if (richSwitch) return richSwitch
```

`buckets/types.ts` - add codes + fields:
- `OperatorQuestionCode` += `| 'switch_scope_pending' | 'switch_catalog_gap' | 'switch_parent_conflict'`
- `DispositionReasonCode` += `| 'switch_scope_pending' | 'switch_catalog_gap' | 'switch_parent_conflict'`
- `TakeoffFinding.code` union += `| 'switch_catalog_gap'`
- `ScopePendingLine` += `switchType?: string` and `fused?: boolean`
- `ApparatusDisposition` += `switchType?: string` and `fused?: boolean`

`emit/emit.ts` - imports (near the other catalog imports):
```ts
import { matchSwitch } from '../catalog/switch-map'
import { SWITCH_R1_RATIFIED } from '../catalog/switch-map.data'
```
add `SwitchSignature` to the `../signature/types` type-import; add the two `ASSESS_TO_REASON` entries:
```ts
  switch_recognized:        'switch_scope_pending',   // unreachable (has signature); present for exhaustiveness
  switch_parent_conflict:   'switch_parent_conflict',
```
and the `kind === 'switch'` branch in the match loop BEFORE the `// kind === 'transformer'` fall-through (mirrors the relay branch; the `continue` keeps the transformer cast valid):
```ts
    if (sig.kind === 'switch') {
      const ssig: SwitchSignature = sig
      const scope = matchSwitch(ssig)
      if (scope) {
        scopePendingLines.push({
          candidateRefs: scope.group, provisionalDefaultRef: scope.defaultRef, r1Ratified: SWITCH_R1_RATIFIED,
          scopeQuestion: scope.scopeQuestion, qty: line.qty, block: ssig.source.block ?? ssig.source.sheet, line,
          switchType: ssig.switchType, fused: ssig.fused,
        })
        for (const i of line.memberIndices) {
          stamp(dispositions, i, 'scope_pending', 'switch_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
          const disp = dispositions[i]!
          disp.candidateRefs = scope.group; disp.provisionalDefaultRef = scope.defaultRef; disp.scopeQuestion = scope.scopeQuestion
          disp.switchType = ssig.switchType; disp.fused = ssig.fused
        }
        questions.push({ question: scope.scopeQuestion, context: `${ssig.tag ?? ssig.source.sheet} (switch ${ssig.switchType}, ${ssig.voltageClass ?? 'unknown'}V; candidate group: ${scope.group.join(' | ')})`, code: 'switch_scope_pending' })
      } else {
        const reason = `recognized switch (${ssig.switchType}, ${ssig.voltageClass ?? 'unknown'}V, fused=${ssig.fused ?? '?'}) - no applicable priced ref`
        unmatchedCandidates.push({ reason, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'switch_catalog_gap', reason, undefined, line.lineKey)
        findings.push({ code: 'switch_catalog_gap', severity: 'warning', message: reason, context: ssig.tag ?? ssig.source.sheet })
        questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: ssig.tag ?? ssig.source.sheet, code: 'switch_catalog_gap' })
      }
      continue
    }
```

- [ ] **Step 5: Run the normalize-switch test + the FULL suite + BOTH typechecks (all five prior goldens byte-identical).**

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: PASS - normalize-switch green; ALL prior tests (including the five golden files) green; both typechecks clean. If a prior golden moved, STOP and investigate (a shared-medium row may have re-routed - see the build-time watch in Task 5).

- [ ] **Step 6: Commit.**

```bash
git add packages/estimator-takeoff/src/signature/normalize.ts packages/estimator-takeoff/src/signature/types.ts packages/estimator-takeoff/src/extraction/types.ts packages/estimator-takeoff/src/extraction/parse.ts packages/estimator-takeoff/src/quantify/quantify.ts packages/estimator-takeoff/src/buckets/types.ts packages/estimator-takeoff/src/emit/emit.ts packages/estimator-takeoff/test/normalize-switch.test.ts packages/estimator-takeoff/test/quantify-switch.test.ts
git commit -m "feat(switch): assessor + union widening + pipeline wiring (Task 3)"
```

---

### Task 4: Report projection + end-to-end pipeline tests

**Files:**
- Modify: `packages/estimator-takeoff/src/runner/report.ts:21` (scopePending interface) + `:82-91` (projection) + `:127` (renderReportText)
- Test: `packages/estimator-takeoff/test/switch-pipeline.test.ts`

**Interfaces:**
- Consumes: `runTakeoff`, the `scope_pending` line shape with `switchType`/`fused` (Task 3).
- Produces: the report's `scopePending` projection carrying `switchType` + `fused`.

- [ ] **Step 1: Write the failing test `test/switch-pipeline.test.ts`** (end-to-end: scope_pending in the result + report; catalog_gap; partial-preview-shaped result; cross-family compiler proof).

```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { renderReportText, buildReconciliationReport } from '../src/runner/report'
import type { ExtractionArtifact } from '../src/extraction/types'

const art = (rows: { raw: string; tag: string; busVoltageV?: number }[]): ExtractionArtifact => ({
  apparatus: rows.map((r) => ({ raw: r.raw, tag: r.tag, sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: r.busVoltageV })),
})

describe('switch pipeline', () => {
  it('an MV fused disconnect -> scope_pending with the MV ref + default, carried into the report', () => {
    const res = runTakeoff(art([{ raw: 'Fused Disconnect', tag: 'DS-1', busVoltageV: 15000 }]))
    expect(res.scopePendingLines?.length).toBe(1)
    const sp = res.scopePendingLines![0]!
    expect(sp.candidateRefs).toContain('Switch MV - Fused Disconnect')
    expect(sp.provisionalDefaultRef).toBe('Switch MV - Fused Disconnect')
    expect(sp.switchType).toBe('fused_disconnect')
    const report = buildReconciliationReport(res)
    expect(report.scopePending[0]!.switchType).toBe('fused_disconnect')
    expect(renderReportText(report)).toContain('type=fused_disconnect')
  })
  it('an LV non-fused disconnect -> switch_catalog_gap (no scope_pending line)', () => {
    const res = runTakeoff(art([{ raw: 'NF Disconnect', tag: 'DS-2', busVoltageV: 480 }]))
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
  })
  it('a switch + a real breaker coexist: the switch scope_pends, the breaker matches', () => {
    const res = runTakeoff(art([
      { raw: 'Fused Disconnect', tag: 'DS-3', busVoltageV: 15000 },
      { raw: '800AF/800AT LSIG', tag: 'CB-1', busVoltageV: 480 },
    ]))
    expect(res.scopePendingLines?.some((s) => s.switchType === 'fused_disconnect')).toBe(true)
    expect(res.matchedLines.length).toBe(1)   // the breaker priced
  })
})
```

- [ ] **Step 2: Run the test, verify it FAILS** (report has no `switchType`).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test -- switch-pipeline'`
Expected: FAIL - `report.scopePending[0].switchType` is undefined (projection not wired).

- [ ] **Step 3: Wire `switchType` + `fused` through `runner/report.ts`.**

Interface at L21 - add the two optional fields:
```ts
  scopePending: { lineKey: string; tag?: string; qty: number; candidateRefs: string[]; provisionalDefaultRef?: string; r1Ratified: boolean; scopeQuestion: string; packagingEvidence?: string; phaseCount?: number; switchType?: string; fused?: boolean }[]
```
Projection (the `scopePending` map, ~L82-91) - add:
```ts
    switchType: sp.switchType,
    fused: sp.fused,
```
renderReportText (~L127) - append to the per-line string:
```ts
      + (sp.switchType ? ' type=' + sp.switchType : '') + (sp.fused !== undefined ? ' fused=' + sp.fused : '')
```

- [ ] **Step 4: Run the test, verify it PASSES; run the full suite + both typechecks.**

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: PASS (switch-pipeline green; all prior tests green; both typechecks clean).

- [ ] **Step 5: Commit.**

```bash
git add packages/estimator-takeoff/src/runner/report.ts packages/estimator-takeoff/test/switch-pipeline.test.ts
git commit -m "feat(switch): report projection + end-to-end pipeline tests (Task 4)"
```

---

### Task 5: The real golden + byte-identical regression + full gates

**Files:**
- Test: `packages/estimator-takeoff/test/switch-golden.test.ts`
- (Read-only verification of the five prior golden tests: `transformer-golden.test.ts`, `relay-golden.test.ts`, `gfp-golden.test.ts`, `itx-golden.test.ts`, `golden-e01-11.test.ts`)

**Interfaces:**
- Consumes: the full pipeline (Tasks 1-4).
- Produces: the switch coexistence golden + the byte-identical regression confirmation.

- [ ] **Step 1: Write the failing golden `test/switch-golden.test.ts`** (a real service one-line: a fused disconnect + an MV switch + a REAL breaker + a switchgear assembly coexist; switches scope_pend, breaker prices, assembly excluded, air-switch -> open, NF disconnect -> gap).

```ts
import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const golden: ExtractionArtifact = {
  apparatus: [
    { raw: 'Fused Disconnect 400A', tag: 'DS-1', sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 15000 },
    { raw: 'Air Switch', tag: 'DS-2', sheet: 'E-1', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line', busVoltageV: 15000 },
    { raw: 'NF Disconnect', tag: 'DS-3', sheet: 'E-1', page: 1, bbox: [2, 0, 3, 1], evidence: 'one-line', busVoltageV: 480 },
    { raw: '800AF/800AT LSIG', tag: 'CB-1', sheet: 'E-1', page: 1, bbox: [3, 0, 4, 1], evidence: 'one-line', busVoltageV: 480 },
    { raw: 'Switchgear - Medium Voltage', tag: 'SWGR-1', sheet: 'E-1', page: 1, bbox: [4, 0, 5, 1], evidence: 'one-line', busVoltageV: 15000 },
  ],
}

describe('switch golden - coexistence', () => {
  it('routes each device to the right family', () => {
    const res = runTakeoff(golden)
    // DS-1 MV fused disconnect + DS-2 air switch (open) -> scope_pending
    const sp = res.scopePendingLines ?? []
    expect(sp.some((s) => s.switchType === 'fused_disconnect' && s.provisionalDefaultRef === 'Switch MV - Fused Disconnect')).toBe(true)
    expect(sp.some((s) => s.switchType === 'open' && s.provisionalDefaultRef === 'Switch MV - Open')).toBe(true)
    // DS-3 NF LV disconnect -> catalog gap
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)
    // CB-1 real breaker -> priced
    expect(res.matchedLines.length).toBe(1)
    // SWGR-1 switchgear assembly -> NOT a switch (no scope_pending, no switch line for it)
    expect(sp.every((s) => s.line.signature.tag !== 'SWGR-1')).toBe(true)
  })
})
```

- [ ] **Step 2: Run the golden, verify it FAILS first, then PASSES after confirming behavior** (it should pass given Tasks 1-4; if it fails, fix the implementation, not the golden, unless the golden's expectation is wrong).

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test -- switch-golden'`
Expected: PASS.

- [ ] **Step 3: Run the FULL suite + both typechecks; confirm the five prior goldens are byte-identical (the build-time watch).**

Run: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$HOME/.local/bin:$PATH; cd /home/olares/code/apex/apex-switch && pnpm --filter @apex/estimator-takeoff test 2>&1 | tail -30 && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter "./apps/operations-web" typecheck'`
Expected: ALL tests pass; the prior golden files (`transformer-golden`, `relay-golden`, `gfp-golden`, `itx-golden`, `golden-e01-11`) unchanged and green. **Build-time watch:** if any prior golden row moved into the switch family (a row carrying a shared `SF6`/`vacuum`/`air` token with a switch anchor that previously fell through to the breaker assessment), STOP and investigate before proceeding - the goldens must stay byte-identical.

- [ ] **Step 4: Commit.**

```bash
git add packages/estimator-takeoff/test/switch-golden.test.ts
git commit -m "feat(switch): coexistence golden + byte-identical regression (Task 5)"
```

---

## Self-Review (completed by the plan author)

**1. Spec coverage:** Every spec section maps to a task: Contract 1-2 / Component 3 (recognition) -> Tasks 2+3; Contract 3 / Component 4 (match) -> Task 1; Contract 4 / Component 5 (quantify) -> Task 3 (`quantify-switch.test.ts` covers #23 rich-switch + specKey separation); Contract 5-6 / Component 6 (disposition+emit+report) -> Tasks 3+4; the 23 spec tests -> distributed (map #10/#11/#13/#22 Task 1; recognition #3/#5/#7/#9/#12/#15/#21/#22 Tasks 2+3; quantify #23 Task 3; pipeline #14/#16/#18 Task 4; golden #19/#20 Task 5). No gaps.

**2. Placeholder scan:** No TBD/TODO. All source is complete code; all regexes literal; all refs verbatim; the #23 test is concrete (Task 3 Step 1).

**3. Type consistency:** `SwitchType`/`SwitchSignature` (Task 1) used identically in `matchSwitch` (Task 1), `assessSwitch`/`specKey`/emit (Task 3). `SwitchScopeMatch {group, defaultRef?, scopeQuestion}` consistent with the emit consumer. `switch_recognized`/`switch_parent_conflict` (AssessmentCode, Task 3) map to `switch_scope_pending`/`switch_parent_conflict` (DispositionReasonCode) via ASSESS_TO_REASON. `switchType?`/`fused?` consistent across ScopePendingLine/ApparatusDisposition/report.
