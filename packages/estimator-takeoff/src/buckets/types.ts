import type { MountingBasis, VoltageBasis } from '../signature/types'
import type { QuantifiedLine } from '../quantify/types'
import type { EvidenceKind } from '../extraction/types'
export type { EvidenceKind }

export interface MatchedLine { ref: string; qty: number; block: string; mountingBasis: MountingBasis; voltageBasis: VoltageBasis; line: QuantifiedLine }
export interface UnmatchedCandidate { reason: string; line: QuantifiedLine }

export interface ScopePendingLine {
  candidateRefs: string[]
  provisionalDefaultRef?: string
  r1Ratified: boolean
  scopeQuestion: string
  qty: number
  block: string
  line: QuantifiedLine
}

export type OperatorQuestionCode =
  | 'missing_voltage' | 'lv_frame_trip_unparsed' | 'missing_power_functions'
  | 'mounting_hint_conflict' | 'non_breaker_carries_rating' | 'location_only'
  | 'unrecognized_apparatus_row' | 'profile_warning'
  | 'transformer_attrs_unparsed'
  | 'transformer_scope_pending' | 'transformer_catalog_gap'
  | 'transformer_breaker_conflict'
  | 'relay_scope_pending' | 'relay_catalog_gap'

export interface OperatorQuestion { question: string; context: string; code: OperatorQuestionCode; inputIndex?: number }
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  scopePendingLines?: ScopePendingLine[]
  operatorQuestions: OperatorQuestion[]
  findings: TakeoffFinding[]
  dispositions: ApparatusDisposition[]
}

export type ApparatusDispositionStatus =
  | 'matched'
  | 'associated_source'
  | 'unmatched'
  | 'question'
  | 'ignored'
  | 'scope_pending'

export type DispositionReasonCode =
  | 'catalog_rule'
  | 'occurrence_of_counted_device'
  | 'unresolved_tag_attached'
  | 'no_catalog_rule'
  | 'missing_voltage'
  | 'location_only_non_authoritative'
  | 'non_breaker_carries_rating'
  | 'unrecognized_apparatus_row'
  | 'non_breaker_excluded'
  | 'transformer_attrs_unparsed'
  | 'transformer_scope_pending'
  | 'transformer_catalog_gap'
  | 'transformer_breaker_conflict'
  | 'relay_scope_pending' | 'relay_catalog_gap'

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
  candidateRefs?: string[]
  provisionalDefaultRef?: string
  scopeQuestion?: string
}

export type FindingSeverity = 'error' | 'warning'

export type VoltageAssertionCode =
  | 'voltage_assertion_unknown_tag'
  | 'voltage_assertion_duplicate_tag'
  | 'voltage_assertion_conflict'
  | 'voltage_assertion_invalid_voltage'
  | 'voltage_assertion_invalid_shape'

export interface TakeoffFinding {
  code: VoltageAssertionCode | 'transformer_catalog_gap' | 'relay_catalog_gap'
  severity: FindingSeverity
  message: string
  context: string
  detail?: { tag?: string; detectedV?: number; assertedV?: number; actor?: string; source?: string }
}
