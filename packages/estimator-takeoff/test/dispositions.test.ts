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
  it('classifies a non-transformer non-breaker as ignored/non_breaker_excluded', () => {
    const d = runTakeoff(art([row({ raw: 'PDU-1 PDU 100A', tag: 'P' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'ignored', reasonCode: 'non_breaker_excluded' })
  })
  it('classifies a recognized transformer (XFMR token) with no voltage as a missing_voltage question', () => {
    const d = runTakeoff(art([row({ raw: 'XFMR 1000KVA', tag: 'T' })])).dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'missing_voltage' })
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
  it('does NOT launder same-tag ambiguous rows into associated_source (the silent-loss class)', () => {
    const a = art([
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' }), // matched
      row({ raw: 'SPARE', tag: 'A' }),                                                                // unrecognized_apparatus_row
      row({ raw: 'ATS 800AF/800AT LSIG', tag: 'A' }),                                                 // transfer_parent_conflict (Task 3: tagged ATS + LSIG trip -> transfer family conflict; was non_breaker_carries_rating)
      row({ raw: 'MCB 100AF/100AT', tag: 'A' }),                                                      // AUTHORITATIVE missing_voltage (distinct device)
    ])
    const d = runTakeoff(a).dispositions
    expect(d[0]!.status).toBe('matched')
    expect(d[1]!).toMatchObject({ status: 'question', reasonCode: 'unrecognized_apparatus_row' })
    expect(d[2]!).toMatchObject({ status: 'question', reasonCode: 'transfer_parent_conflict' })
    expect(d[3]!).toMatchObject({ status: 'question', reasonCode: 'missing_voltage' })
  })
  it('DOES attach a benign non-authoritative missing-voltage re-occurrence of a counted device', () => {
    const a = art([
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'one-line' }), // matched
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', evidence: 'power-plan' }),                                           // same device, power-plan, no voltage
    ])
    const d = runTakeoff(a).dispositions
    expect(d[0]!.status).toBe('matched')
    expect(d[1]!).toMatchObject({ status: 'associated_source', reasonCode: 'unresolved_tag_attached' })
  })

  // FIX 5 (opus I3): conflict via runTakeoff -> status 'question', reasonCode 'transformer_breaker_conflict'
  it('XFMR 800AF/600AT via runTakeoff -> question with transformer_breaker_conflict reasonCode', () => {
    const a = art([row({ raw: 'XFMR 800AF/600AT', tag: 'X1', busVoltageV: 480 })])
    const result = runTakeoff(a)
    const d = result.dispositions
    expect(d[0]!).toMatchObject({ status: 'question', reasonCode: 'transformer_breaker_conflict' })
    // No matched line or scope_pending line should be fabricated
    expect(result.matchedLines).toHaveLength(0)
    expect(result.scopePendingLines ?? []).toHaveLength(0)
    // The question should use the transformer_breaker_conflict code
    const q = result.operatorQuestions.find((qq) => qq.code === 'transformer_breaker_conflict')
    expect(q).toBeDefined()
  })

  // FIX 6 (opus M2): cross-family tag-collision - voltage-less transformer row must NOT attach to breaker line
  it('cross-family tag-collision: voltage-less transformer row is NOT folded as associated_source of breaker', () => {
    const a = art([
      row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'T-1', busVoltageV: 480, mountingHint: 'draw_out', evidence: 'one-line' }), // breaker, matched
      row({ raw: 'XFMR 1000KVA DRY-TYPE', tag: 'T-1', evidence: 'power-plan' }),                                             // transformer, voltage-less, non-authoritative
    ])
    const d = runTakeoff(a).dispositions
    expect(d[0]!.status).toBe('matched')
    // The transformer row must NOT be 'associated_source' of the breaker - it should surface as its own question
    expect(d[1]!.status).not.toBe('associated_source')
    expect(d[1]!.status).toBe('question')
  })
})