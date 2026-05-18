'use client'

import Link from 'next/link'
import * as React from 'react'

type ApprovalRecordContract = {
  record_type?: string
  storage_authority?: string
  required_fields?: string[]
  permitted_decisions?: string[]
  minimum_expected_values?: Record<string, unknown>
  operator_attestation?: string
}

type HumanAcceptancePolicy = {
  accepted_no_go_overrides_field?: string
  required_human_acceptance_check_ids?: string[]
  non_overridable_check_ids?: string[]
  policy?: string
}

type ValidationCheck = {
  check_id?: string
  fields?: string[]
  permitted_decisions?: string[]
  failure_action?: string
}

type FutureMutationContract = {
  proposed_entity_type?: string
  proposed_action?: string
  proposed_route?: string
  current_authority?: string
  idempotency_policy?: string
}

type ApprovalContract = {
  approval_contract_id?: string
  approval_contract_version?: string
  candidate_id?: string
  candidate_version?: string
  readiness_status?: string
  mutation_authority?: string
  persistence_authority?: string
  storage_decision?: string
  approval_record_contract?: ApprovalRecordContract
  required_fields?: string[]
  permitted_decisions?: string[]
  minimum_expected_values?: Record<string, unknown>
  candidate_identity?: Record<string, unknown>
  human_acceptance_policy?: HumanAcceptancePolicy
  decision_payload_template?: Record<string, unknown>
  validation_matrix?: ValidationCheck[]
  future_mutation_contract?: FutureMutationContract
  not_allowed_now?: string[]
}

type RecommendedColumn = {
  name?: string
  type?: string
  required?: boolean
  source?: string
  allowed_values?: string[]
}

type RecommendedConstraint = {
  constraint_id?: string
  applies_to?: string[]
  rule?: string
  allowed_values?: string[]
}

type RejectedStorageOption = {
  option?: string
  reason?: string
}

type ApprovalStoragePlan = {
  storage_plan_id?: string
  storage_plan_version?: string
  candidate_id?: string
  candidate_version?: string
  mutation_authority?: string
  persistence_authority?: string
  selected_storage_decision?: string
  recommended_schema?: string
  recommended_table?: string
  recommended_entity_type?: string
  recommended_route?: string
  contract_dependency?: Record<string, unknown>
  record_lifecycle?: Record<string, string>
  recommended_columns?: RecommendedColumn[]
  recommended_constraints?: RecommendedConstraint[]
  adapter_requirements?: string[]
  readback_requirements?: string[]
  rejected_storage_options?: RejectedStorageOption[]
  future_admission_sequence?: string[]
  not_allowed_now?: string[]
}

type ApprovalReadinessPacket = {
  contract: ApprovalContract
  storagePlan: ApprovalStoragePlan
}

type ApprovalPreviewTaskGroup = {
  group_id?: string
  title?: string
  designation?: string
  apparatus_count?: number
  planned_hours?: number
}

type ApprovalPreviewManualTaskShaping = {
  summary?: {
    group_count?: number
    regrouped_apparatus_count?: number
    designation_override_count?: number
  }
  groups?: ApprovalPreviewTaskGroup[]
}

type CandidateApprovalPreviewArtifact = {
  preview_kind?: string
  preview_version?: string
  generated_locally_at?: string
  storage?: string
  local_review_evidence?: {
    review_notes?: string | null
    manual_task_shaping?: ApprovalPreviewManualTaskShaping | null
  }
  downstream_review_context?: {
    contract_role?: string
  }
}

const { useCallback, useEffect, useMemo, useState } = React

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const READS_BASE = `${API_BASE}/reads`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }

function makeToken() {
  return `Bearer ${btoa(JSON.stringify(PM_ACTOR))}`
}

