import { describe, it, expect } from 'vitest'
import { parseArtifact, ArtifactContractError } from '../src/extraction/parse'

const ok = () => ({
  pdf: 'x.pdf',
  apparatus: [{ raw: 'MSB 4000AF/4000AT LSIG', tag: 'MSB-1', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480 }],
})

function err(mut: (a: any) => void): ArtifactContractError {
  const a = ok(); mut(a)
  try { parseArtifact(a); throw new Error('did not throw') }
  catch (e) { if (e instanceof ArtifactContractError) return e; throw e }
}

describe('parseArtifact', () => {
  it('accepts a valid artifact and returns it', () => {
    const a = ok(); expect(parseArtifact(a)).toBe(a)
  })
  it('rejects a non-array apparatus', () => { expect(err((a) => (a.apparatus = {})).path).toBe('apparatus') })
  it('rejects a missing pdf', () => { expect(err((a) => delete a.pdf).path).toBe('pdf') })
  it('rejects a bad bbox arity', () => { expect(err((a) => (a.apparatus[0].bbox = [0, 0, 1])).path).toBe('apparatus[0].bbox') })
  it('rejects a non-finite bbox value', () => { expect(err((a) => (a.apparatus[0].bbox = [0, 0, 1, Infinity])).path).toBe('apparatus[0].bbox') })
  it('rejects an unknown evidence enum', () => { expect(err((a) => (a.apparatus[0].evidence = 'guess')).path).toBe('apparatus[0].evidence') })
  it('rejects a non-integer page', () => { expect(err((a) => (a.apparatus[0].page = 1.5)).path).toBe('apparatus[0].page') })
  it('rejects a non-integer busVoltageV', () => { expect(err((a) => (a.apparatus[0].busVoltageV = 480.5)).path).toBe('apparatus[0].busVoltageV') })
  it('rejects a non-positive busVoltageV', () => { expect(err((a) => (a.apparatus[0].busVoltageV = 0)).path).toBe('apparatus[0].busVoltageV') })
  it('rejects an oversized payload', () => { expect(err((a) => (a.apparatus = Array.from({ length: 5001 }, () => ok().apparatus[0]))).path).toBe('apparatus') })
  it('rejects a malformed voltageAssertions shape', () => { expect(err((a) => (a.voltageAssertions = [{ voltageV: 480 }])).path).toBe('voltageAssertions[0].tags') })
  it('does not throw a raw TypeError on a non-serializable value (BigInt)', () => {
    expect(err((a) => (a.apparatus = [10n])).path).toBe('apparatus[0]')
  })
})
