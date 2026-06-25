import { describe, it, expect } from 'vitest'
import fixture from './fixtures/stack-phx02a-breakers.json'
import type { ExtractionArtifact } from '../src/extraction/types'

describe('extraction contract', () => {
  it('the STACK fixture conforms to ExtractionArtifact', () => {
    const a = fixture as ExtractionArtifact
    expect(a.apparatus.length).toBeGreaterThan(0)
    const first = a.apparatus[0]!
    expect(typeof first.raw).toBe('string')
    expect(typeof first.sheet).toBe('string')
    expect(first.bbox).toHaveLength(4)
    expect(['one-line', 'panel-schedule', 'switchgear-schedule', 'power-plan']).toContain(first.evidence)
  })
})
