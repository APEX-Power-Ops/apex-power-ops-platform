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
  fieldPrepQueue: OperatingQueueItem[],
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
  const fieldPrepQueueLines = fieldPrepQueue.map((item) => `${item.title}: ${formatLabel(item.status)} - ${item.detail}`)
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
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length

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
    '## Local Field Prep Queue',
    '',
    `Field prep queue: ${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked.`,
    '',
    'This queue is browser-local prep guidance only. It does not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, or production writes.',
    '',
    markdownList(fieldPrepQueueLines),
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
  const [fieldBriefStatus, setFieldBriefStatus] = useState('')
  const [fieldObservationStatus, setFieldObservationStatus] = useState('')
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
  const fieldPrepQueue = useMemo(
    () => buildFieldPrepQueue(fieldReadinessChecks, fieldQuestionsDraft),
    [fieldReadinessChecks, fieldQuestionsDraft],
  )
  const completeQueueCount = operatingQueue.filter((item) => item.status === 'complete').length
  const nextQueueCount = operatingQueue.filter((item) => item.status === 'next').length
  const blockedQueueCount = operatingQueue.filter((item) => item.status === 'blocked').length
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length

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
      buildIntakeBrief(packet, workflowGates, persistenceReadinessGates, operatingQueue, fieldPrepQueue, notAllowed, futureRoute, reviewChecks, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
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
      buildExecutorHandoff(packet, workflowGates, persistenceReadinessGates, operatingQueue, notAllowed, futureRoute, reviewChecks, closeoutChecks, approvalDraft),
      'text/markdown',
    )
    setHandoffStatus(`Executor handoff prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldKickoffBrief() {
    if (!packet) {
      return
    }

    downloadTextFile(
      fieldKickoffBriefFileName(candidate),
      buildFieldKickoffBrief(packet, workflowGates, operatingQueue, fieldPrepQueue, notAllowed, futureRoute, reviewChecks, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
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
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/pm-review/import-candidate">Import candidate</Link>
            <Link href="/pm-review/import-admission-plan">Admission plan</Link>
            <Link href="/pm-review/import-approval-readiness">Approval readiness</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <button className="btn btn-outline" onClick={exportPmBrief} disabled={!packet}>
              Export PM Brief
            </button>
            <button className="btn btn-outline" onClick={exportApprovalPacketPreview} disabled={!packet}>
              Export Approval Preview JSON
            </button>
            <button className="btn btn-outline" onClick={exportExecutorHandoff} disabled={!packet}>
              Export Executor Handoff
            </button>
            <button className="btn btn-outline" onClick={exportFieldKickoffBrief} disabled={!packet}>
              Export Field Kickoff Brief
            </button>
            <button className="btn btn-outline" onClick={exportFieldObservationNotes} disabled={!packet}>
              Export Field Observation Notes
            </button>
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>
        {briefStatus ? <p style={{ margin: '0 0 1rem', color: 'var(--muted)', lineHeight: 1.55 }}>{briefStatus}</p> : null}
        {previewStatus ? <p style={{ margin: '0 0 1rem', color: 'var(--muted)', lineHeight: 1.55 }}>{previewStatus}</p> : null}
        {handoffStatus ? <p style={{ margin: '0 0 1rem', color: 'var(--muted)', lineHeight: 1.55 }}>{handoffStatus}</p> : null}
        {fieldBriefStatus ? <p style={{ margin: '0 0 1rem', color: 'var(--muted)', lineHeight: 1.55 }}>{fieldBriefStatus}</p> : null}
        {fieldObservationStatus ? <p style={{ margin: '0 0 1rem', color: 'var(--muted)', lineHeight: 1.55 }}>{fieldObservationStatus}</p> : null}

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

        <section aria-label="Local PM operating queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local PM Operating Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            Local queue for today&apos;s intake work. It translates the checklist, local decision draft, and readiness gates into practical next moves without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state.
          </p>
          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {formatCount(completeQueueCount)} complete / {formatCount(nextQueueCount)} next / {formatCount(blockedQueueCount)} blocked
          </p>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
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
        </section>

        <section className="notes-grid" style={{ marginBottom: '1rem' }}>
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

        <section aria-label="Workflow gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Workflow Gates</h2>
            <span className="status-pill status-awaiting-values">read-only</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
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
        </section>

        <section className="notes-grid" style={{ marginBottom: '1rem' }}>
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
        </section>

        <section aria-label="Admission and approval contract" className="notes-grid" style={{ marginBottom: '1rem' }}>
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
        </section>

        <section aria-label="Local review checklist" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Review Checklist</h2>
            <span className="status-pill status-configured">
              {formatCount(checklistCheckedCount)} of {formatCount(REVIEW_CHECKLIST_ITEMS.length)}
            </span>
          </div>
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
        </section>

        <section aria-label="Local approval decision draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Approval Decision Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </div>
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
        </section>

        <section aria-label="Local executor closeout intake" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Executor Closeout Intake</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(closeoutCheckedCount)} of {formatCount(CLOSEOUT_CHECKLIST_ITEMS.length)}
            </span>
          </div>
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
        </section>

        <section aria-label="Local field readiness checklist" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Readiness Checklist</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(fieldReadinessCheckedCount)} of {formatCount(FIELD_READINESS_CHECKLIST_ITEMS.length)}
            </span>
          </div>
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
        </section>

        <section aria-label="Local field questions draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Questions Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </div>
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
        </section>

        <section aria-label="Local field prep queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Local Field Prep Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </div>
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

        <section aria-label="Approval persistence readiness gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
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

        <section aria-label="Current PM next actions and guardrails" className="notes-grid">
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
      </section>
    </main>
  )
}
