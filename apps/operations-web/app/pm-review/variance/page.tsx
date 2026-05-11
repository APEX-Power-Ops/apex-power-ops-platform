'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { buildPmReturnContext, buildPmRoute } from '../route-navigation'

declare global {
  interface Window {
    ApexVariance?: {
      VarianceReviewView?: React.ComponentType<any>
    }
    React?: typeof React
  }
}

const VARIANCE_SCRIPT_ID = 'apex-pm-variance-script'
const VARIANCE_SCRIPT_SRC = '/pm-review/variance.js'

function loadVarianceScript(): Promise<void> {
  if (window.ApexVariance?.VarianceReviewView) {
    return Promise.resolve()
  }

  const existing = document.getElementById(VARIANCE_SCRIPT_ID) as HTMLScriptElement | null
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('APEX variance script failed to load')), { once: true })
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = VARIANCE_SCRIPT_ID
    script.src = VARIANCE_SCRIPT_SRC
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('APEX variance script failed to load'))
    document.body.appendChild(script)
  })
}

export default function PmVariancePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [varianceView, setVarianceView] = React.useState<React.ComponentType<any> | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const focusTaskId = searchParams.get('focusTaskId')
  const projectId = searchParams.get('projectId') || 'stack-dc'
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'

  const handleTraceTask = React.useCallback(
    (taskInfo: { taskId?: string; taskLabel?: string }) => {
      router.push(
        buildPmRoute('/pm-review/tracer', {
          taskId: taskInfo?.taskId,
          taskLabel: taskInfo?.taskLabel,
          maxDepth: 10,
          ...buildPmReturnContext('/pm-review/variance', { focusTaskId, projectId }, 'PM variance route'),
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
          ...buildPmReturnContext('/pm-review/variance', { focusTaskId, projectId }, 'PM variance route'),
        }),
      )
    },
    [focusTaskId, projectId, router],
  )

  const handleViewDrivers = React.useCallback(
    (taskId: string | null) => {
      router.push(
        buildPmRoute('/pm-review', {
          focusTaskId: taskId,
          ...buildPmReturnContext('/pm-review/variance', { focusTaskId, projectId }, 'PM variance route'),
        }),
      )
    },
    [focusTaskId, projectId, router],
  )

  React.useEffect(() => {
    document.title = 'APEX PM Variance Route'

    let cancelled = false

    window.React = React

    loadVarianceScript()
      .then(() => {
        if (cancelled) {
          return
        }

        const component = window.ApexVariance?.VarianceReviewView
        if (!component) {
          setError('The PM variance surface loaded without exporting VarianceReviewView.')
          return
        }

        setVarianceView(() => component)
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
            <h1>PM variance now has a real app route.</h1>
            <p className="lede">
              This promotes the schedule-variance slice into the governed Next.js shell while preserving the bounded
              variance read seam and the legacy static page for compare-proof continuity.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/variance</dd>
            </div>
            <div>
              <dt>Legacy compare host</dt>
              <dd>
                <Link href="/pm-review/variance.html">/pm-review/variance.html</Link>
              </dd>
            </div>
            <div>
              <dt>Backend seam</dt>
              <dd>/api/v1/schedule/variance</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Schedule Variance Review</h2>
            <p>
              The promoted route mounts the same browser-reviewed PM variance component from the active lane artifact,
              but now from the governed app shell instead of a static HTML launcher.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            {returnTo && <Link href={returnTo}>Return to {returnLabel}</Link>}
            <Link href="/pm-review">Open promoted drivers route</Link>
            <Link href="/pm-review/schedule">Open promoted schedule route</Link>
            <Link href="/pm-review/variance.html">Open legacy static page</Link>
          </p>
        </div>

        {error ? (
          <div className="card pm-runtime-state pm-runtime-error">
            <h3>Variance route failed to load</h3>
            <p>{error}</p>
          </div>
        ) : varianceView ? (
          React.createElement(varianceView, {
            projectId,
            onTraceTask: handleTraceTask,
            onViewSchedule: handleViewSchedule,
            onViewDrivers: handleViewDrivers,
            focusTaskId,
          })
        ) : (
          <div className="card pm-runtime-state">
            <h3>Loading PM variance surface</h3>
            <p>Bootstrapping the promoted variance review component from the governed browser shell.</p>
          </div>
        )}
      </section>
    </main>
  )
}