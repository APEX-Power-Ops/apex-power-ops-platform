/**
 * B2.1 — the field tolerance SHEET builder (task #130; the MVP north-star).
 *
 * Pure assembly of the print-ready per-breaker sheet from the SERVED payloads:
 * /calculate (values, limits, trust) + /settings (options, units, the SC3
 * terminology block). The sheet derives from the SAME routes the page renders,
 * so sheet ↔ page basis identity holds by construction (operator law: NETA
 * acceptance = manufacturer tolerances; decision 5 defer — no new contract).
 *
 * Honesty carries through unchanged (L5): withheld times print as "— †" with
 * the footnote; the generic LTD estimate prints flagged "est*"; the inject
 * current stays on every row (it is always field-valid). No Date access here —
 * the caller stamps generatedAt.
 */

import type {
  AvailableSettingsResponse,
  DelayBandOption,
  EtuCalculateResponse,
  EtuTestCurrentElement,
  TerminologyBlock,
} from './breaker-resources'
import type { EtuChosenSettings } from './etu-plot-request'
import { delayBasisLabel } from './etu-plot-request'
import { elementDisplay, plugLabel, trustBadgeWord } from './terminology'

export type FieldSheetRow = {
  code: string
  label: string
  symbol: string | null
  note: string | null
  kind: 'pickup' | 'delay'
  setting: string
  testAt: string
  testCurrent: string
  expected: string
  min: string
  max: string
  method: string
  badge: string
  withheld: boolean
  estimated: boolean
  measured: string
}

export type FieldSheetHeader = {
  breaker: string
  trip: string
  sensor: string
  sensorId: number | null
  plugLabel: string
  plugValue: string
  lineage: string | null
}

export type FieldSheet = {
  header: FieldSheetHeader
  rows: FieldSheetRow[]
  maint: boolean
  warnings: string[]
  footnotes: string[]
  footerLaw: string
  generatedAt: string
}

export type FieldSheetInput = {
  selection: { breakerLabel: string; tripLabel: string; ratingLabel?: string | null }
  sensorId: number | null
  settings: AvailableSettingsResponse | null
  chosen: EtuChosenSettings | null
  testMult: Record<'ltd' | 'std' | 'gfd', number>
  measured: Record<string, string>
  maint: boolean
  calc: EtuCalculateResponse | null
  generatedAt: string
}

// Element identity: NETA code -> (settings key, kind). Order = the sheet order.
const ELEMENTS: { code: string; key: string; kind: 'pickup' | 'delay' }[] = [
  { code: 'LTPU', key: 'ltpu', kind: 'pickup' },
  { code: 'LTD', key: 'ltd', kind: 'delay' },
  { code: 'STPU', key: 'stpu', kind: 'pickup' },
  { code: 'STD', key: 'std', kind: 'delay' },
  { code: 'INST', key: 'inst', kind: 'pickup' },
  { code: 'GFPU', key: 'gfpu', kind: 'pickup' },
  { code: 'GFD', key: 'gfd', kind: 'delay' },
]

const FALLBACK_LABELS: Record<string, string> = {
  ltpu: 'Long-Time Pickup', ltd: 'Long-Time Delay', stpu: 'Short-Time Pickup',
  std: 'Short-Time Delay', inst: 'Instantaneous', gfpu: 'Ground-Fault Pickup',
  gfd: 'Ground-Fault Delay',
}

// Ruled fallbacks (mirror the dictionary's '*' note rows, red-line 2026-06-11).
const FALLBACK_WITHHELD =
  'No certified expected time for this element; record the measured value; acceptance per the manufacturer TCC.'
const FALLBACK_EST = 'Estimated −30/+0% band; no manufacturer tolerance on file.'
const FALLBACK_FOOTER =
  'Acceptance values are manufacturer tolerances per the device library; NETA ATS table values are used ' +
  'only where labeled as fallback. Pickup tolerances are per-device. Withheld times are deliberate: no ' +
  'certified basis exists — use the manufacturer TCC.'
const FALLBACK_PICKUP_METHOD = 'Manufacturer per-device tolerance (device library).'

const fmtAmp = (v: number | null | undefined): string =>
  v == null ? '—' : `${Math.round(v).toLocaleString('en-US')} A`
const fmtSec = (v: number | null | undefined): string =>
  v == null ? '—' : `${Number.isInteger(v) ? v : +v.toFixed(2)} s`
const fmtMultiple = (v: number): string => `${Number.isInteger(v) ? v : +v.toFixed(2)}×`

