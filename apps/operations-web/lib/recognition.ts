/**
 * recognition.ts — typed client + view-model for the ops recognition bridge.
 * Routes (base via browserEnv.controlPlaneBaseUrl):
 *   POST /api/v1/ops/recognition/completion/attest
 *   POST /api/v1/ops/recognition/completion/{attestation_id}/revoke
 *   POST /api/v1/ops/recognition/events/recognize
 *   POST /api/v1/ops/recognition/events/{event_id}/reverse
 *   GET  /api/v1/ops/recognition/worklist?project_number=
 *   GET  /api/v1/ops/recognition/rollup?project_number=
 * Dollar-free EXCEPT rollup.recognizedTotal (operator-authoritative, §261).
 */
import { browserEnv } from './browser-env'

export const CLEARANCE_VALUES = ['provided', 'not_applicable'] as const
export type Clearance = (typeof CLEARANCE_VALUES)[number]

export const ATTEST_COPY = 'Attest testing complete - for recognition'

export interface WorklistRow {
  apparatus_id: string
  apparatus_designation: string
  scope_id: string
  project_id: string
  project_number: string
  status: string
  quoted_hours: number
  quoted_revenue: number
  attestation_id: string | null
  attested_by: string | null
  attested_at: string | null
  attest_reason: string | null
  net_recognized: number
  is_recognized: boolean
  recognized_event_id: string | null
  can_attest: boolean
  can_recognize: boolean
  can_revoke: boolean
  can_reverse: boolean
}

export interface RollupRow {
  project_number: string
  scope_id: string
  project_id: string
  recognized_total: number | string
  recognized_count: number
  eligible_count: number
}

export interface ActionFlags {
  canAttest: boolean
  canRecognize: boolean
  canRevoke: boolean
  canReverse: boolean
}

/** Pure pass-through of the DB view flags (the DB is the single source of truth). */
export function actionFlags(row: WorklistRow): ActionFlags {
  return {
    canAttest: !!row.can_attest,
    canRecognize: !!row.can_recognize,
    canRevoke: !!row.can_revoke,
    canReverse: !!row.can_reverse,
  }
}

/** Ref must be non-blank when a clearance is 'provided' (005 ck_revrec_*_ref). Returns the first
 *  offending field label, or null when the clearance/ref combination is submittable. */
export function recognizeRefError(
  datasheetClearance: Clearance, datasheetRef: string,
  cxClearance: Clearance, cxRef: string,
): string | null {
  if (datasheetClearance === 'provided' && !datasheetRef.trim()) return 'datasheet'
  if (cxClearance === 'provided' && !cxRef.trim()) return 'commissioning'
  return null
}

export class RecognitionApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function base(): string {
  return `${browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')}/api/v1/ops/recognition`
}

async function parse<T>(res: Response): Promise<T> {
  let payload: unknown = null
  try { payload = await res.json() } catch { payload = null }
  if (!res.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed (${res.status})`
    throw new RecognitionApiError(detail, res.status)
  }
  return payload as T
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${base()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  })
  return parse<T>(res)
}

export async function fetchWorklist(projectNumber?: string): Promise<WorklistRow[]> {
  const q = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : ''
  return parse<WorklistRow[]>(await fetch(`${base()}/worklist${q}`, { headers: { Accept: 'application/json' } }))
}

export async function fetchRollup(projectNumber?: string): Promise<RollupRow[]> {
  const q = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : ''
  return parse<RollupRow[]>(await fetch(`${base()}/rollup${q}`, { headers: { Accept: 'application/json' } }))
}

export async function attestComplete(apparatusId: string, attestedBy: string, reason: string) {
  return postJson<{ attestation_id: string }>('/completion/attest', {
    apparatus_id: apparatusId, attested_by: attestedBy, reason,
  })
}

export async function revokeAttestation(attestationId: string, revokedBy: string, reason: string) {
  return postJson<{ attestation_id: string }>(`/completion/${attestationId}/revoke`, {
    revoked_by: revokedBy, reason,
  })
}

export async function recognize(
  apparatusId: string, recognizedBy: string,
  datasheetClearance: Clearance, datasheetRef: string | null,
  cxClearance: Clearance, cxRef: string | null,
) {
  return postJson<{ event_id: string }>('/events/recognize', {
    apparatus_id: apparatusId, recognized_by: recognizedBy,
    datasheet_clearance: datasheetClearance, datasheet_ref: datasheetRef,
    cx_clearance: cxClearance, cx_ref: cxRef,
  })
}

export async function reverseEvent(eventId: string, reversedBy: string, reason: string) {
  return postJson<{ reversal_id: string }>(`/events/${eventId}/reverse`, {
    reversed_by: reversedBy, reason,
  })
}
