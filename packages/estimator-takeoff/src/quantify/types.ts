import type { ApparatusSignature } from '../signature/types'
export interface QuantifiedLine {
  signature: ApparatusSignature                 // representative (richest authoritative occurrence)
  qty: number                                   // distinct devices counted
  sources: ApparatusSignature['source'][]       // every contributing occurrence (incl. power-plan locations)
  memberTags: string[]                          // every device tag aggregated into this line (for location association)
  countedFromAuthoritative: true
}
