import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
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
  it('Codex P2: vacuum is a gap at EVERY voltage incl. absent - never widened to any:unknown', () => {
    expect(matchSwitch(sig({ switchType: 'vacuum' }))).toBeNull()                       // no voltage -> still gap (not any:unknown)
    expect(matchSwitch(sig({ switchType: 'vacuum', voltageClass: 'HV' }))).toBeNull()
    expect(matchSwitch(sig({ switchType: 'vacuum', voltageClass: 'LV' }))).toBeNull()
  })
  it('all 11 SWITCH_REFS resolve verbatim in the live seed; PDU also sits at firm 7.5 (string-match proof)', () => {
    const names = new Set(EQUIPMENT_MODELS_SEED.map((r: { ref: string }) => r.ref))
    for (const ref of SWITCH_REFS) expect(names.has(ref), `seed missing ${ref}`).toBe(true)
    expect(names.has('PDU (Power Distribution Unit)')).toBe(true)  // the 12th ref at 7.5 -> must match by STRING, not section
  })
  it('SWITCH_R1_RATIFIED is false (provisional, fail-closed)', () => {
    expect(SWITCH_R1_RATIFIED).toBe(false)
  })
})
