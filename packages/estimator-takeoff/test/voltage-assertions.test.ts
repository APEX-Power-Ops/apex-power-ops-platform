import { describe, it, expect } from 'vitest'
import { applyVoltageAssertions } from '../src/signature/voltage-assertions'
import type { ExtractionArtifact, ExtractedApparatus } from '../src/extraction/types'

const dev = (tag: string, busVoltageV?: number): ExtractedApparatus => ({
  raw: `${tag} 4000AF/4000AT LSIG`, tag, sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1],
  evidence: 'one-line', block: 'P1-110', busVoltageV,
})
const art = (apparatus: ExtractedApparatus[], voltageAssertions?: ExtractionArtifact['voltageAssertions']): ExtractionArtifact =>
  ({ pdf: 'x', apparatus, voltageAssertions })

describe('applyVoltageAssertions', () => {
  it('no assertions → passthrough with recomputed basis (back-compat)', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A', 480), dev('B')]))
    expect(findings).toEqual([])
    expect(resolved.map((r) => r.voltageBasis)).toEqual(['detected', 'none'])
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('applies an asserted voltage and labels basis asserted', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: ['A'], source: 'cli' }]))
    expect(findings).toEqual([])
    expect(resolved[0]!.voltageBasis).toBe('asserted')
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('unknown tag → error finding, no device touched', () => {
    const { findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: ['NOPE'], source: 'cli' }]))
    expect(findings).toHaveLength(1)
    expect(findings[0]!.code).toBe('voltage_assertion_unknown_tag')
    expect(findings[0]!.severity).toBe('error')
  })

  it('duplicate tag → error finding and the device is tainted (basis none, voltage cleared)', () => {
    const { resolved, findings } = applyVoltageAssertions(
      art([dev('A')], [{ voltageV: 480, tags: ['A'] }, { voltageV: 208, tags: ['A'] }]),
    )
    expect(findings.some((f) => f.code === 'voltage_assertion_duplicate_tag' && f.severity === 'error')).toBe(true)
    expect(resolved[0]!.voltageBasis).toBe('none')
    expect(resolved[0]!.apparatus.busVoltageV).toBeUndefined()
  })

  it('duplicate tag WITH a detected voltage is still tainted (no detected fallback)', () => {
    const { resolved } = applyVoltageAssertions(
      art([dev('A', 480)], [{ voltageV: 480, tags: ['A'] }, { voltageV: 480, tags: ['A'] }]),
    )
    expect(resolved[0]!.voltageBasis).toBe('none')              // NOT 'detected'
    expect(resolved[0]!.apparatus.busVoltageV).toBeUndefined()  // detected 480 cleared
  })

  it('invalid voltages (0, -1, 12.5, NaN) → error finding + taint', () => {
    for (const bad of [0, -1, 12.5, NaN]) {
      const { resolved, findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: bad, tags: ['A'] }]))
      expect(findings.some((f) => f.code === 'voltage_assertion_invalid_voltage' && f.severity === 'error')).toBe(true)
      expect(resolved[0]!.voltageBasis).toBe('none')
    }
  })

  it('conflict (detected != asserted) → warning, operator wins, device keeps asserted voltage', () => {
    const { resolved, findings } = applyVoltageAssertions(art([dev('A', 240)], [{ voltageV: 480, tags: ['A'], actor: 'jls' }]))
    const conflict = findings.find((f) => f.code === 'voltage_assertion_conflict')!
    expect(conflict.severity).toBe('warning')
    expect(conflict.detail).toMatchObject({ tag: 'A', detectedV: 240, assertedV: 480, actor: 'jls' })
    expect(resolved[0]!.voltageBasis).toBe('asserted')
    expect(resolved[0]!.apparatus.busVoltageV).toBe(480)
  })

  it('agreeing detected + asserted → no conflict finding', () => {
    const { findings } = applyVoltageAssertions(art([dev('A', 480)], [{ voltageV: 480, tags: ['A'] }]))
    expect(findings).toEqual([])
  })

  it('per-tag: two tags asserted at different voltages each keep their own voltage', () => {
    const { resolved } = applyVoltageAssertions(
      art([dev('A'), dev('B')], [{ voltageV: 480, tags: ['A'] }, { voltageV: 208, tags: ['B'] }]),
    )
    expect(resolved.find((r) => r.apparatus.tag === 'A')!.apparatus.busVoltageV).toBe(480)
    expect(resolved.find((r) => r.apparatus.tag === 'B')!.apparatus.busVoltageV).toBe(208)
  })

  it('provenance is non-forgeable: a stray voltageBasis on the artifact JSON is ignored', () => {
    const sneaky = { ...dev('A', 480), voltageBasis: 'asserted' } as unknown as ExtractedApparatus
    const { resolved } = applyVoltageAssertions(art([sneaky]))     // NO real assertion
    expect(resolved[0]!.voltageBasis).toBe('detected')             // recomputed, never 'asserted'
  })

  it('non-array voltageAssertions → invalid_shape error, nothing applied (no throw)', () => {
    const bad = { pdf: 'x', apparatus: [dev('A', 480)], voltageAssertions: {} } as unknown as ExtractionArtifact
    const { resolved, findings } = applyVoltageAssertions(bad)
    expect(findings.some((f) => f.code === 'voltage_assertion_invalid_shape' && f.severity === 'error')).toBe(true)
    expect(resolved[0]!.voltageBasis).toBe('detected')            // device untouched
  })

  it('assertion missing tags → invalid_shape error', () => {
    const bad = { pdf: 'x', apparatus: [dev('A')], voltageAssertions: [{ voltageV: 480 }] } as unknown as ExtractionArtifact
    expect(applyVoltageAssertions(bad).findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })

  it('assertion with non-array tags → invalid_shape error', () => {
    const bad = { pdf: 'x', apparatus: [dev('A')], voltageAssertions: [{ voltageV: 480, tags: 'A' }] } as unknown as ExtractionArtifact
    expect(applyVoltageAssertions(bad).findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })

  it('assertion with empty tags → invalid_shape error', () => {
    const { findings } = applyVoltageAssertions(art([dev('A')], [{ voltageV: 480, tags: [] }]))
    expect(findings.some((f) => f.code === 'voltage_assertion_invalid_shape')).toBe(true)
  })
})

