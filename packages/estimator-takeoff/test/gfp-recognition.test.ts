import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { assessApparatus } from '../src/signature/normalize'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })
// The invariant is "no GFP LINE" - check BOTH dispositions AND scope-pending lines (a line can exist
// even if a disposition reason code differs).
const noGfp = (r: ReturnType<typeof runTakeoff>) =>
  r.dispositions.every((d) => d.reasonCode !== 'gfp_scope_pending') &&
  (r.scopePendingLines ?? []).every((s) => s.line.signature.kind !== 'gfp')

describe('operator-pinned GFP recognition invariants', () => {
  // #1 - breaker with GF function stays breaker; NEVER a GFP line
  it('800AF/800AT LSIG (+ ground fault protection text) -> breaker only, no GFP', () => {
    const r = runTakeoff(art([row({ raw: '800AF/800AT LSIG DRAW-OUT GROUND FAULT PROTECTION', tag: 'MSB-1', busVoltageV: 480, candidateKind: 'breaker' })]))
    expect(r.matchedLines.length).toBe(1)
    expect(noGfp(r)).toBe(true)
  })

  // #2 - dedicated standalone GFP -> GFP
  it('GROUND FAULT RELAY / GROUND FAULT PROTECTION SYSTEM + tag -> GFP scope_pending', () => {
    for (const raw of ['GROUND FAULT RELAY', 'GROUND FAULT PROTECTION SYSTEM']) {
      const r = runTakeoff(art([row({ raw, tag: 'G1' })]))
      expect((r.scopePendingLines ?? []).length).toBe(1)
      expect(r.dispositions[0]!.reasonCode).toBe('gfp_scope_pending')
    }
  })

  // #3 - a relay element stays relay; only an explicit standalone GFP device becomes GFP
  it('SEL-751 50G 51G (candidateKind relay) stays relay, not GFP', () => {
    const r = runTakeoff(art([row({ raw: 'SEL-751 50G 51G', tag: 'R-1', candidateKind: 'relay' })]))
    expect(noGfp(r)).toBe(true)
    expect((r.scopePendingLines ?? []).some((s) => s.line.signature.kind === 'relay')).toBe(true)
  })
  it('an UNCLASSIFIED dedicated GROUND FAULT RELAY row -> GFP', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT RELAY 64', tag: 'G2' }))
    expect(a.signature?.kind).toBe('gfp')
  })
  it('candidateKind:relay + dedicated GROUND FAULT RELAY wording -> GFP (deferral excludes relay)', () => {
    const a = assessApparatus(row({ raw: 'GROUND FAULT RELAY', tag: 'G3', candidateKind: 'relay' }))
    expect(a.signature?.kind).toBe('gfp')   // dedicated GFP wording wins over a relay producer signal (Rev 2)
  })

  // #4 - bare ANSI / function text never counts
  it('bare 50G / 64 / function text -> not a GFP device (unrecognized)', () => {
    for (const raw of ['50G', '64', 'PERFORM GROUND FAULT TEST PER 7.14', 'GROUND FAULT PROTECTION']) {
      const a = assessApparatus(row({ raw, tag: undefined }))
      expect(a.signature, `raw=${raw}`).toBeNull()
    }
  })

  // parent exclusion overrides candidateKind - assert the INVARIANT (never GFP), not the downstream family
  it('candidateKind:gfp + 400AF/400AT -> NEVER a GFP line (parent exclusion wins)', () => {
    const r = runTakeoff(art([row({ raw: '400AF/400AT', tag: 'B-9', busVoltageV: 480, candidateKind: 'gfp' })]))
    expect(noGfp(r)).toBe(true)
  })
  it('candidateKind:gfp on an ATS (NON_BREAKER) row -> NEVER a GFP line', () => {
    const r = runTakeoff(art([row({ raw: 'ATS 800A GROUND FAULT PROTECTION', tag: 'ATS-1', candidateKind: 'gfp' })]))
    expect(noGfp(r)).toBe(true)
  })
})

describe('GFP quantify aggregation', () => {
  it('two standalone GFP devices (same block) aggregate to one line qty=2', () => {
    const r = runTakeoff(art([
      row({ raw: 'GROUND FAULT RELAY', tag: 'G1' }),
      row({ raw: 'GROUND FAULT RELAY', tag: 'G2' }),
    ]))
    const sp = (r.scopePendingLines ?? []).filter((s) => s.line.signature.kind === 'gfp')
    expect(sp.length).toBe(1)
    expect(sp[0]!.qty).toBe(2)
  })
})
