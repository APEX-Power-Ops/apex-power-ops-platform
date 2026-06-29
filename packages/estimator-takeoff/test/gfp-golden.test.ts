import { describe, it, expect } from 'vitest'
import fixture from './fixtures/gfp-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { reconcile, renderReportText } from '../src/runner/report'
import { buildNativeEnvelope } from '@apex/estimator-core'
import { GFP_REF } from '../src/catalog/gfp-map.data'

describe('GFP family golden - breaker + relay + standalone GFP coexist', () => {
  const r = runTakeoff(fixture as any)

  it('breaker prices; relay + standalone GFP scope_pending; partial_preview', () => {
    expect(r.matchedLines.length).toBe(1)                        // MSB-1 breaker
    expect((r.scopePendingLines ?? []).length).toBe(2)          // R-1 + GFP-1
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-GFP', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)    // the breaker line priced
  })

  it('the embedded-GFP-stays-parent rule holds end-to-end: the LSIG breaker has NO gfp disposition', () => {
    expect(r.dispositions.every((d) => d.reasonCode !== 'gfp_scope_pending' || d.tag === 'GFP-1')).toBe(true)
    const msb = r.dispositions.find((d) => d.tag === 'MSB-1')!
    expect(msb.status).toBe('matched')
  })

  it('the standalone GFP -> scope_pending with the single ref as provisional default', () => {
    const sp = (r.scopePendingLines ?? []).find((s) => s.line.signature.kind === 'gfp')!
    expect(sp.candidateRefs).toEqual([GFP_REF])
    expect(sp.provisionalDefaultRef).toBe(GFP_REF)
    const report = reconcile(fixture as any, r, { bid_cents: 0 })
    expect(renderReportText(report)).toContain('provisional=Ground Fault Protection Device LV')
  })

  // Gate-2 STAND-IN: an operator-confirmed GFP device prices through estimator-core directly.
  // NOT a V1 auto-price path - GFP is never auto-priced (the engine only scope_pends it).
  it('Gate-2 STAND-IN: the confirmed GFP ref prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({
      projectNumber: 'PHX-GFP',
      scopes: [{ name: 'Block GFP', netaStandard: 'ATS', lines: [{ ref: GFP_REF, qty: 1 }] }],
    })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
