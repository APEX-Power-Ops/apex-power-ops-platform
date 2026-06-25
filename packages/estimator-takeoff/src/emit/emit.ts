import { buildNativeEnvelope, type NativeEnvelopeInput, type NetaStandard } from '@apex/estimator-core'
import type { ExtractionArtifact } from '../extraction/types'
import { normalizeApparatus } from '../signature/normalize'
import { quantify } from '../quantify/quantify'
import { matchBreaker } from '../catalog/breaker-map'
import type { MatchedLine, TakeoffResult, UnmatchedCandidate } from '../buckets/types'

export function runTakeoff(artifact: ExtractionArtifact): TakeoffResult {
  const sigs = artifact.apparatus.map(normalizeApparatus).filter((s): s is NonNullable<typeof s> => s !== null)
  const { lines, locationOnly } = quantify(sigs)

  const matchedLines: MatchedLine[] = []
  const unmatchedCandidates: UnmatchedCandidate[] = []
  for (const line of lines) {
    const ref = matchBreaker(line.signature)
    if (ref) matchedLines.push({ ref, qty: line.qty, block: line.signature.source.sheet, line })
    else unmatchedCandidates.push({ reason: `no catalog rule for ${line.signature.mounting}/${line.signature.functions.join('')}`, line })
  }
  const operatorQuestions = locationOnly.map((s) => ({
    question: `Device ${s.tag ?? '(untagged)'} appears only on a non-authoritative sheet — include it?`,
    context: `${s.source.sheet} (${s.source.evidence})`,
  }))
  return { matchedLines, unmatchedCandidates, operatorQuestions }
}

export function emitEnvelope(result: TakeoffResult, opts: { projectNumber: string }) {
  // group matched lines into scopes by block; emit ONLY catalog {ref, qty} lines (fail-closed)
  const byScope = new Map<string, NativeEnvelopeInput['scopes'][number]>()
  for (const m of result.matchedLines) {
    const name = `Block ${m.block}`
    const scope = byScope.get(name) ?? { name, netaStandard: 'ATS' as NetaStandard, lines: [] }
    scope.lines.push({ ref: m.ref, qty: m.qty, designation: m.line.signature.tag, notes: `from ${m.line.sources[0]?.sheet}` })
    byScope.set(name, scope)
  }
  const input: NativeEnvelopeInput = { projectNumber: opts.projectNumber, scopes: [...byScope.values()] }
  return buildNativeEnvelope(input)
}
