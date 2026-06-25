import { computeContentHash } from '../compile/content-hash'
import { divRoundHalfUp, pctToScaled, SCALE4 } from '../money'
import { EXPANSION_POLICIES, isBillingType, isCostCategory, isServiceKind } from '../schema/enums'
import type { EstimateEnvelope, LineC, ScopeC } from '../schema/envelope'
import { SCHEMA_VERSION } from '../schema/envelope'
import { err, type Finding } from './findings'

const EPS = 1e-6

function isInt(n: number | null): boolean {
  return n !== null && Number.isInteger(n)
}

// Field groups for the full both-directions CHECK matrix (spec §7). A line of one kind must carry
// NONE of the other kinds' fields. CUSTOM_IDENT = custom-equipment provenance; APPARATUS_QTY = the
// quantity/hours/policy fields shared by catalog+custom; SERVICE/COST = the service/cost field sets.
type FieldName = keyof LineC
const CUSTOM_IDENT: FieldName[] = ['provisional_token', 'catalog_request_ref', 'equipment_fingerprint', 'provisional_attrs', 'provisional_ref_hours']
const APPARATUS_QTY: FieldName[] = ['base_qty', 'project_intake_qty', 'resolved_ref_hours', 'resolved_hours', 'expansion_policy']
const SERVICE_FIELDS: FieldName[] = ['service_kind', 'billing_type', 'quoted_service_hours', 'quoted_amount_cents', 'ceiling_cents', 'adjusted_quoted_amount_cents', 'adjusted_ceiling_cents']
const COST_FIELDS: FieldName[] = ['cost_category', 'units', 'unit_cost_cents', 'markup_basis_ref']

function requireNull(line: LineC, fields: FieldName[], path: string, out: Finding[]): void {
  for (const f of fields) {
    if (line[f] !== null && line[f] !== undefined) out.push(err('line_kind_matrix', path, `${line.line_kind} must not carry ${f}`))
  }
}

function checkLineMatrix(line: LineC, scope: ScopeC, path: string, out: Finding[]): void {
  const inc = line.included
  // closed-enum membership (spec §7) — TS unions don't protect the runtime gate for workbook_intake
  if (line.service_kind !== null && !isServiceKind(line.service_kind)) out.push(err('enum_membership', path, `service_kind '${line.service_kind}' not in closed enum`))
  if (line.billing_type !== null && !isBillingType(line.billing_type)) out.push(err('enum_membership', path, `billing_type '${line.billing_type}' not in closed enum`))
  if (line.cost_category !== null && !isCostCategory(line.cost_category)) out.push(err('enum_membership', path, `cost_category '${line.cost_category}' not in closed enum`))
  if (line.expansion_policy !== null && !(EXPANSION_POLICIES as readonly string[]).includes(line.expansion_policy)) out.push(err('enum_membership', path, `expansion_policy '${line.expansion_policy}' not in closed enum`))
  switch (line.line_kind) {
    case 'catalog': {
      if (!line.equipment_model_ref) out.push(err('line_kind_matrix', path, 'catalog requires equipment_model_ref'))
      requireNull(line, [...CUSTOM_IDENT, ...SERVICE_FIELDS, ...COST_FIELDS], path, out)
      if (inc) {
        if (!(line.base_qty && line.base_qty > 0)) out.push(err('line_kind_matrix', path, 'included catalog requires base_qty>0'))
        if (line.project_intake_qty !== (line.base_qty ?? 0) * scope.replication_m4) out.push(err('line_kind_matrix', path, 'project_intake_qty != base_qty * M4'))
        if (!isInt(line.base_qty) || !isInt(line.project_intake_qty)) out.push(err('integer_quantity', path, 'base_qty and project_intake_qty must be integers'))
        if (line.resolved_ref_hours === null) out.push(err('line_kind_matrix', path, 'included catalog requires resolved_ref_hours'))
        if (line.resolved_hours === null) out.push(err('line_kind_matrix', path, 'included catalog requires resolved_hours'))
      }
      break
    }
    case 'custom_equipment': {
      if (line.equipment_model_ref) out.push(err('line_kind_matrix', path, 'custom_equipment must not carry equipment_model_ref'))
      if (!line.provisional_token) out.push(err('line_kind_matrix', path, 'custom_equipment requires provisional_token'))
      if (!line.catalog_request_ref) out.push(err('line_kind_matrix', path, 'custom_equipment requires catalog_request_ref'))
      if (!line.equipment_fingerprint) out.push(err('line_kind_matrix', path, 'custom_equipment requires equipment_fingerprint'))
      if (line.resolved_ref_hours !== null) out.push(err('line_kind_matrix', path, 'custom_equipment must not carry resolved_ref_hours (use provisional_ref_hours)'))
      requireNull(line, [...SERVICE_FIELDS, ...COST_FIELDS], path, out)
      if (inc) {
        if (!(line.base_qty && line.base_qty > 0)) out.push(err('line_kind_matrix', path, 'included custom_equipment requires base_qty>0'))
        if (line.project_intake_qty !== (line.base_qty ?? 0) * scope.replication_m4) out.push(err('line_kind_matrix', path, 'project_intake_qty != base_qty * M4'))
        if (!isInt(line.base_qty) || !isInt(line.project_intake_qty)) out.push(err('integer_quantity', path, 'base_qty and project_intake_qty must be integers'))
        if (!(line.provisional_ref_hours && line.provisional_ref_hours > 0)) out.push(err('line_kind_matrix', path, 'included custom_equipment requires provisional_ref_hours>0'))
        if (line.resolved_hours === null) out.push(err('line_kind_matrix', path, 'included custom_equipment requires resolved_hours'))
      }
      break
    }
    case 'service': {
      requireNull(line, ['equipment_model_ref', ...CUSTOM_IDENT, ...APPARATUS_QTY, ...COST_FIELDS], path, out)
      if (!line.billing_type) out.push(err('line_kind_matrix', path, 'service requires billing_type'))
      if (inc) {
        if (!(line.quoted_service_hours && line.quoted_service_hours > 0)) out.push(err('line_kind_matrix', path, 'included service requires quoted_service_hours>0'))
        if (line.billing_type === 'fixed_bid' && !(line.quoted_amount_cents && line.quoted_amount_cents > 0)) out.push(err('line_kind_matrix', path, 'fixed_bid requires quoted_amount_cents>0'))
        if (line.billing_type === 'NTE' && !(line.ceiling_cents && line.ceiling_cents > 0)) out.push(err('line_kind_matrix', path, 'NTE requires ceiling_cents>0'))
        if (line.billing_type === 'TM' && !(line.quoted_amount_cents && line.quoted_amount_cents > 0)) out.push(err('line_kind_matrix', path, 'TM requires quoted_amount_cents>0'))
        // adjusted service basis is the recognition/contract reference (spec §3.2.5/§5.7) — required
        if (line.billing_type === 'NTE') {
          if (line.adjusted_ceiling_cents === null) out.push(err('service_adjusted_basis', path, 'included NTE service requires adjusted_ceiling_cents'))
        } else if (line.adjusted_quoted_amount_cents === null) {
          out.push(err('service_adjusted_basis', path, 'included service requires adjusted_quoted_amount_cents'))
        }
      }
      break
    }
    case 'cost': {
      requireNull(line, ['equipment_model_ref', ...CUSTOM_IDENT, ...APPARATUS_QTY, ...SERVICE_FIELDS], path, out)
      if (inc) {
        if (!line.cost_category) out.push(err('line_kind_matrix', path, 'included cost requires cost_category'))
        if (line.units !== null && line.units < 0) out.push(err('line_kind_matrix', path, 'cost units must be >= 0'))
        if (line.unit_cost_cents !== null && line.unit_cost_cents < 0) out.push(err('line_kind_matrix', path, 'cost unit_cost_cents must be >= 0'))
      }
      break
    }
  }
}

