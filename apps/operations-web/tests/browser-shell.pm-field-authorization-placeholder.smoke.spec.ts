import { expect, test } from '@playwright/test'

test('pm field authorization placeholder route renders no-live field authority guardrails', async ({ page }) => {
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  const response = await page.goto('/pm-review/field-authorization-placeholder', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Field authorization and assignment stay blocked as a placeholder branch/i })).toBeVisible()
  await expect(page.getByText(/field authorization and assignment can move forward only as placeholder taxonomy, guardrails, release-gate planning, and later admission preparation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Output Taxonomy/i })).toBeVisible()
  await expect(page.getByText('FIELD_AUTHORIZATION_DRAFT')).toBeVisible()
  await expect(page.getByText('FIELD_RELEASE_GATE_DRAFT')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Placeholder Guardrails/i })).toBeVisible()
  await expect(page.getByText(/No live POST, authorization, assignment, dispatch, or field release/i)).toBeVisible()
  await expect(page.getByText(/No reuse of import, approval, or field-prep context as live field authority/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Recommended Next Field Authorization Placeholder Work/i })).toBeVisible()
  await expect(page.getByText(/Separate field authorization planning from intake review, field-prep questions, and later schedule or status controls/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Separate Branches Still Held/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /Project overview/i })).toHaveAttribute('href', '/pm-review/project-overview')
  await expect(page.getByRole('link', { name: /Intake workbench/i })).toHaveAttribute('href', '/pm-review/import-intake')

  expect(mutationRequests).toHaveLength(0)
})