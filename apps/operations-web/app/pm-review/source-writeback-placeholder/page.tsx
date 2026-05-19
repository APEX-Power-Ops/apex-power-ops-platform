'use client'

import Link from 'next/link'

const placeholderClasses = [
  'SOURCE_WORKBOOK_WRITEBACK_DRAFT',
  'SOURCE_PDF_WRITEBACK_DRAFT',
  'SOURCE_CORRECTION_PACKAGE_DRAFT',
  'SOURCE_MACRO_EXECUTION_DRAFT',
]

const guardrails = [
  'No live POST, workbook writeback, PDF overwrite, macro execution, or source-system sync.',
  'No mutation-seam source writeback route promotion.',
  'No reuse of import, approval, or customer-delivery proof as source writeback authority.',
  'No widening into finance output, customer billing delivery, or external customer release authority.',
  'No source workbook macro run or source-of-record file replacement from this route.',
  'No source correction commit until a later separately admitted packet exists.',
]

const nextPlaceholderWork = [
  'Define the minimum source correction and writeback package PM expects after review and downstream planning are settled.',
  'Separate source writeback planning from finance handoff, customer billing delivery, and customer-facing delivery proof.',
  'Define the exact workbook, PDF, and source lineage artifacts that any later writeback branch would have to prove.',
  'Define explicit no-go conditions that keep source writeback planning from being mistaken for live source authority.',
]

const separateBoundaries = [
  'Finance handoff planning remains a separate placeholder branch.',
  'Customer billing delivery remains a separate placeholder branch.',
  'Customer delivery execution remains the admitted bounded proof branch and is not source authority.',
  'Approval, import, assignment, schedule or status, field authorization, durable field record, and production tracking remain governed by their own branches.',
]

export default function SourceWritebackPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Downstream Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Source writeback stays blocked as a placeholder downstream branch.</h1>
            <p className="lede">
              This route records the current downstream truth after the admitted customer-delivery slice plus the
              finance and customer-billing placeholder branches: source writeback can move forward only as placeholder
              taxonomy, guardrails, correction-package planning, and later admission preparation. It does not admit
              workbook writeback, PDF overwrite, macro execution, source-system sync, finance writes, or customer
              billing delivery.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/source-writeback-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only source writeback placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Source writeback placeholder only; downstream writes remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Source Writeback Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep source writeback as placeholder
              planning, or later open a separate admitted packet for source correction and writeback authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder</Link>
            <Link href="/pm-review/customer-billing-placeholder">Customer billing placeholder</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Source writeback may advance as no-live design work only. No live source authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Workbook writeback, PDF overwrite, macro execution, source-system sync, finance output, and customer billing delivery remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, correction-package planning, evidence expectations, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Source writeback placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, file write, or source-of-record authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Source writeback placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next source writeback placeholder work">
          <h3>Recommended Next Source Writeback Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for source writeback">
          <h3>Separate Branches Still Held</h3>
          <ul>
            {separateBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  )
}