async function readApprovalReadiness(): Promise<ApprovalReadinessPacket> {
  const headers = { Authorization: makeToken() }
  const [contractResponse, storagePlanResponse] = await Promise.all([
    fetch(`${READS_BASE}/project-import-approval-contract`, { headers }),
    fetch(`${READS_BASE}/project-import-approval-storage-plan`, { headers }),
  ])

  if (!contractResponse.ok) {
    throw new Error('Failed to read PM import approval contract')
  }

  if (!storagePlanResponse.ok) {
    throw new Error('Failed to read PM import approval storage plan')
  }

  return {
    contract: (await contractResponse.json()) as ApprovalContract,
    storagePlan: (await storagePlanResponse.json()) as ApprovalStoragePlan,
  }
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

function authorityTone(value?: string) {
  if (!value || value.includes('not_admitted')) return 'status-deferred'
  if (value.includes('only')) return 'status-awaiting-values'
  return 'status-backend-routed'
}

function renderKeyValueRows(values?: Record<string, unknown>) {
  const entries = Object.entries(values || {})
  if (!entries.length) {
    return (
      <div>
        <dt>Values</dt>
        <dd>none reported</dd>
      </div>
    )
  }

  return entries.map(([key, value]) => (
    <div key={key}>
      <dt>{formatLabel(key)}</dt>
      <dd>{formatValue(value)}</dd>
    </div>
  ))
}

function uniqueGuardrails(contractItems?: string[], storageItems?: string[]) {
  return Array.from(new Set([...(contractItems || []), ...(storageItems || [])])).sort()
}

function approvalPreviewStorageKey(candidateId?: string | null) {
  return candidateId ? `pm-import-candidate-approval-preview:${candidateId}` : null
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

export default function PmImportApprovalReadinessPage() {
  const [packet, setPacket] = useState<ApprovalReadinessPacket | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [localPreview, setLocalPreview] = useState<CandidateApprovalPreviewArtifact | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setPacket(await readApprovalReadiness())
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

  const contract = packet?.contract
  const storagePlan = packet?.storagePlan
  const approvalRecordContract = contract?.approval_record_contract || {}
  const humanPolicy = contract?.human_acceptance_policy || {}
  const futureMutation = contract?.future_mutation_contract || {}
  const recordLifecycle = storagePlan?.record_lifecycle || {}
  const previewCandidateId = contract?.candidate_id || storagePlan?.candidate_id || null
  const notAllowed = useMemo(
    () => uniqueGuardrails(contract?.not_allowed_now, storagePlan?.not_allowed_now),
    [contract?.not_allowed_now, storagePlan?.not_allowed_now],
  )
  const previewStorageKey = previewCandidateId ? approvalPreviewStorageKey(previewCandidateId) : null
  const previewManualTaskShaping = localPreview?.local_review_evidence?.manual_task_shaping || null

  useEffect(() => {
    if (!previewStorageKey || typeof window === 'undefined') {
      setLocalPreview(null)
      return
    }

    setLocalPreview(parseApprovalPreview(window.localStorage.getItem(previewStorageKey)))
  }, [previewStorageKey])

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Import Approval Readiness</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Review the approval gate before it can persist.</h1>
            <p className="lede">
              This route shows the current approval contract and storage decision side by side. It does not approve, persist, import, assign, schedule, change status, or mutate production state.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Contract read seam</dt>
              <dd>/api/v1/reads/project-import-approval-contract</dd>
            </div>
            <div>
              <dt>Storage read seam</dt>
              <dd>/api/v1/reads/project-import-approval-storage-plan</dd>
            </div>
            <div>
              <dt>Future route</dt>
              <dd>{storagePlan?.recommended_route || futureMutation.proposed_route || 'not admitted'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Read seams</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>{loading ? 'Loading approval readiness packet.' : 'Approval readiness is read-only and pre-persistence.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Contract authority</h2>
            <span className={`status-pill ${authorityTone(contract?.persistence_authority)}`}>{contract?.persistence_authority || 'not_admitted'}</span>
          </div>
          <p>{contract?.approval_contract_version || 'Waiting for approval contract version.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Storage authority</h2>
            <span className={`status-pill ${authorityTone(storagePlan?.persistence_authority)}`}>{storagePlan?.persistence_authority || 'not_admitted'}</span>
          </div>
          <p>{storagePlan?.storage_plan_version || 'Waiting for storage plan version.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Recommended table</h2>
            <span className="status-pill status-awaiting-values">future</span>
          </div>
          <p>{storagePlan?.recommended_table || 'No storage table decision is available.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Staged Review Context</h2>
            <span className={`status-pill ${localPreview ? 'status-configured' : 'status-deferred'}`}>{localPreview ? 'staged' : 'not staged'}</span>
          </div>
          <p>
            {localPreview?.generated_locally_at
              ? `Import candidate staged browser-local approval preview context at ${localPreview.generated_locally_at}.`
              : 'Use Import candidate export to stage browser-local PM review context before checking downstream approval readiness.'}
          </p>
        </article>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Approval Readiness Packet</h2>
            <p>
              Use this page to inspect the approval packet shape and storage plan before a later packet admits any PM approval persistence.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/pm-review/import-intake">Intake workbench</Link>
            <Link href="/pm-review/import-candidate">Import candidate</Link>
            <Link href="/pm-review/import-admission-plan">Admission plan</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

        <section className="notes-grid" style={{ marginBottom: '1rem' }}>
          <article className="notes-card">
            <h2>Contract Identity</h2>
            <dl className="contract-panel">
              <div>
                <dt>Contract</dt>
                <dd>{contract?.approval_contract_id || 'waiting for approval contract'}</dd>
              </div>
              <div>
                <dt>Candidate</dt>
                <dd>{contract?.candidate_id || storagePlan?.candidate_id || 'unknown'}</dd>
              </div>
              <div>
                <dt>Candidate version</dt>
                <dd>{contract?.candidate_version || storagePlan?.candidate_version || 'unknown'}</dd>
              </div>
              <div>
                <dt>Mutation authority</dt>
                <dd>{contract?.mutation_authority || 'not_admitted'}</dd>
              </div>
            </dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Storage Decision</h2>
            <dl className="contract-panel">
              <div>
                <dt>Storage plan</dt>
                <dd>{storagePlan?.storage_plan_id || 'waiting for storage plan'}</dd>
              </div>
              <div>
                <dt>Decision</dt>
                <dd>{formatLabel(storagePlan?.selected_storage_decision)}</dd>
              </div>
              <div>
                <dt>Entity</dt>
                <dd>{storagePlan?.recommended_entity_type || 'unknown'}</dd>
              </div>
              <div>
                <dt>Route</dt>
                <dd>{storagePlan?.recommended_route || 'not admitted'}</dd>
              </div>
            </dl>
          </article>
        </section>

        <section aria-label="Candidate review context" className="notes-grid pm-section-spaced">
          <article className="notes-card pm-review-context-card">
            <h2>Candidate Review Context</h2>
            <p className="pm-copy-muted pm-copy-main">
              {localPreview
                ? 'Import candidate exported browser-local PM review context into this governed approval-readiness gate. No network request or persistence path was used.'
                : 'Export Approval Preview JSON from Import candidate to stage PM review notes and manual task shaping here as browser-local review context only.'}
            </p>
            <dl className="contract-panel">
              <div>
                <dt>Preview kind</dt>
                <dd>{localPreview?.preview_kind || 'not staged'}</dd>
              </div>
              <div>
                <dt>Generated locally</dt>
                <dd>{localPreview?.generated_locally_at || 'not yet exported from Import candidate'}</dd>
              </div>
              <div>
                <dt>Storage</dt>
                <dd>{localPreview?.storage || 'browser local only after export'}</dd>
              </div>
              <div>
                <dt>Contract role</dt>
                <dd>{localPreview?.downstream_review_context?.contract_role || 'No local preview contract is currently staged.'}</dd>
              </div>
            </dl>
          </article>
          <article className="notes-card">
            <h2>Manual Task Shaping Context</h2>
            {localPreview ? (
              <>
                <p className="pm-copy-muted pm-copy-main">
                  {localPreview.local_review_evidence?.review_notes || 'No PM review notes were included in the staged approval preview.'}
                </p>
                <dl className="contract-panel">
                  <div>
                    <dt>Local groups</dt>
                    <dd>{formatValue(previewManualTaskShaping?.summary?.group_count)}</dd>
                  </div>
                  <div>
                    <dt>Regrouped apparatus</dt>
                    <dd>{formatValue(previewManualTaskShaping?.summary?.regrouped_apparatus_count)}</dd>
                  </div>
                  <div>
                    <dt>Designation overrides</dt>
                    <dd>{formatValue(previewManualTaskShaping?.summary?.designation_override_count)}</dd>
                  </div>
                </dl>
                <ul>
                  {(previewManualTaskShaping?.groups || []).map((group) => (
                    <li key={group.group_id || group.title}>
                      <strong>{group.title || 'Untitled local task'}</strong>: {formatValue(group.apparatus_count)} apparatus, {formatValue(group.planned_hours)} hours, {group.designation || 'no designation'}
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="pm-copy-muted pm-copy-main">
                No manual task shaping preview is staged yet. Use the Import candidate route to export Approval Preview JSON before reviewing downstream approval context here.
              </p>
            )}
          </article>
        </section>

        <section aria-label="Approval contract detail" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Approval Contract Detail</h2>
            <span className="status-pill status-awaiting-values">{approvalRecordContract.storage_authority || contract?.persistence_authority || 'not_admitted'}</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {approvalRecordContract.operator_attestation || 'Approval record persistence is not admitted.'}
          </p>
          <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Required Fields</h3>
              <ul>
                {(contract?.required_fields || approvalRecordContract.required_fields || []).map((field) => (
                  <li key={field}>{formatLabel(field)}</li>
                ))}
              </ul>
            </article>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Permitted Decisions</h3>
              <ul>
                {(contract?.permitted_decisions || approvalRecordContract.permitted_decisions || []).map((decision) => (
                  <li key={decision}>{formatLabel(decision)}</li>
                ))}
              </ul>
            </article>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Expected Values</h3>
              <dl className="contract-panel">{renderKeyValueRows(contract?.minimum_expected_values || approvalRecordContract.minimum_expected_values)}</dl>
            </article>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Human Acceptance Policy</h3>
              <p style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>{humanPolicy.policy || 'No human acceptance policy is currently reported.'}</p>
              <dl className="contract-panel" style={{ marginTop: '0.75rem' }}>
                <div>
                  <dt>Required acceptance</dt>
                  <dd>{formatValue(humanPolicy.required_human_acceptance_check_ids)}</dd>
                </div>
                <div>
                  <dt>Non-overridable</dt>
                  <dd>{formatValue(humanPolicy.non_overridable_check_ids)}</dd>
                </div>
              </dl>
            </article>
          </div>
        </section>

        <section aria-label="Decision payload template" className="notes-grid" style={{ marginBottom: '1rem' }}>
          <article className="notes-card">
            <h2>Decision Payload Template</h2>
            <dl className="contract-panel">{renderKeyValueRows(contract?.decision_payload_template)}</dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Future Mutation Contract</h2>
            <dl className="contract-panel">{renderKeyValueRows(futureMutation as Record<string, unknown>)}</dl>
          </article>
        </section>

        <section aria-label="Approval validation matrix" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Validation Matrix</h2>
            <span className="status-pill status-configured">{formatValue(contract?.validation_matrix?.length || 0)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {(contract?.validation_matrix || []).map((check) => (
              <article key={check.check_id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <p style={{ margin: 0 }}>
                  <strong>{formatLabel(check.check_id)}</strong>
                </p>
                <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                  Fields: {formatValue(check.fields || check.permitted_decisions)}.
                </p>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>{check.failure_action}</p>
              </article>
            ))}
            {!(contract?.validation_matrix || []).length ? <p style={{ color: 'var(--muted)' }}>No validation checks are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Approval storage plan" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Approval Storage Plan</h2>
            <span className="status-pill status-awaiting-values">{storagePlan?.persistence_authority || 'not_admitted'}</span>
          </div>
          <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Record Lifecycle</h3>
              <dl className="contract-panel">{renderKeyValueRows(recordLifecycle as Record<string, unknown>)}</dl>
            </article>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Adapter Requirements</h3>
              <ul>
                {(storagePlan?.adapter_requirements || []).map((requirement) => (
                  <li key={requirement}>{requirement}</li>
                ))}
              </ul>
            </article>
          </div>
        </section>

        <section aria-label="Recommended approval columns" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Recommended Columns</h2>
            <span className="status-pill status-configured">{formatValue(storagePlan?.recommended_columns?.length || 0)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {(storagePlan?.recommended_columns || []).map((column) => (
              <article key={column.name} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ justifyContent: 'flex-start' }}>
                  <strong>{column.name || 'unknown column'}</strong>
                  <span className="status-pill status-backend-routed">{column.type || 'unknown'}</span>
                  {column.required ? <span className="status-pill status-configured">required</span> : null}
                </div>
                <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>{column.source || 'No source is currently reported.'}</p>
                {column.allowed_values?.length ? (
                  <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>Allowed values: {formatValue(column.allowed_values)}</p>
                ) : null}
              </article>
            ))}
            {!(storagePlan?.recommended_columns || []).length ? <p style={{ color: 'var(--muted)' }}>No recommended columns are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Approval storage constraints and rejected options" className="notes-grid" style={{ marginBottom: '1rem' }}>
          <article className="notes-card">
            <h2>Recommended Constraints</h2>
            <ul>
              {(storagePlan?.recommended_constraints || []).map((constraint) => (
                <li key={constraint.constraint_id}>
                  <strong>{formatLabel(constraint.constraint_id)}</strong>: {constraint.rule || 'No rule reported.'}
                </li>
              ))}
            </ul>
          </article>
          <article className="notes-card accent-card">
            <h2>Rejected Storage Options</h2>
            <ul>
              {(storagePlan?.rejected_storage_options || []).map((option) => (
                <li key={option.option}>
                  <strong>{formatLabel(option.option)}</strong>: {option.reason || 'No reason reported.'}
                </li>
              ))}
            </ul>
          </article>
        </section>

        <section aria-label="Future admission sequence and guardrails" className="notes-grid">
          <article className="notes-card">
            <h2>Future Admission Sequence</h2>
            <ol>
              {(storagePlan?.future_admission_sequence || []).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </article>
          <article className="notes-card accent-card">
            <h2>Not Allowed Now</h2>
            <ul>
              {notAllowed.map((item) => (
                <li key={item}>{formatLabel(item)}</li>
              ))}
            </ul>
          </article>
        </section>
      </section>
    </main>
  )
}
