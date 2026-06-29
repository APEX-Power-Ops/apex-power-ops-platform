import { describe, it, expect } from 'vitest'
import { matchGfp } from '../src/catalog/gfp-map'
import { GFP_REF } from '../src/catalog/gfp-map.data'
import type { GfpSignature } from '../src/signature/types'

const gsig = (o: Partial<GfpSignature> = {}): GfpSignature => ({
  kind: 'gfp', voltageBasis: 'none', tag: 'GFP-1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...o,
})

describe('matchGfp - single ref, never null in V1', () => {
  it('returns the single GFP ref as the only candidate AND the provisional default', () => {
    const m = matchGfp(gsig())
    expect(m.group).toEqual([GFP_REF])
    expect(m.defaultRef).toBe(GFP_REF)
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('is voltage-agnostic (no busVoltage -> still the single-ref match)', () => {
    const m = matchGfp(gsig({ voltageClass: undefined, voltageV: undefined }))
    expect(m.group).toEqual([GFP_REF])
  })
})
