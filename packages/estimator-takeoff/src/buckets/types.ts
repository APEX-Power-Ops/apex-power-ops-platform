import type { MountingBasis, VoltageBasis } from '../signature/types'
import type { QuantifiedLine } from '../quantify/types'
import type { EvidenceKind } from '../extraction/types'
export type { EvidenceKind }

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
  findings: TakeoffFinding[]
  dispositions: ApparatusDisposition[]   // NEW -- EXACTLY one per artifact.apparatus row
}

export type ApparatusDispositionStatus =
  | 'matched'             // counted into a line that matched a catalog ref
  | 'associated_source'   // folded as a source/occurrence of a counted device (not its own line)
  | 'unmatched'           // counted into a line with no catalog rule
  | 'question'            // breaker-shaped but unresolved - needs an operator answer
  | 'ignored'             // explicit exclusion (non-breaker / not breaker-shaped)

export type DispositionReasonCode =
  | 'catalog_rule'                  // matched
  | 'occurrence_of_counted_device' // associated_source (sibling occurrence, had a signature)
  | 'unresolved_tag_attached'      // associated_source (no signature, tag matched a counted line)
  | 'no_catalog_rule'              // unmatched
  | 'missing_voltage'              // question
  | 'location_only_non_authoritative' // question
  | 'non_breaker_carries_rating'   // question - non-breaker token + breaker rating
  | 'unrecognized_apparatus_row'   // question - a producer candidate row the engine cannot classify
  | 'non_breaker_excluded'         // ignored - the ONLY safe-to-ignore case

export interface ApparatusDisposition {
  inputIndex: number
  tag?: string
  raw: string
  sheet: string
  page: number
  bbox: [number, number, number, number]
  evidence: EvidenceKind
  status: ApparatusDispositionStatus
  reasonCode: DispositionReasonCode
  reason: string
  ref?: string
  lineKey?: string
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
