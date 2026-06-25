import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact, ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature } from '../signature/types'
import { assessApparatus } from '../signature/normalize'
import { quantify } from '../quantify/quantify'
import type { QuantifiedLine } from '../quantify/types'
import { matchBreaker } from '../catalog/breaker-map'
import type { MatchedLine, OperatorQuestion, TakeoffResult, UnmatchedCandidate } from '../buckets/types'

export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const sigs: ApparatusSignature[] = []
  const operatorQuestions: OperatorQuestion[] = []
  const locationCandidates: ExtractedApparatus[] = []   // un-normalized rows that may be location refs of a real device

  for (const x of artifact.apparatus) {
    const a = assessApparatus(x)
    operatorQuestions.push(...a.questions)
    if (a.signature) { sigs.push(a.signature); continue }
    if (!a.isBreakerShaped && x.tag) locationCandidates.push(x)
  }

  const { lines, locationOnly } = quantify(sigs)

  // associate location references (e.g. power-plan rows) to their counted device BY TAG — preserves the
  // location source without inflating the count
  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) if (l.signature.tag) byTag.set(l.signature.tag, l)
  for (const x of locationCandidates) {
    const l = x.tag ? byTag.get(x.tag) : undefined
    if (l) l.sources.push({ sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block })
  }

  // power-plan-only normalized devices → operator questions
  for (const s of locationOnly) {
    operatorQuestions.push({ question: `Device ${s.tag ?? '(untagged)'} appears only on a non-authoritative sheet — include it?`, context: `${s.source.sheet} (${s.source.evidence})` })
  }

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) matchedLines.push({ ref, qty: line.qty, block: line.signature.source.block ?? line.signature.source.sheet, mountingBasis: line.signature.mountingBasis, line })
    else unmatchedCandidates.push({ reason: `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('') || '—'}`, line })
  }
  return { matchedLines, unmatchedCandidates, operatorQuestions }
}

export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  // FAIL CLOSED: an all-unmatched takeoff must not silently emit an empty "valid" envelope.
  if (result.matchedLines.length === 0) {
    throw new Error('estimator-takeoff: refusing to emit an envelope with zero matched lines — all candidates are unmatched/uncertain; resolve construction/catalog evidence or review the takeoff.')
  }
  // group matched lines into scopes by ELECTRICAL BLOCK; emit ONLY catalog {ref, qty} lines (fail-closed)
  const byScope = new Map<string, NativeEnvelopeInput['scopes'][number]>()
  for (const m of result.matchedLines) {
    const name = `Block ${m.block}`
    const scope = byScope.get(name) ?? { name, netaStandard: 'ATS' as NetaStandard, lines: [] }
    const src = m.line.sources[0]
    scope.lines.push({
      ref: m.ref,
      qty: m.qty,
      designation: m.line.signature.tag,
      notes: `from ${src?.sheet ?? '?'}; construction basis: ${m.mountingBasis}`,
    })
    byScope.set(name, scope)
  }
  const input: NativeEnvelopeInput = { projectNumber: opts.projectNumber, scopes: [...byScope.values()] }
  return buildNativeEnvelope(input)
}
