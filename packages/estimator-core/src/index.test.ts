import { describe, expect, it } from 'vitest'
import {
  BASELINE_RATE_CARD,
  compile,
  computeContentHash,
  createCatalogResolver,
  LINE_KINDS,
  makeDraft,
  SCHEMA_VERSION,
  validateEnvelope,
} from './index'

describe('public API surface', () => {
  it('re-exports the contract surface', () => {
    expect(typeof compile).toBe('function')
    expect(typeof createCatalogResolver).toBe('function')
    expect(typeof computeContentHash).toBe('function')
    expect(typeof validateEnvelope).toBe('function')
    expect(typeof makeDraft).toBe('function')
    expect(SCHEMA_VERSION).toBe('estimate_envelope_v1')
    expect(LINE_KINDS).toContain('service')
    expect(BASELINE_RATE_CARD.version).toBe('2026-01-23')
  })
})
