'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { buildPmReturnContext, buildPmRoute } from '../route-navigation'

declare global {
  interface Window {
    ApexSchedule?: {
      ScheduleView?: React.ComponentType<any>
    }
    React?: typeof React
  }
}

const SCHEDULE_SCRIPT_ID = 'apex-pm-schedule-script'
const SCHEDULE_SCRIPT_SRC = '/pm-review/schedule.js'

function loadScheduleScript(): Promise<void> {
  if (window.ApexSchedule?.ScheduleView) {
    return Promise.resolve()
  }

  const existing = document.getElementById(SCHEDULE_SCRIPT_ID) as HTMLScriptElement | null
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('APEX schedule script failed to load')), { once: true })
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = SCHEDULE_SCRIPT_ID
    script.src = SCHEDULE_SCRIPT_SRC
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('APEX schedule script failed to load'))
    document.body.appendChild(script)
  })
}

export default function PmSchedulePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [scheduleView, setScheduleView] = React.useState<React.ComponentType<any> | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const focusTaskId = searchParams.get('focusTaskId')
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'

  const handleTraceTask = React.useCallback(
    (taskInfo: { taskId?: string; taskLabel?: string }) => {
      router.push(
        buildPmRoute('/pm-review/tracer', {
          taskId: taskInfo?.taskId,
          taskLabel: taskInfo?.taskLabel,
          maxDepth: 10,
          ...buildPmReturnContext('/pm-review/schedule', { focusTaskId }, 'PM schedule route'),
        }),
      )
    },
    [focusTaskId, router],
  )

  const handleViewVariance = React.useCallback(
    (taskId: string | null) => {
      router.push(
        buildPmRoute('/pm-review/variance', {
          projectId: 'stack-dc',
          focusTaskId: taskId,
          ...buildPmReturnContext('/pm-review/schedule', { focusTaskId }, 'PM schedule route'),
        }),
      )
    },
    [focusTaskId, router],
  )

  const handleViewDrivers = React.useCallback(
    (taskId: string | null) => {
      router.push(
        buildPmRoute('/pm-review', {
          focusTaskId: taskId,
          ...buildPmReturnContext('/pm-review/schedule', { focusTaskId }, 'PM schedule route'),
        }),
      )
    },
    [focusTaskId, router],
  )

  React.useEffect(() => {
    document.title = 'APEX PM Schedule Route'

    let cancelled = false

    window.React = React

    loadScheduleScript()
      .then(() => {
        if (cancelled) {
          return
        }

        const component = window.ApexSchedule?.ScheduleView
        if (!component) {
          setError('The PM schedule surface loaded without exporting ScheduleView.')
          return
        }

        setScheduleView(() => component)
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
            <h1>PM schedule now has a real app route.</h1>
            <p className="lede">
              This promotes the PM schedule slice into the governed Next.js shell while preserving the existing
              bounded schedule read seam and the legacy static page for compare-proof continuity.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/schedule</dd>
            </div>
            <div>
              <dt>Legacy compare host</dt>
              <dd>
                <Link href="/pm-review/schedule.html">/pm-review/schedule.html</Link>
              </dd>
            </div>
            <div>
              <dt>Backend seam</dt>
              <dd>/api/v1/schedule/*</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Project Schedule Review</h2>
            <p>
              The promoted route mounts the same browser-reviewed PM schedule component from the active lane artifact,
              but now from the governed app shell instead of a static HTML launcher.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            {returnTo && <Link href={returnTo}>Return to {returnLabel}</Link>}
            <Link href="/pm-review">Open promoted drivers route</Link>
            <Link href="/pm-review/approval">Open promoted approval route</Link>
            <Link href="/pm-review/schedule.html">Open legacy static page</Link>
          </p>
        </div>

        {error ? (
          <div className="card pm-runtime-state pm-runtime-error">
            <h3>Schedule route failed to load</h3>
            <p>{error}</p>
          </div>
        ) : scheduleView ? (
          React.createElement(scheduleView, {
            onTraceTask: handleTraceTask,
            onViewVariance: handleViewVariance,
            onViewDrivers: handleViewDrivers,
            focusTaskId,
          })
        ) : (
          <div className="card pm-runtime-state">
            <h3>Loading PM schedule surface</h3>
            <p>Bootstrapping the promoted schedule review component from the governed browser shell.</p>
          </div>
        )}
      </section>
    </main>
  )
}