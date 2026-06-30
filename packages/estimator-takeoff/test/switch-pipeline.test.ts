import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { reconcile, renderReportText } from '../src/runner/report'
import type { ExtractionArtifact } from '../src/extraction/types'

const art = (rows: { raw: string; tag: string; busVoltageV?: number }[]): ExtractionArtifact => ({
  pdf: 'test.pdf',
  apparatus: rows.map((r) => ({ raw: r.raw, tag: r.tag, sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: r.busVoltageV })),
})

describe('switch pipeline', () => {
  it('an MV fused disconnect -> scope_pending with the MV ref + default, carried into the report', () => {
    const a = art([{ raw: 'Fused Disconnect', tag: 'DS-1', busVoltageV: 15000 }])
    const res = runTakeoff(a)
    expect(res.scopePendingLines?.length).toBe(1)
    const sp = res.scopePendingLines![0]!
    expect(sp.candidateRefs).toContain('Switch MV - Fused Disconnect')
    expect(sp.provisionalDefaultRef).toBe('Switch MV - Fused Disconnect')
    expect(sp.switchType).toBe('fused_disconnect')
    const report = reconcile(a, res)
    expect(report.scopePending[0]!.switchType).toBe('fused_disconnect')
    expect(renderReportText(report)).toContain('type=fused_disconnect')
    // CORE CONTRACT (switches never auto-price): a recognized switch leaves the envelope a partial preview with
    // an unresolved row - it is NEVER a clean priced line. (Operator spec-review round-2 assertion.)
    expect(report.status).toBe('partial_preview')
    expect(report.counts.unresolved_rows).toBeGreaterThan(0)
  })
  it('an LV non-fused disconnect -> switch_catalog_gap (no scope_pending line)', () => {
    const res = runTakeoff(art([{ raw: 'NF Disconnect', tag: 'DS-2', busVoltageV: 480 }]))
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
  })
  it('a switch + a real breaker coexist: the switch scope_pends, the breaker matches', () => {
    const res = runTakeoff(art([
      { raw: 'Fused Disconnect', tag: 'DS-3', busVoltageV: 15000 },
      { raw: '800AF/800AT LSIG', tag: 'CB-1', busVoltageV: 480 },
    ]))
    expect(res.scopePendingLines?.some((s) => s.switchType === 'fused_disconnect')).toBe(true)
    expect(res.matchedLines.length).toBe(1)   // the breaker priced
  })
  it('Codex P1: a Vacuum Switch is a switch_catalog_gap, NEVER silently priced as a breaker', () => {
    // "vacuum" is in BREAKER_HINT, so without a vacuum-switch anchor the row falls to the breaker path and is
    // mispriced. The vacuum-switch anchor routes it to the switch family -> recognized vacuum switch -> gap.
    const res = runTakeoff(art([{ raw: 'Vacuum Switch', tag: 'DS-9', busVoltageV: 15000 }]))
    expect(res.matchedLines.length).toBe(0)                                       // NOT a priced breaker line
    expect(res.findings.some((f) => f.code === 'switch_catalog_gap')).toBe(true)  // surfaced as a switch gap
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
  })
  it('Codex P2: an MV non-fused disconnect is NOT defaulted to the fused-disconnect ref', () => {
    const res = runTakeoff(art([{ raw: 'Non-Fused Disconnect', tag: 'DS-10', busVoltageV: 15000 }]))
    const sp = res.scopePendingLines?.[0]
    expect(sp).toBeDefined()
    expect(sp!.switchType).toBe('unknown')                       // not 'fused_disconnect'
    expect(sp!.provisionalDefaultRef).toBeUndefined()            // generic -> no default (never the fused ref)
  })
})
