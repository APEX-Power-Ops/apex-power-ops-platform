import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact, ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature } from '../signature/types'
import { assessResolvedApparatus } from '../signature/normalize'
import { applyVoltageAssertions } from '../signature/voltage-assertions'
import { quantify } from '../quantify/quantify'
import type { QuantifiedLine } from '../quantify/types'
import { matchBreaker } from '../catalog/breaker-map'
import type { MatchedLine, OperatorQuestion, TakeoffResult, UnmatchedCandidate, TakeoffFinding } from '../buckets/types'

export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const { resolved, findings } = applyVoltageAssertions(artifact)
  const sigs: ApparatusSignature[] = []
  const questions: OperatorQuestion[] = []
  const unresolved: { x: ExtractedApparatus; questions: OperatorQuestion[] }[] = []

  for (const { apparatus, voltageBasis } of resolved) {
    const a = assessResolvedApparatus(apparatus, voltageBasis)
    if (a.signature) { sigs.push(a.signature); questions.push(...a.questions); continue }
    unresolved.push({ x: apparatus, questions: a.questions })
  }

  const { lines, locationOnly } = quantify(sigs)

  // index EVERY counted device tag (not just the representative) → its line, for location association
  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) for (const t of l.memberTags) byTag.set(t, l)

  for (const { x, questions: qs } of unresolved) {
    const l = x.tag ? byTag.get(x.tag) : undefined
    if (l) { l.sources.push({ sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block }); continue }
    questions.push(...qs)                                                   // genuinely unresolved → surface
  }

  for (const s of locationOnly) {
    questions.push({ question: `Device ${s.tag ?? '(untagged)'} appears only on a non-authoritative sheet — include it?`, context: `${s.source.sheet} (${s.source.evidence})` })
  }

  for (const w of artifact.profileWarnings ?? []) {
    questions.push({ question: w, context: 'legend/profile' })
  }

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) matchedLines.push({ ref, qty: line.qty, block: line.signature.source.block ?? line.signature.source.sheet, mountingBasis: line.signature.mountingBasis, voltageBasis: line.signature.voltageBasis, line })
    else unmatchedCandidates.push({ reason: `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('') || '—'}`, line })
  }
  return { matchedLines, unmatchedCandidates, operatorQuestions: questions, findings }
}

export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  const blocking = result.findings.filter((f) => f.severity === 'error')
  if (blocking.length > 0) {
    const codes = [...new Set(blocking.map((f) => f.code))].join(', ')
    throw new Error(
      `estimator-takeoff: refusing to emit — ${blocking.length} blocking voltage-assertion finding(s) [${codes}]. ` +
      `Resolve the operator voltage assertions before emitting.`,
    )
  }
  if (result.matchedLines.length === 0) {
    throw new Error('estimator-takeoff: refusing to emit an envelope with zero matched lines — all candidates are unmatched/uncertain; resolve construction/catalog evidence or review the takeoff.')
  }
  const byScope = new Map<string, NativeEnvelopeInput['scopes'][number]>()
  for (const m of result.matchedLines) {
    const name = `Block ${m.block}`
    const scope = byScope.get(name) ?? { name, netaStandard: 'ATS' as NetaStandard, lines: [] }
    const src = m.line.sources[0]
    scope.lines.push({ ref: m.ref, qty: m.qty, designation: m.line.signature.tag, notes: `from ${src?.sheet ?? '?'}; construction basis: ${m.mountingBasis}; voltage ${m.line.signature.voltageV}V (${m.voltageBasis})` })
    byScope.set(name, scope)
  }
  const input: NativeEnvelopeInput = { projectNumber: opts.projectNumber, scopes: [...byScope.values()] }
  return buildNativeEnvelope(input)
}