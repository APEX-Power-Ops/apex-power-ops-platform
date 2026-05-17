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
  formula_error_row_count?: number
  formula_error_cell_count?: number
  formula_error_column_counts?: Record<string, number>
  formula_error_sample_rows?: Array<{
    source_row?: number
    scope?: string
    task_id?: string
    task?: string
    apparatus?: string
    designation?: string
    error_columns?: string[]
  }>
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

type ApprovalPersistenceStatus = {
  classification?: string
  current_candidate_match?: boolean
  candidate_id?: string
  candidate_version?: string
  approval_record_id?: string
  decision?: string
  mutation_id?: string
  audit_event_id?: string
  stale_fields?: string[]
  source?: string
  route?: string
  approval_storage_available?: boolean
  approval_record_count_for_candidate?: number
  audit_log_used_for_current_status?: boolean
  import_authority?: string
  error_type?: string
}

type IntakeWorkbenchPacket = {
  candidate: CandidatePayload
  admissionPlan: AdmissionPlan
  approvalContract: ApprovalContract
  storagePlan: ApprovalStoragePlan
  approvalStatus: ApprovalPersistenceStatus
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

type ApprovalDryRunReadinessStatus = 'ready' | 'needs_review' | 'blocked'

type ApprovalDryRunReadinessItem = {
  id: string
  title: string
  status: ApprovalDryRunReadinessStatus
  detail: string
}

type OperatingQueueStatus = 'complete' | 'next' | 'blocked'

type OperatingQueueItem = {
  id: string
  title: string
  status: OperatingQueueStatus
  detail: string
}

type OperatingQueueGroup = {
  id: string
  label: string
  items: OperatingQueueItem[]
}

type WorkflowGateItem = {
  title: string
  status: string
  detail: string
}

type WorkflowGateGroup = {
  id: string
  label: string
  items: WorkflowGateItem[]
}

type FieldPrepCoverageStatus = 'covered' | 'partial' | 'open' | 'blocked'

type FieldPrepCoverageItem = {
  id: string
  title: string
  status: FieldPrepCoverageStatus
  detail: string
}

type FieldPrepCoverageGroup = {
  id: string
  label: string
  items: FieldPrepCoverageItem[]
}

type FieldPrepAgendaStatus = 'context' | 'ask' | 'confirm' | 'blocked'

type FieldPrepAgendaItem = {
  id: string
  title: string
  status: FieldPrepAgendaStatus
  detail: string
}

type FieldPrepAgendaGroup = {
  id: string
  label: string
  items: FieldPrepAgendaItem[]
}

type ImportExceptionRegisterStatus = 'covered' | 'open' | 'blocked'

type ImportExceptionRegisterItem = {
  id: string
  title: string
  status: ImportExceptionRegisterStatus
  detail: string
  evidence: string
}

type ImportExceptionRegisterGroup = {
  id: string
  label: string
  items: ImportExceptionRegisterItem[]
}

type PmIntakeSnapshotStatus = 'covered' | 'open' | 'blocked'

type PmIntakeSnapshotItem = {
  id: string
  title: string
  status: PmIntakeSnapshotStatus
  detail: string
  evidence: string
}

type PmIntakeSnapshotGroup = {
  id: string
  label: string
  items: PmIntakeSnapshotItem[]
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

type FieldStartOperatorScriptStatus = 'say-now' | 'check' | 'export' | 'blocked'

type FieldStartOperatorScriptItem = {
  id: string
  title: string
  status: FieldStartOperatorScriptStatus
  href: string
  detail: string
}

type FieldStartStopLineReviewStatus = 'blocked' | 'context'

type FieldStartStopLineReviewItem = {
  id: string
  title: string
  status: FieldStartStopLineReviewStatus
  href: string
  detail: string
}

type FieldStartCustomerSiteQuestionStatus = 'captured' | 'ask' | 'context' | 'blocked'

type FieldStartCustomerSiteQuestionItem = {
  id: string
  title: string
  status: FieldStartCustomerSiteQuestionStatus
  href: string
  detail: string
}

type FieldStartPmFollowupPromptReviewStatus = 'prompt' | 'ask' | 'context' | 'blocked'

type FieldStartPmFollowupPromptReviewItem = {
  id: string
  title: string
  status: FieldStartPmFollowupPromptReviewStatus
  href: string
  detail: string
}

type FieldStartConversationCloseoutPromptStatus = 'prompt' | 'confirm' | 'context' | 'blocked'

type FieldStartConversationCloseoutPromptItem = {
  id: string
  title: string
  status: FieldStartConversationCloseoutPromptStatus
  href: string
  detail: string
}

type FieldStartBringBackReviewQueueStatus = 'classify' | 'review' | 'context' | 'blocked'

type FieldStartBringBackReviewQueueItem = {
  id: string
  title: string
  status: FieldStartBringBackReviewQueueStatus
  href: string
  detail: string
}

type FieldStartBringBackSummaryTriageStripStatus = 'open' | 'context' | 'review' | 'blocked'

type FieldStartBringBackSummaryTriageStripItem = {
  id: string
  title: string
  status: FieldStartBringBackSummaryTriageStripStatus
  href: string
  detail: string
}

type FieldStartBringBackDetailJumpRailItem = FieldStartBringBackSummaryTriageStripItem

type FieldStartBringBackCueStatusLegendItem = {
  id: string
  label: FieldStartBringBackSummaryTriageStripStatus
  detail: string
}

type FieldStartSourceReviewBringBackLensStatus = 'check' | 'review' | 'context' | 'blocked'

type FieldStartSourceReviewBringBackLensItem = {
  id: string
  title: string
  status: FieldStartSourceReviewBringBackLensStatus
  href: string
  detail: string
}

type FieldStartCustomerSiteClarificationBringBackLensStatus = 'check' | 'review' | 'context' | 'blocked'

type FieldStartCustomerSiteClarificationBringBackLensItem = {
  id: string
  title: string
  status: FieldStartCustomerSiteClarificationBringBackLensStatus
  href: string
  detail: string
}

type FieldStartLeadResourceClarificationBringBackLensStatus = 'check' | 'review' | 'context' | 'blocked'

type FieldStartLeadResourceClarificationBringBackLensItem = {
  id: string
  title: string
  status: FieldStartLeadResourceClarificationBringBackLensStatus
  href: string
  detail: string
}

type FieldStartLaterBoundedPacketCandidateBringBackLensStatus = 'check' | 'review' | 'context' | 'blocked'

type FieldStartLaterBoundedPacketCandidateBringBackLensItem = {
  id: string
  title: string
  status: FieldStartLaterBoundedPacketCandidateBringBackLensStatus
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

type OutputSelectorGroup = {
  id: string
  label: string
  items: OutputSelectorItem[]
}

type HandoffGuideStatus = 'local-review' | 'field-context' | 'executor-context' | 'covered-context' | 'blocked'

type HandoffGuideItem = {
  id: string
  title: string
  status: HandoffGuideStatus
  href: string
  detail: string
}

type HandoffGuideGroup = {
  id: string
  label: string
  items: HandoffGuideItem[]
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

type WorkflowMapGroup = {
  id: string
  label: string
  items: WorkflowMapItem[]
}

type OpenItemsStatus = 'open' | 'blocked' | 'context'

type OpenItemsLensItem = {
  id: string
  title: string
  status: OpenItemsStatus
  href: string
  detail: string
}

type OpenItemsLensGroup = {
  id: string
  label: string
  items: OpenItemsLensItem[]
}

type PersistenceReadinessGateGroup = {
  id: string
  label: string
  items: ReadinessGate[]
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
    detail: 'The hosted approval table and PM-only route are ready for a later controlled submission packet, not browser approval yet.',
  },
  {
    id: 'hosted_parity_acknowledged',
    label: 'Hosted parity acknowledged',
    detail: 'Hosted PM intake, approval readback, and bounded Supabase read proof are green; this checklist still grants no browser write authority.',
  },
  {
    id: 'write_guardrails_confirmed',
    label: 'Write guardrails confirmed',
    detail: 'No browser approval submission, project import, assignment, schedule, or status mutation is admitted.',
  },
]

const REVIEW_CHECKLIST_GROUPS = [
  {
    id: 'source-review-evidence',
    label: 'Source Review Evidence',
    itemIds: ['source_freshness_reviewed', 'exceptions_reviewed', 'pm_decisions_captured'],
  },
  {
    id: 'approval-readiness-evidence',
    label: 'Approval Readiness Evidence',
    itemIds: ['admission_no_go_reviewed', 'approval_storage_understood', 'hosted_parity_acknowledged'],
  },
  {
    id: 'write-boundary-confirmation',
    label: 'Write Boundary Confirmation',
    itemIds: ['write_guardrails_confirmed'],
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

const CLOSEOUT_CHECKLIST_GROUPS = [
  {
    id: 'source-and-hosted-evidence',
    label: 'Source and Hosted Evidence',
    itemIds: ['source_commit_recorded', 'changed_files_listed', 'hosted_action_evidence_captured'],
  },
  {
    id: 'validation-and-verdict-evidence',
    label: 'Validation and Verdict Evidence',
    itemIds: ['validation_results_captured', 'final_verdict_classified', 'remaining_blocker_classified'],
  },
  {
    id: 'guardrails-and-next-action',
    label: 'Guardrails and Next Action',
    itemIds: ['guardrails_confirmed', 'coordinator_recommendation_captured'],
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

const FIELD_READINESS_CHECKLIST_GROUPS = [
  {
    id: 'source-and-scope-context',
    label: 'Source and Scope Readiness',
    itemIds: ['drawing_source_questions_captured', 'scope_assumptions_reviewed'],
  },
  {
    id: 'site-access-and-safety-readiness',
    label: 'Site Access and Safety Readiness',
    itemIds: ['site_access_contacts_captured', 'safety_planning_questions_captured'],
  },
  {
    id: 'crew-material-and-staging-readiness',
    label: 'Crew Material and Staging Readiness',
    itemIds: ['crew_equipment_questions_captured', 'material_staging_questions_captured'],
  },
  {
    id: 'customer-constraints-and-authority-boundary',
    label: 'Customer Constraints and Authority Boundary',
    itemIds: ['customer_constraint_questions_captured', 'field_authority_boundary_acknowledged'],
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
  const [candidate, admissionPlan, approvalContract, storagePlan, approvalStatus] = await Promise.all([
    readJson<CandidatePayload>('project-import-candidate'),
    readJson<AdmissionPlan>('project-import-admission-plan'),
    readJson<ApprovalContract>('project-import-approval-contract'),
    readJson<ApprovalStoragePlan>('project-import-approval-storage-plan'),
    readJson<ApprovalPersistenceStatus>('project-import-approval-status'),
  ])

  return { candidate, admissionPlan, approvalContract, storagePlan, approvalStatus }
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

function approvalStatusTone(status?: ApprovalPersistenceStatus | null) {
  const classification = status?.classification || ''
  if (!status || status.approval_storage_available === false) return 'status-deferred'
  if (classification === 'approved_for_import_packet') return 'status-configured'
  if (classification === 'no_approval_record' || classification === 'stale_approval_record') return 'status-awaiting-values'
  return 'status-deferred'
}

function approvalStatusSummary(status?: ApprovalPersistenceStatus | null) {
  if (!status) return 'waiting for approval status read'
  const storage = status.approval_storage_available === false ? 'storage unavailable' : 'storage available'
  return `${formatLabel(status.classification)}; ${storage}; import authority ${formatLabel(status.import_authority || 'not_admitted')}`
}

function approvalDryRunReadinessTone(status: ApprovalDryRunReadinessStatus) {
  if (status === 'ready') return 'status-configured'
  if (status === 'needs_review') return 'status-awaiting-values'
  return 'status-deferred'
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

function fieldStartOperatorScriptTone(status: FieldStartOperatorScriptStatus) {
  if (status === 'say-now' || status === 'check' || status === 'export') return 'status-configured'
  return 'status-deferred'
}

function fieldStartStopLineReviewTone(status: FieldStartStopLineReviewStatus) {
  if (status === 'context') return 'status-configured'
  return 'status-deferred'
}

function fieldStartCustomerSiteQuestionTone(status: FieldStartCustomerSiteQuestionStatus) {
  if (status === 'captured' || status === 'context') return 'status-configured'
  if (status === 'ask') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartPmFollowupPromptReviewTone(status: FieldStartPmFollowupPromptReviewStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'prompt' || status === 'ask') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartConversationCloseoutPromptTone(status: FieldStartConversationCloseoutPromptStatus) {
  if (status === 'context') return 'status-configured'
  if (status === 'prompt' || status === 'confirm') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartBringBackReviewQueueTone(status: FieldStartBringBackReviewQueueStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'classify') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartBringBackSummaryTriageStripTone(status: FieldStartBringBackSummaryTriageStripStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'open') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartSourceReviewBringBackLensTone(status: FieldStartSourceReviewBringBackLensStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'check') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartCustomerSiteClarificationBringBackLensTone(status: FieldStartCustomerSiteClarificationBringBackLensStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'check') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartLeadResourceClarificationBringBackLensTone(status: FieldStartLeadResourceClarificationBringBackLensStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'check') return 'status-awaiting-values'
  return 'status-deferred'
}

function fieldStartLaterBoundedPacketCandidateBringBackLensTone(status: FieldStartLaterBoundedPacketCandidateBringBackLensStatus) {
  if (status === 'context' || status === 'review') return 'status-configured'
  if (status === 'check') return 'status-awaiting-values'
  return 'status-deferred'
}

function outputSelectorTone(status: OutputSelectorStatus) {
  if (status === 'available-context' || status === 'field-context') return 'status-configured'
  if (status === 'blocked') return 'status-deferred'
  return 'status-awaiting-values'
}

function handoffGuideTone(status: HandoffGuideStatus) {
  if (status === 'field-context' || status === 'executor-context' || status === 'covered-context') return 'status-configured'
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

function warningColumnSummary(warning: CandidateWarning) {
  const counts = warning.formula_error_column_counts || {}
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([column, count]) => `${column}: ${formatCount(count)}`)
    .join('; ')
}

function warningSampleSummary(warning: CandidateWarning) {
  return (warning.formula_error_sample_rows || []).slice(0, 3).map((row) => {
    const rowLabel = row.source_row ? `row ${row.source_row}` : 'sample row'
    const taskLabel = firstAvailable(row.task_id, row.task, row.apparatus, row.designation)
    const columns = row.error_columns?.join(', ') || 'formula column'
    return `${rowLabel}: ${taskLabel} (${columns})`
  })
}

const PROJECT_DATA_ENTRY_WARNING_CODE = 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'

const PROJECT_DATA_ENTRY_DECISION_LABELS = [
  'ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE',
  'REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE',
  'HOLD_DATA_ENTRY_WARNING_NO_LIVE',
  'PROVIDE_EXACT_LIVE_ADMISSION_LATER',
]

const PROJECT_DATA_ENTRY_DECISION_LABEL_DETAILS = [
  {
    label: 'ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE',
    meaning: 'reviewed warning is accepted as non-blocking for no-live planning context only',
  },
  {
    label: 'REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE',
    meaning: 'source workbook correction is requested before warning acceptance or later live admission',
  },
  {
    label: 'HOLD_DATA_ENTRY_WARNING_NO_LIVE',
    meaning: 'keep the warning unresolved and continue no-live review only',
  },
  {
    label: 'PROVIDE_EXACT_LIVE_ADMISSION_LATER',
    meaning: 'defer warning disposition and live admission to a later exact-gate packet',
  },
]

const PROJECT_DATA_ENTRY_DECISION_OUTCOME_ROUTES = [
  {
    label: 'ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE',
    route: 'record no-live warning acceptance context; keep live admission separate',
  },
  {
    label: 'REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE',
    route: 'open a no-live workbook-correction packet before warning acceptance or live admission',
  },
  {
    label: 'HOLD_DATA_ENTRY_WARNING_NO_LIVE',
    route: 'keep the warning unresolved and continue no-live readiness only',
  },
  {
    label: 'PROVIDE_EXACT_LIVE_ADMISSION_LATER',
    route: 'defer disposition until a later exact live-admission packet',
  },
]

const PROJECT_DATA_ENTRY_VALID_RETURN_CHECKLIST = [
  {
    term: 'accepted',
    detail: 'exactly one PM Lane 238 Data Entry label',
  },
  {
    term: 'rejected',
    detail: 'explanation text; paraphrase; REQUEST_SOURCE_CORRECTION_NO_LIVE; multiple labels; continuation instruction; live admission language without a later admitting packet',
  },
  {
    term: 'after valid label',
    detail: 'record the label in a no-live decision packet and keep live admission separate',
  },
]

const PROJECT_DATA_ENTRY_SAFE_CONTINUATION_MOVES = [
  {
    term: 'allowed no-live continuation',
    detail: 'candidate/readiness review, packet drafting, Desktop Codex read-only scout review, and source/resource question preparation',
  },
  {
    term: 'requires exact PM label first',
    detail: 'warning acceptance, workbook-correction action, live admission packet, approval POST, approval row, and project import',
  },
  {
    term: 'Desktop Codex boundary',
    detail: 'review clarity and relay burden only; do not choose the PM label or mutate business state',
  },
]

const PROJECT_SOURCE_RESOURCE_QUESTION_PREP_CUES = [
  {
    term: 'review context',
    detail: 'use estimator, SLD/PDF, equipment inventory, and technician capability context to shape questions only',
  },
  {
    term: 'allowed question prep',
    detail: 'clarify source lineage, crew/tooling/lift/rental/equipment logistics, capability coverage, and customer/site constraints',
  },
  {
    term: 'blocked until admitted',
    detail: 'resource assignment, schedule/status changes, procurement or rental commitments, customer commitments, warning acceptance, approval rows, and project import',
  },
  {
    term: 'Desktop Codex support',
    detail: 'read-only clarity or relay-burden review only; no workbook/PDF content read, macros, hosted access, PM decision authority, or business-state mutation',
  },
]

function projectSourceResourceQuestionPrepCueLines(summary: { equipment_inventory_count?: number | null; capability_count?: number | null } = {}) {
  return [
    `equipment inventory context: ${formatCount(summary.equipment_inventory_count)} rows available for question shaping only`,
    `technician capability context: ${formatCount(summary.capability_count)} rows available for coverage questions only`,
    ...PROJECT_SOURCE_RESOURCE_QUESTION_PREP_CUES.map((item) => `${item.term}: ${item.detail}`),
  ]
}

const PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL = 'REQUEST_SOURCE_CORRECTION_NO_LIVE'
const PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_DESIGNATION = 'Ground Resistance Test Lot'

const PROJECT_DATA_ENTRY_ADMISSION_PREREQUISITES = [
  'current candidate identity',
  'warning disposition',
  'exact live phrase',
  'hosted-read currency',
  'replay/idempotency requirements',
  'approval-row evidence',
  'Desktop Codex review-only boundary',
]

function hasWarningCode(warnings: CandidateWarning[], code: string) {
  return warnings.some((warning) => warning.code === code)
}

function projectDataEntryDecisionGateExportLines(
  warnings: CandidateWarning[],
  summary: { equipment_inventory_count?: number | null; capability_count?: number | null } = {},
) {
  if (!hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)) {
    return []
  }

  return [
    '## Project Data Entry Decision Gate',
    '',
    `- Warning code: ${PROJECT_DATA_ENTRY_WARNING_CODE}`,
    '- Current state: no-live, waiting for one exact PM label before any later live admission path.',
    '- Next input needed: return exactly one PM Lane 238 label.',
    '- Response format: return_exactly_one_pm_lane_238_label.',
    `- Prior source correction already applied: ${PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL} -> ${PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_DESIGNATION}.`,
    '- Current workbook-correction label: REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE.',
    '- Paraphrases or prior source-correction labels do not close this gate.',
    '- Allowed labels:',
    ...PROJECT_DATA_ENTRY_DECISION_LABELS.map((label) => `  - ${label}`),
    '- Outcome routes:',
    ...PROJECT_DATA_ENTRY_DECISION_OUTCOME_ROUTES.map((item) => `  - ${item.label}: ${item.route}`),
    '- Valid return checklist:',
    ...PROJECT_DATA_ENTRY_VALID_RETURN_CHECKLIST.map((item) => `  - ${item.term}: ${item.detail}`),
    '- Safe no-live continuation moves:',
    ...PROJECT_DATA_ENTRY_SAFE_CONTINUATION_MOVES.map((item) => `  - ${item.term}: ${item.detail}`),
    '- Source/resource question prep cue:',
    ...projectSourceResourceQuestionPrepCueLines(summary).map((line) => `  - ${line}`),
    '- Admission prerequisites:',
    ...PROJECT_DATA_ENTRY_ADMISSION_PREREQUISITES.map((prerequisite) => `  - ${prerequisite}`),
    '- Authority boundary: display/export context only; no approval POST, approval row, import write, source writeback, hosted call, or business-state mutation.',
  ]
}

function projectDataEntrySourceCorrectionBoundary() {
  return {
    prior_source_correction_label: PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL,
    prior_source_correction_status: 'already_applied',
    corrected_candidate_designation: PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_DESIGNATION,
    applies_to_current_warning: false,
    current_workbook_correction_label: 'REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE',
    detail: 'The Ground Resistance source-correction label is already resolved for miner-line-015; the current Project Data Entry formula warning requires a Data Entry-specific label before warning acceptance.',
  }
}

function projectDataEntryNextInputNeeded(present: boolean) {
  return {
    required: present,
    response_format: present ? 'return_exactly_one_pm_lane_238_label' : 'not_required',
    warning_code: PROJECT_DATA_ENTRY_WARNING_CODE,
    allowed_labels: present ? PROJECT_DATA_ENTRY_DECISION_LABEL_DETAILS : [],
    no_live_boundary: true,
    detail: present
      ? 'Return exactly one PM Lane 238 label to disposition the Project Data Entry formula warning; paraphrases and prior source-correction labels do not close this gate.'
      : 'No Project Data Entry warning label is needed for this candidate.',
  }
}

function projectDataEntryWarningDispositionGate(warnings: CandidateWarning[]) {
  const present = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)

  return {
    warning_code: PROJECT_DATA_ENTRY_WARNING_CODE,
    present,
    disposition_status: present ? 'requires_exact_pm_label' : 'not_applicable',
    accepted_by_current_local_review: false,
    allowed_labels: present ? PROJECT_DATA_ENTRY_DECISION_LABELS : [],
    admission_prerequisites: present ? PROJECT_DATA_ENTRY_ADMISSION_PREREQUISITES : [],
    source_correction_boundary: present ? projectDataEntrySourceCorrectionBoundary() : null,
    next_input_needed: projectDataEntryNextInputNeeded(present),
    detail: present
      ? 'The Project Data Entry warning has been reviewed locally, but it is not accepted for approval context until Jason provides one exact allowed no-live label.'
      : 'The Project Data Entry warning is not present on this candidate.',
  }
}

function unresolvedProjectDataEntryWarningCodes(warnings: CandidateWarning[]) {
  return hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE) ? [PROJECT_DATA_ENTRY_WARNING_CODE] : []
}

function acceptedWarningCodesForDryRun(warnings: CandidateWarning[], exceptionsReviewed: boolean) {
  if (!exceptionsReviewed) {
    return []
  }

  return warnings
    .map((warning) => warning.code)
    .filter((code): code is string => Boolean(code) && code !== PROJECT_DATA_ENTRY_WARNING_CODE)
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

function approvalDryRunEnvelopeFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-dry-run-envelope.json`
}

function approvalDryRunReadinessFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-dry-run-readiness.json`
}

function approvalReviewBundleFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-review-bundle.json`
}

function approvalLiveGatePreflightFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-approval-live-gate-preflight.json`
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

function fieldStartPreflightFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-start-preflight.json`
}

function fieldExecutionGateDesignFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-execution-gate-design.json`
}

function leadFieldAssignmentDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-lead-field-assignment-draft.json`
}

function fieldAuthorizationAssignmentDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-field-authorization-assignment-draft.json`
}

function scheduleStatusControlsDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-schedule-status-controls-draft.json`
}

function durableFieldRecordDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-durable-field-record-draft.json`
}

function productionTrackingDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-production-tracking-draft.json`
}

function customerReportingDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-customer-reporting-draft.json`
}

function financialHandoffDraftFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-financial-handoff-draft.json`
}

function pilotLaunchBinderFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pilot-launch-binder.json`
}

function pilotLaunchDailyBriefFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pilot-launch-daily-brief.json`
}

function pilotLaunchStandupCardFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pilot-launch-standup-card.json`
}

function pilotLaunchCaptureSheetFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pilot-launch-capture-sheet.json`
}

function pilotLaunchFollowupPacketFileName(candidate?: CandidatePayload | null) {
  const candidateId = candidate?.candidate_id || 'project-miner-intake'
  return `${candidateId.replace(/[^a-zA-Z0-9.-]+/g, '-')}-pilot-launch-follow-up-packet.json`
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
      id: 'hosted-schema-gate',
      title: 'Hosted schema gate',
      status: 'ready',
      detail: 'PM Lane 138 applied migration 003 on hosted Supabase and proved the approval table plus insert-only triggers with zero approval rows.',
    },
    {
      id: 'hosted-approval-route-gate',
      title: 'Hosted approval route gate',
      status: 'ready',
      detail: 'Hosted mutation-seam exposes approval status readback and the PM-only approval POST route, but this workbench does not call that POST.',
    },
    {
      id: 'browser-approval-submit-authority',
      title: 'Browser approval submit authority',
      status: 'blocked',
      detail: 'No browser approval button, approval POST wiring, or live approval-row creation is admitted until a later packet owns that UI submission path.',
    },
    {
      id: 'import-mutation-authority',
      title: 'Import mutation authority',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus import remain blocked until a later packet admits import after an approved approval record exists.',
    },
  ]
}

function groupPersistenceReadinessGates(gates: ReadinessGate[]): PersistenceReadinessGateGroup[] {
  const take = (ids: string[]) => gates.filter((gate) => ids.includes(gate.id))
  return [
    {
      id: 'local-review-context',
      label: 'Local Review Context',
      items: take(['approval-preview-context', 'review-checklist-evidence']),
    },
    {
      id: 'hosted-persistence-surface',
      label: 'Hosted Persistence Surface',
      items: take(['hosted-schema-gate', 'hosted-approval-route-gate']),
    },
    {
      id: 'blocked-future-write-authority',
      label: 'Blocked Future Write Authority',
      items: take(['browser-approval-submit-authority', 'import-mutation-authority']),
    },
  ]
}

function buildApprovalDryRunReadiness(
  packet: IntakeWorkbenchPacket | null,
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
): ApprovalDryRunReadinessItem[] {
  const candidate = packet?.candidate
  const admissionPlan = packet?.admissionPlan
  const approvalStatus = packet?.approvalStatus
  const summary = candidate?.summary || {}
  const warnings = candidate?.warnings || []
  const noGoChecks = admissionPlan?.no_go_checks || []
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const draftStarted = hasApprovalDraftContent(approvalDraft)
  const sourceAndWarningsReviewed = Boolean(reviewChecks.source_freshness_reviewed && reviewChecks.exceptions_reviewed)
  const dataEntryWarningUnresolved = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)
  const checklistHasEvidence = REVIEW_CHECKLIST_ITEMS.some((item) => reviewChecks[item.id])
  const noGoCheckIds = noGoChecks.map((check) => check.check_id).filter(Boolean)
  const noGoBlockerCount = noGoChecks.filter((check) => (check.status || '').includes('no_go')).length
  const approvalRecordCount = approvalStatus?.approval_record_count_for_candidate ?? 0
  const approvalStorageReady = Boolean(approvalStatus && approvalStatus.approval_storage_available !== false)

  return [
    {
      id: 'candidate-source-context',
      title: 'Candidate source context',
      status: candidate?.candidate_id && sourceFingerprint ? 'ready' : 'blocked',
      detail: candidate?.candidate_id && sourceFingerprint
        ? `${candidate.candidate_id} is loaded with source fingerprint ${sourceFingerprint}.`
        : 'Candidate identity or source fingerprint is missing; the dry-run envelope should not be used as packet context yet.',
    },
    {
      id: 'source-warning-review',
      title: 'Source and warning review',
      status: sourceAndWarningsReviewed ? dataEntryWarningUnresolved ? 'needs_review' : 'ready' : checklistHasEvidence ? 'needs_review' : 'blocked',
      detail: sourceAndWarningsReviewed
        ? dataEntryWarningUnresolved
          ? `Source freshness and warnings are checked locally, but ${PROJECT_DATA_ENTRY_WARNING_CODE} still needs one exact PM label before warning acceptance is available.`
          : `Source freshness and warnings are checked locally; candidate reports ${formatCount(summary.warning_count)} warning(s) and ${formatCount(summary.blocker_count)} blocker(s).`
        : 'Mark source freshness and warning review before treating the envelope as review-ready.',
    },
    {
      id: 'local-decision-draft',
      title: 'Local decision draft',
      status: draftComplete ? 'ready' : draftStarted ? 'needs_review' : 'blocked',
      detail: draftComplete
        ? `Decision draft is ${formatLabel(approvalDraft.decision)} with notes and local-only attestation present.`
        : 'Decision value, review notes, and local-only attestation are all required before the dry-run envelope is useful.',
    },
    {
      id: 'admission-no-go-review',
      title: 'Admission no-go review',
      status: noGoCheckIds.length ? reviewChecks.admission_no_go_reviewed ? noGoBlockerCount ? 'needs_review' : 'ready' : 'needs_review' : 'ready',
      detail: noGoCheckIds.length
        ? reviewChecks.admission_no_go_reviewed
          ? `${formatCount(noGoCheckIds.length)} no-go check(s) reviewed locally; ${formatCount(noGoBlockerCount)} still report no-go posture for later human decision.`
          : `${formatCount(noGoCheckIds.length)} no-go check(s) exist; mark admission no-go review before relying on the envelope.`
        : 'No admission no-go checks are reported for the current candidate.',
    },
    {
      id: 'approval-status-readback',
      title: 'Approval status readback',
      status: approvalStorageReady && approvalRecordCount === 0 ? 'ready' : approvalStatus ? 'needs_review' : 'blocked',
      detail: approvalStatus
        ? `${approvalStatusSummary(approvalStatus)}; ${formatCount(approvalRecordCount)} approval record(s) are reported for this candidate.`
        : 'Approval status readback has not loaded yet.',
    },
    {
      id: 'live-write-authority',
      title: 'Live write authority',
      status: 'blocked',
      detail: 'The exact PM Lane 142 live-write admission phrase is still required before any browser approval POST, approval-row creation, or project import.',
    },
  ]
}

function approvalDryRunReadinessCounts(items: ApprovalDryRunReadinessItem[]) {
  return {
    ready: items.filter((item) => item.status === 'ready').length,
    needsReview: items.filter((item) => item.status === 'needs_review').length,
    blocked: items.filter((item) => item.status === 'blocked').length,
  }
}

function approvalDryRunReadinessSummary(counts: ReturnType<typeof approvalDryRunReadinessCounts>) {
  return `${counts.ready} ready, ${counts.needsReview} needs review, ${counts.blocked} blocked`
}

function buildApprovalDryRunReadinessExport(
  packet: IntakeWorkbenchPacket,
  readinessItems: ApprovalDryRunReadinessItem[],
  notAllowed: string[],
  futureRoute: string,
) {
  const candidate = packet.candidate
  const admissionPlan = packet.admissionPlan
  const approvalStatus = packet.approvalStatus
  const counts = approvalDryRunReadinessCounts(readinessItems)
  const warnings = candidate.warnings || []

  return {
    readiness_kind: 'pm_import_candidate_approval_dry_run_readiness',
    readiness_version: 'pm_lane_145_local_readiness_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: candidate.project?.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    readiness_summary: {
      ready_count: counts.ready,
      needs_review_count: counts.needsReview,
      blocked_count: counts.blocked,
      summary: approvalDryRunReadinessSummary(counts),
    },
    warning_disposition_gate: projectDataEntryWarningDispositionGate(warnings),
    readiness_items: readinessItems,
    approval_status_readback: {
      classification: approvalStatus.classification || null,
      current_candidate_match: approvalStatus.current_candidate_match ?? null,
      approval_record_count_for_candidate: approvalStatus.approval_record_count_for_candidate ?? null,
      import_authority: approvalStatus.import_authority || 'not_admitted',
      route: approvalStatus.route || '/api/v1/reads/project-import-approval-status',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_review_only: true,
      future_route: futureRoute,
      project_import_authority: admissionPlan.mutation_authority || 'not_admitted',
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
    required_live_write_gate: 'I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.',
    blocked_boundaries: [
      ...notAllowed,
      'live_approval_post',
      'approval_row_creation',
      'project_import',
      'workpackage_task_apparatus_rows',
      'assignment_schedule_status_writes',
      'production_tracking_writes',
    ],
  }
}

function buildApprovalReviewBundleExport(
  packet: IntakeWorkbenchPacket,
  readinessItems: ApprovalDryRunReadinessItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const dryRunEnvelope = buildLocalApprovalSubmissionDryRun(packet, notAllowed, futureRoute, reviewChecks, approvalDraft)
  const readinessCheckpoint = buildApprovalDryRunReadinessExport(packet, readinessItems, notAllowed, futureRoute)

  return {
    bundle_kind: 'pm_import_candidate_approval_local_review_bundle',
    bundle_version: 'pm_lane_146_local_review_bundle_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: readinessCheckpoint.candidate_identity,
    included_artifacts: {
      dry_run_envelope_file: approvalDryRunEnvelopeFileName(candidate),
      readiness_checkpoint_file: approvalDryRunReadinessFileName(candidate),
      review_bundle_file: approvalReviewBundleFileName(candidate),
    },
    review_sequence: [
      'Confirm source freshness, warning review, and exception posture.',
      'Confirm local decision draft, review notes, and local-only attestation.',
      'Confirm approval status readback still reports no current approval record.',
      'Confirm the exact PM Lane 142 live-write gate is intentionally admitted before any future browser POST.',
    ],
    dry_run_envelope: dryRunEnvelope,
    readiness_checkpoint: readinessCheckpoint,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_review_only: true,
      bundle_export_only: true,
      future_route: futureRoute,
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
    required_live_write_gate: 'I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.',
    blocked_boundaries: Array.from(new Set([
      ...dryRunEnvelope.blocked_boundaries,
      ...readinessCheckpoint.blocked_boundaries,
    ])),
  }
}

function buildApprovalLiveGatePreflightExport(
  packet: IntakeWorkbenchPacket,
  readinessItems: ApprovalDryRunReadinessItem[],
  notAllowed: string[],
  futureRoute: string,
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
) {
  const candidate = packet.candidate
  const approvalStatus = packet.approvalStatus
  const sourceFingerprint = candidate.source_freshness?.aggregate_fingerprint
  const reviewBundle = buildApprovalReviewBundleExport(packet, readinessItems, notAllowed, futureRoute, reviewChecks, approvalDraft)
  const dryRunEnvelope = reviewBundle.dry_run_envelope
  const admissionNoGoReadiness = readinessItems.find((item) => item.id === 'admission-no-go-review')
  const dataEntryWarningDisposition = projectDataEntryWarningDispositionGate(candidate.warnings || [])
  const preflightItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'candidate-identity',
      title: 'Candidate identity',
      status: candidate.candidate_id && candidate.candidate_version && sourceFingerprint ? 'ready' : 'blocked',
      detail: candidate.candidate_id && candidate.candidate_version && sourceFingerprint
        ? `${candidate.candidate_id} ${candidate.candidate_version} is paired with source fingerprint ${sourceFingerprint}.`
        : 'Candidate id, candidate version, and source fingerprint are all required before a live gate can be considered.',
    },
    {
      id: 'local-review-bundle',
      title: 'Local review bundle',
      status: dryRunEnvelope.local_validation.decision_draft_complete ? 'ready' : 'blocked',
      detail: dryRunEnvelope.local_validation.decision_draft_complete
        ? 'The browser-local review bundle contains a complete decision draft and dry-run envelope.'
        : 'Complete the local decision draft before using the review bundle as live-gate context.',
    },
    {
      id: 'approval-status-readback',
      title: 'Approval status readback',
      status: approvalStatus.classification === 'no_approval_record' && approvalStatus.approval_record_count_for_candidate === 0 ? 'ready' : 'needs_review',
      detail: approvalStatus.classification === 'no_approval_record' && approvalStatus.approval_record_count_for_candidate === 0
        ? 'Approval status readback reports no current approval record for this candidate.'
        : 'Approval status readback should be reviewed before any live approval-row attempt.',
    },
    {
      id: 'warning-disposition-gate',
      title: 'Warning disposition gate',
      status: dataEntryWarningDisposition.present ? 'needs_review' : 'ready',
      detail: dataEntryWarningDisposition.present
        ? `${PROJECT_DATA_ENTRY_WARNING_CODE} remains reviewed but not accepted until one exact PM label is supplied.`
        : 'No Project Data Entry warning disposition is required for this candidate.',
    },
    {
      id: 'admission-no-go-posture',
      title: 'Admission no-go posture',
      status: admissionNoGoReadiness?.status || 'needs_review',
      detail: admissionNoGoReadiness?.detail || 'Admission no-go posture must be reviewed before any live approval-row attempt.',
    },
    {
      id: 'live-write-admission',
      title: 'Live write admission',
      status: 'blocked',
      detail: 'The exact PM Lane 142 live-write admission phrase has not been provided in this lane.',
    },
    {
      id: 'downstream-import-boundary',
      title: 'Downstream import boundary',
      status: 'blocked',
      detail: 'Project import, workpackage/task/apparatus writes, assignment, schedule, status, and production tracking remain blocked after any approval preflight.',
    },
  ]
  const counts = approvalDryRunReadinessCounts(preflightItems)

  return {
    preflight_kind: 'pm_import_candidate_approval_live_gate_preflight',
    preflight_version: 'pm_lane_147_local_live_gate_preflight_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: reviewBundle.candidate_identity,
    preflight_summary: {
      ready_count: counts.ready,
      needs_review_count: counts.needsReview,
      blocked_count: counts.blocked,
      summary: approvalDryRunReadinessSummary(counts),
      live_gate_status: 'blocked_until_exact_phrase',
    },
    preflight_items: preflightItems,
    approval_review_bundle: reviewBundle,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_preflight_only: true,
      future_route: futureRoute,
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
    required_live_write_gate: 'I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.',
    blocked_boundaries: reviewBundle.blocked_boundaries,
  }
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
      id: 'hosted-approval-gate-complete',
      title: 'Hosted approval gate complete',
      status: 'complete',
      detail: 'Hosted schema, approval status readback, approval POST route registration, and bounded MCP read proof are green with zero approval rows.',
    },
    {
      id: 'browser-approval-submission-packet',
      title: 'Browser approval submission packet',
      status: 'blocked',
      detail: 'A later packet must admit the browser approval control, live POST evidence, idempotent row creation, and rollback/return handling.',
    },
    {
      id: 'approval-row-creation',
      title: 'Approval row creation',
      status: 'blocked',
      detail: 'The approval table is empty by proof; this workbench must not create the first hosted approval row.',
    },
    {
      id: 'project-import-packet',
      title: 'Project import packet',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus rows remain blocked until approval submission has been admitted and audited in a separate packet.',
    },
  ]
}

function groupPmOperatingQueueItems(queue: OperatingQueueItem[]): OperatingQueueGroup[] {
  const byId = new Map(queue.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is OperatingQueueItem => Boolean(item))

  return [
    {
      id: 'local-review-moves',
      label: 'Local Review Moves',
      items: take(['source-exception-review', 'local-decision-draft', 'review-artifact-export']),
    },
    {
      id: 'approval-submission-boundary',
      label: 'Approval Submission Boundary',
      items: take(['hosted-approval-gate-complete', 'browser-approval-submission-packet', 'approval-row-creation']),
    },
    {
      id: 'future-import-boundary',
      label: 'Future Import Boundary',
      items: take(['project-import-packet']),
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

function groupFieldPrepQueueItems(queue: OperatingQueueItem[]): OperatingQueueGroup[] {
  const byId = new Map(queue.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is OperatingQueueItem => Boolean(item))

  return [
    {
      id: 'field-prep-inputs',
      label: 'Field Prep Inputs',
      items: take(['field-questions-draft', 'field-readiness-evidence']),
    },
    {
      id: 'kickoff-artifact',
      label: 'Kickoff Artifact',
      items: take(['field-kickoff-brief-export']),
    },
    {
      id: 'authority-and-production-boundary',
      label: 'Authority And Production Boundary',
      items: take(['field-authority-boundary-review', 'production-execution-tracking']),
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

function groupFieldPrepCoverageSnapshotItems(fieldPrepCoverageSnapshot: FieldPrepCoverageItem[]): FieldPrepCoverageGroup[] {
  const byId = new Map(fieldPrepCoverageSnapshot.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is FieldPrepCoverageItem => Boolean(item))

  return [
    {
      id: 'source-and-access-coverage',
      label: 'Source And Access Context',
      items: take(['source-drawing-coverage', 'access-safety-coverage']),
    },
    {
      id: 'crew-material-and-customer-coverage',
      label: 'Resource And Staging Context',
      items: take(['crew-equipment-coverage', 'material-staging-coverage', 'customer-constraint-coverage']),
    },
    {
      id: 'authority-and-production-coverage',
      label: 'Authority And Production Boundary',
      items: take(['field-authority-boundary', 'production-tracking-boundary']),
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

function groupFieldPrepConversationAgendaItems(fieldPrepConversationAgenda: FieldPrepAgendaItem[]): FieldPrepAgendaGroup[] {
  const byId = new Map(fieldPrepConversationAgenda.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is FieldPrepAgendaItem => Boolean(item))

  return [
    {
      id: 'source-and-access-conversation',
      label: 'Source And Access Conversation',
      items: take(['source-drawing-coverage-agenda', 'access-safety-coverage-agenda']),
    },
    {
      id: 'resource-and-staging-conversation',
      label: 'Resource And Staging Conversation',
      items: take(['crew-equipment-coverage-agenda', 'material-staging-coverage-agenda', 'customer-constraint-coverage-agenda']),
    },
    {
      id: 'authority-and-production-boundary',
      label: 'Authority And Production Boundary',
      items: take(['field-authority-boundary-agenda', 'production-tracking-boundary-agenda']),
    },
  ]
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

function groupImportExceptionRegisterItems(register: ImportExceptionRegisterItem[]): ImportExceptionRegisterGroup[] {
  const byId = new Map(register.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is ImportExceptionRegisterItem => Boolean(item))

  return [
    {
      id: 'source-review-signals',
      label: 'Source Review Signals',
      items: take(['source-freshness-evidence', 'candidate-warning-signals']),
    },
    {
      id: 'pm-decision-context',
      label: 'PM Decision Context',
      items: take(['human-decision-prompts', 'local-decision-draft-evidence']),
    },
    {
      id: 'admission-boundary',
      label: 'Admission Boundary',
      items: take(['admission-no-go-checks', 'future-write-boundary']),
    },
  ]
}

function groupWorkflowGateItems(workflowGates: WorkflowGateItem[]): WorkflowGateGroup[] {
  const byTitle = new Map(workflowGates.map((gate) => [gate.title, gate]))
  const take = (titles: string[]) => titles.map((title) => byTitle.get(title)).filter((gate): gate is WorkflowGateItem => Boolean(gate))

  return [
    {
      id: 'source-review-gates',
      label: 'Source Review Gates',
      items: take(['Source intake', 'Candidate review']),
    },
    {
      id: 'approval-readiness-gates',
      label: 'Approval Readiness Gates',
      items: take(['Admission gate', 'Approval readiness', 'Hosted parity']),
    },
    {
      id: 'future-import-boundary',
      label: 'Future Import Boundary',
      items: take(['Future import']),
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
      evidence: 'Hosted schema and approval route gates are ready; browser approval submission, first approval row creation, and import mutation remain blocked.',
    },
    {
      id: 'hosted-parity-boundary',
      title: 'Hosted parity boundary',
      status: 'covered',
      detail: 'Hosted PM intake, mutation-seam reads, approval status readback, and bounded Supabase MCP read proof are green.',
      evidence: 'PM Lane 041A/041B/041C/138 plus control-plane pooler maintenance closed the hosted read and schema gates.',
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

function groupPmIntakeSnapshotItems(snapshot: PmIntakeSnapshotItem[]): PmIntakeSnapshotGroup[] {
  const byId = new Map(snapshot.map((item) => [item.id, item]))
  const take = (ids: string[]) => ids.map((id) => byId.get(id)).filter((item): item is PmIntakeSnapshotItem => Boolean(item))

  return [
    {
      id: 'review-posture-snapshot',
      label: 'Review Posture',
      items: take(['exception-review-snapshot', 'decision-draft-snapshot']),
    },
    {
      id: 'field-readiness-posture-snapshot',
      label: 'Field Readiness Posture',
      items: take(['field-prep-snapshot', 'next-local-action-snapshot']),
    },
    {
      id: 'authority-boundary-posture-snapshot',
      label: 'Authority Boundary Posture',
      items: take(['approval-persistence-boundary', 'hosted-parity-boundary']),
    },
  ]
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

function buildFieldStartOperatorScript(
  candidate: CandidatePayload | undefined,
  fieldStartPreflight: ReturnType<typeof buildFieldStartPreflightExport> | null,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartOperatorScriptItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const nextFieldPrepMove = fieldPrepQueue.find((item) => item.status === 'next') || fieldPrepQueue.find((item) => item.status === 'blocked')
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const fieldQuestionsPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldObservationsPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const preflightSummary = fieldStartPreflight?.preflight_summary.summary || 'field-start preflight pending'
  const fieldStartStatus = fieldStartPreflight?.preflight_summary.field_start_status || 'not_admitted'

  return [
    {
      id: 'say-field-start-posture',
      title: 'Say field-start posture',
      status: 'say-now',
      href: '#field-prep',
      detail: `${projectName}: field-start preflight is ${preflightSummary}; field start authority remains ${formatLabel(fieldStartStatus)}.`,
    },
    {
      id: 'check-source-access-questions',
      title: 'Check source and access questions',
      status: fieldQuestionsPresent ? 'check' : 'blocked',
      href: '#field-prep',
      detail: fieldQuestionsPresent
        ? 'Use captured drawing/source and access/safety questions before field reliance.'
        : 'Capture drawing/source and access/safety questions before field reliance.',
    },
    {
      id: 'walk-queue-coverage-agenda',
      title: 'Walk queue, coverage, and agenda',
      status: nextFieldPrepMove?.status === 'blocked' ? 'blocked' : 'check',
      href: '#field-prep',
      detail: `Field prep queue: ${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked. Coverage: ${fieldPrepCoverageSummary(fieldPrepCoverageCount)}. Agenda: ${fieldPrepAgendaSummary(fieldPrepAgendaCount)}.`,
    },
    {
      id: 'export-context-only',
      title: 'Export context only',
      status: 'export',
      href: '#pm-output-selector',
      detail: `Use ${fieldStartPreflightFileName(candidate)} or ${fieldPrepPacketFileName(candidate)} as local conversation context; do not treat exports as authorization.`,
    },
    {
      id: 'stop-line-before-field-authority',
      title: 'Stop line before field authority',
      status: 'blocked',
      href: '#guardrails',
      detail: `Do not approve, import, authorize field work, assign crews, schedule/status work, create durable field records, or start production tracking from this workbench. Field observations present: ${fieldObservationsPresent ? 'yes' : 'no'}.`,
    },
  ]
}

function buildFieldStartStopLineReview(
  candidate: CandidatePayload | undefined,
  fieldStartPreflight: ReturnType<typeof buildFieldStartPreflightExport> | null,
  notAllowed: string[],
): FieldStartStopLineReviewItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const preflightSummary = fieldStartPreflight?.preflight_summary.summary || 'field-start preflight pending'
  const fieldStartStatus = fieldStartPreflight?.preflight_summary.field_start_status || 'blocked_until_field_authority_and_tracking_packet'
  const blockedBoundaryCount = fieldStartPreflight?.blocked_boundaries.length || notAllowed.length

  return [
    {
      id: 'field-authority-stop-line',
      title: 'Field authority stop line',
      status: 'blocked',
      href: '#field-prep',
      detail: `${projectName}: field start authority remains ${formatLabel(fieldStartStatus)}; preflight is ${preflightSummary}.`,
    },
    {
      id: 'assignment-schedule-status-stop-line',
      title: 'Assignment, schedule, and status stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: 'Do not assign leads or crews, schedule work, alter status, or direct field execution from this workbench.',
    },
    {
      id: 'durable-production-stop-line',
      title: 'Durable record and production stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: 'Do not create durable field records, production quantities, progress rows, completion evidence, or customer-facing production truth.',
    },
    {
      id: 'customer-finance-stop-line',
      title: 'Customer and finance stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: 'Do not create customer reports, billing exports, payroll exports, invoices, accounting postings, or external finance-system syncs.',
    },
    {
      id: 'context-only-stop-line',
      title: 'Context-only use',
      status: 'context',
      href: '#approval-readiness',
      detail: `Use the operator script and local exports only as conversation context; ${blockedBoundaryCount} blocked boundaries remain outside this browser-local review.`,
    },
  ]
}

function buildFieldStartCustomerSiteQuestions(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartCustomerSiteQuestionItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const drawingSourceQuestionsPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim())
  const siteAccessQuestionsPresent = Boolean(fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const materialStagingQuestionsPresent = Boolean(fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const customerConstraintQuestionsPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim())
  const pmFollowupContextPresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim() || fieldObservationScratchpad.observer_source.trim())

  return [
    {
      id: 'site-access-safety-question-review',
      title: 'Site access and safety questions',
      status: siteAccessQuestionsPresent ? 'captured' : 'ask',
      href: '#field-prep',
      detail: siteAccessQuestionsPresent
        ? `${projectName}: site access, escort, safety, or LOTO question context is captured locally; treat it as conversation only.`
        : `${projectName}: capture site access, escort, safety, or LOTO questions before the field-start conversation; do not turn them into instructions or commitments here.`,
    },
    {
      id: 'customer-constraint-question-review',
      title: 'Customer constraint questions',
      status: customerConstraintQuestionsPresent ? 'captured' : 'ask',
      href: '#field-prep',
      detail: customerConstraintQuestionsPresent
        ? 'Customer/site constraint question context is captured locally; keep it as conversation context before any future field authority packet.'
        : 'Customer/site constraint questions are still open; ask about access windows, shutdown constraints, escort requirements, and site contact questions as conversation context only.',
    },
    {
      id: 'material-staging-question-review',
      title: 'Material and staging questions',
      status: materialStagingQuestionsPresent ? 'captured' : 'ask',
      href: '#field-prep',
      detail: materialStagingQuestionsPresent
        ? 'Material, equipment, or staging question context is captured locally for the PM and lead conversation.'
        : 'Material, equipment, and staging questions are still open; keep them as local prep questions until a later approved field packet exists.',
    },
    {
      id: 'drawing-source-question-review',
      title: 'Drawing and source questions',
      status: drawingSourceQuestionsPresent ? 'captured' : 'ask',
      href: '#field-prep',
      detail: drawingSourceQuestionsPresent
        ? 'Drawing/source question context is captured locally for the PM and lead conversation.'
        : 'Drawing/source questions are still open; review source truth before any future field-authority packet.',
    },
    {
      id: 'pm-followup-customer-commitment-boundary',
      title: 'PM follow-up and customer commitment boundary',
      status: pmFollowupContextPresent ? 'context' : 'blocked',
      href: '#guardrails',
      detail: pmFollowupContextPresent
        ? 'Use PM follow-up notes and field observations only to frame questions; do not turn them into owner lists, assignments, customer commitments, customer reports, schedule/status changes, or field direction.'
        : 'No PM follow-up/customer-site context is captured yet; do not turn questions into owner lists, assignments, customer commitments, customer reports, schedule/status changes, or field direction from this workbench.',
    },
  ]
}

function buildFieldStartPmFollowupPromptReview(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartPmFollowupPromptReviewItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const pmFollowupPromptPresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())
  const customerSitePromptContextPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const leadPromptContextPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || fieldQuestionsDraft.crew_equipment_questions.trim() || fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const evidencePromptContextPresent = Boolean(fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.observation_date_or_shift.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())

  return [
    {
      id: 'pm-followup-question-prompt',
      title: 'PM follow-up question prompt',
      status: pmFollowupPromptPresent ? 'context' : 'ask',
      href: '#field-prep',
      detail: pmFollowupPromptPresent
        ? `${projectName}: existing PM follow-up prompt context is available; use it only to decide the next question for the PM, lead, or customer conversation.`
        : `${projectName}: PM follow-up prompt is open; decide the next PM question before accountability, timing, field instruction, customer commitment, or status language is discussed.`,
    },
    {
      id: 'customer-site-return-prompt',
      title: 'Customer/site return prompt',
      status: customerSitePromptContextPresent ? 'context' : 'ask',
      href: '#field-prep',
      detail: customerSitePromptContextPresent
        ? 'Use the customer/site question review to pick one return question; do not promise access, shutdown windows, dates, scope outcomes, or customer reporting.'
        : 'Return to site access, escort, shutdown-window, and contact-path questions before relying on field assumptions.',
    },
    {
      id: 'lead-conversation-prompt',
      title: 'Lead conversation prompt',
      status: leadPromptContextPresent ? 'prompt' : 'ask',
      href: '#field-prep',
      detail: leadPromptContextPresent
        ? 'Ask the lead which drawing, safety, material, equipment, or staging uncertainty needs clarification next; keep the answer as local conversation context.'
        : 'Lead prompt is open; start with source, access, material, equipment, and staging unknowns before field reliance.',
    },
    {
      id: 'evidence-source-prompt',
      title: 'Evidence/source prompt',
      status: evidencePromptContextPresent ? 'context' : 'ask',
      href: '#field-prep',
      detail: evidencePromptContextPresent
        ? 'Observation source context is available; ask what source record, site note, or workbook lineage should be reviewed next.'
        : 'Evidence/source prompt is open; identify what source record or site note should be checked before a later bounded packet.',
    },
    {
      id: 'next-packet-boundary-prompt',
      title: 'Next packet boundary prompt',
      status: 'blocked',
      href: '#guardrails',
      detail: 'If the follow-up needs accountability, timing, customer-facing language, field direction, report, schedule/status update, or durable record, stop here and author a later bounded packet; this section records none.',
    },
  ]
}

function buildFieldStartConversationCloseoutPrompts(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartConversationCloseoutPromptItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const hasConversationSource = Boolean(fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.observation_date_or_shift.trim())
  const hasCustomerSiteReturn = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const hasLeadResourceReturn = Boolean(fieldQuestionsDraft.crew_equipment_questions.trim() || fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const hasEvidenceReturn = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())
  const hasPmOpenQuestionReturn = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'conversation-summary-return-prompt',
      title: 'Conversation summary return prompt',
      status: hasConversationSource ? 'context' : 'prompt',
      href: '#field-prep',
      detail: hasConversationSource
        ? `${projectName}: conversation source context exists; bring back only the summary of what was clarified, what stayed open, and what needs later packet authority.`
        : `${projectName}: after the field-start conversation, bring back a short summary of what changed and what stayed open; do not store the summary in this panel.`,
    },
    {
      id: 'customer-site-return-closeout-prompt',
      title: 'Customer/site return closeout prompt',
      status: hasCustomerSiteReturn ? 'context' : 'confirm',
      href: '#field-prep',
      detail: hasCustomerSiteReturn
        ? 'Bring back customer/site clarifications as local review context only; do not turn access, shutdown, escort, or contact answers into promises or field direction here.'
        : 'Customer/site return remains open; ask what access, shutdown, escort, or contact answer still needs local review before any later bounded packet.',
    },
    {
      id: 'lead-resource-return-closeout-prompt',
      title: 'Lead/resource return closeout prompt',
      status: hasLeadResourceReturn ? 'context' : 'confirm',
      href: '#field-prep',
      detail: hasLeadResourceReturn
        ? 'Bring back lead, material, equipment, and staging clarifications as local review context only; do not create crew direction, assignments, or schedule/status changes here.'
        : 'Lead/resource return remains open; ask what material, equipment, staging, or lead clarification should be reviewed locally before field reliance.',
    },
    {
      id: 'evidence-source-return-closeout-prompt',
      title: 'Evidence/source return prompt',
      status: hasEvidenceReturn ? 'context' : 'confirm',
      href: '#field-prep',
      detail: hasEvidenceReturn
        ? 'Bring back the source record, drawing, workbook row, or site note that should be checked next; keep it as local source-review context.'
        : 'Evidence/source return remains open; identify the source record, drawing, workbook row, or site note to inspect before any later authority packet.',
    },
    {
      id: 'next-packet-closeout-boundary',
      title: 'Next packet closeout boundary',
      status: hasPmOpenQuestionReturn ? 'blocked' : 'prompt',
      href: '#guardrails',
      detail: hasPmOpenQuestionReturn
        ? 'Open PM follow-up context exists; if it requires accountability, timing, customer-facing language, field direction, report, schedule/status update, or durable record, stop and author a later bounded packet.'
        : 'If the conversation reveals a needed next move, bring back only the packet question; do not turn it into work lists, accountability fields, timing fields, commitments, reports, or writes here.',
    },
  ]
}

function buildFieldStartBringBackReviewQueue(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartBringBackReviewQueueItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const sourceReviewContextPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())
  const customerSiteClarificationPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const leadResourceClarificationPresent = Boolean(fieldQuestionsDraft.crew_equipment_questions.trim() || fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const boundedPacketCandidatePresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'source-review-return-queue',
      title: 'Source review',
      status: sourceReviewContextPresent ? 'context' : 'classify',
      href: '#field-prep',
      detail: sourceReviewContextPresent
        ? `${projectName}: source-review context exists; route returned drawing, workbook row, site note, observer/source, or work-area context to local source review only.`
        : `${projectName}: if the conversation returns a drawing, workbook row, site note, observer/source, or work-area question, classify it as local source review only.`,
    },
    {
      id: 'customer-site-clarification-return-queue',
      title: 'Customer/site clarification',
      status: customerSiteClarificationPresent ? 'review' : 'classify',
      href: '#field-prep',
      detail: customerSiteClarificationPresent
        ? 'Customer/site clarification context exists; route returned access, shutdown, escort, contact, safety, or constraint answers to local review only.'
        : 'If the conversation returns access, shutdown, escort, contact, safety, or constraint answers, classify them as customer/site clarification only.',
    },
    {
      id: 'lead-resource-clarification-return-queue',
      title: 'Lead/resource clarification',
      status: leadResourceClarificationPresent ? 'review' : 'classify',
      href: '#field-prep',
      detail: leadResourceClarificationPresent
        ? 'Lead/resource clarification context exists; route returned lead, material, equipment, staging, or crew-readiness context to local review only.'
        : 'If the conversation returns lead, material, equipment, staging, or crew-readiness context, classify it as lead/resource clarification only.',
    },
    {
      id: 'later-bounded-packet-candidate-return-queue',
      title: 'Later bounded packet candidate',
      status: boundedPacketCandidatePresent ? 'blocked' : 'classify',
      href: '#guardrails',
      detail: boundedPacketCandidatePresent
        ? 'Open PM follow-up context exists; if the return needs accountability, timing, customer-facing language, field direction, durable record, schedule/status update, report, or write authority, stop and author a later bounded packet.'
        : 'If a returned item needs a move beyond local review, classify only the packet question; do not create work lists, timing fields, commitments, reports, records, or writes here.',
    },
  ]
}

function buildFieldStartBringBackSummaryTriageStrip(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartBringBackSummaryTriageStripItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const sourceReviewContextPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())
  const customerSiteClarificationPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const leadResourceClarificationPresent = Boolean(fieldQuestionsDraft.crew_equipment_questions.trim() || fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const boundedPacketCandidatePresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'source-review-summary-triage',
      title: 'Source review context',
      status: sourceReviewContextPresent ? 'context' : 'open',
      href: '#pm-field-start-source-review-bring-back-lens',
      detail: sourceReviewContextPresent
        ? `${projectName}: source-review context is present; open the source lens for returned drawing, workbook, site note, observer/source, or work-area review only.`
        : `${projectName}: no returned source-review context is captured yet; if one returns, use the source lens before any later packet.`,
    },
    {
      id: 'customer-site-summary-triage',
      title: 'Customer/site clarification context',
      status: customerSiteClarificationPresent ? 'review' : 'open',
      href: '#pm-field-start-customer-site-clarification-bring-back-lens',
      detail: customerSiteClarificationPresent
        ? 'Customer/site clarification context is present; open the clarification lens for access, shutdown, escort, contact, safety, or constraint review only.'
        : 'No returned customer/site clarification context is captured yet; if one returns, keep it local until a later bounded packet admits more.',
    },
    {
      id: 'lead-resource-summary-triage',
      title: 'Lead/resource clarification context',
      status: leadResourceClarificationPresent ? 'review' : 'open',
      href: '#pm-field-start-lead-resource-clarification-bring-back-lens',
      detail: leadResourceClarificationPresent
        ? 'Lead/resource clarification context is present; open the lead/resource lens for lead, crew, material, equipment, or staging review only.'
        : 'No returned lead/resource clarification context is captured yet; if one returns, keep it as browser-local review context only.',
    },
    {
      id: 'later-packet-summary-triage',
      title: 'Later bounded packet candidate context',
      status: boundedPacketCandidatePresent ? 'blocked' : 'open',
      href: '#pm-field-start-later-bounded-packet-candidate-bring-back-lens',
      detail: boundedPacketCandidatePresent
        ? 'Open PM follow-up context is present; open the packet candidate lens and classify only whether a later bounded packet is needed.'
        : 'No later bounded packet candidate context is captured yet; if one returns, classify the packet question without creating work here.',
    },
  ]
}

function buildFieldStartBringBackDetailJumpRail(
  summaryItems: FieldStartBringBackSummaryTriageStripItem[],
): FieldStartBringBackDetailJumpRailItem[] {
  return summaryItems.map((item) => {
    if (item.id === 'source-review-summary-triage') {
      return {
        ...item,
        id: 'source-review-detail-jump',
        title: 'Open source review lens',
        detail: 'Jump to the source review lens for drawing, workbook, site note, observer/source, or work-area context only.',
      }
    }
    if (item.id === 'customer-site-summary-triage') {
      return {
        ...item,
        id: 'customer-site-detail-jump',
        title: 'Open customer/site clarification lens',
        detail: 'Jump to the customer/site clarification lens for access, shutdown, escort, contact, safety, or constraint review only.',
      }
    }
    if (item.id === 'lead-resource-summary-triage') {
      return {
        ...item,
        id: 'lead-resource-detail-jump',
        title: 'Open lead/resource clarification lens',
        detail: 'Jump to the lead/resource clarification lens for lead, crew, material, equipment, staging, or resource review only.',
      }
    }
    return {
      ...item,
      id: 'later-packet-detail-jump',
      title: 'Open later packet candidate lens',
      detail: 'Jump to the later bounded packet candidate lens only to classify whether a later bounded packet is needed; do not create that packet here.',
    }
  })
}

function buildFieldStartBringBackLensOpenContextCue(
  summaryItems: FieldStartBringBackSummaryTriageStripItem[],
): string {
  const cueNames = new Map<string, string>([
    ['source-review-summary-triage', 'Source review'],
    ['customer-site-summary-triage', 'Customer/site clarification'],
    ['lead-resource-summary-triage', 'Lead/resource'],
    ['later-packet-summary-triage', 'later packet candidate'],
  ])
  const populated = summaryItems.filter((item) => item.status !== 'open').map((item) => cueNames.get(item.id) || item.title)
  const empty = summaryItems.filter((item) => item.status === 'open').map((item) => cueNames.get(item.id) || item.title)

  if (populated.length === 0) {
    return 'Populated detail lens context: none yet. Keep returned field-start details local until a later bounded packet admits more.'
  }
  if (empty.length === 0) {
    return `Populated detail lens context: ${populated.join('; ')}. All bring-back lenses currently have local context; keep the cue read-only and use later bounded packets for anything beyond local review.`
  }
  return `Populated detail lens context: ${populated.join('; ')}. ${empty.join(' and ')} lenses have no returned context yet.`
}

function buildFieldStartBringBackCueStatusLegend(): FieldStartBringBackCueStatusLegendItem[] {
  return [
    {
      id: 'context-status-legend',
      label: 'context',
      detail: 'Context means populated source-review local context exists; review the matching lens before any later bounded packet.',
    },
    {
      id: 'review-status-legend',
      label: 'review',
      detail: 'Review means populated clarification context exists; inspect the matching lens locally before field reliance.',
    },
    {
      id: 'open-status-legend',
      label: 'open',
      detail: 'Open means no returned context is captured yet; keep any future return browser-local until admitted.',
    },
    {
      id: 'blocked-status-legend',
      label: 'blocked',
      detail: 'Blocked means a later bounded packet may be needed; classify only the packet question here.',
    },
  ]
}

function buildFieldStartSourceReviewBringBackLens(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartSourceReviewBringBackLensItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const sourceFingerprint = candidate?.source_freshness?.aggregate_fingerprint || 'source fingerprint pending'
  const drawingWorkbookContextPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || candidate?.source_freshness?.aggregate_fingerprint)
  const siteNoteContextPresent = Boolean(fieldObservationScratchpad.access_safety_observations.trim() || fieldObservationScratchpad.material_equipment_observations.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())
  const observerSourceContextPresent = Boolean(fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.observation_date_or_shift.trim())
  const workAreaReferencePresent = Boolean(fieldObservationScratchpad.workpackage_area_reference.trim())
  const laterPacketSourceQuestionPresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'drawing-workbook-source-lens',
      title: 'Drawing/workbook source check',
      status: drawingWorkbookContextPresent ? 'review' : 'check',
      href: '#project-packet',
      detail: drawingWorkbookContextPresent
        ? `${projectName}: drawing, workbook, or source fingerprint context is available; review it locally before relying on a returned field-start source item. Fingerprint: ${sourceFingerprint}.`
        : `${projectName}: if the return names a drawing, workbook row, or estimator source, check source lineage before any later bounded packet.`,
    },
    {
      id: 'site-note-source-lens',
      title: 'Site note source check',
      status: siteNoteContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: siteNoteContextPresent
        ? 'Returned site-note context exists in local observations; review it as source context only before any field reliance.'
        : 'If the return is a site note, access observation, safety observation, or material/equipment note, classify it for local source review before field reliance.',
    },
    {
      id: 'observer-source-lens',
      title: 'Observer/source context check',
      status: observerSourceContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: observerSourceContextPresent
        ? 'Observer/source context exists; verify who provided the return and when it was discussed before any later bounded packet.'
        : 'If the return depends on who said it or when it was discussed, keep that question outside this lens and classify it for source review only.',
    },
    {
      id: 'work-area-reference-lens',
      title: 'Work-area reference check',
      status: workAreaReferencePresent ? 'context' : 'check',
      href: '#field-prep',
      detail: workAreaReferencePresent
        ? 'Work-area reference context exists; review the returned area, workpackage, or apparatus reference locally before field reliance.'
        : 'If the return names an area, workpackage, apparatus, or location reference, check it against source context before any later packet.',
    },
    {
      id: 'source-review-packet-boundary-lens',
      title: 'Source review packet boundary',
      status: laterPacketSourceQuestionPresent ? 'blocked' : 'check',
      href: '#guardrails',
      detail: laterPacketSourceQuestionPresent
        ? 'Open PM follow-up source context exists; if the return requires accountability, field direction, schedule/status, customer-facing language, durable record, report, or write authority, stop and author a later bounded packet.'
        : 'If a returned source item needs more than local review, classify only the packet question; do not create records, tasks, timing fields, commitments, reports, or writes here.',
    },
  ]
}

function buildFieldStartCustomerSiteClarificationBringBackLens(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartCustomerSiteClarificationBringBackLensItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const accessShutdownContextPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const escortContactContextPresent = Boolean(fieldQuestionsDraft.site_access_safety_questions.trim() || fieldQuestionsDraft.customer_constraint_questions.trim() || fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())
  const safetyLotoContextPresent = Boolean(fieldQuestionsDraft.site_access_safety_questions.trim() || fieldObservationScratchpad.access_safety_observations.trim())
  const constraintAnswerContextPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'access-shutdown-answer-check-lens',
      title: 'Access/shutdown answer check',
      status: accessShutdownContextPresent ? 'review' : 'check',
      href: '#field-prep',
      detail: accessShutdownContextPresent
        ? `${projectName}: access, shutdown, escort, safety, or site-entry clarification context is available; keep it as browser-local review context only before any field reliance.`
        : `${projectName}: if the return names access, shutdown, escort, gate, badge, or site-entry details, keep it as customer/site clarification only.`,
    },
    {
      id: 'escort-contact-path-check-lens',
      title: 'Escort/contact path check',
      status: escortContactContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: escortContactContextPresent
        ? 'Customer/site or observer context exists; verify the escort, site contact, or conversation source before any later bounded packet.'
        : 'If the return depends on a customer contact, site escort, observer, or conversation timing, keep that context local and do not assign ownership here.',
    },
    {
      id: 'safety-loto-clarification-check-lens',
      title: 'Safety/LOTO clarification check',
      status: safetyLotoContextPresent ? 'review' : 'check',
      href: '#field-prep',
      detail: safetyLotoContextPresent
        ? 'Safety, LOTO, or access observation context exists; review it as customer/site clarification only before field reliance.'
        : 'If the return names safety, LOTO, PPE, escort, or access restrictions, classify it for local customer/site clarification before field reliance.',
    },
    {
      id: 'constraint-answer-boundary-lens',
      title: 'Constraint answer boundary',
      status: constraintAnswerContextPresent ? 'context' : 'check',
      href: '#guardrails',
      detail: constraintAnswerContextPresent
        ? 'Customer constraint or PM follow-up context exists; keep shutdown, outage-window, timing, and customer-facing answers as local clarification until a later bounded packet.'
        : 'If the return names shutdown windows, outage constraints, access hours, timing assumptions, or customer-facing language, classify only the packet question.',
    },
    {
      id: 'customer-site-promise-stop-line-lens',
      title: 'Customer/site promise stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: `${projectName}: if a returned customer/site answer needs accountability, timing, customer-facing language, field direction, report, schedule/status update, durable record, or write authority, stop and author a later bounded packet; do not create promises here.`,
    },
  ]
}

function buildFieldStartLeadResourceClarificationBringBackLens(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartLeadResourceClarificationBringBackLensItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const leadConversationSourcePresent = Boolean(fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.observation_date_or_shift.trim())
  const crewEquipmentContextPresent = Boolean(fieldQuestionsDraft.crew_equipment_questions.trim())
  const materialStagingContextPresent = Boolean(fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.material_equipment_observations.trim())
  const workAreaResourceContextPresent = Boolean(fieldQuestionsDraft.material_staging_questions.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())

  return [
    {
      id: 'lead-resource-source-check-lens',
      title: 'Lead conversation source check',
      status: leadConversationSourcePresent ? 'context' : 'check',
      href: '#field-prep',
      detail: 'If the return depends on who said it or when it was discussed, classify it as lead/resource clarification only and do not assign ownership here.',
    },
    {
      id: 'crew-equipment-readiness-check-lens',
      title: 'Crew readiness clarification check',
      status: crewEquipmentContextPresent ? 'review' : 'check',
      href: '#field-prep',
      detail: 'If the return names crew count, role mix, readiness, tooling, or lead availability, classify it as lead/resource clarification only before field reliance.',
    },
    {
      id: 'material-staging-path-check-lens',
      title: 'Material/equipment clarification check',
      status: materialStagingContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: 'If the return names material, rental, equipment, tooling, delivery, or receiving details, classify it as lead/resource clarification only before any later packet.',
    },
    {
      id: 'work-area-resource-fit-check-lens',
      title: 'Staging/resource limit check',
      status: workAreaResourceContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: 'If the return names laydown, staging, access-for-equipment, work area, or resource limits, keep it as browser-local review context only.',
    },
    {
      id: 'lead-resource-assignment-stop-line-lens',
      title: 'Lead/resource authority stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: `${projectName}: if a returned lead/resource answer needs a task, action item, owner, due date, assignment, timing field, schedule/status write, durable record, production tracking, report, export, backend route, storage key, button, or write authority, stop and author a later bounded packet; do not create it here.`,
    },
  ]
}

function buildFieldStartLaterBoundedPacketCandidateBringBackLens(
  candidate: CandidatePayload | undefined,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
): FieldStartLaterBoundedPacketCandidateBringBackLensItem[] {
  const projectName = candidate?.project?.name || candidate?.candidate_id || 'current Project Miner candidate'
  const futurePacketContextPresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())
  const evidenceContextPresent = Boolean(fieldQuestionsDraft.drawing_source_questions.trim() || fieldObservationScratchpad.observer_source.trim() || fieldObservationScratchpad.workpackage_area_reference.trim())
  const ownerTimingContextPresent = Boolean(fieldQuestionsDraft.customer_constraint_questions.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())
  const writePathContextPresent = Boolean(fieldQuestionsDraft.pm_followup_notes.trim() || fieldQuestionsDraft.customer_constraint_questions.trim() || fieldObservationScratchpad.open_questions_pm_followup.trim())

  return [
    {
      id: 'future-packet-trigger-check-lens',
      title: 'Future packet trigger check',
      status: futurePacketContextPresent ? 'review' : 'check',
      href: '#guardrails',
      detail: 'If the return needs a move beyond local review, classify only the future packet question; do not create work lists, timing fields, commitments, reports, records, or writes here.',
    },
    {
      id: 'authority-admission-check-lens',
      title: 'Authority admission check',
      status: writePathContextPresent ? 'blocked' : 'check',
      href: '#guardrails',
      detail: 'If the return needs approval submission, import, field authorization, assignment, schedule/status, durable record, production tracking, report, or billing authority, stop and author a later bounded packet.',
    },
    {
      id: 'evidence-context-check-lens',
      title: 'Evidence/context check',
      status: evidenceContextPresent ? 'context' : 'check',
      href: '#field-prep',
      detail: 'If the return depends on a drawing, workbook, site note, observer, work area, or source record, classify the evidence needed for the future packet without storing it here.',
    },
    {
      id: 'owner-timing-language-check-lens',
      title: 'Owner/timing language check',
      status: ownerTimingContextPresent ? 'context' : 'check',
      href: '#guardrails',
      detail: 'If the return needs owner, due date, timing, customer-facing language, field direction, or accountability, classify only that future-packet need and keep this section read-only.',
    },
    {
      id: 'bounded-packet-stop-line-lens',
      title: 'Bounded packet stop line',
      status: 'blocked',
      href: '#guardrails',
      detail: `${projectName}: if a returned item needs a task, action item, owner, due date, assignment, timing field, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking, export, backend route, storage key, button, or write authority, stop and author a later bounded packet; do not create it here.`,
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
      status: closeoutCheckedCount ? 'attention' : 'context',
      href: '#executor-closeout',
      detail: `Executor closeout intake is ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length}; hosted read, schema, approval status, and bounded MCP proof are green while closeout checks remain audit-prep context only.`,
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
): OutputSelectorGroup[] {
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const reviewCheckedCount = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const hasFieldQuestions = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const hasFieldObservations = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const reviewContextStatus: Exclude<OutputSelectorStatus, 'blocked'> = decisionDraftComplete && reviewCheckedCount ? 'available-context' : 'needs-local-context'
  const fieldContextStatus: Exclude<OutputSelectorStatus, 'blocked'> = hasFieldQuestions || hasFieldObservations || completeFieldPrepQueueCount ? 'field-context' : 'needs-local-context'
  const fieldQueueSummary = `${completeFieldPrepQueueCount} complete / ${nextFieldPrepQueueCount} next / ${blockedFieldPrepQueueCount} blocked`

  return [
    {
      id: 'review-outputs',
      label: 'Review Outputs',
      items: [
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
          status: reviewContextStatus,
          href: '#pm-operating-queue',
          detail: decisionDraftComplete && reviewCheckedCount
            ? `Approval Preview JSON has local decision draft context and ${reviewCheckedCount} of ${REVIEW_CHECKLIST_ITEMS.length} review checks for a later admitted approval-persistence packet.`
            : 'Approval Preview JSON should wait on local decision value, review notes, local-only attestation, and checklist evidence for useful later-packet context.',
        },
        {
          id: 'pm-intake-snapshot-output',
          title: 'PM Intake Snapshot',
          status: 'available-context',
          href: '#pm-intake-snapshot',
          detail: 'Use PM Intake Snapshot when the next review needs a compact local scan of exception posture, field prep, hosted parity, and blocked write boundaries.',
        },
        {
          id: 'import-exception-register-output',
          title: 'Import Exception Register',
          status: 'available-context',
          href: '#import-exception-register',
          detail: 'Use Import Exception Register when the next review needs source freshness, warning signals, human decisions, and no-go checks in one local view.',
        },
      ],
    },
    {
      id: 'executor-output',
      label: 'Executor Output',
      items: [
        {
          id: 'executor-handoff-output',
          title: 'Executor Handoff',
          status: closeoutCheckedCount ? 'available-context' : 'needs-local-context',
          href: '#executor-closeout',
          detail: closeoutCheckedCount
            ? `Executor Handoff has ${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks marked for returned executor context.`
            : 'Executor Handoff should wait on local closeout evidence checks when the next packet needs returned executor context.',
        },
      ],
    },
    {
      id: 'field-prep-basics',
      label: 'Field Prep Basics',
      items: [
        {
          id: 'field-kickoff-output',
          title: 'Field Kickoff Brief',
          status: hasFieldQuestions || completeFieldPrepQueueCount ? 'field-context' : 'needs-local-context',
          href: '#field-prep',
          detail: `Field Kickoff Brief is most useful after field questions or readiness evidence are captured; current field prep queue is ${fieldQueueSummary}.`,
        },
        {
          id: 'field-observation-output',
          title: 'Field Observation Notes',
          status: hasFieldObservations ? 'field-context' : 'needs-local-context',
          href: '#field-prep',
          detail: 'Use Field Observation Notes when local day-one observation context has been captured for PM and lead conversation prep.',
        },
        {
          id: 'field-coverage-output',
          title: 'Field Prep Coverage Snapshot',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: `Use Field Prep Coverage Snapshot when the next conversation needs source, access, material, crew, authority, and production-boundary coverage context; field prep queue is ${fieldQueueSummary}.`,
        },
        {
          id: 'field-agenda-output',
          title: 'Field Prep Conversation Agenda',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Field Prep Conversation Agenda when the next conversation needs context, asks, confirmations, and blocked boundary prompts grouped for review.',
        },
        {
          id: 'field-prep-packet-output',
          title: 'Field Prep Packet',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: `Field Prep Packet is the bundled field-prep artifact when the next conversation needs questions, coverage, agenda, readiness evidence, and observation context; current field prep queue is ${fieldQueueSummary}.`,
        },
        {
          id: 'field-start-preflight-output',
          title: 'Field Start Preflight',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Field Start Preflight as browser-local readiness context before any later packet admits field authority or production tracking.',
        },
      ],
    },
    {
      id: 'admission-drafts',
      label: 'Admission Drafts',
      items: [
        {
          id: 'field-execution-gate-output',
          title: 'Field Execution Gate Design',
          status: fieldContextStatus,
          href: '#approval-readiness',
          detail: 'Use Field Execution Gate Design when the next packet needs the no-write bridge toward later approval, import, field, and production admission.',
        },
        {
          id: 'lead-field-assignment-output',
          title: 'Lead Field Assignment Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Lead Field Assignment Draft for PM and lead review before any assignment, authorization, schedule, status, or durable record write is admitted.',
        },
        {
          id: 'field-authorization-assignment-output',
          title: 'Field Authorization Assignment Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Field Authorization Assignment Draft as packet-design context only; it does not authorize work or assign people.',
        },
        {
          id: 'schedule-status-output',
          title: 'Schedule Status Controls Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Schedule Status Controls Draft to review later schedule/status proof needs while schedule and status mutations stay blocked.',
        },
        {
          id: 'durable-field-record-output',
          title: 'Durable Field Record Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Durable Field Record Draft to review later daily record proof while durable record, evidence, production, customer, and finance writes stay blocked.',
        },
        {
          id: 'production-tracking-output',
          title: 'Production Tracking Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Production Tracking Draft to review later quantity, labor, apparatus, progress, audit, and readback proof while production tracking stays blocked.',
        },
        {
          id: 'customer-reporting-output',
          title: 'Customer Reporting Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Customer Reporting Draft to review later report and completion evidence proof while customer-facing outputs stay blocked.',
        },
        {
          id: 'financial-handoff-output',
          title: 'Financial Handoff Draft',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Financial Handoff Draft to review later billing, payroll, invoice/accounting, labor reconciliation, audit, and readback proof while finance writes stay blocked.',
        },
      ],
    },
    {
      id: 'pilot-launch-outputs',
      label: 'Pilot Launch Outputs',
      items: [
        {
          id: 'pilot-launch-binder-output',
          title: 'Pilot Launch Binder',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Pilot Launch Binder when the next review needs one bundled local context across approval preflight, field start, admission drafts, and blocked boundaries.',
        },
        {
          id: 'pilot-launch-daily-brief-output',
          title: 'Pilot Launch Daily Brief',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Pilot Launch Daily Brief when the next PM, lead, or customer conversation needs a compact today-focused review sequence.',
        },
        {
          id: 'pilot-launch-standup-card-output',
          title: 'Pilot Launch Standup Card',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Pilot Launch Standup Card when the next conversation needs role-based talk tracks, no-go checks, and local capture prompts.',
        },
        {
          id: 'pilot-launch-capture-sheet-output',
          title: 'Pilot Launch Capture Sheet',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Pilot Launch Capture Sheet when the next meeting needs blank local prompts for PM decisions, blockers, customer/site questions, and executor follow-up.',
        },
        {
          id: 'pilot-launch-followup-output',
          title: 'Pilot Launch Follow-Up Packet',
          status: fieldContextStatus,
          href: '#field-prep',
          detail: 'Use Pilot Launch Follow-Up Packet when the next review needs copy/paste return sections for VS Code Codex, Desktop Codex, or sidecar scout closeout.',
        },
      ],
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
): HandoffGuideGroup[] {
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
      id: 'review-context-handoff',
      label: 'Review Context',
      items: [
        {
          id: 'jason-local-review-context',
          title: 'Jason local review',
          status: 'local-review',
          href: '#import-exception-register',
          detail: `Use the workbench for Jason review while exceptions are ${importExceptionRegisterSummary(exceptionCount)} and ${decisionDraftState}.`,
        },
      ],
    },
    {
      id: 'field-executor-context-handoff',
      label: 'Field And Executor Context',
      items: [
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
      ],
    },
    {
      id: 'approval-boundary-context-handoff',
      label: 'Approval Boundary Context',
      items: [
        {
          id: 'hosted-parity-executor-boundary',
          title: 'Hosted readiness context',
          status: 'covered-context',
          href: '#approval-readiness',
          detail: 'Hosted Vercel, Render, approval status readback, and bounded MCP proof are green; this local workbench still grants no browser write authority.',
        },
        {
          id: 'future-persistence-packet-boundary',
          title: 'Future approval-persistence packet boundary',
          status: 'blocked',
          href: '#approval-readiness',
          detail: `${blockedPersistenceGateCount} of ${persistenceReadinessGates.length} approval-persistence gates remain blocked and project import remains ${formatLabel(admissionAuthority)}.`,
        },
      ],
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
): WorkflowMapGroup[] {
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
      id: 'intake-review-path',
      label: 'Intake Review Path',
      items: [
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
      ],
    },
    {
      id: 'field-executor-path',
      label: 'Field And Executor Path',
      items: [
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
      ],
    },
    {
      id: 'future-authority-boundaries',
      label: 'Future Authority Boundaries',
      items: [
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
      ],
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
): OpenItemsLensGroup[] {
  const exceptionCount = importExceptionRegisterCounts(importExceptionRegister)
  const decisionDraftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const fieldPrepNextCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const fieldPrepBlockedCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const closeoutCheckedCount = CLOSEOUT_CHECKLIST_ITEMS.filter((item) => closeoutChecks[item.id]).length
  const blockedPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'blocked').length
  const admissionAuthority = admissionPlan?.mutation_authority || 'not_admitted'

  return [
    {
      id: 'local-attention-items',
      label: 'Local Attention Items',
      items: [
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
      ],
    },
    {
      id: 'executor-evidence-context',
      label: 'Executor Evidence Context',
      items: [
        {
          id: 'executor-closeout-open-items',
          title: 'Executor closeout evidence',
          status: closeoutCheckedCount === CLOSEOUT_CHECKLIST_ITEMS.length ? 'context' : 'open',
          href: '#executor-closeout',
          detail: `${closeoutCheckedCount} of ${CLOSEOUT_CHECKLIST_ITEMS.length} local closeout evidence checks are marked.`,
        },
      ],
    },
    {
      id: 'future-authority-blockers',
      label: 'Future Authority Blockers',
      items: [
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
      ],
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
  const approvalStatus = packet.approvalStatus
  const checkedItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).map((item) => item.id)
  const warnings = candidate.warnings || []
  const warningCodes = warnings.map((warning) => warning.code).filter((code): code is string => Boolean(code))
  const unresolvedWarningCodes = unresolvedProjectDataEntryWarningCodes(warnings)
  const acceptedWarningCodes = acceptedWarningCodesForDryRun(warnings, Boolean(reviewChecks.exceptions_reviewed))
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
    approval_status_readback: {
      classification: approvalStatus.classification || null,
      current_candidate_match: approvalStatus.current_candidate_match ?? null,
      approval_record_id: approvalStatus.approval_record_id || null,
      approval_storage_available: approvalStatus.approval_storage_available ?? null,
      approval_record_count_for_candidate: approvalStatus.approval_record_count_for_candidate ?? null,
      source: approvalStatus.source || null,
      route: approvalStatus.route || '/api/v1/reads/project-import-approval-status',
      import_authority: approvalStatus.import_authority || 'not_admitted',
    },
    local_review_evidence: {
      checklist_checked_count: checkedItems.length,
      checklist_total_count: REVIEW_CHECKLIST_ITEMS.length,
      checklist_checked_items: checkedItems,
      warning_review: {
        exceptions_reviewed: Boolean(reviewChecks.exceptions_reviewed),
        reviewed_warning_codes: reviewChecks.exceptions_reviewed ? warningCodes : [],
        accepted_warning_codes: acceptedWarningCodes,
        unresolved_warning_codes: unresolvedWarningCodes,
        warning_disposition_gate: projectDataEntryWarningDispositionGate(warnings),
      },
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

function buildLocalApprovalSubmissionDryRun(
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
  const approvalStatus = packet.approvalStatus
  const checkedItems = REVIEW_CHECKLIST_ITEMS.filter((item) => reviewChecks[item.id]).map((item) => item.id)
  const unresolvedWarningCodes = unresolvedProjectDataEntryWarningCodes(candidate.warnings || [])
  const acceptedWarningCodes = acceptedWarningCodesForDryRun(candidate.warnings || [], Boolean(reviewChecks.exceptions_reviewed))
  const noGoCheckIds = (admissionPlan.no_go_checks || []).map((check) => check.check_id).filter(Boolean)
  const sourceFingerprint = candidate.source_freshness?.aggregate_fingerprint || 'source-fingerprint-missing'
  const draftComplete = Boolean(approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation)
  const idempotencyBase = [
    candidate.candidate_id || 'candidate-unknown',
    candidate.candidate_version || 'candidate-version-unknown',
    sourceFingerprint,
    approvalDraft.decision || 'decision-missing',
  ].join(':')

  return {
    dry_run_kind: 'pm_import_candidate_browser_approval_dry_run',
    dry_run_version: 'pm_lane_142a_local_mock_v1',
    generated_locally_at: new Date().toISOString(),
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_mock_only: true,
      live_post_performed: false,
      approval_row_created: false,
      hosted_deploy_performed: false,
      project_import_authority: admissionPlan.mutation_authority || 'not_admitted',
    },
    intended_request: {
      method: 'POST',
      route: futureRoute,
      route_not_called_by_this_screen: true,
      server_write_performed: false,
    },
    envelope: {
      mutation_class: 'C',
      action_type: 'persist_import_approval',
      idempotency_key: `pm-import-approval:${idempotencyBase}`,
      actor: PM_ACTOR,
    },
    payload: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      source_fingerprint: sourceFingerprint,
      decision: approvalDraft.decision || null,
      review_notes: approvalDraft.review_notes.trim() || null,
      local_attestation: approvalDraft.local_attestation,
      accepted_warning_codes: acceptedWarningCodes,
      unresolved_warning_codes: unresolvedWarningCodes,
      warning_disposition_gate: projectDataEntryWarningDispositionGate(candidate.warnings || []),
      acknowledged_no_go_check_ids: reviewChecks.admission_no_go_reviewed ? noGoCheckIds : [],
      approval_contract_id: approvalContract.approval_contract_id || null,
      storage_table: storagePlan.recommended_table || null,
      approval_status_before_dry_run: {
        classification: approvalStatus.classification || null,
        approval_record_count_for_candidate: approvalStatus.approval_record_count_for_candidate ?? null,
        current_candidate_match: approvalStatus.current_candidate_match ?? null,
      },
    },
    local_validation: {
      decision_draft_complete: draftComplete,
      checklist_checked_count: checkedItems.length,
      checklist_checked_items: checkedItems,
      warning_acceptance_ready: Boolean(reviewChecks.exceptions_reviewed) && unresolvedWarningCodes.length === 0,
      no_go_acknowledgement_ready: Boolean(reviewChecks.admission_no_go_reviewed),
      write_guardrail_confirmed: Boolean(reviewChecks.write_guardrails_confirmed),
    },
    blocked_boundaries: [
      ...notAllowed,
      'live_approval_post',
      'approval_row_creation',
      'project_import',
      'workpackage_task_apparatus_rows',
      'assignment_schedule_status_writes',
      'production_tracking_writes',
    ],
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
  const approvalStatus = packet.approvalStatus
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const warnings = candidate.warnings || []
  const decisions = candidate.human_decisions || []
  const targetRows = admissionPlan.target_row_plan || {}

  const targetRowLines = Object.entries(targetRows).map(([key, value]) => `${formatLabel(key)}: ${formatValue(value)}`)
  const warningLines = warnings.map((warning) => `${warning.severity || 'unknown'} - ${warning.code || 'WARNING'}: ${warning.message || 'Review warning.'}`)
  const decisionLines = decisions.map((decision) => `${formatLabel(decision.decision_id)}: ${decision.prompt || 'Decision prompt unavailable.'}`)
  const projectDataEntryDecisionGateLines = projectDataEntryDecisionGateExportLines(warnings, summary)
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
  const sourceResourceQuestionPrepLines = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)
    ? projectSourceResourceQuestionPrepCueLines(summary)
    : []
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
    ...(projectDataEntryDecisionGateLines.length ? [...projectDataEntryDecisionGateLines, ''] : []),
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
    '## Approval Persistence Status Readback',
    '',
    `Status: ${approvalStatusSummary(approvalStatus)}.`,
    '',
    `- Current candidate match: ${formatValue(approvalStatus.current_candidate_match)}`,
    `- Approval records for candidate: ${formatCount(approvalStatus.approval_record_count_for_candidate)}`,
    `- Storage source: ${approvalStatus.source || storagePlan.recommended_table || 'not reported'}`,
    `- Read route: ${approvalStatus.route || '/api/v1/reads/project-import-approval-status'}`,
    '',
    'This status readback is informational only. It is not approval, persistence authority, import authority, assignment, schedule, status, or production state.',
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
    'This radar is browser-local constraint synthesis only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, perform hosted writes, or write production state.',
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
    ...(sourceResourceQuestionPrepLines.length
      ? [
          'No-live source and resource question preparation cue:',
          '',
          markdownList(sourceResourceQuestionPrepLines),
          '',
          'This cue prepares PM/lead questions only. It does not grant live source access, source writeback, resource assignment, schedule/status change, task creation, field authorization, approval, import, or business-state mutation.',
          '',
        ]
      : []),
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
    `- Approval storage/design authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    `- Hosted approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Hosted approval route: ${futureRoute}`,
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
  const approvalStatus = packet.approvalStatus
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
    'Use this handoff only to review context, draft a later packet, or perform explicitly allowed read-only analysis. Do not treat this handoff as approval, persistence authority, import authority, hosted write proof, or task creation.',
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
    'This radar is browser-local constraint synthesis only. It does not approve, submit approval rows, import, assign, schedule, change status, create issues, create tasks, create durable field records, perform hosted writes, or write production state.',
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
    '## Remaining Approval Submission Blockers',
    '',
    markdownList(blockedGateLines),
    '',
    '## Approval Persistence Status Readback',
    '',
    `- Status: ${approvalStatusSummary(approvalStatus)}`,
    `- Current candidate match: ${formatValue(approvalStatus.current_candidate_match)}`,
    `- Approval records for candidate: ${formatCount(approvalStatus.approval_record_count_for_candidate)}`,
    `- Storage source: ${approvalStatus.source || storagePlan.recommended_table || 'not reported'}`,
    `- Read route: ${approvalStatus.route || '/api/v1/reads/project-import-approval-status'}`,
    '- This readback does not approve, persist, import, assign, schedule, change status, or mutate production state.',
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
    '## Hosted Approval Surface And Remaining Blocks',
    '',
    `- Hosted approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Hosted approval route: ${futureRoute}`,
    `- Admission plan: ${admissionPlan.admission_plan_id || 'unknown'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    `- Approval contract: ${approvalContract.approval_contract_id || 'unknown'}`,
    `- Approval storage/design authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Safe Next Packet Evidence',
    '',
    '- Keep exact read-only source and candidate identity visible.',
    '- Preserve hosted schema, hosted readback, and bounded MCP proof as context only; do not treat them as browser approval authority.',
    '- Keep browser approval submission, first approval-row creation, and import mutation blocked unless a later packet explicitly admits them.',
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
  const sourceResourceQuestionPrepLines = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)
    ? projectSourceResourceQuestionPrepCueLines(summary)
    : []
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
    'Use this brief to align PM, lead, and field review conversations before execution tracking exists in production state. Do not treat it as a work authorization, schedule, assignment, status update, hosted write proof, approval record, import packet, or task creation.',
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
    ...(sourceResourceQuestionPrepLines.length
      ? [
          'No-live source and resource question preparation cue:',
          '',
          markdownList(sourceResourceQuestionPrepLines),
          '',
          'This cue prepares PM/lead questions only. It does not grant live source access, source writeback, resource assignment, schedule/status change, task creation, field authorization, approval, import, or business-state mutation.',
          '',
        ]
      : []),
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
    '## Hosted Approval Surface And Remaining Blocks',
    '',
    `- Hosted approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Hosted approval route: ${futureRoute}`,
    `- Admission plan: ${admissionPlan.admission_plan_id || 'unknown'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    `- Approval contract: ${approvalContract.approval_contract_id || 'unknown'}`,
    `- Approval storage/design authority: ${approvalContract.persistence_authority || storagePlan.persistence_authority || 'not_admitted'}`,
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Field-Prep Use',
    '',
    '- Use this brief as conversation prep and issue discovery only.',
    '- Do not create assignments, schedules, status changes, approval records, schema, SQL, or import rows from this brief.',
    '- Do not treat this local export as browser approval submission authority or hosted write evidence.',
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
    'Use these notes to remember PM, lead, customer, and field conversation context. Do not treat them as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, hosted write proof, or production tracking.',
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
    '- Do not treat this snapshot as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, durable field record, hosted write proof, or production tracking.',
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
    '- Do not treat this agenda as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, durable field record, hosted write proof, or production tracking.',
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
  const warnings = candidate.warnings || []
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
  const sourceResourceQuestionPrepLines = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)
    ? projectSourceResourceQuestionPrepCueLines(summary)
    : []
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
    ...(sourceResourceQuestionPrepLines.length
      ? [
          'No-live source and resource question preparation cue:',
          '',
          markdownList(sourceResourceQuestionPrepLines),
          '',
          'This cue prepares PM/lead questions only. It does not grant live source access, source writeback, resource assignment, schedule/status change, task creation, field authorization, approval, import, or business-state mutation.',
          '',
        ]
      : []),
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
    '## Hosted Approval Surface And Remaining Blocks',
    '',
    `- Hosted approval route: ${futureRoute}`,
    `- Hosted approval table: ${packet.storagePlan.recommended_table || 'not admitted'}`,
    '- Browser approval submission, first approval-row creation, project import, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
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

function buildFieldStartPreflightExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const summary = candidate.summary || {}
  const project = candidate.project || {}
  const fieldQuestionsPresent = hasFieldQuestionsDraftContent(fieldQuestionsDraft)
  const fieldObservationsPresent = hasFieldObservationScratchpadContent(fieldObservationScratchpad)
  const fieldReadinessCheckedItems = FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => fieldReadinessChecks[item.id])
  const fieldBoundaryAcknowledged = Boolean(fieldReadinessChecks.field_authority_boundary_acknowledged)
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const preflightItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'field-questions-context',
      title: 'Field questions context',
      status: fieldQuestionsPresent ? 'ready' : 'blocked',
      detail: fieldQuestionsPresent
        ? 'Browser-local field questions exist for PM, lead, and field review conversations.'
        : 'Capture local field questions before using this candidate as day-one field-start context.',
    },
    {
      id: 'field-readiness-evidence',
      title: 'Field readiness evidence',
      status: fieldReadinessCheckedItems.length > 0 ? 'ready' : 'blocked',
      detail: fieldReadinessCheckedItems.length > 0
        ? `${fieldReadinessCheckedItems.length} of ${FIELD_READINESS_CHECKLIST_ITEMS.length} field-readiness checks are marked as local prep evidence.`
        : 'Mark at least one field-readiness check before relying on the field-start preflight.',
    },
    {
      id: 'field-observation-context',
      title: 'Field observation context',
      status: fieldObservationsPresent ? 'ready' : 'needs_review',
      detail: fieldObservationsPresent
        ? 'Browser-local field observation context exists for the next PM or field conversation.'
        : 'Field observation scratchpad context is optional but should be reviewed before field reliance.',
    },
    {
      id: 'field-authority-boundary',
      title: 'Field authority boundary',
      status: fieldBoundaryAcknowledged ? 'ready' : 'blocked',
      detail: fieldBoundaryAcknowledged
        ? 'The local field-prep authority boundary is acknowledged for this candidate.'
        : 'Field authority boundary remains blocked; this preflight does not authorize work.',
    },
    {
      id: 'production-tracking-boundary',
      title: 'Production tracking boundary',
      status: 'blocked',
      detail: 'Durable field records, production tracking, assignments, schedules, and statuses remain blocked until a later packet explicitly admits the write path.',
    },
  ]
  const preflightCounts = approvalDryRunReadinessCounts(preflightItems)

  return {
    preflight_kind: 'pm_import_candidate_field_start_preflight',
    preflight_version: 'pm_lane_148_local_field_start_preflight_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    preflight_summary: {
      ready_count: preflightCounts.ready,
      needs_review_count: preflightCounts.needsReview,
      blocked_count: preflightCounts.blocked,
      summary: approvalDryRunReadinessSummary(preflightCounts),
      field_start_status: 'blocked_until_field_authority_and_tracking_packet',
    },
    field_prep_queue_summary: {
      complete_count: completeFieldPrepQueueCount,
      next_count: nextFieldPrepQueueCount,
      blocked_count: blockedFieldPrepQueueCount,
      summary: `${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked`,
    },
    field_prep_coverage_summary: {
      covered_count: fieldPrepCoverageCount.covered,
      partial_count: fieldPrepCoverageCount.partial,
      open_count: fieldPrepCoverageCount.open,
      blocked_count: fieldPrepCoverageCount.blocked,
      summary: fieldPrepCoverageSummary(fieldPrepCoverageCount),
    },
    field_prep_agenda_summary: {
      context_count: fieldPrepAgendaCount.context,
      ask_count: fieldPrepAgendaCount.ask,
      confirm_count: fieldPrepAgendaCount.confirm,
      blocked_count: fieldPrepAgendaCount.blocked,
      summary: fieldPrepAgendaSummary(fieldPrepAgendaCount),
    },
    preflight_items: preflightItems,
    field_prep_packet_context: {
      field_prep_packet_file: fieldPrepPacketFileName(candidate),
      field_kickoff_brief_file: fieldKickoffBriefFileName(candidate),
      field_observation_notes_file: fieldObservationNotesFileName(candidate),
      coverage_snapshot_file: fieldPrepCoverageSnapshotFileName(candidate),
      conversation_agenda_file: fieldPrepConversationAgendaFileName(candidate),
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_preflight_only: true,
      field_start_authority: 'not_admitted',
      future_approval_route: futureRoute,
      assignment_performed: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...notAllowed,
      'field_work_authorization',
      'assignment_schedule_status_writes',
      'durable_field_record_creation',
      'production_tracking_writes',
      'project_import',
    ])),
  }
}

function buildFieldExecutionGateDesignExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const fieldStartPreflight = buildFieldStartPreflightExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const gateItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'field-start-preflight-context',
      title: 'Field start preflight context',
      status: fieldStartPreflight.preflight_summary.ready_count > 0 ? 'ready' : 'needs_review',
      detail: `${fieldStartPreflightFileName(candidate)} provides the current no-write field-prep context for this design gate.`,
    },
    {
      id: 'approval-first-row-gate',
      title: 'Approval first-row gate',
      status: 'blocked',
      detail: 'PM Lane 142 exact live-write admission and first approval-row proof are still required before import or field execution can proceed.',
    },
    {
      id: 'project-import-gate',
      title: 'Project import gate',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus rows are not imported; no downstream field work can be assigned from this candidate yet.',
    },
    {
      id: 'lead-assignment-gate',
      title: 'Lead assignment gate',
      status: 'blocked',
      detail: 'Lead assignment is blocked until imported work exists and a later packet admits assignment write authority.',
    },
    {
      id: 'schedule-status-gate',
      title: 'Schedule and status gate',
      status: 'blocked',
      detail: 'Schedule and status changes are blocked until a later packet admits the exact mutation path and validation proof.',
    },
    {
      id: 'durable-field-record-gate',
      title: 'Durable field record gate',
      status: 'blocked',
      detail: 'Durable field records are blocked until a later packet admits the storage contract, mutation route, and audit/readback proof.',
    },
    {
      id: 'production-tracking-gate',
      title: 'Production tracking gate',
      status: 'blocked',
      detail: 'Production tracking rows and progress metrics remain blocked until a later packet admits the write path and rollback/readback rules.',
    },
  ]
  const gateCounts = approvalDryRunReadinessCounts(gateItems)

  return {
    gate_kind: 'pm_import_candidate_field_execution_gate_design',
    gate_version: 'pm_lane_149_local_field_execution_gate_design_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_start_preflight_summary: {
      file_name: fieldStartPreflightFileName(candidate),
      ready_count: fieldStartPreflight.preflight_summary.ready_count,
      needs_review_count: fieldStartPreflight.preflight_summary.needs_review_count,
      blocked_count: fieldStartPreflight.preflight_summary.blocked_count,
      summary: fieldStartPreflight.preflight_summary.summary,
      field_start_status: fieldStartPreflight.preflight_summary.field_start_status,
    },
    gate_summary: {
      ready_count: gateCounts.ready,
      needs_review_count: gateCounts.needsReview,
      blocked_count: gateCounts.blocked,
      summary: approvalDryRunReadinessSummary(gateCounts),
      execution_gate_status: 'blocked_until_approval_import_and_field_tracking_packets',
    },
    gate_items: gateItems,
    proposed_future_routes: {
      approval_route: futureRoute,
      project_import_route: 'not_admitted',
      lead_ops_route: '/lead-ops',
      field_tech_route: '/field-tech',
      pm_workfront_route: '/pm-review/workfront',
      durable_field_record_route: 'not_admitted',
      production_tracking_route: 'not_admitted',
    },
    minimum_admission_packets: [
      {
        id: 'approval-first-row',
        required_before: 'project_import',
        detail: 'Use the PM Lane 142 gate before any first approval row or live approval POST.',
      },
      {
        id: 'project-import',
        required_before: 'lead_assignment',
        detail: 'Admit an idempotent import mutation only after an accepted approval record exists.',
      },
      {
        id: 'field-authorization-and-assignment',
        required_before: 'field_execution',
        detail: 'Admit explicit field work authorization and assignment write rules before lead or field work starts.',
      },
      {
        id: 'schedule-status-controls',
        required_before: 'status_mutation',
        detail: 'Admit exact schedule and status mutation contracts before UI controls can change those records.',
      },
      {
        id: 'durable-field-record-and-production-tracking',
        required_before: 'production_tracking',
        detail: 'Admit durable field record storage, production tracking rows, audit proof, and readback before field progress is persisted.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_design_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_work_authorized: false,
      assignment_performed: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...fieldStartPreflight.blocked_boundaries,
      'live_approval_post',
      'first_approval_row_creation',
      'lead_assignment_writes',
      'schedule_status_mutations',
      'durable_field_record_writes',
    ])),
  }
}

function buildLeadFieldAssignmentDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const fieldStartPreflight = buildFieldStartPreflightExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const fieldExecutionGateDesign = buildFieldExecutionGateDesignExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const fieldPrepAgendaCount = fieldPrepAgendaCounts(fieldPrepConversationAgenda)
  const fieldPrepCoverageCount = fieldPrepCoverageCounts(fieldPrepCoverageSnapshot)
  const completeFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'complete').length
  const nextFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'next').length
  const blockedFieldPrepQueueCount = fieldPrepQueue.filter((item) => item.status === 'blocked').length
  const assignmentItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'field-context-package',
      title: 'Field context package',
      status: fieldStartPreflight.preflight_summary.ready_count > 0 ? 'ready' : 'needs_review',
      detail: `${fieldStartPreflightFileName(candidate)} and ${fieldPrepPacketFileName(candidate)} provide local field-start context for lead review.`,
    },
    {
      id: 'field-questions-and-observations',
      title: 'Field questions and observations',
      status: hasFieldQuestionsDraftContent(fieldQuestionsDraft) && hasFieldObservationScratchpadContent(fieldObservationScratchpad) ? 'ready' : 'needs_review',
      detail: hasFieldQuestionsDraftContent(fieldQuestionsDraft) && hasFieldObservationScratchpadContent(fieldObservationScratchpad)
        ? 'Local field questions and observation context are present for the lead assignment conversation.'
        : 'Capture field questions and observation context before relying on this draft as a lead assignment handoff.',
    },
    {
      id: 'lead-review-agenda',
      title: 'Lead review agenda',
      status: fieldPrepAgendaCount.ask > 0 || fieldPrepAgendaCount.confirm > 0 ? 'ready' : 'needs_review',
      detail: `${fieldPrepConversationAgendaFileName(candidate)} carries ${fieldPrepAgendaSummary(fieldPrepAgendaCount)} for PM and lead review.`,
    },
    {
      id: 'approval-before-assignment',
      title: 'Approval before assignment',
      status: 'blocked',
      detail: 'The first approval row is still blocked until PM Lane 142 live-write admission and proof complete.',
    },
    {
      id: 'import-before-assignment',
      title: 'Import before assignment',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus rows must be imported before any durable assignment can exist.',
    },
    {
      id: 'field-authorization-before-work',
      title: 'Field authorization before work',
      status: 'blocked',
      detail: 'Field work authorization remains blocked until a later packet admits the exact authorization and assignment write path.',
    },
    {
      id: 'schedule-status-authority',
      title: 'Schedule and status authority',
      status: 'blocked',
      detail: 'Schedule and status changes remain blocked until a later packet admits the exact mutation contract and readback proof.',
    },
    {
      id: 'durable-record-and-production-authority',
      title: 'Durable record and production authority',
      status: 'blocked',
      detail: 'Durable field records and production tracking remain blocked until a later packet admits storage, audit, and readback proof.',
    },
  ]
  const assignmentCounts = approvalDryRunReadinessCounts(assignmentItems)

  return {
    draft_kind: 'pm_import_candidate_lead_field_assignment_draft',
    draft_version: 'pm_lane_150_local_lead_field_assignment_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    draft_summary: {
      ready_count: assignmentCounts.ready,
      needs_review_count: assignmentCounts.needsReview,
      blocked_count: assignmentCounts.blocked,
      summary: approvalDryRunReadinessSummary(assignmentCounts),
      assignment_status: 'blocked_until_import_field_authorization_and_assignment_packet',
    },
    field_start_preflight_summary: {
      file_name: fieldStartPreflightFileName(candidate),
      ready_count: fieldStartPreflight.preflight_summary.ready_count,
      needs_review_count: fieldStartPreflight.preflight_summary.needs_review_count,
      blocked_count: fieldStartPreflight.preflight_summary.blocked_count,
      summary: fieldStartPreflight.preflight_summary.summary,
      field_start_status: fieldStartPreflight.preflight_summary.field_start_status,
    },
    field_execution_gate_summary: {
      file_name: fieldExecutionGateDesignFileName(candidate),
      ready_count: fieldExecutionGateDesign.gate_summary.ready_count,
      needs_review_count: fieldExecutionGateDesign.gate_summary.needs_review_count,
      blocked_count: fieldExecutionGateDesign.gate_summary.blocked_count,
      summary: fieldExecutionGateDesign.gate_summary.summary,
      execution_gate_status: fieldExecutionGateDesign.gate_summary.execution_gate_status,
    },
    local_prep_context: {
      field_prep_queue_summary: `${completeFieldPrepQueueCount} complete, ${nextFieldPrepQueueCount} next, ${blockedFieldPrepQueueCount} blocked`,
      field_prep_coverage_summary: fieldPrepCoverageSummary(fieldPrepCoverageCount),
      field_prep_agenda_summary: fieldPrepAgendaSummary(fieldPrepAgendaCount),
      source_files: {
        field_prep_packet_file: fieldPrepPacketFileName(candidate),
        field_start_preflight_file: fieldStartPreflightFileName(candidate),
        field_execution_gate_design_file: fieldExecutionGateDesignFileName(candidate),
        field_kickoff_brief_file: fieldKickoffBriefFileName(candidate),
        field_observation_notes_file: fieldObservationNotesFileName(candidate),
        coverage_snapshot_file: fieldPrepCoverageSnapshotFileName(candidate),
        conversation_agenda_file: fieldPrepConversationAgendaFileName(candidate),
      },
    },
    proposed_assignment_draft: {
      assignment_kind: 'lead_field_assignment',
      assigned_lead: null,
      assigned_crew: null,
      assignment_source: 'not_admitted',
      requires_pm_selection: true,
      requires_imported_workpackage_rows: true,
      requires_field_authorization_packet: true,
      requires_schedule_status_packet: true,
      requires_durable_field_record_packet: true,
      note: 'This draft is conversation context only. It does not select a lead, assign a crew, authorize work, schedule work, change status, or create a durable field record.',
    },
    assignment_items: assignmentItems,
    proposed_handoff_sequence: [
      {
        step: 'review_local_context',
        status: 'ready',
        detail: 'Use field prep, preflight, coverage, agenda, questions, and observation artifacts as PM/lead conversation context.',
      },
      {
        step: 'complete_first_approval_row_gate',
        status: 'blocked',
        detail: 'Complete explicit PM Lane 142 live-write admission before any approval row or import can be used.',
      },
      {
        step: 'admit_project_import_packet',
        status: 'blocked',
        detail: 'Admit project import only after approval proof exists and import idempotency/readback rules are approved.',
      },
      {
        step: 'admit_field_authorization_and_assignment_packet',
        status: 'blocked',
        detail: 'Admit field work authorization and lead/crew assignment write rules before operational field assignment.',
      },
      {
        step: 'admit_schedule_status_and_tracking_packets',
        status: 'blocked',
        detail: 'Admit schedule/status, durable field record, and production tracking packets before field progress is persisted.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_work_authorized: false,
      lead_selected: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...fieldExecutionGateDesign.blocked_boundaries,
      'lead_named_assignment',
      'crew_assignment_writes',
      'field_authorization_write',
      'schedule_status_write',
      'durable_field_record_creation',
      'production_tracking_writes',
    ])),
  }
}

function buildFieldAuthorizationAssignmentDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const fieldExecutionGateDesign = buildFieldExecutionGateDesignExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const leadFieldAssignmentDraft = buildLeadFieldAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const admissionItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'field-execution-gate-context',
      title: 'Field execution gate context',
      status: 'ready',
      detail: `${fieldExecutionGateDesignFileName(candidate)} maps the future approval, import, field, assignment, schedule/status, durable record, and production tracking gates.`,
    },
    {
      id: 'lead-field-assignment-draft-context',
      title: 'Lead field assignment draft context',
      status: 'ready',
      detail: `${leadFieldAssignmentDraftFileName(candidate)} provides PM/lead conversation context before a real assignment exists.`,
    },
    {
      id: 'approval-first-row-prerequisite',
      title: 'Approval first-row prerequisite',
      status: 'blocked',
      detail: 'The first approval row remains blocked until the explicit PM Lane 142 live-write gate is admitted and proved.',
    },
    {
      id: 'project-import-prerequisite',
      title: 'Project import prerequisite',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus rows must exist before any field authorization or assignment write can target durable records.',
    },
    {
      id: 'field-authorization-contract',
      title: 'Field authorization contract',
      status: 'blocked',
      detail: 'A later packet must define who can authorize field work, which candidate/import records it covers, and how audit/readback prove the authorization.',
    },
    {
      id: 'assignment-write-contract',
      title: 'Assignment write contract',
      status: 'blocked',
      detail: 'A later packet must define lead/crew assignment write rules, idempotency, rollback posture, audit linkage, and readback proof.',
    },
    {
      id: 'schedule-status-prerequisite',
      title: 'Schedule and status prerequisite',
      status: 'blocked',
      detail: 'Schedule and status mutations remain separate gates until exact routes, validations, and readback proof are admitted.',
    },
    {
      id: 'durable-record-production-prerequisite',
      title: 'Durable record and production prerequisite',
      status: 'blocked',
      detail: 'Durable field records and production tracking remain separate gates until storage, audit, and readback proof are admitted.',
    },
  ]
  const admissionCounts = approvalDryRunReadinessCounts(admissionItems)

  return {
    draft_kind: 'pm_import_candidate_field_authorization_assignment_admission_draft',
    draft_version: 'pm_lane_151_local_field_authorization_assignment_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    admission_draft_summary: {
      ready_count: admissionCounts.ready,
      needs_review_count: admissionCounts.needsReview,
      blocked_count: admissionCounts.blocked,
      summary: approvalDryRunReadinessSummary(admissionCounts),
      admission_status: 'blocked_until_approval_import_and_explicit_field_authorization_packet',
    },
    field_execution_gate_summary: {
      file_name: fieldExecutionGateDesignFileName(candidate),
      ready_count: fieldExecutionGateDesign.gate_summary.ready_count,
      needs_review_count: fieldExecutionGateDesign.gate_summary.needs_review_count,
      blocked_count: fieldExecutionGateDesign.gate_summary.blocked_count,
      summary: fieldExecutionGateDesign.gate_summary.summary,
      execution_gate_status: fieldExecutionGateDesign.gate_summary.execution_gate_status,
    },
    lead_field_assignment_draft_summary: {
      file_name: leadFieldAssignmentDraftFileName(candidate),
      ready_count: leadFieldAssignmentDraft.draft_summary.ready_count,
      needs_review_count: leadFieldAssignmentDraft.draft_summary.needs_review_count,
      blocked_count: leadFieldAssignmentDraft.draft_summary.blocked_count,
      summary: leadFieldAssignmentDraft.draft_summary.summary,
      assignment_status: leadFieldAssignmentDraft.draft_summary.assignment_status,
    },
    proposed_admission_packet: {
      packet_kind: 'field_authorization_and_assignment',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import'],
      required_before: ['field_execution', 'schedule_status_mutation', 'durable_field_record', 'production_tracking'],
      proposed_routes: {
        field_authorization_route: 'not_admitted',
        lead_assignment_route: 'not_admitted',
        crew_assignment_route: 'not_admitted',
        schedule_status_route: 'not_admitted',
        durable_field_record_route: 'not_admitted',
        production_tracking_route: 'not_admitted',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization write contract is approved',
        'lead/crew assignment idempotency is defined',
        'audit linkage and readback are proved',
        'downstream schedule/status and production tracking remain blocked unless separately admitted',
      ],
    },
    admission_items: admissionItems,
    proposed_packet_sequence: [
      {
        step: 'complete_approval_first_row_gate',
        status: 'blocked',
        detail: 'Use the PM Lane 142 exact admission phrase and proof before any live approval POST or first approval row.',
      },
      {
        step: 'complete_project_import_gate',
        status: 'blocked',
        detail: 'Admit project import only after approval proof exists and import idempotency/readback rules are accepted.',
      },
      {
        step: 'admit_field_authorization_contract',
        status: 'blocked',
        detail: 'Define field work authorization scope, PM approval requirements, audit fields, and readback proof.',
      },
      {
        step: 'admit_assignment_write_contract',
        status: 'blocked',
        detail: 'Define lead/crew assignment target records, idempotency, replay behavior, rollback posture, and audit linkage.',
      },
      {
        step: 'keep_downstream_tracking_blocked',
        status: 'blocked',
        detail: 'Keep schedule/status, durable field record, and production tracking writes blocked until separate packets admit them.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_admission_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_selected: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...leadFieldAssignmentDraft.blocked_boundaries,
      'field_authorization_contract_write',
      'lead_assignment_contract_write',
      'crew_assignment_contract_write',
      'assignment_audit_write',
      'assignment_readback_route',
    ])),
  }
}

function buildScheduleStatusControlsDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const fieldAuthorizationAssignmentDraft = buildFieldAuthorizationAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const controlItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'field-authorization-assignment-context',
      title: 'Field authorization and assignment context',
      status: 'ready',
      detail: `${fieldAuthorizationAssignmentDraftFileName(candidate)} defines the no-write prerequisite packet for later schedule/status controls.`,
    },
    {
      id: 'approval-import-field-prerequisites',
      title: 'Approval, import, and field prerequisites',
      status: 'blocked',
      detail: 'Accepted approval row, imported work rows, and admitted field authorization/assignment proof are required before schedule/status mutation authority can exist.',
    },
    {
      id: 'schedule-plan-contract',
      title: 'Schedule plan contract',
      status: 'blocked',
      detail: 'A later packet must define schedule targets, date/status fields, validation rules, idempotency, and rollback posture before schedule writes.',
    },
    {
      id: 'status-transition-contract',
      title: 'Status transition contract',
      status: 'blocked',
      detail: 'A later packet must define permitted task/workpackage/field statuses, transition rules, actor authority, and no-go checks before status writes.',
    },
    {
      id: 'lead-field-review-contract',
      title: 'Lead and field review contract',
      status: 'blocked',
      detail: 'Schedule/status changes require PM and lead review boundaries before controls can be exposed to lead or field routes.',
    },
    {
      id: 'audit-readback-contract',
      title: 'Audit and readback contract',
      status: 'blocked',
      detail: 'A later packet must prove audit linkage, schedule/status readback, idempotent replay, and unchanged downstream counts.',
    },
    {
      id: 'durable-record-production-boundary',
      title: 'Durable record and production boundary',
      status: 'blocked',
      detail: 'Schedule/status controls cannot create durable field records or production tracking rows unless separate packets admit those writes.',
    },
    {
      id: 'hosted-ui-mutation-boundary',
      title: 'Hosted UI mutation boundary',
      status: 'blocked',
      detail: 'No hosted UI control, backend route, deployment, or production mutation is admitted by this local draft.',
    },
  ]
  const controlCounts = approvalDryRunReadinessCounts(controlItems)

  return {
    draft_kind: 'pm_import_candidate_schedule_status_controls_admission_draft',
    draft_version: 'pm_lane_152_local_schedule_status_controls_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    control_draft_summary: {
      ready_count: controlCounts.ready,
      needs_review_count: controlCounts.needsReview,
      blocked_count: controlCounts.blocked,
      summary: approvalDryRunReadinessSummary(controlCounts),
      control_status: 'blocked_until_field_authorization_assignment_and_schedule_status_packet',
    },
    field_authorization_assignment_draft_summary: {
      file_name: fieldAuthorizationAssignmentDraftFileName(candidate),
      ready_count: fieldAuthorizationAssignmentDraft.admission_draft_summary.ready_count,
      needs_review_count: fieldAuthorizationAssignmentDraft.admission_draft_summary.needs_review_count,
      blocked_count: fieldAuthorizationAssignmentDraft.admission_draft_summary.blocked_count,
      summary: fieldAuthorizationAssignmentDraft.admission_draft_summary.summary,
      admission_status: fieldAuthorizationAssignmentDraft.admission_draft_summary.admission_status,
    },
    proposed_schedule_status_packet: {
      packet_kind: 'schedule_status_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment'],
      required_before: ['durable-field-record', 'production-tracking'],
      proposed_routes: {
        schedule_plan_route: 'not_admitted',
        status_update_route: 'not_admitted',
        schedule_readback_route: 'not_admitted',
        status_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization and assignment proof exists',
        'schedule write contract is approved',
        'status transition contract is approved',
        'audit linkage and readback are proved',
        'durable field record and production tracking remain blocked unless separately admitted',
      ],
    },
    control_items: controlItems,
    proposed_packet_sequence: [
      {
        step: 'complete_field_authorization_assignment_gate',
        status: 'blocked',
        detail: 'Complete approval, import, field authorization, and lead/crew assignment gates before schedule/status controls can be considered.',
      },
      {
        step: 'admit_schedule_plan_contract',
        status: 'blocked',
        detail: 'Define schedule targets, date fields, validation, idempotency, replay behavior, rollback posture, and readback.',
      },
      {
        step: 'admit_status_transition_contract',
        status: 'blocked',
        detail: 'Define permitted statuses, actor authority, transition rules, no-go checks, audit fields, and readback.',
      },
      {
        step: 'prove_hosted_readback_without_downstream_writes',
        status: 'blocked',
        detail: 'Prove schedule/status reads without creating durable field records or production tracking rows.',
      },
      {
        step: 'keep_durable_and_production_tracking_blocked',
        status: 'blocked',
        detail: 'Keep durable field records and production tracking blocked until later packets admit those storage contracts.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_control_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      schedule_performed: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...fieldAuthorizationAssignmentDraft.blocked_boundaries,
      'schedule_plan_contract_write',
      'status_transition_contract_write',
      'schedule_status_mutation_route',
      'schedule_status_audit_write',
      'schedule_status_readback_route',
      'hosted_schedule_status_ui_controls',
    ])),
  }
}

function buildDurableFieldRecordDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const scheduleStatusControlsDraft = buildScheduleStatusControlsDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const durableRecordItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'schedule-status-controls-context',
      title: 'Schedule and status controls context',
      status: 'ready',
      detail: `${scheduleStatusControlsDraftFileName(candidate)} defines the no-write prerequisite packet for later durable field record controls.`,
    },
    {
      id: 'approval-import-field-schedule-prerequisites',
      title: 'Approval, import, field, schedule, and status prerequisites',
      status: 'blocked',
      detail: 'Accepted approval row, imported work rows, field authorization/assignment proof, and admitted schedule/status controls are required before durable field record mutation authority can exist.',
    },
    {
      id: 'durable-field-record-storage-contract',
      title: 'Durable field record storage contract',
      status: 'blocked',
      detail: 'A later packet must define daily field record shape, required fields, actor authority, attachment rules, idempotency, rollback posture, and readback before durable field records can be created.',
    },
    {
      id: 'daily-field-record-required-fields',
      title: 'Daily field record required fields',
      status: 'blocked',
      detail: 'A later packet must define the minimum daily record fields for work performed, site conditions, blockers, safety notes, apparatus context, labor context, and PM/lead acknowledgement.',
    },
    {
      id: 'field-evidence-attachment-contract',
      title: 'Field evidence and attachment contract',
      status: 'blocked',
      detail: 'A later packet must define whether field photos, notes, files, device-offline drafts, and retry behavior are admitted before any field evidence storage is created.',
    },
    {
      id: 'pm-lead-review-contract',
      title: 'PM and lead review contract',
      status: 'blocked',
      detail: 'PM and lead review boundaries must be defined before field-submitted records become visible as operational truth.',
    },
    {
      id: 'audit-readback-reconciliation-contract',
      title: 'Audit, readback, and reconciliation contract',
      status: 'blocked',
      detail: 'A later packet must prove durable field record readback, audit linkage, idempotent replay, reconciliation posture, and unchanged downstream business counts.',
    },
    {
      id: 'production-tracking-boundary',
      title: 'Production tracking boundary',
      status: 'blocked',
      detail: 'Durable field record controls cannot create production tracking rows, quantity updates, customer reports, billing exports, or payroll exports unless separate packets admit those outputs.',
    },
    {
      id: 'hosted-ui-mutation-boundary',
      title: 'Hosted UI mutation boundary',
      status: 'blocked',
      detail: 'No hosted UI control, backend route, deployment, or production mutation is admitted by this local draft.',
    },
  ]
  const durableRecordCounts = approvalDryRunReadinessCounts(durableRecordItems)

  return {
    draft_kind: 'pm_import_candidate_durable_field_record_admission_draft',
    draft_version: 'pm_lane_153_local_durable_field_record_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    durable_record_draft_summary: {
      ready_count: durableRecordCounts.ready,
      needs_review_count: durableRecordCounts.needsReview,
      blocked_count: durableRecordCounts.blocked,
      summary: approvalDryRunReadinessSummary(durableRecordCounts),
      durable_record_status: 'blocked_until_schedule_status_and_durable_field_record_packet',
    },
    schedule_status_controls_draft_summary: {
      file_name: scheduleStatusControlsDraftFileName(candidate),
      ready_count: scheduleStatusControlsDraft.control_draft_summary.ready_count,
      needs_review_count: scheduleStatusControlsDraft.control_draft_summary.needs_review_count,
      blocked_count: scheduleStatusControlsDraft.control_draft_summary.blocked_count,
      summary: scheduleStatusControlsDraft.control_draft_summary.summary,
      control_status: scheduleStatusControlsDraft.control_draft_summary.control_status,
    },
    proposed_durable_field_record_packet: {
      packet_kind: 'durable_field_record_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls'],
      required_before: ['production-tracking', 'customer-or-billing-reporting'],
      proposed_routes: {
        field_record_create_route: 'not_admitted',
        field_record_update_route: 'not_admitted',
        field_record_readback_route: 'not_admitted',
        field_record_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization and assignment proof exists',
        'schedule/status controls proof exists',
        'durable field record storage contract is approved',
        'daily field record required fields and evidence rules are approved',
        'PM/lead review, audit, readback, and reconciliation are proved',
        'production tracking, customer reporting, billing, and payroll outputs remain blocked unless separately admitted',
      ],
    },
    durable_record_items: durableRecordItems,
    proposed_packet_sequence: [
      {
        step: 'complete_schedule_status_controls_gate',
        status: 'blocked',
        detail: 'Complete approval, import, field authorization, assignment, schedule, and status controls before durable field record or production tracking writes can be considered.',
      },
      {
        step: 'admit_durable_field_record_contract',
        status: 'blocked',
        detail: 'Define daily record shape, required fields, actor authority, attachments, idempotency, retry behavior, rollback posture, and readback.',
      },
      {
        step: 'admit_field_evidence_and_review_contract',
        status: 'blocked',
        detail: 'Define field evidence, offline draft, PM/lead review, audit, and reconciliation rules before daily records become operational truth.',
      },
      {
        step: 'prove_hosted_readback_without_production_tracking',
        status: 'blocked',
        detail: 'Prove durable field record reads and audit history without creating production tracking rows, customer reports, billing exports, payroll exports, or customer-facing completion evidence.',
      },
      {
        step: 'keep_production_customer_billing_and_payroll_outputs_blocked',
        status: 'blocked',
        detail: 'Keep production tracking, customer reporting, billing, payroll, and external delivery outputs blocked until later packets admit those surfaces.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_durable_record_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      customer_report_created: false,
      billing_export_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...scheduleStatusControlsDraft.blocked_boundaries,
      'durable_field_record_contract_write',
      'field_daily_record_write',
      'field_evidence_attachment_write',
      'durable_field_record_mutation_route',
      'durable_field_record_audit_write',
      'durable_field_record_readback_route',
      'hosted_durable_field_record_ui_controls',
      'production_tracking_contract_write',
      'production_quantity_tracking_write',
      'customer_reporting_export',
      'billing_or_payroll_export',
    ])),
  }
}

function buildProductionTrackingDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const durableFieldRecordDraft = buildDurableFieldRecordDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const productionItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'durable-field-record-context',
      title: 'Durable field record context',
      status: 'ready',
      detail: `${durableFieldRecordDraftFileName(candidate)} defines the no-write prerequisite packet for later production tracking controls.`,
    },
    {
      id: 'approval-import-field-schedule-durable-prerequisites',
      title: 'Approval, import, field, schedule, and durable record prerequisites',
      status: 'blocked',
      detail: 'Accepted approval row, imported work rows, field authorization/assignment proof, admitted schedule/status controls, and admitted durable field record proof are required before production tracking mutation authority can exist.',
    },
    {
      id: 'production-quantity-contract',
      title: 'Production quantity contract',
      status: 'blocked',
      detail: 'A later packet must define quantity fields, units, validation rules, idempotency, rollback posture, and readback before production quantity rows can be created.',
    },
    {
      id: 'labor-apparatus-progress-contract',
      title: 'Labor, apparatus, and progress contract',
      status: 'blocked',
      detail: 'A later packet must define labor, apparatus, progress, exception, and variance tracking fields before production progress becomes operational truth.',
    },
    {
      id: 'pm-lead-production-review-contract',
      title: 'PM and lead production review contract',
      status: 'blocked',
      detail: 'PM and lead review boundaries must be defined before production updates can drive schedule, reporting, billing, or customer-facing completion posture.',
    },
    {
      id: 'audit-readback-reconciliation-contract',
      title: 'Audit, readback, and reconciliation contract',
      status: 'blocked',
      detail: 'A later packet must prove production tracking readback, history, audit linkage, idempotent replay, and reconciliation against durable field records.',
    },
    {
      id: 'customer-billing-payroll-boundary',
      title: 'Customer, billing, and payroll boundary',
      status: 'blocked',
      detail: 'Production tracking controls cannot create customer reports, billing exports, payroll exports, or customer-facing completion evidence unless separate packets admit those outputs.',
    },
    {
      id: 'hosted-ui-mutation-boundary',
      title: 'Hosted UI mutation boundary',
      status: 'blocked',
      detail: 'No hosted UI control, backend route, deployment, or production mutation is admitted by this local draft.',
    },
  ]
  const productionCounts = approvalDryRunReadinessCounts(productionItems)

  return {
    draft_kind: 'pm_import_candidate_production_tracking_admission_draft',
    draft_version: 'pm_lane_154_local_production_tracking_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    production_tracking_draft_summary: {
      ready_count: productionCounts.ready,
      needs_review_count: productionCounts.needsReview,
      blocked_count: productionCounts.blocked,
      summary: approvalDryRunReadinessSummary(productionCounts),
      production_tracking_status: 'blocked_until_durable_field_record_and_production_tracking_packet',
    },
    durable_field_record_draft_summary: {
      file_name: durableFieldRecordDraftFileName(candidate),
      ready_count: durableFieldRecordDraft.durable_record_draft_summary.ready_count,
      needs_review_count: durableFieldRecordDraft.durable_record_draft_summary.needs_review_count,
      blocked_count: durableFieldRecordDraft.durable_record_draft_summary.blocked_count,
      summary: durableFieldRecordDraft.durable_record_draft_summary.summary,
      durable_record_status: durableFieldRecordDraft.durable_record_draft_summary.durable_record_status,
    },
    proposed_production_tracking_packet: {
      packet_kind: 'production_tracking_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record'],
      required_before: ['customer-or-billing-reporting', 'payroll-export', 'customer-facing-completion-evidence'],
      proposed_routes: {
        production_quantity_update_route: 'not_admitted',
        production_labor_update_route: 'not_admitted',
        production_apparatus_update_route: 'not_admitted',
        production_tracking_readback_route: 'not_admitted',
        production_tracking_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization and assignment proof exists',
        'schedule/status controls proof exists',
        'durable field record proof exists',
        'production quantity, labor, apparatus, and progress contracts are approved',
        'PM/lead production review, audit, readback, and reconciliation are proved',
        'customer reporting, billing, payroll, and customer-facing completion evidence remain blocked unless separately admitted',
      ],
    },
    production_items: productionItems,
    proposed_packet_sequence: [
      {
        step: 'complete_durable_field_record_gate',
        status: 'blocked',
        detail: 'Complete approval, import, field authorization, assignment, schedule, status, and durable field record gates before production tracking writes can be considered.',
      },
      {
        step: 'admit_production_quantity_contract',
        status: 'blocked',
        detail: 'Define quantity fields, units, validation, actor authority, idempotency, rollback posture, and readback.',
      },
      {
        step: 'admit_labor_apparatus_progress_contract',
        status: 'blocked',
        detail: 'Define labor, apparatus, progress, exception, variance, PM/lead review, audit, and reconciliation rules.',
      },
      {
        step: 'prove_hosted_readback_without_customer_reporting',
        status: 'blocked',
        detail: 'Prove production tracking reads and audit history without creating customer reports, billing exports, payroll exports, or customer-facing completion evidence.',
      },
      {
        step: 'keep_customer_billing_payroll_and_completion_outputs_blocked',
        status: 'blocked',
        detail: 'Keep customer reporting, billing, payroll, and external completion evidence outputs blocked until later packets admit those surfaces.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_production_tracking_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_report_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...durableFieldRecordDraft.blocked_boundaries,
      'production_tracking_mutation_route',
      'production_tracking_audit_write',
      'production_tracking_readback_route',
      'hosted_production_tracking_ui_controls',
      'production_labor_tracking_write',
      'production_apparatus_progress_write',
      'customer_completion_evidence_export',
      'payroll_export',
    ])),
  }
}

function buildCustomerReportingDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const productionTrackingDraft = buildProductionTrackingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const reportingItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'production-tracking-context',
      title: 'Production tracking context',
      status: 'ready',
      detail: `${productionTrackingDraftFileName(candidate)} defines the no-write prerequisite packet for later customer reporting and completion evidence controls.`,
    },
    {
      id: 'approval-import-field-production-prerequisites',
      title: 'Approval, import, field, and production prerequisites',
      status: 'blocked',
      detail: 'Accepted approval row, imported work rows, field authorization/assignment proof, schedule/status proof, durable field record proof, and production tracking proof are required before customer reporting authority can exist.',
    },
    {
      id: 'customer-report-contract',
      title: 'Customer report contract',
      status: 'blocked',
      detail: 'A later packet must define customer report fields, included production evidence, audience, review state, idempotency, rollback posture, and readback before reports can be created.',
    },
    {
      id: 'completion-evidence-contract',
      title: 'Completion evidence contract',
      status: 'blocked',
      detail: 'A later packet must define customer-facing completion evidence, supporting field records, photo/file inclusion, omissions, and exception labeling before completion evidence can be generated.',
    },
    {
      id: 'pm-customer-review-contract',
      title: 'PM and customer review contract',
      status: 'blocked',
      detail: 'PM review, customer review status, release rules, and revision behavior must be defined before any report becomes customer-facing truth.',
    },
    {
      id: 'audit-readback-reconciliation-contract',
      title: 'Audit, readback, and reconciliation contract',
      status: 'blocked',
      detail: 'A later packet must prove customer report readback, history, audit linkage, idempotent replay, and reconciliation against production tracking evidence.',
    },
    {
      id: 'billing-payroll-boundary',
      title: 'Billing and payroll boundary',
      status: 'blocked',
      detail: 'Customer reporting controls cannot create invoices, billing exports, payroll exports, or accounting/payroll records unless separate packets admit those outputs.',
    },
    {
      id: 'hosted-ui-mutation-boundary',
      title: 'Hosted UI mutation boundary',
      status: 'blocked',
      detail: 'No hosted UI control, backend route, deployment, or production mutation is admitted by this local draft.',
    },
  ]
  const reportingCounts = approvalDryRunReadinessCounts(reportingItems)

  return {
    draft_kind: 'pm_import_candidate_customer_reporting_admission_draft',
    draft_version: 'pm_lane_155_local_customer_reporting_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    customer_reporting_draft_summary: {
      ready_count: reportingCounts.ready,
      needs_review_count: reportingCounts.needsReview,
      blocked_count: reportingCounts.blocked,
      summary: approvalDryRunReadinessSummary(reportingCounts),
      customer_reporting_status: 'blocked_until_production_tracking_and_customer_reporting_packet',
    },
    production_tracking_draft_summary: {
      file_name: productionTrackingDraftFileName(candidate),
      ready_count: productionTrackingDraft.production_tracking_draft_summary.ready_count,
      needs_review_count: productionTrackingDraft.production_tracking_draft_summary.needs_review_count,
      blocked_count: productionTrackingDraft.production_tracking_draft_summary.blocked_count,
      summary: productionTrackingDraft.production_tracking_draft_summary.summary,
      production_tracking_status: productionTrackingDraft.production_tracking_draft_summary.production_tracking_status,
    },
    proposed_customer_reporting_packet: {
      packet_kind: 'customer_reporting_and_completion_evidence_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record', 'production-tracking'],
      required_before: ['billing-export', 'payroll-export', 'accounting-records'],
      proposed_routes: {
        customer_report_create_route: 'not_admitted',
        completion_evidence_create_route: 'not_admitted',
        customer_report_readback_route: 'not_admitted',
        customer_report_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization and assignment proof exists',
        'schedule/status controls proof exists',
        'durable field record proof exists',
        'production tracking proof exists',
        'customer report, completion evidence, PM/customer review, audit, and readback contracts are approved',
        'billing, payroll, and accounting outputs remain blocked unless separately admitted',
      ],
    },
    reporting_items: reportingItems,
    proposed_packet_sequence: [
      {
        step: 'complete_production_tracking_gate',
        status: 'blocked',
        detail: 'Complete approval, import, field authorization, assignment, schedule, status, durable field record, and production tracking gates before customer reporting can be considered.',
      },
      {
        step: 'admit_customer_report_contract',
        status: 'blocked',
        detail: 'Define report fields, evidence inclusion, audience, review state, revision behavior, idempotency, rollback posture, and readback.',
      },
      {
        step: 'admit_completion_evidence_contract',
        status: 'blocked',
        detail: 'Define completion evidence sources, included and excluded field evidence, exception labeling, PM/customer release rules, audit, and reconciliation.',
      },
      {
        step: 'prove_hosted_readback_without_billing_or_payroll',
        status: 'blocked',
        detail: 'Prove customer report reads and audit history without creating invoices, billing exports, payroll exports, or accounting/payroll records.',
      },
      {
        step: 'keep_billing_payroll_and_accounting_outputs_blocked',
        status: 'blocked',
        detail: 'Keep billing, payroll, accounting, and external financial outputs blocked until later packets admit those surfaces.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_customer_reporting_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_reporting_route_created: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_delivery_performed: false,
      billing_export_created: false,
      payroll_export_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...productionTrackingDraft.blocked_boundaries,
      'customer_reporting_contract_write',
      'customer_report_write',
      'customer_completion_evidence_write',
      'customer_reporting_mutation_route',
      'customer_reporting_audit_write',
      'customer_reporting_readback_route',
      'hosted_customer_reporting_ui_controls',
      'billing_export_contract_write',
      'payroll_export_contract_write',
      'accounting_record_write',
    ])),
  }
}

function buildFinancialHandoffDraftExport(
  packet: IntakeWorkbenchPacket,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const customerReportingDraft = buildCustomerReportingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const financialItems: ApprovalDryRunReadinessItem[] = [
    {
      id: 'customer-reporting-context',
      title: 'Customer reporting context',
      status: 'ready',
      detail: `${customerReportingDraftFileName(candidate)} defines the no-write prerequisite packet for later billing, payroll, invoice, and accounting boundaries.`,
    },
    {
      id: 'approval-import-field-production-customer-prerequisites',
      title: 'Approval, field, production, and customer prerequisites',
      status: 'blocked',
      detail: 'Accepted approval row, imported work rows, field authorization/assignment proof, schedule/status proof, durable field record proof, production tracking proof, and customer reporting proof are required before financial handoff authority can exist.',
    },
    {
      id: 'billing-export-contract',
      title: 'Billing export contract',
      status: 'blocked',
      detail: 'A later packet must define billable scope, included customer evidence, quantities, rates, exclusions, review state, idempotency, rollback posture, and readback before any billing export can exist.',
    },
    {
      id: 'payroll-export-contract',
      title: 'Payroll export contract',
      status: 'blocked',
      detail: 'A later packet must define approved labor source, technician mapping, time boundaries, exceptions, supervisor review, and payroll-system handoff before payroll export can exist.',
    },
    {
      id: 'invoice-accounting-boundary',
      title: 'Invoice and accounting boundary',
      status: 'blocked',
      detail: 'Invoices, accounting records, cost postings, and external finance-system sync remain outside the PM workbench until separate finance authority is admitted.',
    },
    {
      id: 'labor-reconciliation-boundary',
      title: 'Labor reconciliation boundary',
      status: 'blocked',
      detail: 'Production labor, field records, customer report evidence, and payroll source rows must be reconciled before any payroll or cost export is trusted.',
    },
    {
      id: 'customer-release-boundary',
      title: 'Customer release boundary',
      status: 'blocked',
      detail: 'Customer-facing report release and completion evidence acceptance must be separated from billing, payroll, and accounting output creation.',
    },
    {
      id: 'audit-readback-reconciliation-contract',
      title: 'Audit, readback, and reconciliation contract',
      status: 'blocked',
      detail: 'A later packet must prove financial handoff readback, audit lineage, idempotent replay, exception handling, and reconciliation against customer reporting evidence.',
    },
    {
      id: 'hosted-finance-mutation-boundary',
      title: 'Hosted finance mutation boundary',
      status: 'blocked',
      detail: 'No hosted UI control, backend route, deployment, finance integration, or production mutation is admitted by this local draft.',
    },
  ]
  const financialCounts = approvalDryRunReadinessCounts(financialItems)

  return {
    draft_kind: 'pm_import_candidate_financial_handoff_admission_draft',
    draft_version: 'pm_lane_156_local_financial_handoff_admission_draft_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    financial_handoff_draft_summary: {
      ready_count: financialCounts.ready,
      needs_review_count: financialCounts.needsReview,
      blocked_count: financialCounts.blocked,
      summary: approvalDryRunReadinessSummary(financialCounts),
      financial_handoff_status: 'blocked_until_customer_reporting_and_financial_handoff_packet',
    },
    customer_reporting_draft_summary: {
      file_name: customerReportingDraftFileName(candidate),
      ready_count: customerReportingDraft.customer_reporting_draft_summary.ready_count,
      needs_review_count: customerReportingDraft.customer_reporting_draft_summary.needs_review_count,
      blocked_count: customerReportingDraft.customer_reporting_draft_summary.blocked_count,
      summary: customerReportingDraft.customer_reporting_draft_summary.summary,
      customer_reporting_status: customerReportingDraft.customer_reporting_draft_summary.customer_reporting_status,
    },
    proposed_financial_handoff_packet: {
      packet_kind: 'billing_payroll_accounting_boundary_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record', 'production-tracking', 'customer-reporting-and-completion-evidence'],
      required_before: ['billing-export', 'payroll-export', 'invoice-creation', 'accounting-posting', 'external-finance-system-sync'],
      proposed_routes: {
        billing_export_create_route: 'not_admitted',
        payroll_export_create_route: 'not_admitted',
        invoice_record_create_route: 'not_admitted',
        accounting_record_create_route: 'not_admitted',
        financial_handoff_readback_route: 'not_admitted',
        financial_handoff_history_route: 'not_admitted',
        pm_workfront_route: '/pm-review/workfront',
      },
      minimum_proof: [
        'accepted approval row exists',
        'imported project/workpackage/task/apparatus rows exist',
        'field authorization and assignment proof exists',
        'schedule/status controls proof exists',
        'durable field record proof exists',
        'production tracking proof exists',
        'customer report and completion evidence proof exists',
        'billing export, payroll export, invoice/accounting, audit, and readback contracts are approved',
        'external finance system, payroll processing, and accounting posting remain blocked unless separately admitted',
      ],
    },
    financial_handoff_items: financialItems,
    proposed_packet_sequence: [
      {
        step: 'complete_customer_reporting_gate',
        status: 'blocked',
        detail: 'Complete approval, import, field authorization, assignment, schedule, status, durable field record, production tracking, customer report, and completion evidence gates before financial handoff can be considered.',
      },
      {
        step: 'admit_billing_export_contract',
        status: 'blocked',
        detail: 'Define billable scope, quantities, customer evidence, exclusions, review state, idempotency, rollback posture, audit, and readback.',
      },
      {
        step: 'admit_payroll_export_contract',
        status: 'blocked',
        detail: 'Define labor source, technician mapping, time boundaries, exceptions, supervisor review, payroll handoff, audit, and reconciliation.',
      },
      {
        step: 'admit_invoice_accounting_boundary_contract',
        status: 'blocked',
        detail: 'Define what remains inside PM evidence versus what belongs to invoice creation, accounting posting, or external finance-system sync.',
      },
      {
        step: 'prove_readback_without_external_finance_sync',
        status: 'blocked',
        detail: 'Prove financial handoff readback and audit history without creating invoices, payroll records, accounting records, or finance-system sync payloads.',
      },
      {
        step: 'keep_external_finance_and_payroll_processing_blocked',
        status: 'blocked',
        detail: 'Keep invoice creation, payroll processing, accounting posting, and external finance-system outputs blocked until later packets admit those surfaces.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_financial_handoff_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_reporting_route_created: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_delivery_performed: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...customerReportingDraft.blocked_boundaries,
      'financial_handoff_contract_write',
      'financial_handoff_mutation_route',
      'financial_handoff_audit_write',
      'financial_handoff_readback_route',
      'billing_export_write',
      'payroll_export_write',
      'invoice_record_write',
      'payroll_record_write',
      'accounting_record_write',
      'labor_reconciliation_write',
      'customer_billing_delivery',
      'finance_system_integration',
      'hosted_financial_handoff_ui_controls',
    ])),
  }
}

function buildPilotLaunchBinderExport(
  packet: IntakeWorkbenchPacket,
  approvalDryRunReadiness: ApprovalDryRunReadinessItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const project = candidate.project || {}
  const summary = candidate.summary || {}
  const approvalLiveGatePreflight = buildApprovalLiveGatePreflightExport(packet, approvalDryRunReadiness, notAllowed, futureRoute, reviewChecks, approvalDraft)
  const fieldStartPreflight = buildFieldStartPreflightExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const fieldExecutionGateDesign = buildFieldExecutionGateDesignExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const leadFieldAssignmentDraft = buildLeadFieldAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const fieldAuthorizationAssignmentDraft = buildFieldAuthorizationAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const scheduleStatusControlsDraft = buildScheduleStatusControlsDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const durableFieldRecordDraft = buildDurableFieldRecordDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const productionTrackingDraft = buildProductionTrackingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const customerReportingDraft = buildCustomerReportingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const financialHandoffDraft = buildFinancialHandoffDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const sourceArtifacts = [
    {
      artifact_id: 'approval-live-gate-preflight',
      file_name: approvalLiveGatePreflightFileName(candidate),
      artifact_kind: approvalLiveGatePreflight.preflight_kind,
      local_status: 'ready',
      authority_status: approvalLiveGatePreflight.preflight_summary.live_gate_status,
      summary: approvalLiveGatePreflight.preflight_summary.summary,
    },
    {
      artifact_id: 'field-start-preflight',
      file_name: fieldStartPreflightFileName(candidate),
      artifact_kind: fieldStartPreflight.preflight_kind,
      local_status: 'ready',
      authority_status: fieldStartPreflight.preflight_summary.field_start_status,
      summary: fieldStartPreflight.preflight_summary.summary,
    },
    {
      artifact_id: 'field-execution-gate-design',
      file_name: fieldExecutionGateDesignFileName(candidate),
      artifact_kind: fieldExecutionGateDesign.gate_kind,
      local_status: 'ready',
      authority_status: fieldExecutionGateDesign.gate_summary.execution_gate_status,
      summary: fieldExecutionGateDesign.gate_summary.summary,
    },
    {
      artifact_id: 'lead-field-assignment-draft',
      file_name: leadFieldAssignmentDraftFileName(candidate),
      artifact_kind: leadFieldAssignmentDraft.draft_kind,
      local_status: 'ready',
      authority_status: leadFieldAssignmentDraft.draft_summary.assignment_status,
      summary: leadFieldAssignmentDraft.draft_summary.summary,
    },
    {
      artifact_id: 'field-authorization-assignment-draft',
      file_name: fieldAuthorizationAssignmentDraftFileName(candidate),
      artifact_kind: fieldAuthorizationAssignmentDraft.draft_kind,
      local_status: 'ready',
      authority_status: fieldAuthorizationAssignmentDraft.admission_draft_summary.admission_status,
      summary: fieldAuthorizationAssignmentDraft.admission_draft_summary.summary,
    },
    {
      artifact_id: 'schedule-status-controls-draft',
      file_name: scheduleStatusControlsDraftFileName(candidate),
      artifact_kind: scheduleStatusControlsDraft.draft_kind,
      local_status: 'ready',
      authority_status: scheduleStatusControlsDraft.control_draft_summary.control_status,
      summary: scheduleStatusControlsDraft.control_draft_summary.summary,
    },
    {
      artifact_id: 'durable-field-record-draft',
      file_name: durableFieldRecordDraftFileName(candidate),
      artifact_kind: durableFieldRecordDraft.draft_kind,
      local_status: 'ready',
      authority_status: durableFieldRecordDraft.durable_record_draft_summary.durable_record_status,
      summary: durableFieldRecordDraft.durable_record_draft_summary.summary,
    },
    {
      artifact_id: 'production-tracking-draft',
      file_name: productionTrackingDraftFileName(candidate),
      artifact_kind: productionTrackingDraft.draft_kind,
      local_status: 'ready',
      authority_status: productionTrackingDraft.production_tracking_draft_summary.production_tracking_status,
      summary: productionTrackingDraft.production_tracking_draft_summary.summary,
    },
    {
      artifact_id: 'customer-reporting-draft',
      file_name: customerReportingDraftFileName(candidate),
      artifact_kind: customerReportingDraft.draft_kind,
      local_status: 'ready',
      authority_status: customerReportingDraft.customer_reporting_draft_summary.customer_reporting_status,
      summary: customerReportingDraft.customer_reporting_draft_summary.summary,
    },
    {
      artifact_id: 'financial-handoff-draft',
      file_name: financialHandoffDraftFileName(candidate),
      artifact_kind: financialHandoffDraft.draft_kind,
      local_status: 'ready',
      authority_status: financialHandoffDraft.financial_handoff_draft_summary.financial_handoff_status,
      summary: financialHandoffDraft.financial_handoff_draft_summary.summary,
    },
  ]
  const binderItems: ApprovalDryRunReadinessItem[] = [
    ...sourceArtifacts.map((artifact) => ({
      id: artifact.artifact_id,
      title: artifact.artifact_id.split('-').map(formatLabel).join(' '),
      status: 'ready' as ApprovalDryRunReadinessStatus,
      detail: `${artifact.file_name} is available as local review context. Its authority status remains ${artifact.authority_status}.`,
    })),
    {
      id: 'live-approval-row-authority',
      title: 'Live approval row authority',
      status: 'blocked',
      detail: 'The PM Lane 142 exact live-write phrase is still required before any browser approval POST or first approval row can exist.',
    },
    {
      id: 'project-import-authority',
      title: 'Project import authority',
      status: 'blocked',
      detail: 'Project, workpackage, task, and apparatus import writes remain blocked until a later import packet is admitted after approval-row proof.',
    },
    {
      id: 'field-production-customer-finance-authority',
      title: 'Field, production, customer, and finance authority',
      status: 'blocked',
      detail: 'Field authorization, assignment, schedule/status, durable records, production tracking, customer reporting, billing, payroll, invoices, accounting, and external finance sync remain blocked.',
    },
  ]
  const binderCounts = approvalDryRunReadinessCounts(binderItems)

  return {
    binder_kind: 'pm_import_candidate_pilot_launch_binder',
    binder_version: 'pm_lane_157_local_pilot_launch_binder_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: {
      candidate_id: candidate.candidate_id || null,
      candidate_version: candidate.candidate_version || null,
      project_name: project.name || null,
      source_fingerprint: candidate.source_freshness?.aggregate_fingerprint || null,
    },
    field_shape: {
      workpackage_count: summary.workpackage_count ?? null,
      task_count: summary.task_count ?? null,
      apparatus_candidate_count: summary.apparatus_candidate_count ?? null,
      crew_count: summary.crew_count ?? null,
      equipment_inventory_count: summary.equipment_inventory_count ?? null,
    },
    pilot_launch_binder_summary: {
      ready_count: binderCounts.ready,
      needs_review_count: binderCounts.needsReview,
      blocked_count: binderCounts.blocked,
      summary: approvalDryRunReadinessSummary(binderCounts),
      launch_status: 'local_binder_ready_live_writes_blocked',
    },
    source_artifact_manifest: sourceArtifacts,
    source_artifact_summaries: {
      approval_live_gate_preflight: approvalLiveGatePreflight.preflight_summary,
      field_start_preflight: fieldStartPreflight.preflight_summary,
      field_execution_gate_design: fieldExecutionGateDesign.gate_summary,
      lead_field_assignment_draft: leadFieldAssignmentDraft.draft_summary,
      field_authorization_assignment_draft: fieldAuthorizationAssignmentDraft.admission_draft_summary,
      schedule_status_controls_draft: scheduleStatusControlsDraft.control_draft_summary,
      durable_field_record_draft: durableFieldRecordDraft.durable_record_draft_summary,
      production_tracking_draft: productionTrackingDraft.production_tracking_draft_summary,
      customer_reporting_draft: customerReportingDraft.customer_reporting_draft_summary,
      financial_handoff_draft: financialHandoffDraft.financial_handoff_draft_summary,
    },
    binder_items: binderItems,
    recommended_review_sequence: [
      'confirm approval live-gate preflight remains blocked without exact PM Lane 142 phrase',
      'review field-start context with lead/customer before mobilization',
      'review field execution gate design before any write-path packet',
      'review lead field assignment draft before selecting or assigning a lead',
      'review field authorization and assignment draft before authorizing field work',
      'review schedule/status controls draft before schedule or status mutation',
      'review durable field record draft before daily field record persistence',
      'review production tracking draft before quantity, labor, apparatus, or progress writes',
      'review customer reporting draft before customer report or completion evidence writes',
      'review financial handoff draft before billing, payroll, invoice, accounting, or external finance-system outputs',
    ],
    next_packet_options: [
      {
        option: 'approval-first-row-execution-gate',
        status: 'blocked_until_exact_pm_lane_142_phrase',
        detail: 'Use the binder as review context only unless Jason provides the exact PM Lane 142 live-write admission phrase.',
      },
      {
        option: 'project-import-mutation-design',
        status: 'blocked_until_approval_row_proof',
        detail: 'Do not design or run project import mutation until approval-row proof is accepted.',
      },
      {
        option: 'field-execution-write-paths',
        status: 'blocked_until_import_and_field_authorization_packets',
        detail: 'Do not admit field, production, customer, billing, payroll, invoice, accounting, or finance-system write paths from this binder.',
      },
    ],
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_binder_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...approvalLiveGatePreflight.blocked_boundaries,
      ...financialHandoffDraft.blocked_boundaries,
      'pilot_launch_binder_server_write',
      'browser_batch_submit',
      'project_launch_write_path',
      'executor_autonomous_business_state',
    ])),
  }
}

function buildPilotLaunchDailyBriefExport(
  packet: IntakeWorkbenchPacket,
  approvalDryRunReadiness: ApprovalDryRunReadinessItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const binder = buildPilotLaunchBinderExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const dailyBriefItems = [
    {
      id: 'approval-live-gate',
      title: 'Approval live gate',
      status: 'blocked',
      detail: 'Do not send a browser approval POST or create the first approval row until the exact PM Lane 142 phrase is admitted.',
    },
    {
      id: 'field-start-context-review',
      title: 'Field start context review',
      status: 'review_only',
      detail: `${fieldStartPreflightFileName(candidate)} is available for PM, lead, and customer conversation context only.`,
    },
    {
      id: 'lead-and-crew-readiness-review',
      title: 'Lead and crew readiness review',
      status: 'review_only',
      detail: 'Use the lead field assignment draft and field authorization assignment draft as discussion context without creating lead, crew, or field work records.',
    },
    {
      id: 'schedule-status-review',
      title: 'Schedule and status review',
      status: 'blocked',
      detail: 'Schedule and status changes remain blocked until a later packet admits storage, audit, readback, and rollback proof.',
    },
    {
      id: 'daily-field-record-review',
      title: 'Daily field record review',
      status: 'blocked',
      detail: 'Durable daily field records remain blocked until a later packet admits the record contract and readback checks.',
    },
    {
      id: 'production-customer-review',
      title: 'Production and customer review',
      status: 'blocked',
      detail: 'Production tracking, customer reports, and completion evidence remain blocked until separate packets admit those surfaces.',
    },
    {
      id: 'financial-handoff-review',
      title: 'Financial handoff review',
      status: 'blocked',
      detail: 'Billing, payroll, invoice, accounting, labor reconciliation, customer billing delivery, and external finance-system sync remain blocked.',
    },
  ]
  const reviewOnlyCount = dailyBriefItems.filter((item) => item.status === 'review_only').length
  const blockedCount = dailyBriefItems.filter((item) => item.status === 'blocked').length

  return {
    brief_kind: 'pm_import_candidate_pilot_launch_daily_brief',
    brief_version: 'pm_lane_159_local_pilot_launch_daily_brief_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: binder.candidate_identity,
    field_shape: binder.field_shape,
    daily_brief_summary: {
      review_only_count: reviewOnlyCount,
      blocked_count: blockedCount,
      summary: `${reviewOnlyCount} review-only, ${blockedCount} blocked`,
      brief_status: 'local_daily_brief_available_live_writes_blocked',
    },
    source_artifact_manifest: binder.source_artifact_manifest,
    source_artifact_summaries: binder.source_artifact_summaries,
    today_review_sequence: [
      'read the approval live-gate preflight before discussing any approval-row action',
      'use the field-start preflight for PM, lead, and customer conversation context',
      'review lead, field authorization, schedule/status, durable record, and production drafts before field reliance',
      'review customer reporting and financial handoff drafts before customer-facing or finance-facing outputs',
      'keep every write path blocked unless a later packet explicitly admits that exact route and proof set',
    ],
    daily_brief_items: dailyBriefItems,
    blocked_next_packet_options: binder.next_packet_options,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_daily_brief_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...binder.blocked_boundaries,
      'pilot_launch_daily_brief_server_write',
      'daily_brief_business_state_write',
      'field_daily_plan_write',
    ])),
  }
}

function buildPilotLaunchStandupCardExport(
  packet: IntakeWorkbenchPacket,
  approvalDryRunReadiness: ApprovalDryRunReadinessItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const dailyBrief = buildPilotLaunchDailyBriefExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const roleCards = [
    {
      role_id: 'pm',
      role_title: 'Project manager',
      status: 'lead_conversation_only',
      say_now: 'Use the daily brief to confirm what is review-only, what is blocked, and what proof is still required before any live approval, import, field, production, customer, or finance write exists.',
      ask_now: [
        'What must be clarified before the Temp Power start conversation?',
        'Which open item would block mobilization discussion if it stays unanswered?',
      ],
      do_not_cross: ['do_not_approve_candidate', 'do_not_import_project_rows', 'do_not_authorize_field_work'],
    },
    {
      role_id: 'field_lead',
      role_title: 'Field lead',
      status: 'context_review_only',
      say_now: 'Review field-start, lead assignment, field authorization, schedule/status, durable record, and production tracking drafts as context only.',
      ask_now: [
        'What site access, safety, crew, material, or apparatus question needs PM/customer follow-up?',
        'What would the lead need before any later authorized field start?',
      ],
      do_not_cross: ['do_not_assign_lead', 'do_not_assign_crew', 'do_not_change_schedule_or_status'],
    },
    {
      role_id: 'customer_or_site_contact',
      role_title: 'Customer or site contact',
      status: 'expectation_alignment_only',
      say_now: 'Confirm customer-facing expectations, constraints, and completion-evidence questions without creating a customer report or customer commitment record.',
      ask_now: [
        'What customer/site constraint should be recorded as an open question?',
        'What completion evidence will need later agreement before customer reporting exists?',
      ],
      do_not_cross: ['do_not_create_customer_report', 'do_not_create_completion_evidence', 'do_not_create_customer_commitment'],
    },
    {
      role_id: 'executor_ai_relay',
      role_title: 'Executor and AI relay',
      status: 'evidence_collection_only',
      say_now: 'Capture returned evidence and packet recommendations for VS Code Codex review without admitting implementation or live-write authority.',
      ask_now: [
        'Has Desktop Codex returned the PM Lane 158 financial handoff admission design closeout?',
        'Does the next packet need VS Code implementation, Desktop Codex scout work, or explicit PM Lane 142 live-write admission?',
      ],
      do_not_cross: ['do_not_stage_executor_output_without_review', 'do_not_mutate_hosted_services', 'do_not_sync_external_finance_systems'],
    },
  ]
  const noGoChecks = [
    {
      check_id: 'approval-live-write-not-admitted',
      status: 'no_go',
      detail: 'No browser approval POST or first approval row may be created without the exact PM Lane 142 admission phrase.',
    },
    {
      check_id: 'project-import-not-admitted',
      status: 'no_go',
      detail: 'No project, workpackage, task, or apparatus import mutation may be created from this standup card.',
    },
    {
      check_id: 'field-direction-not-admitted',
      status: 'no_go',
      detail: 'No field authorization, lead assignment, crew assignment, schedule/status update, or daily field record may be created from this standup card.',
    },
    {
      check_id: 'customer-finance-output-not-admitted',
      status: 'no_go',
      detail: 'No customer report, completion evidence, billing export, payroll export, invoice, accounting record, or external finance-system sync may be created from this standup card.',
    },
  ]
  const capturePrompts = [
    {
      prompt_id: 'open-decisions',
      label: 'Open decisions to bring back to PM review',
      capture_mode: 'local_prompt_only',
      guidance: 'Capture unresolved PM, lead, customer, or executor questions outside the app; this export does not persist them.',
    },
    {
      prompt_id: 'field-start-blockers',
      label: 'Field-start blockers or dependencies',
      capture_mode: 'local_prompt_only',
      guidance: 'List site, safety, access, material, apparatus, crew, schedule, or customer blockers without creating a field record.',
    },
    {
      prompt_id: 'next-packet-selection',
      label: 'Next packet recommendation',
      capture_mode: 'local_prompt_only',
      guidance: 'Choose whether the next bounded packet should wait for PM Lane 158 closeout, stay local-only, or request explicit PM Lane 142 live-write admission.',
    },
  ]

  return {
    standup_card_kind: 'pm_import_candidate_pilot_launch_standup_card',
    standup_card_version: 'pm_lane_160_local_pilot_launch_standup_card_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: dailyBrief.candidate_identity,
    field_shape: dailyBrief.field_shape,
    source_daily_brief: {
      file_name: pilotLaunchDailyBriefFileName(candidate),
      brief_kind: dailyBrief.brief_kind,
      brief_version: dailyBrief.brief_version,
      brief_status: dailyBrief.daily_brief_summary.brief_status,
      summary: dailyBrief.daily_brief_summary.summary,
    },
    launch_day_summary: {
      role_card_count: roleCards.length,
      capture_prompt_count: capturePrompts.length,
      no_go_count: noGoChecks.length,
      card_status: 'local_standup_card_available_live_writes_blocked',
    },
    source_artifact_manifest: dailyBrief.source_artifact_manifest,
    standup_sequence: [
      'open with the PM Lane 159 daily brief status and confirm this standup is review-only',
      'walk the PM, field lead, customer/site contact, and executor/AI relay role cards',
      'record open decisions, blockers, and next-packet recommendation outside the app',
      'close by confirming no approval, import, field, production, customer, or finance write was admitted',
    ],
    role_cards: roleCards,
    no_go_checks: noGoChecks,
    capture_prompts: capturePrompts,
    next_packet_options: dailyBrief.blocked_next_packet_options,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_standup_card_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...dailyBrief.blocked_boundaries,
      'pilot_launch_standup_card_server_write',
      'standup_card_business_state_write',
      'meeting_action_item_write',
      'field_direction_write',
      'customer_commitment_write',
    ])),
  }
}

function buildPilotLaunchCaptureSheetExport(
  packet: IntakeWorkbenchPacket,
  approvalDryRunReadiness: ApprovalDryRunReadinessItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const standupCard = buildPilotLaunchStandupCardExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const captureSections = [
    {
      section_id: 'pm-decisions-to-review',
      label: 'PM decisions to review',
      capture_mode: 'local_prompt_only',
      prompt: 'Write down the decisions Jason needs to make or approve after the launch conversation.',
      captured_value: null,
      prohibited_use: 'This section does not create an approval row, PM decision record, or project import.',
    },
    {
      section_id: 'field-start-blockers',
      label: 'Field-start blockers',
      capture_mode: 'local_prompt_only',
      prompt: 'Capture site, safety, access, crew, material, apparatus, schedule, or status blockers that need follow-up before any later field authorization.',
      captured_value: null,
      prohibited_use: 'This section does not authorize field work, assign a lead, assign a crew, or change schedule/status.',
    },
    {
      section_id: 'customer-site-questions',
      label: 'Customer and site questions',
      capture_mode: 'local_prompt_only',
      prompt: 'Capture customer/site constraints, access notes, and completion-evidence questions that need future agreement.',
      captured_value: null,
      prohibited_use: 'This section does not create a customer commitment, customer report, or completion evidence record.',
    },
    {
      section_id: 'executor-ai-relay-followup',
      label: 'Executor and AI relay follow-up',
      capture_mode: 'local_prompt_only',
      prompt: 'Capture what needs to be relayed back from Desktop Codex, sidecar scouts, or external executors for VS Code Codex review.',
      captured_value: null,
      prohibited_use: 'This section does not stage executor output, mutate hosted services, or delegate implementation authority.',
    },
    {
      section_id: 'next-packet-recommendation',
      label: 'Next packet recommendation',
      capture_mode: 'local_prompt_only',
      prompt: 'Recommend the next bounded packet: stay local-only, wait for Desktop Codex closeout, prepare PM Lane 142 admission, or open another scout.',
      captured_value: null,
      prohibited_use: 'This section does not authorize live approval, import, field, production, customer, finance, or hosted-service writes.',
    },
  ]
  const handoffRules = [
    'treat handwritten or copied notes from this sheet as review context only until a later packet admits persistence',
    'bring no-go items back to VS Code Codex before any implementation lane is opened',
    'keep customer-facing, field-direction, assignment, schedule/status, production, and finance outputs blocked',
    'preserve Desktop Codex and sidecar outputs as evidence for review, not as direct merge or deployment authority',
  ]

  return {
    capture_sheet_kind: 'pm_import_candidate_pilot_launch_capture_sheet',
    capture_sheet_version: 'pm_lane_161_local_pilot_launch_capture_sheet_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: standupCard.candidate_identity,
    field_shape: standupCard.field_shape,
    source_standup_card: {
      file_name: pilotLaunchStandupCardFileName(candidate),
      standup_card_kind: standupCard.standup_card_kind,
      standup_card_version: standupCard.standup_card_version,
      card_status: standupCard.launch_day_summary.card_status,
      capture_prompt_count: standupCard.launch_day_summary.capture_prompt_count,
      no_go_count: standupCard.launch_day_summary.no_go_count,
    },
    capture_sheet_summary: {
      section_count: captureSections.length,
      handoff_rule_count: handoffRules.length,
      no_go_count: standupCard.no_go_checks.length,
      sheet_status: 'local_capture_sheet_available_live_writes_blocked',
    },
    source_artifact_manifest: standupCard.source_artifact_manifest,
    capture_sections: captureSections,
    handoff_rules: handoffRules,
    inherited_no_go_checks: standupCard.no_go_checks,
    next_packet_options: standupCard.next_packet_options,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_capture_sheet_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_commitment_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      meeting_note_persisted: false,
      owner_assignment_created: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...standupCard.blocked_boundaries,
      'pilot_launch_capture_sheet_server_write',
      'capture_sheet_business_state_write',
      'meeting_note_persistence',
      'owner_assignment_write',
      'field_direction_write',
      'customer_commitment_write',
    ])),
  }
}

function buildPilotLaunchFollowupPacketExport(
  packet: IntakeWorkbenchPacket,
  approvalDryRunReadiness: ApprovalDryRunReadinessItem[],
  reviewChecks: Record<string, boolean>,
  approvalDraft: ApprovalDecisionDraft,
  fieldPrepQueue: OperatingQueueItem[],
  fieldPrepCoverageSnapshot: FieldPrepCoverageItem[],
  fieldPrepConversationAgenda: FieldPrepAgendaItem[],
  notAllowed: string[],
  futureRoute: string,
  fieldReadinessChecks: Record<string, boolean>,
  fieldQuestionsDraft: FieldQuestionsDraft,
  fieldObservationScratchpad: FieldObservationScratchpad,
) {
  const candidate = packet.candidate
  const captureSheet = buildPilotLaunchCaptureSheetExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
  const reviewReturnSections = [
    {
      section_id: 'decisions-to-return',
      source_section_id: 'pm-decisions-to-review',
      return_mode: 'copy_paste_review_only',
      prompt: 'Paste or summarize PM decisions that need VS Code Codex review before any later admission packet.',
      returned_value: null,
      prohibited_use: 'This section does not create an approval row, decision record, owner assignment, due date, or project import.',
    },
    {
      section_id: 'blockers-to-return',
      source_section_id: 'field-start-blockers',
      return_mode: 'copy_paste_review_only',
      prompt: 'Paste or summarize field-start blockers that need packet planning or PM follow-up.',
      returned_value: null,
      prohibited_use: 'This section does not authorize field work, schedule work, change status, assign a lead, or assign a crew.',
    },
    {
      section_id: 'customer-site-questions-to-return',
      source_section_id: 'customer-site-questions',
      return_mode: 'copy_paste_review_only',
      prompt: 'Paste or summarize customer/site questions that should remain review context until a later admitted customer-reporting lane.',
      returned_value: null,
      prohibited_use: 'This section does not create a customer commitment, customer report, completion evidence, or external customer delivery.',
    },
    {
      section_id: 'executor-ai-relay-to-return',
      source_section_id: 'executor-ai-relay-followup',
      return_mode: 'copy_paste_review_only',
      prompt: 'Paste or summarize Desktop Codex, sidecar, or executor evidence that needs technical-authority review.',
      returned_value: null,
      prohibited_use: 'This section does not stage executor output, approve a delegated closeout, mutate hosted services, or grant implementation authority.',
    },
    {
      section_id: 'next-packet-recommendation-to-return',
      source_section_id: 'next-packet-recommendation',
      return_mode: 'copy_paste_review_only',
      prompt: 'Paste or summarize the recommended next bounded packet for VS Code Codex review.',
      returned_value: null,
      prohibited_use: 'This section does not admit live approval, import, field, production, customer, finance, hosted-service, or autonomous AI writes.',
    },
  ]
  const orchestrationReviewSlots = [
    {
      slot_id: 'vs-code-codex-review',
      slot_status: 'review_context_only',
      expected_input: 'Paste the returned follow-up notes into the next VS Code Codex review turn.',
      prohibited_action: 'Do not treat this packet as direct approval to implement or write business state.',
    },
    {
      slot_id: 'desktop-codex-closeout-review',
      slot_status: 'review_context_only',
      expected_input: 'Attach or summarize Desktop Codex closeout evidence when it exists.',
      prohibited_action: 'Do not stage, merge, publish, or deploy Desktop Codex output without VS Code Codex review.',
    },
    {
      slot_id: 'sidecar-scout-review',
      slot_status: 'review_context_only',
      expected_input: 'Attach or summarize sidecar scout findings that influence the next bounded packet.',
      prohibited_action: 'Do not convert scout findings into assignments, schedule/status updates, customer commitments, or hosted writes.',
    },
  ]

  return {
    follow_up_packet_kind: 'pm_import_candidate_pilot_launch_follow_up_packet',
    follow_up_packet_version: 'pm_lane_162_local_pilot_launch_follow_up_packet_v1',
    generated_locally_at: new Date().toISOString(),
    candidate_identity: captureSheet.candidate_identity,
    field_shape: captureSheet.field_shape,
    source_capture_sheet: {
      file_name: pilotLaunchCaptureSheetFileName(candidate),
      capture_sheet_kind: captureSheet.capture_sheet_kind,
      capture_sheet_version: captureSheet.capture_sheet_version,
      sheet_status: captureSheet.capture_sheet_summary.sheet_status,
      section_count: captureSheet.capture_sheet_summary.section_count,
    },
    follow_up_summary: {
      review_return_section_count: reviewReturnSections.length,
      orchestration_review_slot_count: orchestrationReviewSlots.length,
      inherited_no_go_count: captureSheet.inherited_no_go_checks.length,
      packet_status: 'local_follow_up_packet_available_live_writes_blocked',
    },
    source_artifact_manifest: captureSheet.source_artifact_manifest,
    review_return_sections: reviewReturnSections,
    orchestration_review_slots: orchestrationReviewSlots,
    review_return_rules: [
      ...captureSheet.handoff_rules,
      'use this packet as copy/paste review context only',
      'do not create owners, due dates, action items, customer commitments, or schedule/status records from this packet',
    ],
    inherited_no_go_checks: captureSheet.inherited_no_go_checks,
    next_packet_options: captureSheet.next_packet_options,
    authority_boundary: {
      mutation_authority: 'not_admitted',
      persistence_authority: 'not_admitted',
      local_pilot_launch_follow_up_packet_only: true,
      copy_paste_review_return_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      owner_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_commitment_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      meeting_note_persisted: false,
      action_item_persisted: false,
      review_return_persisted: false,
      executor_assignment_created: false,
      due_date_assignment_created: false,
      hosted_service_mutated: false,
      server_write_performed: false,
    },
    blocked_boundaries: Array.from(new Set([
      ...captureSheet.blocked_boundaries,
      'pilot_launch_follow_up_packet_server_write',
      'follow_up_packet_business_state_write',
      'copy_paste_packet_submission',
      'review_return_persistence',
      'meeting_note_persistence',
      'action_item_persistence',
      'owner_assignment_write',
      'due_date_assignment_write',
      'field_direction_write',
      'customer_commitment_write',
      'executor_delegation_write',
      'desktop_codex_output_publication',
      'hosted_service_mutation',
    ])),
  }
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
  const projectDataEntryDecisionGateLines = projectDataEntryDecisionGateExportLines(warnings, summary)
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
    ...(projectDataEntryDecisionGateLines.length ? [...projectDataEntryDecisionGateLines, ''] : []),
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
    '## Hosted Approval Surface And Remaining Blocks',
    '',
    `- Hosted approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Hosted approval route: ${storagePlan.recommended_route || 'not admitted'}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    '- Browser approval submission, first approval-row creation, import rows, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this register as exception-review synthesis only.',
    '- Do not treat this register as approval, persistence authority, import authority, work authorization, assignment, schedule, status update, task creation, issue creation, durable field record, hosted write proof, or production tracking.',
    '- Keep browser approval submission and project import blocked until a later packet explicitly admits the required write path.',
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
    '## Hosted Approval Surface And Remaining Blocks',
    '',
    `- Hosted approval table: ${storagePlan.recommended_table || 'not admitted'}`,
    `- Hosted approval route: ${futureRoute}`,
    `- Admission authority: ${admissionPlan.mutation_authority || 'not_admitted'}`,
    '- Browser approval submission, first approval-row creation, project import, assignment, schedule, status, issue, task, durable field record, and production tracking writes remain blocked.',
    '',
    '## Not Allowed',
    '',
    markdownList(notAllowed.map(formatLabel)),
    '',
    '## Minimum Use',
    '',
    '- Use this snapshot as scan-level PM review synthesis only.',
    '- Do not treat this snapshot as approval, persistence authority, import authority, work authorization, assignment, schedule, status update, task creation, issue creation, durable field record, hosted write proof, or production tracking.',
    '- Keep browser approval submission and project import blocked until a later packet explicitly admits the required write path.',
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
  const [fieldStartPreflightStatus, setFieldStartPreflightStatus] = useState('')
  const [fieldExecutionGateDesignStatus, setFieldExecutionGateDesignStatus] = useState('')
  const [leadFieldAssignmentDraftStatus, setLeadFieldAssignmentDraftStatus] = useState('')
  const [fieldAuthorizationAssignmentDraftStatus, setFieldAuthorizationAssignmentDraftStatus] = useState('')
  const [scheduleStatusControlsDraftStatus, setScheduleStatusControlsDraftStatus] = useState('')
  const [durableFieldRecordDraftStatus, setDurableFieldRecordDraftStatus] = useState('')
  const [productionTrackingDraftStatus, setProductionTrackingDraftStatus] = useState('')
  const [customerReportingDraftStatus, setCustomerReportingDraftStatus] = useState('')
  const [financialHandoffDraftStatus, setFinancialHandoffDraftStatus] = useState('')
  const [pilotLaunchBinderStatus, setPilotLaunchBinderStatus] = useState('')
  const [pilotLaunchDailyBriefStatus, setPilotLaunchDailyBriefStatus] = useState('')
  const [pilotLaunchStandupCardStatus, setPilotLaunchStandupCardStatus] = useState('')
  const [pilotLaunchCaptureSheetStatus, setPilotLaunchCaptureSheetStatus] = useState('')
  const [pilotLaunchFollowupPacketStatus, setPilotLaunchFollowupPacketStatus] = useState('')
  const [approvalDryRunStatus, setApprovalDryRunStatus] = useState('')
  const [approvalDryRunPreview, setApprovalDryRunPreview] = useState('')
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
  const approvalStatus = packet?.approvalStatus
  const summary = candidate?.summary || {}
  const project = candidate?.project || {}
  const warnings = candidate?.warnings || []
  const decisions = candidate?.human_decisions || []
  const hasProjectDataEntryWarning = hasWarningCode(warnings, PROJECT_DATA_ENTRY_WARNING_CODE)
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
  const workflowGates: WorkflowGateItem[] = [
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
      status: approvalStatus?.classification || approvalContract?.persistence_authority || storagePlan?.persistence_authority || 'not_admitted',
      detail: `Approval readback is ${approvalStatusSummary(approvalStatus)}; browser approval submission and future import remain blocked at ${futureRoute}.`,
    },
    {
      title: 'Hosted parity',
      status: 'hosted_schema_and_readback_green',
      detail: 'PM Lane 041A/041B/041C/138 plus control-plane pooler maintenance proved hosted reads, schema, approval status readback, approval POST registration, and bounded MCP read proof; browser approval submission remains blocked.',
    },
    {
      title: 'Future import',
      status: 'not_admitted',
      detail: 'Project, workpackage, task, apparatus, assignment, schedule, and status writes remain blocked.',
    },
  ]
  const workflowGateGroups = groupWorkflowGateItems(workflowGates)
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
  const persistenceReadinessGateGroups = useMemo(
    () => groupPersistenceReadinessGates(persistenceReadinessGates),
    [persistenceReadinessGates],
  )
  const readyPersistenceGateCount = persistenceReadinessGates.filter((gate) => gate.status === 'ready').length
  const approvalDryRunReadiness = useMemo(
    () => buildApprovalDryRunReadiness(packet, reviewChecks, approvalDraft),
    [packet, reviewChecks, approvalDraft],
  )
  const approvalDryRunReadinessCount = approvalDryRunReadinessCounts(approvalDryRunReadiness)
  const operatingQueue = useMemo(
    () => buildPmOperatingQueue(approvalDraft, reviewChecks, persistenceReadinessGates),
    [approvalDraft, reviewChecks, persistenceReadinessGates],
  )
  const operatingQueueGroups = useMemo(
    () => groupPmOperatingQueueItems(operatingQueue),
    [operatingQueue],
  )
  const importExceptionRegister = useMemo(
    () => buildImportExceptionRegister(candidate, noGoChecks, reviewChecks, approvalDraft),
    [candidate, noGoChecks, reviewChecks, approvalDraft],
  )
  const importExceptionRegisterGroups = useMemo(
    () => groupImportExceptionRegisterItems(importExceptionRegister),
    [importExceptionRegister],
  )
  const fieldPrepQueue = useMemo(
    () => buildFieldPrepQueue(fieldReadinessChecks, fieldQuestionsDraft),
    [fieldReadinessChecks, fieldQuestionsDraft],
  )
  const fieldPrepQueueGroups = useMemo(
    () => groupFieldPrepQueueItems(fieldPrepQueue),
    [fieldPrepQueue],
  )
  const fieldPrepCoverageSnapshot = useMemo(
    () => buildFieldPrepCoverageSnapshot(reviewChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad),
    [reviewChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldPrepCoverageSnapshotGroups = useMemo(
    () => groupFieldPrepCoverageSnapshotItems(fieldPrepCoverageSnapshot),
    [fieldPrepCoverageSnapshot],
  )
  const fieldPrepConversationAgenda = useMemo(
    () => buildFieldPrepConversationAgenda(fieldPrepCoverageSnapshot),
    [fieldPrepCoverageSnapshot],
  )
  const fieldPrepConversationAgendaGroups = useMemo(
    () => groupFieldPrepConversationAgendaItems(fieldPrepConversationAgenda),
    [fieldPrepConversationAgenda],
  )
  const fieldStartPreflight = useMemo(
    () => packet ? buildFieldStartPreflightExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad) : null,
    [packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartOperatorScript = useMemo(
    () => buildFieldStartOperatorScript(candidate, fieldStartPreflight, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldStartPreflight, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartStopLineReview = useMemo(
    () => buildFieldStartStopLineReview(candidate, fieldStartPreflight, notAllowed),
    [candidate, fieldStartPreflight, notAllowed],
  )
  const fieldStartCustomerSiteQuestions = useMemo(
    () => buildFieldStartCustomerSiteQuestions(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartPmFollowupPromptReview = useMemo(
    () => buildFieldStartPmFollowupPromptReview(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartConversationCloseoutPrompts = useMemo(
    () => buildFieldStartConversationCloseoutPrompts(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartBringBackSummaryTriageStrip = useMemo(
    () => buildFieldStartBringBackSummaryTriageStrip(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartBringBackDetailJumpRail = useMemo(
    () => buildFieldStartBringBackDetailJumpRail(fieldStartBringBackSummaryTriageStrip),
    [fieldStartBringBackSummaryTriageStrip],
  )
  const fieldStartBringBackLensOpenContextCue = useMemo(
    () => buildFieldStartBringBackLensOpenContextCue(fieldStartBringBackSummaryTriageStrip),
    [fieldStartBringBackSummaryTriageStrip],
  )
  const fieldStartBringBackCueStatusLegend = useMemo(
    () => buildFieldStartBringBackCueStatusLegend(),
    [],
  )
  const fieldStartBringBackReviewQueue = useMemo(
    () => buildFieldStartBringBackReviewQueue(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartSourceReviewBringBackLens = useMemo(
    () => buildFieldStartSourceReviewBringBackLens(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartCustomerSiteClarificationBringBackLens = useMemo(
    () => buildFieldStartCustomerSiteClarificationBringBackLens(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartLeadResourceClarificationBringBackLens = useMemo(
    () => buildFieldStartLeadResourceClarificationBringBackLens(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const fieldStartLaterBoundedPacketCandidateBringBackLens = useMemo(
    () => buildFieldStartLaterBoundedPacketCandidateBringBackLens(candidate, fieldQuestionsDraft, fieldObservationScratchpad),
    [candidate, fieldQuestionsDraft, fieldObservationScratchpad],
  )
  const pmIntakeSnapshot = useMemo(
    () => buildPmIntakeSnapshot(persistenceReadinessGates, operatingQueue, importExceptionRegister, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft),
    [persistenceReadinessGates, operatingQueue, importExceptionRegister, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, closeoutChecks, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad, approvalDraft],
  )
  const pmIntakeSnapshotGroups = useMemo(
    () => groupPmIntakeSnapshotItems(pmIntakeSnapshot),
    [pmIntakeSnapshot],
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
  const fieldPrepOutputStatuses = [fieldBriefStatus, fieldObservationStatus, fieldPrepCoverageStatus, fieldPrepAgendaStatus, fieldPrepPacketStatus, fieldStartPreflightStatus, fieldExecutionGateDesignStatus, leadFieldAssignmentDraftStatus, fieldAuthorizationAssignmentDraftStatus, scheduleStatusControlsDraftStatus, durableFieldRecordDraftStatus, productionTrackingDraftStatus, customerReportingDraftStatus, financialHandoffDraftStatus, pilotLaunchBinderStatus, pilotLaunchDailyBriefStatus, pilotLaunchStandupCardStatus, pilotLaunchCaptureSheetStatus, pilotLaunchFollowupPacketStatus].filter(Boolean)
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

  function buildApprovalDryRun() {
    if (!packet) {
      return
    }

    const dryRun = buildLocalApprovalSubmissionDryRun(packet, notAllowed, futureRoute, reviewChecks, approvalDraft)
    setApprovalDryRunPreview(`${JSON.stringify(dryRun, null, 2)}\n`)
    setApprovalDryRunStatus(`Local approval dry run prepared for ${candidate?.candidate_id || 'the current intake packet'}; no network request was sent.`)
  }

  function exportApprovalDryRunEnvelope() {
    if (!packet) {
      return
    }

    const dryRun = buildLocalApprovalSubmissionDryRun(packet, notAllowed, futureRoute, reviewChecks, approvalDraft)
    const contents = `${JSON.stringify(dryRun, null, 2)}\n`
    setApprovalDryRunPreview(contents)
    downloadTextFile(approvalDryRunEnvelopeFileName(candidate), contents, 'application/json')
    setApprovalDryRunStatus(`Local approval dry run envelope exported for ${candidate?.candidate_id || 'the current intake packet'}; no network request was sent.`)
  }

  function exportApprovalDryRunReadiness() {
    if (!packet) {
      return
    }

    const readiness = buildApprovalDryRunReadinessExport(packet, approvalDryRunReadiness, notAllowed, futureRoute)
    const contents = `${JSON.stringify(readiness, null, 2)}\n`
    downloadTextFile(approvalDryRunReadinessFileName(candidate), contents, 'application/json')
    setApprovalDryRunStatus(`Local approval dry run readiness exported for ${candidate?.candidate_id || 'the current intake packet'}; no network request was sent.`)
  }

  function exportApprovalReviewBundle() {
    if (!packet) {
      return
    }

    const bundle = buildApprovalReviewBundleExport(packet, approvalDryRunReadiness, notAllowed, futureRoute, reviewChecks, approvalDraft)
    const contents = `${JSON.stringify(bundle, null, 2)}\n`
    setApprovalDryRunPreview(`${JSON.stringify(bundle.dry_run_envelope, null, 2)}\n`)
    downloadTextFile(approvalReviewBundleFileName(candidate), contents, 'application/json')
    setApprovalDryRunStatus(`Local approval review bundle exported for ${candidate?.candidate_id || 'the current intake packet'}; no network request was sent.`)
  }

  function exportApprovalLiveGatePreflight() {
    if (!packet) {
      return
    }

    const preflight = buildApprovalLiveGatePreflightExport(packet, approvalDryRunReadiness, notAllowed, futureRoute, reviewChecks, approvalDraft)
    const contents = `${JSON.stringify(preflight, null, 2)}\n`
    setApprovalDryRunPreview(contents)
    downloadTextFile(approvalLiveGatePreflightFileName(candidate), contents, 'application/json')
    setApprovalDryRunStatus(`Local approval live-gate preflight exported for ${candidate?.candidate_id || 'the current intake packet'}; no network request was sent.`)
  }

  function clearApprovalDryRun() {
    setApprovalDryRunPreview('')
    setApprovalDryRunStatus('')
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

  function exportFieldStartPreflight() {
    if (!packet) {
      return
    }

    const preflight = buildFieldStartPreflightExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(fieldStartPreflightFileName(candidate), `${JSON.stringify(preflight, null, 2)}\n`, 'application/json')
    setFieldStartPreflightStatus(`Field start preflight prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldExecutionGateDesign() {
    if (!packet) {
      return
    }

    const design = buildFieldExecutionGateDesignExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(fieldExecutionGateDesignFileName(candidate), `${JSON.stringify(design, null, 2)}\n`, 'application/json')
    setFieldExecutionGateDesignStatus(`Field execution gate design prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportLeadFieldAssignmentDraft() {
    if (!packet) {
      return
    }

    const draft = buildLeadFieldAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(leadFieldAssignmentDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setLeadFieldAssignmentDraftStatus(`Lead field assignment draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFieldAuthorizationAssignmentDraft() {
    if (!packet) {
      return
    }

    const draft = buildFieldAuthorizationAssignmentDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(fieldAuthorizationAssignmentDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setFieldAuthorizationAssignmentDraftStatus(`Field authorization assignment draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportScheduleStatusControlsDraft() {
    if (!packet) {
      return
    }

    const draft = buildScheduleStatusControlsDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(scheduleStatusControlsDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setScheduleStatusControlsDraftStatus(`Schedule status controls draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportDurableFieldRecordDraft() {
    if (!packet) {
      return
    }

    const draft = buildDurableFieldRecordDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(durableFieldRecordDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setDurableFieldRecordDraftStatus(`Durable field record draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportProductionTrackingDraft() {
    if (!packet) {
      return
    }

    const draft = buildProductionTrackingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(productionTrackingDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setProductionTrackingDraftStatus(`Production tracking draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportCustomerReportingDraft() {
    if (!packet) {
      return
    }

    const draft = buildCustomerReportingDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(customerReportingDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setCustomerReportingDraftStatus(`Customer reporting draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportFinancialHandoffDraft() {
    if (!packet) {
      return
    }

    const draft = buildFinancialHandoffDraftExport(packet, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(financialHandoffDraftFileName(candidate), `${JSON.stringify(draft, null, 2)}\n`, 'application/json')
    setFinancialHandoffDraftStatus(`Financial handoff draft prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPilotLaunchBinder() {
    if (!packet) {
      return
    }

    const binder = buildPilotLaunchBinderExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(pilotLaunchBinderFileName(candidate), `${JSON.stringify(binder, null, 2)}\n`, 'application/json')
    setPilotLaunchBinderStatus(`Pilot launch binder prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPilotLaunchDailyBrief() {
    if (!packet) {
      return
    }

    const dailyBrief = buildPilotLaunchDailyBriefExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(pilotLaunchDailyBriefFileName(candidate), `${JSON.stringify(dailyBrief, null, 2)}\n`, 'application/json')
    setPilotLaunchDailyBriefStatus(`Pilot launch daily brief prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPilotLaunchStandupCard() {
    if (!packet) {
      return
    }

    const standupCard = buildPilotLaunchStandupCardExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(pilotLaunchStandupCardFileName(candidate), `${JSON.stringify(standupCard, null, 2)}\n`, 'application/json')
    setPilotLaunchStandupCardStatus(`Pilot launch standup card prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPilotLaunchCaptureSheet() {
    if (!packet) {
      return
    }

    const captureSheet = buildPilotLaunchCaptureSheetExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(pilotLaunchCaptureSheetFileName(candidate), `${JSON.stringify(captureSheet, null, 2)}\n`, 'application/json')
    setPilotLaunchCaptureSheetStatus(`Pilot launch capture sheet prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
  }

  function exportPilotLaunchFollowupPacket() {
    if (!packet) {
      return
    }

    const followupPacket = buildPilotLaunchFollowupPacketExport(packet, approvalDryRunReadiness, reviewChecks, approvalDraft, fieldPrepQueue, fieldPrepCoverageSnapshot, fieldPrepConversationAgenda, notAllowed, futureRoute, fieldReadinessChecks, fieldQuestionsDraft, fieldObservationScratchpad)
    downloadTextFile(pilotLaunchFollowupPacketFileName(candidate), `${JSON.stringify(followupPacket, null, 2)}\n`, 'application/json')
    setPilotLaunchFollowupPacketStatus(`Pilot launch follow-up packet prepared from ${candidate?.candidate_id || 'the current intake packet'} without a server write.`)
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
            <h2>Hosted readiness</h2>
            <span className="status-pill status-ready">green</span>
          </div>
          <p>Hosted PM intake reads, approval status readback, approval route registration, and bounded MCP read proof are green.</p>
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
              <div aria-label="Field prep output subgroups" style={{ display: 'grid', gap: '0.75rem' }}>
                <section aria-label="Field prep basics output actions" style={{ display: 'grid', gap: '0.4rem' }}>
                  <h4 style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: 0, margin: 0, textTransform: 'uppercase' }}>Field Prep Basics</h4>
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
                    <button className="btn btn-outline" onClick={exportFieldStartPreflight} disabled={!packet}>
                      Export Field Start Preflight
                    </button>
                  </div>
                </section>
                <section aria-label="Admission draft output actions" style={{ display: 'grid', gap: '0.4rem' }}>
                  <h4 style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: 0, margin: 0, textTransform: 'uppercase' }}>Admission Drafts</h4>
                  <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                    <button className="btn btn-outline" onClick={exportFieldExecutionGateDesign} disabled={!packet}>
                      Export Field Execution Gate Design
                    </button>
                    <button className="btn btn-outline" onClick={exportLeadFieldAssignmentDraft} disabled={!packet}>
                      Export Lead Field Assignment Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportFieldAuthorizationAssignmentDraft} disabled={!packet}>
                      Export Field Authorization Assignment Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportScheduleStatusControlsDraft} disabled={!packet}>
                      Export Schedule Status Controls Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportDurableFieldRecordDraft} disabled={!packet}>
                      Export Durable Field Record Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportProductionTrackingDraft} disabled={!packet}>
                      Export Production Tracking Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportCustomerReportingDraft} disabled={!packet}>
                      Export Customer Reporting Draft
                    </button>
                    <button className="btn btn-outline" onClick={exportFinancialHandoffDraft} disabled={!packet}>
                      Export Financial Handoff Draft
                    </button>
                  </div>
                </section>
                <section aria-label="Pilot launch output actions" style={{ display: 'grid', gap: '0.4rem' }}>
                  <h4 style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: 0, margin: 0, textTransform: 'uppercase' }}>Pilot Launch Outputs</h4>
                  <div className="pm-review-link-row pm-review-link-row-start" style={{ margin: 0 }}>
                    <button className="btn btn-outline" onClick={exportPilotLaunchBinder} disabled={!packet}>
                      Export Pilot Launch Binder
                    </button>
                    <button className="btn btn-outline" onClick={exportPilotLaunchDailyBrief} disabled={!packet}>
                      Export Pilot Launch Daily Brief
                    </button>
                    <button className="btn btn-outline" onClick={exportPilotLaunchStandupCard} disabled={!packet}>
                      Export Pilot Launch Standup Card
                    </button>
                    <button className="btn btn-outline" onClick={exportPilotLaunchCaptureSheet} disabled={!packet}>
                      Export Pilot Launch Capture Sheet
                    </button>
                    <button className="btn btn-outline" onClick={exportPilotLaunchFollowupPacket} disabled={!packet}>
                      Export Pilot Launch Follow-Up Packet
                    </button>
                  </div>
                </section>
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

        <details open id="pm-command-center" aria-label="Local PM intake command center" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Command Center</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Command center controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Compact top-of-page scan for the current local PM move, next field question posture, handoff context, and blocked future authority. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write.
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
          </div>
        </details>

        <details open id="pm-meeting-readout" aria-label="Local PM intake meeting readout" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Meeting Readout</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Meeting readout controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Conversation-ready local summary for PM, lead, customer, or field review. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write.
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
          </div>
        </details>

        <details open id="pm-constraint-radar" aria-label="Local PM intake constraint radar" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Constraint Radar</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Constraint radar controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Constraint scan for source/review, field-prep, executor/hosted, and future write-authority boundaries. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state; it creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, workbook macro path, workbook writeback, or production write.
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
          </div>
        </details>

          </details>
          <details open aria-label="Daily action helper panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Daily Action Panels</h2>
            </summary>

        <details open id="pm-daily-review-script" aria-label="Local PM intake daily review script" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Daily Review Script</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Daily review script controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              First 5 minutes of browser-local review, derived from the existing workbench state. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write.
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
          </div>
        </details>

        <details open id="pm-field-start-operator-script" aria-label="Local field start operator script" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Start Operator Script</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Local field start operator script controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Morning-of field-start conversation script derived from existing local prep state. It creates no localStorage key, export artifact, backend route, task, issue, field authorization, assignment, schedule/status change, durable field record, production tracking row, hosted write claim, or production write.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartOperatorScript.map((item) => (
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
                    <span className={`status-pill ${fieldStartOperatorScriptTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </details>

        {hasProjectDataEntryWarning ? (
          <section id="pm-field-start-source-resource-question-prep-cue" aria-label="Local field-start source and resource question prep cue" className="card" style={{ display: 'grid', gap: '0.65rem', padding: '1rem', marginBottom: '1rem' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h2 style={{ margin: 0 }}>Local Field-Start Source/Resource Question Prep Cue</h2>
                <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Prepare PM/lead questions only from existing source/resource context. This cue creates no localStorage key, export artifact, backend route, task, action item, owner, due date, source access, source writeback, resource assignment, schedule/status change, procurement or rental commitment, customer commitment, warning acceptance, approval row, import, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">question prep</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
              <li>Equipment inventory context: {formatCount(summary.equipment_inventory_count)} rows available for question shaping only.</li>
              <li>Technician capability context: {formatCount(summary.capability_count)} rows available for coverage questions only.</li>
              {PROJECT_SOURCE_RESOURCE_QUESTION_PREP_CUES.map((item) => (
                <li key={item.term}>
                  <strong>{item.term}</strong>: {item.detail}
                </li>
              ))}
            </ul>
            <p style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
              No live source access, source writeback, resource assignment, schedule/status change, procurement or rental commitment, customer commitment, warning acceptance, approval, import, field authorization, or business-state mutation is granted.
            </p>
          </section>
        ) : null}

        <details open id="pm-field-start-stop-line-review" aria-label="Local field start stop-line quick review" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Start Stop-Line Quick Review</h2>
            <span className="status-pill status-deferred">blocked writes</span>
          </summary>
          <div aria-label="Local field start stop-line quick review controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Morning-of Temp Power stop-line check for the field-start conversation. It creates no approval, import, field, production, customer, or finance write; no localStorage key, export artifact, backend route, approval row, field authorization, assignment, schedule/status change, durable field record, production tracking row, customer report, finance output, hosted write claim, or production write.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartStopLineReview.map((item) => (
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
                    <span className={`status-pill ${fieldStartStopLineReviewTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </details>

        <details open id="pm-field-start-customer-site-questions" aria-label="Local field start customer site questions quick review" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Start Customer/Site Questions Quick Review</h2>
            <span className="status-pill status-awaiting-values">question review</span>
          </summary>
          <div aria-label="Local field start customer site questions quick review controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Morning-of Temp Power customer/site question review derived from existing field questions and observations. It creates no localStorage key, export artifact, backend route, task, issue, assignment, schedule/status change, customer commitment, customer report, field instruction, hosted write claim, or production write.
            </p>
            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartCustomerSiteQuestions.map((item) => (
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
                    <span className={`status-pill ${fieldStartCustomerSiteQuestionTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
          <section id="pm-field-start-pm-followup-prompt-review" aria-label="Local PM follow-up prompt review" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local PM Follow-up Prompt Review</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Copy/paste prompt review for the next PM, lead, or customer question after the customer/site check. It creates no localStorage key, export artifact, backend route, task, action item, owner, due date, customer commitment, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">prompt review</span>
            </div>
            <div aria-label="Local PM follow-up prompt review controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartPmFollowupPromptReview.map((item) => (
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
                    <span className={`status-pill ${fieldStartPmFollowupPromptReviewTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-conversation-closeout-prompt-review" aria-label="Local field-start conversation closeout prompt review" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field-Start Conversation Closeout Prompt Review</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Copy/paste review context for what to bring back after the field-start conversation. It creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, customer commitment, customer report, field instruction, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">closeout prompt</span>
            </div>
            <div aria-label="Local field-start conversation closeout prompt review controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartConversationCloseoutPrompts.map((item) => (
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
                    <span className={`status-pill ${fieldStartConversationCloseoutPromptTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-bring-back-summary-triage-strip" aria-label="Local field-start bring-back summary triage strip" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Bring-Back Summary Triage Strip</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Compact read-only triage strip for returned field-start conversation context. It summarizes which bring-back areas currently have local context only before the detailed queue and lenses; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, assignment, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking row, hosted write claim, or production write, and exposes no buttons.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">summary triage</span>
            </div>
            <div aria-label="Local field-start bring-back summary triage strip controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartBringBackSummaryTriageStrip.map((item) => (
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
                    <span className={`status-pill ${fieldStartBringBackSummaryTriageStripTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-bring-back-detail-jump-rail" aria-label="Local field-start bring-back detail jump rail" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Bring-Back Detail Jump Rail</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Compact read-only jump rail from the summary triage strip to the exact bring-back detail lens. It only navigates within this browser-local review panel; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, assignment, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking row, hosted write claim, or production write, and exposes no buttons.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">detail jumps</span>
            </div>
            <div id="pm-field-start-bring-back-lens-open-context-cue" aria-label="Local field-start bring-back lens open-context cue" className="card" style={{ padding: '0.75rem', marginTop: '0.85rem', boxShadow: 'none' }}>
              <div className="status-row" style={{ alignItems: 'start' }}>
                <div>
                  <p style={{ margin: 0 }}>
                    <strong>Open-context cue</strong>
                  </p>
                  <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    {fieldStartBringBackLensOpenContextCue} This is a browser-local open-context cue only. It shows which existing bring-back detail lens currently has local context; it creates no meeting note, localStorage key, task, action item, owner, due date, assignment, customer commitment, customer report, field instruction, durable field record, production tracking row, report, export artifact, storage key, backend route, button, hosted write claim, or write path.
                  </p>
                </div>
                <span className="status-pill status-awaiting-values">context cue</span>
              </div>
            </div>
            <div id="pm-field-start-bring-back-review-order-hint" aria-label="Local field-start bring-back review order hint" className="card" style={{ padding: '0.75rem', marginTop: '0.75rem', boxShadow: 'none' }}>
              <div className="status-row" style={{ alignItems: 'start' }}>
                <div>
                  <p style={{ margin: 0 }}>
                    <strong>Review order hint</strong>
                  </p>
                  <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    Review first: Source review lens when returned context names a drawing, workbook row, site note, observer/source, or work-area reference; then customer/site clarification; then lead/resource clarification; use the later bounded packet candidate lens only to classify a future packet question. Browser-local display hint only; creates no link, button, localStorage key, sessionStorage key, task, action item, owner, due date, assignment, schedule/status write, customer report, field instruction, export artifact, backend route, hosted write claim, or write path.
                  </p>
                </div>
                <span className="status-pill status-awaiting-values">review order</span>
              </div>
            </div>
            <div id="pm-field-start-bring-back-cue-status-legend" aria-label="Local field-start bring-back cue status legend" className="card" style={{ padding: '0.75rem', marginTop: '0.75rem', boxShadow: 'none' }}>
              <div className="status-row" style={{ alignItems: 'start' }}>
                <div>
                  <p style={{ margin: 0 }}>
                    <strong>Cue status legend</strong>
                  </p>
                  <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    Display-only legend for the bring-back cue and detail jump statuses. It explains existing status words only; it creates no meeting note, link, button, localStorage key, sessionStorage key, task, action item, owner, due date, assignment, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking row, report, export artifact, backend route, hosted write claim, or write path.
                  </p>
                </div>
                <span className="status-pill status-awaiting-values">status legend</span>
              </div>
              <div aria-label="Local field-start bring-back cue status legend items" style={{ display: 'grid', gap: '0.55rem', marginTop: '0.75rem' }}>
                {fieldStartBringBackCueStatusLegend.map((item) => (
                  <div key={item.id} className="status-row" style={{ alignItems: 'start' }}>
                    <span className={`status-pill ${fieldStartBringBackSummaryTriageStripTone(item.label)}`}>{item.label}</span>
                    <p style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                  </div>
                ))}
              </div>
            </div>
            <nav aria-label="Local field-start bring-back detail jump rail links" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartBringBackDetailJumpRail.map((item) => (
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
                    <span className={`status-pill ${fieldStartBringBackSummaryTriageStripTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </nav>
          </section>
          <section id="pm-field-start-bring-back-review-queue" aria-label="Local field-start bring-back review queue" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Bring-Back Review Queue</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Read-only bring-back queue for returned field-start conversation items. It classifies local review context only and creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, customer commitment, customer report, field instruction, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">review queue</span>
            </div>
            <div aria-label="Local field-start bring-back review queue controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartBringBackReviewQueue.map((item) => (
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
                    <span className={`status-pill ${fieldStartBringBackReviewQueueTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-source-review-bring-back-lens" aria-label="Local field-start source review bring-back lens" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Source Review Bring-Back Lens</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Read-only source review lens for returned field-start conversation items. It helps classify drawings, workbook rows, site notes, observer/source context, and work-area references before any later bounded packet; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, customer commitment, customer report, field instruction, durable record, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">source lens</span>
            </div>
            <div aria-label="Local field-start source review bring-back lens controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartSourceReviewBringBackLens.map((item) => (
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
                    <span className={`status-pill ${fieldStartSourceReviewBringBackLensTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-customer-site-clarification-bring-back-lens" aria-label="Local field-start customer/site clarification bring-back lens" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Customer/Site Clarification Bring-Back Lens</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Read-only customer/site clarification lens for returned field-start conversation items. It helps classify access, shutdown, escort, contact, safety, and constraint answers as browser-local review context only; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, customer commitment, customer report, field instruction, durable record, hosted write claim, or production write.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">clarification lens</span>
            </div>
            <div aria-label="Local field-start customer/site clarification bring-back lens controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartCustomerSiteClarificationBringBackLens.map((item) => (
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
                    <span className={`status-pill ${fieldStartCustomerSiteClarificationBringBackLensTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-lead-resource-clarification-bring-back-lens" aria-label="Local field-start lead/resource clarification bring-back lens" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Lead/Resource Clarification Bring-Back Lens</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Read-only lead/resource clarification lens for returned field-start conversation items. It helps classify lead, crew-readiness, material, equipment, staging, and resource-limit details as browser-local review context only; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, assignment, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking row, hosted write claim, or production write, and exposes no buttons.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">lead/resource lens</span>
            </div>
            <div aria-label="Local field-start lead/resource clarification bring-back lens controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartLeadResourceClarificationBringBackLens.map((item) => (
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
                    <span className={`status-pill ${fieldStartLeadResourceClarificationBringBackLensTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section id="pm-field-start-later-bounded-packet-candidate-bring-back-lens" aria-label="Local field-start later bounded packet candidate bring-back lens" className="card" style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}>
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Later Bounded Packet Candidate Bring-Back Lens</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  Read-only later bounded packet candidate lens for returned field-start conversation items. It helps classify whether a returned item needs a future packet for authority, evidence, owner/timing, customer-facing language, or write-path admission; it creates no meeting note, localStorage key, export artifact, backend route, task, action item, owner, due date, assignment, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking row, hosted write claim, or production write, and exposes no buttons.
                </p>
              </div>
              <span className="status-pill status-awaiting-values">packet candidate lens</span>
            </div>
            <div
              id="pm-field-start-later-bounded-packet-future-boundary-reminder"
              role="note"
              aria-label="PM Lane 203 future packet boundary reminder"
              className="card"
              style={{ padding: '0.75rem', marginTop: '0.75rem', boxShadow: 'none' }}
            >
              <div className="status-row" style={{ alignItems: 'start' }}>
                <div>
                  <p style={{ margin: 0 }}>
                    <strong>Future packet boundary reminder</strong>
                  </p>
                  <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    PM Lane 203 reminder: this lane classifies a future bounded packet question only. It does not create the packet, assign accountability, set timing, write status, direct field work, create customer-facing language, publish reports, create storage, call a backend route, expose controls, or admit any write path.
                  </p>
                </div>
                <span className="status-pill status-blocked">future packet boundary</span>
              </div>
            </div>
            <div aria-label="Local field-start later bounded packet candidate bring-back lens controls" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {fieldStartLaterBoundedPacketCandidateBringBackLens.map((item) => (
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
                    <span className={`status-pill ${fieldStartLaterBoundedPacketCandidateBringBackLensTone(item.status)}`}>{formatLabel(item.status)}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section
            id="pm-field-start-bring-back-local-review-closeout-cue"
            role="note"
            aria-label="Local field-start bring-back local review closeout cue"
            className="card"
            style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}
          >
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Bring-Back Local Review Closeout Cue</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  PM Lane 204 cue: before leaving this bring-back panel, keep the return as browser-local review only. Classify what still belongs in source review, customer/site clarification, lead/resource clarification, or future packet classification; do not record meeting notes, create tasks, assign owners, set dates, direct field work, publish reports, call routes, create storage, export artifacts, expose controls, or admit write paths.
                </p>
              </div>
              <span className="status-pill status-blocked">local closeout cue</span>
            </div>
          </section>
          <section
            id="pm-field-start-bring-back-review-exit-summary"
            role="note"
            aria-label="Local field-start bring-back review exit summary"
            className="card"
            style={{ padding: '0.9rem', marginTop: '0.85rem', boxShadow: 'none' }}
          >
            <div className="status-row" style={{ alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0 }}>Local Field Start Bring-Back Review Exit Summary</h3>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  PM Lane 205 summary: leave this panel with four browser-local classifications only: source review, customer/site clarification, lead/resource clarification, and future packet question. Anything needing approval submission, import, assignment, schedule/status, field direction, customer report, storage, export, route, control, or write authority needs a later bounded packet.
                </p>
              </div>
              <span className="status-pill status-blocked">local exit summary</span>
            </div>
          </section>
        </details>

        <details open id="pm-start-here" aria-label="Local PM intake start here" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Start Here</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Start here controls">
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
          </div>
        </details>

        <details open id="pm-output-selector" aria-label="Local PM intake output selector" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Output Selector</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Output selector controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local chooser for existing outputs already on this workbench. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write.
            </p>
            <div aria-label="Output selector groups" style={{ display: 'grid', gap: '0.85rem', gridTemplateColumns: 'repeat(auto-fit, minmax(15rem, 1fr))', marginTop: '0.85rem' }}>
              {pmIntakeOutputSelector.map((group) => (
                <section key={group.id} aria-label={`${group.label} selector group`} style={{ display: 'grid', gap: '0.55rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{group.label}</h3>
                  <div aria-label={`${group.label} selector outputs`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
              ))}
            </div>
          </div>
        </details>

        <details id="pm-handoff-guide" open aria-label="Local PM intake handoff guide" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Handoff Guide</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Handoff guide controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Browser-local guide for the next context lane. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write.
            </p>
            <div aria-label="Local PM intake handoff guide groups" style={{ display: 'grid', gap: '0.85rem', gridTemplateColumns: 'repeat(auto-fit, minmax(15rem, 1fr))', marginTop: '0.85rem' }}>
              {pmIntakeHandoffGuide.map((group) => (
                <section key={group.id} aria-label={`${group.label} handoff guide group`} style={{ display: 'grid', gap: '0.55rem' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{group.label}</h3>
                  <div aria-label={`${group.label} handoff guide items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
                </section>
              ))}
            </div>
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
          <div aria-label="Workflow map controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Visual map of the current intake path from source review through field-prep context, executor closeout, and still-blocked future write authority. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write.
            </p>
            <div aria-label="Local PM intake workflow map groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {pmIntakeWorkflowMap.map((group) => (
                <section key={group.id} aria-label={`${group.label} workflow map group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} workflow map items`} style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(14rem, 1fr))' }}>
                    {group.items.map((item) => (
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
                </section>
              ))}
            </div>
          </div>
        </details>

        <details id="pm-open-items" open aria-label="Local PM intake open items lens" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Intake Open Items Lens</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Open items lens controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Exception-first lens for local attention items and future authority blockers. It creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, work authorization, or production write.
            </p>
            <div aria-label="Local PM intake open items lens groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {pmIntakeOpenItems.map((group) => (
                <section key={group.id} aria-label={`${group.label} open items lens group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} open items lens items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
                </section>
              ))}
            </div>
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
          <div aria-label="PM intake snapshot controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Compact scan view for exception posture, decision draft, field-prep context, next local action, hosted parity, and future write boundaries. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state.
            </p>
            <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              {pmIntakeSnapshotSummary(pmIntakeSnapshotCount)}
            </p>
            <div aria-label="Local PM intake snapshot groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {pmIntakeSnapshotGroups.map((group) => (
                <section key={group.id} aria-label={`${group.label} snapshot group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} snapshot items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
                </section>
              ))}
            </div>
          </div>
        </details>

        <details id="pm-operating-queue" open aria-label="Local PM operating queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local PM Operating Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="PM operating queue controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Local queue for today&apos;s intake work. It translates the checklist, local decision draft, and readiness gates into practical next moves without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state.
            </p>
            <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              {formatCount(completeQueueCount)} complete / {formatCount(nextQueueCount)} next / {formatCount(blockedQueueCount)} blocked
            </p>
            <div aria-label="Local PM operating queue groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {operatingQueueGroups.map((group) => (
                <section key={group.id} aria-label={`${group.label} operating queue group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} operating queue items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
              ))}
            </div>
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
          <div aria-label="Import exception register controls">
            <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              Derived exception register for candidate warnings, human decision prompts, admission no-go checks, local review evidence, and local decision draft context. It does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state.
            </p>
            <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
              {importExceptionRegisterSummary(importExceptionRegisterCount)}
            </p>
            <div aria-label="Local import exception decision register groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {importExceptionRegisterGroups.map((group) => (
                <section key={group.id} aria-label={`${group.label} import exception group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} import exception items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((item) => (
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
                </section>
              ))}
            </div>
          </div>
        </details>

        <details id="workflow-gates" open aria-label="Workflow gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Workflow Gates</h2>
            <span className="status-pill status-awaiting-values">read-only</span>
          </summary>
          <div aria-label="Workflow gates controls">
            <div aria-label="Workflow gate groups" style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
              {workflowGateGroups.map((group) => (
                <section key={group.id} aria-label={`${group.label} workflow gate group`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                  <div aria-label={`${group.label} workflow gate items`} style={{ display: 'grid', gap: '0.75rem' }}>
                    {group.items.map((gate) => (
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
              ))}
            </div>
          </div>
        </details>

        <details open aria-label="Exception review and PM decision detail" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
            <summary style={{ cursor: 'pointer' }}>
            <h2 style={{ display: 'inline', margin: 0 }}>Exception Review and PM Decisions</h2>
          </summary>
          <div aria-label="Exception review and PM decision detail controls">
            <div aria-label="Exception and PM decision detail groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
              <section aria-label="Exception Signals detail group">
                <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Exception Signals</h3>
                <div aria-label="Exception Signals detail cards">
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
                          {warning.review_action ? <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{warning.review_action}</p> : null}
                          {warning.formula_error_row_count || warning.formula_error_cell_count ? (
                            <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                              Formula detail: {formatCount(warning.formula_error_row_count)} row(s), {formatCount(warning.formula_error_cell_count)} cell(s).
                            </p>
                          ) : null}
                          {warningColumnSummary(warning) ? (
                            <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                              Affected columns: {warningColumnSummary(warning)}.
                            </p>
                          ) : null}
                          {warningSampleSummary(warning).map((sample) => (
                            <p key={sample} style={{ margin: '0.25rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{sample}</p>
                          ))}
                          {warning.source_path ? <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>Source: {warning.source_path}</p> : null}
                        </article>
                      ))}
                      {!warnings.length ? <p style={{ color: 'var(--muted)' }}>No candidate warnings are currently reported.</p> : null}
                    </div>
                  </article>
                </div>
              </section>
              <section aria-label="PM Decision Context detail group">
                <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>PM Decision Context</h3>
                <div aria-label="PM Decision Context detail cards">
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
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry decision gate" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>Project Data Entry decision gate</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                PM Lane 239 keeps this warning open until one exact no-live label is returned. This cue does not approve, import, persist, or write source files.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">no-live</span>
                          </div>
                          <p style={{ margin: '0.55rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                            Allowed labels: {PROJECT_DATA_ENTRY_DECISION_LABELS.join('; ')}.
                          </p>
                          <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                            Prior source correction is already applied: {PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL} -&gt; {PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_DESIGNATION}. For this Project Data Entry warning, use REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE if workbook correction is requested.
                          </p>
                          <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                            Admission prerequisites: {PROJECT_DATA_ENTRY_ADMISSION_PREREQUISITES.join('; ')}.
                          </p>
                        </article>
                      ) : null}
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry next input needed" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>Next exact input needed</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                Return exactly one PM Lane 238 label for {PROJECT_DATA_ENTRY_WARNING_CODE}. Do not use paraphrases or the already-applied Ground Resistance source-correction label.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">waiting</span>
                          </div>
                          <ul style={{ margin: '0.65rem 0 0', paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                            {PROJECT_DATA_ENTRY_DECISION_LABEL_DETAILS.map((item) => (
                              <li key={item.label}>
                                <code>{item.label}</code>: {item.meaning}
                              </li>
                            ))}
                          </ul>
                        </article>
                      ) : null}
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry exact reply options" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>Exact reply options</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                Copy exactly one line only. Do not include explanation text, a paraphrase, or {PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL}.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">one-line reply</span>
                          </div>
                          <ul style={{ margin: '0.65rem 0 0', paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                            {PROJECT_DATA_ENTRY_DECISION_LABELS.map((label) => (
                              <li key={label}>
                                <code>{label}</code>
                              </li>
                            ))}
                          </ul>
                        </article>
                      ) : null}
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry outcome routes" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>What each reply does next</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                Route preview only. These outcomes do not run until one exact PM Lane 238 label is returned and a later packet records it.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">route preview</span>
                          </div>
                          <ul style={{ margin: '0.65rem 0 0', paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                            {PROJECT_DATA_ENTRY_DECISION_OUTCOME_ROUTES.map((item) => (
                              <li key={item.label}>
                                <code>{item.label}</code>: {item.route}
                              </li>
                            ))}
                          </ul>
                        </article>
                      ) : null}
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry valid return checklist" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>Valid return checklist</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                Use this only to screen a future reply. It does not choose a label.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">intake rule</span>
                          </div>
                          <ul style={{ margin: '0.65rem 0 0', paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                            {PROJECT_DATA_ENTRY_VALID_RETURN_CHECKLIST.map((item) => (
                              <li key={item.term}>
                                <strong>{item.term}</strong>: {item.detail}
                              </li>
                            ))}
                          </ul>
                        </article>
                      ) : null}
                      {hasProjectDataEntryWarning ? (
                        <article aria-label="Project Data Entry safe no-live continuation" className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                          <div className="status-row" style={{ alignItems: 'start' }}>
                            <div>
                              <p style={{ margin: 0 }}>
                                <strong>Safe no-live continuation</strong>
                              </p>
                              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                                These moves may continue while the exact Project Data Entry label is pending. They do not close the warning gate.
                              </p>
                            </div>
                            <span className="status-pill status-awaiting-values">safe path</span>
                          </div>
                          <ul style={{ margin: '0.65rem 0 0', paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                            {PROJECT_DATA_ENTRY_SAFE_CONTINUATION_MOVES.map((item) => (
                              <li key={item.term}>
                                <strong>{item.term}</strong>: {item.detail}
                              </li>
                            ))}
                          </ul>
                        </article>
                      ) : null}
                      {!decisions.length ? <p style={{ color: 'var(--muted)' }}>No PM decisions are currently reported.</p> : null}
                    </div>
                  </article>
                </div>
              </section>
            </div>
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
          <div aria-label="Admission and approval contract controls">
            <div aria-label="Admission and approval contract groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
              <section aria-label="Admission Shape Context contract group">
                <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Admission Shape Context</h3>
                <div aria-label="Admission Shape Context contract cards">
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
                </div>
              </section>
              <section aria-label="Approval Contract Context contract group">
                <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Approval Contract Context</h3>
                <div aria-label="Approval Contract Context contract cards">
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
              </section>
              <section aria-label="Approval Status Context contract group">
                <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Approval Status Context</h3>
                <div aria-label="Approval Status Context contract cards">
                  <article className="notes-card">
                    <h2>Approval Status Readback</h2>
                    <dl className="contract-panel">
                      <div>
                        <dt>Status</dt>
                        <dd>
                          <span className={`status-pill ${approvalStatusTone(approvalStatus)}`}>
                            {formatLabel(approvalStatus?.classification)}
                          </span>
                        </dd>
                      </div>
                      <div>
                        <dt>Current candidate match</dt>
                        <dd>{formatValue(approvalStatus?.current_candidate_match)}</dd>
                      </div>
                      <div>
                        <dt>Storage</dt>
                        <dd>{approvalStatus?.approval_storage_available === false ? 'unavailable' : 'available'}</dd>
                      </div>
                      <div>
                        <dt>Approval records</dt>
                        <dd>{formatCount(approvalStatus?.approval_record_count_for_candidate)}</dd>
                      </div>
                      <div>
                        <dt>Import authority</dt>
                        <dd>{approvalStatus?.import_authority || 'not_admitted'}</dd>
                      </div>
                      <div>
                        <dt>Read route</dt>
                        <dd>{approvalStatus?.route || '/api/v1/reads/project-import-approval-status'}</dd>
                      </div>
                    </dl>
                    <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                      Status readback only. This panel does not approve, persist, import, assign, schedule, change status, or mutate production state.
                    </p>
                  </article>
                </div>
              </section>
            </div>
          </div>
        </details>

        <details open aria-label="Local review checklist" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Review Checklist</h2>
            <span className="status-pill status-configured">
              {formatCount(checklistCheckedCount)} of {formatCount(REVIEW_CHECKLIST_ITEMS.length)}
            </span>
          </summary>
          <div aria-label="Local review checklist controls">
            <div aria-label="Review checklist controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local review prep only. Checking these items does not approve, persist, import, assign, schedule, change status, or mutate production state.
              </p>
              <div aria-label="Review checklist groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {REVIEW_CHECKLIST_GROUPS.map((group) => (
                  <section key={group.id} aria-label={`${group.label} checklist group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} checklist items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {REVIEW_CHECKLIST_ITEMS.filter((item) => group.itemIds.includes(item.id)).map((item) => (
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
                  </section>
                ))}
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearReviewChecklist} disabled={!checklistCheckedCount}>
                  Clear checklist
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local approval decision draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Approval Decision Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </summary>
          <div aria-label="Local approval decision draft controls">
            <div aria-label="Approval draft controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Draft the future approval decision and notes for the PM brief only. This does not approve, persist, import, assign, schedule, change status, or mutate production state.
              </p>
              <div aria-label="Approval decision draft groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                <section aria-label="Decision Value Context approval draft group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Decision Value Context</h3>
                  <div aria-label="Decision Value Context approval draft items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                  </div>
                </section>
                <section aria-label="Review Notes Context approval draft group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Review Notes Context</h3>
                  <div aria-label="Review Notes Context approval draft items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                </section>
                <section aria-label="Local Attestation Context approval draft group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Local Attestation Context</h3>
                  <div aria-label="Local Attestation Context approval draft items" style={{ display: 'grid', gap: '0.75rem' }}>
                    <label className="card" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.75rem', padding: '0.85rem', boxShadow: 'none', cursor: 'pointer' }}>
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
                  </div>
                </section>
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearApprovalDraft} disabled={!approvalDraftHasContent}>
                  Clear decision draft
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Included in the PM brief only when exported from this browser.</span>
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local approval submission dry run" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Approval Submission Dry Run</h2>
            <span className="status-pill status-awaiting-values">
              {approvalDryRunReadinessSummary(approvalDryRunReadinessCount)}
            </span>
          </summary>
          <div aria-label="Local approval submission dry run controls">
            <div aria-label="Approval dry run controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Builds the future approval POST envelope in this browser for review only. It does not call live services, perform hosted writes, create an approval record, import project rows, assign work, schedule work, change status, or mutate production state.
              </p>
              <div aria-label="Approval dry run groups" style={{ display: 'grid', gap: '0.85rem', marginTop: '0.85rem' }}>
                <section aria-label="Dry Run Readiness Context approval dry run group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Dry Run Readiness Context</h3>
                  <div aria-label="Approval dry run readiness checkpoint" className="notes-grid">
                    {approvalDryRunReadiness.map((item) => (
                      <article key={item.id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                        <div className="status-row" style={{ alignItems: 'flex-start' }}>
                          <h2 style={{ margin: 0 }}>{item.title}</h2>
                          <span className={`status-pill ${approvalDryRunReadinessTone(item.status)}`}>
                            {formatLabel(item.status)}
                          </span>
                        </div>
                        <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{item.detail}</p>
                      </article>
                    ))}
                  </div>
                </section>
                <section aria-label="Future Request Boundary Context approval dry run group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Future Request Boundary Context</h3>
                  <div aria-label="Approval dry run future request boundary cards" className="notes-grid">
                    <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                      <h2>Future route</h2>
                      <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>{futureRoute}</p>
                    </article>
                    <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                      <h2>Local draft gate</h2>
                      <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                        {approvalDraft.decision && approvalDraft.review_notes.trim() && approvalDraft.local_attestation
                          ? 'Decision value, review notes, and local-only attestation are present.'
                          : 'Decision value, review notes, and local-only attestation are needed before this dry run is useful packet context.'}
                      </p>
                    </article>
                    <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                      <h2>Write boundary</h2>
                      <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                        Live approval POST, first approval-row creation, and project import remain blocked until a separate explicit admission.
                      </p>
                    </article>
                  </div>
                </section>
                <section aria-label="Local Artifact Actions Context approval dry run group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Local Artifact Actions Context</h3>
                  <div aria-label="Approval dry run local artifact actions">
                    <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                      <button className="btn btn-outline" onClick={buildApprovalDryRun} disabled={!packet}>
                        Build Local Approval Dry Run
                      </button>
                      <button className="btn btn-outline" onClick={exportApprovalDryRunEnvelope} disabled={!packet}>
                        Export Dry Run Envelope
                      </button>
                      <button className="btn btn-outline" onClick={exportApprovalDryRunReadiness} disabled={!packet}>
                        Export Readiness Checkpoint
                      </button>
                      <button className="btn btn-outline" onClick={exportApprovalReviewBundle} disabled={!packet}>
                        Export Review Bundle
                      </button>
                      <button className="btn btn-outline" onClick={exportApprovalLiveGatePreflight} disabled={!packet}>
                        Export Live Gate Preflight
                      </button>
                      <button className="btn btn-outline" onClick={clearApprovalDryRun} disabled={!approvalDryRunPreview && !approvalDryRunStatus}>
                        Clear dry run
                      </button>
                      <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>The generated envelope stays local to this browser or downloads as a review artifact and sends no request.</span>
                    </div>
                    {approvalDryRunStatus ? <p role="status" style={{ color: 'var(--muted)', lineHeight: 1.55 }}>{approvalDryRunStatus}</p> : null}
                    {approvalDryRunPreview ? (
                      <pre data-testid="local-approval-dry-run-preview" style={{ marginTop: '0.85rem', maxHeight: '24rem', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                        {approvalDryRunPreview}
                      </pre>
                    ) : (
                      <p style={{ color: 'var(--muted)', lineHeight: 1.55 }}>No local dry run has been built for this browser session.</p>
                    )}
                  </div>
                </section>
              </div>
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
          <div aria-label="Local executor closeout intake controls">
            <div aria-label="Executor closeout controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local audit prep for external executor returns. Checking these items does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state.
              </p>
              <div aria-label="Local executor closeout intake groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {CLOSEOUT_CHECKLIST_GROUPS.map((group) => (
                  <section key={group.id} aria-label={`${group.label} executor closeout group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} executor closeout items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {CLOSEOUT_CHECKLIST_ITEMS.filter((item) => group.itemIds.includes(item.id)).map((item) => (
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
                  </section>
                ))}
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearCloseoutChecklist} disabled={!closeoutCheckedCount}>
                  Clear closeout intake
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
              </div>
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
          <div aria-label="Local field readiness checklist controls">
            <div aria-label="Field readiness controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local prep evidence for PM, lead, and field review conversations. Checking these items does not authorize work, approve, persist, import, assign, schedule, change status, or mutate production state.
              </p>
              <div aria-label="Local field readiness checklist groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {FIELD_READINESS_CHECKLIST_GROUPS.map((group) => (
                  <section key={group.id} aria-label={`${group.label} field readiness group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} field readiness items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {FIELD_READINESS_CHECKLIST_ITEMS.filter((item) => group.itemIds.includes(item.id)).map((item) => (
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
                  </section>
                ))}
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearFieldReadinessChecklist} disabled={!fieldReadinessCheckedCount}>
                  Clear field readiness
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only.</span>
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local field questions draft" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Questions Draft</h2>
            <span className="status-pill status-awaiting-values">local only</span>
          </summary>
          <div aria-label="Local field questions draft controls">
            <div aria-label="Field questions controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local question notes for PM, lead, and field prep conversations. These notes do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes.
              </p>
              <div aria-label="Local field questions draft groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                <section aria-label="Source and Site Questions field questions group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Source and Site Questions</h3>
                  <div aria-label="Source and Site Questions field question items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                  </div>
                  {hasProjectDataEntryWarning ? (
                    <article aria-label="No-live source and resource question preparation cue" className="card" style={{ display: 'grid', gap: '0.55rem', padding: '0.85rem', boxShadow: 'none', marginTop: '0.75rem' }}>
                      <div className="status-row" style={{ alignItems: 'start' }}>
                        <div>
                          <p style={{ margin: 0 }}>
                            <strong>No-live source and resource question prep</strong>
                          </p>
                          <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                            Prepare PM or lead questions about source records, drawings, workbook rows, crew, equipment, capability coverage, material, or staging context. This does not close the Data Entry warning gate.
                          </p>
                        </div>
                        <span className="status-pill status-awaiting-values">question prep</span>
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '1.15rem', color: 'var(--muted)', lineHeight: 1.55 }}>
                        <li>Equipment inventory context: {formatCount(summary.equipment_inventory_count)} rows available for question shaping only.</li>
                        <li>Technician capability context: {formatCount(summary.capability_count)} rows available for coverage questions only.</li>
                        {PROJECT_SOURCE_RESOURCE_QUESTION_PREP_CUES.map((item) => (
                          <li key={item.term}>
                            <strong>{item.term}</strong>: {item.detail}
                          </li>
                        ))}
                      </ul>
                      <p style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
                        No live source access, source writeback, resource assignment, schedule/status change, task creation, field authorization, approval, import, or business-state mutation is granted.
                      </p>
                    </article>
                  ) : null}
                </section>
                <section aria-label="Crew Material and Staging Questions field questions group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Crew Material and Staging Questions</h3>
                  <div aria-label="Crew Material and Staging Questions field question items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                  </div>
                </section>
                <section aria-label="Customer Constraints and PM Follow-up field questions group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Customer Constraints and PM Follow-up</h3>
                  <div aria-label="Customer Constraints and PM Follow-up field question items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                </section>
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearFieldQuestionsDraft} disabled={!fieldQuestionsDraftHasContent}>
                  Clear field questions
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only and included in local exports.</span>
              </div>
            </div>
          </div>
        </details>

        <details id="field-prep" open aria-label="Local field prep queue" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Prep Queue</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Local field prep queue controls">
            <div aria-label="Field prep queue controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Derived queue for field-prep conversations. It translates local field questions and readiness evidence into practical next moves without creating tasks, issues, assignments, schedules, status updates, approval records, import rows, or production writes.
              </p>
              <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                {formatCount(completeFieldPrepQueueCount)} complete / {formatCount(nextFieldPrepQueueCount)} next / {formatCount(blockedFieldPrepQueueCount)} blocked
              </p>
              <div aria-label="Local field prep queue groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {fieldPrepQueueGroups.map((group) => (
                  <section key={group.id} aria-label={`${group.label} field prep queue group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} field prep queue items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {group.items.map((item) => (
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
                ))}
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local field prep coverage snapshot" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Prep Coverage Snapshot</h2>
            <span className="status-pill status-awaiting-values">derived</span>
          </summary>
          <div aria-label="Local field prep coverage snapshot controls">
            <div aria-label="Field prep coverage controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local coverage snapshot derived from existing local prep state. It shows what field-prep context is covered, partial, open, or blocked without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.
              </p>
              <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                {fieldPrepCoverageSummary(fieldPrepCoverageCount)}
              </p>
              <div aria-label="Local field prep coverage snapshot groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {fieldPrepCoverageSnapshotGroups.map((group) => (
                  <section key={group.id} aria-label={`${group.label} field prep coverage group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} field prep coverage items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {group.items.map((item) => (
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
                ))}
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local field prep conversation agenda" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Prep Conversation Agenda</h2>
            <span className="status-pill status-awaiting-values">derived</span>
          </summary>
          <div aria-label="Local field prep conversation agenda controls">
            <div aria-label="Field prep agenda controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local agenda derived from the coverage snapshot. It turns covered, partial, open, and blocked prep areas into conversation context, ask, confirm, and blocked agenda items without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes.
              </p>
              <p style={{ margin: '0.6rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                {fieldPrepAgendaSummary(fieldPrepAgendaCount)}
              </p>
              <div aria-label="Local field prep conversation agenda groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {fieldPrepConversationAgendaGroups.map((group) => (
                  <section key={group.id} aria-label={`${group.label} field prep agenda group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} field prep agenda items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {group.items.map((item) => (
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
                ))}
              </div>
            </div>
          </div>
        </details>

        <details open aria-label="Local field observation scratchpad" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Local Field Observation Scratchpad</h2>
            <span className="status-pill status-awaiting-values">browser-local</span>
          </summary>
          <div aria-label="Local field observation scratchpad controls">
            <div aria-label="Field observation scratchpad controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Browser-local observation notes for PM, lead, and field conversations. These notes do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes.
              </p>
              <div aria-label="Local field observation scratchpad groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                <section aria-label="Source And Area Observation field observation group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Source And Area Observation</h3>
                  <div aria-label="Source And Area Observation field observation items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                  </div>
                </section>
                <section aria-label="Access And Resource Observation field observation group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Access And Resource Observation</h3>
                  <div aria-label="Access And Resource Observation field observation items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                  </div>
                </section>
                <section aria-label="PM Follow-up And Authority Boundary field observation group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>PM Follow-up And Authority Boundary</h3>
                  <div aria-label="PM Follow-up And Authority Boundary field observation items" style={{ display: 'grid', gap: '0.75rem' }}>
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
                </section>
              </div>
              <div className="pm-review-link-row pm-review-link-row-start" style={{ alignItems: 'center' }}>
                <button className="btn btn-outline" onClick={clearFieldObservationScratchpad} disabled={!fieldObservationScratchpadHasContent}>
                  Clear field observations
                </button>
                <span style={{ color: 'var(--muted)', lineHeight: 1.55 }}>Retained in this browser for the current candidate only and included in local field-prep exports.</span>
              </div>
            </div>
          </div>
        </details>

          </details>
          <details open aria-label="Authority boundary detail panels" style={{ display: 'grid', gap: '0.75rem' }}>
            <summary style={{ cursor: 'pointer' }}>
              <h2 style={{ display: 'inline', margin: 0 }}>Authority Boundary Detail</h2>
            </summary>

        <details open id="approval-readiness" aria-label="Approval persistence readiness gates" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <summary className="status-row" style={{ cursor: 'pointer' }}>
            <h2 style={{ margin: 0 }}>Approval Persistence Readiness</h2>
            <span className="status-pill status-awaiting-values">
              {formatCount(readyPersistenceGateCount)} of {formatCount(persistenceReadinessGates.length)} ready
            </span>
          </summary>
          <div aria-label="Approval persistence readiness body controls">
            <div aria-label="Approval persistence readiness controls">
              <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                Local readiness map for the future approval-persistence packet. It reflects review context and blockers only; it does not approve, persist, import, assign, schedule, change status, or mutate production state.
              </p>
              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                PM Lane 138 closed the hosted schema gate with zero approval rows, and the bounded Supabase MCP read path is restored. Browser approval submission and import mutation remain blocked until later packets explicitly admit them.
              </p>
              <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
                <article className="notes-card accent-card">
                  <h2>Approval Status Readback</h2>
                  <dl className="contract-panel">
                    <div>
                      <dt>Current status</dt>
                      <dd>{formatLabel(approvalStatus?.classification)}</dd>
                    </div>
                    <div>
                      <dt>Storage source</dt>
                      <dd>{approvalStatus?.source || storagePlan?.recommended_table || 'not reported'}</dd>
                    </div>
                    <div>
                      <dt>Audit dependency</dt>
                      <dd>{approvalStatus?.audit_log_used_for_current_status ? 'audit log used' : 'approval table readback'}</dd>
                    </div>
                    <div>
                      <dt>Boundary</dt>
                      <dd>{approvalStatus?.import_authority || 'not_admitted'}</dd>
                    </div>
                  </dl>
                  <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    Readback is informational only; project import remains blocked until a later packet explicitly admits that write path.
                  </p>
                </article>
              </div>
              <div aria-label="Approval persistence readiness gate groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                {persistenceReadinessGateGroups.map((group) => (
                  <section key={group.id} aria-label={`${group.label} approval persistence readiness group`}>
                    <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>{group.label}</h3>
                    <div aria-label={`${group.label} approval readiness items`} style={{ display: 'grid', gap: '0.75rem' }}>
                      {group.items.map((gate) => (
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
                ))}
              </div>
            </div>
          </div>
        </details>

        <details open id="guardrails" aria-label="Current PM next actions and guardrails" style={{ marginBottom: '1rem' }}>
          <summary style={{ cursor: 'pointer' }}>
            <h2 style={{ display: 'inline', margin: 0 }}>Current PM Next Actions and Guardrails</h2>
          </summary>
          <div aria-label="Current PM guardrails body controls">
            <div aria-label="Current PM guardrails controls">
              <div aria-label="Current PM guardrail groups" className="notes-grid" style={{ marginTop: '0.85rem' }}>
                <section aria-label="Current Review Actions guardrail group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Current Review Actions</h3>
                  <div aria-label="Current Review Actions guardrail items" style={{ display: 'grid', gap: '0.75rem' }}>
                    <article className="notes-card">
                      <h2>Current PM Next Actions</h2>
                      <ol>
                        <li>Review candidate exceptions, source freshness, and required human decisions.</li>
                        <li>Confirm the Project Miner source files have not changed before any future approval packet is used.</li>
                        <li>Treat hosted schema, hosted readback, and bounded Supabase read proof as green, with approval rows still at zero.</li>
                        <li>Keep browser approval submission and project import blocked until later packets explicitly admit those writes.</li>
                      </ol>
                    </article>
                    {hasProjectDataEntryWarning ? (
                      <article aria-label="Current open Project Data Entry decision" className="notes-card accent-card">
                        <h2>Current Open PM Decision</h2>
                        <p>
                          PROJECT_DATA_ENTRY_FORMULA_ERRORS remains open. Return exactly one PM Lane 238 label from the Project Data Entry exact reply options card; do not use explanation text, a paraphrase, or {PROJECT_MINER_RESOLVED_SOURCE_CORRECTION_LABEL}.
                        </p>
                        <p style={{ marginBottom: 0 }}>
                          No-live boundary: this cue does not accept the warning, approve the candidate, create an approval row, import project rows, write source files, or call a hosted mutation.
                        </p>
                      </article>
                    ) : null}
                  </div>
                </section>
                <section aria-label="Blocked Write Guardrails guardrail group">
                  <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.65rem' }}>Blocked Write Guardrails</h3>
                  <div aria-label="Blocked Write Guardrails guardrail items" style={{ display: 'grid', gap: '0.75rem' }}>
                    <article className="notes-card accent-card">
                      <h2>Not Allowed Now</h2>
                      <ul>
                        {(notAllowed.length ? notAllowed : ['write_supabase', 'persist_approval_record', 'import_project_rows', 'run_workbook_macros', 'assign_work', 'mutate_schedule', 'change_status']).map((item) => (
                          <li key={item}>{formatLabel(item)}</li>
                        ))}
                      </ul>
                    </article>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </details>
          </details>
        </section>
      </section>
    </main>
  )
}
