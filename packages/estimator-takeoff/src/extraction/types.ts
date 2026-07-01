import type { Mounting } from '../signature/types'

export type EvidenceKind = 'one-line' | 'panel-schedule' | 'switchgear-schedule' | 'power-plan'

export interface ExtractedApparatus {
  raw: string                                   // raw label/spec text near the device
  tag?: string                                  // device identity, e.g. "MSB-P1-110-GB"
  sheet: string                                 // e.g. "E01-11"
  page: number
  bbox: [number, number, number, number]
  evidence: EvidenceKind
  busVoltageV?: number                          // nominal bus voltage if drawing-nav associated one
  block?: string                                // electrical block, e.g. "P1-110"
  mountingHint?: Mounting                        // construction evidence (schedule/symbol/operator); engine prefers this over text parsing
  candidateKind?: 'breaker' | 'transformer' | 'relay' | 'gfp' | 'instrument_transformer' | 'switch'   // 'gfp' = producer asserts a STANDALONE ground-fault protection device (honored only on a non-parent-shaped row)
}

export interface VoltageAssertion {
  voltageV: number          // engine requires Number.isInteger(voltageV) && voltageV > 0
  tags: string[]            // device tags this assertion covers (may be empty IFF sheets is non-empty)
  sheets?: string[]         // sheet ids (operator sheet-voltage; fallback - a tag assertion or detected voltage wins)
  actor?: string            // evidence-only; engine never branches on it
  note?: string             // evidence-only
  source?: 'cli' | 'gate1' | 'operator_sheet_voltage'  // evidence-only
  at?: string               // untrusted metadata; engine never trusts it for ordering/authority
}

export interface ExtractionArtifact {
  pdf: string
  extractedAt?: string                          // ISO string stamped by drawing-nav (string, not Date)
  profileWarnings?: string[]                    // legend-fallback / unknown-title notices from the extractor (see Plan 2a)
  apparatus: ExtractedApparatus[]
  voltageAssertions?: VoltageAssertion[]
}
