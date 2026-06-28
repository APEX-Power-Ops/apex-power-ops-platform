import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { TransformerSignature } from '../src/signature/types'

const t = (tag: string, overrides: Partial<TransformerSignature> = {}): TransformerSignature => ({
  kind: 'transformer',
  voltageClass: 'LV',
  voltageV: 480,
  voltageBasis: 'detected',
  coolant: 'dry',
  kvaRating: 1500,
  tag,
  inputIndex: 0,
  source: { sheet: 'E1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ...overrides,
})

describe('quantify transformer specKey', () => {
  it('dedupes two identical dry 1500kVA 480V transformers into one line with qty 2', () => {
    const { lines } = quantify([t('TA'), t('TB')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.memberTags.sort()).toEqual(['TA', 'TB'])
  })

  it('keeps two transformers with different kVA on separate lines (qty 1 each)', () => {
    const { lines } = quantify([t('TA', { kvaRating: 1500 }), t('TB', { kvaRating: 750 })])
    expect(lines).toHaveLength(2)
    expect(lines.every((l) => l.qty === 1)).toBe(true)
  })

  it('keeps dry vs liquid transformers on separate lines', () => {
    const { lines } = quantify([t('TA', { coolant: 'dry' }), t('TB', { coolant: 'liquid' })])
    expect(lines).toHaveLength(2)
    expect(lines.every((l) => l.qty === 1)).toBe(true)
  })
})
