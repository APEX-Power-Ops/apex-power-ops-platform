import type { NetaStandard } from '../catalog/types'
import type { LaborType } from '../pricing/rate-card'
import type { BillingType, CostCategory, ExpansionPolicy, LineKind, ServiceKind } from './enums'

export const SCHEMA_VERSION = 'estimate_envelope_v1' as const

export interface LaborChargeLine {
  labor_type: LaborType
  pct_of_app: number // decimal fraction (0.35 == 35%), same convention as LaborAllocationEntry; hashed via mult() ×10⁴
  resolved_hours: number
  rate_basis_ref: string // e.g. `${card_version}:${labor_type}`
  cents: number
}

export interface LineC {
  line_uid: string
  line_kind: LineKind
  included: boolean
  excluded_hours: number | null
  exclusion_reason: string | null
  expansion_policy: ExpansionPolicy | null
  equipment_model_ref: string | null
  provisional_token: string | null
  catalog_request_ref: string | null
  provisional_attrs: Record<string, unknown> | null
  equipment_fingerprint: string | null
  provisional_ref_hours: number | null
  base_qty: number | null
  project_intake_qty: number | null
  resolved_ref_hours: number | null
  resolved_hours: number | null
  service_kind: ServiceKind | null
  billing_type: BillingType | null
  quoted_service_hours: number | null
  quoted_amount_cents: number | null
  ceiling_cents: number | null
  adjusted_quoted_amount_cents: number | null
  adjusted_ceiling_cents: number | null
  cost_category: CostCategory | null
  units: number | null
  unit_cost_cents: number | null
  markup_basis_ref: string | null
  rate_basis_ref: string | null
  extended_cents: number
}

export interface ScopeTotals {
  base_app_hours: number
  quoted_app_hours: number
  service_hours: number
  onsite_labor_cents: number
  offsite_labor_cents: number
  cost_cents: number
  service_cents: number
  pre_adjust_cents: number
  adjusted_cents: number
}

export interface ScopeC {
  scope_id: string
  name: string
  neta_standard: NetaStandard
  replication_m4: number
  adjustment_multiplier_n4: number
  lines: LineC[]
  labor_charge_lines: LaborChargeLine[]
  scope_totals: ScopeTotals
}

export interface EnvelopeTotals {
  base_app_hours: number
  quoted_app_hours: number
  service_hours: number
  bid_cents: number
}

export interface EstimateEnvelope {
  envelope_id: string
  schema_version: typeof SCHEMA_VERSION
  source_kind: 'native' | 'workbook_intake'
  source_draft_id: string | null
  source_revision_id: string | null
  job_number_source_ref: string | null
  project_number: string | null
  quote_version: number | null
  pricing_card_version: string
  compiled_at: string | null
  content_hash: string
  scopes: ScopeC[]
  totals: EnvelopeTotals
}
