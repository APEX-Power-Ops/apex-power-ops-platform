import { describe, expect, it } from 'vitest'
import {
  BILLING_TYPES,
  isBillingType,
  isLineKind,
  isServiceKind,
  LINE_KINDS,
  SERVICE_KINDS,
} from './enums'
import { makeDraft } from './draft'

describe('closed enums + guards', () => {
  it('exposes the four line kinds', () => {
    expect(LINE_KINDS).toEqual(['catalog', 'custom_equipment', 'service', 'cost'])
    expect(isLineKind('catalog')).toBe(true)
    expect(isLineKind('misc')).toBe(false)
  })

  it('guards service_kind and billing_type as closed enums', () => {
    expect(SERVICE_KINDS).toContain('troubleshoot')
    expect(isServiceKind('repair')).toBe(true)
    expect(isServiceKind('frobnicate')).toBe(false)
    expect(BILLING_TYPES).toEqual(['fixed_bid', 'NTE', 'TM'])
    expect(isBillingType('NTE')).toBe(true)
    expect(isBillingType('hourly')).toBe(false)
  })
})

describe('draft factory', () => {
  it('builds a minimal one-scope draft with linear revision defaults', () => {
    const d = makeDraft({ draft_id: 'd1', estimator_ref: 'est-1' })
    expect(d.status).toBe('draft')
    expect(d.revisions).toHaveLength(1)
    expect(d.selected_revision_id).toBe(d.revisions[0]!.revision_id)
    expect(d.revisions[0]!.rev_number).toBe(1)
    expect(d.revisions[0]!.scopes).toEqual([])
  })
})
