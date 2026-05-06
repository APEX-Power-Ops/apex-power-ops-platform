'use client'

import { useEffect, useState } from 'react'

import {
  ApparatusByCategoryError,
  ApparatusByCategorySummaryRow,
  fetchApparatusByCategory,
} from '../lib/apparatus-by-category'

export function ApparatusByCategoryExplorer() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [items, setItems] = useState<ApparatusByCategorySummaryRow[]>([])

  useEffect(() => {
    let isActive = true

    async function load() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await fetchApparatusByCategory()
        if (isActive) {
          setItems(response)
        }
      } catch (error) {
        if (!isActive) {
          return
        }
        if (error instanceof ApparatusByCategoryError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('The governed apparatus-by-category seam could not be reached from the browser shell.')
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

  const totalCategories = items.length
  const totalBlocked = items.reduce((sum, item) => sum + item.blocked, 0)
  const totalReady = items.reduce((sum, item) => sum + item.ready_to_work, 0)
  const totalRemaining = items.reduce((sum, item) => sum + item.remaining, 0)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Adjacent Operations Visibility Consumer</p>
          <h2>Read grouped apparatus categories through the governed ops API.</h2>
        </div>
        <p className="resource-lane-copy">
          This panel consumes `v_apparatus_by_category` through a read-only backend route so grouped apparatus
          breakdowns stay inside the governed browser boundary.
        </p>
      </div>

      {isLoading ? <p className="resource-banner resource-banner-neutral">Loading the governed category rollup…</p> : null}
      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!isLoading && !errorMessage ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Category rows loaded</span>
              <strong>{totalCategories}</strong>
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
              <span className="resource-summary-label">Remaining apparatus</span>
              <strong>{totalRemaining}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {items.map((item) => (
              <article className="resource-item" key={`${item.project_id}-${item.scope_id ?? 'unknown-scope'}-${item.apparatus_category ?? 'unknown-category'}`}>
                <div className="resource-item-row">
                  <span className="resource-chip">{item.apparatus_category ?? 'Unspecified'}</span>
                  <span className="resource-chip resource-chip-muted">{item.percent_complete.toFixed(2)}% complete</span>
                </div>
                <h3>{item.scope_name ?? 'Unnamed scope'}</h3>
                <p>{[item.project_number, item.apparatus_category].filter(Boolean).join(' · ')}</p>
                <dl>
                  <div>
                    <dt>Total count</dt>
                    <dd>{item.total_count}</dd>
                  </div>
                  <div>
                    <dt>Remaining</dt>
                    <dd>{item.remaining}</dd>
                  </div>
                  <div>
                    <dt>Blocked</dt>
                    <dd>{item.blocked}</dd>
                  </div>
                  <div>
                    <dt>Ready to work</dt>
                    <dd>{item.ready_to_work}</dd>
                  </div>
                  <div>
                    <dt>Completed</dt>
                    <dd>{item.completed}</dd>
                  </div>
                  <div>
                    <dt>Project</dt>
                    <dd>{item.project_number ?? 'Unknown project'}</dd>
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