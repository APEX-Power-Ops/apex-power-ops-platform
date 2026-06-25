import type { ExtractedApparatus } from '../extraction/types'
import type { ApparatusSignature, Mounting, MvType, TripFunction } from './types'
import { classifyVoltage } from './voltage'

const FRAME_TRIP = /(\d{2,4})\s*AF\s*\/\s*(\d{2,4})\s*A(?:T|F)?/i
const BREAKER_HINT = /\b(AF\s*\/|MCB|MCCB|ACB|VCB|breaker|draw.?out|vacuum|SF6|air\s*frame|GB|FB)\b/i
// device tags that are clearly NOT breakers
const NON_BREAKER = /\b(TX|XFMR|KVA|PDU|UPS|ATS|MTS|SPD|PQM|METER|BUS\s*DUCT)\b/i

function parseFunctions(raw: string): TripFunction[] {
  const m = raw.match(/\bL?S?I?G?E?\b/g)?.find((t) => /^L?S?I?G?E?$/.test(t) && t.length >= 2 && /[LSIG]/.test(t))
  if (!m) return []
  const out: TripFunction[] = []
  if (m.includes('L')) out.push('L')
  if (m.includes('S')) out.push('S')
  if (m.includes('I')) out.push('I')
  if (m.includes('G') || m.includes('E')) out.push('G') // trailing E = ground-fault sensing → G
  return out
}

function parseMounting(raw: string): Mounting {
  if (/\bMCB\b|panelboard/i.test(raw)) return 'panelboard'
  if (/molded\s*case|MCCB/i.test(raw)) return 'molded_case'
  if (/insulated\s*case|\bICCB\b/i.test(raw)) return 'insulated_case'
  if (/electrically\s*operated|\bEO\b/i.test(raw)) return 'electrically_operated'
  if (/draw.?out|\bDO\b/i.test(raw)) return 'draw_out'
  return 'unknown'
}

function parseMvType(raw: string): MvType {
  if (/vacuum|\bVCB\b/i.test(raw)) return 'vacuum'
  if (/SF6/i.test(raw)) return 'sf6'
  if (/\boil\b/i.test(raw)) return 'oil'
  if (/air\s*frame/i.test(raw)) return 'air_frame'
  return 'unknown'
}

export function normalizeApparatus(x: ExtractedApparatus): ApparatusSignature | null {
  if (NON_BREAKER.test(x.raw) && !/AF\s*\//i.test(x.raw)) return null
  if (!BREAKER_HINT.test(x.raw)) return null
  const voltageClass = classifyVoltage(x.busVoltageV)
  if (!voltageClass) return null
  const ft = x.raw.match(FRAME_TRIP)
  const mounting = voltageClass === 'LV' ? parseMounting(x.raw) : 'unknown'
  const mvType = voltageClass !== 'LV' ? parseMvType(x.raw) : undefined
  return {
    kind: 'breaker',
    voltageClass,
    voltageV: x.busVoltageV,
    frameA: ft ? Number(ft[1]) : undefined,
    tripA: ft ? Number(ft[2]) : undefined,
    functions: parseFunctions(x.raw),
    mounting,
    mvType,
    tag: x.tag,
    source: { sheet: x.sheet, page: x.page, bbox: x.bbox, evidence: x.evidence },
  }
}
