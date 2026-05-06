import { browserEnv } from './browser-env'

export type ScheduleHealthSummary = {
  project_number: string | null
  project_name: string | null
  project_due: string | null
  scope_name: string | null
  scope_due: string | null
  percent_complete: number
  overdue_items: number
  on_hold_items: number
  not_available_items: number
  health_status: string
}

export class ScheduleHealthError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ScheduleHealthError'
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

export async function fetchScheduleHealth(limit = 12): Promise<ScheduleHealthSummary[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/schedule-health?limit=${limit}`, {
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
    throw new ScheduleHealthError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as ScheduleHealthSummary[]
}