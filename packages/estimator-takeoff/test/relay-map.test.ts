import { describe, it, expect } from 'vitest'
import { matchRelay } from '../src/catalog/relay-map'
import { RELAY_TIERS } from '../src/catalog/relay-map.data'
import type { RelaySignature } from '../src/signature/types'

const base = (o: Partial<RelaySignature> & { role: RelaySignature['role'] }): RelaySignature => ({
  kind: 'relay', technology: 'microprocessor', voltageBasis: 'none', tag: 'R1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...o,
})

describe('matchRelay', () => {
  it('legible role -> group + provisional defaultRef (the role tier)', () => {
    const m = matchRelay(base({ role: 'differential' }))!
    expect(m.group).toEqual([...RELAY_TIERS])
    expect(m.defaultRef).toBe('Protective Relay (Differential Protection)')
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('electromechanical role -> the Electromechanical tier as default', () => {
    const m = matchRelay(base({ role: 'electromechanical', technology: 'electromechanical_solid_state' }))!
    expect(m.defaultRef).toBe('Protective Relay (Electromechanical)')
  })
  it('illegible role (unknown) -> group with NO defaultRef (no-default case)', () => {
    const m = matchRelay(base({ role: 'unknown' }))!
    expect(m.group).toEqual([...RELAY_TIERS])
    expect(m.defaultRef).toBeUndefined()
  })
  it('orphan-dominant role -> null (catalog_gap)', () => {
    const m = matchRelay(base({ role: 'unknown', ansiFunctions: ['86'] }))
    expect(m).toBeNull()
  })
})
