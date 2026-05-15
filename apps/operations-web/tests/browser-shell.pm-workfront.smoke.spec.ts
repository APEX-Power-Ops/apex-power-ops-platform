import { expect, test } from '@playwright/test'

test('pm workfront route renders read-only readiness queue from governed seam', async ({ page }) => {
  let readCalls = 0
  const mutationRequests: Array<{ authorization?: string; body: any }> = []

  await page.route('**/api/v1/mutations/issues', async (route) => {
    mutationRequests.push({
      authorization: route.request().headers().authorization,
      body: route.request().postDataJSON(),
    })
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
        rows: [
          {
            id: 'workfront-app-003',
            apparatus_id: 'app-003',
            apparatus_name: 'Cable Assembly A',
            status: 'active',
            readiness: 'blocked',
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
            returnable_issue_id: 'issue-200',
            blocking_issues: [
              {
                id: 'issue-200',
                title: 'IR reading below threshold',
                status: 'escalated',
                severity: 'high',
                blocks_completion: true,
                reported_by: 'tech-001',
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

  const response = await page.goto('/pm-review/workfront', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /PM workfront now has a governed read model/i })).toBeVisible()
  await expect(page.getByText(/not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toBeVisible()
  await expect(page.getByText(/SWBD-3/i)).toBeVisible()
  await expect(page.getByText(/SLD B-101/i)).toBeVisible()
  await expect(page.getByText(/Resolve blocker: IR reading below threshold/i).first()).toBeVisible()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()

  await page.getByRole('button', { name: /Draft lead follow-up/i }).first().click()
  await expect(page.getByText('AI advisory', { exact: true })).toBeVisible()
  await expect(page.getByText(/draft only .* not_admitted/i)).toBeVisible()
  await expect(page.getByText(/Lead target .* issue-200/i)).toBeVisible()
  await expect(page.getByText(/Requested lead follow-up: Resolve blocker: IR reading below threshold/i)).toBeVisible()
  expect(mutationRequests).toHaveLength(0)

  await page.getByRole('button', { name: /Return to lead/i }).click()
  await expect(page.getByText(/PM returned this issue to lead review/i)).toBeVisible()

  expect(mutationRequests).toHaveLength(1)
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

  await page.getByRole('button', { name: /Unassigned 1/i }).click()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toHaveCount(0)
})
