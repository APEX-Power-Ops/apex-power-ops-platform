'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { buildPmReturnContext, buildPmRoute } from './route-navigation'

declare global {
  interface Window {
    ApexDrivers?: {
      DriversReviewView?: React.ComponentType<any>
    }
    React?: typeof React
  }
}

const DRIVERS_SCRIPT_ID = 'apex-pm-drivers-script'
const DRIVERS_SCRIPT_SRC = '/pm-review/drivers.js'

function loadDriversScript(): Promise<void> {
  if (window.ApexDrivers?.DriversReviewView) {
    return Promise.resolve()
  }

  const existing = document.getElementById(DRIVERS_SCRIPT_ID) as HTMLScriptElement | null
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('APEX drivers script failed to load')), { once: true })
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = DRIVERS_SCRIPT_ID
    script.src = DRIVERS_SCRIPT_SRC
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('APEX drivers script failed to load'))
    document.body.appendChild(script)
  })
}

export default function PmDriversPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [driversView, setDriversView] = React.useState<React.ComponentType<any> | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const focusTaskId = searchParams.get('focusTaskId')
  const projectId = searchParams.get('projectId')
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'

  const handleTraceTask = React.useCallback(
    (taskInfo: { taskId?: string; taskLabel?: string }) => {
      router.push(
        buildPmRoute('/pm-review/tracer', {
          taskId: taskInfo?.taskId,
          taskLabel: taskInfo?.taskLabel,
          maxDepth: 10,
          ...buildPmReturnContext('/pm-review', { focusTaskId, projectId }, 'PM drivers route'),
        }),
      )
    },
    [focusTaskId, projectId, router],
  )

  const handleViewVariance = React.useCallback(
    (taskId: string | null) => {
      router.push(
        buildPmRoute('/pm-review/variance', {
          projectId: 'stack-dc',
          focusTaskId: taskId,
          ...buildPmReturnContext('/pm-review', { focusTaskId, projectId }, 'PM drivers route'),
        }),
      )
    },
    [focusTaskId, projectId, router],
  )

  const handleViewSchedule = React.useCallback(
    (taskId: string | null) => {
      router.push(
        buildPmRoute('/pm-review/schedule', {
          focusTaskId: taskId,
          ...buildPmReturnContext('/pm-review', { focusTaskId, projectId }, 'PM drivers route'),
        }),
      )
    },
    [focusTaskId, projectId, router],
  )

  React.useEffect(() => {
    document.title = 'APEX PM Drivers Route'

    let cancelled = false

    window.React = React

    loadDriversScript()
      .then(() => {
        if (cancelled) {
          return
        }

        const component = window.ApexDrivers?.DriversReviewView
        if (!component) {
          setError('The PM drivers surface loaded without exporting DriversReviewView.')
          return
        }

        setDriversView(() => component)
      })
      .catch((loadError) => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : String(loadError))
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Review Promotion</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>PM drivers now have a real app route.</h1>
            <p className="lede">
              This promotes the first PM review slice into the governed Next.js shell while preserving the existing
              read-only schedule seam and the legacy static host for compare-proof continuity.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review</dd>
            </div>
            <div>
              <dt>Legacy compare host</dt>
              <dd>
                <Link href="/pm-review/index.html">/pm-review/index.html</Link>
              </dd>
            </div>
            <div>
              <dt>Backend seam</dt>
              <dd>/api/v1/schedule/drivers</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Critical-Path Drivers</h2>
            <p>
              The promoted route mounts the same browser-reviewed PM drivers component from the active lane artifact,
              but now from the governed app shell instead of a static HTML launcher.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/workfront">Open PM workfront</Link>
            <Link href="/pm-review/import-intake">Project Miner intake</Link>
            <Link href="/pm-review/field-authorization-placeholder">Field authorization placeholder</Link>
            <Link href="/pm-review/schedule-status-placeholder">Schedule status placeholder</Link>
            <Link href="/pm-review/durable-field-record-placeholder">Durable field record placeholder</Link>
            <Link href="/pm-review/production-tracking-placeholder">Production tracking placeholder</Link>
            <Link href="/pm-review/customer-reporting-placeholder">Customer reporting placeholder</Link>
            <Link href="/pm-review/financial-handoff-placeholder">Financial handoff placeholder</Link>
            <Link href="/pm-review/customer-delivery-execution">Customer delivery execution</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder</Link>
            <Link href="/pm-review/customer-billing-placeholder">Customer billing placeholder</Link>
            <Link href="/pm-review/source-writeback-placeholder">Source writeback placeholder</Link>
            {returnTo && <Link href={returnTo}>Return to {returnLabel}</Link>}
            <Link href="/pm-review/index.html">Open legacy static page</Link>
          </p>
        </div>

        {error ? (
          <div className="card pm-runtime-state pm-runtime-error">
            <h3>Drivers route failed to load</h3>
            <p>{error}</p>
          </div>
        ) : driversView ? (
          React.createElement(driversView, {
            projectId,
            onTraceTask: handleTraceTask,
            onViewVariance: handleViewVariance,
            onViewSchedule: handleViewSchedule,
            focusTaskId,
          })
        ) : (
          <div className="card pm-runtime-state">
            <h3>Loading PM drivers surface</h3>
            <p>Bootstrapping the promoted drivers review component from the governed browser shell.</p>
          </div>
        )}
      </section>
    </main>
  )
}
