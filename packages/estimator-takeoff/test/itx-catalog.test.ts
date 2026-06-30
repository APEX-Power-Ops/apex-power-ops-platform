import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { ITX_REFS, ITX_GROUPS, ITX_R1_RATIFIED } from '../src/catalog/instrument-transformer-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('instrument-transformer catalog authority', () => {
  it('all 9 instrument-transformer refs resolve verbatim in the live seed', () => {
    expect(ITX_REFS.length).toBe(9)
    for (const ref of ITX_REFS) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
  })
  it('every ITX_GROUPS member is one of ITX_REFS and resolves in the seed', () => {
    for (const group of Object.values(ITX_GROUPS)) for (const ref of group) {
      expect(ITX_REFS).toContain(ref)
      expect(REFS.has(ref)).toBe(true)
    }
  })
  it('section is OVERLOADED/DRIFTED: the 9 refs scatter across 7.1/7.6/7.14/7.15, NONE at canonical 7.10 -> match by STRING', () => {
    const secs = new Set(ITX_REFS.map((ref) => {
      const m = EQUIPMENT_MODELS_SEED.find((x: { ref: string }) => x.ref === ref) as { neta_section?: { ATS?: string | null } } | undefined
      return m?.neta_section?.ATS ?? null
    }))
    expect(secs.has('7.10')).toBe(false)                 // NONE at canonical 7.10
    expect(secs.size).toBeGreaterThan(1)                 // scattered
    for (const s of secs) expect(['7.1', '7.6', '7.14', '7.15']).toContain(s)
  })
  it.todo('R1: SME confirms ITX_GROUPS defaults + set/each convention -> flip ITX_R1_RATIFIED=true')
  it('R1 provisional', () => { expect(ITX_R1_RATIFIED).toBe(false) })
})
