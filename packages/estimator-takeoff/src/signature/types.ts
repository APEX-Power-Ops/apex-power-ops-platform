export type VoltageClass = 'LV' | 'MV' | 'HV'
export type Mounting =
  | 'draw_out' | 'electrically_operated' | 'insulated_case'
  | 'molded_case' | 'panelboard' | 'unknown'
export type MvType = 'air_frame' | 'vacuum' | 'sf6' | 'oil' | 'unknown'
export type TripFunction = 'L' | 'S' | 'I' | 'G'

// How the resolved mounting was determined — surfaced so the estimator can see when construction was
// ASSUMED (estimating_baseline) vs read from evidence (hint) or label text. NOTE: trip FUNCTIONS are
// parsed text-only (never inferred); add a parallel `functionBasis` here only if a function-inference
// path is ever introduced.
export type MountingBasis = 'hint' | 'text' | 'estimating_baseline' | 'none'

export type VoltageBasis = 'detected' | 'asserted' | 'none'

export interface ApparatusSignature {
  kind: 'breaker'
  voltageClass: VoltageClass
  voltageV?: number
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting
  mountingBasis: MountingBasis
  mvType?: MvType
  tag?: string
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string; block?: string }
}
