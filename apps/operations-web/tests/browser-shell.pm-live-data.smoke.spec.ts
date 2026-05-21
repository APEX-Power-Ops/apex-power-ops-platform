import { expect, test, type APIRequestContext } from '@playwright/test'

const pmLiveDataSmokeEnabled = process.env.OPERATIONS_WEB_ENABLE_PM_LIVE_DATA_SMOKE === '1'

test.skip(
  !pmLiveDataSmokeEnabled,
  'PM live-data smoke is a dedicated seam-backed proof; use smoke:pm-live-data to run it explicitly.',
)

type ScheduleProject = {
  project_id?: string
  project_name?: string
  project_code?: string
}

type ApprovalQueueItem = {
  id?: string
  workpackage_id?: string
}

type ApprovalQueue = {
  total_count: number
  snapshots?: ApprovalQueueItem[]
}

type DriverEdge = {
  driver_task_id?: string
  driver_task_code?: string
  driver_task_name?: string
  driven_task_id?: string
  driven_task_code?: string
  driven_task_name?: string
}

type WorkfrontRow = {
  apparatus_name?: string
  apparatus_id?: string
  primary_blocking_issue_id?: string | null
  returnable_issue_id?: string | null
  last_pm_decision?: {
    entity_id?: string
  } | null
  blocking_issues?: Array<{
    id?: string
  }>
}

type WorkfrontPayload = {
  summary?: {
    total_count?: number
  }
  rows?: WorkfrontRow[]
  advisory?: {
    mode?: string
    ai_mutation_authority?: string
  }
}

type DecisionHistoryRow = {
  entity_id?: string
}

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(path)
  expect(response.ok(), `${path} should return a successful JSON response`).toBeTruthy()
  return (await response.json()) as T
}

function collectWorkfrontEntityIds(workfront: WorkfrontPayload, maxIds = 5): string[] {
  const ids = new Set<string>()

  for (const row of workfront.rows ?? []) {
    if (row.primary_blocking_issue_id) ids.add(row.primary_blocking_issue_id)
    if (row.returnable_issue_id) ids.add(row.returnable_issue_id)
    if (row.last_pm_decision?.entity_id) ids.add(row.last_pm_decision.entity_id)
    row.blocking_issues?.forEach((issue) => {
      if (issue.id) ids.add(issue.id)
    })
  }

  return Array.from(ids).slice(0, maxIds)
}

function decisionHistoryPath(entityIds: string[]) {
  const params = new URLSearchParams()
  const scopedEntityIds = entityIds.length ? entityIds : ['__pm_workfront_smoke_noop__']
  scopedEntityIds.forEach((entityId) => params.append('entity_id', entityId))
  params.set('limit', '25')
  return `/api/v1/reads/decision-history?${params.toString()}`
}

function firstText(...values: Array<string | undefined | null>): string | null {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) {
      return value.trim()
    }
  }

  return null
}

test('promoted PM routes render live seam-backed data through operations-web ingress', async ({ page, request }) => {
  const mutationRequests: string[] = []
  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.abort()
  })

  const projects = await getJson<ScheduleProject[]>(request, '/api/v1/schedule/projects')
  expect(projects.length).toBeGreaterThan(0)
  const projectMarker =
    firstText(projects[0]?.project_name, projects[0]?.project_code, projects[0]?.project_id) ?? 'Project Schedule'

  const approvalQueue = await getJson<ApprovalQueue>(request, '/api/v1/reads/approval-queue')
  const approvalCount = Number(approvalQueue.total_count ?? 0)
  const snapshot = approvalQueue.snapshots?.[0]
  const snapshotMarker = firstText(
    snapshot?.workpackage_id ? `Snapshot: ${snapshot.workpackage_id}` : null,
    snapshot?.id,
  )

  const driverEdges = await getJson<DriverEdge[]>(request, '/api/v1/schedule/drivers')
  const driverMarker = firstText(
    driverEdges[0]?.driver_task_name,
    driverEdges[0]?.driver_task_code,
    driverEdges[0]?.driver_task_id,
    driverEdges[0]?.driven_task_name,
    driverEdges[0]?.driven_task_code,
    driverEdges[0]?.driven_task_id,
  )

  const workfront = await getJson<WorkfrontPayload>(request, '/api/v1/reads/pm-workfront')
  expect(Array.isArray(workfront.rows), 'PM workfront rows should be an array').toBeTruthy()
  expect(Number(workfront.summary?.total_count ?? workfront.rows?.length ?? 0)).toBeGreaterThanOrEqual(0)
  expect(workfront.advisory?.mode ?? 'read_only').toBe('read_only')
  expect(workfront.advisory?.ai_mutation_authority ?? 'not_admitted').toBe('not_admitted')
  const workfrontMarker = firstText(workfront.rows?.[0]?.apparatus_name, workfront.rows?.[0]?.apparatus_id)
  const workfrontEntityIds = collectWorkfrontEntityIds(workfront)
  const history = await getJson<DecisionHistoryRow[]>(request, decisionHistoryPath(workfrontEntityIds))
  expect(history.length).toBeLessThanOrEqual(25)
  if (workfrontEntityIds.length) {
    const allowed = new Set(workfrontEntityIds)
    for (const row of history) {
      if (row.entity_id) {
        expect(allowed.has(row.entity_id), `decision history entity ${row.entity_id} should be row-scoped`).toBeTruthy()
      }
    }
  } else {
    expect(history, 'no-op PM decision history smoke should return no rows').toHaveLength(0)
  }

  const scheduleResponse = await page.goto('/pm-review/schedule')
  expect(scheduleResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM schedule now has a real app route/i })).toBeVisible()
  await expect(page.getByText(/Schedule bridge offline/i)).toHaveCount(0)
  await expect(page.getByText(projectMarker, { exact: false }).first()).toBeVisible()

  const approvalResponse = await page.goto('/pm-review/approval')
  expect(approvalResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM approval now has a real app route/i })).toBeVisible()
  await expect(page.getByText(new RegExp(`${approvalCount}\\s+items awaiting review`, 'i'))).toBeVisible()
  if (approvalCount > 0 && snapshotMarker) {
    await expect(page.getByText(snapshotMarker, { exact: false }).first()).toBeVisible()
  }

  const driversResponse = await page.goto('/pm-review')
  expect(driversResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM drivers now have a real app route/i })).toBeVisible()
  await expect(page.getByText(/Schedule drivers bridge offline/i)).toHaveCount(0)
  if (driverMarker) {
    await expect(page.getByText(driverMarker, { exact: false }).first()).toBeVisible()
  } else {
    await expect(page.getByText(/No critical-path driving edges landed for this project/i)).toBeVisible()
  }

  const workfrontResponse = await page.goto('/pm-review/workfront')
  expect(workfrontResponse?.ok()).toBeTruthy()
  await expect(page.getByRole('heading', { name: /PM workfront now has a governed read model/i })).toBeVisible()
  await expect(page.getByText(/Workfront seam/i)).toBeVisible()
  await expect(page.getByText(/offline/i)).toHaveCount(0)
  if (workfrontMarker) {
    await expect(page.getByText(workfrontMarker, { exact: false }).first()).toBeVisible()
  }
  expect(mutationRequests).toHaveLength(0)
})
