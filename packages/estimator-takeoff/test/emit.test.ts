import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('runTakeoff + emitEnvelope (golden, construction-evidence boundary)', () => {
  const result = runTakeoff(fixture as ExtractionArtifact)

  it('matches the two draw-out-hinted breakers and de-dups ACC-1-09-FB to qty 1', () => {
    expect(result.matchedLines).toHaveLength(2)                          // MSB + ACC (both hinted draw_out)
    const refs = result.matchedLines.map((m) => m.ref)
    expect(refs).toContain('Circuit Breaker LV - Draw-Out (LSIG)')
    expect(refs.every((r) => r === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)
    const acc = result.matchedLines.find((m) => m.line.signature.tag === 'ACC-1-09-FB')!
    expect(acc.qty).toBe(1)                                              // counted once (power-plan row is not authoritative)
    expect(acc.ref).toBe('Circuit Breaker LV - Draw-Out (LSIG)')
  })

  it('fails closed: the 400AF LSI breaker with no construction evidence is unmatched, not guessed', () => {
    expect(result.unmatchedCandidates).toHaveLength(1)
    expect(result.unmatchedCandidates[0]!.line.signature.tag).toBe('HF-P1-110-01-FB')
  })

  it('emits a valid envelope with no error-severity findings and at least one scope', () => {
    const { envelope, findings } = emitEnvelope(result, { projectNumber: 'STACK-PHX02A' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])   // estimator-core asserts no ERROR findings (not zero findings)
    expect(envelope.scopes.length).toBeGreaterThan(0)                    // guards against the empty-envelope false green
  })
})
