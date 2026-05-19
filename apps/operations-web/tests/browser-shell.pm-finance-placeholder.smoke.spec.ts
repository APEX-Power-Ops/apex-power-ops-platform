import { expect, test } from '@playwright/test'

test('pm finance placeholder route renders downstream no-live planning guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/finance-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Finance is open only as a placeholder design branch/i })).toBeVisible()
  await expect(page.getByText(/placeholder taxonomy, guardrails, evidence expectations, no-go checks, and later-admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('BILLING_EXPORT_DRAFT')).toBeVisible()
  await expect(page.getByText('ACCOUNTING_POST_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, write, export, sync, or delivery/i)).toBeVisible()
  await expect(page.getByText(/No reuse of the customer-delivery admission phrase for finance/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Finance Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/finance output planning from the dedicated financial handoff placeholder branch and from external customer billing delivery/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Non-Finance Boundaries Still Separate/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Project overview/i })).toHaveAttribute('href', '/pm-review/project-overview')
  await expect(page.getByRole('link', { name: /Financial handoff placeholder/i })).toHaveAttribute('href', '/pm-review/financial-handoff-placeholder')
  await expect(page.getByRole('link', { name: /Customer delivery execution/i })).toHaveAttribute('href', '/pm-review/customer-delivery-execution')

  expect(mutationRequests).toHaveLength(0)
})