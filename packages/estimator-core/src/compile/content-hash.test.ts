import { describe, expect, it } from 'vitest'
import type { EstimateEnvelope, LineC, ScopeC } from '../schema/envelope'
import { SCHEMA_VERSION } from '../schema/envelope'
import { computeContentHash } from './content-hash'

function baseEnv(): EstimateEnvelope {
  return {
    envelope_id: 'e1',
    schema_version: SCHEMA_VERSION,
    source_kind: 'native',
    source_draft_id: 'd1',
    source_revision_id: 'r1',
    job_number_source_ref: null,
    project_number: null,
    quote_version: null,
    pricing_card_version: '2026-01-23',
    compiled_at: '2026-06-22T00:00:00Z',
    content_hash: '',
    scopes: [],
    totals: { base_app_hours: 0, quoted_app_hours: 0, service_hours: 0, bid_cents: 0 },
  }
}

describe('content hash (economic content only)', () => {
  it('is identical when only excluded fields differ', () => {
    const a = baseEnv()
    const b = {
      ...baseEnv(),
      envelope_id: 'DIFFERENT',
      compiled_at: '2030-01-01T00:00:00Z',
      source_kind: 'workbook_intake' as const,
      source_draft_id: 'other',
      project_number: 'JOB-999',
      quote_version: 7,
    }
    expect(computeContentHash(a)).toBe(computeContentHash(b))
  })

  it('changes when an economic value changes', () => {
    const a = baseEnv()
    const b = baseEnv()
    b.totals.bid_cents = 100
    expect(computeContentHash(a)).not.toBe(computeContentHash(b))
  })

  it('is a 64-char sha256 hex string', () => {
    expect(computeContentHash(baseEnv())).toMatch(/^[0-9a-f]{64}$/)
  })

  function customLine(fingerprint: string, requestRef: string, token: string): LineC {
    return {
      line_uid: 'L1', line_kind: 'custom_equipment', included: true, excluded_hours: null,
      exclusion_reason: null, expansion_policy: 'one_unit_per_qty', equipment_model_ref: null,
      provisional_token: token, catalog_request_ref: requestRef, provisional_attrs: null,
      equipment_fingerprint: fingerprint, provisional_ref_hours: 4, base_qty: 1, project_intake_qty: 1,
      resolved_ref_hours: null, resolved_hours: 4, service_kind: null, billing_type: null,
      quoted_service_hours: null, quoted_amount_cents: null, ceiling_cents: null,
      adjusted_quoted_amount_cents: null, adjusted_ceiling_cents: null, cost_category: null,
      units: null, unit_cost_cents: null, markup_basis_ref: null, rate_basis_ref: null, extended_cents: 66000,
    }
  }
  const customScope = (line: LineC): ScopeC => ({
    scope_id: 'S1', name: 'S', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
    lines: [line], labor_charge_lines: [],
    scope_totals: { base_app_hours: 4, quoted_app_hours: 4, service_hours: 0, onsite_labor_cents: 66000, offsite_labor_cents: 0, cost_cents: 0, service_cents: 0, pre_adjust_cents: 66000, adjusted_cents: 66000 },
  })

  it('differs for custom_equipment lines with identical economics but different identity', () => {
    const a = baseEnv(); a.scopes = [customScope(customLine('FP-AAA', 'REQ-1', 'T1'))]
    const b = baseEnv(); b.scopes = [customScope(customLine('FP-BBB', 'REQ-2', 'T1'))]
    expect(computeContentHash(a)).not.toBe(computeContentHash(b))
  })

  it('ignores the draft-local provisional_token (same equipment, different token -> same hash)', () => {
    const a = baseEnv(); a.scopes = [customScope(customLine('FP-AAA', 'REQ-1', 'token-X'))]
    const b = baseEnv(); b.scopes = [customScope(customLine('FP-AAA', 'REQ-1', 'token-Y'))]
    expect(computeContentHash(a)).toBe(computeContentHash(b))
  })

  it('is independent of line array order (canonical serialization)', () => {
    const l1 = customLine('FP-1', 'REQ-1', 'T1'); l1.line_uid = 'A'
    const l2 = customLine('FP-2', 'REQ-2', 'T2'); l2.line_uid = 'B'
    const mk = (lines: LineC[]): EstimateEnvelope => {
      const e = baseEnv()
      e.scopes = [{
        scope_id: 'S1', name: 'S', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
        lines, labor_charge_lines: [],
        scope_totals: { base_app_hours: 8, quoted_app_hours: 8, service_hours: 0, onsite_labor_cents: 132000, offsite_labor_cents: 0, cost_cents: 0, service_cents: 0, pre_adjust_cents: 132000, adjusted_cents: 132000 },
      }]
      return e
    }
    expect(computeContentHash(mk([l1, l2]))).toBe(computeContentHash(mk([l2, l1])))
  })

  it('distinguishes cost lines whose only economic difference is markup (carried via extended_cents)', () => {
    const costLine = (extended: number, markupRef: string | null): LineC => ({
      line_uid: 'C1', line_kind: 'cost', included: true, excluded_hours: null, exclusion_reason: null,
      expansion_policy: null, equipment_model_ref: null, provisional_token: null, catalog_request_ref: null,
      provisional_attrs: null, equipment_fingerprint: null, provisional_ref_hours: null, base_qty: null,
      project_intake_qty: null, resolved_ref_hours: null, resolved_hours: null, service_kind: null,
      billing_type: null, quoted_service_hours: null, quoted_amount_cents: null, ceiling_cents: null,
      adjusted_quoted_amount_cents: null, adjusted_ceiling_cents: null, cost_category: 'travel', units: 4,
      unit_cost_cents: 27500, markup_basis_ref: markupRef, rate_basis_ref: null, extended_cents: extended,
    })
    const mk = (line: LineC): EstimateEnvelope => {
      const e = baseEnv()
      e.scopes = [{ scope_id: 'S1', name: 'S', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1, lines: [line], labor_charge_lines: [], scope_totals: { base_app_hours: 0, quoted_app_hours: 0, service_hours: 0, onsite_labor_cents: 0, offsite_labor_cents: 0, cost_cents: line.extended_cents, service_cents: 0, pre_adjust_cents: line.extended_cents, adjusted_cents: line.extended_cents } }]
      return e
    }
    // markup on -> 4*27500*1.5 = 165000 ; markup off -> 4*27500 = 110000
    expect(computeContentHash(mk(costLine(165000, '2026-01-23:markup')))).not.toBe(computeContentHash(mk(costLine(110000, null))))
  })
})
