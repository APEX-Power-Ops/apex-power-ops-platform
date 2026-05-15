import { expect, test } from '@playwright/test'

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
          ready_count: 1,
          in_progress_count: 0,
          pm_review_count: 0,
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
            task_id: 'task-002',
            blocker_count: 0,
            open_issue_count: 0,
            owner_name: null,
            workpackage_name: 'Primary Switchgear Testing',
            task_name: 'Switchgear Sweep',
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
            status: 'ready',
            readiness: 'ready',
            task_id: 'task-001',
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
            next_action: 'Start field work',
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

  const response = await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /PM workfront now has a governed read model/i })).toBeVisible()
  await expect(page.getByText(/not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toBeVisible()
  await expect(page.getByText(/SWBD-3/i)).toBeVisible()
  await expect(page.getByText(/SLD B-101/i)).toBeVisible()
  await expect(page.getByText(/Resolve blocker: IR reading below threshold/i).first()).toBeVisible()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()
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

  await page.getByRole('button', { name: /Draft lead follow-up/i }).first().click()
  await expect(page.getByText('AI advisory', { exact: true })).toBeVisible()
  await expect(page.getByText(/draft only .* not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Lead target .* issue-200/i)).toBeVisible()
  await expect(page.getByText(/Requested lead follow-up: Resolve blocker: IR reading below threshold/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /Needs PM disposition 1/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Stale blockers 1/i })).toBeVisible()
  await page.getByRole('button', { name: /View history/i }).click()
  const historyPanel = page.getByRole('region', { name: /Disposition history for Cable Assembly A/i })
  await expect(historyPanel.getByText(/This history panel is read-only/i)).toBeVisible()
  await expect(historyPanel.getByText(/No PM disposition recorded/i)).toBeVisible()
  expect(historyCalls).toBe(1)
  expect(historyRequests[0]).toEqual({ entityIds: ['issue-200'], limit: '25' })
  expect(mutationRequests).toHaveLength(0)

  await page.getByRole('button', { name: /Return to lead/i }).click()
  await expect(page.getByText(/PM returned this issue to lead review/i)).toBeVisible()
  await expect(page.getByText(/Returned to lead review/i)).toBeVisible()
  await expect(page.getByText(/Last PM disposition/i)).toBeVisible()
  await expect(page.getByText(/Last PM decision .* return to lead .* in_review/i)).toBeVisible()
  await expect(page.getByText(/PM reason: PM returned issue issue-200 to lead review/i)).toBeVisible()
  await page.getByRole('button', { name: /Refresh history/i }).click()
  await expect(historyPanel.getByText(/return to lead .* escalated -> in review/i)).toBeVisible()
  await expect(historyPanel.getByText(/2026-05-15T16:30:00Z .* pm/i)).toBeVisible()
  await expect(historyPanel.getByText(/Unrelated approval/i)).toHaveCount(0)

  expect(mutationRequests).toHaveLength(1)
  expect(historyCalls).toBe(2)
  expect(historyRequests[1]).toEqual({ entityIds: ['issue-200'], limit: '25' })
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
