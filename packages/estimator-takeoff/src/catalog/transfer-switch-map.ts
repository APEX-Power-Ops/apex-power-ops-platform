import type { TransferSwitchSignature } from '../signature/types'
import { TRANSFER_GROUPS } from './transfer-switch-map.data'

export interface TransferScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }
const SCOPE_Q =
  'Confirm the transfer-switch ref (automatic vs manual; base vs iso-bypass; IR/DLRO scope) at Gate-2.'

export function matchTransferSwitch(sig: TransferSwitchSignature): TransferScopeMatch | null {
  if (sig.automationClass === 'static') return null                                   // D5 gap (FIRST)
  if (sig.automationClass === 'manual' && sig.bypassIsolation === true) return null    // D6 gap
  const key = sig.automationClass === 'unknown' ? 'unknown' : sig.automationClass
  const group = TRANSFER_GROUPS[key as 'automatic' | 'manual' | 'unknown']
  if (!group || group.length === 0) return null
  let defaultRef: string | undefined
  if (sig.automationClass === 'automatic') {
    defaultRef = sig.bypassIsolation === true
      ? 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)'
      : 'Automatic Transfer Switch - (IR/DLRO)'
  } else if (sig.automationClass === 'manual') {
    defaultRef = 'Manual Transfer Switch - (IR/DLRO)'
  } // 'unknown' -> no default (D2)
  return { group: [...group], defaultRef, scopeQuestion: SCOPE_Q }
}
