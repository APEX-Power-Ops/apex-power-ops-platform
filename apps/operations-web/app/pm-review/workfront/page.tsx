'use client'

import * as React from 'react'
import Link from 'next/link'

type WorkfrontSummary = {
  total_count?: number
  blocked_count?: number
  unassigned_count?: number
  ready_count?: number
  in_progress_count?: number
  pm_review_count?: number
  complete_count?: number
}

type WorkfrontRow = {
  id: string
  apparatus_id?: string
  apparatus_name?: string
  status?: string
  status_label?: string
  readiness?: string
  blocked?: boolean
  blocker_count?: number
  open_issue_count?: number
  owner_name?: string | null
  task_name?: string | null
  workpackage_name?: string | null
  designation?: string | null
  apparatus_type?: string | null
  drawing_ref?: string | null
  checklist_complete_count?: number
  checklist_total_count?: number
  next_action?: string
}

type WorkfrontPayload = {
  summary?: WorkfrontSummary
  rows?: WorkfrontRow[]
  advisory?: {
    mode?: string
    ai_mutation_authority?: string
    recommended_focus?: string
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

async function readWorkfront(): Promise<WorkfrontPayload> {
  const response = await fetch(`${READS_BASE}/pm-workfront`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read PM workfront')
  }

  return (await response.json()) as WorkfrontPayload
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/_/g, ' ')
}

function readinessTone(readiness?: string | null) {
  switch (readiness) {
    case 'blocked':
      return { background: 'rgba(122, 61, 44, 0.12)', color: 'var(--defer)' }
    case 'unassigned':
      return { background: 'rgba(163, 94, 26, 0.12)', color: 'var(--warn)' }
    case 'ready':
      return { background: 'rgba(18, 62, 87, 0.12)', color: 'var(--brand)' }
    case 'complete':
      return { background: 'rgba(45, 122, 85, 0.12)', color: 'var(--ok)' }
    default:
      return { background: 'rgba(89, 106, 119, 0.12)', color: 'var(--muted)' }
  }
}

function ReadinessBadge({ value }: { value?: string | null }) {
  return (
    <span
      style={{
        ...readinessTone(value),
        borderRadius: 999,
        padding: '0.32rem 0.64rem',
        fontSize: '0.72rem',
        fontFamily: 'var(--font-mono), monospace',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        whiteSpace: 'nowrap',
      }}
    >
      {formatLabel(value)}
    </span>
  )
}

export default function PmWorkfrontPage() {
  const [payload, setPayload] = useState<WorkfrontPayload>({})
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [filter, setFilter] = useState('all')

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setPayload(await readWorkfront())
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

  const summary = payload.summary || {}
  const rows = payload.rows || []
  const filteredRows = useMemo(() => (filter === 'all' ? rows : rows.filter((row) => row.readiness === filter)), [filter, rows])

  const filters = [
    ['all', `All ${summary.total_count ?? rows.length}`],
    ['blocked', `Blocked ${summary.blocked_count ?? 0}`],
    ['unassigned', `Unassigned ${summary.unassigned_count ?? 0}`],
    ['ready', `Ready ${summary.ready_count ?? 0}`],
    ['in_progress', `Active ${summary.in_progress_count ?? 0}`],
    ['pm_review', `PM review ${summary.pm_review_count ?? 0}`],
  ]

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Workfront</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>PM workfront now has a governed read model.</h1>
            <p className="lede">
              This route composes lead assignment, field readiness, apparatus metadata, blockers, and next actions into one PM queue without opening mutation authority.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Read seam</dt>
              <dd>/api/v1/reads/pm-workfront</dd>
            </div>
            <div>
              <dt>AI posture</dt>
              <dd>{payload.advisory?.ai_mutation_authority || 'not_admitted'}</dd>
            </div>
            <div>
              <dt>PM focus</dt>
              <dd>{payload.advisory?.recommended_focus || 'Waiting for workfront data'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Workfront seam</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>{loading ? 'Refreshing the PM queue.' : `${summary.total_count ?? rows.length} apparatus rows are available for PM triage.`}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Blocked</h2>
            <span className="status-pill status-deferred">{summary.blocked_count ?? 0}</span>
          </div>
          <p>Rows with unresolved blockers or hold posture are surfaced first.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Unassigned</h2>
            <span className="status-pill status-awaiting-values">{summary.unassigned_count ?? 0}</span>
          </div>
          <p>Owner gaps stay visible before they turn into field delay.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Ready</h2>
            <span className="status-pill status-configured">{summary.ready_count ?? 0}</span>
          </div>
          <p>Assigned apparatus ready for field start or continuation.</p>
        </article>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Read-Only PM Queue</h2>
            <p>
              Filter by readiness while preserving the downstream context PM needs: owner, designation, drawing reference, task, blocker count, checklist progress, and next action.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/lead-ops">Lead ops</Link>
            <Link href="/field-tech">Field tech</Link>
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          {filters.map(([value, label]) => (
            <button
              key={value}
              className="btn btn-outline"
              onClick={() => setFilter(value)}
              style={{
                background: filter === value ? 'rgba(18, 62, 87, 0.12)' : 'transparent',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ display: 'grid', gap: '0.85rem' }}>
          {filteredRows.map((row) => (
            <article
              key={row.id}
              className="card"
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 1.25fr) minmax(0, 1fr) minmax(0, 1fr)',
                gap: '1rem',
                padding: '1rem 1.1rem',
                alignItems: 'start',
              }}
            >
              <div>
                <div className="status-row" style={{ justifyContent: 'flex-start', gap: '0.65rem' }}>
                  <strong>{row.apparatus_name || row.apparatus_id}</strong>
                  <ReadinessBadge value={row.readiness} />
                </div>
                <p style={{ margin: '0.4rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                  {[row.designation, row.apparatus_type, row.drawing_ref].filter(Boolean).join(' · ') || row.apparatus_id}
                </p>
              </div>
              <div>
                <p style={{ margin: 0 }}>
                  Owner: <strong>{row.owner_name || 'Unassigned'}</strong>
                </p>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                  {row.workpackage_name || 'Unmapped work package'} · {row.task_name || 'Unmapped task'}
                </p>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                  Checklist {row.checklist_complete_count ?? 0}/{row.checklist_total_count ?? 0} · {row.open_issue_count ?? 0} open issue{row.open_issue_count === 1 ? '' : 's'}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontFamily: 'var(--font-mono), monospace', fontSize: '0.78rem', color: 'var(--brand)', textTransform: 'uppercase' }}>
                  Next action
                </p>
                <p style={{ margin: '0.4rem 0 0', lineHeight: 1.55 }}>{row.next_action || 'Monitor for next status'}</p>
              </div>
            </article>
          ))}
          {!filteredRows.length ? <p style={{ color: 'var(--muted)' }}>No rows match this readiness filter.</p> : null}
        </div>
      </section>
    </main>
  )
}
