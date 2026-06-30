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
  it('SWITCH_TRIP_FN does not false-positive on a 2-char tag prefix carried into the raw (LS/LG/LI/LE)', () => {
    // A legitimate disconnect whose tag (LS-1 / LG-2 / LI-7 / LE-3) is embedded in the raw must be RECOGNIZED,
    // not mis-flagged as switch_parent_conflict. The guard requires >=2 trip-function letters after L, so a bare
    // 2-char tag prefix (where the delimiter satisfies \b after a single SIGE letter) no longer trips it.
    for (const raw of ['LS-1 Fused Disconnect', 'LG-2 Disconnect Switch', 'LI-7 Safety Switch', 'LE-3 Disconnect Switch']) {
      const a = assessApparatus(row(raw, { tag: raw.split(' ')[0], busVoltageV: 15000 }))
      expect(a.signature?.kind, raw).toBe('switch')
      expect(a.assessmentCode, raw).toBe('switch_recognized')
    }
    // A GENUINE trip descriptor (LSIG, >=2 letters) on a switch row STILL conflicts (must-pin #21 preserved).
    expect(assessApparatus(row('DS-9 Disconnect Switch LSIG', { tag: 'DS-9' })).assessmentCode).toBe('switch_parent_conflict')
    // LV (L+V) and LBS (L+B) prefixes never trip the guard.
    expect(assessApparatus(row('LV-4 Disconnect Switch', { tag: 'LV-4', busVoltageV: 15000 })).signature?.kind).toBe('switch')
    expect(assessApparatus(row('LBS-1 Load Break Switch', { tag: 'LBS-1', busVoltageV: 15000 })).signature?.kind).toBe('switch')
  })
  it('Codex P2 (pass 5): candidateKind:switch wins over pad-mount transformer text (Vista not stolen)', () => {
    // looksLikeTransformer must yield to an explicit switch producer signal, exactly as it does for relay /
    // instrument_transformer - so a pad-mount Vista SWITCH is recognized as a switch, not a pad-mount transformer.
    const a = assessApparatus(row('Pad Mount Vista Disconnect', { candidateKind: 'switch', busVoltageV: 15000 }))
    expect(a.signature?.kind).toBe('switch')
    expect(a.assessmentCode).toBe('switch_recognized')
    if (a.signature?.kind === 'switch') expect(a.signature.switchType).toBe('vista')
  })
  it('Codex P1 (pass 6): a TAGLESS vacuum/SF6 switch is NOT priced as a breaker (root breaker-gate guard)', () => {
    // looksLikeSwitch requires a tag (device-first), so a tagless switch anchor with a shared medium (vacuum/SF6
    // in BREAKER_HINT) would otherwise fall through to the breaker assessment and be priced. The breaker-gate
    // SWITCH_DEVICE guard forces it to unrecognized_apparatus_row (fail-closed) instead - never a priced breaker.
    for (const raw of ['Vacuum Switch', 'SF6 Switch']) {
      const a = assessApparatus(row(raw, { tag: undefined, busVoltageV: 15000 }))
      expect(a.signature?.kind, raw).not.toBe('breaker')
      expect(a.assessmentCode, raw).toBe('unrecognized_apparatus_row')
    }
  })
  it('D3 grammar (operator-ratified): switch/DISC + construction recognizes; bare switch/DISC does not', () => {
    // switch-ish noun + explicit construction medium/type (either order) -> switch, NOT a breaker.
    // (Pad-Mount-Vista bare-text is NOT here: "pad mount" collides with the transformer recognizer -> deferred R1;
    //  it is reachable via candidateKind:'switch', proven in the pass-5 test above.)
    for (const [raw, type] of [['Switch (SF6)', 'sf6'], ['Switch, SF6', 'sf6'], ['DISC SF6', 'sf6'], ['Switch (Vacuum)', 'vacuum'], ['Switch MV - Motor Operated', 'motor_operated']] as const) {
      const a = assessApparatus(row(raw, { tag: 'SW-1', busVoltageV: 15000 }))
      expect(a.signature?.kind, raw).toBe('switch')
      if (a.signature?.kind === 'switch') expect(a.signature.switchType, raw).toBe(type)
    }
    // breaker-shaped rows are NOT pulled into the switch family.
    for (const raw of ['SF6 Breaker', 'VCB', '800AF/800AT LSIG']) {
      expect(assessApparatus(row(raw, { tag: 'CB-1', busVoltageV: 480 })).signature?.kind, raw).not.toBe('switch')
    }
    // exclusions still run first.
    for (const raw of ['Switchgear - MV', 'Transfer Switch', 'Circuit Switcher MV']) {
      expect(assessApparatus(row(raw, { tag: 'X-1', busVoltageV: 15000 })).signature?.kind, raw).not.toBe('switch')
    }
    // bare switch / bare DISC (no construction evidence) -> NOT counted as a switch.
    expect(assessApparatus(row('Switch', { tag: 'SW-9', busVoltageV: 15000 })).signature?.kind).not.toBe('switch')
    expect(assessApparatus(row('DISC', { tag: 'D-9', busVoltageV: 15000 })).signature?.kind).not.toBe('switch')
  })
  it('Codex P2 (pass 7): a transformer with an accessory disconnect mention stays a TRANSFORMER (no switch steal)', () => {
    // The switch grammar must NOT steal a real transformer that merely names an accessory disconnect - the
    // strong transformer evidence (kVA + XFMR/dry-type) wins; no text-based switch yield in looksLikeTransformer.
    const a = assessApparatus(row('T-1 1500KVA DRY-TYPE XFMR FUSED DISCONNECT', { tag: 'T-1', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
})
