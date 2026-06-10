import { expect, test } from '@playwright/test'

import { bandPolygonPoints, bandWidthNote } from '../lib/tcc-band'
import type { EtuPlotCompositeBand } from '../lib/breaker-resources'

const pt = (amps: number, seconds: number) => ({ amps, seconds })

const BAND: EtuPlotCompositeBand = {
  id: 'phase_band',
  family: 'phase',
  open_points: [pt(2475, 1_000_000), pt(2475, 1000), pt(8000, 5.5), pt(8000, 0.42), pt(100_000, 0.05)],
  clear_points: [pt(2475, 1_000_000), pt(2475, 1400), pt(8000, 8.0), pt(8000, 0.6), pt(100_000, 0.08)],
  open_only_elements: [],
  right_edge_amps: 100_000,
}

test('closes the band polygon as open + reversed clear', () => {
  const poly = bandPolygonPoints(BAND)
  expect(poly.length).toBe(10)
  // Walks the open boundary forward…
  expect(poly[0]).toEqual(pt(2475, 1_000_000))
  expect(poly[4]).toEqual(pt(100_000, 0.05))
  // …then the clear boundary in reverse, back to the start.
  expect(poly[5]).toEqual(pt(100_000, 0.08))
  expect(poly[9]).toEqual(pt(2475, 1_000_000))
})

test('returns no polygon when either boundary is empty', () => {
  // Closing a lone boundary with Z would fill a false region — the caller
  // must stroke the surviving boundary as a line instead.
  expect(bandPolygonPoints({ ...BAND, clear_points: [] })).toEqual([])
  expect(bandPolygonPoints({ ...BAND, open_points: [] })).toEqual([])
})

test('band width note names open-only elements', () => {
  expect(bandWidthNote({ ...BAND, open_only_elements: ['LTD', 'STD'] })).toContain('LTD, STD')
  expect(bandWidthNote(BAND)).toBeNull()
})
