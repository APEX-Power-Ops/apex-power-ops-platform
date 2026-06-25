import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver, type CatalogResolver } from '../catalog/resolver'
import type { EquipmentModel, NetaStandard } from '../catalog/types'
import { compile } from '../compile/compile'
import type { EstimateEnvelope } from '../schema/envelope'
import { makeDraft, type ScopeDraft } from '../schema/draft'
import type { Finding } from '../validate/findings'
import { validateEnvelope } from '../validate/validator'

/** The bundled equipment-model catalog the native renderer authors against (mirrors core.equipment_models). */
export const EQUIPMENT_MODELS_SEED = seed as EquipmentModel[]

/** A resolver over the bundled seed catalog. */
export function createDefaultCatalogResolver(): CatalogResolver {
  return createCatalogResolver(EQUIPMENT_MODELS_SEED)
}

export interface NativeLineInput {
  ref: string
  qty: number
  designation?: string
  notes?: string
  description?: string
}

export interface NativeScopeInput {
  name: string
  netaStandard: NetaStandard
  lines: NativeLineInput[]
}

export interface NativeEnvelopeInput {
  projectNumber: string
  quoteVersion?: number
  scopes: NativeScopeInput[]
}

/**
 * Author a compiled, native EstimateEnvelope from a minimal line list. The result reconciles BY
 * CONSTRUCTION (it is produced by `compile`), so the server's `validate_envelope` accepts it: every
 * scope has M4=1, N4=1, catalog lines (`base_qty === project_intake_qty`), and 100% of the scope's
 * catalog hours allocated to onsite blended labor at the baseline rate — which yields a non-zero
 * `onsite_labor_cents` and therefore a non-zero, reconciling `bid_cents`.
 *
 * `source_kind`, `project_number`, and `quote_version` are passed through `CompileOptions` so the
 * single content_hash is computed over the final envelope (no post-compile mutation).
 */
export function buildNativeEnvelope(input: NativeEnvelopeInput): {
  envelope: EstimateEnvelope
  findings: Finding[]
} {
  const resolver = createDefaultCatalogResolver()

  const scopes: ScopeDraft[] = input.scopes.map((s, si) => ({
    scope_id: `S${si + 1}`,
    name: s.name,
    neta_standard: s.netaStandard,
    replication_m4: 1,
    adjustment_multiplier_n4: 1,
    // All catalog hours flow to onsite blended labor at the baseline rate — the same allocation the
    // corpus uses (case-a), guaranteeing onsite_labor_cents > 0 when the scope carries any hours.
    labor_allocation: [{ labor_type: 'onsite_blended_10hr', pct_of_app: 1 }],
    lines: s.lines.map((l, li) => ({
      line_uid: `S${si + 1}:r${li + 1}`,
      line_kind: 'catalog' as const,
      included: true,
      equipment_model_ref: l.ref,
      base_qty: l.qty,
      expansion_policy: 'one_unit_per_qty' as const,
      designation: l.designation,
      notes: l.notes,
      description: l.description,
    })),
  }))

  const draft = makeDraft({
    draft_id: `native-${input.projectNumber}`,
    estimator_ref: input.projectNumber,
    scopes,
  })

  const envelope = compile(draft, draft.selected_revision_id, resolver, {
    sourceKind: 'native',
    projectNumber: input.projectNumber,
    quoteVersion: input.quoteVersion ?? 1,
  })

  const findings = validateEnvelope(envelope)
  return { envelope, findings }
}
