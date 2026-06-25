export type NetaStandard = 'ATS' | 'MTS'
export type LifecycleStatus = 'active' | 'deprecated' | 'merged'
export type UnitOfIssue = 'each' | 'set'

/** Mirrors the future core.equipment_models row 1:1. `ref` is the stable identity key. */
export interface EquipmentModel {
  ref: string
  apparatus: string
  neta_section: Record<NetaStandard, string | null>
  ref_hours: Record<NetaStandard, number | null>
  unit_of_issue: UnitOfIssue
  lifecycle_status: LifecycleStatus
  merged_into_ref: string | null
}
