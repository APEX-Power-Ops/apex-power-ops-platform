import { describe, it, expect } from 'vitest'
import { createDefaultCatalogResolver, EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'

describe('estimator-takeoff wiring', () => {
  it('can reach the canonical estimator-core catalog', () => {
    expect(EQUIPMENT_MODELS_SEED.length).toBeGreaterThan(100)
    const r = createDefaultCatalogResolver()
    expect(r.tryResolve('Circuit Breaker LV - Draw-Out (LSIG)')).not.toBeNull()
  })
})
