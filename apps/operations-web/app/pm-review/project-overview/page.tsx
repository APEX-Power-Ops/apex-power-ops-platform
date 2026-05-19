'use client'

import * as React from 'react'
import Link from 'next/link'

type CandidateSummary = {
  workpackage_count?: number
  task_count?: number
  apparatus_candidate_count?: number
  warning_count?: number
  blocker_count?: number
  human_decision_count?: number
}

type CandidateProject = {
  name?: string | null
  location?: string | null
  drawing_package?: string | null
  source_sheet?: string | null
}

type CandidatePayload = {
  candidate_id?: string
  mutation_authority?: string
  project?: CandidateProject
  summary?: CandidateSummary
  source_freshness?: {
    aggregate_fingerprint?: string
    missing_count?: number
  }
  review_guidance?: {
    primary_review_goal?: string
    allowed_now?: string[]
    not_allowed_now?: string[]
  }
}

type AdmissionPlan = {
  readiness_status?: string
  mutation_authority?: string
  no_go_checks?: Array<{
    status?: string
  }>
}

type ApprovalContract = {
  persistence_authority?: string
  mutation_authority?: string
}

type ApprovalStoragePlan = {
  persistence_authority?: string
  recommended_table?: string
  recommended_route?: string
}

type ApprovalPersistenceStatus = {
  approval_record_count_for_candidate?: number
  import_authority?: string
}

type TaskPlanStatus = {
  classification?: string
  route?: string
  task_plan_route?: string
  task_plan_authority?: string
  current_candidate_match?: boolean
  planning_context_only?: boolean
  persisted_row_counts?: {
    projects?: number
    workpackages?: number
    tasks?: number
    apparatus?: number
  }
}

type WorkfrontSummary = {
  total_count?: number
  blocked_count?: number
  unassigned_count?: number
  ready_count?: number
  in_progress_count?: number
  pm_review_count?: number
}

type WorkfrontPayload = {
  summary?: WorkfrontSummary
  advisory?: {
    recommended_focus?: string
    ai_mutation_authority?: string
  }
}

type DeliveryStatusReadback = {
  status?: string
  latest_customer_delivery_event_id?: string | null
  latest_delivered_at_utc?: string | null
  finance_authority?: string
  source_writeback_authority?: string
  customer_billing_delivery_authority?: string
}

type ProjectOverviewPacket = {
  candidate: CandidatePayload
  admissionPlan: AdmissionPlan
  approvalContract: ApprovalContract
  storagePlan: ApprovalStoragePlan
  approvalStatus: ApprovalPersistenceStatus
  taskPlanStatus: TaskPlanStatus
  workfront: WorkfrontPayload
  deliveryStatus: DeliveryStatusReadback
}

type StageTone = 'ready' | 'active' | 'attention' | 'blocked'

type StageCard = {
  id: string
  step: string
  title: string
  tone: StageTone
  summary: string
  decision: string
  when: string
  availableNow: string[]
  routeHref: string
  routeLabel: string
}

type AttentionItem = {
  id: string
  title: string
  detail: string
}

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const READS_BASE = `${API_BASE}/reads`
const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] }

