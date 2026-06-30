import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { SwitchSignature } from '../src/signature/types'

const sw = (o: Partial<SwitchSignature>, i: number): SwitchSignature => ({
  kind: 'switch', switchType: 'unknown', voltageBasis: 'detected', inputIndex: i, tag: 'DS-1', voltageClass: 'LV',
  source: { sheet: o.source?.evidence === 'one-line' ? 'one' : 'sch', page: 1, bbox: [i, 0, i + 1, 1], evidence: o.source?.evidence ?? 'panel-schedule' },
  ...o,
})

describe('quantify switch', () => {
  it('#23 rich-switch keeps fused:false evidence over a sparse same-tag occurrence', () => {
    // an authoritative schedule row carrying fused:false + a sparser authoritative one-line occurrence, same tag
    const rich: SwitchSignature = sw({ fused: false, source: { sheet: 'sch', page: 1, bbox: [0, 0, 1, 1], evidence: 'panel-schedule' } }, 0)
    const sparse: SwitchSignature = sw({ fused: undefined, source: { sheet: 'one', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' } }, 1)
    const { lines } = quantify([sparse, rich])
    expect(lines.length).toBe(1)
    const rep = lines[0]!.signature
    expect(rep.kind).toBe('switch')
    if (rep.kind === 'switch') expect(rep.fused).toBe(false)   // the fused:false representative wins -> LV gap proof holds
  })
  it('Codex P2: fused/type evidence beats an AMP-ONLY occurrence regardless of order', () => {
    // amp-only authoritative occurrence FIRST, NF (fused:false) authoritative occurrence SECOND, same tag.
    // The old flat-OR predicate (which counted ampRating as rich) picked the amp-first row and dropped fused:false;
    // the two-tier rule prefers the fused-bearing representative so the LV non-fused gap proof survives.
    const ampFirst: SwitchSignature = sw({ ampRating: 400, source: { sheet: 'one', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' } }, 0)
    const nfSecond: SwitchSignature = sw({ fused: false, source: { sheet: 'sch', page: 1, bbox: [1, 0, 2, 1], evidence: 'panel-schedule' } }, 1)
    const { lines } = quantify([ampFirst, nfSecond])
    expect(lines.length).toBe(1)
    const rep = lines[0]!.signature
    if (rep.kind === 'switch') expect(rep.fused).toBe(false)
  })
  it('specKey separates by switchType / voltage / fused', () => {
    const a = sw({ switchType: 'sf6', voltageClass: 'MV', tag: 'A', source: { sheet: 'one', page: 1, bbox: [0,0,1,1], evidence: 'one-line' } }, 0)
    const b = sw({ switchType: 'open', voltageClass: 'MV', tag: 'B', source: { sheet: 'one', page: 1, bbox: [1,0,2,1], evidence: 'one-line' } }, 1)
    const { lines } = quantify([a, b])
    expect(lines.length).toBe(2)
  })
})
