'use client'

import { useEffect, useState } from 'react'

import {
  fetchProjectApparatusSummary,
  ProjectApparatusSummaryError,
  ProjectApparatusSummaryRow,
} from '../lib/project-apparatus-summary'

export function ProjectApparatusSummaryExplorer() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [items, setItems] = useState<ProjectApparatusSummaryRow[]>([])

  useEffect(() => {
    let isActive = true

    async function load() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await fetchProjectApparatusSummary()
        if (isActive) {
          setItems(response)
        }
      } catch (error) {
        if (!isActive) {
          return
        }
        if (error instanceof ProjectApparatusSummaryError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('The governed scope KPI seam could not be reached from the browser shell.')
        }
        setItems([])
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void load()

    return () => {
      isActive = false
    }
  }, [])

  const totalScopes = items.length
  const totalBlocked = items.reduce((sum, item) => sum + item.blocked, 0)
  const totalReady = items.reduce((sum, item) => sum + item.ready_to_work, 0)
  const totalRemainingHours = items.reduce((sum, item) => sum + item.remaining_hours, 0)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Adjacent Operations Visibility Consumer</p>
          <h2>Read scope KPI rollups through the governed ops API.</h2>
        </div>
        <p className="resource-lane-copy">
          This panel consumes `v_project_apparatus_summary` through a read-only backend route so scope-level KPI
          visibility stays inside the governed browser boundary.
        </p>
      </div>

      {isLoading ? <p className="resource-banner resource-banner-neutral">Loading the governed scope KPI rollup…</p> : null}
      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!isLoading && !errorMessage ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Scope rows loaded</span>
              <strong>{totalScopes}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Blocked apparatus</span>
              <strong>{totalBlocked}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Ready apparatus</span>
              <strong>{totalReady}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Remaining hours</span>
              <strong>{totalRemainingHours.toFixed(1)}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {items.map((item) => (
              <article className="resource-item" key={`${item.project_id}-${item.scope_id ?? item.scope_name ?? 'unknown-scope'}`}>
                <div className="resource-item-row">
                  <span className="resource-chip">{item.completion_percent.toFixed(2)}% complete</span>
                  <span className="resource-chip resource-chip-muted">{item.total_remaining} remaining</span>
                </div>
                <h3>{item.scope_name ?? 'Unnamed scope'}</h3>
                <p>
                  {[item.project_number, item.project_name]
                    .filter((value) => typeof value === 'string' && value.trim().length > 0)
                    .join(' · ') || 'No project metadata is available for this scope KPI row yet.'}
                </p>
                <dl>
                  <div>
                    <dt>Total apparatus</dt>
                    <dd>{item.total_apparatus}</dd>
                  </div>
                  <div>
                    <dt>Blocked</dt>
                    <dd>{item.blocked}</dd>
                  </div>
                  <div>
                    <dt>Issues failed</dt>
                    <dd>{item.issues_failed}</dd>
                  </div>
                  <div>
                    <dt>Past due</dt>
                    <dd>{item.past_due}</dd>
                  </div>
                  <div>
                    <dt>Quoted hours</dt>
                    <dd>{item.total_quoted_hours.toFixed(1)}</dd>
                  </div>
                  <div>
                    <dt>Remaining hours</dt>
                    <dd>{item.remaining_hours.toFixed(1)}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}