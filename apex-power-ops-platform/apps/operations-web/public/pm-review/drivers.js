/*
 * APEX PM Schedule Drivers Review Surface — canonical active-lane copy.
 *
 * Re-homed from `apps/pm-surface/public/drivers.js` as the first bounded
 * PM read-only review slice admitted into `apps/operations-web`.
 *
 * Read-only PM review view of CRITICAL-PATH DRIVING EDGES only. An edge is
 * "driving" when the predecessor sits on the critical path. This is the
 * narrow first slice authorized by UI-002e; it intentionally does NOT render
 * the full TASKPRED graph, does NOT show a broader float-driver analysis,
 * and does NOT fabricate dependency semantics the schedule does not already
 * carry.
 *
 * Posture (per UI-002e packet + Source-Of-Truth memo §2.2 / §3):
 *   * READ-ONLY BY CONSTRUCTION. Every fetch below is GET against
 *     `/api/v1/schedule/drivers`. No form inputs, no drag-to-reschedule,
 *     no inline dependency editing. If a future packet introduces schedule
 *     writes they must go through the governed mutation seam, not here.
 *   * Mirrors the actor-token pattern used by schedule.js so no new auth
 *     surface is introduced.
 *   * Exposes `window.ApexDrivers = { DriversReviewView, useDriverEdges }`
 *     so a static host shell can mount it, and a small `__internals__` set
 *     for Node sandbox tests.
 */

