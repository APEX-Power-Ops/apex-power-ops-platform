import { createHash } from 'node:crypto'
import type { EstimateEnvelope, LaborChargeLine, LineC, ScopeC } from '../schema/envelope'

const SCALE4 = 10_000

function mult(v: number): number {
  // multiplier/percentage -> x10^4 integer; no floats in the preimage
  return Math.round(v * SCALE4)
}

function h(v: number | null): number | null {
  // hours / fractional quantities -> x10^6 integer (no floats in the preimage); null passes through
  return v === null ? null : Math.round(v * 1_000_000)
}

const byStr = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0)

function laborChargeToken(l: LaborChargeLine): unknown[] {
  return [l.labor_type, mult(l.pct_of_app), h(l.resolved_hours), l.cents]
}

function lineToken(l: LineC): unknown[] {
  // Economic content + CANONICAL IDENTITY, fixed order. For custom_equipment the identity IS
  // economic: catalog_request_ref + equipment_fingerprint distinguish two lines with identical
  // economics but different equipment (each mints a different canonical row at approve) — so they
  // MUST be hashed, or approve idempotency could collapse two distinct awards. equipment_fingerprint
  // is the canonical digest of provisional_attrs, so raw provisional_attrs need not be hashed.
  // provisional_token is DRAFT-LOCAL (not canonical) — EXCLUDED, else two producers/revisions of the
  // same equipment would hash differently and break preview==approved equality. Pure provenance refs
  // (rate_basis_ref, markup_basis_ref) stay excluded too.
  return [
    l.line_uid,
    l.line_kind,
    l.included,
    h(l.excluded_hours),
    l.expansion_policy,
    l.equipment_model_ref,
    l.catalog_request_ref,
    l.equipment_fingerprint,
    h(l.provisional_ref_hours),
    l.base_qty,
    l.project_intake_qty,
    h(l.resolved_ref_hours),
    h(l.resolved_hours),
    l.service_kind,
    l.billing_type,
    h(l.quoted_service_hours),
    l.quoted_amount_cents,
    l.ceiling_cents,
    l.adjusted_quoted_amount_cents,
    l.adjusted_ceiling_cents,
    l.cost_category,
    h(l.units),
    l.unit_cost_cents,
    l.extended_cents,
  ]
}

function scopeToken(s: ScopeC): unknown[] {
  const t = s.scope_totals
  // canonical order so identical economic content hashes the same regardless of producer line order
  const charges = [...s.labor_charge_lines].sort((a, b) => byStr(a.labor_type, b.labor_type))
  const lines = [...s.lines].sort((a, b) => byStr(a.line_uid, b.line_uid))
  return [
    s.neta_standard,
    mult(s.replication_m4),
    mult(s.adjustment_multiplier_n4),
    charges.map(laborChargeToken),
    [
      h(t.base_app_hours),
      h(t.quoted_app_hours),
      h(t.service_hours),
      t.onsite_labor_cents,
      t.offsite_labor_cents,
      t.cost_cents,
      t.service_cents,
      t.pre_adjust_cents,
      t.adjusted_cents,
    ],
    lines.map(lineToken),
  ]
}

export function canonicalPreimage(env: EstimateEnvelope): string {
  const scopes = [...env.scopes].sort((a, b) => byStr(a.scope_id, b.scope_id))
  const preimage = [
    env.schema_version,
    env.pricing_card_version,
    scopes.map(scopeToken),
    [h(env.totals.base_app_hours), h(env.totals.quoted_app_hours), h(env.totals.service_hours), env.totals.bid_cents],
  ]
  return JSON.stringify(preimage)
}

export function computeContentHash(env: EstimateEnvelope): string {
  return createHash('sha256').update(canonicalPreimage(env), 'utf8').digest('hex')
}
