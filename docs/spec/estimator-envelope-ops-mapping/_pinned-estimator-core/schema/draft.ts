import type { NetaStandard } from '../catalog/types'
import type { LaborType } from '../pricing/rate-card'
import type { BillingType, CostCategory, ExpansionPolicy, LineKind, ServiceKind } from './enums'

export interface LaborAllocationEntry {
  labor_type: LaborType
  pct_of_app: number // decimal fraction; 0.35 == 35%
}

export interface LineDraft {
  line_uid: string
  line_kind: LineKind
  designation?: string
  notes?: string
  included: boolean
  excluded_hours?: number
  exclusion_reason?: string
  // catalog / custom_equipment
  equipment_model_ref?: string | null
  provisional_token?: string | null
  catalog_request_ref?: string | null
  base_qty?: number
  expansion_policy?: ExpansionPolicy
  // custom_equipment provenance
  provisional_attrs?: Record<string, unknown> | null
  equipment_fingerprint?: string | null
  provisional_ref_hours?: number | null
  // service (D-SVC)
  service_kind?: ServiceKind
  billing_type?: BillingType
  quoted_service_hours?: number
  quoted_amount_cents?: number
  ceiling_cents?: number
  // cost
  cost_category?: CostCategory
  units?: number
  unit_cost_cents?: number
  cost_default_key?: string // resolve a versioned cost_default; explicit fields below override it
  markup_applies?: boolean // override: false for the un-marked travel-hours bucket; else per the default, else true
}

export interface ScopeDraft {
  scope_id: string
  name: string
  neta_standard: NetaStandard
  replication_m4: number // M4 integer >= 1
  adjustment_multiplier_n4: number // N4 decimal, default 1.0
  labor_allocation: LaborAllocationEntry[]
  lines: LineDraft[]
}

export interface Revision {
  revision_id: string
  rev_number: number
  copied_from_revision_id?: string | null
  reason?: string
  pricing_card_version: string
  scopes: ScopeDraft[]
}

export type DraftStatus = 'draft' | 'submitted' | 'approved' | 'superseded'

export interface EstimateDraft {
  draft_id: string
  opportunity_ref?: string | null
  job_number_ref?: string | null
  estimator_ref: string
  status: DraftStatus
  selected_revision_id: string
  revisions: Revision[]
}

/** Minimal one-revision draft. pricing_card_version defaults to the baseline. */
export function makeDraft(args: {
  draft_id: string
  estimator_ref: string
  pricing_card_version?: string
  scopes?: ScopeDraft[]
}): EstimateDraft {
  const revision: Revision = {
    revision_id: `${args.draft_id}-r1`,
    rev_number: 1,
    copied_from_revision_id: null,
    pricing_card_version: args.pricing_card_version ?? '2026-01-23',
    scopes: args.scopes ?? [],
  }
  return {
    draft_id: args.draft_id,
    estimator_ref: args.estimator_ref,
    status: 'draft',
    selected_revision_id: revision.revision_id,
    revisions: [revision],
  }
}
