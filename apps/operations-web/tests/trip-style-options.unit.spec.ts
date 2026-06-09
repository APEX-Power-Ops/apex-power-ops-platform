import { expect, test } from '@playwright/test'

import { tripStyleOptionLabel, tripStylesForType, type TripStyleOption } from '../lib/trip-style-options'

// A trip-style row as the cascade returns it (carries its owning trip type so the
// Style dropdown can be scoped to the selected Trip Type).
function typed(over: Partial<{ trip_style_id: number; trip_type_id: number; trip_type_ids: number[] | null; protection_class: string }>) {
  return {
    trip_style_id: 1073,
    trip_type_id: 64,
    trip_type_ids: null as number[] | null,
    protection_class: 'LSIG',
    sensor_count: 8,
    ...over,
  }
}

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

// --- tripStylesForType: scope the Style dropdown to the selected Trip Type ---

test('scopes trip styles to the selected trip type, dropping cross-type leaks', () => {
  const styles = [
    typed({ trip_style_id: 1566, trip_type_id: 64, protection_class: 'LIG' }),  // EntelliGuard
    typed({ trip_style_id: 1073, trip_type_id: 64, protection_class: 'LSIG' }), // EntelliGuard
    typed({ trip_style_id: 251, trip_type_id: 83, protection_class: 'LSIG' }),  // native MVT-PM (other type)
  ]
  const scoped = tripStylesForType(styles, [64])
  expect(scoped.map((s) => s.trip_style_id)).toEqual([1566, 1073])
  // the cross-type native LSIG (251) must NOT survive under the EntelliGuard type
  expect(scoped.some((s) => s.trip_style_id === 251)).toBe(false)
})

test('the WavePro->EntelliGuard case keeps exactly one LSIG (no duplicate)', () => {
  const styles = [
    typed({ trip_style_id: 1566, trip_type_id: 64, protection_class: 'LIG' }),
    typed({ trip_style_id: 1073, trip_type_id: 64, protection_class: 'LSIG' }),
    typed({ trip_style_id: 251, trip_type_id: 83, protection_class: 'LSIG' }),
  ]
  const scoped = tripStylesForType(styles, [64])
  expect(scoped.filter((s) => s.protection_class === 'LSIG')).toHaveLength(1)
})

test('returns all styles untouched when no trip type is selected', () => {
  const styles = [
    typed({ trip_style_id: 1073, trip_type_id: 64 }),
    typed({ trip_style_id: 251, trip_type_id: 83 }),
  ]
  expect(tripStylesForType(styles, null)).toHaveLength(2)
  expect(tripStylesForType(styles, [])).toHaveLength(2)
})

test('matches a style via its merged trip_type_ids, not just trip_type_id', () => {
  const styles = [
    typed({ trip_style_id: 900, trip_type_id: 218, trip_type_ids: [218, 64] }), // representative id differs, merged set includes 64
    typed({ trip_style_id: 251, trip_type_id: 83, trip_type_ids: [83] }),
  ]
  const scoped = tripStylesForType(styles, [64])
  expect(scoped.map((s) => s.trip_style_id)).toEqual([900])
})
