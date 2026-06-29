import type { RelaySignature } from '../signature/types'
import { RELAY_TIERS, ROLE_TO_TIER, ORPHAN_ANSI } from './relay-map.data'

export interface RelayScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }

const SCOPE_Q =
  'Select relay test-scope tier (application/function): which of the priced relay tiers applies to this device?'

export function matchRelay(sig: RelaySignature): RelayScopeMatch | null {
  // Orphan device types (86/79/25/27/59/81 standalone-dominant) have no priced tier home -> catalog_gap.
  if (sig.ansiFunctions && sig.ansiFunctions.length === 1 && ORPHAN_ANSI.has(sig.ansiFunctions[0]!)) return null
  const role = sig.role ?? 'unknown'
  const defaultRef = role !== 'unknown' ? ROLE_TO_TIER[role] : undefined
  // Always offer the full tier group; provisional default only where the role is legible.
  return { group: [...RELAY_TIERS], defaultRef, scopeQuestion: SCOPE_Q }
}
