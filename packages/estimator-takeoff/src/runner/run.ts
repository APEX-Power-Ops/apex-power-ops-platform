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

  // 1. Error findings: UNCONDITIONAL hard block. allowOpenItems must NOT relax this.
  const errorFindings = result.findings.filter((f) => f.severity === 'error')
  if (errorFindings.length > 0) {
    const codes = [...new Set(errorFindings.map((f) => f.code))].join(', ')
    stderr.push(`blocking error findings [${codes}] - resolve before emit (these are not open items)`)
    return { report: reconcile(artifact, result), findings: [], exitCode: 1, stderr }
  }

  // 2. Zero matched guard: nothing to price.
  if (result.matchedLines.length === 0) {
    stderr.push('no matched lines - nothing to price; resolve construction/catalog evidence or review the takeoff')
    return { report: reconcile(artifact, result), findings: [], exitCode: 1, stderr }
  }

  // 3. Clean -> emit clean.
  if (isClean(result)) {
    const { envelope, findings } = emitEnvelope(result, { projectNumber: opts.projectNumber })
    const report = reconcile(artifact, result, { bid_cents: envelope.totals.bid_cents })
    return { report, envelope, findings, exitCode: 0, stderr }
  }

  // 4. Open items present (unmatched/questions, no error findings).
  if (!opts.allowOpenItems) {
    const report = reconcile(artifact, result)
    stderr.push(`open items present: ${report.counts.unresolved_rows} unresolved row(s) (${report.counts.unmatched_candidates} unmatched candidate-lines, ${report.counts.operator_questions} flagged questions); pass --allow-open-items to emit a partial preview`)
    return { report, findings: [], exitCode: 1, stderr }
  }
  const { envelope, findings } = emitEnvelope(result, { projectNumber: opts.projectNumber })
  const report = reconcile(artifact, result, { bid_cents: envelope.totals.bid_cents })   // status === 'partial_preview' (isClean false)
  stderr.push(`WARNING: partial preview - ${report.counts.unresolved_rows} unresolved row(s) (${report.counts.unmatched_candidates} unmatched candidate-lines, ${report.counts.operator_questions} flagged questions); envelope is NOT a complete bid`)
  return { report, envelope, findings, exitCode: 0, stderr }
}