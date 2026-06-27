import { expect, test } from '@playwright/test'
import { parseArtifact, reconcile, type ReconciliationReport } from '@apex/estimator-takeoff'
import { evaluate, resolvableVoltageGroups, otherOpenItems } from '../lib/gate1'

const ARTIFACT = parseArtifact({
  pdf: 't.pdf',
  apparatus: [
    { raw: 'FB-1 400AF/400AT', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' },
    { raw: 'UNLABELED 225AF/225AT', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' },
  ],
  voltageAssertions: [],
})

test('evaluate (thin helper = runTakeoff + reconcile) returns both result and report', () => {
  const { result, report } = evaluate(ARTIFACT)
  expect(result.dispositions.length).toBe(2)
  expect(report.status).toBe('partial_preview')
})

test('resolvableVoltageGroups includes the TAGGED missing-voltage row grouped by sheet/block/tag', () => {
  const { result } = evaluate(ARTIFACT)
  const tags = resolvableVoltageGroups(result, ARTIFACT).flatMap((g) => g.blocks.flatMap((b) => b.tags.map((t) => t.tag)))
  expect(tags).toContain('FB-1')
})

test('resolvableVoltageGroups EXCLUDES untagged rows (engine is tag-keyed)', () => {
  const { result } = evaluate(ARTIFACT)
  const raws = resolvableVoltageGroups(result, ARTIFACT).flatMap((g) => g.blocks.flatMap((b) => b.tags.map((t) => t.raw)))
  expect(raws).not.toContain('UNLABELED 225AF/225AT')
})

test('otherOpenItems includes the untagged missing-voltage row as read-only', () => {
  const { result } = evaluate(ARTIFACT)
  expect(otherOpenItems(result, ARTIFACT).some((i) => i.kind === 'untagged_missing_voltage')).toBe(true)
})

import { buildAssertions, mergeAssertionsByTag } from '../lib/gate1'

test('buildAssertions stamps source gate1 + actor, one tag per entry', () => {
  expect(buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
    .toEqual([{ voltageV: 480, tags: ['FB-1'], source: 'gate1', actor: 'JLS' }])
})

test('mergeAssertionsByTag REPLACES a same-tag existing/CLI assertion (no duplicate-tag)', () => {
  const existing = [{ voltageV: 208, tags: ['FB-1'], source: 'cli' as const }]
  const merged = mergeAssertionsByTag(existing, buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
  const fb1 = merged.filter((m) => m.tags.includes('FB-1'))
  expect(fb1).toHaveLength(1)
  expect(fb1[0].voltageV).toBe(480)
  expect(fb1[0].source).toBe('gate1')
})

test('mergeAssertionsByTag keeps unrelated existing tags', () => {
  const merged = mergeAssertionsByTag([{ voltageV: 208, tags: ['OTHER'], source: 'cli' as const }],
    buildAssertions([{ tag: 'FB-1', voltageV: 480 }], 'JLS'))
  expect(merged.some((m) => m.tags.includes('OTHER') && m.voltageV === 208)).toBe(true)
  expect(merged.some((m) => m.tags.includes('FB-1') && m.voltageV === 480)).toBe(true)
})

import { buildExport } from '../lib/gate1'

test('buildExport omits envelope and labels partial_preview when not clean', async () => {
  // Two-row artifact: FB-1 matched (800AF/LSIG + 480V assertion), FB-2 missing-voltage question.
  // matchedLines=1 -> passes the zero-matched guard; isClean=false -> partial_preview path.
  const art = parseArtifact({ pdf: 't.pdf', apparatus: [
    { raw: 'FB-1 800AF/800AT LSIG', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' },
    { raw: 'FB-2 400AF/400AT', tag: 'FB-2', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' }],
    voltageAssertions: [{ voltageV: 480, tags: ['FB-1'] }] })
  const { result, report } = evaluate(art)
  const { combined } = await buildExport({ artifact: art, result, report,
    projectCtx: { projectNumber: 'P1', operatorName: 'JLS' }, nowIso: '2026-06-26T00:00:00Z' })
  const c = combined as any
  expect(c.manifest.status).toBe('partial_preview')
  expect(c.envelope).toBeUndefined()
  // FIX C (P2-3): partial path emits NO envelope, so the exported report carries no envelopeTotals.
  expect(c.report.envelopeTotals).toBeUndefined()
  expect(c.manifest.operatorEvidence.authoritative).toBe(false)
  expect(c.manifest.artifactContentHash).toMatch(/^[0-9a-f]{64}$/)
})

// CLEAN-path proof. Probed minimal single-row artifact: an LV draw-out main reached via the
// engine baseline (>=800AF + G-function -> draw_out) plus a per-tag 480V Gate-1 assertion.
// raw "FB-1 800AF/800AT LSIG" + assert 480V on FB-1 -> matched LSIG draw-out, 0 questions/findings,
// isClean=true, matchedLines=1 (verified by throwaway probe: bid_cents 66000).
test('buildExport includes a priced envelope when clean', async () => {
  const art = parseArtifact({ pdf: 'c.pdf', apparatus: [
    { raw: 'FB-1 800AF/800AT LSIG', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1' }],
    voltageAssertions: [{ voltageV: 480, tags: ['FB-1'] }] })
  const { result, report } = evaluate(art)
  const { combined } = await buildExport({ artifact: art, result, report,
    projectCtx: { projectNumber: 'P1', operatorName: 'JLS' }, nowIso: '2026-06-26T00:00:00Z' })
  const c = combined as any
  expect(c.manifest.status).toBe('clean')
  expect(c.envelope).toBeDefined()
  expect(c.envelope.totals.bid_cents).toBeGreaterThan(0)
  // FIX C (P2-3): the exported clean report must be the POST-emit reconcile (matching the runner),
  // so report.envelopeTotals is present and mirrors the emitted envelope.
  expect(c.report.envelopeTotals).toBeDefined()
  expect(c.report.envelopeTotals.bid_cents).toBe(c.envelope.totals.bid_cents)
  expect(c.report.envelopeTotals.bid_cents).toBeGreaterThan(0)
})

// ---------------------------------------------------------------------------
// FIX A (P2-1): advisory-on-matched / non-surfaced operator questions must
// appear in "Other Open Items" (they block Clean Export via isClean, so the
// operator must be able to SEE them). Hand-crafted TakeoffResult - no engine.
// ---------------------------------------------------------------------------
import type { TakeoffResult, ApparatusDisposition } from '@apex/estimator-takeoff'
import type { ExtractionArtifact } from '@apex/estimator-takeoff'

function matchedDisposition(inputIndex: number, tag: string): ApparatusDisposition {
  return {
    inputIndex, tag, raw: `${tag} 800AF/800AT LSIG`, sheet: 'E1', page: 0,
    bbox: [0, 0, 1, 1], evidence: 'one-line', status: 'matched',
    reasonCode: 'catalog_rule', reason: 'matched a catalog rule', ref: 'BRK-X', lineKey: 'L1',
  }
}

function questionDisposition(inputIndex: number, tag: string): ApparatusDisposition {
  return {
    inputIndex, tag, raw: `${tag} location-only`, sheet: 'E9', page: 0,
    bbox: [0, 0, 1, 1], evidence: 'one-line', status: 'question',
    reasonCode: 'location_only_non_authoritative', reason: 'device only on a non-authoritative sheet',
  }
}

function emptyResult(dispositions: ApparatusDisposition[], operatorQuestions: TakeoffResult['operatorQuestions']): TakeoffResult {
  return { matchedLines: [], unmatchedCandidates: [], operatorQuestions, findings: [], dispositions }
}

function artifactFor(dispositions: ApparatusDisposition[]): ExtractionArtifact {
  return {
    pdf: 't.pdf',
    apparatus: dispositions.map((d) => ({
      raw: d.raw, tag: d.tag, sheet: d.sheet, page: d.page, bbox: d.bbox, evidence: d.evidence,
    })),
  } as unknown as ExtractionArtifact
}

test('otherOpenItems surfaces an advisory-on-matched operator question (P2-1)', () => {
  const dispositions = [matchedDisposition(0, 'FB-1')]
  const result = emptyResult(dispositions, [
    { question: 'mounting hint conflict on FB-1 - confirm mounting', context: 'E1', code: 'mounting_hint_conflict', inputIndex: 0 },
  ])
  const artifact = artifactFor(dispositions)
  const items = otherOpenItems(result, artifact)
  // The matched row's disposition is NOT question/unmatched, so before the fix this question
  // (inputIndex !== undefined, and not surfaced by a disposition) was dropped entirely.
  const questions = items.filter((i) => i.kind === 'question')
  expect(questions).toHaveLength(1)
  expect(questions[0].label).toContain('mounting hint conflict')
  expect(questions[0].sheet).toBe('E1')
  expect(questions[0].reasonCode).toBe('mounting_hint_conflict')
})

test('otherOpenItems surfaces a location_only row exactly once (no duplicate from same-index question) (P2-1)', () => {
  const dispositions = [questionDisposition(0, 'FB-9')]
  const result = emptyResult(dispositions, [
    { question: 'Device appears only on a non-authoritative sheet - include it?', context: 'E9', code: 'location_only', inputIndex: 0 },
  ])
  const artifact = artifactFor(dispositions)
  const items = otherOpenItems(result, artifact)
  // Disposition is a 'question' (surfaced by the disposition loop). The same-index operatorQuestion
  // must NOT also be pushed -> exactly one item referencing inputIndex 0.
  const forRow = items.filter((i) => i.kind === 'question')
  expect(forRow).toHaveLength(1)
})

// ---------------------------------------------------------------------------
// ZERO-MATCHED GUARD (cross-engine finding): buildExport must REJECT a run
// where matchedLines.length === 0, mirroring the runner's hard block in run.ts.
// Hand-crafted TakeoffResult: 3 non-breaker apparatus rows all disposition
// 'ignored' / 'non_breaker_excluded' -> 0 matchedLines, isClean=true.
// Engine-verified (probe 2026-06-26): TX/PDU/METER rows w/ no frame rating
// get non_breaker_excluded; reconcile yields report.status='clean'.
// This test: RED before the Layer-1 guard in buildExport; GREEN after.
// ---------------------------------------------------------------------------
function ignoredDisposition(inputIndex: number, tag: string, raw: string): ApparatusDisposition {
  return {
    inputIndex, tag, raw, sheet: 'E1', page: 0,
    bbox: [0, 0, 1, 1], evidence: 'one-line', status: 'ignored',
    reasonCode: 'non_breaker_excluded', reason: 'non-breaker device token',
  }
}

test('buildExport rejects a zero-matched run (no matched lines - nothing to price)', async () => {
  // Craft a minimal all-ignored zero-matched artifact.
  // The apparatus rows are non-breaker tokens (XFMR, PDU, METER) with no frame/trip rating.
  // Engine-verified: these yield non_breaker_excluded dispositions, matchedLines=0, isClean=true.
  const dispositions = [
    ignoredDisposition(0, 'TX-1', 'TX-1 XFMR'),
    ignoredDisposition(1, 'PDU-2', 'PDU-2 PDU'),
    ignoredDisposition(2, 'METER-3', 'METER-3 METER'),
  ]
  const zeroResult: TakeoffResult = {
    matchedLines: [],
    unmatchedCandidates: [],
    operatorQuestions: [],
    findings: [],
    dispositions,
  }
  const zeroArtifact = {
    pdf: 'zero.pdf',
    apparatus: dispositions.map((d) => ({
      raw: d.raw, tag: d.tag, sheet: d.sheet, page: d.page, bbox: d.bbox, evidence: d.evidence,
    })),
    voltageAssertions: [],
  } as unknown as ExtractionArtifact

  // report.status is 'clean' per the engine (probe-verified 2026-06-26).
  const zeroReport = reconcile(zeroArtifact, zeroResult)





  await expect(buildExport({
    artifact: zeroArtifact,
    result: zeroResult,
    report: zeroReport,
    projectCtx: { projectNumber: 'P-ZERO', operatorName: 'JLS' },
    nowIso: '2026-06-26T00:00:00Z',
  })).rejects.toThrow('nothing to price')
})
