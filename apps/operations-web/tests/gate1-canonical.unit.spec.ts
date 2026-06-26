import { expect, test } from '@playwright/test'
import { canonicalJson, sha256Hex } from '../lib/gate1-canonical'

test('canonicalJson is key-order independent', () => {
  expect(canonicalJson({ b: 1, a: 2 })).toBe(canonicalJson({ a: 2, b: 1 }))
})

test('canonicalJson sorts nested object keys and preserves array order', () => {
  expect(canonicalJson({ z: [3, { y: 1, x: 2 }], a: 1 })).toBe('{"a":1,"z":[3,{"x":2,"y":1}]}')
})

test('canonicalJson preserves number and string fidelity', () => {
  expect(canonicalJson({ n: 480, s: 'MSB-1' })).toBe('{"n":480,"s":"MSB-1"}')
})

test('sha256Hex is reproducible and 64 hex chars', async () => {
  const a = await sha256Hex('{"a":1}')
  expect(a).toBe(await sha256Hex('{"a":1}'))
  expect(a).toMatch(/^[0-9a-f]{64}$/)
})

test('sha256Hex matches a known vector', async () => {
  expect(await sha256Hex('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
})
