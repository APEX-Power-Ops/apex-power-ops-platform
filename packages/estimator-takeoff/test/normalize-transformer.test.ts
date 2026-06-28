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
    expect(a.assessmentCode).not.toBe('transformer_recognized')   // -> unrecognized_apparatus_row (a question), not a TX candidate
  })

  it('flags a transformer token carrying a breaker frame/trip as a conflict', () => {
    const a = assessApparatus({ ...base, raw: 'XFMR 800AF/600AT', tag: 'X1', busVoltageV: 480 })
    expect(a.assessmentCode).toBe('transformer_breaker_conflict')
    expect(a.signature).toBeNull()
  })
})
