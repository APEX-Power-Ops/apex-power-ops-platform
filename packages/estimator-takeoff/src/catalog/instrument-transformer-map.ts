import type { InstrumentTransformerSignature, VoltageClass } from '../signature/types'
import { ITX_GROUPS } from './instrument-transformer-map.data'

export interface ItxScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select instrument-transformer packaging/count (individual vs 3-phase set) and confirm the priced ref; instrument transformers are priced per device or per set and are never auto-priced.'

// RANKED set selection. A "set" packaging prefers a set-variant ref; individual prefers a non-set ref. A KNOWN
// 3-phase set (set_of_3 / three_phase) must pick the EXPLICIT "Set of 3" ref, NOT merely the first set-named ref -
// e.g. ct:MV is ['...Bushing HV/MV', '...Bushing, HV/MV (Set)', '...MV - Set of 3'] and a naive `find(isSetRef)`
// returns the broad bushing "(Set)" at index 1, not the MV "Set of 3" the Gate-2 evidence implies. group[0] is the
// last-resort fallback so a default (when evidence exists) is never empty.
const matchesSetOf3 = (ref: string): boolean => /set\s+of\s+3/i.test(ref)
const matchesAnySet = (ref: string): boolean => /\bset\b/i.test(ref)

export function matchInstrumentTransformer(sig: InstrumentTransformerSignature): ItxScopeMatch | null {
  const vc: VoltageClass | 'unknown' = sig.voltageClass ?? 'unknown'
  const group = ITX_GROUPS[`${sig.itxType}:${vc}`] ?? ITX_GROUPS[`${sig.itxType}:unknown`]
  if (!group || group.length === 0) return null                     // no priced home (missing OR empty group) -> catalog_gap
  // D2: provisional default ONLY with explicit packaging evidence, ranked within the group.
  let defaultRef: string | undefined
  if (sig.packagingEvidence !== 'none') {
    if (sig.packaging === 'set') {
      defaultRef = (sig.packagingEvidence === 'set_of_3' || sig.packagingEvidence === 'three_phase')
        ? (group.find(matchesSetOf3) ?? group.find(matchesAnySet) ?? group[0])   // explicit Set of 3 wins
        : (group.find(matchesAnySet) ?? group[0])                                 // weaker set signal -> any set ref
    } else if (sig.packaging === 'individual') {
      defaultRef = group.find((r) => !matchesAnySet(r)) ?? group[0]               // individual -> a non-set ref
    } else {
      defaultRef = group[0]
    }
  }
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
