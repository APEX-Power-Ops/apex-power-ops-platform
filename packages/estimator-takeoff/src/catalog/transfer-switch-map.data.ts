export const TRANSFER_REFS = [
  'Automatic Transfer Switch - (IR/DLRO)',
  'Automatic Transfer Switch - Iso Bypass (IR/DLRO)',
  'Manual Transfer Switch - (IR/DLRO)',
] as const

// R1 PROVISIONAL until the estimating authority confirms (TRANSFER_R1_RATIFIED=false).
export const TRANSFER_GROUPS: Record<'automatic' | 'manual' | 'unknown', string[]> = {
  automatic: ['Automatic Transfer Switch - (IR/DLRO)', 'Automatic Transfer Switch - Iso Bypass (IR/DLRO)'],
  manual: ['Manual Transfer Switch - (IR/DLRO)'],
  unknown: ['Automatic Transfer Switch - (IR/DLRO)', 'Manual Transfer Switch - (IR/DLRO)'],
  // ABSENT (deliberate gaps): 'static'; manual+bypassIsolation; MV transfer
}
export const TRANSFER_R1_RATIFIED = false
