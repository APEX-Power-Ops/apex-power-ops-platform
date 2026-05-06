import { browserEnv } from './browser-env'

export type ProjectApparatusSummaryRow = {
  project_id: string
  project_number: string | null
  project_name: string | null
  scope_id: string | null
  scope_name: string | null
  total_apparatus: number
  total_completed: number
  total_remaining: number
  completion_percent: number
  ready_to_work: number
  blocked: number
  issues_failed: number
  past_due: number
  due_this_week: number
  total_quoted_hours: number
  total_actual_hours: number
  remaining_hours: number
}

export class ProjectApparatusSummaryError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ProjectApparatusSummaryError'
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

export async function fetchProjectApparatusSummary(limit = 12): Promise<ProjectApparatusSummaryRow[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/project-apparatus-summary?limit=${limit}`, {
    headers: {
      Accept: 'application/json',
    },
  })

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new ProjectApparatusSummaryError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as ProjectApparatusSummaryRow[]
}