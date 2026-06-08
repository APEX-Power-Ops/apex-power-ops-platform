/**
 * ETU compatible-sensor terminal — pure decision logic for the lvbreakertcc dual-axis
 * selector. Extracted from app/lvbreakertcc/page.tsx so the "which sensors are pickable,
 * and how many" rules are unit-testable (see tests/etu-sensor-pool.unit.spec.ts).
 *
 * The shared terminal yields the compatible (breaker frame x trip x sensor) rows from
 * whichever axis the operator narrowed:
 *   - trip-style leaf chosen  -> the trip cascade's sensors[] (the breaker∩trip intersection)
 *   - else a breaker picked    -> the SST bridge sensors for that breaker (breaker grain) or
 *                                 a specific frame (frame grain), via /etu/bridge-sensors
 *
 * Breaker grain (a breaker picked, no frame yet) is the fix for the "8 compatible but
 * empty dropdown" report: the bridge backend already unions every style of the breaker
 * (rating-narrowed per style), so the terminal can list them the moment the breaker is
 * chosen — including alt-trip retrofits (e.g. WavePro -> EntelliGuard TU, migration 017).
 */

import type { CascadeResponse, EtuBridgeSensorsResponse } from './breaker-resources'

export const SENSOR_CAP = 250

export type SensorPoolItem = {
  sensor_id: number
  rating: number | null
  desc: string
  tripMfr: string
  tripType: string
  tripStyle: string
  /** trip_styles.id for this row's trip — keys the alt-trip (retrofit) lookup. */
  tripStyleId: number | null
  /** breaker_style_frame (normalized) when the row came from the breaker axis; else null. */
  frame: string | null
  /** breaker_style_id when known (breaker/frame grain); lets resolution keep the frame. */
  styleId: number | null
  /** De-duplicated trip identity (mfr + type [+ style] [+ "(retrofit · CLASS)"]) — the
   *  nameplate trip label, sans frame prefix and sensor rating. */
  tripLabel: string
  label: string
}

/** A trip that is a retrofit/upgrade for the selected breaker (from the alt-trip bridge),
 *  with its protection-element class (e.g. 'LSIG', 'LIG'). Keyed in altTrips by trip_style_id. */
export type AltTripInfo = { relation: string; protectionClass: string | null }

export type SensorTerminalInput = {
  tStyle: string
  tCascade: CascadeResponse | null
  bStyle: string
  bId: string
  bridge: EtuBridgeSensorsResponse | null
  /** Alt-trip (retrofit/upgrade) lookup for the selected breaker, keyed by trip_style_id. */
  altTrips?: Record<number, AltTripInfo>
}

export type SensorTerminalState = 'idle' | 'ready' | 'narrow' | 'empty'

export type SensorTerminalSummary = {
  state: SensorTerminalState
  /** Sensors pickable now (state 'ready') or reachable after more narrowing (state 'narrow'). */
  count: number
  /** True when the pool hit SENSOR_CAP and the list is truncated. */
  capped: boolean
}

const ratingSuffix = (rating: number | null | undefined) => (rating ? ` (${rating}A)` : '')

/** True when the model/style token adds nothing over the type token (it's empty or a
 *  substring of the type) — e.g. type "Entelliguard TU" + style "Entelliguard". */
function styleEchoesType(type: string, style: string): boolean {
  const t = type.trim().toLowerCase()
  const s = style.trim().toLowerCase()
  return s.length === 0 || (t.length > 0 && t.includes(s))
}

/** The de-duplicated trip identity: mfr + type, keeping the model/style only when it adds
 *  information — dropped when it echoes the type ("Entelliguard TU Entelliguard" ->
 *  "Entelliguard TU") or when an alt-trip tag will carry the variant — plus a
 *  "(retrofit · LSIG)" tag for alternative (retrofit/upgrade) trips. */
