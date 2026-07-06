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
    const spare = row({ raw: 'SPARE', tag: 'S' })
    const blocked = runFromArtifact(art([matched(), spare]), { projectNumber: 'P', allowOpenItems: false })
    expect(blocked.exitCode).not.toBe(0)
    expect(blocked.stderr.join(' ')).toMatch(/[1-9]\d* unresolved row/)

    const allowed = runFromArtifact(art([matched(), spare]), { projectNumber: 'P', allowOpenItems: true })
    expect(allowed.exitCode).toBe(0)
    expect(allowed.report!.status).toBe('partial_preview')
    expect(allowed.stderr.join(' ')).toMatch(/[1-9]\d* unresolved row/)
  })
  it('does not emit a clean envelope when same-tag ambiguous rows are present (no silent laundering)', () => {
    const out = runFromArtifact(art([
      matched(),
      row({ raw: 'SPARE', tag: 'A' }),
      row({ raw: 'ATS 800AF/800AT LSIG', tag: 'A' }),
      row({ raw: 'MCB 100AF/100AT', tag: 'A' }),
    ]), { projectNumber: 'P', allowOpenItems: false })
    expect(out.exitCode).not.toBe(0)
    expect(out.report!.status).not.toBe('clean')
    expect(out.envelope).toBeUndefined()
    expect(out.report!.counts.operator_questions).toBeGreaterThanOrEqual(2)  // SPARE has question disposition but no operatorQuestion (by design); the tagged ATS (now a transfer_parent_conflict) + MCB each push one
  })
})
