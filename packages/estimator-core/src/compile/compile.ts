import type { CatalogResolver } from '../catalog/resolver'
import {
  allocateByLargestRemainder,
  divRoundHalfUp,
  hoursToMicro,
  MICRO,
  microToCents,
  pctToScaled,
  SCALE4,
} from '../money'
import { isOnsite, resolveCostDefault, resolveRateCard, type RateCard } from '../pricing/rate-card'
import type { EstimateDraft, LineDraft, Revision, ScopeDraft } from '../schema/draft'
import type {
  EstimateEnvelope,
  LaborChargeLine,
  LineC,
  ScopeC,
  ScopeTotals,
} from '../schema/envelope'
import { SCHEMA_VERSION } from '../schema/envelope'
import { computeContentHash } from './content-hash'

export interface CompileOptions {
  envelopeId?: string
  sourceKind?: 'native' | 'workbook_intake'
  compiledAt?: string | null
  projectNumber?: string | null
  quoteVersion?: number | null
  jobNumberSourceRef?: string | null
}

function emptyLineC(d: LineDraft): LineC {
  return {
    line_uid: d.line_uid,
    line_kind: d.line_kind,
    included: d.included,
    excluded_hours: d.included ? null : d.excluded_hours ?? 0,
    exclusion_reason: d.included ? null : d.exclusion_reason ?? null,
    expansion_policy: d.expansion_policy ?? null,
    equipment_model_ref: null,
    provisional_token: null,
    catalog_request_ref: null,
    provisional_attrs: null,
    equipment_fingerprint: null,
    provisional_ref_hours: null,
    base_qty: null,
    project_intake_qty: null,
    resolved_ref_hours: null,
    resolved_hours: null,
    service_kind: null,
    billing_type: null,
    quoted_service_hours: null,
    quoted_amount_cents: null,
    ceiling_cents: null,
    adjusted_quoted_amount_cents: null,
    adjusted_ceiling_cents: null,
    cost_category: null,
    units: null,
    unit_cost_cents: null,
    markup_basis_ref: null,
    rate_basis_ref: null,
    extended_cents: 0,
  }
}

const isApparatus = (l: LineC): boolean =>
  l.line_kind === 'catalog' || l.line_kind === 'custom_equipment'

// canonical line ordering so penny-allocation (and thus extended_cents) is producer-order-independent
const byUid = (a: LineC, b: LineC): number => (a.line_uid < b.line_uid ? -1 : a.line_uid > b.line_uid ? 1 : 0)

function round6(n: number): number {
  return Math.round(n * 1_000_000) / 1_000_000
}

/**
 * Compile one scope's resolved lines into a ScopeC (pure + deterministic). Catalog
 * resolved_ref_hours are already filled by compile(); custom lines carry provisional_ref_hours.
 *
 * extended_cents is auditable per line: each COST line carries its OWN post-N4 cost; each
 * APPARATUS line carries its hours-weighted share of the labor pool post-N4; each SERVICE line
 * carries its adjusted basis (Task 8). The three sets sum EXACTLY to adjusted_cents via
 * largest-remainder allocation — drift is never dumped into an unrelated line.
 */
