// Catalog
export type { EquipmentModel, LifecycleStatus, NetaStandard, UnitOfIssue } from './catalog/types'
export { createCatalogResolver } from './catalog/resolver'
export type { CatalogResolver } from './catalog/resolver'

// Pricing
export {
  BASELINE_RATE_CARD,
  isOnsite,
  resolveCostDefault,
  resolveRateCard,
} from './pricing/rate-card'
export type { CostDefault, LaborType, OffsiteLaborType, OnsiteLaborType, RateCard } from './pricing/rate-card'

// Schema
export {
  BILLING_TYPES,
  COST_CATEGORIES,
  EXPANSION_POLICIES,
  isBillingType,
  isCostCategory,
  isLineKind,
  isServiceKind,
  LINE_KINDS,
  SERVICE_KINDS,
} from './schema/enums'
export type { BillingType, CostCategory, ExpansionPolicy, LineKind, ServiceKind } from './schema/enums'
export { makeDraft } from './schema/draft'
export type {
  DraftStatus,
  EstimateDraft,
  LaborAllocationEntry,
  LineDraft,
  Revision,
  ScopeDraft,
} from './schema/draft'
export { SCHEMA_VERSION } from './schema/envelope'
export type {
  EnvelopeTotals,
  EstimateEnvelope,
  LaborChargeLine,
  LineC,
  ScopeC,
  ScopeTotals,
} from './schema/envelope'

// Compile + validate
export { compile } from './compile/compile'
export type { CompileOptions } from './compile/compile'
export { canonicalPreimage, computeContentHash } from './compile/content-hash'
export { validateEnvelope } from './validate/validator'
export type { Finding, Severity } from './validate/findings'

// Corpus
export { loadCorpusCases, runCorpusCase } from './corpus/harness'
export type { CorpusCase, ScopeExpectation } from './corpus/harness'

// Money primitives
export {
  allocateByLargestRemainder,
  divRoundHalfUp,
  hoursToMicro,
  microToCents,
  pctToScaled,
} from './money'
