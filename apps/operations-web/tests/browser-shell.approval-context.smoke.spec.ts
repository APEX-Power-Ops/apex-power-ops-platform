import { expect, test } from '@playwright/test'

async function mockApprovalReads(page: Parameters<typeof test>[1] extends never ? never : any, overrides?: {
  queue?: Record<string, unknown>
  apparatus?: Array<Record<string, unknown>>
  tasks?: Array<Record<string, unknown>>
  workpackages?: Array<Record<string, unknown>>
  snapshots?: Array<Record<string, unknown>>
  issues?: Array<Record<string, unknown>>
  decisionHistory?: Array<Record<string, unknown>>
}) {
  const queue = {
    tasks: [],
    workpackages: [],
    snapshots: [],
    escalated_issues: [],
    total_count: 0,
    ...overrides?.queue,
  }
  const apparatus = overrides?.apparatus ?? []
  const tasks = overrides?.tasks ?? []
  const workpackages = overrides?.workpackages ?? []
  const snapshots = overrides?.snapshots ?? []
  const issues = overrides?.issues ?? []
  const decisionHistory = overrides?.decisionHistory ?? []
  const historyRequests: Array<{ entityIds: string[]; limit: string | null }> = []

  await Promise.all([
    page.route('**/api/v1/reads/approval-queue', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(queue) })
    }),
    page.route('**/api/v1/reads/decision-history**', async (route: any) => {
      const url = new URL(route.request().url())
      historyRequests.push({
        entityIds: url.searchParams.getAll('entity_id'),
        limit: url.searchParams.get('limit'),
      })
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(decisionHistory) })
    }),
    page.route('**/api/v1/reads/apparatus', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(apparatus) })
    }),
    page.route('**/api/v1/reads/tasks', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(tasks) })
    }),
    page.route('**/api/v1/reads/workpackages', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(workpackages) })
    }),
    page.route('**/api/v1/reads/snapshots', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(snapshots) })
    }),
    page.route('**/api/v1/reads/issues', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(issues) })
    }),
    page.route('**/api/v1/reads/assignments', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/tracer?*', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/projects', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/projects/*/wbs', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/tasks-with-scope?*', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/relationships?*', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
    page.route('**/api/v1/schedule/sync-log?*', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    }),
  ])

  return { historyRequests }
}

function taskReviewFixture() {
  return {
    queue: {
      tasks: [
        {
          id: 'task-009',
          name: 'Relay Functional Test',
          workpackage_id: 'wp-009',
          project_id: 'proj-001',
          status: 'awaiting_review',
        },
      ],
      total_count: 1,
    },
    apparatus: [{ id: 'app-009', name: 'Protection Relay 9', task_id: 'task-009', status: 'complete', neta_standard: 'NETA ATS 7.9' }],
    tasks: [{ id: 'task-009', name: 'Relay Functional Test', workpackage_id: 'wp-009', status: 'awaiting_review' }],
    workpackages: [{ id: 'wp-009', name: 'Relay Commissioning' }],
    decisionHistory: [
      {
        entity_id: 'task-009',
        entity_type: 'task',
        action_type: 'reject',
        actor_id: 'pm-004',
        actor_role: 'pm',
        timestamp: '2026-05-03T17:45:00Z',
        from_state: { status: 'awaiting_review' },
        to_state: { status: 'active' },
        reason: 'Retest required before approval',
      },
    ],
  }
}

function workpackageReviewFixture() {
  return {
    queue: {
      workpackages: [
        {
          id: 'wp-017',
          name: 'Feeder Acceptance Package',
          project_id: 'proj-001',
          status: 'awaiting_review',
        },
      ],
      total_count: 1,
    },
    apparatus: [
      { id: 'app-017', name: 'Relay Bank A', task_id: 'task-017', status: 'complete', neta_standard: 'NETA ATS 7.10' },
      { id: 'app-018', name: 'Relay Bank B', task_id: 'task-018', status: 'complete', neta_standard: 'NETA ATS 7.10' },
    ],
    tasks: [
      { id: 'task-018', name: 'Completed WP Task', workpackage_id: 'wp-017', status: 'complete' },
      { id: 'task-017', name: 'Focused WP Task', workpackage_id: 'wp-017', status: 'active' },
    ],
    workpackages: [{ id: 'wp-017', name: 'Feeder Acceptance Package', project_id: 'proj-001', status: 'awaiting_review' }],
    decisionHistory: [
      {
        entity_id: 'wp-017',
        entity_type: 'workpackage',
        action_type: 'reject',
        actor_id: 'pm-005',
        actor_role: 'pm',
        timestamp: '2026-05-04T18:00:00Z',
        from_state: { status: 'awaiting_review' },
        to_state: { status: 'awaiting_review' },
        reason: 'WP needs focused task review',
      },
    ],
  }
}

