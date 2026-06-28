import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, BreakerSignature, Mounting, MountingBasis, MvType, TransformerSignature, TripFunction, VoltageBasis } from './types'
import type { OperatorQuestion, OperatorQuestionCode } from '../buckets/types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(?<!\d)(\d{2,6})\s*AF\s*\/\s*(\d{2,6})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
const NON_BREAKER = /\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i   // TX/XFMR/KVA removed

const TRANSFORMER_DEVICE = /\b(XFMR|transformer|dry.?type|pad.?mount|oil.?filled)\b/i
const KVA_RATING = /(?<!\w)\d+(?:\.\d+)?\s*kVA\b/i

function looksLikeTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'transformer') return true
  if (TRANSFORMER_DEVICE.test(x.raw)) return true
  return KVA_RATING.test(x.raw) && (x.tag !== undefined && x.tag.length > 0)   // rating+designation, never bare KVA
}

function looksLikeBreaker(raw: string): boolean {
  return BREAKER_HINT.test(raw) || FRAME_TRIP.test(raw)
}

// Trip-unit descriptor -- TEXT-ONLY. Begins with L AND is followed by at least one of S/I/G/E (so a lone
// 'L' word is not a function), searched AFTER the frame/trip spec. Rejects noise like 'GE'/'SE'/'L PHASE'.
function parseFunctions(raw: string): TripFunction[] {
  const ft = raw.match(FRAME_TRIP)
  const region = ft && ft.index !== undefined ? raw.slice(ft.index + ft[0].length) : raw
  const m = region.match(/\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i)
  if (!m) return []
  const tok = m[0].toUpperCase()
  const out: TripFunction[] = ['L']
  if (tok.includes('S')) out.push('S')
  if (tok.includes('I')) out.push('I')
  if (tok.includes('G') || tok.includes('E')) out.push('G') // trailing E (ground-fault sensing) -> G
  return out
}

// Construction keywords -- require UNAMBIGUOUS context (no bare DO/EO).
function parseMounting(raw: string): Mounting {
  if (/\bMCB\b|panelboard/i.test(raw)) return 'panelboard'
  if (/molded\s*case|MCCB/i.test(raw)) return 'molded_case'
  if (/insulated\s*case|\bICCB\b/i.test(raw)) return 'insulated_case'
  if (/electrically\s*operated|\(EO\)/i.test(raw)) return 'electrically_operated'
  if (/draw.?out|\bD\/O\b|\(DO\)/i.test(raw)) return 'draw_out'
  return 'unknown'
}

function parseMvType(raw: string): MvType {
  if (/vacuum|\bVCB\b/i.test(raw)) return 'vacuum'
  if (/SF6/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/air\s*frame/i.test(raw)) return 'air_frame'
  return 'unknown'
}

function resolveMounting(
  x: ExtractedApparatus, frameA: number | undefined, functions: TripFunction[],
): { mounting: Mounting; basis: MountingBasis; conflict: boolean } {
  const textMount = parseMounting(x.raw)
  if (x.mountingHint) {
    const conflict = textMount !== 'unknown' && textMount !== x.mountingHint
    return { mounting: x.mountingHint, basis: 'hint', conflict }
  }
  if (textMount !== 'unknown') return { mounting: textMount, basis: 'text', conflict: false }
  const hasG = functions.includes('G')
  if (frameA !== undefined && frameA >= 800 && hasG) return { mounting: 'draw_out', basis: 'estimating_baseline', conflict: false }
  return { mounting: 'unknown', basis: 'none', conflict: false }
}

export type AssessmentCode =
  | 'classified'                      // a breaker signature was built
  | 'transformer_recognized'          // a transformer signature was built
  | 'transformer_breaker_conflict'    // label names a transformer but carries a breaker frame/trip rating
  | 'transformer_scope_pending'       // transformer recognized; no resolved scope input (Task 7)
  | 'transformer_catalog_gap'         // transformer recognized; no ref-group covers it
  | 'transformer_attrs_unparsed'      // transformer recognized; attribute parsing failed
  | 'non_breaker_excluded'            // NON_BREAKER token, no rating -> disposition 'ignored'
  | 'non_breaker_carries_rating'      // NON_BREAKER token + rating   -> disposition 'question'
  | 'missing_voltage'                 // breaker/tx-shaped, no voltage -> disposition 'question'
  | 'unrecognized_apparatus_row'      // not breaker-shaped            -> disposition 'question'

export interface ApparatusAssessment {
  signature: ApparatusSignature | null
  questions: OperatorQuestion[]
  isBreakerShaped: boolean
  assessmentCode: AssessmentCode
}

