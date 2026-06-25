import { describe, expect, it } from 'vitest'
import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver } from '../catalog/resolver'
import { compile } from './compile'
import { computeContentHash } from './content-hash'
import { makeDraft } from '../schema/draft'
import type { EquipmentModel } from '../catalog/types'
import type { LineDraft } from '../schema/draft'

const resolver = createCatalogResolver(seed as EquipmentModel[])
const REF = (seed as EquipmentModel[]).find((m) => m.lifecycle_status === 'active' && m.ref_hours.ATS != null)!.ref

function draftWith(meta: Partial<Pick<LineDraft, 'designation' | 'notes' | 'description'>>) {
  return makeDraft({
    draft_id: 'd1',
    estimator_ref: 'e1',
    scopes: [{
      scope_id: 'S1', name: 'Scope A', neta_standard: 'ATS',
      replication_m4: 1, adjustment_multiplier_n4: 1,
      lines: [{ line_uid: 'S1:r1', line_kind: 'catalog', included: true, equipment_model_ref: REF, base_qty: 2, ...meta }],
      labor_allocation: [],
    }],
  })
}

describe('line metadata promotion', () => {
  it('compile carries designation/notes/description onto LineC', () => {
    const draft = draftWith({ designation: 'D-1', notes: 'n', description: 'CB tested' })
    const env = compile(draft, draft.selected_revision_id, resolver)
    const line = env.scopes[0]!.lines[0]!
    expect(line.designation).toBe('D-1')
    expect(line.notes).toBe('n')
    expect(line.description).toBe('CB tested')
  })

  it('metadata is economic-neutral: content_hash is identical regardless of the three fields', () => {
    const dA = draftWith({})
    const dB = draftWith({ designation: 'D-9', notes: 'whatever', description: 'long text here' })
    const a = compile(dA, dA.selected_revision_id, resolver)
    const b = compile(dB, dB.selected_revision_id, resolver)
    expect(computeContentHash(a)).toBe(computeContentHash(b))
    expect(a.content_hash).toBe(b.content_hash)
  })
})
