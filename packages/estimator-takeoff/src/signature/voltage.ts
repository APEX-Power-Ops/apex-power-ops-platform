import type { VoltageClass } from './types'

// Takeoff routing convention (NOT a universal taxonomy):
// LV < 1000 V ; MV >= 1000 V and <= 69000 V ; HV > 69000 V
export function classifyVoltage(voltageV: number | undefined): VoltageClass | undefined {
  if (voltageV === undefined) return undefined
  if (voltageV < 1000) return 'LV'
  if (voltageV <= 69000) return 'MV'
  return 'HV'
}