function finalizeScope(
  scope: ScopeDraft,
  card: RateCard,
  lines: LineC[],
  m4: number,
  n4Scaled: bigint,
): ScopeC {
  // --- 1. apparatus base/quoted hours + per-line hour weights (for labor attribution) ---
  let baseHoursMicro = 0n
  const apparatusWeights: { uid: string; weightMicro: bigint }[] = []
  for (const lc of lines) {
    if (isApparatus(lc) && lc.included) {
      const ref = lc.resolved_ref_hours ?? lc.provisional_ref_hours ?? 0
      const lineHours = (lc.base_qty ?? 0) * ref
      lc.resolved_hours = lineHours
      const wm = hoursToMicro(lineHours)
      baseHoursMicro += wm
      apparatusWeights.push({ uid: lc.line_uid, weightMicro: wm })
    }
  }
  const baseAppHours = round6(Number(baseHoursMicro) / 1_000_000)
  const quotedAppHoursMicro = baseHoursMicro * BigInt(m4)
  const quotedAppHours = round6(Number(quotedAppHoursMicro) / 1_000_000)

  // --- 2. labor distribution -> charges; block totals penny-allocated across charge lines ---
  const charges: LaborChargeLine[] = []
  const onsiteCharges: { idx: number; weightMicro: bigint }[] = []
  const offsiteCharges: { idx: number; weightMicro: bigint }[] = []
  let onsiteBlockMicro = 0n
  let offsiteBlockMicro = 0n
  scope.labor_allocation.forEach((entry) => {
    const pctScaled = pctToScaled(entry.pct_of_app)
    const hoursMicro = (quotedAppHoursMicro * pctScaled) / SCALE4
    const rate = BigInt(card.labor_rates_cents[entry.labor_type])
    const centsMicro = hoursMicro * rate // micro-cents
    const idx = charges.length
    charges.push({
      labor_type: entry.labor_type,
      pct_of_app: entry.pct_of_app,
      resolved_hours: round6(Number(hoursMicro) / 1_000_000),
      rate_basis_ref: `${card.version}:${entry.labor_type}`,
      cents: 0,
    })
    if (isOnsite(card, entry.labor_type)) {
      onsiteBlockMicro += centsMicro
      onsiteCharges.push({ idx, weightMicro: centsMicro })
    } else {
      offsiteBlockMicro += centsMicro
      offsiteCharges.push({ idx, weightMicro: centsMicro })
    }
  })
  const onsiteCents = microToCents(onsiteBlockMicro)
  const offsiteCents = microToCents(offsiteBlockMicro)
  for (const [block, group] of [
    [onsiteCents, onsiteCharges] as const,
    [offsiteCents, offsiteCharges] as const,
  ]) {
    const parts = allocateByLargestRemainder(block, group.map((g) => g.weightMicro))
    group.forEach((g, i) => {
      charges[g.idx]!.cents = parts[i]!
    })
  }
  const laborTotal = onsiteCents + offsiteCents

  // --- 3. cost lines: per-line numerator -> block round (P26/P33) -> penny-allocate to lines ---
  const preAdjustByUid = new Map<string, number>()
  let travelCents = 0
  let outsideCents = 0
  for (const category of ['travel', 'outside_services'] as const) {
    const costLines = lines
      .filter((l) => l.line_kind === 'cost' && l.included && l.cost_category === category)
      .sort(byUid)
    const weights = costLines.map((l) => {
      const markup = l.markup_basis_ref ? card.markup_scaled : SCALE4
      // units may be fractional (e.g. car rental "tech days/2") -> micro-scale, so BigInt never sees a float
      const unitsMicro = hoursToMicro(l.units ?? 0)
      return unitsMicro * BigInt(l.unit_cost_cents ?? 0) * BigInt(m4) * markup // scaled by MICRO*SCALE4
    })
    const blockCents = Number(divRoundHalfUp(weights.reduce((a, w) => a + w, 0n), MICRO * SCALE4))
    const parts = allocateByLargestRemainder(blockCents, weights)
    costLines.forEach((l, i) => preAdjustByUid.set(l.line_uid, parts[i]!))
    if (category === 'travel') travelCents = blockCents
    else outsideCents = blockCents
  }
  const costCents = travelCents + outsideCents

  // attribute the labor pool to apparatus lines by hours weight (auditable; sums to laborTotal)
  const laborParts = allocateByLargestRemainder(laborTotal, apparatusWeights.map((a) => a.weightMicro))
  apparatusWeights.forEach((a, i) => preAdjustByUid.set(a.uid, laborParts[i]!))

  // --- 4. service lines: hours isolated; amounts replicate by M4; adjusted basis = round(M4*N4) ---
  // sorted by line_uid so the N4 penny-allocation is deterministic (spec §3.2.5 "by line_uid order")
  const serviceLines = lines.filter((l) => l.included && l.line_kind === 'service').sort(byUid)
  let serviceHours = 0
  let serviceCents = 0
  for (const l of serviceLines) {
    serviceHours += (l.quoted_service_hours ?? 0) * m4
    const base = l.billing_type === 'NTE' ? (l.ceiling_cents ?? 0) : (l.quoted_amount_cents ?? 0)
    serviceCents += base * m4
  }
  const adjustedServiceShare = Number(divRoundHalfUp(BigInt(serviceCents) * n4Scaled, SCALE4))
  const svcParts = allocateByLargestRemainder(
    adjustedServiceShare,
    serviceLines.map((l) =>
      BigInt((l.billing_type === 'NTE' ? (l.ceiling_cents ?? 0) : (l.quoted_amount_cents ?? 0)) * m4),
    ),
  )
  serviceLines.forEach((l, i) => {
    if (l.billing_type === 'NTE') {
      l.adjusted_ceiling_cents = svcParts[i]!
      l.adjusted_quoted_amount_cents = null
    } else {
      l.adjusted_quoted_amount_cents = svcParts[i]!
      l.adjusted_ceiling_cents = null
    }
    l.extended_cents = svcParts[i]!
  })

  // --- 5. cascade ---
  const preAdjust = onsiteCents + offsiteCents + costCents + serviceCents
  const adjustedCents = Number(divRoundHalfUp(BigInt(preAdjust) * n4Scaled, SCALE4))

  // --- 6. per-line extended_cents: non-service lines share (adjusted - adjustedServiceShare) ---
  // allocate over a canonically-ordered list so per-line extended_cents is producer-order-independent
  const nonService = lines.filter((l) => l.included && l.line_kind !== 'service').sort(byUid)
  const extParts = allocateByLargestRemainder(
    adjustedCents - adjustedServiceShare,
    nonService.map((l) => BigInt(preAdjustByUid.get(l.line_uid) ?? 0)),
  )
  nonService.forEach((l, i) => {
    l.extended_cents = extParts[i]!
  })
  // excluded lines keep extended_cents = 0; service lines are set in Task 8

  const totals: ScopeTotals = {
    base_app_hours: baseAppHours,
    quoted_app_hours: quotedAppHours,
    service_hours: round6(serviceHours),
    onsite_labor_cents: onsiteCents,
    offsite_labor_cents: offsiteCents,
    cost_cents: costCents,
    service_cents: serviceCents,
    pre_adjust_cents: preAdjust,
    adjusted_cents: adjustedCents,
  }
  return {
    scope_id: scope.scope_id,
    name: scope.name,
    neta_standard: scope.neta_standard,
    replication_m4: m4,
    adjustment_multiplier_n4: scope.adjustment_multiplier_n4,
    lines,
    labor_charge_lines: charges,
    scope_totals: totals,
  }
}

