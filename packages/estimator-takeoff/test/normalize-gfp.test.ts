import { describe, it, expect } from 'vitest'
import { assessApparatus, isGfpParentShape } from '../src/signature/normalize'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })

describe('GFP recognition - standalone-only', () => {
  it('standalone GROUND FAULT RELAY + tag -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT RELAY', tag: 'GFR-1' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
    expect(a.signature?.kind).toBe('gfp')
  })
  it('GROUND FAULT PROTECTION SYSTEM + tag -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT PROTECTION SYSTEM', tag: 'GFP-1' }))
    expect(a.signature?.kind).toBe('gfp')
  })
  it('candidateKind:gfp on a non-parent row -> gfp_recognized', () => {
    const a = assessApparatus(row({ raw: 'GFP-2', tag: 'GFP-2', candidateKind: 'gfp' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
  })
  it('a GFP device with NO bus voltage never emits missing_voltage', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT MONITOR', tag: 'GFM-1' }))
    expect(a.assessmentCode).toBe('gfp_recognized')
  })
})

describe('isGfpParentShape - the load-bearing guard (direct)', () => {
  it('a breaker frame row is parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: '800AF/800AT LSIG', tag: 'B1' }))).toBe(true)
  })
  it('a NON_BREAKER row (ATS) is parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: 'ATS 800A GROUND FAULT PROTECTION', tag: 'ATS-1' }))).toBe(true)
  })
  it('a standalone GFP device row is NOT parent-shaped', () => {
    expect(isGfpParentShape(row({ raw: 'GROUND FAULT RELAY', tag: 'GFR-1' }))).toBe(false)
  })
})
