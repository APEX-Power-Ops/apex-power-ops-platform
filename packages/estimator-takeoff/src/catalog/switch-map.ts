import type { SwitchSignature, SwitchType, VoltageClass } from '../signature/types'
import { SWITCH_GROUPS } from './switch-map.data'

export interface SwitchScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select switch/disconnect voltage class and construction type (fused/open/oil/SF6/cutout/motor-operated/Vista) and confirm the priced ref; switches are priced per device and are never auto-priced.'

// LV is fused-only (both LV refs are "Fused Disconnect"), so a definitively non-fused LV disconnect has no priced
// home. MV/HV are NOT gated here: "Switch MV - Open" / "Switch HV - Open" are plausible non-fused homes.
function isNonFusedLvGap(sig: SwitchSignature): boolean {
  return sig.fused === false && sig.voltageClass === 'LV'
    && (sig.switchType === 'unknown' || sig.switchType === 'fused_disconnect')
}

export function matchSwitch(sig: SwitchSignature): SwitchScopeMatch | null {
  if (isNonFusedLvGap(sig)) return null                         // D1: non-fused LV -> catalog_gap
  const vc: VoltageClass | 'unknown' = sig.voltageClass ?? 'unknown'
  const typeKey: SwitchType | 'any' = sig.switchType === 'unknown' ? 'any' : sig.switchType
  // Primary lookup: specific type:voltage key. When voltage is absent (vc='unknown') and the specific
  // type:unknown key is missing, widen to any:unknown so the caller gets a group to surface to the user.
  // When voltage IS present and the specific key is missing, it is a true structural gap -> return null.
  const directGroup = SWITCH_GROUPS[`${typeKey}:${vc}`]
  const group = directGroup ?? (vc === 'unknown' && typeKey !== 'any' ? SWITCH_GROUPS['any:unknown'] : undefined)
  if (!group || group.length === 0) return null                 // missing OR empty key -> catalog_gap (vacuum, HV fused/cutout/oil/sf6, open:LV)
  // D2 conservative default: ONLY with a voltage class AND a specific type token AND a direct group entry.
  // Falling back to any:unknown means no effective type+voltage specificity -> no default (widen, but do not price).
  const defaultRef = (sig.voltageClass !== undefined && sig.switchType !== 'unknown' && directGroup !== undefined) ? group[0] : undefined
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
