import { expect, test } from '@playwright/test'

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

  const pmScheduleResponse = await page.goto('/pm-review/schedule.html')
  expect(pmScheduleResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Schedule Review/)

  const pmTracerResponse = await page.goto('/pm-review/tracer.html')
  expect(pmTracerResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Upstream Tracer Review/)

  const pmVarianceResponse = await page.goto('/pm-review/variance.html')
  expect(pmVarianceResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Variance Review/)
})
