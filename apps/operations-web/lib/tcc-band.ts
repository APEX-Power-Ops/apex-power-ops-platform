// Composite-boundary band helpers (#122, G4 §3g) + tolerance-envelope
// helpers (#124) — pure logic for the lvbreakertcc Screen-3 render, kept out
// of the page component so it can be unit-tested without a browser.

import type {
  EtuPlotCompositeBand,
  EtuPlotEnvelopeBand,
  EtuPlotEnvelopeElementBasis,
  PlotCurvePoint,
} from './breaker-resources'

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

// ── Tolerance envelope (#124) ───────────────────────────────────────────

/** Close the acceptance envelope into one polygon outline: min boundary
 *  forward, max boundary reversed — same both-boundaries-or-nothing law as
 *  the composite band (a lone boundary must be stroked, never filled). */
export function envelopePolygonPoints(band: EtuPlotEnvelopeBand): PlotCurvePoint[] {
  const min = band.min_points ?? []
  const max = band.max_points ?? []
  if (!min.length || !max.length) return []
  return [...min, ...[...max].reverse()]
}

/** Honesty notes for the envelope: withheld/truncated-out elements (the
 *  corridor never spans an uncertified element's region — it ends there)
 *  and elements whose max edge reuses the open data. */
export function envelopeNote(band: EtuPlotEnvelopeBand): string | null {
  const parts: string[] = []
  const withheld = band.no_envelope_elements ?? []
  if (withheld.length) {
    parts.push(`${withheld.join(', ')}: no envelope over their region (no certified acceptance basis)`)
  }
  const openOnly = band.open_only_elements ?? []
  if (openOnly.length) {
    parts.push(`${openOnly.join(', ')}: max edge from open data (no clear curve served)`)
  }
  return parts.length ? parts.join(' · ') : null
}

const fmtSignedPct = (v: number | null): string => {
  if (v == null) return '—'
  const r = Math.round(Math.abs(v) * 10) / 10
  return `${v < 0 ? '−' : '+'}${r}`
}

/** One per-element basis line for the legend panel, e.g.
 *  "LTD: PU −10/+10% (DB) · time −26.8/+0% (mfr DS2 tol)". The flagged
 *  generic fallback reads "(generic est)" so a placeholder never passes as
 *  DB-authoritative (NETA=mfr law). */
export function envelopeBasisLine(b: EtuPlotEnvelopeElementBasis): string {
  const pu = `PU ${fmtSignedPct(b.pu_tol_lo_pct)}/${fmtSignedPct(b.pu_tol_hi_pct)}% (DB)`
  let time: string
  if (b.time_source === 'published_band') {
    time = 'time = published band'
  } else if (b.time_tol_lo_pct != null && b.time_tol_hi_pct != null) {
    const basis = b.estimated ? 'generic est' : 'mfr DS2 tol'
    time = `time ${fmtSignedPct(b.time_tol_lo_pct)}/${fmtSignedPct(b.time_tol_hi_pct)}% (${basis})`
  } else {
    time = 'time —'
  }
  return `${b.element}: ${pu} · ${time}`
}
