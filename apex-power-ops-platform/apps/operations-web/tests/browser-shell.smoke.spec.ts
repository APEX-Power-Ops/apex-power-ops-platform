import { expect, test } from '@playwright/test'

test('root shell renders and blocks invalid apparatus IDs before backend fetch', async ({
  page,
}) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'Operations Web now has a real frontend boundary.' }),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Validation Surface' })).toBeVisible()

  await page.getByLabel('Apparatus UUID').fill('invalid-id')
  await page.getByRole('button', { name: 'Load Resources' }).click()

  await expect(
    page.getByText('Enter a valid apparatus UUID to read the governed backend study-resource seam.'),
  ).toBeVisible()
})

test('re-homed browser surfaces render their expected headings in a real browser', async ({ page }) => {
  const integrationResponse = await page.goto('/integration-dashboard/index.html')
  expect(integrationResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Cross-Surface Integration Test Dashboard/)

  const leadResponse = await page.goto('/lead-ops/index.html')
  expect(leadResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Lead Surface/)

  const pmDriversResponse = await page.goto('/pm-review/index.html')
  expect(pmDriversResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Drivers Review/)

  const pmApprovalResponse = await page.goto('/pm-review/approval-surface.html')
  expect(pmApprovalResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Approval Surface/)
})