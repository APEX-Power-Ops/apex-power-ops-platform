import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = fs.readFileSync(path.join(HERE, 'drivers.js'), 'utf-8').replace(/\r\n/g, '\n');

function extract(name, src) {
  const re = new RegExp(`\\n  function ${name}\\b[\\s\\S]*?\\n  \\}\\n`, 'm');
  const m = src.match(re);
  if (!m) throw new Error(`could not extract function ${name}`);
  return m[0];
}

const pureSrc = [
  extract('parseTs', SRC),
  extract('fmtDate', SRC),
  extract('fmtLagHours', SRC),
  extract('labelFor', SRC),
  extract('summarizeEdges', SRC),
].join('\n');

const mod = new Function(pureSrc + `
  return { parseTs, fmtDate, fmtLagHours, labelFor, summarizeEdges };
`)();

let ran = 0, passed = 0;
function test(name, fn) {
  ran++;
  try { fn(); passed++; console.log(`  ok  ${name}`); }
  catch (e) { console.log(`  FAIL ${name}: ${e && e.message || e}`); process.exitCode = 1; }
}

test('parseTs returns null for null, undefined, bad strings', () => {
  assert.equal(mod.parseTs(null), null);
  assert.equal(mod.parseTs(undefined), null);
  assert.equal(mod.parseTs(''), null);
  assert.equal(mod.parseTs('not-a-date'), null);
});

test('parseTs returns a Date for ISO strings', () => {
  const d = mod.parseTs('2026-04-10T07:00:00Z');
  assert.ok(d instanceof Date);
  assert.equal(d.toISOString().slice(0, 10), '2026-04-10');
});

test('fmtDate handles Date, ISO string, and null/undefined', () => {
  assert.equal(mod.fmtDate(null), '—');
  assert.equal(mod.fmtDate(undefined), '—');
  assert.equal(mod.fmtDate('2026-04-10T07:00:00Z'), '2026-04-10');
  assert.equal(mod.fmtDate(new Date('2026-04-10T07:00:00Z')), '2026-04-10');
  assert.equal(mod.fmtDate('not-a-date'), '—');
});

test('fmtLagHours renders zero, positive, and negative hours cleanly', () => {
  assert.equal(mod.fmtLagHours(0), '0h');
  assert.equal(mod.fmtLagHours(null), '0h');
  assert.equal(mod.fmtLagHours(undefined), '0h');
  assert.equal(mod.fmtLagHours(8), '+8h');
  assert.equal(mod.fmtLagHours(-4), '-4h');
});

test('fmtLagHours falls through to 0h on non-numeric input', () => {
  assert.equal(mod.fmtLagHours('abc'), '0h');
});

test('labelFor prefers task_code, falls back to p6_task_id, then task_id', () => {
  assert.equal(mod.labelFor('A10', 'p6-7001', 'task-1'), 'A10');
  assert.equal(mod.labelFor(null, 'p6-7001', 'task-1'), 'p6-7001');
  assert.equal(mod.labelFor('', '', 'task-1'), 'task-1');
  assert.equal(mod.labelFor(null, null, null), '—');
  assert.equal(mod.labelFor(undefined, undefined, undefined), '—');
});

test('summarizeEdges tallies driven-on-critical and signed-lag counts', () => {
  const edges = [
    { driven_critical_flag: true, lag_hours: 0 },
    { driven_critical_flag: true, lag_hours: 8 },
    { driven_critical_flag: false, lag_hours: -4 },
    { driven_critical_flag: false, lag_hours: 0 },
  ];
  const s = mod.summarizeEdges(edges);
  assert.equal(s.total, 4);
  assert.equal(s.drivenOnCritical, 2);
  assert.equal(s.withPositiveLag, 1);
  assert.equal(s.withNegativeLag, 1);
});

test('summarizeEdges handles empty input without exploding', () => {
  const s = mod.summarizeEdges([]);
  assert.deepEqual(s, {
    total: 0,
    drivenOnCritical: 0,
    withPositiveLag: 0,
    withNegativeLag: 0,
  });
});

console.log(`\n${passed}/${ran} pure-logic tests passed`);
if (passed !== ran) process.exit(1);