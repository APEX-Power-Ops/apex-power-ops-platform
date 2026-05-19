'use client'

import Link from 'next/link'

const placeholderClasses = [
  'SCHEDULE_WINDOW_DRAFT',
  'STATUS_TRANSITION_DRAFT',
  'FIELD_HOLD_ESCALATION_DRAFT',
  'DISPATCH_SEQUENCE_DRAFT',
]

const guardrails = [
  'No live POST, schedule commit, status transition, dispatch release, or hold removal.',
  'No mutation-seam schedule or status route promotion.',
  'No reuse of field authorization, intake, or workfront context as live timing or state authority.',
  'No customer promise, external completion update, or crew-calendar commit from this route.',
  'No durable field record, production tracking, customer reporting, or finance output widening.',
  'No status history commit until a later separately admitted packet exists.',
]

const nextPlaceholderWork = [
  'Define the minimum schedule and status contract PM expects before timing or state can be changed for live work.',
  'Separate schedule or status planning from field authorization, daily records, and later production tracking proof.',
  'Define the exact hold, readiness, dispatch, promised-date, and state-transition evidence a later control branch would have to satisfy.',
  'Define explicit no-go conditions that keep schedule or status planning from being mistaken for live work-state authority.',
]

const separateBoundaries = [
  'Field authorization and assignment remain a separate upstream placeholder branch.',
  'Durable field record and production tracking remain separate later branches.',
  'Customer reporting, finance, customer billing delivery, and source writeback remain governed by their own branches.',
  'Customer delivery execution remains the admitted bounded proof branch and is not schedule or status authority.',
]

export default function ScheduleStatusPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Schedule And State Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Schedule and status stay blocked as a placeholder control branch.</h1>
            <p className="lede">
              This route records the current timing and state-control truth after read-only intake, workfront, and
              field-authorization planning: schedule and status may move forward only as placeholder taxonomy,
              guardrails, hold-and-dispatch planning, and later admission preparation. It does not admit schedule
              changes, status writes, promised dates, hold release, durable field records, or production tracking.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/schedule-status-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only schedule and status placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Schedule and status placeholder only; live timing and state control remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Schedule Status Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep schedule and status as placeholder
              planning, or later open a separate admitted packet for live timing and state control authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/field-authorization-placeholder">Field authorization placeholder</Link>
            <Link href="/pm-review/workfront">PM workfront</Link>
            <Link href="/pm-review/schedule.html">Schedule review</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Schedule and status may advance as no-live design work only. No live timing or state authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Schedule changes, status transitions, promised dates, hold release, durable field records, and production tracking remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, hold-and-dispatch planning, evidence expectations, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Schedule status placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, schedule change, or status authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Schedule status placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next schedule status placeholder work">
          <h3>Recommended Next Schedule Status Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for schedule status">
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