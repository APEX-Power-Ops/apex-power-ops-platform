import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { InstrumentTransformerSignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const itxSig: InstrumentTransformerSignature = {
  kind: 'instrument_transformer', itxType: 'ct', packaging: 'unknown', packagingEvidence: 'none', voltageBasis: 'none', tag: 'CT-1',
  source: { sheet: 'E01', page: 1, bbox: [0,0,1,1], evidence: 'one-line' },
}

describe('instrument-transformer cross-family guards', () => {
  it('an instrument transformer and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: 'CURRENT TRANSFORMER 600:5', tag: 'CT-1' }),
      row({ raw: 'MSB-1 800AF/600AT LSIG', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'instrument_transformer').length).toBe(1)
    expect(r.matchedLines.length).toBe(1)
  })
  it('matchBreaker is type- AND runtime-defended against an instrument-transformer signature', () => {
    let forced: unknown
    // @ts-expect-error itx is not a BreakerSignature
    expect(() => { forced = matchBreaker(itxSig) }).not.toThrow()
    expect(forced).toBeFalsy()
  })
  it('matchTransformer is type- AND runtime-defended against an instrument-transformer signature', () => {
    let forced: unknown
    // @ts-expect-error itx is not a TransformerSignature
    expect(() => { forced = matchTransformer(itxSig) }).not.toThrow()
    expect(forced).toBeNull()
  })
})
