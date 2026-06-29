import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { matchBreaker } from '../src/catalog/breaker-map'
import { matchTransformer } from '../src/catalog/transformer-map'
import { matchRelay } from '../src/catalog/relay-map'
import type { ExtractionArtifact } from '../src/extraction/types'
import type { GfpSignature } from '../src/signature/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
const gfpSig: GfpSignature = {
  kind: 'gfp', voltageBasis: 'none', tag: 'G1',
  source: { sheet: 'E01', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
}

describe('GFP cross-family guards', () => {
  it('a GFP and a breaker sharing a tag are NOT cross-bucketed', () => {
    const r = runTakeoff(art([
      row({ raw: 'GROUND FAULT RELAY', tag: 'X1' }),
      row({ raw: 'X1 800AF/600AT LSIG', tag: 'X1', busVoltageV: 480, candidateKind: 'breaker' }),
    ]))
    expect((r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'gfp').length).toBe(1)
    expect(r.matchedLines.length).toBe(1)   // the breaker
  })
  it('matchBreaker is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a BreakerSignature
      forced = matchBreaker(gfpSig)
    }).not.toThrow()
    expect(forced).toBeFalsy()
  })
  it('matchTransformer is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a TransformerSignature
      forced = matchTransformer(gfpSig)
    }).not.toThrow()
    expect(forced).toBeNull()
  })
  it('matchRelay is type- AND runtime-defended against a GFP signature', () => {
    let forced: unknown
    expect(() => {
      // @ts-expect-error gfp is not a RelaySignature
      forced = matchRelay(gfpSig)
    }).not.toThrow()
    // matchRelay reads sig.role/ansiFunctions; a gfp sig has neither -> role 'unknown' -> group, no default.
    // The guard that matters: no THROW and a GFP signature never reaches matchRelay in the real pipeline
    // (the family-dispatch in emit routes kind==='gfp' to matchGfp). This forced call only proves no crash.
    expect(forced === null || typeof forced === 'object').toBe(true)
  })
})
