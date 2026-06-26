import { describe, it, expect } from 'vitest'
import { execFileSync } from 'node:child_process'
import { writeFileSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Synthetic artifact: one matched main + one open (missing-voltage) breaker -> partial preview.
const ARTIFACT = {
  pdf: 'synthetic.pdf',
  apparatus: [
    { raw: 'MSB 4000AF/4000AT LSIG', tag: 'A', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line', busVoltageV: 480, mountingHint: 'draw_out' },
    { raw: 'MCB 100AF/100AT', tag: 'B', sheet: 'E01-11', page: 1, bbox: [0, 0, 1, 1], evidence: 'one-line' },
  ],
}

// On Linux/macOS the .bin/tsx shim is a shell script (not a node module), so we cannot invoke it
// via `node node_modules/.bin/tsx`. Use the real CJS entry directly instead.
const TSX_CJS = 'node_modules/tsx/dist/cli.cjs'

describe('runner CLI (real tsx path)', () => {
  it('runs the artifact: exits non-zero on partial without the flag, zero with it', () => {
    const f = join(mkdtempSync(join(tmpdir(), 'rrt-')), 'a.json')
    writeFileSync(f, JSON.stringify(ARTIFACT))
    const run = (extra: string[]) => {
      try { const out = execFileSync('node', [TSX_CJS, 'src/runner/cli.ts', 'run', f, '--project', 'P', ...extra], { encoding: 'utf8' }); return { code: 0, out } }
      catch (e: any) { return { code: e.status as number, out: String(e.stdout ?? '') + String(e.stderr ?? '') } }
    }
    expect(run([]).code).not.toBe(0)                  // open item, no flag -> blocked
    const ok = run(['--allow-open-items'])
    expect(ok.code).toBe(0)
    expect(ok.out).toMatch(/partial_preview/i)        // report status on stdout
  })
})
