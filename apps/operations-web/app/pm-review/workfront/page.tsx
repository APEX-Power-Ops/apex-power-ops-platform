'use client'

import * as React from 'react'
import Link from 'next/link'

import { buildPmReturnContext, buildPmRoute } from '../route-navigation'

type WorkfrontSummary = {
  total_count?: number
  blocked_count?: number
  unassigned_count?: number
  ready_count?: number
  in_progress_count?: number
  pm_review_count?: number
  complete_count?: number
}

type WorkfrontLenses = {
  all_count?: number
  blocked_count?: number
  needs_pm_disposition_count?: number
  returned_to_lead_count?: number
  stale_blocker_count?: number
  unassigned_count?: number
}

type WorkfrontRow = {
  id: string
  apparatus_id?: string
  apparatus_name?: string
  status?: string
  status_label?: string
  readiness?: string
  task_id?: string | null
  workpackage_id?: string | null
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
  primary_blocking_issue_id?: string | null
  returnable_issue_id?: string | null
  blocking_issues?: Array<{
    id?: string
    title?: string
    status?: string
    severity?: string
    blocks_completion?: boolean
    reported_by?: string
    pm_followup_note?: string | null
    pm_followup_sent_at?: string | null
    pm_followup_workfront_row_id?: string | null
  }>
  latest_pm_followup_note?: string | null
  latest_pm_followup_sent_at?: string | null
  lens_tags?: string[]
  last_pm_decision?: {
    id?: string
    mutation_id?: string
    actor_id?: string
    actor_role?: string
    action_type?: string
    entity_id?: string
    reason?: string
    timestamp?: string
    from_status?: string
    to_status?: string
  } | null
  ai_advisory?: {
    mode?: string
    mutation_authority?: string
    target_audience?: string
    brief?: string
  }
}

type DecisionHistoryRow = {
  id?: string
  mutation_id?: string
  actor_id?: string
  actor_role?: string
  action_type?: string
  entity_id?: string
  reason?: string
  timestamp?: string
  server_timestamp?: string
  client_timestamp?: string
  from_state?: {
    status?: string
  }
  to_state?: {
    status?: string
  }
}

type ReviewSnapshot = {
  id?: string
  workpackage_id?: string | null
  status?: string | null
  period_start?: string | null
  period_end?: string | null
  percent_complete?: number | null
  hours_reported?: number | null
  submitted_by?: string | null
}

type WorkfrontPayload = {
  summary?: WorkfrontSummary
  lenses?: WorkfrontLenses
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
const MUTATIONS_BASE = `${API_BASE}/mutations`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }
const DECISION_HISTORY_LIMIT = 25
const WORKFRONT_RETURN_CONTEXT = buildPmReturnContext('/pm-review/workfront', {}, 'PM workfront')

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

async function readReviewSnapshots(): Promise<ReviewSnapshot[]> {
  const response = await fetch(`${READS_BASE}/snapshots`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read progress snapshots')
  }

  return (await response.json()) as ReviewSnapshot[]
}

async function readDecisionHistory(entityIds: string[], limit = DECISION_HISTORY_LIMIT): Promise<DecisionHistoryRow[]> {
  const params = new URLSearchParams()
  entityIds.forEach((entityId) => params.append('entity_id', entityId))
  params.set('limit', String(limit))
  const response = await fetch(`${READS_BASE}/decision-history?${params.toString()}`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read PM decision history')
  }

  return (await response.json()) as DecisionHistoryRow[]
}

