import { describe, it, expect } from 'vitest'
import fixture from './fixtures/itx-mixed.extract.json'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import { reconcile, renderReportText } from '../src/runner/report'
import { buildNativeEnvelope } from '@apex/estimator-core'

describe('instrument-transformer golden - breaker + power transformer + CT + PT coexist', () => {
  const r = runTakeoff(fixture as any)
  it('breaker prices; power transformer + CT + PT scope_pending; partial_preview', () => {
    expect(r.matchedLines.length).toBe(1)                         // MSB-1
    expect((r.scopePendingLines ?? []).length).toBe(3)            // T-1 (power) + CT-1 + PT-1
    const res = runFromArtifact(fixture as any, { projectNumber: 'PHX-ITX', allowOpenItems: true })
    expect(res.report?.status).toBe('partial_preview')
    expect(res.envelope!.totals.bid_cents).toBeGreaterThan(0)
  })
  it('the power transformer stayed power (NOT instrument); CT/PT are instrument', () => {
    const sp = r.scopePendingLines ?? []
    expect(sp.some((s) => s.line.signature.kind === 'transformer')).toBe(true)
    expect(sp.filter((s) => s.line.signature.kind === 'instrument_transformer').length).toBe(2)
    const ct = sp.find((s) => s.line.signature.kind === 'instrument_transformer' && (s.line.signature as any).itxType === 'ct')!
    expect(ct.provisionalDefaultRef).toBe('Current Transformer MV - Set of 3')
    expect(renderReportText(reconcile(fixture as any, r, { bid_cents: 0 }))).toContain('packaging=set_of_3')
  })
  it('Gate-2 STAND-IN: a chosen instrument-transformer ref prices through estimator-core', () => {
    const { envelope } = buildNativeEnvelope({ projectNumber: 'PHX-ITX', scopes: [{ name: 'Block ITX', netaStandard: 'ATS', lines: [{ ref: 'Current Transformer MV - Set of 3', qty: 1 }] }] })
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
  })
})
