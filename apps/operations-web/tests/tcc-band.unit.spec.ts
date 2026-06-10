import { expect, test } from '@playwright/test'

import {
  bandPolygonPoints,
  bandWidthNote,
  envelopeBasisLine,
  envelopeNote,
  envelopePolygonPoints,
} from '../lib/tcc-band'
import type {
  EtuPlotCompositeBand,
  EtuPlotEnvelopeBand,
  EtuPlotEnvelopeElementBasis,
} from '../lib/breaker-resources'

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

// ── Tolerance envelope helpers (#124) ──────────────────────────────────

const ENVELOPE: EtuPlotEnvelopeBand = {
  id: 'phase_envelope',
  family: 'phase',
  min_points: [pt(2228, 1_000_000), pt(2228, 700), pt(7200, 3.8), pt(7200, 0.38), pt(100_000, 0.04)],
  max_points: [pt(2723, 1_000_000), pt(2723, 1400), pt(8800, 8.0), pt(8800, 0.66), pt(100_000, 0.09)],
  element_basis: [],
  open_only_elements: [],
  no_envelope_elements: [],
  right_edge_amps: 100_000,
}

test('closes the envelope polygon as min + reversed max', () => {
  const poly = envelopePolygonPoints(ENVELOPE)
  expect(poly.length).toBe(10)
  expect(poly[0]).toEqual(pt(2228, 1_000_000))
  expect(poly[5]).toEqual(pt(100_000, 0.09))
  expect(poly[9]).toEqual(pt(2723, 1_000_000))
})

test('returns no envelope polygon when either boundary is empty', () => {
  expect(envelopePolygonPoints({ ...ENVELOPE, max_points: [] })).toEqual([])
  expect(envelopePolygonPoints({ ...ENVELOPE, min_points: [] })).toEqual([])
})

test('envelope note surfaces withheld and open-only elements', () => {
  expect(envelopeNote(ENVELOPE)).toBeNull()
  expect(envelopeNote({ ...ENVELOPE, no_envelope_elements: ['STD'] })).toContain('STD')
  expect(envelopeNote({ ...ENVELOPE, no_envelope_elements: ['STD'] })).toContain('no envelope')
  const both = envelopeNote({
    ...ENVELOPE,
    no_envelope_elements: ['LTD'],
    open_only_elements: ['GFD'],
  })
  expect(both).toContain('LTD')
  expect(both).toContain('GFD')
})

const LTD_BASIS: EtuPlotEnvelopeElementBasis = {
  element: 'LTD',
  pu_tol_lo_pct: -10,
  pu_tol_hi_pct: 10,
  time_tol_lo_pct: -26.83,
  time_tol_hi_pct: 0,
  pu_source: 'db_sensor_tolerance',
  time_source: 'ltd_curve_tol',
  estimated: false,
}

test('envelope basis line shows PU and time bases per element', () => {
  const ltd = envelopeBasisLine(LTD_BASIS)
  expect(ltd).toContain('LTD')
  expect(ltd).toContain('−10/+10%')
  expect(ltd).toContain('−26.8/+0%')
  expect(ltd).toContain('mfr')
  expect(ltd).not.toContain('est')

  const generic = envelopeBasisLine({
    ...LTD_BASIS,
    time_tol_lo_pct: -30,
    time_source: 'ltd_generic_estimate',
    estimated: true,
  })
  expect(generic).toContain('est')

  const published = envelopeBasisLine({
    ...LTD_BASIS,
    element: 'STD',
    time_tol_lo_pct: null,
    time_tol_hi_pct: null,
    time_source: 'published_band',
  })
  expect(published).toContain('STD')
  expect(published).toContain('published band')
})
