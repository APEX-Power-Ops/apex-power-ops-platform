import { expect, test } from '@playwright/test'

test('pm project overview surfaces planning-only task-plan baseline without widening authority', async ({ page }) => {
  const readCalls = {
    candidate: 0,
    admissionPlan: 0,
    approvalContract: 0,
    storagePlan: 0,
    approvalStatus: 0,
    taskPlanStatus: 0,
    workfront: 0,
    deliveryStatus: 0,
  }
  const mutationRequests: string[] = []
  const unexpectedReadRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  await page.route('**/api/v1/reads/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname

    if (path.endsWith('/project-import-candidate')) {
      readCalls.candidate += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          candidate_id: 'pm-import-candidate-miner-temp-power',
          mutation_authority: 'not_admitted',
          project: {
            name: 'Project Miner Temp Power',
            location: 'Phoenix, AZ',
            drawing_package: 'TMP-347 Rev B',
            source_sheet: 'Temp Power Survey',
          },
          summary: {
            workpackage_count: 1,
            task_count: 0,
            apparatus_candidate_count: 6,
            warning_count: 0,
            blocker_count: 0,
            human_decision_count: 0,
          },
          source_freshness: {
            aggregate_fingerprint: 'source-fp-347-current',
            missing_count: 0,
          },
          review_guidance: {
            primary_review_goal: 'Confirm the PM baseline stays planning-only until a later admitted packet widens authority.',
          },
        }),
      })
      return
    }

    if (path.endsWith('/project-import-admission-plan')) {
      readCalls.admissionPlan += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          readiness_status: 'design_only_review_current',
          mutation_authority: 'not_admitted',
          no_go_checks: [{ status: 'blocked' }],
        }),
      })
      return
    }

    if (path.endsWith('/project-import-approval-contract')) {
      readCalls.approvalContract += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          persistence_authority: 'not_admitted',
          mutation_authority: 'not_admitted',
        }),
      })
      return
    }

    if (path.endsWith('/project-import-approval-storage-plan')) {
      readCalls.storagePlan += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          persistence_authority: 'storage_decision_only_not_admitted',
          recommended_table: 'seam.pm_import_candidate_approvals',
          recommended_route: '/api/v1/mutations/project-import-approvals',
        }),
      })
      return
    }

    if (path.endsWith('/project-import-approval-status')) {
      readCalls.approvalStatus += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          approval_record_count_for_candidate: 0,
          import_authority: 'not_admitted',
        }),
      })
      return
    }

    if (path.endsWith('/project-import-task-plan-status')) {
      readCalls.taskPlanStatus += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          classification: 'no_task_plan_record',
          route: '/api/v1/reads/project-import-task-plan-status',
          task_plan_route: '/api/v1/mutations/project-import-task-plans',
          task_plan_authority: 'admitted_by_pm_lane_361_task_plan_persistence',
          current_candidate_match: false,
          planning_context_only: true,
          persisted_row_counts: {
            projects: 0,
            workpackages: 0,
            tasks: 0,
            apparatus: 0,
          },
        }),
      })
      return
    }

    if (path.endsWith('/pm-workfront')) {
      readCalls.workfront += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          summary: {
            total_count: 0,
            blocked_count: 0,
            unassigned_count: 0,
            ready_count: 0,
            in_progress_count: 0,
            pm_review_count: 0,
          },
          advisory: {
            recommended_focus: 'Keep the PM route in review-only mode.',
            ai_mutation_authority: 'not_admitted',
          },
        }),
      })
      return
    }

    if (path.endsWith('/temp-power-customer-delivery-event-status')) {
      readCalls.deliveryStatus += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'customer_delivery_event_recorded_current_match',
          latest_customer_delivery_event_id: 'temp-power-delivery-event-0001',
          latest_delivered_at_utc: '2026-05-18T23:45:00Z',
          finance_authority: 'not_admitted',
          source_writeback_authority: 'not_admitted',
          customer_billing_delivery_authority: 'not_admitted',
        }),
      })
      return
    }

    unexpectedReadRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: `unexpected read route: ${route.request().url()}` }),
    })
  })

  const response = await page.goto('/pm-review/project-overview', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: 'See the testing project top to bottom in one place.', exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Open import candidate', exact: true })).toHaveAttribute('href', '/pm-review/import-candidate')

  const summaryGrid = page.locator('.pm-project-overview-summary-grid')
  await expect(summaryGrid.getByRole('heading', { name: 'Task plan baseline', exact: true })).toBeVisible()
  await expect(summaryGrid.getByText('no task plan record', { exact: true })).toBeVisible()
  await expect(summaryGrid.getByText('No planning-only task baseline has been persisted for the current candidate yet.', { exact: true })).toBeVisible()

  const attentionList = page.locator('.pm-project-overview-attention-list')
  await expect(attentionList.getByRole('heading', { name: 'Refresh the durable task-plan baseline', exact: true })).toBeVisible()
  await expect(attentionList.getByText(/No planning-only task baseline exists yet; persist it from import candidate review/i)).toBeVisible()

  const stageList = page.locator('.pm-project-overview-stage-list')
  await expect(stageList.getByRole('heading', { name: 'Task plan baseline and approval gate', exact: true })).toBeVisible()
  await expect(stageList.getByText(/No planning-only task baseline has been persisted for the current candidate yet\. Approval persistence and project import are still intentionally blocked\./i)).toBeVisible()
  await expect(stageList.getByRole('link', { name: 'Open task shaping and candidate review', exact: true })).toHaveAttribute('href', '/pm-review/import-candidate')

  expect(readCalls).toEqual({
    candidate: 1,
    admissionPlan: 1,
    approvalContract: 1,
    storagePlan: 1,
    approvalStatus: 1,
    taskPlanStatus: 1,
    workfront: 1,
    deliveryStatus: 1,
  })
  expect(mutationRequests).toEqual([])
  expect(unexpectedReadRequests).toEqual([])
})