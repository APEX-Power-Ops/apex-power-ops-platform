import { expect, test } from '@playwright/test'

test('pm source writeback placeholder route renders downstream no-live planning guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/source-writeback-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Source writeback stays blocked as a placeholder downstream branch/i })).toBeVisible()
  await expect(page.getByText(/source writeback can move forward only as placeholder taxonomy, guardrails, correction-package planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('SOURCE_WORKBOOK_WRITEBACK_DRAFT')).toBeVisible()
  await expect(page.getByText('SOURCE_MACRO_EXECUTION_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, workbook writeback, PDF overwrite, macro execution, or source-system sync/i)).toBeVisible()
  await expect(page.getByText(/No reuse of import, approval, or customer-delivery proof as source writeback authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Source Writeback Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate source writeback planning from finance handoff, customer billing delivery, and customer-facing delivery proof/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Project overview/i })).toHaveAttribute('href', '/pm-review/project-overview')
  await expect(page.getByRole('link', { name: /Financial handoff placeholder/i })).toHaveAttribute('href', '/pm-review/financial-handoff-placeholder')
  await expect(page.getByRole('link', { name: /Customer billing placeholder/i })).toHaveAttribute('href', '/pm-review/customer-billing-placeholder')

  expect(mutationRequests).toHaveLength(0)
})