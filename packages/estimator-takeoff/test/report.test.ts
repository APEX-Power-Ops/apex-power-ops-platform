import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { reconcile, isClean } from '../src/runner/report'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('reconcile', () => {
  const a = art([
    row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' }),  // matched
    row({ raw: 'XFMR 1000KVA', tag: 'T' }),                                                          // transformer_recognized -> missing_voltage -> question (Task 3: XFMR recognized, no voltage)
    row({ raw: 'MCB 100AF/100AT', tag: 'B' }),                                                       // breaker-shaped, no voltage -> question
  ])
  const result = runTakeoff(a)
  const report = reconcile(a, result)

  it('counts inputs, matched lines, ignored, and questions', () => {
    expect(report.counts.apparatus_in).toBe(3)
    expect(report.counts.matched_lines).toBe(1)
    expect(report.counts.ignored).toBe(0)   // XFMR now routes to transformer path (question), not non_breaker_excluded (ignored)
    expect(report.counts.operator_questions).toBeGreaterThanOrEqual(2)  // XFMR missing_voltage + MCB missing_voltage
  })
  it('is accounted (exhaustive + index-aligned)', () => {
    expect(report.accounted).toBe(true)
  })
  it('reports partial_preview when open items exist, consistent with isClean', () => {
    expect(report.status).toBe('partial_preview')
    expect(isClean(result)).toBe(false)
  })
  it('carries envelopeTotals only when supplied', () => {
    expect(reconcile(a, result).envelopeTotals).toBeUndefined()
    expect(reconcile(a, result, { bid_cents: 12345 }).envelopeTotals).toEqual({ bid_cents: 12345 })
  })
})

describe('isClean zero-matched contract (operator-directed root fix)', () => {
  // A run where every disposition is 'ignored' (non_breaker_excluded), matchedLines=[],
  // no questions, no errors: the OLD isClean (3 conjuncts only) returned true - a bug.
  // After the fix (4th conjunct: matchedLines.length > 0) isClean must return false,
  // mirroring the runner's zero-matched hard-block in run.ts.
  const zeroMatchedResult = {
    matchedLines: [],
    unmatchedCandidates: [],
    operatorQuestions: [],
    findings: [],
    dispositions: [
      {
        inputIndex: 0, tag: 'TX-1', raw: 'TX-1 XFMR', sheet: 'E1', page: 0,
        bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const,
        status: 'ignored' as const, reasonCode: 'non_breaker_excluded', reason: 'non-breaker device token',
      },
      {
        inputIndex: 1, tag: 'PDU-2', raw: 'PDU-2 PDU', sheet: 'E1', page: 0,
        bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const,
        status: 'ignored' as const, reasonCode: 'non_breaker_excluded', reason: 'non-breaker device token',
      },
    ],
  }
  const zeroArtifact = art([
    row({ raw: 'TX-1 XFMR', tag: 'TX-1', sheet: 'E1', page: 0 }),
    row({ raw: 'PDU-2 PDU', tag: 'PDU-2', sheet: 'E1', page: 0 }),
  ])

  it('isClean returns false for zero-matched run (matchedLines.length===0 blocks clean)', () => {
    expect(isClean(zeroMatchedResult as any)).toBe(false)
  })

  it('reconcile.status is partial_preview (not clean) for zero-matched run', () => {
    const report = reconcile(zeroArtifact, zeroMatchedResult as any)
    expect(report.status).toBe('partial_preview')
    expect(report.status).not.toBe('clean')
  })
})
