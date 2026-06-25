import { describe, expect, it } from 'vitest'
import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver } from '../catalog/resolver'
import type { EquipmentModel } from '../catalog/types'
import { makeDraft, type LineDraft, type ScopeDraft } from '../schema/draft'
import { compile } from './compile'
import { validateEnvelope } from '../validate/validator'

const resolver = createCatalogResolver(seed as EquipmentModel[])

function apparatusScope(over: Partial<ScopeDraft> = {}): ScopeDraft {
  return {
    scope_id: 'S1', name: 'Scope A', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
    labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
    lines: [
      { line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - (IR/DLRO)', base_qty: 2, expansion_policy: 'one_unit_per_qty' },
      { line_uid: 'L2', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)', base_qty: 1, expansion_policy: 'one_unit_per_qty' },
    ],
    ...over,
  }
}

describe('compile — apparatus + default labor (Case A)', () => {
  it('reproduces J3=10h, P14=165000, P4=165000', () => {
    const draft = makeDraft({ draft_id: 'dA', estimator_ref: 'e', scopes: [apparatusScope()] })
    const env = compile(draft, draft.selected_revision_id, resolver)
    const s = env.scopes[0]!
    expect(s.scope_totals.base_app_hours).toBe(10)
    expect(s.scope_totals.quoted_app_hours).toBe(10)
    expect(s.scope_totals.onsite_labor_cents).toBe(165000)
    expect(s.scope_totals.adjusted_cents).toBe(165000)
    expect(env.totals.bid_cents).toBe(165000)
    expect(s.lines[0]!.project_intake_qty).toBe(2)
    expect(s.lines[0]!.resolved_ref_hours).toBe(3)
  })
})

describe('compile — input guards', () => {
  it('throws a clear error (not a RangeError) on non-integer replication_m4', () => {
    const draft = makeDraft({ draft_id: 'dM4', estimator_ref: 'e', scopes: [apparatusScope({ replication_m4: 1.5 })] })
    expect(() => compile(draft, draft.selected_revision_id, resolver)).toThrow(/replication_m4 must be an integer/)
  })

  it('throws on replication_m4 < 1', () => {
    const draft = makeDraft({ draft_id: 'dM0', estimator_ref: 'e', scopes: [apparatusScope({ replication_m4: 0 })] })
    expect(() => compile(draft, draft.selected_revision_id, resolver)).toThrow(/replication_m4 must be an integer/)
  })
})

describe('compile — labor split + travel + outside services (Case B)', () => {
  it('reproduces P14=237600, P19=54000, P26=360000, P33=112500, P4=764100', () => {
    const scope: ScopeDraft = {
      scope_id: 'S1', name: 'Scope B', neta_standard: 'MTS', replication_m4: 1, adjustment_multiplier_n4: 1,
      labor_allocation: [
        { labor_type: 'onsite_blended_10hr', pct_of_app: 0.8 },
        { labor_type: 'offsite_report', pct_of_app: 0.2 },
      ],
      lines: [
        { line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch (Functional Testing)', base_qty: 3, expansion_policy: 'one_unit_per_qty' },
        { line_uid: 'L2', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)', base_qty: 1, expansion_policy: 'one_unit_per_qty' },
        { line_uid: 'C1', line_kind: 'cost', included: true, cost_category: 'travel', units: 4, unit_cost_cents: 27500, markup_applies: true },
        { line_uid: 'C2', line_kind: 'cost', included: true, cost_category: 'travel', units: 2, unit_cost_cents: 65000, markup_applies: true },
        { line_uid: 'C3', line_kind: 'cost', included: true, cost_category: 'outside_services', units: 1, unit_cost_cents: 75000, markup_applies: true },
      ],
    }
    const draft = makeDraft({ draft_id: 'dB', estimator_ref: 'e', scopes: [scope] })
    const s = compile(draft, draft.selected_revision_id, resolver).scopes[0]!
    expect(s.scope_totals.quoted_app_hours).toBe(18)
    expect(s.scope_totals.onsite_labor_cents).toBe(237600)
    expect(s.scope_totals.offsite_labor_cents).toBe(54000)
    expect(s.scope_totals.cost_cents).toBe(360000 + 112500)
    expect(s.scope_totals.adjusted_cents).toBe(764100)
  })
})

describe('compile — cost defaults resolve by key (override-aware)', () => {
  const withCost = (cost: LineDraft): ScopeDraft => ({
    scope_id: 'S1', name: 'Scope', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
    labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
    lines: [
      { line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - (IR/DLRO)', base_qty: 1, expansion_policy: 'one_unit_per_qty' },
      cost,
    ],
  })
  it('reproduces the workbook default from a key, and honors an explicit override', () => {
    // hotel_per_diem default = 27500, markup 1.5; 4 units -> 4*27500*1.5 = 165000
    const byKey = makeDraft({ draft_id: 'dk', estimator_ref: 'e', scopes: [withCost({ line_uid: 'C1', line_kind: 'cost', included: true, cost_default_key: 'hotel_per_diem', units: 4 })] })
    expect(compile(byKey, byKey.selected_revision_id, resolver).scopes[0]!.scope_totals.cost_cents).toBe(165000)
    // override unit cost -> 4*30000*1.5 = 180000
    const over = makeDraft({ draft_id: 'do', estimator_ref: 'e', scopes: [withCost({ line_uid: 'C1', line_kind: 'cost', included: true, cost_default_key: 'hotel_per_diem', units: 4, unit_cost_cents: 30000 })] })
    expect(compile(over, over.selected_revision_id, resolver).scopes[0]!.scope_totals.cost_cents).toBe(180000)
  })

  it('applies NO markup to travel_hours (workbook cell O21=1, the ×1 exception)', () => {
    // travel_hours default = 15000c, markup off; 3 units -> 3*15000*1 = 45000 (NOT *1.5 = 67500)
    const d = makeDraft({ draft_id: 'dth', estimator_ref: 'e', scopes: [withCost({ line_uid: 'C1', line_kind: 'cost', included: true, cost_default_key: 'travel_hours', units: 3 })] })
    expect(compile(d, d.selected_revision_id, resolver).scopes[0]!.scope_totals.cost_cents).toBe(45000)
  })
})

describe('compile — custom_equipment line (mint-pending, on provisional_ref_hours)', () => {
  it('compiles + validates clean; resolved_ref_hours stays null', () => {
    const scope: ScopeDraft = {
      scope_id: 'S1', name: 'Scope CE', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
      labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
      lines: [
        { line_uid: 'CE1', line_kind: 'custom_equipment', included: true, provisional_token: 'T-1', catalog_request_ref: 'REQ-1', equipment_fingerprint: 'FP-1', provisional_ref_hours: 5, base_qty: 2, expansion_policy: 'one_unit_per_qty' },
      ],
    }
    const draft = makeDraft({ draft_id: 'dCE', estimator_ref: 'e', scopes: [scope] })
    const env = compile(draft, draft.selected_revision_id, resolver)
    const s = env.scopes[0]!
    expect(s.scope_totals.base_app_hours).toBe(10) // 2 x 5
    expect(s.scope_totals.onsite_labor_cents).toBe(165000) // 10 x 16500
    const ce = s.lines[0]!
    expect(ce.resolved_ref_hours).toBeNull()
    expect(ce.provisional_ref_hours).toBe(5)
    expect(ce.resolved_hours).toBe(10)
    expect(validateEnvelope(env)).toEqual([])
  })
})

describe('compile — M4 materialization + N4 discount (Case C)', () => {
  it('base J3=2 retained, quoted=6, P4=89100 (99000 x 0.9)', () => {
    const scope: ScopeDraft = {
      scope_id: 'S1', name: 'Scope C', neta_standard: 'ATS', replication_m4: 3, adjustment_multiplier_n4: 0.9,
      labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
      lines: [{ line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Arrestor (SPD) - Low Voltage', base_qty: 4, expansion_policy: 'one_unit_per_qty' }],
    }
    const draft = makeDraft({ draft_id: 'dC', estimator_ref: 'e', scopes: [scope] })
    const s = compile(draft, draft.selected_revision_id, resolver).scopes[0]!
    expect(s.scope_totals.base_app_hours).toBe(2)
    expect(s.scope_totals.quoted_app_hours).toBe(6)
    expect(s.lines[0]!.project_intake_qty).toBe(12)
    expect(s.scope_totals.onsite_labor_cents).toBe(99000)
    expect(s.scope_totals.adjusted_cents).toBe(89100)
  })
})

describe('compile — excluded line (Case E)', () => {
  it('excluded apparatus contributes 0 hours and 0 cents', () => {
    const scope: ScopeDraft = {
      scope_id: 'S1', name: 'Scope E', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1,
      labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
      lines: [
        { line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - (IR/DLRO)', base_qty: 2, expansion_policy: 'one_unit_per_qty' },
        { line_uid: 'L2', line_kind: 'catalog', included: false, excluded_hours: 4, exclusion_reason: 'alternate', equipment_model_ref: 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)', base_qty: 1, expansion_policy: 'one_unit_per_qty' },
      ],
    }
    const draft = makeDraft({ draft_id: 'dE', estimator_ref: 'e', scopes: [scope] })
    const s = compile(draft, draft.selected_revision_id, resolver).scopes[0]!
    expect(s.scope_totals.base_app_hours).toBe(6)
    expect(s.scope_totals.adjusted_cents).toBe(99000)
    const excluded = s.lines.find((l) => l.line_uid === 'L2')!
    expect(excluded.included).toBe(false)
    expect(excluded.excluded_hours).toBe(4)
    expect(excluded.extended_cents).toBe(0)
  })
})