(function () {
  const { useState, useEffect, useCallback, useMemo } = React;

  const SCHEDULE_BASE = 'http://localhost:8000/api/v1/schedule';
  const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] };

  function makeToken(actor) {
    return 'Bearer ' + btoa(JSON.stringify(actor));
  }

  async function driversGet(path) {
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

  function useDriverEdges(projectId) {
    const [edges, setEdges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [online, setOnline] = useState(true);
    const [error, setError] = useState(null);
    const [lastRefresh, setLast] = useState(null);

    const refresh = useCallback(async () => {
      setLoading(true);
      setError(null);
      try {
        const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
        const rows = await driversGet(`/drivers${qs}`);
        setEdges(rows);
        setOnline(true);
        setLast(new Date());
      } catch (e) {
        setOnline(false);
        setError(String(e && e.message || e));
      } finally {
        setLoading(false);
      }
    }, [projectId]);

    useEffect(() => { refresh(); }, [refresh]);

    return { edges, loading, online, error, lastRefresh, refresh };
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

  function fmtLagHours(h) {
    const n = Number(h || 0);
    if (!Number.isFinite(n) || n === 0) return '0h';
    return `${n > 0 ? '+' : ''}${n}h`;
  }

  function labelFor(task_code, p6_task_id, task_id) {
    return task_code || p6_task_id || task_id || '—';
  }

  function summarizeEdges(edges) {
    const total = edges.length;
    const drivenOnCritical = edges.filter(e => !!e.driven_critical_flag).length;
    const withPositiveLag = edges.filter(e => Number(e.lag_hours || 0) > 0).length;
    const withNegativeLag = edges.filter(e => Number(e.lag_hours || 0) < 0).length;
    return { total, drivenOnCritical, withPositiveLag, withNegativeLag };
  }

  function DriverRow({ edge, i, onTraceTask, onViewVariance, onViewSchedule, focusTaskId }) {
    const drivenCritical = !!edge.driven_critical_flag;
    const relTypeColor = edge.rel_type === 'FS' ? '#015687'
      : edge.rel_type === 'SS' ? '#5FA844'
      : edge.rel_type === 'FF' ? '#b45309'
      : edge.rel_type === 'SF' ? '#6b21a8'
      : '#4b5563';
    const driverLabel = labelFor(edge.driver_task_code, edge.driver_p6_task_id, edge.driver_task_id);
    const drivenLabel = labelFor(edge.driven_task_code, edge.driven_p6_task_id, edge.driven_task_id);
    const isFocused = !!(focusTaskId && (
      edge.driver_task_id === focusTaskId || edge.driven_task_id === focusTaskId
    ));

    return React.createElement('div', {
      'data-focus-match': isFocused ? 'true' : null,
      style: {
        display: 'grid',
        gridTemplateColumns: '160px 40px 160px 48px 56px 1fr',
        gap: 10, alignItems: 'center', padding: '6px 10px',
        background: isFocused ? '#dbeafe' : (i % 2 ? '#fafafa' : 'white'),
        outline: isFocused ? '2px solid #015687' : 'none',
        outlineOffset: isFocused ? '-2px' : '0',
        borderBottom: '1px solid #f3f4f6', fontSize: 12,
      },
    },
      React.createElement('div', { style: { color: '#dc2626', fontWeight: 700 } },
        React.createElement('div', null, driverLabel),
        React.createElement('div', { style: { fontSize: 10, color: '#6b7280', fontWeight: 400 } },
          edge.driver_task_name || ''),
      ),
      React.createElement('div', {
        style: {
          textAlign: 'center', fontWeight: 700, color: relTypeColor,
          fontFamily: 'monospace', fontSize: 11,
        },
      },
        React.createElement('div', null, edge.rel_type || '—'),
        React.createElement('div', { style: { fontSize: 9, color: '#6b7280', fontWeight: 400 } },
          fmtLagHours(edge.lag_hours)),
      ),
      React.createElement('div', {
        style: { color: drivenCritical ? '#dc2626' : '#111827', fontWeight: drivenCritical ? 700 : 500 },
      },
        React.createElement('div', null, drivenLabel),
        React.createElement('div', { style: { fontSize: 10, color: '#6b7280', fontWeight: 400 } },
          edge.driven_task_name || ''),
      ),
      React.createElement('div', { style: { fontSize: 11, color: '#4b5563' } },
        fmtDate(edge.driver_planned_finish)),
      React.createElement('div', { style: { fontSize: 11, color: '#4b5563' } },
        fmtDate(edge.driven_planned_start)),
      React.createElement('div', {
        style: { fontSize: 10, color: '#6b7280', display: 'flex', alignItems: 'center', gap: 8 },
      },
        React.createElement('span', { style: { flex: 1 } },
          `driver float: ${edge.driver_total_float_hours ?? '—'} h`,
          drivenCritical ? ' · driven also on critical path' : '',
        ),
        onTraceTask && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onTraceTask({
              taskId: edge.driven_task_id,
              taskLabel: labelFor(edge.driven_task_code, edge.driven_p6_task_id, edge.driven_task_id)
                + (edge.driven_task_name ? ' — ' + edge.driven_task_name : ''),
            });
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'Trace the upstream constraint chain for this driven task',
        }, '🔍 Trace upstream'),
        onViewVariance && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onViewVariance(edge.driven_task_id);
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'View the driven task in the Variance surface',
        }, '📈 Variance'),
        onViewSchedule && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onViewSchedule(edge.driven_task_id);
          },
          className: 'btn btn-outline',
          style: { fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap' },
          title: 'View the driven task in the Schedule',
        }, '📊 Schedule'),
      ),
    );
  }

  function DriversReviewView({ projectId, onTraceTask, onViewVariance, onViewSchedule, focusTaskId }) {
    const hook = useDriverEdges(projectId);
    const summary = useMemo(() => summarizeEdges(hook.edges), [hook.edges]);

    useEffect(() => {
      if (!focusTaskId || hook.edges.length === 0) return;
      const first = document.querySelector('[data-focus-match="true"]');
      if (first && typeof first.scrollIntoView === 'function') {
        first.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
    }, [focusTaskId, hook.edges.length]);

    if (hook.loading && hook.edges.length === 0) {
      return React.createElement('div', { className: 'card text-center p-8' },
        'Loading schedule drivers…');
    }
    if (!hook.online) {
      return React.createElement('div', {
        className: 'card', style: { borderLeft: '3px solid #dc2626' },
      },
        React.createElement('div', { style: { fontWeight: 700, color: '#991b1b' } },
          'Schedule drivers bridge offline'),
        React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 4 } },
          hook.error
            || 'Could not reach /api/v1/schedule/drivers. Confirm the mutation-seam server is running and the schedule.* tables are populated.'),
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
          marginBottom: 12,
        },
      },
        React.createElement('div', null,
          React.createElement('h2', { className: 'text-lg font-bold resa-blue', style: { margin: 0 } }, 'Critical-path driving edges'),
          React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 2 } },
            'First slice — predecessor on critical path. Read-only.'),
        ),
        React.createElement('div', { style: { textAlign: 'right', fontSize: 11, color: '#6b7280' } },
          React.createElement('div', null,
            `${summary.total} edge${summary.total === 1 ? '' : 's'} · ${summary.drivenOnCritical} driven-also-critical · ${summary.withPositiveLag}+lag / ${summary.withNegativeLag}−lag`),
          React.createElement('button', {
            onClick: hook.refresh, className: 'btn btn-outline',
            style: { marginTop: 6, fontSize: 11, padding: '4px 10px' },
          }, 'Refresh'),
        ),
      ),
      React.createElement('div', { className: 'card', style: { padding: 0, overflow: 'hidden' } },
        React.createElement('div', {
          style: {
            display: 'grid',
            gridTemplateColumns: '160px 40px 160px 48px 56px 1fr',
            gap: 10, alignItems: 'center',
            padding: '8px 10px', borderBottom: '1px solid #e5e7eb',
            background: '#f9fafb', fontSize: 10,
            textTransform: 'uppercase', color: '#6b7280', fontWeight: 700,
            letterSpacing: '0.04em',
          },
        },
          React.createElement('div', null, 'Driver (on critical path)'),
          React.createElement('div', { style: { textAlign: 'center' } }, 'Rel'),
          React.createElement('div', null, 'Driven task'),
          React.createElement('div', null, 'Drv finish'),
          React.createElement('div', null, 'Drvn start'),
          React.createElement('div', null, 'Context'),
        ),
        hook.edges.length === 0
          ? React.createElement('div', {
              style: { padding: 20, fontSize: 12, color: '#6b7280', textAlign: 'center' },
            }, 'No critical-path driving edges landed for this project.')
          : hook.edges.map((e, i) => React.createElement(DriverRow, {
              key: e.relationship_id || `row-${i}`,
              edge: e, i, onTraceTask, onViewVariance, onViewSchedule, focusTaskId,
            })),
      ),
      React.createElement('div', {
        style: { marginTop: 10, fontSize: 11, color: '#5FA844', fontWeight: 600 },
      }, 'Read-only · no schedule writes'),
    );
  }

  window.ApexDrivers = {
    DriversReviewView,
    useDriverEdges,
    __internals__: {
      parseTs, fmtDate, fmtLagHours, labelFor, summarizeEdges,
      SCHEDULE_BASE, PM_ACTOR,
    },
  };
})();