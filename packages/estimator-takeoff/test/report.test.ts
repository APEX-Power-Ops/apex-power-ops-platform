import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { reconcile, isClean } from '../src/runner/report'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('reconcile', () => {
  const a = art([
    row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' }),  // matched
    row({ raw: 'XFMR 1000KVA', tag: 'T' }),                                                          // ignored / non_breaker_excluded
    row({ raw: 'MCB 100AF/100AT', tag: 'B' }),                                                       // breaker-shaped, no voltage -> question
  ])
  const result = runTakeoff(a)
  const report = reconcile(a, result)

  it('counts inputs, matched lines, ignored, and questions', () => {
    expect(report.counts.apparatus_in).toBe(3)
    expect(report.counts.matched_lines).toBe(1)
    expect(report.counts.ignored).toBe(1)
    expect(report.counts.operator_questions).toBeGreaterThanOrEqual(1)
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
