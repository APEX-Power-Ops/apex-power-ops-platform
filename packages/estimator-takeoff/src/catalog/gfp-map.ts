import type { GfpSignature } from '../signature/types'
import { GFP_REF } from './gfp-map.data'

export interface GfpScopeMatch { group: string[]; defaultRef: string; scopeQuestion: string }

const SCOPE_Q =
  'Confirm this standalone ground-fault protection device/system is in test scope (NETA 7.14); it is priced per device, separate from any breaker/ATS ground-fault trip function (which is carried by the parent ref).'

// Single ref: a recognized standalone GFP device always maps to the one priced ref (no tier choice,
// no V1 catalog_gap). The single ref is BOTH the only candidate and the provisional default (a one-click
// Gate-2 confirm). _sig is unused in V1 - the match does not depend on device attributes.
export function matchGfp(_sig: GfpSignature): GfpScopeMatch {
  return { group: [GFP_REF], defaultRef: GFP_REF, scopeQuestion: SCOPE_Q }
}
