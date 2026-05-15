import { expect, test } from '@playwright/test'

async function assertWorkfrontDrillthroughReturn(
  page: Parameters<typeof test>[1] extends never ? never : any,
  rowName: string,
  linkName: string,
  expectedUrl: RegExp,
  additionalUrlExpectation?: RegExp,
  absentUrlExpectations: RegExp[] = [],
) {
  const workfrontResponse = await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  expect(workfrontResponse?.ok()).toBeTruthy()
  const scheduleDrillthrough = page.locator(`[aria-label="Schedule drillthrough for ${rowName}"]`)
  await scheduleDrillthrough.getByRole('link', { name: linkName }).click()
  await expect(page).toHaveURL(expectedUrl)
  if (additionalUrlExpectation) {
    await expect(page).toHaveURL(additionalUrlExpectation)
  }
  for (const absentUrlExpectation of absentUrlExpectations) {
    expect(page.url()).not.toMatch(absentUrlExpectation)
  }
  const returnLink = page.getByRole('link', { name: /Return to PM workfront/i })
  await expect(returnLink).toHaveAttribute('href', /\/pm-review\/workfront$/)
  await returnLink.click()
  await expect(page).toHaveURL(/\/pm-review\/workfront$/)
}

test('pm workfront route renders read-only readiness queue from governed seam', async ({ page }) => {
  let readCalls = 0
  let historyCalls = 0
  const historyRequests: Array<{ entityIds: string[]; limit: string | null }> = []
  let returnedToLead = false
  const mutationRequests: Array<{ authorization?: string; body: any }> = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push({
      authorization: route.request().headers().authorization,
      body: route.request().postDataJSON(),
    })
    returnedToLead = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'accepted',
        entity_id: 'issue-200',
        entity_type: 'issue',
        action_type: 'return_to_lead',
        new_state: {
          id: 'issue-200',
          status: 'in_review',
          pm_disposition: 'return_to_lead',
          pm_followup_note: 'Cable Assembly A lead follow-up',
        },
      }),
    })
  })

  await page.route('**/api/v1/reads/pm-workfront', async (route) => {
    readCalls += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        summary: {
          total_count: 3,
          blocked_count: 1,
          unassigned_count: 1,
          ready_count: 0,
          in_progress_count: 0,
          pm_review_count: 1,
          complete_count: 0,
        },
        advisory: {
          mode: 'read_only',
          ai_mutation_authority: 'not_admitted',
          recommended_focus: 'Resolve blocker: IR reading below threshold',
        },
        lenses: {
          all_count: 3,
          blocked_count: 1,
          needs_pm_disposition_count: returnedToLead ? 0 : 1,
          returned_to_lead_count: returnedToLead ? 1 : 0,
          stale_blocker_count: returnedToLead ? 0 : 1,
          unassigned_count: 1,
        },
        rows: [
          {
            id: 'workfront-app-003',
            apparatus_id: 'app-003',
            apparatus_name: 'Cable Assembly A',
            status: 'active',
            readiness: 'blocked',
            task_id: 'task-002',
            workpackage_id: 'wp-001',
            blocker_count: 1,
            open_issue_count: 1,
            owner_name: 'Alex Rivera',
            workpackage_name: 'Primary Switchgear Testing',
            task_name: 'Switchgear Sweep',
            designation: 'SWBD-3',
            apparatus_type: 'Switchgear - Medium Voltage',
            drawing_ref: 'SLD B-101',
            checklist_complete_count: 1,
            checklist_total_count: 3,
            next_action: 'Resolve blocker: IR reading below threshold',
            primary_blocking_issue_id: 'issue-200',
            returnable_issue_id: returnedToLead ? null : 'issue-200',
            lens_tags: returnedToLead ? ['all', 'blocked', 'returned_to_lead'] : ['all', 'blocked', 'needs_pm_disposition', 'stale_blocker'],
            latest_pm_followup_note: returnedToLead ? 'Cable Assembly A is blocked for Primary Switchgear Testing / Switchgear Sweep; owner Alex Rivera; reference SLD B-101.' : null,
            latest_pm_followup_sent_at: returnedToLead ? '2026-05-15T16:30:00Z' : null,
            last_pm_decision: returnedToLead
              ? {
                  action_type: 'return_to_lead',
                  actor_id: 'pm-001',
                  actor_role: 'pm',
                  entity_id: 'issue-200',
                  reason: 'PM returned issue issue-200 to lead review',
                  timestamp: '2026-05-15T16:30:00Z',
                  from_status: 'escalated',
                  to_status: 'in_review',
                }
              : null,
            blocking_issues: [
              {
                id: 'issue-200',
                title: 'IR reading below threshold',
                status: returnedToLead ? 'in_review' : 'escalated',
                severity: 'high',
                blocks_completion: true,
                reported_by: 'tech-001',
                pm_followup_note: returnedToLead ? 'Cable Assembly A is blocked for Primary Switchgear Testing / Switchgear Sweep; owner Alex Rivera; reference SLD B-101.' : null,
                pm_followup_sent_at: returnedToLead ? '2026-05-15T16:30:00Z' : null,
              },
            ],
            ai_advisory: {
              mode: 'draft_only',
              mutation_authority: 'not_admitted',
              target_audience: 'lead',
              brief: 'Cable Assembly A is blocked for Primary Switchgear Testing / Switchgear Sweep; owner Alex Rivera; reference SLD B-101. Blocking issue: IR reading below threshold. Checklist 1/3. Requested lead follow-up: Resolve blocker: IR reading below threshold.',
            },
          },
          {
            id: 'workfront-app-004',
            apparatus_id: 'app-004',
            apparatus_name: 'Main Switchgear',
            status: 'not_started',
            readiness: 'unassigned',
            task_id: null,
            blocker_count: 0,
            open_issue_count: 0,
            owner_name: null,
            workpackage_name: 'Primary Switchgear Testing',
            task_name: null,
            designation: 'MVS-4',
            apparatus_type: 'Switchgear - Medium Voltage',
            drawing_ref: 'SLD B-102',
            checklist_complete_count: 0,
            checklist_total_count: 3,
            next_action: 'Assign owner',
          },
          {
            id: 'workfront-app-002',
            apparatus_id: 'app-002',
            apparatus_name: 'Distribution Panel',
            status: 'awaiting_review',
            readiness: 'pm_review',
            task_id: 'task-001',
            workpackage_id: 'wp-001',
            blocker_count: 0,
            open_issue_count: 0,
            owner_name: 'Alex Rivera',
            workpackage_name: 'Primary Switchgear Testing',
            task_name: 'Primary Intake Test',
            designation: 'LVPP-2A',
            apparatus_type: 'Distribution Panel',
            drawing_ref: 'SLD A-201',
            checklist_complete_count: 0,
            checklist_total_count: 3,
            next_action: 'Review task completion',
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/reads/decision-history**', async (route) => {
    historyCalls += 1
    const url = new URL(route.request().url())
    historyRequests.push({
      entityIds: url.searchParams.getAll('entity_id'),
      limit: url.searchParams.get('limit'),
    })
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(
        returnedToLead
          ? [
              {
                id: 'audit-return-200',
                mutation_id: 'mutation-return-200',
                actor_id: 'pm-001',
                actor_role: 'pm',
                action_type: 'return_to_lead',
                entity_id: 'issue-200',
                reason: 'PM returned issue issue-200 to lead review',
                timestamp: '2026-05-15T16:30:00Z',
                from_state: { status: 'escalated' },
                to_state: { status: 'in_review' },
              },
              {
                id: 'audit-unrelated',
                mutation_id: 'mutation-unrelated',
                actor_id: 'pm-001',
                actor_role: 'pm',
                action_type: 'approve',
                entity_id: 'issue-999',
                reason: 'Unrelated approval',
                timestamp: '2026-05-15T16:00:00Z',
                from_state: { status: 'awaiting_review' },
                to_state: { status: 'complete' },
              },
            ]
          : [],
      ),
    })
  })

  await Promise.all([
    page.route('**/api/v1/reads/approval-queue', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          escalated_issues: [
            {
              id: 'issue-200',
              apparatus_id: 'app-003',
              task_id: 'task-002',
              title: 'IR reading below threshold',
              severity: 'high',
              status: 'escalated',
              blocks_completion: true,
              reported_by: 'tech-001',
            },
          ],
          tasks: [
            {
              id: 'task-001',
              name: 'Primary Intake Test',
              workpackage_id: 'wp-001',
              project_id: 'stack-dc',
              status: 'awaiting_review',
            },
          ],
          workpackages: [],
          snapshots: [],
          total_count: 2,
        }),
      })
    }),
    page.route('**/api/v1/reads/apparatus', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'app-002', name: 'Distribution Panel', task_id: 'task-001', status: 'complete' },
          { id: 'app-003', name: 'Cable Assembly A', task_id: 'task-002' },
        ]),
      })
    }),
    page.route('**/api/v1/reads/tasks', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'task-001', name: 'Primary Intake Test', workpackage_id: 'wp-001', status: 'awaiting_review' },
          { id: 'task-002', name: 'Switchgear Sweep', workpackage_id: 'wp-001', status: 'active' },
        ]),
      })
    }),
    page.route('**/api/v1/reads/workpackages', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 'wp-001', name: 'Primary Switchgear Testing' }]),
      })
    }),
    page.route('**/api/v1/reads/snapshots', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/reads/issues', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'issue-200',
            apparatus_id: 'app-003',
            task_id: 'task-002',
            title: 'IR reading below threshold',
            severity: 'high',
            status: 'escalated',
            blocks_completion: true,
            reported_by: 'tech-001',
          },
        ]),
      })
    }),
    page.route('**/api/v1/reads/assignments', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
  ])

  await page.route('**/api/v1/schedule/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    let body: Array<Record<string, unknown>> = []
    if (path.endsWith('/projects')) {
      body = [{ id: 'stack-dc', name: 'Stack Data Center', data_date: '2026-05-15' }]
    } else if (path.includes('/tasks-with-scope')) {
      body = [
        {
          id: 'task-002',
          task_id: 'task-002',
          task_code: 'SWG-002',
          name: 'Switchgear Sweep',
          project_id: 'stack-dc',
          start: '2026-05-15T08:00:00Z',
          finish: '2026-05-16T17:00:00Z',
        },
      ]
    } else if (path.includes('/drivers')) {
      body = [
        {
          driver_task_id: 'task-001',
          driver_task_code: 'PRI-001',
          driven_task_id: 'task-002',
          driven_task_code: 'SWG-002',
          driven_critical_flag: true,
          rel_type: 'FS',
        },
      ]
    } else if (path.includes('/tracer')) {
      body = [
        {
          depth: 1,
          predecessor_task_id: 'task-001',
          predecessor_task_code: 'PRI-001',
          successor_task_id: 'task-002',
          successor_task_code: 'SWG-002',
          rel_type: 'FS',
        },
      ]
    } else if (path.includes('/variance')) {
      body = [
        {
          task_id: 'task-002',
          task_code: 'SWG-002',
          name: 'Switchgear Sweep',
          project_id: 'stack-dc',
          start_variance_hours: 0,
          finish_variance_hours: 8,
          duration_variance_hours: 8,
        },
      ]
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })

  const response = await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /PM workfront now has a governed read model/i })).toBeVisible()
  await expect(page.getByText(/not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toBeVisible()
  await expect(page.getByText(/SWBD-3/i)).toBeVisible()
  await expect(page.getByText(/SLD B-101/i)).toBeVisible()
  await expect(page.getByText(/Resolve blocker: IR reading below threshold/i).first()).toBeVisible()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()
  const escalationReviewLink = page.getByRole('link', { name: /Review escalation/i })
  await expect(escalationReviewLink).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=escalations&detailId=issue-200&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  const taskReviewLink = page.getByRole('link', { name: /Review task/i })
  await expect(taskReviewLink).toHaveCount(1)
  await expect(taskReviewLink).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=task-review&detailId=task-001&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  const packageReviewLink = page.getByRole('link', { name: /Review package/i })
  await expect(packageReviewLink).toHaveCount(1)
  await expect(packageReviewLink).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=wp-review&detailId=wp-001&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  const decisionHistoryLink = page.getByRole('link', { name: /Review history/i })
  await expect(decisionHistoryLink).toHaveCount(1)
  await expect(decisionHistoryLink).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=history&historySearch=issue-200&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  const cableScheduleDrillthrough = page.locator('[aria-label="Schedule drillthrough for Cable Assembly A"]')
  await expect(cableScheduleDrillthrough.getByRole('link', { name: 'Drivers' })).toHaveAttribute(
    'href',
    /\/pm-review\?focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  await expect(cableScheduleDrillthrough.getByRole('link', { name: 'Schedule' })).toHaveAttribute(
    'href',
    /\/pm-review\/schedule\?focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  await expect(cableScheduleDrillthrough.getByRole('link', { name: 'Trace' })).toHaveAttribute(
    'href',
    /\/pm-review\/tracer\?taskId=task-002&taskLabel=Switchgear\+Sweep&maxDepth=10&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  await expect(cableScheduleDrillthrough.getByRole('link', { name: 'Variance' })).toHaveAttribute(
    'href',
    /\/pm-review\/variance\?projectId=stack-dc&focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/,
  )
  const mainScheduleDrillthrough = page.locator('[aria-label="Schedule drillthrough for Main Switchgear"]')
  const mainDriversHref = await mainScheduleDrillthrough.getByRole('link', { name: 'Drivers' }).getAttribute('href')
  expect(mainDriversHref || '').toMatch(/\/pm-review\?returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/)
  expect(mainDriversHref || '').not.toContain('focusTaskId')
  expect(mainDriversHref || '').not.toContain('undefined')
  const mainScheduleHref = await mainScheduleDrillthrough.getByRole('link', { name: 'Schedule' }).getAttribute('href')
  expect(mainScheduleHref || '').toMatch(/\/pm-review\/schedule\?returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/)
  expect(mainScheduleHref || '').not.toContain('focusTaskId')
  expect(mainScheduleHref || '').not.toContain('undefined')
  const mainTraceHref = await mainScheduleDrillthrough.getByRole('link', { name: 'Trace' }).getAttribute('href')
  expect(mainTraceHref || '').toMatch(/\/pm-review\/tracer\?taskLabel=Main\+Switchgear&maxDepth=10&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/)
  expect(mainTraceHref || '').not.toContain('taskId')
  expect(mainTraceHref || '').not.toContain('undefined')
  const mainVarianceHref = await mainScheduleDrillthrough.getByRole('link', { name: 'Variance' }).getAttribute('href')
  expect(mainVarianceHref || '').toMatch(/\/pm-review\/variance\?projectId=stack-dc&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM\+workfront$/)
  expect(mainVarianceHref || '').not.toContain('focusTaskId')
  expect(mainVarianceHref || '').not.toContain('undefined')

  await assertWorkfrontDrillthroughReturn(page, 'Cable Assembly A', 'Drivers', /\/pm-review\?[^#]*focusTaskId=task-002/)
  await assertWorkfrontDrillthroughReturn(page, 'Cable Assembly A', 'Schedule', /\/pm-review\/schedule\?[^#]*focusTaskId=task-002/)
  await assertWorkfrontDrillthroughReturn(page, 'Cable Assembly A', 'Trace', /\/pm-review\/tracer\?[^#]*taskId=task-002/)
  await assertWorkfrontDrillthroughReturn(
    page,
    'Cable Assembly A',
    'Variance',
    /\/pm-review\/variance\?[^#]*focusTaskId=task-002/,
    /[?&]projectId=stack-dc/,
  )
  await assertWorkfrontDrillthroughReturn(
    page,
    'Main Switchgear',
    'Drivers',
    /\/pm-review\?[^#]*returnTo=%2Fpm-review%2Fworkfront/,
    undefined,
    [/[?&]focusTaskId=/],
  )
  await assertWorkfrontDrillthroughReturn(
    page,
    'Main Switchgear',
    'Schedule',
    /\/pm-review\/schedule\?[^#]*returnTo=%2Fpm-review%2Fworkfront/,
    undefined,
    [/[?&]focusTaskId=/],
  )
  await assertWorkfrontDrillthroughReturn(
    page,
    'Main Switchgear',
    'Trace',
    /\/pm-review\/tracer\?[^#]*taskLabel=Main\+Switchgear/,
    undefined,
    [/[?&]taskId=/],
  )
  await assertWorkfrontDrillthroughReturn(
    page,
    'Main Switchgear',
    'Variance',
    /\/pm-review\/variance\?[^#]*projectId=stack-dc/,
    undefined,
    [/[?&]focusTaskId=/],
  )
  expect(mutationRequests).toHaveLength(0)

  await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  const historyRequestsBeforeApprovalHistory = historyRequests.length
  await page.getByRole('link', { name: /Review history/i }).click()
  await expect(page).toHaveURL(/\/pm-review\/approval\?[^#]*screen=history/)
  await expect(page).toHaveURL(/[?&]historySearch=issue-200/)
  await expect(page.getByRole('heading', { name: /Decision History/i })).toBeVisible()
  await expect(page.getByRole('textbox', { name: /Decision history search/i })).toHaveValue('issue-200')
  const historyReturnLink = page.getByRole('link', { name: /Return to PM workfront/i })
  await expect(historyReturnLink).toHaveAttribute('href', /\/pm-review\/workfront$/)
  expect(historyRequests.length).toBeGreaterThan(historyRequestsBeforeApprovalHistory)
  expect(historyRequests.at(-1)).toEqual({ entityIds: [], limit: null })
  await historyReturnLink.click()
  await expect(page).toHaveURL(/\/pm-review\/workfront$/)
  expect(mutationRequests).toHaveLength(0)

  await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  await page.getByRole('link', { name: /Review package/i }).click()
  await expect(page).toHaveURL(/\/pm-review\/approval\?[^#]*screen=wp-review/)
  await expect(page).toHaveURL(/[?&]detailId=wp-001/)
  await expect(page.getByRole('heading', { name: /Primary Switchgear Testing/i })).toBeVisible()
  const packageReturnLink = page.getByRole('link', { name: /Return to PM workfront/i })
  await expect(packageReturnLink).toHaveAttribute('href', /\/pm-review\/workfront$/)
  await packageReturnLink.click()
  await expect(page).toHaveURL(/\/pm-review\/workfront$/)
  expect(historyRequests).toContainEqual({ entityIds: ['wp-001'], limit: '25' })
  expect(mutationRequests).toHaveLength(0)

  await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  await page.getByRole('link', { name: /Review task/i }).click()
  await expect(page).toHaveURL(/\/pm-review\/approval\?[^#]*screen=task-review/)
  await expect(page).toHaveURL(/[?&]detailId=task-001/)
  await expect(page.getByRole('heading', { name: /Primary Intake Test/i })).toBeVisible()
  const taskReturnLink = page.getByRole('link', { name: /Return to PM workfront/i })
  await expect(taskReturnLink).toHaveAttribute('href', /\/pm-review\/workfront$/)
  await taskReturnLink.click()
  await expect(page).toHaveURL(/\/pm-review\/workfront$/)
  expect(mutationRequests).toHaveLength(0)

  await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  await page.getByRole('link', { name: /Review escalation/i }).click()
  await expect(page).toHaveURL(/\/pm-review\/approval\?[^#]*screen=escalations/)
  await expect(page).toHaveURL(/[?&]detailId=issue-200/)
  await expect(page.getByRole('heading', { name: /Escalation Queue/i })).toBeVisible()
  await expect(page.getByText(/IR reading below threshold/i)).toBeVisible()
  const approvalReturnLink = page.getByRole('link', { name: /Return to PM workfront/i })
  await expect(approvalReturnLink).toHaveAttribute('href', /\/pm-review\/workfront$/)
  await approvalReturnLink.click()
  await expect(page).toHaveURL(/\/pm-review\/workfront$/)
  expect(mutationRequests).toHaveLength(0)

  await page.getByRole('button', { name: /Draft lead follow-up/i }).first().click()
  await expect(page.getByText('AI advisory', { exact: true })).toBeVisible()
  await expect(page.getByText(/draft only .* not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Lead target .* issue-200/i)).toBeVisible()
  await expect(page.getByText(/Requested lead follow-up: Resolve blocker: IR reading below threshold/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /Needs PM disposition 1/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Stale blockers 1/i })).toBeVisible()
  const historyCallsBeforeWorkfrontHistory = historyCalls
  await page.getByRole('button', { name: /View history/i }).click()
  const historyPanel = page.getByRole('region', { name: /Disposition history for Cable Assembly A/i })
  await expect(historyPanel.getByText(/This history panel is read-only/i)).toBeVisible()
  await expect(historyPanel.getByText(/No PM disposition recorded/i)).toBeVisible()
  expect(historyCalls).toBe(historyCallsBeforeWorkfrontHistory + 1)
  expect(historyRequests.at(-1)).toEqual({ entityIds: ['issue-200'], limit: '25' })
  expect(mutationRequests).toHaveLength(0)

  await page.getByRole('button', { name: /Return to lead/i }).click()
  await expect(page.getByText(/PM returned this issue to lead review/i)).toBeVisible()
  await expect(page.getByText(/Returned to lead review/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Review escalation/i })).toHaveCount(0)
  await expect(page.getByText(/Last PM disposition/i)).toBeVisible()
  await expect(page.getByText(/Last PM decision .* return to lead .* in_review/i)).toBeVisible()
  await expect(page.getByText(/PM reason: PM returned issue issue-200 to lead review/i)).toBeVisible()
  await page.getByRole('button', { name: /Refresh history/i }).click()
  await expect(historyPanel.getByText(/return to lead .* escalated -> in review/i)).toBeVisible()
  await expect(historyPanel.getByText(/2026-05-15T16:30:00Z .* pm/i)).toBeVisible()
  await expect(historyPanel.getByText(/Unrelated approval/i)).toHaveCount(0)

  expect(mutationRequests).toHaveLength(1)
  expect(historyCalls).toBe(historyCallsBeforeWorkfrontHistory + 2)
  expect(historyRequests.at(-1)).toEqual({ entityIds: ['issue-200'], limit: '25' })
  const mutation = mutationRequests[0]
  const tokenPayload = JSON.parse(Buffer.from((mutation.authorization || '').replace(/^Bearer /, ''), 'base64').toString('utf8'))
  expect(tokenPayload.actor_role).toBe('pm')
  expect(mutation.body.idempotency_key).toBeTruthy()
  expect(Number.isNaN(Date.parse(mutation.body.client_timestamp))).toBeFalsy()
  expect(mutation.body).toMatchObject({
    mutation_class: 'C',
    action_type: 'return_to_lead',
    entity_id: 'issue-200',
    payload: {
      status: 'in_review',
      pm_disposition: 'return_to_lead',
      pm_followup_workfront_row_id: 'workfront-app-003',
      pm_followup_source: 'pm_workfront',
    },
    reason: 'PM returned issue issue-200 to lead review',
    source: 'online',
  })
  expect(mutation.body.payload.pm_followup_note).toContain('Cable Assembly A is blocked')
  expect(readCalls).toBeGreaterThanOrEqual(2)

  await page.getByRole('button', { name: /Returned to lead 1/i }).click()
  await expect(page.getByText('Cable Assembly A', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /Stale blockers 0/i }).click()
  await expect(page.getByText(/No rows match this read-only lens/i)).toBeVisible()

  await page.getByRole('button', { name: /Unassigned 1/i }).click()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toHaveCount(0)
})
