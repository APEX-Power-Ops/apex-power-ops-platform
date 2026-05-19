'use client'

import Link from 'next/link'

const placeholderClasses = [
  'CUSTOMER_REPORT_DRAFT',
  'COMPLETION_EVIDENCE_DRAFT',
  'REPORT_REVIEW_STATE_DRAFT',
  'CUSTOMER_READBACK_AUDIT_DRAFT',
]

const guardrails = [
  'No live POST, customer report creation, completion evidence generation, or customer-facing publication.',
  'No mutation-seam customer reporting route promotion.',
  'No reuse of production tracking, durable field record, or customer delivery execution proof as live reporting authority.',
  'No invoice, billing export, payroll export, accounting record, or finance-system sync widening from this route.',
  'No customer-facing completion truth commit until a later separately admitted packet exists.',
  'No hosted UI mutation, backend route, or production write from this route.',
]

const nextPlaceholderWork = [
  'Define the minimum customer report contract PM expects before any report can become customer-facing truth.',
  'Separate customer reporting planning from production tracking proof and later financial handoff proof.',
  'Define the exact production evidence, completion evidence, audience, review state, and readback a later reporting branch would have to satisfy.',
  'Define explicit no-go conditions that keep customer reporting planning from being mistaken for live customer-facing authority.',
]

const separateBoundaries = [
  'Production tracking remains a separate upstream placeholder branch.',
  'Financial handoff remains a separate later branch.',
  'Finance, customer billing delivery, and source writeback remain governed by their own branches.',
  'Customer delivery execution remains the admitted bounded proof branch and is not customer reporting authority.',
]

export default function CustomerReportingPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Customer Reporting Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Customer reporting stays blocked as a placeholder downstream branch.</h1>
            <p className="lede">
              This route records the current customer-facing output boundary after read-only intake, production
              tracking planning, and the admitted customer-delivery proof seam: customer reporting may move forward
              only as placeholder taxonomy, guardrails, report-package planning, and later admission preparation. It
              does not admit customer reports, completion evidence publication, invoice creation, payroll export, or
              accounting output.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/customer-reporting-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only customer reporting placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Customer reporting placeholder only; customer-facing output remains not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Customer Reporting Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep customer reporting as placeholder
              planning, or later open a separate admitted packet for live report and completion-evidence authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/production-tracking-placeholder">Production tracking placeholder</Link>
            <Link href="/pm-review/financial-handoff-placeholder">Financial handoff placeholder</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Customer reporting may advance as no-live design work only. No live customer-facing output authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Customer reports, completion evidence publication, billing exports, payroll exports, and accounting outputs remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, report-package planning, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer reporting placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, report release, or customer-facing authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer reporting placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next customer reporting placeholder work">
          <h3>Recommended Next Customer Reporting Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for customer reporting">
          <h3>Separate Branches Still Held</h3>
          <ul>
            {separateBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>
            <Link href="/pm-review/financial-handoff-placeholder">Financial handoff placeholder</Link> carries the
            next separate no-live branch after customer reporting planning. It does not admit billing export, payroll
            export, or accounting output.
          </p>
        </div>
      </section>
    </main>
  )
}