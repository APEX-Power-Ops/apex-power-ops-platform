// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED. Switches / disconnects (NETA 7.5).
// Matched by exact STRING ONLY: a 12th ref, 'PDU (Power Distribution Unit)', also sits at firm 7.5, so a
// section match would sweep PDU. Section is NOISE here; only the ref string is authoritative.
export const SWITCH_REFS = [
  'Switch LV - Fused Disconnect',
  'Switch LV - Fused Disconnect (Open)',
  'Switch MV - Fused Disconnect',
  'Switch MV - Open',
  'Switch MV - Cutout',
  'Switch MV - Oil Insulated',
  'Switch MV - Motor Operated',
  'Switch (SF6) - Medium Voltage',
  'Switch (Pad Mount Vista) - Medium Voltage',
  'Switch HV - Open',
  'Switch HV - Motor Operated',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: candidate ref-GROUP keyed by `${SwitchType}:${VoltageClass}` plus
// per-type `${SwitchType}:unknown` (typed but no voltage -> that TYPE's refs across voltage classes), generic
// `any:${VoltageClass}` (no type token) and `any:unknown` (neither). The conservative default (Task 3 matchSwitch)
// is the FIRST ref in a type-x-voltage group; per-type :unknown / generic / no-voltage -> no default.
// R1-a: a typed switch with illegible voltage now narrows to its `${type}:unknown` group (NOT the full any:unknown
// set); voltageless still yields NO default, so this is candidate-breadth ergonomics only - never an auto-price.
// GAPS are encoded as ABSENT keys -> matchSwitch returns null -> switch_catalog_gap:
//   vacuum:* (no vacuum ref - incl. vacuum:unknown, so the :unknown widening can never resurrect it);
//   fused_disconnect:HV / cutout:HV / oil:HV / sf6:HV (HV has only Open + Motor-Operated);
//   open:LV (LV has only the fused refs). The LV non-fused gap (fused:false at LV) is handled in matchSwitch.
export const SWITCH_GROUPS: Record<string, string[]> = {
  'fused_disconnect:LV': ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)'],
  'fused_disconnect:MV': ['Switch MV - Fused Disconnect'],
  'open:MV': ['Switch MV - Open'],
  'open:HV': ['Switch HV - Open'],
  'cutout:MV': ['Switch MV - Cutout'],
  'oil:MV': ['Switch MV - Oil Insulated'],
  'motor_operated:MV': ['Switch MV - Motor Operated'],
  'motor_operated:HV': ['Switch HV - Motor Operated'],
  'sf6:MV': ['Switch (SF6) - Medium Voltage'],
  'vista:MV': ['Switch (Pad Mount Vista) - Medium Voltage'],
  // R1-a per-type :unknown groups (typed, no legible voltage -> the type's refs across voltage classes). No vacuum
  // key (vacuum is a structural gap at every voltage). All :unknown lookups yield NO default (no voltage class).
  'fused_disconnect:unknown': ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)', 'Switch MV - Fused Disconnect'],
  'open:unknown': ['Switch MV - Open', 'Switch HV - Open'],
  'cutout:unknown': ['Switch MV - Cutout'],
  'oil:unknown': ['Switch MV - Oil Insulated'],
  'motor_operated:unknown': ['Switch MV - Motor Operated', 'Switch HV - Motor Operated'],
  'sf6:unknown': ['Switch (SF6) - Medium Voltage'],
  'vista:unknown': ['Switch (Pad Mount Vista) - Medium Voltage'],
  'any:LV': ['Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)'],
  'any:MV': ['Switch MV - Fused Disconnect', 'Switch MV - Open', 'Switch MV - Cutout', 'Switch MV - Oil Insulated', 'Switch MV - Motor Operated', 'Switch (SF6) - Medium Voltage', 'Switch (Pad Mount Vista) - Medium Voltage'],
  'any:HV': ['Switch HV - Open', 'Switch HV - Motor Operated'],
  'any:unknown': [
    'Switch LV - Fused Disconnect', 'Switch LV - Fused Disconnect (Open)', 'Switch MV - Fused Disconnect',
    'Switch MV - Open', 'Switch MV - Cutout', 'Switch MV - Oil Insulated', 'Switch MV - Motor Operated',
    'Switch (SF6) - Medium Voltage', 'Switch (Pad Mount Vista) - Medium Voltage', 'Switch HV - Open', 'Switch HV - Motor Operated',
  ],
}

// Operator flips when the SME confirms the voltage-x-type -> default-ref table + the open-vs-enclosed convention + the bounded gaps.
export const SWITCH_R1_RATIFIED = false
