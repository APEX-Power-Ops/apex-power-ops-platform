import type { ApparatusSignature } from '../signature/types'
export interface QuantifiedLine {
  signature: ApparatusSignature                 // representative (richest authoritative occurrence); widened from BreakerSignature in Task 3
  qty: number                                   // distinct devices counted
  sources: ApparatusSignature['source'][]       // every contributing occurrence (incl. power-plan locations)
  memberTags: string[]                          // every device tag aggregated into this line (for location association)
  memberIndices: number[]   // inputIndex of every device aggregated into this line
  lineKey: string           // stable spec key for this line (used by dispositions/associations)
  countedFromAuthoritative: true
}
