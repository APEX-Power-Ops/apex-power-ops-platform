import { browserEnv } from './browser-env'

export type RevenueRecognitionRow = {
  project_id: string
  project_number: string | null
  project_name: string | null
  scope_id: string | null
  scope_name: string | null
  quoted_revenue: number
  recognized_revenue: number
  recognition_percent: number
  billable_now: number
  total_apparatus: number
  completed_apparatus: number
}

export type ProjectRevenueRollup = {
  project_id: string
  project_number: string | null
  project_name: string | null
  quoted_revenue: number
  recognized_revenue: number
  recognition_percent: number
  billable_now: number
  total_apparatus: number
  completed_apparatus: number
  scopes: RevenueRecognitionRow[]
}

export class RevenueRecognitionError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'RevenueRecognitionError'
    this.status = status
  }
}

function getErrorDetail(payload: unknown, fallback: string) {
  if (typeof payload !== 'object' || payload === null) {
    return fallback
  }
  const detail = (payload as { detail?: unknown }).detail
  return typeof detail === 'string' && detail.trim().length > 0 ? detail : fallback
}

export async function fetchRevenueRecognition(limit = 12): Promise<RevenueRecognitionRow[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/revenue-recognition?limit=${limit}`, {
    headers: { Accept: 'application/json' },
  })

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new RevenueRecognitionError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as RevenueRecognitionRow[]
}

export function rollupByProject(rows: RevenueRecognitionRow[]): ProjectRevenueRollup[] {
  const byId = new Map<string, ProjectRevenueRollup>()
  for (const row of rows) {
    let project = byId.get(row.project_id)
    if (!project) {
      project = {
        project_id: row.project_id,
        project_number: row.project_number,
        project_name: row.project_name,
        quoted_revenue: 0,
        recognized_revenue: 0,
        recognition_percent: 0,
        billable_now: 0,
        total_apparatus: 0,
        completed_apparatus: 0,
        scopes: [],
      }
      byId.set(row.project_id, project)
    }
    project.quoted_revenue += row.quoted_revenue
    project.recognized_revenue += row.recognized_revenue
    project.billable_now += row.billable_now
    project.total_apparatus += row.total_apparatus
    project.completed_apparatus += row.completed_apparatus
    project.scopes.push(row)
  }
  for (const project of byId.values()) {
    project.recognition_percent =
      project.quoted_revenue > 0
        ? Math.round((project.recognized_revenue / project.quoted_revenue) * 10000) / 100
        : 0
  }
  return Array.from(byId.values())
}
