'use client'

import * as React from 'react'
import Link from 'next/link'

type DeliveryExecutionForm = {
  idempotency_key: string
  project_id: string
  candidate_id: string
  source_fingerprint: string
  customer_preview_review_id: string
  customer_delivery_proof_review_id: string
  customer_delivery_event_id: string
  named_recipient_name: string
  named_recipient_role: string
  delivery_channel: string
  delivery_artifact_refs: string
  delivered_at_utc: string
  execution_method: string
  delivery_proof_type: string
  delivery_proof_ref: string
  customer_delivery_status: string
  execution_note: string
  proof_recorded_at_utc: string
}

type MutationResult = {
  status?: string
  mutation_id?: string
  entity_id?: string
  new_state?: Record<string, unknown>
  error?: {
    message?: string
  }
}

type StatusReadback = {
  status?: string
  latest_customer_delivery_event_id?: string | null
  latest_delivered_at_utc?: string | null
  latest_delivery_proof_type?: string | null
  latest_delivery_proof_ref?: string | null
  preview_review_lineage_match?: boolean
  delivery_proof_review_lineage_match?: boolean
  finance_authority?: string
  source_writeback_authority?: string
  customer_billing_delivery_authority?: string
}

const API_BASE =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1'

const PM_ACTOR = {
  actor_id: 'pm-001',
  actor_role: 'pm',
  project_scope: ['pm-import-project-miner-temp-power'],
}

const DEFAULT_FORM: Omit<DeliveryExecutionForm, 'idempotency_key'> = {
  project_id: 'pm-import-project-miner-temp-power',
  candidate_id: 'pm-import-candidate-miner-temp-power',
  source_fingerprint: 'e111fdbe934bf9de07ed24c1',
  customer_preview_review_id: 'temp-power-customer-preview-review-demo',
  customer_delivery_proof_review_id: 'temp-power-customer-delivery-proof-review-demo',
  customer_delivery_event_id: 'temp-power-delivery-event-0001',
  named_recipient_name: 'Jordan Buyer',
  named_recipient_role: 'Operations Manager',
  delivery_channel: 'CONTROLLED_EMAIL',
  delivery_artifact_refs: 'delivery://temp-power/2026-05-18/email-package-0001',
  delivered_at_utc: '2026-05-18T23:45:00Z',
  execution_method: 'CONTROLLED_EMAIL_OPERATOR_SEND',
  delivery_proof_type: 'EMAIL_RECEIPT',
  delivery_proof_ref: 'receipt://temp-power/2026-05-18/email-receipt-0001',
  customer_delivery_status: 'DELIVERED_AND_PROOF_ATTACHED',
  execution_note:
    'PM executed the admitted customer-facing delivery event only; finance, source writeback, and customer billing delivery remain blocked.',
  proof_recorded_at_utc: '2026-05-18T23:45:00Z',
}

function makeToken() {
  return `Bearer ${btoa(JSON.stringify(PM_ACTOR))}`
}

function buildIdempotencyKey() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `pm-lane-347-customer-delivery-event:${crypto.randomUUID()}`
  }
  return `pm-lane-347-customer-delivery-event:${Date.now()}`
}

function buildPayload(form: DeliveryExecutionForm) {
  return {
    ...form,
    delivery_artifact_refs: form.delivery_artifact_refs
      .split('\n')
      .map((value) => value.trim())
      .filter(Boolean),
  }
}

async function readDeliveryEventStatus(): Promise<StatusReadback> {
  const response = await fetch(`${API_BASE}/reads/temp-power-customer-delivery-event-status`, {
    headers: { Authorization: makeToken() },
  })

  if (!response.ok) {
    throw new Error('Failed to read customer delivery event status')
  }

  return (await response.json()) as StatusReadback
}

