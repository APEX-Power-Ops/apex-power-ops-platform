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
    unresolved_rows: number       // dispositions with status 'unmatched' or 'question' (blocks clean)
  }
  accounted: boolean              // every input row has a disposition AND index-aligned
  dispositions: ApparatusDisposition[]
  envelopeTotals?: { bid_cents: number }   // present when an envelope was emitted
}

// clean = nothing unresolved is hiding AND at least one line was matched/priced.
// The matchedLines>0 conjunct mirrors the runner's zero-matched hard-block in run.ts
// (which fires before isClean is called): a run where everything was ignored/excluded
// produces zero priced lines and must NOT be labeled 'clean' - there is no envelope to
// stand behind. Computed over the EXHAUSTIVE dispositions, NOT the buckets:
// an 'unrecognized_apparatus_row' is a question DISPOSITION that emits no operatorQuestion,
// so a bucket-only gate (zero operatorQuestions) would let it pass. The disposition check catches it.
export function isClean(result: TakeoffResult): boolean {
  const noErrorFindings = result.findings.every((f) => f.severity !== 'error')
  const allRowsResolved = result.dispositions.every(
    (d) => d.status === 'matched' || d.status === 'associated_source' || d.status === 'ignored',
  )                                                   // any 'unmatched' or 'question' row blocks
  const noOpenQuestions = result.operatorQuestions.length === 0   // catches advisory-on-matched + profile_warning
  const hasMatchedLines = result.matchedLines.length > 0          // zero priced lines is never 'clean'
  return noErrorFindings && allRowsResolved && noOpenQuestions && hasMatchedLines
}

// Internal consistency: matched/unmatched dispositions must exactly mirror the produced line memberships,
// matched rows must carry a ref + lineKey, and every referenced lineKey must exist. A false here means the
// reconciliation itself is broken (an engine bug) - the runner treats it as a hard failure.
function reconcilesInternally(result: TakeoffResult): boolean {
  const d = result.dispositions
  const matchedIdx = new Set(d.filter((x) => x.status === 'matched').map((x) => x.inputIndex))
  const matchedMembers = new Set(result.matchedLines.flatMap((m) => m.line.memberIndices))
  if (matchedIdx.size !== matchedMembers.size) return false
  for (const i of matchedIdx) if (!matchedMembers.has(i)) return false
  if (d.some((x) => x.status === 'matched' && (x.ref === undefined || x.lineKey === undefined))) return false
  const unmatchedIdx = new Set(d.filter((x) => x.status === 'unmatched').map((x) => x.inputIndex))
  const unmatchedMembers = new Set(result.unmatchedCandidates.flatMap((u) => u.line.memberIndices))
  if (unmatchedIdx.size !== unmatchedMembers.size) return false
  for (const i of unmatchedIdx) if (!unmatchedMembers.has(i)) return false
  const lineKeys = new Set<string>([
    ...result.matchedLines.map((m) => m.line.lineKey),
    ...result.unmatchedCandidates.map((u) => u.line.lineKey),
  ])
  if (d.some((x) => x.lineKey !== undefined && !lineKeys.has(x.lineKey))) return false
  return true
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
    unresolved_rows: d.filter((x) => x.status === 'unmatched' || x.status === 'question').length,
  }
  const accounted = d.length === apparatus_in && d.every((x, i) => x.inputIndex === i) && reconcilesInternally(result)
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
  out.push(`  unresolved_rows      ${c.unresolved_rows}`)
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
