import { describe, it, expect } from 'vitest'
import { quantify } from '../src/quantify/quantify'
import { runTakeoff } from '../src/emit/emit'
import type { ApparatusSignature, BreakerSignature, TransformerSignature } from '../src/signature/types'
import type { ExtractionArtifact } from '../src/extraction/types'

// ---------------------------------------------------------------------------
// FIX Y: cross-family same-tag bucketing -- kind must be in deviceId
// ---------------------------------------------------------------------------
describe('FIX Y: cross-family same-tag deviceId isolation', () => {
  // Build raw signatures that quantify() will consume (inputIndex pre-stamped)
  const breakerSig: BreakerSignature = {
    kind: 'breaker',
    tag: 'T-1',
    voltageClass: 'LV',
    voltageV: 480,
    voltageBasis: 'detected',
    mounting: 'draw_out',
    mountingBasis: 'hint',
    frameA: 4000,
    tripA: 4000,
    functions: ['L', 'S', 'I', 'G'],
    inputIndex: 0,
    source: { sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', block: 'P1-110' },
  }
  const transformerSig: TransformerSignature = {
    kind: 'transformer',
    tag: 'T-1',
    voltageClass: 'LV',
    voltageV: 480,
    voltageBasis: 'detected',
    coolant: 'dry',
    kvaRating: 1500,
    inputIndex: 1,
    source: { sheet: 'E01-11', page: 1, bbox: [2, 2, 3, 3], evidence: 'one-line', block: 'XFMR-PAD' },
  }

  it('two devices sharing tag T-1 but different kinds produce TWO distinct lines', () => {
    const { lines } = quantify([breakerSig, transformerSig] as ApparatusSignature[])
    expect(lines).toHaveLength(2)
  })

  it('one line is breaker-kind, one is transformer-kind -- no cross-family folding', () => {
    const { lines } = quantify([breakerSig, transformerSig] as ApparatusSignature[])
    const kinds = lines.map((l) => l.signature.kind).sort()
    expect(kinds).toEqual(['breaker', 'transformer'])
  })

  it('each line has qty 1 (the same-tag device is NOT folded via associated_source)', () => {
    const { lines } = quantify([breakerSig, transformerSig] as ApparatusSignature[])
    expect(lines.every((l) => l.qty === 1)).toBe(true)
  })
})

// End-to-end via runTakeoff: one breaker T-1 matched, one transformer T-1 scope_pending
// Both must survive -- neither folded into the other's line.
describe('FIX Y: runTakeoff -- same-tag breaker+transformer produce independent dispositions', () => {
  const art: ExtractionArtifact = {
    pdf: 'x.pdf',
    apparatus: [
      // Breaker T-1: rated, draw-out, 480V on one-line -> matched
      { raw: 'T-1 4000AF/4000AT LSIG', tag: 'T-1', sheet: 'E01-11', page: 1,
        bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'P1-110', mountingHint: 'draw_out' },
      // Transformer T-1: dry-type 1500kVA 480V on one-line -> scope_pending
      { raw: 'T-1 1500KVA 480V DRY-TYPE XFMR', tag: 'T-1', sheet: 'E01-11', page: 1,
        bbox: [2, 2, 3, 3], evidence: 'one-line', busVoltageV: 480, block: 'XFMR-PAD' },
    ],
  }

  const r = runTakeoff(art)

  it('breaker T-1 produces a matched line', () => {
    expect(r.matchedLines).toHaveLength(1)
  })

  it('transformer T-1 produces a scope_pending line', () => {
    expect(r.scopePendingLines ?? []).toHaveLength(1)
  })

  it('both dispositions survive: matched + scope_pending (no cross-family loss)', () => {
    const statuses = r.dispositions.map((d) => d.status).sort()
    expect(statuses).toContain('matched')
    expect(statuses).toContain('scope_pending')
  })

  it('neither disposition is associated_source (no folding)', () => {
    expect(r.dispositions.every((d) => d.status !== 'associated_source')).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// FIX Z: inverse cross-family attach -- a breaker row must NOT attach to a transformer line
// ---------------------------------------------------------------------------
describe('FIX Z: breaker missing-voltage row does NOT attach to transformer line sharing its tag', () => {
  const art: ExtractionArtifact = {
    pdf: 'x.pdf',
    apparatus: [
      // Transformer T-1 on one-line (authoritative) with voltage -> scope_pending
      { raw: 'T-1 1500KVA 480V DRY-TYPE XFMR', tag: 'T-1', sheet: 'E01-11', page: 1,
        bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, block: 'XFMR-PAD' },
      // Breaker-shaped T-1 on a NON-authoritative (power-plan) sheet, missing voltage
      // This simulates the inverse-attach scenario: byTag used to include transformer lines.
      { raw: 'T-1 1500AF/1500AT LSIG', tag: 'T-1', sheet: 'E02-03D', page: 3,
        bbox: [0, 0, 1, 1], evidence: 'power-plan' },
    ],
  }

  const r = runTakeoff(art)

  it('the transformer T-1 is scope_pending (not eaten by breaker attach)', () => {
    expect(r.scopePendingLines ?? []).toHaveLength(1)
  })

  it('the breaker-shaped T-1 row on power-plan surfaces as a question (NOT associated_source of the transformer)', () => {
    // The second apparatus row (inputIndex 1) must NOT be associated_source of transformer line T-1
    const d1 = r.dispositions[1]!
    expect(d1.status).not.toBe('associated_source')
  })

  it('no disposition is associated_source (the breaker row cannot attach to a transformer line)', () => {
    expect(r.dispositions.every((d) => d.status !== 'associated_source')).toBe(true)
  })

  it('two dispositions total: scope_pending for transformer, question for breaker-shaped row', () => {
    const statuses = r.dispositions.map((d) => d.status).sort()
    // transformer -> scope_pending; breaker-shaped missing-voltage -> question (missing_voltage)
    expect(statuses).toContain('scope_pending')
    expect(statuses).toContain('question')
  })
})
