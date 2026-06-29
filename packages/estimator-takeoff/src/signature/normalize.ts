import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, BreakerSignature, Coolant, Mounting, MountingBasis, MvType, RelayRole, RelaySignature, RelayTechnology, TransformerSignature, TripFunction, VoltageBasis } from './types'
import type { OperatorQuestion, OperatorQuestionCode } from '../buckets/types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(?<!\d)(\d{2,6})\s*AF\s*\/\s*(\d{2,6})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
const NON_BREAKER = /\b(PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

const TRANSFORMER_DEVICE = /\b(XFMR|transformer|dry.?type|pad.?mount|oil.?filled)\b/i
const KVA_RATING = /(?<!\w)\d+(?:\.\d+)?\s*kVA\b/i

const RELAY_DEVICE = /\b(protective\s+relay|relay|SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom)\b/i
const ANSI_FN = /\b(2[1-7]|32|37|38|40|46N?|47|49[RT]?|50N?|51N?|55|59|60|63|64|67|79|81|86|87[TBGN]?)\b/gi
// Transformer-protection accessory relays (pressure/temperature/Buchholz/gas) are NOT standalone
// protective-relay DEVICES the firm prices. Exclude them from token-based recognition so a plain
// "FAULT PRESSURE RELAY" does not become a priced relay (an explicit candidateKind:'relay' still wins).
const RELAY_ACCESSORY = /\b((sudden|fault)\s*pressure|pressure|buchholz|gas\s*accumulator)\s*relay\b/i
// A relay MODEL family is a strong device anchor (device-first); it outranks a transformer text token.
const RELAY_MODEL = /\b(SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom)\b/i

function looksLikeTransformer(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'relay') return false                  // relay producer signal wins over XFMR text
  if (x.candidateKind === 'transformer') return true
  // A relay MODEL + tag outranks a transformer text token (device-first) ONLY when the row lacks
  // strong transformer evidence. A real transformer (kVA rating or a coolant/construction token) that
  // merely MENTIONS a relay model must stay a transformer - never silently reclassified as a relay.
  if (RELAY_MODEL.test(x.raw) && x.tag !== undefined && x.tag.length > 0
      && !KVA_RATING.test(x.raw) && parseCoolant(x.raw) === 'unknown') return false
  if (TRANSFORMER_DEVICE.test(x.raw)) return true
  // FIX 4: kVA-rating fallback must not steal NON_BREAKER rows (UPS, PDU, etc. can carry kVA ratings).
  // A real transformer device token (XFMR/transformer/dry-type/pad-mount/oil-filled) already recognizes above.
  // kVA-breaker guard: also exclude a breaker label that merely carries a kVA value (e.g. a main feeding a 500kVA xfmr) via !looksLikeBreaker.
  return KVA_RATING.test(x.raw) && (x.tag !== undefined && x.tag.length > 0) && !NON_BREAKER.test(x.raw) && !looksLikeBreaker(x.raw)
}

function looksLikeBreaker(raw: string): boolean {
  return BREAKER_HINT.test(raw) || FRAME_TRIP.test(raw)
}

function parseFunctions(raw: string): TripFunction[] {
  const ft = raw.match(FRAME_TRIP)
  const region = ft && ft.index !== undefined ? raw.slice(ft.index + ft[0].length) : raw
  const m = region.match(/\bL(?=[SIGE])(S?)(I?)(G?)(E?)\b/i)
  if (!m) return []
  const tok = m[0].toUpperCase()
  const out: TripFunction[] = ['L']
  if (tok.includes('S')) out.push('S')
  if (tok.includes('I')) out.push('I')
  if (tok.includes('G') || tok.includes('E')) out.push('G')
  return out
}

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

// Transformer attribute parsers -- text-only, fail-closed.
// kVA vs kV: the word boundary after 'kVA' ensures '30KVA' matches but '30kV' does not.
function parseKva(raw: string): number | undefined {
  const m = raw.match(/(?<!\w)(\d+(?:\.\d+)?)\s*kVA\b/i)
  return m ? Number(m[1]) : undefined
}

function parseCoolant(raw: string): Coolant {
  if (/\b(oil.?filled|pad.?mount|liquid|mineral\s*oil)\b/i.test(raw)) return 'liquid'
  if (/\b(dry.?type|\bAA\b|ventilated|cast\s*resin)\b/i.test(raw)) return 'dry'
  return 'unknown'
}

function parsePadMount(raw: string): boolean {
  return /\bpad.?mount\b/i.test(raw)
}

function parseLtc(raw: string): boolean {
  return /\b(LTC|load\s*tap\s*changer|on.?load\s*tap)\b/i.test(raw)
}

function looksLikeRelay(x: ExtractedApparatus): boolean {
  if (x.candidateKind === 'relay') return true                  // explicit producer signal wins
  if (RELAY_ACCESSORY.test(x.raw)) return false                 // transformer accessory, not a priced relay device
  return RELAY_DEVICE.test(x.raw) && x.tag !== undefined && x.tag.length > 0
}

function parseRelayTechnology(raw: string): RelayTechnology {
  if (/\b(SEL-?\d{2,4}[A-Z]?|multilin|beckwith|basler|micom|microprocessor|uP)\b/i.test(raw)) return 'microprocessor'
  if (/\b(electromechanical|EM|solid.?state)\b/i.test(raw)) return 'electromechanical_solid_state'
  return 'unknown'
}

