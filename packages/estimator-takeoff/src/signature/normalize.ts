import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, Mounting, MountingBasis, MvType, TripFunction, VoltageBasis } from './types'
import type { OperatorQuestion } from '../buckets/types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(?<!\d)(\d{2,6})\s*AF\s*\/\s*(\d{2,6})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
const NON_BREAKER = /\b(TX|XFMR|KVA|PDU|UPS|STS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

function looksLikeBreaker(raw: string): boolean {
  return BREAKER_HINT.test(raw) || FRAME_TRIP.test(raw)
}

// Trip-unit descriptor — TEXT-ONLY. Begins with L AND is followed by at least one of S/I/G/E (so a lone
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
  if (tok.includes('G') || tok.includes('E')) out.push('G') // trailing E (ground-fault sensing) → G
  return out
}

// Construction keywords — require UNAMBIGUOUS context (no bare DO/EO).
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

export interface ApparatusAssessment {
  signature: ApparatusSignature | null
  questions: OperatorQuestion[]
  isBreakerShaped: boolean
}

function q(x: ExtractedApparatus, question: string): OperatorQuestion {
  return { question, context: `${x.tag ?? x.raw} @ ${x.sheet} (${x.evidence})` }
}

// PRIVATE — the basis-taking core. NOT exported.
function assessCore(x: ExtractedApparatus, voltageBasis?: VoltageBasis): ApparatusAssessment {
  // A strong non-breaker device-type token is authoritative exclusion. If it also carries a breaker
  // frame/trip rating, surface a question (do NOT fabricate a breaker line or fire the baseline).
  if (NON_BREAKER.test(x.raw)) {
    if (FRAME_TRIP.test(x.raw)) {
      return { signature: null, isBreakerShaped: false, questions: [q(x, 'Label names a non-breaker device (ATS/MTS/SPD/XFMR/…) but carries a breaker frame/trip rating — confirm device type before counting.')] }
    }
    return { signature: null, questions: [], isBreakerShaped: false }
  }
  if (x.candidateKind !== 'breaker' && !looksLikeBreaker(x.raw)) return { signature: null, questions: [], isBreakerShaped: false }

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
    if (functions.length === 0 && (mounting === 'draw_out' || mounting === 'electrically_operated' || mounting === 'insulated_case')) {
      questions.push(q(x, 'Power-breaker trip-function descriptor (e.g. LSIG) missing — confirm functions (affects LSIG vs LS/LSI vs unmatched).'))
    }
  }
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined

  const basis: VoltageBasis = voltageBasis ?? (x.busVoltageV !== undefined ? 'detected' : 'none')

  const signature: ApparatusSignature = {
    kind: 'breaker', voltageClass, voltageV: x.busVoltageV, voltageBasis: basis, frameA, tripA, functions,
    mounting, mountingBasis, mvType, tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence, block: x.block },
  }
  return { signature, questions, isBreakerShaped: true }
}

// PUBLIC — one-arg only. A caller cannot supply 'asserted'; basis is derived detected/none.
export function assessApparatus(x: ExtractedApparatus): ApparatusAssessment {
  return assessCore(x)
}

// ENGINE-INTERNAL — used by runTakeoff to pass the validated/controlled basis.
// Exported from this module for emit.ts, but DELIBERATELY NOT re-exported from src/index.ts.
export function assessResolvedApparatus(x: ExtractedApparatus, voltageBasis: VoltageBasis): ApparatusAssessment {
  return assessCore(x, voltageBasis)
}

export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  return assessApparatus(x).signature
}