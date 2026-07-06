import { describe, it, expect } from 'vitest'
import { assessApparatus } from '../src/signature/normalize'

const at = (raw: string, tag = 'X', kind?: any, v?: number) =>
  assessApparatus({ raw, tag, sheet: 'E', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', candidateKind: kind, busVoltageV: v } as any)

describe('assessTransferSwitch T1-B', () => {
  it('clean tagged ATS -> transfer_recognized, automatic', () => {
    const a = at('ATS-1')
    expect(a.assessmentCode).toBe('transfer_recognized')
    expect((a.signature as any).kind).toBe('transfer_switch')
    expect((a.signature as any).automationClass).toBe('automatic')
  })
  it('bare AF/AT is rating evidence, not a conflict', () => {
    const a = at('ATS-1 800AF/800AT')
    expect(a.assessmentCode).toBe('transfer_recognized')
    expect((a.signature as any).ampRating).toBe(800)
  })
  it('LSIG on a transfer row -> conflict, signature null', () => {
    const a = at('ATS-1 800AF/800AT LSIG')
    expect(a.assessmentCode).toBe('transfer_parent_conflict')
    expect(a.signature).toBeNull()
  })
  it('VCB on a transfer row -> conflict', () => {
    expect(at('ATS-1 VCB').assessmentCode).toBe('transfer_parent_conflict')
  })
  it('co-located UPS -> conflict', () => {
    expect(at('ATS-1 UPS').assessmentCode).toBe('transfer_parent_conflict')
  })
  it('STS clean -> transfer_recognized (static); still assessed here, gap comes at emit', () => {
    const a = at('STS-1')
    expect(a.assessmentCode).toBe('transfer_recognized')
    expect((a.signature as any).automationClass).toBe('static')
  })
  it('STS 800AF/800AT (no LSIG) -> transfer_recognized (static)', () => {
    expect(at('STS-1 800AF/800AT').assessmentCode).toBe('transfer_recognized')
  })
  it('STS 800AF/800AT LSIG -> conflict', () => {
    expect(at('STS-1 800AF/800AT LSIG').assessmentCode).toBe('transfer_parent_conflict')
  })
  it('candidateKind hard-win beats relay wording (top-of-assessCore short-circuit)', () => {
    expect(at('ATS-1 SEL-751 relay', 'X', 'transfer_switch').assessmentCode).toBe('transfer_recognized')
  })
})
