import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { RelaySignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const relaySig: RelaySignature = {
  kind: 'relay', technology: 'microprocessor', role: 'feeder', voltageBasis: 'none', tag: 'R1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}

describe('relay cross-family guards', () => {
  it('a relay and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: '87T', tag: 'X1', candidateKind: 'relay' }),
      row({ raw: 'X1 800AF/600AT LSIG', tag: 'X1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).length).toBe(1)   // the relay
    expect(r.matchedLines.length).toBe(1)                 // the breaker
  })
  it('matchBreaker is type- AND runtime-defended against a relay signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error relay is not a BreakerSignature - the family-dispatch boundary is type-defended
      forced = matchBreaker(relaySig)
    }).not.toThrow()
    expect(forced).toBeFalsy()                            // even force-passed, no breaker rule matches a relay
  })
  it('matchTransformer is type- AND runtime-defended against a relay signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error relay is not a TransformerSignature
      forced = matchTransformer(relaySig)
    }).not.toThrow()
    expect(forced).toBeNull()                             // coolant undefined -> no group -> null
  })
  it('two relays differing only in technology get separate lines', () => {
    const r = runTakeoff(art([
      row({ raw: 'OVERCURRENT RELAY 50/51', tag: 'R1', candidateKind: 'relay' }),                 // microprocessor-unknown
      row({ raw: 'ELECTROMECHANICAL OVERCURRENT RELAY 50/51', tag: 'R2', candidateKind: 'relay' }), // em
    ]))
    expect((r.scopePendingLines ?? []).length).toBe(2)
  })
})
