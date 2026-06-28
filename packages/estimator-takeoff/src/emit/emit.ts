import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact, ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, BreakerSignature, TransformerSignature } from '../signature/types'
import { assessResolvedApparatus } from '../signature/normalize'
import type { AssessmentCode } from '../signature/normalize'
import { applyVoltageAssertions } from '../signature/voltage-assertions'
import { quantify, isAuthoritativeEvidence } from '../quantify/quantify'
import type { QuantifiedLine } from '../quantify/types'
import { matchBreaker } from '../catalog/breaker-map'
import { matchTransformer } from '../catalog/transformer-map'
import type {
  MatchedLine, OperatorQuestion, TakeoffResult, UnmatchedCandidate, TakeoffFinding,
  ApparatusDisposition, ApparatusDispositionStatus, DispositionReasonCode, ScopePendingLine,
} from '../buckets/types'

const UNSTAMPED = '__unstamped__'

// baseDisp creates a LOUD sentinel disposition: its `reason` is UNSTAMPED so assertExhaustive can detect any
// row that was never stamped (status+reasonCode alone cannot -- a real unrecognized_apparatus_row shares them).
function baseDisp(x: ExtractedApparatus, i: number): ApparatusDisposition {
  return {
    inputIndex: i, tag: x.tag, raw: x.raw, sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence,
    status: 'question', reasonCode: 'unrecognized_apparatus_row', reason: UNSTAMPED,
  }
}

function stamp(
  d: ApparatusDisposition[], i: number, status: ApparatusDispositionStatus,
  reasonCode: DispositionReasonCode, reason: string, ref?: string, lineKey?: string,
): void {
  const cur = d[i]!
  cur.status = status
  cur.reasonCode = reasonCode
  cur.reason = reason
  if (ref !== undefined) cur.ref = ref
  if (lineKey !== undefined) cur.lineKey = lineKey
}

function assertExhaustive(d: ApparatusDisposition[], n: number): void {
  if (d.length !== n) throw new Error(`estimator-takeoff: disposition count ${d.length} does not equal apparatus count ${n}`)
  d.forEach((x, i) => {
    if (x.inputIndex !== i) throw new Error(`estimator-takeoff: disposition at ${i} has misaligned inputIndex ${x.inputIndex}`)
    if (x.reason === UNSTAMPED) throw new Error(`estimator-takeoff: apparatus row ${i} (${x.tag ?? x.raw}) was never assigned a disposition`)
  })
}

