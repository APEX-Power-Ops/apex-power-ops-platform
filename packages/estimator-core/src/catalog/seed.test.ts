import { describe, expect, it } from 'vitest'
import seed from './equipment-models.seed.json'
import { createCatalogResolver } from './resolver'
import type { EquipmentModel } from './types'

const models = seed as EquipmentModel[]

describe('committed catalog seed', () => {
  it('is non-empty and loads into a resolver without duplicate refs', () => {
    expect(models.length).toBeGreaterThan(0)
    expect(() => createCatalogResolver(models)).not.toThrow()
  })

  it('every row has a ref, a unit_of_issue, and at least one applicable standard', () => {
    for (const m of models) {
      expect(typeof m.ref).toBe('string')
      expect(m.ref.length).toBeGreaterThan(0)
      expect(['each', 'set']).toContain(m.unit_of_issue)
      expect(m.ref_hours.ATS !== null || m.ref_hours.MTS !== null).toBe(true)
    }
  })

  it('contains the apparatus the golden corpus depends on, with authentic ref hours', () => {
    const r = createCatalogResolver(models)
    expect(r.refHours('Automatic Transfer Switch - (IR/DLRO)', 'ATS')).toBe(3)
    expect(r.refHours('Automatic Transfer Switch - Iso Bypass (IR/DLRO)', 'ATS')).toBe(4)
    expect(r.refHours('Arrestor (SPD) - Low Voltage', 'ATS')).toBe(0.5)
    expect(r.refHours('Automatic Transfer Switch (Functional Testing)', 'MTS')).toBe(4)
    expect(r.refHours('Automatic Transfer Switch - Iso Bypass (IR/DLRO)', 'MTS')).toBe(6)
  })
})
