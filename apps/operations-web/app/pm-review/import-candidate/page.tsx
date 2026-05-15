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

type CandidateDecision = {
  decision_id?: string
  severity?: string
  prompt?: string
  recommended_action?: string
  warning_code?: string
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
  apparatus_candidates?: Array<{
    candidate_id?: string
    display_name?: string | null
    source_row?: number | null
    source_line_id?: string | null
  }>
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

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/_/g, ' ')
}

function formatCount(value?: number) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString() : '0'
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

export default function PmImportCandidatePage() {
  const [candidate, setCandidate] = useState<CandidatePayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)

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
  const decisions = candidate?.human_decisions || []
  const workpackages = candidate?.workpackages || []
  const sourceBundle = candidate?.source_bundle || {}
  const notAllowed = candidate?.review_guidance?.not_allowed_now || []
  const allowedNow = candidate?.review_guidance?.allowed_now || []
  const readinessLabel = useMemo(() => {
    if (!online) return 'offline'
    if ((summary.blocker_count || 0) > 0) return 'blocked'
    if ((summary.warning_count || 0) > 0) return 'needs review'
    return 'ready for review'
  }, [online, summary.blocker_count, summary.warning_count])

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

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
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
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

        <section className="status-grid status-grid-wide" aria-label="Import candidate summary" style={{ marginBottom: '1rem' }}>
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
        </section>

        <section aria-label="Required decisions" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Required Decisions</h2>
            <span className="status-pill status-awaiting-values">{formatCount(decisions.length)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {decisions.map((decision) => (
              <article key={decision.decision_id || decision.prompt} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ justifyContent: 'flex-start' }}>
                  <span className={`status-pill ${warningTone(decision.severity)}`}>{formatLabel(decision.severity)}</span>
                  {decision.warning_code ? <span className="status-pill status-backend-routed">{decision.warning_code}</span> : null}
                </div>
                <p style={{ margin: '0.6rem 0 0', lineHeight: 1.55 }}>{decision.prompt || 'Review candidate decision'}</p>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  {decision.recommended_action || 'Confirm before the candidate can advance.'}
                </p>
              </article>
            ))}
            {!decisions.length ? <p style={{ color: 'var(--muted)' }}>No required decisions are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Warning review" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Warning Review</h2>
            <span className="status-pill status-awaiting-values">{formatCount(warnings.length)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {warnings.map((warning) => (
              <article key={`${warning.code}-${warning.message}`} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ justifyContent: 'flex-start' }}>
                  <span className={`status-pill ${warningTone(warning.severity)}`}>{formatLabel(warning.severity)}</span>
                  <span className="status-pill status-backend-routed">{warning.code || 'WARNING'}</span>
                </div>
                <p style={{ margin: '0.6rem 0 0', lineHeight: 1.55 }}>{warning.message || 'Review warning'}</p>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                  {warning.review_action || 'Review before import.'}
                </p>
              </article>
            ))}
            {!warnings.length ? <p style={{ color: 'var(--muted)' }}>No warnings are currently reported.</p> : null}
          </div>
        </section>

        <section aria-label="Proposed project structure" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Proposed Structure</h2>
            <span className="status-pill status-configured">{formatCount(workpackages.length)} groups</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {workpackages.map((workpackage) => {
              const tasks = workpackage.tasks || []
              return (
                <details key={workpackage.workpackage_id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                  <summary style={{ cursor: 'pointer' }}>
                    <strong>{workpackage.title || workpackage.workpackage_id}</strong>
                    <span style={{ color: 'var(--muted)' }}>
                      {' '}
                      · {formatCount(workpackage.task_count)} tasks · {formatCount(workpackage.apparatus_candidate_count)} apparatus · {workpackage.planned_hours ?? 0} hours
                    </span>
                  </summary>
                  <p style={{ margin: '0.55rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
                    Drawing refs: {(workpackage.drawing_refs || []).join(', ') || 'none'} · Source rows: {sourceRows(tasks) || 'unknown'}
                  </p>
                  <div style={{ display: 'grid', gap: '0.55rem', marginTop: '0.75rem' }}>
                    {tasks.map((task) => (
                      <article key={task.task_id} className="card" style={{ padding: '0.75rem', boxShadow: 'none' }}>
                        <div className="status-row" style={{ alignItems: 'start' }}>
                          <div>
                            <p style={{ margin: 0 }}>
                              <strong>{task.title || task.task_id}</strong>
                            </p>
                            <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                              {task.designation || 'no designation'} · {task.apparatus_type || 'unknown apparatus'} · drawing {task.drawing_ref || 'unknown'}
                            </p>
                          </div>
                          <span className="status-pill status-backend-routed">
                            {formatCount(task.apparatus_candidates?.length)} apparatus
                          </span>
                        </div>
                        <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                          Source {task.source_ref?.source_sheet || 'unknown sheet'} row {task.source_ref?.source_row ?? 'unknown'} · line {task.source_ref?.line_id || 'unknown'}
                        </p>
                      </article>
                    ))}
                  </div>
                </details>
              )
            })}
            {!workpackages.length ? <p style={{ color: 'var(--muted)' }}>No workpackages are currently proposed.</p> : null}
          </div>
        </section>

        <section className="status-grid status-grid-wide" aria-label="Resource context" style={{ marginBottom: '1rem' }}>
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
            <div style={{ display: 'grid', gap: '0.8rem', marginTop: '0.9rem' }}>
              <div>
                <p style={{ margin: '0 0 0.45rem', fontWeight: 700 }}>Allowed now</p>
                <ul>
                  {allowedNow.map((item) => (
                    <li key={item}>{formatLabel(item)}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p style={{ margin: '0 0 0.45rem', fontWeight: 700 }}>Not allowed now</p>
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
