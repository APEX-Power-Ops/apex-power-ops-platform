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
