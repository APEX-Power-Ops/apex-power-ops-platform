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
