export type Severity = 'error' | 'warning'

export interface Finding {
  code: string
  severity: Severity
  path: string
  message: string
}

export function err(code: string, path: string, message: string): Finding {
  return { code, severity: 'error', path, message }
}
