import type { BreakerSignature } from '../signature/types'
import { BREAKER_MAP } from './breaker-map.data'

export function matchBreaker(sig: BreakerSignature): string | null {
  return BREAKER_MAP.find((rule) => rule.when(sig))?.ref ?? null
}
