// Trip-axis "Style" dropdown option labels.
//
// Step-2 restructure (task #106): Trip TYPE is the model (e.g. "Entelliguard"),
// Trip STYLE is the protection class — the L/S/I/G element set (LSI, LSIG, LIG…).
// The backend cascade now derives `protection_class` per style and re-keys the
// style dedup on it, so a model with two distinct classes surfaces both.
//
// Pure, JSX-free so it unit-tests via the Playwright runner (no browser env).

export interface TripStyleOption {
  trip_style_id: number
  trip_model_display?: string | null
  trip_style_name?: string | null
  protection_class?: string | null
  sensor_count: number
}

/**
 * Label for a Trip Style option: the protection class with its sensor count
 * (e.g. "LSIG (8)"). Falls back to the model/style name when the backend has
 * not supplied a protection class yet (e.g. during a deploy lag).
 */
export function tripStyleOptionLabel(style: TripStyleOption): string {
  const cls = (style.protection_class ?? '').trim()
  const base =
    cls ||
    (style.trip_model_display ?? '').trim() ||
    (style.trip_style_name ?? '').trim() ||
    '—'
  return `${base} (${style.sensor_count})`
}
