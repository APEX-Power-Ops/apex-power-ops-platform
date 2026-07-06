import type { ExtractionArtifact, EvidenceKind } from './types'
import type { Mounting } from '../signature/types'

const EVIDENCE: ReadonlySet<string> = new Set<EvidenceKind>(['one-line', 'panel-schedule', 'switchgear-schedule', 'power-plan'])
const MOUNTING: ReadonlySet<string> = new Set<Mounting>(['draw_out', 'electrically_operated', 'insulated_case', 'molded_case', 'panelboard', 'unknown'])
const MAX_APPARATUS = 5000

export class ArtifactContractError extends Error {
  constructor(public path: string, public expected: string, public got: string) {
    super(`artifact contract violation at ${path}: expected ${expected}, got ${got}`)
    this.name = 'ArtifactContractError'
  }
}

function preview(v: unknown): string {
  if (v === undefined) return 'undefined'
  try { return JSON.stringify(v)?.slice(0, 60) ?? String(v) } catch { return String(v) }
}
function fail(path: string, expected: string, v: unknown): never {
  throw new ArtifactContractError(path, expected, preview(v))
}
const isStr = (v: unknown) => typeof v === 'string'
const nonEmptyStr = (v: unknown) => isStr(v) && (v as string).length > 0
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)

export function parseArtifact(json: unknown): ExtractionArtifact {
  if (!isObj(json)) fail('', 'object', json)
  const a = json as Record<string, unknown>
  if (!nonEmptyStr(a['pdf'])) fail('pdf', 'non-empty string', a['pdf'])
  if (a['extractedAt'] !== undefined && !isStr(a['extractedAt'])) fail('extractedAt', 'string', a['extractedAt'])
  if (a['profileWarnings'] !== undefined && (!Array.isArray(a['profileWarnings']) || !a['profileWarnings'].every(isStr))) fail('profileWarnings', 'string[]', a['profileWarnings'])
  if (!Array.isArray(a['apparatus'])) fail('apparatus', 'array', a['apparatus'])
  const apparatus = a['apparatus'] as unknown[]
  if (apparatus.length > MAX_APPARATUS) fail('apparatus', `<= ${MAX_APPARATUS} rows`, apparatus.length)
  apparatus.forEach((row, i) => validateRow(row, `apparatus[${i}]`))
  if (a['voltageAssertions'] !== undefined) {
    if (!Array.isArray(a['voltageAssertions'])) fail('voltageAssertions', 'array', a['voltageAssertions'])
    const vas = a['voltageAssertions'] as unknown[]
    vas.forEach((va, i) => validateAssertionShape(va, `voltageAssertions[${i}]`))
  }
  return json as unknown as ExtractionArtifact
}

function validateRow(row: unknown, p: string): void {
  if (!isObj(row)) fail(p, 'object', row)
  const r = row as Record<string, unknown>
  if (!nonEmptyStr(r['raw'])) fail(`${p}.raw`, 'non-empty string', r['raw'])
  if (!nonEmptyStr(r['sheet'])) fail(`${p}.sheet`, 'non-empty string', r['sheet'])
  if (!(typeof r['page'] === 'number' && Number.isInteger(r['page']) && (r['page'] as number) >= 0)) fail(`${p}.page`, 'integer >= 0', r['page'])
  const bbox = r['bbox']
  if (!Array.isArray(bbox) || bbox.length !== 4 || !bbox.every((n) => typeof n === 'number' && Number.isFinite(n))) fail(`${p}.bbox`, '[number,number,number,number]', bbox)
  if (!EVIDENCE.has(r['evidence'] as string)) fail(`${p}.evidence`, [...EVIDENCE].join('|'), r['evidence'])
  if (r['tag'] !== undefined && !isStr(r['tag'])) fail(`${p}.tag`, 'string', r['tag'])
  if (r['block'] !== undefined && !isStr(r['block'])) fail(`${p}.block`, 'string', r['block'])
  if (r['busVoltageV'] !== undefined && !(typeof r['busVoltageV'] === 'number' && Number.isInteger(r['busVoltageV']) && (r['busVoltageV'] as number) > 0)) fail(`${p}.busVoltageV`, 'positive integer', r['busVoltageV'])
  if (r['mountingHint'] !== undefined && !MOUNTING.has(r['mountingHint'] as string)) fail(`${p}.mountingHint`, [...MOUNTING].join('|'), r['mountingHint'])
  // candidateKind: 'breaker' | 'transformer' | 'relay' | 'gfp' | 'instrument_transformer' | 'switch' | 'transfer_switch'
  if (r['candidateKind'] !== undefined && r['candidateKind'] !== 'breaker' && r['candidateKind'] !== 'transformer' && r['candidateKind'] !== 'relay' && r['candidateKind'] !== 'gfp' && r['candidateKind'] !== 'instrument_transformer' && r['candidateKind'] !== 'switch' && r['candidateKind'] !== 'transfer_switch') fail(`${p}.candidateKind`, "'breaker'|'transformer'|'relay'|'gfp'|'instrument_transformer'|'switch'|'transfer_switch'", r['candidateKind'])
}

function validateAssertionShape(va: unknown, p: string): void {
  if (!isObj(va)) fail(p, 'object', va)
  const v = va as Record<string, unknown>
  if (typeof v['voltageV'] !== 'number') fail(`${p}.voltageV`, 'number', v['voltageV'])
  const tags = v['tags']; const sheets = v['sheets']
  if (!Array.isArray(tags) || !(tags as unknown[]).every(isStr)) fail(`${p}.tags`, 'string[]', tags)
  if (sheets !== undefined && (!Array.isArray(sheets) || !(sheets as unknown[]).every(isStr))) fail(`${p}.sheets`, 'string[]', sheets)
  if ((tags as unknown[]).length === 0 && !(Array.isArray(sheets) && (sheets as unknown[]).length > 0)) fail(`${p}.tags`, 'non-empty tags or sheets', va)
}