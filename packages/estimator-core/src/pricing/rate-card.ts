export type OnsiteLaborType =
  | 'onsite_blended_10hr'
  | 'onsite_blended_12hr'
  | 'onsite_ot'
  | 'onsite_dt'
  | 'onsite_badging'
  | 'onsite_loto'
  | 'onsite_pm'
  | 'onsite_commute'

export type OffsiteLaborType = 'offsite_report' | 'offsite_project_mgmt' | 'offsite_loading_prep'
export type LaborType = OnsiteLaborType | OffsiteLaborType

export interface CostDefault {
  cost_category: 'travel' | 'outside_services'
  key: string
  label: string
  unit_cost_cents: number
  markup_applies: boolean
}

export interface RateCard {
  version: string
  effective_date: string
  labor_rates_cents: Record<LaborType, number>
  labor_segment: Record<LaborType, 'onsite' | 'offsite'>
  markup_scaled: bigint
  cost_defaults: CostDefault[]
}

export const BASELINE_RATE_CARD: RateCard = {
  version: '2026-01-23',
  effective_date: '2026-01-23',
  labor_rates_cents: {
    onsite_blended_10hr: 16500,
    onsite_blended_12hr: 18750,
    onsite_ot: 22500,
    onsite_dt: 30000,
    onsite_badging: 16500,
    onsite_loto: 16500,
    onsite_pm: 16500,
    onsite_commute: 16500,
    offsite_report: 15000,
    offsite_project_mgmt: 15000,
    offsite_loading_prep: 15000,
  },
  labor_segment: {
    onsite_blended_10hr: 'onsite',
    onsite_blended_12hr: 'onsite',
    onsite_ot: 'onsite',
    onsite_dt: 'onsite',
    onsite_badging: 'onsite',
    onsite_loto: 'onsite',
    onsite_pm: 'onsite',
    onsite_commute: 'onsite',
    offsite_report: 'offsite',
    offsite_project_mgmt: 'offsite',
    offsite_loading_prep: 'offsite',
  },
  markup_scaled: 15000n, // 1.5 x 10^4 — pass-through markup on COSTS PAID OUT (vendor invoices:
  // per-diem/flights/car/generator/test-equip/oil-sample). NOT on travel_hours (own labor, ×1).
  cost_defaults: [
    // Travel Hours is the ONE travel row with multiplier 1 (workbook cell O21='1'), NOT 1.5 — verified
    // against the scope-sheet dump; the ×1.5 markup applies to per-diem/flights/car/generator/etc. only.
    { cost_category: 'travel', key: 'travel_hours', label: 'Travel Hours', unit_cost_cents: 15000, markup_applies: false },
    { cost_category: 'travel', key: 'hotel_per_diem', label: 'Hotel & Per Diem (Tech Days)', unit_cost_cents: 27500, markup_applies: true },
    { cost_category: 'travel', key: 'flights', label: 'Flights', unit_cost_cents: 65000, markup_applies: true },
    { cost_category: 'travel', key: 'car_rental', label: 'Car Rental (Tech Days/2)', unit_cost_cents: 10000, markup_applies: true },
    { cost_category: 'outside_services', key: 'generator', label: 'Generator Rental', unit_cost_cents: 75000, markup_applies: true },
    { cost_category: 'outside_services', key: 'test_equipment', label: 'Test Equipment Rental', unit_cost_cents: 50000, markup_applies: true },
    { cost_category: 'outside_services', key: 'oil_sample', label: 'Oil Sample (Lab)', unit_cost_cents: 25000, markup_applies: true },
  ],
}

const CARDS: Record<string, RateCard> = {
  [BASELINE_RATE_CARD.version]: BASELINE_RATE_CARD,
}

export function resolveRateCard(version: string): RateCard {
  const card = CARDS[version]
  if (!card) throw new Error(`unknown rate card version ${version}`)
  return card
}

export function isOnsite(card: RateCard, t: LaborType): boolean {
  return card.labor_segment[t] === 'onsite'
}

/** Resolve a versioned cost default by key (so workbook defaults reproduce without manual re-entry). */
export function resolveCostDefault(card: RateCard, key: string): CostDefault {
  const def = card.cost_defaults.find((d) => d.key === key)
  if (!def) throw new Error(`unknown cost_default key ${key}`)
  return def
}
