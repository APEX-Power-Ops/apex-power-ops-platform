'use client'

import Link from 'next/link'
import * as React from 'react'

type AdmissionCheck = {
  check_id?: string
  status?: string
  message?: string
  required_resolution?: string
}

type DiffCheck = {
  check_id?: string
  compare?: string[]
  expected?: unknown
  failure_action?: string
}

type AdmissionPlan = {
  admission_plan_id?: string
  admission_plan_version?: string
  candidate_id?: string
  candidate_version?: string
  review_status?: string
  readiness_status?: string
  mutation_authority?: string
  candidate_shape_fingerprint?: string
  source_stat_fingerprint?: string
  target_row_plan?: Record<string, number | string | null | undefined>
  warning_breakdown?: Record<string, number>
  approval_record_contract?: {
    record_type?: string
    storage_authority?: string
    required_fields?: string[]
    permitted_decisions?: string[]
    minimum_expected_values?: Record<string, unknown>
    operator_attestation?: string
  }
  idempotency_plan?: {
    strategy?: string
    components?: Record<string, unknown>
    sample_key?: string
    collision_policy?: string
  }
  preview_to_import_diff_checks?: DiffCheck[]
  no_go_checks?: AdmissionCheck[]
  future_import_sequence?: string[]
  not_allowed_now?: string[]
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

async function readAdmissionPlan(): Promise<AdmissionPlan> {
  const response = await fetch(`${READS_BASE}/project-import-admission-plan`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read PM import admission plan')
  }

  return (await response.json()) as AdmissionPlan
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/[_-]/g, ' ')
}

function formatCount(value?: number | string | null) {
  if (typeof value === 'number' && Number.isFinite(value)) return value.toLocaleString()
  if (typeof value === 'string') return value
  return '0'
}

function sourceValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 'unknown'
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'none'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function checkTone(status?: string) {
  switch (status) {
    case 'pass':
      return 'status-configured'
    case 'needs_human_acceptance':
    case 'pending_future_admission':
      return 'status-awaiting-values'
    case 'no_go':
      return 'status-deferred'
    default:
      return 'status-backend-routed'
  }
}

function planReadinessTone(status?: string) {
  if (status === 'blocked_before_admission_design') return 'status-deferred'
  if (status === 'needs_human_acceptance_before_import_packet') return 'status-awaiting-values'
  return 'status-configured'
}

