/*
 * APEX PM Schedule Variance Review Surface — canonical active-lane copy.
 *
 * Re-homed from `apps/pm-surface/public/variance.js` as a bounded PM
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

  async function varianceGet(path) {
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

  function useVarianceRows(projectId, { withBaselineOnly, onlySlipping } = {}) {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [online, setOnline] = useState(true);
    const [error, setError] = useState(null);
    const [lastRefresh, setLast] = useState(null);

    const refresh = useCallback(async () => {
      setLoading(true);
      setError(null);
      try {
        const params = [];
        if (projectId) params.push(`project_id=${encodeURIComponent(projectId)}`);
        if (withBaselineOnly) params.push('with_baseline_only=true');
        if (onlySlipping) params.push('only_slipping=true');
        const qs = params.length ? `?${params.join('&')}` : '';
        const data = await varianceGet(`/variance${qs}`);
        setRows(data);
        setOnline(true);
        setLast(new Date());
      } catch (e) {
        setOnline(false);
        setError(String(e && e.message || e));
      } finally {
        setLoading(false);
      }
    }, [projectId, withBaselineOnly, onlySlipping]);

    useEffect(() => { refresh(); }, [refresh]);

    return { rows, loading, online, error, lastRefresh, refresh };
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

  function labelFor(task_code, p6_task_id, task_id) {
    return task_code || p6_task_id || task_id || '—';
  }

  function fmtVarianceHours(h) {
    if (h === null || h === undefined || h === '') return '—';
    const n = Number(h);
    if (!Number.isFinite(n)) return '—';
    if (Math.abs(n) < 0.0005) return '0h';
    return `${n > 0 ? '+' : ''}${n.toFixed(1)}h`;
  }

  function fmtVarianceDays(h) {
    if (h === null || h === undefined || h === '') return '—';
    const n = Number(h);
    if (!Number.isFinite(n)) return '—';
    const abs = Math.abs(n);
    const days = abs / 24;
    const sign = n > 0 ? '+' : n < 0 ? '-' : '';
    if (abs < 0.0005) return '0d';
    if (days < 1) return `${sign}${abs.toFixed(1)}h`;
    return `${sign}${days.toFixed(1)}d`;
  }

  function classifyVariance(row) {
    if (!row || !row.has_baseline) return 'no-baseline';
    const fv = row.finish_variance_hours;
    if (fv === null || fv === undefined) return 'no-baseline';
    const n = Number(fv);
    if (!Number.isFinite(n)) return 'no-baseline';
    if (n > 0.5) return 'slipping';
    if (n < -0.5) return 'ahead';
    return 'on-plan';
  }

  function sortByFinishVariance(rows, direction) {
    const dir = (direction === 'asc') ? 1 : -1;
    const indexed = rows.map((r, i) => [r, i]);
    indexed.sort((a, b) => {
      const av = a[0].finish_variance_hours;
      const bv = b[0].finish_variance_hours;
      const aNull = (av === null || av === undefined);
      const bNull = (bv === null || bv === undefined);
      if (aNull && bNull) return a[1] - b[1];
      if (aNull) return 1;
      if (bNull) return -1;
      const an = Number(av), bn = Number(bv);
      if (an === bn) return a[1] - b[1];
      return (an < bn ? -1 : 1) * dir;
    });
    return indexed.map(([r]) => r);
  }

  function summarizeVariance(rows) {
    let total = 0;
    let withBaseline = 0;
    let slipping = 0;
    let ahead = 0;
    let onPlan = 0;
    let noBaseline = 0;
    let worstSlipHours = null;
    let bestLeadHours = null;
    for (const r of rows) {
      total += 1;
      const state = classifyVariance(r);
      if (state === 'no-baseline') {
        noBaseline += 1;
        continue;
      }
      withBaseline += 1;
      const fv = Number(r.finish_variance_hours);
      if (state === 'slipping') {
        slipping += 1;
        if (worstSlipHours === null || fv > worstSlipHours) worstSlipHours = fv;
      } else if (state === 'ahead') {
        ahead += 1;
        if (bestLeadHours === null || fv < bestLeadHours) bestLeadHours = fv;
      } else {
        onPlan += 1;
      }
    }
    return {
      total,
      withBaseline,
      noBaseline,
      slipping,
      ahead,
      onPlan,
      worstSlipHours,
      bestLeadHours,
    };
  }

  function VarianceRow({ row, i, onTraceTask, onViewSchedule, onViewDrivers, isFocused }) {
    const state = classifyVariance(row);
    const critical = !!row.critical_flag;
    const stateColor = state === 'slipping' ? '#dc2626' : state === 'ahead' ? '#5FA844' : state === 'on-plan' ? '#015687' : '#9ca3af';
    const stateLabel = state === 'slipping' ? 'Slipping' : state === 'ahead' ? 'Ahead' : state === 'on-plan' ? 'On plan' : 'No baseline';
    const label = labelFor(row.task_code, row.p6_task_id, row.schedule_task_id);

    return React.createElement('div', {
      'data-task-id': row.schedule_task_id || '',
      style: {
        display: 'grid',
        gridTemplateColumns: '160px 90px 74px 74px 74px 64px 1fr',
        gap: 10, alignItems: 'center', padding: '6px 10px',
        background: isFocused ? '#dbeafe' : (i % 2 ? '#fafafa' : 'white'),
        outline: isFocused ? '2px solid #015687' : 'none',
        outlineOffset: isFocused ? '-2px' : '0',
        borderBottom: '1px solid #f3f4f6', fontSize: 12,
      },
    },
      React.createElement('div', {
        style: { color: critical ? '#dc2626' : '#111827', fontWeight: critical ? 700 : 500 },
      },
        React.createElement('div', null, label),
        React.createElement('div', { style: { fontSize: 10, color: '#6b7280', fontWeight: 400 } }, row.task_name || ''),
      ),
      React.createElement('div', {
        style: { color: stateColor, fontWeight: 700, fontSize: 11, textAlign: 'left' },
      }, stateLabel),
      React.createElement('div', {
        style: {
          fontFamily: 'monospace', fontSize: 11,
          color: Number(row.start_variance_hours) > 0 ? '#dc2626' : Number(row.start_variance_hours) < 0 ? '#5FA844' : '#4b5563',
        },
      }, fmtVarianceHours(row.start_variance_hours)),
      React.createElement('div', {
        style: {
          fontFamily: 'monospace', fontSize: 11, fontWeight: 700,
          color: Number(row.finish_variance_hours) > 0 ? '#dc2626' : Number(row.finish_variance_hours) < 0 ? '#5FA844' : '#4b5563',
        },
      }, fmtVarianceHours(row.finish_variance_hours)),
      React.createElement('div', {
        style: {
          fontFamily: 'monospace', fontSize: 11,
          color: Number(row.duration_variance_hours) > 0 ? '#b45309' : Number(row.duration_variance_hours) < 0 ? '#5FA844' : '#4b5563',
        },
      }, fmtVarianceHours(row.duration_variance_hours)),
      React.createElement('div', { style: { fontSize: 11, color: '#4b5563', textAlign: 'right' } },
        row.total_float_hours === null || row.total_float_hours === undefined ? '—' : `${row.total_float_hours}h`),
      React.createElement('div', {
        style: { fontSize: 10, color: '#6b7280', display: 'flex', alignItems: 'center', gap: 8 },
      },
        React.createElement('span', { style: { flex: 1 } },
          `plan fin ${fmtDate(row.planned_finish)}`,
          row.has_baseline ? ` vs base ${fmtDate(row.baseline_end_at)}` : ' · no baseline on record',
          critical ? ' · critical' : ''),
        (onTraceTask && row.schedule_task_id) && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onTraceTask({
              taskId: row.schedule_task_id,
              taskLabel: label + (row.task_name ? ' — ' + row.task_name : ''),
            });
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'Trace the upstream constraint chain for this task',
        }, '🔍 Trace'),
        (onViewSchedule && row.schedule_task_id) && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onViewSchedule(row.schedule_task_id);
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'View this task in the Schedule',
        }, '📊 Schedule'),
        (onViewDrivers && row.schedule_task_id) && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onViewDrivers(row.schedule_task_id);
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'View any critical-path edges involving this task in Drivers',
        }, '🎯 Drivers'),
      ),
    );
  }

  function VarianceReviewView({ projectId, onTraceTask, onViewSchedule, onViewDrivers, focusTaskId }) {
    const [withBaselineOnly, setWithBaselineOnly] = useState(false);
    const [onlySlipping, setOnlySlipping] = useState(false);
    const [sortDir, setSortDir] = useState('desc');

    const hook = useVarianceRows(projectId, { withBaselineOnly, onlySlipping });
    const sorted = useMemo(() => sortByFinishVariance(hook.rows, sortDir), [hook.rows, sortDir]);
    const summary = useMemo(() => summarizeVariance(hook.rows), [hook.rows]);

    useEffect(() => {
      if (!focusTaskId || hook.rows.length === 0) return;
      const row = document.querySelector(`[data-task-id="${focusTaskId}"]`);
      if (row && typeof row.scrollIntoView === 'function') {
        row.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
    }, [focusTaskId, hook.rows.length]);

    if (hook.loading && hook.rows.length === 0) {
      return React.createElement('div', { className: 'card text-center p-8' }, 'Loading schedule variance…');
    }
    if (!hook.online) {
      return React.createElement('div', {
        className: 'card', style: { borderLeft: '3px solid #dc2626' },
      },
        React.createElement('div', { style: { fontWeight: 700, color: '#991b1b' } }, 'Schedule variance bridge offline'),
        React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 4 } },
          hook.error || 'Could not reach /api/v1/schedule/variance. Confirm the mutation-seam server is running and the schedule.* tables are populated.'),
        React.createElement('button', {
          onClick: hook.refresh, className: 'btn btn-outline',
          style: { marginTop: 8, fontSize: 11 },
        }, 'Retry'),
      );
    }

    return React.createElement('div', null,
      React.createElement('div', {
        style: {
          display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
          marginBottom: 12, flexWrap: 'wrap', gap: 10,
        },
      },
        React.createElement('div', null,
          React.createElement('h2', { className: 'text-lg font-bold resa-blue', style: { margin: 0 } }, 'Schedule variance — current vs baseline'),
          React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 2 } },
            'First slice — per-task start/finish/duration variance. Read-only. Derived from persisted schedule baseline; never from delta exports.'),
        ),
        React.createElement('div', { style: { textAlign: 'right', fontSize: 11, color: '#6b7280' } },
          React.createElement('div', null,
            `${summary.total} task${summary.total === 1 ? '' : 's'} · ${summary.withBaseline} w/ baseline · ${summary.slipping} slipping · ${summary.onPlan} on plan · ${summary.ahead} ahead · ${summary.noBaseline} no baseline`),
          React.createElement('div', { style: { marginTop: 3, fontSize: 10, color: '#9ca3af' } },
            `worst slip ${fmtVarianceDays(summary.worstSlipHours)} · best lead ${fmtVarianceDays(summary.bestLeadHours)}`),
          React.createElement('button', {
            onClick: hook.refresh, className: 'btn btn-outline',
            style: { marginTop: 6, fontSize: 11, padding: '4px 10px' },
          }, 'Refresh'),
        ),
      ),
      React.createElement('div', {
        style: {
          display: 'flex', gap: 14, alignItems: 'center',
          marginBottom: 8, fontSize: 11, color: '#4b5563',
        },
      },
        React.createElement('label', { style: { display: 'flex', alignItems: 'center', gap: 4 } },
          React.createElement('input', {
            type: 'checkbox', checked: withBaselineOnly,
            onChange: e => setWithBaselineOnly(e.target.checked),
          }),
          'With baseline only',
        ),
        React.createElement('label', { style: { display: 'flex', alignItems: 'center', gap: 4 } },
          React.createElement('input', {
            type: 'checkbox', checked: onlySlipping,
            onChange: e => setOnlySlipping(e.target.checked),
          }),
          'Slipping only',
        ),
        React.createElement('label', { style: { display: 'flex', alignItems: 'center', gap: 4 } },
          'Sort finish variance:',
          React.createElement('select', {
            value: sortDir,
            onChange: e => setSortDir(e.target.value),
            style: { fontSize: 11 },
          },
            React.createElement('option', { value: 'desc' }, 'Worst slip first'),
            React.createElement('option', { value: 'asc' }, 'Best lead first'),
          ),
        ),
      ),
      React.createElement('div', { className: 'card', style: { padding: 0, overflow: 'hidden' } },
        React.createElement('div', {
          style: {
            display: 'grid',
            gridTemplateColumns: '160px 90px 74px 74px 74px 64px 1fr',
            gap: 10, alignItems: 'center',
            padding: '8px 10px', borderBottom: '1px solid #e5e7eb',
            background: '#f9fafb', fontSize: 10,
            textTransform: 'uppercase', color: '#6b7280', fontWeight: 700,
            letterSpacing: '0.04em',
          },
        },
          React.createElement('div', null, 'Task'),
          React.createElement('div', null, 'State'),
          React.createElement('div', null, 'Start Δ'),
          React.createElement('div', null, 'Finish Δ'),
          React.createElement('div', null, 'Dur Δ'),
          React.createElement('div', { style: { textAlign: 'right' } }, 'Float'),
          React.createElement('div', null, 'Context'),
        ),
        sorted.length === 0
          ? React.createElement('div', {
              style: { padding: 20, fontSize: 12, color: '#6b7280', textAlign: 'center' },
            }, 'No variance rows returned. Adjust filters or confirm the schedule project has baseline tasks imported.')
          : sorted.map((r, i) => React.createElement(VarianceRow, {
              key: r.schedule_task_id || `row-${i}`,
              row: r, i, onTraceTask, onViewSchedule, onViewDrivers,
              isFocused: !!(focusTaskId && r.schedule_task_id === focusTaskId),
            })),
      ),
      React.createElement('div', {
        style: { marginTop: 10, fontSize: 11, color: '#5FA844', fontWeight: 600 },
      }, 'Read-only · derived from persisted schedule baseline · no schedule writes · no third-party delta dependency'),
    );
  }

  window.ApexVariance = {
    VarianceReviewView,
    useVarianceRows,
    __internals__: {
      parseTs, fmtDate, fmtVarianceHours, fmtVarianceDays, labelFor,
      classifyVariance, sortByFinishVariance, summarizeVariance,
      SCHEDULE_BASE, PM_ACTOR,
    },
  };
})();