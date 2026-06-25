export type VoltageClass = 'LV' | 'MV' | 'HV'
export type Mounting =
  | 'draw_out' | 'electrically_operated' | 'insulated_case'
  | 'molded_case' | 'panelboard' | 'unknown'
export type MvType = 'air_frame' | 'vacuum' | 'sf6' | 'oil' | 'unknown'
export type TripFunction = 'L' | 'S' | 'I' | 'G'

export interface ApparatusSignature {
  kind: 'breaker'
  voltageClass: VoltageClass
  voltageV?: number
  frameA?: number
  tripA?: number
  functions: TripFunction[]
  mounting: Mounting
  mvType?: MvType
  tag?: string
  source: { sheet: string; page: number; bbox: [number, number, number, number]; evidence: string }
}
