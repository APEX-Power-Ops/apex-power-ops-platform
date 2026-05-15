import { browserEnv, hasSupabaseBrowserConfig } from '../lib/browser-env'
import { ApparatusResourceExplorer } from './apparatus-resource-explorer'
import { ApparatusByCategoryExplorer } from './apparatus-by-category-explorer'
import { BlockersSummaryExplorer } from './blockers-summary-explorer'
import { MasterOperationsExplorer } from './master-operations-explorer'
import { ProjectApparatusSummaryExplorer } from './project-apparatus-summary-explorer'
import { RelayResourceExplorer } from './relay-resource-explorer'
import { ScheduleHealthExplorer } from './schedule-health-explorer'

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
  {
    label: 'Relay browser slice',
    status: 'backend-routed',
    detail: 'Relay browse and preview now stay inside the browser shell by consuming the mounted read-only relay API.',
  },
  {
    label: 'Operations visibility seam',
    status: 'backend-routed',
    detail: 'The first Operations Visibility rollup now flows through /api/v1/ops/master-operations instead of direct browser database admission.',
  },
  {
    label: 'Schedule health seam',
    status: 'backend-routed',
    detail: 'The second governed Operations Visibility seam now reads /api/v1/ops/schedule-health for scope-level risk visibility.',
  },
  {
    label: 'Scope KPI seam',
    status: 'backend-routed',
    detail: 'The third governed Operations Visibility seam now reads /api/v1/ops/project-apparatus-summary for scope-level KPI rollups.',
  },
  {
    label: 'Category seam',
    status: 'backend-routed',
    detail: 'The fourth governed Operations Visibility seam now reads /api/v1/ops/apparatus-by-category for grouped apparatus rollups.',
  },
  {
    label: 'Blockers seam',
    status: 'backend-routed',
    detail: 'The fifth governed Operations Visibility seam now reads /api/v1/ops/blockers-summary for blocker aggregation.',
  },
]

const nextMoves = [
  'Now that promoted PM routes preserve return-path context and tracer can infer seeds from governed origins, stand up the bounded seam services and validate that those handoffs carry real schedule and approval data instead of shell-derived fallbacks.',
  'Use bounded backend seams for additional live reads instead of widening direct browser database authority.',
  'Treat /api/v1/ops/master-operations as the first governed dashboard rollup seam for the newly live 09 schema tranche.',
  'Treat /api/v1/ops/schedule-health as the adjacent scope-level risk seam for the same governed operations lane.',
  'Treat /api/v1/ops/project-apparatus-summary as the adjacent scope KPI seam before widening into grouped category or blocker views.',
  'Treat /api/v1/ops/apparatus-by-category as the grouped category seam before widening into blocker-note aggregation.',
  'Treat /api/v1/ops/blockers-summary as the final populated blocker aggregation seam before considering empty live views.',
  'Exercise the new apparatus study-resource route against a migrated host surface when runtime proof is needed.',
  'Keep relay preview source-faithful by surfacing storage-kind identity and unsupported warnings rather than simplifying them away.',
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

      <section className="status-grid status-grid-wide">
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
            <li>Consumes the first Operations Visibility dashboard rollup through the governed ops API.</li>
            <li>Consumes the adjacent Operations Visibility schedule-health rollup through the same governed ops API boundary.</li>
            <li>Consumes the adjacent Operations Visibility scope KPI rollup through the same governed ops API boundary.</li>
            <li>Consumes the adjacent Operations Visibility category rollup through the same governed ops API boundary.</li>
            <li>Consumes the adjacent Operations Visibility blocker aggregation through the same governed ops API boundary.</li>
            <li>Consumes the bounded relay discovery, context, settings, and preview seam through the same governed API boundary.</li>
            <li>Hosts the preserved cross-surface validation dashboard at /integration-dashboard/index.html.</li>
            <li>Hosts the re-homed lead operations prototype at /lead-ops/index.html.</li>
            <li>Hosts the promoted lead assignment app route at /lead-ops.</li>
            <li>Hosts the promoted field technician app route at /field-tech.</li>
            <li>Hosts the promoted PM drivers app route at /pm-review.</li>
            <li>Hosts the read-only PM workfront app route at /pm-review/workfront.</li>
            <li>Hosts the promoted PM approval app route at /pm-review/approval.</li>
            <li>Hosts the promoted PM schedule app route at /pm-review/schedule.</li>
            <li>Hosts the promoted PM tracer app route at /pm-review/tracer.</li>
            <li>Hosts the promoted PM variance app route at /pm-review/variance.</li>
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
          The promoted lead assignment route is available in the governed shell at <a href="/lead-ops">/lead-ops</a>.
        </p>
        <p>
          The promoted field technician route is available in the governed shell at <a href="/field-tech">/field-tech</a>.
        </p>
        <p>
          The promoted PM drivers route is available in the governed shell at <a href="/pm-review">/pm-review</a>.
        </p>
        <p>
          The read-only PM workfront route is available in the governed shell at <a href="/pm-review/workfront">/pm-review/workfront</a>.
        </p>
        <p>
          The promoted PM approval route is available in the governed shell at <a href="/pm-review/approval">/pm-review/approval</a>.
        </p>
        <p>
          The promoted PM schedule route is available in the governed shell at <a href="/pm-review/schedule">/pm-review/schedule</a>.
        </p>
        <p>
          The promoted PM tracer route is available in the governed shell at <a href="/pm-review/tracer">/pm-review/tracer</a>.
        </p>
        <p>
          The promoted PM variance route is available in the governed shell at <a href="/pm-review/variance">/pm-review/variance</a>.
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

      <MasterOperationsExplorer />
      <ScheduleHealthExplorer />
      <ProjectApparatusSummaryExplorer />
      <ApparatusByCategoryExplorer />
      <BlockersSummaryExplorer />
      <ApparatusResourceExplorer />
      <RelayResourceExplorer />
    </main>
  )
}
