import { browserEnv, hasSupabaseBrowserConfig } from '../lib/browser-env'
import { ApparatusResourceExplorer } from './apparatus-resource-explorer'

const shellChecks = [
  {
    label: 'Package boundary',
    status: 'landed',
    detail: 'A real Next.js app package now exists under apps/operations-web.',
  },
  {
    label: 'Browser env contract',
    status: hasSupabaseBrowserConfig ? 'configured' : 'awaiting values',
    detail: hasSupabaseBrowserConfig
      ? 'Public browser config values are present.'
      : 'NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY still need local values.',
  },
  {
    label: 'Data boundary',
    status: 'backend-routed',
    detail: 'The first live read now flows through a governed control-plane route rather than direct browser database admission.',
  },
]

const nextMoves = [
  'Use bounded backend seams for additional live reads instead of widening direct browser database authority.',
  'Exercise the new apparatus study-resource route against a migrated host surface when runtime proof is needed.',
  'Keep the legacy Supabase browser client deferred until a separate client-shape admission decision lands.',
]

export default function HomePage() {
  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Governed Browser Shell</p>
        <div className="hero-grid">
          <div>
            <h1>Operations Web now has a real frontend boundary.</h1>
            <p className="lede">
              This shell intentionally stops before live data wiring. The goal of this packet is boundary creation,
              not accidental client admission.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Target app</dt>
              <dd>apps/operations-web</dd>
            </div>
            <div>
              <dt>Public API base</dt>
              <dd>{browserEnv.controlPlaneBaseUrl}</dd>
            </div>
            <div>
              <dt>Supabase browser values</dt>
              <dd>{hasSupabaseBrowserConfig ? 'Configured locally' : 'Awaiting local values'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="status-grid">
        {shellChecks.map((item) => (
          <article key={item.label} className="status-card">
            <div className="status-row">
              <h2>{item.label}</h2>
              <span className={`status-pill status-${item.status.replace(/\s+/g, '-')}`}>{item.status}</span>
            </div>
            <p>{item.detail}</p>
          </article>
        ))}
      </section>

      <section className="notes-grid">
        <article className="notes-card">
          <h2>What This Shell Does</h2>
          <ul>
            <li>Creates a governed frontend package and source tree.</li>
            <li>Establishes the first browser-side environment contract.</li>
            <li>Consumes the first live study-resource read through the governed control-plane API.</li>
            <li>Hosts the preserved cross-surface validation dashboard at /integration-dashboard/index.html.</li>
            <li>Hosts the re-homed lead operations prototype at /lead-ops/index.html.</li>
            <li>Hosts the first re-homed PM read-only review slice at /pm-review/index.html.</li>
            <li>Hosts the re-homed PM approval prototype shell at /pm-review/approval-surface.html.</li>
            <li>Hosts the re-homed PM schedule slice at /pm-review/schedule.html.</li>
            <li>Hosts the re-homed PM upstream tracer slice at /pm-review/tracer.html.</li>
            <li>Hosts the re-homed PM variance slice at /pm-review/variance.html.</li>
          </ul>
        </article>
        <article className="notes-card accent-card">
          <h2>Next Safe Moves</h2>
          <ol>
            {nextMoves.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </article>
      </section>

      <section className="notes-card">
        <h2>Validation Surface</h2>
        <p>
          The browser-side cross-surface dashboard has been re-homed into the active operator shell and remains available at{' '}
          <a href="/integration-dashboard/index.html">/integration-dashboard/index.html</a>.
        </p>
        <p>
          The lead operations prototype is available in the active lane at <a href="/lead-ops/index.html">/lead-ops/index.html</a>.
        </p>
        <p>
          The first PM drivers review slice is also available in the active lane at <a href="/pm-review/index.html">/pm-review/index.html</a>.
        </p>
        <p>
          The PM approval prototype shell is available at <a href="/pm-review/approval-surface.html">/pm-review/approval-surface.html</a>.
        </p>
        <p>
          The PM schedule slice is available at <a href="/pm-review/schedule.html">/pm-review/schedule.html</a>.
        </p>
        <p>
          The PM upstream tracer slice is available at <a href="/pm-review/tracer.html">/pm-review/tracer.html</a>.
        </p>
        <p>
          The PM variance slice is available at <a href="/pm-review/variance.html">/pm-review/variance.html</a>.
        </p>
      </section>

      <ApparatusResourceExplorer />
    </main>
  )
}