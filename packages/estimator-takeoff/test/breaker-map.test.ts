import { describe, it, expect } from 'vitest'
import { matchBreaker } from '../src/catalog/breaker-map'
import { BREAKER_MAP } from '../src/catalog/breaker-map.data'
import { createDefaultCatalogResolver } from '@apex/estimator-core'
import type { ApparatusSignature } from '../src/signature/types'

const base: ApparatusSignature = {
  kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out', mountingBasis: 'text',
  frameA: 800, tripA: 800,
  source: { sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}
const resolver = createDefaultCatalogResolver()

describe('matchBreaker', () => {
  it('maps LV draw-out LSIG to a ref that exists in the canonical catalog', () => {
    const ref = matchBreaker(base)!
    expect(ref).toBe('Circuit Breaker LV - Draw-Out (LSIG)')
    expect(resolver.tryResolve(ref)).not.toBeNull()
  })
  it('maps LV draw-out LS/LSI (no G) to the LS/LSI ref', () => {
    expect(matchBreaker({ ...base, functions: ['L', 'S', 'I'] })).toBe('Circuit Breaker LV - Draw-Out (LS/LSI)')
  })
  it('maps LV molded_case to the molded-case ref', () => {
    expect(matchBreaker({ ...base, mounting: 'molded_case', functions: [] })).toBe('Circuit Breaker LV - Molded Case Thermal/Mag')
  })
  it('maps an MV vacuum breaker', () => {
    expect(matchBreaker({ ...base, voltageClass: 'MV', mounting: 'unknown', mvType: 'vacuum' }))
      .toBe('Circuit Breaker MV - Vacuum Bkr')
  })
  it('returns null for unknown LV mounting and unknown MV type (fail-closed)', () => {
    expect(matchBreaker({ ...base, mounting: 'unknown' })).toBeNull()
    expect(matchBreaker({ ...base, voltageClass: 'MV', mounting: 'unknown', mvType: 'unknown' })).toBeNull()
  })
  it('does NOT price a power-breaker construction when trip functions are unknown (fail-closed)', () => {
    expect(matchBreaker({ ...base, mounting: 'draw_out', functions: [] })).toBeNull()
    expect(matchBreaker({ ...base, mounting: 'insulated_case', functions: [] })).toBeNull()
  })
  it('returns null for an unmappable signature (HV, no type)', () => {
    expect(matchBreaker({ ...base, voltageClass: 'HV', mounting: 'unknown' })).toBeNull()
  })
  it('does NOT price an LV breaker with no parsed frame rating (frameA undefined)', () => {
    expect(matchBreaker({ ...base, mounting: 'panelboard', functions: [], frameA: undefined })).toBeNull()
    expect(matchBreaker({ ...base, mounting: 'molded_case', functions: [], frameA: undefined })).toBeNull()
    expect(matchBreaker({ ...base, mounting: 'draw_out', functions: ['L', 'S', 'I', 'G'], frameA: undefined })).toBeNull()
  })
  it('prices a rated LV panelboard MCB (frameA present, no functions needed)', () => {
    expect(matchBreaker({ ...base, mounting: 'panelboard', functions: [], frameA: 400 })).toBe('Circuit Breaker LV - Panelboard MCB')
  })
  it('has all 12 breaker rules and every ref resolves in the canonical catalog', () => {
    expect(BREAKER_MAP).toHaveLength(12)
    for (const rule of BREAKER_MAP) expect(resolver.tryResolve(rule.ref)).not.toBeNull()
  })
})
