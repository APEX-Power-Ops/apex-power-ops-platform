'use client'
import * as React from 'react'
import {
  actionFlags, fetchWorklist, fetchRollup, attestComplete, recognize,
  reverseEvent, revokeAttestation, CLEARANCE_VALUES, ATTEST_COPY,
  type WorklistRow, type RollupRow, type Clearance,
} from '../../../lib/recognition'

const { useCallback, useMemo, useState } = React
const PM_ACTOR_ID = process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '00000000-0000-0000-0000-000000000001'

// Modal descriptor: which action is pending on which row. Spec §8 mandates a
// reason-required modal (attest/revoke/reverse) and enum-constrained clearance
// <select>s (recognize) — NO window.prompt anywhere.
type ModalKind = 'attest' | 'recognize' | 'revoke' | 'reverse'
interface ModalState { kind: ModalKind; row: WorklistRow }

export default function RecognitionPage() {
  const [pn, setPn] = useState('')
  const [rows, setRows] = useState<WorklistRow[]>([])
  const [rollup, setRollup] = useState<RollupRow[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [modal, setModal] = useState<ModalState | null>(null)

  const load = useCallback(async (project?: string) => {
    setBusy(true); setErr(null)
    try {
      const [w, r] = await Promise.all([fetchWorklist(project), fetchRollup(project)])
      setRows(w); setRollup(r)
    } catch (e) { setErr(e instanceof Error ? e.message : 'load failed') }
    finally { setBusy(false) }
  }, [])

  // Action buttons OPEN the modal; the modal's submit performs the API call.
  const openModal = useCallback((kind: ModalKind, row: WorklistRow) => {
    setErr(null); setModal({ kind, row })
  }, [])

  // Submit handler invoked by the modal with the collected, validated inputs.
  const submitModal = useCallback(async (
    kind: ModalKind, row: WorklistRow,
    reason: string, ds: Clearance, cx: Clearance,
  ) => {
    try {
      if (kind === 'attest') await attestComplete(row.apparatus_id, PM_ACTOR_ID, reason)
      else if (kind === 'recognize') await recognize(row.apparatus_id, PM_ACTOR_ID, ds, null, cx, null)
      else if (kind === 'revoke') { if (!row.attestation_id) return; await revokeAttestation(row.attestation_id, PM_ACTOR_ID, reason) }
      else if (kind === 'reverse') { if (!row.recognized_event_id) return; await reverseEvent(row.recognized_event_id, PM_ACTOR_ID, reason) }
      setModal(null)
      await load(pn || undefined)
    } catch (e) { setErr(e instanceof Error ? e.message : `${kind} failed`) }
  }, [load, pn])

  const grouped = useMemo(() => {
    const m = new Map<string, WorklistRow[]>()
    for (const r of rows) { const k = r.scope_id; (m.get(k) ?? m.set(k, []).get(k)!).push(r) }
    return [...m.entries()]
  }, [rows])

  return (
    <main className="p-6">
      <h1 className="text-xl font-semibold">Recognition — {ATTEST_COPY}</h1>
      <div className="mt-4 flex gap-2">
        <input aria-label="project number" value={pn} onChange={(e) => setPn(e.target.value)}
               placeholder="project number" className="rounded border px-2 py-1" />
        <button onClick={() => load(pn || undefined)} disabled={busy}
                className="rounded bg-gray-800 px-3 py-1 text-white">Load</button>
      </div>
      {err && <p role="alert" className="mt-2 text-red-700">{err}</p>}

      {modal && (
        <ActionModal
          kind={modal.kind}
          row={modal.row}
          onCancel={() => setModal(null)}
          onSubmit={submitModal}
        />
      )}

      <section className="mt-6">
        <h2 className="font-medium">Recognized $ rollup</h2>
        <table className="mt-2 w-full text-sm">
          <thead><tr><th className="text-left">Project</th><th className="text-right">Recognized $</th>
            <th className="text-right">Recognized</th><th className="text-right">Eligible</th></tr></thead>
          <tbody>
            {rollup.map((r) => (
              <tr key={`${r.project_number}-${r.scope_id}`} className="border-t">
                <td>{r.project_number}</td>
                <td className="text-right">{Number(r.recognized_total).toLocaleString()}</td>
                <td className="text-right">{r.recognized_count}</td>
                <td className="text-right">{r.eligible_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mt-6">
        <h2 className="font-medium">Worklist</h2>
        {grouped.map(([scopeId, scopeRows]) => (
          <div key={scopeId} className="mt-3">
            <table className="w-full text-sm">
              <thead><tr><th className="text-left">Apparatus</th><th className="text-left">Status</th>
                <th className="text-left">Actions</th></tr></thead>
              <tbody>
                {scopeRows.map((row) => {
                  const f = actionFlags(row)
                  return (
                    <tr key={row.apparatus_id} className="border-t">
                      <td>{row.apparatus_designation}</td>
                      <td>{row.status}</td>
                      <td className="flex gap-2">
                        <button disabled={!f.canAttest} onClick={() => openModal('attest', row)}
                                className="rounded border px-2 py-0.5 disabled:opacity-40">Attest</button>
                        <button disabled={!f.canRecognize} onClick={() => openModal('recognize', row)}
                                className="rounded border px-2 py-0.5 disabled:opacity-40">Recognize</button>
                        <button disabled={!f.canRevoke} onClick={() => openModal('revoke', row)}
                                className="rounded border px-2 py-0.5 disabled:opacity-40">Revoke</button>
                        <button disabled={!f.canReverse} onClick={() => openModal('reverse', row)}
                                className="rounded border px-2 py-0.5 disabled:opacity-40">Reverse</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ))}
      </section>
    </main>
  )
}

// ---- Reason-required modal + enum-constrained clearance <select>s (spec §8) ----
const MODAL_TITLE: Record<ModalKind, string> = {
  attest: ATTEST_COPY,                 // 'Attest testing complete - for recognition' (never 'production complete')
  recognize: 'Recognize revenue',
  revoke: 'Revoke attestation',
  reverse: 'Reverse recognition',
}

function ActionModal(props: {
  kind: ModalKind
  row: WorklistRow
  onCancel: () => void
  onSubmit: (kind: ModalKind, row: WorklistRow, reason: string, ds: Clearance, cx: Clearance) => void | Promise<void>
}) {
  const { kind, row, onCancel, onSubmit } = props
  const [reason, setReason] = useState('')
  const [ds, setDs] = useState<Clearance>('not_applicable')
  const [cx, setCx] = useState<Clearance>('not_applicable')
  const isRecognize = kind === 'recognize'
  // attest/revoke/reverse REQUIRE a non-blank reason; recognize requires two enum clearances.
  const canSubmit = isRecognize
    ? CLEARANCE_VALUES.includes(ds) && CLEARANCE_VALUES.includes(cx)
    : reason.trim().length > 0

  return (
    <div role="dialog" aria-modal="true" aria-label={MODAL_TITLE[kind]}
         className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-[28rem] rounded bg-white p-4 shadow-lg">
        <h3 className="font-semibold">{MODAL_TITLE[kind]}</h3>
        <p className="mt-1 text-sm text-gray-600">{row.apparatus_designation}</p>

        {isRecognize ? (
          <div className="mt-3 grid grid-cols-2 gap-3">
            <label className="text-sm">Datasheet clearance
              <select aria-label="datasheet clearance" value={ds}
                      onChange={(e) => setDs(e.target.value as Clearance)}
                      className="mt-1 w-full rounded border px-2 py-1">
                {CLEARANCE_VALUES.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </label>
            <label className="text-sm">Cx clearance
              <select aria-label="cx clearance" value={cx}
                      onChange={(e) => setCx(e.target.value as Clearance)}
                      className="mt-1 w-full rounded border px-2 py-1">
                {CLEARANCE_VALUES.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </label>
          </div>
        ) : (
          <label className="mt-3 block text-sm">Reason (required)
            <textarea aria-label="reason" value={reason} onChange={(e) => setReason(e.target.value)}
                      className="mt-1 w-full rounded border px-2 py-1" rows={3} />
          </label>
        )}

        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="rounded border px-3 py-1">Cancel</button>
          <button aria-label="confirm" disabled={!canSubmit}
                  onClick={() => onSubmit(kind, row, reason.trim(), ds, cx)}
                  className="rounded bg-gray-800 px-3 py-1 text-white disabled:opacity-40">Confirm</button>
        </div>
      </div>
    </div>
  )
}
