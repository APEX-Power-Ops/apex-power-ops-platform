import { browserEnv } from './browser-env'

export type MasterOperationsSummary = {
  project_id: string
  project_number: string | null
  project_name: string | null
  project_status: string | null
  client_name: string | null
  resa_location: string | null
  site_city: string | null
  project_due: string | null
  scope_count: number
  total_apparatus: number
  completed: number
  remaining: number
  completion_percent: number
  ready_to_work: number
  on_hold: number
  not_available: number
  issues: number
  overdue: number
  due_today: number
  due_this_week: number
  ready_hours: number
  remaining_hours: number
  health_status: string
}

export class MasterOperationsError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'MasterOperationsError'
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

export async function fetchMasterOperations(limit = 12): Promise<MasterOperationsSummary[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/master-operations?limit=${limit}`, {
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
    throw new MasterOperationsError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as MasterOperationsSummary[]
}