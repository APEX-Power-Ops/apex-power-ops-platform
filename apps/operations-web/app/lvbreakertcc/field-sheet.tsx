'use client'

/**
 * B2.1 — the print-ready FIELD TOLERANCE SHEET (task #130; decision-4 lean:
 * page-integrated print-first). A light-themed overlay a tech prints (or saves
 * to PDF) and carries: the SC2 confirmation block, writable job/equipment/
 * tech/date blanks, the per-element table (SC3 vocabulary + dial symbols,
 * MFR/VERIFY/N/A badges, Method column) with writable Measured / Pass-Fail
 * columns, and the honesty footnotes + the NETA=mfr footer law line.
 *
 * All values come from buildFieldSheet over the SERVED /calculate + /settings
 * payloads — the sheet can never diverge from the page (basis identity).
 */

import { buildFieldSheet, type FieldSheetInput } from '../../lib/field-sheet'

export function FieldSheetView({ input, onClose }: {
  input: Omit<FieldSheetInput, 'generatedAt'>
  onClose: () => void
}) {
  const sheet = buildFieldSheet({ ...input, generatedAt: new Date().toLocaleString('en-US') })
  const elementNotes = sheet.rows.filter((r) => r.note)
  return (
    <div className="sheet-overlay" role="dialog" aria-label="Field tolerance sheet">
      <div className="sheet-actions no-print">
        <button className="btn" onClick={() => window.print()}>🖨 Print / Save PDF</button>
        <button className="btn ghost" onClick={onClose}>Close</button>
      </div>
      <div className="sheet-card">
        <div className="sheet-head">
          <div>
            <div className="sheet-title">NETA Field Tolerance Sheet — LV Breaker</div>
            <div className="sheet-sub">Manufacturer (device-library) acceptance values · field-trust gated</div>
          </div>
          <div className="sheet-meta">
            <div>Generated {sheet.generatedAt}</div>
            <div>Sensor ID {sheet.header.sensorId ?? '—'}</div>
          </div>
        </div>

        <div className="sheet-id">
          <div><span>Breaker</span><b>{sheet.header.breaker}</b></div>
          <div><span>Trip unit</span><b>{sheet.header.trip}</b></div>
          <div><span>Sensor</span><b>{sheet.header.sensor}</b></div>
          <div><span>{sheet.header.plugLabel}</span><b>{sheet.header.plugValue}</b></div>
        </div>
        {sheet.maint && (
          <div className="sheet-maint">⚠ MAINTENANCE MODE (ARMS) ON — test points reflect maintenance settings</div>
        )}

        <div className="sheet-fill">
          <div><span>Job / Project</span><i /></div>
          <div><span>Equipment ID</span><i /></div>
          <div><span>Technician</span><i /></div>
          <div><span>Test date</span><i /></div>
        </div>

        <table className="sheet-table">
          <thead>
            <tr>
              <th>Element</th><th>Setting</th><th>Trust</th><th>Test ×</th><th>Test Current</th>
              <th>Expected</th><th>Min</th><th>Max</th><th>Method / Basis</th>
              <th className="wide">Measured</th><th>Pass / Fail</th>
            </tr>
          </thead>
          <tbody>
            {sheet.rows.map((r) => (
              <tr key={r.code + r.label} className={r.withheld ? 'wh' : ''}>
                <td className="el"><b>{r.code}</b> {r.label}{r.symbol ? ` (${r.symbol})` : ''}{r.note ? ' ‡' : ''}</td>
                <td>{r.setting}</td>
                <td className="badge-cell">{r.badge}</td>
                <td>{r.testAt}</td>
                <td className="num">{r.testCurrent}</td>
                <td className="num">{r.expected}</td>
                <td className="num">{r.min}</td>
                <td className="num">{r.max}</td>
                <td className="meth">{r.method}</td>
                <td className="fill">{r.measured}</td>
                <td className="fill" />
              </tr>
            ))}
          </tbody>
        </table>

        {elementNotes.length > 0 && (
          <div className="sheet-elnotes">
            {elementNotes.map((r) => (
              <div key={r.code + r.label}>‡ <b>{r.code} {r.label}:</b> {r.note}</div>
            ))}
          </div>
        )}
        {sheet.warnings.length > 0 && (
          <div className="sheet-warn">{sheet.warnings.join(' · ')}</div>
        )}
        {sheet.footnotes.length > 0 && (
          <div className="sheet-notes">
            {sheet.footnotes.map((f) => (<div key={f.slice(0, 24)}>{f}</div>))}
          </div>
        )}
        <div className="sheet-law">{sheet.footerLaw}</div>
        <div className="sheet-gen">operations.apexpowerops.com/lvbreakertcc — values served live from the governed device library at print time</div>
      </div>
    </div>
  )
}
