import { describe, expect, it } from 'vitest'
import { loadCorpusCases, runCorpusCase } from './harness'

describe('golden-workbook corpus (acceptance gate)', () => {
  for (const c of loadCorpusCases()) {
    it(`${c.name}: reproduces within tolerance and validates clean`, () => {
      const { findings, mismatches } = runCorpusCase(c)
      expect(mismatches).toEqual([])
      expect(findings).toEqual([])
    })
  }
})
