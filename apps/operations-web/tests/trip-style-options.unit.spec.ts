import { expect, test } from '@playwright/test'

import { tripStyleOptionLabel, type TripStyleOption } from '../lib/trip-style-options'

function style(over: Partial<TripStyleOption>): TripStyleOption {
  return {
    trip_style_id: 1073,
    trip_model_display: 'Entelliguard',
    trip_style_name: 'WavePro',
    protection_class: 'LSIG',
    sensor_count: 8,
    ...over,
  }
}

test('labels a style by its protection class and sensor count', () => {
  expect(tripStyleOptionLabel(style({ protection_class: 'LSIG', sensor_count: 8 }))).toBe('LSIG (8)')
})

test('the two EntelliGuard classes get distinct labels', () => {
  const lsig = tripStyleOptionLabel(style({ protection_class: 'LSIG', sensor_count: 8 }))
  const lig = tripStyleOptionLabel(style({ protection_class: 'LIG', sensor_count: 8 }))
  expect(lsig).toBe('LSIG (8)')
  expect(lig).toBe('LIG (8)')
  expect(lsig).not.toBe(lig)
})

test('falls back to the model display when protection class is missing', () => {
  expect(tripStyleOptionLabel(style({ protection_class: null, sensor_count: 16 }))).toBe('Entelliguard (16)')
})

test('an empty protection class falls back to the model display', () => {
  expect(tripStyleOptionLabel(style({ protection_class: '   ', sensor_count: 4 }))).toBe('Entelliguard (4)')
})

test('falls back to the style name when neither class nor model display is present', () => {
  expect(
    tripStyleOptionLabel(style({ protection_class: null, trip_model_display: null, trip_style_name: 'MVT-PM', sensor_count: 2 })),
  ).toBe('MVT-PM (2)')
})
