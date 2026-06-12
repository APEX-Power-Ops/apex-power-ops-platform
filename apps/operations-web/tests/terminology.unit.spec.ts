/**
 * SC3 field-terminology helpers (task #129) — unit tests.
 *
 * The served TerminologyBlock wins; absent block = the RULED fallbacks
 * (operator red-line 2026-06-11: Q2 MFR, Q3 N/A, Q5 "Test Current",
 * plug = "Rating plug (In)").
 */
import { test, expect } from '@playwright/test'

import {
  elementDisplay,
  plugLabel,
  testCurrentLabel,
  trustBadgeWord,
  trustTitle,
} from '../lib/terminology'
import { delayBasisLabel } from '../lib/etu-plot-request'
import type { TerminologyBlock } from '../lib/breaker-resources'

const TERM: TerminologyBlock = {
  lineage: 'micrologic_iec',
  elements: {
    ltpu: { code: 'LTPU', label: 'Long-Time Pickup', symbol: 'Ir' },
    gfpu: { code: 'EL', label: 'Earth-Leakage Pickup', symbol: 'IΔn', note: 'not a ground-fault overcurrent test' },
  },
  plug_label: 'Rating plug (In)',
  test_current_label: 'Test Current',
  trust: { 'delay.db': { badge: 'MFR', text: 'Manufacturer time band (validated)' } },
  method_labels: { band_table: 'Manufacturer delay band (per-sensor)' },
}

test('elementDisplay prefers the served lineage row (symbol + code rename)', () => {
  expect(elementDisplay('ltpu', 'LTPU', 'Long-Time Pickup', TERM)).toEqual({
    code: 'LTPU', label: 'Long-Time Pickup', symbol: 'Ir', note: null,
  })
  const el = elementDisplay('gfpu', 'GFPU', 'Ground-Fault Pickup', TERM)
  expect(el.code).toBe('EL')
  expect(el.label).toBe('Earth-Leakage Pickup')
  expect(el.symbol).toBe('IΔn')
})

test('elementDisplay falls back to the built-in meta without a served row', () => {
  expect(elementDisplay('std', 'STD', 'Short-Time Delay', TERM)).toEqual({
    code: 'STD', label: 'Short-Time Delay', symbol: null, note: null,
  })
  expect(elementDisplay('std', 'STD', 'Short-Time Delay', null)).toEqual({
    code: 'STD', label: 'Short-Time Delay', symbol: null, note: null,
  })
})

test('the ruled badge words serve with and without the block (Q2 MFR / Q3 N/A)', () => {
  expect(trustBadgeWord('delay.db', TERM)).toBe('MFR')
  expect(trustBadgeWord('delay.db', null)).toBe('MFR')
  expect(trustBadgeWord('delay.unsupported', null)).toBe('N/A')
  expect(trustBadgeWord('delay.verify', null)).toBe('VERIFY')
  expect(trustBadgeWord('pickup.db', null)).toBe('MFR')
})

test('trustTitle leads with field phrasing, keeps the engineering audit trail', () => {
  expect(trustTitle('delay.db', 'route 0 — validated row-for-row (G4)', TERM)).toBe(
    'Manufacturer time band (validated) — route 0 — validated row-for-row (G4)',
  )
  expect(trustTitle('delay.db', 'reason only', null)).toBe('reason only')
})

test('plug and test-current labels: ruled fallbacks (the Plug-(Ir) fix / Q5)', () => {
  expect(plugLabel(TERM)).toBe('Rating plug (In)')
  expect(plugLabel(null)).toBe('Rating plug (In)')
  expect(testCurrentLabel(null)).toBe('Test Current')
})

test('delayBasisLabel speaks the ruled method vocabulary', () => {
  expect(delayBasisLabel('timing_source=ltd_reference_window')).toBe(
    'Manufacturer LTD tolerance (device library)',
  )
  expect(delayBasisLabel('timing_source=ltd_reference_window_generic')).toContain(
    'no manufacturer tolerance on file',
  )
  expect(delayBasisLabel('timing_source=band_table')).toBe('Manufacturer delay band (per-sensor)')
  expect(delayBasisLabel('timing_source=i2x_composite')).toBe(
    'Manufacturer I²t characteristic (validated)',
  )
})

test('delayBasisLabel prefers a served method_labels map (exact + i2x prefix)', () => {
  const labels = { band_table: 'OVERRIDE BAND', i2x: 'OVERRIDE I2X' }
  expect(delayBasisLabel('timing_source=band_table', labels)).toBe('OVERRIDE BAND')
  expect(delayBasisLabel('timing_source=i2x_ramp', labels)).toBe('OVERRIDE I2X')
  expect(delayBasisLabel('timing_source=maint_profile', labels)).toBe(
    'Maintenance-mode (ARMS) profile',
  )
})
