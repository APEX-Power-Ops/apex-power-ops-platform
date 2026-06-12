/**
 * B2.1 field-sheet builder (task #130) — unit tests.
 *
 * The sheet is a pure rendering of the SERVED /calculate + /settings
 * (terminology) payloads — basis identity with the page by construction.
 * These tests pin: row composition + ordering, the SC3 vocabulary (captions,
 * symbols, MFR/N/A badges, Method column), setting/band label resolution,
 * the withheld + est honesty footnotes, measured passthrough, and the
 * sheet-footer law line fallback.
 */
import { test, expect } from '@playwright/test'

import { buildFieldSheet } from '../lib/field-sheet'
import type {
  AvailableSettingsResponse,
  EtuCalculateResponse,
} from '../lib/breaker-resources'

const SETTINGS: AvailableSettingsResponse = {
  sensor_id: 3833,
  plug_values: [400, 600, 800, 1000, 1200],
  ltpu_settings: [0.4, 0.9, 1.0],
  ltd_settings: [
    { band: '0.5', label: '0.5', open_time: 0.5, clear_time: null, is_default: false },
    { band: '4', label: '4', open_time: 4, clear_time: null, is_default: false },
  ],
  std_settings: [
    { band: '0.3', label: '0.3', open_time: 0.23, clear_time: 0.32, is_default: false },
  ],
  gfd_settings: [
    { band: 'Off', label: 'Off', open_time: 0.02, clear_time: 0.08, is_default: false },
  ],
  ltd_multipliers: [],
  stpu_settings: [1.5, 5, 10],
  inst_settings: [2, 10, 15],
  gfpu_settings: [0.2, 0.4],
  units: { ltpu: 'x In', stpu: 'x Ir', inst: 'x In', gfpu: 'x In' },
  terminology: {
    lineage: 'micrologic_iec',
    elements: {
      ltpu: { code: 'LTPU', label: 'Long-Time Pickup', symbol: 'Ir' },
      ltd: { code: 'LTD', label: 'Long-Time Delay', symbol: 'tr' },
      stpu: { code: 'STPU', label: 'Short-Time Pickup', symbol: 'Isd' },
      std: { code: 'STD', label: 'Short-Time Delay', symbol: 'tsd' },
      inst: { code: 'INST', label: 'Instantaneous', symbol: 'Ii' },
      gfpu: { code: 'GFPU', label: 'Ground-Fault Pickup', symbol: 'Ig' },
      gfd: { code: 'GFD', label: 'Ground-Fault Delay', symbol: 'tg' },
    },
    plug_label: 'Rating plug (In)',
    test_current_label: 'Test Current',
    trust: {
      'pickup.db': { badge: 'MFR', method_text: 'Manufacturer per-device tolerance (device library).' },
      'delay.db': { badge: 'MFR', method_text: 'Manufacturer time band for this sensor + setting (validated).' },
      'delay.unsupported': { badge: 'N/A', method_text: 'No certified trip time — record the measured value; acceptance per the manufacturer TCC.' },
    },
    method_labels: {
      ltd_reference_window: 'Manufacturer LTD tolerance (device library)',
      ltd_reference_window_generic: 'Estimated band −30%/+0% — no manufacturer tolerance on file (flagged)',
      band_table: 'Manufacturer delay band (per-sensor)',
      i2x: 'Manufacturer I²t characteristic (validated)',
    },
    notes: {
      withheld: 'No certified expected time for this element; record the measured value; acceptance per the manufacturer TCC.',
      est: 'Estimated −30/+0% band; no manufacturer tolerance on file.',
      sheet_footer: 'Acceptance values are manufacturer tolerances per the device library; NETA ATS table values are used only where labeled as fallback.',
    },
  },
}

const CALC: EtuCalculateResponse = {
  sensor_id: 3833,
  sensor_desc: '1200 Masterpact NW',
  plug_rating: 1200,
  maint_mode: false,
  maint_capable: true,
  maint_support_level: 'full',
  resolved_equipment: null,
  warnings: [],
  elements: [
    { element: 'LTPU', kind: 'pickup', test_current: 1080, limit_low: 1026, limit_high: 1134, multiplier: 1, calc_method: null, time_limit_low: null, time_limit_high: null, delay_seconds: null, notes: null, delay_route: null, trust: null, trust_reason: null },
    { element: 'LTD', kind: 'delay', test_current: 3240, limit_low: null, limit_high: null, multiplier: 3, calc_method: null, time_limit_low: 11.2, time_limit_high: 16, delay_seconds: 16, notes: 'timing_source=ltd_reference_window_generic', delay_route: null, trust: 'db', trust_reason: 'LTD reference window' },
    { element: 'STPU', kind: 'pickup', test_current: 6000, limit_low: 5100, limit_high: 6900, multiplier: 1, calc_method: null, time_limit_low: null, time_limit_high: null, delay_seconds: null, notes: null, delay_route: null, trust: null, trust_reason: null },
    { element: 'STD', kind: 'delay', test_current: 9000, limit_low: null, limit_high: null, multiplier: 1.5, calc_method: null, time_limit_low: 0.23, time_limit_high: 0.32, delay_seconds: 0.23, notes: 'timing_source=band_table', delay_route: 1, trust: 'db', trust_reason: 'I2X composite (#72)' },
    { element: 'GFD', kind: 'delay', test_current: 720, limit_low: null, limit_high: null, multiplier: 1.5, calc_method: null, time_limit_low: null, time_limit_high: null, delay_seconds: null, notes: null, delay_route: 4, trust: 'unsupported', trust_reason: 'GE-TU route — solver not built' },
  ],
}

