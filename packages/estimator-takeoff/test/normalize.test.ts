import { describe, it, expect } from 'vitest'
import { normalizeApparatus } from '../src/signature/normalize'
import type { ExtractedApparatus } from '../src/extraction/types'

const mk = (raw: string, v?: number): ExtractedApparatus => ({
  raw, tag: 'X', sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: v,
})

describe('normalizeApparatus', () => {
  it('parses frame/trip and LSIG functions on a 480V draw-out breaker', () => {
    const s = normalizeApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480))!
    expect(s.voltageClass).toBe('LV')
    expect(s.frameA).toBe(4000)
    expect(s.tripA).toBe(4000)
    expect(s.functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('parses LS/LSI subset and trailing E (ground-fault sensing) as G', () => {
    const s = normalizeApparatus(mk('ACC-1-09-FB 800AF/800AT LSIGE', 480))!
    expect(s.functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('classifies molded-case from the MCB/molded keyword', () => {
    expect(normalizeApparatus(mk('LP-1 MCB 100AF/20AT', 480))!.mounting).toBe('panelboard')
  })
  it('classifies an MV vacuum breaker', () => {
    const s = normalizeApparatus(mk('MV-SWGR-1 VACUUM 1200A', 13800)!)!
    expect(s.voltageClass).toBe('MV')
    expect(s.mvType).toBe('vacuum')
  })
  it('returns null for a non-breaker label', () => {
    expect(normalizeApparatus(mk('TX-P1-110 535KVA', 480))).toBeNull()
  })
})
