import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, Mounting, MountingBasis, MvType, TripFunction } from './types'
import type { OperatorQuestion } from '../buckets/types'
import { classifyVoltage } from './voltage'

// Frame/trip amps (2–6 digits). The non-digit lookbehind prevents capturing the tail of a longer
// number, e.g. 10000AF must yield 10000, not 0000.
const FRAME_TRIP = /(?<!\d)(\d{2,6})\s*AF\s*\/\s*(\d{2,6})\s*A(?:T|F)?/i
// A label looks like a breaker if it carries a breaker keyword OR a frame/trip spec. (The old bare
// "AF/" alternative was dead behind \b on a real frame like "4000AF"; FRAME_TRIP.test covers it.)
const BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
const NON_BREAKER = /\b(TX|XFMR|KVA|PDU|UPS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

function looksLikeBreaker(raw: string): boolean {
  return BREAKER_HINT.test(raw) || FRAME_TRIP.test(raw)
}

// Trip-unit descriptor — TEXT-ONLY, never inferred. A real descriptor begins with L (long-time is
// always present), then optional S,I,G,E in order, and is annotated AFTER the frame/trip spec. This
// rejects label/manufacturer noise ('GE','SE', orphan letters) that must NOT fabricate a ground-fault.
function parseFunctions(raw: string): TripFunction[] {
  const ft = raw.match(FRAME_TRIP)
  const region = ft && ft.index !== undefined ? raw.slice(ft.index + ft[0].length) : raw
  const m = region.match(/\bL(S?)(I?)(G?)(E?)\b/i)
  if (!m) return []
  const tok = m[0].toUpperCase()
  const out: TripFunction[] = ['L']
  if (tok.includes('S')) out.push('S')
  if (tok.includes('I')) out.push('I')
  if (tok.includes('G') || tok.includes('E')) out.push('G') // trailing E (ground-fault sensing) → G
  return out
}

// Construction keywords — require UNAMBIGUOUS context. Bare two-letter DO/EO tokens were removed: an
// incidental 'DO'/'EO' in a tag must not assert real construction and silence the guarded fallback.
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

// LV construction resolution with explicit provenance + a hint/text conflict flag:
//   1) explicit mountingHint (evidence) → basis 'hint'; conflict=true if text says something concrete & different
//   2) construction keyword in text → basis 'text'
//   3) conservative estimating baseline: frameA>=800 WITH ground-fault → draw_out → basis 'estimating_baseline'
//   4) fail-closed → 'unknown' → basis 'none' (never silently draw-out)
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

export interface ApparatusAssessment {
  signature: ApparatusSignature | null   // null when the row cannot be classified
  questions: OperatorQuestion[]          // first-class parser-failure / uncertainty questions
  isBreakerShaped: boolean               // passed a breaker hint (so a null signature is a real gap, not a skip)
}

function q(x: ExtractedApparatus, question: string): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})` }
}

// Full assessment of one extracted apparatus → a breaker signature and/or parser-failure questions.
export function assessApparatus(x: ExtractedApparatus): ApparatusAssessment {
  if (NON_BREAKER.test(x.raw) && !FRAME_TRIP.test(x.raw)) return { signature: null, questions: [], isBreakerShaped: false }
  if (!looksLikeBreaker(x.raw)) return { signature: null, questions: [], isBreakerShaped: false }

  const questions: OperatorQuestion[] = []
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) {
    questions.push(q(x, 'Looks like a breaker but has no associated bus voltage — supply voltage to classify (LV/MV/HV).'))
    return { signature: null, questions, isBreakerShaped: true }
  }

  const ft = x.raw.match(FRAME_TRIP)
  const frameA = ft ? Number(ft[1]) : undefined
  const tripA = ft ? Number(ft[2]) : undefined
  const functions = parseFunctions(x.raw)

  if (voltageClass === 'LV' && !ft) {
    questions.push(q(x, 'LV breaker frame/trip rating (AF/AT) could not be parsed — verify rating.'))
  }

  let mounting: Mounting = 'unknown'
  let mountingBasis: MountingBasis = 'none'
  if (voltageClass === 'LV') {
    const r = resolveMounting(x, frameA, functions)
    mounting = r.mounting
    mountingBasis = r.basis
    if (r.conflict) {
      questions.push(q(x, `Construction hint "${x.mountingHint}" conflicts with the label text — verify breaker construction.`))
    }
    // a power-breaker construction with unknown trip functions will be matched as LS/LSI by default — surface it
    if (functions.length === 0 && (mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case')) {
      questions.push(q(x, 'Power-breaker trip-function descriptor (e.g. LSIG) missing — confirm functions (affects LSIG vs LS/LSI).'))
    }
  }
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined

  const signature: ApparatusSignature = {
    kind: 'breaker',
    voltageClass,
    voltageV: x.busVoltageV,
    frameA,
    tripA,
    functions,
    mounting,
    mountingBasis,
    mvType,
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature, questions, isBreakerShaped: true }
}

// Back-compat thin wrapper: a breaker signature or null. Questions are available via assessApparatus.
export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  return assessApparatus(x).signature
}
