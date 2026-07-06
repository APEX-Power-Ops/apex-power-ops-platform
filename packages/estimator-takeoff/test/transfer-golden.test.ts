import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { runTakeoff } from '../src/emit/emit'
import { runFromArtifact } from '../src/runner/run'
import type { ExtractionArtifact } from '../src/extraction/types'

// ---------------------------------------------------------------------------
// D4 re-baseline accounting (documented before/after for Task 5)
// ---------------------------------------------------------------------------
// The ONLY intentional deltas from the transfer-switch family admission are the
// TAGGED transfer rows. On the E01-11 real artifact:
//
//   BEFORE (six-family main):  the 8 `STS-P1-110-##(A|P) 1200AF/1200AT LSI`
//                              rows were `non_breaker_carries_rating` (the
//                              NON_BREAKER tail claimed them).
//   AFTER  (transfer family):  the same 8 rows are `transfer_parent_conflict`
//                              (a TAGGED `\bSTS\b` transfer anchor carrying an
//                              LSI trip -> T1-B conflict guard fires). Still an
//                              unpriced operator question -> bid + question count
//                              are UNCHANGED.
//
// EXPLICITLY NOT re-baselined (must stay byte-identical):
//   * `STSDP-P1-110-MCB 3000AF/3000AT LSIG` - the `STSDP` prefix has NO word
//     boundary before `DP`, so it is NOT a `\bSTS\b` transfer anchor. It stays a
//     breaker-shaped `missing_voltage` question (no voltage assertion for it),
//     exactly as on main. It is a breaker, NOT a transfer row.
//   * the 5 `UPS-*` rows stay `non_breaker_carries_rating` (NON_BREAKER tail).
//   * every non-transfer row (mains, all other breakers, warnings) unchanged.
//
// Net on the priced envelope: `bid_cents` 198000, `operator_questions` 39, and
// `findings` 0 are IDENTICAL before and after (a conflict question is still an
// unpriced question). The E01-11 PIN below makes that a TEST, not an eyeball.
// ---------------------------------------------------------------------------

