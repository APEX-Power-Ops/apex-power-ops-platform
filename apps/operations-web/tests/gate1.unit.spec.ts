import { expect, test } from '@playwright/test'
import { parseArtifact } from '@apex/estimator-takeoff'
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
  const art = parseArtifact({ pdf: 't.pdf', apparatus: [
    { raw: 'FB-1 400AF/400AT', tag: 'FB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line' }], voltageAssertions: [] })
  const { result, report } = evaluate(art)
  const { combined } = await buildExport({ artifact: art, result, report,
    projectCtx: { projectNumber: 'P1', operatorName: 'JLS' }, nowIso: '2026-06-26T00:00:00Z' })
  const c = combined as any
  expect(c.manifest.status).toBe('partial_preview')
  expect(c.envelope).toBeUndefined()
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
})
