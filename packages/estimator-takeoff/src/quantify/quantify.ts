import type { ApparatusSignature } from '../signature/types'
import type { QuantifiedLine } from './types'

const AUTHORITATIVE = (e: string) => e === 'one-line' || e.endsWith('-schedule')

function specKey(s: ApparatusSignature): string {
  return [s.voltageClass, s.mounting, s.mvType ?? '-', s.functions.join(''), s.frameA ?? '-', s.tripA ?? '-'].join('|')
}

// Stable device identity used for BOTH grouping AND source-retrieval. These MUST be identical in
// both places — keying grouping by `…@sheet:bbox` but retrieval by `…@sheet` collides untagged
// devices and drops their sources. Tagged → the tag; untagged → spec + sheet + bbox.
function deviceId(s: ApparatusSignature): string {
  return s.tag ?? `${specKey(s)}@${s.source.sheet}:${s.source.bbox.join(',')}`
}

export function quantify(sigs: ApparatusSignature[]): {
  lines: QuantifiedLine[]
  locationOnly: ApparatusSignature[]
} {
  // 1) group every occurrence by device identity
  const byDevice = new Map<string, ApparatusSignature[]>()
  for (const s of sigs) {
    const id = deviceId(s)
    ;(byDevice.get(id) ?? byDevice.set(id, []).get(id)!).push(s)
  }

  // 2) a device counts only if it has >=1 authoritative occurrence; store sources under the SAME id
  const counted: ApparatusSignature[] = []
  const locationOnly: ApparatusSignature[] = []
  const sourcesByDevice = new Map<string, ApparatusSignature['source'][]>()
  for (const [id, occ] of byDevice) {
    const auth = occ.find((o) => AUTHORITATIVE(o.source.evidence))
    if (!auth) { locationOnly.push(occ[0]!); continue }
    counted.push(auth)
    sourcesByDevice.set(id, occ.map((o) => o.source))
  }

  // 3) aggregate counted devices by spec into quantified lines; retrieve sources by the SAME deviceId
  const bySpec = new Map<string, ApparatusSignature[]>()
  for (const s of counted) {
    const k = specKey(s)
    ;(bySpec.get(k) ?? bySpec.set(k, []).get(k)!).push(s)
  }
  const lines: QuantifiedLine[] = [...bySpec.values()].map((group) => ({
    signature: group[0]!,
    qty: group.length,
    sources: group.flatMap((s) => sourcesByDevice.get(deviceId(s)) ?? [s.source]),
    countedFromAuthoritative: true as const,
  }))
  return { lines, locationOnly }
}
