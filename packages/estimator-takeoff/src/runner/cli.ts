import { readFileSync, writeFileSync } from 'node:fs'
import { runFromArtifact } from './run'
import { renderReportText } from './report'

// Usage: run <artifact.json> --project <N> [--out <file>] [--allow-open-items]
function main(argv: string[]): void {
  const args = argv.slice(2)
  if (args[0] !== 'run') { process.stderr.write('usage: run <artifact.json> --project <N> [--out <file>] [--allow-open-items]\n'); process.exit(2) }
  const file = args[1]
  if (file === undefined || file.startsWith('--')) { process.stderr.write('error: missing <artifact.json>\n'); process.exit(2) }
  const pIdx = args.indexOf('--project')
  const projectNumber = pIdx >= 0 ? args[pIdx + 1] : undefined
  if (projectNumber === undefined || projectNumber.startsWith('--')) { process.stderr.write('error: --project requires a value\n'); process.exit(2) }
  const oIdx = args.indexOf('--out')
  const out = oIdx >= 0 ? args[oIdx + 1] : undefined
  if (out !== undefined && out.startsWith('--')) { process.stderr.write('error: --out requires a value\n'); process.exit(2) }
  const allowOpenItems = args.includes('--allow-open-items')

  let json: unknown
  try { json = JSON.parse(readFileSync(file, 'utf8')) }
  catch (e) { process.stderr.write(`error: cannot read or parse ${file}: ${(e as Error).message}\n`); process.exit(2) }

  const result = runFromArtifact(json, { projectNumber, allowOpenItems })
  for (const line of result.stderr) process.stderr.write(line + '\n')
  if (result.report) {
    if (out !== undefined) writeFileSync(out, JSON.stringify(result.report, null, 2))
    else process.stdout.write(renderReportText(result.report) + '\n')
  }
  process.exit(result.exitCode)
}

main(process.argv)