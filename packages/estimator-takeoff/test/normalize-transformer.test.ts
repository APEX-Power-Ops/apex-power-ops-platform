import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'

const base = { sheet: 'E1', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const }

describe('transformer recognition', () => {
  it('recognizes a dry-type transformer device token', () => {
    const a = assessApparatus({ ...base, raw: 'T-1 480V 1500KVA DRY-TYPE XFMR', tag: 'T-1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('transformer_recognized')
  })

  it('does NOT recognize a bare KVA load-summary note as a transformer', () => {
    const a = assessApparatus({ ...base, raw: 'TOTAL CONNECTED LOAD 250 KVA', evidence: 'power-plan' })
    expect(a.assessmentCode).not.toBe('transformer_recognized')
  })

  it('flags a transformer token carrying a breaker frame/trip as a conflict', () => {
    const a = assessApparatus({ ...base, raw: 'XFMR 800AF/600AT', tag: 'X1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('transformer_breaker_conflict')
    expect(a.signature).toBeNull()
  })

  // kVA-breaker regression: a breaker label carrying a kVA value (no transformer token) must match as a breaker
  it('does NOT misclassify a kVA-bearing breaker label as a transformer conflict', () => {
    const a = assessApparatus({ ...base, raw: 'MSB-1 500KVA 800AF/800AT LSIG', tag: 'MSB-1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('classified')
    expect(a.signature?.kind).toBe('breaker')
  })

  // FIX 4: UPS/PDU with kVA rating must NOT be recognized as a transformer
  it('does NOT recognize UPS-1 with kVA as a transformer (NON_BREAKER gate)', () => {
    const a = assessApparatus({ ...base, raw: 'UPS-1 250 KVA', tag: 'UPS-1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('non_breaker_excluded')
  })

  it('does NOT recognize PDU-1 with kVA as a transformer (NON_BREAKER gate)', () => {
    const a = assessApparatus({ ...base, raw: 'PDU-1 100 KVA', tag: 'PDU-1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('non_breaker_excluded')
  })

  // opus M4: bare TX (no kVA, no device token) -> unrecognized_apparatus_row
  it('TX-1 alone (no kVA, no device token) -> unrecognized_apparatus_row', () => {
    const a = assessApparatus({ ...base, raw: 'TX-1', tag: 'TX-1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('unrecognized_apparatus_row')
  })
})

describe('transformer attribute parsers', () => {
  it('parses kVA, not kV (30KVA != 30kV)', () => {
    const a = assessApparatus({ ...base, raw: 'T-2 30KVA 480V DRY', tag: 'T-2', busVoltageV: 480 })
    expect((a.signature as any).kvaRating).toBe(30)
  })

  it('parses coolant dry vs pad-mount oil', () => {
    expect((assessApparatus({ ...base, raw: 'PAD MOUNT OIL XFMR', tag:'T3', busVoltageV: 480 }).signature as any).coolant).toBe('liquid')
    expect((assessApparatus({ ...base, raw: 'DRY-TYPE XFMR', tag:'T4', busVoltageV: 480 }).signature as any).coolant).toBe('dry')
  })

  it('asks when neither kVA nor coolant is parseable', () => {
    const a = assessApparatus({ ...base, raw: 'XFMR T-9', tag: 'T-9', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('transformer_attrs_unparsed')
  })
})