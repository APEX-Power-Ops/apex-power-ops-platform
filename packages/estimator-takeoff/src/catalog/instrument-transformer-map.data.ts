// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED. Instrument transformers (CT/VT/CCVT, NETA 7.10).
// Matched by exact STRING ONLY: the firm neta_section for these scatters across 7.1/7.6/7.14/7.15 (NONE at
// canonical 7.10) and is overloaded with unrelated refs - section is NOISE here.
export const ITX_REFS = [
  'Current Transformer - Bushing HV/MV',
  'Current Transformer - Bushing, HV/MV (Set)',
  'Current Transformer LV - Set of 3',
  'Current Transformer MV - Set of 3',
  'Potential Transformer - MV',
  'Potential Transformer - MV Set',
  'Potential Transformer (set)',
  'CCVT Voltage Transformer - Individual',
  'CCVT Voltage Transformer - Set of 3',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: candidate ref-GROUP keyed by `${itxType}:${voltageClass|'unknown'}`.
// Individual + set variants are BOTH offered (the operator picks packaging at Gate-2). The Bushing HV/MV refs
// cover HV and MV CT. PT is MV-specific; there is NO priced LV/HV PT ref, so vt:LV / vt:HV are INTENTIONALLY
// EMPTY -> instrument_transformer_catalog_gap (a bounded V1 gap per spec R1). The generic "Potential Transformer
// (set)" is offered ONLY for vt:unknown (voltage absent -> wider group). CCVT is voltage-agnostic.
// CRITICAL: an EMPTY group ([]) is NOT the same as a MISSING key. matchInstrumentTransformer falls back to the
// `:unknown` group ONLY on a missing (undefined) key; an explicit [] yields null -> catalog_gap. Keep vt:LV / vt:HV
// present-and-empty so a KNOWN non-MV voltage fails closed instead of silently borrowing the vt:unknown set.
export const ITX_GROUPS: Record<string, string[]> = {
  'ct:LV': ['Current Transformer LV - Set of 3'],
  'ct:MV': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)', 'Current Transformer MV - Set of 3'],
  'ct:HV': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)'],
  'ct:unknown': ['Current Transformer - Bushing HV/MV', 'Current Transformer - Bushing, HV/MV (Set)', 'Current Transformer LV - Set of 3', 'Current Transformer MV - Set of 3'],
  'vt:MV': ['Potential Transformer - MV', 'Potential Transformer - MV Set'],
  'vt:LV': [],   // bounded catalog gap: no priced LV PT ref (spec R1) - present-and-empty -> catalog_gap, never vt:unknown fallback
  'vt:HV': [],   // bounded catalog gap: no priced HV PT ref (spec R1) - present-and-empty -> catalog_gap, never vt:unknown fallback
  'vt:unknown': ['Potential Transformer - MV', 'Potential Transformer - MV Set', 'Potential Transformer (set)'],
  'ccvt:LV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:MV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:HV': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
  'ccvt:unknown': ['CCVT Voltage Transformer - Individual', 'CCVT Voltage Transformer - Set of 3'],
}

// Operator flips when the SME confirms the type x voltage -> default-ref table + the set/each counting convention.
export const ITX_R1_RATIFIED = false