function tripIdentity(mfr: string, type: string, style: string, alt: AltTripInfo | undefined): string {
  const dropStyle = alt != null || styleEchoesType(type, style)
  const base = [mfr, type, dropStyle ? '' : style].filter(Boolean).join(' ').trim()
  if (alt != null) {
    const cls = alt.protectionClass ? ` · ${alt.protectionClass}` : ''
    return `${base} (${alt.relation}${cls})`.trim()
  }
  return base
}

/** Has the operator narrowed far enough that the terminal source actually loaded? */
function reachedTerminal(input: SensorTerminalInput): boolean {
  if (input.tStyle && input.tCascade) return true
  if ((input.bStyle || input.bId) && input.bridge) return true
  return false
}

export function buildSensorPool(input: SensorTerminalInput): SensorPoolItem[] {
  const { tStyle, tCascade, bStyle, bId, bridge } = input
  const altTrips = input.altTrips ?? {}

  let src: SensorPoolItem[]
  if (tStyle && tCascade) {
    // Trip-style leaf -> the precise breaker∩trip intersection.
    src = tCascade.sensors.map((s) => {
      const style = s.trip_model_display ?? s.trip_style_name ?? ''
      const tripStyleId = s.trip_style_id ?? null
      const alt = tripStyleId != null ? altTrips[tripStyleId] : undefined
      const tripLabel = tripIdentity(s.manufacturer_name ?? '', s.trip_type_name ?? '', style, alt)
      return {
        sensor_id: s.sensor_id,
        rating: s.sensor_rating,
        desc: s.sensor_desc ?? '',
        tripMfr: s.manufacturer_name ?? '',
        tripType: s.trip_type_name ?? '',
        tripStyle: style,
        tripStyleId,
        frame: null,
        styleId: null,
        tripLabel,
        label: `${tripLabel} — ${s.sensor_desc ?? ''}${ratingSuffix(s.sensor_rating)}`.trim(),
      }
    })
  } else if ((bStyle || bId) && bridge) {
    // Breaker axis -> the SST bridge sensors. With no frame chosen yet (pure breaker
    // grain) the union spans every style, so prefix the frame to keep same-rating rows
    // from different frames distinct.
    const breakerGrain = !bStyle
    src = bridge.sensors.map((s) => {
      const frame = s.breaker_model_display ?? s.breaker_style_frame ?? null
      const tripStyleId = s.trip_style_id ?? null
      const alt = tripStyleId != null ? altTrips[tripStyleId] : undefined
      const tripLabel = tripIdentity(s.tmt_sst_mfr ?? '', s.tmt_sst_type ?? '', s.tmt_sst_style ?? '', alt)
      const prefix = breakerGrain && frame ? `${frame} ` : ''
      return {
        sensor_id: s.sensor_id,
        rating: s.sensor_rating,
        desc: s.sensor_description ?? '',
        tripMfr: s.tmt_sst_mfr ?? '',
        tripType: s.tmt_sst_type ?? '',
        tripStyle: s.tmt_sst_style ?? '',
        tripStyleId,
        frame,
        styleId: s.breaker_style_id ?? null,
        tripLabel,
        label: `${prefix}${tripLabel} — ${s.sensor_description ?? ''}${ratingSuffix(s.sensor_rating)}`.trim(),
      }
    })
  } else {
    src = []
  }

  return src.slice(0, SENSOR_CAP)
}

export function summarizeSensorTerminal(
  input: SensorTerminalInput,
  pool: SensorPoolItem[],
  anySel: boolean,
): SensorTerminalSummary {
  if (pool.length > 0) {
    return { state: 'ready', count: pool.length, capped: pool.length >= SENSOR_CAP }
  }
  if (!anySel) {
    return { state: 'idle', count: 0, capped: false }
  }
  if (reachedTerminal(input)) {
    // A terminal source loaded and returned nothing compatible.
    return { state: 'empty', count: 0, capped: false }
  }
  // Pre-terminal: the cross-filter universe is reachable but the operator must narrow
  // to a breaker, frame, or trip style before the sensors can be listed.
  return { state: 'narrow', count: input.tCascade?.count ?? 0, capped: false }
}
