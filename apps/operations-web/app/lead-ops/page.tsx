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
  assigned_by?: string | null
}

type TaskRow = {
  id: string
  name?: string
  workpackage_id?: string
}

type WorkPackageRow = {
  id: string
  name?: string
  status?: string
}

type IssueRow = {
  id: string
  title?: string
  severity?: string
  status?: string
  blocks_completion?: boolean
  apparatus_id?: string
}

type CrewRow = {
  id: string
  name?: string
  role?: string
}

const { useCallback, useEffect, useMemo, useState } = React

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const SEAM_BASE = `${API_BASE}/mutations`
const READS_BASE = `${API_BASE}/reads`
const LEAD_ACTOR = { actor_id: 'lead-001', actor_role: 'lead', project_scope: ['proj-001'] }

function makeToken(actor: typeof LEAD_ACTOR) {
  return `Bearer ${btoa(JSON.stringify(actor))}`
}

async function readData<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${READS_BASE}/${endpoint}`, {
    headers: { Authorization: makeToken(LEAD_ACTOR) },
  })

  if (!response.ok) {
    throw new Error(`Failed to read ${endpoint}`)
  }

  return (await response.json()) as T
}

async function seamPost(
  endpoint: string,
  actionType: string,
  mutationClass: string,
  entityId: string,
  payload: Record<string, unknown>,
  reason: string,
) {
  const response = await fetch(`${SEAM_BASE}/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: makeToken(LEAD_ACTOR),
    },
    body: JSON.stringify({
      idempotency_key: crypto.randomUUID(),
      mutation_class: mutationClass,
      action_type: actionType,
      entity_id: entityId,
      payload,
      reason,
      source: 'online',
      client_timestamp: new Date().toISOString(),
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to post ${endpoint}:${actionType}`)
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

function useLeadOpsData() {
  const [apparatus, setApparatus] = useState<ApparatusRow[]>([])
  const [assignments, setAssignments] = useState<AssignmentRow[]>([])
  const [tasks, setTasks] = useState<TaskRow[]>([])
  const [workpackages, setWorkpackages] = useState<WorkPackageRow[]>([])
  const [issues, setIssues] = useState<IssueRow[]>([])
  const [crew, setCrew] = useState<CrewRow[]>([])
  const [projectPlan, setProjectPlan] = useState<ProjectApparatusPlan>({})
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const [apparatusRows, assignmentRows, taskRows, workpackageRows, issueRows, crewRows, projectPlanRows] = await Promise.all([
        readData<ApparatusRow[]>('apparatus'),
        readData<AssignmentRow[]>('assignments'),
        readData<TaskRow[]>('tasks'),
        readData<WorkPackageRow[]>('workpackages'),
        readData<IssueRow[]>('issues'),
        readData<CrewRow[]>('crew'),
        readData<ProjectApparatusPlan>('project-apparatus-plan'),
      ])

      setApparatus(apparatusRows)
      setAssignments(assignmentRows)
      setTasks(taskRows)
      setWorkpackages(workpackageRows)
      setIssues(issueRows)
      setCrew(crewRows)
      setProjectPlan(projectPlanRows)
      setOnline(true)
      setLastRefresh(new Date())
    } catch {
      setOnline(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { apparatus, assignments, tasks, workpackages, issues, crew, projectPlan, loading, online, lastRefresh, refresh }
}

function statusTone(status?: string | null) {
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
        ...statusTone(status),
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

function buildApparatusContext(row: ApparatusRow) {
  return [row.source_designation, row.source_apparatus_type].filter(Boolean).join(' · ')
}

export default function LeadOpsPage() {
  const { apparatus, assignments, tasks, workpackages, issues, crew, projectPlan, loading, online, lastRefresh, refresh } = useLeadOpsData()
  const [assigningApparatusId, setAssigningApparatusId] = useState<string | null>(null)
  const [selectedTech, setSelectedTech] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const taskMap = useMemo(() => new Map(tasks.map((row) => [row.id, row])), [tasks])
  const workpackageMap = useMemo(() => new Map(workpackages.map((row) => [row.id, row])), [workpackages])
  const assignmentMap = useMemo(() => new Map(assignments.map((row) => [row.apparatus_id, row])), [assignments])
  const crewMap = useMemo(() => new Map(crew.map((row) => [row.id, row])), [crew])
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

  const techCards = useMemo(() => {
    return crew.map((tech) => {
      const rows = assignments.filter((assignment) => assignment.assigned_to === tech.id)
      const assignedApparatus = rows
        .map((assignment) => (assignment.apparatus_id ? apparatus.find((row) => row.id === assignment.apparatus_id) : null))
        .filter((row): row is ApparatusRow => Boolean(row))
      const completed = assignedApparatus.filter((row) => row.status === 'complete').length
      const active = assignedApparatus.filter((row) => row.status === 'active').length

      return {
        tech,
        assignedCount: rows.length,
        completed,
        active,
      }
    })
  }, [apparatus, assignments, crew])

  const groupedWork = useMemo(() => {
    return workpackages
      .map((workpackage) => {
        const items = apparatus
          .map((row) => {
            const task = row.task_id ? taskMap.get(row.task_id) : undefined
            if (!task || task.workpackage_id !== workpackage.id) {
              return null
            }

            return {
              apparatus: row,
              task,
              assignment: assignmentMap.get(row.id),
            }
          })
          .filter((row): row is { apparatus: ApparatusRow; task: TaskRow; assignment: AssignmentRow | undefined } => Boolean(row))

        const completeCount = items.filter((item) => item.apparatus.status === 'complete').length

        return {
          workpackage,
          items,
          completeCount,
        }
      })
      .filter((row) => row.items.length > 0)
  }, [apparatus, assignmentMap, taskMap, workpackages])

  const blockingIssues = useMemo(
    () => issues.filter((issue) => issue.blocks_completion && issue.status !== 'resolved' && issue.status !== 'closed'),
    [issues],
  )

  async function handleAssign() {
    if (!assigningApparatusId || !selectedTech) {
      return
    }

    const existing = assignmentMap.get(assigningApparatusId)
    const selectedApparatus = apparatus.find((row) => row.id === assigningApparatusId)
    const actionType = existing ? 'reassign' : 'assign'
    const entityId = existing?.id ?? `assign-${crypto.randomUUID().slice(0, 8)}`
    const payload = existing
      ? { assigned_to: selectedTech }
      : {
          apparatus_id: assigningApparatusId,
          assigned_to: selectedTech,
          assigned_by: LEAD_ACTOR.actor_id,
          task_id: selectedApparatus?.task_id ?? null,
          project_id: 'proj-001',
        }

    setSubmitting(true)
    try {
      await seamPost('assignments', actionType, 'B', entityId, payload, 'Lead apparatus assignment')
      setAssigningApparatusId(null)
      setSelectedTech('')
      await refresh()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">Lead Delivery Lane</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Lead apparatus assignments now have a real app route.</h1>
            <p className="lede">
              This route promotes the bounded lead workflow the PM lane needs first: apparatus-level assignment,
              field completion visibility, and direct handoff into PM review.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Lane focus</dt>
              <dd>Field job lead apparatus assignment</dd>
            </div>
            <div>
              <dt>Field visibility</dt>
              <dd>{apparatus.length} apparatus rows across {tasks.length} active task contexts</dd>
            </div>
            <div>
              <dt>PM escalation load</dt>
              <dd>{blockingIssues.length} blocking issues ready for PM visibility</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid status-grid-wide" style={{ marginBottom: '1rem' }}>
        <article className="status-card">
          <div className="status-row">
            <h2>Assignment seam</h2>
            <span className={`status-pill ${online ? 'status-backend-routed' : 'status-deferred'}`}>{online ? 'live' : 'offline'}</span>
          </div>
          <p>Apparatus assignments, technician load, and PM issue counts are reading through the governed seam.</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>Last refresh</h2>
            <span className="status-pill status-configured">{lastRefresh ? 'current' : 'pending'}</span>
          </div>
          <p>{lastRefresh ? lastRefresh.toLocaleTimeString() : 'Waiting for the first seam-backed refresh.'}</p>
        </article>
        <article className="status-card">
          <div className="status-row">
            <h2>PM handoff</h2>
            <span className="status-pill status-landed">ready</span>
          </div>
          <p>
            Use <a href="/pm-review/approval?screen=escalations">PM escalations</a> and <a href="/pm-review/schedule">PM schedule</a>{' '}
            to review the downstream operational effect.
          </p>
        </article>
      </section>

      <section className="notes-grid" style={{ marginBottom: '1rem' }}>
        <article className="notes-card">
          <h2>Technician Load</h2>
          <div style={{ display: 'grid', gap: '0.85rem' }}>
            {techCards.map(({ tech, assignedCount, completed, active }) => (
              <div key={tech.id} className="card" style={{ padding: '1rem 1.1rem' }}>
                <div className="status-row">
                  <strong>{tech.name || tech.id}</strong>
                  <StatusBadge status={tech.role} />
                </div>
                <p style={{ margin: '0.5rem 0 0', color: 'var(--muted)' }}>
                  {assignedCount} assigned apparatus, {active} active, {completed} complete.
                </p>
              </div>
            ))}
          </div>
        </article>

        <article className="notes-card accent-card">
          <h2>Operations Visibility</h2>
          <ul>
            <li>{blockingIssues.length} blocking issues currently affect completion readiness.</li>
            <li>{apparatus.filter((row) => row.status === 'active').length} apparatus are actively in progress.</li>
            <li>{apparatus.filter((row) => row.status === 'complete').length} apparatus are complete and ready for PM confirmation.</li>
            <li>{apparatus.filter((row) => !assignmentMap.get(row.id)).length} apparatus still need a lead assignment decision.</li>
          </ul>
        </article>
      </section>

      <section className="notes-card" style={{ marginBottom: '1rem' }}>
        <div className="status-row">
          <h2>Assignment Board</h2>
          <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh seam data'}
          </button>
        </div>
        {groupedWork.map(({ workpackage, items, completeCount }) => (
          <div key={workpackage.id} className="card" style={{ marginTop: '1rem', padding: '1rem 1.1rem' }}>
            <div className="status-row" style={{ marginBottom: '0.75rem' }}>
              <div>
                <strong>{workpackage.name || workpackage.id}</strong>
                <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)' }}>
                  {completeCount}/{items.length} apparatus complete in this work package.
                </p>
              </div>
              <StatusBadge status={workpackage.status} />
            </div>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {items.map(({ apparatus: row, task, assignment }) => {
                const technician = assignment?.assigned_to ? crewMap.get(assignment.assigned_to) : undefined
                const apparatusIssues = issues.filter((issue) => issue.apparatus_id === row.id && issue.status !== 'resolved' && issue.status !== 'closed')
                const metadata = resolveApparatusMetadata(row, apparatusMetadataByName)

                return (
                  <article
                    key={row.id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr) auto',
                      gap: '1rem',
                      alignItems: 'center',
                      padding: '0.9rem 1rem',
                      borderRadius: 18,
                      background: 'rgba(255, 252, 246, 0.94)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <div>
                      <div className="status-row" style={{ justifyContent: 'flex-start', gap: '0.7rem' }}>
                        <strong>{row.name || row.id}</strong>
                        <StatusBadge status={row.status} />
                      </div>
                      <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)' }}>
                        {(row.neta_standard || 'Unknown standard')} on {task.name || task.id}
                        {buildApparatusContext({ ...row, source_designation: metadata.designation, source_apparatus_type: metadata.apparatusType })
                          ? ` · ${buildApparatusContext({ ...row, source_designation: metadata.designation, source_apparatus_type: metadata.apparatusType })}`
                          : ''}
                        {metadata.drawingRef ? ` · ${metadata.drawingRef}` : ''}
                      </p>
                    </div>
                    <div>
                      <p style={{ margin: 0 }}>
                        Assigned to: <strong>{technician?.name || assignment?.assigned_to || 'Unassigned'}</strong>
                      </p>
                      <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)' }}>
                        {apparatusIssues.length} open issue{apparatusIssues.length === 1 ? '' : 's'} for this apparatus.
                      </p>
                    </div>
                    <button
                      className="btn btn-outline"
                      onClick={() => {
                        setAssigningApparatusId(row.id)
                        setSelectedTech(assignment?.assigned_to || '')
                      }}
                    >
                      {assignment ? 'Reassign' : 'Assign'}
                    </button>
                  </article>
                )
              })}
            </div>
          </div>
        ))}
      </section>

      {blockingIssues.length > 0 ? (
        <section className="notes-card">
          <h2>Blocking Issue Watch</h2>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {blockingIssues.map((issue) => (
              <article key={issue.id} className="card" style={{ padding: '1rem 1.1rem' }}>
                <div className="status-row">
                  <strong>{issue.title || issue.id}</strong>
                  <StatusBadge status={issue.severity} />
                </div>
                <p style={{ margin: '0.45rem 0 0', color: 'var(--muted)' }}>
                  Apparatus {issue.apparatus_id || 'unknown'} is blocking completion and should be visible from PM escalations.
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {assigningApparatusId ? (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(21, 38, 54, 0.28)',
            display: 'grid',
            placeItems: 'center',
            padding: '1rem',
          }}
          onClick={(event) => {
            if (event.target === event.currentTarget && !submitting) {
              setAssigningApparatusId(null)
            }
          }}
        >
          <div className="notes-card" style={{ width: 'min(460px, 100%)' }}>
            <h2>Assign Apparatus</h2>
            <p style={{ margin: '0 0 0.9rem', color: 'var(--muted)' }}>
              Route the selected apparatus to a field technician without leaving the governed lead lane.
            </p>
            <label style={{ display: 'grid', gap: '0.45rem' }}>
              <span style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Technician
              </span>
              <select
                value={selectedTech}
                onChange={(event) => setSelectedTech(event.target.value)}
                style={{
                  padding: '0.8rem 0.9rem',
                  borderRadius: 16,
                  border: '1px solid var(--border)',
                  background: 'rgba(255, 252, 246, 0.96)',
                  color: 'var(--ink)',
                  font: 'inherit',
                }}
              >
                <option value="">Select technician</option>
                {crew.map((tech) => (
                  <option key={tech.id} value={tech.id}>
                    {tech.name || tech.id}
                  </option>
                ))}
              </select>
            </label>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <button className="btn btn-outline" onClick={() => setAssigningApparatusId(null)} disabled={submitting}>
                Cancel
              </button>
              <button className="btn btn-outline" onClick={() => void handleAssign()} disabled={!selectedTech || submitting}>
                {submitting ? 'Saving...' : 'Confirm assignment'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  )
}