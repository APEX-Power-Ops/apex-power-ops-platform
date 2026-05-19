'use client'

import Link from 'next/link'

const placeholderClasses = [
  'DAILY_RECORD_PACKET_DRAFT',
  'FIELD_EVIDENCE_BUNDLE_DRAFT',
  'LABOR_READBACK_DRAFT',
  'COMPLETION_NOTE_DRAFT',
]

const guardrails = [
  'No live POST, daily record commit, evidence upload, labor readback, or completion-note release.',
  'No mutation-seam durable field record route promotion.',
  'No reuse of schedule or status, field authorization, or workfront context as live daily-record authority.',
  'No quantity, labor, apparatus, or completion truth commit from this route.',
  'No customer reporting, finance output, customer billing delivery, or source writeback widening.',
  'No production tracking row commit until a later separately admitted packet exists.',
]

const nextPlaceholderWork = [
  'Define the minimum durable field record contract PM expects before a daily record can become system truth.',
  'Separate durable field record planning from schedule or status control and later production tracking proof.',
  'Define the exact labor, evidence, apparatus, and completion support a later durable-record branch would have to satisfy.',
  'Define explicit no-go conditions that keep durable field record planning from being mistaken for live field evidence authority.',
]

const separateBoundaries = [
  'Schedule and status remain a separate upstream placeholder branch.',
  'Production tracking remains a separate later branch.',
  'Customer reporting, finance, customer billing delivery, and source writeback remain governed by their own branches.',
  'Customer delivery execution remains the admitted bounded proof branch and is not durable field record authority.',
]

export default function DurableFieldRecordPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Durable Field Record Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Durable field record stays blocked as a placeholder evidence branch.</h1>
            <p className="lede">
              This route records the current field-evidence truth after read-only intake, workfront, field
              authorization, and schedule-status planning: durable field records may move forward only as placeholder
              taxonomy, guardrails, evidence-package planning, and later admission preparation. It does not admit
              daily record writes, evidence uploads, labor readback, completion notes, or production tracking.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/durable-field-record-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only durable field record placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Durable field record placeholder only; live field evidence remains not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Durable Field Record Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep durable field records as placeholder
              planning, or later open a separate admitted packet for live daily-record and evidence authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/schedule-status-placeholder">Schedule status placeholder</Link>
            <Link href="/pm-review/production-tracking-placeholder">Production tracking placeholder</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Durable field records may advance as no-live design work only. No live field evidence authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Daily record writes, evidence uploads, labor readback, completion notes, and production tracking remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, evidence-package planning, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Durable field record placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, daily record write, or field evidence authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Durable field record placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next durable field record placeholder work">
          <h3>Recommended Next Durable Field Record Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for durable field record">
          <h3>Separate Branches Still Held</h3>
          <ul>
            {separateBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>
            <Link href="/pm-review/production-tracking-placeholder">Production tracking placeholder</Link> carries the
            next separate no-live branch after durable field record planning. It does not admit quantity, labor, or
            apparatus progress authority.
          </p>
        </div>
      </section>
    </main>
  )
}