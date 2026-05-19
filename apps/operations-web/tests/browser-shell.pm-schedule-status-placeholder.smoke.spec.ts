import { expect, test } from '@playwright/test'

test('pm schedule status placeholder route renders no-live timing and state guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/schedule-status-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Schedule and status stay blocked as a placeholder control branch/i })).toBeVisible()
  await expect(page.getByText(/schedule and status may move forward only as placeholder taxonomy, guardrails, hold-and-dispatch planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('SCHEDULE_WINDOW_DRAFT')).toBeVisible()
  await expect(page.getByText('STATUS_TRANSITION_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, schedule commit, status transition, dispatch release, or hold removal/i)).toBeVisible()
  await expect(page.getByText(/No reuse of field authorization, intake, or workfront context as live timing or state authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Schedule Status Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate schedule or status planning from field authorization, daily records, and later production tracking proof/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Field authorization placeholder/i })).toHaveAttribute('href', '/pm-review/field-authorization-placeholder')
  await expect(page.getByRole('link', { name: /Schedule review/i })).toHaveAttribute('href', '/pm-review/schedule.html')

  expect(mutationRequests).toHaveLength(0)
})