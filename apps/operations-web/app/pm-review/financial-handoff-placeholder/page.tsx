'use client'

import Link from 'next/link'

const placeholderClasses = [
  'BILLING_EXPORT_DRAFT',
  'PAYROLL_EXPORT_DRAFT',
  'LABOR_RECONCILIATION_DRAFT',
  'HANDOFF_AUDIT_READBACK_DRAFT',
]

const guardrails = [
  'No live POST, billing export, payroll export, invoice creation, or accounting output from this route.',
  'No hosted finance mutation, finance-system sync, or production handoff write from this route.',
  'No reuse of customer reporting, production tracking, or customer delivery execution proof as live financial authority.',
  'No customer-facing report release or completion-evidence acceptance widening from this route.',
  'No durable payroll, accounting, cost posting, or external finance sync state may be created here.',
  'No backend route or mutation-seam promotion is admitted by this placeholder branch.',
]

const nextPlaceholderWork = [
  'Define the minimum billing export contract before any billable handoff can exist.',
  'Define the approved labor and payroll-source contract before any payroll export can exist.',
  'Define labor reconciliation, audit lineage, idempotent replay, exception handling, and readback expectations for a later admitted handoff packet.',
  'Keep customer reporting release, finance output, customer billing delivery, and source writeback as separate downstream branches.',
]

const separateBoundaries = [
  'Customer reporting remains a separate upstream placeholder branch.',
  'Finance output remains a separate later branch.',
  'Customer billing delivery and source writeback remain separate later branches.',
  'Invoices, accounting records, and external finance-system sync remain outside PM authority until separate admission exists.',
]

export default function FinancialHandoffPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Financial Handoff Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Financial handoff stays blocked as a placeholder downstream branch.</h1>
            <p className="lede">
              This route records the current downstream handoff boundary after customer reporting planning: financial
              handoff may move forward only as placeholder taxonomy, guardrails, billing and payroll contract planning,
              reconciliation design, and later admission preparation. It does not admit billing export, payroll export,
              invoice creation, accounting output, finance-system sync, or source writeback.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/financial-handoff-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only financial handoff placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Financial handoff placeholder only; billing, payroll, and accounting output remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Financial Handoff Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep financial handoff as placeholder
              planning, or later open a separate admitted packet for billing export, payroll export, and reconciliation
              authority.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/customer-reporting-placeholder">Customer reporting placeholder</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder</Link>
            <Link href="/pm-review/customer-billing-placeholder">Customer billing placeholder</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Financial handoff may advance as no-live design work only. No billing, payroll, or accounting authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Billing exports, payroll exports, invoice creation, accounting outputs, finance sync, and source writeback remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, billing and payroll contract planning, reconciliation design, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Financial handoff placeholder taxonomy">
          <h3>Placeholder Handoff Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live export, invoice, payroll release, or accounting authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Financial handoff placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next financial handoff placeholder work">
          <h3>Recommended Next Financial Handoff Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held for financial handoff">
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