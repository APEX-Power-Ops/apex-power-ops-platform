import {
  runTakeoff, reconcile, isClean, emitEnvelope,
  type ExtractionArtifact, type TakeoffResult, type ReconciliationReport, type VoltageAssertion,
} from '@apex/estimator-takeoff'
import { canonicalJson, sha256Hex } from './gate1-canonical'

export class Gate1Error extends Error {
  constructor(message: string, readonly path?: string) { super(message); this.name = 'Gate1Error' }
}

export interface TagRow { tag: string; inputIndexes: number[]; raw: string; evidence: string; reason: string }
export interface SheetGroup { sheet: string; blocks: { block: string; tags: TagRow[] }[] }
export type OpenItemKind = 'untagged_missing_voltage' | 'unmatched_candidate' | 'question'
export interface OpenItem { kind: OpenItemKind; label: string; sheet?: string; reasonCode?: string }

// THE SEAM: runTakeoff + reconcile, returning BOTH so the UI can read TakeoffResult.findings.
// Never use runFromArtifact for the interactive surface - it drops voltage findings.
export function evaluate(artifact: ExtractionArtifact): { result: TakeoffResult; report: ReconciliationReport } {
  const result = runTakeoff(artifact)
  const report = reconcile(artifact, result)
  return { result, report }
}

export function resolvableVoltageGroups(result: TakeoffResult, artifact: ExtractionArtifact): SheetGroup[] {
  const sheets = new Map<string, Map<string, Map<string, TagRow>>>()
  for (const d of result.dispositions) {
    if (d.reasonCode !== 'missing_voltage' || !d.tag) continue
    const row = artifact.apparatus[d.inputIndex]
    const block = row?.block ?? '(no block)'
    const byBlock = sheets.get(d.sheet) ?? sheets.set(d.sheet, new Map()).get(d.sheet)!
    const byTag = byBlock.get(block) ?? byBlock.set(block, new Map()).get(block)!
    const existing = byTag.get(d.tag)
    if (existing) existing.inputIndexes.push(d.inputIndex)
    else byTag.set(d.tag, { tag: d.tag, inputIndexes: [d.inputIndex], raw: row?.raw ?? '', evidence: d.evidence, reason: d.reason })
  }
  return [...sheets.entries()].map(([sheet, byBlock]) => ({
    sheet,
    blocks: [...byBlock.entries()].map(([block, byTag]) => ({ block, tags: [...byTag.values()] })),
  }))
}

export function otherOpenItems(result: TakeoffResult, artifact: ExtractionArtifact): OpenItem[] {
  const items: OpenItem[] = []
  // Every inputIndex already represented somewhere on the surface: each disposition this loop
  // emits, AND each tagged missing_voltage row routed to Panel 1 (Voltage Questions) below.
  // Used so the operatorQuestions sweep below does not double-list a row (e.g. location_only,
  // which has BOTH a 'question' disposition AND a same-index operatorQuestion).
  const surfaced = new Set<number>()
  for (const d of result.dispositions) {
    if (d.status !== 'question' && d.status !== 'unmatched') continue
    if (d.reasonCode === 'missing_voltage' && d.tag) { surfaced.add(d.inputIndex); continue }
    const row = artifact.apparatus[d.inputIndex]
    if (d.reasonCode === 'missing_voltage') {
      items.push({ kind: 'untagged_missing_voltage', label: row?.raw ?? `row ${d.inputIndex}`, sheet: d.sheet, reasonCode: d.reasonCode })
    } else if (d.status === 'unmatched') {
      items.push({ kind: 'unmatched_candidate', label: `${d.tag ?? row?.raw ?? `row ${d.inputIndex}`}`, sheet: d.sheet, reasonCode: d.reasonCode })
    } else {
      items.push({ kind: 'question', label: `${d.tag ?? row?.raw ?? `row ${d.inputIndex}`}: ${d.reason}`, sheet: d.sheet, reasonCode: d.reasonCode })
    }
    surfaced.add(d.inputIndex)
  }
  // Operator questions not already on the surface. Advisory-on-matched questions carry a DEFINED
  // inputIndex on a 'matched' row (no question/unmatched disposition) - they block Clean Export via
  // isClean, so the operator must be able to SEE them here. inputIndex === undefined = global
  // questions (e.g. profile_warning) with no row.
  for (const q of result.operatorQuestions) {
    if (q.inputIndex === undefined) {
      items.push({ kind: 'question', label: q.question })
    } else if (!surfaced.has(q.inputIndex)) {
      items.push({ kind: 'question', label: q.question, sheet: artifact.apparatus[q.inputIndex]?.sheet, reasonCode: q.code })
      surfaced.add(q.inputIndex)
    }
  }
  return items
}

