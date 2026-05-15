import { expect, test } from '@playwright/test'

test('pm workfront route renders read-only readiness queue from governed seam', async ({ page }) => {
  await page.route('**/api/v1/reads/pm-workfront', async (route) => {
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

  await page.getByRole('button', { name: /Unassigned 1/i }).click()
  await expect(page.getByText(/Main Switchgear/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toHaveCount(0)
})
