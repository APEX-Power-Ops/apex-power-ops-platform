import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver } from '../catalog/resolver'
import type { EquipmentModel } from '../catalog/types'
import { compile } from '../compile/compile'
import type { EstimateDraft } from '../schema/draft'
import type { Finding } from '../validate/findings'
import { validateEnvelope } from '../validate/validator'
import caseA from './cases/case-a-apparatus-default.json'
import caseB from './cases/case-b-labor-split-cost.json'
import caseC from './cases/case-c-m4-n4.json'
import caseD from './cases/case-d-service.json'
import caseE from './cases/case-e-excluded.json'
import caseF from './cases/case-f-penny-allocation.json'

export interface LineExpectation {
  project_intake_qty?: number
  extended_cents?: number
  adjusted_quoted_amount_cents?: number
  adjusted_ceiling_cents?: number
}

export interface ScopeExpectation {
  base_app_hours: number
  quoted_app_hours: number
  service_hours: number
  onsite_labor_cents: number
  offsite_labor_cents: number
  cost_cents: number
  service_cents: number
  pre_adjust_cents: number
  adjusted_cents: number
  lines?: Record<string, LineExpectation>
  labor_charge_cents?: Record<string, number>
}

export interface CorpusCase {
  name: string
  provenance: string
  draft: EstimateDraft
  expected: { bid_cents: number; scope_totals: Record<string, ScopeExpectation> }
}

const resolver = createCatalogResolver(seed as EquipmentModel[])

export function loadCorpusCases(): CorpusCase[] {
  return [caseA, caseB, caseC, caseD, caseE, caseF] as unknown as CorpusCase[]
}

function near(actual: number, expected: number, tol: number): boolean {
  return Math.abs(actual - expected) <= tol
}

export function runCorpusCase(c: CorpusCase): { findings: Finding[]; mismatches: string[] } {
  const env = compile(c.draft, c.draft.selected_revision_id, resolver)
  const mismatches: string[] = []
  if (env.totals.bid_cents !== c.expected.bid_cents) {
    mismatches.push(`bid_cents: got ${env.totals.bid_cents}, want ${c.expected.bid_cents}`)
  }
  for (const [scopeId, exp] of Object.entries(c.expected.scope_totals)) {
    const sc = env.scopes.find((s) => s.scope_id === scopeId)
    if (!sc) {
      mismatches.push(`scope ${scopeId} missing`)
      continue
    }
    const t = sc.scope_totals
    const checks: [string, number, number, number][] = [
      ['base_app_hours', t.base_app_hours, exp.base_app_hours, 1e-6],
      ['quoted_app_hours', t.quoted_app_hours, exp.quoted_app_hours, 1e-6],
      ['service_hours', t.service_hours, exp.service_hours, 1e-6],
      ['onsite_labor_cents', t.onsite_labor_cents, exp.onsite_labor_cents, 1],
      ['offsite_labor_cents', t.offsite_labor_cents, exp.offsite_labor_cents, 1],
      ['cost_cents', t.cost_cents, exp.cost_cents, 1],
      ['service_cents', t.service_cents, exp.service_cents, 1],
      ['pre_adjust_cents', t.pre_adjust_cents, exp.pre_adjust_cents, 1],
      ['adjusted_cents', t.adjusted_cents, exp.adjusted_cents, 1],
    ]
    for (const [field, got, want, tol] of checks) {
      if (!near(got, want, tol)) mismatches.push(`${scopeId}.${field}: got ${got}, want ${want} (tol ${tol})`)
    }

    // per-line assertions
    if (exp.lines) {
      for (const [uid, le] of Object.entries(exp.lines)) {
        const lc = sc.lines.find((l) => l.line_uid === uid)
        if (!lc) {
          mismatches.push(`${scopeId}.lines[${uid}] missing`)
          continue
        }
        if (le.project_intake_qty !== undefined && lc.project_intake_qty !== le.project_intake_qty) {
          mismatches.push(`${scopeId}.lines[${uid}].project_intake_qty: got ${lc.project_intake_qty}, want ${le.project_intake_qty}`)
        }
        if (le.extended_cents !== undefined && !near(lc.extended_cents, le.extended_cents, 1)) {
          mismatches.push(`${scopeId}.lines[${uid}].extended_cents: got ${lc.extended_cents}, want ${le.extended_cents} (tol 1)`)
        }
        if (le.adjusted_quoted_amount_cents !== undefined && !near(lc.adjusted_quoted_amount_cents ?? 0, le.adjusted_quoted_amount_cents, 1)) {
          mismatches.push(`${scopeId}.lines[${uid}].adjusted_quoted_amount_cents: got ${lc.adjusted_quoted_amount_cents}, want ${le.adjusted_quoted_amount_cents} (tol 1)`)
        }
        if (le.adjusted_ceiling_cents !== undefined && !near(lc.adjusted_ceiling_cents ?? 0, le.adjusted_ceiling_cents, 1)) {
          mismatches.push(`${scopeId}.lines[${uid}].adjusted_ceiling_cents: got ${lc.adjusted_ceiling_cents}, want ${le.adjusted_ceiling_cents} (tol 1)`)
        }
      }
    }

    // labor_charge_cents assertions
    if (exp.labor_charge_cents) {
      for (const [labor_type, cents] of Object.entries(exp.labor_charge_cents)) {
        const ch = sc.labor_charge_lines.find((c) => c.labor_type === labor_type)
        if (!ch) {
          mismatches.push(`${scopeId}.labor_charge_lines[${labor_type}] missing`)
          continue
        }
        if (!near(ch.cents, cents, 1)) {
          mismatches.push(`${scopeId}.labor_charge_lines[${labor_type}].cents: got ${ch.cents}, want ${cents} (tol 1)`)
        }
      }
      // assert sum of all labor_charge_lines.cents == onsite_labor_cents + offsite_labor_cents
      const laborSum = sc.labor_charge_lines.reduce((a, c) => a + c.cents, 0)
      const expectedLaborSum = t.onsite_labor_cents + t.offsite_labor_cents
      if (laborSum !== expectedLaborSum) {
        mismatches.push(`${scopeId}.labor_charge_lines sum: got ${laborSum}, want ${expectedLaborSum} (onsite+offsite)`)
      }
    }
  }
  return { findings: validateEnvelope(env), mismatches }
}
