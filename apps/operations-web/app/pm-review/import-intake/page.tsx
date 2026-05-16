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

export default function ProjectMinerIntakeWorkbenchPage() {
  const [packet, setPacket] = useState<IntakeWorkbenchPacket | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)

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
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

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
