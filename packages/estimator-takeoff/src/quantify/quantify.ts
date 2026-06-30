import type { ApparatusSignature } from '../signature/types'
import type { QuantifiedLine } from './types'

export const isAuthoritativeEvidence = (e: string): boolean => e === 'one-line' || e.endsWith('-schedule')
const AUTHORITATIVE = isAuthoritativeEvidence

function specKey(s: ApparatusSignature): string {
  if (s.kind === 'breaker') {
    return [
      s.voltageClass, s.voltageV ?? '-', s.voltageBasis, s.mounting, s.mvType ?? '-', s.functions.join(''),
      s.frameA ?? '-', s.tripA ?? '-', s.source.block ?? '-',   // voltageV + voltageBasis -> per-tag voltage/provenance preserved
    ].join('|')
  }
  if (s.kind === 'relay') {
    // per-device application tier; voltage optional/contextual; role+technology+model dedup
    return [s.kind, s.role ?? '-', s.technology, s.model ?? '-', s.voltageClass ?? '-', s.source.block ?? '-'].join('|')
  }
  if (s.kind === 'gfp') {
    // single-ref family: per device; voltage optional/contextual; ANSI evidence NOT in the key.
    return [s.kind, s.voltageClass ?? '-', s.source.block ?? '-'].join('|')
  }
  if (s.kind === 'instrument_transformer') {
    return [s.kind, s.itxType, s.voltageClass ?? '-', s.packaging, s.source.block ?? '-'].join('|')   // phaseCount/ratio are evidence, not key
  }
  if (s.kind === 'switch') {
    return [s.kind, s.switchType, s.voltageClass ?? '-', s.fused === undefined ? '-' : (s.fused ? 'F' : 'NF'), s.source.block ?? '-'].join('|')
  }
  // transformer: full key so two transformers that differ only in coolant/kVA/padMount/ltc get separate lines
  return [s.kind, s.voltageClass, s.voltageV ?? '-', s.voltageBasis, s.source.block ?? '-',
          s.coolant, s.kvaRating ?? '-', s.padMount ? 'pad' : '-', s.ltc ? 'ltc' : '-'].join('|')
}

// Stable device identity used for BOTH grouping AND source-retrieval (identical formula in both places).
function deviceId(s: ApparatusSignature): string {
  return s.tag ? `${s.kind}:${s.tag}` : `${specKey(s)}@${s.source.sheet}:${s.source.bbox.join(',')}`
}

// Prefer the RICHEST authoritative occurrence (known construction) so a sparse one-line row does not win
// over a detailed schedule row for the same device.
function pickAuthoritative(occ: ApparatusSignature[]): ApparatusSignature | undefined {
  const auths = occ.filter((o) => AUTHORITATIVE(o.source.evidence))
  if (auths.length === 0) return undefined
  // For breakers: prefer known mounting. For relays: prefer legible role. Otherwise: first authoritative.
  const richBreaker = auths.find((o) => o.kind === 'breaker' && o.mounting !== 'unknown')
  if (richBreaker) return richBreaker
  const richRelay = auths.find((o) => o.kind === 'relay' && o.role !== undefined && o.role !== 'unknown')
  if (richRelay) return richRelay
  const richSwitch = auths.find((o) => o.kind === 'switch' && (o.switchType !== 'unknown' || o.fused !== undefined || o.ampRating !== undefined))
  if (richSwitch) return richSwitch
  return auths[0]
}

export function quantify(sigs: ApparatusSignature[]): {
  lines: QuantifiedLine[]
  associated: { inputIndex: number; lineKey: string }[]
  locationOnly: { inputIndex: number; sig: ApparatusSignature }[]
} {
  const byDevice = new Map<string, ApparatusSignature[]>()
  for (const s of sigs) {
    const id = deviceId(s)
    ;(byDevice.get(id) ?? byDevice.set(id, []).get(id)!).push(s)
  }

  const counted: ApparatusSignature[] = []
  const locationOnly: { inputIndex: number; sig: ApparatusSignature }[] = []
  const nonRep: ApparatusSignature[] = []            // signature-built occurrences that are NOT the representative
  const sourcesByDevice = new Map<string, ApparatusSignature['source'][]>()
  for (const [id, occ] of byDevice) {
    const auth = pickAuthoritative(occ)
    if (!auth) { for (const o of occ) locationOnly.push({ inputIndex: o.inputIndex ?? -1, sig: o }); continue }
    counted.push(auth)
    for (const o of occ) if (o !== auth) nonRep.push(o)
    sourcesByDevice.set(id, occ.map((o) => o.source))
  }

  const bySpec = new Map<string, ApparatusSignature[]>()
  for (const s of counted) {
    const k = specKey(s)
    ;(bySpec.get(k) ?? bySpec.set(k, []).get(k)!).push(s)
  }
  // QuantifiedLine.signature is ApparatusSignature (widened in Task 3 to admit transformer signatures).
  const lines: QuantifiedLine[] = [...bySpec.entries()].map(([k, group]) => ({
    signature: group[0]!,
    qty: group.length,
    sources: group.flatMap((s) => sourcesByDevice.get(deviceId(s)) ?? [s.source]),
    memberTags: group.map((s) => s.tag).filter((t): t is string => !!t),
    memberIndices: group.map((s) => s.inputIndex ?? -1),
    lineKey: k,
    countedFromAuthoritative: true as const,
  }))
  // Map each device to its line's key = the REPRESENTATIVE's specKey. A sparser sibling occurrence can have a
  // different mounting (hence different specKey) than the chosen representative; that asymmetry is exactly why
  // pickAuthoritative exists, so reading specKey(sibling) would point at a wrong/absent line.
  const lineKeyByDevice = new Map<string, string>()
  for (const s of counted) lineKeyByDevice.set(deviceId(s), specKey(s))
  const associated = nonRep.map((o) => ({ inputIndex: o.inputIndex ?? -1, lineKey: lineKeyByDevice.get(deviceId(o))! }))
  return { lines, associated, locationOnly }
}
