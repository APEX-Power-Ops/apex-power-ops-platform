import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = fs.readFileSync(path.join(HERE, 'schedule.js'), 'utf-8').replace(/\r\n/g, '\n');

function extract(name, src) {
  const re = new RegExp(`\\n  function ${name}\\b[\\s\\S]*?\\n  \\}\\n`, 'm');
  const m = src.match(re);
  if (!m) throw new Error(`could not extract function ${name}`);
  return m[0];
}

const pureSrc = [
  extract('dayFloor', SRC),
  extract('daysBetween', SRC),
  extract('parseTs', SRC),
  extract('fmtDate', SRC),
  extract('computeRange', SRC),
  extract('buildRows', SRC),
  extract('taskRowIndex', SRC),
  extract('relEdges', SRC),
  extract('connectorPath', SRC),
  extract('baselineOverlayFor', SRC),
  extract('baselineVarianceDays', SRC),
].join('\n');

const prelude = `
  const MS_PER_DAY = 24 * 3600 * 1000;
  const PX_PER_DAY = 14;
  const ROW_HEIGHT = 28;
  const BAR_HEIGHT = 16;
  const HEADER_HEIGHT = 40;
  const LEFT_PANEL_WIDTH = 420;
  const CHART_PADDING_RIGHT = 40;
`;

const mod = new Function(prelude + pureSrc + `
  return { dayFloor, daysBetween, parseTs, fmtDate, computeRange, buildRows, taskRowIndex, relEdges, connectorPath, baselineOverlayFor, baselineVarianceDays };
`)();

let ran = 0, passed = 0;
function test(name, fn) {
  ran++;
  try { fn(); passed++; console.log(`  ok  ${name}`); }
  catch (e) { console.log(`  FAIL ${name}: ${e && e.message || e}`); process.exitCode = 1; }
}

test('relEdges maps FS/SS/FF/SF correctly', () => {
  assert.deepEqual(mod.relEdges('FS'), ['finish', 'start']);
  assert.deepEqual(mod.relEdges('SS'), ['start', 'start']);
  assert.deepEqual(mod.relEdges('FF'), ['finish', 'finish']);
  assert.deepEqual(mod.relEdges('SF'), ['start', 'finish']);
  assert.deepEqual(mod.relEdges('XX'), ['finish', 'start']);
});

test('connectorPath produces a valid three-segment SVG path', () => {
  const geom = new Map([
    ['a', { x: 100, y: 50, w: 40 }],
    ['b', { x: 200, y: 80, w: 40 }],
  ]);
  const xFor = (id, edge) => edge === 'start' ? geom.get(id).x : geom.get(id).x + geom.get(id).w;
  const yFor = (id) => geom.get(id).y + 8;
  const d = mod.connectorPath('a', 'b', 'FS', xFor, yFor);
  assert.match(d, /^M 140 58 L \d+ 58 L \d+ 88 L 200 88$/);
});

test('buildRows preserves WBS hierarchy and assigns task depth', () => {
  const wbs = [
    { id: 'w1', parent_wbs_id: null, name: 'Root A', seq: 1 },
    { id: 'w2', parent_wbs_id: 'w1', name: 'Child A.1', seq: 1 },
    { id: 'w3', parent_wbs_id: null, name: 'Root B', seq: 2 },
  ];
  const tasks = [
    { schedule_task_id: 't1', schedule_wbs_id: 'w2', task_name: 'T1', planned_start: '2026-04-01' },
    { schedule_task_id: 't2', schedule_wbs_id: 'w3', task_name: 'T2', planned_start: '2026-04-10' },
    { schedule_task_id: 't3', schedule_wbs_id: null, task_name: 'Orphan', planned_start: '2026-04-05' },
  ];
  const rows = mod.buildRows(wbs, tasks);
  const kinds = rows.map(r => r.kind + ':' + (r.wbs ? r.wbs.id : '') + (r.task ? r.task.schedule_task_id : ''));
  assert.deepEqual(kinds, [
    'wbs:w1',
    'wbs:w2',
    'task:w2t1',
    'wbs:w3',
    'task:w3t2',
    'wbs:__orphan__',
    'task:t3',
  ]);
  const depths = rows.map(r => r.depth);
  assert.deepEqual(depths, [0, 1, 2, 0, 1, 0, 1]);
});

test('computeRange pads the span with a week on either side', () => {
  const tasks = [
    { planned_start: '2026-04-10', planned_finish: '2026-04-15' },
    { planned_start: '2026-04-12', planned_finish: '2026-04-20' },
  ];
  const r = mod.computeRange(tasks, '2026-04-14T00:00:00Z');
  const spanDays = (r.end - r.start) / (24 * 3600 * 1000);
  assert.equal(spanDays, 24);
  assert.equal(r.start.toISOString().slice(0, 10), '2026-04-03');
  assert.equal(r.end.toISOString().slice(0, 10), '2026-04-27');
});

