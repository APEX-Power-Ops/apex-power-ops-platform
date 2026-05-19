import { expect, test } from '@playwright/test'

test('pm customer reporting placeholder route renders no-live customer-facing guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/customer-reporting-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Customer reporting stays blocked as a placeholder downstream branch/i })).toBeVisible()
  await expect(page.getByText(/customer reporting may move forward only as placeholder taxonomy, guardrails, report-package planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('CUSTOMER_REPORT_DRAFT')).toBeVisible()
  await expect(page.getByText('COMPLETION_EVIDENCE_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, customer report creation, completion evidence generation, or customer-facing publication/i)).toBeVisible()
  await expect(page.getByText(/No reuse of production tracking, durable field record, or customer delivery execution proof as live reporting authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Customer Reporting Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate customer reporting planning from production tracking proof and later financial handoff proof/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Production tracking placeholder/i })).toHaveAttribute('href', '/pm-review/production-tracking-placeholder')
  await expect(page.getByRole('link', { name: /Finance placeholder/i })).toHaveAttribute('href', '/pm-review/finance-placeholder')

  expect(mutationRequests).toHaveLength(0)
})