import { expect, test, type APIRequestContext } from '@playwright/test'

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

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(path)
  expect(response.ok(), `${path} should return a successful JSON response`).toBeTruthy()
  return (await response.json()) as T
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
})