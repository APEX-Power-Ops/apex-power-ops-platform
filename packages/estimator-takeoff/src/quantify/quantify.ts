import type { ApparatusSignature } from '../signature/types'
import type { QuantifiedLine } from './types'

const AUTHORITATIVE = (e: string) => e === 'one-line' || e.endsWith('-schedule')

function specKey(s: ApparatusSignature): string {
  return [
    s.voltageClass, s.mounting, s.mvType ?? '-', s.functions.join(''),
    s.frameA ?? '-', s.tripA ?? '-', s.source.block ?? '-',   // block included → one line (and scope) per electrical block
  ].join('|')
}

// Stable device identity used for BOTH grouping AND source-retrieval (identical formula in both places).
function deviceId(s: ApparatusSignature): string {
  return s.tag ?? `${specKey(s)}@${s.source.sheet}:${s.source.bbox.join(',')}`
}

// Prefer the RICHEST authoritative occurrence (known construction) so a sparse one-line row does not win
// over a detailed schedule row for the same device.
function pickAuthoritative(occ: ApparatusSignature[]): ApparatusSignature | undefined {
  const auths = occ.filter((o) => AUTHORITATIVE(o.source.evidence))
  return auths.find((o) => o.mounting !== 'unknown') ?? auths[0]
}

export function quantify(sigs: ApparatusSignature[]): {
  lines: QuantifiedLine[]
  locationOnly: ApparatusSignature[]
} {
  const byDevice = new Map<string, ApparatusSignature[]>()
  for (const s of sigs) {
    const id = deviceId(s)
    ;(byDevice.get(id) ?? byDevice.set(id, []).get(id)!).push(s)
  }

  const counted: ApparatusSignature[] = []
  const locationOnly: ApparatusSignature[] = []
  const sourcesByDevice = new Map<string, ApparatusSignature['source'][]>()
  for (const [id, occ] of byDevice) {
    const auth = pickAuthoritative(occ)
    if (!auth) { locationOnly.push(occ[0]!); continue }
    counted.push(auth)
    sourcesByDevice.set(id, occ.map((o) => o.source))
  }

  const bySpec = new Map<string, ApparatusSignature[]>()
  for (const s of counted) {
    const k = specKey(s)
    ;(bySpec.get(k) ?? bySpec.set(k, []).get(k)!).push(s)
  }
  const lines: QuantifiedLine[] = [...bySpec.values()].map((group) => ({
    signature: group[0]!,
    qty: group.length,
    sources: group.flatMap((s) => sourcesByDevice.get(deviceId(s)) ?? [s.source]),
    memberTags: group.map((s) => s.tag).filter((t): t is string => !!t),
    countedFromAuthoritative: true as const,
  }))
  return { lines, locationOnly }
}
