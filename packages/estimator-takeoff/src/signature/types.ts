export type VoltageClass = 'LV' | 'MV' | 'HV'
export type Mounting =
  | 'draw_out' | 'electrically_operated' | 'insulated_case'
  | 'molded_case' | 'panelboard' | 'unknown'
export type MvType = 'air_frame' | 'vacuum' | 'sf6' | 'oil' | 'unknown'
export type TripFunction = 'L' | 'S' | 'I' | 'G'

// How the resolved mounting was determined -- surfaced so the estimator can see when construction was
// ASSUMED (estimating_baseline) vs read from evidence (hint) or label text. NOTE: trip FUNCTIONS are
// parsed text-only (never inferred); add a parallel `functionBasis` here only if a function-inference
// path is ever introduced.
export type MountingBasis = 'hint' | 'text' | 'estimating_baseline' | 'none'

export type VoltageBasis = 'detected' | 'asserted' | 'none'

export type Coolant = 'dry' | 'liquid' | 'unknown'

export interface BaseSignature {
  voltageClass?: VoltageClass        // optional at the base; required for breaker/transformer (re-declared), contextual for relay
  voltageV?: number
  voltageBasis: VoltageBasis
  tag?: string
  inputIndex?: number   // artifact-row position; stamped by runTakeoff. Optional: assessCore builds unstamped.
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string; block?: string }
}

export interface BreakerSignature extends BaseSignature {
  kind: 'breaker'
  voltageClass: VoltageClass         // required for breakers (narrows the optional base)
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting          // breaker-only: how the unit is constructed/installed
  mountingBasis: MountingBasis
  mvType?: MvType
}

export interface TransformerSignature extends BaseSignature {
  kind: 'transformer'
  voltageClass: VoltageClass         // required for transformers (narrows the optional base)
  kvaRating?: number
  coolant: Coolant
  padMount?: boolean
  ltc?: boolean
}

export type RelayTechnology = 'electromechanical_solid_state' | 'microprocessor' | 'unknown'
export type RelayRole =
  | 'overcurrent' | 'feeder' | 'motor' | 'bus_differential' | 'differential'
  | 'line' | 'generator' | 'multifunction_meter' | 'electromechanical' | 'unknown'

export interface RelaySignature extends BaseSignature {
  kind: 'relay'
  technology: RelayTechnology
  ansiFunctions?: string[]
  model?: string
  role?: RelayRole
  // voltageClass stays optional (inherited): relay voltage is contextual and never gates.
}

export interface GfpSignature extends BaseSignature {
  kind: 'gfp'
  ansiFunctions?: string[]   // evidence/display only (e.g. 64, 50G); never used to match or to count
  // voltageClass stays optional (inherited): GFP voltage is contextual and never gates.
}

export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature | GfpSignature
