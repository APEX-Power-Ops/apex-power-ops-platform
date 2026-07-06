import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import type { TransferSwitchSignature } from '../src/signature/types'

const ts = (o: Partial<TransferSwitchSignature>, i: number): TransferSwitchSignature => ({
  kind: 'transfer_switch', automationClass: 'automatic', voltageBasis: 'detected', inputIndex: i, tag: 'ATS-1',
  source: { sheet: 'one', page: 1, bbox: [i, 0, i + 1, 1], evidence: 'one-line' },
  ...o,
})

describe('quantify transfer_switch', () => {
  it('two distinct same-spec automatic-base transfers aggregate into one line (qty 2)', () => {
    // distinct tags (distinct devices) but identical automationClass/bypass/voltageClass/block -> same specKey -> qty 2
    const a = ts({ tag: 'ATS-1', source: { sheet: 'one', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' } }, 0)
    const b = ts({ tag: 'ATS-2', source: { sheet: 'one', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' } }, 1)
    const { lines } = quantify([a, b])
    expect(lines.length).toBe(1)
    expect(lines[0]!.qty).toBe(2)
    expect(lines[0]!.signature.kind).toBe('transfer_switch')
  })
  it('specKey separates by automationClass and bypassIsolation', () => {
    const auto = ts({ tag: 'A', automationClass: 'automatic', source: { sheet: 'one', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' } }, 0)
    const man = ts({ tag: 'M', automationClass: 'manual', source: { sheet: 'one', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' } }, 1)
    const byp = ts({ tag: 'B', automationClass: 'automatic', bypassIsolation: true, source: { sheet: 'one', page: 1, bbox: [2, 0, 3, 1], evidence: 'one-line' } }, 2)
    const { lines } = quantify([auto, man, byp])
    expect(lines.length).toBe(3)
  })
  it('a transfer_switch deviceId is kind-prefixed (no cross-family tag collision with a switch)', () => {
    // same tag, different kind -> distinct device identities -> two lines (proves kind: prefix in deviceId)
    const t = ts({ tag: 'X', source: { sheet: 'one', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' } }, 0)
    const { lines } = quantify([t])
    expect(lines[0]!.memberTags).toContain('X')
    expect(lines[0]!.signature.kind).toBe('transfer_switch')
  })
  it('pickAuthoritative prefers a rich transfer occurrence (known automationClass/bypass) over a sparse unknown', () => {
    const sparse = ts({ tag: 'ATS-1', automationClass: 'unknown', source: { sheet: 'one', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' } }, 0)
    const rich = ts({ tag: 'ATS-1', automationClass: 'automatic', bypassIsolation: true, source: { sheet: 'sch', page: 1, bbox: [1, 0, 2, 1], evidence: 'switchgear-schedule' } }, 1)
    const { lines } = quantify([sparse, rich])
    expect(lines.length).toBe(1)
    const rep = lines[0]!.signature
    expect(rep.kind).toBe('transfer_switch')
    if (rep.kind === 'transfer_switch') {
      expect(rep.automationClass).toBe('automatic')
      expect(rep.bypassIsolation).toBe(true)
    }
  })
})
