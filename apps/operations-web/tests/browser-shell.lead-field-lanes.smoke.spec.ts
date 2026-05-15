import { expect, test } from '@playwright/test'

type LaneFixture = {
  apparatus: Array<Record<string, unknown>>
  assignments: Array<Record<string, unknown>>
  tasks?: Array<Record<string, unknown>>
  workpackages?: Array<Record<string, unknown>>
  issues?: Array<Record<string, unknown>>
  crew?: Array<Record<string, unknown>>
  checklist?: Array<Record<string, unknown>>
  hours?: Array<Record<string, unknown>>
}

async function mockLeadFieldRoutes(page: Parameters<typeof test>[1] extends never ? never : any, fixture: LaneFixture) {
  const crew = fixture.crew ?? [
    { id: 'tech-001', name: 'Alex Rivera', role: 'field_tech' },
    { id: 'tech-002', name: 'Sam Chen', role: 'field_tech' },
  ]
  const tasks = fixture.tasks ?? []
  const workpackages = fixture.workpackages ?? []
  const issues = fixture.issues ?? []
  const checklist = fixture.checklist ?? []
  const hours = fixture.hours ?? []
  const projectPlan = {
    expanded_apparatus_candidates: fixture.apparatus.map((row) => ({
      display_name: row.name,
      designation: row.source_designation,
      apparatus_type: row.source_apparatus_type,
      drawing_ref: row.source_drawing_ref,
    })),
  }

  await Promise.all([
    page.route('**/api/v1/reads/apparatus', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(fixture.apparatus) })
    }),
    page.route('**/api/v1/reads/assignments', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(fixture.assignments) })
    }),
    page.route('**/api/v1/reads/tasks', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(tasks) })
    }),
    page.route('**/api/v1/reads/workpackages', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(workpackages) })
    }),
    page.route('**/api/v1/reads/issues', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(issues) })
    }),
    page.route('**/api/v1/reads/crew', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(crew) })
    }),
    page.route('**/api/v1/reads/project-apparatus-plan', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(projectPlan) })
    }),
    page.route('**/api/v1/reads/checklist/*', async (route: any) => {
      const apparatusId = route.request().url().split('/').pop()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(checklist.filter((item) => item.apparatus_id === apparatusId)),
      })
    }),
    page.route('**/api/v1/reads/hours', async (route: any) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(hours) })
    }),
    page.route('**/api/v1/mutations/assignments', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'accepted', entity_id: 'assign-200', action_type: 'assign' }),
      })
    }),
    page.route('**/api/v1/mutations/apparatus', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'accepted', entity_id: 'app-003', action_type: 'update_status' }),
      })
    }),
  ])
}

test('lead ops route renders apparatus assignment visibility with named crew roster', async ({ page }) => {
  await mockLeadFieldRoutes(page, {
    apparatus: [
      {
        id: 'app-002',
        name: 'Distribution Panel',
        task_id: 'task-001',
        neta_standard: 'MTS',
        status: 'ready',
        assigned_to: 'tech-001',
        source_designation: 'LVPP-2A',
        source_apparatus_type: 'Distribution Panel',
        source_drawing_ref: 'SLD A-201',
      },
      {
        id: 'app-003',
        name: 'Cable Assembly A',
        task_id: 'task-002',
        neta_standard: 'ATS',
        status: 'active',
        assigned_to: 'tech-001',
        source_designation: 'SWBD-3',
        source_apparatus_type: 'Switchgear - Medium Voltage',
        source_drawing_ref: 'SLD B-101',
      },
      { id: 'app-004', name: 'Main Switchgear', task_id: 'task-002', neta_standard: 'ATS', status: 'not_started', assigned_to: null },
    ],
    assignments: [
      { id: 'assign-001', apparatus_id: 'app-002', task_id: 'task-001', assigned_to: 'tech-001', assigned_by: 'lead-001' },
      { id: 'assign-002', apparatus_id: 'app-003', task_id: 'task-002', assigned_to: 'tech-001', assigned_by: 'lead-001' },
    ],
    tasks: [
      { id: 'task-001', name: 'Primary Intake Test', workpackage_id: 'wp-001' },
      { id: 'task-002', name: 'Switchgear Sweep', workpackage_id: 'wp-001' },
    ],
    workpackages: [{ id: 'wp-001', name: 'Primary Switchgear Testing', status: 'active' }],
    issues: [
      { id: 'issue-001', title: 'IR reading below threshold', severity: 'high', status: 'open', blocks_completion: true, apparatus_id: 'app-003' },
    ],
  })

  const response = await page.goto('/lead-ops', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /Lead apparatus assignments now have a real app route/i })).toBeVisible()
  await expect(page.getByText(/Alex Rivera/i).first()).toBeVisible()
  await expect(page.getByText(/Primary Switchgear Testing/i)).toBeVisible()
  await expect(page.getByText(/Cable Assembly A/i)).toBeVisible()
  await expect(page.getByText(/SWBD-3/i)).toBeVisible()
  await expect(page.getByText(/SLD B-101/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Assign', exact: true })).toBeVisible()
})

test('field tech route renders assigned apparatus and accepts a status transition', async ({ page }) => {
  await mockLeadFieldRoutes(page, {
    apparatus: [
      {
        id: 'app-002',
        name: 'Distribution Panel',
        task_id: 'task-001',
        neta_standard: 'MTS',
        status: 'ready',
        assigned_to: 'tech-001',
        source_designation: 'LVPP-2A',
        source_apparatus_type: 'Distribution Panel',
        source_drawing_ref: 'SLD A-201',
      },
      { id: 'app-003', name: 'Cable Assembly A', task_id: 'task-002', neta_standard: 'ATS', status: 'active', assigned_to: 'tech-001' },
    ],
    assignments: [
      { id: 'assign-001', apparatus_id: 'app-002', task_id: 'task-001', assigned_to: 'tech-001' },
      { id: 'assign-002', apparatus_id: 'app-003', task_id: 'task-002', assigned_to: 'tech-001' },
    ],
    issues: [
      { id: 'issue-001', title: 'Cable insulation check pending', severity: 'medium', status: 'open', apparatus_id: 'app-003' },
    ],
    checklist: [
      { id: 'check-001', apparatus_id: 'app-002', name: 'Visual inspection', completed: true },
      { id: 'check-002', apparatus_id: 'app-002', name: 'Torque verification', completed: false },
    ],
    hours: [{ id: 'hours-001', apparatus_id: 'app-002', hours: 1.5 }],
  })

  const response = await page.goto('/field-tech', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /Field technician completion now has a real app route/i })).toBeVisible()
  const distributionPanelCard = page.getByRole('button', { name: /Distribution Panel/i })
  await expect(distributionPanelCard).toBeVisible()
  await expect(page.getByLabel(/Technician selector/i)).toHaveValue('tech-001')
  await expect(distributionPanelCard).toContainText('LVPP-2A')
  await expect(distributionPanelCard).toContainText('SLD A-201')

  await page.getByRole('button', { name: /Mark active/i }).click()
  await expect(page.getByText(/Status updated to active\./i)).toBeVisible()
})