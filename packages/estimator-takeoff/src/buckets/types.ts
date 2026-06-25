import type { MountingBasis } from '../signature/types'
import type { QuantifiedLine } from '../quantify/types'

export interface MatchedLine { ref: string; qty: number; block: string; mountingBasis: MountingBasis; line: QuantifiedLine }
export interface UnmatchedCandidate { reason: string; line: QuantifiedLine }
export interface OperatorQuestion { question: string; context: string }
export interface TakeoffResult {
  matchedLines: MatchedLine[]
  unmatchedCandidates: UnmatchedCandidate[]
  operatorQuestions: OperatorQuestion[]
}
