import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[], voltageAssertions?: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus, voltageAssertions })

describe('dispositions', () => {
  it('is exhaustive and index-aligned (one per input row)', () => {
    const a = art([row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480 }), row({ raw: 'XFMR 1000KVA', tag: 'T' }), row({ raw: 'SPARE', tag: 'S' })])
    const d = runTakeoff(a).dispositions
    expect(d).toHaveLength(3)
    d.forEach((x, i) => expect(x.inputIndex).toBe(i))
  })
  it('classifies non-breaker as ignored/non_breaker_excluded', () => {
    const d = runTakeoff(art([row({ raw: 'XFMR 1000KVA', tag: 'T' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'ignored', reasonCode: 'non_breaker_excluded' })
  })
  it('classifies an unclassifiable producer row as a question, never ignored', () => {
    const d = runTakeoff(art([row({ raw: 'SPARE', tag: 'S' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'unrecognized_apparatus_row' })
  })
  it('classifies a missing-voltage breaker as a question', () => {
    const d = runTakeoff(art([row({ raw: 'MCB 100AF/100AT', tag: 'B' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'missing_voltage' })
  })
  it('classifies a matched breaker with a ref', () => {
    const d = runTakeoff(art([row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' })])).dispositions
    expect(d[0]!.status).toBe('matched'); expect(d[0]!.ref).toBeTruthy(); expect(d[0]!.lineKey).toBeTruthy()
  })
  it('marks a non-representative occurrence as associated_source', () => {
    const a = art([
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'one-line' }),
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'power-plan' }),
    ])
    const d = runTakeoff(a).dispositions
    expect(d[1]!).toMatchObject({ status: 'associated_source', reasonCode: 'occurrence_of_counted_device' })
  })
  it('INVARIANT: no ignored row has any reasonCode other than non_breaker_excluded', () => {
    const a = art([row({ raw: 'XFMR' }), row({ raw: 'SPARE' }), row({ raw: 'ATS', tag: 'x' }), row({ raw: 'STS 800AF/800AT' })])
    for (const x of runTakeoff(a).dispositions) if (x.status === 'ignored') expect(x.reasonCode).toBe('non_breaker_excluded')
  })
})
