'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { buildPmReturnContext, buildPmRoute } from '../route-navigation'

declare global {
  interface Window {
    React?: typeof React
    ApexSchedule?: { ScheduleView?: React.ComponentType<any> }
    ApexDrivers?: { DriversReviewView?: React.ComponentType<any> }
    ApexTracer?: { TracerReviewView?: React.ComponentType<any> }
    ApexVariance?: { VarianceReviewView?: React.ComponentType<any> }
  }
}

const { useState, useEffect, useCallback, useMemo } = React

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'
const SEAM_BASE = `${API_BASE}/mutations`
const READS_BASE = `${API_BASE}/reads`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }

const reviewModules = [
  { id: 'apex-approval-schedule-module', src: '/pm-review/schedule.js', isLoaded: () => !!window.ApexSchedule?.ScheduleView },
  { id: 'apex-approval-drivers-module', src: '/pm-review/drivers.js', isLoaded: () => !!window.ApexDrivers?.DriversReviewView },
  { id: 'apex-approval-tracer-module', src: '/pm-review/tracer.js', isLoaded: () => !!window.ApexTracer?.TracerReviewView },
  { id: 'apex-approval-variance-module', src: '/pm-review/variance.js', isLoaded: () => !!window.ApexVariance?.VarianceReviewView },
] as const

function makeToken(actor: typeof PM_ACTOR) {
  return `Bearer ${btoa(JSON.stringify(actor))}`
}

function attachScript(id: string, src: string, isLoaded: () => boolean) {
  if (isLoaded()) {
    return Promise.resolve()
  }

  const existing = document.getElementById(id) as HTMLScriptElement | null
  if (existing) {
    return new Promise<void>((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error(`Failed to load ${src}`)), { once: true })
    })
  }

  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.id = id
    script.src = src
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`Failed to load ${src}`))
    document.body.appendChild(script)
  })
}

