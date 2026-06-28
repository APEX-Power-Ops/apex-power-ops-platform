// Refs verbatim from estimator-core EQUIPMENT_MODELS_SEED. Groups = the priced scope tiers per coolant (D3: power dry + oil only).
export const DRY_GROUP = [
  'Transformer - Dry Type (TTR/IR)',
  'Transformer - Dry Type (TTR/WR/IR)',
  'Transformer - Dry Type (TTR/IR/WR/PF)',
] as const satisfies readonly string[]
export const OIL_GROUP = [
  'Transformer - Pad Mount Oil (TTR/WR/IR)',
  'Transformer - Pad Mount Oil (TTR/IR/WR/PF/Oil)',
] as const satisfies readonly string[]
// R1 (estimating authority). If NOT operator-ratified, leave the PLACEHOLDER below (fails Step-4 ratify check).
export const DRY_DEFAULT_REF: string = 'Transformer - Dry Type (TTR/WR/IR)'    // [operator lean]
export const OIL_DEFAULT_REF: string = 'Transformer - Pad Mount Oil (TTR/WR/IR)' // [operator lean]
export const R1_RATIFIED = false   // operator flips to true when the two tiers are confirmed
