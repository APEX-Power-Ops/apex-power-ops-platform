// Composite-boundary band helpers (#122, G4 §3g) — pure logic for the
// lvbreakertcc Screen-3 render, kept out of the page component so it can be
// unit-tested without a browser.

import type { EtuPlotCompositeBand, PlotCurvePoint } from './breaker-resources'

/** Close the band into one polygon outline: the open (min-trip) boundary
 *  forward, then the clear (total-clear) boundary reversed — the classic
 *  shaded TCC band. A fillable polygon needs BOTH boundaries: with either
 *  one missing this returns [] (stroke the surviving boundary as a line —
 *  closing a single polyline would fill a false region). */
export function bandPolygonPoints(band: EtuPlotCompositeBand): PlotCurvePoint[] {
  const open = band.open_points ?? []
  const clear = band.clear_points ?? []
  if (!open.length || !clear.length) return []
  return [...open, ...[...clear].reverse()]
}

/** Honest width annotation: elements whose clear boundary reuses the open
 *  data (the engine serves them open-only), i.e. zero band width there. */
export function bandWidthNote(band: EtuPlotCompositeBand): string | null {
  const els = band.open_only_elements ?? []
  if (!els.length) return null
  return `${els.join(', ')}: open boundary only (no clear curve served) — zero band width`
}
