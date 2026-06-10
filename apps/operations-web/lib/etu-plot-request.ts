// Pure builders for the Screen-3 /plot-tcc request (TCC-rendering core pass, lean (a)):
// Screen 3 renders the operator's ACTUAL Screen-2 configuration — plug, pickups,
// delay bands, test multiples, maintenance mode, and any measured field entries —
// instead of re-fetching defaults. When no Screen-2 state exists (the operator
// jumped straight to the curve), the nominal-defaults builder mirrors the legacy
// auto-pick and the caller labels the plot accordingly.

import type {
  AvailableSettingsResponse,
  DelayBandOption,
  EtuPlotMeasurement,
  EtuPlotRequest,
} from './breaker-resources'

export type EtuChosenSettings = {
  plug: number
  ltpu?: number
  stpu?: number
  inst?: number
  gfpu?: number
  ltd?: number
  std?: number
  gfd?: number
}

export type EtuDelayTestMultiples = { ltd: number; std: number; gfd: number }

const PICKUP_ELEMENTS = ['LTPU', 'STPU', 'INST', 'GFPU'] as const
const DELAY_ELEMENTS = ['LTD', 'STD', 'GFD'] as const

// Screen-2 measured inputs are free-text strings keyed by element code. Pickups
// are currents (A), delays are trip times (s); blank / non-numeric entries are
// simply not measurements.
export function parseMeasuredEntries(measured: Record<string, string>): EtuPlotMeasurement[] {
  const out: EtuPlotMeasurement[] = []
  for (const el of PICKUP_ELEMENTS) {
    const v = parseFloat((measured[el] ?? '').trim())
    if (Number.isFinite(v)) out.push({ element: el, measured_current: v })
  }
  for (const el of DELAY_ELEMENTS) {
    const v = parseFloat((measured[el] ?? '').trim())
    if (Number.isFinite(v)) out.push({ element: el, measured_time: v })
  }
  return out
}

export function buildEtuPlotRequest(args: {
  sensorId: number
  chosen: EtuChosenSettings
  testMult: EtuDelayTestMultiples
  maint: boolean
  measured?: Record<string, string>
}): EtuPlotRequest {
  const measurements = parseMeasuredEntries(args.measured ?? {})
  return {
    sensor_id: args.sensorId,
    plug_rating: args.chosen.plug,
    ltpu_setting: args.chosen.ltpu,
    stpu_setting: args.chosen.stpu,
    inst_setting: args.chosen.inst,
    gfpu_setting: args.chosen.gfpu,
    // The explicit fields separate band selection from test multiple (#46/#48);
    // the band value is the option's open_time, which the backend float-matches
    // against band-table open times AND route-2 InvEq dial labels alike.
    ltd_delay_setting: args.chosen.ltd,
    std_delay_setting: args.chosen.std,
    gfd_delay_setting: args.chosen.gfd,
    ltd_test_multiple: args.testMult.ltd,
    std_test_multiple: args.testMult.std,
    gfd_test_multiple: args.testMult.gfd,
    maint_mode: args.maint,
    measurements: measurements.length ? measurements : undefined,
    include_nominal_curve: true,
    include_expected_markers: true,
    include_measured_markers: measurements.length > 0,
  }
}

export function defaultBandValue(bands: DelayBandOption[]): number | undefined {
  const b = bands.find((x) => x.is_default) ?? bands[0]
  return b ? b.open_time : undefined
}

// Nominal defaults when the operator hasn't configured Screen 2: first plug,
// mid-list pickups, default/first delay bands, NETA default test multiples.
export function buildDefaultEtuPlotRequest(
  sensorId: number,
  s: AvailableSettingsResponse,
): EtuPlotRequest {
  const mid = (arr: number[]) => (arr.length ? arr[Math.floor(arr.length / 2)] : undefined)
  return {
    sensor_id: sensorId,
    plug_rating: s.plug_values[0] ?? 0,
    ltpu_setting: mid(s.ltpu_settings),
    stpu_setting: mid(s.stpu_settings),
    inst_setting: mid(s.inst_settings),
    gfpu_setting: mid(s.gfpu_settings),
    ltd_delay_setting: defaultBandValue(s.ltd_settings),
    std_delay_setting: defaultBandValue(s.std_settings),
    gfd_delay_setting: defaultBandValue(s.gfd_settings),
    ltd_test_multiple: 3,
    std_test_multiple: 1.5,
    gfd_test_multiple: 1.5,
    maint_mode: false,
    include_nominal_curve: true,
    include_expected_markers: true,
    include_measured_markers: false,
  }
}

// Tolerance-basis label from a delay table-row's notes ("timing_source=<src>").
// NETA acceptance = manufacturer tolerances (operator law 2026-06-09): the mfr
// basis is stated plainly and anything else is surfaced as exactly what it is.
export function delayBasisLabel(notes: string | null | undefined): string | null {
  if (!notes) return null
  const m = /timing_source=([\w-]+)/.exec(notes)
  if (!m) return null
  const src = m[1]
  if (src === 'ltd_reference_window') return 'mfr tolerance (DS2)'
  if (src === 'ltd_reference_window_generic') return 'generic estimate — no mfr tolerance on file'
  if (src === 'band_table') return 'mfr band (per-sensor DB)'
  if (src.startsWith('i2x_')) return 'validated I²t surface'
  if (src === 'curve_interpolation') return 'curve envelope (open/clear)'
  if (src === 'maint_profile') return 'maintenance-mode profile'
  return src
}
