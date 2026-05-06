import { browserEnv } from './browser-env'

export type BlockersSummaryRow = {
  project_number: string | null
  project_name: string | null
  apparatus_type: string | null
  availability: string | null
  blocked_count: number
  blocked_hours: number
  sample_notes: string | null
}

export class BlockersSummaryError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'BlockersSummaryError'
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

export async function fetchBlockersSummary(limit = 12): Promise<BlockersSummaryRow[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/blockers-summary?limit=${limit}`, {
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
    throw new BlockersSummaryError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as BlockersSummaryRow[]
}