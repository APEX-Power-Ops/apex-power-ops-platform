import { expect, test } from '@playwright/test'

test('pm durable field record placeholder route renders no-live evidence guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/durable-field-record-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Durable field record stays blocked as a placeholder evidence branch/i })).toBeVisible()
  await expect(page.getByText(/durable field records may move forward only as placeholder taxonomy, guardrails, evidence-package planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('DAILY_RECORD_PACKET_DRAFT')).toBeVisible()
  await expect(page.getByText('FIELD_EVIDENCE_BUNDLE_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, daily record commit, evidence upload, labor readback, or completion-note release/i)).toBeVisible()
  await expect(page.getByText(/No reuse of schedule or status, field authorization, or workfront context as live daily-record authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Durable Field Record Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate durable field record planning from schedule or status control and later production tracking proof/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Schedule status placeholder/i })).toHaveAttribute('href', '/pm-review/schedule-status-placeholder')
  await expect(page.getByRole('link', { name: /Customer delivery execution/i })).toHaveAttribute('href', '/pm-review/customer-delivery-execution')

  expect(mutationRequests).toHaveLength(0)
})