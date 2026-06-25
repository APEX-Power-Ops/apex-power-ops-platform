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
    expect(r.operatorQuestions.length).toBeGreaterThan(0)       // every breaker surfaced as a question (no silent drop)
    expect(() => emitEnvelope(r, { projectNumber: 'GOLDEN' })).toThrow(/zero matched lines/)  // fail-closed
  })

  it('e01_11_with_operator_voltage_assertion_emits_drawout_lsig', () => {
    // Operator Gate-1 voltage assertion — the one fact the extractor refused to guess. Clearly labeled as
    // operator-supplied, NOT auto-extracted. V1 demonstration asserts the dominant 480V main bus; per-device
    // voltage association is a later slice. The CLI override (--assert-voltage) is the next slice.
    const asserted: ExtractionArtifact = {
      ...fixture,
      apparatus: fixture.apparatus.map((a) => ({ ...a, busVoltageV: 480 })),
    }
    const r = runTakeoff(asserted)
    expect(r.matchedLines.length).toBeGreaterThan(0)
    expect(r.matchedLines.some((m) => m.ref === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)
    const { envelope, findings } = emitEnvelope(r, { projectNumber: 'GOLDEN' })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])   // emits with no error findings
    expect(envelope.scopes.length).toBeGreaterThan(0)
  })
})
