import type { EquipmentModel, NetaStandard } from './types'

export interface CatalogResolver {
  resolve(ref: string): EquipmentModel
  tryResolve(ref: string): EquipmentModel | null
  refHours(ref: string, standard: NetaStandard): number
}

export function createCatalogResolver(seed: EquipmentModel[]): CatalogResolver {
  const byRef = new Map<string, EquipmentModel>()
  for (const m of seed) {
    if (byRef.has(m.ref)) throw new Error(`catalog: duplicate ref ${m.ref}`)
    byRef.set(m.ref, m)
  }

  function resolve(ref: string): EquipmentModel {
    let cur = byRef.get(ref)
    if (!cur) throw new Error(`catalog: unknown ref ${ref}`)
    const seen = new Set<string>([ref])
    while (cur.lifecycle_status === 'merged') {
      const next = cur.merged_into_ref
      if (!next) throw new Error(`catalog: merged ref ${cur.ref} has no merge target`)
      if (seen.has(next)) throw new Error(`catalog: merge cycle at ${next}`)
      const resolved = byRef.get(next)
      if (!resolved) throw new Error(`catalog: ${cur.ref} merge target ${next} missing`)
      seen.add(next)
      cur = resolved
    }
    return cur
  }

  function tryResolve(ref: string): EquipmentModel | null {
    return byRef.has(ref) ? resolve(ref) : null
  }

  function refHours(ref: string, standard: NetaStandard): number {
    const m = resolve(ref)
    const h = m.ref_hours[standard]
    if (h === null || h === undefined) {
      throw new Error(`catalog: ref ${m.ref} does not apply to standard ${standard}`)
    }
    return h
  }

  return { resolve, tryResolve, refHours }
}
