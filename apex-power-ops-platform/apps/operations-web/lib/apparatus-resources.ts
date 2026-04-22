import { browserEnv } from './browser-env'

export type ApparatusStudyResource = {
  resource_id: string
  title: string
  resource_type: string
  source_table: string
  level: string | null
  description: string | null
  url_slug: string | null
  estimated_minutes: number | null
}

export type ApparatusStudyResourcesResponse = {
  apparatus_id: string
  count: number
  resources: ApparatusStudyResource[]
}

export class ApparatusResourcesError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApparatusResourcesError'
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

export async function fetchApparatusStudyResources(
  apparatusId: string,
): Promise<ApparatusStudyResourcesResponse> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(
    `${baseUrl}/api/v1/neta/apparatus/${encodeURIComponent(apparatusId)}/resources`,
    {
      headers: {
        Accept: 'application/json',
      },
    },
  )

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new ApparatusResourcesError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as ApparatusStudyResourcesResponse
}