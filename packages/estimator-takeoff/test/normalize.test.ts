import { describe, it, expect } from 'vitest'
import { normalizeApparatus, assessApparatus, assessResolvedApparatus } from '../src/signature/normalize'
import type { BreakerSignature } from '../src/signature/types'
import type { ExtractedApparatus } from '../src/extraction/types'

const mk = (raw: string, v?: number): ExtractedApparatus => ({
  raw, tag: 'X', sheet: 'E01-11', page: 11, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: v,
})

// Narrow to BreakerSignature — only call when the apparatus is known to be a breaker.
function asBreaker(s: ReturnType<typeof normalizeApparatus>): BreakerSignature {
  if (!s || s.kind !== 'breaker') throw new Error(`expected BreakerSignature, got ${s?.kind ?? 'null'}`)
  return s
}

describe('normalizeApparatus — parse', () => {
  it('parses frame/trip and LSIG functions on a 480V breaker', () => {
    const s = asBreaker(normalizeApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)))
    expect(s.voltageClass).toBe('LV'); expect(s.frameA).toBe(4000); expect(s.tripA).toBe(4000)
    expect(s.functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('parses LSIGE (trailing E ground-fault sensing -> G)', () => {
    expect(asBreaker(normalizeApparatus(mk('ACC-1-09-FB 800AF/800AT LSIGE', 480))).functions).toEqual(['L', 'S', 'I', 'G'])
  })
  it('parses a 5-digit frame without truncation', () => {
    const s = asBreaker(normalizeApparatus(mk('TIE-FB 10000AF/8000AT LSIG', 480)))
    expect(s.frameA).toBe(10000); expect(s.tripA).toBe(8000)
  })
  it('treats a frame-only label (no GB/FB tag) as a breaker', () => {
    expect(normalizeApparatus(mk('MAIN 4000AF/4000AT LSIG', 480))).not.toBeNull()
  })
  it('returns null for a non-breaker/non-transformer label (ATS without kVA rating)', () => {
    expect(normalizeApparatus(mk('ATS-1 1000A', 480))).toBeNull()  // ATS still in NON_BREAKER; no kVA/device-token
  })
  it('classifies an MV vacuum breaker', () => {
    const s = asBreaker(normalizeApparatus(mk('MV-SWGR-1 VACUUM 1200A', 13800)))
    expect(s.voltageClass).toBe('MV'); expect(s.mvType).toBe('vacuum')
  })
})

describe('normalizeApparatus — trip functions are text-only (no fabrication)', () => {
  it('does not fabricate G from "GE"', () => {
    const s = asBreaker(normalizeApparatus(mk('ACME-FB GE 800AF/800AT', 480)))
    expect(s.functions).toEqual([]); expect(s.mounting).toBe('unknown'); expect(s.mountingBasis).toBe('none')
  })
  it('does not fabricate functions from "SE"', () => {
    expect(asBreaker(normalizeApparatus(mk('PNL-SE 600AF/600AT', 480))).functions).toEqual([])
  })
  it('does not synthesize a function from a lone "L" token', () => {
    expect(asBreaker(normalizeApparatus(mk('PNL-FB 800AF/800AT L PHASE', 480))).functions).toEqual([])
  })
})

describe('normalizeApparatus — construction (mounting) + provenance', () => {
  it('uses an explicit mountingHint first (basis = hint)', () => {
    const s = asBreaker(normalizeApparatus({ ...mk('HF-P1-110-01-FB 400AF/300AT LSI', 480), mountingHint: 'insulated_case' }))
    expect(s.mounting).toBe('insulated_case'); expect(s.mountingBasis).toBe('hint')
  })
  it('reads molded_case from MCCB (basis = text)', () => {
    const s = asBreaker(normalizeApparatus(mk('PNL-1 MCCB 250AF/250AT', 480)))
    expect(s.mounting).toBe('molded_case'); expect(s.mountingBasis).toBe('text')
  })
  it('reads panelboard from MCB (basis = text)', () => {
    expect(asBreaker(normalizeApparatus(mk('LP-1 MCB 100AF/20AT', 480))).mounting).toBe('panelboard')
  })
  it('applies the >=800AF+G estimating baseline (basis = estimating_baseline)', () => {
    const s = asBreaker(normalizeApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)))
    expect(s.mounting).toBe('draw_out'); expect(s.mountingBasis).toBe('estimating_baseline')
  })
  it('stays unknown (fail-closed) for a 400AF LSI breaker with no evidence', () => {
    const s = asBreaker(normalizeApparatus(mk('HF-P1-110-01-FB 400AF/300AT LSI', 480)))
    expect(s.mounting).toBe('unknown'); expect(s.mountingBasis).toBe('none')
  })
  it('does NOT apply the baseline for a large frame without ground-fault (LS/LSI)', () => {
    expect(asBreaker(normalizeApparatus(mk('BIG-FB 1600AF/1600AT LSI', 480))).mounting).toBe('unknown')
  })
  it('does not treat an incidental "DO"/"EO" token as real construction', () => {
    expect(asBreaker(normalizeApparatus(mk('PANEL-DO-3 200AF/200AT LSI', 480))).mounting).toBe('unknown')
  })
})

