import { describe, it, expect } from 'vitest'
import { matchBreaker } from '../src/catalog/breaker-map'
import type { TransformerSignature } from '../src/signature/types'

it('matchBreaker rejects a transformer signature (type + runtime)', () => {
  const tx = { kind: 'transformer', voltageClass: 'LV', voltageBasis: 'detected', coolant: 'dry',
    source: { sheet: 'E1', page: 1, bbox: [0,0,1,1], evidence: 'one-line' } } as unknown as TransformerSignature
  // @ts-expect-error matchBreaker only accepts BreakerSignature
  expect(matchBreaker(tx)).toBeNull()
})
