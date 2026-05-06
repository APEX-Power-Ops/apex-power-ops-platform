import { browserEnv } from './browser-env'

export type ApparatusByCategorySummaryRow = {
  project_id: string
  project_number: string | null
  scope_id: string | null
  scope_name: string | null
  apparatus_category: string | null
  total_count: number
  completed: number
  remaining: number
  percent_complete: number
  ready_to_work: number
  blocked: number
}

export class ApparatusByCategoryError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApparatusByCategoryError'
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

export async function fetchApparatusByCategory(limit = 12): Promise<ApparatusByCategorySummaryRow[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/apparatus-by-category?limit=${limit}`, {
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
    throw new ApparatusByCategoryError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as ApparatusByCategorySummaryRow[]
}