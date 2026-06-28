import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF, OIL_DEFAULT_REF, R1_RATIFIED } from '../src/catalog/transformer-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('transformer catalog authority', () => {
  it('every group ref resolves in the live seed; no group is empty', () => {
    for (const g of [DRY_GROUP, OIL_GROUP]) {
      expect(g.length).toBeGreaterThan(0)
      for (const ref of g) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
    }
  })
  it('each default is a member of its own group and resolves', () => {
    expect(DRY_GROUP).toContain(DRY_DEFAULT_REF)
    expect(OIL_GROUP).toContain(OIL_DEFAULT_REF)
    expect(REFS.has(DRY_DEFAULT_REF) && REFS.has(OIL_DEFAULT_REF)).toBe(true)
  })
  it.todo('R1: estimator ratifies the dry/oil default tiers -> flip R1_RATIFIED=true')
  it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests, not here)', () => {
    expect(typeof R1_RATIFIED).toBe('boolean')   // provisional defaults exist; never auto-priced (Task 7)
  })
})