function checkIncludedInvariant(line: LineC, path: string, out: Finding[]): void {
  if (!line.included) {
    if (line.excluded_hours === null) out.push(err('included_invariant', path, 'excluded line requires excluded_hours'))
    if (!line.exclusion_reason) out.push(err('included_invariant', path, 'excluded line requires a non-empty exclusion_reason'))
    if (line.extended_cents !== 0) out.push(err('included_invariant', path, 'excluded line must contribute extended_cents=0'))
  } else {
    if (line.excluded_hours !== null) out.push(err('included_invariant', path, 'included line must have null excluded_hours'))
    if (line.exclusion_reason !== null) out.push(err('included_invariant', path, 'included line must have null exclusion_reason'))
  }
}

function isRecognizable(line: LineC): boolean {
  if (!line.included) return false
  if (line.line_kind === 'catalog' || line.line_kind === 'custom_equipment') return true
  if (line.line_kind === 'service') return !!line.billing_type && !!line.quoted_service_hours
  return false
}

function checkScope(scope: ScopeC, sIdx: number, out: Finding[]): void {
  const sp = `scopes[${sIdx}]`
  if (!Number.isInteger(scope.replication_m4) || scope.replication_m4 < 1) out.push(err('integer_quantity', sp, 'replication_m4 must be an integer >= 1'))
  // line-level
  const tokens = new Set<string>()
  scope.lines.forEach((line, i) => {
    const lp = `${sp}.lines[${i}]`
    checkLineMatrix(line, scope, lp, out)
    checkIncludedInvariant(line, lp, out)
    if (!isInt(line.extended_cents)) out.push(err('integer_cents', lp, 'extended_cents must be an integer'))
    if (line.line_kind === 'custom_equipment' && line.provisional_token) {
      if (tokens.has(line.provisional_token)) out.push(err('provisional_token_unique', lp, `provisional_token ${line.provisional_token} reused`))
      tokens.add(line.provisional_token)
    }
  })

  if (!scope.lines.some(isRecognizable)) out.push(err('scope_recognizable_unit', sp, 'scope needs >=1 included recognizable unit'))

  // hours reproduce
  const apparatus = scope.lines.filter((l) => l.included && (l.line_kind === 'catalog' || l.line_kind === 'custom_equipment'))
  const baseHours = apparatus.reduce((a, l) => a + (l.base_qty ?? 0) * (l.resolved_ref_hours ?? l.provisional_ref_hours ?? 0), 0)
  if (Math.abs(baseHours - scope.scope_totals.base_app_hours) > EPS) out.push(err('hours_reproduce', sp, 'base_app_hours != sum(base_qty*ref_hours)'))
  if (Math.abs(scope.scope_totals.base_app_hours * scope.replication_m4 - scope.scope_totals.quoted_app_hours) > EPS) out.push(err('hours_reproduce', sp, 'quoted_app_hours != base_app_hours*M4'))

  // service hours isolated
  const svcHours = scope.lines.filter((l) => l.included && l.line_kind === 'service').reduce((a, l) => a + (l.quoted_service_hours ?? 0) * scope.replication_m4, 0)
  if (Math.abs(svcHours - scope.scope_totals.service_hours) > EPS) out.push(err('service_hours_isolated', sp, 'service_hours != sum(included service quoted_service_hours*M4)'))

  // labor charge lines sum to block totals
  const t = scope.scope_totals
  const laborSum = scope.labor_charge_lines.reduce((a, l) => a + l.cents, 0)
  if (t.quoted_app_hours > 0 && scope.labor_charge_lines.length === 0) out.push(err('labor_charge_lines', sp, 'labor_charge_lines required when quoted_app_hours>0'))
  if (laborSum !== t.onsite_labor_cents + t.offsite_labor_cents) out.push(err('labor_charge_lines', sp, 'labor_charge_lines.cents must sum to onsite+offsite block totals'))

  // integer cents on totals
  for (const [k, v] of Object.entries(t)) {
    if (k.endsWith('_cents') && !Number.isInteger(v)) out.push(err('integer_cents', sp, `${k} must be an integer`))
  }

  // rounding cascade — recompute via the SHARED fixed-point resolver (exact; same path as compile).
  // Guard the BigInt recompute behind integrality so a malformed (non-integer) total is REPORTED by
  // the integer_cents rule above, not crashed on (BigInt(249500.5) throws RangeError).
  const n4Scaled = pctToScaled(scope.adjustment_multiplier_n4)
  const pre = t.onsite_labor_cents + t.offsite_labor_cents + t.cost_cents + t.service_cents
  if (pre !== t.pre_adjust_cents) out.push(err('rounding_cascade', sp, 'pre_adjust_cents != onsite+offsite+cost+service'))
  if (Number.isInteger(t.pre_adjust_cents)) {
    const expectedAdjusted = Number(divRoundHalfUp(BigInt(t.pre_adjust_cents) * n4Scaled, SCALE4))
    if (t.adjusted_cents !== expectedAdjusted) out.push(err('rounding_cascade', sp, 'adjusted_cents != round(pre_adjust*N4) [fixed-point]'))
  }

  // extended_cents sum reconciles to the adjusted scope total (spec 1.2)
  const extSum = scope.lines.reduce((a, l) => a + l.extended_cents, 0)
  if (extSum !== t.adjusted_cents) out.push(err('extended_cents_sum', sp, 'sum(line.extended_cents) != adjusted_cents'))

  // adjusted service basis reconciles EXACTLY to round(service_cents * N4) via fixed-point (spec §5.7)
  if (Number.isInteger(t.service_cents)) {
    const adjSvcSum = scope.lines
      .filter((l) => l.included && l.line_kind === 'service')
      .reduce((a, l) => a + (l.adjusted_quoted_amount_cents ?? l.adjusted_ceiling_cents ?? 0), 0)
    const expectedAdjSvc = Number(divRoundHalfUp(BigInt(t.service_cents) * n4Scaled, SCALE4))
    if (adjSvcSum !== expectedAdjSvc) out.push(err('service_adjusted_basis', sp, 'sum(adjusted service basis) != round(service_cents*N4) [fixed-point]'))
  }
}

export function validateEnvelope(
  env: EstimateEnvelope,
  ctx?: { siblingEnvelopes?: EstimateEnvelope[] },
): Finding[] {
  const out: Finding[] = []
  if (env.schema_version !== SCHEMA_VERSION) out.push(err('schema_version', '', `schema_version must be ${SCHEMA_VERSION}`))

  env.scopes.forEach((s, i) => checkScope(s, i, out))

  if (env.content_hash !== computeContentHash(env)) out.push(err('content_hash', '', 'content_hash does not match recomputed economic content'))

  if (env.project_number !== null && env.quote_version !== null && ctx?.siblingEnvelopes) {
    const clash = ctx.siblingEnvelopes.some(
      (o) => o.project_number === env.project_number && o.quote_version === env.quote_version,
    )
    if (clash) out.push(err('quote_version_unique', '', `(project_number, quote_version) collides with an existing quote`))
  }
  return out
}
