import type { ApparatusSignature } from '../signature/types'
export interface QuantifiedLine {
  signature: ApparatusSignature                 // representative signature (authoritative occurrence)
  qty: number                                   // distinct devices counted
  sources: ApparatusSignature['source'][]       // every contributing occurrence (incl. power-plan locations)
  countedFromAuthoritative: true
}
