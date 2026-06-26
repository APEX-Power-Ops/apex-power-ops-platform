import { describe, it, expect } from 'vitest'
import { runFromArtifact } from '../src/runner/run'
import type { ExtractionArtifact } from '../src/extraction/types'

const row = (o: Partial<any> & { raw: string }) => ({ sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', ...o })
const art = (apparatus: any[], voltageAssertions?: any[]): ExtractionArtifact => ({ pdf: 'x.pdf', apparatus, voltageAssertions })
const matched = () => row({ raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', busVoltageV: 480, mountingHint: 'draw_out' })

describe('runFromArtifact', () => {
  it('emits a clean envelope when there are no open items', () => {
    const out = runFromArtifact(art([matched()]), { projectNumber: 'P', allowOpenItems: false })
    expect(out.exitCode).toBe(0)
    expect(out.report!.status).toBe('clean')
    expect(out.envelope).toBeDefined()
  })
  it('blocks open items without the flag (no envelope)', () => {
    const out = runFromArtifact(art([matched(), row({ raw: 'MCB 100AF/100AT', tag: 'B' })]), { projectNumber: 'P', allowOpenItems: false })
    expect(out.exitCode).not.toBe(0)
    expect(out.envelope).toBeUndefined()
  })
  it('allows open items WITH the flag -> partial_preview, warning, exit 0', () => {
    const out = runFromArtifact(art([matched(), row({ raw: 'MCB 100AF/100AT', tag: 'B' })]), { projectNumber: 'P', allowOpenItems: true })
    expect(out.exitCode).toBe(0)
    expect(out.report!.status).toBe('partial_preview')
    expect(out.envelope).toBeDefined()
    expect(out.stderr.join(' ')).toMatch(/partial preview/i)
  })
  it('error findings are an UNCONDITIONAL hard block, not launderable by allowOpenItems', () => {
    const out = runFromArtifact(art([matched()], [{ voltageV: 480, tags: ['NOPE'] }]), { projectNumber: 'P', allowOpenItems: true })
    expect(out.exitCode).not.toBe(0)
    expect(out.envelope).toBeUndefined()
  })
  it('a contract error -> exit 2, no envelope', () => {
    const out = runFromArtifact({ pdf: 'x', apparatus: 'notarray' }, { projectNumber: 'P', allowOpenItems: true })
    expect(out.exitCode).toBe(2)
    expect(out.envelope).toBeUndefined()
  })
  it('SPARE row (unrecognized_apparatus_row) blocks without flag and warns with positive unresolved count with flag', () => {
    // SPARE row: no breaker hint, no FRAME_TRIP -> assessmentCode=unrecognized_apparatus_row -> disposition=question but no operatorQuestion
    // This means isClean=false but operatorQuestions is empty, so naive count would show "0 open questions"
    const spare = row({ raw: 'SPARE', tag: 'S' })
    // Without --allow-open-items: should block (exitCode != 0) and stderr should mention unresolved row count > 0
    const blocked = runFromArtifact(art([matched(), spare]), { projectNumber: 'P', allowOpenItems: false })
    expect(blocked.exitCode).not.toBe(0)
    expect(blocked.stderr.join(' ')).toMatch(/[1-9]\d* unresolved row/)

    // With --allow-open-items: partial_preview, exit 0, stderr warns with positive unresolved count
    const allowed = runFromArtifact(art([matched(), spare]), { projectNumber: 'P', allowOpenItems: true })
    expect(allowed.exitCode).toBe(0)
    expect(allowed.report!.status).toBe('partial_preview')
    expect(allowed.stderr.join(' ')).toMatch(/[1-9]\d* unresolved row/)
  })
})