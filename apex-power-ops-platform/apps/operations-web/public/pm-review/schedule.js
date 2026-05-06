/*
 * APEX PM Schedule Surface — canonical active-lane copy.
 *
 * Re-homed from `apps/pm-surface/public/schedule.js` as a bounded PM
 * read-only review slice admitted into `apps/operations-web`.
 */

(function () {
  const { useState, useEffect, useCallback, useMemo } = React;

  const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : `${window.location.origin}/api/v1`;
  const SCHEDULE_BASE = API_BASE + '/schedule';
  const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] };

  function makeToken(actor) {
    return 'Bearer ' + btoa(JSON.stringify(actor));
  }

  async function scheduleGet(path) {
    const resp = await fetch(SCHEDULE_BASE + path, {
      method: 'GET',
      headers: { 'Authorization': makeToken(PM_ACTOR) },
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status} ${path}: ${text}`);
    }
    return resp.json();
  }

  function useScheduleData(initialProjectId) {
    const [projects, setProjects] = useState([]);
    const [activeProjectId, setActiveId] = useState(initialProjectId || null);
    const [wbs, setWbs] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [relationships, setRels] = useState([]);
    const [syncLog, setSyncLog] = useState([]);
    const [loading, setLoading] = useState(true);
    const [online, setOnline] = useState(true);
    const [lastRefresh, setLastRefresh] = useState(null);
    const [error, setError] = useState(null);

    const refresh = useCallback(async () => {
      setLoading(true);
      setError(null);
      try {
        const projs = await scheduleGet('/projects');
        setProjects(projs);
        const projId = activeProjectId || (projs[0] && projs[0].id);
        if (!projId) {
          setWbs([]); setTasks([]); setRels([]); setSyncLog([]);
          setOnline(true);
          setLastRefresh(new Date());
          return;
        }
        if (!activeProjectId) setActiveId(projId);
        const [wbsRows, taskRows, relRows, logRows] = await Promise.all([
          scheduleGet(`/projects/${projId}/wbs`),
          scheduleGet(`/tasks-with-scope?project_id=${projId}`),
          scheduleGet(`/relationships?project_id=${projId}`),
          scheduleGet(`/sync-log?limit=5`),
        ]);
        setWbs(wbsRows);
        setTasks(taskRows);
        setRels(relRows);
        setSyncLog(logRows);
        setOnline(true);
        setLastRefresh(new Date());
      } catch (e) {
        setOnline(false);
        setError(String(e && e.message || e));
      } finally {
        setLoading(false);
      }
    }, [activeProjectId]);

    useEffect(() => { refresh(); }, [refresh]);

    return {
      projects, activeProjectId, setActiveId,
      wbs, tasks, relationships, syncLog,
      loading, online, lastRefresh, error, refresh,
    };
  }

  const ROW_HEIGHT = 34;
  const BAR_HEIGHT = 16;
  const HEADER_HEIGHT = 40;
  const LEFT_PANEL_WIDTH = 420;
  const PX_PER_DAY = 14;
  const CHART_PADDING_RIGHT = 40;

  const MS_PER_DAY = 24 * 3600 * 1000;

  function dayFloor(d) {
    const x = new Date(d);
    x.setUTCHours(0, 0, 0, 0);
    return x;
  }

  function daysBetween(a, b) {
    return (dayFloor(b).getTime() - dayFloor(a).getTime()) / MS_PER_DAY;
  }

  function parseTs(s) {
    if (!s) return null;
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }

  function fmtDate(d) {
    if (!d) return '—';
    const dt = (d instanceof Date) ? d : parseTs(d);
    if (!dt) return '—';
    return dt.toISOString().slice(0, 10);
  }

  function computeRange(tasks, dataDate) {
    const all = [];
    for (const t of tasks) {
      [t.planned_start, t.planned_finish].forEach(v => {
        const d = parseTs(v); if (d) all.push(d);
      });
    }
    if (dataDate) {
      const d = parseTs(dataDate); if (d) all.push(d);
    }
    if (all.length === 0) {
      const now = dayFloor(new Date());
      return { start: now, end: new Date(now.getTime() + 30 * MS_PER_DAY) };
    }
    const min = new Date(Math.min.apply(null, all.map(d => d.getTime())));
    const max = new Date(Math.max.apply(null, all.map(d => d.getTime())));
    const start = new Date(dayFloor(min).getTime() - 7 * MS_PER_DAY);
    const end = new Date(dayFloor(max).getTime() + 7 * MS_PER_DAY);
    return { start, end };
  }

  function buildRows(wbs, tasks) {
    const byParent = new Map();
    const wbsById = new Map();
    wbs.forEach(w => {
      wbsById.set(w.id, w);
      const k = w.parent_wbs_id || '__root__';
      if (!byParent.has(k)) byParent.set(k, []);
      byParent.get(k).push(w);
    });
    byParent.forEach(arr => arr.sort((a, b) => (a.seq || 0) - (b.seq || 0) || String(a.id).localeCompare(b.id)));

    const tasksByWbs = new Map();
    tasks.forEach(t => {
      const k = t.schedule_wbs_id || '__orphan__';
      if (!tasksByWbs.has(k)) tasksByWbs.set(k, []);
      tasksByWbs.get(k).push(t);
    });
    tasksByWbs.forEach(arr => arr.sort((a, b) => {
      const sa = parseTs(a.planned_start), sb = parseTs(b.planned_start);
      if (sa && sb) return sa.getTime() - sb.getTime();
      return String(a.schedule_task_id || a.id).localeCompare(String(b.schedule_task_id || b.id));
    }));

    const rows = [];

    function walk(wbsRow, depth) {
      rows.push({ kind: 'wbs', wbs: wbsRow, depth });
      const ts = tasksByWbs.get(wbsRow.id) || [];
      for (const t of ts) rows.push({ kind: 'task', task: t, depth: depth + 1, wbs: wbsRow });
      const children = byParent.get(wbsRow.id) || [];
      for (const c of children) walk(c, depth + 1);
    }
    const roots = byParent.get('__root__') || [];
    for (const r of roots) walk(r, 0);

    const orphans = tasksByWbs.get('__orphan__') || [];
    if (orphans.length) {
      rows.push({ kind: 'wbs', wbs: { id: '__orphan__', name: '(Unassigned)', short_name: null }, depth: 0, isOrphan: true });
      for (const t of orphans) rows.push({ kind: 'task', task: t, depth: 1, wbs: null });
    }
    return rows;
  }

  function taskRowIndex(rows) {
    const m = new Map();
    rows.forEach((r, i) => { if (r.kind === 'task') m.set(r.task.schedule_task_id, i); });
    return m;
  }

  function relEdges(type) {
    switch (type) {
      case 'FS': return ['finish', 'start'];
      case 'SS': return ['start', 'start'];
      case 'FF': return ['finish', 'finish'];
      case 'SF': return ['start', 'finish'];
      default: return ['finish', 'start'];
    }
  }

  function connectorPath(pred, succ, type, xFor, yFor) {
    const [pe, se] = relEdges(type);
    const px = xFor(pred, pe);
    const py = yFor(pred);
    const sx = xFor(succ, se);
    const sy = yFor(succ);
    Math.min(px, sx) - 6;
    const dx = 10;
    const p1x = px + (pe === 'finish' ? dx : -dx);
    const p2x = sx + (se === 'start' ? -dx : dx);
    return `M ${px} ${py} L ${p1x} ${py} L ${p1x} ${sy} L ${sx} ${sy}`;
  }

  function baselineOverlayFor(task, xForDate) {
    const bs = parseTs(task && (task.baseline_start_at || task.baseline_start));
    const bf = parseTs(task && (task.baseline_end_at || task.baseline_finish));
    if (!bs || !bf) return null;
    const x = xForDate(bs);
    const xe = xForDate(bf);
    const w = Math.max(2, xe - x);
    return {
      x, w,
      baseline_start: bs,
      baseline_finish: bf,
      baseline_name: task.baseline_name || null,
      baseline_source: task.baseline_source || null,
    };
  }

  function baselineVarianceDays(task) {
    const bf = parseTs(task && (task.baseline_end_at || task.baseline_finish));
    const pf = parseTs(task && task.planned_finish);
    if (!bf || !pf) return null;
    return Math.round((pf.getTime() - bf.getTime()) / MS_PER_DAY);
  }

  function GanttCanvas({ rows, relationships, rangeStart, rangeEnd, dataDate }) {
    const totalDays = Math.max(1, Math.round((rangeEnd - rangeStart) / MS_PER_DAY));
    const chartWidth = totalDays * PX_PER_DAY + CHART_PADDING_RIGHT;
    const chartHeight = HEADER_HEIGHT + rows.length * ROW_HEIGHT + 20;

    const xForDate = (d) => {
      const dt = (d instanceof Date) ? d : parseTs(d);
      if (!dt) return null;
      return daysBetween(rangeStart, dt) * PX_PER_DAY;
    };

    const ticks = [];
    const monthMarkers = [];
    for (let i = 0; i <= totalDays; i++) {
      const d = new Date(rangeStart.getTime() + i * MS_PER_DAY);
      const x = i * PX_PER_DAY;
      if (d.getUTCDay() === 1) {
        ticks.push({ x, label: d.toISOString().slice(5, 10), kind: 'week' });
      }
      if (d.getUTCDate() === 1) {
        monthMarkers.push({
          x,
          label: d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        });
      }
    }

    const dataDateX = dataDate ? xForDate(dataDate) : null;

    const taskGeom = new Map();
    rows.forEach((r, i) => {
      if (r.kind !== 'task') return;
      const t = r.task;
      const ps = parseTs(t.planned_start);
      const pf = parseTs(t.planned_finish);
      if (!ps || !pf) return;
      const x = xForDate(ps);
      const w = Math.max(2, xForDate(pf) - x);
      const y = HEADER_HEIGHT + i * ROW_HEIGHT + (ROW_HEIGHT - BAR_HEIGHT) / 2;
      taskGeom.set(t.schedule_task_id, { x, y, w, task: t });
    });

    const xFor = (taskId, edge) => {
      const g = taskGeom.get(taskId); if (!g) return 0;
      return edge === 'start' ? g.x : g.x + g.w;
    };
    const yFor = (taskId) => {
      const g = taskGeom.get(taskId); if (!g) return 0;
      return g.y + BAR_HEIGHT / 2;
    };

    return React.createElement('svg', {
      width: chartWidth, height: chartHeight, style: { background: 'white', display: 'block' },
    },
      React.createElement('defs', null,
        React.createElement('marker', {
          id: 'sched-arrow', viewBox: '0 0 6 6', refX: 5, refY: 3,
          markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse',
        },
          React.createElement('path', { d: 'M 0 0 L 6 3 L 0 6 z', fill: '#6b7280' }),
        ),
      ),
      rows.map((r, i) => React.createElement('rect', {
        key: `row-${i}`, x: 0, y: HEADER_HEIGHT + i * ROW_HEIGHT,
        width: chartWidth, height: ROW_HEIGHT,
        fill: i % 2 ? '#fafafa' : 'white',
      })),
      ticks.map((t, idx) => React.createElement('g', { key: `tick-${idx}` },
        React.createElement('line', {
          x1: t.x, x2: t.x, y1: HEADER_HEIGHT, y2: chartHeight - 20,
          stroke: '#e5e7eb', strokeWidth: 1,
        }),
        React.createElement('text', {
          x: t.x + 2, y: HEADER_HEIGHT - 4, fontSize: 9, fill: '#9ca3af',
        }, t.label),
      )),
      monthMarkers.map((m, idx) => React.createElement('text', {
        key: `mon-${idx}`, x: m.x + 2, y: 14, fontSize: 11, fontWeight: 600, fill: '#374151',
      }, m.label)),
      dataDateX != null && React.createElement('g', null,
        React.createElement('line', {
          x1: dataDateX, x2: dataDateX, y1: HEADER_HEIGHT - 6, y2: chartHeight - 20,
          stroke: '#dc2626', strokeWidth: 2, strokeDasharray: '4 3',
        }),
        React.createElement('text', {
          x: dataDateX + 4, y: HEADER_HEIGHT - 10, fontSize: 10, fill: '#dc2626', fontWeight: 700,
        }, `data_date ${fmtDate(dataDate)}`),
      ),
      rows.map((r, i) => {
        if (r.kind !== 'task') return null;
        const t = r.task;
        const g = taskGeom.get(t.schedule_task_id);
        if (!g) {
          return React.createElement('text', {
            key: `nobar-${i}`, x: 4, y: HEADER_HEIGHT + i * ROW_HEIGHT + 18,
            fontSize: 10, fill: '#9ca3af', fontStyle: 'italic',
          }, '(no dates)');
        }
        const isCritical = !!t.critical_flag;
        const barFill = isCritical ? '#dc2626' : '#015687';
        const floatDays = Number(t.total_float_hours || 0) / 8;
        const floatPx = Math.max(0, floatDays * PX_PER_DAY);

        const baseline = baselineOverlayFor(t, xForDate);
        const varianceDays = baselineVarianceDays(t);
        const baselineBarY = g.y + BAR_HEIGHT + 1;
        const baselineBarH = 5;

        return React.createElement('g', { key: `bar-${i}` },
          baseline && React.createElement('rect', {
            x: baseline.x, y: baselineBarY,
            width: baseline.w, height: baselineBarH,
            fill: '#9ca3af', opacity: 0.85, rx: 1,
          }),
          baseline && React.createElement('line', {
            x1: baseline.x + baseline.w, x2: baseline.x + baseline.w,
            y1: baselineBarY - 1, y2: baselineBarY + baselineBarH + 1,
            stroke: '#6b7280', strokeWidth: 1,
          }),
          floatPx > 0 && React.createElement('rect', {
            x: g.x + g.w, y: g.y + BAR_HEIGHT * 0.25, width: floatPx, height: BAR_HEIGHT * 0.5,
            fill: '#d1d5db', stroke: '#9ca3af', strokeDasharray: '2 2', rx: 2,
          }),
          React.createElement('rect', {
            x: g.x, y: g.y, width: g.w, height: BAR_HEIGHT,
            fill: barFill, rx: 3,
          }),
          React.createElement('line', {
            x1: g.x + g.w, x2: g.x + g.w,
            y1: g.y - 2, y2: g.y + BAR_HEIGHT + 2,
            stroke: isCritical ? '#991b1b' : '#014168', strokeWidth: 1,
          }),
          baseline && varianceDays !== null && varianceDays !== 0 && React.createElement('g', null,
            React.createElement('rect', {
              x: g.x + g.w + 2, y: g.y + BAR_HEIGHT - 10,
              width: 30, height: 12, rx: 6,
              fill: varianceDays > 0 ? '#fecaca' : '#d1fae5',
            }),
            React.createElement('text', {
              x: g.x + g.w + 17, y: g.y + BAR_HEIGHT - 1,
              fontSize: 9, textAnchor: 'middle', fontWeight: 700,
              fill: varianceDays > 0 ? '#991b1b' : '#065f46',
            }, `${varianceDays > 0 ? '+' : ''}${varianceDays}d`),
          ),
          React.createElement('text', {
            x: g.x + g.w + floatPx + (baseline && varianceDays !== null && varianceDays !== 0 ? 38 : 6),
            y: g.y + BAR_HEIGHT - 4,
            fontSize: 10, fill: '#4b5563',
          }, t.task_code || t.schedule_task_id),
          React.createElement('title', null,
            `${t.task_code || t.schedule_task_id} — ${t.task_name}\n`
            + `planned:  ${fmtDate(t.planned_start)} → ${fmtDate(t.planned_finish)}\n`
            + (baseline
                ? `baseline: ${fmtDate(baseline.baseline_start)} → ${fmtDate(baseline.baseline_finish)}`
                  + ` (${baseline.baseline_name || '—'}, ${baseline.baseline_source || '—'})\n`
                  + `variance: ${varianceDays > 0 ? '+' : ''}${varianceDays ?? '—'} d (finish)\n`
                : `baseline: — (none captured)\n`)
            + `total_float: ${t.total_float_hours ?? '—'} h\n`
            + `critical: ${isCritical ? 'yes' : 'no'}\n`
            + `seam_status: ${t.seam_status ?? '(unresolved)'}`
          ),
        );
      }),
      relationships.map((r, idx) => {
        if (!taskGeom.has(r.predecessor_task_id)) return null;
        if (!taskGeom.has(r.successor_task_id)) return null;
        const d = connectorPath(r.predecessor_task_id, r.successor_task_id, r.rel_type, xFor, yFor);
        const pe = relEdges(r.rel_type)[0];
        const px = xFor(r.predecessor_task_id, pe);
        const py = yFor(r.predecessor_task_id);
        const sy = yFor(r.successor_task_id);
        const labelX = px + (pe === 'finish' ? 14 : -14);
        const labelY = (py + sy) / 2 - 2;
        const lagHours = Number(r.lag_hours || 0);
        return React.createElement('g', { key: `rel-${idx}` },
          React.createElement('path', {
            d, fill: 'none', stroke: '#6b7280', strokeWidth: 1.2,
            markerEnd: 'url(#sched-arrow)',
          }),
          React.createElement('text', {
            x: labelX, y: labelY, fontSize: 9, fill: '#4b5563',
          }, `${r.rel_type}${lagHours ? ` ${lagHours > 0 ? '+' : ''}${lagHours}h` : ''}`),
        );
      }),
    );
  }

  function LeftPanel({ rows, onTraceTask, onViewVariance, onViewDrivers, focusTaskId }) {
    let gridCols = '1fr 72px 64px 56px';
    if (onTraceTask) gridCols += ' 28px';
    if (onViewVariance) gridCols += ' 28px';
    if (onViewDrivers) gridCols += ' 28px';
    return React.createElement('div', {
      style: { width: LEFT_PANEL_WIDTH, borderRight: '1px solid #e5e7eb', background: 'white' },
    },
      React.createElement('div', {
        style: {
          display: 'grid', gridTemplateColumns: gridCols,
          height: HEADER_HEIGHT, alignItems: 'center', padding: '0 10px',
          borderBottom: '1px solid #e5e7eb', fontSize: 10,
          textTransform: 'uppercase', color: '#6b7280', fontWeight: 700, letterSpacing: '0.04em',
        },
      },
        React.createElement('div', null, 'Task / WBS'),
        React.createElement('div', { style: { textAlign: 'right' } }, 'Status'),
        React.createElement('div', { style: { textAlign: 'right' } }, 'Float (h)'),
        React.createElement('div', { style: { textAlign: 'right' } }, 'Crit'),
        onTraceTask && React.createElement('div', { style: { textAlign: 'right' } }, 'Trace'),
        onViewVariance && React.createElement('div', { style: { textAlign: 'right' } }, 'Var'),
        onViewDrivers && React.createElement('div', { style: { textAlign: 'right' } }, 'Drv'),
      ),
      rows.map((r, i) => {
        if (r.kind === 'wbs') {
          return React.createElement('div', {
            key: `lp-${i}`,
            style: {
              height: ROW_HEIGHT, display: 'flex', alignItems: 'center',
              padding: `0 10px 0 ${10 + r.depth * 14}px`,
              background: i % 2 ? '#fafafa' : 'white',
              fontWeight: 700, fontSize: 12, color: '#015687',
              borderBottom: '1px solid #f3f4f6',
            },
          }, `${r.wbs.short_name || ''} ${r.wbs.name}`);
        }
        const t = r.task;
        const isFocused = !!(focusTaskId && t.schedule_task_id === focusTaskId);
        return React.createElement('div', {
          key: `lp-${i}`,
          'data-task-id': t.schedule_task_id || '',
          style: {
            display: 'grid', gridTemplateColumns: gridCols,
            height: ROW_HEIGHT, alignItems: 'center',
            padding: `0 10px 0 ${10 + r.depth * 14}px`,
            background: isFocused ? '#dbeafe' : (i % 2 ? '#fafafa' : 'white'),
            outline: isFocused ? '2px solid #015687' : 'none',
            outlineOffset: isFocused ? '-2px' : '0',
            fontSize: 12, borderBottom: '1px solid #f3f4f6',
          },
        },
          React.createElement('div', {
            style: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
            title: `${t.task_code || ''} ${t.task_name}`,
          }, `${t.task_code || ''} ${t.task_name}`),
          React.createElement('div', {
            style: { textAlign: 'right', fontSize: 10, color: '#6b7280' },
          }, (t.seam_status || t.schedule_apex_status || '—').replace(/_/g, ' ')),
          React.createElement('div', {
            style: { textAlign: 'right', fontSize: 11, color: '#4b5563' },
          }, t.total_float_hours != null ? String(t.total_float_hours) : '—'),
          React.createElement('div', {
            style: {
              textAlign: 'right', fontSize: 11,
              color: t.critical_flag ? '#dc2626' : '#9ca3af',
              fontWeight: t.critical_flag ? 700 : 400,
            },
          }, t.critical_flag ? 'yes' : '—'),
          onTraceTask && React.createElement('button', {
            onClick: (ev) => {
              ev.stopPropagation();
              onTraceTask({
                taskId: t.schedule_task_id,
                taskLabel: (t.task_code ? t.task_code + ' — ' : '') + (t.task_name || t.schedule_task_id),
              });
            },
            className: 'btn btn-outline',
            style: {
              fontSize: 11, padding: '1px 4px', lineHeight: 1.1,
              justifySelf: 'end', minWidth: 24,
            },
            title: 'Trace the upstream constraint chain for this task',
          }, '🔍'),
          (onViewVariance && t.schedule_task_id) && React.createElement('button', {
            onClick: (ev) => {
              ev.stopPropagation();
              onViewVariance(t.schedule_task_id);
            },
            className: 'btn btn-outline',
            style: {
              fontSize: 11, padding: '1px 4px', lineHeight: 1.1,
              justifySelf: 'end', minWidth: 24,
            },
            title: 'View schedule variance for this task',
          }, '📈'),
          (onViewDrivers && t.schedule_task_id) && React.createElement('button', {
            onClick: (ev) => {
              ev.stopPropagation();
              onViewDrivers(t.schedule_task_id);
            },
            className: 'btn btn-outline',
            style: {
              fontSize: 11, padding: '1px 4px', lineHeight: 1.1,
              justifySelf: 'end', minWidth: 24,
            },
            title: 'View any critical-path edges involving this task in Drivers',
          }, '🎯'),
        );
      }),
    );
  }

  function ScheduleHeader({ proj, data, onRefresh }) {
    const latestSync = data.syncLog && data.syncLog[0];
    const baselineName = (() => {
      const tasks = (data && data.tasks) || [];
      for (const t of tasks) {
        const n = t.baseline_name || null;
        if (n) return { name: n, source: t.baseline_source || null };
      }
      return null;
    })();
    return React.createElement('div', null,
      React.createElement('div', {
        style: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 },
      },
        React.createElement('div', null,
          React.createElement('h1', { className: 'text-xl font-bold resa-blue', style: { margin: 0 } },
            'Project Schedule'),
          proj && React.createElement('div', { style: { fontSize: 13, color: '#4b5563', marginTop: 2 } },
            `${proj.name} · ${proj.p6_project_id}`),
        ),
        React.createElement('div', { style: { textAlign: 'right', fontSize: 11, color: '#6b7280' } },
          proj && React.createElement('div', null, `data_date: ${fmtDate(proj.data_date)}`),
          latestSync && React.createElement('div', null,
            `last import: ${fmtDate(latestSync.started_at)} (${latestSync.source_type}, ${latestSync.status})`),
          baselineName && React.createElement('div', { style: { color: '#374151' } },
            `baseline: ${baselineName.name}`
            + (baselineName.source ? ` (${baselineName.source})` : '')),
          React.createElement('button', {
            onClick: onRefresh, className: 'btn btn-outline',
            style: { marginTop: 6, fontSize: 11, padding: '4px 10px' },
          }, 'Refresh'),
        ),
      ),
    );
  }

  function Legend() {
    const sw = (bg, extra) => ({
      display: 'inline-block', width: 20, height: 10, marginRight: 6,
      background: bg, borderRadius: 2, ...(extra || {}),
    });
    return React.createElement('div', {
      style: {
        display: 'flex', flexWrap: 'wrap', gap: 18, padding: '10px 12px', marginTop: 12,
        border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 11, color: '#4b5563', background: '#fafafa',
      },
    },
      React.createElement('span', null, React.createElement('span', { style: sw('#015687') }), 'Planned'),
      React.createElement('span', null, React.createElement('span', { style: sw('#dc2626') }), 'Critical path'),
      React.createElement('span', null,
        React.createElement('span', { style: sw('#9ca3af', { height: 5, opacity: 0.85 }) }),
        'Baseline (persisted)'),
      React.createElement('span', null,
        React.createElement('span', { style: { ...sw('#fecaca', { width: 22, height: 12, borderRadius: 6 }), color: '#991b1b' } }),
        'Slip (+d)'),
      React.createElement('span', null,
        React.createElement('span', { style: { ...sw('#d1fae5', { width: 22, height: 12, borderRadius: 6 }), color: '#065f46' } }),
        'Ahead (−d)'),
      React.createElement('span', null,
        React.createElement('span', { style: sw('#d1d5db', { border: '1px dashed #9ca3af' }) }),
        'Float'),
      React.createElement('span', null,
        React.createElement('span', {
          style: {
            display: 'inline-block', width: 20, height: 0, borderTop: '2px dashed #dc2626',
            verticalAlign: 'middle', marginRight: 6,
          },
        }),
        'data_date'),
      React.createElement('span', { style: { color: '#6b7280' } },
        'Dep arrows: FS · SS · FF · SF; lag shown in hours next to arrow.'),
      React.createElement('span', {
        style: { marginLeft: 'auto', color: '#5FA844', fontWeight: 600 },
      }, 'Read-only · no schedule writes'),
    );
  }

  function ScheduleView({ onTraceTask, onViewVariance, onViewDrivers, focusTaskId }) {
    const data = useScheduleData();
    const proj = data.projects.find(p => p.id === data.activeProjectId) || null;
    const rows = useMemo(() => buildRows(data.wbs, data.tasks), [data.wbs, data.tasks]);
    const range = useMemo(
      () => computeRange(data.tasks, proj && proj.data_date),
      [data.tasks, proj]
    );

    useEffect(() => {
      if (!focusTaskId || data.tasks.length === 0) return;
      const row = document.querySelector(`[data-task-id="${focusTaskId}"]`);
      if (row && typeof row.scrollIntoView === 'function') {
        row.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
    }, [focusTaskId, data.tasks.length]);

    if (data.loading && data.tasks.length === 0) {
      return React.createElement('div', { className: 'card text-center p-8' }, 'Loading schedule bridge…');
    }
    if (!data.online) {
      return React.createElement('div', { className: 'card', style: { borderLeft: '3px solid #dc2626' } },
        React.createElement('div', { style: { fontWeight: 700, color: '#991b1b' } }, 'Schedule bridge offline'),
        React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 4 } },
          data.error || 'Could not reach /api/v1/schedule. Confirm the mutation-seam server is running and the schedule.* tables are populated (see run_schedule_bootstrap.py).'),
        React.createElement('button', { onClick: data.refresh, className: 'btn btn-outline', style: { marginTop: 8, fontSize: 11 } }, 'Retry'),
      );
    }
    if (data.projects.length === 0) {
      return React.createElement('div', { className: 'card' },
        'No schedule projects landed yet. Run `python run_schedule_bootstrap.py` on the host to populate the `schedule.*` tables.');
    }

    return React.createElement('div', null,
      data.projects.length > 1 && React.createElement('div', { style: { marginBottom: 8 } },
        React.createElement('label', { style: { fontSize: 12, marginRight: 6, color: '#4b5563' } }, 'Project:'),
        React.createElement('select', {
          value: data.activeProjectId || '',
          onChange: e => data.setActiveId(e.target.value),
        }, data.projects.map(p =>
          React.createElement('option', { key: p.id, value: p.id }, `${p.name} (${p.p6_project_id})`)
        )),
      ),
      React.createElement(ScheduleHeader, { proj, data, onRefresh: data.refresh }),
      React.createElement('div', {
        className: 'card',
        style: { padding: 0, overflow: 'hidden', display: 'flex' },
      },
        React.createElement(LeftPanel, { rows, onTraceTask, onViewVariance, onViewDrivers, focusTaskId }),
        React.createElement('div', { style: { overflowX: 'auto', overflowY: 'hidden', flex: 1 } },
          React.createElement(GanttCanvas, {
            rows,
            relationships: data.relationships,
            rangeStart: range.start,
            rangeEnd: range.end,
            dataDate: proj && proj.data_date,
          }),
        ),
      ),
      React.createElement(Legend, null),
      data.syncLog && data.syncLog.length > 0 && React.createElement('div', {
        style: { marginTop: 12, fontSize: 11, color: '#6b7280' },
      }, 'Latest sync events: ', data.syncLog.map((s, i) =>
        React.createElement('span', {
          key: s.id,
          style: { marginRight: 8, padding: '2px 6px', background: s.status === 'success' ? '#d1fae5' : (s.status === 'failed' ? '#fecaca' : '#fef3c7'), borderRadius: 4 },
        }, `${s.source_type}·${s.status}·${fmtDate(s.started_at)}`))
      ),
    );
  }

  window.ApexSchedule = {
    ScheduleView,
    useScheduleData,
    __internals__: {
      buildRows, taskRowIndex, computeRange, relEdges, connectorPath,
      baselineOverlayFor, baselineVarianceDays,
      SCHEDULE_BASE, PM_ACTOR,
    },
  };
})();