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
}

type CandidateDecision = {
  decision_id?: string
  severity?: string
  prompt?: string
  recommended_action?: string
  warning_code?: string
}

type CandidateWorkpackage = {
  workpackage_id?: string
  title?: string
  drawing_refs?: string[]
  planned_hours?: number
  task_count?: number
  apparatus_candidate_count?: number
}

type CandidatePayload = {
  candidate_id?: string
  candidate_version?: string
  review_status?: string
  mutation_authority?: string
  project?: CandidateProject
  source_freshness?: {
    strategy?: string
    mutation_authority?: string
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

type AdmissionPlan = {
  admission_plan_id?: string
  admission_plan_version?: string
  candidate_id?: string
  readiness_status?: string
  mutation_authority?: string
  target_row_plan?: Record<string, number | string | null | undefined>
  no_go_checks?: Array<{
    check_id?: string
    status?: string
    message?: string
  }>
  future_import_sequence?: string[]
  not_allowed_now?: string[]
}

type ApprovalContract = {
  approval_contract_id?: string
  approval_contract_version?: string
  candidate_id?: string
  readiness_status?: string
  mutation_authority?: string
  persistence_authority?: string
  approval_record_contract?: {
    record_type?: string
    required_fields?: string[]
    permitted_decisions?: string[]
    operator_attestation?: string
  }
  future_mutation_contract?: {
    proposed_route?: string
    current_authority?: string
  }
  not_allowed_now?: string[]
}

type ApprovalStoragePlan = {
  storage_plan_id?: string
  storage_plan_version?: string
  candidate_id?: string
  mutation_authority?: string
  persistence_authority?: string
  selected_storage_decision?: string
  recommended_table?: string
  recommended_entity_type?: string
  recommended_route?: string
  adapter_requirements?: string[]
  rejected_storage_options?: Array<{
    option?: string
    reason?: string
  }>
  future_admission_sequence?: string[]
  not_allowed_now?: string[]
}

type IntakeWorkbenchPacket = {
  candidate: CandidatePayload
  admissionPlan: AdmissionPlan
  approvalContract: ApprovalContract
  storagePlan: ApprovalStoragePlan
}

type ReviewChecklistItem = {
  id: string
  label: string
  detail: string
}

type CloseoutChecklistItem = {
  id: string
  label: string
  detail: string
}

type FieldReadinessChecklistItem = {
  id: string
  label: string
  detail: string
}

type FieldQuestionsDraft = {
  drawing_source_questions: string
  site_access_safety_questions: string
  crew_equipment_questions: string
  material_staging_questions: string
  customer_constraint_questions: string
  pm_followup_notes: string
}

type FieldObservationScratchpad = {
  observation_date_or_shift: string
  observer_source: string
  workpackage_area_reference: string
  access_safety_observations: string
  material_equipment_observations: string
  open_questions_pm_followup: string
}

type ApprovalDecisionDraft = {
  decision: string
  review_notes: string
  local_attestation: boolean
}

type ReadinessGateStatus = 'ready' | 'blocked'

type ReadinessGate = {
  id: string
  title: string
  status: ReadinessGateStatus
  detail: string
}

type OperatingQueueStatus = 'complete' | 'next' | 'blocked'

type OperatingQueueItem = {
  id: string
  title: string
  status: OperatingQueueStatus
  detail: string
}

type FieldPrepCoverageStatus = 'covered' | 'partial' | 'open' | 'blocked'

type FieldPrepCoverageItem = {
  id: string
  title: string
  status: FieldPrepCoverageStatus
  detail: string
}

type FieldPrepAgendaStatus = 'context' | 'ask' | 'confirm' | 'blocked'

type FieldPrepAgendaItem = {
  id: string
  title: string
  status: FieldPrepAgendaStatus
  detail: string
}

type ImportExceptionRegisterStatus = 'covered' | 'open' | 'blocked'

type ImportExceptionRegisterItem = {
  id: string
  title: string
  status: ImportExceptionRegisterStatus
  detail: string
  evidence: string
}

type PmIntakeSnapshotStatus = 'covered' | 'open' | 'blocked'

type PmIntakeSnapshotItem = {
  id: string
  title: string
  status: PmIntakeSnapshotStatus
  detail: string
  evidence: string
}

type QuickJumpItem = {
  id: string
  label: string
  href: string
  detail: string
}

type QuickJumpGroup = {
  id: string
  label: string
  items: QuickJumpItem[]
}

type RouteLinkItem = {
  id: string
  label: string
  href: string
}

type RouteLinkGroup = {
  id: string
  label: string
  items: RouteLinkItem[]
}

type StartHereStatus = 'focus' | 'attention' | 'context' | 'blocked'

type StartHereItem = {
  id: string
  title: string
  status: StartHereStatus
  href: string
  detail: string
}

type DailyReviewScriptStatus = 'do-now' | 'confirm' | 'context' | 'blocked'

type DailyReviewScriptItem = {
  id: string
  title: string
  status: DailyReviewScriptStatus
  href: string
  detail: string
}

type OutputSelectorStatus = 'available-context' | 'needs-local-context' | 'field-context' | 'blocked'

type OutputSelectorItem = {
  id: string
  title: string
  status: Exclude<OutputSelectorStatus, 'blocked'>
  href: string
  detail: string
}

type HandoffGuideStatus = 'local-review' | 'field-context' | 'executor-context' | 'blocked'

type HandoffGuideItem = {
  id: string
  title: string
  status: HandoffGuideStatus
  href: string
  detail: string
}

type CommandCenterStatus = 'do-now' | 'ask-next' | 'prepare-context' | 'blocked'

type CommandCenterItem = {
  id: string
  title: string
  status: CommandCenterStatus
  href: string
  detail: string
}

type MeetingReadoutStatus = 'say-now' | 'ask-next' | 'context' | 'blocked'

type MeetingReadoutItem = {
  id: string
  title: string
  status: MeetingReadoutStatus
  href: string
  detail: string
}

type ConstraintRadarStatus = 'constraint' | 'attention' | 'context' | 'blocked'

type ConstraintRadarItem = {
  id: string
  title: string
  status: ConstraintRadarStatus
  href: string
  detail: string
}

type WorkflowMapStatus = 'source' | 'attention' | 'context' | 'draft' | 'prep' | 'audit' | 'blocked'

type WorkflowMapItem = {
  id: string
  title: string
  status: WorkflowMapStatus
  href: string
  detail: string
}

type OpenItemsStatus = 'open' | 'blocked' | 'context'

type OpenItemsLensItem = {
  id: string
  title: string
  status: OpenItemsStatus
  href: string
  detail: string
}

const { useCallback, useEffect, useMemo, useState } = React

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const READS_BASE = `${API_BASE}/reads`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }
const EMPTY_APPROVAL_DRAFT: ApprovalDecisionDraft = {
  decision: '',
  review_notes: '',
  local_attestation: false,
}
const EMPTY_FIELD_QUESTIONS_DRAFT: FieldQuestionsDraft = {
  drawing_source_questions: '',
  site_access_safety_questions: '',
  crew_equipment_questions: '',
  material_staging_questions: '',
  customer_constraint_questions: '',
  pm_followup_notes: '',
}
const EMPTY_FIELD_OBSERVATION_SCRATCHPAD: FieldObservationScratchpad = {
  observation_date_or_shift: '',
  observer_source: '',
  workpackage_area_reference: '',
  access_safety_observations: '',
  material_equipment_observations: '',
  open_questions_pm_followup: '',
}
const PM_INTAKE_ROUTE_LINKS: RouteLinkItem[] = [
  {
    id: 'return-shell',
    label: 'Return to shell',
    href: '/',
  },
  {
    id: 'import-candidate',
    label: 'Import candidate',
    href: '/pm-review/import-candidate',
  },
  {
    id: 'admission-plan',
    label: 'Admission plan',
    href: '/pm-review/import-admission-plan',
  },
  {
    id: 'approval-readiness',
    label: 'Approval readiness',
    href: '/pm-review/import-approval-readiness',
  },
  {
    id: 'pm-workfront',
    label: 'PM workfront',
    href: '/pm-review/workfront',
  },
]
const PM_INTAKE_ROUTE_LINK_GROUPS: RouteLinkGroup[] = [
  {
    id: 'shell',
    label: 'Shell',
    items: PM_INTAKE_ROUTE_LINKS.slice(0, 1),
  },
  {
    id: 'intake-reads',
    label: 'Intake Reads',
    items: PM_INTAKE_ROUTE_LINKS.slice(1, 4),
  },
  {
    id: 'pm-workfront',
    label: 'PM Workfront',
    items: PM_INTAKE_ROUTE_LINKS.slice(4),
  },
]
const PM_INTAKE_QUICK_JUMPS: QuickJumpItem[] = [
  {
    id: 'command-center',
    label: 'Command Center',
    href: '#pm-command-center',
    detail: 'Top local scan.',
  },
  {
    id: 'meeting-readout',
    label: 'Meeting Readout',
    href: '#pm-meeting-readout',
    detail: 'Conversation summary.',
  },
  {
    id: 'constraint-radar',
    label: 'Constraint Radar',
    href: '#pm-constraint-radar',
    detail: 'Constraint scan.',
  },
  {
    id: 'start-here',
    label: 'Start Here',
    href: '#pm-start-here',
    detail: 'First local focus.',
  },
  {
    id: 'daily-script',
    label: 'Daily Script',
    href: '#pm-daily-review-script',
    detail: 'Five-minute routine.',
  },
  {
    id: 'output-selector',
    label: 'Output Selector',
    href: '#pm-output-selector',
    detail: 'Choose an existing artifact.',
  },
  {
    id: 'handoff-guide',
    label: 'Handoff Guide',
    href: '#pm-handoff-guide',
    detail: 'Next context lane.',
  },
  {
    id: 'workflow-map',
    label: 'Workflow Map',
    href: '#pm-workflow-map',
    detail: 'Current intake path.',
  },
  {
    id: 'open-items',
    label: 'Open Items',
    href: '#pm-open-items',
    detail: 'Attention and blockers.',
  },
  {
    id: 'snapshot',
    label: 'Snapshot',
    href: '#pm-intake-snapshot',
    detail: 'Top scan view.',
  },
  {
    id: 'operating-queue',
    label: 'Operating Queue',
    href: '#pm-operating-queue',
    detail: 'Current local PM moves.',
  },
  {
    id: 'exception-register',
    label: 'Exception Register',
    href: '#import-exception-register',
    detail: 'Warning and decision synthesis.',
  },
  {
    id: 'project-packet',
    label: 'Project Packet',
    href: '#project-packet',
    detail: 'Candidate and source fingerprint.',
  },
  {
    id: 'workflow-gates',
    label: 'Workflow Gates',
    href: '#workflow-gates',
    detail: 'Read-only gate posture.',
  },
  {
    id: 'approval-readiness',
    label: 'Approval Readiness',
    href: '#approval-readiness',
    detail: 'Future persistence blockers.',
  },
  {
    id: 'field-prep',
    label: 'Field Prep',
    href: '#field-prep',
    detail: 'Local field-prep context.',
  },
  {
    id: 'executor-closeout',
    label: 'Executor Closeout',
    href: '#executor-closeout',
    detail: 'Returned executor evidence.',
  },
  {
    id: 'guardrails',
    label: 'Guardrails',
    href: '#guardrails',
    detail: 'Current boundaries.',
  },
]
const PM_INTAKE_QUICK_JUMP_GROUPS: QuickJumpGroup[] = [
  {
    id: 'daily-review',
    label: 'Daily Review',
    items: PM_INTAKE_QUICK_JUMPS.slice(0, 5),
  },
  {
    id: 'outputs-and-handoff',
    label: 'Outputs and Handoff',
    items: PM_INTAKE_QUICK_JUMPS.slice(5, 7),
  },
  {
    id: 'review-flow',
    label: 'Review Flow',
    items: PM_INTAKE_QUICK_JUMPS.slice(7, 12),
  },
  {
    id: 'source-field-guardrails',
    label: 'Source, Field, and Guardrails',
    items: PM_INTAKE_QUICK_JUMPS.slice(12),
  },
]
const REVIEW_CHECKLIST_ITEMS: ReviewChecklistItem[] = [
  {
    id: 'source_freshness_reviewed',
    label: 'Source freshness reviewed',
    detail: 'Source paths, modified times, and aggregate fingerprint were checked before relying on this candidate.',
  },
  {
    id: 'exceptions_reviewed',
    label: 'Warnings reviewed',
    detail: 'Candidate warnings and blocker counts were reviewed before moving toward approval planning.',
  },
  {
    id: 'pm_decisions_captured',
    label: 'PM decisions captured',
    detail: 'Human decision prompts were reviewed and any open questions were captured outside production state.',
  },
  {
    id: 'admission_no_go_reviewed',
    label: 'Admission no-go checks reviewed',
    detail: 'No-go checks and target row counts were reviewed before any future import packet.',
  },
  {
    id: 'approval_storage_understood',
    label: 'Approval storage understood',
    detail: 'The future approval table and route were reviewed as design-only, not admitted persistence.',
  },
  {
    id: 'hosted_parity_acknowledged',
    label: 'Hosted parity acknowledged',
    detail: 'Vercel and Render hosted parity still require executor closeout before production-read proof.',
  },
  {
    id: 'write_guardrails_confirmed',
    label: 'Write guardrails confirmed',
    detail: 'No Supabase write, approval persistence, import, assignment, schedule, or status mutation is admitted.',
  },
]
const CLOSEOUT_CHECKLIST_ITEMS: CloseoutChecklistItem[] = [
  {
    id: 'source_commit_recorded',
    label: 'Source commit recorded',
    detail: 'Executor return names the exact source branch and commit tested.',
  },
  {
    id: 'changed_files_listed',
    label: 'Changed files listed',
    detail: 'Executor return lists all changed repo files, or explicitly says no repo files changed.',
  },
  {
    id: 'hosted_action_evidence_captured',
    label: 'Hosted action evidence captured',
    detail: 'Executor return includes non-secret hosted action evidence or clearly states that hosted action was unavailable.',
  },
  {
    id: 'validation_results_captured',
    label: 'Validation results captured',
    detail: 'Executor return includes exact validation commands and exact results without summarizing failures as success.',
  },
  {
    id: 'final_verdict_classified',
    label: 'Final verdict classified',
    detail: 'Executor return uses a concrete final verdict such as PASS, PARTIAL_PASS_WITH_REMAINING_BLOCKER, or a blocked classification.',
  },
  {
    id: 'remaining_blocker_classified',
    label: 'Remaining blocker classified',
    detail: 'If the result is not PASS, the remaining blocker is classified with a specific hosted, schema, permission, or product-code cause.',
  },
  {
    id: 'guardrails_confirmed',
    label: 'Guardrails confirmed',
    detail: 'Executor return confirms no widened service, DNS, auth, ingress, secret, SQL, schema, approval, import, assignment, schedule, status, or AI mutation.',
  },
  {
    id: 'coordinator_recommendation_captured',
    label: 'Coordinator recommendation captured',
    detail: 'Executor return recommends one bounded next action such as record and continue, redelegate, open a product packet, or stop for stakeholder exception.',
  },
]
const FIELD_READINESS_CHECKLIST_ITEMS: FieldReadinessChecklistItem[] = [
  {
    id: 'drawing_source_questions_captured',
    label: 'Drawing and source questions captured',
    detail: 'Open drawing, estimator, or Project Data Entry source questions are captured for PM and lead review before field reliance.',
  },
  {
    id: 'scope_assumptions_reviewed',
    label: 'Scope assumptions reviewed',
    detail: 'Candidate workpackage and apparatus assumptions are reviewed as planning context only, not imported project scope.',
  },
  {
    id: 'site_access_contacts_captured',
    label: 'Site access and contacts captured',
    detail: 'Known site access, customer contact, escort, badging, and entry questions are captured for follow-up outside production state.',
  },
  {
    id: 'safety_planning_questions_captured',
    label: 'Safety planning questions captured',
    detail: 'JHA, PPE, LOTO, energization, and temp-power safety questions are captured for field discussion before any work authorization.',
  },
  {
    id: 'crew_equipment_questions_captured',
    label: 'Crew and equipment questions captured',
    detail: 'Crew, equipment, tooling, lift, and rental questions are captured as planning prompts only, not assignment or schedule state.',
  },
  {
    id: 'material_staging_questions_captured',
    label: 'Material and staging questions captured',
    detail: 'Material, apparatus staging, laydown, delivery, and receiving questions are captured before relying on the candidate shape.',
  },
  {
    id: 'customer_constraint_questions_captured',
    label: 'Customer constraint questions captured',
    detail: 'Customer, outage, access-window, milestone, and communication constraints are captured for PM review without changing schedule state.',
  },
  {
    id: 'field_authority_boundary_acknowledged',
    label: 'Field authority boundary acknowledged',
    detail: 'This checklist is field-prep evidence only and does not authorize work, create tasks, assign resources, schedule work, change status, or write production state.',
  },
]

function makeToken() {
  return `Bearer ${btoa(JSON.stringify(PM_ACTOR))}`
}

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${READS_BASE}/${path}`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error(`Failed to read ${path}`)
  }

  return (await response.json()) as T
}

async function readIntakeWorkbench(): Promise<IntakeWorkbenchPacket> {
  const [candidate, admissionPlan, approvalContract, storagePlan] = await Promise.all([
    readJson<CandidatePayload>('project-import-candidate'),
    readJson<AdmissionPlan>('project-import-admission-plan'),
    readJson<ApprovalContract>('project-import-approval-contract'),
    readJson<ApprovalStoragePlan>('project-import-approval-storage-plan'),
  ])

  return { candidate, admissionPlan, approvalContract, storagePlan }
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/[_-]/g, ' ')
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'unknown'
  if (Array.isArray(value)) return value.length ? value.map(formatValue).join(', ') : 'none'
  if (typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  return String(value)
}

function formatCount(value?: number | string | null) {
  if (typeof value === 'number' && Number.isFinite(value)) return value.toLocaleString()
  if (typeof value === 'string') return value
  return '0'
}

function statusTone(value?: string | null) {
  if (!value) return 'status-awaiting-values'
  if (value.includes('not_admitted') || value.includes('blocked') || value.includes('no_go')) return 'status-deferred'
  if (value.includes('needs') || value.includes('pending') || value.includes('future') || value.includes('design')) return 'status-awaiting-values'
  return 'status-configured'
}

function operatingQueueTone(status: OperatingQueueStatus) {
  if (status === 'complete') return 'status-configured'
  if (status === 'next') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldPrepCoverageTone(status: FieldPrepCoverageStatus) {
  if (status === 'covered') return 'status-configured'
  if (status === 'partial') return 'status-awaiting-values'
  if (status === 'open') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldPrepAgendaTone(status: FieldPrepAgendaStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'ask' || status === 'confirm') return 'status-awaiting-values'
  return 'status-deferred'
}

function importExceptionRegisterTone(status: ImportExceptionRegisterStatus) {
  if (status === 'covered') return 'status-configured'
  if (status === 'open') return 'status-awaiting-values'
  return 'status-deferred'
}

function pmIntakeSnapshotTone(status: PmIntakeSnapshotStatus) {
  if (status === 'covered') return 'status-configured'
  if (status === 'open') return 'status-awaiting-values'
  return 'status-deferred'
}

function startHereTone(status: StartHereStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function dailyReviewScriptTone(status: DailyReviewScriptStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function outputSelectorTone(status: OutputSelectorStatus) {
  if (status === 'available-context' || status === 'field-context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function handoffGuideTone(status: HandoffGuideStatus) {
  if (status === 'field-context' || status === 'executor-context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function commandCenterTone(status: CommandCenterStatus) {
  if (status === 'prepare-context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function meetingReadoutTone(status: MeetingReadoutStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function constraintRadarTone(status: ConstraintRadarStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function workflowMapTone(status: WorkflowMapStatus) {
  if (status === 'source' || status === 'context' || status === 'prep' || status === 'audit') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function openItemsTone(status: OpenItemsStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function uniqueItems(...lists: Array<string[] | undefined>) {
  return Array.from(new Set(lists.flatMap((items) => items || []))).sort()
}

function firstAvailable(...values: Array<string | undefined | null>) {
  return values.find((value): value is string => Boolean(value)) || 'not admitted'
}

function visibleWarnings(warnings: CandidateWarning[]) {
  return warnings.slice(0, 3)
}

function visibleDecisions(decisions: CandidateDecision[]) {
  return decisions.slice(0, 3)
}

function briefFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-intake-brief.md`
}

function approvalPreviewFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-packet-preview.json`
}

function executorHandoffFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-executor-handoff.md`
}

function fieldKickoffBriefFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-kickoff-brief.md`
}

function fieldObservationNotesFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-observation-notes.md`
}

function fieldPrepCoverageSnapshotFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-prep-coverage-snapshot.md`
}

function fieldPrepConversationAgendaFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-prep-conversation-agenda.md`
}

function fieldPrepPacketFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-prep-packet.md`
}

function importExceptionRegisterFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-import-exception-register.md`
}

function pmIntakeSnapshotFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pm-intake-snapshot.md`
}

function markdownList(items: string[]) {
  return items.length ? items.map((item) => `- ${item}`).join('\n') : '- none reported'
}

function formatMultilineMarkdown(value: string) {
  const trimmed = value.trim()
  return trimmed ? trimmed.replace(/\r\n/g, '\n').replace(/\n/g, '\n  ') : 'none entered'
}

function hasApprovalDraftContent(draft: ApprovalDecisionDraft) {
  return Boolean(draft.decision || draft.review_notes.trim() || draft.local_attestation)
}

function hasFieldQuestionsDraftContent(draft: FieldQuestionsDraft) {
  return Boolean(
    draft.drawing_source_questions.trim()
      || draft.site_access_safety_questions.trim()
      || draft.crew_equipment_questions.trim()
      || draft.material_staging_questions.trim()
      || draft.customer_constraint_questions.trim()
      || draft.pm_followup_notes.trim(),
  )
}

function hasFieldObservationScratchpadContent(draft: FieldObservationScratchpad) {
  return Boolean(
    draft.observation_date_or_shift.trim()
      || draft.observer_source.trim()
      || draft.workpackage_area_reference.trim()
      || draft.access_safety_observations.trim()
      || draft.material_equipment_observations.trim()
      || draft.open_questions_pm_followup.trim(),
  )
}

function buildFieldObservationLines(draft: FieldObservationScratchpad) {
  return [
    `Observation date or shift note: ${formatMultilineMarkdown(draft.observation_date_or_shift)}`,
    `Observer / source: ${formatMultilineMarkdown(draft.observer_source)}`,
    `Workpackage or area reference: ${formatMultilineMarkdown(draft.workpackage_area_reference)}`,
    `Access and safety observations: ${formatMultilineMarkdown(draft.access_safety_observations)}`,
    `Material, staging, or equipment observations: ${formatMultilineMarkdown(draft.material_equipment_observations)}`,
    `Open questions / PM follow-up: ${formatMultilineMarkdown(draft.open_questions_pm_followup)}`,
  ]
}

function fieldPrepCoverageStatus(hasCheck: boolean, hasText: boolean): FieldPrepCoverageStatus {
  if (hasCheck && hasText) return 'covered'
  if (hasCheck || hasText) return 'partial'
  return 'open'
}

function buildPersistenceReadinessGates(
  packet: IntakeWorkbenchPacket | null,
  approvalDraft: ApprovalDecisionDraft,
  reviewChecks: Record<string, boolean>,
): ReadinessGate[] {
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const checklistHasEvidence = REVIEW_CHECKLIST_ITEMS.some((item) => reviewChecks[item.id])
  const hasPacketContext = Boolean(packet && packet.candidate.candidate_id && packet.approvalContract && packet.storagePlan)

  return [
    {
      id: 'approval-preview-context',
      title: 'Approval preview context',
      status: hasPacketContext && draftComplete ? 'ready' : 'blocked',
      detail: hasPacketContext && draftComplete
        ? 'Local preview context can carry candidate, contract, storage, checklist, and decision-draft evidence.'
        : 'Prepare a complete local decision draft before treating the preview as later packet context.',
    },
    {
      id: 'review-checklist-evidence',
      title: 'Review checklist evidence',
      status: checklistHasEvidence ? 'ready' : 'blocked',
      detail: checklistHasEvidence
        ? 'Browser-local checklist evidence is present for the current candidate.'
        : 'Use the local checklist before relying on the preview as review context.',
    },
    {
      id: 'hosted-parity-closeout',
      title: 'Hosted parity closeout',
      status: 'blocked',
      detail: 'PM Lane 041A/041B must prove or precisely classify Vercel and Render hosted parity before live approval persistence is claimed.',
    },
    {
      id: 'schema-authority',
      title: 'Schema authority',
      status: 'blocked',
      detail: 'PM Lane 049 authored the schema and adapter admission design, but no SQL execution or schema migration is admitted.',
    },
    {
      id: 'approval-persistence-authority',
      title: 'Approval persistence authority',
      status: 'blocked',
      detail: 'No approval record may be persisted until a later packet admits the dedicated table and adapter implementation.',
    },
    {
      id: 'import-mutation-authority',
      title: 'Import mutation authority',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus import remain blocked until approval persistence is explicitly admitted and validated in a later packet.',
    },
  ]
}

function buildPmOperatingQueue(
  approvalDraft: ApprovalDecisionDraft,
  reviewChecks: Record<string, boolean>,
  persistenceReadinessGates: ReadinessGate[],
): OperatingQueueItem[] {
  const sourceAndWarningReviewDone = Boolean(reviewChecks.source_freshness_reviewed && reviewChecks.exceptions_reviewed)
  const checklistHasEvidence = REVIEW_CHECKLIST_ITEMS.some((item) => reviewChecks[item.id])
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const previewContextReady = persistenceReadinessGates.some((gate) => gate.id === 'approval-preview-context' && gate.status === 'ready')

  return [
    {
      id: 'source-exception-review',
      title: 'Review source and exceptions',
      status: sourceAndWarningReviewDone ? 'complete' : 'next',
      detail: sourceAndWarningReviewDone
        ? 'Source freshness and warning review are marked in local prep for the current candidate.'
        : 'Start with source freshness and warning review before relying on the candidate shape.',
    },
    {
      id: 'local-decision-draft',
      title: 'Prepare local decision draft',
      status: draftComplete ? 'complete' : checklistHasEvidence ? 'next' : 'blocked',
      detail: draftComplete
        ? 'A local decision value, review notes, and local-only attestation are present.'
        : checklistHasEvidence
          ? 'Add a local decision value, review notes, and local-only attestation for future packet context.'
          : 'Capture at least one local checklist item before preparing the decision draft.',
    },
    {
      id: 'review-artifact-export',
      title: 'Export review artifacts',
      status: previewContextReady && checklistHasEvidence ? 'next' : 'blocked',
      detail: previewContextReady && checklistHasEvidence
        ? 'Use the PM brief and approval preview JSON as browser-local context for the next admitted packet.'
        : 'Complete local checklist evidence and the decision draft before treating exports as packet context.',
    },
    {
      id: 'hosted-parity-executor-closeout',
      title: 'Hosted parity executor closeout',
      status: 'blocked',
      detail: 'PM Lane 041A/041B still need executor closeout before hosted parity can be claimed.',
    },
    {
      id: 'approval-persistence-implementation',
      title: 'Approval persistence implementation',
      status: 'blocked',
      detail: 'PM Lane 049 is design-only; schema and adapter implementation still need an explicit later packet.',
    },
    {
      id: 'project-import-packet',
      title: 'Project import packet',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus rows remain blocked until approval persistence is explicitly admitted and validated in a later packet.',
    },
  ]
}

function buildFieldPrepQueue(
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
): OperatingQueueItem[] {
  const readinessEvidencePresent = FIELD_READINESS_CHECKLIST_ITEMS.some((item) => fieldReadinessChecks[item.id])
  const fieldQuestionsPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldBoundaryAcknowledged = Boolean(fieldReadinessChecks.field_authority_boundary_acknowledged)
  const fieldPrepContextReady = readinessEvidencePresent && fieldQuestionsPresent

  return [
    {
      id: 'field-questions-draft',
      title: 'Capture field questions draft',
      status: fieldQuestionsPresent ? 'complete' : 'next',
      detail: fieldQuestionsPresent
        ? 'Browser-local field questions are present for the current candidate.'
        : 'Capture drawing/source, access/safety, material, customer, or PM follow-up questions before the kickoff brief is used.',
    },
    {
      id: 'field-readiness-evidence',
      title: 'Mark field readiness prep evidence',
      status: readinessEvidencePresent ? 'complete' : fieldQuestionsPresent ? 'next' : 'blocked',
      detail: readinessEvidencePresent
        ? 'Browser-local field readiness evidence is present for the current candidate.'
        : fieldQuestionsPresent
          ? 'Mark local field readiness evidence before treating the kickoff brief as conversation prep.'
          : 'Capture field questions before marking readiness evidence as useful prep context.',
    },
    {
      id: 'field-kickoff-brief-export',
      title: 'Export field kickoff prep brief',
      status: fieldPrepContextReady ? 'next' : 'blocked',
      detail: fieldPrepContextReady
        ? 'Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review.'
        : 'Field questions and readiness evidence are needed before the kickoff brief has useful prep context.',
    },
    {
      id: 'field-authority-boundary-review',
      title: 'Confirm field authority boundary',
      status: fieldBoundaryAcknowledged ? 'complete' : fieldPrepContextReady ? 'next' : 'blocked',
      detail: fieldBoundaryAcknowledged
        ? 'The local field-authority boundary is acknowledged for this candidate.'
        : fieldPrepContextReady
          ? 'Acknowledge that field prep evidence does not authorize work, tasks, assignments, schedules, or status changes.'
          : 'Field authority boundary review waits for field questions and readiness evidence.',
    },
    {
      id: 'production-execution-tracking',
      title: 'Production execution tracking',
      status: 'blocked',
      detail: 'No issue, task, assignment, schedule, status, import, approval, or production tracking write is admitted by this local workbench.',
    },
  ]
}

function buildFieldPrepCoverageSnapshot(
  reviewChecks: Record<string, boolean>,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldPrepCoverageItem[] {
  const drawingSourceQuestionText = Boolean(fieldQuestionsDraft.drawing_source_questions.trim())
  const accessSafetyText = Boolean(fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const crewEquipmentText = Boolean(fieldQuestionsDraft.crew_equipment_questions.trim())
  const materialStagingText = Boolean(fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const customerConstraintText = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim())
  const fieldBoundaryAcknowledged = Boolean(fieldReadinessChecks.field_authority_boundary_acknowledged)

  return [
    {
      id: 'source-drawing-coverage',
      title: 'Source and drawing coverage',
      status: fieldPrepCoverageStatus(Boolean(fieldReadinessChecks.drawing_source_questions_captured), drawingSourceQuestionText),
      detail: 'Uses the drawing/source readiness check and drawing/source question text as browser-local conversation coverage.',
    },
    {
      id: 'access-safety-coverage',
      title: 'Access and safety coverage',
      status: fieldPrepCoverageStatus(Boolean(fieldReadinessChecks.safety_planning_questions_captured), accessSafetyText),
      detail: 'Uses the safety planning readiness check plus site/access/safety questions or access/safety observation notes.',
    },
    {
      id: 'crew-equipment-coverage',
      title: 'Crew and equipment coverage',
      status: fieldPrepCoverageStatus(Boolean(fieldReadinessChecks.crew_equipment_questions_captured), Boolean(fieldQuestionsDraft.crew_equipment_questions.trim())),
      detail: 'Uses the crew/equipment readiness check and crew/equipment question text as local prep coverage.',
    },
    {
      id: 'material-staging-coverage',
      title: 'Material and staging coverage',
      status: fieldPrepCoverageStatus(Boolean(fieldReadinessChecks.material_staging_questions_captured), materialStagingText),
      detail: 'Uses the material/staging readiness check plus material/staging questions or material/equipment observation notes.',
    },
    {
      id: 'customer-constraint-coverage',
      title: 'Customer constraint coverage',
      status: fieldPrepCoverageStatus(Boolean(fieldReadinessChecks.customer_constraint_questions_captured), customerConstraintText),
      detail: 'Uses the customer constraint readiness check and customer constraint question text as local prep coverage.',
    },
    {
      id: 'field-authority-boundary',
      title: 'Field authority boundary',
      status: fieldBoundaryAcknowledged ? 'covered' : 'blocked',
      detail: fieldBoundaryAcknowledged
        ? 'The local field-prep authority boundary is acknowledged for this candidate.'
        : 'Boundary acknowledgement remains blocked until explicitly checked; local prep does not authorize work.',
    },
    {
      id: 'production-tracking-boundary',
      title: 'Production tracking boundary',
      status: 'blocked',
      detail: 'Production tracking remains blocked until a later packet explicitly admits the required write path.',
    },
  ]
}

function fieldPrepCoverageCounts(fieldPrepCoverageSnapshot: FieldPrepCoverageItem[]) {
  return {
    covered: fieldPrepCoverageSnapshot.filter((item) => item.status === 'covered').length,
    partial: fieldPrepCoverageSnapshot.filter((item) => item.status === 'partial').length,
    open: fieldPrepCoverageSnapshot.filter((item) => item.status === 'open').length,
    blocked: fieldPrepCoverageSnapshot.filter((item) => item.status === 'blocked').length,
  }
}

function fieldPrepCoverageSummary(counts: ReturnType<typeof fieldPrepCoverageCounts>) {
  return `${counts.covered} covered, ${counts.partial} partial, ${counts.open} open, ${counts.blocked} blocked`
}

function buildFieldPrepConversationAgenda(fieldPrepCoverageSnapshot: FieldPrepCoverageItem[]): FieldPrepAgendaItem[] {
  const coverageById = new Map(fieldPrepCoverageSnapshot.map((item) => [item.id, item]))
  const conversationCoverageItems = fieldPrepCoverageSnapshot.filter((item) =>
    item.id !== 'field-authority-boundary' && item.id !== 'production-tracking-boundary',
  )
  const hasConversationContext = conversationCoverageItems.some((item) => item.status === 'covered' || item.status === 'partial')
  const fieldBoundaryCoverage = coverageById.get('field-authority-boundary')

  const agendaItems = conversationCoverageItems.map((item): FieldPrepAgendaItem => {
    if (item.status === 'covered') {
      return {
        id: `${item.id}-agenda`,
        title: item.title,
        status: 'context',
        detail: `Use existing ${item.title.toLowerCase()} as conversation context and only revisit it if source or site context changes.`,
      }
    }

    if (item.status === 'partial') {
      return {
        id: `${item.id}-agenda`,
        title: item.title,
        status: 'confirm',
        detail: `Confirm the missing local check or note for ${item.title.toLowerCase()} before relying on the field-prep brief.`,
      }
    }

    return {
      id: `${item.id}-agenda`,
      title: item.title,
      status: 'ask',
      detail: `Ask PM, lead, customer, or field contact for ${item.title.toLowerCase()} context before the next field-prep conversation.`,
    }
  })

  agendaItems.push({
    id: 'field-authority-boundary-agenda',
    title: 'Field authority boundary conversation',
    status: fieldBoundaryCoverage?.status === 'covered' ? 'context' : hasConversationContext ? 'confirm' : 'blocked',
    detail: fieldBoundaryCoverage?.status === 'covered'
      ? 'Use the acknowledged local boundary as context: field-prep artifacts do not authorize work.'
      : hasConversationContext
        ? 'Confirm that local field-prep context does not authorize work, assignments, schedules, status changes, or production writes.'
        : 'Boundary conversation waits for at least one local field-prep coverage area.',
  })
  agendaItems.push({
    id: 'production-tracking-boundary-agenda',
    title: 'Production tracking boundary',
    status: 'blocked',
    detail: 'Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  })

  return agendaItems
}

function fieldPrepAgendaCounts(fieldPrepConversationAgenda: FieldPrepAgendaItem[]) {
  return {
    context: fieldPrepConversationAgenda.filter((item) => item.status === 'context').length,
    ask: fieldPrepConversationAgenda.filter((item) => item.status === 'ask').length,
    confirm: fieldPrepConversationAgenda.filter((item) => item.status === 'confirm').length,
    blocked: fieldPrepConversationAgenda.filter((item) => item.status === 'blocked').length,
  }
}

function fieldPrepAgendaSummary(counts: ReturnType<typeof fieldPrepAgendaCounts>) {
  return `${counts.context} context, ${counts.ask} ask, ${counts.confirm} confirm, ${counts.blocked} blocked`
}

function buildImportExceptionRegister(
  candidate: CandidatePayload | undefined,
  noGoChecks: AdmissionPlan['no_go_checks'],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
): ImportExceptionRegisterItem[] {
  const warnings = candidate?.warnings || []
  const decisions = candidate?.human_decisions || []
  const noGoCheckItems = noGoChecks || []
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const draftStarted = hasApprovalDraftContent(approvalDraft)
  const hasNoGoBlocker = noGoCheckItems.some((check) => (check.status || '').includes('no_go'))
  const noGoEvidence = noGoCheckItems.map((check) => `${formatLabel(check.check_id)}: ${formatLabel(check.status)} - ${check.message || 'Review check.'}`)

  return [
    {
      id: 'source-freshness-evidence',
      title: 'Source freshness evidence',
      status: reviewChecks.source_freshness_reviewed ? 'covered' : 'open',
      detail: reviewChecks.source_freshness_reviewed
        ? 'Source freshness review is marked in local prep for this candidate.'
        : 'Mark source freshness review before relying on the candidate shape for later packet context.',
      evidence: candidate?.source_freshness?.aggregate_fingerprint || 'unknown fingerprint',
    },
    {
      id: 'candidate-warning-signals',
      title: 'Candidate warning signals',
      status: warnings.length && !reviewChecks.exceptions_reviewed ? 'open' : 'covered',
      detail: warnings.length
        ? `${warnings.length} warning signal(s) are present for PM review.`
        : 'No candidate warnings are currently reported.',
      evidence: warnings.map((warning) => `${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`).join('; ') || 'none reported',
    },
    {
      id: 'human-decision-prompts',
      title: 'Human decision prompts',
      status: decisions.length && !reviewChecks.pm_decisions_captured && !draftStarted ? 'open' : 'covered',
      detail: decisions.length
        ? `${decisions.length} human decision prompt(s) need local PM context before any later import packet.`
        : 'No human decision prompts are currently reported.',
      evidence: decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'}`).join('; ') || 'none reported',
    },
    {
      id: 'admission-no-go-checks',
      title: 'Admission no-go checks',
      status: hasNoGoBlocker ? 'blocked' : reviewChecks.admission_no_go_reviewed ? 'covered' : 'open',
      detail: hasNoGoBlocker
        ? 'At least one admission no-go check keeps import mutation blocked.'
        : 'Admission no-go checks need local PM review before any later import packet.',
      evidence: noGoEvidence.join('; ') || 'none reported',
    },
    {
      id: 'local-decision-draft-evidence',
      title: 'Local decision draft evidence',
      status: draftComplete ? 'covered' : 'open',
      detail: draftComplete
        ? 'A decision value, review notes, and local-only attestation are present.'
        : 'Prepare a local decision value, review notes, and local-only attestation for future packet context.',
      evidence: `Decision draft: ${approvalDraft.decision || 'none selected'}; notes: ${formatMultilineMarkdown(approvalDraft.review_notes)}; attestation: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    },
    {
      id: 'future-write-boundary',
      title: 'Future write boundary',
      status: 'blocked',
      detail: 'Approval persistence, import rows, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
      evidence: 'A later packet must explicitly admit any write path before implementation.',
    },
  ]
}

function importExceptionRegisterCounts(register: ImportExceptionRegisterItem[]) {
  return {
    covered: register.filter((item) => item.status === 'covered').length,
    open: register.filter((item) => item.status === 'open').length,
    blocked: register.filter((item) => item.status === 'blocked').length,
  }
}

function importExceptionRegisterSummary(counts: ReturnType<typeof importExceptionRegisterCounts>) {
  return `${counts.covered} covered, ${counts.open} open, ${counts.blocked} blocked`
}

function buildPmIntakeSnapshot(
  persistenceReadinessGates: ReadinessGate[],
  operatingQueue: OperatingQueueItem[],
  importExceptionRegister: ImportExceptionRegisterItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  closeoutChecks: Record<string, boolean>,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  approvalDraft: ApprovalDecisionDraft,
): PmIntakeSnapshotItem[] {
  const registerCount = importExceptionRegisterCounts(importExceptionRegister)
  const nextQueueItem = operatingQueue.find((item) => item.status === 'next')
  const readyPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'ready').length
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const fieldReadinessCheckedCount = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id]).length
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const fieldPrepContextPresent = Boolean(
    FIELD_READINESS_CHECKLIST_ITEMS.some((item) => fieldReadinessChecks[item.id])
      || hasFieldQuestionsDraftContent(fieldQuestionsDraft)
      || hasFieldObservationScratchpadContent(fieldObservationScratchpad),
  )

  return [
    {
      id: 'exception-review-snapshot',
      title: 'Exception review snapshot',
      status: registerCount.open ? 'open' : 'covered',
      detail: `Import exception register: ${importExceptionRegisterSummary(registerCount)}.`,
      evidence: registerCount.open
        ? 'Open local exception evidence remains in the register.'
        : 'Local exception evidence is covered; future write boundaries may still be blocked.',
    },
    {
      id: 'decision-draft-snapshot',
      title: 'Decision draft snapshot',
      status: decisionDraftComplete ? 'covered' : 'open',
      detail: decisionDraftComplete
        ? 'Decision value, review notes, and local-only attestation are present.'
        : 'Decision value, review notes, and local-only attestation still need local draft context.',
      evidence: `Decision draft: ${approvalDraft.decision || 'none selected'}`,
    },
    {
      id: 'field-prep-snapshot',
      title: 'Field prep snapshot',
      status: fieldPrepContextPresent ? 'covered' : 'open',
      detail: `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}. Conversation agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
      evidence: `Field readiness checks: ${fieldReadinessCheckedCount} of ${FIELD_READINESS_CHECKLIST_ITEMS.length}; field questions draft: ${hasFieldQuestionsDraftContent(fieldQuestionsDraft) ? 'yes' : 'no'}; observation scratchpad: ${hasFieldObservationScratchpadContent(fieldObservationScratchpad) ? 'yes' : 'no'}.`,
    },
    {
      id: 'next-local-action-snapshot',
      title: 'Next local action snapshot',
      status: nextQueueItem ? 'open' : 'covered',
      detail: nextQueueItem ? `${nextQueueItem.title}: ${nextQueueItem.detail}` : 'No next local operating-queue item is currently reported.',
      evidence: `Executor closeout intake: ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} checked.`,
    },
    {
      id: 'approval-persistence-boundary',
      title: 'Approval persistence boundary',
      status: 'blocked',
      detail: `Approval persistence readiness gates: ${readyPersistenceGateCount} of ${persistenceReadinessGates.length} ready.`,
      evidence: 'Schema authority, approval persistence authority, and import mutation remain blocked until a later packet admits them.',
    },
    {
      id: 'hosted-parity-boundary',
      title: 'Hosted parity boundary',
      status: 'blocked',
      detail: 'PM Lane 041A/041B still own hosted Vercel promotion and Render mutation-seam parity evidence.',
      evidence: 'This snapshot is local-current only until hosted executor closeout is returned and audited.',
    },
  ]
}

