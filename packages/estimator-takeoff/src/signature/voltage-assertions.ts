import type { ExtractedApparatus, ExtractionArtifact } from '../extraction/types'
import type { VoltageBasis } from './types'
import type { TakeoffFinding } from '../buckets/types'

export interface ResolvedApparatus {
  apparatus: ExtractedApparatus     // effective busVoltageV already applied/cleared
  voltageBasis: VoltageBasis        // authoritative - recomputed here, never read from input
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
interface ValidSheetPair { sheet: string; voltageV: number; actor?: string; source?: string }

export function applyVoltageAssertions(
  artifact: ExtractionArtifact,
): { resolved: ResolvedApparatus[]; findings: TakeoffFinding[] } {
  const rawAssertions: unknown = artifact.voltageAssertions
  const findings: TakeoffFinding[] = []
  const passthrough = (): ResolvedApparatus[] =>
    artifact.apparatus.map((apparatus) => ({ apparatus, voltageBasis: detectedOrNone(apparatus.busVoltageV) }))

  // Container shape guard - the engine is the authoritative JSON seam; never throw on malformed input.
  if (rawAssertions === undefined) return { resolved: passthrough(), findings }
  if (!Array.isArray(rawAssertions)) {
    findings.push({
      code: 'voltage_assertion_invalid_shape', severity: 'error',
      message: 'voltageAssertions must be an array - all assertions ignored.',
      context: 'voltageAssertions (not an array)',
    })
    return { resolved: passthrough(), findings }
  }
  if (rawAssertions.length === 0) return { resolved: passthrough(), findings }

  const tainted = new Set<string>()
  const taintedSheets = new Set<string>()
  const validPairs: ValidPair[] = []
  const validSheetPairs: ValidSheetPair[] = []

  // Per-assertion shape guard FIRST (an assertion must carry non-empty tags OR non-empty sheets),
  // then voltage validation; taint tags of invalid entries (invalid -> error + taint).
  for (const item of rawAssertions as unknown[]) {
    const a = item as { voltageV?: unknown; tags?: unknown; sheets?: unknown; actor?: string; source?: string }
    const rawTags = a?.tags
    const rawSheets = a?.sheets
    const tagsOk = rawTags === undefined || (Array.isArray(rawTags) && rawTags.every((t) => typeof t === 'string'))
    const sheetsOk = rawSheets === undefined || (Array.isArray(rawSheets) && rawSheets.every((s) => typeof s === 'string'))
    const tags = Array.isArray(rawTags) ? (rawTags as string[]) : []
    const sheets = Array.isArray(rawSheets) ? (rawSheets as string[]) : []
    if (a == null || typeof a !== 'object' || !tagsOk || !sheetsOk || (tags.length === 0 && sheets.length === 0)) {
      findings.push({
        code: 'voltage_assertion_invalid_shape', severity: 'error',
        message: 'Malformed voltage assertion (no tags and no sheets) - rejected.',
        context: `assertion ${safePreview(a)}`,
      })
      continue
    }
    if (!(typeof a.voltageV === 'number' && Number.isInteger(a.voltageV) && a.voltageV > 0)) {
      for (const tag of tags) {
        tainted.add(tag)
        findings.push({
          code: 'voltage_assertion_invalid_voltage', severity: 'error',
          message: `Voltage assertion ${String(a.voltageV)} for ${tag} is not a positive integer - rejected.`,
          context: `${tag} (assert ${String(a.voltageV)}V)`,
          detail: { tag, assertedV: typeof a.voltageV === 'number' ? a.voltageV : undefined, actor: a.actor, source: a.source },
        })
      }
      for (const sheet of sheets) {
        taintedSheets.add(sheet)
        findings.push({
          code: 'voltage_assertion_invalid_voltage', severity: 'error',
          message: `Voltage assertion ${String(a.voltageV)} for sheet ${sheet} is not a positive integer - rejected.`,
          context: `${sheet} (assert ${String(a.voltageV)}V)`,
          detail: { sheet, assertedV: typeof a.voltageV === 'number' ? a.voltageV : undefined, actor: a.actor, source: a.source },
        })
      }
      continue
    }
    for (const tag of tags) validPairs.push({ tag, voltageV: a.voltageV, actor: a.actor, source: a.source })
    for (const sheet of sheets) validSheetPairs.push({ sheet, voltageV: a.voltageV, actor: a.actor, source: a.source })
  }

  // Group valid tag pairs; duplicate tag -> error + taint (strict, even same voltage).
  const byTag = new Map<string, ValidPair[]>()
  for (const p of validPairs) (byTag.get(p.tag) ?? byTag.set(p.tag, []).get(p.tag)!).push(p)
  for (const [tag, ps] of byTag) {
    if (ps.length > 1) {
      tainted.add(tag)
      const volts = [...new Set(ps.map((p) => p.voltageV))].join('/')
      findings.push({
        code: 'voltage_assertion_duplicate_tag', severity: 'error',
        message: `Tag ${tag} is asserted ${ps.length} times (${volts}V) - ambiguous, rejected.`,
        context: `${tag} (${ps.length} assertions)`,
        detail: { tag },
      })
    }
  }

  // Unknown tag -> error (no device to taint).
  const presentTags = new Set(artifact.apparatus.map((x) => x.tag).filter((t): t is string => !!t))
  for (const tag of byTag.keys()) {
    if (!presentTags.has(tag)) {
      findings.push({
        code: 'voltage_assertion_unknown_tag', severity: 'error',
        message: `Asserted tag ${tag} does not match any extracted device - check the tag/sheet.`,
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

  // Sheet-scoped assertions (operator sheet-voltage). Precedence tag > detected > sheet: these fill only
  // rows with no per-tag assertion and no detected bus voltage. Fail-closed like tags: an invalid-voltage
  // sheet or a sheet asserted at >1 DISTINCT voltage is tainted (a same-voltage repeat is not a conflict).
  const bySheet = new Map<string, ValidSheetPair[]>()
  for (const p of validSheetPairs) (bySheet.get(p.sheet) ?? bySheet.set(p.sheet, []).get(p.sheet)!).push(p)
  for (const [sheet, ps] of bySheet) {
    const volts = [...new Set(ps.map((p) => p.voltageV))]
    if (volts.length > 1) {
      taintedSheets.add(sheet)
      findings.push({
        code: 'voltage_assertion_sheet_conflict', severity: 'error',
        message: `Sheet ${sheet} is asserted ${volts.join('/')}V - ambiguous, rejected.`,
        context: `${sheet} (${ps.length} assertions)`,
        detail: { sheet },
      })
    }
  }

  // Unknown sheet -> error.
  const presentSheets = new Set(artifact.apparatus.map((x) => x.sheet))
  for (const sheet of bySheet.keys()) {
    if (!presentSheets.has(sheet)) {
      findings.push({
        code: 'voltage_assertion_unknown_sheet', severity: 'error',
        message: `Asserted sheet ${sheet} does not match any extracted device - check the sheet id.`,
        context: `${sheet} (unknown)`,
        detail: { sheet },
      })
    }
  }

  const sheetEffective = new Map<string, ValidSheetPair>()
  for (const [sheet, ps] of bySheet) {
    if (taintedSheets.has(sheet) || !presentSheets.has(sheet)) continue
    sheetEffective.set(sheet, ps[0]!)
  }

  const sheetApplied = new Map<string, number>()
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
          message: `Asserted ${eff.voltageV}V overrides detected ${detectedV}V for ${tag} - operator wins.`,
          context: `${tag} (detected ${detectedV}V to asserted ${eff.voltageV}V)`,
          detail: { tag, detectedV, assertedV: eff.voltageV, actor: eff.actor, source: eff.source },
        })
      }
      return { apparatus: { ...apparatus, busVoltageV: eff.voltageV }, voltageBasis: 'asserted' }
    }
    // Detected wins over a sheet assertion (sheet is the coarsest fallback).
    if (apparatus.busVoltageV !== undefined) return { apparatus, voltageBasis: 'detected' }
    const sv = sheetEffective.get(apparatus.sheet)
    if (sv) {
      sheetApplied.set(apparatus.sheet, (sheetApplied.get(apparatus.sheet) ?? 0) + 1)
      return { apparatus: { ...apparatus, busVoltageV: sv.voltageV }, voltageBasis: 'asserted' }
    }
    return { apparatus, voltageBasis: 'none' }
  })

  // Surface the sheet-level assumption so the envelope never hides that it rests on an operator block
  // attestation. One warning per DISTINCT applied voltage, naming the voltage and the sheets it filled.
  if (sheetApplied.size > 0) {
    const byVoltage = new Map<number, { sheets: string[]; rows: number }>()
    for (const [sheet, rows] of sheetApplied) {
      const v = sheetEffective.get(sheet)!.voltageV
      const g = byVoltage.get(v) ?? { sheets: [], rows: 0 }
      g.sheets.push(sheet)
      g.rows += rows
      byVoltage.set(v, g)
    }
    for (const [v, g] of byVoltage) {
      const sheets = g.sheets.sort()
      findings.push({
        code: 'voltage_assertion_sheet_applied', severity: 'warning',
        message: `${g.rows} row(s) priced under an operator sheet-voltage assumption of ${v}V (sheets: ${sheets.join(', ')}; source operator_sheet_voltage).`,
        context: `operator_sheet_voltage (${sheets.length} sheet(s) @ ${v}V)`,
        detail: { sheets, rows: g.rows },
      })
    }
  }

  return { resolved, findings }
}
