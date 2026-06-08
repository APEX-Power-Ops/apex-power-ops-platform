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
  /** breaker_style_frame (normalized) when the row came from the breaker axis; else null. */
  frame: string | null
  /** breaker_style_id when known (breaker/frame grain); lets resolution keep the frame. */
  styleId: number | null
  label: string
}

export type SensorTerminalInput = {
  tStyle: string
  tCascade: CascadeResponse | null
  bStyle: string
  bId: string
  bridge: EtuBridgeSensorsResponse | null
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

function tripLabel(mfr: string, type: string, style: string, desc: string, rating: number | null): string {
  return `${mfr} ${type} ${style} — ${desc}${ratingSuffix(rating)}`.trim()
}

/** Has the operator narrowed far enough that the terminal source actually loaded? */
function reachedTerminal(input: SensorTerminalInput): boolean {
  if (input.tStyle && input.tCascade) return true
  if ((input.bStyle || input.bId) && input.bridge) return true
  return false
}

export function buildSensorPool(input: SensorTerminalInput): SensorPoolItem[] {
  const { tStyle, tCascade, bStyle, bId, bridge } = input

  let src: SensorPoolItem[]
  if (tStyle && tCascade) {
    // Trip-style leaf -> the precise breaker∩trip intersection.
    src = tCascade.sensors.map((s) => {
      const style = s.trip_model_display ?? s.trip_style_name ?? ''
      return {
        sensor_id: s.sensor_id,
        rating: s.sensor_rating,
        desc: s.sensor_desc ?? '',
        tripMfr: s.manufacturer_name ?? '',
        tripType: s.trip_type_name ?? '',
        tripStyle: style,
        frame: null,
        styleId: null,
        label: tripLabel(s.manufacturer_name ?? '', s.trip_type_name ?? '', style, s.sensor_desc ?? '', s.sensor_rating),
      }
    })
  } else if ((bStyle || bId) && bridge) {
    // Breaker axis -> the SST bridge sensors. With no frame chosen yet (pure breaker
    // grain) the union spans every style, so prefix the frame to keep same-rating rows
    // from different frames distinct.
    const breakerGrain = !bStyle
    src = bridge.sensors.map((s) => {
      const frame = s.breaker_model_display ?? s.breaker_style_frame ?? null
      const base = tripLabel(
        s.tmt_sst_mfr ?? '',
        s.tmt_sst_type ?? '',
        s.tmt_sst_style ?? '',
        s.sensor_description ?? '',
        s.sensor_rating,
      )
      return {
        sensor_id: s.sensor_id,
        rating: s.sensor_rating,
        desc: s.sensor_description ?? '',
        tripMfr: s.tmt_sst_mfr ?? '',
        tripType: s.tmt_sst_type ?? '',
        tripStyle: s.tmt_sst_style ?? '',
        frame,
        styleId: s.breaker_style_id ?? null,
        label: breakerGrain && frame ? `${frame} ${base}`.trim() : base,
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