const INPUT = {
  selection: { breakerLabel: 'Square-D Masterpact NW 1200', tripLabel: 'Square-D MICROLOGIC 6.0' },
  sensorId: 3833,
  settings: SETTINGS,
  chosen: { plug: 1200, ltpu: 0.9, stpu: 5, inst: 10, gfpu: 0.4, ltd: 4, std: 0.23, gfd: 0.02 },
  testMult: { ltd: 3, std: 1.5, gfd: 1.5 },
  measured: { STPU: '5980' },
  maint: false,
  calc: CALC,
  generatedAt: '2026-06-11 18:00',
}

test('rows follow element order with SC3 captions, symbols and badges', () => {
  const sheet = buildFieldSheet(INPUT)
  expect(sheet.rows.map((r) => r.code)).toEqual(['LTPU', 'LTD', 'STPU', 'STD', 'GFD'])
  const ltpu = sheet.rows[0]
  expect(ltpu.label).toBe('Long-Time Pickup')
  expect(ltpu.symbol).toBe('Ir')
  expect(ltpu.badge).toBe('MFR')
  expect(ltpu.testAt).toBe('1×')
  expect(ltpu.testCurrent).toBe('1,080 A')
  expect(ltpu.expected).toBe('1,080 A')
  expect(ltpu.min).toBe('1,026 A')
  expect(ltpu.max).toBe('1,134 A')
  expect(ltpu.method).toContain('Manufacturer per-device tolerance')
})

test('pickup settings render with the served unit; delay settings show the band label', () => {
  const sheet = buildFieldSheet(INPUT)
  expect(sheet.rows[0].setting).toBe('0.9 × In')
  const ltd = sheet.rows.find((r) => r.code === 'LTD')!
  expect(ltd.setting).toBe('4')
  expect(ltd.testAt).toBe('3×')
  expect(ltd.expected).toBe('16 s')
  expect(ltd.min).toBe('11.2 s')
  expect(ltd.max).toBe('16 s')
})

test('the generic LTD band is flagged est* and carries the est footnote', () => {
  const sheet = buildFieldSheet(INPUT)
  const ltd = sheet.rows.find((r) => r.code === 'LTD')!
  expect(ltd.estimated).toBe(true)
  expect(ltd.method).toContain('no manufacturer tolerance on file')
  expect(sheet.footnotes.some((f) => f.includes('Estimated −30/+0%'))).toBe(true)
})

test('withheld delay rows stay withheld: dashes, N/A badge, honesty footnote', () => {
  const sheet = buildFieldSheet(INPUT)
  const gfd = sheet.rows.find((r) => r.code === 'GFD')!
  expect(gfd.withheld).toBe(true)
  expect(gfd.badge).toBe('N/A')
  expect(gfd.expected).toBe('— †')
  expect(gfd.min).toBe('—')
  expect(gfd.max).toBe('—')
  expect(gfd.testCurrent).toBe('720 A') // the inject current stays field-valid
  expect(sheet.footnotes.some((f) => f.startsWith('† No certified expected time'))).toBe(true)
})

test('measured values pass through; header carries the confirmation block', () => {
  const sheet = buildFieldSheet(INPUT)
  expect(sheet.rows.find((r) => r.code === 'STPU')!.measured).toBe('5980')
  expect(sheet.header.breaker).toBe('Square-D Masterpact NW 1200')
  expect(sheet.header.trip).toBe('Square-D MICROLOGIC 6.0')
  expect(sheet.header.sensor).toBe('1200 Masterpact NW')
  expect(sheet.header.sensorId).toBe(3833)
  expect(sheet.header.plugLabel).toBe('Rating plug (In)')
  expect(sheet.header.plugValue).toBe('1,200 A')
  expect(sheet.generatedAt).toBe('2026-06-11 18:00')
})

test('the sheet-footer law line serves from the dictionary with a ruled fallback', () => {
  const sheet = buildFieldSheet(INPUT)
  expect(sheet.footerLaw).toContain('Acceptance values are manufacturer tolerances')
  const bare = buildFieldSheet({ ...INPUT, settings: { ...SETTINGS, terminology: null } })
  expect(bare.footerLaw).toContain('manufacturer tolerances')
  // Without the served block the captions fall back to the built-in meta.
  expect(bare.rows[0].label).toBe('Long-Time Pickup')
  expect(bare.rows[0].symbol).toBeNull()
})

test('maintenance mode is surfaced on the sheet', () => {
  const sheet = buildFieldSheet({ ...INPUT, maint: true, calc: { ...CALC, maint_mode: true } })
  expect(sheet.maint).toBe(true)
})

test('no calc -> empty rows (the component gates the button on calc readiness)', () => {
  const sheet = buildFieldSheet({ ...INPUT, calc: null })
  expect(sheet.rows).toEqual([])
})
