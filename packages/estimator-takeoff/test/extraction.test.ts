import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('extraction contract', () => {
  it('the STACK fixture conforms to ExtractionArtifact', () => {
    const a = fixture as ExtractionArtifact
    expect(a.apparatus.length).toBeGreaterThan(0)
    const first = a.apparatus[0]!
    expect(typeof first.raw).toBe('string')
    expect(typeof first.sheet).toBe('string')
    expect(first.bbox).toHaveLength(4)
    expect(['one-line', 'panel-schedule', 'switchgear-schedule', 'power-plan']).toContain(first.evidence)
  })
  it('the contract carries optional profileWarnings (string[]) and candidateKind (breaker)', () => {
    const a: ExtractionArtifact = { pdf: 'x', profileWarnings: ['w'], apparatus: [
      { raw: 'X-UB', tag: 'X-UB', sheet: 'E01-30', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', candidateKind: 'breaker' },
    ] }
    expect(Array.isArray(a.profileWarnings)).toBe(true)
    expect(a.apparatus[0]!.candidateKind).toBe('breaker')
  })
})
