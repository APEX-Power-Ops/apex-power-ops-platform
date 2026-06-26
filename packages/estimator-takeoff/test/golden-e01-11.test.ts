import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { runFromArtifact } from '../src/runner/run'
import type { ExtractionArtifact } from '../src/extraction/types'

// The canonical real artifact: drawing-nav extract of E01-11 (STACK PHX02A Addendum 4) at producer e7a3fb4,
// WITH the operator voltage assertion (480V for the 3 confirmed draw-out mains). Provenance is pinned by the
// manifest + drift-check (test/fixtures/stack-phx02a-e01-11.artifact.manifest.json).
const artifact = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/stack-phx02a-e01-11.artifact.json', import.meta.url)), 'utf8'),
) as ExtractionArtifact

describe('golden E01-11 (real artifact -> reconciled priced envelope)', () => {
  const out = runFromArtifact(artifact, { projectNumber: 'PHX02A-DEMO', allowOpenItems: true })

  it('accounts for every input row (exhaustive reconciliation)', () => {
    expect(out.report!.counts.apparatus_in).toBe(artifact.apparatus.length)
    expect(out.report!.accounted).toBe(true)
  })
  it('matches the 480V-asserted draw-out mains with a catalog ref', () => {
    const matched = out.report!.dispositions.filter((d) => d.status === 'matched')
    expect(matched.length).toBeGreaterThan(0)
    expect(matched.every((d) => !!d.ref)).toBe(true)
  })
  it('surfaces the real producer noise as unmatched/ignored/question (never silently lost)', () => {
    const c = out.report!.counts
    expect(c.unmatched_candidates + c.operator_questions + c.ignored).toBeGreaterThan(0)
  })
  it('is a partial_preview (open items present) and prices positive AND validator-clean', () => {
    expect(out.report!.status).toBe('partial_preview')
    expect(out.envelope!.totals.bid_cents).toBeGreaterThan(0)
    expect(out.findings.length).toBe(0)   // estimator-core validator findings empty -> the priced seam is clean
  })
  it('fails closed when the operator assertion is removed (no voltage -> nothing priced)', () => {
    const noAssert: ExtractionArtifact = { ...artifact, voltageAssertions: [] }
    const blocked = runFromArtifact(noAssert, { projectNumber: 'PHX02A-DEMO', allowOpenItems: true })
    expect(blocked.exitCode).not.toBe(0)        // zero matched -> hard block, even with allowOpenItems
    expect(blocked.envelope).toBeUndefined()
  })
})
