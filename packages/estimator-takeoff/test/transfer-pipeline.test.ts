import { describe, it, expect } from 'vitest'
import { runTakeoff } from '../src/emit/emit'
import { reconcile, renderReportText } from '../src/runner/report'
import type { ExtractionArtifact, ExtractedApparatus } from '../src/extraction/types'

type Row = { raw: string; tag?: string; busVoltageV?: number; candidateKind?: ExtractedApparatus['candidateKind'] }
const art = (rows: Row[]): ExtractionArtifact => ({
  pdf: 'test.pdf',
  apparatus: rows.map((r) => ({
    raw: r.raw, tag: r.tag, sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1],
    evidence: 'one-line', busVoltageV: r.busVoltageV, candidateKind: r.candidateKind,
  })),
})

describe('transfer-switch pipeline (crux cases)', () => {
  // crux #1: tagged ATS-1 -> transfer scope_pending (automatic, default IR/DLRO)
  it('#1 a tagged ATS-1 -> transfer scope_pending (automatic, default IR/DLRO), carried into the report', () => {
    const a = art([{ raw: 'ATS-1', tag: 'ATS-1' }])
    const res = runTakeoff(a)
    expect(res.scopePendingLines?.length).toBe(1)
    const sp = res.scopePendingLines![0]!
    expect(sp.automationClass).toBe('automatic')
    expect(sp.provisionalDefaultRef).toBe('Automatic Transfer Switch - (IR/DLRO)')
    expect(sp.candidateRefs).toContain('Automatic Transfer Switch - (IR/DLRO)')
    // report projection carries automationClass/bypassIsolation
    const report = reconcile(a, res)
    expect(report.scopePending[0]!.automationClass).toBe('automatic')
    expect(renderReportText(report)).toContain('automation=automatic')
    // CORE CONTRACT: transfer switches never auto-price -> partial preview, unresolved row.
    expect(report.status).toBe('partial_preview')
    expect(report.counts.unresolved_rows).toBeGreaterThan(0)
    expect(res.matchedLines.length).toBe(0)
  })

  // crux #2: tagged MTS-2 -> manual
  it('#2 a tagged MTS-2 -> transfer scope_pending (manual, default Manual IR/DLRO)', () => {
    const res = runTakeoff(art([{ raw: 'MTS-2', tag: 'MTS-2' }]))
    const sp = res.scopePendingLines![0]!
    expect(sp.automationClass).toBe('manual')
    expect(sp.provisionalDefaultRef).toBe('Manual Transfer Switch - (IR/DLRO)')
  })

  // crux #3: tagged ATS + bypass -> Iso-Bypass default
  it('#3 a tagged ATS-3 Iso Bypass -> Iso-Bypass default ref', () => {
    const a = art([{ raw: 'ATS-3 Iso Bypass', tag: 'ATS-3' }])
    const res = runTakeoff(a)
    const sp = res.scopePendingLines![0]!
    expect(sp.automationClass).toBe('automatic')
    expect(sp.bypassIsolation).toBe(true)
    expect(sp.provisionalDefaultRef).toBe('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')
    const report = reconcile(a, res)
    expect(report.scopePending[0]!.bypassIsolation).toBe(true)
    expect(renderReportText(report)).toContain('bypassIso=true')
  })

  // crux #4: bare "transfer switch" tagged -> unknown group, no default
  it('#4 a tagged bare "Transfer Switch" -> unknown group, NO provisional default', () => {
    const res = runTakeoff(art([{ raw: 'Transfer Switch', tag: 'TS-4' }]))
    const sp = res.scopePendingLines![0]!
    expect(sp.automationClass).toBe('unknown')
    expect(sp.provisionalDefaultRef).toBeUndefined()
    expect(sp.candidateRefs.length).toBeGreaterThan(1)   // the unknown group (both ATS + MTS refs)
  })

  // crux #5-#6 (gap side): MTS + bypass -> transfer_catalog_gap; STS-1 -> gap
  it('#5 a tagged MTS-5 Iso Bypass -> transfer_catalog_gap (no scope_pending line)', () => {
    const res = runTakeoff(art([{ raw: 'MTS-5 Iso Bypass', tag: 'MTS-5' }]))
    expect(res.findings.some((f) => f.code === 'transfer_catalog_gap')).toBe(true)
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
  })
  it('#6 a tagged STS-1 (static) -> transfer_catalog_gap (no scope_pending line)', () => {
    const res = runTakeoff(art([{ raw: 'STS-1', tag: 'STS-1' }]))
    expect(res.findings.some((f) => f.code === 'transfer_catalog_gap')).toBe(true)
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
  })

  // crux #7 / spec must-pin #5: a UPS main carrying a frame/trip -> non_breaker_carries_rating, UNCHANGED.
  it('#7 a UPS-1-MIB 1600AF/1600AT main -> non_breaker_carries_rating (UNCHANGED, NOT claimed by transfer, NOT priced)', () => {
    const res = runTakeoff(art([{ raw: 'UPS-1-MIB 1600AF/1600AT', tag: 'UPS-1' }]))
    expect(res.matchedLines.length).toBe(0)
    expect(res.scopePendingLines?.length ?? 0).toBe(0)
    const disp = res.dispositions[0]!
    expect(disp.reasonCode).toBe('non_breaker_carries_rating')
  })

  // crux #10 (cross-family byte-identical): ATS-1 500kVA tagged -> transfer scope_pending, NOT transformer.
  it('#8 a tagged ATS-1 500kVA -> transfer scope_pending (automatic), NOT transformer', () => {
    const res = runTakeoff(art([{ raw: 'ATS-1 500kVA', tag: 'ATS-1' }]))
    expect(res.scopePendingLines?.length).toBe(1)
    const sp = res.scopePendingLines![0]!
    expect(sp.automationClass).toBe('automatic')
    // NOT a transformer: no transformer scope_pending / transformer disposition
    expect(res.dispositions[0]!.reasonCode).toBe('transfer_scope_pending')
  })

  // crux #10 (gfp-tagged tail): a tagged ATS-1 GROUND FAULT PROTECTION with candidateKind:'gfp' carrying a rating
  // -> stays on the NON_BREAKER tail as non_breaker_carries_rating (parent-excluded; NOT claimed by transfer;
  // NOT a priced GFP line). NON-VACUOUS: assert the exact reasonCode (the coarse "not a priced GFP line" passes
  // on the old path too, so we pin the precise tail code).
  it('#10 a candidateKind:gfp ATS-1 ... GROUND FAULT PROTECTION 800AF/800AT -> non_breaker_carries_rating (tail, NOT transfer, NOT GFP)', () => {
    const res = runTakeoff(art([{ raw: 'ATS-1 GROUND FAULT PROTECTION 800AF/800AT', tag: 'ATS-1', candidateKind: 'gfp' }]))
    expect(res.scopePendingLines?.length ?? 0).toBe(0)   // NOT a transfer scope_pending, NOT a priced GFP line
    expect(res.matchedLines.length).toBe(0)
    const disp = res.dispositions[0]!
    expect(disp.reasonCode).toBe('non_breaker_carries_rating')   // non-vacuous: exact tail reasonCode
  })

  // crux #14 (producer hard-win): candidateKind:'transfer_switch' on a raw ALSO containing a relay device noun
  // -> transfer family (the top-of-assessCore short-circuit beats looksLikeRelay).
  it('#14 candidateKind:transfer_switch wins over relay wording in the raw -> transfer scope_pending', () => {
    const res = runTakeoff(art([{ raw: 'protective relay SEL-751', tag: 'TS-14', candidateKind: 'transfer_switch' }]))
    expect(res.scopePendingLines?.length).toBe(1)
    expect(res.dispositions[0]!.reasonCode).toBe('transfer_scope_pending')
  })
})
