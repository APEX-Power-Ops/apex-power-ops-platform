'use client'

import Link from 'next/link'

const placeholderClasses = [
  'FINANCE_HANDOFF_DRAFT',
  'BILLING_EXPORT_DRAFT',
  'PAYROLL_EXPORT_DRAFT',
  'ACCOUNTING_POST_DRAFT',
  'LABOR_RECONCILIATION_DRAFT',
]

const guardrails = [
  'No live POST, write, export, sync, or delivery.',
  'No mutation-seam finance route promotion.',
  'No Supabase finance write or schema change.',
  'No customer billing delivery widening.',
  'No source workbook or PDF writeback widening.',
  'No reuse of the customer-delivery admission phrase for finance.',
]

const nextPlaceholderWork = [
  'Define the minimum placeholder finance handoff contract PM expects after customer delivery execution.',
  'Separate internal finance handoff planning from external customer billing delivery.',
  'Define the evidence PM must retain before any later finance-output admission can be considered.',
  'Define explicit no-go conditions that keep finance placeholder work from being mistaken for live authority.',
]

const separateBoundaries = [
  'Customer billing delivery remains a separate later downstream branch.',
  'Source workbook or PDF writeback and workbook macros remain a separate later source-authority branch.',
  'Approval, import, assignment, schedule or status, field authorization, durable field record, and production tracking remain governed by their own branches.',
]

export default function FinancePlaceholderPage() {
  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Downstream Planning</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Finance is open only as a placeholder design branch.</h1>
            <p className="lede">
              This route records the current downstream truth after the admitted customer-delivery slice: finance can
              move forward only as placeholder taxonomy, guardrails, no-go checks, output-shape planning, and later
              admission preparation. It does not admit billing, payroll, invoice, accounting, external finance sync,
              customer billing delivery, or source writeback.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/finance-placeholder</dd>
            </div>
            <div>
              <dt>Current route class</dt>
              <dd>Documentation-backed read-only placeholder planning</dd>
            </div>
            <div>
              <dt>Authority posture</dt>
              <dd>Finance placeholder only; downstream writes remain not admitted</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Finance Placeholder Scope</h2>
            <p>
              Use this surface when the PM decision is branch selection only: keep finance as placeholder planning, or
              later open a separate admitted packet for finance output, customer billing delivery, or source writeback.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/import-admission-plan">Import admission plan</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
            <Link href="/pm-review/customer-billing-placeholder">Customer billing placeholder</Link>
          </p>
        </div>

        <div className="status-grid status-grid-wide">
          <article className="status-card">
            <div className="status-row">
              <h3>Current posture</h3>
              <span className="status-pill status-deferred">placeholder only</span>
            </div>
            <p>Finance may advance as no-live design work only. No live finance authority is admitted here.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Still blocked</h3>
              <span className="status-pill status-deferred">not admitted</span>
            </div>
            <p>Billing export, payroll export, invoice creation, accounting persistence, customer billing delivery, and source writeback remain blocked.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h3>Use this route for</h3>
              <span className="status-pill status-configured">design only</span>
            </div>
            <p>Placeholder taxonomy, guardrails, evidence expectations, no-go checks, and later-admission preparation.</p>
          </article>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Finance placeholder taxonomy">
          <h3>Placeholder Output Taxonomy</h3>
          <p>These labels are planning classes only. They do not imply a live route, persistence target, or delivery authority.</p>
          <ul>
            {placeholderClasses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Finance placeholder guardrails">
          <h3>Placeholder Guardrails</h3>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Recommended next finance placeholder work">
          <h3>Recommended Next Finance Placeholder Work</h3>
          <ul>
            {nextPlaceholderWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Non-finance boundaries still separate">
          <h3>Non-Finance Boundaries Still Separate</h3>
          <ul>
            {separateBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>
            The separate customer-billing placeholder route is available at{' '}
            <Link href="/pm-review/customer-billing-placeholder">/pm-review/customer-billing-placeholder</Link>.
          </p>
        </div>
      </section>
    </main>
  )
}