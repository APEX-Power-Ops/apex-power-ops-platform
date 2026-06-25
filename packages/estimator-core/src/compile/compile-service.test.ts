import { describe, expect, it } from 'vitest'
import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver } from '../catalog/resolver'
import type { EquipmentModel } from '../catalog/types'
import { makeDraft, type ScopeDraft } from '../schema/draft'
import { compile } from './compile'
import { validateEnvelope } from '../validate/validator'

const resolver = createCatalogResolver(seed as EquipmentModel[])

describe('compile — service line + N4 on whole scope (Case D)', () => {
  it('isolates service hours, sets adjusted basis, P4=274450', () => {
    const scope: ScopeDraft = {
      scope_id: 'S1', name: 'Scope D', neta_standard: 'ATS', replication_m4: 1, adjustment_multiplier_n4: 1.1,
      labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
      lines: [
        { line_uid: 'L1', line_kind: 'catalog', included: true, equipment_model_ref: 'Automatic Transfer Switch - (IR/DLRO)', base_qty: 1, expansion_policy: 'one_unit_per_qty' },
        { line_uid: 'SV1', line_kind: 'service', included: true, service_kind: 'repair', billing_type: 'fixed_bid', quoted_service_hours: 8, quoted_amount_cents: 200000 },
      ],
    }
    const draft = makeDraft({ draft_id: 'dD', estimator_ref: 'e', scopes: [scope] })
    const env = compile(draft, draft.selected_revision_id, resolver)
    const s = env.scopes[0]!
    expect(s.scope_totals.base_app_hours).toBe(3) // service hours NOT included
    expect(s.scope_totals.service_hours).toBe(8)
    expect(s.scope_totals.onsite_labor_cents).toBe(49500)
    expect(s.scope_totals.service_cents).toBe(200000)
    expect(s.scope_totals.pre_adjust_cents).toBe(249500)
    expect(s.scope_totals.adjusted_cents).toBe(274450)
    const svc = s.lines.find((l) => l.line_uid === 'SV1')!
    expect(svc.adjusted_quoted_amount_cents).toBe(220000)
    expect(validateEnvelope(env)).toEqual([])
  })
})
