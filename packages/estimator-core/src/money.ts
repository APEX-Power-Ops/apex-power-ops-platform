/**
 * Fixed-point money/quantity math. No floats in any monetary calculation.
 *
 * Scales:
 *  - MICRO  (1e6): cents scaled to micro-cents, and hours scaled to micro-hours.
 *  - SCALE4 (1e4): multipliers / percentages / markup (matches content_hash encoding).
 * Rates are integer cents-per-hour.
 */
export const MICRO = 1_000_000n
export const SCALE4 = 10_000n

/** Hours (a JS number with few decimals) -> exact micro-hours BigInt. */
export function hoursToMicro(hours: number): bigint {
  return BigInt(Math.round(hours * 1_000_000))
}

/** Decimal fraction (0.35 == 35%) -> x10^4 scaled integer. */
export function pctToScaled(pct: number): bigint {
  return BigInt(Math.round(pct * 10_000))
}

/** Integer division rounding half-up away from zero. denominator must be > 0. */
export function divRoundHalfUp(numerator: bigint, denominator: bigint): bigint {
  if (denominator <= 0n) throw new Error('divRoundHalfUp: denominator must be positive')
  if (numerator >= 0n) {
    return (numerator + denominator / 2n) / denominator
  }
  return -((-numerator + denominator / 2n) / denominator)
}

/** Micro-cents BigInt -> integer cents, half-up. */
export function microToCents(micro: bigint): number {
  return Number(divRoundHalfUp(micro, MICRO))
}

/**
 * Distribute an integer `total` across lines weighted by `weights` (any non-negative
 * BigInt scale), returning integer parts that sum EXACTLY to `total`. Remainder units
 * go to the largest fractional remainders; ties break by ascending index.
 */
export function allocateByLargestRemainder(total: number, weights: bigint[]): number[] {
  const n = weights.length
  if (n === 0) return []
  for (let i = 0; i < n; i++) {
    if (weights[i]! < 0n) {
      throw new Error('allocateByLargestRemainder: weights must be non-negative')
    }
  }
  const sum = weights.reduce((a, w) => a + w, 0n)
  if (sum === 0n) return weights.map(() => 0)

  const totalB = BigInt(total)
  const floors: bigint[] = []
  const remainders: { idx: number; rem: bigint }[] = []
  let allocated = 0n
  for (let i = 0; i < n; i++) {
    const exact = totalB * weights[i]! // scaled by sum
    const floor = exact / sum
    const rem = exact - floor * sum
    floors.push(floor)
    remainders.push({ idx: i, rem })
    allocated += floor
  }
  let leftover = totalB - allocated
  remainders.sort((a, b) => (b.rem === a.rem ? a.idx - b.idx : b.rem > a.rem ? 1 : -1))
  for (let k = 0; leftover > 0n && k < remainders.length; k++) {
    floors[remainders[k]!.idx]! += 1n
    leftover -= 1n
  }
  return floors.map((f) => Number(f))
}
