export const LINE_KINDS = ['catalog', 'custom_equipment', 'service', 'cost'] as const
export type LineKind = (typeof LINE_KINDS)[number]
export function isLineKind(x: unknown): x is LineKind {
  return typeof x === 'string' && (LINE_KINDS as readonly string[]).includes(x)
}

export const SERVICE_KINDS = ['repair', 'investigate', 'troubleshoot', 'other'] as const
export type ServiceKind = (typeof SERVICE_KINDS)[number]
export function isServiceKind(x: unknown): x is ServiceKind {
  return typeof x === 'string' && (SERVICE_KINDS as readonly string[]).includes(x)
}

export const BILLING_TYPES = ['fixed_bid', 'NTE', 'TM'] as const
export type BillingType = (typeof BILLING_TYPES)[number]
export function isBillingType(x: unknown): x is BillingType {
  return typeof x === 'string' && (BILLING_TYPES as readonly string[]).includes(x)
}

export const COST_CATEGORIES = ['travel', 'outside_services'] as const
export type CostCategory = (typeof COST_CATEGORIES)[number]
export function isCostCategory(x: unknown): x is CostCategory {
  return typeof x === 'string' && (COST_CATEGORIES as readonly string[]).includes(x)
}

export const EXPANSION_POLICIES = ['one_unit_per_qty'] as const
export type ExpansionPolicy = (typeof EXPANSION_POLICIES)[number]
