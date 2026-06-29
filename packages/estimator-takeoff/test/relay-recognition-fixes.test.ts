import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const relayRole = (a: ReturnType<typeof assessApparatus>) => (a.signature && a.signature.kind === 'relay' ? a.signature.role : null)
const relayTech = (a: ReturnType<typeof assessApparatus>) => (a.signature && a.signature.kind === 'relay' ? a.signature.technology : null)

describe('F1 - multi-digit SEL model recognition + technology', () => {
  it('SEL-751 (token-only, tag, no candidateKind) is recognized as a microprocessor relay', () => {
    const a = assessApparatus(row({ raw: 'SEL-751', tag: 'R-1' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(relayTech(a)).toBe('microprocessor')
  })
  it('SEL-751 FEEDER RELAY classifies technology=microprocessor (not unknown)', () => {
    const a = assessApparatus(row({ raw: 'SEL-751 FEEDER RELAY', tag: 'R-2' }))
    expect(relayTech(a)).toBe('microprocessor')
    expect(relayRole(a)).toBe('feeder')
  })
})

describe('F2 - model-tagged relay outranks a transformer text token (device-first)', () => {
  it('SEL-787 XFMR DIFFERENTIAL RELAY (tag, NO candidateKind) -> relay differential, not transformer/missing_voltage', () => {
    const a = assessApparatus(row({ raw: 'SEL-787 XFMR DIFFERENTIAL RELAY', tag: 'R-3' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(relayRole(a)).toBe('differential')
  })
  it('end-to-end: that row -> scope_pending differential (no missing_voltage)', () => {
    const r = runTakeoff(art([row({ raw: 'SEL-787 XFMR DIFFERENTIAL RELAY', tag: 'R-3' })]))
    expect((r.scopePendingLines ?? []).length).toBe(1)
    expect(r.dispositions.every((d) => d.reasonCode !== 'missing_voltage')).toBe(true)
  })
  it('a genuine transformer accessory phrase still stays with the transformer path (not stolen by relay)', () => {
    // A real transformer row mentioning a pressure relay must NOT become a relay (no relay MODEL anchor here).
    const a = assessApparatus(row({ raw: 'T-9 2000KVA DRY-TYPE XFMR W/ SUDDEN PRESSURE RELAY', tag: 'T-9', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
})

describe('F3 - relay evidence not downgraded during de-dupe', () => {
  it('a generic PROTECTIVE RELAY preceding a richer SEL-751 FEEDER (same tag) keeps the feeder role', () => {
    const r = runTakeoff(art([
      row({ raw: 'PROTECTIVE RELAY', tag: 'R-7', candidateKind: 'relay' }),
      row({ raw: 'SEL-751 FEEDER PROTECTION RELAY', tag: 'R-7', evidence: 'panel-schedule', candidateKind: 'relay' }),
    ]))
    expect((r.scopePendingLines ?? []).length).toBe(1)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect((sp.line.signature as any).role).toBe('feeder')
    expect(sp.provisionalDefaultRef).toBe('Protective Relay (Feeder Protection)')
  })
})

describe('F4 - multi-orphan ANSI combinations are catalog gaps', () => {
  it('PROTECTIVE RELAY 27/59/81 -> relay_catalog_gap (not scope_pending against priced tiers)', () => {
    const r = runTakeoff(art([row({ raw: 'PROTECTIVE RELAY 27/59/81', tag: 'R-8', candidateKind: 'relay' })]))
    expect((r.scopePendingLines ?? []).length).toBe(0)
    expect(r.dispositions[0]!.reasonCode).toBe('relay_catalog_gap')
  })
})

describe('F5 - lowercase ANSI suffixes parse', () => {
  it('lowercase 87t -> differential role', () => {
    const a = assessApparatus(row({ raw: '87t', tag: 'R-5', candidateKind: 'relay' }))
    expect(relayRole(a)).toBe('differential')
  })
})
