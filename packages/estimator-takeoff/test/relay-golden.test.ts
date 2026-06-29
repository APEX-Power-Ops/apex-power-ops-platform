import { describe, it, expect } from 'vitest'
import fixture from './fixtures/relay-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { reconcile, renderReportText } from '../src/runner/report'
import { buildNativeEnvelope } from '@apex/estimator-core'
import { ROLE_TO_TIER } from '../src/catalog/relay-map.data'

describe('relay family golden - breaker + transformer + relay coexist', () => {
  const r = runTakeoff(fixture as any)

  it('breaker prices; transformer + 3 relays scope_pending; partial_preview', () => {
    expect(r.matchedLines.length).toBe(1)                        // the breaker (MSB-1)
    expect((r.scopePendingLines ?? []).length).toBe(4)          // T-1 + R-1 + R-2 + R-3
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-RLY', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)    // the breaker line priced
  })

  it('the 87T relay has differential provisional default; the bare relay has none', () => {
    const sp = (r.scopePendingLines ?? [])
    const diff = sp.find((s) => s.line.signature.kind === 'relay' && (s.line.signature as any).role === 'differential')!
    const bare = sp.find((s) => s.line.signature.kind === 'relay' && (s.line.signature as any).role === 'unknown')!
    expect(diff.provisionalDefaultRef).toBe('Protective Relay (Differential Protection)')
    expect(bare.provisionalDefaultRef).toBeUndefined()
  })

  it('no-default relay renders provisional=none in BOTH JSON and text', () => {
    const report = reconcile(fixture as any, r, { bid_cents: 0 })
    expect(report.scopePending.some((s) => s.provisionalDefaultRef === undefined)).toBe(true)   // JSON
    const text = renderReportText(report)
    expect(text).toContain('provisional=none')                  // human report
    expect(text).not.toContain('provisional=undefined')
  })

  // Gate-2 STAND-IN: an operator-chosen relay tier prices through estimator-core directly.
  // NOT a V1 auto-price path - relays are never auto-priced (the engine only scope_pends them).
  it('Gate-2 STAND-IN: a chosen relay tier prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({
      projectNumber: 'PHX-RLY',
      scopes: [{ name: 'Block R', netaStandard: 'ATS', lines: [{ ref: ROLE_TO_TIER.differential!, qty: 1 }] }],
    })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
