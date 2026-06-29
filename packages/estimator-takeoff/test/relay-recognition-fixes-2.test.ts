import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const role = (a: ReturnType<typeof assessApparatus>) => (a.signature && a.signature.kind === 'relay' ? a.signature.role : null)

describe('R1 - a real transformer mentioning a relay model stays a transformer', () => {
  it('T-9 1500KVA DRY-TYPE XFMR W/ SEL-787 RELAY (tag, no candidateKind) -> transformer, not relay', () => {
    const a = assessApparatus(row({ raw: 'T-9 1500KVA DRY-TYPE XFMR W/ SEL-787 RELAY', tag: 'T-9', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
  it('the F2 case still works: SEL-787 XFMR DIFFERENTIAL RELAY (no kVA/coolant) -> relay differential', () => {
    const a = assessApparatus(row({ raw: 'SEL-787 XFMR DIFFERENTIAL RELAY', tag: 'R-3' }))
    expect(a.signature?.kind).toBe('relay')
    expect(role(a)).toBe('differential')
  })
})

describe('R2 - all-orphan ANSI wins over a text-derived role', () => {
  it('FEEDER LOCKOUT RELAY 86 -> relay_catalog_gap (not feeder scope_pending)', () => {
    const r = runTakeoff(art([row({ raw: 'FEEDER LOCKOUT RELAY 86', tag: 'R-86', candidateKind: 'relay' })]))
    expect((r.scopePendingLines ?? []).length).toBe(0)
    expect(r.dispositions[0]!.reasonCode).toBe('relay_catalog_gap')
  })
  it('LINE RECLOSING RELAY 79 -> relay_catalog_gap', () => {
    const r = runTakeoff(art([row({ raw: 'LINE RECLOSING RELAY 79', tag: 'R-79', candidateKind: 'relay' })]))
    expect(r.dispositions[0]!.reasonCode).toBe('relay_catalog_gap')
  })
  it('a mixed legible+orphan relay still scope_pends its legible tier (50 + 86 -> overcurrent)', () => {
    const r = runTakeoff(art([row({ raw: 'OVERCURRENT RELAY 50 WITH LOCKOUT 86', tag: 'R-50', candidateKind: 'relay' })]))
    expect((r.scopePendingLines ?? []).length).toBe(1)
  })
})