function pmIntakeSnapshotCounts(snapshot: PmIntakeSnapshotItem[]) {
  return {
    covered: snapshot.filter((item) => item.status === 'covered').length,
    open: snapshot.filter((item) => item.status === 'open').length,
    blocked: snapshot.filter((item) => item.status === 'blocked').length,
  }
}

function pmIntakeSnapshotSummary(counts: ReturnType<typeof pmIntakeSnapshotCounts>) {
  return `${counts.covered} covered, ${counts.open} open, ${counts.blocked} blocked`
}

function buildPmIntakeStartHere(
  operatingQueue: OperatingQueueItem[],
  importExceptionRegister: ImportExceptionRegisterItem[],
  fieldPrepQueue: OperatingQueueItem[],
  pmIntakeSnapshot: PmIntakeSnapshotItem[],
  persistenceReadinessGates: ReadinessGate[],
): StartHereItem[] {
  const nextOperatingMove = operatingQueue.find((item) => item.status === 'next') || operatingQueue.find((item) => item.status === 'blocked')
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const snapshotCount = pmIntakeSnapshotCounts(pmIntakeSnapshot)
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const hasFieldPrepContext = fieldPrepQueue.some((item) => item.status === 'complete')
  const usefulExport = hasFieldPrepContext
    ? 'Use Export Field Prep Packet when the next conversation needs field-prep context.'
    : 'Use Export PM Brief first when the next review needs compact candidate, gate, and guardrail context.'

  return [
    {
      id: 'first-local-move',
      title: 'First local move',
      status: nextOperatingMove?.status === 'blocked' ? 'blocked' : 'focus',
      href: '#pm-operating-queue',
      detail: nextOperatingMove
        ? `${nextOperatingMove.title}: ${nextOperatingMove.detail}`
        : 'No local PM operating-queue item is currently reported.',
    },
    {
      id: 'exception-attention',
      title: 'Exception attention',
      status: exceptionCount.open ? 'attention' : exceptionCount.blocked ? 'blocked' : 'context',
      href: '#import-exception-register',
      detail: `Import exception register: ${importExceptionRegisterSummary(exceptionCount)}.`,
    },
    {
      id: 'field-prep-focus',
      title: 'Field-prep focus',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'focus',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : 'No local field-prep queue item is currently reported.',
    },
    {
      id: 'useful-local-export',
      title: 'Useful local export',
      status: 'context',
      href: hasFieldPrepContext ? '#field-prep' : '#pm-intake-snapshot',
      detail: usefulExport,
    },
    {
      id: 'blocked-future-authority',
      title: 'Blocked future authority',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked. Snapshot posture: ${pmIntakeSnapshotSummary(snapshotCount)}.`,
    },
  ]
}

function buildPmIntakeDailyReviewScript(
  candidate: CandidatePayload | undefined,
  importExceptionRegister: ImportExceptionRegisterItem[],
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): DailyReviewScriptItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const decisionDraftStarted = hasApprovalDraftContent(approvalDraft)
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint || 'source fingerprint pending'
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'minute-0-confirm-source-context',
      title: 'Minute 0: Confirm source context',
      status: sourceFingerprint === 'source fingerprint pending' ? 'do-now' : 'confirm',
      href: '#project-packet',
      detail: `${projectName}: source fingerprint ${sourceFingerprint}; candidate authority remains ${formatLabel(admissionAuthority)}.`,
    },
    {
      id: 'minute-1-scan-exceptions',
      title: 'Minute 1: Scan exceptions',
      status: exceptionCount.open ? 'do-now' : 'confirm',
      href: '#import-exception-register',
      detail: `Import exception register: ${importExceptionRegisterSummary(exceptionCount)}.`,
    },
    {
      id: 'minute-2-capture-local-draft-notes',
      title: 'Minute 2: Capture local draft notes',
      status: decisionDraftComplete ? 'context' : decisionDraftStarted ? 'confirm' : 'do-now',
      href: '#pm-operating-queue',
      detail: decisionDraftComplete
        ? 'Local decision draft has decision value, review notes, and local-only attestation for this browser-local review.'
        : decisionDraftStarted
          ? 'Local decision draft has partial browser-local context; confirm the missing decision, notes, or local-only attestation.'
          : 'Local decision draft has not started; capture decision value, review notes, and local-only attestation before any future persistence packet.',
    },
    {
      id: 'minute-3-check-field-prep-questions',
      title: 'Minute 3: Check field-prep questions',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'do-now',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `Field prep queue: ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. ${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : 'No local field-prep queue item is currently reported.',
    },
    {
      id: 'minute-4-name-blocked-future-authority',
      title: 'Minute 4: Name blocked future authority',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks are marked; ${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked and project import remains ${formatLabel(admissionAuthority)}.`,
    },
  ]
}

function buildPmIntakeCommandCenter(
  candidate: CandidatePayload | undefined,
  importExceptionRegister: ImportExceptionRegisterItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): CommandCenterItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const reviewCheckedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const sourceAndWarningReviewDone = Boolean(reviewChecks.source_freshness_reviewed && reviewChecks.exceptions_reviewed)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const hasFieldQuestions = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const hasFieldObservations = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint || 'source fingerprint pending'
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const doNowHref = exceptionCount.open || !sourceAndWarningReviewDone
    ? '#import-exception-register'
    : decisionDraftComplete
      ? '#pm-output-selector'
      : '#pm-operating-queue'
  const doNowDetail = exceptionCount.open || !sourceAndWarningReviewDone
    ? `${projectName}: start with source and exception review. Source fingerprint ${sourceFingerprint}; review checklist has ${reviewCheckedCount} of ${REVIEW_CHECKLIST_ITEMS.length} local checks marked and exceptions are ${importExceptionRegisterSummary(exceptionCount)}.`
    : decisionDraftComplete
      ? 'Local review context is captured; use the output selector to choose the existing local artifact for the next conversation or packet context.'
      : 'Source and exception review have local checklist context; capture local decision value, review notes, and local-only attestation next.'
  const handoffContextPresent = decisionDraftComplete || closeoutCheckedCount > 0 || hasFieldQuestions || hasFieldObservations

  return [
    {
      id: 'do-now-command-center',
      title: 'Do now',
      status: 'do-now',
      href: doNowHref,
      detail: doNowDetail,
    },
    {
      id: 'ask-next-command-center',
      title: 'Ask next',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'ask-next',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `Field prep queue is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. ${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : `Field prep queue is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked.`,
    },
    {
      id: 'prepare-handoff-command-center',
      title: 'Prepare handoff context',
      status: handoffContextPresent ? 'prepare-context' : 'do-now',
      href: handoffContextPresent ? '#pm-handoff-guide' : '#pm-output-selector',
      detail: handoffContextPresent
        ? `Local handoff context exists from decision draft: ${decisionDraftComplete ? 'yes' : 'no'}; closeout checks: ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length}; field questions: ${hasFieldQuestions ? 'yes' : 'no'}; field observations: ${hasFieldObservations ? 'yes' : 'no'}.`
        : 'Use the output selector after local decision notes, field questions, observation notes, or executor closeout evidence exist.',
    },
    {
      id: 'blocked-command-center',
      title: 'Still blocked',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked and project import remains ${formatLabel(admissionAuthority)}.`,
    },
  ]
}

function buildPmIntakeMeetingReadout(
  candidate: CandidatePayload | undefined,
  importExceptionRegister: ImportExceptionRegisterItem[],
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): MeetingReadoutItem[] {
  const project = candidate?.project || {}
  const summary = candidate?.summary || {}
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const decisionDraftStarted = hasApprovalDraftContent(approvalDraft)
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const hasFieldQuestions = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const hasFieldObservations = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const projectName = project.name || candidate?.candidate_id || 'current Project Miner candidate'
  const location = project.location || 'unknown location'
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint || 'source fingerprint pending'
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'project-meeting-readout',
      title: 'Project readout',
      status: 'context',
      href: '#project-packet',
      detail: `${projectName} in ${location}: ${formatCount(summary.workpackage_count)} workpackages, ${formatCount(summary.task_count)} tasks, and ${formatCount(summary.apparatus_candidate_count)} apparatus candidates are loaded from source fingerprint ${sourceFingerprint}.`,
    },
    {
      id: 'review-meeting-readout',
      title: 'Review posture',
      status: decisionDraftComplete ? 'context' : exceptionCount.open ? 'say-now' : 'ask-next',
      href: decisionDraftComplete ? '#pm-output-selector' : '#import-exception-register',
      detail: decisionDraftComplete
        ? `Local review notes are captured; exceptions are ${importExceptionRegisterSummary(exceptionCount)} for later packet context.`
        : decisionDraftStarted
          ? `Local review notes are partial; exceptions are ${importExceptionRegisterSummary(exceptionCount)}.`
          : `Exceptions are ${importExceptionRegisterSummary(exceptionCount)} and local review notes have not started.`,
    },
    {
      id: 'field-meeting-readout',
      title: 'Field ask',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : hasFieldQuestions || hasFieldObservations || completeFieldPrepQueueCount ? 'context' : 'ask-next',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `Field prep is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. ${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : `Field prep is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked.`,
    },
    {
      id: 'boundary-meeting-readout',
      title: 'Boundary statement',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked; project import remains ${formatLabel(admissionAuthority)}; executor closeout evidence is ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length}.`,
    },
  ]
}

function buildPmIntakeConstraintRadar(
  candidate: CandidatePayload | undefined,
  importExceptionRegister: ImportExceptionRegisterItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): ConstraintRadarItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const reviewCheckedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const decisionDraftStarted = hasApprovalDraftContent(approvalDraft)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const hasFieldQuestions = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const hasFieldObservations = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint || 'source fingerprint pending'
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'
  const reviewNotesState = decisionDraftComplete
    ? 'are captured'
    : decisionDraftStarted
      ? 'are partial'
      : 'have not started'

  return [
    {
      id: 'source-review-constraint',
      title: 'Source and review constraints',
      status: exceptionCount.open || !decisionDraftComplete ? 'attention' : 'context',
      href: '#import-exception-register',
      detail: `Source fingerprint ${sourceFingerprint}; review checklist has ${reviewCheckedCount} of ${REVIEW_CHECKLIST_ITEMS.length} local checks marked; exceptions are ${importExceptionRegisterSummary(exceptionCount)}; local review notes ${reviewNotesState}.`,
    },
    {
      id: 'field-prep-constraint',
      title: 'Field-prep constraints',
      status: blockedFieldPrepQueueCount ? 'attention' : 'context',
      href: '#field-prep',
      detail: `Field prep is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. Field questions present: ${hasFieldQuestions ? 'yes' : 'no'}; field observations present: ${hasFieldObservations ? 'yes' : 'no'}.`,
    },
    {
      id: 'executor-hosted-constraint',
      title: 'Executor and hosted constraints',
      status: closeoutCheckedCount ? 'attention' : 'blocked',
      href: '#executor-closeout',
      detail: `Executor closeout evidence is ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length}; hosted parity remains an external executor boundary and is not claimed here.`,
    },
    {
      id: 'future-write-authority-constraint',
      title: 'Future write authority constraints',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked; project import remains ${formatLabel(admissionAuthority)}; future write authority remains outside this browser-local workbench.`,
    },
  ]
}

function buildPmIntakeOutputSelector(
  approvalDraft: ApprovalDecisionDraft,
  reviewChecks: Record<string, boolean>,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): OutputSelectorItem[] {
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const reviewCheckedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const hasFieldQuestions = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const hasFieldObservations = hasFieldObservationScratchpadContent(fieldObservationScratchpad)

  return [
    {
      id: 'pm-brief-output',
      title: 'PM Brief',
      status: 'available-context',
      href: '#pm-intake-snapshot',
      detail: 'Use PM Brief when the next review needs compact candidate, gate, and guardrail context.',
    },
    {
      id: 'approval-preview-output',
      title: 'Approval Preview JSON',
      status: decisionDraftComplete && reviewCheckedCount ? 'available-context' : 'needs-local-context',
      href: '#pm-operating-queue',
      detail: decisionDraftComplete && reviewCheckedCount
        ? `Approval Preview JSON has local decision draft context and ${reviewCheckedCount} of ${REVIEW_CHECKLIST_ITEMS.length} review checks for a later admitted approval-persistence packet.`
        : 'Approval Preview JSON should wait on local decision value, review notes, local-only attestation, and checklist evidence for useful later-packet context.',
    },
    {
      id: 'executor-handoff-output',
      title: 'Executor Handoff',
      status: closeoutCheckedCount ? 'available-context' : 'needs-local-context',
      href: '#executor-closeout',
      detail: closeoutCheckedCount
        ? `Executor Handoff has ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks marked for returned executor context.`
        : 'Executor Handoff should wait on local closeout evidence checks when the next packet needs returned executor context.',
    },
    {
      id: 'field-kickoff-output',
      title: 'Field Kickoff Brief',
      status: hasFieldQuestions || completeFieldPrepQueueCount ? 'field-context' : 'needs-local-context',
      href: '#field-prep',
      detail: `Field Kickoff Brief is most useful after field questions or readiness evidence are captured; current field prep queue is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked.`,
    },
    {
      id: 'field-prep-packet-output',
      title: 'Field Prep Packet',
      status: hasFieldQuestions || hasFieldObservations || completeFieldPrepQueueCount ? 'field-context' : 'needs-local-context',
      href: '#field-prep',
      detail: `Field Prep Packet is the bundled field-prep artifact when the next conversation needs questions, coverage, agenda, readiness evidence, and observation context; current field prep queue is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked.`,
    },
  ]
}

function buildPmIntakeHandoffGuide(
  importExceptionRegister: ImportExceptionRegisterItem[],
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): HandoffGuideItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const decisionDraftState = decisionDraftComplete
    ? 'local decision draft has decision value, review notes, and local-only attestation'
    : hasApprovalDraftContent(approvalDraft)
      ? 'local decision draft has partial browser-local context'
      : 'local decision draft has not started'
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'jason-local-review-context',
      title: 'Jason local review',
      status: 'local-review',
      href: '#import-exception-register',
      detail: `Use the workbench for Jason review while exceptions are ${importExceptionRegisterSummary(exceptionCount)} and ${decisionDraftState}.`,
    },
    {
      id: 'field-conversation-context',
      title: 'Field conversation prep',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'field-context',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `Field prep queue is ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. ${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : 'No local field-prep queue item is currently reported.',
    },
    {
      id: 'bounded-executor-context',
      title: 'Bounded executor context',
      status: closeoutCheckedCount || decisionDraftComplete ? 'executor-context' : 'local-review',
      href: '#executor-closeout',
      detail: closeoutCheckedCount || decisionDraftComplete
        ? `Existing Executor Handoff context has ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks marked plus ${decisionDraftState}.`
        : 'Keep executor context local until review notes, local decision context, or closeout evidence are present.',
    },
    {
      id: 'hosted-parity-executor-boundary',
      title: 'Hosted parity executor boundary',
      status: 'blocked',
      href: '#approval-readiness',
      detail: 'Hosted Vercel and Render parity remain external executor lanes; this local workbench claims no hosted parity.',
    },
    {
      id: 'future-persistence-packet-boundary',
      title: 'Future approval-persistence packet boundary',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked and project import remains ${formatLabel(admissionAuthority)}.`,
    },
  ]
}

