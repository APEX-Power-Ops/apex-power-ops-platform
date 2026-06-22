/**
 * estimator-intake.ts
 *
 * Typed API client + PM-safe view-model for the ops intake envelope.
 *
 * Finance-redaction contract: NO dollar fields are exposed in any exported
 * type or function.  Specifically, onsite_labor / offsite_labor / travel /
 * outside_services / unit_multiplier / pct_adjust / blended_rate /
 * quoted_revenue / scope_quote are intentionally omitted everywhere.
 *
 * Routes (base URL via lib/browser-env.ts controlPlaneBaseUrl):
 *   POST   /api/v1/ops/intake                   uploadWorkbook
 *   GET    /api/v1/ops/intake/{run_id}           fetchRun
 *   POST   /api/v1/ops/intake/{run_id}/review    editReview  (POST not PATCH - CORS)
 *   POST   /api/v1/ops/intake/{run_id}/approve   approveRun
 *   POST   /api/v1/ops/intake/{run_id}/reject    rejectRun
 */

import { browserEnv } from './browser-env'

// ---------------------------------------------------------------------------
// Types -- finding (PM-safe: message only, no diagnostic_detail)
// ---------------------------------------------------------------------------

export type FindingSeverity = 'info' | 'warning' | 'blocking'

/** PM-safe finding: only {code, severity, ok, message}.  diagnostic_detail is
 *  intentionally absent -- it may contain dollar figures. */
export interface IntakeFinding {
  code: string
  severity: FindingSeverity
  ok: boolean
  message: string
}

// ---------------------------------------------------------------------------
// Types -- run
// ---------------------------------------------------------------------------

export type IntakeRunStatus =
  | 'parsed'
  | 'reviewing'
  | 'approved'
  | 'rejected'
  | 'revision_blocked'
  | 'superseded'

export interface IntakeRun {
  run_id: string
  status: IntakeRunStatus
  conflict_kind: string | null
  source_format: string | null
  /** review_payload is the raw server shape used by buildTree */
  review_payload: ReviewPayload
  findings: IntakeFinding[]
}

// ---------------------------------------------------------------------------
// Types -- raw review payload shapes (from the ops-intake engine)
// ---------------------------------------------------------------------------

/** Raw line shape from the server review_payload */
interface RawLine {
  apparatus_type: string
  test_standard: string
  qty: number
  hrs_per_unit: number
  section: string | null
  line_uid: string | null
  drawing?: string | null
  designation?: string | null
  notes?: string | null
  // dollar fields are explicitly absent here -- they must not be forwarded
}

/** Raw scope shape */
interface RawScope {
  scope_name: string
  scope_type?: string
  sort_order?: number
  // quote is intentionally NOT typed to prevent accidental forwarding
  lines: RawLine[]
}

/** The review_payload object returned by the server */
export interface ReviewPayload {
  project: {
    project_number: string
    project_name: string
    [key: string]: unknown
  }
  scopes: RawScope[]
}

// ---------------------------------------------------------------------------
// View-model types -- PM-safe tree (scope -> task -> line, hours only)
// ---------------------------------------------------------------------------

/** A single apparatus line -- hours only, no dollars */
export interface LineNode {
  apparatusType: string
  testStandard: string
  qty: number
  hoursPerUnit: number
  /** totalHours = qty x hoursPerUnit */
  totalHours: number
  lineUid: string | null
  drawing: string | null
  designation: string | null
  notes: string | null
  section: string | null
}

/** A task (group of lines sharing the same section).
 *  Section null maps to the sentinel task name "__ungrouped__". */
export interface TaskNode {
  taskName: string
  lines: LineNode[]
}

/** A scope containing an ordered list of tasks */
export interface ScopeNode {
  scopeName: string
  scopeType: string
  sortOrder: number
  tasks: TaskNode[]
}

// ---------------------------------------------------------------------------
// buildTree -- the pure PM-safe view-model builder
// ---------------------------------------------------------------------------

/**
 * Build a scope->task->line tree from a server review_payload.
 *
 * - Lines are grouped under tasks by their `section` value.
 * - Lines with section === null are placed under a task named "__ungrouped__".
 * - NO dollar values are exposed anywhere in the returned tree.
 *
 * @param reviewPayload  The review_payload object from an IntakeRun response.
 * @returns              Ordered array of ScopeNode (scope order preserved from server).
 */
export function buildTree(reviewPayload: ReviewPayload): ScopeNode[] {
  const scopes: ScopeNode[] = []

  for (const rawScope of reviewPayload.scopes ?? []) {
    // Group lines by section, preserving insertion order
    const taskMap = new Map<string, LineNode[]>()

    for (const rawLine of rawScope.lines ?? []) {
      const taskName = rawLine.section ?? '__ungrouped__'
      if (!taskMap.has(taskName)) {
        taskMap.set(taskName, [])
      }

      const qty = rawLine.qty ?? 0
      const hoursPerUnit = rawLine.hrs_per_unit ?? 0

      const lineNode: LineNode = {
        apparatusType: rawLine.apparatus_type,
        testStandard: rawLine.test_standard,
        qty,
        hoursPerUnit,
        totalHours: Math.round(qty * hoursPerUnit * 10000) / 10000,
        lineUid: rawLine.line_uid ?? null,
        drawing: rawLine.drawing ?? null,
        designation: rawLine.designation ?? null,
        notes: rawLine.notes ?? null,
        section: rawLine.section ?? null,
      }
      taskMap.get(taskName)!.push(lineNode)
    }

    const tasks: TaskNode[] = Array.from(taskMap.entries()).map(([taskName, lines]) => ({
      taskName,
      lines,
    }))

    scopes.push({
      scopeName: rawScope.scope_name,
      scopeType: rawScope.scope_type ?? 'OTHER',
      sortOrder: rawScope.sort_order ?? 0,
      tasks,
    })
  }

  return scopes
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class IntakeError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'IntakeError'
    this.status = status
  }
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

