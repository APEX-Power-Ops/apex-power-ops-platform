'use client'

import { useEffect, useState } from 'react'

import {
  fetchMasterOperations,
  MasterOperationsError,
  MasterOperationsSummary,
} from '../lib/master-operations'

export function MasterOperationsExplorer() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [items, setItems] = useState<MasterOperationsSummary[]>([])

  useEffect(() => {
    let isActive = true

    async function load() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await fetchMasterOperations()
        if (isActive) {
          setItems(response)
        }
      } catch (error) {
        if (!isActive) {
          return
        }
        if (error instanceof MasterOperationsError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('The governed operations dashboard seam could not be reached from the browser shell.')
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

  const totalReady = items.reduce((sum, item) => sum + item.ready_to_work, 0)
  const totalOverdue = items.reduce((sum, item) => sum + item.overdue, 0)
  const totalRemainingHours = items.reduce((sum, item) => sum + item.remaining_hours, 0)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">First Operations Visibility Consumer Seam</p>
          <h2>Read the master operations dashboard through the governed ops API.</h2>
        </div>
        <p className="resource-lane-copy">
          This panel consumes `v_master_operations` through a read-only backend route instead of widening the
          browser boundary to direct Supabase reads.
        </p>
      </div>

      {isLoading ? <p className="resource-banner resource-banner-neutral">Loading the governed operations rollup…</p> : null}
      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!isLoading && !errorMessage ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Projects loaded</span>
              <strong>{items.length}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Ready apparatus</span>
              <strong>{totalReady}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Overdue apparatus</span>
              <strong>{totalOverdue}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Remaining hours</span>
              <strong>{totalRemainingHours.toFixed(1)}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {items.map((item) => (
              <article className="resource-item" key={item.project_id}>
                <div className="resource-item-row">
                  <span className="resource-chip">{item.health_status}</span>
                  <span className="resource-chip resource-chip-muted">{item.project_status ?? 'Unknown status'}</span>
                </div>
                <h3>{item.project_name ?? item.project_number ?? item.project_id}</h3>
                <p>
                  {[item.project_number, item.client_name, item.site_city, item.resa_location]
                    .filter((value) => typeof value === 'string' && value.trim().length > 0)
                    .join(' · ') || 'No secondary project metadata is available for this rollup row yet.'}
                </p>
                <dl>
                  <div>
                    <dt>Completion</dt>
                    <dd>{item.completion_percent.toFixed(2)}%</dd>
                  </div>
                  <div>
                    <dt>Ready to work</dt>
                    <dd>{item.ready_to_work}</dd>
                  </div>
                  <div>
                    <dt>Overdue</dt>
                    <dd>{item.overdue}</dd>
                  </div>
                  <div>
                    <dt>Due this week</dt>
                    <dd>{item.due_this_week}</dd>
                  </div>
                  <div>
                    <dt>Remaining hours</dt>
                    <dd>{item.remaining_hours.toFixed(1)}</dd>
                  </div>
                  <div>
                    <dt>Due date</dt>
                    <dd>{item.project_due ?? 'Unscheduled'}</dd>
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