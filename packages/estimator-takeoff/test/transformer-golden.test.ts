import { describe, it, expect } from 'vitest'
import fixture from './fixtures/transformer-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { buildNativeEnvelope } from '@apex/estimator-core'
import { DRY_DEFAULT_REF } from '../src/catalog/transformer-map.data'

describe('transformer family golden', () => {
  it('families coexist: breaker prices, transformers scope_pending, partial_preview', () => {
    const r = runTakeoff(fixture as any)
    expect(r.matchedLines.length).toBe(1)                        // the breaker (MSB-1 draw-out LSIG)
    expect(r.scopePendingLines.length).toBe(2)                   // T-1 dry + T-2 oil
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-TX', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)    // the breaker line priced
  })

  // Gate-2 STAND-IN: a chosen transformer tier prices through estimator-core directly.
  // NOT a V1 auto-price path - the engine never auto-prices a transformer (invariant 9).
  // This test represents the operator authoring a scope decision and feeding a ref to estimator-core
  // manually (the human-in-the-loop Gate-2 path), NOT an automatic takeoff match.
  it('Gate-2 STAND-IN: a chosen transformer tier prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({
      projectNumber: 'PHX-TX',
      scopes: [{
        name: 'Block X',
        netaStandard: 'ATS',
        lines: [{ ref: DRY_DEFAULT_REF, qty: 1 }],
      }],
    })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
