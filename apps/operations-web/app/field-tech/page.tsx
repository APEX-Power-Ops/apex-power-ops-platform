'use client'

import * as React from 'react'

type ApparatusRow = {
  id: string
  name?: string
  neta_standard?: string
  status?: string
  task_id?: string
  assigned_to?: string | null
  source_apparatus_type?: string | null
  source_designation?: string | null
  source_drawing_ref?: string | null
}

type ProjectApparatusPlan = {
  expanded_apparatus_candidates?: Array<{
    display_name?: string
    designation?: string | null
    apparatus_type?: string | null
    drawing_ref?: string | null
  }>
}

type AssignmentRow = {
  id: string
  apparatus_id?: string
  task_id?: string
  assigned_to?: string | null
}

type CrewRow = {
  id: string
  name?: string
  role?: string
}

type IssueRow = {
  id: string
  title?: string
  severity?: string
  status?: string
  apparatus_id?: string
}

type ChecklistRow = {
  id: string
  apparatus_id?: string
  name?: string
  completed?: boolean
}

type HoursRow = {
  id: string
  apparatus_id?: string
  hours?: number
}

const { useCallback, useEffect, useMemo, useState } = React

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const SEAM_BASE = `${API_BASE}/mutations`
const READS_BASE = `${API_BASE}/reads`

function makeToken(actorId: string) {
  return `Bearer ${btoa(JSON.stringify({ actor_id: actorId, actor_role: 'field_tech', project_scope: ['proj-001'] }))}`
}

async function readData<T>(endpoint: string, actorId: string): Promise<T> {
  const response = await fetch(`${READS_BASE}/${endpoint}`, {
    headers: { Authorization: makeToken(actorId) },
  })

  if (!response.ok) {
    throw new Error(`Failed to read ${endpoint}`)
  }

  return (await response.json()) as T
}

