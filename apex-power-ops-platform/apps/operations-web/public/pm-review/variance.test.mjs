import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = fs.readFileSync(path.join(HERE, 'variance.js'), 'utf-8').replace(/\r\n/g, '\n');

function extract(name, src) {
  const re = new RegExp(`\\n  function ${name}\\b[\\s\\S]*?\\n  \\}\\n`, 'm');
  const m = src.match(re);
  if (!m) throw new Error(`could not extract function ${name}`);
  return m[0];
}

const pureSrc = [
  extract('parseTs', SRC),
  extract('fmtDate', SRC),
  extract('labelFor', SRC),
  extract('fmtVarianceHours', SRC),
  extract('fmtVarianceDays', SRC),
  extract('classifyVariance', SRC),
  extract('sortByFinishVariance', SRC),
  extract('summarizeVariance', SRC),
].join('\n');

const mod = new Function(pureSrc + `
  return {
    parseTs, fmtDate, labelFor,
    fmtVarianceHours, fmtVarianceDays,
    classifyVariance, sortByFinishVariance, summarizeVariance,
  };
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

test('labelFor prefers task_code → p6_task_id → task_id → em-dash', () => {
  assert.equal(mod.labelFor('A10', 'p6-1', 't-1'), 'A10');
  assert.equal(mod.labelFor(null, 'p6-1', 't-1'), 'p6-1');
  assert.equal(mod.labelFor(null, null, 't-1'), 't-1');
  assert.equal(mod.labelFor(null, null, null), '—');
});

test('fmtVarianceHours returns em-dash for null/undefined/empty/NaN', () => {
  assert.equal(mod.fmtVarianceHours(null), '—');
  assert.equal(mod.fmtVarianceHours(undefined), '—');
  assert.equal(mod.fmtVarianceHours(''), '—');
  assert.equal(mod.fmtVarianceHours('not a number'), '—');
  assert.equal(mod.fmtVarianceHours(NaN), '—');
});

test('fmtVarianceHours renders signed hours with one decimal', () => {
  assert.equal(mod.fmtVarianceHours(0), '0h');
  assert.equal(mod.fmtVarianceHours(0.0001), '0h');
  assert.equal(mod.fmtVarianceHours(4), '+4.0h');
  assert.equal(mod.fmtVarianceHours(-8.25), '-8.3h');
});

test('fmtVarianceDays collapses to days above 24h, preserves null', () => {
  assert.equal(mod.fmtVarianceDays(null), '—');
  assert.equal(mod.fmtVarianceDays(0), '0d');
  assert.equal(mod.fmtVarianceDays(12), '+12.0h');
  assert.equal(mod.fmtVarianceDays(-12), '-12.0h');
  assert.equal(mod.fmtVarianceDays(48), '+2.0d');
  assert.equal(mod.fmtVarianceDays(-72), '-3.0d');
});

test('classifyVariance returns no-baseline when has_baseline is false', () => {
  assert.equal(mod.classifyVariance({ has_baseline: false }), 'no-baseline');
  assert.equal(mod.classifyVariance({ has_baseline: false, finish_variance_hours: 99 }), 'no-baseline');
  assert.equal(mod.classifyVariance({}), 'no-baseline');
  assert.equal(mod.classifyVariance(null), 'no-baseline');
});

test('classifyVariance returns no-baseline when finish_variance is null even if has_baseline', () => {
  assert.equal(mod.classifyVariance({ has_baseline: true, finish_variance_hours: null }), 'no-baseline');
});

test('classifyVariance distinguishes slipping / ahead / on-plan by finish variance', () => {
  assert.equal(mod.classifyVariance({ has_baseline: true, finish_variance_hours: 48 }), 'slipping');
  assert.equal(mod.classifyVariance({ has_baseline: true, finish_variance_hours: -48 }), 'ahead');
  assert.equal(mod.classifyVariance({ has_baseline: true, finish_variance_hours: 0 }), 'on-plan');
  assert.equal(mod.classifyVariance({ has_baseline: true, finish_variance_hours: 0.2 }), 'on-plan');
});

test('sortByFinishVariance desc puts worst slip first, nulls last, ties stable', () => {
  const rows = [
    { schedule_task_id: 'A', finish_variance_hours: 10 },
    { schedule_task_id: 'B', finish_variance_hours: null },
    { schedule_task_id: 'C', finish_variance_hours: 48 },
    { schedule_task_id: 'D', finish_variance_hours: 48 },
    { schedule_task_id: 'E', finish_variance_hours: -12 },
  ];
  const out = mod.sortByFinishVariance(rows, 'desc');
  assert.deepEqual(out.map(r => r.schedule_task_id), ['C', 'D', 'A', 'E', 'B']);
});

test('sortByFinishVariance asc puts best lead first, nulls last', () => {
  const rows = [
    { schedule_task_id: 'A', finish_variance_hours: 10 },
    { schedule_task_id: 'B', finish_variance_hours: null },
    { schedule_task_id: 'C', finish_variance_hours: -48 },
    { schedule_task_id: 'D', finish_variance_hours: 0 },
  ];
  const out = mod.sortByFinishVariance(rows, 'asc');
  assert.deepEqual(out.map(r => r.schedule_task_id), ['C', 'D', 'A', 'B']);
});

test('summarizeVariance partitions rows into slipping / ahead / on-plan / no-baseline', () => {
  const rows = [
    { has_baseline: true, finish_variance_hours: 48 },
    { has_baseline: true, finish_variance_hours: 0 },
    { has_baseline: true, finish_variance_hours: -12 },
    { has_baseline: false, finish_variance_hours: null },
    { has_baseline: true, finish_variance_hours: 96 },
    { has_baseline: true, finish_variance_hours: -48 },
  ];
  const s = mod.summarizeVariance(rows);
  assert.equal(s.total, 6);
  assert.equal(s.withBaseline, 5);
  assert.equal(s.noBaseline, 1);
  assert.equal(s.slipping, 2);
  assert.equal(s.ahead, 2);
  assert.equal(s.onPlan, 1);
  assert.equal(s.worstSlipHours, 96);
  assert.equal(s.bestLeadHours, -48);
});

test('summarizeVariance returns clean zeros on empty and all-no-baseline inputs', () => {
  const empty = mod.summarizeVariance([]);
  assert.deepEqual(empty, {
    total: 0, withBaseline: 0, noBaseline: 0,
    slipping: 0, ahead: 0, onPlan: 0,
    worstSlipHours: null, bestLeadHours: null,
  });
  const s = mod.summarizeVariance([
    { has_baseline: false, finish_variance_hours: null },
    { has_baseline: false, finish_variance_hours: null },
  ]);
  assert.equal(s.total, 2);
  assert.equal(s.withBaseline, 0);
  assert.equal(s.noBaseline, 2);
  assert.equal(s.slipping, 0);
  assert.equal(s.worstSlipHours, null);
  assert.equal(s.bestLeadHours, null);
});

console.log(`\n${passed}/${ran} pure-logic tests passed`);
if (passed !== ran) process.exit(1);