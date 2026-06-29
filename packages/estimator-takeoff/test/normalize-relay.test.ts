import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('relay recognition - device-first', () => {
  it('bare 87T text with NO anchor is NOT a relay (unrecognized)', () => {
    const a = assessApparatus(row({ raw: '87T', tag: undefined }))
    expect(a.signature).toBeNull()
    expect(a.assessmentCode).toBe('unrecognized_apparatus_row')
  })
  it('candidateKind:relay + 87T -> relay device, differential role', () => {
    const a = assessApparatus(row({ raw: '87T', tag: 'R-1', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature?.kind).toBe('relay')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.role : null).toBe('differential')
  })
  it('a relay with NO bus voltage never emits missing_voltage', () => {
    const a = assessApparatus(row({ raw: 'SEL-751 FEEDER RELAY', tag: 'R-2' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature?.kind).toBe('relay')
  })
  it('a relay carrying a breaker frame/trip -> relay_breaker_conflict (null signature)', () => {
    const a = assessApparatus(row({ raw: 'RELAY 800AF/600AT', tag: 'R-3', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_breaker_conflict')
    expect(a.signature).toBeNull()
  })
  it('a legacy single-function EM/solid-state relay -> electromechanical role', () => {
    const a = assessApparatus(row({ raw: 'EM OVERCURRENT RELAY 51', tag: 'R-4', candidateKind: 'relay' }))
    expect(a.assessmentCode).toBe('relay_recognized')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.technology : null).toBe('electromechanical_solid_state')
    expect(a.signature && a.signature.kind === 'relay' ? a.signature.role : null).toBe('electromechanical')
  })
  it('a standalone transformer-accessory pressure relay is NOT a protective relay device', () => {
    const a = assessApparatus(row({ raw: 'FAULT PRESSURE RELAY', tag: 'X63' }))
    expect(a.signature).toBeNull()
    expect(a.assessmentCode).toBe('unrecognized_apparatus_row')
  })
})

describe('relay end-to-end through runTakeoff', () => {
  it('anchored 87T -> scope_pending differential (with provisional default)', () => {
    const r = runTakeoff(art([row({ raw: '87T', tag: 'R-1', candidateKind: 'relay' })]))
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines ?? []).toHaveLength(1)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.provisionalDefaultRef).toBe('Protective Relay (Differential Protection)')
    expect(sp.r1Ratified).toBe(false)
    expect(r.dispositions[0]!.reasonCode).toBe('relay_scope_pending')
  })
  it('illegible relay -> no-default scope_pending (provisionalDefaultRef undefined)', () => {
    const r = runTakeoff(art([row({ raw: 'PROTECTIVE RELAY', tag: 'R-9', candidateKind: 'relay' })]))
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs.length).toBe(9)
    expect(sp.provisionalDefaultRef).toBeUndefined()
  })
  it('relay-only extraction is not "nothing to price" (no missing_voltage row)', () => {
    const r = runTakeoff(art([row({ raw: 'SEL-787 87T XFMR DIFF RELAY', tag: 'R-1', candidateKind: 'relay' })]))
    expect(r.dispositions.every((d) => d.reasonCode !== 'missing_voltage')).toBe(true)
  })
})
