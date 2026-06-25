import { describe, it, expect } from 'vitest'
import { matchBreaker } from '../src/catalog/breaker-map'
import { BREAKER_MAP } from '../src/catalog/breaker-map.data'
import { createDefaultCatalogResolver } from '@apex/estimator-core'
import type { ApparatusSignature } from '../src/signature/types'

const base: ApparatusSignature = {
  kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out',
  source: { sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}
const resolver = createDefaultCatalogResolver()

describe('matchBreaker', () => {
  it('maps LV draw-out LSIG to a ref that exists in the canonical catalog', () => {
    const ref = matchBreaker(base)!
    expect(ref).toBe('Circuit Breaker LV - Draw-Out (LSIG)')
    expect(resolver.tryResolve(ref)).not.toBeNull()      // every mapped ref MUST resolve
  })
  it('maps LV draw-out LS/LSI (no G) to the LS/LSI ref', () => {
    expect(matchBreaker({ ...base, functions: ['L', 'S', 'I'] })).toBe('Circuit Breaker LV - Draw-Out (LS/LSI)')
  })
  it('maps an MV vacuum breaker', () => {
    expect(matchBreaker({ ...base, voltageClass: 'MV', mounting: 'unknown', mvType: 'vacuum' }))
      .toBe('Circuit Breaker MV - Vacuum Bkr')
  })
  it('returns null for an unmappable signature (HV, no type)', () => {
    expect(matchBreaker({ ...base, voltageClass: 'HV', mounting: 'unknown' })).toBeNull()
  })
  it('every ref in the map resolves in the canonical catalog', () => {
    for (const rule of BREAKER_MAP) expect(resolver.tryResolve(rule.ref)).not.toBeNull()
  })
})
