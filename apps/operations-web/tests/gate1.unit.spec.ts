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
