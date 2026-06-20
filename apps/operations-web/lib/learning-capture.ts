import { browserEnv } from './browser-env'

export type LearningUser = { id: string; email: string }

export type LearningEvent = {
  event_id: string
  user_id: string
  event_type: string
  study_content_id: string | null
  neta_section: string | null
  occurred_at: string
  payload: Record<string, unknown>
  created_at: string
}

export class LearningCaptureError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'LearningCaptureError'
    this.status = status
  }
}

const base = () => browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')

async function parse(response: Response) {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null
        ? ((payload as { detail?: unknown }).detail as string | undefined) ?? null
        : null
    throw new LearningCaptureError(detail ?? `Request failed with status ${response.status}`, response.status)
  }
  return payload
}

export async function fetchLearningUsers(limit = 100): Promise<LearningUser[]> {
  const r = await fetch(`${base()}/api/v1/learning/users?limit=${limit}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { users: LearningUser[] }).users
}

export async function fetchLearningSections(limit = 500): Promise<string[]> {
  const r = await fetch(`${base()}/api/v1/learning/sections?limit=${limit}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { sections: string[] }).sections
}

export async function fetchLearningEvents(userId: string, limit = 20): Promise<LearningEvent[]> {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) })
  const r = await fetch(`${base()}/api/v1/learning/events?${params.toString()}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { events: LearningEvent[] }).events
}

export async function recordLearningEvent(input: {
  user_id: string
  event_type: string
  study_content_id?: string | null
  neta_section?: string | null
  payload?: Record<string, unknown>
}): Promise<LearningEvent> {
  const r = await fetch(`${base()}/api/v1/learning/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(input),
  })
  return ((await parse(r)) as { event: LearningEvent }).event
}
