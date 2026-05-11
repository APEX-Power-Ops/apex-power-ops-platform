'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

import { buildPmReturnContext, buildPmRoute, parsePmRoute } from '../route-navigation'

declare global {
  interface Window {
    ApexTracer?: {
      TracerReviewView?: React.ComponentType<any>
    }
    React?: typeof React
  }
}

const TRACER_SCRIPT_ID = 'apex-pm-tracer-script'
const TRACER_SCRIPT_SRC = '/pm-review/tracer.js'

function loadTracerScript(): Promise<void> {
  if (window.ApexTracer?.TracerReviewView) {
    return Promise.resolve()
  }

  const existing = document.getElementById(TRACER_SCRIPT_ID) as HTMLScriptElement | null
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('APEX tracer script failed to load')), { once: true })
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = TRACER_SCRIPT_ID
    script.src = TRACER_SCRIPT_SRC
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('APEX tracer script failed to load'))
    document.body.appendChild(script)
  })
}

export default function PmTracerPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [tracerView, setTracerView] = React.useState<React.ComponentType<any> | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const returnTo = searchParams.get('returnTo')
  const returnLabel = searchParams.get('returnLabel') || 'previous PM view'
  const parsedMaxDepth = Number(searchParams.get('maxDepth') || '10')
  const maxDepth = Number.isFinite(parsedMaxDepth) && parsedMaxDepth > 0 ? parsedMaxDepth : 10
  const derivedReturnRoute = React.useMemo(() => parsePmRoute(returnTo), [returnTo])
  const derivedSeedTaskId = React.useMemo(() => {
    if (!derivedReturnRoute) {
      return null
    }

    switch (derivedReturnRoute.pathname) {
      case '/pm-review':
      case '/pm-review/schedule':
      case '/pm-review/variance':
        return derivedReturnRoute.searchParams.get('focusTaskId')
      case '/pm-review/approval':
        return derivedReturnRoute.searchParams.get('focusTaskId') || derivedReturnRoute.searchParams.get('taskId')
      default:
        return null
    }
  }, [derivedReturnRoute])
  const derivedSeedTaskLabel = React.useMemo(() => {
    if (!derivedReturnRoute || !derivedSeedTaskId) {
      return null
    }

    if (derivedReturnRoute.pathname === '/pm-review/approval') {
      return derivedReturnRoute.searchParams.get('taskLabel') || `Focused task ${derivedSeedTaskId}`
    }

    return `Focused task ${derivedSeedTaskId}`
  }, [derivedReturnRoute, derivedSeedTaskId])
  const seedTaskId = searchParams.get('taskId') || derivedSeedTaskId || 'stack-dc-task-001'
  const seedTaskLabel =
    searchParams.get('taskLabel') ||
    derivedSeedTaskLabel ||
    'Seed task'

  const handleTraceTask = React.useCallback(
    (taskInfo: { taskId?: string; taskLabel?: string }) => {
      router.push(
        buildPmRoute('/pm-review/tracer', {
          taskId: taskInfo?.taskId,
          taskLabel: taskInfo?.taskLabel,
          maxDepth,
          ...buildPmReturnContext('/pm-review/tracer', { taskId: seedTaskId, taskLabel: seedTaskLabel, maxDepth }, 'PM tracer route'),
        }),
      )
    },
    [maxDepth, router, seedTaskId, seedTaskLabel],
  )

  React.useEffect(() => {
    document.title = 'APEX PM Tracer Route'

    let cancelled = false

    window.React = React

    loadTracerScript()
      .then(() => {
        if (cancelled) {
          return
        }

        const component = window.ApexTracer?.TracerReviewView
        if (!component) {
          setError('The PM tracer surface loaded without exporting TracerReviewView.')
          return
        }

        setTracerView(() => component)
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
            <h1>PM tracer now has a real app route.</h1>
            <p className="lede">
              This promotes the upstream constraint tracer into the governed Next.js shell while preserving the bounded
              tracer read seam and the legacy static page for compare-proof continuity.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/tracer</dd>
            </div>
            <div>
              <dt>Legacy compare host</dt>
              <dd>
                <Link href="/pm-review/tracer.html">/pm-review/tracer.html</Link>
              </dd>
            </div>
            <div>
              <dt>Backend seam</dt>
              <dd>/api/v1/schedule/tracer</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Upstream Constraint Tracer</h2>
            <p>
              The promoted route mounts the same browser-reviewed PM tracer component from the active lane artifact,
              but now from the governed app shell instead of a static HTML launcher.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/">Return to shell</Link>
            {returnTo && <Link href={returnTo}>Return to {returnLabel}</Link>}
            <Link href="/pm-review">Open promoted drivers route</Link>
            <Link href="/pm-review/schedule">Open promoted schedule route</Link>
            <Link href="/pm-review/tracer.html">Open legacy static page</Link>
          </p>
        </div>

        {!error && tracerView && (
          <div className="card pm-runtime-state">
            <h3>Seeded trace</h3>
            <p>
              Current seed: {seedTaskLabel} ({seedTaskId})
            </p>
          </div>
        )}

        {error ? (
          <div className="card pm-runtime-state pm-runtime-error">
            <h3>Tracer route failed to load</h3>
            <p>{error}</p>
          </div>
        ) : tracerView ? (
          React.createElement(tracerView, {
            taskId: seedTaskId,
            taskLabel: seedTaskLabel,
            maxDepth,
            onTraceTask: handleTraceTask,
          })
        ) : (
          <div className="card pm-runtime-state">
            <h3>Loading PM tracer surface</h3>
            <p>Bootstrapping the promoted tracer review component from the governed browser shell.</p>
          </div>
        )}
      </section>
    </main>
  )
}