async function seamPost(actorId: string, entityId: string, status: string) {
  const response = await fetch(`${SEAM_BASE}/apparatus`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: makeToken(actorId),
    },
    body: JSON.stringify({
      idempotency_key: crypto.randomUUID(),
      mutation_class: 'B',
      action_type: 'update_status',
      entity_id: entityId,
      payload: { status },
      reason: `Field technician moved apparatus to ${status}`,
      source: 'online',
      client_timestamp: new Date().toISOString(),
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to update apparatus status')
  }

  return response.json()
}

function formatStatus(status?: string | null) {
  return (status || 'unknown').replace(/_/g, ' ')
}

function resolveApparatusMetadata(
  row: ApparatusRow,
  metadataByName: Map<string, { designation?: string | null; apparatusType?: string | null; drawingRef?: string | null }>,
) {
  const fallback = metadataByName.get(row.name || '')
  return {
    designation: row.source_designation ?? fallback?.designation ?? null,
    apparatusType: row.source_apparatus_type ?? fallback?.apparatusType ?? null,
    drawingRef: row.source_drawing_ref ?? fallback?.drawingRef ?? null,
  }
}

function badgeTone(status?: string | null) {
  switch (status) {
    case 'complete':
      return { background: 'rgba(45, 122, 85, 0.12)', color: 'var(--ok)' }
    case 'active':
      return { background: 'rgba(18, 62, 87, 0.12)', color: 'var(--brand)' }
    case 'ready':
      return { background: 'rgba(189, 109, 47, 0.12)', color: 'var(--warn)' }
    case 'on_hold':
      return { background: 'rgba(122, 61, 44, 0.12)', color: 'var(--defer)' }
    default:
      return { background: 'rgba(89, 106, 119, 0.12)', color: 'var(--muted)' }
  }
}

function StatusBadge({ status }: { status?: string | null }) {
  return (
    <span
      style={{
        ...badgeTone(status),
        borderRadius: 999,
        padding: '0.32rem 0.64rem',
        fontSize: '0.72rem',
        fontFamily: 'var(--font-mono), monospace',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}
    >
      {formatStatus(status)}
    </span>
  )
}

function buildApparatusContext(row: ApparatusRow | null) {
  if (!row) {
    return ''
  }

  return [row.source_designation, row.source_apparatus_type].filter(Boolean).join(' · ')
}

export default function FieldTechPage() {
  const [crew, setCrew] = useState<CrewRow[]>([])
  const [selectedTechId, setSelectedTechId] = useState('tech-001')
  const [apparatus, setApparatus] = useState<ApparatusRow[]>([])
  const [assignments, setAssignments] = useState<AssignmentRow[]>([])
  const [issues, setIssues] = useState<IssueRow[]>([])
  const [hours, setHours] = useState<HoursRow[]>([])
  const [checklist, setChecklist] = useState<ChecklistRow[]>([])
  const [projectPlan, setProjectPlan] = useState<ProjectApparatusPlan>({})
  const [selectedApparatusId, setSelectedApparatusId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState('')
  const [updatingStatus, setUpdatingStatus] = useState(false)

  const refresh = useCallback(async (actorId: string) => {
    setLoading(true)
    try {
      const [crewRows, apparatusRows, assignmentRows, issueRows, hourRows, projectPlanRows] = await Promise.all([
        readData<CrewRow[]>('crew', actorId),
        readData<ApparatusRow[]>('apparatus', actorId),
        readData<AssignmentRow[]>('assignments', actorId),
        readData<IssueRow[]>('issues', actorId),
        readData<HoursRow[]>('hours', actorId),
        readData<ProjectApparatusPlan>('project-apparatus-plan', actorId),
      ])

      setCrew(crewRows)
      setApparatus(apparatusRows)
      setAssignments(assignmentRows)
      setIssues(issueRows)
      setHours(hourRows)
      setProjectPlan(projectPlanRows)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh(selectedTechId)
  }, [refresh, selectedTechId])

  const assignedApparatus = useMemo(() => {
    const assignmentIds = new Set(
      assignments.filter((assignment) => assignment.assigned_to === selectedTechId).map((assignment) => assignment.apparatus_id),
    )

    return apparatus.filter((row) => assignmentIds.has(row.id) || row.assigned_to === selectedTechId)
  }, [apparatus, assignments, selectedTechId])

  const apparatusMetadataByName = useMemo(
    () =>
      new Map(
        (projectPlan.expanded_apparatus_candidates || [])
          .filter((row) => row.display_name)
          .map((row) => [
            row.display_name as string,
            {
              designation: row.designation,
              apparatusType: row.apparatus_type,
              drawingRef: row.drawing_ref,
            },
          ]),
      ),
    [projectPlan],
  )

  useEffect(() => {
    if (!assignedApparatus.length) {
      setSelectedApparatusId(null)
      return
    }
    if (!selectedApparatusId || !assignedApparatus.some((row) => row.id === selectedApparatusId)) {
      setSelectedApparatusId(assignedApparatus[0].id)
    }
  }, [assignedApparatus, selectedApparatusId])

  const selectedApparatus = useMemo(
    () => assignedApparatus.find((row) => row.id === selectedApparatusId) ?? assignedApparatus[0] ?? null,
    [assignedApparatus, selectedApparatusId],
  )

  useEffect(() => {
    if (!selectedApparatus?.id) {
      setChecklist([])
      return
    }

    void readData<ChecklistRow[]>(`checklist/${selectedApparatus.id}`, selectedTechId).then(setChecklist)
  }, [selectedApparatus?.id, selectedTechId])

  const selectedIssues = useMemo(
    () => issues.filter((issue) => issue.apparatus_id === selectedApparatus?.id && issue.status !== 'resolved' && issue.status !== 'closed'),
    [issues, selectedApparatus?.id],
  )

  const totalLoggedHours = useMemo(
    () => hours.filter((entry) => entry.apparatus_id === selectedApparatus?.id).reduce((sum, entry) => sum + (entry.hours || 0), 0),
    [hours, selectedApparatus?.id],
  )

  const availableTransitions = useMemo(() => {
    switch (selectedApparatus?.status) {
      case 'not_started':
        return ['ready', 'active']
      case 'ready':
        return ['active', 'not_started']
      case 'active':
        return ['on_hold', 'complete']
      case 'on_hold':
        return ['active', 'ready']
      default:
        return []
    }
  }, [selectedApparatus?.status])

  async function handleStatusChange(nextStatus: string) {
    if (!selectedApparatus) {
      return
    }

    setUpdatingStatus(true)
    try {
      await seamPost(selectedTechId, selectedApparatus.id, nextStatus)
      setApparatus((rows) => rows.map((row) => (row.id === selectedApparatus.id ? { ...row, status: nextStatus } : row)))
      setStatusMessage(`Status updated to ${formatStatus(nextStatus)}.`)
    } finally {
      setUpdatingStatus(false)
    }
  }

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">Field Execution Lane</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Field technician completion now has a real app route.</h1>
            <p className="lede">
              This route gives field technicians an assignment queue, apparatus status transitions, and the same seam-backed
              progress signals that feed lead and PM visibility.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Selected technician</dt>
              <dd>{crew.find((row) => row.id === selectedTechId)?.name || selectedTechId}</dd>
            </div>
            <div>
              <dt>Assigned apparatus</dt>
              <dd>{assignedApparatus.length} apparatus in the active queue</dd>
            </div>
            <div>
              <dt>PM visibility</dt>
              <dd>
                Review downstream impact in <a href="/lead-ops">lead ops</a> and <a href="/pm-review/approval">PM approval</a>.
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Queue readiness</h2>
            <span className={`status-pill ${loading ? 'status-awaiting-values' : 'status-backend-routed'}`}>{loading ? 'loading' : 'live'}</span>
          </div>
          <p>Assigned apparatus, open issues, checklist progress, and logged hours come through the governed seam.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Work in progress</h2>
            <span className="status-pill status-configured">{assignedApparatus.filter((row) => row.status === 'active').length} active</span>
          </div>
          <p>{assignedApparatus.filter((row) => row.status === 'complete').length} apparatus are already complete for this technician.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Escalation watch</h2>
            <span className="status-pill status-landed">{issues.filter((issue) => issue.status === 'escalated').length} escalated</span>
          </div>
          <p>Field-side blockers stay visible while PM approval and lead assignment remain in the same governed surface family.</p>
        </article>
      </section>

      <section className="notes-grid" style={{ marginBottom: '1rem' }}>
        <article className="notes-card">
          <div className="status-row">
            <h2>Assignment Queue</h2>
            <select
              aria-label="Technician selector"
              value={selectedTechId}
              onChange={(event) => {
                setSelectedTechId(event.target.value)
                setStatusMessage('')
              }}
              style={{
                padding: '0.6rem 0.75rem',
                borderRadius: 14,
                border: '1px solid var(--border)',
                background: 'rgba(255, 252, 246, 0.96)',
                color: 'var(--ink)',
                font: 'inherit',
              }}
            >
              {crew.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.name || row.id}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {assignedApparatus.map((row) => (
              <button
                key={row.id}
                className="card"
                style={{
                  padding: '1rem 1.1rem',
                  textAlign: 'left',
                  background: selectedApparatus?.id === row.id ? 'rgba(216, 229, 234, 0.62)' : 'rgba(255, 252, 246, 0.94)',
                  cursor: 'pointer',
                }}
                onClick={() => {
                  setSelectedApparatusId(row.id)
                  setStatusMessage('')
                }}
              >
                {(() => {
                  const metadata = resolveApparatusMetadata(row, apparatusMetadataByName)
                  const contextLabel = buildApparatusContext({
                    ...row,
                    source_designation: metadata.designation,
                    source_apparatus_type: metadata.apparatusType,
                  })
                  return (
                    <>
                <div className="status-row">
                  <strong>{row.name || row.id}</strong>
                  <StatusBadge status={row.status} />
                </div>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)' }}>
                  {(row.neta_standard || 'Unknown standard')} · {row.id}
                  {contextLabel ? ` · ${contextLabel}` : ''}
                  {metadata.drawingRef ? ` · ${metadata.drawingRef}` : ''}
                </p>
                    </>
                  )
                })()}
              </button>
            ))}
            {!assignedApparatus.length ? <p style={{ color: 'var(--muted)' }}>No apparatus are currently assigned.</p> : null}
          </div>
        </article>

        <article className="notes-card accent-card">
          <h2>Completion Snapshot</h2>
          {selectedApparatus ? (
            <ul>
              <li>{checklist.filter((item) => item.completed).length} of {checklist.length} checklist items are complete.</li>
              <li>{selectedIssues.length} open issue{selectedIssues.length === 1 ? '' : 's'} remain on this apparatus.</li>
              <li>{totalLoggedHours.toFixed(1)} hours have been logged for the current apparatus.</li>
              <li>The current apparatus status is {formatStatus(selectedApparatus.status)}.</li>
            </ul>
          ) : (
            <p style={{ color: 'var(--muted)' }}>Select an apparatus to view progress detail.</p>
          )}
        </article>
      </section>

      <section className="notes-card">
        <div className="status-row">
          <h2>Apparatus Detail</h2>
          {selectedApparatus ? <StatusBadge status={selectedApparatus.status} /> : null}
        </div>
        {selectedApparatus ? (
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div className="card" style={{ padding: '1rem 1.1rem' }}>
              {(() => {
                const metadata = resolveApparatusMetadata(selectedApparatus, apparatusMetadataByName)
                const contextLabel = buildApparatusContext({
                  ...selectedApparatus,
                  source_designation: metadata.designation,
                  source_apparatus_type: metadata.apparatusType,
                })
                return (
                  <>
              <div className="status-row">
                <strong>{selectedApparatus.name || selectedApparatus.id}</strong>
                <span style={{ color: 'var(--muted)' }}>{selectedApparatus.id}</span>
              </div>
              <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)' }}>
                {selectedApparatus.neta_standard || 'Unknown standard'} · current workflow status {formatStatus(selectedApparatus.status)}
                {contextLabel ? ` · ${contextLabel}` : ''}
                {metadata.drawingRef ? ` · ${metadata.drawingRef}` : ''}.
              </p>
                  </>
                )
              })()}
            </div>

            <div className="card" style={{ padding: '1rem 1.1rem' }}>
              <h3 style={{ margin: '0 0 0.75rem' }}>Update Status</h3>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {availableTransitions.map((status) => (
                  <button key={status} className="btn btn-outline" onClick={() => void handleStatusChange(status)} disabled={updatingStatus}>
                    {updatingStatus ? 'Saving...' : `Mark ${formatStatus(status)}`}
                  </button>
                ))}
              </div>
              {statusMessage ? <p style={{ margin: '0.85rem 0 0', color: 'var(--ok)' }}>{statusMessage}</p> : null}
            </div>

            <div className="card" style={{ padding: '1rem 1.1rem' }}>
              <h3 style={{ margin: '0 0 0.75rem' }}>Open Issues</h3>
              <div style={{ display: 'grid', gap: '0.65rem' }}>
                {selectedIssues.length ? (
                  selectedIssues.map((issue) => (
                    <article key={issue.id} style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center' }}>
                      <div>
                        <strong>{issue.title || issue.id}</strong>
                        <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>{formatStatus(issue.status)}</p>
                      </div>
                      <StatusBadge status={issue.severity} />
                    </article>
                  ))
                ) : (
                  <p style={{ margin: 0, color: 'var(--muted)' }}>No unresolved issues on this apparatus.</p>
                )}
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: 'var(--muted)' }}>Select an apparatus from the queue to update status.</p>
        )}
      </section>
    </main>
  )
}