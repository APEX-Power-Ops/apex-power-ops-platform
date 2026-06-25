import type { ApparatusSignature } from '../signature/types'

export interface BreakerRule {
  when: (s: ApparatusSignature) => boolean
  ref: string                                    // MUST exist in estimator-core EQUIPMENT_MODELS_SEED
}

const hasG = (s: ApparatusSignature) => s.functions.includes('G')
const hasFns = (s: ApparatusSignature) => s.functions.length > 0   // a real trip descriptor was parsed (no assumed LS/LSI)

// Refs are verbatim from the canonical catalog. LS/LSI power-breaker rules require a parsed descriptor so
// an unknown-function breaker stays unmatched rather than being priced as LS/LSI.
export const BREAKER_MAP: BreakerRule[] = [
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out' && hasG(s),                ref: 'Circuit Breaker LV - Draw-Out (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'draw_out' && hasFns(s),              ref: 'Circuit Breaker LV - Draw-Out (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'electrically_operated' && hasG(s),   ref: 'Circuit Breaker LV - Electrically Operated (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'electrically_operated' && hasFns(s), ref: 'Circuit Breaker LV - Electrically Operated (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'insulated_case' && hasG(s),          ref: 'Circuit Breaker LV - Insulated Case (LSIG)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'insulated_case' && hasFns(s),        ref: 'Circuit Breaker LV - Insulated Case (LS/LSI)' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'panelboard',                         ref: 'Circuit Breaker LV - Panelboard MCB' },
  { when: (s) => s.voltageClass === 'LV' && s.mounting === 'molded_case',                        ref: 'Circuit Breaker LV - Molded Case Thermal/Mag' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'vacuum',                               ref: 'Circuit Breaker MV - Vacuum Bkr' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'air_frame',                            ref: 'Circuit Breaker MV - Air Frame' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'oil',                                  ref: 'Circuit Breaker MV - Oil Insluated' },
  { when: (s) => s.voltageClass === 'MV' && s.mvType === 'sf6',                                  ref: 'Circuit Breaker MV - SF6 (230kV & Under)' },
]
