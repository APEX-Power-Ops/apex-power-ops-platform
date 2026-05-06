'use client'

import { useEffect, useState } from 'react'

import {
  fetchScheduleHealth,
  ScheduleHealthError,
  ScheduleHealthSummary,
} from '../lib/schedule-health'

export function ScheduleHealthExplorer() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [items, setItems] = useState<ScheduleHealthSummary[]>([])

  useEffect(() => {
    let isActive = true

    async function load() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await fetchScheduleHealth()
        if (isActive) {
          setItems(response)
        }
      } catch (error) {
        if (!isActive) {
          return
        }
        if (error instanceof ScheduleHealthError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('The governed schedule-health seam could not be reached from the browser shell.')
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

  const atRiskCount = items.filter((item) => item.health_status === 'At Risk').length
  const blockedCount = items.filter((item) => item.health_status === 'Blocked').length
  const overdueTotal = items.reduce((sum, item) => sum + item.overdue_items, 0)
  const onHoldTotal = items.reduce((sum, item) => sum + item.on_hold_items, 0)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Adjacent Operations Visibility Consumer</p>
          <h2>Read scope-level schedule health through the governed ops API.</h2>
        </div>
        <p className="resource-lane-copy">
          This panel consumes `v_schedule_health` through a read-only backend route so scope risk visibility stays
          inside the governed browser boundary.
        </p>
      </div>

      {isLoading ? <p className="resource-banner resource-banner-neutral">Loading the governed schedule health rollup…</p> : null}
      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!isLoading && !errorMessage ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Scope rows loaded</span>
              <strong>{items.length}</strong>
            </div>
            <div>
              <span className="resource-summary-label">At-risk scopes</span>
              <strong>{atRiskCount}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Blocked scopes</span>
              <strong>{blockedCount}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Overdue items</span>
              <strong>{overdueTotal}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {items.map((item) => (
              <article className="resource-item" key={`${item.project_number ?? 'unknown'}-${item.scope_name ?? 'unknown'}`}>
                <div className="resource-item-row">
                  <span className="resource-chip">{item.health_status}</span>
                  <span className="resource-chip resource-chip-muted">{item.percent_complete.toFixed(2)}% complete</span>
                </div>
                <h3>{item.scope_name ?? 'Unnamed scope'}</h3>
                <p>
                  {[item.project_number, item.project_name]
                    .filter((value) => typeof value === 'string' && value.trim().length > 0)
                    .join(' · ') || 'No project metadata is available for this schedule row yet.'}
                </p>
                <dl>
                  <div>
                    <dt>Overdue items</dt>
                    <dd>{item.overdue_items}</dd>
                  </div>
                  <div>
                    <dt>On hold</dt>
                    <dd>{item.on_hold_items}</dd>
                  </div>
                  <div>
                    <dt>Not available</dt>
                    <dd>{item.not_available_items}</dd>
                  </div>
                  <div>
                    <dt>Scope due</dt>
                    <dd>{item.scope_due ?? 'Unscheduled'}</dd>
                  </div>
                  <div>
                    <dt>Project due</dt>
                    <dd>{item.project_due ?? 'Unscheduled'}</dd>
                  </div>
                  <div>
                    <dt>At-risk and blocked</dt>
                    <dd>{item.overdue_items + item.on_hold_items}</dd>
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