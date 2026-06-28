import { describe, it, expect } from 'vitest'
import { matchTransformer } from '../src/catalog/transformer-map'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF, OIL_DEFAULT_REF } from '../src/catalog/transformer-map.data'
import type { TransformerSignature } from '../src/signature/types'

const tx = (o: Partial<TransformerSignature>): TransformerSignature => ({
  kind: 'transformer',
  voltageClass: 'LV',
  voltageBasis: 'detected',
  coolant: 'dry',
  source: { sheet: 'E1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...o,
})

describe('matchTransformer', () => {
  it('dry -> dry tier group + dry default ref', () => {
    const r = matchTransformer(tx({ coolant: 'dry' }))!
    expect(r).not.toBeNull()
    expect(r.group).toEqual([...DRY_GROUP])
    expect(r.defaultRef).toBe(DRY_DEFAULT_REF)
    expect(r.scopeQuestion).toContain('dry-type')
  })

  it('dry group has 3 tiers', () => {
    const r = matchTransformer(tx({ coolant: 'dry' }))!
    expect(r.group).toHaveLength(3)
  })

  it('liquid pad-mount -> oil group + oil default ref', () => {
    const r = matchTransformer(tx({ coolant: 'liquid', padMount: true }))!
    expect(r).not.toBeNull()
    expect(r.group).toEqual([...OIL_GROUP])
    expect(r.defaultRef).toBe(OIL_DEFAULT_REF)
    expect(r.scopeQuestion).toContain('pad-mount-oil')
  })

  it('unknown coolant -> null (catalog gap)', () => {
    expect(matchTransformer(tx({ coolant: 'unknown' }))).toBeNull()
  })

  // FIX 2: liquid-but-not-pad-mount -> null (catalog gap, no V1 ref applicable)
  it('liquid non-pad-mount -> null (catalog gap, no V1 ref)', () => {
    expect(matchTransformer(tx({ coolant: 'liquid', padMount: false }))).toBeNull()
  })

  it('liquid without padMount set -> null (catalog gap)', () => {
    expect(matchTransformer(tx({ coolant: 'liquid' }))).toBeNull()
  })

  it('ltc:true dry -> still returns DRY_GROUP with V2 deferral note in scopeQuestion', () => {
    const r = matchTransformer(tx({ coolant: 'dry', ltc: true }))!
    expect(r).not.toBeNull()
    expect(r.group).toEqual([...DRY_GROUP])
    expect(r.defaultRef).toBe(DRY_DEFAULT_REF)
    expect(r.scopeQuestion).toContain('LTC')
    expect(r.scopeQuestion).toContain('deferred to V2')
    expect(r.scopeQuestion).toContain('base unit only')
  })

  it('ltc:true liquid pad-mount -> still returns OIL_GROUP with V2 deferral note in scopeQuestion', () => {
    const r = matchTransformer(tx({ coolant: 'liquid', padMount: true, ltc: true }))!
    expect(r).not.toBeNull()
    expect(r.group).toEqual([...OIL_GROUP])
    expect(r.scopeQuestion).toContain('LTC')
    expect(r.scopeQuestion).toContain('deferred to V2')
  })

  it('ltc:false dry -> scopeQuestion has no LTC note', () => {
    const r = matchTransformer(tx({ coolant: 'dry', ltc: false }))!
    expect(r.scopeQuestion).not.toContain('LTC')
  })

  it('ltc absent dry -> scopeQuestion has no LTC note', () => {
    const r = matchTransformer(tx({ coolant: 'dry' }))!
    expect(r.scopeQuestion).not.toContain('LTC')
  })
})