'use client'

import { useEffect, useState } from 'react'

import {
  BlockersSummaryError,
  BlockersSummaryRow,
  fetchBlockersSummary,
} from '../lib/blockers-summary'

export function BlockersSummaryExplorer() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [items, setItems] = useState<BlockersSummaryRow[]>([])

  useEffect(() => {
    let isActive = true

    async function load() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const response = await fetchBlockersSummary()
        if (isActive) {
          setItems(response)
        }
      } catch (error) {
        if (!isActive) {
          return
        }
        if (error instanceof BlockersSummaryError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('The governed blockers-summary seam could not be reached from the browser shell.')
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

  const totalBlockedItems = items.reduce((sum, item) => sum + item.blocked_count, 0)
  const totalBlockedHours = items.reduce((sum, item) => sum + item.blocked_hours, 0)
  const rowsWithNotes = items.filter((item) => typeof item.sample_notes === 'string' && item.sample_notes.trim().length > 0).length

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Adjacent Operations Visibility Consumer</p>
          <h2>Read blocker aggregation through the governed ops API.</h2>
        </div>
        <p className="resource-lane-copy">
          This panel consumes `v_blockers_summary` through a read-only backend route so blocker visibility stays
          inside the governed browser boundary.
        </p>
      </div>

      {isLoading ? <p className="resource-banner resource-banner-neutral">Loading the governed blocker summary…</p> : null}
      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!isLoading && !errorMessage ? (
        <div className="resource-results">
          <div className="resource-summary">
            <div>
              <span className="resource-summary-label">Blocker rows loaded</span>
              <strong>{items.length}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Blocked items</span>
              <strong>{totalBlockedItems}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Blocked hours</span>
              <strong>{totalBlockedHours.toFixed(1)}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Rows with notes</span>
              <strong>{rowsWithNotes}</strong>
            </div>
          </div>

          <div className="resource-grid">
            {items.map((item) => (
              <article
                className="resource-item"
                key={`${item.project_number ?? 'unknown-project'}-${item.apparatus_type ?? 'unknown-type'}-${item.availability ?? 'unknown-availability'}`}
              >
                <div className="resource-item-row">
                  <span className="resource-chip">{item.availability ?? 'Unknown status'}</span>
                  <span className="resource-chip resource-chip-muted">{item.blocked_hours.toFixed(1)} blocked hours</span>
                </div>
                <h3>{item.apparatus_type ?? 'Unknown apparatus type'}</h3>
                <p>
                  {[item.project_number, item.project_name]
                    .filter((value) => typeof value === 'string' && value.trim().length > 0)
                    .join(' · ') || 'No project metadata is available for this blocker row yet.'}
                </p>
                <dl>
                  <div>
                    <dt>Blocked count</dt>
                    <dd>{item.blocked_count}</dd>
                  </div>
                  <div>
                    <dt>Blocked hours</dt>
                    <dd>{item.blocked_hours.toFixed(1)}</dd>
                  </div>
                  <div>
                    <dt>Availability</dt>
                    <dd>{item.availability ?? 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt>Sample notes</dt>
                    <dd>{item.sample_notes ?? 'No notes captured in current rows.'}</dd>
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