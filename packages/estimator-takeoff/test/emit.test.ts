import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('runTakeoff + emitEnvelope (golden)', () => {
  const result = runTakeoff(fixture as ExtractionArtifact)

  it('matches the two draw-out breakers; de-dups ACC across one-line + power-plan keeping BOTH sources', () => {
    expect(result.matchedLines).toHaveLength(2)
    const refs = result.matchedLines.map((m) => m.ref)
    expect(refs.every((r) => r === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)
    const acc = result.matchedLines.find((m) => m.line.signature.tag === 'ACC-1-09-FB')!
    expect(acc.qty).toBe(1)
    expect(acc.mountingBasis).toBe('hint')
    const sheets = acc.line.sources.map((s) => s.sheet).sort()
    expect(sheets).toEqual(['E01-11', 'E02-03D'])     // one-line + power-plan location both retained
  })

  it('groups scopes by electrical BLOCK (P1-110), not by sheet', () => {
    expect(result.matchedLines.every((m) => m.block === 'P1-110')).toBe(true)
    const { envelope } = emitEnvelope(result, { projectNumber: 'STACK-PHX02A' })
    expect(envelope.scopes.map((s) => s.name)).toContain('Block P1-110')
  })

  it('fails closed: the 400AF LSI breaker with no evidence is unmatched, not guessed', () => {
    expect(result.unmatchedCandidates).toHaveLength(1)
    expect(result.unmatchedCandidates[0]!.line.signature.tag).toBe('HF-P1-110-01-FB')
  })

  it('emits a valid envelope with no error-severity findings and at least one scope', () => {
    const { envelope, findings } = emitEnvelope(result, { projectNumber: 'STACK-PHX02A' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(envelope.scopes.length).toBeGreaterThan(0)
  })

  it('emitEnvelope fails closed (throws) when there are zero matched lines', () => {
    expect(() => emitEnvelope({ matchedLines: [], unmatchedCandidates: [], operatorQuestions: [] }, { projectNumber: 'X' }))
      .toThrow(/zero matched lines/)
  })
})
