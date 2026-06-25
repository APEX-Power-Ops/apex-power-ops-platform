import { describe, expect, it } from 'vitest'
import { buildNativeEnvelope, EQUIPMENT_MODELS_SEED, createDefaultCatalogResolver } from '../index'
import { computeContentHash } from '../compile/content-hash'

const REF = EQUIPMENT_MODELS_SEED.find((m) => m.lifecycle_status === 'active' && m.ref_hours.ATS != null)!.ref

describe('buildNativeEnvelope', () => {
  it('produces a native, reconciling envelope with non-zero bid', () => {
    const { envelope, findings } = buildNativeEnvelope({
      projectNumber: 'DEMO-NATIVE-001',
      scopes: [{ name: 'Scope A', netaStandard: 'ATS', lines: [{ ref: REF, qty: 3, description: 'CB' }] }],
    })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(envelope.source_kind).toBe('native')
    expect(envelope.project_number).toBe('DEMO-NATIVE-001')
    expect(envelope.quote_version).toBe(1)
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
    const scope = envelope.scopes[0]!
    expect(scope.replication_m4).toBe(1)
    expect(envelope.content_hash).toBe(computeContentHash(envelope))
    expect(scope.lines[0]!.description).toBe('CB')
  })

  it('default resolver resolves the seed refs', () => {
    expect(createDefaultCatalogResolver().tryResolve(REF)?.ref).toBeTruthy()
  })
})
