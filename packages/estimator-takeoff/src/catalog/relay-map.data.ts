// Refs VERBATIM from estimator-core EQUIPMENT_MODELS_SEED (NETA 7.9, unit_of_issue=each).
// Note the " - " in Bus Differential and Line Protection; matching is string-keyed.
export const RELAY_TIERS = [
  'Protective Relay (Electromechanical)',
  'Protective Relay (Overcurrent Protection)',
  'Protective Relay (Feeder Protection)',
  'Protective Relay (Motor Control)',
  'Protective Relay - (Bus Differential)',
  'Protective Relay (Differential Protection)',
  'Protective Relay - (Line Protection)',
  'Protective Relay (Generator Protection)',
  'Protective Relay (Multi-function w Meter)',
] as const satisfies readonly string[]

// R1 (estimating authority) PROVISIONAL: legible dominant-role -> default tier. 'unknown' is absent
// (illegible relays carry NO default -> no-default scope_pending). String keys (RelayRole shape lands in Task 2).
export const ROLE_TO_TIER: Record<string, string> = {
  overcurrent:         'Protective Relay (Overcurrent Protection)',
  feeder:              'Protective Relay (Feeder Protection)',
  motor:               'Protective Relay (Motor Control)',
  bus_differential:    'Protective Relay - (Bus Differential)',
  differential:        'Protective Relay (Differential Protection)',
  line:                'Protective Relay - (Line Protection)',
  generator:           'Protective Relay (Generator Protection)',
  multifunction_meter: 'Protective Relay (Multi-function w Meter)',
  electromechanical:   'Protective Relay (Electromechanical)',
}

// D1 policy: standalone-dominant device types with no priced tier home -> catalog_gap until SME decides.
export const ORPHAN_ANSI: ReadonlySet<string> = new Set(['86', '79', '25', '27', '59', '81'])

// Operator flips to true when the estimator confirms the role->tier mapping + EM-vs-uP convention.
export const RELAY_R1_RATIFIED = false
