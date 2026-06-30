import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const golden: ExtractionArtifact = {
  pdf: 'test.pdf',
  apparatus: [
    { raw: 'Fused Disconnect 400A', tag: 'DS-1', sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 15000 },
    { raw: 'Air Switch', tag: 'DS-2', sheet: 'E-1', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line', busVoltageV: 15000 },
    { raw: 'NF Disconnect', tag: 'DS-3', sheet: 'E-1', page: 1, bbox: [2, 0, 3, 1], evidence: 'one-line', busVoltageV: 480 },
    { raw: '800AF/800AT LSIG', tag: 'CB-1', sheet: 'E-1', page: 1, bbox: [3, 0, 4, 1], evidence: 'one-line', busVoltageV: 480 },
    { raw: 'Switchgear - Medium Voltage', tag: 'SWGR-1', sheet: 'E-1', page: 1, bbox: [4, 0, 5, 1], evidence: 'one-line', busVoltageV: 15000 },
  ],
}

describe('switch golden - coexistence', () => {
  it('routes each device to the right family', () => {
    const res = runTakeoff(golden)
    // DS-1 MV fused disconnect + DS-2 air switch (open) -> scope_pending
    const sp = res.scopePendingLines ?? []
    expect(sp.some((s) => s.switchType === 'fused_disconnect' && s.provisionalDefaultRef === 'Switch MV - Fused Disconnect')).toBe(true)
    expect(sp.some((s) => s.switchType === 'open' && s.provisionalDefaultRef === 'Switch MV - Open')).toBe(true)
    // DS-3 NF LV disconnect -> catalog gap
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)
    // CB-1 real breaker -> priced
    expect(res.matchedLines.length).toBe(1)
    // SWGR-1 switchgear assembly -> NOT a switch (no scope_pending, no switch line for it)
    expect(sp.every((s) => s.line.signature.tag !== 'SWGR-1')).toBe(true)
  })
})
