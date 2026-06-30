import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0,0,1,1] as [number,number,number,number], evidence: 'one-line' as const, ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

describe('instrument-transformer end-to-end', () => {
  it('CT set of 3 MV -> scope_pending with a provisional default + carried evidence', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER MV SET OF 3', tag: 'CT-1', busVoltageV: 4160 })]))
    expect(r.matchedLines).toHaveLength(0)
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.candidateRefs.length).toBeGreaterThan(1)
    expect(sp.provisionalDefaultRef).toBe('Current Transformer MV - Set of 3')
    expect(sp.packagingEvidence).toBe('set_of_3')
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_scope_pending')
    expect(r.dispositions[0]!.packagingEvidence).toBe('set_of_3')
  })
  it('CT MV with NO packaging evidence -> scope_pending, no default', () => {
    const r = runTakeoff(art([row({ raw: 'CURRENT TRANSFORMER', tag: 'CT-2', busVoltageV: 4160 })]))
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.provisionalDefaultRef).toBeUndefined()
  })
  it('LV PT (480V) has no priced home -> catalog_gap disposition, NO scope_pending (bounded V1 gap)', () => {
    const r = runTakeoff(art([row({ raw: 'POTENTIAL TRANSFORMER', tag: 'PT-9', busVoltageV: 480 })]))
    expect((r.scopePendingLines ?? []).length).toBe(0)
    expect(r.dispositions[0]!.reasonCode).toBe('instrument_transformer_catalog_gap')
  })
  it('CCVT Individual (480V) -> scope_pending with the individual provisional default (P2-b)', () => {
    const r = runTakeoff(art([row({ raw: 'CCVT VOLTAGE TRANSFORMER - INDIVIDUAL', tag: 'CCVT-1', busVoltageV: 480 })]))
    const sp = (r.scopePendingLines ?? [])[0]!
    expect(sp.provisionalDefaultRef).toBe('CCVT Voltage Transformer - Individual')
    expect(sp.packagingEvidence).toBe('individual_token')
  })
})