function intakeBase(): string {
  return `${browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')}/api/v1/ops/intake`
}

function getErrorDetail(payload: unknown, fallback: string): string {
  if (typeof payload !== 'object' || payload === null) return fallback
  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === 'string' && detail.trim().length > 0) return detail
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail)
  }
  return fallback
}

async function parseResponse<T>(res: Response): Promise<T> {
  let payload: unknown = null
  try {
    payload = await res.json()
  } catch {
    payload = null
  }
  if (!res.ok) {
    throw new IntakeError(
      getErrorDetail(payload, `Request failed with status ${res.status}`),
      res.status,
    )
  }
  return payload as T
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Fetch an existing intake run by ID (PM-safe findings). */
export async function fetchRun(runId: string): Promise<IntakeRun> {
  const res = await fetch(`${intakeBase()}/${runId}`, {
    headers: { Accept: 'application/json' },
  })
  return parseResponse<IntakeRun>(res)
}

/**
 * Upload a workbook file and create an intake run.
 *
 * @param file         The workbook File object.
 * @param uploadedBy   Identifier of the PM performing the upload.
 * @param contentType  MIME type of the workbook.
 */
export async function uploadWorkbook(
  file: File,
  uploadedBy: string,
  contentType: string,
): Promise<IntakeRun> {
  const form = new FormData()
  form.append('file', file)
  form.append('uploaded_by', uploadedBy)
  form.append('content_type', contentType)

  const res = await fetch(intakeBase(), {
    method: 'POST',
    body: form,
  })
  return parseResponse<IntakeRun>(res)
}

/**
 * POST a revised review_payload to the server (POST, not PATCH -- CORS allows only GET/POST/OPTIONS).
 *
 * @param runId         The intake run ID.
 * @param reviewPayload The full updated review_payload object.
 */
export async function editReview(runId: string, reviewPayload: ReviewPayload): Promise<IntakeRun> {
  const res = await fetch(`${intakeBase()}/${runId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ review_payload: reviewPayload }),
  })
  return parseResponse<IntakeRun>(res)
}

/**
 * Approve an intake run (identity-gated on the server).
 *
 * @param runId      The intake run ID.
 * @param approvedBy Identifier of the approver.
 */
export async function approveRun(
  runId: string,
  approvedBy: string,
): Promise<{ status: string; run_id: string }> {
  const res = await fetch(`${intakeBase()}/${runId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy }),
  })
  return parseResponse<{ status: string; run_id: string }>(res)
}

/**
 * Reject an active intake run.
 *
 * @param runId  The intake run ID.
 * @param reason Human-readable rejection reason.
 */
export async function rejectRun(runId: string, reason: string): Promise<IntakeRun> {
  const res = await fetch(`${intakeBase()}/${runId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ reason }),
  })
  return parseResponse<IntakeRun>(res)
}

// ---------------------------------------------------------------------------
// Upload helpers + inverse of buildTree (fold the edited tree back to a payload)
// ---------------------------------------------------------------------------

/** The DB-allowed content_type literal ('xlsm' | 'json'), derived from the file NAME (not the browser
 *  MIME, which is application/vnd... and would violate the 007 check), or null for an unsupported ext. */
export function workbookContentType(filename: string): 'xlsm' | 'json' | null {
  const lower = filename.toLowerCase()
  if (lower.endsWith('.xlsm') || lower.endsWith('.xlsx')) return 'xlsm'
  if (lower.endsWith('.json')) return 'json'
  return null
}

/**
 * Fold the edited tree back into a review_payload for editReview.
 *
 * The server allowlist pins EVERY field except per-line `section` + `hrs_per_unit`. Rebuilding the
 * payload from the (lossy) tree drops server-pinned fields the tree never carries -- the scope
 * `quote` (the dollar basis) and the line `line_number`/catalog fields -- so the edit would 400.
 * Instead we DEEP-CLONE the original (preserving every runtime field, including ones these TS types
 * deliberately omit) and overlay ONLY the two mutable fields per line, matched by line_uid. Cross-scope
 * moves are forbidden server-side, so a line keeps its scope; "regroup into a task" is a section change.
 */
export function treeToReviewPayload(tree: ScopeNode[], original: ReviewPayload): ReviewPayload {
  const edits = new Map<string, { section: string | null; hrs_per_unit: number }>()
  for (const scope of tree) {
    for (const task of scope.tasks) {
      for (const line of task.lines) {
        if (line.lineUid != null) {
          edits.set(line.lineUid, { section: line.section ?? null, hrs_per_unit: line.hoursPerUnit })
        }
      }
    }
  }
  const clone: ReviewPayload = JSON.parse(JSON.stringify(original))
  for (const scope of clone.scopes ?? []) {
    for (const line of scope.lines ?? []) {
      const e = line.line_uid != null ? edits.get(line.line_uid) : undefined
      if (e) {
        line.section = e.section
        line.hrs_per_unit = e.hrs_per_unit
      }
    }
  }
  return clone
}
