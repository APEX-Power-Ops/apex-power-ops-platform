import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { GFP_REF, GFP_R1_RATIFIED } from '../src/catalog/gfp-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('GFP catalog authority', () => {
  it('the single GFP ref resolves verbatim in the live seed', () => {
    expect(GFP_REF).toBe('Ground Fault Protection Device LV')
    expect(REFS.has(GFP_REF), `seed missing ref: ${GFP_REF}`).toBe(true)
  })
  it('the GFP ref is active and unit_of_issue=each in the seed', () => {
    const m = EQUIPMENT_MODELS_SEED.find((x: { ref: string }) => x.ref === GFP_REF) as
      { lifecycle_status?: string; unit_of_issue?: string } | undefined
    expect(m).toBeDefined()
    expect(m!.lifecycle_status).toBe('active')
    expect(m!.unit_of_issue).toBe('each')
  })
  it('section 7.14 is OVERLOADED (CT refs share it) -> must match by STRING, not section', () => {
    const at714 = EQUIPMENT_MODELS_SEED.filter((m: { neta_section?: { ATS?: string | null } }) => m.neta_section?.ATS === '7.14')
    expect(at714.length).toBeGreaterThan(1)                                                   // 7.14 is NOT unique to GFP
    expect(at714.some((m: { ref: string }) => /current transformer/i.test(m.ref))).toBe(true) // a CT ref shares 7.14
    expect(at714.some((m: { ref: string }) => m.ref === GFP_REF)).toBe(true)                  // and so does the GFP ref
  })
  it.todo('R1: SME confirms the single-ref-covers-all convention -> flip GFP_R1_RATIFIED=true')
  it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests)', () => {
    expect(GFP_R1_RATIFIED).toBe(false)
  })
})