export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const apparatus = artifact.apparatus
  const dispositions: ApparatusDisposition[] = apparatus.map((x, i) => baseDisp(x, i))
  const { resolved, findings } = applyVoltageAssertions(artifact)
  const questions: OperatorQuestion[] = []
  const sigs: ApparatusSignature[] = []
  const unresolved: { i: number; x: ExtractedApparatus; questions: OperatorQuestion[]; assessmentCode: AssessmentCode }[] = []

  resolved.forEach(({ apparatus: x, voltageBasis }, i) => {
    const a = assessResolvedApparatus(x, voltageBasis)
    if (a.signature) {                                  // counted candidate; stamped later as matched/unmatched/associated/location
      sigs.push({ ...a.signature, inputIndex: i })
      for (const qq of a.questions) questions.push({ ...qq, inputIndex: i })
      return
    }
    // No signature: drive the disposition from the STRUCTURED assessmentCode, NOT questions.length.
    if (a.assessmentCode === 'non_breaker_excluded') {
      stamp(dispositions, i, 'ignored', 'non_breaker_excluded', 'non-breaker device token')   // FINAL, not attach-eligible
      return
    }
    // every other null shape is a question; assessmentCode is one of non_breaker_carries_rating |
    // missing_voltage | unrecognized_apparatus_row, each also a valid DispositionReasonCode.
    // ('classified' is excluded by the a.signature guard above; 'non_breaker_excluded' handled above)
    stamp(dispositions, i, 'question', a.assessmentCode as DispositionReasonCode, a.questions[0]?.question ?? 'producer candidate could not be classified as a breaker')
    unresolved.push({ i, x, questions: a.questions, assessmentCode: a.assessmentCode })
  })

  const { lines, associated, locationOnly } = quantify(sigs)
  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) for (const t of l.memberTags) byTag.set(t, l)

  // Attach + suppress ONLY a benign same-device occurrence: a breaker-shaped row missing only its voltage on a
  // NON-authoritative sheet (a plausible power-plan re-occurrence of a counted device). NEVER launder a genuine
  // ambiguity (non_breaker_carries_rating, unrecognized_apparatus_row) or an AUTHORITATIVE missing-voltage row
  // (a distinct breaker) into associated_source just because its tag collides with a counted line - that is the
  // silent-loss class this slice exists to kill. Ineligible rows KEEP their 'question' disposition + surface.
  for (const { i, x, questions: qs, assessmentCode } of unresolved) {
    const attachEligible = assessmentCode === 'missing_voltage' && !isAuthoritativeEvidence(x.evidence)
    const l = attachEligible && x.tag ? byTag.get(x.tag) : undefined
    if (l) {
      l.sources.push({ sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block })
      stamp(dispositions, i, 'associated_source', 'unresolved_tag_attached', `source for ${l.lineKey}`, undefined, l.lineKey)
    } else {
      for (const qq of qs) questions.push({ ...qq, inputIndex: i })
    }
  }

  for (const { inputIndex, lineKey } of associated) {
    stamp(dispositions, inputIndex, 'associated_source', 'occurrence_of_counted_device', `occurrence of ${lineKey}`, undefined, lineKey)
  }

  for (const { inputIndex } of locationOnly) {
    stamp(dispositions, inputIndex, 'question', 'location_only_non_authoritative', 'device only on a non-authoritative sheet')
    questions.push({ question: 'Device appears only on a non-authoritative sheet - include it?', context: `${apparatus[inputIndex]!.sheet}`, code: 'location_only', inputIndex })
  }

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  const scopePendingLines: ScopePendingLine[] = []

  for (const line of lines) {
    const sig = line.signature
    if (sig.kind === 'breaker') {
      // kind === 'breaker': TypeScript now knows sig is BreakerSignature
      const bsig: BreakerSignature = sig
      const ref = matchBreaker(bsig)
      if (ref) {
        matchedLines.push({ ref, qty: line.qty, block: bsig.source.block ?? bsig.source.sheet, mountingBasis: bsig.mountingBasis, voltageBasis: bsig.voltageBasis, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'matched', 'catalog_rule', `matched ${ref}`, ref, line.lineKey)
      } else {
        const reason = `no catalog rule for ${bsig.mounting}/${bsig.functions.join('') || '-'}`
        unmatchedCandidates.push({ reason, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'no_catalog_rule', reason, undefined, line.lineKey)
      }
      continue
    }
    // kind === 'transformer'
    const tsig: TransformerSignature = sig
    const scope = matchTransformer(tsig)
    if (scope) {
      scopePendingLines.push({ candidateRefs: scope.group, defaultRef: scope.defaultRef, scopeQuestion: scope.scopeQuestion, qty: line.qty, block: tsig.source.block ?? tsig.source.sheet, line })
      for (const i of line.memberIndices) stamp(dispositions, i, 'scope_pending', 'transformer_scope_pending', scope.scopeQuestion, scope.defaultRef, line.lineKey)
      questions.push({ question: scope.scopeQuestion, context: `${tsig.tag ?? tsig.source.sheet} (candidate group: ${scope.group.join(' | ')})`, code: 'transformer_scope_pending' })
    } else {
      const reason = `recognized transformer (coolant ${tsig.coolant}, ${tsig.kvaRating ?? '?'}kVA) - no applicable priced ref-group`
      unmatchedCandidates.push({ reason, line })
      for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'transformer_catalog_gap', reason, undefined, line.lineKey)
      findings.push({ code: 'transformer_catalog_gap', severity: 'warning', message: reason, context: tsig.tag ?? tsig.source.sheet })
      questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: tsig.tag ?? tsig.source.sheet, code: 'transformer_catalog_gap' })
    }
  }

  for (const w of artifact.profileWarnings ?? []) questions.push({ question: w, context: 'legend/profile', code: 'profile_warning' })

  assertExhaustive(dispositions, apparatus.length)
  return { matchedLines, unmatchedCandidates, scopePendingLines, operatorQuestions: questions, findings, dispositions }
}

export function emitEnvelope(result: Pick<TakeoffResult, 'matchedLines' | 'unmatchedCandidates' | 'operatorQuestions' | 'findings'>, opts: { projectNumber: string }) {
  const blocking = result.findings.filter((f) => f.severity === 'error')
  if (blocking.length > 0) {
    const codes = [...new Set(blocking.map((f) => f.code))].join(', ')
    throw new Error(
      `estimator-takeoff: refusing to emit - ${blocking.length} blocking voltage-assertion finding(s) [${codes}]. ` +
      `Resolve the operator voltage assertions before emitting.`,
    )
  }
  if (result.matchedLines.length === 0) {
    throw new Error('estimator-takeoff: refusing to emit an envelope with zero matched lines - all candidates are unmatched/uncertain; resolve construction/catalog evidence or review the takeoff.')
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
