import { describe, it, expect } from 'vitest'
import { matchTransferSwitch, TransferScopeMatch } from '../src/catalog/transfer-switch-map'
import { TRANSFER_REFS } from '../src/catalog/transfer-switch-map.data'
import type { TransferSwitchSignature } from '../src/signature/types'
import seed from '../../estimator-core/src/catalog/equipment-models.seed.json'

const sig = (o: Partial<TransferSwitchSignature>): TransferSwitchSignature => ({
  kind: 'transfer_switch', automationClass: 'automatic', voltageBasis: 'none',
  source: { sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' }, ...o,
} as TransferSwitchSignature)   // full BaseSignature.source (block optional; never null) so the cast compiles

describe('matchTransferSwitch', () => {
  it('automatic -> default base IR/DLRO ref, group of 2', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'automatic' })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Automatic Transfer Switch - (IR/DLRO)')
    expect(m.group).toContain('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')
  })
  it('automatic + bypass -> Iso-Bypass default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'automatic', bypassIsolation: true })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')
  })
  it('manual -> Manual default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'manual' })) as TransferScopeMatch
    expect(m.defaultRef).toBe('Manual Transfer Switch - (IR/DLRO)')
  })
  it('unknown -> group [auto base, manual base], NO default', () => {
    const m = matchTransferSwitch(sig({ automationClass: 'unknown' })) as TransferScopeMatch
    expect(m.defaultRef).toBeUndefined()
    expect(m.group).toEqual(['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)'])
  })
  it('static -> null (catalog gap)', () => {
    expect(matchTransferSwitch(sig({ automationClass: 'static' }))).toBeNull()
  })
  it('manual + bypass -> null (no manual-iso-bypass ref; D6)', () => {
    expect(matchTransferSwitch(sig({ automationClass: 'manual', bypassIsolation: true }))).toBeNull()
  })
  it('never routes to the Functional-Testing ref in V1', () => {
    for (const ac of ['automatic', 'manual', 'unknown'] as const) {
      const m = matchTransferSwitch(sig({ automationClass: ac }))
      const refs = m ? [...m.group, m.defaultRef] : []
      expect(refs).not.toContain('Automatic Transfer Switch (Functional Testing)')
    }
  })
  it('the 3 V1 refs resolve verbatim in the live seed', () => {
    const names = new Set((seed as any[]).map((r) => r.ref))
    for (const r of TRANSFER_REFS) expect(names.has(r)).toBe(true)
  })
  it('7.18 overload: the Functional-Testing transfer ref + DC-Battery + DC-Charger all sit at firm 7.18 -> match by STRING', () => {
    const at718 = (seed as any[]).filter((r) => r.neta_section?.ATS === '7.18').map((r) => r.ref)
    expect(at718).toContain('Automatic Transfer Switch (Functional Testing)')
    expect(at718.some((r: string) => /Direct-Current Systems - Batteries/.test(r))).toBe(true)
    expect(at718.some((r: string) => /Direct-Current Systems - Chargers/.test(r))).toBe(true)
  })
})