async function sendIssueFollowup(row: WorkfrontRow) {
  const issue = returnableIssue(row)
  const issueId = issue?.id || row.returnable_issue_id
  if (!issueId) {
    throw new Error('No escalated issue is available to return to lead')
  }

  const now = new Date().toISOString()
  const note =
    row.ai_advisory?.brief ||
    `${row.apparatus_name || row.apparatus_id} needs lead follow-up: ${row.next_action || 'Monitor for next status'}.`
  const idempotencyKey =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `pm-workfront-${issueId}-${Date.now()}`

  const response = await fetch(`${MUTATIONS_BASE}/issues`, {
    method: 'POST',
    headers: {
      Authorization: makeToken(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      idempotency_key: idempotencyKey,
      mutation_class: 'C',
      action_type: 'return_to_lead',
      entity_id: issueId,
      payload: {
        status: 'in_review',
        pm_disposition: 'return_to_lead',
        pm_followup_note: note,
        pm_followup_sent_at: now,
        pm_followup_workfront_row_id: row.id,
        pm_followup_source: 'pm_workfront',
      },
      reason: `PM returned issue ${issueId} to lead review`,
      source: 'online',
      client_timestamp: now,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to send lead follow-up')
  }

  const result = await response.json()
  if (result.status !== 'accepted' && result.status !== 'idempotent_hit') {
    throw new Error(result.error?.message || 'Lead follow-up was rejected')
  }

  return result
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/_/g, ' ')
}

function returnableIssue(row: WorkfrontRow) {
  return row.blocking_issues?.find((issue) => issue.status === 'escalated' && issue.id === row.returnable_issue_id) ||
    row.blocking_issues?.find((issue) => issue.status === 'escalated')
}

function rowDecisionEntityIds(row: WorkfrontRow) {
  const ids = new Set<string>()
  if (row.primary_blocking_issue_id) ids.add(row.primary_blocking_issue_id)
  if (row.returnable_issue_id) ids.add(row.returnable_issue_id)
  if (row.last_pm_decision?.entity_id) ids.add(row.last_pm_decision.entity_id)
  row.blocking_issues?.forEach((issue) => {
    if (issue.id) ids.add(issue.id)
  })
  return ids
}

function rowTaskLabel(row: WorkfrontRow) {
  return row.task_name || row.apparatus_name || row.apparatus_id || row.id
}

function rowNeedsPmReview(row: WorkfrontRow) {
  return row.readiness === 'pm_review' || row.status === 'awaiting_review'
}

function workfrontDrillthroughLinks(row: WorkfrontRow) {
  const taskId = row.task_id || undefined
  const taskLabel = rowTaskLabel(row)

  return {
    drivers: buildPmRoute('/pm-review', {
      focusTaskId: taskId,
      ...WORKFRONT_RETURN_CONTEXT,
    }),
    schedule: buildPmRoute('/pm-review/schedule', {
      focusTaskId: taskId,
      ...WORKFRONT_RETURN_CONTEXT,
    }),
    tracer: buildPmRoute('/pm-review/tracer', {
      taskId,
      taskLabel,
      maxDepth: 10,
      ...WORKFRONT_RETURN_CONTEXT,
    }),
    variance: buildPmRoute('/pm-review/variance', {
      projectId: 'stack-dc',
      focusTaskId: taskId,
      ...WORKFRONT_RETURN_CONTEXT,
    }),
  }
}

function workfrontEscalationReviewLink(issueId?: string | null) {
  return issueId
    ? buildPmRoute('/pm-review/approval', {
        screen: 'escalations',
        detailId: issueId,
        ...WORKFRONT_RETURN_CONTEXT,
      })
    : null
}

function workfrontTaskReviewLink(row: WorkfrontRow) {
  if (!row.task_id || !rowNeedsPmReview(row)) {
    return null
  }

  return buildPmRoute('/pm-review/approval', {
    screen: 'task-review',
    detailId: row.task_id,
    ...WORKFRONT_RETURN_CONTEXT,
  })
}

function workfrontWorkPackageReviewLink(row: WorkfrontRow) {
  if (!row.workpackage_id || !rowNeedsPmReview(row)) {
    return null
  }

  return buildPmRoute('/pm-review/approval', {
    screen: 'wp-review',
    detailId: row.workpackage_id,
    ...WORKFRONT_RETURN_CONTEXT,
  })
}

function workfrontSubmittedSnapshot(row: WorkfrontRow, snapshots: ReviewSnapshot[]) {
  if (!row.workpackage_id || !rowNeedsPmReview(row)) {
    return null
  }

  return snapshots.find((snapshot) => snapshot.id && snapshot.workpackage_id === row.workpackage_id && snapshot.status === 'submitted') || null
}

function workfrontSnapshotReviewLink(snapshot: ReviewSnapshot | null) {
  if (!snapshot?.id) {
    return null
  }

  return buildPmRoute('/pm-review/approval', {
    screen: 'snapshot-review',
    detailId: snapshot.id,
    ...WORKFRONT_RETURN_CONTEXT,
  })
}

function workfrontDecisionHistoryLink(row: WorkfrontRow) {
  const [historySearch] = Array.from(rowDecisionEntityIds(row))
  if (!historySearch) {
    return null
  }

  return buildPmRoute('/pm-review/approval', {
    screen: 'history',
    historySearch,
    ...WORKFRONT_RETURN_CONTEXT,
  })
}

function decisionTimestamp(row: DecisionHistoryRow) {
  return row.timestamp || row.server_timestamp || row.client_timestamp || ''
}

function decisionTransition(row: DecisionHistoryRow) {
  const fromStatus = row.from_state?.status
  const toStatus = row.to_state?.status
  return fromStatus || toStatus ? `${formatLabel(fromStatus)} -> ${formatLabel(toStatus)}` : 'No status transition recorded'
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
  const [reviewSnapshots, setReviewSnapshots] = useState<ReviewSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [filter, setFilter] = useState('all')
  const [draftRowId, setDraftRowId] = useState<string | null>(null)
  const [sendingRowId, setSendingRowId] = useState<string | null>(null)
  const [followupResult, setFollowupResult] = useState<Record<string, string>>({})
  const [historyRows, setHistoryRows] = useState<DecisionHistoryRow[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const [nextPayload, nextSnapshots] = await Promise.all([
        readWorkfront(),
        readReviewSnapshots().catch(() => [] as ReviewSnapshot[]),
      ])
      setPayload(nextPayload)
      setReviewSnapshots(nextSnapshots)
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
  const lenses = payload.lenses || {}
  const rows = payload.rows || []
  const filteredRows = useMemo(
    () => (filter === 'all' ? rows : rows.filter((row) => row.readiness === filter || row.lens_tags?.includes(filter))),
    [filter, rows],
  )

  const filters = [
    ['all', `All ${lenses.all_count ?? summary.total_count ?? rows.length}`],
    ['blocked', `Blocked ${lenses.blocked_count ?? summary.blocked_count ?? 0}`],
    ['needs_pm_disposition', `Needs PM disposition ${lenses.needs_pm_disposition_count ?? 0}`],
    ['returned_to_lead', `Returned to lead ${lenses.returned_to_lead_count ?? 0}`],
    ['stale_blocker', `Stale blockers ${lenses.stale_blocker_count ?? 0}`],
    ['unassigned', `Unassigned ${lenses.unassigned_count ?? summary.unassigned_count ?? 0}`],
    ['ready', `Ready ${summary.ready_count ?? 0}`],
    ['in_progress', `Active ${summary.in_progress_count ?? 0}`],
    ['pm_review', `PM review ${summary.pm_review_count ?? 0}`],
  ]

  const sendFollowup = useCallback(
    async (row: WorkfrontRow) => {
      try {
        setSendingRowId(row.id)
        await sendIssueFollowup(row)
        setFollowupResult((current) => ({
          ...current,
          [row.id]: 'PM returned this issue to lead review.',
        }))
        await refresh()
      } catch (error) {
        setFollowupResult((current) => ({
          ...current,
          [row.id]: error instanceof Error ? error.message : 'Lead follow-up failed',
        }))
      } finally {
        setSendingRowId(null)
      }
    },
    [refresh],
  )

  const refreshHistory = useCallback(async (row: WorkfrontRow) => {
    const entityIds = Array.from(rowDecisionEntityIds(row))
    if (!entityIds.length) {
      setHistoryRows([])
      setHistoryError(null)
      setHistoryLoaded(true)
      return
    }

    try {
      setHistoryLoading(true)
      setHistoryError(null)
      setHistoryRows(await readDecisionHistory(entityIds))
      setHistoryLoaded(true)
    } catch (error) {
      setHistoryRows([])
      setHistoryError(error instanceof Error ? error.message : 'Decision history is unavailable')
    } finally {
      setHistoryLoading(false)
    }
  }, [])

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
              Use read-only lenses while preserving the downstream context PM needs: owner, designation, drawing reference, task, blocker count, checklist progress, disposition history, and next action.
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
            (() => {
              const escalatedIssue = returnableIssue(row)
              const rowEntityIds = rowDecisionEntityIds(row)
              const rowHistory = historyRows.filter((event) => event.entity_id && rowEntityIds.has(event.entity_id))
              const drillthroughLinks = workfrontDrillthroughLinks(row)
              const escalationReviewLink = workfrontEscalationReviewLink(escalatedIssue?.id)
              const taskReviewLink = workfrontTaskReviewLink(row)
              const workPackageReviewLink = workfrontWorkPackageReviewLink(row)
              const snapshotReviewLink = workfrontSnapshotReviewLink(workfrontSubmittedSnapshot(row, reviewSnapshots))
              const decisionHistoryLink = workfrontDecisionHistoryLink(row)

              return (
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
                <div
                  aria-label={`Schedule drillthrough for ${row.apparatus_name || row.apparatus_id || row.id}`}
                  style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.65rem' }}
                >
                  <Link className="btn btn-outline" href={drillthroughLinks.drivers}>
                    Drivers
                  </Link>
                  <Link className="btn btn-outline" href={drillthroughLinks.schedule}>
                    Schedule
                  </Link>
                  <Link className="btn btn-outline" href={drillthroughLinks.tracer}>
                    Trace
                  </Link>
                  <Link className="btn btn-outline" href={drillthroughLinks.variance}>
                    Variance
                  </Link>
                </div>
              </div>
              <div>
                <p style={{ margin: 0, fontFamily: 'var(--font-mono), monospace', fontSize: '0.78rem', color: 'var(--brand)', textTransform: 'uppercase' }}>
                  Next action
                </p>
                <p style={{ margin: '0.4rem 0 0', lineHeight: 1.55 }}>{row.next_action || 'Monitor for next status'}</p>
                <button
                  className="btn btn-outline"
                  onClick={() => setDraftRowId(draftRowId === row.id ? null : row.id)}
                  style={{ marginTop: '0.75rem' }}
                >
                  {draftRowId === row.id ? 'Hide follow-up' : 'Draft lead follow-up'}
                </button>
                {escalationReviewLink ? (
                  <Link
                    className="btn btn-outline"
                    href={escalationReviewLink}
                    style={{ marginTop: '0.75rem', marginLeft: '0.5rem' }}
                  >
                    Review escalation
                  </Link>
                ) : null}
                {taskReviewLink ? (
                  <Link className="btn btn-outline" href={taskReviewLink} style={{ marginTop: '0.75rem', marginLeft: '0.5rem' }}>
                    Review task
                  </Link>
                ) : null}
                {workPackageReviewLink ? (
                  <Link className="btn btn-outline" href={workPackageReviewLink} style={{ marginTop: '0.75rem', marginLeft: '0.5rem' }}>
                    Review package
                  </Link>
                ) : null}
                {snapshotReviewLink ? (
                  <Link className="btn btn-outline" href={snapshotReviewLink} style={{ marginTop: '0.75rem', marginLeft: '0.5rem' }}>
                    Review snapshot
                  </Link>
                ) : null}
                {decisionHistoryLink ? (
                  <Link className="btn btn-outline" href={decisionHistoryLink} style={{ marginTop: '0.75rem', marginLeft: '0.5rem' }}>
                    Review history
                  </Link>
                ) : null}
              </div>
              {draftRowId === row.id ? (
                <div
                  style={{
                    gridColumn: '1 / -1',
                    borderTop: '1px solid var(--border)',
                    paddingTop: '0.85rem',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 0.8fr) minmax(0, 1.5fr)',
                    gap: '1rem',
                  }}
                >
                  <div>
                    <p
                      style={{
                        margin: 0,
                        fontFamily: 'var(--font-mono), monospace',
                        fontSize: '0.74rem',
                        color: 'var(--muted)',
                        textTransform: 'uppercase',
                      }}
                    >
                      AI advisory
                    </p>
                    <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                      {(row.ai_advisory?.mode || 'draft_only').replace(/_/g, ' ')} · {row.ai_advisory?.mutation_authority || 'not_admitted'}
                    </p>
                    <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                      Lead target · {escalatedIssue?.id || row.primary_blocking_issue_id || 'no escalated issue'}
                    </p>
                    {row.last_pm_decision ? (
                      <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                        Last PM decision · {formatLabel(row.last_pm_decision.action_type)} · {row.last_pm_decision.to_status || 'unknown'}
                      </p>
                    ) : null}
                  </div>
                  <div>
                    {row.latest_pm_followup_note ? (
                      <p style={{ margin: '0 0 0.65rem', color: 'var(--ok)', lineHeight: 1.5 }}>
                        Returned to lead review{row.latest_pm_followup_sent_at ? ` at ${row.latest_pm_followup_sent_at}` : ''}.
                      </p>
                    ) : null}
                    {row.last_pm_decision ? (
                      <p style={{ margin: '0 0 0.65rem', fontFamily: 'var(--font-mono), monospace', fontSize: '0.78rem', color: 'var(--brand)', textTransform: 'uppercase' }}>
                        Last PM disposition
                      </p>
                    ) : null}
                    {row.last_pm_decision?.reason ? (
                      <p style={{ margin: '0 0 0.65rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                        PM reason: {row.last_pm_decision.reason}
                      </p>
                    ) : null}
                    <div
                      role="region"
                      aria-label={`Disposition history for ${row.apparatus_name || row.apparatus_id || row.id}`}
                      style={{
                        border: '1px solid var(--border)',
                        borderRadius: 8,
                        padding: '0.85rem',
                        marginBottom: '0.75rem',
                      }}
                    >
                      <div className="status-row" style={{ gap: '0.65rem', alignItems: 'center' }}>
                        <p style={{ margin: 0, fontFamily: 'var(--font-mono), monospace', fontSize: '0.78rem', color: 'var(--brand)', textTransform: 'uppercase' }}>
                          Disposition history
                        </p>
                        <button className="btn btn-outline" onClick={() => void refreshHistory(row)} disabled={historyLoading}>
                          {historyLoading ? 'Loading...' : historyLoaded ? 'Refresh history' : 'View history'}
                        </button>
                      </div>
                      <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)', fontSize: '0.86rem', lineHeight: 1.5 }}>
                        This history panel is read-only. Return to lead is the only mutation action on this surface.
                      </p>
                      {historyError ? (
                        <p style={{ margin: '0.55rem 0 0', color: 'var(--defer)', lineHeight: 1.5 }}>{historyError}</p>
                      ) : null}
                      {historyLoaded && !rowHistory.length && !historyError ? (
                        <p style={{ margin: '0.55rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>No PM disposition recorded.</p>
                      ) : null}
                      {!historyError && rowHistory.length ? (
                        <div style={{ display: 'grid', gap: '0.55rem', marginTop: '0.65rem' }}>
                          {rowHistory.map((event) => (
                            <div key={event.id || `${event.entity_id}-${event.timestamp}`} style={{ borderTop: '1px solid var(--border)', paddingTop: '0.55rem' }}>
                              <p style={{ margin: 0, lineHeight: 1.5 }}>
                                {formatLabel(event.action_type)} · {decisionTransition(event)}
                              </p>
                              <p style={{ margin: '0.3rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                                {decisionTimestamp(event) || 'No timestamp'} · {event.actor_role || 'unknown actor'}
                              </p>
                              {event.reason ? (
                                <p style={{ margin: '0.3rem 0 0', color: 'var(--muted)', lineHeight: 1.5 }}>
                                  PM reason: {event.reason}
                                </p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <p style={{ margin: 0, lineHeight: 1.55 }}>
                      {row.ai_advisory?.brief ||
                        `${row.apparatus_name || row.apparatus_id} needs lead follow-up: ${row.next_action || 'Monitor for next status'}.`}
                    </p>
                    <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                      <button
                        className="btn btn-outline"
                        onClick={() => void sendFollowup(row)}
                        disabled={sendingRowId === row.id || !escalatedIssue}
                      >
                        {sendingRowId === row.id ? 'Returning...' : 'Return to lead'}
                      </button>
                      <span style={{ color: 'var(--muted)', fontSize: '0.86rem' }}>
                        This records a PM disposition through the governed seam. AI advisory remains draft-only.
                      </span>
                    </div>
                    {followupResult[row.id] ? (
                      <p style={{ margin: '0.6rem 0 0', color: followupResult[row.id].startsWith('PM returned') ? 'var(--ok)' : 'var(--defer)', lineHeight: 1.5 }}>
                        {followupResult[row.id]}
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </article>
              )
            })()
          ))}
          {!filteredRows.length ? <p style={{ color: 'var(--muted)' }}>No rows match this read-only lens.</p> : null}
        </div>
      </section>
    </main>
  )
}
