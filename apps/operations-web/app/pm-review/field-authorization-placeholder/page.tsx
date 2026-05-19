'use client'

import Link from 'next/link'

const placeholderClasses = [
  'FIELD_AUTHORIZATION_DRAFT',
  'LEAD_ASSIGNMENT_DRAFT',
  'CREW_ASSIGNMENT_DRAFT',
  'FIELD_RELEASE_GATE_DRAFT',
]

const guardrails = [
  'No live POST, authorization, assignment, dispatch, or field release.',
  'No mutation-seam field authorization or assignment route promotion.',
  'No reuse of import, approval, or field-prep context as live field authority.',
  'No schedule or status write widening from this route.',
  'No durable field record, production tracking, customer reporting, or finance output widening.',
  'No lead or crew assignment commit until a later separately admitted packet exists.',
]

const nextPlaceholderWork = [
  'Define the minimum field authorization contract PM expects before any work can be released to lead or field roles.',
  'Separate field authorization planning from intake review, field-prep questions, and later schedule or status controls.',
  'Define the exact lead, crew, access, and safety proof that any later authorization branch would have to satisfy.',
  'Define explicit no-go conditions that keep field authorization planning from being mistaken for live work release authority.',
]

const separateBoundaries = [
  'Import approval and project import remain separate prerequisite branches.',
  'Schedule or status controls remain a separate later branch after field authorization and assignment proof exists.',
  'Durable field record and production tracking remain separate later branches.',
  'Finance, customer billing delivery, and source writeback remain governed by their own branches.',
]

export default function FieldAuthorizationPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Field Authority Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Field authorization and assignment stay blocked as a placeholder branch.</h1>
            <p className="lede">
              This route records the current field-authority truth after read-only intake and field-prep context: field
              authorization and assignment can move forward only as placeholder taxonomy, guardrails, release-gate
              planning, and later admission preparation. It does not admit work authorization, lead or crew assignment,
              schedule changes, status writes, durable field records, or production tracking.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/field-authorization-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only field authorization placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Field authorization placeholder only; assignment and work release remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Field Authorization Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep field authorization and assignment as
              placeholder planning, or later open a separate admitted packet for live field release authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/import-intake">Intake workbench</Link>
            <Link href="/pm-review/import-candidate">Import candidate</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Field authorization may advance as no-live design work only. No live work release authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Lead assignment, crew assignment, schedule changes, status writes, durable field records, and production tracking remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, release-gate planning, evidence expectations, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Field authorization placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, assignment, or work-release authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Field authorization placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next field authorization placeholder work">
          <h3>Recommended Next Field Authorization Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for field authorization">
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