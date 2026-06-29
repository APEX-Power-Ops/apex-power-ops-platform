import type { RelaySignature } from '../signature/types'
import { RELAY_TIERS, ROLE_TO_TIER, ORPHAN_ANSI } from './relay-map.data'

export interface RelayScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select relay test-scope tier (application/function): which of the priced relay tiers applies to this device?'

export function matchRelay(sig: RelaySignature): RelayScopeMatch | null {
  const role = sig.role ?? 'unknown'
  // Orphan device types (86/79/25/27/59/81) have no priced tier home -> catalog_gap.
  // All-orphan ANSI wins over a text-derived role: a "FEEDER LOCKOUT RELAY 86" is an orphan lockout,
  // not a priced feeder tier. (No ANSI functions -> fall through to the role/no-default path.)
  if (sig.ansiFunctions && sig.ansiFunctions.length > 0 && sig.ansiFunctions.every((f) => ORPHAN_ANSI.has(f))) return null
  const defaultRef = role !== 'unknown' ? ROLE_TO_TIER[role] : undefined
  return { group: [...RELAY_TIERS], defaultRef, scopeQuestion: SCOPE_Q }
}
