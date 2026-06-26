import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { ApparatusSignature } from '../src/signature/types'

const sig = (tag: string, evidence: string, sheet = 'E01-11'): ApparatusSignature => ({
  kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out', mountingBasis: 'text',
  tag, source: { sheet, page: 1, bbox: [0, 0, 1, 1], evidence },
})

const mk = (o: { tag?: string; evidence: string; inputIndex: number; mounting?: ApparatusSignature['mounting']; sheet?: string }): ApparatusSignature => ({
  kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'],
  mounting: o.mounting ?? 'draw_out', mountingBasis: 'text', tag: o.tag, inputIndex: o.inputIndex,
  source: { sheet: o.sheet ?? 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: o.evidence },
})

describe('quantify', () => {
  it('counts the same device once across one-line + power-plan, keeping both sources', () => {
    const { lines } = quantify([sig('ACC-1-09-FB', 'one-line'), sig('ACC-1-09-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(1)
    expect(lines[0]!.sources).toHaveLength(2)
  })
  it('counts two distinct devices of the same spec as qty 2 with both member tags', () => {
    const { lines } = quantify([sig('HF-01-FB', 'one-line'), sig('HF-02-FB', 'one-line')])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.memberTags.sort()).toEqual(['HF-01-FB', 'HF-02-FB'])
  })
  it('does NOT count a device seen only on a power-plan; reports it location-only', () => {
    const { lines, locationOnly } = quantify([sig('GHOST-FB', 'power-plan', 'E02-03D')])
    expect(lines).toHaveLength(0)
    expect(locationOnly).toHaveLength(1)
    expect(locationOnly[0]!.sig.tag).toBe('GHOST-FB')
  })
  it('keeps two UNTAGGED same-spec devices distinct by bbox (no source collision)', () => {
    const untagged = (bbox: [number, number, number, number]): ApparatusSignature => ({
      kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I'], mounting: 'molded_case', mountingBasis: 'text',
      source: { sheet: 'E05-20', page: 1, bbox, evidence: 'panel-schedule' },
    })
    const { lines } = quantify([untagged([0, 0, 1, 1]), untagged([2, 2, 3, 3])])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.sources).toHaveLength(2)
  })
  it('aggregates two distinct tagged devices each also on a power-plan to qty 2 / 4 sources / 2 member tags', () => {
    const { lines } = quantify([
      sig('A-FB', 'one-line'), sig('A-FB', 'power-plan', 'E02-03D'),
      sig('B-FB', 'one-line'), sig('B-FB', 'power-plan', 'E02-03D'),
    ])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.sources).toHaveLength(4)
    expect(lines[0]!.memberTags.sort()).toEqual(['A-FB', 'B-FB'])
  })
  it('separates same-spec devices in DIFFERENT electrical blocks into distinct lines', () => {
    const inBlock = (tag: string, block: string): ApparatusSignature => ({
      kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'], mounting: 'draw_out', mountingBasis: 'hint',
      tag, source: { sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', block },
    })
    const { lines } = quantify([inBlock('M1', 'P1-110'), inBlock('M2', 'P2-110')])
    expect(lines).toHaveLength(2)
    expect(lines.map((l) => l.signature.source.block).sort()).toEqual(['P1-110', 'P2-110'])
  })
  it('prefers the richest authoritative occurrence (known mounting) as the representative', () => {
    const sparse: ApparatusSignature = {
      kind: 'breaker', voltageClass: 'LV', voltageBasis: 'detected', functions: ['L', 'S', 'I', 'G'], mounting: 'unknown', mountingBasis: 'none',
      tag: 'X-FB', source: { sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
    }
    const rich: ApparatusSignature = {
      ...sparse, mounting: 'molded_case', mountingBasis: 'text',
      source: { sheet: 'E05-20', page: 1, bbox: [0, 0, 1, 1], evidence: 'panel-schedule' },
    }
    const { lines } = quantify([sparse, rich])
    expect(lines).toHaveLength(1)
    expect(lines[0]!.signature.mounting).toBe('molded_case')
  })

  it('exposes lineKey, memberIndices, and associated non-representative occurrences', () => {
    const oneLine = mk({ tag: 'B1', evidence: 'one-line', inputIndex: 0 })
    const powerPlan = mk({ tag: 'B1', evidence: 'power-plan', inputIndex: 1 })
    const r = quantify([oneLine, powerPlan])
    expect(r.lines).toHaveLength(1)
    expect(r.lines[0]!.memberIndices).toEqual([0])           // the authoritative representative
    expect(r.lines[0]!.lineKey).toBeTruthy()                 // present + stable
    expect(r.associated).toContainEqual({ inputIndex: 1, lineKey: r.lines[0]!.lineKey })
  })

  it('associated row points at the REPRESENTATIVE line key even when the sibling is sparser (mixed richness)', () => {
    const sparse = mk({ tag: 'B2', evidence: 'one-line', mounting: 'unknown', inputIndex: 0 })
    const rich = mk({ tag: 'B2', evidence: 'panel-schedule', mounting: 'draw_out', inputIndex: 1 })
    const r = quantify([sparse, rich])
    expect(r.lines).toHaveLength(1)
    expect(r.lines[0]!.memberIndices).toContain(1)           // pickAuthoritative chose the known-mounting (rich) row
    const assoc = r.associated.find((a) => a.inputIndex === 0)!
    expect(assoc.lineKey).toBe(r.lines[0]!.lineKey)          // NOT specKey(sparse)
  })
})

describe('quantify — per-tag voltage + provenance never collapse (the slice invariant)', () => {
  it('keeps two same-spec breakers in one block on separate lines when voltage differs', () => {
    const a = sig('A-480', 'one-line'); a.voltageV = 480
    const b = sig('B-208', 'one-line'); b.voltageV = 208
    const { lines } = quantify([a, b])
    expect(lines).toHaveLength(2)
    expect(lines.map((l) => l.signature.voltageV).sort((x, y) => (x ?? 0) - (y ?? 0))).toEqual([208, 480])
  })
  it('keeps same-spec same-voltage breakers separate when provenance differs (detected vs asserted)', () => {
    const det = sig('A', 'one-line'); det.voltageV = 480                       // basis detected (helper default)
    const asr = sig('B', 'one-line'); asr.voltageV = 480; asr.voltageBasis = 'asserted'
    expect(quantify([det, asr]).lines).toHaveLength(2)
  })
  it('still aggregates two identical-spec identical-voltage devices into one line (qty 2)', () => {
    const a = sig('A', 'one-line'); a.voltageV = 480
    const b = sig('B', 'one-line'); b.voltageV = 480
    const { lines } = quantify([a, b])
    expect(lines).toHaveLength(1); expect(lines[0]!.qty).toBe(2)
  })
})
