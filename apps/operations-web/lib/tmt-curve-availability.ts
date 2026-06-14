// Honest-withhold gate for the TMT (thermal-magnetic) trip-curve view.
//
// `available_trip_classes` is derived from `tcc.tmt_curves`, so an empty list means the
// frame has NO thermal-magnetic curve on file. The E2E audit (F06) established that the
// curveless TMT-MCCB frames are magnetic-only motor protectors (MA/MF), molded-case
// switches, and electronic-trip devices — none of which have a thermal-magnetic curve by
// design. Rendering a blank plot for these reads as broken; the field-trust rule is to
// withhold honestly and point the tech to the instantaneous (magnetic) test values.

export interface TmtCurveAvailability {
  hasCurve: boolean
  note: string | null
}

const NO_CURVE_NOTE =
  'No thermal-magnetic trip curve on file for this frame. This is expected for magnetic-only ' +
  '(instantaneous), switch/disconnector, and electronic-trip devices — their characteristic is ' +
  'not a thermal-magnetic curve. Use the Protection Settings test plan for the instantaneous ' +
  '(magnetic) pickup values.'

export function tmtCurveAvailability(
  availableTripClasses: number[] | null | undefined,
): TmtCurveAvailability {
  const hasCurve = Array.isArray(availableTripClasses) && availableTripClasses.length > 0
  return hasCurve ? { hasCurve: true, note: null } : { hasCurve: false, note: NO_CURVE_NOTE }
}
