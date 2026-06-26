import type { ExtractionArtifact } from '../extraction/types'
import type { TakeoffResult, ApparatusDisposition } from '../buckets/types'

export interface ReconciliationReport {
  status: 'clean' | 'partial_preview'
  counts: {
    apparatus_in: number          // === artifact.apparatus.length
    matched_lines: number
    matched_qty: number           // sum of matchedLines.qty
    associated_sources: number
    unmatched_candidates: number
    operator_questions: number
    error_findings: number
    warning_findings: number
    ignored: number
  }
  accounted: boolean              // every input row has a disposition AND index-aligned
  dispositions: ApparatusDisposition[]
  envelopeTotals?: { bid_cents: number }   // present when an envelope was emitted
}

// clean = nothing unresolved is hiding. Computed over the EXHAUSTIVE dispositions, NOT the buckets:
// an 'unrecognized_apparatus_row' is a question DISPOSITION that emits no operatorQuestion, so a
// bucket-only gate (zero operatorQuestions) would let it pass. The disposition check catches it.
export function isClean(result: TakeoffResult): boolean {
  const noErrorFindings = result.findings.every((f) => f.severity !== 'error')
  const allRowsResolved = result.dispositions.every(
    (d) => d.status === 'matched' || d.status === 'associated_source' || d.status === 'ignored',
  )                                                   // any 'unmatched' or 'question' row blocks
  const noOpenQuestions = result.operatorQuestions.length === 0   // catches advisory-on-matched + profile_warning
  return noErrorFindings && allRowsResolved && noOpenQuestions
}

export function reconcile(
  artifact: ExtractionArtifact, result: TakeoffResult, envelopeTotals?: { bid_cents: number },
): ReconciliationReport {
  const d = result.dispositions
  const apparatus_in = artifact.apparatus.length
  const counts = {
    apparatus_in,
    matched_lines: result.matchedLines.length,
    matched_qty: result.matchedLines.reduce((s, m) => s + m.qty, 0),
    associated_sources: d.filter((x) => x.status === 'associated_source').length,
    unmatched_candidates: result.unmatchedCandidates.length,
    operator_questions: result.operatorQuestions.length,
    error_findings: result.findings.filter((f) => f.severity === 'error').length,
    warning_findings: result.findings.filter((f) => f.severity === 'warning').length,
    ignored: d.filter((x) => x.status === 'ignored').length,
  }
  const accounted = d.length === apparatus_in && d.every((x, i) => x.inputIndex === i)
  const report: ReconciliationReport = {
    status: isClean(result) ? 'clean' : 'partial_preview',
    counts, accounted, dispositions: d,
  }
  if (envelopeTotals) report.envelopeTotals = envelopeTotals
  return report
}

const pad = (s: string, n: number): string => (s.length >= n ? s : s + ' '.repeat(n - s.length))

// ASCII-only human render: counts block + a per-row table (inputIndex status reasonCode tag ref).
export function renderReportText(report: ReconciliationReport): string {
  const c = report.counts
  const out: string[] = []
  out.push(`Reconciliation: ${report.status}`)
  out.push(`  apparatus_in         ${c.apparatus_in}`)
  out.push(`  matched_lines        ${c.matched_lines}  (qty ${c.matched_qty})`)
  out.push(`  associated_sources   ${c.associated_sources}`)
  out.push(`  unmatched_candidates ${c.unmatched_candidates}`)
  out.push(`  operator_questions   ${c.operator_questions}`)
  out.push(`  ignored              ${c.ignored}`)
  out.push(`  findings             ${c.error_findings} error, ${c.warning_findings} warning`)
  out.push(`  accounted            ${report.accounted}`)
  if (report.envelopeTotals) out.push(`  bid_cents            ${report.envelopeTotals.bid_cents}`)
  out.push('')
  out.push(`  ${pad('idx', 5)}${pad('status', 20)}${pad('reasonCode', 32)}${pad('tag', 18)}ref`)
  for (const x of report.dispositions) {
    out.push(`  ${pad(String(x.inputIndex), 5)}${pad(x.status, 20)}${pad(x.reasonCode, 32)}${pad(x.tag ?? '-', 18)}${x.ref ?? ''}`)
  }
  return out.join('\n')
}
