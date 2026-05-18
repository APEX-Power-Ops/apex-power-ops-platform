'use client'

import Link from 'next/link'
import * as React from 'react'

type CandidateSummary = {
  workpackage_count?: number
  task_count?: number
  apparatus_candidate_count?: number
  crew_count?: number
  equipment_inventory_count?: number
  capability_count?: number
  warning_count?: number
  blocker_count?: number
  human_decision_count?: number
}

type CandidateProject = {
  name?: string | null
  location?: string | null
  drawing_package?: string | null
  issue_date?: string | null
  source_format?: string | null
  source_sheet?: string | null
}

type CandidateWarning = {
  severity?: string
  code?: string
  message?: string
  review_action?: string
  source_path?: string
}

type CandidateSourceFile = {
  source_id?: string
  label?: string
  path?: string | null
  found?: boolean
  size_bytes?: number | null
  modified_at?: string | null
  fingerprint?: string | null
  freshness_status?: string
}

type CandidateDecision = {
  decision_id?: string
  severity?: string
  prompt?: string
  recommended_action?: string
  warning_code?: string
}

type CandidateApparatus = {
  candidate_id?: string
  display_name?: string | null
  source_row?: number | null
  source_line_id?: string | null
}

type CandidateTask = {
  task_id?: string
  title?: string
  apparatus_type?: string | null
  designation?: string | null
  quantity?: number
  drawing_ref?: string | null
  planned_hours?: number
  source_ref?: {
    estimator_workbook_path?: string | null
    source_format?: string | null
    source_sheet?: string | null
    scope_sheet?: string | null
    source_row?: number | null
    line_id?: string | null
    drawing_ref?: string | null
  }
  apparatus_candidates?: CandidateApparatus[]
}

type LocalTaskApparatusRow = {
  candidate_id: string
  default_group_id: string
  source_task_id: string | null
  source_task_title: string
  source_task_designation: string
  display_name: string
  designation: string
  source_row: number | null
  source_line_id: string | null
  apparatus_type: string
  drawing_ref: string | null
  planned_hours: number
}

type LocalTaskGroup = {
  group_id: string
  title: string
  designation: string
  apparatus_type: string
  drawing_ref: string | null
  seeded_from_source: boolean
  source_task_id: string | null
}

type LocalTaskApparatusDraft = {
  group_id: string
  display_name: string
  designation: string
}

type LocalTaskShapingDraft = {
  version: string
  groups: LocalTaskGroup[]
  apparatus: Record<string, LocalTaskApparatusDraft>
}

type LocalTaskGroupSummary = LocalTaskGroup & {
  apparatus_rows: Array<LocalTaskApparatusRow & LocalTaskApparatusDraft>
  planned_hours: number
  source_task_count: number
}

type ManualTaskShapingArtifact = {
  storage: 'local_browser_only'
  version: string
  summary: {
    group_count: number
    regrouped_apparatus_count: number
    designation_override_count: number
  }
  groups: Array<{
    group_id: string
    title: string
    designation: string
    seeded_from_source: boolean
    source_task_id: string | null
    apparatus_count: number
    planned_hours: number
    apparatus_candidate_ids: string[]
  }>
  apparatus: Array<{
    candidate_id: string
    local_task_group_id: string
    display_name: string
    designation: string
    source_task_id: string | null
    source_task_title: string
  }>
}

type CandidateApprovalPreviewArtifact = {
  preview_kind: 'pm_import_candidate_review_approval_preview'
  preview_version: 'pm_import_candidate_review_approval_preview_v1'
  generated_locally_at: string
  storage: 'local_browser_only'
  candidate_identity: {
    candidate_id: string | null
    candidate_version: string | null
    project_name: string | null
    project_location: string | null
    source_fingerprint: string | null
    mutation_authority: string
  }
  local_review_evidence: {
    review_notes: string | null
    warning_summary: {
      warning_count: number
      blocker_count: number
      human_decision_count: number
    }
    manual_task_shaping: ManualTaskShapingArtifact | null
  }
  downstream_review_context: {
    target_route: '/pm-review/import-approval-readiness'
    contract_role: string
    not_allowed_now: string[]
  }
}

type TaskPlanMutationResult = {
  status?: string
  mutation_id?: string
  entity_id?: string
  new_state?: {
    project_id?: string
    row_counts?: {
      projects?: number
      workpackages?: number
      tasks?: number
      apparatus?: number
    }
    blocked_downstream?: string[]
  }
  error?: {
    message?: string
  }
}

type TaskPlanStatus = {
  classification?: string
  route?: string
  task_plan_route?: string
  task_plan_authority?: string
  project_id?: string
  persisted_at?: string | null
  current_candidate_match?: boolean
  planning_context_only?: boolean
  expected_row_counts?: {
    projects?: number
    workpackages?: number
    tasks?: number
    apparatus?: number
  }
  persisted_row_counts?: {
    projects?: number
    workpackages?: number
    tasks?: number
    apparatus?: number
  }
  blocked_downstream?: string[]
}

type CandidateWorkpackage = {
  workpackage_id?: string
  title?: string
  source_section?: string | null
  source_scope_sheet?: string | null
  drawing_refs?: string[]
  planned_hours?: number
  task_count?: number
  apparatus_candidate_count?: number
  tasks?: CandidateTask[]
}

type CandidatePayload = {
  candidate_id?: string
  candidate_version?: string
  review_status?: string
  mutation_authority?: string
  project?: CandidateProject
  source_bundle?: Record<string, unknown>
  source_freshness?: {
    strategy?: string
    mutation_authority?: string
    source_files?: CandidateSourceFile[]
    available_count?: number
    missing_count?: number
    aggregate_fingerprint?: string
    review_action?: string
  }
  summary?: CandidateSummary
  workpackages?: CandidateWorkpackage[]
  warnings?: CandidateWarning[]
  human_decisions?: CandidateDecision[]
  review_guidance?: {
    primary_review_goal?: string
    allowed_now?: string[]
    not_allowed_now?: string[]
  }
}

const { useCallback, useEffect, useMemo, useState } = React

const warningFilters = ['all', 'blocker', 'warning', 'info'] as const
type WarningFilter = (typeof warningFilters)[number]
const LOCAL_TASK_SHAPING_VERSION = 'pm_import_candidate_task_shaping_v1'

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const READS_BASE = `${API_BASE}/reads`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }

function makeToken() {
  return `Bearer ${btoa(JSON.stringify(PM_ACTOR))}`
}

async function readImportCandidate(): Promise<CandidatePayload> {
  const response = await fetch(`${READS_BASE}/project-import-candidate`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read PM import candidate')
  }

  return (await response.json()) as CandidatePayload
}

async function readTaskPlanStatus(): Promise<TaskPlanStatus> {
  const response = await fetch(`${READS_BASE}/project-import-task-plan-status`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read PM task-plan status')
  }

  return (await response.json()) as TaskPlanStatus
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/_/g, ' ')
}