async function seamPost(
  endpoint: string,
  actionType: string,
  mutationClass: string,
  entityId: string,
  payload: Record<string, unknown>,
  reason: string,
) {
  const body = {
    idempotency_key: crypto.randomUUID(),
    mutation_class: mutationClass,
    action_type: actionType,
    entity_id: entityId,
    payload,
    reason: reason || '',
    source: 'online',
    client_timestamp: new Date().toISOString(),
  }

  const response = await fetch(`${SEAM_BASE}/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: makeToken(PM_ACTOR),
    },
    body: JSON.stringify(body),
  })

  return response.json()
}

async function readData(endpoint: string) {
  const response = await fetch(`${READS_BASE}/${endpoint}`, {
    headers: { Authorization: makeToken(PM_ACTOR) },
  })
  return response.json()
}

function useProjectData() {
  const [queue, setQueue] = useState({ tasks: [], workpackages: [], snapshots: [], escalated_issues: [], total_count: 0 } as any)
  const [history, setHistory] = useState<any[]>([])
  const [apparatus, setApparatus] = useState<any[]>([])
  const [tasks, setTasks] = useState<any[]>([])
  const [workpackages, setWorkpackages] = useState<any[]>([])
  const [snapshots, setSnapshots] = useState<any[]>([])
  const [issues, setIssues] = useState<any[]>([])
  const [assignments, setAssignments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const [queueRows, historyRows, apparatusRows, taskRows, workPackageRows, snapshotRows, issueRows, assignmentRows] =
        await Promise.all([
          readData('approval-queue'),
          readData('decision-history'),
          readData('apparatus'),
          readData('tasks'),
          readData('workpackages'),
          readData('snapshots'),
          readData('issues'),
          readData('assignments'),
        ])

      setQueue(queueRows)
      setHistory(historyRows)
      setApparatus(apparatusRows)
      setTasks(taskRows)
      setWorkpackages(workPackageRows)
      setSnapshots(snapshotRows)
      setIssues(issueRows)
      setAssignments(assignmentRows)
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
    const intervalId = setInterval(() => {
      void refresh()
    }, 15_000)
    return () => clearInterval(intervalId)
  }, [refresh])

  return {
    queue,
    history,
    apparatus,
    tasks,
    workpackages,
    snapshots,
    issues,
    assignments,
    loading,
    online,
    refresh,
    lastRefresh,
  }
}

const APPROVAL_INTERNAL_SCREENS = new Set([
  'queue',
  'wp-review',
  'task-review',
  'snapshot-review',
  'escalations',
  'history',
])

const APPROVAL_EXTERNAL_SCREENS = new Set(['schedule', 'drivers', 'tracer', 'variance'])

function getApprovalReturnLabel(screen: string) {
  switch (screen) {
    case 'history':
      return 'PM approval history'
    case 'escalations':
      return 'PM approval escalations'
    case 'wp-review':
      return 'PM work package review'
    case 'task-review':
      return 'PM task review'
    case 'snapshot-review':
      return 'PM snapshot review'
    default:
      return 'PM approval queue'
  }
}

function getImplicitApprovalDetailId(data: any, screen: string) {
  switch (screen) {
    case 'wp-review':
      return data.queue.workpackages.length === 1 ? data.queue.workpackages[0]?.id ?? null : null
    case 'task-review':
      return data.queue.tasks.length === 1 ? data.queue.tasks[0]?.id ?? null : null
    case 'snapshot-review':
      return data.queue.snapshots.length === 1 ? data.queue.snapshots[0]?.id ?? null : null
    case 'escalations':
      return data.queue.escalated_issues.length === 1 ? data.queue.escalated_issues[0]?.id ?? null : null
    default:
      return null
  }
}

function pickFocusedTask(tasks: any[]) {
  return tasks.find((task: any) => task.status !== 'complete') ?? tasks[0] ?? null
}

function getIssueTaskContext(data: any, issueId: string | null) {
  if (!issueId) {
    return null
  }

  const issue =
    data.issues.find((row: any) => row.id === issueId) ||
    data.queue.escalated_issues.find((row: any) => row.id === issueId)

  if (!issue) {
    return null
  }

  const directTask = issue.task_id ? data.tasks.find((row: any) => row.id === issue.task_id) : null
  const apparatusRow = issue.apparatus_id ? data.apparatus.find((row: any) => row.id === issue.apparatus_id) : null
  const apparatusTask = apparatusRow?.task_id ? data.tasks.find((row: any) => row.id === apparatusRow.task_id) : null
  const task = directTask || apparatusTask

  return task ? { taskId: task.id, taskLabel: task.name } : null
}

function getApprovalTraceContext(data: any, screen: string, detailId: string | null) {
  if (!detailId) {
    return null
  }

  if (screen === 'task-review') {
    const task = data.tasks.find((row: any) => row.id === detailId)
    return task ? { taskId: task.id, taskLabel: task.name } : null
  }

  if (screen === 'wp-review') {
    const task = pickFocusedTask(data.tasks.filter((row: any) => row.workpackage_id === detailId))
    return task ? { taskId: task.id, taskLabel: task.name } : null
  }

  if (screen === 'snapshot-review') {
    const snapshot =
      data.snapshots.find((row: any) => row.id === detailId) ||
      data.queue.snapshots.find((row: any) => row.id === detailId)
    const task = snapshot
      ? pickFocusedTask(data.tasks.filter((row: any) => row.workpackage_id === snapshot.workpackage_id))
      : null
    return task ? { taskId: task.id, taskLabel: task.name } : null
  }

  if (screen === 'escalations') {
    return getIssueTaskContext(data, detailId)
  }

  return null
}

function StatusBadge({ status }: { status: string }) {
  return React.createElement('span', { className: `badge status-${status}` }, status?.replace(/_/g, ' '))
}

function TypeBadge({ type }: { type: string }) {
  return React.createElement('span', { className: `badge type-badge-${type}` }, type)
}

function SeverityLabel({ severity }: { severity: string }) {
  return React.createElement('span', { className: `severity-${severity}` }, severity)
}

function ApprovalQueue({ data, navigate }: { data: any; navigate: (target: string, id?: string | null) => void }) {
  const { queue } = data
  const allItems = [
    ...queue.workpackages.map((workPackage: any) => ({ ...workPackage, _type: 'workpackage', _name: workPackage.name })),
    ...queue.tasks.map((task: any) => ({ ...task, _type: 'task', _name: task.name })),
    ...queue.snapshots.map((snapshot: any) => ({
      ...snapshot,
      _type: 'snapshot',
      _name: `Snapshot: ${snapshot.workpackage_id} (${snapshot.period_start} - ${snapshot.period_end})`,
    })),
  ]

  return React.createElement(
    'div',
    null,
    React.createElement('h1', { className: 'text-xl font-bold resa-blue mb-1' }, 'Approval Queue'),
    React.createElement('p', { className: 'text-sm text-gray-500 mb-4' }, `${queue.total_count} items awaiting review`),
    allItems.length === 0
      ? React.createElement('div', { className: 'card text-center text-gray-400 py-8' }, 'No items awaiting review')
      : React.createElement(
          'div',
          { className: 'card' },
          React.createElement(
            'table',
            null,
            React.createElement(
              'thead',
              null,
              React.createElement(
                'tr',
                null,
                React.createElement('th', null, 'Type'),
                React.createElement('th', null, 'Name'),
                React.createElement('th', null, 'State'),
                React.createElement('th', null, 'Project'),
                React.createElement('th', null, 'Action'),
              ),
            ),
            React.createElement(
              'tbody',
              null,
              allItems.map((item: any) =>
                React.createElement(
                  'tr',
                  {
                    key: item.id,
                    className: 'clickable',
                    onClick: () => navigate(item._type === 'workpackage' ? 'wp-review' : item._type === 'task' ? 'task-review' : 'snapshot-review', item.id),
                  },
                  React.createElement('td', null, React.createElement(TypeBadge, { type: item._type })),
                  React.createElement('td', { className: 'font-medium' }, item._name),
                  React.createElement('td', null, React.createElement(StatusBadge, { status: item.status })),
                  React.createElement('td', { className: 'text-xs text-gray-500' }, item.project_id),
                  React.createElement('td', null, React.createElement('button', { className: 'btn btn-outline', style: { fontSize: 11, padding: '3px 8px' } }, 'Review →')),
                ),
              ),
            ),
          ),
        ),
    queue.escalated_issues.length > 0 &&
      React.createElement(
        'div',
        { className: 'card mt-4', style: { borderLeft: '4px solid #dc2626' } },
        React.createElement('h3', { className: 'text-sm font-bold text-red-600 mb-2' }, `Escalated Issues (${queue.escalated_issues.length})`),
        React.createElement('p', { className: 'text-xs text-gray-500 mb-2' }, 'Issues escalated to PM for disposition'),
        queue.escalated_issues.map((issue: any) =>
          React.createElement(
            'div',
            {
              key: issue.id,
              className: 'flex justify-between items-center py-2 border-b border-gray-100 cursor-pointer',
              onClick: () => navigate('escalations', issue.id),
            },
            React.createElement('span', { className: 'font-medium text-sm' }, issue.title),
            React.createElement(
              'div',
              { className: 'flex gap-2' },
              React.createElement(SeverityLabel, { severity: issue.severity }),
              issue.blocks_completion && React.createElement('span', { className: 'badge bg-red-100 text-red-700' }, 'BLOCKING'),
            ),
          ),
        ),
      ),
  )
}

function WorkPackageReview({ wpId, data, navigate, onMutate }: { wpId: string; data: any; navigate: (target: string, id?: string | null) => void; onMutate: () => void }) {
  const { workpackages, tasks, apparatus, issues } = data
  const workPackage = workpackages.find((row: any) => row.id === wpId)
  const [reason, setReason] = useState('')
  const [result, setResult] = useState<any>(null)

  if (!workPackage) {
    return React.createElement('div', { className: 'card' }, 'WorkPackage not found')
  }

  const workPackageTasks = tasks.filter((task: any) => task.workpackage_id === wpId)
  const workPackageApparatus = apparatus.filter((item: any) => workPackageTasks.some((task: any) => task.id === item.task_id))
  const workPackageIssues = issues.filter((issue: any) => workPackageApparatus.some((item: any) => item.id === issue.apparatus_id))
  const blockingIssues = workPackageIssues.filter((issue: any) => issue.blocks_completion && issue.status !== 'resolved' && issue.status !== 'closed')
  const completeTasks = workPackageTasks.filter((task: any) => task.status === 'complete').length
  const completeApparatus = workPackageApparatus.filter((item: any) => item.status === 'complete').length
  const canApprove = workPackage.status === 'awaiting_review' && blockingIssues.length === 0

  const doAction = async (action: string, payload: Record<string, unknown>) => {
    if (!reason.trim()) {
      window.alert('Reason/note required')
      return
    }

    const nextResult = await seamPost('workpackages', action, 'C', wpId, payload, reason)
    setResult(nextResult)
    if (nextResult.status === 'accepted') {
      setTimeout(() => {
        onMutate()
        navigate('queue')
      }, 800)
    }
  }

  return React.createElement(
    'div',
    null,
    React.createElement('button', { className: 'text-sm resa-blue mb-3 cursor-pointer', onClick: () => navigate('queue') }, '← Back to Queue'),
    React.createElement(
      'div',
      { className: 'flex items-center gap-3 mb-4' },
      React.createElement(TypeBadge, { type: 'workpackage' }),
      React.createElement('h1', { className: 'text-xl font-bold resa-blue' }, workPackage.name),
      React.createElement(StatusBadge, { status: workPackage.status }),
    ),
    React.createElement(
      'div',
      { className: 'grid grid-cols-4 gap-3 mb-4' },
      React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold resa-blue' }, `${completeTasks}/${workPackageTasks.length}`), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Tasks Complete')),
      React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold resa-blue' }, `${completeApparatus}/${workPackageApparatus.length}`), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Apparatus Complete')),
      React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold', style: { color: blockingIssues.length > 0 ? '#dc2626' : '#059669' } }, blockingIssues.length), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Blocking Issues')),
      React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold resa-blue' }, `${workPackageApparatus.length > 0 ? Math.round((completeApparatus / workPackageApparatus.length) * 100) : 0}%`), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Progress')),
    ),
    blockingIssues.length > 0 &&
      React.createElement(
        'div',
        { className: 'blocker-warning' },
        React.createElement('h3', { className: 'text-sm font-bold text-red-700 mb-1' }, `⚠ ${blockingIssues.length} Unresolved Blocking Issue(s) — Approval Disabled`),
        blockingIssues.map((issue: any) => React.createElement('div', { key: issue.id, className: 'text-sm py-1' }, React.createElement(SeverityLabel, { severity: issue.severity }), ' ', issue.title)),
        React.createElement('p', { className: 'text-xs text-red-500 mt-2' }, 'Blocking issues must be resolved before this WorkPackage can be approved. This is a server-enforced precondition.'),
      ),
    React.createElement(
      'div',
      { className: 'card' },
      React.createElement('h3', { className: 'text-sm font-bold text-gray-700 mb-2' }, 'Tasks'),
      React.createElement(
        'table',
        null,
        React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Task'), React.createElement('th', null, 'Status'), React.createElement('th', null, 'Apparatus'), React.createElement('th', null, 'Issues'))),
        React.createElement(
          'tbody',
          null,
          workPackageTasks.map((task: any) => {
            const taskApparatus = workPackageApparatus.filter((item: any) => item.task_id === task.id)
            const taskIssues = workPackageIssues.filter((issue: any) => taskApparatus.some((item: any) => item.id === issue.apparatus_id))
            return React.createElement(
              'tr',
              { key: task.id },
              React.createElement('td', { className: 'font-medium' }, task.name),
              React.createElement('td', null, React.createElement(StatusBadge, { status: task.status })),
              React.createElement('td', { className: 'text-xs' }, `${taskApparatus.filter((item: any) => item.status === 'complete').length}/${taskApparatus.length}`),
              React.createElement('td', null, taskIssues.length > 0 ? React.createElement('span', { className: 'text-red-500 text-xs font-bold' }, `${taskIssues.length}`) : '—'),
            )
          }),
        ),
      ),
    ),
    workPackageIssues.length > 0 &&
      React.createElement(
        'div',
        { className: 'card' },
        React.createElement('h3', { className: 'text-sm font-bold text-gray-700 mb-2' }, `Issues (${workPackageIssues.length})`),
        workPackageIssues.map((issue: any) =>
          React.createElement(
            'div',
            { key: issue.id, className: 'flex justify-between py-1 border-b border-gray-100 text-sm' },
            React.createElement('span', null, issue.title),
            React.createElement('div', { className: 'flex gap-2' }, React.createElement(SeverityLabel, { severity: issue.severity }), React.createElement(StatusBadge, { status: issue.status }), issue.blocks_completion && React.createElement('span', { className: 'badge bg-red-100 text-red-700' }, 'BLOCKING')),
          ),
        ),
      ),
    React.createElement(
      'div',
      { className: 'card', style: { borderTop: '3px solid #015687' } },
      React.createElement('h3', { className: 'text-sm font-bold resa-blue mb-3' }, 'Decision'),
      React.createElement('textarea', { className: 'w-full border border-gray-300 rounded p-2 text-sm mb-3', rows: 3, placeholder: 'Decision reason/note (required)...', value: reason, onChange: (event: any) => setReason(event.target.value) }),
      React.createElement('p', { className: 'text-xs text-gray-400 mb-3' }, 'Class C server-authoritative — requires online connectivity.'),
      result && React.createElement('div', { className: `text-sm mb-3 p-2 rounded ${result.status === 'accepted' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}` }, result.status === 'accepted' ? '✓ Decision recorded' : `✗ ${result.error?.message || JSON.stringify(result)}`),
      React.createElement('div', { className: 'flex gap-2' }, React.createElement('button', { className: 'btn btn-approve', disabled: !canApprove, onClick: () => void doAction('approve', { status: 'complete' }), title: !canApprove ? 'Blocked by unresolved issues' : '' }, canApprove ? 'Approve' : 'Approve (blocked)'), React.createElement('button', { className: 'btn btn-reject', onClick: () => void doAction('reject', { status: 'active' }) }, 'Reject'), React.createElement('button', { className: 'btn btn-escalate', onClick: () => void doAction('escalate_review', {}) }, 'Escalate')),
    ),
  )
}

function TaskReview({ taskId, data, navigate, onMutate }: { taskId: string; data: any; navigate: (target: string, id?: string | null) => void; onMutate: () => void }) {
  const { tasks, apparatus, issues, workpackages } = data
  const task = tasks.find((row: any) => row.id === taskId)
  const [reason, setReason] = useState('')
  const [result, setResult] = useState<any>(null)

  if (!task) {
    return React.createElement('div', { className: 'card' }, 'Task not found')
  }

  const workPackage = workpackages.find((row: any) => row.id === task.workpackage_id)
  const taskApparatus = apparatus.filter((item: any) => item.task_id === taskId)
  const taskIssues = issues.filter((issue: any) => taskApparatus.some((item: any) => item.id === issue.apparatus_id))
  const blockingIssues = taskIssues.filter((issue: any) => issue.blocks_completion && issue.status !== 'resolved' && issue.status !== 'closed')
  const canApprove = task.status === 'awaiting_review' && blockingIssues.length === 0

  const doAction = async (action: string, payload: Record<string, unknown>) => {
    if (!reason.trim()) {
      window.alert('Reason/note required')
      return
    }

    const nextResult = await seamPost('tasks', action, 'C', taskId, payload, reason)
    setResult(nextResult)
    if (nextResult.status === 'accepted') {
      setTimeout(() => {
        onMutate()
        navigate('queue')
      }, 800)
    }
  }

  return React.createElement(
    'div',
    null,
    React.createElement('button', { className: 'text-sm resa-blue mb-3 cursor-pointer', onClick: () => navigate('queue') }, '← Back to Queue'),
    React.createElement('div', { className: 'flex items-center gap-3 mb-4' }, React.createElement(TypeBadge, { type: 'task' }), React.createElement('h1', { className: 'text-xl font-bold resa-blue' }, task.name), React.createElement(StatusBadge, { status: task.status })),
    React.createElement('p', { className: 'text-sm text-gray-500 mb-4' }, `WorkPackage: ${workPackage?.name || task.workpackage_id}`),
    React.createElement('div', { className: 'grid grid-cols-3 gap-3 mb-4' }, React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold resa-blue' }, `${taskApparatus.filter((item: any) => item.status === 'complete').length}/${taskApparatus.length}`), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Apparatus Complete')), React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold', style: { color: blockingIssues.length > 0 ? '#dc2626' : '#059669' } }, blockingIssues.length), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Blocking Issues')), React.createElement('div', { className: 'card text-center' }, React.createElement('div', { className: 'text-2xl font-bold resa-blue' }, taskIssues.length), React.createElement('div', { className: 'text-xs text-gray-500' }, 'Total Issues'))),
    blockingIssues.length > 0 && React.createElement('div', { className: 'blocker-warning' }, React.createElement('h3', { className: 'text-sm font-bold text-red-700 mb-1' }, `⚠ ${blockingIssues.length} Blocking Issue(s) — Approval Disabled`), blockingIssues.map((issue: any) => React.createElement('div', { key: issue.id, className: 'text-sm py-1' }, React.createElement(SeverityLabel, { severity: issue.severity }), ' ', issue.title))),
    React.createElement('div', { className: 'card' }, React.createElement('h3', { className: 'text-sm font-bold text-gray-700 mb-2' }, 'Apparatus'), taskApparatus.map((item: any) => React.createElement('div', { key: item.id, className: 'flex justify-between py-1 border-b border-gray-100 text-sm' }, React.createElement('span', { className: 'font-medium' }, item.name), React.createElement('div', { className: 'flex gap-2' }, React.createElement('span', { className: 'text-xs text-gray-500' }, item.neta_standard), React.createElement(StatusBadge, { status: item.status }))))),
    React.createElement('div', { className: 'card', style: { borderTop: '3px solid #015687' } }, React.createElement('h3', { className: 'text-sm font-bold resa-blue mb-3' }, 'Decision'), React.createElement('textarea', { className: 'w-full border border-gray-300 rounded p-2 text-sm mb-3', rows: 3, placeholder: 'Decision reason/note (required)...', value: reason, onChange: (event: any) => setReason(event.target.value) }), result && React.createElement('div', { className: `text-sm mb-3 p-2 rounded ${result.status === 'accepted' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}` }, result.status === 'accepted' ? '✓ Decision recorded' : `✗ ${result.error?.message || JSON.stringify(result)}`), React.createElement('div', { className: 'flex gap-2' }, React.createElement('button', { className: 'btn btn-approve', disabled: !canApprove, onClick: () => void doAction('approve', { status: 'complete' }) }, canApprove ? 'Approve' : 'Approve (blocked)'), React.createElement('button', { className: 'btn btn-reject', onClick: () => void doAction('reject', { status: 'rejected' }) }, 'Reject'), React.createElement('button', { className: 'btn btn-escalate', onClick: () => void doAction('escalate_review', {}) }, 'Escalate'))),
  )
}

function SnapshotReview({
  snapId,
  data,
  navigate,
  onMutate,
  onTraceTask,
  onViewVariance,
  onViewSchedule,
  onViewDrivers,
}: {
  snapId: string
  data: any
  navigate: (target: string, id?: string | null) => void
  onMutate: () => void
  onTraceTask: (taskInfo: { taskId?: string; taskLabel?: string } | null) => void
  onViewVariance: (taskId: string | null) => void
  onViewSchedule: (taskId: string | null) => void
  onViewDrivers: (taskId: string | null) => void
}) {
  const [reason, setReason] = useState('')
  const [result, setResult] = useState<any>(null)

  const snapshot = data.snapshots.find((row: any) => row.id === snapId) || data.queue.snapshots.find((row: any) => row.id === snapId)
  if (!snapshot) {
    return React.createElement('div', { className: 'card' }, 'Snapshot not found')
  }

  const workPackage = data.workpackages.find((row: any) => row.id === snapshot.workpackage_id)
  const focusedTask = pickFocusedTask(data.tasks.filter((row: any) => row.workpackage_id === snapshot.workpackage_id))

  const doAction = async (action: string, payload: Record<string, unknown>) => {
    if (!reason.trim()) {
      window.alert('Reason/note required')
      return
    }

    const nextResult = await seamPost('snapshots', action, 'C', snapId, payload, reason)
    setResult(nextResult)
    if (nextResult.status === 'accepted') {
      setTimeout(() => {
        onMutate()
        navigate('queue')
      }, 800)
    }
  }

  return React.createElement(
    'div',
    null,
    React.createElement('button', { className: 'text-sm resa-blue mb-3 cursor-pointer', onClick: () => navigate('queue') }, '← Back to Queue'),
    React.createElement('div', { className: 'flex items-center gap-3 mb-4' }, React.createElement(TypeBadge, { type: 'snapshot' }), React.createElement('h1', { className: 'text-xl font-bold resa-blue' }, 'Progress Snapshot'), React.createElement(StatusBadge, { status: snapshot.status })),
    React.createElement('div', { className: 'card' }, React.createElement('div', { className: 'grid grid-cols-2 gap-4 text-sm' }, React.createElement('div', null, React.createElement('span', { className: 'text-gray-500' }, 'WorkPackage: '), React.createElement('span', { className: 'font-medium' }, workPackage?.name || snapshot.workpackage_id)), React.createElement('div', null, React.createElement('span', { className: 'text-gray-500' }, 'Period: '), React.createElement('span', null, `${snapshot.period_start} — ${snapshot.period_end}`)), React.createElement('div', null, React.createElement('span', { className: 'text-gray-500' }, 'Completion: '), React.createElement('span', { className: 'font-bold' }, `${snapshot.percent_complete}%`)), React.createElement('div', null, React.createElement('span', { className: 'text-gray-500' }, 'Hours Reported: '), React.createElement('span', null, snapshot.hours_reported)), React.createElement('div', null, React.createElement('span', { className: 'text-gray-500' }, 'Submitted By: '), React.createElement('span', null, snapshot.submitted_by)))),
    focusedTask && React.createElement('div', { className: 'card' }, React.createElement('h3', { className: 'text-sm font-bold text-gray-700 mb-3' }, 'Related Task Actions'), React.createElement('div', { className: 'flex gap-2 flex-wrap' }, React.createElement('button', { className: 'btn btn-outline', onClick: () => onTraceTask({ taskId: focusedTask.id, taskLabel: focusedTask.name }) }, 'Trace Task'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewSchedule(focusedTask.id) }, 'Open Schedule'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewDrivers(focusedTask.id) }, 'Open Drivers'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewVariance(focusedTask.id) }, 'Open Variance'))),
    React.createElement('div', { className: 'card' }, React.createElement('div', { className: 'mb-3' }, React.createElement('span', { className: 'text-sm text-gray-500' }, 'Progress'), React.createElement('div', { className: 'progress-bar mt-1', style: { height: 10 } }, React.createElement('div', { className: 'progress-fill', style: { width: `${snapshot.percent_complete}%` } }))), React.createElement('p', { className: 'text-xs text-gray-400' }, 'Approved snapshot becomes period truth. Does not trigger billing (Class D deferred).')),
    React.createElement('div', { className: 'card', style: { borderTop: '3px solid #015687' } }, React.createElement('h3', { className: 'text-sm font-bold resa-blue mb-3' }, 'Decision'), React.createElement('textarea', { className: 'w-full border border-gray-300 rounded p-2 text-sm mb-3', rows: 3, placeholder: 'Decision reason/note (required)...', value: reason, onChange: (event: any) => setReason(event.target.value) }), result && React.createElement('div', { className: `text-sm mb-3 p-2 rounded ${result.status === 'accepted' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}` }, result.status === 'accepted' ? '✓ Decision recorded' : `✗ ${result.error?.message || JSON.stringify(result)}`), React.createElement('div', { className: 'flex gap-2' }, React.createElement('button', { className: 'btn btn-approve', disabled: snapshot.status !== 'submitted', onClick: () => void doAction('approve', { status: 'approved' }) }, 'Approve'), React.createElement('button', { className: 'btn btn-reject', onClick: () => void doAction('reject', { status: 'rejected' }) }, 'Reject'))),
  )
}

function EscalationQueue({
  data,
  detailId,
  navigate,
  onMutate,
  onTraceTask,
  onViewVariance,
  onViewSchedule,
  onViewDrivers,
}: {
  data: any
  detailId: string | null
  navigate: (target: string, id?: string | null) => void
  onMutate: () => void
  onTraceTask: (taskInfo: { taskId?: string; taskLabel?: string } | null) => void
  onViewVariance: (taskId: string | null) => void
  onViewSchedule: (taskId: string | null) => void
  onViewDrivers: (taskId: string | null) => void
}) {
  const { issues, apparatus, tasks, workpackages } = data
  const escalatedIssues = issues.filter((issue: any) => issue.status === 'escalated')
  const [activeIssueId, setActiveIssueId] = useState<string | null>(() => {
    if (detailId) {
      return detailId
    }

    if (typeof window !== 'undefined') {
      return new URLSearchParams(window.location.search).get('detailId')
    }

    return null
  })
  const [reason, setReason] = useState('')
  const [result, setResult] = useState<any>(null)
  const selectedIssueId = detailId || activeIssueId

  useEffect(() => {
    const nextActiveIssueId = detailId || (typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('detailId') : null)
    setActiveIssueId(nextActiveIssueId)
    setReason('')
    setResult(null)
  }, [detailId])

  const doAction = async (issueId: string, action: string, payload: Record<string, unknown>) => {
    if (!reason.trim()) {
      window.alert('Reason required')
      return
    }

    const nextResult = await seamPost('issues', action, 'C', issueId, payload, reason)
    setResult({ id: issueId, ...nextResult })
    if (nextResult.status === 'accepted') {
      setActiveIssueId(null)
      setReason('')
      onMutate()
      navigate('escalations')
    }
  }

  return React.createElement(
    'div',
    null,
    React.createElement('h1', { className: 'text-xl font-bold resa-blue mb-4' }, 'Escalation Queue'),
    escalatedIssues.length === 0
      ? React.createElement('div', { className: 'card text-center text-gray-400 py-8' }, 'No escalated items')
      : escalatedIssues.map((issue: any) => {
          const apparatusRow = apparatus.find((row: any) => row.id === issue.apparatus_id)
          const task = apparatusRow ? tasks.find((row: any) => row.id === apparatusRow.task_id) : null
          const workPackage = task ? workpackages.find((row: any) => row.id === task.workpackage_id) : null
          const isActive = selectedIssueId === issue.id

          return React.createElement(
            'div',
            { key: issue.id, className: 'card', style: isActive ? { borderLeft: '4px solid #015687' } : {} },
            React.createElement(
              'div',
              { className: 'flex justify-between items-start mb-2' },
              React.createElement('div', null, React.createElement('h3', { className: 'font-medium' }, issue.title), React.createElement('div', { className: 'flex gap-2 mt-1' }, React.createElement(SeverityLabel, { severity: issue.severity }), React.createElement(StatusBadge, { status: issue.status }), issue.blocks_completion && React.createElement('span', { className: 'badge bg-red-100 text-red-700' }, 'BLOCKING'))),
              !isActive && React.createElement('button', { className: 'btn btn-outline', onClick: () => { setActiveIssueId(issue.id); navigate('escalations', issue.id) } }, 'Take Action'),
            ),
            React.createElement('div', { className: 'text-xs text-gray-500 mb-2' }, `Apparatus: ${apparatusRow?.name || issue.apparatus_id} • Task: ${task?.name || '—'} • WP: ${workPackage?.name || '—'} • Reporter: ${issue.reported_by}`),
            isActive && React.createElement('div', { className: 'mt-3 pt-3 border-t border-gray-200' }, task && React.createElement('div', { className: 'flex gap-2 mb-3 flex-wrap' }, React.createElement('button', { className: 'btn btn-outline', onClick: () => onTraceTask({ taskId: task.id, taskLabel: task.name }) }, 'Trace Task'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewSchedule(task.id) }, 'Open Schedule'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewDrivers(task.id) }, 'Open Drivers'), React.createElement('button', { className: 'btn btn-outline', onClick: () => onViewVariance(task.id) }, 'Open Variance')), React.createElement('textarea', { className: 'w-full border border-gray-300 rounded p-2 text-sm mb-3', rows: 2, placeholder: 'Disposition reason (required)...', value: reason, onChange: (event: any) => setReason(event.target.value) }), result && result.id === issue.id && React.createElement('div', { className: `text-sm mb-2 p-2 rounded ${result.status === 'accepted' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}` }, result.status === 'accepted' ? '✓ Done' : `✗ ${result.error?.message || 'Failed'}`), React.createElement('div', { className: 'flex gap-2' }, React.createElement('button', { className: 'btn btn-approve', onClick: () => void doAction(issue.id, 'resolve_escalated', { status: 'resolved' }) }, 'Resolve'), React.createElement('button', { className: 'btn btn-escalate', onClick: () => void doAction(issue.id, 're_escalate', { status: 'escalated' }) }, 'Re-escalate'), React.createElement('button', { className: 'btn btn-return', onClick: () => void doAction(issue.id, 'return_to_lead', { status: 'in_review' }) }, 'Return to Lead'), React.createElement('button', { className: 'btn btn-outline', onClick: () => { setActiveIssueId(null); navigate('escalations') } }, 'Cancel'))),
          )
        }),
  )
}

function DecisionHistory({ data }: { data: any }) {
  const { history } = data
  const [filterType, setFilterType] = useState('all')
  const [filterAction, setFilterAction] = useState('all')
  const [search, setSearch] = useState('')

  const filteredHistory = history.filter((entry: any) => {
    if (filterType !== 'all' && entry.entity_type !== filterType) {
      return false
    }
    if (filterAction !== 'all' && entry.action_type !== filterAction) {
      return false
    }
    if (search && !JSON.stringify(entry).toLowerCase().includes(search.toLowerCase())) {
      return false
    }
    return true
  })

  return React.createElement(
    'div',
    null,
    React.createElement('h1', { className: 'text-xl font-bold resa-blue mb-4' }, 'Decision History'),
    React.createElement('div', { className: 'card flex gap-3 items-center mb-4' }, React.createElement('select', { value: filterType, onChange: (event: any) => setFilterType(event.target.value) }, React.createElement('option', { value: 'all' }, 'All Types'), ['task', 'workpackage', 'snapshot', 'issue'].map((type) => React.createElement('option', { key: type, value: type }, type))), React.createElement('select', { value: filterAction, onChange: (event: any) => setFilterAction(event.target.value) }, React.createElement('option', { value: 'all' }, 'All Actions'), ['approve', 'reject', 'escalate_review', 'resolve_escalated', 're_escalate', 'return_to_lead'].map((action) => React.createElement('option', { key: action, value: action }, action.replace(/_/g, ' ')))), React.createElement('input', { type: 'text', placeholder: 'Search...', value: search, onChange: (event: any) => setSearch(event.target.value), className: 'flex-1' })),
    filteredHistory.length === 0
      ? React.createElement('div', { className: 'card text-center text-gray-400 py-8' }, 'No decisions recorded yet')
      : React.createElement('div', { className: 'card' }, React.createElement('table', null, React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Time'), React.createElement('th', null, 'Type'), React.createElement('th', null, 'Entity'), React.createElement('th', null, 'Action'), React.createElement('th', null, 'Actor'), React.createElement('th', null, 'From → To'), React.createElement('th', null, 'Reason'))), React.createElement('tbody', null, filteredHistory.map((entry: any, index: number) => React.createElement('tr', { key: `${entry.entity_id ?? 'entry'}-${index}` }, React.createElement('td', { className: 'text-xs text-gray-500' }, entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'), React.createElement('td', null, React.createElement(TypeBadge, { type: entry.entity_type || 'unknown' })), React.createElement('td', { className: 'text-xs font-medium' }, entry.entity_id), React.createElement('td', null, React.createElement('span', { className: 'badge bg-gray-100 text-gray-700' }, entry.action_type?.replace(/_/g, ' '))), React.createElement('td', { className: 'text-xs' }, `${entry.actor_id} (${entry.actor_role})`), React.createElement('td', { className: 'text-xs' }, `${entry.from_state?.status || '—'} → ${entry.to_state?.status || '—'}`), React.createElement('td', { className: 'text-xs text-gray-500', style: { maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' } }, entry.reason || '—')))))),
  )
}

function ApprovalSurfaceApp() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const data = useProjectData()
  const [browserDetailId, setBrowserDetailId] = useState<string | null>(null)
  const requestedScreen = searchParams.get('screen')
  const screen = requestedScreen && APPROVAL_INTERNAL_SCREENS.has(requestedScreen) ? requestedScreen : 'queue'
  const detailId = searchParams.get('detailId')
  const resolvedDetailId = detailId || browserDetailId || getImplicitApprovalDetailId(data, screen)
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'
  const approvalReturnLabel = getApprovalReturnLabel(screen)
  const approvalTraceContext = useMemo(() => getApprovalTraceContext(data, screen, resolvedDetailId), [data, resolvedDetailId, screen])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    setBrowserDetailId(new URLSearchParams(window.location.search).get('detailId'))
  }, [searchParams])

  const navigate = useCallback((target: string, id?: string | null) => {
    if (APPROVAL_EXTERNAL_SCREENS.has(target)) {
      return
    }

    router.push(
      buildPmRoute('/pm-review/approval', {
        screen: target,
        detailId: id || null,
      }),
    )
  }, [router])

  useEffect(() => {
    if (detailId || !resolvedDetailId || !APPROVAL_INTERNAL_SCREENS.has(screen) || screen === 'queue' || screen === 'history') {
      return
    }

    navigate(screen, resolvedDetailId)
  }, [detailId, navigate, resolvedDetailId, screen])

  const onTraceTask = useCallback((taskInfo: any) => {
    const taskId = taskInfo?.taskId || approvalTraceContext?.taskId || null
    const taskLabel = taskInfo?.taskLabel || approvalTraceContext?.taskLabel || null

    router.push(
      buildPmRoute('/pm-review/tracer', {
        taskId,
        taskLabel,
        maxDepth: 10,
        ...buildPmReturnContext('/pm-review/approval', { screen, detailId: resolvedDetailId, focusTaskId: taskId, taskLabel }, approvalReturnLabel),
      }),
    )
  }, [approvalReturnLabel, approvalTraceContext, resolvedDetailId, router, screen])

  const onViewVariance = useCallback((taskId: string | null) => {
    const resolvedTaskId = taskId || approvalTraceContext?.taskId || null

    router.push(
      buildPmRoute('/pm-review/variance', {
        projectId: 'stack-dc',
        focusTaskId: resolvedTaskId,
        ...buildPmReturnContext('/pm-review/approval', { screen, detailId: resolvedDetailId }, approvalReturnLabel),
      }),
    )
  }, [approvalReturnLabel, approvalTraceContext, resolvedDetailId, router, screen])

  const onViewSchedule = useCallback((taskId: string | null) => {
    const resolvedTaskId = taskId || approvalTraceContext?.taskId || null

    router.push(
      buildPmRoute('/pm-review/schedule', {
        focusTaskId: resolvedTaskId,
        ...buildPmReturnContext('/pm-review/approval', { screen, detailId: resolvedDetailId }, approvalReturnLabel),
      }),
    )
  }, [approvalReturnLabel, approvalTraceContext, resolvedDetailId, router, screen])

  const onViewDrivers = useCallback((taskId: string | null) => {
    const resolvedTaskId = taskId || approvalTraceContext?.taskId || null

    router.push(
      buildPmRoute('/pm-review', {
        focusTaskId: resolvedTaskId,
        projectId: 'stack-dc',
        ...buildPmReturnContext('/pm-review/approval', { screen, detailId: resolvedDetailId }, approvalReturnLabel),
      }),
    )
  }, [approvalReturnLabel, approvalTraceContext, resolvedDetailId, router, screen])

  const navItems = [
    { key: 'queue', label: 'Approval Queue', icon: '📋' },
    { key: 'escalations', label: 'Escalations', icon: '⚠️' },
    { key: 'history', label: 'Decision History', icon: '📜' },
    { key: 'schedule', label: 'Schedule', icon: '📊' },
    { key: 'drivers', label: 'Drivers', icon: '🎯' },
    { key: 'tracer', label: 'Tracer', icon: '🔍' },
    { key: 'variance', label: 'Variance', icon: '📈' },
  ]

  const renderedScreen = useMemo(() => {
    if (data.loading) {
      return React.createElement('div', { className: 'card text-center p-8' }, 'Loading...')
    }

    switch (screen) {
      case 'queue':
        return React.createElement(ApprovalQueue, { data, navigate })
      case 'wp-review':
        return resolvedDetailId
          ? React.createElement(WorkPackageReview, { wpId: resolvedDetailId, data, navigate, onMutate: data.refresh })
          : React.createElement('div', { className: 'card' }, 'Select a work package from the queue to review it.')
      case 'task-review':
        return resolvedDetailId
          ? React.createElement(TaskReview, { taskId: resolvedDetailId, data, navigate, onMutate: data.refresh })
          : React.createElement('div', { className: 'card' }, 'Select a task from the queue to review it.')
      case 'snapshot-review':
        return resolvedDetailId
          ? React.createElement(SnapshotReview, {
              snapId: resolvedDetailId,
              data,
              navigate,
              onMutate: data.refresh,
              onTraceTask,
              onViewVariance,
              onViewSchedule,
              onViewDrivers,
            })
          : React.createElement('div', { className: 'card' }, 'Select a snapshot from the queue to review it.')
      case 'escalations':
        return React.createElement(EscalationQueue, {
          data,
          detailId: resolvedDetailId,
          navigate,
          onMutate: data.refresh,
          onTraceTask,
          onViewVariance,
          onViewSchedule,
          onViewDrivers,
        })
      case 'history':
        return React.createElement(DecisionHistory, { data })
      case 'schedule':
        return window.ApexSchedule?.ScheduleView
          ? React.createElement(window.ApexSchedule.ScheduleView, { onTraceTask, onViewVariance, onViewDrivers, focusTaskId: null })
          : React.createElement('div', { className: 'card' }, 'Schedule module not loaded. Reload the page; schedule.js must load alongside index.html.')
      case 'drivers':
        return window.ApexDrivers?.DriversReviewView
          ? React.createElement(window.ApexDrivers.DriversReviewView as React.ComponentType<any>, { onTraceTask, onViewVariance, onViewSchedule, focusTaskId: null })
          : React.createElement('div', { className: 'card' }, 'Drivers module not loaded. Reload the page; drivers.js must load alongside index.html.')
      case 'tracer':
        return window.ApexTracer?.TracerReviewView
          ? React.createElement(window.ApexTracer.TracerReviewView, { taskId: null, maxDepth: 10, taskLabel: null, onTraceTask })
          : React.createElement('div', { className: 'card' }, 'Tracer module not loaded. Reload the page; tracer.js must load alongside index.html.')
      case 'variance':
        return window.ApexVariance?.VarianceReviewView
          ? React.createElement(window.ApexVariance.VarianceReviewView, { onTraceTask, onViewSchedule, onViewDrivers, focusTaskId: null })
          : React.createElement('div', { className: 'card' }, 'Variance module not loaded. Reload the page; variance.js must load alongside index.html.')
      default:
        return React.createElement(ApprovalQueue, { data, navigate })
    }
  }, [data, detailId, navigate, onTraceTask, onViewDrivers, onViewSchedule, onViewVariance, screen])

  return React.createElement(
    'div',
    { className: 'pm-approval-shell' },
    React.createElement(
      'div',
      { className: 'sidebar' },
      React.createElement('div', { className: 'mb-6' }, React.createElement('div', { className: 'font-bold text-lg resa-blue' }, 'APEX PM'), React.createElement('div', { className: 'text-xs resa-green font-semibold' }, 'Approval Surface'), React.createElement('div', { className: 'text-xs text-gray-400 mt-1' }, 'pm-001 • proj-001'), React.createElement('div', { className: 'text-xs mt-2' }, React.createElement('span', { className: data.online ? 'online-indicator' : 'offline-indicator' }), data.online ? 'Online' : 'Offline — decisions disabled')),
      navItems.map((item) => React.createElement('div', { key: item.key, className: `nav-item ${screen === item.key ? 'active' : ''}`, onClick: () => {
        if (item.key === 'schedule') {
          onViewSchedule(null)
          return
        }
        if (item.key === 'drivers') {
          onViewDrivers(null)
          return
        }
        if (item.key === 'tracer') {
          onTraceTask(null)
          return
        }
        if (item.key === 'variance') {
          onViewVariance(null)
          return
        }
        navigate(item.key)
      } }, `${item.icon} ${item.label}`, item.key === 'queue' && data.queue.total_count > 0 && React.createElement('span', { style: { marginLeft: 8, background: '#dc2626', color: 'white', borderRadius: '50%', padding: '1px 6px', fontSize: 10 } }, data.queue.total_count), item.key === 'escalations' && data.queue.escalated_issues?.length > 0 && React.createElement('span', { style: { marginLeft: 8, background: '#d97706', color: 'white', borderRadius: '50%', padding: '1px 6px', fontSize: 10 } }, data.queue.escalated_issues.length))),
      React.createElement('div', { className: 'mt-6 pt-4 border-t border-gray-200' }, React.createElement('div', { className: 'text-xs text-gray-400' }, 'Last refresh:'), React.createElement('div', { className: 'text-xs text-gray-500' }, data.lastRefresh?.toLocaleTimeString() || '—'), React.createElement('button', { className: 'btn btn-outline mt-2 w-full text-xs', onClick: data.refresh }, 'Refresh')),
    ),
    React.createElement('div', { className: 'main-content' }, !data.online && React.createElement('div', { style: { background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: '8px 12px', marginBottom: 12 } }, React.createElement('span', { className: 'offline-indicator' }), React.createElement('span', { className: 'text-sm text-red-700 font-medium' }, 'Connectivity lost — all decision actions are disabled. Queue data may be stale.')), renderedScreen),
  )
}

export default function ApprovalRoutePage() {
  const searchParams = useSearchParams()
  const [moduleError, setModuleError] = useState<string | null>(null)
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'

  useEffect(() => {
    document.title = 'APEX PM Approval Route'
    window.React = React

    void Promise.all(reviewModules.map((moduleDef) => attachScript(moduleDef.id, moduleDef.src, moduleDef.isLoaded))).catch((error: unknown) => {
      setModuleError(error instanceof Error ? error.message : String(error))
    })
  }, [])

  return (
    <main className="shell-page pm-review-page pm-approval-route">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Approval Promotion</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>PM approval now has a real app route.</h1>
            <p className="lede">
              This promotes the approval prototype into the governed Next.js shell while preserving the same reads and
              mutation seam contract used by the legacy static surface.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/approval</dd>
            </div>
            <div>
              <dt>Legacy compare host</dt>
              <dd>
                <Link href="/pm-review/approval-surface.html">/pm-review/approval-surface.html</Link>
              </dd>
            </div>
            <div>
              <dt>Backend seam</dt>
              <dd>/api/v1/reads/* and /api/v1/mutations/*</dd>
            </div>
          </dl>
        </div>
        {returnTo && (
          <p className="pm-review-link-row pm-review-link-row-start">
            <Link href={returnTo}>Return to {returnLabel}</Link>
          </p>
        )}
      </section>

      {moduleError && (
        <section className="notes-card pm-review-card pm-runtime-error">
          <h2>Review Modules Failed To Load</h2>
          <p>{moduleError}</p>
        </section>
      )}

      <ApprovalSurfaceApp />
    </main>
  )
}
