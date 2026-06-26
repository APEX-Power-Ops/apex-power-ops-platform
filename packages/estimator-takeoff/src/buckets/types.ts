import type { MountingBasis, VoltageBasis } from '../signature/types'
import type { QuantifiedLine } from '../quantify/types'

export interface MatchedLine { ref: string; qty: number; block: string; mountingBasis: MountingBasis; voltageBasis: VoltageBasis; line: QuantifiedLine }
export interface UnmatchedCandidate { reason: string; line: QuantifiedLine }

export type OperatorQuestionCode =
  | 'missing_voltage' | 'lv_frame_trip_unparsed' | 'missing_power_functions'
  | 'mounting_hint_conflict' | 'non_breaker_carries_rating' | 'location_only'
  | 'unrecognized_apparatus_row' | 'profile_warning'

export interface OperatorQuestion { question: string; context: string; code: OperatorQuestionCode; inputIndex?: number }
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]
  findings: TakeoffFinding[]   // NEW — coded, severity-tagged assertion findings
}

export type FindingSeverity = 'error' | 'warning'

export type VoltageAssertionCode =
  | 'voltage_assertion_unknown_tag'
  | 'voltage_assertion_duplicate_tag'
  | 'voltage_assertion_conflict'
  | 'voltage_assertion_invalid_voltage'
  | 'voltage_assertion_invalid_shape'

export interface TakeoffFinding {
  code: VoltageAssertionCode
  severity: FindingSeverity
  message: string
  context: string
  detail?: { tag?: string; detectedV?: number; assertedV?: number; actor?: string; source?: string }
}