function buildPmIntakeWorkflowMap(
  candidate: CandidatePayload | undefined,
  importExceptionRegister: ImportExceptionRegisterItem[],
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): WorkflowMapItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const decisionDraftStarted = hasApprovalDraftContent(approvalDraft)
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'source-intake',
      title: 'Source intake',
      status: sourceFingerprint ? 'source' : 'attention',
      href: '#project-packet',
      detail: sourceFingerprint
        ? `Source fingerprint ${sourceFingerprint} is loaded for the current candidate.`
        : 'Source freshness is waiting for the candidate read.',
    },
    {
      id: 'exception-review',
      title: 'Exception review',
      status: exceptionCount.open ? 'attention' : exceptionCount.blocked ? 'blocked' : 'context',
      href: '#import-exception-register',
      detail: `Import exception register: ${importExceptionRegisterSummary(exceptionCount)}.`,
    },
    {
      id: 'decision-draft',
      title: 'Decision draft',
      status: decisionDraftComplete ? 'context' : decisionDraftStarted ? 'draft' : 'attention',
      href: '#pm-operating-queue',
      detail: decisionDraftComplete
        ? 'Local decision draft has a decision value, review notes, and local-only attestation.'
        : decisionDraftStarted
          ? 'Local decision draft has partial browser-local context.'
          : 'Decision draft has not started.',
    },
    {
      id: 'field-prep',
      title: 'Field prep',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'prep',
      href: '#field-prep',
      detail: nextFieldPrepMove
        ? `${nextFieldPrepMove.title}: ${nextFieldPrepMove.detail}`
        : 'No local field-prep queue item is currently reported.',
    },
    {
      id: 'executor-closeout',
      title: 'Executor closeout',
      status: closeoutCheckedCount ? 'audit' : 'attention',
      href: '#executor-closeout',
      detail: `${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout checks marked for returned executor evidence.`,
    },
    {
      id: 'approval-persistence-boundary',
      title: 'Approval persistence boundary',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked until a later packet admits that path.`,
    },
    {
      id: 'project-import-boundary',
      title: 'Project import boundary',
      status: 'blocked',
      href: '#guardrails',
      detail: `Project import remains ${formatLabel(admissionAuthority)} for project, workpackage, task, apparatus, assignment, schedule, and status rows.`,
    },
  ]
}

function buildPmIntakeOpenItemsLens(
  importExceptionRegister: ImportExceptionRegisterItem[],
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  closeoutChecks: Record<string, boolean>,
  persistenceReadinessGates: ReadinessGate[],
  admissionPlan: AdmissionPlan | undefined,
): OpenItemsLensItem[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const fieldPrepNextCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const fieldPrepBlockedCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'exception-review-open-items',
      title: 'Exception review',
      status: exceptionCount.open ? 'open' : exceptionCount.blocked ? 'blocked' : 'context',
      href: '#import-exception-register',
      detail: exceptionCount.open
        ? `${exceptionCount.open} local exception item(s) still need attention; ${exceptionCount.blocked} future boundary item(s) remain blocked.`
        : exceptionCount.blocked
          ? `Local exception attention is covered, but ${exceptionCount.blocked} future boundary item(s) remain blocked.`
          : 'No local exception items are currently open.',
    },
    {
      id: 'decision-draft-open-items',
      title: 'Decision draft',
      status: decisionDraftComplete ? 'context' : 'open',
      href: '#pm-operating-queue',
      detail: decisionDraftComplete
        ? 'Local decision value, review notes, and local-only attestation are present.'
        : 'Decision value, review notes, and local-only attestation still need local draft context.',
    },
    {
      id: 'field-prep-open-items',
      title: 'Field prep',
      status: fieldPrepNextCount ? 'open' : fieldPrepBlockedCount ? 'blocked' : 'context',
      href: '#field-prep',
      detail: `${fieldPrepNextCount} field-prep item(s) are next; ${fieldPrepBlockedCount} field-prep item(s) are blocked.`,
    },
    {
      id: 'executor-closeout-open-items',
      title: 'Executor closeout evidence',
      status: closeoutCheckedCount === CLOSEOUT_CHECKLIST_ITEMS.length ? 'context' : 'open',
      href: '#executor-closeout',
      detail: `${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks are marked.`,
    },
    {
      id: 'approval-persistence-open-items',
      title: 'Approval persistence boundary',
      status: 'blocked',
      href: '#approval-readiness',
      detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked until a later packet admits that path.`,
    },
    {
      id: 'project-import-open-items',
      title: 'Project import boundary',
      status: 'blocked',
      href: '#guardrails',
      detail: `Project import remains ${formatLabel(admissionAuthority)} for project, workpackage, task, apparatus, assignment, schedule, and status rows.`,
    },
  ]
}

function buildApprovalPacketPreview(
  packet: IntakeWorkbenchPacket,
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const approvalContract = packet.approvalContract
  const storagePlan = packet.storagePlan
  const checkedItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).map((item) => item.id)
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)

  return {
    preview_kind: 'pm_import_candidate_approval_packet_preview',
    preview_version: 'pm_import_candidate_approval_packet_preview_v1',
    generated_locally_at: new Date().toISOString(),
    mutation_authority: 'not_admitted',
    persistence_authority: approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted',
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: candidate.project?.name || null,
      project_location: candidate.project?.location || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
      warning_count: candidate.summary?.warning_count ?? null,
      blocker_count: candidate.summary?.blocker_count ?? null,
    },
    approval_contract: {
      approval_contract_id: approvalContract.approval_contract_id || null,
      approval_contract_version: approvalContract.approval_contract_version || null,
      record_type: approvalContract.approval_record_contract?.record_type || storagePlan.recommended_entity_type || null,
      required_fields: approvalContract.approval_record_contract?.required_fields || [],
      permitted_decisions: approvalContract.approval_record_contract?.permitted_decisions || [],
      operator_attestation: approvalContract.approval_record_contract?.operator_attestation || null,
    },
    storage_plan: {
      storage_plan_id: storagePlan.storage_plan_id || null,
      recommended_table: storagePlan.recommended_table || null,
      recommended_route: futureRoute,
      selected_storage_decision: storagePlan.selected_storage_decision || null,
      adapter_requirements: storagePlan.adapter_requirements || [],
    },
    local_review_evidence: {
      checklist_checked_count: checkedItems.length,
      checklist_total_count: REVIEW_CHECKLIST_ITEMS.length,
      checklist_checked_items: checkedItems,
      decision_draft: {
        decision: approvalDraft.decision || null,
        review_notes: approvalDraft.review_notes.trim() || null,
        local_attestation: approvalDraft.local_attestation,
        draft_complete: draftComplete,
      },
    },
    future_packet_boundary: {
      target_route: futureRoute,
      target_table: storagePlan.recommended_table || null,
      admission_plan_id: admissionPlan.admission_plan_id || null,
      not_allowed_now: notAllowed,
      required_later_authority: [
        'dedicated approval schema migration',
        'explicit approval persistence adapter',
        'hosted Vercel and Render parity closeout',
        'operator approval of the admitted persistence packet',
      ],
    },
  }
}

function buildIntakeBrief(
  packet: IntakeWorkbenchPacket,
  workflowGates: Array<{ title: string; status: string; detail: string }>,
  persistenceReadinessGates: ReadinessGate[],
  operatingQueue: OperatingQueueItem[],
  pmIntakeSnapshot: PmIntakeSnapshotItem[],
  pmIntakeConstraintRadar: ConstraintRadarItem[],
  importExceptionRegister: ImportExceptionRegisterItem[],
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  closeoutChecks: Record<string, boolean>,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const approvalContract = packet.approvalContract
  const storagePlan = packet.storagePlan
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const warnings = candidate.warnings || []
  const decisions = candidate.human_decisions || []
  const targetRows = admissionPlan.target_row_plan || {}

  const targetRowLines = Object.entries(targetRows).map(([key, value]) => `${formatLabel(key)}: ${formatValue(value)}`)
  const warningLines = warnings.map((warning) => `${warning.severity || 'unknown'} - ${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`)
  const decisionLines = decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'}`)
  const gateLines = workflowGates.map((gate) => `${gate.title}: ${formatLabel(gate.status)} - ${gate.detail}`)
  const persistenceGateLines = persistenceReadinessGates.map((gate) => `${gate.title}: ${formatLabel(gate.status)} - ${gate.detail}`)
  const operatingQueueLines = operatingQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const pmIntakeSnapshotLines = pmIntakeSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)
  const pmIntakeConstraintRadarLines = pmIntakeConstraintRadar.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const importExceptionRegisterLines = importExceptionRegister.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepCoverageLines = fieldPrepCoverageSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepAgendaLines = fieldPrepConversationAgenda.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const checklistLines = REVIEW_CHECKLIST_ITEMS.map((item) => `${reviewChecks[item.id] ? '[x]' : '[ ]'} ${item.label}: ${item.detail}`)
  const closeoutChecklistLines = CLOSEOUT_CHECKLIST_ITEMS.map((item) => `${closeoutChecks[item.id] ? '[x]' : '[ ]'} ${item.label}: ${item.detail}`)
  const fieldReadinessChecklistLines = FIELD_READINESS_CHECKLIST_ITEMS.map((item) => `${fieldReadinessChecks[item.id] ? '[x]' : '[ ]'} ${item.label}: ${item.detail}`)
  const checkedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const fieldReadinessCheckedCount = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id]).length
  const fieldQuestionsDraftPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldQuestionLines = [
    `Drawing/source questions: ${formatMultilineMarkdown(fieldQuestionsDraft.drawing_source_questions)}`,
    `Site access and safety questions: ${formatMultilineMarkdown(fieldQuestionsDraft.site_access_safety_questions)}`,
    `Crew and equipment questions: ${formatMultilineMarkdown(fieldQuestionsDraft.crew_equipment_questions)}`,
    `Material and staging questions: ${formatMultilineMarkdown(fieldQuestionsDraft.material_staging_questions)}`,
    `Customer constraint questions: ${formatMultilineMarkdown(fieldQuestionsDraft.customer_constraint_questions)}`,
    `PM follow-up notes: ${formatMultilineMarkdown(fieldQuestionsDraft.pm_followup_notes)}`,
  ]
  const fieldObservationScratchpadPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const fieldObservationLines = buildFieldObservationLines(fieldObservationScratchpad)
  const draftPresent = hasApprovalDraftContent(approvalDraft)
  const readyPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'ready').length
  const completeQueueCount = operatingQueue.filter((item) => item.status === 'complete').length
  const nextQueueCount = operatingQueue.filter((item) => item.status === 'next').length
  const blockedQueueCount = operatingQueue.filter((item) => item.status === 'blocked').length
  const pmIntakeSnapshotCount = pmIntakeSnapshotCounts(pmIntakeSnapshot)
  const importExceptionRegisterCount = importExceptionRegisterCounts(importExceptionRegister)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)

  return [
    '# Project Miner PM Intake Brief',
    '',
    'Generated locally from the read-only PM intake workbench. This brief is not approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    '## Project',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    '',
    '## Proposed Shape',
    '',
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Blockers: ${formatCount(summary.blocker_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Exceptions',
    '',
    markdownList(warningLines),
    '',
    '## PM Decisions',
    '',
    markdownList(decisionLines),
    '',
    '## Workflow Gates',
    '',
    markdownList(gateLines),
    '',
    '## Local Review Checklist',
    '',
    `Checklist progress: ${checkedCount} of ${REVIEW_CHECKLIST_ITEMS.length} checked.`,
    '',
    'This browser-local checklist is review prep only. It is not approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    markdownList(checklistLines),
    '',
    '## Local Approval Decision Draft',
    '',
    `Draft present: ${draftPresent ? 'yes' : 'no'}.`,
    '',
    'This browser-local decision draft is review prep only. It is not approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    `- Decision draft: ${approvalDraft.decision || 'none selected'}`,
    `- Local-only attestation checked: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    `- Review notes draft: ${formatMultilineMarkdown(approvalDraft.review_notes)}`,
    '',
    '## Approval Persistence Readiness',
    '',
    `Readiness gates ready: ${readyPersistenceGateCount} of ${persistenceReadinessGates.length}.`,
    '',
    'These readiness gates are local review context only. They do not approve, persist, import, assign, schedule, change status, or mutate production state.',
    '',
    markdownList(persistenceGateLines),
    '',
    '## PM Operating Queue',
    '',
    `Queue status: ${completeQueueCount} complete, ${nextQueueCount} next, ${blockedQueueCount} blocked.`,
    '',
    'This queue is local review guidance only. It does not approve, persist, import, assign, schedule, change status, or mutate production state.',
    '',
    markdownList(operatingQueueLines),
    '',
    '## Local PM Intake Snapshot',
    '',
    `PM intake snapshot: ${pmIntakeSnapshotSummary(pmIntakeSnapshotCount)}.`,
    '',
    'This snapshot is browser-local review synthesis only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, or write production state.',
    '',
    markdownList(pmIntakeSnapshotLines),
    '',
    '## Local PM Constraint Radar',
    '',
    'This radar is browser-local constraint synthesis only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, claim hosted parity, or write production state.',
    '',
    markdownList(pmIntakeConstraintRadarLines),
    '',
    '## Local Import Exception Decision Register',
    '',
    `Import exception register: ${importExceptionRegisterSummary(importExceptionRegisterCount)}.`,
    '',
    'This register is browser-local review synthesis only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, or write production state.',
    '',
    markdownList(importExceptionRegisterLines),
    '',
    '## Local Field Prep Queue',
    '',
    `Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked.`,
    '',
    'This queue is browser-local prep guidance only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, or production writes.',
    '',
    markdownList(fieldPrepQueueLines),
    '',
    '## Local Field Prep Coverage Snapshot',
    '',
    `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}.`,
    '',
    'This snapshot is browser-local conversation prep only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.',
    '',
    markdownList(fieldPrepCoverageLines),
    '',
    '## Local Field Prep Conversation Agenda',
    '',
    `Conversation agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
    '',
    'This agenda is browser-local conversation prep only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.',
    '',
    markdownList(fieldPrepAgendaLines),
    '',
    '## Local Executor Closeout Intake',
    '',
    `Closeout checks: ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} checked.`,
    '',
    'This browser-local closeout intake is audit prep only. It is not acceptance, approval, persistence, import, deployment, assignment, schedule, status, or production state.',
    '',
    markdownList(closeoutChecklistLines),
    '',
    '## Local Field Readiness Checklist',
    '',
    `Field readiness checks: ${fieldReadinessCheckedCount} of ${FIELD_READINESS_CHECKLIST_ITEMS.length} checked.`,
    '',
    'This browser-local field readiness checklist is prep evidence only. It is not work authorization, approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    markdownList(fieldReadinessChecklistLines),
    '',
    '## Local Field Questions Draft',
    '',
    `Draft present: ${fieldQuestionsDraftPresent ? 'yes' : 'no'}.`,
    '',
    'This browser-local field questions draft is prep context only. It is not a task, issue, work authorization, approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    markdownList(fieldQuestionLines),
    '',
    '## Local Field Observation Scratchpad',
    '',
    `Scratchpad present: ${fieldObservationScratchpadPresent ? 'yes' : 'no'}.`,
    '',
    'This browser-local observation scratchpad is field-prep context only. It is not a task, issue, work authorization, approval, persistence, import, assignment, schedule, status, or production state.',
    '',
    markdownList(fieldObservationLines),
    '',
    '## Admission And Approval',
    '',
    `- Admission plan: ${admissionPlan.admission_plan_id || 'unknown'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    `- Approval contract: ${approvalContract.approval_contract_id || 'unknown'}`,
    `- Approval persistence authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    `- Future approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Future approval route: ${futureRoute}`,
    '',
    '## Target Rows',
    '',
    markdownList(targetRowLines),
    '',
    '## Not Allowed Now',
    '',
    markdownList(notAllowed.map(formatLabel)),
  ].join('\n')
}