export function buildAssertions(entries: { tag: string; voltageV: number }[], actor: string): VoltageAssertion[] {
  return entries.map((e) => ({ voltageV: e.voltageV, tags: [e.tag], source: 'gate1' as const, actor }))
}

// Replace-by-tag (last-write-wins). Gate-1 entries override any existing same-tag assertion
// (CLI or prior edit). Guarantees <= 1 assertion per tag -> never trips the engine's hard
// duplicate-tag error. Each output assertion carries exactly one tag.
export function mergeAssertionsByTag(existing: VoltageAssertion[] | undefined, gate1: VoltageAssertion[]): VoltageAssertion[] {
  const byTag = new Map<string, VoltageAssertion>()
  for (const a of existing ?? []) for (const tag of a.tags) byTag.set(tag, { ...a, tags: [tag] })
  for (const a of gate1) for (const tag of a.tags) byTag.set(tag, { ...a, tags: [tag] })
  return [...byTag.values()]
}

export interface Gate1Export { combined: Record<string, unknown>; runnerArtifact: ExtractionArtifact }

export async function buildExport(input: {
  artifact: ExtractionArtifact; result: TakeoffResult; report: ReconciliationReport
  projectCtx: { projectNumber: string; packageName?: string; operatorName: string }; nowIso: string
}): Promise<Gate1Export> {
  const { artifact, result, report, projectCtx, nowIso } = input
  const clean = isClean(result) && result.matchedLines.length > 0
  const envelope = clean ? emitEnvelope(result, { projectNumber: projectCtx.projectNumber }).envelope : undefined
  // FIX C (P2-3): on a clean run the runner (run.ts) re-reconciles AFTER emit with the envelope's
  // bid_cents, so its ReconciliationReport carries envelopeTotals. Mirror that here so the exported
  // report shape AND reportContentHash match the runner. Partials emit no envelope -> export the
  // input report unchanged (deliberate: a partial preview carries no envelope and no envelopeTotals).
  const exportReport = envelope
    ? reconcile(artifact, result, { bid_cents: envelope.totals.bid_cents })
    : report
  const artifactContentHash = await sha256Hex(canonicalJson(artifact))
  const reportContentHash = await sha256Hex(canonicalJson(exportReport))
  const manifest = {
    projectNumber: projectCtx.projectNumber,
    packageName: projectCtx.packageName ?? null,
    sheet: artifact.apparatus[0]?.sheet ?? null,
    pdf: artifact.pdf,
    status: exportReport.status,
    apparatusCount: artifact.apparatus.length,
    unresolvedRows: exportReport.counts.unresolved_rows,
    gate1AssertionTags: (artifact.voltageAssertions ?? []).flatMap((a) => a.tags),
    operatorEvidence: { name: projectCtx.operatorName, assertedAtClient: nowIso, authoritative: false },
    artifactContentHash, reportContentHash,
  }
  const combined: Record<string, unknown> = { schemaVersion: 1, manifest, artifact, report: exportReport }
  if (envelope) combined.envelope = envelope
  return { combined, runnerArtifact: artifact }
}
