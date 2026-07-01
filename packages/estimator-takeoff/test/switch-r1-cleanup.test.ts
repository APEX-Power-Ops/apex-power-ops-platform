import { describe, it, expect } from 'vitest'
import { matchSwitch } from '../src/catalog/switch-map'
import { SWITCH_GROUPS } from '../src/catalog/switch-map.data'
import { assessApparatus, looksLikeSwitch, parseSwitchType } from '../src/signature/normalize'
import { runTakeoff } from '../src/emit/emit'
import type { SwitchSignature } from '../src/signature/types'
import type { ExtractedApparatus, ExtractionArtifact } from '../src/extraction/types'

const base = { voltageBasis: 'detected' as const, source: { sheet: 's', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' } }
const sig = (o: Partial<SwitchSignature>): SwitchSignature => ({ kind: 'switch', switchType: 'unknown', ...base, ...o })
const row = (raw: string, o: Partial<ExtractedApparatus> = {}): ExtractedApparatus =>
  ({ raw, tag: o.tag ?? 'D-1', sheet: 's', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })

// ============================================================================
// (a) Typed-no-voltage Gate-2 candidate breadth: a typed switch with illegible
// voltage narrows to the TYPE's refs across voltage classes, NOT the full 11.
// Never auto-prices (no voltage -> no defaultRef). vacuum stays a gap (NO_HOME).
// ============================================================================
describe('R1-a: typed + no-voltage narrows to per-type :unknown group', () => {
  const cases: Array<[SwitchSignature['switchType'], string[]]> = [
    ['fused_disconnect', ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)', 'Switch MV - Fused Disconnect']],
    ['open', ['Switch MV - Open', 'Switch HV - Open']],
    ['motor_operated', ['Switch MV - Motor Operated', 'Switch HV - Motor Operated']],
    ['cutout', ['Switch MV - Cutout']],
    ['oil', ['Switch MV - Oil Insulated']],
    ['sf6', ['Switch (SF6) - Medium Voltage']],
    ['vista', ['Switch (Pad Mount Vista) - Medium Voltage']],
  ]
  for (const [t, refs] of cases) {
    it(`${t} + no voltage -> ${t}:unknown group, no default`, () => {
      const m = matchSwitch(sig({ switchType: t }))
      expect(m).not.toBeNull()
      expect(m!.group).toEqual(refs)
      expect(m!.group).toEqual(SWITCH_GROUPS[`${t}:unknown`])
      expect(m!.defaultRef).toBeUndefined()              // no voltage -> NEVER a default (D2 invariant)
    })
  }
  it('vacuum + no voltage stays a gap (NO_HOME, never resurrected by :unknown widening)', () => {
    expect(matchSwitch(sig({ switchType: 'vacuum' }))).toBeNull()
  })
  it('typeless (unknown) + no voltage still widens to the full any:unknown set (no type signal)', () => {
    const m = matchSwitch(sig({ switchType: 'unknown' }))
    expect(m!.group).toEqual(SWITCH_GROUPS['any:unknown'])
    expect(m!.group.length).toBe(11)
    expect(m!.defaultRef).toBeUndefined()
  })
  it('typed + voltage keeps the existing default (no regression)', () => {
    expect(matchSwitch(sig({ switchType: 'sf6', voltageClass: 'MV' }))!.defaultRef).toBe('Switch (SF6) - Medium Voltage')
  })
})

// ============================================================================
// (c) Load-Interrupter Switch: a synonym of the already-anchored load-break
// switch (LBS). Recognized into the fail-closed switch path; type stays unknown
// (no priced-type mapping without SME). Does NOT overreach to bare "interrupter".
// ============================================================================
describe('R1-c: load-interrupter switch anchor', () => {
  it('load interrupter / load-interrupter (+/- switch) recognize as a switch', () => {
    for (const r of ['Load Interrupter Switch', 'Load-Interrupter Switch', 'Load Interrupter', 'Load-Interrupter'])
      expect(looksLikeSwitch(row(r)), r).toBe(true)
  })
  it('routes to the switch family (not unrecognized), type unknown -> Gate-2', () => {
    const a = assessApparatus(row('Load Interrupter Switch', { tag: 'LIS-1' }))
    expect(a.signature?.kind).toBe('switch')
    expect((a.signature as SwitchSignature).switchType).toBe('unknown')  // no SME type mapping; fail-closed to Gate-2
  })
  it('does NOT overreach to a bare "interrupter"', () => {
    expect(looksLikeSwitch(row('Interrupter', { tag: 'X-1' }))).toBe(false)
    expect(looksLikeSwitch(row('Fault Interrupter', { tag: 'X-2' }))).toBe(false)
  })
  it('breaker discriminator still wins over the new anchor (AF/AT + LSIG -> parent conflict)', () => {
    const a = assessApparatus(row('Load Interrupter Switch 800AF LSIG', { tag: 'LIS-2' }))
    expect(a.assessmentCode).toBe('switch_parent_conflict')
    expect(a.signature).toBeNull()
  })
})

// ============================================================================
// (b) Bare-text Pad-Mount-Vista: a Vista switch (S&C product) must route to the
// switch family, NOT be claimed by the "pad mount" transformer token (which
// dispatches before the switch route). NARROW: isSwitchAnchored AND \bvista\b.
// ============================================================================
describe('R1-b: Vista switch product -> switch; place-name / kVA transformers stay transformer', () => {
  it('Vista switch product labels -> switch (vista), incl. bare + fully-hyphenated "Pad-Mount[-]Vista" (no "switch" word)', () => {
    for (const r of ['Pad-Mount Vista', 'Pad Mount Vista', 'Pad-Mount-Vista', 'Pad Mount-Vista', 'Pad Mount Vista Switch', 'Vista Switch', 'Vista Disconnect']) {
      const a = assessApparatus(row(r, { tag: 'DS-V' }))
      expect(a.signature?.kind, r).toBe('switch')
      expect((a.signature as SwitchSignature).switchType, r).toBe('vista')
    }
    expect(parseSwitchType('Pad-Mount-Vista')).toBe('vista')
  })
  it('GUARD: real pad-mount / kVA transformers (no vista product name) STAY transformer', () => {
    for (const r of ['1500KVA Pad Mount Transformer', 'T-2 2500KVA PAD-MOUNT OIL XFMR', 'Pad-Mount Oil Transformer', '1500KVA DRY-TYPE XFMR FUSED DISCONNECT'])
      expect(assessApparatus(row(r, { tag: 'T-1', busVoltageV: 480 })).signature?.kind, r).toBe('transformer')
  })
  it('GUARD (misprice class - opus): a real transformer at a "VISTA" site with a switch accessory STAYS transformer', () => {
    // "vista" is a US place name (Vista/Chula Vista/Buena Vista). Product-name discriminator + the kVA/XFMR-evidence guard.
    for (const r of [
      '1500KVA DRY-TYPE XFMR FUSED DISCONNECT, VISTA SUB',
      'XFMR 750KVA DRY TYPE BUENA VISTA SUBSTATION DISCONNECT',
      'CHULA VISTA 1000KVA PAD MOUNT TRANSFORMER W/ LOAD INTERRUPTER',
      'T-5 2500KVA PAD-MOUNT XFMR w/ Vista disconnect',
    ])
      expect(assessApparatus(row(r, { tag: 'T-9', busVoltageV: 15000 })).signature?.kind, r).toBe('transformer')
  })
  it('GUARD (misprice class - MVA + non-oil-filled coolant, even with the vista PRODUCT phrase): STAYS transformer', () => {
    // The veto must mirror the engine's own evidence: kVA OR MVA rating OR a liquid-coolant token (mineral oil / liquid),
    // not just the literal "oil-filled". A real liquid/MVA transformer that contains "pad-mount vista" stays a transformer.
    for (const r of [
      '2.5 MVA PAD-MOUNT VISTA, MINERAL OIL, 12.47KV',
      'PAD-MOUNT VISTA, LIQUID FILLED, 13.8KV',
      'Pad-Mount Liquid Filled w/ Vista Disconnect',
      '1000 KVA PAD-MOUNT VISTA',
      'PAD-MOUNT VISTA OIL-FILLED 5MVA',
    ])
      expect(assessApparatus(row(r, { tag: 'T-8', busVoltageV: 12470 })).signature?.kind, r).toBe('transformer')
  })
  it('place-name "vista" on a non-Vista switch (load interrupter) types as unknown, NOT the Vista product (codex P2-3)', () => {
    const a = assessApparatus(row('CHULA VISTA LOAD INTERRUPTER', { tag: 'LIS-9', busVoltageV: 15000 }))
    expect(a.signature?.kind).toBe('switch')
    expect((a.signature as SwitchSignature).switchType).toBe('unknown')   // generic load-interrupter -> Gate-2, no Vista default
    expect(parseSwitchType('CHULA VISTA LOAD INTERRUPTER')).toBe('unknown')
  })
})

// ============================================================================
// Breaker discriminators preserved end-to-end (operator-required regression set).
// ============================================================================
describe('R1: breaker rows remain breakers (never swept into the switch family)', () => {
  for (const r of ['SF6 Breaker', 'VCB', '800AF/800AT LSIG', 'Vacuum Circuit Breaker'])
    it(`${r} -> breaker (breaker-shaped, never switch)`, () => {
      const a = assessApparatus(row(r, { tag: 'CB-1', busVoltageV: 480 }))   // voltage present -> full breaker classification
      expect(a.isBreakerShaped, r).toBe(true)            // THE guard: breaker route, never assessSwitch (which returns isBreakerShaped:false)
      expect(a.signature?.kind, r).toBe('breaker')
    })
})

// ============================================================================
// Pipeline (runTakeoff): the headline operator cases, end-to-end through emit.
// ============================================================================
describe('R1 pipeline: SF6-no-voltage scope + vacuum-no-voltage gap', () => {
  const artifact: ExtractionArtifact = {
    pdf: 'r1.pdf',
    apparatus: [
      { raw: 'Switch (SF6)', tag: 'DS-S', sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },        // no busVoltageV
      { raw: 'Switch (Vacuum)', tag: 'DS-V', sheet: 'E-1', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' },     // no busVoltageV
    ],
  }
  it('SF6 + no voltage -> switch scope_pending, SF6-only candidate group, no default', () => {
    const res = runTakeoff(artifact)
    const sp = res.scopePendingLines ?? []
    const sf6 = sp.find((s) => s.line.signature.tag === 'DS-S')
    expect(sf6, 'SF6 row should be scope_pending').toBeDefined()
    expect(sf6!.switchType).toBe('sf6')
    expect(sf6!.candidateRefs).toEqual(['Switch (SF6) - Medium Voltage'])
    expect(sf6!.provisionalDefaultRef).toBeUndefined()
  })
  it('Vacuum + no voltage -> switch_catalog_gap (NOT a priced breaker)', () => {
    const res = runTakeoff(artifact)
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)
    expect(res.matchedLines.length).toBe(0)              // nothing auto-priced; not swept to the breaker path
    const sp = res.scopePendingLines ?? []
    expect(sp.some((s) => s.line.signature.tag === 'DS-V')).toBe(false)  // gap, not scope_pending
  })
})
