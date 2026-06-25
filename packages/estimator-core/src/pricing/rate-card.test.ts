import { describe, expect, it } from 'vitest'
import { BASELINE_RATE_CARD, isOnsite, resolveCostDefault, resolveRateCard } from './rate-card'

describe('baseline rate card', () => {
  it('resolves the baseline version', () => {
    expect(resolveRateCard('2026-01-23')).toBe(BASELINE_RATE_CARD)
    expect(() => resolveRateCard('nope')).toThrow(/unknown rate card/)
  })

  it('carries the authentic onsite/offsite cents-per-hour rates', () => {
    const c = BASELINE_RATE_CARD.labor_rates_cents
    expect(c.onsite_blended_10hr).toBe(16500)
    expect(c.onsite_blended_12hr).toBe(18750)
    expect(c.onsite_ot).toBe(22500)
    expect(c.onsite_dt).toBe(30000)
    expect(c.offsite_report).toBe(15000)
    expect(c.offsite_project_mgmt).toBe(15000)
  })

  it('encodes the 1.5 pass-through markup as a x10^4 int', () => {
    expect(BASELINE_RATE_CARD.markup_scaled).toBe(15000n)
  })

  it('classifies labor segments', () => {
    expect(isOnsite(BASELINE_RATE_CARD, 'onsite_pm')).toBe(true)
    expect(isOnsite(BASELINE_RATE_CARD, 'offsite_report')).toBe(false)
  })

  it('has cost defaults; travel hours are NOT marked up, per-diem IS', () => {
    const defs = BASELINE_RATE_CARD.cost_defaults
    const travelHours = defs.find((d) => d.key === 'travel_hours')!
    const perDiem = defs.find((d) => d.key === 'hotel_per_diem')!
    expect(travelHours.markup_applies).toBe(false)
    expect(travelHours.unit_cost_cents).toBe(15000)
    expect(perDiem.markup_applies).toBe(true)
    expect(perDiem.unit_cost_cents).toBe(27500)
  })

  it('resolves a cost default by key and throws on unknown', () => {
    const def = resolveCostDefault(BASELINE_RATE_CARD, 'generator')
    expect(def.unit_cost_cents).toBe(75000)
    expect(def.cost_category).toBe('outside_services')
    expect(() => resolveCostDefault(BASELINE_RATE_CARD, 'nope')).toThrow(/unknown cost_default/)
  })
})
