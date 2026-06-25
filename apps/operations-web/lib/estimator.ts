import { browserEnv } from './browser-env'
import {
  buildNativeEnvelope, EQUIPMENT_MODELS_SEED, type EstimateEnvelope, type Finding, type NativeScopeInput,
} from '@apex/estimator-core'

export const DEMO_PROJECT_NUMBER = 'DEMO-NATIVE-001'
// Dev-only default: the real ops.persons PK (Jason Swenson) seeded on ops_dev. Production wiring MUST set
// NEXT_PUBLIC_OPS_DEV_PM_ID. Do NOT fall back to all-zeroes — that is not a known person and the API 400s.
export const PM_ACTOR_ID = process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '0a000000-0000-4000-8000-000000000001'

export class EstimatorError extends Error {
  constructor(message: string, public status: number) { super(message) }
}
function intakeBase(): string { return `${browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')}/api/v1/ops/intake` }
async function parseResponse<T>(res: Response): Promise<T> {
  let payload: unknown = null
  try { payload = await res.json() } catch { payload = null }
  if (!res.ok) {
    const detail = (payload as { detail?: unknown })?.detail
    throw new EstimatorError(typeof detail === 'string' ? detail : `Request failed with status ${res.status}`, res.status)
  }
  return payload as T
}

export interface NativeRunResult { run_id: string; status: string; conflict_kind: string | null; source_format: string; findings: { code: string; severity: string; ok: boolean; message: string }[] }

export function catalogRefs(): string[] {
  return EQUIPMENT_MODELS_SEED.filter((m) => m.lifecycle_status === 'active').map((m) => m.ref).sort()
}

/** Always pins project_number = DEMO_PROJECT_NUMBER (never Miner; never caller-supplied). */
export function buildDemoEnvelope(scopes: NativeScopeInput[]): { envelope: EstimateEnvelope; findings: Finding[] } {
  return buildNativeEnvelope({ projectNumber: DEMO_PROJECT_NUMBER, quoteVersion: 1, scopes })
}

export async function submitNative(envelope: EstimateEnvelope, uploadedBy = PM_ACTOR_ID): Promise<NativeRunResult> {
  const res = await fetch(`${intakeBase()}/native`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ uploaded_by: uploadedBy, envelope }),
  })
  return parseResponse<NativeRunResult>(res)
}

export async function approveRun(runId: string, approvedBy = PM_ACTOR_ID): Promise<{ status: string; run_id: string }> {
  const res = await fetch(`${intakeBase()}/${runId}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy }),
  })
  return parseResponse<{ status: string; run_id: string }>(res)
}
