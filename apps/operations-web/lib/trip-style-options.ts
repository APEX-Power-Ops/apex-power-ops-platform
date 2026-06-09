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

/** A trip-style row carries the trip TYPE it belongs to (its model). */
export interface TripStyleTypeRef {
  trip_type_id: number
  trip_type_ids?: number[] | null
}

/**
 * Scope the Trip Style options to the selected Trip Type.
 *
 * The bridge-cross-filtered cascade returns trip styles for EVERY trip type
 * bridged to the chosen breaker (e.g. for a GE WavePro: the EntelliGuard TU
 * retrofit AND the native MVT-PM). The Trip Style axis (Type=model, Style=class)
 * must show only the classes of the SELECTED type — otherwise a foreign-type
 * style surfaces as a duplicate class (a native "MVT-PM LSIG" sitting next to the
 * EntelliGuard "LSIG"), and picking it yields an empty type ∩ style intersection
 * ("No compatible sensors"). Matching is via the representative trip_type_id OR
 * the merged trip_type_ids set (§195 dedup can give a style a representative id
 * that differs from the selected one while still belonging to the type).
 *
 * `selectedTypeIds` empty/nullish → no Trip Type chosen → return the list intact.
 */
export function tripStylesForType<T extends TripStyleTypeRef>(
  styles: T[],
  selectedTypeIds: number[] | null | undefined,
): T[] {
  if (!selectedTypeIds || selectedTypeIds.length === 0) return styles
  const want = new Set(selectedTypeIds)
  return styles.filter(
    (s) => want.has(s.trip_type_id) || (s.trip_type_ids ?? []).some((id) => want.has(id)),
  )
}