import { runTakeoff } from '../src/emit/emit'

describe('runTakeoff threads voltage assertions + findings', () => {
  const breaker = (tag: string, busVoltageV?: number): ExtractedApparatus => ({
    raw: `${tag} 4000AF/4000AT LSIG`, tag, sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1],
    evidence: 'one-line', block: 'P1-110', busVoltageV,
  })

  it('asserted voltage produces a matched line with voltageBasis asserted', () => {
    const r = runTakeoff({ pdf: 'x', apparatus: [breaker('M1-GB')], voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'], source: 'cli' }] })
    expect(r.findings).toEqual([])
    expect(r.matchedLines).toHaveLength(1)
    expect(r.matchedLines[0]!.voltageBasis).toBe('asserted')
  })

  it('an unknown-tag assertion surfaces an error finding even when another line matches', () => {
    const r = runTakeoff({
      pdf: 'x', apparatus: [breaker('M1-GB')],
      voltageAssertions: [{ voltageV: 480, tags: ['M1-GB'] }, { voltageV: 480, tags: ['GHOST'] }],
    })
    expect(r.matchedLines.length).toBeGreaterThan(0)
    expect(r.findings.some((f) => f.code === 'voltage_assertion_unknown_tag' && f.severity === 'error')).toBe(true)
  })

  it('non-forgeable end to end: stray voltageBasis on JSON does not yield asserted', () => {
    const sneaky = { ...breaker('M1-GB', 480), voltageBasis: 'asserted' } as unknown as ExtractedApparatus
    const r = runTakeoff({ pdf: 'x', apparatus: [sneaky] })   // no assertion
    expect(r.matchedLines[0]!.voltageBasis).toBe('detected')
  })
})
