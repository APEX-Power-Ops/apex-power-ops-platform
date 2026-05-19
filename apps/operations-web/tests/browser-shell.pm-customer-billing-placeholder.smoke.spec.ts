import { expect, test } from '@playwright/test'

test('pm customer billing placeholder route renders downstream no-live planning guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/customer-billing-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Customer billing delivery stays blocked as a placeholder downstream branch/i })).toBeVisible()
  await expect(page.getByText(/customer billing delivery can move forward only as placeholder taxonomy, guardrails, customer-facing release planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('CUSTOMER_BILLING_DELIVERY_DRAFT')).toBeVisible()
  await expect(page.getByText('BILLING_EXPORT_PACKAGE_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, write, export, invoice, email, portal push, or customer delivery artifact release/i)).toBeVisible()
  await expect(page.getByText(/No reuse of customer-delivery execution proof as billing authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Customer Billing Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate customer billing delivery from internal finance handoff, payroll, and accounting persistence/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Project overview/i })).toHaveAttribute('href', '/pm-review/project-overview')
  await expect(page.getByRole('link', { name: /Financial handoff placeholder/i })).toHaveAttribute('href', '/pm-review/financial-handoff-placeholder')
  await expect(page.getByRole('link', { name: /Finance placeholder/i })).toHaveAttribute('href', '/pm-review/finance-placeholder')

  expect(mutationRequests).toHaveLength(0)
})