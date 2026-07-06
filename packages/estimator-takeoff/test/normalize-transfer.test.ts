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
