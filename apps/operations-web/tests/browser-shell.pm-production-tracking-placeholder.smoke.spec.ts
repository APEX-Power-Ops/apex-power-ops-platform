import { expect, test } from '@playwright/test'

test('pm production tracking placeholder route renders no-live progress guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/production-tracking-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Production tracking stays blocked as a placeholder progress branch/i })).toBeVisible()
  await expect(page.getByText(/production tracking may move forward only as placeholder taxonomy, guardrails, progress-package planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('PRODUCTION_QUANTITY_DRAFT')).toBeVisible()
  await expect(page.getByText('LABOR_PROGRESS_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, production quantity write, labor progress write, apparatus completion update, or audit readback commit/i)).toBeVisible()
  await expect(page.getByText(/No reuse of durable field record, schedule or status, or workfront context as live production authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Production Tracking Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate production tracking planning from durable field record evidence, customer reporting, and later financial handoff proof/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Durable field record placeholder/i })).toHaveAttribute('href', '/pm-review/durable-field-record-placeholder')
  await expect(page.getByRole('link', { name: /Customer delivery execution/i })).toHaveAttribute('href', '/pm-review/customer-delivery-execution')

  expect(mutationRequests).toHaveLength(0)
})