function makeToken() {
  return `Bearer ${btoa(JSON.stringify(PM_ACTOR))}`
}

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${READS_BASE}/${path}`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error(`Failed to read ${path}`)
  }

  return (await response.json()) as T
}

async function readProjectOverview(): Promise<ProjectOverviewPacket> {
  const [candidate, admissionPlan, approvalContract, storagePlan, approvalStatus, taskPlanStatus, workfront, deliveryStatus] = await Promise.all([
    readJson<CandidatePayload>('project-import-candidate'),
    readJson<AdmissionPlan>('project-import-admission-plan'),
    readJson<ApprovalContract>('project-import-approval-contract'),
    readJson<ApprovalStoragePlan>('project-import-approval-storage-plan'),
    readJson<ApprovalPersistenceStatus>('project-import-approval-status'),
    readJson<TaskPlanStatus>('project-import-task-plan-status'),
    readJson<WorkfrontPayload>('pm-workfront'),
    readJson<DeliveryStatusReadback>('temp-power-customer-delivery-event-status'),
  ])

  return {
    candidate,
    admissionPlan,
    approvalContract,
    storagePlan,
    approvalStatus,
    taskPlanStatus,
    workfront,
    deliveryStatus,
  }
}

function formatLabel(value?: string | null) {
  return (value || 'unknown').replace(/[_-]/g, ' ')
}

function formatCount(value?: number | null) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString() : '0'
}

function formatTimestamp(value?: string | null) {
  if (!value) return 'not recorded yet'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

function toneClass(tone: StageTone) {
  switch (tone) {
    case 'ready':
      return 'status-configured'
    case 'active':
      return 'status-backend-routed'
    case 'attention':
      return 'status-awaiting-values'
    default:
      return 'status-deferred'
  }
}

function taskPlanCurrent(status?: TaskPlanStatus | null) {
  return status?.classification === 'task_plan_persisted' && status.current_candidate_match !== false
}

function taskPlanSummary(status?: TaskPlanStatus | null) {
  if (!status) {
    return 'Waiting for the current planning-only task baseline.'
  }

  if (taskPlanCurrent(status)) {
    return `${formatCount(status.persisted_row_counts?.tasks)} tasks and ${formatCount(status.persisted_row_counts?.apparatus)} apparatus rows are persisted as the current planning-only baseline.`
  }

  if (status.classification === 'task_plan_record_stale') {
    return 'The last planning-only task baseline no longer matches the current candidate and should be refreshed before it is treated as settled PM grouping context.'
  }

  return 'No planning-only task baseline has been persisted for the current candidate yet.'
}

function taskPlanToneClass(status?: TaskPlanStatus | null) {
  if (taskPlanCurrent(status)) {
    return 'status-configured'
  }

  if (status?.classification === 'task_plan_record_stale') {
    return 'status-awaiting-values'
  }

  return 'status-deferred'
}

function buildStageCards(packet: ProjectOverviewPacket): StageCard[] {
  const candidateSummary = packet.candidate.summary || {}
  const projectName = packet.candidate.project?.name || 'Current project candidate'
  const warningCount = candidateSummary.warning_count || 0
  const decisionCount = candidateSummary.human_decision_count || 0
  const workfrontSummary = packet.workfront.summary || {}
  const readyCount = workfrontSummary.ready_count || 0
  const blockedCount = workfrontSummary.blocked_count || 0
  const deliveryCurrent = packet.deliveryStatus.status === 'customer_delivery_event_recorded_current_match'
  const approvalBlocked = (packet.approvalContract.persistence_authority || 'not_admitted') === 'not_admitted'
  const taskPlanStatus = packet.taskPlanStatus
  const taskPlanCurrentMatch = taskPlanCurrent(taskPlanStatus)
  const taskPlanStageSummary = taskPlanCurrentMatch
    ? `The planning-only task baseline is current at ${formatCount(taskPlanStatus.persisted_row_counts?.tasks)} tasks and ${formatCount(taskPlanStatus.persisted_row_counts?.apparatus)} apparatus rows.`
    : taskPlanSummary(taskPlanStatus)

  return [
    {
      id: 'source-intake',
      step: '01',
      title: 'Source and candidate intake',
      tone: packet.candidate.candidate_id ? (warningCount || decisionCount ? 'attention' : 'ready') : 'blocked',
      summary: packet.candidate.candidate_id
        ? `${projectName} is loaded as ${packet.candidate.candidate_id} with ${formatCount(candidateSummary.workpackage_count)} workpackages, ${formatCount(candidateSummary.task_count)} tasks, and ${formatCount(candidateSummary.apparatus_candidate_count)} apparatus candidates.`
        : 'The overview is waiting for the current candidate read before source scope can be trusted.',
      decision: warningCount || decisionCount
        ? `Review ${formatCount(warningCount)} warnings and ${formatCount(decisionCount)} human decisions before treating the candidate as settled PM context.`
        : 'No source warning or decision queue is currently reported; confirm the candidate still reflects the intended testing package.',
      when: warningCount || decisionCount
        ? 'Before you rely on any downstream PM queue, field-prep, or customer delivery interpretation.'
        : 'At the start of the PM review cycle or any time the source fingerprint changes.',
      availableNow: [
        'Review source-derived project shape',
        'Inspect warnings and required PM decisions',
        'Check source fingerprint and traceability',
      ],
      routeHref: '/pm-review/import-candidate',
      routeLabel: 'Open import candidate review',
    },
    {
      id: 'approval-gate',
      step: '02',
      title: 'Task plan baseline and approval gate',
      tone: approvalBlocked ? 'blocked' : 'ready',
      summary: approvalBlocked
        ? `${taskPlanStageSummary} Approval persistence and project import are still intentionally blocked. The current surface is design and readiness review only.`
        : `${taskPlanStageSummary} Approval persistence has opened beyond the current default boundary.`,
      decision: 'Treat task-plan persistence as planning-only PM context. Review the future approval gate design, idempotency assumptions, and no-go checks without treating route presence as live approval authority.',
      when: 'Before any request to widen from read-only PM review into import or approval persistence authority.',
      availableNow: [
        taskPlanCurrentMatch
          ? 'Review the current planning-only task baseline'
          : 'Open import candidate review to persist or refresh the planning-only task baseline',
        'Review admission plan and no-go checks',
        'Review approval storage plan and contract shape',
        'Confirm zero approval rows remain the current truth',
      ],
      routeHref: '/pm-review/import-candidate',
      routeLabel: 'Open task shaping and candidate review',
    },
    {
      id: 'pm-workfront',
      step: '03',
      title: 'PM queue and execution visibility',
      tone: readyCount > 0 ? 'active' : blockedCount > 0 ? 'attention' : 'ready',
      summary: `${formatCount(workfrontSummary.total_count)} apparatus rows are on the PM queue, with ${formatCount(readyCount)} ready, ${formatCount(blockedCount)} blocked, and ${formatCount(workfrontSummary.unassigned_count)} unassigned.`,
      decision: readyCount > 0
        ? 'Work the ready queue first, then use drivers, schedule, tracer, and variance drillthroughs where timing or dependency questions exist.'
        : 'Refresh the PM queue and confirm whether the current project still has actionable apparatus rows.',
      when: readyCount > 0
        ? 'Now. This is the live execution surface that tells you what can move without opening a new governance branch.'
        : 'As soon as new ready work appears or blocked rows clear.',
      availableNow: [
        'Review the PM workfront queue',
        'Follow drillthroughs into drivers, schedule, tracer, and variance',
        'Identify owner gaps and blockers before field delay',
      ],
      routeHref: '/pm-review/workfront',
      routeLabel: 'Open PM workfront',
    },
    {
      id: 'field-prep',
      step: '04',
      title: 'Field prep and operational readiness',
      tone: readyCount > 0 ? 'attention' : 'blocked',
      summary: readyCount > 0
        ? 'Field-facing context is available as planning material, durable field record remains placeholder-only, and production tracking is now surfaced as the next separate no-live progress branch.'
        : 'Field prep remains conceptual until the queue shows concrete ready work and the next branch selection is explicit.',
      decision: 'Use field prep artifacts and questions to prepare conversations, keep durable field record as an upstream placeholder branch, and keep production tracking as placeholder planning only until a later packet admits live quantity, labor, and apparatus progress authority.',
      when: readyCount > 0
        ? 'As soon as PM-ready work needs customer, access, safety, or material clarification before field delay develops.'
        : 'After the PM queue shows concrete ready work worth preparing around.',
      availableNow: [
        'Prepare field kickoff and observation context',
        'Capture open access, safety, material, and customer questions',
        'Draft field-facing prep artifacts without creating work state',
        'Review the production tracking placeholder branch',
      ],
      routeHref: '/pm-review/production-tracking-placeholder',
      routeLabel: 'Open production tracking placeholder branch',
    },
    {
      id: 'customer-delivery',
      step: '05',
      title: 'Customer delivery execution',
      tone: deliveryCurrent ? 'ready' : 'attention',
      summary: deliveryCurrent
        ? `The admitted customer delivery branch is current. Latest event ${packet.deliveryStatus.latest_customer_delivery_event_id || 'unknown'} was recorded at ${formatTimestamp(packet.deliveryStatus.latest_delivered_at_utc)}.`
        : 'The customer delivery branch exists, but the current hosted readback is not reporting the current-match proof state.',
      decision: 'Use this route only for the bounded delivery-event persistence and readback proof already admitted. Do not widen into billing or finance from here.',
      when: deliveryCurrent
        ? 'When you need to verify or append bounded customer delivery proof without widening into downstream finance or billing branches.'
        : 'Only when delivery proof is the immediate operator need; otherwise keep attention on source and PM queue control.',
      availableNow: [
        'Review current customer delivery event readback',
        'Use the admitted bounded delivery execution route',
        'Confirm lineage remains current before any new delivery event request',
      ],
      routeHref: '/pm-review/customer-delivery-execution',
      routeLabel: 'Open customer delivery execution',
    },
    {
      id: 'downstream-outputs',
      step: '06',
      title: 'Downstream outputs and blocked branches',
      tone: 'blocked',
      summary: `Financial handoff is placeholder-only, finance remains placeholder-only, customer billing delivery remains ${formatLabel(packet.deliveryStatus.customer_billing_delivery_authority || 'not_admitted')}, and source writeback remains ${formatLabel(packet.deliveryStatus.source_writeback_authority || 'not_admitted')}.`,
      decision: 'Your next decision here is branch selection only: keep financial handoff as placeholder planning, or later open separate admitted packets for finance output, customer billing delivery, or source writeback.',
      when: 'Only after you intentionally choose a new governance packet for a downstream write branch.',
      availableNow: [
        'Review the financial handoff placeholder branch',
        'Review the customer reporting placeholder branch',
        'Review the finance placeholder branch',
        'Review the customer billing placeholder branch',
        'Review the source writeback placeholder branch',
        'See the canonical route-to-authority map',
        'Keep downstream write branches separate until explicitly admitted',
      ],
      routeHref: '/pm-review/financial-handoff-placeholder',
      routeLabel: 'Open financial handoff placeholder branch',
    },
  ]
}

function buildAttentionItems(packet: ProjectOverviewPacket): AttentionItem[] {
  const items: AttentionItem[] = []
  const decisionCount = packet.candidate.summary?.human_decision_count || 0
  const warningCount = packet.candidate.summary?.warning_count || 0
  const taskPlanStatus = packet.taskPlanStatus
  const readyCount = packet.workfront.summary?.ready_count || 0
  const blockedCount = packet.workfront.summary?.blocked_count || 0
  const deliveryCurrent = packet.deliveryStatus.status === 'customer_delivery_event_recorded_current_match'

  if (decisionCount || warningCount) {
    items.push({
      id: 'source-review',
      title: 'Clear the source review queue first',
      detail: `${formatCount(warningCount)} warnings and ${formatCount(decisionCount)} human decisions are still shaping the trusted PM starting point.`,
    })
  }

  if (!taskPlanCurrent(taskPlanStatus)) {
    items.push({
      id: 'task-plan-baseline',
      title: 'Refresh the durable task-plan baseline',
      detail:
        taskPlanStatus.classification === 'task_plan_record_stale'
          ? 'The last planning-only task baseline is stale against the current candidate and should be refreshed before grouped tasks are treated as settled PM context.'
          : 'No planning-only task baseline exists yet; persist it from import candidate review if the current grouping and designation plan is now the working baseline.',
    })
  }

  if (readyCount) {
    items.push({
      id: 'ready-queue',
      title: 'Work the ready PM queue now',
      detail: `${formatCount(readyCount)} apparatus rows are ready and can move without asking for a new governance branch.`,
    })
  }

  if (blockedCount) {
    items.push({
      id: 'blocked-queue',
      title: 'Resolve blocked PM rows before field delay',
      detail: `${formatCount(blockedCount)} rows are blocked and should drive your schedule, dependency, and escalation follow-up.`,
    })
  }

  if (!deliveryCurrent) {
    items.push({
      id: 'delivery-proof',
      title: 'Treat delivery execution as bounded proof only',
      detail: 'Customer delivery exists as an admitted slice, but the current readback is not yet the current-match proof state.',
    })
  }

  if (!items.length) {
    items.push({
      id: 'monitor',
      title: 'Monitor the current PM posture',
      detail: 'No immediate escalations are visible in the overview, so keep the route as your current-state scan before opening a detail surface.',
    })
  }

  return items.slice(0, 3)
}

export default function PmProjectOverviewPage() {
  const [packet, setPacket] = React.useState<ProjectOverviewPacket | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const refresh = React.useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const next = await readProjectOverview()
      setPacket(next)
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : String(refreshError))
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    document.title = 'APEX PM Project Overview'
    void refresh()
  }, [refresh])

  const stageCards = React.useMemo(() => (packet ? buildStageCards(packet) : []), [packet])
  const projectName = packet?.candidate.project?.name || 'Project Miner Temp Power'
  const location = packet?.candidate.project?.location || 'unknown location'
  const fingerprint = packet?.candidate.source_freshness?.aggregate_fingerprint || 'waiting for source fingerprint'
  const reviewGoal = packet?.candidate.review_guidance?.primary_review_goal || 'See the project from source intake through downstream blocked branches.'
  const attentionItems = React.useMemo(() => (packet ? buildAttentionItems(packet) : []), [packet])
  const drawingPackage = packet?.candidate.project?.drawing_package || 'waiting for drawing package'
  const sourceSheet = packet?.candidate.project?.source_sheet || 'waiting for source sheet'

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Project Overview</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>See the testing project top to bottom in one place.</h1>
            <p className="lede">
              This route turns the current PM lane into one visual project story: where the job stands, what is available
              now, what decisions are waiting on you, and which branches are intentionally blocked.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Project</dt>
              <dd>{loading ? 'Loading project overview' : `${projectName} · ${location}`}</dd>
            </div>
            <div>
              <dt>Current source fingerprint</dt>
              <dd>{loading ? 'Loading fingerprint' : fingerprint}</dd>
            </div>
            <div>
              <dt>PM focus</dt>
              <dd>{loading ? 'Loading PM focus' : reviewGoal}</dd>
            </div>
            <div>
              <dt>Drawing package</dt>
              <dd>{loading ? 'Loading drawing package' : drawingPackage}</dd>
            </div>
            <div>
              <dt>Source sheet</dt>
              <dd>{loading ? 'Loading source sheet' : sourceSheet}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>What You Can See And Do Today</h2>
            <p>
              Read this page from top to bottom. Each step shows current state, the decision you need to make, and the
              route to open when you want detail.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/import-candidate">Open import candidate</Link>
            <Link href="/pm-review/workfront">Open PM workfront</Link>
            <Link href="/pm-review/import-intake">Open intake workbench</Link>
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
            <button className="btn btn-outline" onClick={() => void refresh()} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </p>
        </div>

        {error ? (
          <div className="card pm-runtime-state pm-runtime-error">
            <h3>Overview route failed to load</h3>
            <p>{error}</p>
          </div>
        ) : null}

        <section className="status-grid status-grid-wide pm-project-overview-summary-grid">
          <article className="status-card">
            <div className="status-row">
              <h2>Candidate</h2>
              <span className={`status-pill ${packet?.candidate.candidate_id ? 'status-backend-routed' : 'status-deferred'}`}>
                {packet?.candidate.candidate_id ? 'loaded' : 'waiting'}
              </span>
            </div>
            <p>{packet?.candidate.candidate_id || 'Waiting for the current project candidate.'}</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h2>Decision queue</h2>
              <span className={`status-pill ${(packet?.candidate.summary?.human_decision_count || 0) > 0 ? 'status-awaiting-values' : 'status-configured'}`}>
                {formatCount(packet?.candidate.summary?.human_decision_count)} decisions
              </span>
            </div>
            <p>{formatCount(packet?.candidate.summary?.warning_count)} warnings and {formatCount(packet?.candidate.summary?.blocker_count)} blockers are currently reported.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h2>Task plan baseline</h2>
              <span className={`status-pill ${taskPlanToneClass(packet?.taskPlanStatus)}`}>
                {taskPlanCurrent(packet?.taskPlanStatus)
                  ? 'current'
                  : formatLabel(packet?.taskPlanStatus?.classification || 'not_persisted')}
              </span>
            </div>
            <p>{taskPlanSummary(packet?.taskPlanStatus)}</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h2>Queue readiness</h2>
              <span className={`status-pill ${((packet?.workfront.summary?.ready_count || 0) > 0) ? 'status-backend-routed' : 'status-awaiting-values'}`}>
                {formatCount(packet?.workfront.summary?.ready_count)} ready
              </span>
            </div>
            <p>{formatCount(packet?.workfront.summary?.total_count)} apparatus rows are on the PM workfront.</p>
          </article>
          <article className="status-card">
            <div className="status-row">
              <h2>Downstream posture</h2>
              <span className="status-pill status-deferred">blocked</span>
            </div>
            <p>Finance, customer billing delivery, and source writeback remain separate branches.</p>
          </article>
        </section>

        <section className="notes-card pm-project-overview-attention-card">
          <div className="pm-project-overview-attention-header">
            <div>
              <h2>What Needs Your Attention Next</h2>
              <p>These are the immediate PM moves the current project state is asking you to make.</p>
            </div>
            <p className="pm-project-overview-section-label">In priority order</p>
          </div>

          <div className="pm-project-overview-attention-list">
            {attentionItems.map((item) => (
              <article key={item.id} className="pm-project-overview-attention-item">
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="pm-project-overview-stage-list" aria-label="Project overview stages">
          {loading && !stageCards.length ? (
            <div className="card pm-runtime-state">
              <h3>Loading overview stages</h3>
              <p>Collecting the current PM candidate, gate, queue, and customer delivery status.</p>
            </div>
          ) : null}

          {stageCards.map((stage) => (
            <article key={stage.id} className="notes-card pm-project-overview-stage">
              <div className="status-row pm-project-overview-stage-header">
                <div>
                  <p className="eyebrow pm-project-overview-step">Step {stage.step}</p>
                  <h2 className="pm-project-overview-stage-title">{stage.title}</h2>
                </div>
                <span className={`status-pill ${toneClass(stage.tone)}`}>{formatLabel(stage.tone)}</span>
              </div>

              <p className="pm-project-overview-copy">{stage.summary}</p>

              <div className="pm-project-overview-section">
                <p className="pm-project-overview-section-label">
                  Decision you need to make
                </p>
                <p className="pm-project-overview-copy">{stage.decision}</p>
              </div>

              <div className="pm-project-overview-section">
                <p className="pm-project-overview-section-label">
                  When this matters
                </p>
                <p className="pm-project-overview-copy">{stage.when}</p>
              </div>

              <div className="pm-project-overview-section">
                <p className="pm-project-overview-section-label">
                  Available now
                </p>
                <ul className="pm-project-overview-available-list">
                  {stage.availableNow.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <p className="pm-review-link-row pm-project-overview-stage-links">
                <Link href={stage.routeHref}>{stage.routeLabel}</Link>
              </p>
            </article>
          ))}
        </section>
      </section>
    </main>
  )
}