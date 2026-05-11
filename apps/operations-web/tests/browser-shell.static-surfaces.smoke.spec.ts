import { expect, test } from '@playwright/test'

test('re-homed browser surfaces render their expected headings in a real browser', async ({ page }) => {
  const integrationResponse = await page.goto('/integration-dashboard/index.html')
  expect(integrationResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Cross-Surface Integration Test Dashboard/)

  const leadResponse = await page.goto('/lead-ops/index.html')
  expect(leadResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Lead Surface/)

  const promotedPmDriversResponse = await page.goto('/pm-review')
  expect(promotedPmDriversResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM drivers now have a real app route/i })).toBeVisible()

  const promotedPmApprovalResponse = await page.goto('/pm-review/approval')
  expect(promotedPmApprovalResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM approval now has a real app route/i })).toBeVisible()

  const deepLinkedApprovalResponse = await page.goto('/pm-review/approval?screen=history')
  expect(deepLinkedApprovalResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /Decision History/i })).toBeVisible()

  const promotedPmScheduleResponse = await page.goto('/pm-review/schedule')
  expect(promotedPmScheduleResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM schedule now has a real app route/i })).toBeVisible()

  const returnLinkedScheduleResponse = await page.goto(
    '/pm-review/schedule?focusTaskId=stack-dc-task-007&returnTo=%2Fpm-review%2Fapproval%3Fscreen%3Dhistory&returnLabel=PM%20approval%20history',
  )
  expect(returnLinkedScheduleResponse?.ok()).toBeTruthy()
  const returnToApprovalLink = page.getByRole('link', { name: /Return to PM approval history/i })
  await expect(returnToApprovalLink).toBeVisible()
  await expect(returnToApprovalLink).toHaveAttribute('href', /\/pm-review\/approval\?screen=history$/)

  const promotedPmTracerResponse = await page.goto('/pm-review/tracer')
  expect(promotedPmTracerResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM tracer now has a real app route/i })).toBeVisible()

  const deepLinkedTracerResponse = await page.goto('/pm-review/tracer?taskId=stack-dc-task-042&taskLabel=Deep%20Link%20Seed&maxDepth=7')
  expect(deepLinkedTracerResponse?.ok()).toBeTruthy()
  await expect(page.getByText(/Current seed: Deep Link Seed \(stack-dc-task-042\)/i)).toBeVisible()

  const returnSeedTracerResponse = await page.goto(
    '/pm-review/tracer?returnTo=%2Fpm-review%2Fschedule%3FfocusTaskId%3Dstack-dc-task-007&returnLabel=PM%20schedule%20route',
  )
  expect(returnSeedTracerResponse?.ok()).toBeTruthy()
  await expect(page.getByText(/Current seed: Focused task stack-dc-task-007 \(stack-dc-task-007\)/i)).toBeVisible()
  const returnToScheduleLink = page.getByRole('link', { name: /Return to PM schedule route/i })
  await expect(returnToScheduleLink).toBeVisible()
  await expect(returnToScheduleLink).toHaveAttribute('href', /\/pm-review\/schedule\?focusTaskId=stack-dc-task-007$/)

  const approvalSeedTracerResponse = await page.goto(
    '/pm-review/tracer?returnTo=%2Fpm-review%2Fapproval%3Fscreen%3Dtask-review%26detailId%3Dstack-dc-task-042%26focusTaskId%3Dstack-dc-task-042%26taskLabel%3Dapproval-task-042&returnLabel=PM%20task%20review',
  )
  expect(approvalSeedTracerResponse?.ok()).toBeTruthy()
  await expect(page.getByText(/Current seed: approval-task-042 \(stack-dc-task-042\)/i)).toBeVisible()
  const returnToApprovalTaskLink = page.getByRole('link', { name: /Return to PM task review/i })
  await expect(returnToApprovalTaskLink).toBeVisible()
  await expect(returnToApprovalTaskLink).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=task-review&detailId=stack-dc-task-042&focusTaskId=stack-dc-task-042&taskLabel=approval-task-042$/,
  )

  const promotedPmVarianceResponse = await page.goto('/pm-review/variance')
  expect(promotedPmVarianceResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM variance now has a real app route/i })).toBeVisible()

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
