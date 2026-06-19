import { expect, test } from '@playwright/test'

import { rollupByProject, RevenueRecognitionRow } from '../lib/revenue-recognition'

const scopeRow = (over: Partial<RevenueRecognitionRow>): RevenueRecognitionRow => ({
  project_id: 'p1', project_number: 'P-001', project_name: 'Project A',
  scope_id: 's', scope_name: 'Scope', quoted_revenue: 0, recognized_revenue: 0,
  recognition_percent: 0, billable_now: 0, total_apparatus: 0, completed_apparatus: 0,
  ...over,
})

test('rollupByProject sums scopes and recomputes the project percent', () => {
  const rows = [
    scopeRow({ scope_id: 's1', scope_name: 'One', quoted_revenue: 6000, recognized_revenue: 3000, billable_now: 3000, total_apparatus: 3, completed_apparatus: 2 }),
    scopeRow({ scope_id: 's2', scope_name: 'Two', quoted_revenue: 5000, recognized_revenue: 0, billable_now: 0, total_apparatus: 2, completed_apparatus: 0 }),
  ]
  const result = rollupByProject(rows)
  expect(result).toHaveLength(1)
  const p = result[0]
  expect(p.quoted_revenue).toBe(11000)
  expect(p.recognized_revenue).toBe(3000)
  expect(p.billable_now).toBe(3000)
  expect(p.recognition_percent).toBeCloseTo(27.27, 2)
  expect(p.total_apparatus).toBe(5)
  expect(p.completed_apparatus).toBe(2)
  expect(p.scopes).toHaveLength(2)
})

test('rollupByProject yields 0 percent when nothing is quoted', () => {
  const result = rollupByProject([scopeRow({ quoted_revenue: 0, recognized_revenue: 0 })])
  expect(result[0].recognition_percent).toBe(0)
})