function q(x: ExtractedApparatus, question: string, code: OperatorQuestionCode): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})`, code }
}

// Stub transformer assessor -- Task 4 will add attribute parsing (kVA, coolant, pad-mount, LTC).
function assessTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'missing_voltage',
      questions: [q(x, 'Looks like a transformer but has no associated bus voltage - supply voltage to classify.', 'missing_voltage')],
    }
  }
  const sig: TransformerSignature = {
    kind: 'transformer', voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    coolant: 'unknown', tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'transformer_recognized', questions: [] }
}

// PRIVATE -- the basis-taking core. NOT exported.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // Transformer recognition -- BEFORE the NON_BREAKER exclusion.
  // Evidence-gated: device token (XFMR/transformer/dry-type/...) OR kVA-rating+tag; bare KVA word alone does NOT qualify.
  if (looksLikeTransformer(x)) {
    if (FRAME_TRIP.test(x.raw)) {
      return {
        signature: null, isBreakerShaped: false, assessmentCode: 'transformer_breaker_conflict',
        questions: [q(x, 'Label names a transformer but carries a breaker frame/trip rating - confirm device type before counting.', 'non_breaker_carries_rating')],
      }
    }
    return assessTransformer(x, voltageBasis)
  }

  // A strong non-breaker device-type token is authoritative exclusion. If it also carries a breaker
  // frame/trip rating, surface a question (do NOT fabricate a breaker line or fire the baseline).
  if (NON_BREAKER.test(x.raw)) {
    if (FRAME_TRIP.test(x.raw)) {
      return { signature: null, isBreakerShaped: false, questions: [q(x, 'Label names a non-breaker device (ATS/MTS/SPD/etc.) but carries a breaker frame/trip rating - confirm device type before counting.', 'non_breaker_carries_rating')], assessmentCode: 'non_breaker_carries_rating' }
    }
    return { signature: null, questions: [], isBreakerShaped: false, assessmentCode: 'non_breaker_excluded' }
  }
  if (x.candidateKind !== 'breaker' && !looksLikeBreaker(x.raw)) return { signature: null, questions: [], isBreakerShaped: false, assessmentCode: 'unrecognized_apparatus_row' }

  const questions: OperatorQuestion[] = []
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    questions.push(q(x, 'Looks like a breaker but has no associated bus voltage - supply voltage to classify (LV/MV/HV).', 'missing_voltage'))
    return { signature: null, questions, isBreakerShaped: true, assessmentCode: 'missing_voltage' }
  }

  const ft = x.raw.match(FRAME_TRIP)
  const frameA = ft ? Number(ft[1]) : undefined
  const tripA = ft ? Number(ft[2]) : undefined
  const functions = parseFunctions(x.raw)

  if (voltageClass === 'LV' && !ft) {
    questions.push(q(x, 'LV breaker frame/trip rating (AF/AT) could not be parsed - verify rating.', 'lv_frame_trip_unparsed'))
  }

  let mounting: Mounting = 'unknown'
  let mountingBasis: MountingBasis = 'none'
  if (voltageClass === 'LV') {
    const r = resolveMounting(x, frameA, functions)
    mounting = r.mounting
    mountingBasis = r.basis
    if (r.conflict) {
      questions.push(q(x, `Construction hint "${x.mountingHint}" conflicts with the label text - verify breaker construction.`, 'mounting_hint_conflict'))
    }
    if (functions.length === 0 && (mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case')) {
      questions.push(q(x, 'Power-breaker trip-function descriptor (e.g. LSIG) missing - confirm functions (affects LSIG vs LS/LSI vs unmatched).', 'missing_power_functions'))
    }
  }
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined

  const basis: VoltageBasis = voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')

  const signature: BreakerSignature = {
    kind: 'breaker', voltageClass, voltageV: x.busVoltageV, voltageBasis: basis, frameA, tripA, functions,
    mounting, mountingBasis, mvType, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature, questions, isBreakerShaped: true, assessmentCode: 'classified' }
}

// PUBLIC -- one-arg only. A caller cannot supply 'asserted'; basis is derived detected/none.
export function assessApparatus(x: ExtractedApparatus): ApparatusAssessment {
  return assessCore(x)
}

// ENGINE-INTERNAL -- used by runTakeoff to pass the validated/controlled basis.
// Exported from this module for emit.ts, but DELIBERATELY NOT re-exported from src/index.ts.
export function assessResolvedApparatus(x: ExtractedApparatus, voltageBasis: VoltageBasis): ApparatusAssessment {
  return assessCore(x, voltageBasis)
}

export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  return assessApparatus(x).signature
}
