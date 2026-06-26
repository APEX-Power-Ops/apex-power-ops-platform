import { expect, test } from '@playwright/test'
import { parseArtifact, runTakeoff } from '@apex/estimator-takeoff'

test('estimator-takeoff engine is importable + browser-safe (parse + run, no Node deps)', () => {
  const artifact = parseArtifact({
    pdf: 't.pdf',
    apparatus: [{ raw: 'MSB 800AF/800AT', tag: 'MSB-1', sheet: 'E1', page: 0, bbox: [0, 0, 1, 1], evidence: 'one-line' }],
    voltageAssertions: [],
  })
  const result = runTakeoff(artifact)
  expect(result.dispositions).toHaveLength(1)
})
