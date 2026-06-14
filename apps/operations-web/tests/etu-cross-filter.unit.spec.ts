import { expect, test } from '@playwright/test'

import { effectiveBreakerClass } from '../lib/etu-cross-filter'

// F02 — the cross-class cascade leak. breaker_id / breaker_style_id are PER-CLASS serials
// that COLLIDE across ICCB / MCCB / PCB, so every breaker-scoped fetch must carry the
// breaker's class. When the operator skips the class dropdown, the class is DERIVED from
// the chosen breaker. The bridge + alt-trip fetches already did this; the two cross-filter
// cascades passed `bClass || null` and leaked foreign-class trips (a Square D breaker
// surfacing an Entelliguard "MICROLOGIC 6.0"). One shared resolver keeps the four call
// sites from drifting apart again.

test('the explicit class dropdown wins when set', () => {
  expect(effectiveBreakerClass('MCCB', 'PCB')).toBe('MCCB')
})

test('falls back to the derived breaker class when the class dropdown was skipped (the F02 fix)', () => {
  expect(effectiveBreakerClass(null, 'mccb')).toBe('mccb')
  expect(effectiveBreakerClass('', 'pcb')).toBe('pcb')
})

test('resolves to null when neither an explicit nor a derived class is available', () => {
  expect(effectiveBreakerClass(null, null)).toBeNull()
  expect(effectiveBreakerClass('', undefined)).toBeNull()
})
