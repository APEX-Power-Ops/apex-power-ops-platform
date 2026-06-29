import { describe, it, expect } from 'vitest'
import { EQUIPMENT_MODELS_SEED } from '@apex/estimator-core'
import { RELAY_TIERS, ROLE_TO_TIER, ORPHAN_ANSI, RELAY_R1_RATIFIED } from '../src/catalog/relay-map.data'

const REFS = new Set(EQUIPMENT_MODELS_SEED.map((m: { ref: string }) => m.ref))

describe('relay catalog authority', () => {
  it('every relay tier ref resolves verbatim in the live seed; 9 tiers', () => {
    expect(RELAY_TIERS.length).toBe(9)
    for (const ref of RELAY_TIERS) expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
  })
  it('every ROLE_TO_TIER value is a member of RELAY_TIERS and resolves in the seed', () => {
    for (const ref of Object.values(ROLE_TO_TIER)) {
      expect(RELAY_TIERS).toContain(ref)
      expect(REFS.has(ref), `seed missing ref: ${ref}`).toBe(true)
    }
  })
  it('ORPHAN_ANSI holds the deferred device types (D1 policy)', () => {
    for (const n of ['86', '79', '25', '27', '59', '81']) expect(ORPHAN_ANSI.has(n)).toBe(true)
  })
  it.todo('R1: estimator ratifies the relay role->tier mapping -> flip RELAY_R1_RATIFIED=true')
  it('R1 is tracked + provisional (fail-closed lives in the scope_pending tests)', () => {
    expect(RELAY_R1_RATIFIED).toBe(false)
  })
})
