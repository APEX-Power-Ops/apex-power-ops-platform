import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { ApparatusSignature } from '../src/signature/types'

const sig = (tag: string, evidence: string, sheet = 'E01-11'): ApparatusSignature => ({
  kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out', mountingBasis: 'text',
  tag, source: { sheet, page: 1, bbox: [0, 0, 1, 1], evidence },
})

describe('quantify', () => {
  it('counts the same device once across one-line + power-plan, keeping both sources', () => {
    const { lines } = quantify([sig('ACC-1-09-FB', 'one-line'), sig('ACC-1-09-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(1)
    expect(lines[0]!.sources).toHaveLength(2)
  })
  it('counts two distinct devices of the same spec as qty 2', () => {
    const { lines } = quantify([sig('HF-01-FB', 'one-line'), sig('HF-02-FB', 'one-line')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
  })
  it('does NOT count a device seen only on a power-plan; reports it location-only', () => {
    const { lines, locationOnly } = quantify([sig('GHOST-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(0)
    expect(locationOnly).toHaveLength(1)
    expect(locationOnly[0]!.tag).toBe('GHOST-FB')
  })
  it('keeps two UNTAGGED same-spec devices distinct by bbox (no source collision)', () => {
    const untagged = (bbox: [number, number, number, number]): ApparatusSignature => ({
      kind: 'breaker', voltageClass: 'LV', functions: ['L', 'S', 'I'], mounting: 'molded_case', mountingBasis: 'text',
      source: { sheet: 'E05-20', page: 1, bbox, evidence: 'panel-schedule' },
    })
    const { lines } = quantify([untagged([0, 0, 1, 1]), untagged([2, 2, 3, 3])])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.sources).toHaveLength(2)
  })
  it('aggregates two distinct tagged devices of the same spec, each also on a power-plan, to qty 2 with 4 sources', () => {
    const { lines } = quantify([
      sig('A-FB', 'one-line'), sig('A-FB', 'power-plan', 'E02-03D'),
      sig('B-FB', 'one-line'), sig('B-FB', 'power-plan', 'E02-03D'),
    ])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.sources).toHaveLength(4)
  })
})
