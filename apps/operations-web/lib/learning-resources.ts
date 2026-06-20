import { browserEnv } from './browser-env'

export type LearningResource = {
  resource_type: string
  title: string
  source: 'curated' | 'section_match'
  reference: Record<string, unknown>
  is_primary: boolean
  is_mandatory: boolean
  cert_level: string | null
  score: number
  why: string
}

export type LearningResourcesResponse = {
  context: { neta_section: string; level: string | null; limit: number }
  resources: LearningResource[]
}

export class LearningResourcesError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'LearningResourcesError'
    this.status = status
  }
}

export async function fetchLearningResources(
  netaSection: string,
  level?: string,
  limit = 20,
): Promise<LearningResourcesResponse> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const params = new URLSearchParams({ neta_section: netaSection, limit: String(limit) })
  if (level) params.set('level', level)
  const response = await fetch(`${baseUrl}/api/v1/learning/resources?${params.toString()}`, {
    headers: { Accept: 'application/json' },
  })
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (!response.ok) {
    throw new LearningResourcesError(`Request failed with status ${response.status}`, response.status)
  }
  return payload as LearningResourcesResponse
}
