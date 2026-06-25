import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('runTakeoff + emitEnvelope (golden)', () => {
  const result = runTakeoff(fixture as ExtractionArtifact)

  it('matches two draw-out breakers; de-dups ACC across one-line + power-plan keeping BOTH sources, no spurious question', () => {
    expect(result.matchedLines).toHaveLength(2)
    const refs = result.matchedLines.map((m) => m.ref)
    expect(refs.every((r) => r === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)
    const acc = result.matchedLines.find((m) => m.line.signature.tag === 'ACC-1-09-FB')!
    expect(acc.qty).toBe(1)
    expect(acc.mountingBasis).toBe('hint')
    expect(acc.line.sources.map((s) => s.sheet).sort()).toEqual(['E01-11', 'E02-03D'])
    expect(result.operatorQuestions).toEqual([])     // the breaker-shaped power-plan row attached by tag, not questioned
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

  it('does not fabricate a breaker line from a non-breaker carrying a frame/trip (MTS)', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'MTS-2 800AF/800AT LSIG', tag: 'MTS-2', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'P1-110' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(0)
    expect(r.operatorQuestions.length).toBeGreaterThan(0)
  })

  it('creates one scope per electrical block for same-spec devices in different blocks', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'M1-GB 4000AF/4000AT LSIG', tag: 'M1-GB', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'P1-110', mountingHint: 'draw_out' },
      { raw: 'M2-GB 4000AF/4000AT LSIG', tag: 'M2-GB', sheet: 'E01-11', page: 1, bbox: [2, 2, 3, 3], evidence: 'one-line', busVoltageV: 480, block: 'P2-110', mountingHint: 'draw_out' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(2)
    const { envelope } = emitEnvelope(r, { projectNumber: 'X' })
    expect(envelope.scopes.map((s) => s.name).sort()).toEqual(['Block P1-110', 'Block P2-110'])
  })
})

describe('LV frameA eligibility (the MCB pricing leak)', () => {
  it('an unrated MCB candidate (candidateKind, 480V, no AF/AT) is never priced — surfaced instead', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'LP-1-MCB', tag: 'LP-1-MCB', sheet: 'E01-50', page: 20, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'HOUSE_NON_CRITICAL', candidateKind: 'breaker' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(0)                  // never priced
    expect(r.unmatchedCandidates.length + r.operatorQuestions.length).toBeGreaterThan(0)  // surfaced
  })
  it('a real rated MCB (400AF/400AT, 480V) is matched', () => {
    const art: ExtractionArtifact = { pdf: 'x', apparatus: [
      { raw: 'LP-2-MCB 400AF/400AT', tag: 'LP-2-MCB', sheet: 'E01-50', page: 20, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'HOUSE_NON_CRITICAL' },
    ] }
    const r = runTakeoff(art)
    expect(r.matchedLines).toHaveLength(1)
    expect(r.matchedLines[0]!.ref).toBe('Circuit Breaker LV - Panelboard MCB')
  })
})

describe('profileWarnings propagation', () => {
  it('surfaces artifact.profileWarnings as operator questions', () => {
    const art: ExtractionArtifact = { pdf: 'x', profileWarnings: ['legend E00-01 unparsed — default profile assumed'], apparatus: [] }
    const r = runTakeoff(art)
    expect(r.operatorQuestions.some((q) => /default profile assumed/.test(q.question) && q.context === 'legend/profile')).toBe(true)
  })
})