function parseAnsiFunctions(raw: string): string[] {
  const out = new Set<string>()
  for (const m of raw.matchAll(ANSI_FN)) out.add(m[1]!.toUpperCase())
  return [...out]
}

function parseRelayModel(raw: string): string | undefined {
  const m = raw.match(/\b(SEL-?\d{2,4}[A-Z]?|multilin\s*\w+|beckwith\s*\w+|basler\s*\w+|micom\s*\w+)\b/i)
  return m ? m[0] : undefined
}

function deriveRole(ansi: string[], raw: string, tech: RelayTechnology): RelayRole {
  const has = (n: string) => ansi.includes(n)
  // Complex / multi-element roles first (these take their tier even on legacy technology).
  if (has('87T') || /(transformer|XFMR)\s+diff/i.test(raw)) return 'differential'
  if (has('87B') || /\bbus\b/i.test(raw)) return 'bus_differential'
  if (has('87')) return 'differential'
  if (/generator/i.test(raw) || (has('40') && (has('32') || has('46')))) return 'generator'
  if (has('21') || /\b(line|distance)\b/i.test(raw)) return 'line'
  if (/motor/i.test(raw) || (has('49') && has('50') && has('51'))) return 'motor'
  if (/multi.?function/i.test(raw) && /meter/i.test(raw)) return 'multifunction_meter'
  // Legacy single-function EM/solid-state -> the cheap electromechanical tier (before the generic feeder/OC roles).
  if (tech === 'electromechanical_solid_state' && ansi.length <= 1) return 'electromechanical'
  if (/feeder/i.test(raw)) return 'feeder'
  if (has('50') || has('51') || /overcurrent/i.test(raw)) return 'overcurrent'
  return 'unknown'
}

function assessRelay(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  if (FRAME_TRIP.test(x.raw)) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'relay_breaker_conflict',
      questions: [q(x, 'Label names a relay but carries a breaker frame/trip rating - confirm device type before counting.', 'relay_breaker_conflict')],
    }
  }
  const ansiFunctions = parseAnsiFunctions(x.raw)
  const technology = parseRelayTechnology(x.raw)
  const role = deriveRole(ansiFunctions, x.raw, technology)
  const voltageClass = classifyVoltage(x.busVoltageV)   // MAY be undefined - relay voltage is contextual, NOT gated
  const sig: RelaySignature = {
    kind: 'relay', technology, ansiFunctions, role,
    model: parseRelayModel(x.raw),
    voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'relay_recognized', questions: [] }
}

export type AssessmentCode =
  | 'classified'
  | 'transformer_recognized'
  | 'transformer_breaker_conflict'
  | 'transformer_scope_pending'
  | 'transformer_catalog_gap'
  | 'transformer_attrs_unparsed'
  | 'relay_recognized'
  | 'relay_breaker_conflict'
  | 'non_breaker_excluded'
  | 'non_breaker_carries_rating'
  | 'missing_voltage'
  | 'unrecognized_apparatus_row'

export interface ApparatusAssessment {
  signature: ApparatusSignature | null
  questions: OperatorQuestion[]
  isBreakerShaped: boolean
  assessmentCode: AssessmentCode
}

function q(x: ExtractedApparatus, question: string, code: OperatorQuestionCode): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})`, code }
}

// Transformer assessor with full attribute parsing (kVA, coolant, pad-mount, LTC).
// Fail-closed: if kVA AND coolant are both absent -> transformer_attrs_unparsed question.
function assessTransformer(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'missing_voltage',
      questions: [q(x, 'Looks like a transformer but has no associated bus voltage - supply voltage to classify.', 'missing_voltage')],
    }
  }

  const kvaRating = parseKva(x.raw)
  const coolant = parseCoolant(x.raw)
  const padMount = parsePadMount(x.raw)
  const ltc = parseLtc(x.raw)

  // Fail-closed: if neither kVA nor coolant can be determined, ask the operator.
  if (kvaRating === undefined && coolant === 'unknown') {
    return {
      signature: null, isBreakerShaped: false, assessmentCode: 'transformer_attrs_unparsed',
      questions: [q(x, 'Transformer recognized but kVA rating and coolant type could not be parsed - supply kVA and coolant (dry/liquid) to continue.', 'transformer_attrs_unparsed')],
    }
  }

  const sig: TransformerSignature = {
    kind: 'transformer', voltageClass, voltageV: x.busVoltageV,
    voltageBasis: voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none'),
    kvaRating, coolant, padMount, ltc, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature: sig, isBreakerShaped: false, assessmentCode: 'transformer_recognized', questions: [] }
}

// PRIVATE -- the basis-taking core. NOT exported.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  if (looksLikeTransformer(x)) {
    if (FRAME_TRIP.test(x.raw)) {
      return {
        signature: null, isBreakerShaped: false, assessmentCode: 'transformer_breaker_conflict',
        // FIX 5: use 'transformer_breaker_conflict' as the OperatorQuestionCode (now valid in the union)
        questions: [q(x, 'Label names a transformer but carries a breaker frame/trip rating - confirm device type before counting.', 'transformer_breaker_conflict')],
      }
    }
    return assessTransformer(x, voltageBasis)
  }

  if (looksLikeRelay(x)) {
    return assessRelay(x, voltageBasis)
  }

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