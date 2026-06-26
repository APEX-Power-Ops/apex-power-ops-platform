import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

// Real extraction of E01-11 (STACK PHX02A Addendum 4) produced by `drawing-nav extract` (Plan 2b).
const fixture = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/stack-phx02a-e01-11-extract.json', import.meta.url)), 'utf8'),
) as ExtractionArtifact

describe('golden: real E01-11 (STACK PHX02A Addendum 4)', () => {
  it('e01_11_auto_multibus_surfaces_questions_no_matches', () => {
    // Pure-auto: the extractor correctly refused to broadcast a voltage on this multi-bus / MV-incoming sheet.
    expect(fixture.apparatus.every((a) => a.busVoltageV === undefined)).toBe(true)
    const r = runTakeoff(fixture)
    expect(r.matchedLines).toHaveLength(0)                       // nothing priced without voltage
    expect(r.operatorQuestions.length).toBeGreaterThanOrEqual(20)  // dozens of breaker-shaped rows each surfaced (no silent drop), not merely non-empty
    expect(() => emitEnvelope(r, { projectNumber: 'GOLDEN' })).toThrow(/zero matched lines/)  // fail-closed
  })

  it('e01_11_named_480_subset_emits_drawout_lsig (per-tag operator assertion; 208V house bus intentionally NOT asserted)', () => {
    // Operator asserts 480V for a NAMED SUBSET of confirmed-480 tags (MSB-P1-110-GB is the draw-out LSIG main).
    // The mixed-bus 208/120 house tags are deliberately left unasserted (their voltage is an unresolved operator input).
    const NAMED_480 = ['MSB-P1-110-GB', 'ACC-1-09-FB', 'ACC-1-10-FB']
    const asserted: ExtractionArtifact = {
      ...fixture,
      voltageAssertions: [{ voltageV: 480, tags: NAMED_480, source: 'cli' }],
    }
    const r = runTakeoff(asserted)
    expect(r.findings.filter((f) => f.severity === 'error')).toEqual([])      // no blocking findings
    const lsig = r.matchedLines.find((m) => m.ref === 'Circuit Breaker LV - Draw-Out (LSIG)')
    expect(lsig).toBeDefined()
    expect(lsig!.mountingBasis).toBe('estimating_baseline')                   // construction is an estimating assumption
    expect(lsig!.voltageBasis).toBe('asserted')                              // voltage is operator-supplied
    const { envelope, findings } = emitEnvelope(r, { projectNumber: 'GOLDEN' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(envelope.scopes.length).toBeGreaterThan(0)
  })
})