async function assertApprovalDrillthroughReturn(
  page: Parameters<typeof test>[1] extends never ? never : any,
  startUrl: string,
  buttonName: RegExp,
  expectedUrl: RegExp,
  returnLinkName: RegExp,
  expectedHref: RegExp,
  additionalUrlExpectation?: RegExp,
) {
  const approvalResponse = await page.goto(startUrl, { waitUntil: 'networkidle' })
  expect(approvalResponse?.ok()).toBeTruthy()
  await page.getByRole('button', { name: buttonName }).click()
  await expect(page).toHaveURL(expectedUrl)
  if (additionalUrlExpectation) {
    await expect(page).toHaveURL(additionalUrlExpectation)
  }
  await expect(page.getByRole('link', { name: returnLinkName })).toHaveAttribute('href', expectedHref)
}

test('approval escalation deep link seeds tracer from the related task context', async ({ page }) => {
  const { historyRequests } = await mockApprovalReads(page, {
    queue: {
      escalated_issues: [
        {
          id: 'issue-001',
          apparatus_id: 'app-003',
          task_id: 'task-002',
          title: 'Insulation resistance out of range',
          severity: 'medium',
          status: 'escalated',
          blocks_completion: false,
          reported_by: 'tech-001',
        },
      ],
      total_count: 1,
    },
    apparatus: [{ id: 'app-003', name: '480V Switchgear A', task_id: 'task-002' }],
    tasks: [{ id: 'task-002', name: 'Switchgear IR Sweep', workpackage_id: 'wp-001', status: 'active' }],
    workpackages: [{ id: 'wp-001', name: 'Primary Switchgear Testing' }],
    issues: [
      {
        id: 'issue-001',
        apparatus_id: 'app-003',
        task_id: 'task-002',
        title: 'Insulation resistance out of range',
        severity: 'medium',
        status: 'escalated',
        blocks_completion: false,
        reported_by: 'tech-001',
      },
    ],
    decisionHistory: [
      {
        entity_id: 'issue-001',
        entity_type: 'issue',
        action_type: 'return_to_lead',
        actor_id: 'pm-002',
        actor_role: 'pm',
        timestamp: '2026-05-01T15:00:00Z',
        from_state: { status: 'escalated' },
        to_state: { status: 'in_review' },
        reason: 'Needs lead clarification',
      },
    ],
  })

  const approvalResponse = await page.goto('/pm-review/approval?screen=escalations&detailId=issue-001', { waitUntil: 'networkidle' })
  expect(approvalResponse?.ok()).toBeTruthy()
  await expect.poll(() => historyRequests.length).toBeGreaterThan(0)
  expect(historyRequests).toContainEqual({ entityIds: ['issue-001'], limit: '25' })
  expect(historyRequests.some((request) => request.entityIds.length === 0)).toBe(false)
  await expect(page.getByRole('heading', { name: /Escalation Queue/i })).toBeVisible()
  await expect(page.getByText(/Insulation resistance out of range/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /Resolve/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Schedule/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Drivers/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Variance/i })).toBeVisible()
  const escalationHistoryContext = page.getByTestId('approval-decision-history-context')
  await expect(escalationHistoryContext).toBeVisible()
  await expect(escalationHistoryContext.getByTestId('approval-decision-history-row')).toHaveCount(1)
  await expect(escalationHistoryContext).toContainText(/return to lead/i)
  await expect(escalationHistoryContext).toContainText(/pm-002 \(pm\)/i)
  await expect(escalationHistoryContext).toContainText(/Needs lead clarification/i)

  await page.locator('.nav-item', { hasText: 'Tracer' }).click()

  await expect(page).toHaveURL(/\/pm-review\/tracer\?[^#]*taskId=task-002/)
  await expect(page.getByText(/Current seed: Switchgear IR Sweep \(task-002\)/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Return to PM approval escalations/i })).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=escalations&detailId=issue-001&focusTaskId=task-002&taskLabel=Switchgear\+IR\+Sweep$/,
  )

  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=escalations&detailId=issue-001',
    /Open Schedule/i,
    /\/pm-review\/schedule\?[^#]*focusTaskId=task-002/,
    /Return to PM approval escalations/i,
    /\/pm-review\/approval\?screen=escalations&detailId=issue-001$/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=escalations&detailId=issue-001',
    /Open Drivers/i,
    /\/pm-review\?[^#]*focusTaskId=task-002/,
    /Return to PM approval escalations/i,
    /\/pm-review\/approval\?screen=escalations&detailId=issue-001$/,
    /[?&]projectId=stack-dc/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=escalations&detailId=issue-001',
    /Open Variance/i,
    /\/pm-review\/variance\?[^#]*focusTaskId=task-002/,
    /Return to PM approval escalations/i,
    /\/pm-review\/approval\?screen=escalations&detailId=issue-001$/,
    /[?&]projectId=stack-dc/,
  )
})

test('approval snapshot review uses derived task context for schedule handoff', async ({ page }) => {
  const { historyRequests } = await mockApprovalReads(page, {
    queue: {
      snapshots: [
        {
          id: 'snap-001',
          workpackage_id: 'wp-001',
          project_id: 'proj-001',
          period_start: '2026-04-01',
          period_end: '2026-04-15',
          status: 'submitted',
          percent_complete: 45,
          hours_reported: 120,
          submitted_by: 'lead-001',
        },
      ],
      total_count: 1,
    },
    tasks: [{ id: 'task-007', name: 'Switchgear Closeout', workpackage_id: 'wp-001', status: 'active' }],
    workpackages: [{ id: 'wp-001', name: 'Primary Switchgear Testing' }],
    snapshots: [
      {
        id: 'snap-001',
        workpackage_id: 'wp-001',
        project_id: 'proj-001',
        period_start: '2026-04-01',
        period_end: '2026-04-15',
        status: 'submitted',
        percent_complete: 45,
        hours_reported: 120,
        submitted_by: 'lead-001',
      },
    ],
    decisionHistory: [
      {
        entity_id: 'snap-001',
        entity_type: 'snapshot',
        action_type: 'approve',
        actor_id: 'pm-003',
        actor_role: 'pm',
        timestamp: '2026-05-02T16:30:00Z',
        from_state: { status: 'submitted' },
        to_state: { status: 'approved' },
        reason: 'Progress accepted for period',
      },
    ],
  })

  const approvalResponse = await page.goto('/pm-review/approval?screen=snapshot-review&detailId=snap-001', { waitUntil: 'networkidle' })
  expect(approvalResponse?.ok()).toBeTruthy()
  await expect.poll(() => historyRequests.length).toBeGreaterThan(0)
  expect(historyRequests).toContainEqual({ entityIds: ['snap-001'], limit: '25' })
  expect(historyRequests.some((request) => request.entityIds.length === 0)).toBe(false)
  await expect(page.getByRole('heading', { name: /Progress Snapshot/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Schedule/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Drivers/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Variance/i })).toBeVisible()
  const snapshotHistoryContext = page.getByTestId('approval-decision-history-context')
  await expect(snapshotHistoryContext).toBeVisible()
  await expect(snapshotHistoryContext.getByTestId('approval-decision-history-row')).toHaveCount(1)
  await expect(snapshotHistoryContext).toContainText(/approve/i)
  await expect(snapshotHistoryContext).toContainText(/pm-003 \(pm\)/i)
  await expect(snapshotHistoryContext).toContainText(/Progress accepted for period/i)

  await page.getByRole('button', { name: /Open Schedule/i }).click()

  await expect(page).toHaveURL(/\/pm-review\/schedule\?[^#]*focusTaskId=task-007/)
  await expect(page.getByRole('link', { name: /Return to PM snapshot review/i })).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=snapshot-review&detailId=snap-001$/,
  )

  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=snapshot-review&detailId=snap-001',
    /Open Drivers/i,
    /\/pm-review\?[^#]*focusTaskId=task-007/,
    /Return to PM snapshot review/i,
    /\/pm-review\/approval\?screen=snapshot-review&detailId=snap-001$/,
    /[?&]projectId=stack-dc/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=snapshot-review&detailId=snap-001',
    /Open Variance/i,
    /\/pm-review\/variance\?[^#]*focusTaskId=task-007/,
    /Return to PM snapshot review/i,
    /\/pm-review\/approval\?screen=snapshot-review&detailId=snap-001$/,
    /[?&]projectId=stack-dc/,
  )
})

test('approval task review exposes scoped history and task drillthrough', async ({ page }) => {
  const { historyRequests } = await mockApprovalReads(page, taskReviewFixture())

  const approvalResponse = await page.goto('/pm-review/approval?screen=task-review&detailId=task-009', { waitUntil: 'networkidle' })
  expect(approvalResponse?.ok()).toBeTruthy()
  await expect.poll(() => historyRequests.length).toBeGreaterThan(0)
  expect(historyRequests).toContainEqual({ entityIds: ['task-009'], limit: '25' })
  expect(historyRequests.some((request) => request.entityIds.length === 0)).toBe(false)
  await expect(page.getByRole('heading', { name: /Relay Functional Test/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: /Related Task Actions/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Trace Task/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Schedule/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Drivers/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Variance/i })).toBeVisible()

  const historyContext = page.getByTestId('approval-decision-history-context')
  await expect(historyContext).toBeVisible()
  await expect(historyContext.getByTestId('approval-decision-history-row')).toHaveCount(1)
  await expect(historyContext).toContainText(/reject/i)
  await expect(historyContext).toContainText(/pm-004 \(pm\)/i)
  await expect(historyContext).toContainText(/Retest required before approval/i)

  await page.getByRole('button', { name: /Trace Task/i }).click()

  await expect(page).toHaveURL(/\/pm-review\/tracer\?[^#]*taskId=task-009/)
  await expect(page.getByText(/Current seed: Relay Functional Test \(task-009\)/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Return to PM task review/i })).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=task-review&detailId=task-009&focusTaskId=task-009&taskLabel=Relay\+Functional\+Test$/,
  )

  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=task-review&detailId=task-009',
    /Open Schedule/i,
    /\/pm-review\/schedule\?[^#]*focusTaskId=task-009/,
    /Return to PM task review/i,
    /\/pm-review\/approval\?screen=task-review&detailId=task-009$/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=task-review&detailId=task-009',
    /Open Drivers/i,
    /\/pm-review\?[^#]*focusTaskId=task-009/,
    /Return to PM task review/i,
    /\/pm-review\/approval\?screen=task-review&detailId=task-009$/,
    /[?&]projectId=stack-dc/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=task-review&detailId=task-009',
    /Open Variance/i,
    /\/pm-review\/variance\?[^#]*focusTaskId=task-009/,
    /Return to PM task review/i,
    /\/pm-review\/approval\?screen=task-review&detailId=task-009$/,
    /[?&]projectId=stack-dc/,
  )
})

test('approval workpackage review uses focused task drillthrough', async ({ page }) => {
  const { historyRequests } = await mockApprovalReads(page, workpackageReviewFixture())

  const approvalResponse = await page.goto('/pm-review/approval?screen=wp-review&detailId=wp-017', { waitUntil: 'networkidle' })
  expect(approvalResponse?.ok()).toBeTruthy()
  await expect.poll(() => historyRequests.length).toBeGreaterThan(0)
  expect(historyRequests).toContainEqual({ entityIds: ['wp-017'], limit: '25' })
  expect(historyRequests.some((request) => request.entityIds.length === 0)).toBe(false)
  await expect(page.getByRole('heading', { name: /Feeder Acceptance Package/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: /Related Task Actions/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Trace Task/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Schedule/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Drivers/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Open Variance/i })).toBeVisible()

  const historyContext = page.getByTestId('approval-decision-history-context')
  await expect(historyContext).toBeVisible()
  await expect(historyContext.getByTestId('approval-decision-history-row')).toHaveCount(1)
  await expect(historyContext).toContainText(/reject/i)
  await expect(historyContext).toContainText(/pm-005 \(pm\)/i)
  await expect(historyContext).toContainText(/WP needs focused task review/i)

  await page.getByRole('button', { name: /Trace Task/i }).click()

  await expect(page).toHaveURL(/\/pm-review\/tracer\?[^#]*taskId=task-017/)
  await expect(page.getByText(/Current seed: Focused WP Task \(task-017\)/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Return to PM work package review/i })).toHaveAttribute(
    'href',
    /\/pm-review\/approval\?screen=wp-review&detailId=wp-017&focusTaskId=task-017&taskLabel=Focused\+WP\+Task$/,
  )

  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=wp-review&detailId=wp-017',
    /Open Schedule/i,
    /\/pm-review\/schedule\?[^#]*focusTaskId=task-017/,
    /Return to PM work package review/i,
    /\/pm-review\/approval\?screen=wp-review&detailId=wp-017$/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=wp-review&detailId=wp-017',
    /Open Drivers/i,
    /\/pm-review\?[^#]*focusTaskId=task-017/,
    /Return to PM work package review/i,
    /\/pm-review\/approval\?screen=wp-review&detailId=wp-017$/,
    /[?&]projectId=stack-dc/,
  )
  await assertApprovalDrillthroughReturn(
    page,
    '/pm-review/approval?screen=wp-review&detailId=wp-017',
    /Open Variance/i,
    /\/pm-review\/variance\?[^#]*focusTaskId=task-017/,
    /Return to PM work package review/i,
    /\/pm-review\/approval\?screen=wp-review&detailId=wp-017$/,
    /[?&]projectId=stack-dc/,
  )
})
