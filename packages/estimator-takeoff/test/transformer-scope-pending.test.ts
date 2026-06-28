import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { isClean, reconcile } from '../src/runner/report'
import { runFromArtifact } from '../src/runner/run'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus })

// A dry-type transformer with voltage: recognized -> scope_pending (DRY_GROUP)
const dryRow = row({ raw: 'T-1 1500KVA 480V DRY-TYPE XFMR', tag: 'T-1', busVoltageV: 480 })
// An unknown-coolant transformer (no coolant token) with voltage: recognized but coolant=unknown -> catalog_gap
const unknownCoolantRow = row({ raw: 'T-2 1000KVA 480V XFMR', tag: 'T-2', busVoltageV: 480 })

describe('scope_pending disposition -- dry transformer with voltage', () => {
  const r = runTakeoff(art([dryRow]))

  it('produces exactly one scopePendingLines entry (no priced line)', () => {
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines).toHaveLength(1)
  })

  it('scopePendingLine carries candidateRefs (DRY_GROUP) and a defaultRef', () => {
    const sp = r.scopePendingLines[0]!
    expect(sp.candidateRefs.length).toBeGreaterThan(0)
    expect(sp.defaultRef).toBeTruthy()
    expect(sp.candidateRefs).toContain(sp.defaultRef)
  })

  it('scopePendingLine carries qty and a lineKey', () => {
    const sp = r.scopePendingLines[0]!
    expect(sp.qty).toBeGreaterThan(0)
    expect(sp.line.lineKey).toBeTruthy()
  })

  it('disposition is scope_pending / transformer_scope_pending', () => {
    expect(r.dispositions[0]!.status).toBe('scope_pending')
    expect(r.dispositions[0]!.reasonCode).toBe('transformer_scope_pending')
  })

  it('disposition carries the defaultRef as ref', () => {
    expect(r.dispositions[0]!.ref).toBe(r.scopePendingLines[0]!.defaultRef)
  })

  it('isClean returns false (scope_pending blocks clean)', () => {
    expect(isClean(r)).toBe(false)
  })

  it('reconcile counts scope_pending in unresolved_rows', () => {
    const report = reconcile(art([dryRow]), r)
    expect(report.counts.unresolved_rows).toBeGreaterThanOrEqual(1)
  })

  it('reconcile is accounted (internal consistency holds)', () => {
    const report = reconcile(art([dryRow]), r)
    expect(report.accounted).toBe(true)
  })

  it('emits a scope-question operatorQuestion with transformer_scope_pending code', () => {
    const q = r.operatorQuestions.find((q) => q.code === 'transformer_scope_pending')
    expect(q).toBeDefined()
    expect(q!.context).toMatch(/T-1/)
  })
})

describe('catalog_gap finding -- unknown-coolant transformer with voltage', () => {
  const r = runTakeoff(art([unknownCoolantRow]))

  it('is unmatched (never priced), status unmatched', () => {
    expect(r.matchedLines).toHaveLength(0)
    expect(r.scopePendingLines).toHaveLength(0)
    expect(r.dispositions[0]!.status).toBe('unmatched')
    expect(r.dispositions[0]!.reasonCode).toBe('transformer_catalog_gap')
  })

  it('emits a warning finding with code transformer_catalog_gap', () => {
    const f = r.findings.find((f) => f.code === 'transformer_catalog_gap')
    expect(f).toBeDefined()
    expect(f!.severity).toBe('warning')
  })

  it('emits a transformer_catalog_gap operatorQuestion', () => {
    const q = r.operatorQuestions.find((q) => q.code === 'transformer_catalog_gap')
    expect(q).toBeDefined()
  })
})

describe('transformer-only artifact through runFromArtifact with allowOpenItems', () => {
  it('partial_preview, exitCode 0 (NOT the nothing-to-price exit 1)', () => {
    const res = runFromArtifact(art([dryRow]), { projectNumber: 'P1', allowOpenItems: true })
    expect(res.exitCode).toBe(0)
    expect(res.report?.status).toBe('partial_preview')
  })

  it('WITHOUT allowOpenItems: exitCode non-zero (open items blocked)', () => {
    const res = runFromArtifact(art([dryRow]), { projectNumber: 'P1', allowOpenItems: false })
    expect(res.exitCode).not.toBe(0)
    expect(res.envelope).toBeUndefined()
  })

  it('transformer-ONLY with no matched lines and no scope_pending (unknown coolant) -> nothing-to-price exit 1', () => {
    // unknown coolant -> catalog_gap -> unmatched (not scope_pending) -> 0 matched + 0 scope_pending -> exit 1
    const res = runFromArtifact(art([unknownCoolantRow]), { projectNumber: 'P1', allowOpenItems: true })
    expect(res.exitCode).toBe(1)
    expect(res.stderr.join(' ')).toMatch(/nothing to price/)
  })
})

describe('breaker path invariant -- scope_pending does not affect breaker runs', () => {
  const matchedBreaker = row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' })

  it('a breaker-only run still produces matchedLines and isClean (no regression)', () => {
    const r = runTakeoff(art([matchedBreaker]))
    expect(r.matchedLines).toHaveLength(1)
    expect(r.scopePendingLines).toHaveLength(0)
    expect(isClean(r)).toBe(true)
  })

  it('mixed breaker+transformer: matched from breaker, scope_pending from transformer, partial_preview', () => {
    const r = runTakeoff(art([matchedBreaker, dryRow]))
    expect(r.matchedLines).toHaveLength(1)
    expect(r.scopePendingLines).toHaveLength(1)
    expect(isClean(r)).toBe(false)
    const report = reconcile(art([matchedBreaker, dryRow]), r)
    expect(report.counts.unresolved_rows).toBeGreaterThanOrEqual(1)
    expect(report.accounted).toBe(true)
  })
})
