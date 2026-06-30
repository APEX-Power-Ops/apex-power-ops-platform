import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const itx = (a: ReturnType<typeof assessApparatus>) => (a.signature && a.signature.kind === 'instrument_transformer' ? a.signature : null)

describe('instrument-transformer recognition', () => {
  it('Current Transformer + tag -> instrument (itxType ct)', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_recognized')
    expect(itx(a)?.itxType).toBe('ct')
  })
  it('Potential / Voltage Transformer -> itxType vt', () => {
    expect(itx(assessApparatus(row({ raw: 'POTENTIAL TRANSFORMER', tag: 'PT-1' })))?.itxType).toBe('vt')
    expect(itx(assessApparatus(row({ raw: 'VOLTAGE TRANSFORMER', tag: 'VT-1' })))?.itxType).toBe('vt')
  })
  it('CCVT -> itxType ccvt (not vt)', () => {
    expect(itx(assessApparatus(row({ raw: 'CCVT', tag: 'CCVT-1' })))?.itxType).toBe('ccvt')
  })
  it('bare CT with instrument-shaped tag -> instrument (A-prime)', () => {
    expect(assessApparatus(row({ raw: 'CT 600:5', tag: 'CT-1' })).assessmentCode).toBe('instrument_transformer_recognized')
  })
  it('bare CT in a non-instrument-tag row -> NOT instrument (A-prime)', () => {
    const a = assessApparatus(row({ raw: 'FEEDER WITH CT METERING', tag: 'F-1' }))
    expect(a.signature?.kind).not.toBe('instrument_transformer')
  })
  it('3-phase notation -> packagingEvidence three_phase + phaseCount 3', () => {
    const s = itx(assessApparatus(row({ raw: 'CURRENT TRANSFORMER (3) MV', tag: 'CT-1' })))
    expect(s?.packagingEvidence).toBe('three_phase'); expect(s?.phaseCount).toBe(3)
  })
  it('explicit Individual token -> packaging individual + packagingEvidence individual_token (P2-b)', () => {
    const s = itx(assessApparatus(row({ raw: 'CCVT VOLTAGE TRANSFORMER - INDIVIDUAL', tag: 'CCVT-1' })))
    expect(s?.packaging).toBe('individual'); expect(s?.packagingEvidence).toBe('individual_token')
  })
  it('parent conflict: candidateKind itx + AF/AT -> parent_conflict, null sig', () => {
    const a = assessApparatus(row({ raw: '800AF/800AT LSIG', tag: 'MSB-1', candidateKind: 'instrument_transformer' }))
    expect(a.assessmentCode).toBe('instrument_transformer_parent_conflict')
    expect(a.signature).toBeNull()
  })
  it('power conflict: instrument noun + kVA -> power_conflict', () => {
    const a = assessApparatus(row({ raw: 'CURRENT TRANSFORMER 500KVA', tag: 'CT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_power_conflict')
  })
  it('type unparsed: instrument flagged (candidateKind) but no CT/PT/VT/CCVT token -> type_unparsed, null sig (no fabricated CT)', () => {
    const a = assessApparatus(row({ raw: '600:5', tag: 'X9', candidateKind: 'instrument_transformer' }))
    expect(a.assessmentCode).toBe('instrument_transformer_type_unparsed')
    expect(a.signature).toBeNull()
  })
  it('generic INSTRUMENT TRANSFORMER noun with no CT/PT/VT type -> type_unparsed (not a fabricated ct)', () => {
    const a = assessApparatus(row({ raw: 'INSTRUMENT TRANSFORMER', tag: 'IT-1' }))
    expect(a.assessmentCode).toBe('instrument_transformer_type_unparsed')
    expect(a.signature).toBeNull()
  })
  it('a bare instrument transformer with no voltage never emits missing_voltage', () => {
    expect(assessApparatus(row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-1' })).assessmentCode).toBe('instrument_transformer_recognized')
  })
})

describe('power-transformer behavior PRESERVED (additive exclusion)', () => {
  it('Transformer T-1 500kVA dry-type -> power transformer (NOT instrument)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1 500KVA DRY-TYPE', tag: 'T-1', busVoltageV: 480 }))
    expect(a.signature?.kind).toBe('transformer')
  })
  it('Transformer T-1 (bare) -> transformer_attrs_unparsed (existing fail-closed behavior, unchanged)', () => {
    const a = assessApparatus(row({ raw: 'TRANSFORMER T-1', tag: 'T-1', busVoltageV: 480 }))
    expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
  })
})