export default function PmImportAdmissionPlanPage() {
  const [plan, setPlan] = useState<AdmissionPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setPlan(await readAdmissionPlan())
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

  const targetRows = plan?.target_row_plan || {}
  const approvalContract = plan?.approval_record_contract || {}
  const idempotencyPlan = plan?.idempotency_plan || {}
  const diffChecks = plan?.preview_to_import_diff_checks || []
  const noGoChecks = plan?.no_go_checks || []
  const notAllowed = plan?.not_allowed_now || []
  const futureSteps = plan?.future_import_sequence || []
  const blockingNoGoCount = useMemo(
    () => noGoChecks.filter((check) => check.status === 'no_go').length,
    [noGoChecks],
  )

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Import Admission Plan</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Design the import gate before it can write.</h1>
            <p className="lede">
              This route defines the approval record, idempotency key, preview-to-import diff checks, and no-go checks needed for a future import packet. It does not approve, persist, import, assign, schedule, or mutate production state.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Read seam</dt>
              <dd>/api/v1/reads/project-import-admission-plan</dd>
            </div>
            <div>
              <dt>Plan</dt>
              <dd>{plan?.admission_plan_id || 'waiting for admission plan'}</dd>
            </div>
            <div>
              <dt>Mutation authority</dt>
              <dd>{plan?.mutation_authority || 'not_admitted'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Plan seam</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>{loading ? 'Loading admission plan.' : 'Admission design is read-only and pre-mutation.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Readiness</h2>
            <span className={`status-pill ${planReadinessTone(plan?.readiness_status)}`}>{formatLabel(plan?.readiness_status)}</span>
          </div>
          <p>Future import remains blocked until an explicit packet admits approval and write authority.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>No-Go Checks</h2>
            <span className="status-pill status-deferred">{formatCount(blockingNoGoCount)}</span>
          </div>
          <p>Includes the intentional no-go for the missing import mutation path.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Idempotency</h2>
            <span className="status-pill status-configured">planned</span>
          </div>
          <p>{idempotencyPlan.sample_key || 'waiting for candidate key'}</p>
        </article>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Admission Gate Design</h2>
            <p>
              Use this page to review the future import contract before any production write path is opened.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/pm-review/import-candidate">Import candidate</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

        <section className="status-grid status-grid-wide" aria-label="Admission target row plan" style={{ marginBottom: '1rem' }}>
          {Object.entries(targetRows).map(([key, value]) => (
            <article key={key} className="status-card">
              <h2>{formatLabel(key)}</h2>
              <p>{formatCount(value)}</p>
            </article>
          ))}
          {!Object.keys(targetRows).length ? (
            <article className="status-card">
              <h2>Target Rows</h2>
              <p>No target row plan is currently available.</p>
            </article>
          ) : null}
        </section>

        <section className="notes-grid" style={{ marginBottom: '1rem' }}>
          <article className="notes-card">
            <h2>Fingerprints</h2>
            <dl className="contract-panel">
              <div>
                <dt>Candidate</dt>
                <dd>{plan?.candidate_id || 'unknown'}</dd>
              </div>
              <div>
                <dt>Source stat</dt>
                <dd>{plan?.source_stat_fingerprint || 'unknown'}</dd>
              </div>
              <div>
                <dt>Candidate shape</dt>
                <dd>{plan?.candidate_shape_fingerprint || 'unknown'}</dd>
              </div>
            </dl>
          </article>
          <article className="notes-card accent-card">
            <h2>Idempotency Plan</h2>
            <p>{idempotencyPlan.collision_policy || 'No idempotency policy is currently reported.'}</p>
            <dl className="contract-panel" style={{ marginTop: '0.9rem' }}>
              <div>
                <dt>Strategy</dt>
                <dd>{idempotencyPlan.strategy || 'unknown'}</dd>
              </div>
              <div>
                <dt>Sample key</dt>
                <dd>{idempotencyPlan.sample_key || 'unknown'}</dd>
              </div>
            </dl>
          </article>
        </section>

        <section aria-label="Approval record contract" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Approval Record Contract</h2>
            <span className="status-pill status-awaiting-values">{approvalContract.storage_authority || 'not_admitted'}</span>
          </div>
          <p style={{ margin: '0.65rem 0 0', color: 'var(--muted)', lineHeight: 1.55 }}>
            {approvalContract.operator_attestation || 'Approval record persistence is not admitted.'}
          </p>
          <div className="notes-grid" style={{ marginTop: '0.85rem' }}>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Required Fields</h3>
              <ul>
                {(approvalContract.required_fields || []).map((field) => (
                  <li key={field}>{formatLabel(field)}</li>
                ))}
              </ul>
            </article>
            <article className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
              <h3 style={{ margin: '0 0 0.6rem' }}>Permitted Decisions</h3>
              <ul>
                {(approvalContract.permitted_decisions || []).map((decision) => (
                  <li key={decision}>{formatLabel(decision)}</li>
                ))}
              </ul>
            </article>
          </div>
        </section>

        <section aria-label="Preview to import diff checks" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>Preview-To-Import Diff Checks</h2>
            <span className="status-pill status-configured">{formatCount(diffChecks.length)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {diffChecks.map((check) => (
              <article key={check.check_id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <p style={{ margin: 0 }}>
                  <strong>{formatLabel(check.check_id)}</strong>
                </p>
                <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                  Compare {sourceValue(check.compare)}. Expected {sourceValue(check.expected)}.
                </p>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>{check.failure_action}</p>
              </article>
            ))}
          </div>
        </section>

        <section aria-label="No-go checks" className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
          <div className="status-row">
            <h2 style={{ margin: 0 }}>No-Go Checks</h2>
            <span className="status-pill status-deferred">{formatCount(noGoChecks.length)}</span>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem', marginTop: '0.85rem' }}>
            {noGoChecks.map((check) => (
              <article key={check.check_id} className="card" style={{ padding: '0.85rem', boxShadow: 'none' }}>
                <div className="status-row" style={{ justifyContent: 'flex-start' }}>
                  <span className={`status-pill ${checkTone(check.status)}`}>{formatLabel(check.status)}</span>
                  <strong>{formatLabel(check.check_id)}</strong>
                </div>
                <p style={{ margin: '0.55rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>{check.message}</p>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>{check.required_resolution}</p>
              </article>
            ))}
          </div>
        </section>

        <section aria-label="Future import sequence and guardrails" className="notes-grid">
          <article className="notes-card">
            <h2>Future Import Sequence</h2>
            <ol>
              {futureSteps.map((step) => (
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
