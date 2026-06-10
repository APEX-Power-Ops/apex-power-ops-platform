import { expect, test } from '@playwright/test'

import {
  buildDefaultEtuPlotRequest,
  buildEtuPlotRequest,
  defaultBandValue,
  delayBasisLabel,
  parseMeasuredEntries,
} from '../lib/etu-plot-request'
import type { AvailableSettingsResponse, DelayBandOption } from '../lib/breaker-resources'

const CHOSEN = { plug: 1200, ltpu: 0.8, stpu: 2.5, inst: 6, gfpu: 0.4, ltd: 0.5, std: 0.2, gfd: 0.2 }
const MULT = { ltd: 3, std: 1.5, gfd: 1.5 }

test('builds the plot request from the operator Screen-2 state', () => {
  const req = buildEtuPlotRequest({ sensorId: 4628, chosen: CHOSEN, testMult: { ltd: 6, std: 2, gfd: 1.5 }, maint: true })
  expect(req.sensor_id).toBe(4628)
  expect(req.plug_rating).toBe(1200)
  expect(req.ltpu_setting).toBe(0.8)
  expect(req.std_delay_setting).toBe(0.2)
  expect(req.gfd_delay_setting).toBe(0.2)
  expect(req.ltd_test_multiple).toBe(6)
  expect(req.std_test_multiple).toBe(2)
  expect(req.maint_mode).toBe(true)
  expect(req.measurements).toBeUndefined()
  expect(req.include_measured_markers).toBe(false)
})

test('parses measured entries — pickups as current, delays as time, junk skipped', () => {
  const entries = parseMeasuredEntries({
    LTPU: '952', STD: '0.21', GFD: '', INST: 'abc', LTD: ' 4.9 ',
  })
  expect(entries).toEqual([
    { element: 'LTPU', measured_current: 952 },
    { element: 'LTD', measured_time: 4.9 },
    { element: 'STD', measured_time: 0.21 },
  ])
})

test('measured entries ride the request and flip the measured-marker flag', () => {
  const req = buildEtuPlotRequest({
    sensorId: 1, chosen: CHOSEN, testMult: MULT, maint: false,
    measured: { LTPU: '952', STD: '0.21' },
  })
  expect(req.measurements).toHaveLength(2)
  expect(req.include_measured_markers).toBe(true)
})

test('default band value prefers is_default, falls back to the first, uses open_time', () => {
  const bands: DelayBandOption[] = [
    { band: 'I2T Min', label: 'Min', open_time: 0.1, clear_time: 0.2, is_default: false },
    { band: 'I2T Mid', label: 'Mid', open_time: 0.2, clear_time: 0.3, is_default: true },
  ]
  // open_time (numeric, backend-matchable) — NOT Number(band), which is NaN for
  // textual band-table labels like "I2T Mid".
  expect(defaultBandValue(bands)).toBe(0.2)
  expect(defaultBandValue([bands[0]])).toBe(0.1)
  expect(defaultBandValue([])).toBeUndefined()
})

test('nominal-defaults request mirrors the legacy auto-pick', () => {
  const settings = {
    sensor_id: 7,
    plug_values: [800, 1200],
    ltpu_settings: [0.4, 0.6, 0.8],
    ltd_settings: [
      { band: '0.5', label: '0.5', open_time: 0.5, clear_time: null, is_default: false },
      { band: '2', label: '2', open_time: 2, clear_time: null, is_default: false },
    ],
    ltd_multipliers: [],
    std_settings: [
      { band: '0.1', label: '0.1', open_time: 0.1, clear_time: null, is_default: false },
    ],
    gfd_settings: [],
    stpu_settings: [1.5, 2.5, 4],
    inst_settings: [2, 6, 10],
    gfpu_settings: [0.2, 0.4],
  } as unknown as AvailableSettingsResponse
  const req = buildDefaultEtuPlotRequest(7, settings)
  expect(req.plug_rating).toBe(800)
  expect(req.ltpu_setting).toBe(0.6)
  expect(req.ltd_delay_setting).toBe(0.5)
  expect(req.std_delay_setting).toBe(0.1)
  expect(req.gfd_delay_setting).toBeUndefined()
  expect(req.ltd_test_multiple).toBe(3)
  expect(req.include_measured_markers).toBe(false)
})

test('delay basis labels surface the mfr-vs-fallback distinction (NETA = mfr tolerances)', () => {
  expect(delayBasisLabel('timing_source=ltd_reference_window')).toBe('mfr tolerance (DS2)')
  expect(delayBasisLabel('timing_source=ltd_reference_window_generic')).toContain('generic estimate')
  expect(delayBasisLabel('timing_source=band_table')).toBe('mfr band (per-sensor DB)')
  expect(delayBasisLabel('timing_source=i2x_composite')).toBe('validated I²t surface')
  expect(delayBasisLabel('timing_source=curve_interpolation')).toBe('curve envelope (open/clear)')
  expect(delayBasisLabel(null)).toBeNull()
  expect(delayBasisLabel('no marker here')).toBeNull()
})
