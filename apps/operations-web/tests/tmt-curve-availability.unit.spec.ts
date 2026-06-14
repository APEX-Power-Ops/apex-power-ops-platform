import { test, expect } from '@playwright/test'
import { tmtCurveAvailability } from '../lib/tmt-curve-availability'

// E2E audit F06: TMT frames whose `available_trip_classes` is empty carry no thermal
// curve (magnetic-only MCPs, switches/disconnectors, electronic-trip devices). The
// curve view must honestly withhold instead of rendering an empty/blank plot.

test('curve is available when trip classes exist', () => {
  const r = tmtCurveAvailability([1, 2])
  expect(r.hasCurve).toBe(true)
  expect(r.note).toBeNull()
})

test('curve is withheld with an honest note when there are no trip classes', () => {
  const r = tmtCurveAvailability([])
  expect(r.hasCurve).toBe(false)
  expect(r.note).toContain('No thermal-magnetic trip curve')
})

test('curve is withheld for null/undefined trip classes (defensive)', () => {
  expect(tmtCurveAvailability(null).hasCurve).toBe(false)
  expect(tmtCurveAvailability(undefined).hasCurve).toBe(false)
})