async function submitDeliveryEvent(form: DeliveryExecutionForm): Promise<MutationResult> {
  const payload = buildPayload(form)
  const body = {
    idempotency_key: form.idempotency_key,
    mutation_class: 'C',
    action_type: 'persist_temp_power_customer_delivery_event',
    entity_id: form.customer_delivery_event_id,
    payload,
    reason:
      'Persist admitted Temp Power customer-facing delivery execution event only; finance, source writeback, and customer billing delivery remain blocked.',
    source: 'online',
    client_timestamp: new Date().toISOString(),
  }

  const response = await fetch(`${API_BASE}/mutations/temp-power-customer-delivery-events`, {
    method: 'POST',
    headers: {
      Authorization: makeToken(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  return (await response.json()) as MutationResult
}

export default function CustomerDeliveryExecutionPage() {
  const [form, setForm] = React.useState<DeliveryExecutionForm>(() => ({
    idempotency_key: buildIdempotencyKey(),
    ...DEFAULT_FORM,
  }))
  const [statusReadback, setStatusReadback] = React.useState<StatusReadback | null>(null)
  const [mutationResult, setMutationResult] = React.useState<MutationResult | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const refreshStatus = React.useCallback(async () => {
    setError(null)
    try {
      const next = await readDeliveryEventStatus()
      setStatusReadback(next)
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : String(refreshError))
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    document.title = 'APEX PM Customer Delivery Execution Route'
    void refreshStatus()
  }, [refreshStatus])

  function updateField<K extends keyof DeliveryExecutionForm>(field: K, value: DeliveryExecutionForm[K]) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitDeliveryEvent(form)
      setMutationResult(result)
      if (result.status !== 'accepted' && result.status !== 'idempotent_hit') {
        setError(result.error?.message || 'Customer delivery execution was rejected')
        return
      }
      await refreshStatus()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : String(submitError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Delivery Execution</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>PM customer delivery execution now has an admitted orchestration route.</h1>
            <p className="lede">
              This route orchestrates one bounded customer-facing delivery execution packet against the governed mutation
              seam while keeping finance output, source writeback, and customer billing delivery explicitly blocked.
            </p>
          </div>
          <dl className="contract-panel">
            <div>
              <dt>Promoted route</dt>
              <dd>/pm-review/customer-delivery-execution</dd>
            </div>
            <div>
              <dt>Mutation seam route</dt>
              <dd>/api/v1/mutations/temp-power-customer-delivery-events</dd>
            </div>
            <div>
              <dt>Status readback</dt>
              <dd>/api/v1/reads/temp-power-customer-delivery-event-status</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Customer Delivery Execution Orchestration</h2>
            <p>
              The orchestration surface collects current lineage ids, bounded recipient proof, and one admitted delivery
              execution request. It does not widen into finance output, source writeback, or customer billing delivery.
            </p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/workfront">Open PM workfront</Link>
          </p>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer delivery execution guardrails">
          <h3>Guardrails</h3>
          <p>Allowed delivery channels: CONTROLLED_EMAIL, LATER_APPROVED_PORTAL.</p>
          <p>Allowed execution methods: CONTROLLED_EMAIL_OPERATOR_SEND, LATER_APPROVED_PORTAL_OPERATOR_RELEASE.</p>
          <p>Boundaries remain blocked: finance export, source writeback, customer billing delivery.</p>
        </div>

        <form className="card pm-runtime-state" onSubmit={handleSubmit}>
          <h3>Execution request</h3>
          <p>This admitted route sends one bounded seam request using the current PM actor token.</p>
          <label>
            Customer preview review id
            <input value={form.customer_preview_review_id} onChange={(event) => updateField('customer_preview_review_id', event.target.value)} />
          </label>
          <label>
            Customer delivery proof review id
            <input
              value={form.customer_delivery_proof_review_id}
              onChange={(event) => updateField('customer_delivery_proof_review_id', event.target.value)}
            />
          </label>
          <label>
            Customer delivery event id
            <input value={form.customer_delivery_event_id} onChange={(event) => updateField('customer_delivery_event_id', event.target.value)} />
          </label>
          <label>
            Named recipient name
            <input value={form.named_recipient_name} onChange={(event) => updateField('named_recipient_name', event.target.value)} />
          </label>
          <label>
            Named recipient role
            <input value={form.named_recipient_role} onChange={(event) => updateField('named_recipient_role', event.target.value)} />
          </label>
          <label>
            Delivery artifact refs
            <textarea value={form.delivery_artifact_refs} onChange={(event) => updateField('delivery_artifact_refs', event.target.value)} rows={3} />
          </label>
          <label>
            Execution note
            <textarea value={form.execution_note} onChange={(event) => updateField('execution_note', event.target.value)} rows={3} />
          </label>
          <div className="pm-review-link-row">
            <button type="submit" disabled={submitting}>{submitting ? 'Executing delivery event...' : 'Execute customer delivery event'}</button>
            <button type="button" onClick={() => void refreshStatus()} disabled={submitting}>Refresh delivery event readback</button>
            <button type="button" onClick={() => setForm({ idempotency_key: buildIdempotencyKey(), ...DEFAULT_FORM })} disabled={submitting}>
              Reset seeded request
            </button>
          </div>
        </form>

        {error && (
          <div className="card pm-runtime-state pm-runtime-error" role="alert">
            <h3>Customer delivery execution error</h3>
            <p>{error}</p>
          </div>
        )}

        <div className="card pm-runtime-state" role="region" aria-label="Customer delivery execution mutation result">
          <h3>Mutation result</h3>
          <pre>{JSON.stringify(mutationResult ?? { status: 'not_run' }, null, 2)}</pre>
        </div>

        <div className="card pm-runtime-state" role="region" aria-label="Customer delivery execution readback">
          <h3>Delivery event readback</h3>
          {loading ? <p>Loading current customer delivery event status...</p> : <pre>{JSON.stringify(statusReadback ?? { status: 'unavailable' }, null, 2)}</pre>}
        </div>
      </section>
    </main>
  )
}