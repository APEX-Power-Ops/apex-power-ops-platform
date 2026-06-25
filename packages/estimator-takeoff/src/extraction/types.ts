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
}

export interface ExtractionArtifact {
  pdf: string
  extractedAt?: string                          // ISO string stamped by drawing-nav (string, not Date)
  apparatus: ExtractedApparatus[]
}
