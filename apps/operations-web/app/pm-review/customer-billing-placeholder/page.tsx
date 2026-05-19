'use client'

import Link from 'next/link'

const placeholderClasses = [
  'CUSTOMER_BILLING_DELIVERY_DRAFT',
  'BILLING_EXPORT_PACKAGE_DRAFT',
  'INVOICE_RELEASE_DRAFT',
  'RECEIVABLE_NOTICE_DRAFT',
]

const guardrails = [
  'No live POST, write, export, invoice, email, portal push, or customer delivery artifact release.',
  'No mutation-seam customer billing route promotion.',
  'No reuse of customer-delivery execution proof as billing authority.',
  'No widening into finance write authority, payroll, accounting persistence, or external sync.',
  'No source workbook or PDF writeback widening.',
  'No customer-facing billing commitment until a later separately admitted packet exists.',
]

const nextPlaceholderWork = [
  'Define the minimum customer-facing billing package PM expects after the internal finance handoff is complete.',
  'Separate customer billing delivery from internal finance handoff, payroll, and accounting persistence.',
  'Define the exact customer-facing artifacts, recipient rules, and release checkpoints for any later billing branch.',
  'Define explicit no-go conditions that keep customer billing planning from being mistaken for a live delivery authority.',
]

const separateBoundaries = [
  'Financial handoff remains a separate placeholder branch.',
  'Finance output remains a separate placeholder branch.',
  'Customer delivery execution remains the admitted bounded proof branch and is not billing authority.',
  'Source workbook or PDF writeback and workbook macros remain a separate later source-authority branch.',
  'Approval, import, assignment, schedule or status, field authorization, durable field record, and production tracking remain governed by their own branches.',
]

export default function CustomerBillingPlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Downstream Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Customer billing delivery stays blocked as a placeholder downstream branch.</h1>
            <p className="lede">
              This route records the current downstream truth after the financial-handoff and finance placeholder
              branches: customer billing delivery can move forward only as placeholder taxonomy, guardrails,
              customer-facing release planning, and later admission preparation. It does not admit billing exports,
              invoice release, customer billing notifications, finance writes, external finance sync, or source
              writeback.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/customer-billing-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only customer billing placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Customer billing delivery placeholder only; downstream writes remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Customer Billing Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep customer billing delivery as
              placeholder planning, or later open a separate admitted packet for customer-facing billing release.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/financial-handoff-placeholder">Financial handoff placeholder</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder</Link>
            <Link href="/pm-review/source-writeback-placeholder">Source writeback placeholder</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Customer billing delivery may advance as no-live design work only. No live customer-facing billing authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Billing export release, invoice delivery, external finance sync, customer-facing billing notices, and source writeback remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, customer-facing release planning, evidence expectations, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer billing placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, persistence target, or customer-facing release authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer billing placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next customer billing placeholder work">
          <h3>Recommended Next Customer Billing Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Separate branches still held">
          <h3>Separate Branches Still Held</h3>
          <ul>
            {separateBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>
            The separate financial-handoff placeholder route is available at{' '}
            <Link href="/pm-review/financial-handoff-placeholder">/pm-review/financial-handoff-placeholder</Link>.
          </p>
          <p>
            The separate source-writeback placeholder route is available at{' '}
            <Link href="/pm-review/source-writeback-placeholder">/pm-review/source-writeback-placeholder</Link>.
          </p>
        </div>
      </section>
    </main>
  )
}