export function compile(
  draft: EstimateDraft,
  revisionId: string,
  resolver: CatalogResolver,
  opts: CompileOptions = {},
): EstimateEnvelope {
  const revision: Revision | undefined = draft.revisions.find((r) => r.revision_id === revisionId)
  if (!revision) throw new Error(`compile: revision ${revisionId} not found`)
  const card = resolveRateCard(revision.pricing_card_version)

  // Guard the integer-M4 precondition BEFORE any BigInt(m4) in finalizeScope: a non-integer or <1
  // replication_m4 would otherwise throw an opaque RangeError mid-compile. Surface a clear, catchable
  // error instead (validateEnvelope's integer-M4 finding only runs on an already-compiled envelope).
  for (const scope of revision.scopes) {
    if (!Number.isInteger(scope.replication_m4) || scope.replication_m4 < 1) {
      throw new Error(
        `compile: scope ${scope.scope_id} replication_m4 must be an integer >= 1 (got ${scope.replication_m4})`,
      )
    }
  }

  const scopes: ScopeC[] = revision.scopes.map((scope) => {
    // build lines, fill catalog resolved_ref_hours via resolver, then finalize
    const lines: LineC[] = scope.lines.map((d) => {
      const lc = emptyLineC(d)
      if (d.line_kind === 'catalog' || d.line_kind === 'custom_equipment') {
        lc.equipment_model_ref = d.line_kind === 'catalog' ? d.equipment_model_ref ?? null : null
        lc.provisional_token = d.line_kind === 'custom_equipment' ? d.provisional_token ?? null : null
        lc.catalog_request_ref = d.catalog_request_ref ?? null
        lc.equipment_fingerprint = d.equipment_fingerprint ?? null
        lc.provisional_attrs = d.provisional_attrs ?? null
        lc.base_qty = d.base_qty ?? 0
        lc.project_intake_qty = (d.base_qty ?? 0) * scope.replication_m4
        lc.expansion_policy = d.expansion_policy ?? 'one_unit_per_qty'
        const refHours =
          d.line_kind === 'catalog'
            ? resolver.refHours(d.equipment_model_ref!, scope.neta_standard)
            : d.provisional_ref_hours ?? 0
        if (d.line_kind === 'catalog') {
          lc.resolved_ref_hours = refHours
          lc.rate_basis_ref = card.version
        } else {
          lc.provisional_ref_hours = refHours
        }
        // excluded apparatus: derive excluded_hours = base_qty x ref_hours (not taken verbatim)
        if (!d.included) lc.excluded_hours = (d.base_qty ?? 0) * refHours
      } else if (d.line_kind === 'cost') {
        // resolve the versioned cost default by key; explicit draft fields override it
        const def = d.cost_default_key ? resolveCostDefault(card, d.cost_default_key) : null
        lc.cost_category = d.cost_category ?? def?.cost_category ?? null
        if (d.included && lc.cost_category === null) {
          throw new Error(`compile: included cost line ${d.line_uid} has no cost_category (set it or use a cost_default_key)`)
        }
        lc.units = d.units ?? 0
        lc.unit_cost_cents = d.unit_cost_cents ?? def?.unit_cost_cents ?? 0
        const markupApplies = d.markup_applies ?? def?.markup_applies ?? true
        lc.markup_basis_ref = markupApplies ? `${card.version}:markup` : null
      } else if (d.line_kind === 'service') {
        lc.service_kind = d.service_kind ?? null
        lc.billing_type = d.billing_type ?? null
        lc.quoted_service_hours = d.quoted_service_hours ?? 0
        lc.quoted_amount_cents = d.quoted_amount_cents ?? null
        lc.ceiling_cents = d.ceiling_cents ?? null
      }
      return lc
    })
    return finalizeScope(scope, card, lines, scope.replication_m4, pctToScaled(scope.adjustment_multiplier_n4))
  })

  const totals = {
    base_app_hours: round6(scopes.reduce((a, s) => a + s.scope_totals.base_app_hours, 0)),
    quoted_app_hours: round6(scopes.reduce((a, s) => a + s.scope_totals.quoted_app_hours, 0)),
    service_hours: round6(scopes.reduce((a, s) => a + s.scope_totals.service_hours, 0)),
    bid_cents: scopes.reduce((a, s) => a + s.scope_totals.adjusted_cents, 0),
  }

  const env: EstimateEnvelope = {
    envelope_id: opts.envelopeId ?? `${draft.draft_id}:${revisionId}`,
    schema_version: SCHEMA_VERSION,
    source_kind: opts.sourceKind ?? 'native',
    source_draft_id: draft.draft_id,
    source_revision_id: revisionId,
    job_number_source_ref: opts.jobNumberSourceRef ?? null,
    project_number: opts.projectNumber ?? null,
    quote_version: opts.quoteVersion ?? null,
    pricing_card_version: card.version,
    compiled_at: opts.compiledAt ?? null,
    content_hash: '',
    scopes,
    totals,
  }
  env.content_hash = computeContentHash(env)
  return env
}
