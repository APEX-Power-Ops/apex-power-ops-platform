import { describe, it, expect } from 'vitest'
import { matchInstrumentTransformer } from '../src/catalog/instrument-transformer-map'
import type { InstrumentTransformerSignature } from '../src/signature/types'

const sig = (o: Partial<InstrumentTransformerSignature> & { itxType: InstrumentTransformerSignature['itxType'] }): InstrumentTransformerSignature => ({
  kind: 'instrument_transformer', packaging: 'unknown', packagingEvidence: 'none', voltageBasis: 'none', tag: 'CT-1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' }, ...o,
})

describe('matchInstrumentTransformer', () => {
  it('CT + MV -> the MV CT candidate group', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV' }))!
    expect(m.group).toContain('Current Transformer MV - Set of 3')
    expect(m.group.length).toBeGreaterThan(1)
    expect(m.scopeQuestion.length).toBeGreaterThan(0)
  })
  it('packaging evidence present -> provisional default set (a set variant)', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'set_of_3' }))!
    expect(m.defaultRef).toBe('Current Transformer MV - Set of 3')
  })
  it('NO packaging evidence -> NO provisional default (D2)', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'unknown', packagingEvidence: 'none' }))!
    expect(m.defaultRef).toBeUndefined()
  })
  it('absent voltage -> wider (unknown) group, no default without packaging', () => {
    const m = matchInstrumentTransformer(sig({ itxType: 'vt' }))!
    expect(m.group.length).toBeGreaterThanOrEqual(2)
    expect(m.defaultRef).toBeUndefined()
  })
  it('set_of_3 / three_phase ranks the EXPLICIT Set-of-3 ref above a broader bushing (Set)', () => {
    const a = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'set_of_3' }))!
    expect(a.defaultRef).toBe('Current Transformer MV - Set of 3')          // NOT 'Current Transformer - Bushing, HV/MV (Set)'
    const b = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'set', packagingEvidence: 'three_phase' }))!
    expect(b.defaultRef).toBe('Current Transformer MV - Set of 3')
  })
  it('LV/HV PT has NO priced home -> null (catalog_gap), never the generic "(set)" ref (bounded V1 gap)', () => {
    expect(matchInstrumentTransformer(sig({ itxType: 'vt', voltageClass: 'LV' }))).toBeNull()
    expect(matchInstrumentTransformer(sig({ itxType: 'vt', voltageClass: 'HV' }))).toBeNull()
  })
  it('individual packaging evidence -> the individual (non-set) default where the group has one (P2-b)', () => {
    const ccvt = matchInstrumentTransformer(sig({ itxType: 'ccvt', voltageClass: 'MV', packaging: 'individual', packagingEvidence: 'individual_token' }))!
    expect(ccvt.defaultRef).toBe('CCVT Voltage Transformer - Individual')   // the non-set ref
    const ct = matchInstrumentTransformer(sig({ itxType: 'ct', voltageClass: 'MV', packaging: 'individual', packagingEvidence: 'individual_token' }))!
    expect(ct.defaultRef).toBe('Current Transformer - Bushing HV/MV')        // first non-set ref in ct:MV
  })
})
