import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact, ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, BreakerSignature, TransformerSignature, RelaySignature, GfpSignature } from '../signature/types'
import { assessResolvedApparatus } from '../signature/normalize'
import type { AssessmentCode } from '../signature/normalize'
import { applyVoltageAssertions } from '../signature/voltage-assertions'
import { quantify, isAuthoritativeEvidence } from '../quantify/quantify'
import type { QuantifiedLine } from '../quantify/types'
import { matchBreaker } from '../catalog/breaker-map'
import { matchTransformer } from '../catalog/transformer-map'
import { R1_RATIFIED } from '../catalog/transformer-map.data'
import { matchRelay } from '../catalog/relay-map'
import { RELAY_R1_RATIFIED } from '../catalog/relay-map.data'
import { matchGfp } from '../catalog/gfp-map'
import { GFP_R1_RATIFIED } from '../catalog/gfp-map.data'
import type {
  MatchedLine, OperatorQuestion, TakeoffResult, UnmatchedCandidate, TakeoffFinding,
  ApparatusDisposition, ApparatusDispositionStatus, DispositionReasonCode, ScopePendingLine,
} from '../buckets/types'

const UNSTAMPED = '__unstamped__'

// COMPILER-CHECKED mapping: every non-'classified' AssessmentCode -> a valid DispositionReasonCode.
// A future unmapped code is a COMPILE ERROR (restores the cast-safety invariant killed by 'as DispositionReasonCode').
const ASSESS_TO_REASON: Record<Exclude<AssessmentCode, 'classified'>, DispositionReasonCode> = {
  transformer_recognized:        'transformer_scope_pending',   // unreachable (has signature); present for exhaustiveness
  transformer_breaker_conflict:  'transformer_breaker_conflict',
  transformer_scope_pending:     'transformer_scope_pending',
  transformer_catalog_gap:       'transformer_catalog_gap',
  transformer_attrs_unparsed:    'transformer_attrs_unparsed',
  non_breaker_excluded:          'non_breaker_excluded',
  non_breaker_carries_rating:    'non_breaker_carries_rating',
  missing_voltage:               'missing_voltage',
  unrecognized_apparatus_row:    'unrecognized_apparatus_row',
  relay_recognized:              'relay_scope_pending',   // unreachable (has signature); present for exhaustiveness
  relay_breaker_conflict:        'relay_breaker_conflict',
  gfp_recognized:                'gfp_scope_pending',   // unreachable (has signature); present for exhaustiveness
}

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
  // isBreakerShaped tracks whether normalize recognized the row as breaker-shaped (not transformer-shaped).
  // A transformer-recognized row that is voltage-less gets assessmentCode 'missing_voltage' but isBreakerShaped=false.
  // We use isBreakerShaped to prevent cross-family silent attachment (FIX 6).
  const unresolved: { i: number; x: ExtractedApparatus; questions: OperatorQuestion[]; assessmentCode: AssessmentCode; isBreakerShaped: boolean }[] = []

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
    // every other null shape is a question; use ASSESS_TO_REASON for a compiler-checked mapping
    // ('classified' is excluded by the a.signature guard above; 'non_breaker_excluded' handled above)
    stamp(dispositions, i, 'question', ASSESS_TO_REASON[a.assessmentCode as Exclude<AssessmentCode,'classified'>], a.questions[0]?.question ?? 'producer candidate could not be classified as a breaker')
    unresolved.push({ i, x, questions: a.questions, assessmentCode: a.assessmentCode, isBreakerShaped: a.isBreakerShaped })
  })

  const { lines, associated, locationOnly } = quantify(sigs)
  const byTag = new Map<string, QuantifiedLine>()
  for (const l of lines) if (l.signature.kind === 'breaker') for (const t of l.memberTags) byTag.set(t, l)

  // Attach + suppress ONLY a benign same-device occurrence: a breaker-shaped row missing only its voltage on a
  // NON-authoritative sheet (a plausible power-plan re-occurrence of a counted device). NEVER launder a genuine
  // ambiguity (non_breaker_carries_rating, unrecognized_apparatus_row) or an AUTHORITATIVE missing-voltage row
  // (a distinct breaker) into associated_source just because its tag collides with a counted line - that is the
  // silent-loss class this slice exists to kill. Ineligible rows KEEP their 'question' disposition + surface.
  //
  // FIX 6: also do NOT attach a transformer-shaped row to a (breaker) counted line - cross-family tag collision
  // would fold a voltage-less transformer as 'associated_source' of a breaker (silent cross-family loss).
  // isBreakerShaped=false means the assessor recognized it as transformer-shaped (or genuinely ambiguous non-breaker).
  for (const { i, x, questions: qs, assessmentCode, isBreakerShaped } of unresolved) {
    const attachEligible = assessmentCode === 'missing_voltage'
      && !isAuthoritativeEvidence(x.evidence)
      && isBreakerShaped
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
    if (sig.kind === 'relay') {
      const rsig: RelaySignature = sig
      const scope = matchRelay(rsig)
      if (scope) {
        scopePendingLines.push({
          candidateRefs: scope.group,
          provisionalDefaultRef: scope.defaultRef,   // may be undefined (no-default relay)
          r1Ratified: RELAY_R1_RATIFIED,
          scopeQuestion: scope.scopeQuestion,
          qty: line.qty,
          block: rsig.source.block ?? rsig.source.sheet,
          line,
        })
        for (const i of line.memberIndices) {
          stamp(dispositions, i, 'scope_pending', 'relay_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
          const disp = dispositions[i]!
          disp.candidateRefs = scope.group
          disp.provisionalDefaultRef = scope.defaultRef
          disp.scopeQuestion = scope.scopeQuestion
        }
        questions.push({ question: scope.scopeQuestion, context: `${rsig.tag ?? rsig.source.sheet} (candidate group: ${scope.group.join(' | ')})`, code: 'relay_scope_pending' })
      } else {
        const reason = `recognized relay (role ${rsig.role ?? 'unknown'}) - no applicable priced ref-group`
        unmatchedCandidates.push({ reason, line })
        for (const i of line.memberIndices) stamp(dispositions, i, 'unmatched', 'relay_catalog_gap', reason, undefined, line.lineKey)
        findings.push({ code: 'relay_catalog_gap', severity: 'warning', message: reason, context: rsig.tag ?? rsig.source.sheet })
        questions.push({ question: `Catalog gap: ${reason} - estimator must author/confirm a ref before pricing.`, context: rsig.tag ?? rsig.source.sheet, code: 'relay_catalog_gap' })
      }
      continue
    }
    if (sig.kind === 'gfp') {
      const gsig: GfpSignature = sig
      const scope = matchGfp(gsig)
      scopePendingLines.push({
        candidateRefs: scope.group,
        provisionalDefaultRef: scope.defaultRef,
        r1Ratified: GFP_R1_RATIFIED,
        scopeQuestion: scope.scopeQuestion,
        qty: line.qty,
        block: gsig.source.block ?? gsig.source.sheet,
        line,
      })
      for (const i of line.memberIndices) {
        stamp(dispositions, i, 'scope_pending', 'gfp_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
        const disp = dispositions[i]!
        disp.candidateRefs = scope.group
        disp.provisionalDefaultRef = scope.defaultRef
        disp.scopeQuestion = scope.scopeQuestion
      }
      questions.push({ question: scope.scopeQuestion, context: `${gsig.tag ?? gsig.source.sheet} (standalone GFP; priced per device; NETA 7.14)`, code: 'gfp_scope_pending' })
      continue
    }
    // kind === 'transformer'
    const tsig: TransformerSignature = sig
    const scope = matchTransformer(tsig)
    if (scope) {
      // scope_pending: ref slot is NOT populated (ref implies an authoritative matched ref).
      // candidateRefs, provisionalDefaultRef, and scopeQuestion are carried on the disposition for Gate-2.
      scopePendingLines.push({
        candidateRefs: scope.group,
        provisionalDefaultRef: scope.defaultRef,
        r1Ratified: R1_RATIFIED,
        scopeQuestion: scope.scopeQuestion,
        qty: line.qty,
        block: tsig.source.block ?? tsig.source.sheet,
        line,
      })
      for (const i of line.memberIndices) {
        stamp(dispositions, i, 'scope_pending', 'transformer_scope_pending', scope.scopeQuestion, undefined, line.lineKey)
        const disp = dispositions[i]!
        disp.candidateRefs = scope.group
        disp.provisionalDefaultRef = scope.defaultRef
        disp.scopeQuestion = scope.scopeQuestion
      }
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