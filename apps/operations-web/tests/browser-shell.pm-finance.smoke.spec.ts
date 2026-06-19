import { expect, test } from '@playwright/test'

test('pm finance route renders derived recognized revenue (read-only)', async ({ page }) => {
  const mutationRequests: string[] = []
  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'no mutations' }) })
  })

  await page.route('**/api/v1/ops/revenue-recognition*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          project_id: '11111111-1111-1111-1111-111111111111',
          project_number: 'P-001', project_name: 'Test Project A',
          scope_id: 's1', scope_name: 'Scope One',
          quoted_revenue: 6000, recognized_revenue: 3000, recognition_percent: 50,
          billable_now: 3000, total_apparatus: 3, completed_apparatus: 2,
        },
      ]),
    })
  })

  const response = await page.goto('/pm-review/finance', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Recognized revenue by project/i })).toBeVisible()
  await expect(page.getByText(/derived from apparatus completion/i)).toBeVisible()
  await expect(page.getByText('Test Project A')).toBeVisible()
  await expect(page.getByText('Scope One')).toBeVisible()
  expect(mutationRequests).toHaveLength(0)
})