function buildExecutorHandoff(
  packet: IntakeWorkbenchPacket,
  workflowGates: Array<{ title: string; status: string; detail: string }>,
  persistenceReadinessGates: ReadinessGate[],
  operatingQueue: OperatingQueueItem[],
  pmIntakeSnapshot: PmIntakeSnapshotItem[],
  pmIntakeConstraintRadar: ConstraintRadarItem[],
  importExceptionRegister: ImportExceptionRegisterItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  closeoutChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const approvalContract = packet.approvalContract
  const storagePlan = packet.storagePlan
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const warnings = candidate.warnings || []
  const decisions = candidate.human_decisions || []
  const checkedItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id])
  const openChecklistItems = REVIEW_CHECKLIST_ITEMS.filter((item) => !reviewChecks[item.id])
  const checkedCloseoutItems = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id])
  const openCloseoutItems = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => !closeoutChecks[item.id])
  const nextQueueItems = operatingQueue.filter((item) => item.status === 'next')
  const blockedQueueItems = operatingQueue.filter((item) => item.status === 'blocked')
  const blockedReadinessGates = persistenceReadinessGates.filter((gate) => gate.status === 'blocked')
  const warningLines = warnings.map((warning) => `${warning.severity || 'unknown'} - ${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`)
  const decisionLines = decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'}`)
  const checkedLines = checkedItems.map((item) => `${item.label}: ${item.detail}`)
  const openChecklistLines = openChecklistItems.map((item) => `${item.label}: ${item.detail}`)
  const checkedCloseoutLines = checkedCloseoutItems.map((item) => `${item.label}: ${item.detail}`)
  const openCloseoutLines = openCloseoutItems.map((item) => `${item.label}: ${item.detail}`)
  const nextQueueLines = nextQueueItems.map((item) => `${item.title}: ${item.detail}`)
  const blockedQueueLines = blockedQueueItems.map((item) => `${item.title}: ${item.detail}`)
  const blockedGateLines = blockedReadinessGates.map((gate) => `${gate.title}: ${gate.detail}`)
  const workflowGateLines = workflowGates.map((gate) => `${gate.title}: ${formatLabel(gate.status)} - ${gate.detail}`)
  const pmIntakeSnapshotCount = pmIntakeSnapshotCounts(pmIntakeSnapshot)
  const pmIntakeSnapshotLines = pmIntakeSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)
  const pmIntakeConstraintRadarLines = pmIntakeConstraintRadar.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const importExceptionRegisterCount = importExceptionRegisterCounts(importExceptionRegister)
  const importExceptionRegisterLines = importExceptionRegister.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)

  return [
    '# Project Miner Intake Executor Handoff',
    '',
    'Generated locally from the read-only PM intake workbench. This handoff is context only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, or mutate production state.',
    '',
    '## Bounded Instruction',
    '',
    'Use this handoff only to review context, draft a later packet, or perform explicitly allowed read-only analysis. Do not treat this handoff as approval, persistence authority, import authority, hosted parity proof, or task creation.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Blockers: ${formatCount(summary.blocker_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Current PM Review State',
    '',
    `- Checklist checked: ${checkedItems.length} of ${REVIEW_CHECKLIST_ITEMS.length}`,
    `- Closeout checks: ${checkedCloseoutItems.length} of ${CLOSEOUT_CHECKLIST_ITEMS.length}`,
    `- Decision draft: ${approvalDraft.decision || 'none selected'}`,
    `- Local-only attestation checked: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    `- Review notes draft: ${formatMultilineMarkdown(approvalDraft.review_notes)}`,
    '',
    '## Checked Review Evidence',
    '',
    markdownList(checkedLines),
    '',
    '## Open Review Evidence',
    '',
    markdownList(openChecklistLines),
    '',
    '## Operating Queue',
    '',
    'Next local review moves:',
    '',
    markdownList(nextQueueLines),
    '',
    'Blocked future moves:',
    '',
    markdownList(blockedQueueLines),
    '',
    '## PM Intake Snapshot',
    '',
    `PM intake snapshot: ${pmIntakeSnapshotSummary(pmIntakeSnapshotCount)}.`,
    '',
    markdownList(pmIntakeSnapshotLines),
    '',
    '## PM Constraint Radar',
    '',
    'This radar is browser-local constraint synthesis only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, claim hosted parity, or write production state.',
    '',
    markdownList(pmIntakeConstraintRadarLines),
    '',
    '## Import Exception Decision Register',
    '',
    `Import exception register: ${importExceptionRegisterSummary(importExceptionRegisterCount)}.`,
    '',
    markdownList(importExceptionRegisterLines),
    '',
    '## Executor Closeout Intake',
    '',
    'This intake checklist is browser-local audit prep only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state.',
    '',
    'Checked closeout evidence:',
    '',
    markdownList(checkedCloseoutLines),
    '',
    'Open closeout evidence:',
    '',
    markdownList(openCloseoutLines),
    '',
    '## Approval Persistence Blockers',
    '',
    markdownList(blockedGateLines),
    '',
    '## Exceptions And Decisions',
    '',
    'Warnings:',
    '',
    markdownList(warningLines),
    '',
    'Human decisions:',
    '',
    markdownList(decisionLines),
    '',
    '## Workflow Gates',
    '',
    markdownList(workflowGateLines),
    '',
    '## Future Surfaces Are Not Admitted',
    '',
    `- Future approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Future approval route: ${futureRoute}`,
    `- Admission plan: ${admissionPlan.admission_plan_id || 'unknown'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    `- Approval contract: ${approvalContract.approval_contract_id || 'unknown'}`,
    `- Approval persistence authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Safe Next Packet Evidence',
    '',
    '- Keep exact read-only source and candidate identity visible.',
    '- Keep hosted Vercel and Render parity classified before claiming hosted proof.',
    '- Keep schema, approval persistence, and import mutation blocked unless a later packet explicitly admits them.',
    '- Preserve zero mutation calls for review-only work.',
    '- Do not widen backend routes, auth, ingress, secrets, SQL, workbook macros, assignment, schedule, status, or autonomous AI business-state authority.',
  ].join('\n')
}

function buildFieldKickoffBrief(
  packet: IntakeWorkbenchPacket,
  workflowGates: Array<{ title: string; status: string; detail: string }>,
  operatingQueue: OperatingQueueItem[],
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  closeoutChecks: Record<string, boolean>,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const approvalContract = packet.approvalContract
  const storagePlan = packet.storagePlan
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const warnings = candidate.warnings || []
  const decisions = candidate.human_decisions || []
  const workpackages = candidate.workpackages || []
  const checkedItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id])
  const checkedCloseoutItems = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id])
  const checkedFieldReadinessItems = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id])
  const openFieldReadinessItems = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => !fieldReadinessChecks[item.id])
  const nextQueueItems = operatingQueue.filter((item) => item.status === 'next')
  const blockedQueueItems = operatingQueue.filter((item) => item.status === 'blocked')
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepCoverageLines = fieldPrepCoverageSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const fieldPrepAgendaLines = fieldPrepConversationAgenda.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const warningLines = warnings.map((warning) => `${warning.severity || 'unknown'} - ${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`)
  const decisionLines = decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'}`)
  const workpackageLines = workpackages.map((workpackage) => {
    const drawingRefs = workpackage.drawing_refs?.length ? workpackage.drawing_refs.join(', ') : 'drawing refs not listed'
    return `${workpackage.title || workpackage.workpackage_id || 'Untitled workpackage'}: ${formatCount(workpackage.task_count)} tasks, ${formatCount(workpackage.apparatus_candidate_count)} apparatus candidates, drawings ${drawingRefs}`
  })
  const checkedReviewLines = checkedItems.map((item) => `${item.label}: ${item.detail}`)
  const checkedCloseoutLines = checkedCloseoutItems.map((item) => `${item.label}: ${item.detail}`)
  const checkedFieldReadinessLines = checkedFieldReadinessItems.map((item) => `${item.label}: ${item.detail}`)
  const openFieldReadinessLines = openFieldReadinessItems.map((item) => `${item.label}: ${item.detail}`)
  const fieldQuestionsDraftPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldQuestionLines = [
    `Drawing/source questions: ${formatMultilineMarkdown(fieldQuestionsDraft.drawing_source_questions)}`,
    `Site access and safety questions: ${formatMultilineMarkdown(fieldQuestionsDraft.site_access_safety_questions)}`,
    `Crew and equipment questions: ${formatMultilineMarkdown(fieldQuestionsDraft.crew_equipment_questions)}`,
    `Material and staging questions: ${formatMultilineMarkdown(fieldQuestionsDraft.material_staging_questions)}`,
    `Customer constraint questions: ${formatMultilineMarkdown(fieldQuestionsDraft.customer_constraint_questions)}`,
    `PM follow-up notes: ${formatMultilineMarkdown(fieldQuestionsDraft.pm_followup_notes)}`,
  ]
  const fieldObservationScratchpadPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const fieldObservationLines = buildFieldObservationLines(fieldObservationScratchpad)
  const nextQueueLines = nextQueueItems.map((item) => `${item.title}: ${item.detail}`)
  const blockedQueueLines = blockedQueueItems.map((item) => `${item.title}: ${item.detail}`)
  const workflowGateLines = workflowGates.map((gate) => `${gate.title}: ${formatLabel(gate.status)} - ${gate.detail}`)
  const fieldPrepLines = [
    'Confirm latest drawings, estimator source, and Project Data Entry source remain current before field reliance.',
    'Review warnings and human-decision prompts with PM before using the candidate shape for field planning.',
    'Use workpackage and apparatus counts to prepare questions, material review, and crew/equipment discussion only.',
    'Keep assignment, schedule, status, approval persistence, and import rows blocked until later admitted packets own those writes.',
  ]

  return [
    '# Project Miner Field Kickoff Prep Brief',
    '',
    'Generated locally from the read-only PM intake workbench. This brief is field-prep context only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, or mutate production state.',
    '',
    '## Field-Prep Boundary',
    '',
    'Use this brief to align PM, lead, and field review conversations before execution tracking exists in production state. Do not treat it as a work authorization, schedule, assignment, status update, hosted parity proof, approval record, import packet, or task creation.',
    '',
    '## Project Snapshot',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source sheet: ${project.source_sheet || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    '',
    '## Proposed Field Shape',
    '',
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Crew rows: ${formatCount(summary.crew_count)}`,
    `- Equipment inventory rows: ${formatCount(summary.equipment_inventory_count)}`,
    `- Capability rows: ${formatCount(summary.capability_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Blockers: ${formatCount(summary.blocker_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Workpackage Preview',
    '',
    markdownList(workpackageLines),
    '',
    '## Field Prep Questions',
    '',
    markdownList(fieldPrepLines),
    '',
    '## Exceptions And PM Decisions',
    '',
    'Warnings:',
    '',
    markdownList(warningLines),
    '',
    'Human decisions:',
    '',
    markdownList(decisionLines),
    '',
    '## Local Review Evidence',
    '',
    `- Review checklist: ${checkedItems.length} of ${REVIEW_CHECKLIST_ITEMS.length} checked`,
    `- Executor closeout intake: ${checkedCloseoutItems.length} of ${CLOSEOUT_CHECKLIST_ITEMS.length} checked`,
    `- Field readiness prep: ${checkedFieldReadinessItems.length} of ${FIELD_READINESS_CHECKLIST_ITEMS.length} checked`,
    `- Decision draft: ${approvalDraft.decision || 'none selected'}`,
    `- Local-only attestation checked: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    `- Review notes draft: ${formatMultilineMarkdown(approvalDraft.review_notes)}`,
    '',
    'Checked review evidence:',
    '',
    markdownList(checkedReviewLines),
    '',
    'Checked executor closeout evidence:',
    '',
    markdownList(checkedCloseoutLines),
    '',
    'Checked field readiness prep:',
    '',
    markdownList(checkedFieldReadinessLines),
    '',
    'Open field readiness prep:',
    '',
    markdownList(openFieldReadinessLines),
    '',
    '## Local Field Questions Draft',
    '',
    `Draft present: ${fieldQuestionsDraftPresent ? 'yes' : 'no'}.`,
    '',
    'This browser-local questions draft is prep context only. It does not create tasks, issues, work authorization, assignments, schedule state, status updates, approval records, import packets, or production writes.',
    '',
    markdownList(fieldQuestionLines),
    '',
    '## Local Field Observation Scratchpad',
    '',
    `Scratchpad present: ${fieldObservationScratchpadPresent ? 'yes' : 'no'}.`,
    '',
    'This browser-local observation scratchpad is field-prep context only. It does not create tasks, issues, work authorization, assignments, schedule state, status updates, approval records, import packets, or production writes.',
    '',
    markdownList(fieldObservationLines),
    '',
    '## Local Field Prep Queue',
    '',
    `Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked.`,
    '',
    'This queue is browser-local prep guidance only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, or production writes.',
    '',
    markdownList(fieldPrepQueueLines),
    '',
    '## Local Field Prep Coverage Snapshot',
    '',
    `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}.`,
    '',
    'This snapshot is browser-local conversation prep only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.',
    '',
    markdownList(fieldPrepCoverageLines),
    '',
    '## Local Field Prep Conversation Agenda',
    '',
    `Conversation agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
    '',
    'This agenda is browser-local conversation prep only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.',
    '',
    markdownList(fieldPrepAgendaLines),
    '',
    '## Local PM Operating Queue',
    '',
    'Next local moves:',
    '',
    markdownList(nextQueueLines),
    '',
    'Blocked future moves:',
    '',
    markdownList(blockedQueueLines),
    '',
    '## Workflow Gates',
    '',
    markdownList(workflowGateLines),
    '',
    '## Future Surfaces Are Not Admitted',
    '',
    `- Future approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Future approval route: ${futureRoute}`,
    `- Admission plan: ${admissionPlan.admission_plan_id || 'unknown'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    `- Approval contract: ${approvalContract.approval_contract_id || 'unknown'}`,
    `- Approval persistence authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Field-Prep Use',
    '',
    '- Use this brief as conversation prep and issue discovery only.',
    '- Do not create assignments, schedules, status changes, approval records, schema, SQL, or import rows from this brief.',
    '- Do not claim hosted parity from this local export.',
    '- Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildFieldObservationNotes(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  notAllowed: string[],
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const checkedFieldReadinessItems = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id])
  const fieldQuestionsDraftPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldObservationScratchpadPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const fieldObservationLines = buildFieldObservationLines(fieldObservationScratchpad)
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length

  return [
    '# Project Miner Local Field Observation Notes',
    '',
    'Generated locally from the read-only PM intake workbench. These notes are browser-local field-prep context only and grant no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, or mutate production state.',
    '',
    '## Field-Prep Boundary',
    '',
    'Use these notes to remember PM, lead, customer, and field conversation context. Do not treat them as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, hosted parity proof, or production tracking.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    '',
    '## Observation Scratchpad',
    '',
    `Scratchpad present: ${fieldObservationScratchpadPresent ? 'yes' : 'no'}.`,
    '',
    markdownList(fieldObservationLines),
    '',
    '## Local Field Prep Context',
    '',
    `- Field readiness prep: ${checkedFieldReadinessItems.length} of ${FIELD_READINESS_CHECKLIST_ITEMS.length} checked`,
    `- Field questions draft present: ${fieldQuestionsDraftPresent ? 'yes' : 'no'}`,
    `- Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked`,
    '',
    markdownList(fieldPrepQueueLines),
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Keep these notes local unless a later admitted packet owns a durable field record.',
    '- Use them as conversation prep and follow-up question capture only.',
    '- Do not create assignments, schedules, status changes, approval records, schema, SQL, task rows, issue rows, or import rows from these notes.',
    '- Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildFieldPrepCoverageSnapshotExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldObservationScratchpad: FieldObservationScratchpad,
  notAllowed: string[],
) {
  const candidate = packet.candidate
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepCoverageLines = fieldPrepCoverageSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldObservationScratchpadPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)

  return [
    '# Project Miner Local Field Prep Coverage Snapshot',
    '',
    'Generated locally from the read-only PM intake workbench. This snapshot is browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    '',
    '## Proposed Shape',
    '',
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Coverage Snapshot',
    '',
    `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}.`,
    '',
    markdownList(fieldPrepCoverageLines),
    '',
    '## Field Prep Queue Summary',
    '',
    `Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked.`,
    '',
    markdownList(fieldPrepQueueLines),
    '',
    '## Observation Presence',
    '',
    `- Field observation scratchpad present: ${fieldObservationScratchpadPresent ? 'yes' : 'no'}`,
    '',
    '## Production Tracking Boundary',
    '',
    '- Production execution tracking: blocked',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this as conversation prep only.',
    '- Do not treat this snapshot as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, durable field record, hosted parity proof, or production tracking.',
    '- Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildFieldPrepConversationAgendaExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
) {
  const candidate = packet.candidate
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepCoverageLines = fieldPrepCoverageSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const fieldPrepAgendaLines = fieldPrepConversationAgenda.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)

  return [
    '# Project Miner Local Field Prep Conversation Agenda',
    '',
    'Generated locally from the read-only PM intake workbench. This agenda is browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Conversation Agenda',
    '',
    `Conversation agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
    '',
    markdownList(fieldPrepAgendaLines),
    '',
    '## Coverage Context',
    '',
    `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}.`,
    '',
    markdownList(fieldPrepCoverageLines),
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this as conversation prep only.',
    '- Do not treat this agenda as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, durable field record, hosted parity proof, or production tracking.',
    '- Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildFieldPrepPacket(
  packet: IntakeWorkbenchPacket,
  workflowGates: Array<{ title: string; status: string; detail: string }>,
  operatingQueue: OperatingQueueItem[],
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  closeoutChecks: Record<string, boolean>,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const checkedReviewItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id])
  const checkedCloseoutItems = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id])
  const checkedFieldReadinessItems = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id])
  const workflowGateLines = workflowGates.map((gate) => `${gate.title}: ${formatLabel(gate.status)} - ${gate.detail}`)
  const operatingQueueLines = operatingQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepCoverageLines = fieldPrepCoverageSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldPrepAgendaLines = fieldPrepConversationAgenda.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
  const fieldQuestionLines = [
    `Drawing/source questions: ${formatMultilineMarkdown(fieldQuestionsDraft.drawing_source_questions)}`,
    `Site access and safety questions: ${formatMultilineMarkdown(fieldQuestionsDraft.site_access_safety_questions)}`,
    `Crew and equipment questions: ${formatMultilineMarkdown(fieldQuestionsDraft.crew_equipment_questions)}`,
    `Material and staging questions: ${formatMultilineMarkdown(fieldQuestionsDraft.material_staging_questions)}`,
    `Customer constraint questions: ${formatMultilineMarkdown(fieldQuestionsDraft.customer_constraint_questions)}`,
    `PM follow-up notes: ${formatMultilineMarkdown(fieldQuestionsDraft.pm_followup_notes)}`,
  ]
  const fieldObservationLines = buildFieldObservationLines(fieldObservationScratchpad)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const completeQueueCount = operatingQueue.filter((item) => item.status === 'complete').length
  const nextQueueCount = operatingQueue.filter((item) => item.status === 'next').length
  const blockedQueueCount = operatingQueue.filter((item) => item.status === 'blocked').length
  const fieldQuestionsDraftPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldObservationScratchpadPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const approvalDraftPresent = hasApprovalDraftContent(approvalDraft)

  return [
    '# Project Miner Local Field Prep Packet',
    '',
    'Generated locally from the read-only PM intake workbench. This packet is browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Drawings: ${project.drawing_package || 'unknown'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Field Prep Queue',
    '',
    `Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked.`,
    '',
    markdownList(fieldPrepQueueLines),
    '',
    '## Field Prep Coverage Snapshot',
    '',
    `Coverage snapshot: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}.`,
    '',
    markdownList(fieldPrepCoverageLines),
    '',
    '## Field Prep Conversation Agenda',
    '',
    `Conversation agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
    '',
    markdownList(fieldPrepAgendaLines),
    '',
    '## Field Readiness Evidence',
    '',
    `Field readiness checks: ${checkedFieldReadinessItems.length} of ${FIELD_READINESS_CHECKLIST_ITEMS.length} checked.`,
    '',
    markdownList(checkedFieldReadinessItems.map((item) => `${item.label}: ${item.detail}`)),
    '',
    '## Field Questions Draft',
    '',
    `Draft present: ${fieldQuestionsDraftPresent ? 'yes' : 'no'}.`,
    '',
    markdownList(fieldQuestionLines),
    '',
    '## Field Observation Scratchpad',
    '',
    `Scratchpad present: ${fieldObservationScratchpadPresent ? 'yes' : 'no'}.`,
    '',
    markdownList(fieldObservationLines),
    '',
    '## Review And Closeout Context',
    '',
    `- Review checklist: ${checkedReviewItems.length} of ${REVIEW_CHECKLIST_ITEMS.length} checked`,
    `- Executor closeout intake: ${checkedCloseoutItems.length} of ${CLOSEOUT_CHECKLIST_ITEMS.length} checked`,
    `- PM operating queue: ${completeQueueCount} complete, ${nextQueueCount} next, ${blockedQueueCount} blocked`,
    `- Decision draft present: ${approvalDraftPresent ? 'yes' : 'no'}`,
    `- Decision draft value: ${approvalDraft.decision || 'none selected'}`,
    `- Local-only attestation checked: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    `- Review notes draft: ${formatMultilineMarkdown(approvalDraft.review_notes)}`,
    '',
    markdownList(operatingQueueLines),
    '',
    '## Workflow Gates',
    '',
    markdownList(workflowGateLines),
    '',
    '## Future Surfaces Are Not Admitted',
    '',
    `- Future approval route: ${futureRoute}`,
    `- Future approval table: ${packet.storagePlan.recommended_table || 'not admitted'}`,
    '- Approval persistence, project import, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this packet as conversation prep only.',
    '- Do not create assignments, schedules, status changes, approval records, schema, SQL, task rows, issue rows, durable field records, production tracking rows, or import rows from this packet.',
    '- Keep production execution tracking blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildImportExceptionRegisterExport(
  packet: IntakeWorkbenchPacket,
  importExceptionRegister: ImportExceptionRegisterItem[],
  notAllowed: string[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const storagePlan = packet.storagePlan
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const warnings = candidate.warnings || []
  const decisions = candidate.human_decisions || []
  const noGoChecks = admissionPlan.no_go_checks || []
  const registerCount = importExceptionRegisterCounts(importExceptionRegister)
  const registerLines = importExceptionRegister.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)
  const warningLines = warnings.map((warning) => `${warning.severity || 'unknown'} - ${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`)
  const decisionLines = decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'} Recommended action: ${decision.recommended_action || 'Review before future import.'}`)
  const noGoLines = noGoChecks.map((check) => `${formatLabel(check.check_id)}: ${formatLabel(check.status)} - ${check.message || 'Review check.'}`)
  const checkedReviewLines = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).map((item) => `${item.label}: ${item.detail}`)
  const openReviewLines = REVIEW_CHECKLIST_ITEMS.filter((item) => !reviewChecks[item.id]).map((item) => `${item.label}: ${item.detail}`)

  return [
    '# Project Miner Local Import Exception Decision Register',
    '',
    'Generated locally from the read-only PM intake workbench. This register is browser-local review synthesis only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Register Summary',
    '',
    `Import exception register: ${importExceptionRegisterSummary(registerCount)}.`,
    '',
    markdownList(registerLines),
    '',
    '## Warning Signals',
    '',
    markdownList(warningLines),
    '',
    '## Human Decision Prompts',
    '',
    markdownList(decisionLines),
    '',
    '## Admission No-Go Checks',
    '',
    markdownList(noGoLines),
    '',
    '## Local Review Evidence',
    '',
    'Checked review evidence:',
    '',
    markdownList(checkedReviewLines),
    '',
    'Open review evidence:',
    '',
    markdownList(openReviewLines),
    '',
    '## Local Decision Draft',
    '',
    `- Decision draft: ${approvalDraft.decision || 'none selected'}`,
    `- Local-only attestation checked: ${approvalDraft.local_attestation ? 'yes' : 'no'}`,
    `- Review notes draft: ${formatMultilineMarkdown(approvalDraft.review_notes)}`,
    '',
    '## Future Surfaces Are Not Admitted',
    '',
    `- Future approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Future approval route: ${storagePlan.recommended_route || 'not admitted'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    '- Approval persistence, import rows, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this register as exception-review synthesis only.',
    '- Do not treat this register as approval, persistence authority, import authority, work authorization, assignment, schedule, status update, task creation, issue creation, durable field record, hosted parity proof, or production tracking.',
    '- Keep approval persistence and project import blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function buildPmIntakeSnapshotExport(
  packet: IntakeWorkbenchPacket,
  pmIntakeSnapshot: PmIntakeSnapshotItem[],
  notAllowed: string[],
  futureRoute: string,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const storagePlan = packet.storagePlan
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const snapshotCount = pmIntakeSnapshotCounts(pmIntakeSnapshot)
  const snapshotLines = pmIntakeSnapshot.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail} Evidence: ${item.evidence}`)

  return [
    '# Project Miner Local PM Intake Snapshot',
    '',
    'Generated locally from the read-only PM intake workbench. This snapshot is browser-local review synthesis only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.',
    '',
    '## Candidate Context',
    '',
    `- Candidate: ${candidate.candidate_id || 'unknown'}`,
    `- Candidate version: ${candidate.candidate_version || 'unknown'}`,
    `- Candidate authority: ${candidate.mutation_authority || 'not_admitted'}`,
    `- Project: ${project.name || 'unknown project'}`,
    `- Location: ${project.location || 'unknown location'}`,
    `- Source freshness: ${candidate.source_freshness?.aggregate_fingerprint || 'unknown'}`,
    `- Workpackages: ${formatCount(summary.workpackage_count)}`,
    `- Tasks: ${formatCount(summary.task_count)}`,
    `- Apparatus candidates: ${formatCount(summary.apparatus_candidate_count)}`,
    `- Warnings: ${formatCount(summary.warning_count)}`,
    `- Human decisions: ${formatCount(summary.human_decision_count)}`,
    '',
    '## Snapshot Summary',
    '',
    `PM intake snapshot: ${pmIntakeSnapshotSummary(snapshotCount)}.`,
    '',
    markdownList(snapshotLines),
    '',
    '## Future Surfaces Are Not Admitted',
    '',
    `- Future approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Future approval route: ${futureRoute}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    '- Approval persistence, project import, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this snapshot as scan-level PM review synthesis only.',
    '- Do not treat this snapshot as approval, persistence authority, import authority, work authorization, assignment, schedule, status update, task creation, issue creation, durable field record, hosted parity proof, or production tracking.',
    '- Keep approval persistence and project import blocked until a later packet explicitly admits the required write path.',
  ].join('\n')
}

function downloadTextFile(fileName: string, contents: string, contentType: string) {
  const blob = new Blob([contents], { type: contentType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export default function ProjectMinerIntakeWorkbenchPage() {
  const [packet, setPacket] = useState<IntakeWorkbenchPacket | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [briefStatus, setBriefStatus] = useState('')
  const [previewStatus, setPreviewStatus] = useState('')
  const [handoffStatus, setHandoffStatus] = useState('')
  const [pmIntakeSnapshotStatus, setPmIntakeSnapshotStatus] = useState('')
  const [exceptionRegisterStatus, setExceptionRegisterStatus] = useState('')
  const [fieldBriefStatus, setFieldBriefStatus] = useState('')
  const [fieldObservationStatus, setFieldObservationStatus] = useState('')
  const [fieldPrepCoverageStatus, setFieldPrepCoverageStatus] = useState('')
  const [fieldPrepAgendaStatus, setFieldPrepAgendaStatus] = useState('')
  const [fieldPrepPacketStatus, setFieldPrepPacketStatus] = useState('')
  const [reviewChecks, setReviewChecks] = useState<Record<string, boolean>>({})
  const [closeoutChecks, setCloseoutChecks] = useState<Record<string, boolean>>({})
  const [fieldReadinessChecks, setFieldReadinessChecks] = useState<Record<string, boolean>>({})
  const [fieldQuestionsDraft, setFieldQuestionsDraft] = useState<FieldQuestionsDraft>(EMPTY_FIELD_QUESTIONS_DRAFT)
  const [fieldObservationScratchpad, setFieldObservationScratchpad] = useState<FieldObservationScratchpad>(EMPTY_FIELD_OBSERVATION_SCRATCHPAD)
  const [approvalDraft, setApprovalDraft] = useState<ApprovalDecisionDraft>(EMPTY_APPROVAL_DRAFT)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setPacket(await readIntakeWorkbench())
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

  const candidate = packet?.candidate
  const admissionPlan = packet?.admissionPlan
  const approvalContract = packet?.approvalContract
  const storagePlan = packet?.storagePlan
  const summary = candidate?.summary || {}
  const project = candidate?.project || {}
  const warnings = candidate?.warnings || []
  const decisions = candidate?.human_decisions || []
  const noGoChecks = admissionPlan?.no_go_checks || []
  const targetRows = admissionPlan?.target_row_plan || {}
  const reviewChecklistKey = candidate?.candidate_id ? `pm-import-intake-review-checklist:${candidate.candidate_id}` : null
  const closeoutChecklistKey = candidate?.candidate_id ? `pm-import-intake-executor-closeout:${candidate.candidate_id}` : null
  const fieldReadinessChecklistKey = candidate?.candidate_id ? `pm-import-intake-field-readiness:${candidate.candidate_id}` : null
  const fieldQuestionsDraftKey = candidate?.candidate_id ? `pm-import-intake-field-questions:${candidate.candidate_id}` : null
  const fieldObservationScratchpadKey = candidate?.candidate_id ? `pm-import-intake-field-observations:${candidate.candidate_id}` : null
  const approvalDraftKey = candidate?.candidate_id ? `pm-import-intake-approval-draft:${candidate.candidate_id}` : null
  const permittedDecisions = approvalContract?.approval_record_contract?.permitted_decisions || []
  const notAllowed = useMemo(
    () =>
      uniqueItems(
        candidate?.review_guidance?.not_allowed_now,
        admissionPlan?.not_allowed_now,
        approvalContract?.not_allowed_now,
        storagePlan?.not_allowed_now,
      ),
    [
      candidate?.review_guidance?.not_allowed_now,
      admissionPlan?.not_allowed_now,
      approvalContract?.not_allowed_now,
      storagePlan?.not_allowed_now,
    ],
  )
  const futureRoute = firstAvailable(storagePlan?.recommended_route, approvalContract?.future_mutation_contract?.proposed_route)
  const workflowGates = [
    {
      title: 'Source intake',
      status: candidate?.source_freshness?.aggregate_fingerprint ? 'source current' : 'waiting',
      detail: candidate?.source_freshness?.review_action || 'Read-only source freshness is waiting for the candidate read.',
    },
    {
      title: 'Candidate review',
      status: candidate?.review_status || 'waiting',
      detail: 'Exception review stays at /pm-review/import-candidate before any import approval is admitted.',
    },
    {
      title: 'Admission gate',
      status: admissionPlan?.readiness_status || 'waiting',
      detail: 'The admission plan defines idempotency, diff checks, target rows, and no-go checks before write authority exists.',
    },
    {
      title: 'Approval readiness',
      status: approvalContract?.persistence_authority || storagePlan?.persistence_authority || 'not_admitted',
      detail: `Future approval persistence is shaped for ${storagePlan?.recommended_table || 'a dedicated approval table'} and ${futureRoute}.`,
    },
    {
      title: 'Hosted parity',
      status: 'executor closeout pending',
      detail: 'PM Lane 041A/041B still own hosted Vercel promotion and Render mutation-seam parity evidence.',
    },
    {
      title: 'Future import',
      status: 'not_admitted',
      detail: 'Project, workpackage, task, apparatus, assignment, schedule, and status writes remain blocked.',
    },
  ]
  const checklistCheckedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const fieldReadinessCheckedCount = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id]).length
  const fieldQuestionsDraftHasContent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldObservationScratchpadHasContent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const approvalDraftHasContent = hasApprovalDraftContent(approvalDraft)
  const persistenceReadinessGates = useMemo(
    () => buildPersistenceReadinessGates(packet, approvalDraft, reviewChecks),
    [packet, approvalDraft, reviewChecks],
  )
  const readyPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'ready').length
  const operatingQueue = useMemo(
    () => buildPmOperatingQueue(approvalDraft, reviewChecks, persistenceReadinessGates),
    [approvalDraft, reviewChecks, persistenceReadinessGates],
  )
  const importExceptionRegister = useMemo(
    () => buildImportExceptionRegister(candidate, noGoChecks, reviewChecks, approvalDraft),
    [candidate, noGoChecks, reviewChecks, approvalDraft],
  )
  const fieldPrepQueue = useMemo(
    () => buildFieldPrepQueue(fieldReadinessChecks, fieldQuestionsDraft),
    [fieldReadinessChecks, fieldQuestionsDraft],
  )
  const fieldPrepCoverageSnapshot = useMemo(
    () => buildFieldPrepCoverageSnapshot(reviewChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad),
    [reviewChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldPrepConversationAgenda = useMemo(
    () => buildFieldPrepConversationAgenda(fieldPrepCoverageSnapshot),
    [fieldPrepCoverageSnapshot],
  )
  const pmIntakeSnapshot = useMemo(
    () => buildPmIntakeSnapshot(persistenceReadinessGates, operatingQueue, importExceptionRegister, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
    [persistenceReadinessGates, operatingQueue, importExceptionRegister, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft],
  )
  const pmIntakeStartHere = useMemo(
    () => buildPmIntakeStartHere(operatingQueue, importExceptionRegister, fieldPrepQueue, pmIntakeSnapshot, persistenceReadinessGates),
    [operatingQueue, importExceptionRegister, fieldPrepQueue, pmIntakeSnapshot, persistenceReadinessGates],
  )
  const pmIntakeDailyReviewScript = useMemo(
    () => buildPmIntakeDailyReviewScript(candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan),
    [candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeCommandCenter = useMemo(
    () => buildPmIntakeCommandCenter(candidate, importExceptionRegister, reviewChecks, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan),
    [candidate, importExceptionRegister, reviewChecks, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeMeetingReadout = useMemo(
    () => buildPmIntakeMeetingReadout(candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan),
    [candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeConstraintRadar = useMemo(
    () => buildPmIntakeConstraintRadar(candidate, importExceptionRegister, reviewChecks, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan),
    [candidate, importExceptionRegister, reviewChecks, approvalDraft, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeOutputSelector = useMemo(
    () => buildPmIntakeOutputSelector(approvalDraft, reviewChecks, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad),
    [approvalDraft, reviewChecks, fieldPrepQueue, closeoutChecks, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const pmIntakeHandoffGuide = useMemo(
    () => buildPmIntakeHandoffGuide(importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan),
    [importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeWorkflowMap = useMemo(
    () => buildPmIntakeWorkflowMap(candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan),
    [candidate, importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan],
  )
  const pmIntakeOpenItems = useMemo(
    () => buildPmIntakeOpenItemsLens(importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan),
    [importExceptionRegister, approvalDraft, fieldPrepQueue, closeoutChecks, persistenceReadinessGates, admissionPlan],
  )
  const completeQueueCount = operatingQueue.filter((item) => item.status === 'complete').length
  const nextQueueCount = operatingQueue.filter((item) => item.status === 'next').length
  const blockedQueueCount = operatingQueue.filter((item) => item.status === 'blocked').length
  const pmIntakeSnapshotCount = pmIntakeSnapshotCounts(pmIntakeSnapshot)
  const importExceptionRegisterCount = importExceptionRegisterCounts(importExceptionRegister)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const reviewOutputStatuses = [briefStatus, previewStatus, pmIntakeSnapshotStatus, exceptionRegisterStatus].filter(Boolean)
  const executorOutputStatuses = [handoffStatus].filter(Boolean)
  const fieldPrepOutputStatuses = [fieldBriefStatus, fieldObservationStatus, fieldPrepCoverageStatus, fieldPrepAgendaStatus, fieldPrepPacketStatus].filter(Boolean)
  const hasOutputStatuses = reviewOutputStatuses.length > 0 || executorOutputStatuses.length > 0 || fieldPrepOutputStatuses.length > 0

  useEffect(() => {
    if (!reviewChecklistKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(reviewChecklistKey)
      setReviewChecks(stored ? (JSON.parse(stored) as Record<string, boolean>) : {})
    } catch {
      setReviewChecks({})
    }
  }, [reviewChecklistKey])

  useEffect(() => {
    if (!closeoutChecklistKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(closeoutChecklistKey)
      setCloseoutChecks(stored ? (JSON.parse(stored) as Record<string, boolean>) : {})
    } catch {
      setCloseoutChecks({})
    }
  }, [closeoutChecklistKey])

  useEffect(() => {
    if (!fieldReadinessChecklistKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(fieldReadinessChecklistKey)
      setFieldReadinessChecks(stored ? (JSON.parse(stored) as Record<string, boolean>) : {})
    } catch {
      setFieldReadinessChecks({})
    }
  }, [fieldReadinessChecklistKey])

  useEffect(() => {
    if (!fieldQuestionsDraftKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(fieldQuestionsDraftKey)
      setFieldQuestionsDraft(stored ? { ...EMPTY_FIELD_QUESTIONS_DRAFT, ...(JSON.parse(stored) as Partial<FieldQuestionsDraft>) } : EMPTY_FIELD_QUESTIONS_DRAFT)
    } catch {
      setFieldQuestionsDraft(EMPTY_FIELD_QUESTIONS_DRAFT)
    }
  }, [fieldQuestionsDraftKey])

  useEffect(() => {
    if (!fieldObservationScratchpadKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(fieldObservationScratchpadKey)
      setFieldObservationScratchpad(stored ? { ...EMPTY_FIELD_OBSERVATION_SCRATCHPAD, ...(JSON.parse(stored) as Partial<FieldObservationScratchpad>) } : EMPTY_FIELD_OBSERVATION_SCRATCHPAD)
    } catch {
      setFieldObservationScratchpad(EMPTY_FIELD_OBSERVATION_SCRATCHPAD)
    }
  }, [fieldObservationScratchpadKey])

  useEffect(() => {
    if (!approvalDraftKey || typeof window === 'undefined') {
      return
    }

    try {
      const stored = window.localStorage.getItem(approvalDraftKey)
      setApprovalDraft(stored ? { ...EMPTY_APPROVAL_DRAFT, ...(JSON.parse(stored) as Partial<ApprovalDecisionDraft>) } : EMPTY_APPROVAL_DRAFT)
    } catch {
      setApprovalDraft(EMPTY_APPROVAL_DRAFT)
    }
  }, [approvalDraftKey])

  function updateReviewCheck(itemId: string, checked: boolean) {
    const next = { ...reviewChecks, [itemId]: checked }
    setReviewChecks(next)
    if (reviewChecklistKey && typeof window !== 'undefined') {
      window.localStorage.setItem(reviewChecklistKey, JSON.stringify(next))
    }
  }

  function clearReviewChecklist() {
    setReviewChecks({})
    if (reviewChecklistKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(reviewChecklistKey)
    }
  }

  function updateCloseoutCheck(itemId: string, checked: boolean) {
    const next = { ...closeoutChecks, [itemId]: checked }
    setCloseoutChecks(next)
    if (closeoutChecklistKey && typeof window !== 'undefined') {
      window.localStorage.setItem(closeoutChecklistKey, JSON.stringify(next))
    }
  }

  function clearCloseoutChecklist() {
    setCloseoutChecks({})
    if (closeoutChecklistKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(closeoutChecklistKey)
    }
  }

  function updateFieldReadinessCheck(itemId: string, checked: boolean) {
    const next = { ...fieldReadinessChecks, [itemId]: checked }
    setFieldReadinessChecks(next)
    if (fieldReadinessChecklistKey && typeof window !== 'undefined') {
      window.localStorage.setItem(fieldReadinessChecklistKey, JSON.stringify(next))
    }
  }

  function clearFieldReadinessChecklist() {
    setFieldReadinessChecks({})
    if (fieldReadinessChecklistKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(fieldReadinessChecklistKey)
    }
  }

  function updateFieldQuestionsDraft(nextPartial: Partial<FieldQuestionsDraft>) {
    const next = { ...fieldQuestionsDraft, ...nextPartial }
    setFieldQuestionsDraft(next)
    if (fieldQuestionsDraftKey && typeof window !== 'undefined') {
      window.localStorage.setItem(fieldQuestionsDraftKey, JSON.stringify(next))
    }
  }

  function clearFieldQuestionsDraft() {
    setFieldQuestionsDraft(EMPTY_FIELD_QUESTIONS_DRAFT)
    if (fieldQuestionsDraftKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(fieldQuestionsDraftKey)
    }
  }

  function updateFieldObservationScratchpad(nextPartial: Partial<FieldObservationScratchpad>) {
    const next = { ...fieldObservationScratchpad, ...nextPartial }
    setFieldObservationScratchpad(next)
    if (fieldObservationScratchpadKey && typeof window !== 'undefined') {
      window.localStorage.setItem(fieldObservationScratchpadKey, JSON.stringify(next))
    }
  }

  function clearFieldObservationScratchpad() {
    setFieldObservationScratchpad(EMPTY_FIELD_OBSERVATION_SCRATCHPAD)
    if (fieldObservationScratchpadKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(fieldObservationScratchpadKey)
    }
  }

  function updateApprovalDraft(nextPartial: Partial<ApprovalDecisionDraft>) {
    const next = { ...approvalDraft, ...nextPartial }
    setApprovalDraft(next)
    if (approvalDraftKey && typeof window !== 'undefined') {
      window.localStorage.setItem(approvalDraftKey, JSON.stringify(next))
    }
  }

  function clearApprovalDraft() {
    setApprovalDraft(EMPTY_APPROVAL_DRAFT)
    if (approvalDraftKey && typeof window !== 'undefined') {
      window.localStorage.removeItem(approvalDraftKey)
    }
  }

  function exportPmBrief() {
    if (!packet) {
      return
    }

    downloadTextFile(
      briefFileName(candidate),
      buildIntakeBrief(packet, workflowGates, persistenceReadinessGates, operatingQueue, pmIntakeSnapshot, pmIntakeConstraintRadar, importExceptionRegister, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, reviewChecks, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
      'text/markdown',
    )
    setBriefStatus(`PM brief prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportApprovalPacketPreview() {
    if (!packet) {
      return
    }

    const preview = buildApprovalPacketPreview(packet, notAllowed, futureRoute, reviewChecks, approvalDraft)
    downloadTextFile(approvalPreviewFileName(candidate), `${JSON.stringify(preview, null, 2)}\n`, 'application/json')
    setPreviewStatus(`Approval packet preview prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportExecutorHandoff() {
    if (!packet) {
      return
    }

    downloadTextFile(
      executorHandoffFileName(candidate),
      buildExecutorHandoff(packet, workflowGates, persistenceReadinessGates, operatingQueue, pmIntakeSnapshot, pmIntakeConstraintRadar, importExceptionRegister, notAllowed, futureRoute, reviewChecks, closeoutChecks, approvalDraft),
      'text/markdown',
    )
    setHandoffStatus(`Executor handoff prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPmIntakeSnapshot() {
    if (!packet) {
      return
    }

    downloadTextFile(
      pmIntakeSnapshotFileName(candidate),
      buildPmIntakeSnapshotExport(packet, pmIntakeSnapshot, notAllowed, futureRoute),
      'text/markdown',
    )
    setPmIntakeSnapshotStatus(`PM intake snapshot prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportImportExceptionRegister() {
    if (!packet) {
      return
    }

    downloadTextFile(
      importExceptionRegisterFileName(candidate),
      buildImportExceptionRegisterExport(packet, importExceptionRegister, notAllowed, reviewChecks, approvalDraft),
      'text/markdown',
    )
    setExceptionRegisterStatus(`Import exception register prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldKickoffBrief() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldKickoffBriefFileName(candidate),
      buildFieldKickoffBrief(packet, workflowGates, operatingQueue, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, reviewChecks, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
      'text/markdown',
    )
    setFieldBriefStatus(`Field kickoff prep brief prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldObservationNotes() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldObservationNotesFileName(candidate),
      buildFieldObservationNotes(packet, fieldPrepQueue, notAllowed, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad),
      'text/markdown',
    )
    setFieldObservationStatus(`Field observation notes prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldPrepCoverageSnapshot() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldPrepCoverageSnapshotFileName(candidate),
      buildFieldPrepCoverageSnapshotExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldObservationScratchpad, notAllowed),
      'text/markdown',
    )
    setFieldPrepCoverageStatus(`Field prep coverage snapshot prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldPrepConversationAgenda() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldPrepConversationAgendaFileName(candidate),
      buildFieldPrepConversationAgendaExport(packet, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed),
      'text/markdown',
    )
    setFieldPrepAgendaStatus(`Field prep conversation agenda prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldPrepPacket() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldPrepPacketFileName(candidate),
      buildFieldPrepPacket(packet, workflowGates, operatingQueue, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, reviewChecks, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
      'text/markdown',
    )
    setFieldPrepPacketStatus(`Field prep packet prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">Project Miner Intake Workbench</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Run Project Miner intake from one workbench.</h1>
            <p className="lede">
              One read-only PM starting point for the current candidate, import gate, approval contract, and storage plan. It consolidates review context without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Route</dt>
              <dd>/pm-review/import-intake</dd>
            </div>
            <div>
              <dt>Read seams</dt>
              <dd>candidate, admission plan, approval contract, storage plan</dd>
            </div>
            <div>
              <dt>Future route</dt>
              <dd>{futureRoute}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Read status</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>{loading ? 'Loading the current intake packet.' : candidate?.candidate_id || 'Waiting for the candidate read.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Project</h2>
            <span className="status-pill status-configured">{formatLabel(project.source_format)}</span>
          </div>
          <p>
            {project.name || 'Unknown project'} - {project.location || 'unknown location'}
          </p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Approval storage</h2>
            <span className={`status-pill ${statusTone(storagePlan?.persistence_authority)}`}>{storagePlan?.persistence_authority || 'not_admitted'}</span>
          </div>
          <p>{storagePlan?.recommended_table || 'No approval storage table is admitted.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Hosted parity</h2>
            <span className="status-pill status-awaiting-values">pending</span>
          </div>
          <p>Use PM Lane 041 closeouts before claiming hosted live parity for this consolidated route.</p>
        </article>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Daily Intake Starting Point</h2>
            <p>
              Review the source-derived project shape, current gates, and guardrails before moving to any dedicated detail route.
            </p>
          </div>
          <details
            open
            aria-label="PM intake route links"
            style={{ minWidth: 'min(100%, 34rem)' }}
          >
            <summary style={{ cursor: 'pointer', marginBottom: '0.65rem' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Route Links</h2>
            </summary>
            <div
              aria-label="PM intake route link groups"
              style={{ display: 'grid', gap: '0.65rem', gridTemplateColumns: 'repeat(auto-fit, minmax(12rem, 1fr))' }}
            >
              {PM_INTAKE_ROUTE_LINK_GROUPS.map((group) => (
                <section key={group.id} aria-label={`${group.label} route links`} style={{ display: 'grid', gap: '0.45rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{group.label}</h3>
                  <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                    {group.items.map((item) => (
                      <Link key={item.id} href={item.href}>
                        {item.label}
                      </Link>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </details>
        </div>
        <details
          open
          aria-label="PM intake output action rail"
          style={{ margin: '0.85rem 0 1rem' }}
        >
          <summary style={{ cursor: 'pointer', marginBottom: '0.65rem' }}>
            <h2 style={{ display: 'inline', margin: 0 }}>Output Actions</h2>
          </summary>
          <div
            aria-label="PM intake output action groups"
            style={{ display: 'grid', gap: '0.85rem', gridTemplateColumns: 'repeat(auto-fit, minmax(15rem, 1fr))' }}
          >
            <section aria-label="Review output actions" style={{ display: 'grid', gap: '0.55rem' }}>
              <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Review Outputs</h3>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                <button className="btn btn-outline" onClick={exportPmBrief} disabled={!packet}>
                  Export PM Brief
                </button>
                <button className="btn btn-outline" onClick={exportApprovalPacketPreview} disabled={!packet}>
                  Export Approval Preview JSON
                </button>
                <button className="btn btn-outline" onClick={exportPmIntakeSnapshot} disabled={!packet}>
                  Export PM Intake Snapshot
                </button>
                <button className="btn btn-outline" onClick={exportImportExceptionRegister} disabled={!packet}>
                  Export Import Exception Register
                </button>
              </div>
            </section>
            <section aria-label="Executor output actions" style={{ display: 'grid', gap: '0.55rem' }}>
              <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Executor Output</h3>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                <button className="btn btn-outline" onClick={exportExecutorHandoff} disabled={!packet}>
                  Export Executor Handoff
                </button>
              </div>
            </section>
            <section aria-label="Field prep output actions" style={{ display: 'grid', gap: '0.55rem' }}>
              <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Field Prep Outputs</h3>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                <button className="btn btn-outline" onClick={exportFieldKickoffBrief} disabled={!packet}>
                  Export Field Kickoff Brief
                </button>
                <button className="btn btn-outline" onClick={exportFieldObservationNotes} disabled={!packet}>
                  Export Field Observation Notes
                </button>
                <button className="btn btn-outline" onClick={exportFieldPrepCoverageSnapshot} disabled={!packet}>
                  Export Field Prep Coverage Snapshot
                </button>
                <button className="btn btn-outline" onClick={exportFieldPrepConversationAgenda} disabled={!packet}>
                  Export Field Prep Conversation Agenda
                </button>
                <button className="btn btn-outline" onClick={exportFieldPrepPacket} disabled={!packet}>
                  Export Field Prep Packet
                </button>
              </div>
            </section>
            <section aria-label="Refresh action" style={{ display: 'grid', gap: '0.55rem' }}>
              <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Refresh</h3>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
            </section>
          </div>
        </details>
        {hasOutputStatuses ? (
          <details
            open
            aria-label="PM intake output status rail"
            style={{
              borderBottom: '1px solid var(--border)',
              borderTop: '1px solid var(--border)',
              margin: '0 0 1rem',
              padding: '0.85rem 0',
            }}
          >
            <summary style={{ cursor: 'pointer', marginBottom: '0.65rem' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Output Status</h2>
            </summary>
            <div
              aria-label="PM intake output status groups"
              style={{
                display: 'grid',
                gap: '0.85rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(15rem, 1fr))',
              }}
            >
              {reviewOutputStatuses.length > 0 ? (
                <section aria-label="Review output status" style={{ display: 'grid', gap: '0.45rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Review Output Status</h3>
                  {reviewOutputStatuses.map((status) => (
                    <p key={status} style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
                      {status}
                    </p>
                  ))}
                </section>
              ) : null}
              {executorOutputStatuses.length > 0 ? (
                <section aria-label="Executor output status" style={{ display: 'grid', gap: '0.45rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Executor Output Status</h3>
                  {executorOutputStatuses.map((status) => (
                    <p key={status} style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
                      {status}
                    </p>
                  ))}
                </section>
              ) : null}
              {fieldPrepOutputStatuses.length > 0 ? (
                <section aria-label="Field prep output status" style={{ display: 'grid', gap: '0.45rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Field Prep Output Status</h3>
                  {fieldPrepOutputStatuses.map((status) => (
                    <p key={status} style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
                      {status}
                    </p>
                  ))}
                </section>
              ) : null}
            </div>
          </details>
        ) : null}

        <section className="status-grid status-grid-wide" aria-label="Project Miner intake summary" style={{ marginBottom: '1rem' }}>
          <article className="status-card">
            <h2>Workpackages</h2>
            <p>{formatCount(summary.workpackage_count)} proposed groups.</p>
          </article>
          <article className="status-card">
            <h2>Tasks</h2>
            <p>{formatCount(summary.task_count)} proposed task rows.</p>
          </article>
          <article className="status-card">
            <h2>Apparatus</h2>
            <p>{formatCount(summary.apparatus_candidate_count)} candidate apparatus rows.</p>
          </article>
          <article className="status-card">
            <h2>Review signals</h2>
            <p>
              {formatCount(summary.warning_count)} warnings, {formatCount(summary.blocker_count)} blockers, {formatCount(summary.human_decision_count)} human decisions.
            </p>
          </article>
        </section>

        <details id="pm-quick-jump-rail" open aria-label="PM intake quick jump rail" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>PM Intake Quick Jump Rail</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Fast local navigation for the current intake workbench. These links do not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, or mutate production state.
          </p>
          <nav
            aria-label="PM intake section links"
            style={{ display: 'grid', gap: '0.65rem', gridTemplateColumns: 'repeat(auto-fit, minmax(12rem, 1fr))', marginTop: '0.85rem' }}
          >
            {PM_INTAKE_QUICK_JUMP_GROUPS.map((group) => (
              <section key={group.id} aria-label={`${group.label} quick jump links`} style={{ display: 'grid', gap: '0.55rem' }}>
                <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{group.label}</h3>
                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  {group.items.map((item) => (
                    <a
                      key={item.id}
                      className="btn btn-outline"
                      href={item.href}
                      style={{ alignItems: 'start', display: 'grid', gap: '0.25rem', height: '100%', justifyContent: 'stretch', textAlign: 'left', whiteSpace: 'normal' }}
                    >
                      <strong>{item.label}</strong>
                      <span style={{ color: 'var(--muted)', fontSize: '0.86rem', lineHeight: 1.35 }}>{item.detail}</span>
                    </a>
                  ))}
                </div>
              </section>
            ))}
          </nav>
        </details>

        <section aria-label="PM intake helper panel stack" style={{ display: 'grid', gap: '1rem', marginBottom: '1rem' }}>
          <details open aria-label="Intake triage helper panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Intake Triage Panels</h2>
            </summary>

        <section id="pm-command-center" aria-label="Local PM intake command center" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Command Center</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Compact top-of-page scan for the current local PM move, next field question posture, handoff context, and blocked future authority. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeCommandCenter.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${commandCenterTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section id="pm-meeting-readout" aria-label="Local PM intake meeting readout" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Meeting Readout</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Conversation-ready local summary for PM, lead, customer, or field review. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeMeetingReadout.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${meetingReadoutTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section id="pm-constraint-radar" aria-label="Local PM intake constraint radar" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Constraint Radar</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Constraint scan for source/review, field-prep, executor/hosted, and future write-authority boundaries. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, workbook macro path, workbook writeback, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeConstraintRadar.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${constraintRadarTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

          </details>
          <details open aria-label="Daily action helper panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Daily Action Panels</h2>
            </summary>

        <section id="pm-daily-review-script" aria-label="Local PM intake daily review script" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Daily Review Script</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            First 5 minutes of browser-local review, derived from the existing workbench state. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeDailyReviewScript.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${dailyReviewScriptTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section id="pm-start-here" aria-label="Local PM intake start here" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Start Here</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Top-level focus for this intake session, derived from the existing workbench state. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, or mutate production state.
            {' '}It links to existing local sections and exports only; it creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeStartHere.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${startHereTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section id="pm-output-selector" aria-label="Local PM intake output selector" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Intake Output Selector</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Browser-local chooser for existing outputs already on this workbench. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeOutputSelector.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${outputSelectorTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <details id="pm-handoff-guide" open aria-label="Local PM intake handoff guide" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Handoff Guide</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Browser-local guide for the next context lane. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write.
          </p>
          <div aria-label="Local PM intake handoff guide items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeHandoffGuide.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${handoffGuideTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </details>

          </details>
          <details open aria-label="Workflow review helper panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Workflow Review Panels</h2>
            </summary>

        <details id="pm-workflow-map" open aria-label="Local PM intake workflow map" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Workflow Map</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Visual map of the current intake path from source review through field-prep context, executor closeout, and still-blocked future write authority. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write.
          </p>
          <div aria-label="Local PM intake workflow map items" style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(14rem, 1fr))', marginTop: '0.85rem' }}>
            {pmIntakeWorkflowMap.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${workflowMapTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </details>

        <details id="pm-open-items" open aria-label="Local PM intake open items lens" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Open Items Lens</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Exception-first lens for local attention items and future authority blockers. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, work authorization, or production write.
          </p>
          <div aria-label="Local PM intake open items lens items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeOpenItems.map((item) => (
              <a
                key={item.id}
                className="card"
                href={item.href}
                style={{ color: 'inherit', display: 'block', padding: '0.85rem', textDecoration: 'none', boxShadow: 'none' }}
              >
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${openItemsTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </a>
            ))}
          </div>
        </details>
          </details>
        </section>

        <section aria-label="PM intake detail workbench" style={{ display: 'grid', gap: '1rem' }}>
          <details open aria-label="Review snapshot detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Review Snapshot Detail</h2>
            </summary>

        <details id="pm-intake-snapshot" open aria-label="Local PM intake snapshot" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Snapshot</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Compact scan view for exception posture, decision draft, field-prep context, next local action, hosted parity, and future write boundaries. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state.
          </p>
          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {pmIntakeSnapshotSummary(pmIntakeSnapshotCount)}
          </p>
          <div aria-label="Local PM intake snapshot items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {pmIntakeSnapshot.map((item) => (
              <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                    <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.evidence}</p>
                  </div>
                  <span className={`status-pill ${pmIntakeSnapshotTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </details>

        <details id="pm-operating-queue" open aria-label="Local PM operating queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Operating Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Local queue for today&apos;s intake work. It translates the checklist, local decision draft, and readiness gates into practical next moves without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state.
          </p>
          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {formatCount(completeQueueCount)} complete / {formatCount(nextQueueCount)} next / {formatCount(blockedQueueCount)} blocked
          </p>
          <div aria-label="Local PM operating queue items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {operatingQueue.map((item) => (
              <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${operatingQueueTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </details>

          </details>
          <details open aria-label="Source and exception detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Source and Exception Detail</h2>
            </summary>

        <section id="project-packet" aria-label="Project packet and source freshness" className="notes-grid" style={{ marginBottom: '1rem' }}>
          <article className="notes-card">
            <h2>Project Packet</h2>
            <dl className="contract-panel">
              <div>
                <dt>Candidate</dt>
                <dd>{candidate?.candidate_id || 'waiting for candidate'}</dd>
              </div>
              <div>
                <dt>Version</dt>
                <dd>{candidate?.candidate_version || 'unknown'}</dd>
              </div>
              <div>
                <dt>Candidate authority</dt>
                <dd>{candidate?.mutation_authority || 'not_admitted'}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{project.location || 'unknown'}</dd>
              </div>
              <div>
                <dt>Drawings</dt>
                <dd>{project.drawing_package || 'unknown'}</dd>
              </div>
            </dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Source Freshness</h2>
            <dl className="contract-panel">
              <div>
                <dt>Strategy</dt>
                <dd>{candidate?.source_freshness?.strategy || 'pending'}</dd>
              </div>
              <div>
                <dt>Fingerprint</dt>
                <dd>{candidate?.source_freshness?.aggregate_fingerprint || 'unknown'}</dd>
              </div>
              <div>
                <dt>Available</dt>
                <dd>{formatCount(candidate?.source_freshness?.available_count)} available, {formatCount(candidate?.source_freshness?.missing_count)} missing</dd>
              </div>
            </dl>
          </article>
        </section>

        <details id="import-exception-register" open aria-label="Local import exception decision register" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Import Exception Decision Register</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Derived exception register for candidate warnings, human decision prompts, admission no-go checks, local review evidence, and local decision draft context. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state.
          </p>
          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {importExceptionRegisterSummary(importExceptionRegisterCount)}
          </p>
          <div aria-label="Local import exception decision register items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {importExceptionRegister.map((item) => (
              <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                    <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.evidence}</p>
                  </div>
                  <span className={`status-pill ${importExceptionRegisterTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </details>

        <details id="workflow-gates" open aria-label="Workflow gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Workflow Gates</h2>
            <span className="status-pill status-awaiting-values">read-only</span>
          </summary>
          <div aria-label="Workflow gate items" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {workflowGates.map((gate) => (
              <article key={gate.title} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{gate.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{gate.detail}</p>
                  </div>
                  <span className={`status-pill ${statusTone(gate.status)}`}>{formatLabel(gate.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </details>

        <details open aria-label="Exception review and PM decision detail" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary style={{ cursor: 'pointer' }}>
            <h2 style={{ display: 'inline', margin: 0 }}>Exception Review and PM Decisions</h2>
          </summary>
          <div aria-label="Exception and PM decision detail cards" className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <article className="notes-card">
              <h2>Exception Review</h2>
              <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
                {visibleWarnings(warnings).map((warning) => (
                  <article key={`${warning.code}-${warning.message}`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                    <div className="status-row" style={{ justifyContent: 'flex-start' }}>
                      <span className={`status-pill ${statusTone(warning.severity)}`}>{formatLabel(warning.severity)}</span>
                      <span className="status-pill status-backend-routed">{warning.code || 'WARNING'}</span>
                    </div>
                    <p style={{ margin: '0.55rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{warning.message || 'Review warning.'}</p>
                  </article>
                ))}
                {!warnings.length ? <p style={{ color: 'var(--muted)' }}>No candidate warnings are currently reported.</p> : null}
              </div>
            </article>
            <article className="notes-card accent-card">
              <h2>PM Decisions</h2>
              <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
                {visibleDecisions(decisions).map((decision) => (
                  <article key={decision.decision_id || decision.prompt} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                    <p style={{ margin: 0 }}>
                      <strong>{formatLabel(decision.decision_id)}</strong>
                    </p>
                    <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{decision.prompt || 'Decision prompt is waiting for the candidate.'}</p>
                    <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{decision.recommended_action || 'Review before future import.'}</p>
                  </article>
                ))}
                {!decisions.length ? <p style={{ color: 'var(--muted)' }}>No PM decisions are currently reported.</p> : null}
              </div>
            </article>
          </div>
        </details>

          </details>
          <details open aria-label="Approval prep detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Approval Prep Detail</h2>
            </summary>

        <details open aria-label="Admission and approval contract" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary style={{ cursor: 'pointer' }}>
            <h2 style={{ display: 'inline', margin: 0 }}>Admission and Approval Contract</h2>
          </summary>
          <div aria-label="Admission and approval contract cards" className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <article className="notes-card">
              <h2>Admission Shape</h2>
              <dl className="contract-panel">
                <div>
                  <dt>Admission plan</dt>
                  <dd>{admissionPlan?.admission_plan_id || 'waiting for admission plan'}</dd>
                </div>
                <div>
                  <dt>Admission authority</dt>
                  <dd>{admissionPlan?.mutation_authority || 'not_admitted'}</dd>
                </div>
                <div>
                  <dt>Target rows</dt>
                  <dd>{Object.entries(targetRows).map(([key, value]) => `${formatLabel(key)}: ${formatValue(value)}`).join('; ') || 'none reported'}</dd>
                </div>
                <div>
                  <dt>No-go checks</dt>
                  <dd>{formatCount(noGoChecks.length)}</dd>
                </div>
              </dl>
            </article>
            <article className="notes-card accent-card">
              <h2>Approval Contract</h2>
              <dl className="contract-panel">
                <div>
                  <dt>Contract</dt>
                  <dd>{approvalContract?.approval_contract_id || 'waiting for approval contract'}</dd>
                </div>
                <div>
                  <dt>Record type</dt>
                  <dd>{approvalContract?.approval_record_contract?.record_type || storagePlan?.recommended_entity_type || 'unknown'}</dd>
                </div>
                <div>
                  <dt>Contract authority</dt>
                  <dd>{approvalContract?.mutation_authority || 'not_admitted'}</dd>
                </div>
                <div>
                  <dt>Persistence authority</dt>
                  <dd>{approvalContract?.persistence_authority || storagePlan?.persistence_authority || 'not_admitted'}</dd>
                </div>
                <div>
                  <dt>Storage table</dt>
                  <dd>{storagePlan?.recommended_table || 'not admitted'}</dd>
                </div>
                <div>
                  <dt>Mutation route</dt>
                  <dd>{futureRoute}</dd>
                </div>
              </dl>
            </article>
          </div>
        </details>

        <details open aria-label="Local review checklist" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Review Checklist</h2>
            <span className="status-pill status-configured">
              {formatCount(checklistCheckedCount)} of {formatCount(REVIEW_CHECKLIST_ITEMS.length)}
            </span>
          </summary>
          <div aria-label="Review checklist controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local review prep only. Checking these items does not approve, persist, import, assign, schedule, change status, or mutate production state.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {REVIEW_CHECKLIST_ITEMS.map((item) => (
                <label key={item.id} className="card" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.75rem', padding: '0.85rem', boxShadow: 'none', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={Boolean(reviewChecks[item.id])}
                    onChange={(event) => updateReviewCheck(item.id, event.target.checked)}
                    style={{ marginTop: '0.25rem' }}
                  />
                  <span>
                    <strong>{item.label}</strong>
                    <span style={{ display: 'block', marginTop: '0.35rem', color: 'var(--muted)', lineHeight: 1.5 }}>{item.detail}</span>
                  </span>
                </label>
              ))}
            </div>
            <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
              <button className="btn btn-outline" onClick={clearReviewChecklist} disabled={!checklistCheckedCount}>
                Clear checklist
              </button>
              <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
            </div>
          </div>
        </details>

        <details open aria-label="Local approval decision draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Approval Decision Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </summary>
          <div aria-label="Approval draft controls">
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Draft the future approval decision and notes for the PM brief only. This does not approve, persist, import, assign, schedule, change status, or mutate production state.
          </p>
          <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Decision draft</strong>
              <select
                value={approvalDraft.decision}
                onChange={(event) => updateApprovalDraft({ decision: event.target.value })}
                disabled={!permittedDecisions.length}
                style={{ width: '100%', minHeight: '2.5rem' }}
              >
                <option value="">Select local draft decision</option>
                {permittedDecisions.map((decision) => (
                  <option key={decision} value={decision}>
                    {formatLabel(decision)}
                  </option>
                ))}
              </select>
              <span style={{ color: 'var(--muted)', lineHeight: 1.5 }}>Allowed by the read-only approval contract, but not persisted by this screen.</span>
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Review notes draft</strong>
              <textarea
                value={approvalDraft.review_notes}
                onChange={(event) => updateApprovalDraft({ review_notes: event.target.value })}
                rows={5}
                placeholder="Summarize reviewed exceptions, assumptions, and open questions for the future approval packet."
                style={{ width: '100%', resize: 'vertical', minHeight: '8rem' }}
              />
              <span style={{ color: 'var(--muted)', lineHeight: 1.5 }}>Retained in this browser for the current candidate only.</span>
            </label>
          </div>
          <label className="card" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.75rem', padding: '0.85rem', boxShadow: 'none', cursor: 'pointer', marginTop: '0.85rem' }}>
            <input
              type="checkbox"
              checked={approvalDraft.local_attestation}
              onChange={(event) => updateApprovalDraft({ local_attestation: event.target.checked })}
              style={{ marginTop: '0.25rem' }}
            />
            <span>
              <strong>Local-only draft attestation</strong>
              <span style={{ display: 'block', marginTop: '0.35rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                I understand this draft is local review prep and a later admitted packet must own any approval persistence or import mutation.
              </span>
            </span>
          </label>
          <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
            <button className="btn btn-outline" onClick={clearApprovalDraft} disabled={!approvalDraftHasContent}>
              Clear decision draft
            </button>
            <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Included in the PM brief only when exported from this browser.</span>
          </div>
          </div>
        </details>

          </details>
          <details open aria-label="Executor closeout detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Executor Closeout Detail</h2>
            </summary>

        <details open id="executor-closeout" aria-label="Local executor closeout intake" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Executor Closeout Intake</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(closeoutCheckedCount)} of {formatCount(CLOSEOUT_CHECKLIST_ITEMS.length)}
            </span>
          </summary>
          <div aria-label="Executor closeout controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local audit prep for external executor returns. Checking these items does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {CLOSEOUT_CHECKLIST_ITEMS.map((item) => (
                <label key={item.id} className="card" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.75rem', padding: '0.85rem', boxShadow: 'none', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={Boolean(closeoutChecks[item.id])}
                    onChange={(event) => updateCloseoutCheck(item.id, event.target.checked)}
                    style={{ marginTop: '0.25rem' }}
                  />
                  <span>
                    <strong>{item.label}</strong>
                    <span style={{ display: 'block', marginTop: '0.35rem', color: 'var(--muted)', lineHeight: 1.5 }}>{item.detail}</span>
                  </span>
                </label>
              ))}
            </div>
            <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
              <button className="btn btn-outline" onClick={clearCloseoutChecklist} disabled={!closeoutCheckedCount}>
                Clear closeout intake
              </button>
              <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
            </div>
          </div>
        </details>

          </details>
          <details open aria-label="Field prep detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Field Prep Detail</h2>
            </summary>

        <details open aria-label="Local field readiness checklist" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Readiness Checklist</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(fieldReadinessCheckedCount)} of {formatCount(FIELD_READINESS_CHECKLIST_ITEMS.length)}
            </span>
          </summary>
          <div aria-label="Field readiness controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local prep evidence for PM, lead, and field review conversations. Checking these items does not authorize work, approve, persist, import, assign, schedule, change status, or mutate production state.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {FIELD_READINESS_CHECKLIST_ITEMS.map((item) => (
                <label key={item.id} className="card" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.75rem', padding: '0.85rem', boxShadow: 'none', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={Boolean(fieldReadinessChecks[item.id])}
                    onChange={(event) => updateFieldReadinessCheck(item.id, event.target.checked)}
                    style={{ marginTop: '0.25rem' }}
                  />
                  <span>
                    <strong>{item.label}</strong>
                    <span style={{ display: 'block', marginTop: '0.35rem', color: 'var(--muted)', lineHeight: 1.5 }}>{item.detail}</span>
                  </span>
                </label>
              ))}
            </div>
            <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
              <button className="btn btn-outline" onClick={clearFieldReadinessChecklist} disabled={!fieldReadinessCheckedCount}>
                Clear field readiness
              </button>
              <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
            </div>
          </div>
        </details>

        <details open aria-label="Local field questions draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Questions Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </summary>
          <div aria-label="Field questions controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local question notes for PM, lead, and field prep conversations. These notes do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes.
            </p>
            <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>Drawing/source questions</strong>
                <textarea
                  value={fieldQuestionsDraft.drawing_source_questions}
                  onChange={(event) => updateFieldQuestionsDraft({ drawing_source_questions: event.target.value })}
                  rows={4}
                  placeholder="Capture drawing, estimator, Project Data Entry, source-freshness, or scope-origin questions."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>Site access and safety questions</strong>
                <textarea
                  value={fieldQuestionsDraft.site_access_safety_questions}
                  onChange={(event) => updateFieldQuestionsDraft({ site_access_safety_questions: event.target.value })}
                  rows={4}
                  placeholder="Capture access, escort, badging, JHA, PPE, LOTO, energization, or temp-power safety questions."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>Crew and equipment questions</strong>
                <textarea
                  value={fieldQuestionsDraft.crew_equipment_questions}
                  onChange={(event) => updateFieldQuestionsDraft({ crew_equipment_questions: event.target.value })}
                  rows={4}
                  placeholder="Capture crew size, tooling, lift, rental, equipment, or logistics questions without assigning resources."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>Material and staging questions</strong>
                <textarea
                  value={fieldQuestionsDraft.material_staging_questions}
                  onChange={(event) => updateFieldQuestionsDraft({ material_staging_questions: event.target.value })}
                  rows={4}
                  placeholder="Capture material, apparatus staging, laydown, delivery, receiving, or storage questions."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>Customer constraint questions</strong>
                <textarea
                  value={fieldQuestionsDraft.customer_constraint_questions}
                  onChange={(event) => updateFieldQuestionsDraft({ customer_constraint_questions: event.target.value })}
                  rows={4}
                  placeholder="Capture outage, access-window, communication, milestone, or customer coordination questions without changing schedule state."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
              <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
                <strong>PM follow-up notes</strong>
                <textarea
                  value={fieldQuestionsDraft.pm_followup_notes}
                  onChange={(event) => updateFieldQuestionsDraft({ pm_followup_notes: event.target.value })}
                  rows={4}
                  placeholder="Capture PM follow-up notes for the next conversation or bounded packet."
                  style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
                />
              </label>
            </div>
            <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
              <button className="btn btn-outline" onClick={clearFieldQuestionsDraft} disabled={!fieldQuestionsDraftHasContent}>
                Clear field questions
              </button>
              <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only and included in local exports.</span>
            </div>
          </div>
        </details>

        <details id="field-prep" open aria-label="Local field prep queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Prep Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Field prep queue controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Derived queue for field-prep conversations. It translates local field questions and readiness evidence into practical next moves without creating tasks, issues, assignments, schedules, status updates, approval records, import rows, or production writes.
            </p>
            <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              {formatCount(completeFieldPrepQueueCount)} complete / {formatCount(nextFieldPrepQueueCount)} next / {formatCount(blockedFieldPrepQueueCount)} blocked
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldPrepQueue.map((item) => (
                <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <div className="status-row" style={{ alignItems: 'start' }}>
                    <div>
                      <p style={{ margin: 0 }}>
                        <strong>{item.title}</strong>
                      </p>
                      <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                    </div>
                    <span className={`status-pill ${operatingQueueTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </details>

        <section aria-label="Local field prep coverage snapshot" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Prep Coverage Snapshot</h2>
            <span className="status-pill status-awaiting-values">derived</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Browser-local coverage snapshot derived from existing local prep state. It shows what field-prep context is covered, partial, open, or blocked without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.
          </p>
          <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {fieldPrepCoverageSummary(fieldPrepCoverageCount)}
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {fieldPrepCoverageSnapshot.map((item) => (
              <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${fieldPrepCoverageTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section aria-label="Local field prep conversation agenda" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Prep Conversation Agenda</h2>
            <span className="status-pill status-awaiting-values">derived</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Browser-local agenda derived from the coverage snapshot. It turns covered, partial, open, and blocked prep areas into conversation context, ask, confirm, and blocked agenda items without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.
          </p>
          <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {fieldPrepAgendaSummary(fieldPrepAgendaCount)}
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {fieldPrepConversationAgenda.map((item) => (
              <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{item.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                  <span className={`status-pill ${fieldPrepAgendaTone(item.status)}`}>{formatLabel(item.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section aria-label="Local field observation scratchpad" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Observation Scratchpad</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Browser-local observation notes for PM, lead, and field conversations. These notes do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes.
          </p>
          <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Observation date or shift note</strong>
              <textarea
                value={fieldObservationScratchpad.observation_date_or_shift}
                onChange={(event) => updateFieldObservationScratchpad({ observation_date_or_shift: event.target.value })}
                rows={3}
                placeholder="Capture the date, shift, or conversation timing for local field-prep context."
                style={{ width: '100%', resize: 'vertical', minHeight: '5rem' }}
              />
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Observer / source</strong>
              <textarea
                value={fieldObservationScratchpad.observer_source}
                onChange={(event) => updateFieldObservationScratchpad({ observer_source: event.target.value })}
                rows={3}
                placeholder="Capture who provided the local observation, such as PM, lead, customer, or field contact."
                style={{ width: '100%', resize: 'vertical', minHeight: '5rem' }}
              />
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Workpackage or area reference</strong>
              <textarea
                value={fieldObservationScratchpad.workpackage_area_reference}
                onChange={(event) => updateFieldObservationScratchpad({ workpackage_area_reference: event.target.value })}
                rows={3}
                placeholder="Capture the workpackage, apparatus group, room, yard, or area being discussed."
                style={{ width: '100%', resize: 'vertical', minHeight: '5rem' }}
              />
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Access and safety observations</strong>
              <textarea
                value={fieldObservationScratchpad.access_safety_observations}
                onChange={(event) => updateFieldObservationScratchpad({ access_safety_observations: event.target.value })}
                rows={4}
                placeholder="Capture access, escort, PPE, LOTO, energization, or safety conversation notes without creating a field record."
                style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
              />
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Material, staging, or equipment observations</strong>
              <textarea
                value={fieldObservationScratchpad.material_equipment_observations}
                onChange={(event) => updateFieldObservationScratchpad({ material_equipment_observations: event.target.value })}
                rows={4}
                placeholder="Capture material, staging, laydown, receiving, equipment, tooling, or rental notes without assigning resources."
                style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
              />
            </label>
            <label className="card" style={{ display: 'grid', gap: '0.45rem', padding: '0.85rem', boxShadow: 'none' }}>
              <strong>Open questions / PM follow-up</strong>
              <textarea
                value={fieldObservationScratchpad.open_questions_pm_followup}
                onChange={(event) => updateFieldObservationScratchpad({ open_questions_pm_followup: event.target.value })}
                rows={4}
                placeholder="Capture follow-up questions for PM review or a later bounded packet."
                style={{ width: '100%', resize: 'vertical', minHeight: '6rem' }}
              />
            </label>
          </div>
          <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
            <button className="btn btn-outline" onClick={clearFieldObservationScratchpad} disabled={!fieldObservationScratchpadHasContent}>
              Clear field observations
            </button>
            <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only and included in local field-prep exports.</span>
          </div>
        </section>

          </details>
          <details open aria-label="Authority boundary detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Authority Boundary Detail</h2>
            </summary>

        <section id="approval-readiness" aria-label="Approval persistence readiness gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Approval Persistence Readiness</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(readyPersistenceGateCount)} of {formatCount(persistenceReadinessGates.length)} ready
            </span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Local readiness map for the future approval-persistence packet. It reflects review context and blockers only; it does not approve, persist, import, assign, schedule, change status, or mutate production state.
          </p>
          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            PM Lane 049 authored the schema and adapter admission design. Hosted parity, schema authority, approval persistence authority, and import mutation authority remain blocked until later packets explicitly admit them.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {persistenceReadinessGates.map((gate) => (
              <article key={gate.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ alignItems: 'start' }}>
                  <div>
                    <p style={{ margin: 0 }}>
                      <strong>{gate.title}</strong>
                    </p>
                    <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{gate.detail}</p>
                  </div>
                  <span className={`status-pill ${gate.status === 'ready' ? 'status-configured' : 'status-deferred'}`}>{formatLabel(gate.status)}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="guardrails" aria-label="Current PM next actions and guardrails" className="notes-grid">
          <article className="notes-card">
            <h2>Current PM Next Actions</h2>
            <ol>
              <li>Review candidate exceptions, source freshness, and required human decisions.</li>
              <li>Confirm the Project Miner source files have not changed before any future approval packet is used.</li>
              <li>Use the Vercel and Render executor closeout lanes for hosted parity before claiming production-read proof.</li>
              <li>Keep approval persistence and project import blocked until a later packet explicitly admits those writes.</li>
            </ol>
          </article>
          <article className="notes-card accent-card">
            <h2>Not Allowed Now</h2>
            <ul>
              {(notAllowed.length ? notAllowed : ['write_supabase', 'persist_approval_record', 'import_project_rows', 'run_workbook_macros', 'assign_work', 'mutate_schedule', 'change_status']).map((item) => (
                <li key={item}>{formatLabel(item)}</li>
              ))}
            </ul>
          </article>
        </section>
          </details>
        </section>
      </section>
    </main>
  )
}
