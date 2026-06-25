'use client'

import Link from 'next/link'
import * as React from 'react'

import {
  buildDemoEnvelope,
  submitNative,
  approveRun,
  catalogRefs,
  DEMO_PROJECT_NUMBER,
  EstimatorError,
  type NativeRunResult,
} from '../../lib/estimator'

const { useState, useCallback } = React

type NetaStd = 'ATS' | 'MTS'

interface LineEntry {
  id: number
  ref: string
  qty: number
  description: string
  designation: string
  notes: string
}

let lineIdCounter = 0

function nextId(): number {
  return ++lineIdCounter
}

interface FindingBadgeProps {
  severity: string
}

function FindingBadge({ severity }: FindingBadgeProps) {
  const cls =
    severity === 'error'
      ? 'bg-red-100 text-red-800'
      : severity === 'warning'
        ? 'bg-yellow-100 text-yellow-800'
        : 'bg-blue-100 text-blue-700'
  return (
    <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>
      {severity}
    </span>
  )
}

export default function EstimatorPage() {
  const refs = catalogRefs()

  // Scope fields
  const [scopeName, setScopeName] = useState('Scope 1')
  const [netaStandard, setNetaStandard] = useState<NetaStd>('ATS')

  // Add-line form
  const [addRef, setAddRef] = useState(refs[0] ?? '')
  const [addQty, setAddQty] = useState(1)
  const [addDesc, setAddDesc] = useState('')
  const [addDesig, setAddDesig] = useState('')
  const [addNotes, setAddNotes] = useState('')

  // Line list
  const [lines, setLines] = useState<LineEntry[]>([])

  // Submission state
  const [submitting, setSubmitting] = useState(false)
  const [findings, setFindings] = useState<{ severity: string; message: string; code: string }[]>([])
  const [result, setResult] = useState<{ run_id: string } | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [is409, setIs409] = useState(false)

  const handleAddLine = useCallback(() => {
    if (!addRef) return
    setLines((prev) => [
      ...prev,
      {
        id: nextId(),
        ref: addRef,
        qty: addQty,
        description: addDesc,
        designation: addDesig,
        notes: addNotes,
      },
    ])
    // Reset add-line form except ref
    setAddQty(1)
    setAddDesc('')
    setAddDesig('')
    setAddNotes('')
  }, [addRef, addQty, addDesc, addDesig, addNotes])

  const handleSubmit = useCallback(async () => {
    setFindings([])
    setResult(null)
    setApiError(null)
    setIs409(false)

    if (lines.length === 0) {
      setApiError('Add at least one line before compiling.')
      return
    }

    setSubmitting(true)
    try {
      const { envelope, findings: clientFindings } = buildDemoEnvelope([
        {
          name: scopeName,
          netaStandard,
          lines: lines.map((l) => ({
            ref: l.ref,
            qty: l.qty,
            description: l.description || undefined,
            designation: l.designation || undefined,
            notes: l.notes || undefined,
          })),
        },
      ])

      if (clientFindings.some((f) => f.severity === 'error')) {
        setFindings(clientFindings.map((f) => ({ severity: f.severity, message: f.message, code: f.code })))
        return
      }

      const run: NativeRunResult = await submitNative(envelope)
      if (run.status === 'parsed') {
        await approveRun(run.run_id)
        setResult({ run_id: run.run_id })
      } else {
        setApiError(`Unexpected run status: ${run.status}`)
      }
    } catch (err) {
      if (err instanceof EstimatorError && err.status === 409) {
        setIs409(true)
        setApiError(err.message)
      } else if (err instanceof Error) {
        setApiError(err.message)
      } else {
        setApiError(String(err))
      }
    } finally {
      setSubmitting(false)
    }
  }, [lines, scopeName, netaStandard])

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      {/* Banner */}
      <div className="mb-6 flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-4 py-2 text-sm">
        <span className="font-medium text-gray-700">
          Project:{' '}
          <span className="font-mono text-gray-900">{DEMO_PROJECT_NUMBER}</span>
        </span>
        <span className="text-xs text-gray-400">read-only · ephemeral demo</span>
      </div>

      <h1 className="mb-6 text-2xl font-bold text-gray-900">Estimator — Native Renderer</h1>

      {/* Scope */}
      <section className="mb-6 rounded border border-gray-200 bg-white p-4">
        <h2 className="mb-4 text-base font-semibold text-gray-800">Scope</h2>
        <div className="flex flex-wrap gap-4">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Scope name</span>
            <input
              type="text"
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={scopeName}
              onChange={(e) => setScopeName(e.target.value)}
              aria-label="Scope name"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">NETA standard</span>
            <select
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={netaStandard}
              onChange={(e) => setNetaStandard(e.target.value as NetaStd)}
              aria-label="NETA standard"
            >
              <option value="ATS">ATS</option>
              <option value="MTS">MTS</option>
            </select>
          </label>
        </div>
      </section>

      {/* Add-line control */}
      <section className="mb-6 rounded border border-gray-200 bg-white p-4">
        <h2 className="mb-4 text-base font-semibold text-gray-800">Add line</h2>
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Apparatus ref</span>
            <select
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={addRef}
              onChange={(e) => setAddRef(e.target.value)}
              aria-label="Apparatus ref"
            >
              {refs.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Qty</span>
            <input
              type="number"
              className="w-20 rounded border border-gray-300 px-3 py-1.5 text-sm"
              min={1}
              value={addQty}
              onChange={(e) => setAddQty(Math.max(1, parseInt(e.target.value, 10) || 1))}
              aria-label="Qty"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Description</span>
            <input
              type="text"
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={addDesc}
              onChange={(e) => setAddDesc(e.target.value)}
              aria-label="Description"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Designation</span>
            <input
              type="text"
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={addDesig}
              onChange={(e) => setAddDesig(e.target.value)}
              aria-label="Designation"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Notes</span>
            <input
              type="text"
              className="rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={addNotes}
              onChange={(e) => setAddNotes(e.target.value)}
              aria-label="Notes"
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleAddLine}
              disabled={!addRef}
              className="rounded bg-gray-800 px-4 py-1.5 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-40"
            >
              Add
            </button>
          </div>
        </div>
      </section>

      {/* Lines grid */}
      {lines.length > 0 && (
        <section className="mb-6 overflow-x-auto rounded border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-3 py-2">Qty</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2">Apparatus</th>
                <th className="px-3 py-2">Designation</th>
                <th className="px-3 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="px-3 py-1.5 text-right">{l.qty}</td>
                  <td className="px-3 py-1.5 text-gray-700">{l.description || '—'}</td>
                  <td className="px-3 py-1.5 font-mono text-gray-600">{l.ref}</td>
                  <td className="px-3 py-1.5 text-gray-600">{l.designation || '—'}</td>
                  <td className="px-3 py-1.5 text-gray-500">{l.notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Submit */}
      <div className="mb-6">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || lines.length === 0}
          className="rounded bg-blue-700 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-600 disabled:opacity-40"
        >
          {submitting ? 'Compiling…' : 'Compile & Submit'}
        </button>
      </div>

      {/* Client findings */}
      {findings.length > 0 && (
        <section className="mb-6 rounded border border-red-200 bg-red-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-red-900">Compilation findings</h3>
          <ul className="space-y-1">
            {findings.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <FindingBadge severity={f.severity} />
                <span className="text-gray-800">{f.message}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* API error */}
      {apiError && (
        <section className="mb-6 rounded border border-red-200 bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-900">Error</p>
          <p className="mt-1 text-red-800">{apiError}</p>
          {is409 && (
            <p className="mt-2 text-gray-700">
              <strong>DEMO-NATIVE-001 already has a frozen quote.</strong> Reset it on the backend (delete the
              existing approved run for this project) to re-run the demo.
            </p>
          )}
        </section>
      )}

      {/* Success */}
      {result && (
        <section className="mb-6 rounded border border-green-200 bg-green-50 p-4 text-sm">
          <p className="font-semibold text-green-900">Run approved</p>
          <p className="mt-1 text-gray-700">
            Run ID: <span className="font-mono">{result.run_id}</span>
          </p>
          <p className="mt-3">
            <Link
              href="/pm-review/recognition"
              className="inline-block rounded bg-green-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-600"
            >
              Go to Recognition →
            </Link>
          </p>
        </section>
      )}
    </main>
  )
}
