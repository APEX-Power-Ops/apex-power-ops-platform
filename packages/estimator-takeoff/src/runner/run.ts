import { emitEnvelope, runTakeoff } from '../emit/emit'
import { parseArtifact, ArtifactContractError } from '../extraction/parse'
import { reconcile, isClean, type ReconciliationReport } from './report'
import type { EstimateEnvelope, Finding } from '@apex/estimator-core'

export interface RunResult {
  report?: ReconciliationReport     // absent only when the artifact failed to parse
  envelope?: EstimateEnvelope
  findings: Finding[]               // estimator-core validator findings from emit (empty unless an envelope was built)
  exitCode: number
  stderr: string[]
}

// Pure: returns, never process.exit. The CLI wraps it. Emit-discipline order is load-bearing.
export function runFromArtifact(json: unknown, opts: { projectNumber: string; allowOpenItems: boolean }): RunResult {
  const stderr: string[] = []

  let artifact
  try {
    artifact = parseArtifact(json)
  } catch (e) {
    if (e instanceof ArtifactContractError) {
      stderr.push(`artifact contract error at ${e.path}: expected ${e.expected}, got ${e.got}`)
      return { findings: [], exitCode: 2, stderr }
    }
    throw e
  }

  const result = runTakeoff(artifact)   // throws on an exhaustiveness violation (a real bug, not user error)

  const accountedReport = reconcile(artifact, result)
  if (!accountedReport.accounted) {
    stderr.push('reconciliation invariant failed: dispositions do not reconcile with the produced lines (engine bug, not user input)')
    return { report: accountedReport, findings: [], exitCode: 1, stderr }
  }

  // 1. Error findings: UNCONDITIONAL hard block. allowOpenItems must NOT relax this.
  const errorFindings = result.findings.filter((f) => f.severity === 'error')
  if (errorFindings.length > 0) {
    const codes = [...new Set(errorFindings.map((f) => f.code))].join(', ')
    stderr.push(`blocking error findings [${codes}] - resolve before emit (these are not open items)`)
    return { report: accountedReport, findings: [], exitCode: 1, stderr }
  }

  // 2. Zero matched guard: nothing to price ONLY if there is also nothing scope-pending.
  //    A run with only scope_pending falls through: isClean is false (scope_pending blocks)
  //    -> open-items path -> --allow-open-items -> partial_preview.
  if (result.matchedLines.length === 0 && (result.scopePendingLines ?? []).length === 0) {
    stderr.push('no matched or scope-pending lines - nothing to price; resolve construction/catalog evidence or review the takeoff')
    return { report: accountedReport, findings: [], exitCode: 1, stderr }
  }

  // 3. Clean -> emit clean.
  if (isClean(result)) {
    const { envelope, findings } = emitEnvelope(result, { projectNumber: opts.projectNumber })
    const report = reconcile(artifact, result, { bid_cents: envelope.totals.bid_cents })
    return { report, envelope, findings, exitCode: 0, stderr }
  }

  // 4. Open items present (unmatched/questions/scope_pending, no error findings).
  if (!opts.allowOpenItems) {
    stderr.push(`open items present: ${accountedReport.counts.unresolved_rows} unresolved row(s) (${accountedReport.counts.unmatched_candidates} unmatched candidate-lines, ${accountedReport.counts.operator_questions} flagged questions); pass --allow-open-items to emit a partial preview`)
    return { report: accountedReport, findings: [], exitCode: 1, stderr }
  }
  // scope_pending-only runs have no matched lines so emitEnvelope would throw.
  // We must guard against calling it when there are zero matched lines.
  if (result.matchedLines.length === 0) {
    // Only scope_pending lines present: partial_preview without envelope.
    stderr.push(`WARNING: partial preview - ${accountedReport.counts.unresolved_rows} unresolved row(s) (scope-pending, no priced lines yet); envelope deferred until scope questions are resolved`)
    return { report: accountedReport, findings: [], exitCode: 0, stderr }
  }
  const { envelope, findings } = emitEnvelope(result, { projectNumber: opts.projectNumber })
  const report = reconcile(artifact, result, { bid_cents: envelope.totals.bid_cents })   // status === 'partial_preview' (isClean false)
  stderr.push(`WARNING: partial preview - ${report.counts.unresolved_rows} unresolved row(s) (${report.counts.unmatched_candidates} unmatched candidate-lines, ${report.counts.operator_questions} flagged questions); envelope is NOT a complete bid`)
  return { report, envelope, findings, exitCode: 0, stderr }
}
