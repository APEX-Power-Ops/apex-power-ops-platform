import { expect, test } from '@playwright/test'

const WORKLIST = [
  { apparatus_id: 'a1', apparatus_designation: 'CB-1', scope_id: 's1', project_id: 'p1',
    project_number: 'PN-1', status: 'Complete', quoted_hours: 10, quoted_revenue: 1500,
    attestation_id: 'att1', attested_by: 'pm', attested_at: '2026-06-23', attest_reason: 'done',
    net_recognized: 0, is_recognized: false, recognized_event_id: null,
    can_attest: false, can_recognize: true, can_revoke: true, can_reverse: false },
  { apparatus_id: 'a2', apparatus_designation: 'DS-1', scope_id: 's1', project_id: 'p1',
    project_number: 'PN-1', status: 'In Progress', quoted_hours: 4, quoted_revenue: 600,
    attestation_id: null, attested_by: null, attested_at: null, attest_reason: null,
    net_recognized: 0, is_recognized: false, recognized_event_id: null,
    can_attest: true, can_recognize: false, can_revoke: false, can_reverse: false },
]
const ROLLUP = [{ project_number: 'PN-1', scope_id: 's1', project_id: 'p1',
  recognized_total: 0, recognized_count: 0, eligible_count: 2 }]

test('recognition page: renders worklist, gates buttons by flags, modal attest + recognize post, for-recognition copy', async ({ page }) => {
  await page.route('**/api/v1/ops/recognition/worklist*', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(WORKLIST) }))
  await page.route('**/api/v1/ops/recognition/rollup*', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ROLLUP) }))
  let attestBody: unknown = null
  await page.route('**/api/v1/ops/recognition/completion/attest', async (r) => {
    attestBody = r.request().postDataJSON()
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ attestation_id: 'att2' }) })
  })
  let recognizeBody: unknown = null
  await page.route('**/api/v1/ops/recognition/events/recognize', async (r) => {
    recognizeBody = r.request().postDataJSON()
    await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ event_id: 'ev1' }) })
  })
  // the shared PM shell probes assorted /api/v1/reads/* and /api/v1/schedule/* endpoints on every
  // /pm-review/* route; CI runs no backend, so stub them ALL empty to let the page reach networkidle.
  // (recognition data is mocked above; these are shell-context calls this test does not assert on.)
  await page.route('**/api/v1/reads/**', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.route('**/api/v1/schedule/**', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))

  const resp = await page.goto('/pm-review/recognition', { waitUntil: 'networkidle' })
  expect(resp?.ok()).toBeTruthy()
  await expect(page.getByText('for recognition')).toBeVisible()
  await expect(page.locator('body')).not.toContainText('production complete')

  await page.getByLabel('project number').fill('PN-1')
  await page.getByRole('button', { name: 'Load' }).click()
  await expect(page.getByText('CB-1')).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText('DS-1')).toBeVisible()

  // a1 is Complete+attested -> Recognize enabled, Attest disabled; a2 -> Attest enabled
  const row1 = page.getByRole('row', { name: /CB-1/ })
  await expect(row1.getByRole('button', { name: 'Recognize' })).toBeEnabled()
  await expect(row1.getByRole('button', { name: 'Attest' })).toBeDisabled()
  const row2 = page.getByRole('row', { name: /DS-1/ })
  await expect(row2.getByRole('button', { name: 'Attest' })).toBeEnabled()

  // --- ATTEST: opens a reason-required modal (NO window.prompt); Confirm posts the typed reason ---
  await row2.getByRole('button', { name: 'Attest' }).click()
  const attestModal = page.getByRole('dialog')
  await expect(attestModal).toBeVisible()
  await expect(attestModal).toContainText('for recognition')
  await expect(attestModal).not.toContainText('production complete')
  // Confirm is disabled until a non-blank reason is entered.
  await expect(attestModal.getByRole('button', { name: 'Confirm' })).toBeDisabled()
  await attestModal.getByLabel('reason').fill('tested ok')
  await attestModal.getByRole('button', { name: 'Confirm' }).click()
  await expect.poll(() => attestBody).not.toBeNull()
  expect((attestBody as { apparatus_id: string }).apparatus_id).toBe('a2')
  expect((attestBody as { reason: string }).reason).toBe('tested ok')

  // --- RECOGNIZE: opens a modal with two enum-constrained <select>s; POST carries the chosen value ---
  await row1.getByRole('button', { name: 'Recognize' }).click()
  const recModal = page.getByRole('dialog')
  await expect(recModal).toBeVisible()
  const dsSelect = recModal.getByLabel('datasheet clearance')
  // the <select> offers EXACTLY provided | not_applicable
  await expect(dsSelect.locator('option')).toHaveText(['provided', 'not_applicable'])
  await dsSelect.selectOption('provided')
  await recModal.getByLabel('cx clearance').selectOption('not_applicable')
  await recModal.getByRole('button', { name: 'Confirm' }).click()
  await expect.poll(() => recognizeBody).not.toBeNull()
  expect((recognizeBody as { apparatus_id: string }).apparatus_id).toBe('a1')
  expect((recognizeBody as { datasheet_clearance: string }).datasheet_clearance).toBe('provided')
  expect((recognizeBody as { cx_clearance: string }).cx_clearance).toBe('not_applicable')
})
