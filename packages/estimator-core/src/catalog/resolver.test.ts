import { describe, expect, it } from 'vitest'
import { createCatalogResolver } from './resolver'
import type { EquipmentModel } from './types'

function model(p: Partial<EquipmentModel> & { ref: string }): EquipmentModel {
  return {
    apparatus: p.ref,
    neta_section: { ATS: '7.22', MTS: '7.22' },
    ref_hours: { ATS: 3, MTS: 4 },
    unit_of_issue: 'each',
    lifecycle_status: 'active',
    merged_into_ref: null,
    ...p,
  }
}

describe('catalog resolver', () => {
  it('resolves an active model directly and returns ref hours by standard', () => {
    const r = createCatalogResolver([model({ ref: 'ATS - (IR/DLRO)', ref_hours: { ATS: 3, MTS: 4 } })])
    expect(r.resolve('ATS - (IR/DLRO)').lifecycle_status).toBe('active')
    expect(r.refHours('ATS - (IR/DLRO)', 'ATS')).toBe(3)
    expect(r.refHours('ATS - (IR/DLRO)', 'MTS')).toBe(4)
  })

  it('chases merged_into to the active identity', () => {
    const r = createCatalogResolver([
      model({ ref: 'OLD', lifecycle_status: 'merged', merged_into_ref: 'NEW' }),
      model({ ref: 'NEW', ref_hours: { ATS: 5, MTS: 5 } }),
    ])
    expect(r.resolve('OLD').ref).toBe('NEW')
    expect(r.refHours('OLD', 'ATS')).toBe(5)
  })

  it('throws on a standard that does not apply (NA)', () => {
    const r = createCatalogResolver([model({ ref: 'MTS-only', ref_hours: { ATS: null, MTS: 4 } })])
    expect(() => r.refHours('MTS-only', 'ATS')).toThrow(/does not apply/)
  })

  it('tryResolve returns null for unknown refs; resolve throws', () => {
    const r = createCatalogResolver([model({ ref: 'A' })])
    expect(r.tryResolve('missing')).toBeNull()
    expect(() => r.resolve('missing')).toThrow(/unknown/)
  })

  it('throws on a broken merge chain', () => {
    const r = createCatalogResolver([model({ ref: 'X', lifecycle_status: 'merged', merged_into_ref: 'GONE' })])
    expect(() => r.resolve('X')).toThrow(/merge target/)
  })
})
