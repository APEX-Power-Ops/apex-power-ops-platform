import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { assessApparatus } from '../src/signature/normalize'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const noItx = (r: ReturnType<typeof runTakeoff>) =>
  r.dispositions.every((d) => d.reasonCode !== 'instrument_transformer_scope_pending') &&
  (r.scopePendingLines ?? []).every((s) => s.line.signature.kind !== 'instrument_transformer')

describe('operator must-pin: instrument vs power transformer', () => {
  it('#1 Current Transformer + tag -> instrument scope_pending', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' })]))
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_scope_pending')
  })
  it('#2 Potential / Voltage Transformer -> instrument', () => {
    for (const raw of ['POTENTIAL TRANSFORMER', 'VOLTAGE TRANSFORMER']) {
      const a = assessApparatus(row({ raw, tag: 'PT-1' }))
      expect(a.signature?.kind).toBe('instrument_transformer')
    }
  })
  it('#3 Transformer T-1 500kVA dry-type -> POWER transformer', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1 500KVA DRY-TYPE', tag: 'T-1', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
  it('#4 Transformer T-1 (bare) -> transformer_attrs_unparsed (unchanged behavior)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1', tag: 'T-1', busVoltageV: 480 }))
    expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
  })
  it('#5 bare CT without instrument-shaped tag -> NOT counted; CT-1 tag + candidateKind -> instrument', () => {
    expect(noItx(runTakeoff(art([row({ raw: 'FEEDER WITH CT METERING', tag: 'F-1' })])))).toBe(true)
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'CT-1' })).signature?.kind).toBe('instrument_transformer')
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'X9', candidateKind: 'instrument_transformer' })).signature?.kind).toBe('instrument_transformer')
  })
  it('#6 type+voltage, no packaging -> scope_pending, no default', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-1', busVoltageV: 4160 })]))
    expect((r.scopePendingLines ?? [])[0]!.provisionalDefaultRef).toBeUndefined()
  })
  it('parent conflict: candidateKind itx + AF/AT -> conflict, NO instrument line, breaker not suppressed', () => {
    const r = runTakeoff(art([row({ raw: '800AF/800AT LSIG DRAW-OUT', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'instrument_transformer' })]))
    expect(noItx(r)).toBe(true)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_parent_conflict')
  })
  it('power conflict: instrument noun + kVA -> power_conflict', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 500KVA', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_power_conflict')
  })
  it('phase/default-gate: (3) notation drives the default; no packaging -> no default', () => {
    const withPhase = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER (3) MV', tag: 'CT-1', busVoltageV: 4160 })]))
    expect((withPhase.scopePendingLines ?? [])[0]!.provisionalDefaultRef).toBeDefined()
    expect((withPhase.scopePendingLines ?? [])[0]!.phaseCount).toBe(3)
  })
  it('type unparsed: candidateKind itx + opaque ratio/tag (no type token) -> type_unparsed, NO instrument line', () => {
    const r = runTakeoff(art([row({ raw: '600:5', tag: 'X9', candidateKind: 'instrument_transformer' })]))
    expect(noItx(r)).toBe(true)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_type_unparsed')
  })
})
