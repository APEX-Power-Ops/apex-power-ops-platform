import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = fs.readFileSync(path.join(HERE, 'tracer.js'), 'utf-8').replace(/\r\n/g, '\n');

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
  extract('groupByDepth', SRC),
  extract('summarizeChain', SRC),
].join('\n');

const mod = new Function(pureSrc + `
  return { parseTs, fmtDate, fmtLagHours, labelFor, groupByDepth, summarizeChain };
`)();

let ran = 0, passed = 0;
function test(name, fn) {
  ran++;
  try { fn(); passed++; console.log(`  ok  ${name}`); }
  catch (e) { console.log(`  FAIL ${name}: ${e && e.message || e}`); process.exitCode = 1; }
}

test('parseTs returns null for null/bad strings, Date for valid ISO', () => {
  assert.equal(mod.parseTs(null), null);
  assert.equal(mod.parseTs('not-a-date'), null);
  const d = mod.parseTs('2026-04-10T00:00:00Z');
  assert.ok(d instanceof Date);
  assert.equal(d.toISOString().slice(0, 10), '2026-04-10');
});

test('fmtDate handles Date, string, null', () => {
  assert.equal(mod.fmtDate(null), '—');
  assert.equal(mod.fmtDate('2026-04-10T00:00:00Z'), '2026-04-10');
  assert.equal(mod.fmtDate('nonsense'), '—');
});

test('fmtLagHours renders zero, positive, negative', () => {
  assert.equal(mod.fmtLagHours(0), '0h');
  assert.equal(mod.fmtLagHours(null), '0h');
  assert.equal(mod.fmtLagHours(4), '+4h');
  assert.equal(mod.fmtLagHours(-8), '-8h');
});

test('labelFor prefers task_code → p6_task_id → task_id → em-dash', () => {
  assert.equal(mod.labelFor('A10', 'p6-1', 't-1'), 'A10');
  assert.equal(mod.labelFor(null, 'p6-1', 't-1'), 'p6-1');
  assert.equal(mod.labelFor(null, null, 't-1'), 't-1');
  assert.equal(mod.labelFor(null, null, null), '—');
});

test('groupByDepth returns rows grouped and sorted by depth', () => {
  const edges = [
    { depth: 2, parent_task_id: 'A10' },
    { depth: 1, parent_task_id: 'A20' },
    { depth: 2, parent_task_id: 'A15' },
    { depth: 1, parent_task_id: 'A25' },
  ];
  const groups = mod.groupByDepth(edges);
  assert.equal(groups.length, 2);
  assert.equal(groups[0].depth, 1);
  assert.equal(groups[1].depth, 2);
  assert.equal(groups[0].edges.length, 2);
  assert.equal(groups[1].edges.length, 2);
  assert.equal(groups[0].edges[0].parent_task_id, 'A20');
  assert.equal(groups[0].edges[1].parent_task_id, 'A25');
});

test('groupByDepth handles empty and single-depth inputs', () => {
  assert.deepEqual(mod.groupByDepth([]), []);
  const one = mod.groupByDepth([{ depth: 1, parent_task_id: 'A' }]);
  assert.equal(one.length, 1);
  assert.equal(one[0].edges.length, 1);
});

test('summarizeChain counts unique parents and criticals', () => {
  const edges = [
    { depth: 1, parent_task_id: 'A10', parent_critical_flag: true },
    { depth: 2, parent_task_id: 'A20', parent_critical_flag: false },
    { depth: 3, parent_task_id: 'A10', parent_critical_flag: true },
  ];
  const s = mod.summarizeChain(edges);
  assert.equal(s.total, 3);
  assert.equal(s.maxDepth, 3);
  assert.equal(s.uniqueParents, 2);
  assert.equal(s.parentsOnCritical, 1);
});

test('summarizeChain returns zeros on empty input', () => {
  const s = mod.summarizeChain([]);
  assert.deepEqual(s, { total: 0, maxDepth: 0, uniqueParents: 0, parentsOnCritical: 0 });
});

console.log(`\n${passed}/${ran} pure-logic tests passed`);
if (passed !== ran) process.exit(1);