describe('assessApparatus — first-class questions / non-breaker handling', () => {
  it('surfaces a breaker-shaped row with no voltage as a question (not a silent drop)', () => {
    const a = assessApparatus(mk('MSB-GB 4000AF/4000AT LSIG'))
    expect(a.signature).toBeNull(); expect(a.isBreakerShaped).toBe(true); expect(a.questions).toHaveLength(1)
  })
  it('does not classify a NON-breaker that carries a frame/trip; raises a question instead', () => {
    const a = assessApparatus(mk('MTS-2 800AF/800AT LSIG', 480))
    expect(a.signature).toBeNull(); expect(a.isBreakerShaped).toBe(false)
    expect(a.questions.length).toBeGreaterThan(0)
  })
  it('flags a mountingHint that conflicts with the label text (hint still wins)', () => {
    const a = assessApparatus({ ...mk('PNL-1 MCCB 250AF/250AT', 480), mountingHint: 'draw_out' })
    const bsig = a.signature
    if (!bsig || bsig.kind !== 'breaker') throw new Error('expected breaker signature')
    expect(bsig.mounting).toBe('draw_out'); expect(bsig.mountingBasis).toBe('hint')
    expect(a.questions.some((qq) => /conflict/i.test(qq.question))).toBe(true)
  })
  it('does not question a clean device', () => {
    expect(assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)).questions).toEqual([])
  })
  it('surfaces an exotic-suffix breaker candidate (no GB/FB hint, no AF/AT, no voltage) via candidateKind', () => {
    const a = assessApparatus({
      raw: 'DH110-UB', tag: 'DH110-UB', sheet: 'E01-30', page: 18, bbox: [1200, 800, 1280, 812],
      evidence: 'one-line', candidateKind: 'breaker',
    })
    expect(a.isBreakerShaped).toBe(true)
    expect(a.signature).toBeNull()                 // no voltage → not classifiable
    expect(a.questions.length).toBeGreaterThan(0)  // surfaced, not dropped
  })
  it('without candidateKind, the same exotic-suffix row is not breaker-shaped (drops, pre-fix behavior)', () => {
    const a = assessApparatus({ raw: 'DH110-UB', tag: 'DH110-UB', sheet: 'E01-30', page: 18, bbox: [0, 0, 1, 1], evidence: 'one-line' })
    expect(a.isBreakerShaped).toBe(false)
  })
  it('excludes a static transfer switch (STS) carrying a frame/trip as a non-breaker (aligns the producer profile)', () => {
    const a = assessApparatus(mk('STS-1 800AF/800AT LSIG', 480))
    expect(a.signature).toBeNull(); expect(a.isBreakerShaped).toBe(false)
    expect(a.questions.length).toBeGreaterThan(0)   // surfaced for device-type confirmation, never priced
  })
})

describe('assessApparatus — voltage provenance (voltageBasis)', () => {
  it('labels asserted when the controlled basis arg says so', () => {
    const a = assessResolvedApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480), 'asserted')
    expect(a.signature!.voltageBasis).toBe('asserted')
  })
  it('derives detected from busVoltageV when no basis arg is given', () => {
    expect(assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)).signature!.voltageBasis).toBe('detected')
  })
  it('never yields asserted from a raw apparatus call (no basis arg)', () => {
    expect(assessApparatus(mk('MSB-P1-110-GB 4000AF/4000AT LSIG', 480)).signature!.voltageBasis).not.toBe('asserted')
  })
  it('public assessApparatus does not accept a basis arg (forgery prevented at the type level)', () => {
    // @ts-expect-error - assessApparatus is one-arg; 'asserted' can only come via assessResolvedApparatus (engine path)
    assessApparatus(mk('GUARD 4000AF/4000AT LSIG', 480), 'asserted')
    expect(true).toBe(true)
  })
})

it('every operator question carries a structured code', () => {
  const a = assessApparatus({ raw: 'breaker', sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' })
  expect(a.questions.length).toBeGreaterThan(0)
  expect(a.questions[0]!.code).toBe('missing_voltage')
})

it('sets a structured assessmentCode distinguishing the null-signature shapes', () => {
  const at = (raw: string, extra: any = {}) => assessApparatus({ raw, sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...extra })
  expect(at('MSB 4000AF/4000AT LSIG', { busVoltageV: 480, mountingHint: 'draw_out' }).assessmentCode).toBe('classified')
  expect(at('XFMR 1000KVA').assessmentCode).toBe('missing_voltage')      // transformer recognized (XFMR token), no bus voltage
  expect(at('PDU 1000A').assessmentCode).toBe('non_breaker_excluded')     // PDU stays in NON_BREAKER
  expect(at('SPARE').assessmentCode).toBe('unrecognized_apparatus_row')
  expect(at('MCB 100AF/100AT').assessmentCode).toBe('missing_voltage')
  expect(at('ATS 800AF/800AT').assessmentCode).toBe('non_breaker_carries_rating')
})
