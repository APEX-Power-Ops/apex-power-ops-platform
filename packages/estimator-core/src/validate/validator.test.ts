import { describe, expect, it } from 'vitest'
import type { EstimateEnvelope, LineC, ScopeC } from '../schema/envelope'
import { SCHEMA_VERSION } from '../schema/envelope'
import { computeContentHash } from '../compile/content-hash'
import { validateEnvelope } from './validator'

function emptyLine(p: Partial<LineC> & { line_uid: string; line_kind: LineC['line_kind'] }): LineC {
  return {
    designation: null, notes: null, description: null,
    included: true, excluded_hours: null, exclusion_reason: null, expansion_policy: null,
    equipment_model_ref: null, provisional_token: null, catalog_request_ref: null,
    provisional_attrs: null, equipment_fingerprint: null, provisional_ref_hours: null,
    base_qty: null, project_intake_qty: null, resolved_ref_hours: null, resolved_hours: null,
    service_kind: null, billing_type: null, quoted_service_hours: null, quoted_amount_cents: null,
    ceiling_cents: null, adjusted_quoted_amount_cents: null, adjusted_ceiling_cents: null,
    cost_category: null, units: null, unit_cost_cents: null, markup_basis_ref: null,
    rate_basis_ref: null, extended_cents: 0, ...p,
  }
}

function catalogLine(): LineC {
  return emptyLine({
    line_uid: 'L1', line_kind: 'catalog', equipment_model_ref: 'ATS - (IR/DLRO)',
    expansion_policy: 'one_unit_per_qty', base_qty: 2, project_intake_qty: 2,
    resolved_ref_hours: 3, resolved_hours: 6, rate_basis_ref: '2026-01-23', extended_cents: 99000,
  })
}

function oneScope(): ScopeC {
  return {
    scope_id: 'S1', name: 'Scope', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
    lines: [catalogLine()],
    labor_charge_lines: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1, resolved_hours: 6, rate_basis_ref: '2026-01-23:onsite_blended_10hr', cents: 99000 }],
    scope_totals: {
      base_app_hours: 6, quoted_app_hours: 6, service_hours: 0,
      onsite_labor_cents: 99000, offsite_labor_cents: 0, cost_cents: 0, service_cents: 0,
      pre_adjust_cents: 99000, adjusted_cents: 99000,
    },
  }
}

function goodEnv(): EstimateEnvelope {
  const env: EstimateEnvelope = {
    envelope_id: 'e1', schema_version: SCHEMA_VERSION, source_kind: 'native',
    source_draft_id: 'd1', source_revision_id: 'r1', job_number_source_ref: null,
    project_number: null, quote_version: null, pricing_card_version: '2026-01-23',
    compiled_at: null, content_hash: '', scopes: [oneScope()],
    totals: { base_app_hours: 6, quoted_app_hours: 6, service_hours: 0, bid_cents: 99000 },
  }
  env.content_hash = computeContentHash(env)
  return env
}

