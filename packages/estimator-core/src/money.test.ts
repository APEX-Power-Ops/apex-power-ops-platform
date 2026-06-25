import { describe, expect, it } from 'vitest'
import {
  allocateByLargestRemainder,
  divRoundHalfUp,
  hoursToMicro,
  microToCents,
  pctToScaled,
} from './money'

describe('money fixed-point primitives', () => {
  it('converts hours to micro-hours exactly', () => {
    expect(hoursToMicro(3.5)).toBe(3_500_000n)
    expect(hoursToMicro(0.5)).toBe(500_000n)
    expect(hoursToMicro(10)).toBe(10_000_000n)
  })

  it('encodes percent fractions as x10^4 ints', () => {
    expect(pctToScaled(0.35)).toBe(3500n)
    expect(pctToScaled(1)).toBe(10_000n)
    expect(pctToScaled(0.6667)).toBe(6667n)
  })

  it('rounds half-up away from zero', () => {
    expect(divRoundHalfUp(5n, 2n)).toBe(3n) // 2.5 -> 3
    expect(divRoundHalfUp(4n, 2n)).toBe(2n)
    expect(divRoundHalfUp(-5n, 2n)).toBe(-3n) // -2.5 -> -3
  })

  it('rounds micro-cents to integer cents', () => {
    expect(microToCents(180_000_750_000n)).toBe(180001) // 180000.75 -> 180001
    expect(microToCents(165_000_000_000n)).toBe(165000)
  })

  it('allocates a block total by largest remainder, summing exactly', () => {
    // weights 54994.5 and 125006.25 (micro-cents), block total 180001
    const parts = allocateByLargestRemainder(180001, [54_994_500_000n, 125_006_250_000n])
    expect(parts).toEqual([54995, 125006])
    expect(parts[0]! + parts[1]!).toBe(180001)
  })

  it('allocation handles zero weights without dividing by zero', () => {
    expect(allocateByLargestRemainder(0, [0n, 0n])).toEqual([0, 0])
  })

  it('rejects negative weights (the documented non-negative contract)', () => {
    // Reproduction: before the guard, allocateByLargestRemainder(10, [-9,1,1,1]) returned
    // [15,-1,-1,-1] (sum 12 != 10) — silently violating "sum EXACTLY to total".
    expect(() => allocateByLargestRemainder(10, [-9n, 1n, 1n, 1n])).toThrow(/non-negative/)
  })
})