function formatCount(value?: number) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString() : '0'
}

function formatHours(value?: number | null) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return '0'
  }

  return value.toLocaleString(undefined, {
    minimumFractionDigits: Number.isInteger(value) ? 0 : 1,
    maximumFractionDigits: 1,
  })
}

function warningTone(severity?: string) {
  switch (severity) {
    case 'blocker':
      return 'status-deferred'
    case 'warning':
      return 'status-awaiting-values'
    case 'info':
      return 'status-backend-routed'
    default:
      return 'status-configured'
  }
}

function sourceFileTone(found?: boolean) {
  return found ? 'status-configured' : 'status-deferred'
}

function sourceValue(value: unknown) {
  if (value === null || value === undefined || value === '') {
    return 'unknown'
  }
  if (Array.isArray(value)) {
    return value.length ? value.join(', ') : 'none'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function sourceRows(tasks: CandidateTask[]) {
  return tasks
    .map((task) => task.source_ref?.source_row)
    .filter((row): row is number => typeof row === 'number')
    .join(', ')
}

function localTaskShapingStorageKey(candidate?: CandidatePayload | null) {
  return candidate?.candidate_id ? `pm-import-candidate-task-shaping:${candidate.candidate_id}` : null
}

function approvalPreviewStorageKey(candidate?: CandidatePayload | null) {
  return candidate?.candidate_id ? `pm-import-candidate-approval-preview:${candidate.candidate_id}` : null
}

function defaultGroupId(task: CandidateTask, apparatus: CandidateApparatus) {
  return `source-task:${task.task_id || apparatus.candidate_id || 'unknown'}`
}

function flattenCandidateApparatus(workpackages: CandidateWorkpackage[]) {
  const rows: LocalTaskApparatusRow[] = []

  for (const workpackage of workpackages) {
    for (const task of workpackage.tasks || []) {
      const apparatusCandidates = task.apparatus_candidates || []
      const apparatusCount = apparatusCandidates.length || 1
      const perApparatusHours = typeof task.planned_hours === 'number' ? task.planned_hours / apparatusCount : 0

      for (const apparatus of apparatusCandidates) {
        if (!apparatus.candidate_id) {
          continue
        }

        rows.push({
          candidate_id: apparatus.candidate_id,
          default_group_id: defaultGroupId(task, apparatus),
          source_task_id: task.task_id || null,
          source_task_title: task.title || task.task_id || 'Untitled source task',
          source_task_designation: task.designation || '',
          display_name: apparatus.display_name || task.title || task.task_id || apparatus.candidate_id,
          designation: task.designation || '',
          source_row: apparatus.source_row ?? task.source_ref?.source_row ?? null,
          source_line_id: apparatus.source_line_id || task.source_ref?.line_id || null,
          apparatus_type: task.apparatus_type || 'unknown apparatus',
          drawing_ref: task.source_ref?.drawing_ref || task.drawing_ref || null,
          planned_hours: perApparatusHours,
        })
      }
    }
  }

  return rows
}

function buildDefaultLocalTaskGroups(apparatusRows: LocalTaskApparatusRow[]) {
  const groups = new Map<string, LocalTaskGroup>()

  for (const row of apparatusRows) {
    if (!groups.has(row.default_group_id)) {
      groups.set(row.default_group_id, {
        group_id: row.default_group_id,
        title: row.source_task_title,
        designation: row.source_task_designation,
        apparatus_type: row.apparatus_type,
        drawing_ref: row.drawing_ref,
        seeded_from_source: true,
        source_task_id: row.source_task_id,
      })
    }
  }

  return Array.from(groups.values())
}

function buildDefaultLocalTaskShapingDraft(apparatusRows: LocalTaskApparatusRow[]): LocalTaskShapingDraft {
  return {
    version: LOCAL_TASK_SHAPING_VERSION,
    groups: buildDefaultLocalTaskGroups(apparatusRows),
    apparatus: apparatusRows.reduce<Record<string, LocalTaskApparatusDraft>>((accumulator, row) => {
      accumulator[row.candidate_id] = {
        group_id: row.default_group_id,
        display_name: row.display_name,
        designation: row.designation,
      }
      return accumulator
    }, {}),
  }
}

function parseLocalTaskShaping(raw: string | null) {
  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as Partial<LocalTaskShapingDraft>
    if (!parsed || typeof parsed !== 'object') {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

function mergeLocalTaskShapingDraft(candidate: CandidatePayload, raw: string | null) {
  const apparatusRows = flattenCandidateApparatus(candidate.workpackages || [])
  const defaultDraft = buildDefaultLocalTaskShapingDraft(apparatusRows)
  const stored = parseLocalTaskShaping(raw)

  if (!stored) {
    return defaultDraft
  }

  const defaultGroupsById = new Map(defaultDraft.groups.map((group) => [group.group_id, group]))
  const groups: LocalTaskGroup[] = []
  const seen = new Set<string>()

  for (const group of stored.groups || []) {
    if (!group || typeof group.group_id !== 'string' || !group.group_id) {
      continue
    }

    const base = defaultGroupsById.get(group.group_id)
    groups.push({
      group_id: group.group_id,
      title: typeof group.title === 'string' && group.title ? group.title : base?.title || 'Untitled local task',
      designation: typeof group.designation === 'string' ? group.designation : base?.designation || '',
      apparatus_type: typeof group.apparatus_type === 'string' && group.apparatus_type ? group.apparatus_type : base?.apparatus_type || 'mixed apparatus',
      drawing_ref: typeof group.drawing_ref === 'string' && group.drawing_ref ? group.drawing_ref : base?.drawing_ref || null,
      seeded_from_source: typeof group.seeded_from_source === 'boolean' ? group.seeded_from_source : base?.seeded_from_source || false,
      source_task_id: typeof group.source_task_id === 'string' && group.source_task_id ? group.source_task_id : base?.source_task_id || null,
    })
    seen.add(group.group_id)
  }

  for (const group of defaultDraft.groups) {
    if (!seen.has(group.group_id)) {
      groups.push(group)
    }
  }

  const groupIds = new Set(groups.map((group) => group.group_id))
  const apparatus: Record<string, LocalTaskApparatusDraft> = {}

  for (const row of apparatusRows) {
    const storedApparatus = stored.apparatus?.[row.candidate_id]
    const groupId =
      storedApparatus && typeof storedApparatus.group_id === 'string' && groupIds.has(storedApparatus.group_id)
        ? storedApparatus.group_id
        : row.default_group_id

    apparatus[row.candidate_id] = {
      group_id: groupId,
      display_name:
        storedApparatus && typeof storedApparatus.display_name === 'string' && storedApparatus.display_name
          ? storedApparatus.display_name
          : row.display_name,
      designation:
        storedApparatus && typeof storedApparatus.designation === 'string'
          ? storedApparatus.designation
          : row.designation,
    }
  }

  return {
    version: LOCAL_TASK_SHAPING_VERSION,
    groups,
    apparatus,
  }
}

function createManualTaskGroupId(count: number) {
  return `manual-task:${count}:${Date.now().toString(36)}`
}

function candidateFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'pm-import-candidate'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-review.json`
}

function approvalPreviewFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'pm-import-candidate'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-preview.json`
}

function taskPlanProjectId(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner'
  const slug = candidateId.replace(/^pm-import-candidate-/, '').replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase()
  return `pm-task-plan-project-${slug || 'project-miner'}`
}

function buildManualTaskShapingArtifact(
  taskShapingDraft: LocalTaskShapingDraft | null,
  localTaskGroups: LocalTaskGroupSummary[],
  apparatusRows: LocalTaskApparatusRow[],
  taskShapingSummary: {
    local_group_count: number
    regrouped_apparatus_count: number
    designation_override_count: number
  },
): ManualTaskShapingArtifact | null {
  if (!taskShapingDraft) {
    return null
  }

  return {
    storage: 'local_browser_only',
    version: taskShapingDraft.version,
    summary: {
      group_count: taskShapingSummary.local_group_count,
      regrouped_apparatus_count: taskShapingSummary.regrouped_apparatus_count,
      designation_override_count: taskShapingSummary.designation_override_count,
    },
    groups: localTaskGroups.map((group) => ({
      group_id: group.group_id,
      title: group.title,
      designation: group.designation,
      seeded_from_source: group.seeded_from_source,
      source_task_id: group.source_task_id,
      apparatus_count: group.apparatus_rows.length,
      planned_hours: group.planned_hours,
      apparatus_candidate_ids: group.apparatus_rows.map((row) => row.candidate_id),
    })),
    apparatus: apparatusRows.map((row) => ({
      candidate_id: row.candidate_id,
      local_task_group_id: taskShapingDraft.apparatus[row.candidate_id]?.group_id || row.default_group_id,
      display_name: taskShapingDraft.apparatus[row.candidate_id]?.display_name || row.display_name,
      designation: taskShapingDraft.apparatus[row.candidate_id]?.designation ?? row.designation,
      source_task_id: row.source_task_id,
      source_task_title: row.source_task_title,
    })),
  }
}

function buildApprovalPreviewArtifact(
  candidate: CandidatePayload,
  reviewDraft: string,
  manualTaskShaping: ManualTaskShapingArtifact | null,
  notAllowed: string[],
): CandidateApprovalPreviewArtifact {
  const summary = candidate.summary || {}
  const project = candidate.project || {}

  return {
    preview_kind: 'pm_import_candidate_review_approval_preview',
    preview_version: 'pm_import_candidate_review_approval_preview_v1',
    generated_locally_at: new Date().toISOString(),
    storage: 'local_browser_only',
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      project_location: project.location || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
      mutation_authority: candidate.mutation_authority || 'not_admitted',
    },
    local_review_evidence: {
      review_notes: reviewDraft.trim() || null,
      warning_summary: {
        warning_count: summary.warning_count ?? 0,
        blocker_count: summary.blocker_count ?? 0,
        human_decision_count: summary.human_decision_count ?? 0,
      },
      manual_task_shaping: manualTaskShaping,
    },
    downstream_review_context: {
      target_route: '/pm-review/import-approval-readiness',
      contract_role: 'Browser-local PM review context for later admitted approval persistence review only.',
      not_allowed_now: notAllowed,
    },
  }
}

function parseApprovalPreview(raw: string | null) {
  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as CandidateApprovalPreviewArtifact
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

function normalizeReviewNotes(value: string) {
  const trimmed = value.trim()
  return trimmed || null
}

function buildTaskPlanIdempotencyKey(candidate?: CandidatePayload | null) {
  const base = candidate?.candidate_id || 'pm-import-candidate'
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `pm-task-plan:${base}:${crypto.randomUUID()}`
  }
  return `pm-task-plan:${base}:${Date.now()}`
}

async function submitTaskPlan(
  candidate: CandidatePayload,
  reviewDraft: string,
  manualTaskShaping: ManualTaskShapingArtifact,
): Promise<TaskPlanMutationResult> {
  const idempotencyKey = buildTaskPlanIdempotencyKey(candidate)
  const body = {
    idempotency_key: idempotencyKey,
    mutation_class: 'C',
    action_type: 'persist_project_import_task_plan',
    entity_id: taskPlanProjectId(candidate),
    payload: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      source_stat_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
      idempotency_key: idempotencyKey,
      review_notes: normalizeReviewNotes(reviewDraft),
      manual_task_shaping: manualTaskShaping,
    },
    reason:
      'Persist manual PM task grouping as planning-only durable rows; keep approval persistence, project import, assignment, schedule, status, finance, and source writeback blocked.',
    source: 'online',
    client_timestamp: new Date().toISOString(),
  }

  const response = await fetch(`${API_BASE}/mutations/project-import-task-plans`, {
    method: 'POST',
    headers: {
      Authorization: makeToken(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  return (await response.json()) as TaskPlanMutationResult
}

function approvalPreviewMatchesCurrentReview(
  preview: CandidateApprovalPreviewArtifact | null,
  reviewDraft: string,
  manualTaskShaping: ManualTaskShapingArtifact | null,
) {
  if (!preview) {
    return false
  }

  return (
    normalizeReviewNotes(reviewDraft) === (preview.local_review_evidence?.review_notes || null) &&
    JSON.stringify(manualTaskShaping || null) === JSON.stringify(preview.local_review_evidence?.manual_task_shaping || null)
  )
}

export default function PmImportCandidatePage() {
  const [candidate, setCandidate] = useState<CandidatePayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [warningFilter, setWarningFilter] = useState<WarningFilter>('all')
  const [warningCodeFilter, setWarningCodeFilter] = useState('all')
  const [reviewDraft, setReviewDraft] = useState('')
  const [taskShapingDraft, setTaskShapingDraft] = useState<LocalTaskShapingDraft | null>(null)
  const [stagedApprovalPreview, setStagedApprovalPreview] = useState<CandidateApprovalPreviewArtifact | null>(null)
  const [taskPlanStatus, setTaskPlanStatus] = useState<TaskPlanStatus | null>(null)
  const [taskPlanMutationResult, setTaskPlanMutationResult] = useState<TaskPlanMutationResult | null>(null)
  const [taskPlanError, setTaskPlanError] = useState<string | null>(null)
  const [persistingTaskPlan, setPersistingTaskPlan] = useState(false)
  const [exportStatus, setExportStatus] = useState('')

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setCandidate(await readImportCandidate())
      setOnline(true)
    } catch {
      setOnline(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const summary = candidate?.summary || {}
  const project = candidate?.project || {}
  const warnings = candidate?.warnings || []
  const warningCodes = useMemo(
    () => Array.from(new Set(warnings.map((warning) => warning.code).filter((code): code is string => Boolean(code)))).sort(),
    [warnings],
  )
  const filteredWarnings = warnings.filter((warning) => {
    const severityMatches = warningFilter === 'all' || warning.severity === warningFilter
    const codeMatches = warningCodeFilter === 'all' || warning.code === warningCodeFilter
    return severityMatches && codeMatches
  })
  const decisions = candidate?.human_decisions || []
  const workpackages = candidate?.workpackages || []
  const apparatusRows = useMemo(() => flattenCandidateApparatus(workpackages), [workpackages])
  const sourceBundle = candidate?.source_bundle || {}
  const sourceFreshness = candidate?.source_freshness
  const sourceFiles = sourceFreshness?.source_files || []
  const notAllowed = candidate?.review_guidance?.not_allowed_now || []
  const allowedNow = candidate?.review_guidance?.allowed_now || []
  const draftStorageKey = candidate?.candidate_id ? `pm-import-candidate-review-draft:${candidate.candidate_id}` : null
  const taskShapingKey = localTaskShapingStorageKey(candidate)
  const previewStorageKey = approvalPreviewStorageKey(candidate)
  const readinessLabel = useMemo(() => {
    if (!online) return 'offline'
    if ((summary.blocker_count || 0) > 0) return 'blocked'
    if ((summary.warning_count || 0) > 0) return 'needs review'
    return 'ready for review'
  }, [online, summary.blocker_count, summary.warning_count])

  useEffect(() => {
    if (!draftStorageKey || typeof window === 'undefined') {
      return
    }
    setReviewDraft(window.localStorage.getItem(draftStorageKey) || '')
  }, [draftStorageKey])

  useEffect(() => {
    if (!candidate || !taskShapingKey || typeof window === 'undefined') {
      setTaskShapingDraft(null)
      return
    }

    setTaskShapingDraft(mergeLocalTaskShapingDraft(candidate, window.localStorage.getItem(taskShapingKey)))
  }, [candidate, taskShapingKey])

  useEffect(() => {
    if (!previewStorageKey || typeof window === 'undefined') {
      setStagedApprovalPreview(null)
      return
    }

    setStagedApprovalPreview(parseApprovalPreview(window.localStorage.getItem(previewStorageKey)))
  }, [previewStorageKey])

  useEffect(() => {
    if (!candidate) {
      setTaskPlanStatus(null)
      setTaskPlanMutationResult(null)
      setTaskPlanError(null)
      return
    }

    let cancelled = false

    void readTaskPlanStatus()
      .then((status) => {
        if (!cancelled) {
          setTaskPlanStatus(status)
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setTaskPlanError(error instanceof Error ? error.message : String(error))
        }
      })

    return () => {
      cancelled = true
    }
  }, [candidate])

  function handleDraftChange(value: string) {
    setReviewDraft(value)
    if (draftStorageKey && typeof window !== 'undefined') {
      window.localStorage.setItem(draftStorageKey, value)
    }
  }

  function clearDraft() {
    setReviewDraft('')
    if (draftStorageKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(draftStorageKey)
    }
  }

  function writeTaskShapingDraft(nextDraft: LocalTaskShapingDraft) {
    setTaskShapingDraft(nextDraft)
    if (taskShapingKey && typeof window !== 'undefined') {
      window.localStorage.setItem(taskShapingKey, JSON.stringify(nextDraft))
    }
  }

  function updateTaskShapingGroup(groupId: string, field: 'title' | 'designation', value: string) {
    if (!taskShapingDraft) {
      return
    }

    writeTaskShapingDraft({
      ...taskShapingDraft,
      groups: taskShapingDraft.groups.map((group) => (group.group_id === groupId ? { ...group, [field]: value } : group)),
    })
  }

  function updateTaskShapingApparatus(candidateId: string, field: keyof LocalTaskApparatusDraft, value: string) {
    if (!taskShapingDraft) {
      return
    }

    writeTaskShapingDraft({
      ...taskShapingDraft,
      apparatus: {
        ...taskShapingDraft.apparatus,
        [candidateId]: {
          ...(taskShapingDraft.apparatus[candidateId] || { group_id: '', display_name: '', designation: '' }),
          [field]: value,
        },
      },
    })
  }

  function addLocalTaskGroup() {
    if (!taskShapingDraft) {
      return
    }

    const nextCount = taskShapingDraft.groups.length + 1
    writeTaskShapingDraft({
      ...taskShapingDraft,
      groups: [
        ...taskShapingDraft.groups,
        {
          group_id: createManualTaskGroupId(nextCount),
          title: `Manual Task ${nextCount}`,
          designation: '',
          apparatus_type: 'mixed apparatus',
          drawing_ref: null,
          seeded_from_source: false,
          source_task_id: null,
        },
      ],
    })
  }

  function removeLocalTaskGroup(groupId: string) {
    if (!taskShapingDraft) {
      return
    }

    const hasAssignedApparatus = Object.values(taskShapingDraft.apparatus).some((apparatus) => apparatus.group_id === groupId)
    if (hasAssignedApparatus) {
      return
    }

    writeTaskShapingDraft({
      ...taskShapingDraft,
      groups: taskShapingDraft.groups.filter((group) => group.group_id !== groupId),
    })
  }

  function resetTaskShaping() {
    const nextDraft = buildDefaultLocalTaskShapingDraft(apparatusRows)
    setTaskShapingDraft(nextDraft)
    if (taskShapingKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(taskShapingKey)
    }
  }

  const localTaskGroups = useMemo(() => {
    if (!taskShapingDraft) {
      return [] as LocalTaskGroupSummary[]
    }

    const summaries = new Map<string, LocalTaskGroupSummary>()
    const sourceTaskCounts = new Map<string, Set<string>>()

    for (const group of taskShapingDraft.groups) {
      summaries.set(group.group_id, {
        ...group,
        apparatus_rows: [],
        planned_hours: 0,
        source_task_count: 0,
      })
    }

    for (const row of apparatusRows) {
      const apparatusDraft = taskShapingDraft.apparatus[row.candidate_id]
      const groupId = apparatusDraft?.group_id || row.default_group_id
      const summary = summaries.get(groupId)
      if (!summary) {
        continue
      }

      summary.apparatus_rows.push({
        ...row,
        group_id: groupId,
        display_name: apparatusDraft?.display_name || row.display_name,
        designation: apparatusDraft?.designation ?? row.designation,
      })
      summary.planned_hours += row.planned_hours

      if (!sourceTaskCounts.has(groupId)) {
        sourceTaskCounts.set(groupId, new Set())
      }
      sourceTaskCounts.get(groupId)?.add(row.source_task_id || row.default_group_id)
    }

    return taskShapingDraft.groups.map((group) => ({
      ...(summaries.get(group.group_id) || {
        ...group,
        apparatus_rows: [],
        planned_hours: 0,
        source_task_count: 0,
      }),
      source_task_count: sourceTaskCounts.get(group.group_id)?.size || 0,
    }))
  }, [apparatusRows, taskShapingDraft])

  const taskShapingSummary = useMemo(() => {
    if (!taskShapingDraft) {
      return {
        local_group_count: 0,
        regrouped_apparatus_count: 0,
        designation_override_count: 0,
      }
    }

    let regrouped = 0
    let overrides = 0

    for (const row of apparatusRows) {
      const apparatusDraft = taskShapingDraft.apparatus[row.candidate_id]
      if (!apparatusDraft) {
        continue
      }
      if (apparatusDraft.group_id !== row.default_group_id) {
        regrouped += 1
      }
      if (apparatusDraft.display_name !== row.display_name || apparatusDraft.designation !== row.designation) {
        overrides += 1
      }
    }

    return {
      local_group_count: taskShapingDraft.groups.length,
      regrouped_apparatus_count: regrouped,
      designation_override_count: overrides,
    }
  }, [apparatusRows, taskShapingDraft])

  const currentManualTaskShaping = useMemo(
    () => buildManualTaskShapingArtifact(taskShapingDraft, localTaskGroups, apparatusRows, taskShapingSummary),
    [apparatusRows, localTaskGroups, taskShapingDraft, taskShapingSummary],
  )

  const approvalPreviewCurrent = useMemo(
    () => approvalPreviewMatchesCurrentReview(stagedApprovalPreview, reviewDraft, currentManualTaskShaping),
    [currentManualTaskShaping, reviewDraft, stagedApprovalPreview],
  )

  async function persistDurableTaskPlan() {
    if (!candidate || !currentManualTaskShaping) {
      return
    }

    setPersistingTaskPlan(true)
    setTaskPlanError(null)

    try {
      const result = await submitTaskPlan(candidate, reviewDraft, currentManualTaskShaping)
      setTaskPlanMutationResult(result)
      if (result.status !== 'accepted' && result.status !== 'idempotent_hit') {
        setTaskPlanError(result.error?.message || 'Task-plan persistence was rejected')
        return
      }
      setTaskPlanStatus(await readTaskPlanStatus())
      setExportStatus('Durable PM task plan persisted for this candidate as planning-only rows.')
    } catch (error) {
      setTaskPlanError(error instanceof Error ? error.message : String(error))
    } finally {
      setPersistingTaskPlan(false)
    }
  }

  function exportCandidateJson() {
    if (!candidate || typeof document === 'undefined') {
      return
    }
    const exportPayload = {
      candidate,
      pm_review_draft: {
        storage: 'local_browser_only',
        mutation_authority: candidate.mutation_authority || 'not_admitted',
        notes: reviewDraft,
      },
      manual_task_shaping: currentManualTaskShaping,
    }
    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = candidateFileName(candidate)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
    setExportStatus(`${candidateFileName(candidate)} prepared from the current read-only candidate.`)
  }

  function exportApprovalPreviewJson() {
    if (!candidate || typeof document === 'undefined') {
      return
    }

    const preview = buildApprovalPreviewArtifact(candidate, reviewDraft, currentManualTaskShaping, notAllowed)
    const previewKey = approvalPreviewStorageKey(candidate)
    if (previewKey && typeof window !== 'undefined') {
      window.localStorage.setItem(previewKey, JSON.stringify(preview))
    }
    setStagedApprovalPreview(preview)

    const blob = new Blob([JSON.stringify(preview, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = approvalPreviewFileName(candidate)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
    setExportStatus(`${approvalPreviewFileName(candidate)} prepared from the current read-only candidate and staged for Approval readiness.`)
  }

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Import Candidate</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Review exceptions before import exists.</h1>
            <p className="lede">
              This route reads the Project Miner Temp Power import candidate and keeps review focused on warnings, required decisions, and source traceability. It does not approve, import, assign, schedule, or write production state.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Read seam</dt>
              <dd>/api/v1/reads/project-import-candidate</dd>
            </div>
            <div>
              <dt>Candidate</dt>
              <dd>{candidate?.candidate_id || 'waiting for candidate'}</dd>
            </div>
            <div>
              <dt>Mutation authority</dt>
              <dd>{candidate?.mutation_authority || 'not_admitted'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide pm-section-spaced">
        <article className="status-card">
          <div className="status-row">
            <h2>Candidate seam</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>{loading ? 'Loading candidate.' : `${formatCount(summary.task_count)} proposed tasks are ready for PM review.`}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Readiness</h2>
            <span className={`status-pill ${readinessLabel === 'blocked' ? 'status-deferred' : readinessLabel === 'needs review' ? 'status-awaiting-values' : 'status-configured'}`}>
              {readinessLabel}
            </span>
          </div>
          <p>Warnings and decisions are surfaced before dense apparatus rows.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Workpackages</h2>
            <span className="status-pill status-configured">{formatCount(summary.workpackage_count)}</span>
          </div>
          <p>Proposed groups from estimator sections and drawing context.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Apparatus</h2>
            <span className="status-pill status-backend-routed">{formatCount(summary.apparatus_candidate_count)}</span>
          </div>
          <p>Quantity-expanded candidates remain review-only.</p>
        </article>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Exception-First Review Packet</h2>
            <p>
              Start with required decisions and warning signals. Clean task rows stay collapsed so review time goes to the items that need judgment.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <Link href="/pm-review/import-intake">Intake workbench</Link>
            <Link href="/pm-review/import-admission-plan">Admission plan</Link>
            <Link href="/pm-review/import-approval-readiness">Approval readiness</Link>
            <button className="btn btn-outline" onClick={exportCandidateJson} disabled={!candidate}>
              Export JSON
            </button>
            <button className="btn btn-outline" onClick={exportApprovalPreviewJson} disabled={!candidate}>
              Export Approval Preview JSON
            </button>
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>
        {exportStatus ? <p className="pm-copy-muted pm-copy-main pm-section-status">{exportStatus}</p> : null}

        <section className="notes-grid pm-section-spaced" aria-label="Approval preview handoff status">
          <article className="notes-card pm-review-context-card">
            <h2>Approval Preview Handoff</h2>
            <p className="pm-copy-muted pm-copy-main">
              {stagedApprovalPreview
                ? approvalPreviewCurrent
                  ? 'Approval Preview JSON is already staged in this browser for Approval readiness and matches the current browser-local review context.'
                  : 'Approval Preview JSON is staged in this browser, but the current browser-local review context is newer. Re-export before downstream review so Approval readiness receives the latest notes and manual task shaping.'
                : 'No Approval Preview JSON is currently staged in this browser. Export it after your PM review notes and manual task shaping are ready for downstream review.'}
            </p>
            <dl className="contract-panel">
              <div>
                <dt>Stage state</dt>
                <dd>{stagedApprovalPreview ? 'staged browser-local context available' : 'not staged yet'}</dd>
              </div>
              <div>
                <dt>Stage freshness</dt>
                <dd>
                  {stagedApprovalPreview
                    ? approvalPreviewCurrent
                      ? 'current with the latest browser-local review context'
                      : 'stale relative to the latest browser-local review context'
                    : 'waiting for first approval preview export'}
                </dd>
              </div>
              <div>
                <dt>Generated locally</dt>
                <dd>{stagedApprovalPreview?.generated_locally_at || 'waiting for first approval preview export'}</dd>
              </div>
              <div>
                <dt>Next review route</dt>
                <dd>
                  <Link href="/pm-review/import-approval-readiness">/pm-review/import-approval-readiness</Link>
                </dd>
              </div>
            </dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Manual Task Authority Boundary</h2>
            <p className="pm-copy-muted pm-copy-main">
              Manual task shaping remains browser-local until you explicitly persist a durable task plan. That admitted action creates planning-only rows for PM grouping and designation decisions, while approval persistence, project import, assignments, schedule or status mutation, finance, and source writeback remain outside this lane.
            </p>
          </article>
          <article className="notes-card pm-review-context-card">
            <h2>Durable Task Plan</h2>
            <p className="pm-copy-muted pm-copy-main">
              {taskPlanStatus?.classification === 'task_plan_persisted'
                ? 'The current candidate already has a persisted PM task plan made from manual task shaping. These rows are planning-only and stay outside approval persistence, project import, assignment, schedule, status, finance, and source writeback.'
                : 'Persist the current manual task shaping as durable planning rows when you want PM grouping decisions to survive this browser and become the governed task-planning baseline.'}
            </p>
            <dl className="contract-panel">
              <div>
                <dt>Persistence state</dt>
                <dd>{taskPlanStatus?.classification || 'waiting for task-plan status'}</dd>
              </div>
              <div>
                <dt>Authority</dt>
                <dd>{taskPlanStatus?.task_plan_authority || 'not yet loaded'}</dd>
              </div>
              <div>
                <dt>Persisted rows</dt>
                <dd>
                  {taskPlanStatus?.persisted_row_counts
                    ? `${formatCount(taskPlanStatus.persisted_row_counts.tasks)} tasks · ${formatCount(taskPlanStatus.persisted_row_counts.apparatus)} apparatus`
                    : 'no planning rows persisted yet'}
                </dd>
              </div>
              <div>
                <dt>Blocked downstream</dt>
                <dd>{taskPlanStatus?.blocked_downstream?.length ? taskPlanStatus.blocked_downstream.join(', ') : 'approval, import, schedule, and finance remain blocked'}</dd>
              </div>
            </dl>
            <div className="pm-review-link-row pm-review-link-row-start pm-link-row-center">
              <button className="btn btn-outline" onClick={() => void persistDurableTaskPlan()} disabled={!candidate || !currentManualTaskShaping || persistingTaskPlan}>
                {persistingTaskPlan ? 'Persisting durable task plan...' : 'Persist durable task plan'}
              </button>
              <span className="pm-copy-muted pm-copy-main">Route: /api/v1/mutations/project-import-task-plans</span>
            </div>
            {taskPlanStatus?.persisted_at ? <p className="pm-copy-muted pm-copy-main pm-copy-top-sm">Last persisted at {taskPlanStatus.persisted_at}.</p> : null}
            {taskPlanError ? <p className="pm-copy-muted pm-copy-main pm-copy-top-sm">{taskPlanError}</p> : null}
          </article>
        </section>

        <section className="status-grid status-grid-wide pm-section-spaced" aria-label="Import candidate summary">
          <article className="status-card">
            <h2>Project</h2>
            <p>
              <strong>{project.name || 'unknown project'}</strong>
              <br />
              {project.location || 'unknown location'}
            </p>
          </article>
          <article className="status-card">
            <h2>Source</h2>
            <p>
              {formatLabel(project.source_format)}
              <br />
              {project.source_sheet || 'unknown sheet'}
            </p>
          </article>
          <article className="status-card">
            <h2>Warnings</h2>
            <p>
              {formatCount(summary.warning_count)} total · {formatCount(summary.blocker_count)} blockers
            </p>
          </article>
          <article className="status-card">
            <h2>Human Decisions</h2>
            <p>{formatCount(summary.human_decision_count)} prompts before any later import path.</p>
          </article>
          <article className="status-card">
            <h2>Source Fingerprint</h2>
            <p>
              {sourceFreshness?.aggregate_fingerprint || 'waiting'} · {formatCount(sourceFreshness?.missing_count)} missing
            </p>
          </article>
        </section>

        <section aria-label="Required decisions" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">Required Decisions</h2>
            <span className="status-pill status-awaiting-values">{formatCount(decisions.length)}</span>
          </div>
          <div className="pm-stack-md pm-top-md">
            {decisions.map((decision) => (
              <article key={decision.decision_id || decision.prompt} className="card pm-subcard">
                <div className="status-row pm-status-row-start">
                  <span className={`status-pill ${warningTone(decision.severity)}`}>{formatLabel(decision.severity)}</span>
                  {decision.warning_code ? <span className="status-pill status-backend-routed">{decision.warning_code}</span> : null}
                </div>
                <p className="pm-copy-main pm-copy-top-lg">{decision.prompt || 'Review candidate decision'}</p>
                <p className="pm-copy-muted pm-copy-main pm-copy-top-sm">
                  {decision.recommended_action || 'Confirm before the candidate can advance.'}
                </p>
              </article>
            ))}
            {!decisions.length ? <p className="pm-copy-muted">No required decisions are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Warning review" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">Warning Review</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(filteredWarnings.length)} of {formatCount(warnings.length)}
            </span>
          </div>
          <div className="pm-review-link-row pm-review-link-row-start" aria-label="Warning severity filters">
            {warningFilters.map((filter) => (
              <button
                key={filter}
                className="btn btn-outline"
                onClick={() => setWarningFilter(filter)}
              >
                {formatLabel(filter)}
              </button>
            ))}
            <select
              aria-label="Warning code filter"
              value={warningCodeFilter}
              onChange={(event) => setWarningCodeFilter(event.target.value)}
              className="pm-control-select-pill"
            >
              <option value="all">All warning codes</option>
              {warningCodes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </div>
          <div className="pm-stack-md pm-top-md">
            {filteredWarnings.map((warning) => (
              <article key={`${warning.code}-${warning.message}`} className="card pm-subcard">
                <div className="status-row pm-status-row-start">
                  <span className={`status-pill ${warningTone(warning.severity)}`}>{formatLabel(warning.severity)}</span>
                  <span className="status-pill status-backend-routed">{warning.code || 'WARNING'}</span>
                </div>
                <p className="pm-copy-main pm-copy-top-lg">{warning.message || 'Review warning'}</p>
                <p className="pm-copy-muted pm-copy-main pm-copy-top-sm">
                  {warning.review_action || 'Review before import.'}
                </p>
              </article>
            ))}
            {!warnings.length ? <p className="pm-copy-muted">No warnings are currently reported.</p> : null}
            {warnings.length && !filteredWarnings.length ? <p className="pm-copy-muted">No warnings match the active filter.</p> : null}
          </div>
        </section>

        <section aria-label="PM review questions draft" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">PM Questions Draft</h2>
            <span className="status-pill status-configured">local only</span>
          </div>
          <textarea
            aria-label="PM review notes draft"
            value={reviewDraft}
            onChange={(event) => handleDraftChange(event.target.value)}
            placeholder="Questions, duplicate rows to inspect, drawing cross-checks, or import approval blockers."
            className="pm-control-textarea"
          />
          <div className="pm-review-link-row pm-review-link-row-start pm-link-row-center">
            <button className="btn btn-outline" onClick={clearDraft} disabled={!reviewDraft}>
              Clear draft
            </button>
            <span className="pm-copy-muted pm-copy-main">
              {formatCount(reviewDraft.trim().length)} characters retained in this browser.
            </span>
          </div>
        </section>

        <section aria-label="Manual task shaping" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">Manual Task Shaping</h2>
            <span className="status-pill status-configured">browser local</span>
          </div>
          <p className="pm-copy-muted pm-copy-main pm-copy-top-lg">
            PM or Operations manager can regroup apparatus candidates into local task buckets, rename the task, and assign designations manually before any later admitted import or task-creation path exists.
          </p>
          <section className="status-grid status-grid-wide pm-top-lg pm-section-spaced">
            <article className="status-card">
              <h2>Local Task Groups</h2>
              <p>{formatCount(taskShapingSummary.local_group_count)} groups currently staged in this browser.</p>
            </article>
            <article className="status-card">
              <h2>Regrouped Apparatus</h2>
              <p>{formatCount(taskShapingSummary.regrouped_apparatus_count)} apparatus candidates have been moved away from the proposed source task.</p>
            </article>
            <article className="status-card">
              <h2>Label Overrides</h2>
              <p>{formatCount(taskShapingSummary.designation_override_count)} local naming or designation overrides are staged.</p>
            </article>
            <article className="status-card">
              <h2>Export Path</h2>
              <p>Export JSON downloads the full candidate packet. Approval Preview JSON stages browser-local downstream review context and still does not call mutations.</p>
            </article>
          </section>
          <div className="pm-review-link-row pm-review-link-row-start pm-link-row-bottom">
            <button className="btn btn-outline" onClick={addLocalTaskGroup} disabled={!taskShapingDraft}>
              Add local task group
            </button>
            <button className="btn btn-outline" onClick={resetTaskShaping} disabled={!taskShapingDraft}>
              Reset local shaping
            </button>
            <button className="btn btn-outline" onClick={() => void persistDurableTaskPlan()} disabled={!candidate || !currentManualTaskShaping || persistingTaskPlan}>
              {persistingTaskPlan ? 'Persisting durable task plan...' : 'Persist durable task plan'}
            </button>
            <span className="pm-copy-muted pm-copy-main">
              Browser-local planning remains available, and the admitted durable task-plan action persists only planning rows. Approval, full project import, assignment, schedule, status, finance, and source writeback remain blocked.
            </span>
          </div>
          {taskPlanMutationResult?.new_state?.row_counts ? (
            <p className="pm-copy-muted pm-copy-main pm-copy-top-sm">
              Latest durable task-plan write: {formatCount(taskPlanMutationResult.new_state.row_counts.tasks)} tasks and {formatCount(taskPlanMutationResult.new_state.row_counts.apparatus)} apparatus rows.
            </p>
          ) : null}
          <div className="pm-stack-md">
            {localTaskGroups.map((group) => {
              const canRemoveGroup = !group.seeded_from_source && group.apparatus_rows.length === 0
              return (
                <details key={group.group_id} className="card pm-subcard">
                  <summary className="pm-summary">
                    <strong>{group.title || 'Untitled local task'}</strong>
                    <span className="pm-summary-meta">
                      {' '}
                      · {formatCount(group.apparatus_rows.length)} apparatus · {formatHours(group.planned_hours)} hours · {group.designation || 'no designation'}
                    </span>
                  </summary>
                  <div className="pm-stack-lg pm-top-lg">
                    <div className="pm-form-grid-wide">
                      <label className="pm-field">
                        <span>Local task title</span>
                        <input
                          aria-label="Local task title"
                          value={group.title}
                          onChange={(event) => updateTaskShapingGroup(group.group_id, 'title', event.target.value)}
                          className="pm-control"
                        />
                      </label>
                      <label className="pm-field">
                        <span>Local task designation</span>
                        <input
                          aria-label="Local task designation"
                          value={group.designation}
                          onChange={(event) => updateTaskShapingGroup(group.group_id, 'designation', event.target.value)}
                          className="pm-control"
                        />
                      </label>
                    </div>
                    <p className="pm-copy-reset pm-copy-muted pm-copy-main">
                      {group.seeded_from_source
                        ? `Seeded from ${group.source_task_id || 'source task'} and fully editable here.`
                        : 'Manual task group added in this browser for local planning only.'}{' '}
                      {group.apparatus_type ? `Apparatus context: ${group.apparatus_type}.` : ''} {group.drawing_ref ? `Drawing ${group.drawing_ref}.` : ''}
                    </p>
                    {canRemoveGroup ? (
                      <div className="pm-review-link-row pm-review-link-row-start">
                        <button className="btn btn-outline" onClick={() => removeLocalTaskGroup(group.group_id)}>
                          Remove empty group
                        </button>
                      </div>
                    ) : null}
                    <div className="pm-stack-sm">
                      {group.apparatus_rows.map((apparatus) => (
                        <article key={apparatus.candidate_id} className="card pm-subcard">
                          <div className="status-row pm-status-row-top">
                            <div>
                              <p className="pm-copy-reset">
                                <strong>{apparatus.display_name}</strong>
                              </p>
                              <p className="pm-copy-muted pm-copy-detail pm-copy-top-xs">
                                Source task {apparatus.source_task_title} · row {apparatus.source_row ?? 'unknown'} · line {apparatus.source_line_id || 'unknown'}
                              </p>
                            </div>
                            <span className="status-pill status-backend-routed">{formatHours(apparatus.planned_hours)} hrs</span>
                          </div>
                          <div className="pm-form-grid-compact pm-top-sm">
                            <label className="pm-field">
                              <span>Local task group</span>
                              <select
                                aria-label="Local task group"
                                value={apparatus.group_id}
                                onChange={(event) => updateTaskShapingApparatus(apparatus.candidate_id, 'group_id', event.target.value)}
                                className="pm-control-select"
                              >
                                {taskShapingDraft?.groups.map((taskGroup) => (
                                  <option key={taskGroup.group_id} value={taskGroup.group_id}>
                                    {taskGroup.title || 'Untitled local task'}{taskGroup.designation ? ` (${taskGroup.designation})` : ''}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <label className="pm-field">
                              <span>Apparatus label</span>
                              <input
                                aria-label="Apparatus label"
                                value={apparatus.display_name}
                                onChange={(event) => updateTaskShapingApparatus(apparatus.candidate_id, 'display_name', event.target.value)}
                                className="pm-control"
                              />
                            </label>
                            <label className="pm-field">
                              <span>Apparatus designation</span>
                              <input
                                aria-label="Apparatus designation"
                                value={apparatus.designation}
                                onChange={(event) => updateTaskShapingApparatus(apparatus.candidate_id, 'designation', event.target.value)}
                                className="pm-control"
                              />
                            </label>
                          </div>
                        </article>
                      ))}
                      {!group.apparatus_rows.length ? (
                        <p className="pm-copy-reset pm-copy-muted pm-copy-main">
                          No apparatus are currently assigned to this local task group.
                        </p>
                      ) : null}
                    </div>
                  </div>
                </details>
              )
            })}
            {!localTaskGroups.length ? <p className="pm-copy-muted">No apparatus candidates are available for local task shaping.</p> : null}
          </div>
        </section>

        <section aria-label="Proposed project structure" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">Proposed Structure</h2>
            <span className="status-pill status-configured">{formatCount(workpackages.length)} groups</span>
          </div>
          <div className="pm-stack-md pm-top-md">
            {workpackages.map((workpackage) => {
              const tasks = workpackage.tasks || []
              return (
                <details key={workpackage.workpackage_id} className="card pm-subcard">
                  <summary className="pm-summary">
                    <strong>{workpackage.title || workpackage.workpackage_id}</strong>
                    <span className="pm-summary-meta">
                      {' '}
                      · {formatCount(workpackage.task_count)} tasks · {formatCount(workpackage.apparatus_candidate_count)} apparatus · {workpackage.planned_hours ?? 0} hours
                    </span>
                  </summary>
                  <p className="pm-copy-muted pm-copy-main pm-copy-top-md">
                    Drawing refs: {(workpackage.drawing_refs || []).join(', ') || 'none'} · Source rows: {sourceRows(tasks) || 'unknown'}
                  </p>
                  <div className="pm-stack-xs pm-top-sm">
                    {tasks.map((task) => (
                      <article key={task.task_id} className="card pm-subcard-compact">
                        <div className="status-row pm-status-row-top">
                          <div>
                            <p className="pm-copy-reset">
                              <strong>{task.title || task.task_id}</strong>
                            </p>
                            <p className="pm-copy-muted pm-copy-detail pm-copy-top-xs">
                              {task.designation || 'no designation'} · {task.apparatus_type || 'unknown apparatus'} · drawing {task.drawing_ref || 'unknown'}
                            </p>
                          </div>
                          <span className="status-pill status-backend-routed">
                            {formatCount(task.apparatus_candidates?.length)} apparatus
                          </span>
                        </div>
                        <p className="pm-copy-muted pm-copy-detail pm-copy-top-sm">
                          Source {task.source_ref?.source_sheet || 'unknown sheet'} row {task.source_ref?.source_row ?? 'unknown'} · line {task.source_ref?.line_id || 'unknown'}
                        </p>
                      </article>
                    ))}
                  </div>
                </details>
              )
            })}
            {!workpackages.length ? <p className="pm-copy-muted">No workpackages are currently proposed.</p> : null}
          </div>
        </section>

        <section className="status-grid status-grid-wide pm-section-spaced" aria-label="Resource context">
          <article className="status-card">
            <h2>Crew</h2>
            <p>{formatCount(summary.crew_count)} people in the current capability context.</p>
          </article>
          <article className="status-card">
            <h2>Equipment</h2>
            <p>{formatCount(summary.equipment_inventory_count)} inventory rows for readiness context.</p>
          </article>
          <article className="status-card">
            <h2>Capabilities</h2>
            <p>{formatCount(summary.capability_count)} capability rows available for later staffing review.</p>
          </article>
          <article className="status-card">
            <h2>Source Bundle</h2>
            <p>{sourceValue(sourceBundle.estimator_workbook_found)} estimator · {sourceValue(sourceBundle.capability_workbook_found)} capability.</p>
          </article>
        </section>

        <section aria-label="Source freshness" className="card pm-review-section">
          <div className="status-row">
            <h2 className="pm-section-title">Source Freshness</h2>
            <span className="status-pill status-backend-routed">{sourceFreshness?.strategy || 'pending'}</span>
          </div>
          <p className="pm-copy-muted pm-copy-main pm-copy-top-lg">
            {sourceFreshness?.review_action || 'Source freshness is waiting for the candidate read.'}
          </p>
          <div className="pm-stack-md pm-top-md">
            {sourceFiles.map((sourceFile) => (
              <article key={sourceFile.source_id || sourceFile.label} className="card pm-subcard">
                <div className="status-row pm-status-row-top">
                  <div>
                    <p className="pm-copy-reset">
                      <strong>{sourceFile.label || sourceFile.source_id || 'Source file'}</strong>
                    </p>
                    <p className="pm-copy-muted pm-copy-detail pm-copy-top-xs">
                      {sourceValue(sourceFile.path)}
                    </p>
                  </div>
                  <span className={`status-pill ${sourceFileTone(sourceFile.found)}`}>
                    {sourceFile.freshness_status || (sourceFile.found ? 'available' : 'missing')}
                  </span>
                </div>
                <p className="pm-copy-muted pm-copy-detail pm-copy-top-md">
                  Modified {sourceFile.modified_at || 'unknown'} · size {formatCount(sourceFile.size_bytes || undefined)} bytes · fingerprint {sourceFile.fingerprint || 'none'}
                </p>
              </article>
            ))}
            {!sourceFiles.length ? <p className="pm-copy-muted">No source file fingerprints are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Source traceability and guardrails" className="notes-grid">
          <article className="notes-card">
            <h2>Source Traceability</h2>
            <dl className="contract-panel">
              <div>
                <dt>Estimator</dt>
                <dd>{sourceValue(sourceBundle.estimator_workbook_path)}</dd>
              </div>
              <div>
                <dt>Drawing PDF</dt>
                <dd>{sourceValue(sourceBundle.sld_pdf_path)}</dd>
              </div>
              <div>
                <dt>Project data entry</dt>
                <dd>{sourceValue((sourceBundle.project_data_entry as Record<string, unknown> | undefined)?.path)}</dd>
              </div>
            </dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Guardrails</h2>
            <p>{candidate?.review_guidance?.primary_review_goal || 'Review candidate only. No production write is admitted.'}</p>
            <div className="pm-stack-lg pm-top-lg">
              <div>
                <p className="pm-label-heading">Allowed now</p>
                <ul>
                  {allowedNow.map((item) => (
                    <li key={item}>{formatLabel(item)}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="pm-label-heading">Not allowed now</p>
                <ul>
                  {notAllowed.map((item) => (
                    <li key={item}>{formatLabel(item)}</li>
                  ))}
                </ul>
              </div>
            </div>
          </article>
        </section>
      </section>
    </main>
  )
}
