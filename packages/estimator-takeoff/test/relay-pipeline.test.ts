import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { RelaySignature } from '../src/signature/types'

const rsig = (o: Partial<RelaySignature> & { role: RelaySignature['role']; tag: string }): RelaySignature => ({
  kind: 'relay', technology: 'microprocessor', voltageBasis: 'none', inputIndex: 0,
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' }, ...o,
})

describe('relay flows through quantify (kind-aware specKey, no voltage required)', () => {
  it('two relays differing only in role get separate lines; no voltage needed', () => {
    const { lines } = quantify([
      rsig({ role: 'differential', tag: 'R1' }),
      rsig({ role: 'feeder', tag: 'R2', inputIndex: 1 }),
    ])
    expect(lines).toHaveLength(2)
    expect(lines.every((l) => l.signature.kind === 'relay')).toBe(true)
  })
})
