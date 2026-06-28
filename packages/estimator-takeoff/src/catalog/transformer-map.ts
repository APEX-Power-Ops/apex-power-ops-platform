import type { TransformerSignature } from '../signature/types'
import { DRY_GROUP, OIL_GROUP, DRY_DEFAULT_REF, OIL_DEFAULT_REF } from './transformer-map.data'

export interface ScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }

export function matchTransformer(sig: TransformerSignature): ScopeMatch | null {
  const ltc = sig.ltc
    ? ' NOTE: LTC present - LTC test scope (Tap Changer / Power-w/-LTC) deferred to V2; covers the base unit only.'
    : ''
  if (sig.coolant === 'dry')
    return {
      group: [...DRY_GROUP],
      defaultRef: DRY_DEFAULT_REF,
      scopeQuestion: 'Select dry-type test scope tier (TTR/IR vs TTR/WR/IR vs TTR/IR/WR/PF).' + ltc,
    }
  if (sig.coolant === 'liquid')
    return {
      group: [...OIL_GROUP],
      defaultRef: OIL_DEFAULT_REF,
      scopeQuestion: 'Select pad-mount-oil test scope tier (TTR/WR/IR vs +PF/Oil).' + ltc,
    }
  return null // unknown coolant / out-of-V1 sub-type -> catalog_gap (surfaced, never fabricated)
}
