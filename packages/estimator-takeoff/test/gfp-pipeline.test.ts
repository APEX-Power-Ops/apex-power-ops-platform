import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { GFP_REF } from '../src/catalog/gfp-map.data'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1] as [number, number, number, number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('GFP end-to-end through runTakeoff', () => {
  it('standalone GFP -> scope_pending(single ref) with the ref as provisional default', () => {
    const r = runTakeoff(art([row({ raw: 'GROUND FAULT PROTECTION SYSTEM', tag: 'GFP-1' })]))
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines ?? []).toHaveLength(1)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs).toEqual([GFP_REF])
    expect(sp.provisionalDefaultRef).toBe(GFP_REF)
    expect(sp.r1Ratified).toBe(false)
    expect(r.dispositions[0]!.reasonCode).toBe('gfp_scope_pending')
  })
})
