// Ref VERBATIM from estimator-core EQUIPMENT_MODELS_SEED (NETA 7.14, unit_of_issue=each).
// STANDALONE ground-fault protection device/system only. Matched by exact STRING, never by the firm
// section "7.14" (the firm catalog overloads 7.14 onto Current-Transformer refs - match the string).
export const GFP_REF = 'Ground Fault Protection Device LV'

// Single-ref-covers-all convention is PROVISIONAL until the SME confirms whether a dedicated
// GFPE / ground-fault relay / sensor ever prices differently from this one device ref (D1).
// GFP never auto-prices, so provisional is fail-closed.
export const GFP_R1_RATIFIED = false