describe('envelope validator', () => {
  it('passes a clean envelope', () => {
    expect(validateEnvelope(goodEnv())).toEqual([])
  })

  it('flags a wrong content_hash', () => {
    const env = goodEnv()
    env.content_hash = 'deadbeef'
    expect(validateEnvelope(env).map((f) => f.code)).toContain('content_hash')
  })

  it('flags a pure-cost scope (no recognizable unit)', () => {
    const env = goodEnv()
    env.scopes[0]!.lines = [emptyLine({ line_uid: 'C1', line_kind: 'cost', cost_category: 'travel', units: 1, unit_cost_cents: 100, extended_cents: 150 })]
    env.scopes[0]!.labor_charge_lines = []
    env.scopes[0]!.scope_totals = { ...env.scopes[0]!.scope_totals, base_app_hours: 0, quoted_app_hours: 0, onsite_labor_cents: 0, cost_cents: 150, pre_adjust_cents: 150, adjusted_cents: 150 }
    env.totals = { base_app_hours: 0, quoted_app_hours: 0, service_hours: 0, bid_cents: 150 }
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('scope_recognizable_unit')
  })

  it('flags labor_charge_lines that do not sum to the block totals', () => {
    const env = goodEnv()
    env.scopes[0]!.labor_charge_lines[0]!.cents = 88888
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('labor_charge_lines')
  })

  it('flags an included=false line missing excluded_hours', () => {
    const env = goodEnv()
    env.scopes[0]!.lines.push(emptyLine({ line_uid: 'L2', line_kind: 'catalog', equipment_model_ref: 'X', included: false, base_qty: 1, project_intake_qty: 1, resolved_ref_hours: 1, resolved_hours: 1 }))
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('included_invariant')
  })

  it('flags duplicate (project_number, quote_version) across siblings', () => {
    const a = goodEnv(); a.project_number = 'JOB-1'; a.quote_version = 1; a.content_hash = computeContentHash(a)
    const b = goodEnv(); b.project_number = 'JOB-1'; b.quote_version = 1; b.content_hash = computeContentHash(b)
    expect(validateEnvelope(a, { siblingEnvelopes: [b] }).map((f) => f.code)).toContain('quote_version_unique')
  })

  it('flags extended_cents that do not sum to adjusted_cents', () => {
    const env = goodEnv()
    env.scopes[0]!.lines[0]!.extended_cents = 1 // was 99000; breaks the sum
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('extended_cents_sum')
  })

  it('flags an included service line missing its adjusted basis', () => {
    const env = goodEnv()
    env.scopes[0]!.lines.push(
      emptyLine({
        line_uid: 'SV1', line_kind: 'service', billing_type: 'fixed_bid',
        quoted_service_hours: 8, quoted_amount_cents: 200000,
        // adjusted_quoted_amount_cents intentionally null
      }),
    )
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('service_adjusted_basis')
  })

  it('flags a non-integer apparatus quantity', () => {
    const env = goodEnv()
    env.scopes[0]!.lines[0]!.base_qty = 2.5
    env.scopes[0]!.lines[0]!.project_intake_qty = 2.5
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('integer_quantity')
  })

  it('flags a non-member closed-enum discriminator (workbook_intake hardening)', () => {
    const env = goodEnv()
    env.scopes[0]!.lines.push(
      emptyLine({
        line_uid: 'SV1', line_kind: 'service', billing_type: 'fixed_bid', quoted_service_hours: 8,
        quoted_amount_cents: 200000, adjusted_quoted_amount_cents: 200000,
        service_kind: 'frobnicate' as never,
      }),
    )
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('enum_membership')
  })

  it('flags a wrong schema_version', () => {
    const env = goodEnv()
    env.schema_version = 'estimate_envelope_v0' as never
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('schema_version')
  })

  it('flags a non-integer scope total (integer_cents)', () => {
    const env = goodEnv()
    env.scopes[0]!.scope_totals.onsite_labor_cents = 99000.5
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('integer_cents')
  })

  it('flags a mutated base_app_hours that does not reproduce (hours_reproduce)', () => {
    const env = goodEnv()
    env.scopes[0]!.scope_totals.base_app_hours = 999
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('hours_reproduce')
  })

  it('flags service_hours that do not match included service lines (service_hours_isolated)', () => {
    const env = goodEnv()
    env.scopes[0]!.scope_totals.service_hours = 5
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('service_hours_isolated')
  })

  it('flags duplicate provisional_token across custom_equipment lines (provisional_token_unique)', () => {
    const env = goodEnv()
    const mk = (uid: string) =>
      emptyLine({
        line_uid: uid, line_kind: 'custom_equipment', provisional_token: 'TKN',
        catalog_request_ref: 'REQ', equipment_fingerprint: 'FP',
        provisional_ref_hours: 1, base_qty: 1, project_intake_qty: 1,
        resolved_hours: 1, expansion_policy: 'one_unit_per_qty',
      })
    env.scopes[0]!.lines = [mk('A'), mk('B')]
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('provisional_token_unique')
  })

  it('flags adjusted_cents that does not match the rounding cascade (rounding_cascade)', () => {
    const env = goodEnv()
    env.scopes[0]!.scope_totals.adjusted_cents = 99050
    env.content_hash = computeContentHash(env)
    expect(validateEnvelope(env).map((f) => f.code)).toContain('rounding_cascade')
  })
})
