'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

import {
  fetchRevenueRecognition,
  rollupByProject,
  ProjectRevenueRollup,
  RevenueRecognitionError,
} from '../../../lib/revenue-recognition'

const usd = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export default function FinancePage() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [projects, setProjects] = useState<ProjectRevenueRollup[]>([])

  useEffect(() => {
    let isActive = true
    async function load() {
      setIsLoading(true)
      setErrorMessage(null)
      try {
        const rows = await fetchRevenueRecognition()
        if (isActive) setProjects(rollupByProject(rows))
      } catch (error) {
        if (!isActive) return
        setErrorMessage(
          error instanceof RevenueRecognitionError
            ? error.message
            : 'The governed recognized-revenue seam could not be reached from the browser shell.',
        )
        setProjects([])
      } finally {
        if (isActive) setIsLoading(false)
      }
    }
    void load()
    return () => {
      isActive = false
    }
  }, [])

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Execution &rarr; Billing</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Recognized revenue by project (read-only).</h1>
            <p className="lede">
              Recognized = quoted revenue of apparatus marked Complete (binary, at completion),
              derived from apparatus completion &mdash; not yet a persisted recognition ledger. Billable =
              recognized &minus; billed; billing is not admitted, so billable equals recognized. This route
              is read-only: it admits no billing, invoice, payroll, accounting, export, or source
              writeback.
            </p>
          </div>
          <dl className="contract-panel">
            <div><dt>Promoted route</dt><dd>/pm-review/finance</dd></div>
            <div><dt>Current route class</dt><dd>Read-only derived recognized-revenue view</dd></div>
            <div><dt>Authority posture</dt><dd>Finance READ admitted; finance writes remain held</dd></div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Recognized Revenue</h2>
            <p>Derived live through the governed control-plane API; no direct browser database reads.</p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder (writes held)</Link>
          </p>
        </div>

        {isLoading ? <p className="resource-banner resource-banner-neutral">Loading recognized revenue&hellip;</p> : null}
        {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

        {!isLoading && !errorMessage ? (
          <div className="resource-results">
            {projects.length === 0 ? (
              <p className="resource-banner resource-banner-neutral">No active projects with quoted revenue yet.</p>
            ) : null}
            <div className="resource-grid">
              {projects.map((project) => (
                <article className="resource-item" key={project.project_id}>
                  <div className="resource-item-row">
                    <span className="resource-chip">{project.recognition_percent.toFixed(2)}% recognized</span>
                    <span className="resource-chip resource-chip-muted">
                      {project.completed_apparatus}/{project.total_apparatus} apparatus complete
                    </span>
                  </div>
                  <h3>
                    {[project.project_number, project.project_name]
                      .filter((value) => typeof value === 'string' && value.trim().length > 0)
                      .join(' · ') || 'Unnamed project'}
                  </h3>
                  <dl>
                    <div><dt>Quoted</dt><dd>{usd(project.quoted_revenue)}</dd></div>
                    <div><dt>Recognized</dt><dd>{usd(project.recognized_revenue)}</dd></div>
                    <div><dt>Billable now</dt><dd>{usd(project.billable_now)}</dd></div>
                  </dl>
                  <ul>
                    {project.scopes.map((scope) => (
                      <li key={scope.scope_id ?? scope.scope_name ?? 'scope'}>
                        {scope.scope_name ?? 'Unnamed scope'}: {usd(scope.recognized_revenue)} of {usd(scope.quoted_revenue)} ({scope.recognition_percent.toFixed(2)}%)
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  )
}
