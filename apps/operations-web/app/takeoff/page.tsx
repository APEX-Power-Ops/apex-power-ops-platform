'use client'

import * as React from 'react'
import {
  evaluate,
  resolvableVoltageGroups,
  otherOpenItems,
  buildAssertions,
  mergeAssertionsByTag,
  buildExport,
  type SheetGroup,
  type OpenItem,
} from '../../lib/gate1'
import { parseArtifact, ArtifactContractError, type ExtractionArtifact } from '@apex/estimator-takeoff'

const { useState, useCallback, useRef } = React

interface EvalState {
  result: ReturnType<typeof evaluate>['result']
  report: ReturnType<typeof evaluate>['report']
}

interface ProjectCtx {
  projectNumber: string
  packageName: string
  operatorName: string
}

function downloadBlob(content: string, filename: string) {
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FindingRow({ finding }: { finding: EvalState['result']['findings'][number] }) {
  const isConflict = finding.code === 'voltage_assertion_conflict'
  const severityCls =
    finding.severity === 'error'
      ? 'bg-red-100 text-red-800'
      : 'bg-yellow-100 text-yellow-800'
  const detail = finding.detail
  return (
    <li className="flex flex-col gap-0.5 py-1.5 text-sm">
      <div className="flex items-start gap-2">
        <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${severityCls}`}>
          {finding.severity}
        </span>
        <span className="font-medium text-gray-900">{finding.code}</span>
      </div>
      {finding.message && (
        <p className="ml-12 text-gray-700">{finding.message}</p>
      )}
      {isConflict && detail && (
        <p className="ml-12 text-xs text-gray-500">
          {detail.tag && <span>tag: <span className="font-mono">{detail.tag}</span> | </span>}
          {detail.detectedV !== undefined && <span>detected: <span className="font-mono">{detail.detectedV}V</span> | </span>}
          {detail.assertedV !== undefined && <span>asserted: <span className="font-mono">{detail.assertedV}V</span></span>}
        </p>
      )}
    </li>
  )
}

function VoltagePanel({
  groups,
  entries,
  onEntryChange,
  onApply,
  applyMessage,
  applyDisabled,
}: {
  groups: SheetGroup[]
  entries: Map<string, string>
  onEntryChange: (tag: string, val: string) => void
  onApply: () => void
  applyMessage: string | null
  applyDisabled: boolean
}) {
  if (groups.length === 0) {
    return (
      <section className="mb-6 rounded border border-green-200 bg-green-50 p-4">
        <h2 className="mb-2 text-base font-semibold text-green-900">Voltage Questions</h2>
        <p className="text-sm text-green-800">No unresolved voltage questions.</p>
      </section>
    )
  }
  return (
    <section className="mb-6 rounded border border-gray-200 bg-white p-4">
      <h2 className="mb-4 text-base font-semibold text-gray-800">Voltage Questions</h2>
      {groups.map((g) => (
        <div key={g.sheet} className="mb-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Sheet: {g.sheet}</p>
          {g.blocks.map((b) => (
            <div key={b.block} className="mb-4">
              <p className="mb-1 text-xs font-medium text-gray-600">Block: {b.block}</p>
              <div className="overflow-x-auto rounded border border-gray-100">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    <tr>
                      <th className="px-3 py-2">Tag</th>
                      <th className="px-3 py-2">Raw</th>
                      <th className="px-3 py-2">Evidence</th>
                      <th className="px-3 py-2">Reason</th>
                      <th className="px-3 py-2">Voltage (V)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {b.tags.map((row) => (
                      <tr key={row.tag} className="border-t">
                        <td className="px-3 py-1.5 font-mono text-gray-900">{row.tag}</td>
                        <td className="px-3 py-1.5 text-gray-600">{row.raw}</td>
                        <td className="px-3 py-1.5 text-gray-500">{row.evidence}</td>
                        <td className="px-3 py-1.5 text-gray-500">{row.reason}</td>
                        <td className="px-3 py-1.5">
                          <input
                            type="number"
                            min={1}
                            step={1}
                            className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                            value={entries.get(row.tag) ?? ''}
                            onChange={(e) => onEntryChange(row.tag, e.target.value)}
                            aria-label={`Voltage for tag ${row.tag}`}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ))}
      {applyMessage && (
        <p className="mb-3 text-sm text-amber-700" role="alert">{applyMessage}</p>
      )}
      <button
        type="button"
        onClick={onApply}
        disabled={applyDisabled}
        className="rounded bg-gray-800 px-4 py-1.5 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Apply
      </button>
    </section>
  )
}

function OtherOpenItemsPanel({ items }: { items: OpenItem[] }) {
  return (
    <section className="mb-6 rounded border border-gray-200 bg-white p-4">
      <h2 className="mb-4 text-base font-semibold text-gray-800">Other Open Items</h2>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">No other open items.</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {items.map((item, i) => (
            <li key={i} className="flex flex-col gap-0.5 py-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600">
                  {item.kind}
                </span>
                <span className="text-gray-800">{item.label}</span>
              </div>
              {item.sheet && (
                <p className="ml-12 text-xs text-gray-400">sheet: {item.sheet}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TakeoffPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [artifact, setArtifact] = useState<ExtractionArtifact | null>(null)
  const [evald, setEvald] = useState<EvalState | null>(null)
  const [entries, setEntries] = useState<Map<string, string>>(new Map())
  const [projectCtx, setProjectCtx] = useState<ProjectCtx>({
    projectNumber: '',
    packageName: '',
    operatorName: '',
  })
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [applyMsg, setApplyMsg] = useState<string | null>(null)

  // Derived
  const voltageGroups = artifact && evald ? resolvableVoltageGroups(evald.result, artifact) : []
  const openItems = artifact ? (evald ? otherOpenItems(evald.result, artifact) : []) : []
  const isCleanStatus = evald?.report.status === 'clean'
  const hasMatched = (evald?.result.matchedLines.length ?? 0) > 0
  const canExport =
    projectCtx.projectNumber.trim() !== '' && projectCtx.operatorName.trim() !== ''
  const applyDisabled = projectCtx.operatorName.trim() === ''

  // -------------------------------------------------------------------------
  // Load artifact
  // -------------------------------------------------------------------------
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const input = e.target
    // FIX B (P2-2): reset to a clean slate at the START of every load. On a bad JSON or
    // ArtifactContractError we must NOT leave the previous artifact/eval/worklist + ENABLED
    // export buttons on screen (stale data could be exported under a new error). Only a
    // successful parseArtifact below re-populates artifact/evald.
    setArtifact(null)
    setEvald(null)
    setEntries(new Map())
    setApplyMsg(null)
    setErr(null)
    setBusy(true)
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const raw = ev.target?.result
        if (typeof raw !== 'string') throw new Error('Failed to read file as text')
        let parsed: unknown
        try {
          parsed = JSON.parse(raw)
        } catch {
          setErr('Invalid JSON: could not parse artifact file.')
          setBusy(false)
          return
        }
        const art = parseArtifact(parsed)
        setArtifact(art)
        setEvald(evaluate(art))
        setEntries(new Map())
        setApplyMsg(null)
      } catch (ex) {
        if (ex instanceof ArtifactContractError) {
          setErr(`artifact contract error at ${ex.path ?? ex.message}`)
        } else if (ex instanceof Error) {
          setErr(ex.message)
        } else {
          setErr(String(ex))
        }
      } finally {
        setBusy(false)
        input.value = ''
      }
    }
    reader.onerror = () => {
      setErr('Failed to read file.')
      setBusy(false)
      input.value = ''
    }
    reader.readAsText(file)
  }, [])

  // -------------------------------------------------------------------------
  // Apply voltage entries
  // -------------------------------------------------------------------------
  const handleApply = useCallback(() => {
    if (!artifact || !evald) return
    if (projectCtx.operatorName.trim() === '') {
      setApplyMsg('Enter operator initials (Project Context) before applying voltage answers.')
      return
    }
    // FIX 1: Recompute currently-resolvable tags INSIDE the handler so stale hidden
    // entries (already resolved from a prior Apply) are not re-submitted. A re-submitted
    // resolved tag with a changed operator name would silently rewrite its actor field
    // (provenance corruption), and is also redundant.
    const groups = resolvableVoltageGroups(evald.result, artifact)
    const currentTags = new Set(
      groups.flatMap((g) => g.blocks.flatMap((b) => b.tags.map((t) => t.tag)))
    )
    const invalid: string[] = []
    const validEntries: { tag: string; voltageV: number }[] = []
    for (const [tag, raw] of entries.entries()) {
      // Skip stale/hidden entries whose tag is no longer in the visible worklist
      if (!currentTags.has(tag)) continue
      if (raw === '' || raw === undefined) continue
      const v = Number(raw)
      if (!Number.isInteger(v) || v <= 0) {
        invalid.push(tag)
      } else {
        validEntries.push({ tag, voltageV: v })
      }
    }
    if (validEntries.length === 0 && invalid.length === 0) {
      setApplyMsg('No voltage values entered.')
      return
    }
    if (validEntries.length === 0) {
      setApplyMsg(
        `Invalid voltage for tag(s): ${invalid.join(', ')}. Enter a positive whole number.`
      )
      return
    }
    const msg =
      invalid.length > 0
        ? `Applied valid entries. Invalid (skipped): ${invalid.join(', ')}`
        : null
    const clone = structuredClone(artifact) as ExtractionArtifact
    clone.voltageAssertions = mergeAssertionsByTag(
      clone.voltageAssertions,
      buildAssertions(validEntries, projectCtx.operatorName.trim())
    )
    const newEvald = evaluate(clone)
    setArtifact(clone)
    setEvald(newEvald)
    // FIX 1 (cont.): Prune the just-applied tags from entries so they cannot
    // re-submit on a future Apply (they are now resolved and will leave the worklist).
    setEntries((prev) => {
      const next = new Map(prev)
      for (const e of validEntries) next.delete(e.tag)
      return next
    })
    setApplyMsg(msg)
  }, [artifact, evald, entries, projectCtx.operatorName])

  // -------------------------------------------------------------------------
  // Export
  // -------------------------------------------------------------------------
  const handleExport = useCallback(
    async (mode: 'clean' | 'partial') => {
      if (!artifact || !evald) return
      if (!canExport) return
      setExporting(true)
      try {
        const { combined } = await buildExport({
          artifact,
          result: evald.result,
          report: evald.report,
          projectCtx: {
            projectNumber: projectCtx.projectNumber.trim(),
            packageName: projectCtx.packageName.trim() || undefined,
            operatorName: projectCtx.operatorName.trim(),
          },
          nowIso: new Date().toISOString(),
        })
        const slug = projectCtx.projectNumber.trim().replace(/[^a-zA-Z0-9_-]/g, '_')
        const suffix = mode === 'clean' ? 'gate1' : 'gate1-partial'
        downloadBlob(JSON.stringify(combined, null, 2), `${slug}_${suffix}.json`)
      } catch (ex) {
        setErr(ex instanceof Error ? ex.message : String(ex))
      } finally {
        setExporting(false)
      }
    },
    [artifact, evald, projectCtx, canExport]
  )

  const handleDownloadRunnerArtifact = useCallback(
    async () => {
      if (!artifact || !evald) return
      if (!canExport) return
      setExporting(true)
      try {
        const { runnerArtifact } = await buildExport({
          artifact,
          result: evald.result,
          report: evald.report,
          projectCtx: {
            projectNumber: projectCtx.projectNumber.trim(),
            packageName: projectCtx.packageName.trim() || undefined,
            operatorName: projectCtx.operatorName.trim(),
          },
          nowIso: new Date().toISOString(),
        })
        const slug = projectCtx.projectNumber.trim().replace(/[^a-zA-Z0-9_-]/g, '_')
        downloadBlob(JSON.stringify(runnerArtifact, null, 2), `${slug}_runner-artifact.json`)
      } catch (ex) {
        setErr(ex instanceof Error ? ex.message : String(ex))
      } finally {
        setExporting(false)
      }
    },
    [artifact, evald, projectCtx, canExport]
  )

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Takeoff Review</p>
        <h1 className="text-2xl font-bold text-gray-900">Takeoff Gate 1</h1>
        <p className="lede">
          Load an extraction artifact, answer missing-voltage questions per tag, re-evaluate, and
          export. This page is browser-only - no data is sent to any server.
        </p>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Load artifact                                                         */}
      {/* ------------------------------------------------------------------ */}
      <section className="mb-6 rounded border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-base font-semibold text-gray-800">Load Artifact</h2>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-gray-700">Extraction artifact JSON</span>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            className="text-sm text-gray-600 file:mr-3 file:rounded file:border file:border-gray-300 file:bg-gray-50 file:px-3 file:py-1 file:text-sm file:font-medium file:text-gray-700 hover:file:bg-gray-100"
            onChange={handleFileChange}
            aria-label="Load extraction artifact JSON"
          />
        </label>
        {busy && <p className="mt-2 text-sm text-gray-400">Loading...</p>}
        {err && (
          <div role="alert" className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {err}
          </div>
        )}
        {artifact && evald && (
          <div className="mt-3 text-sm text-gray-600">
            Loaded: <span className="font-mono">{artifact.pdf}</span> -{' '}
            {artifact.apparatus.length} apparatus row(s)
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Status banner (shown once artifact loaded)                            */}
      {/* ------------------------------------------------------------------ */}
      {evald && (
        <div
          className={`mb-6 rounded border px-4 py-3 text-sm font-medium ${
            !hasMatched
              ? 'border-red-200 bg-red-50 text-red-900'
              : isCleanStatus
              ? 'border-green-200 bg-green-50 text-green-900'
              : 'border-amber-200 bg-amber-50 text-amber-900'
          }`}
          role="status"
        >
          {!hasMatched
            ? 'no matched lines - nothing to price; resolve construction/catalog evidence or review the takeoff'
            : isCleanStatus
            ? 'clean'
            : `partial preview - ${evald.report.counts.unresolved_rows} unresolved row(s); NOT a complete bid`}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Findings strip                                                        */}
      {/* ------------------------------------------------------------------ */}
      {evald && evald.result.findings.length > 0 && (
        <section className="mb-6 rounded border border-gray-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">Findings</h2>
          <ul className="divide-y divide-gray-100">
            {evald.result.findings.map((f, i) => (
              <FindingRow key={i} finding={f} />
            ))}
          </ul>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Panel 1: Voltage Questions (only when artifact loaded + evald)        */}
      {/* ------------------------------------------------------------------ */}
      {artifact && evald && (
        <VoltagePanel
          groups={voltageGroups}
          entries={entries}
          onEntryChange={(tag, val) =>
            setEntries((prev) => new Map(prev).set(tag, val))
          }
          onApply={handleApply}
          applyMessage={applyMsg}
          applyDisabled={applyDisabled}
        />
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Panel 2: Other Open Items (always visible when artifact loaded, R3)  */}
      {/* ------------------------------------------------------------------ */}
      {artifact && (
        <OtherOpenItemsPanel items={openItems} />
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Project context                                                        */}
      {/* ------------------------------------------------------------------ */}
      {artifact && (
        <section className="mb-6 rounded border border-gray-200 bg-white p-4">
          <h2 className="mb-4 text-base font-semibold text-gray-800">Project Context</h2>
          <div className="flex flex-wrap gap-4">
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">
                Project number <span className="text-red-600">*</span>
              </span>
              <input
                type="text"
                className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                value={projectCtx.projectNumber}
                onChange={(e) =>
                  setProjectCtx((p) => ({ ...p, projectNumber: e.target.value }))
                }
                aria-label="Project number"
                placeholder="e.g. JUP-2026-001"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Package name (optional)</span>
              <input
                type="text"
                className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                value={projectCtx.packageName}
                onChange={(e) =>
                  setProjectCtx((p) => ({ ...p, packageName: e.target.value }))
                }
                aria-label="Package name"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">
                Operator initials <span className="text-red-600">*</span>
              </span>
              <input
                type="text"
                className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                value={projectCtx.operatorName}
                onChange={(e) =>
                  setProjectCtx((p) => ({ ...p, operatorName: e.target.value }))
                }
                aria-label="Operator initials"
                placeholder="e.g. JLS"
              />
            </label>
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Export controls                                                        */}
      {/* ------------------------------------------------------------------ */}
      {artifact && evald && (
        <section className="mb-6 rounded border border-gray-200 bg-white p-4">
          <h2 className="mb-4 text-base font-semibold text-gray-800">Export</h2>

          {!canExport && (
            <p className="mb-3 text-xs text-gray-500">
              Enter project number and operator initials to export.
            </p>
          )}

          <div className="flex flex-wrap gap-3">
            {/* Clean Export - only enabled when status is clean AND context fields are filled */}
            <button
              type="button"
              disabled={!isCleanStatus || !canExport || exporting || !hasMatched}
              onClick={() => handleExport('clean')}
              className="rounded bg-blue-700 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Clean Export
            </button>

            {/* Partial Preview Export - disabled when run is clean (FIX 2: contradictory to export
               clean-status run under the gate1-partial filename with NOT-a-complete-bid label) */}
            <button
              type="button"
              disabled={!canExport || exporting || isCleanStatus || !hasMatched}
              onClick={() => handleExport('partial')}
              className="rounded border border-gray-300 bg-gray-50 px-5 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              partial preview - NOT a complete bid
            </button>
          </div>

          {!isCleanStatus && evald && canExport && (
            <p className="mt-2 text-xs text-amber-700">
              partial preview - {evald.report.counts.unresolved_rows} unresolved row(s) remain. Use
              'Clean Export' only after all voltage questions are resolved and status is clean.
            </p>
          )}

          {canExport && (
            <div className="mt-4 border-t border-gray-100 pt-3">
              <button
                type="button"
                disabled={exporting}
                onClick={handleDownloadRunnerArtifact}
                className="text-xs text-gray-500 underline hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Download runner artifact (JSON)
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  )
}
