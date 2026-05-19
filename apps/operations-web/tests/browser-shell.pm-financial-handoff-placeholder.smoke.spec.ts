import { expect, test } from '@playwright/test'

test('pm financial handoff placeholder route renders no-live finance handoff guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/financial-handoff-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Financial handoff stays blocked as a placeholder downstream branch/i })).toBeVisible()
  await expect(page.getByText(/financial handoff may move forward only as placeholder taxonomy, guardrails, billing and payroll contract planning/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Handoff Taxonomy/i })).toBeVisible()
  await expect(page.getByText('BILLING_EXPORT_DRAFT')).toBeVisible()
  await expect(page.getByText('PAYROLL_EXPORT_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, billing export, payroll export, invoice creation, or accounting output from this route/i)).toBeVisible()
  await expect(page.getByText(/No reuse of customer reporting, production tracking, or customer delivery execution proof as live financial authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Financial Handoff Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Define the minimum billing export contract before any billable handoff can exist/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Customer reporting placeholder/i })).toHaveAttribute('href', '/pm-review/customer-reporting-placeholder')
  await expect(page.getByRole('link', { name: /Customer billing placeholder/i })).toHaveAttribute('href', '/pm-review/customer-billing-placeholder')

  expect(mutationRequests).toHaveLength(0)
})