const golden: ExtractionArtifact = {
  pdf: 'test.pdf',
  apparatus: [
    // ATS-1: clean automatic transfer -> scope_pending (default IR/DLRO)
    { raw: 'ATS-1', tag: 'ATS-1', sheet: 'E-1', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
    // ATS-2 Iso Bypass: automatic + bypass -> Iso-Bypass default
    { raw: 'ATS-2 Iso Bypass', tag: 'ATS-2', sheet: 'E-1', page: 1, bbox: [1, 0, 2, 1], evidence: 'one-line' },
    // MTS-3: manual transfer -> scope_pending (Manual IR/DLRO)
    { raw: 'MTS-3', tag: 'MTS-3', sheet: 'E-1', page: 1, bbox: [2, 0, 3, 1], evidence: 'one-line' },
    // STS-4: static transfer -> transfer_catalog_gap (no V1 priced ref)
    { raw: 'STS-4', tag: 'STS-4', sheet: 'E-1', page: 1, bbox: [3, 0, 4, 1], evidence: 'one-line' },
    // Main-Tie-Main: a pair of REAL draw-out breakers -> priced (byte-identical breaker path)
    { raw: 'MAIN 4000AF/4000AT LSIG', tag: 'MAIN-1', sheet: 'E-1', page: 1, bbox: [4, 0, 5, 1], evidence: 'one-line', busVoltageV: 480, mountingHint: 'draw_out' },
    { raw: 'TIE 4000AF/4000AT LSIG', tag: 'TIE-1', sheet: 'E-1', page: 1, bbox: [5, 0, 6, 1], evidence: 'one-line', busVoltageV: 480, mountingHint: 'draw_out' },
    // UPS-5 main carrying a frame/trip -> non_breaker_carries_rating (NON_BREAKER tail, UNCHANGED)
    { raw: 'UPS-5-MIB 1600AF/1600AT', tag: 'UPS-5', sheet: 'E-1', page: 1, bbox: [6, 0, 7, 1], evidence: 'one-line' },
  ],
}

describe('transfer golden - coexistence (all six prior families + transfer)', () => {
  it('routes every device to the right family and never auto-prices a transfer switch', () => {
    const res = runTakeoff(golden)
    const byTag = (t: string) => res.dispositions.find((d) => d.tag === t)!
    const sp = res.scopePendingLines ?? []
    const spByTag = (t: string) => sp.find((s) => s.line.signature.tag === t)

    // ATS-1 -> automatic scope_pending, default IR/DLRO
    expect(byTag('ATS-1').reasonCode).toBe('transfer_scope_pending')
    expect(spByTag('ATS-1')!.automationClass).toBe('automatic')
    expect(spByTag('ATS-1')!.provisionalDefaultRef).toBe('Automatic Transfer Switch - (IR/DLRO)')

    // ATS-2 -> Iso-Bypass default
    expect(byTag('ATS-2').reasonCode).toBe('transfer_scope_pending')
    expect(spByTag('ATS-2')!.bypassIsolation).toBe(true)
    expect(spByTag('ATS-2')!.provisionalDefaultRef).toBe('Automatic Transfer Switch - Iso Bypass (IR/DLRO)')

    // MTS-3 -> manual
    expect(byTag('MTS-3').reasonCode).toBe('transfer_scope_pending')
    expect(spByTag('MTS-3')!.automationClass).toBe('manual')
    expect(spByTag('MTS-3')!.provisionalDefaultRef).toBe('Manual Transfer Switch - (IR/DLRO)')

    // STS-4 -> catalog gap (no scope_pending line, a finding)
    expect(byTag('STS-4').reasonCode).toBe('transfer_catalog_gap')
    expect(spByTag('STS-4')).toBeUndefined()
    expect(res.findings.some((f) => f.code === 'transfer_catalog_gap')).toBe(true)

    // Main-Tie-Main -> two PRICED breaker rows (one grouped matched line, qty 2)
    expect(byTag('MAIN-1').status).toBe('matched')
    expect(byTag('TIE-1').status).toBe('matched')
    expect(res.matchedLines.length).toBe(1)
    expect(res.matchedLines[0]!.qty).toBe(2)
    expect(res.matchedLines[0]!.ref).toBe('Circuit Breaker LV - Draw-Out (LSIG)')

    // UPS-5 -> non_breaker_carries_rating (NON_BREAKER tail, NOT claimed by transfer, NOT priced)
    expect(byTag('UPS-5').reasonCode).toBe('non_breaker_carries_rating')
    expect(byTag('UPS-5').status).toBe('question')
    expect(spByTag('UPS-5')).toBeUndefined()

    // no transfer switch is ever auto-priced
    expect(res.matchedLines.every((m) => !/Transfer Switch/i.test(m.ref ?? ''))).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// Executable E01-11 re-baseline PIN: "bid + question-count unchanged" is a TEST.
// ---------------------------------------------------------------------------
const e0111 = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/stack-phx02a-e01-11.artifact.json', import.meta.url)), 'utf8'),
) as ExtractionArtifact

describe('E01-11 transfer re-baseline PIN (bid + question count unchanged)', () => {
  const out = runFromArtifact(e0111, { projectNumber: 'PHX02A-DEMO', allowOpenItems: true })
  const d = out.report!.dispositions

  it('re-baselines exactly the 8 tagged STS-P1-110 rows to transfer_parent_conflict', () => {
    const conflicts = d.filter((x) => x.reasonCode === 'transfer_parent_conflict')
    expect(conflicts.length).toBe(8)
    expect(conflicts.every((x) => /^STS-P1-110-/.test(x.tag ?? ''))).toBe(true)
  })

  it('leaves the STSDP-P1-110-MCB breaker byte-identical (NOT a transfer row, NOT re-baselined)', () => {
    const stsdp = d.find((x) => (x.tag ?? '').includes('STSDP'))!
    expect(stsdp.reasonCode).not.toBe('transfer_parent_conflict')
    expect(stsdp).toMatchObject({ status: 'question', reasonCode: 'missing_voltage' })
    expect(stsdp.raw).toMatch(/AF\/\d+AT/)   // still a breaker-shaped MCB row
  })

  it('leaves the 5 UPS-* rows as non_breaker_carries_rating (NON_BREAKER tail, unchanged)', () => {
    const ups = d.filter((x) => x.reasonCode === 'non_breaker_carries_rating')
    expect(ups.length).toBe(5)
    expect(ups.every((x) => /^UPS-/.test(x.tag ?? ''))).toBe(true)
  })

  it('holds the bid + question count + validator-clean figures verbatim', () => {
    expect(out.envelope!.totals.bid_cents).toBe(198000)
    expect(out.report!.counts.operator_questions).toBe(39)
    expect(out.findings.length).toBe(0)
    expect(out.report!.status).toBe('partial_preview')
    expect(out.report!.accounted).toBe(true)
  })
})