function settingDisplay(
  el: { key: string; kind: 'pickup' | 'delay' },
  chosen: EtuChosenSettings | null,
  settings: AvailableSettingsResponse | null,
): string {
  const value = chosen?.[el.key as keyof EtuChosenSettings]
  if (value == null) return '—'
  if (el.kind === 'pickup') {
    const unit = settings?.units?.[el.key as 'ltpu' | 'stpu' | 'inst' | 'gfpu']
    if (unit === 'A') return `${value} A`
    if (unit) return `${value} ${unit.replace(/^x /, '× ')}`
    return String(value)
  }
  // Delay: show the band's faceplate label (the option whose open_time matches).
  const bands = (settings?.[`${el.key}_settings` as 'ltd_settings' | 'std_settings' | 'gfd_settings'] ??
    []) as DelayBandOption[]
  const band = bands.find((b) => b.open_time === value)
  return band?.label ?? String(value)
}

function methodFor(
  e: EtuTestCurrentElement,
  kind: 'pickup' | 'delay',
  withheld: boolean,
  term: TerminologyBlock | null | undefined,
): string {
  if (kind === 'pickup') {
    return term?.trust?.['pickup.db']?.method_text ?? FALLBACK_PICKUP_METHOD
  }
  if (withheld) {
    return term?.trust?.['delay.unsupported']?.method_text
      ?? 'No certified trip time — record the measured value; acceptance per the manufacturer TCC.'
  }
  return (
    delayBasisLabel(e.notes, term?.method_labels)
    ?? term?.trust?.['delay.db']?.method_text
    ?? 'Manufacturer time band (validated)'
  )
}

export function buildFieldSheet(input: FieldSheetInput): FieldSheet {
  const { selection, sensorId, settings, chosen, testMult, measured, maint, calc, generatedAt } = input
  const term = settings?.terminology ?? null

  const byCode = new Map<string, EtuTestCurrentElement>(
    (calc?.elements ?? []).map((e) => [e.element.toUpperCase(), e]),
  )

  const rows: FieldSheetRow[] = []
  let anyWithheld = false
  let anyEstimated = false

  for (const el of ELEMENTS) {
    const e = byCode.get(el.code)
    if (!e) continue
    const disp = elementDisplay(el.key, el.code, FALLBACK_LABELS[el.key], term)
    const delay = el.kind === 'delay'
    const withheld = delay && (e.trust ?? '').toLowerCase() === 'unsupported'
    const estimated = delay && !withheld && (e.notes ?? '').includes('_generic')
    anyWithheld = anyWithheld || withheld
    anyEstimated = anyEstimated || estimated

    const trustKey = delay
      ? `delay.${(e.trust ?? 'verify').toLowerCase()}`
      : 'pickup.db'

    rows.push({
      code: disp.code,
      label: disp.label,
      symbol: disp.symbol ?? null,
      note: disp.note ?? null,
      kind: el.kind,
      setting: settingDisplay(el, chosen, settings),
      testAt: delay ? fmtMultiple(testMult[el.key as 'ltd' | 'std' | 'gfd'] ?? e.multiplier) : '1×',
      testCurrent: fmtAmp(e.test_current),
      expected: withheld
        ? '— †'
        : delay
          ? fmtSec(e.delay_seconds)
          : fmtAmp(e.test_current),
      min: withheld ? '—' : delay ? fmtSec(e.time_limit_low) : fmtAmp(e.limit_low),
      max: withheld ? '—' : delay ? fmtSec(e.time_limit_high) : fmtAmp(e.limit_high),
      method: estimated
        ? `${methodFor(e, el.kind, withheld, term)} (est*)`
        : methodFor(e, el.kind, withheld, term),
      badge: trustBadgeWord(trustKey, term),
      withheld,
      estimated,
      measured: measured[el.code] ?? '',
    })
  }

  const footnotes: string[] = []
  if (anyWithheld) footnotes.push(`† ${term?.notes?.withheld ?? FALLBACK_WITHHELD}`)
  if (anyEstimated) footnotes.push(`est* ${term?.notes?.est ?? FALLBACK_EST}`)

  return {
    header: {
      breaker: selection.breakerLabel,
      trip: selection.tripLabel,
      sensor: calc?.sensor_desc ?? selection.ratingLabel ?? '—',
      sensorId,
      plugLabel: plugLabel(term),
      plugValue: chosen?.plug ? fmtAmp(chosen.plug) : '—',
      lineage: term?.lineage ?? null,
    },
    rows,
    maint: Boolean(maint || calc?.maint_mode),
    warnings: calc?.warnings ?? [],
    footnotes,
    footerLaw: term?.notes?.sheet_footer ?? FALLBACK_FOOTER,
    generatedAt,
  }
}
