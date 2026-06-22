'use client'

import Link from 'next/link'
import * as React from 'react'

import {
  type IntakeFinding,
  type IntakeRun,
  type LineNode,
  type ReviewPayload,
  type ScopeNode,
  type TaskNode,
  buildTree,
  editReview,
  approveRun,
  uploadWorkbook,
  treeToReviewPayload,
  workbookContentType,
} from '../../../lib/estimator-intake'

const { useCallback, useState } = React

// The intake actor must be a real ops.persons(person_id) UUID (the DB FKs uploaded_by / approved_by).
// In dev, configure NEXT_PUBLIC_OPS_DEV_PM_ID to a real seeded person; real multi-user auth is the
// named prod follow-on. The fallback is a valid-FORMAT placeholder UUID (NOT the old non-UUID
// "pm-001"): if it ever reaches a real backend unconfigured, the ops.persons FK rejects it LOUDLY
// (a clear 4xx), never silently mis-attributing a run.
const PM_ACTOR_ID =
  process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '00000000-0000-0000-0000-000000000001'

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FindingRow({ finding }: { finding: IntakeFinding }) {
  const badge =
    finding.severity === 'blocking'
      ? 'bg-red-100 text-red-800'
      : finding.severity === 'warning'
        ? 'bg-yellow-100 text-yellow-800'
        : 'bg-blue-100 text-blue-700'
  return (
    <li className="flex items-start gap-2 py-1 text-sm">
      <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${badge}`}>
        {finding.severity}
      </span>
      <span className={finding.ok ? 'text-gray-600' : 'font-medium text-gray-900'}>
        {finding.message}
      </span>
    </li>
  )
}

function LineRow({
  line,
  scopeIdx,
  taskIdx,
  lineIdx,
  onHrsChange,
  onRegroup,
  taskNames,
}: {
  line: LineNode
  scopeIdx: number
  taskIdx: number
  lineIdx: number
  onHrsChange: (scopeIdx: number, taskIdx: number, lineIdx: number, value: number) => void
  onRegroup: (scopeIdx: number, taskIdx: number, lineIdx: number, newTask: string) => void
  taskNames: string[]
}) {
  const [regroupVal, setRegroupVal] = useState(line.section ?? '__ungrouped__')

  return (
    <tr className="border-t text-sm">
      <td className="px-3 py-1.5 text-gray-700">{line.apparatusType}</td>
      <td className="px-3 py-1.5 text-gray-500">{line.testStandard}</td>
      <td className="px-3 py-1.5 text-right text-gray-700">{line.qty}</td>
      <td className="px-3 py-1.5 text-right">
        <input
          type="number"
          className="w-20 rounded border border-gray-300 px-1.5 py-0.5 text-right text-sm"
          min={0}
          step={0.25}
          value={line.hoursPerUnit}
          onChange={(e) => onHrsChange(scopeIdx, taskIdx, lineIdx, parseFloat(e.target.value) || 0)}
          aria-label={`hrs/unit for ${line.apparatusType}`}
        />
      </td>
      <td className="px-3 py-1.5 text-right text-gray-700">
        {line.totalHours.toFixed(2)}
      </td>
      <td className="px-3 py-1.5 text-gray-500">{line.designation ?? '-'}</td>
      <td className="px-3 py-1.5">
        <select
          className="rounded border border-gray-300 px-1.5 py-0.5 text-sm"
          value={regroupVal}
          onChange={(e) => {
            const next = e.target.value
            setRegroupVal(next)
            onRegroup(scopeIdx, taskIdx, lineIdx, next)
          }}
          aria-label={`task group for ${line.apparatusType}`}
        >
          {taskNames.map((t) => (
            <option key={t} value={t}>
              {t === '__ungrouped__' ? '(ungrouped)' : t}
            </option>
          ))}
          <option value="__ungrouped__">(ungrouped)</option>
        </select>
      </td>
    </tr>
  )
}

function TaskSection({
  task,
  scopeIdx,
  taskIdx,
  onHrsChange,
  onRegroup,
  taskNames,
}: {
  task: TaskNode
  scopeIdx: number
  taskIdx: number
  onHrsChange: (scopeIdx: number, taskIdx: number, lineIdx: number, value: number) => void
  onRegroup: (scopeIdx: number, taskIdx: number, lineIdx: number, newTask: string) => void
  taskNames: string[]
}) {
  const displayName = task.taskName === '__ungrouped__' ? '(ungrouped)' : task.taskName
  return (
    <div className="mb-4">
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
        Task: {displayName}
      </h4>
      <table className="w-full text-left">
        <thead>
          <tr className="bg-gray-50 text-xs text-gray-500">
            <th className="px-3 py-1.5">Apparatus</th>
            <th className="px-3 py-1.5">Standard</th>
            <th className="px-3 py-1.5 text-right">Qty</th>
            <th className="px-3 py-1.5 text-right">Hrs/Unit</th>
            <th className="px-3 py-1.5 text-right">Total Hrs</th>
            <th className="px-3 py-1.5">Designation</th>
            <th className="px-3 py-1.5">Regroup</th>
          </tr>
        </thead>
        <tbody>
          {task.lines.map((line, lineIdx) => (
            <LineRow
              key={line.lineUid ?? lineIdx}
              line={line}
              scopeIdx={scopeIdx}
              taskIdx={taskIdx}
              lineIdx={lineIdx}
              onHrsChange={onHrsChange}
              onRegroup={onRegroup}
              taskNames={taskNames}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ScopeSection({
  scope,
  scopeIdx,
  onHrsChange,
  onRegroup,
}: {
  scope: ScopeNode
  scopeIdx: number
  onHrsChange: (scopeIdx: number, taskIdx: number, lineIdx: number, value: number) => void
  onRegroup: (scopeIdx: number, taskIdx: number, lineIdx: number, newTask: string) => void
}) {
  const taskNames = scope.tasks.map((t) => t.taskName)
  return (
    <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-base font-semibold text-gray-900">
        {scope.scopeName}
        <span className="ml-2 text-xs font-normal text-gray-400">{scope.scopeType}</span>
      </h3>
      {scope.tasks.map((task, taskIdx) => (
        <TaskSection
          key={task.taskName}
          task={task}
          scopeIdx={scopeIdx}
          taskIdx={taskIdx}
          onHrsChange={onHrsChange}
          onRegroup={onRegroup}
          taskNames={taskNames}
        />
      ))}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Tree editor helper: apply edits to a ScopeNode[] immutably
// ---------------------------------------------------------------------------

function applyHrsEdit(
  tree: ScopeNode[],
  scopeIdx: number,
  taskIdx: number,
  lineIdx: number,
  hoursPerUnit: number,
): ScopeNode[] {
  return tree.map((scope, si) => {
    if (si !== scopeIdx) return scope
    return {
      ...scope,
      tasks: scope.tasks.map((task, ti) => {
        if (ti !== taskIdx) return task
        return {
          ...task,
          lines: task.lines.map((line, li) => {
            if (li !== lineIdx) return line
            const qty = line.qty
            return {
              ...line,
              hoursPerUnit,
              totalHours: Math.round(qty * hoursPerUnit * 10000) / 10000,
            }
          }),
        }
      }),
    }
  })
}

function applyRegroup(
  tree: ScopeNode[],
  scopeIdx: number,
  taskIdx: number,
  lineIdx: number,
  newTaskName: string,
): ScopeNode[] {
  return tree.map((scope, si) => {
    if (si !== scopeIdx) return scope
    // Pull the line out of its current task
    const movedLine: LineNode = { ...scope.tasks[taskIdx].lines[lineIdx], section: newTaskName === '__ungrouped__' ? null : newTaskName }
    const tasks = scope.tasks
      .map((task, ti) => {
        if (ti !== taskIdx) return task
        return { ...task, lines: task.lines.filter((_, li) => li !== lineIdx) }
      })
      .filter((task) => task.lines.length > 0)

    // Insert line into the target task (or create it)
    const targetIdx = tasks.findIndex((t) => t.taskName === newTaskName)
    if (targetIdx >= 0) {
      return {
        ...scope,
        tasks: tasks.map((task, ti) => {
          if (ti !== targetIdx) return task
          return { ...task, lines: [...task.lines, movedLine] }
        }),
      }
    }
    // Create a new task
    return {
      ...scope,
      tasks: [...tasks, { taskName: newTaskName, lines: [movedLine] }],
    }
  })
}

// ---------------------------------------------------------------------------
// reviewPayload rebuild from ScopeNode[] (for editReview)
// ---------------------------------------------------------------------------

// treeToReviewPayload + workbookContentType now live in lib/estimator-intake.ts (testable, co-located
// with buildTree). Imported above.

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function EstimatorIntakePage() {
  const [run, setRun] = useState<IntakeRun | null>(null)
  const [tree, setTree] = useState<ScopeNode[]>([])
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [approving, setApproving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Determine if Approve should be disabled
  const hasOpenBlocker =
    run !== null &&
    run.findings.some((f) => f.severity === 'blocking' && !f.ok)
  const isRevisionBlocked = run?.status === 'revision_blocked'
  const approveDisabled = !run || hasOpenBlocker || isRevisionBlocked || approving

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      const contentType = workbookContentType(file.name)
      if (!contentType) {
        setError('Unsupported file type — upload a .xlsm/.xlsx workbook or a .json export.')
        e.target.value = ''
        return
      }
      setUploading(true)
      setError(null)
      setSuccessMsg(null)
      try {
        const result = await uploadWorkbook(file, PM_ACTOR_ID, contentType)
        setRun(result)
        setTree(buildTree(result.review_payload))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed')
      } finally {
        setUploading(false)
      }
    },
    [],
  )

  const handleHrsChange = useCallback(
    (scopeIdx: number, taskIdx: number, lineIdx: number, value: number) => {
      setTree((prev) => applyHrsEdit(prev, scopeIdx, taskIdx, lineIdx, value))
    },
    [],
  )

  const handleRegroup = useCallback(
    (scopeIdx: number, taskIdx: number, lineIdx: number, newTask: string) => {
      setTree((prev) => applyRegroup(prev, scopeIdx, taskIdx, lineIdx, newTask))
    },
    [],
  )

  const handleSaveReview = useCallback(async () => {
    if (!run) return
    setSaving(true)
    setError(null)
    try {
      const payload = treeToReviewPayload(tree, run.review_payload)
      const updated = await editReview(run.run_id, payload)
      setRun(updated)
      setTree(buildTree(updated.review_payload))
      setSuccessMsg('Review saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }, [run, tree])

  const handleApprove = useCallback(async () => {
    if (!run || approveDisabled) return
    setApproving(true)
    setError(null)
    try {
      await approveRun(run.run_id, PM_ACTOR_ID)
      setSuccessMsg('Run approved.')
      // Refresh
      setRun((prev) => prev ? { ...prev, status: 'approved' } : prev)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve failed')
    } finally {
      setApproving(false)
    }
  }, [run, approveDisabled])

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Estimator Intake</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload a workbook, review the scope-task-line tree, and approve when ready.
          </p>
        </div>
        <Link href="/pm-review" className="text-sm text-blue-600 hover:underline">
          PM Review
        </Link>
      </div>

      {/* Upload control */}
      <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold text-gray-700">Upload Workbook</h2>
        <input
          type="file"
          accept=".xlsm,.xlsx,.xls,.json"
          onChange={handleFileChange}
          disabled={uploading}
          aria-label="Upload estimator workbook"
          className="block text-sm text-gray-700 file:mr-3 file:rounded file:border file:border-gray-300 file:bg-gray-50 file:px-3 file:py-1 file:text-sm file:font-medium"
        />
        {uploading && (
          <p className="mt-2 text-sm text-gray-500" aria-live="polite">
            Uploading…
          </p>
        )}
        {error && (
          <p className="mt-2 text-sm font-medium text-red-600" role="alert">
            {error}
          </p>
        )}
        {successMsg && (
          <p className="mt-2 text-sm text-green-700" aria-live="polite">
            {successMsg}
          </p>
        )}
      </section>

      {/* Run metadata */}
      {run && (
        <>
          <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">Run Info</h2>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <dt className="text-gray-500">Run ID</dt>
              <dd className="font-mono text-gray-800">{run.run_id}</dd>
              <dt className="text-gray-500">Status</dt>
              <dd className="font-medium text-gray-800">{run.status}</dd>
              {run.source_format && (
                <>
                  <dt className="text-gray-500">Format</dt>
                  <dd className="text-gray-800">{run.source_format}</dd>
                </>
              )}
              {run.review_payload.project?.project_number && (
                <>
                  <dt className="text-gray-500">Project</dt>
                  <dd className="text-gray-800">
                    {run.review_payload.project.project_number}
                    {run.review_payload.project.project_name
                      ? ` — ${run.review_payload.project.project_name}`
                      : ''}
                  </dd>
                </>
              )}
            </dl>
          </section>

          {/* Findings */}
          {run.findings.length > 0 && (
            <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-gray-700">Findings</h2>
              <ul className="divide-y divide-gray-100">
                {run.findings.map((f) => (
                  <FindingRow key={f.code} finding={f} />
                ))}
              </ul>
              {hasOpenBlocker && (
                <p className="mt-2 text-xs font-medium text-red-600">
                  One or more blocking findings are open. Resolve before approving.
                </p>
              )}
            </section>
          )}

          {/* Scope-Task-Line tree */}
          <section className="mb-6">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">Scope Review</h2>
            {tree.map((scope, scopeIdx) => (
              <ScopeSection
                key={scope.scopeName}
                scope={scope}
                scopeIdx={scopeIdx}
                onHrsChange={handleHrsChange}
                onRegroup={handleRegroup}
              />
            ))}
          </section>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleSaveReview}
              disabled={saving}
              className="rounded bg-gray-100 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-200 disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save Review'}
            </button>
            <button
              type="button"
              onClick={handleApprove}
              disabled={approveDisabled}
              aria-label="Approve run"
              className="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {approving ? 'Approving…' : 'Approve'}
            </button>
            {approveDisabled && !approving && (
              <span className="text-xs text-gray-500">
                {isRevisionBlocked
                  ? 'Run is revision-blocked.'
                  : hasOpenBlocker
                    ? 'Blocked by open finding.'
                    : ''}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  )
}
