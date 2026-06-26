import { describe, it, expect } from 'vitest'
import { classifyVoltage } from '../src/signature/voltage'

describe('classifyVoltage (takeoff routing convention)', () => {
  it.each([
    [480, 'LV'], [600, 'LV'], [999, 'LV'],
    [1000, 'MV'], [4160, 'MV'], [13800, 'MV'], [69000, 'MV'],
    [69001, 'HV'], [115000, 'HV'], [230000, 'HV'],
  ])('classifies %iV as %s', (v, cls) => {
    expect(classifyVoltage(v)).toBe(cls)
  })
  it('returns undefined when voltage is unknown', () => {
    expect(classifyVoltage(undefined)).toBeUndefined()
  })
  it('returns undefined for impossible (non-positive) voltages', () => {
    expect(classifyVoltage(0)).toBeUndefined()
    expect(classifyVoltage(-1)).toBeUndefined()
    expect(classifyVoltage(-480)).toBeUndefined()
  })
})
