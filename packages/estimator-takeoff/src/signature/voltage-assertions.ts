import type { ExtractedApparatus, ExtractionArtifact } from '../extraction/types'
import type { VoltageBasis } from './types'
import type { TakeoffFinding } from '../buckets/types'

export interface ResolvedApparatus {
  apparatus: ExtractedApparatus     // effective busVoltageV already applied/cleared
  voltageBasis: VoltageBasis        // authoritative — recomputed here, never read from input
}

function detectedOrNone(busVoltageV: number | undefined): VoltageBasis {
  return busVoltageV !== undefined ? 'detected' : 'none'
}

function safePreview(value: unknown): string {
  try {
    return (JSON.stringify(value) ?? String(value)).slice(0, 80)
  } catch {
    return String(value).slice(0, 80)
  }
}

interface ValidPair { tag: string; voltageV: number; actor?: string; source?: string }

export function applyVoltageAssertions(
  artifact: ExtractionArtifact,
): { resolved: ResolvedApparatus[]; findings: TakeoffFinding[] } {
  const rawAssertions: unknown = artifact.voltageAssertions
  const findings: TakeoffFinding[] = []
  const passthrough = (): ResolvedApparatus[] =>
    artifact.apparatus.map((apparatus) => ({ apparatus, voltageBasis: detectedOrNone(apparatus.busVoltageV) }))

  // Container shape guard — the engine is the authoritative JSON seam; never throw on malformed input.
  if (rawAssertions === undefined) return { resolved: passthrough(), findings }
  if (!Array.isArray(rawAssertions)) {
    findings.push({
      code: 'voltage_assertion_invalid_shape', severity: 'error',
      message: 'voltageAssertions must be an array — all assertions ignored.',
      context: 'voltageAssertions (not an array)',
    })
    return { resolved: passthrough(), findings }
  }
  if (rawAssertions.length === 0) return { resolved: passthrough(), findings }

  const tainted = new Set<string>()
  const validPairs: ValidPair[] = []

  // Per-assertion shape guard FIRST (missing/empty/non-array tags → coded error, never a throw),
  // then voltage validation; taint tags of invalid entries (Global: invalid → error + taint).
  for (const item of rawAssertions as unknown[]) {
    const a = item as { voltageV?: unknown; tags?: unknown; actor?: string; source?: string }
    if (a == null || typeof a !== 'object' || !Array.isArray(a.tags) || a.tags.length === 0) {
      findings.push({
        code: 'voltage_assertion_invalid_shape', severity: 'error',
        message: 'Malformed voltage assertion (missing, empty, or non-array tags) — rejected.',
        context: `assertion ${safePreview(a)}`,
      })
      continue
    }
    const tags = a.tags as string[]
    if (!(typeof a.voltageV === 'number' && Number.isInteger(a.voltageV) && a.voltageV > 0)) {
      for (const tag of tags) {
        tainted.add(tag)
        findings.push({
          code: 'voltage_assertion_invalid_voltage', severity: 'error',
          message: `Voltage assertion ${String(a.voltageV)} for ${tag} is not a positive integer — rejected.`,
          context: `${tag} (assert ${String(a.voltageV)}V)`,
          detail: { tag, assertedV: typeof a.voltageV === 'number' ? a.voltageV : undefined, actor: a.actor, source: a.source },
        })
      }
      continue
    }
    for (const tag of tags) validPairs.push({ tag, voltageV: a.voltageV, actor: a.actor, source: a.source })
  }

  // Group valid pairs by tag; duplicate tag → error + taint (Global: duplicate strict, even same voltage).
  const byTag = new Map<string, ValidPair[]>()
  for (const p of validPairs) (byTag.get(p.tag) ?? byTag.set(p.tag, []).get(p.tag)!).push(p)
  for (const [tag, ps] of byTag) {
    if (ps.length > 1) {
      tainted.add(tag)
      const volts = [...new Set(ps.map((p) => p.voltageV))].join('/')
      findings.push({
        code: 'voltage_assertion_duplicate_tag', severity: 'error',
        message: `Tag ${tag} is asserted ${ps.length} times (${volts}V) — ambiguous, rejected.`,
        context: `${tag} (${ps.length} assertions)`,
        detail: { tag },
      })
    }
  }

  // Unknown tag → error (no device to taint).
  const presentTags = new Set(artifact.apparatus.map((x) => x.tag).filter((t): t is string => !!t))
  for (const tag of byTag.keys()) {
    if (!presentTags.has(tag)) {
      findings.push({
        code: 'voltage_assertion_unknown_tag', severity: 'error',
        message: `Asserted tag ${tag} does not match any extracted device — check the tag/sheet.`,
        context: `${tag} (unknown)`,
        detail: { tag },
      })
    }
  }

  // Effective single-assertion map for non-tainted, present tags.
  const effective = new Map<string, ValidPair>()
  for (const [tag, ps] of byTag) {
    if (tainted.has(tag) || !presentTags.has(tag)) continue
    if (ps.length === 1) effective.set(tag, ps[0]!)
  }

  const resolved: ResolvedApparatus[] = artifact.apparatus.map((apparatus) => {
    const tag = apparatus.tag
    if (tag && tainted.has(tag)) {
      // Taint: clear effective voltage so no detected fallback can price it.
      return { apparatus: { ...apparatus, busVoltageV: undefined }, voltageBasis: 'none' }
    }
    const eff = tag ? effective.get(tag) : undefined
    if (eff) {
      const detectedV = apparatus.busVoltageV
      if (detectedV !== undefined && detectedV !== eff.voltageV) {
        findings.push({
          code: 'voltage_assertion_conflict', severity: 'warning',
          message: `Asserted ${eff.voltageV}V overrides detected ${detectedV}V for ${tag} — operator wins.`,
          context: `${tag} (detected ${detectedV}V → asserted ${eff.voltageV}V)`,
          detail: { tag, detectedV, assertedV: eff.voltageV, actor: eff.actor, source: eff.source },
        })
      }
      return { apparatus: { ...apparatus, busVoltageV: eff.voltageV }, voltageBasis: 'asserted' }
    }
    return { apparatus, voltageBasis: detectedOrNone(apparatus.busVoltageV) }
  })

  return { resolved, findings }
}