test('computeRange falls back to a 30-day window when tasks have no dates', () => {
  const r = mod.computeRange([], null);
  const span = (r.end - r.start) / (24 * 3600 * 1000);
  assert.equal(span, 30);
});

test('taskRowIndex maps schedule_task_id to its row index', () => {
  const rows = [
    { kind: 'wbs', wbs: { id: 'w1' } },
    { kind: 'task', task: { schedule_task_id: 't1' } },
    { kind: 'wbs', wbs: { id: 'w2' } },
    { kind: 'task', task: { schedule_task_id: 't2' } },
  ];
  const m = mod.taskRowIndex(rows);
  assert.equal(m.get('t1'), 1);
  assert.equal(m.get('t2'), 3);
  assert.equal(m.size, 2);
});

test('fmtDate handles Date, ISO string, and null/undefined', () => {
  assert.equal(mod.fmtDate(null), '—');
  assert.equal(mod.fmtDate(undefined), '—');
  assert.equal(mod.fmtDate('2026-04-10T07:00:00Z'), '2026-04-10');
  assert.equal(mod.fmtDate(new Date('2026-04-10T07:00:00Z')), '2026-04-10');
  assert.equal(mod.fmtDate('not-a-date'), '—');
});

test('baselineOverlayFor returns null when either baseline date is NULL', () => {
  const xForDate = () => 0;
  assert.equal(mod.baselineOverlayFor(null, xForDate), null);
  assert.equal(mod.baselineOverlayFor({}, xForDate), null);
  assert.equal(mod.baselineOverlayFor({ baseline_start_at: '2026-04-10T00:00:00Z', baseline_end_at: null }, xForDate), null);
  assert.equal(mod.baselineOverlayFor({ baseline_start_at: null, baseline_end_at: '2026-04-12T00:00:00Z' }, xForDate), null);
});

test('baselineOverlayFor accepts either *_at or *_start/*_finish naming', () => {
  const xForDate = (d) => ((d instanceof Date) ? d.getUTCDate() * 14 : 0);
  const overlay1 = mod.baselineOverlayFor({
    baseline_start_at: '2026-04-10T00:00:00Z',
    baseline_end_at: '2026-04-12T00:00:00Z',
    baseline_name: 'Original',
    baseline_source: 'p6_import',
  }, xForDate);
  assert.ok(overlay1);
  assert.equal(overlay1.baseline_name, 'Original');
  assert.equal(overlay1.baseline_source, 'p6_import');
  const overlay2 = mod.baselineOverlayFor({
    baseline_start: '2026-04-10T00:00:00Z',
    baseline_finish: '2026-04-12T00:00:00Z',
  }, xForDate);
  assert.ok(overlay2);
});

test('baselineOverlayFor width is always positive', () => {
  const xForDate = (d) => ((d instanceof Date) ? d.getUTCDate() : 0);
  const overlay = mod.baselineOverlayFor({
    baseline_start_at: '2026-04-10T00:00:00Z',
    baseline_end_at: '2026-04-10T00:00:00Z',
  }, xForDate);
  assert.ok(overlay);
  assert.ok(overlay.w >= 2, 'width must be clamped to at least 2 px');
});

test('baselineVarianceDays returns positive when planned finishes after baseline', () => {
  const v = mod.baselineVarianceDays({
    planned_finish: '2026-04-15T00:00:00Z',
    baseline_end_at: '2026-04-10T00:00:00Z',
  });
  assert.equal(v, 5);
});

test('baselineVarianceDays returns negative when planned finishes before baseline', () => {
  const v = mod.baselineVarianceDays({
    planned_finish: '2026-04-07T00:00:00Z',
    baseline_end_at: '2026-04-10T00:00:00Z',
  });
  assert.equal(v, -3);
});

test('baselineVarianceDays returns null when baseline missing', () => {
  assert.equal(mod.baselineVarianceDays({ planned_finish: '2026-04-07T00:00:00Z' }), null);
  assert.equal(mod.baselineVarianceDays({ baseline_end_at: '2026-04-10T00:00:00Z' }), null);
  assert.equal(mod.baselineVarianceDays({}), null);
});

test('baselineVarianceDays returns 0 when plan matches baseline', () => {
  const v = mod.baselineVarianceDays({
    planned_finish: '2026-04-10T00:00:00Z',
    baseline_end_at: '2026-04-10T00:00:00Z',
  });
  assert.equal(v, 0);
});

console.log(`\n${passed}/${ran} pure-logic tests passed`);
if (passed !== ran) process.exit(1);