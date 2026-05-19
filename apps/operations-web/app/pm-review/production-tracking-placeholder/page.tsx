'use client'

import Link from 'next/link'

const placeholderClasses = [
  'PRODUCTION_QUANTITY_DRAFT',
  'LABOR_PROGRESS_DRAFT',
  'APPARATUS_COMPLETION_DRAFT',
  'READBACK_AUDIT_DRAFT',
]

const guardrails = [
  'No live POST, production quantity write, labor progress write, apparatus completion update, or audit readback commit.',
  'No mutation-seam production tracking route promotion.',
  'No reuse of durable field record, schedule or status, or workfront context as live production authority.',
  'No customer reporting, invoice, payroll, or source writeback widening from this route.',
  'No performance metric or completion truth commit until a later separately admitted packet exists.',
  'No production dashboard or report publication from this route.',
]

const nextPlaceholderWork = [
  'Define the minimum production tracking contract PM expects before quantity, labor, and apparatus progress can become system truth.',
  'Separate production tracking planning from durable field record evidence, customer reporting, and later financial handoff proof.',
  'Define the exact quantity, labor, apparatus, completion, and audit readback evidence a later production branch would have to satisfy.',
  'Define explicit no-go conditions that keep production tracking planning from being mistaken for live progress authority.',
]

const separateBoundaries = [
  'Durable field record remains a separate upstream placeholder branch.',
  'Customer reporting and financial handoff remain separate later branches.',
  'Finance, customer billing delivery, and source writeback remain governed by their own branches.',
  'Customer delivery execution remains the admitted bounded proof branch and is not production tracking authority.',
]

export default function ProductionTrackingPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Production Tracking Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Production tracking stays blocked as a placeholder progress branch.</h1>
            <p className="lede">
              This route records the current progress-truth boundary after read-only intake, workfront, field
              authorization, schedule-status, and durable-field-record planning: production tracking may move forward
              only as placeholder taxonomy, guardrails, progress-package planning, and later admission preparation. It
              does not admit quantity writes, labor progress writes, apparatus completion updates, or customer-facing
              production truth.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/production-tracking-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only production tracking placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Production tracking placeholder only; live progress authority remains not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Production Tracking Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep production tracking as placeholder
              planning, or later open a separate admitted packet for live quantity, labor, apparatus, and progress
              authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/durable-field-record-placeholder">Durable field record placeholder</Link>
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
            <p>Production tracking may advance as no-live design work only. No live progress authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Quantity writes, labor progress writes, apparatus completion updates, customer reporting, and financial handoff remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, progress-package planning, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Production tracking placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, progress write, or production authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Production tracking placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next production tracking placeholder work">
          <h3>Recommended Next Production Tracking Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for production tracking">
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