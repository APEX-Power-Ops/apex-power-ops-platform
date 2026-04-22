/*
 * APEX PM Schedule Tracer Review Surface — canonical active-lane copy.
 *
 * Re-homed from `apps/pm-surface/public/tracer.js` as a bounded PM
 * read-only review slice admitted into `apps/operations-web`.
 *
 * Read-only PM review view of the BOUNDED UPSTREAM PREDECESSOR CHAIN for a
 * selected task. The tracer explains why a task is constrained by walking
 * predecessor edges in `schedule.relationships` backwards, up to a bounded
 * depth. This is the narrow first slice UI-002f authorizes; it does NOT
 * render a general graph view, does NOT fabricate edges the schedule does
 * not carry, and does NOT expose mutation behavior.
 */

(function () {
  const { useState, useEffect, useCallback, useMemo } = React;

  const SCHEDULE_BASE = 'http://localhost:8000/api/v1/schedule';
  const PM_ACTOR = { actor_id: 'pm-001', actor_role: 'pm', project_scope: ['proj-001'] };
  const DEFAULT_MAX_DEPTH = 10;

  function makeToken(actor) {
    return 'Bearer ' + btoa(JSON.stringify(actor));
  }

  async function tracerGet(path) {
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

  function useTracerChain(taskId, maxDepth) {
    const [edges, setEdges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [online, setOnline] = useState(true);
    const [error, setError] = useState(null);
    const [lastRefresh, setLast] = useState(null);

    const refresh = useCallback(async () => {
      if (!taskId) {
        setEdges([]);
        setLoading(false);
        setOnline(true);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const qs = `?task_id=${encodeURIComponent(taskId)}&max_depth=${encodeURIComponent(maxDepth || DEFAULT_MAX_DEPTH)}`;
        const rows = await tracerGet(`/tracer${qs}`);
        setEdges(rows);
        setOnline(true);
        setLast(new Date());
      } catch (e) {
        setOnline(false);
        setError(String(e && e.message || e));
      } finally {
        setLoading(false);
      }
    }, [taskId, maxDepth]);

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

  function labelFor(task_code, p6_task_id, task_id) {
    return task_code || p6_task_id || task_id || '—';
  }

  function fmtLagHours(h) {
    const n = Number(h || 0);
    if (!Number.isFinite(n) || n === 0) return '0h';
    return `${n > 0 ? '+' : ''}${n}h`;
  }

  function groupByDepth(edges) {
    const groups = new Map();
    for (const e of edges) {
      const d = Number(e.depth || 0);
      if (!groups.has(d)) groups.set(d, []);
      groups.get(d).push(e);
    }
    return Array.from(groups.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([depth, rows]) => ({ depth, edges: rows }));
  }

  function summarizeChain(edges) {
    const total = edges.length;
    let maxDepth = 0;
    const uniqueParents = new Set();
    let parentsOnCritical = 0;
    for (const e of edges) {
      if (Number(e.depth || 0) > maxDepth) maxDepth = Number(e.depth || 0);
      const p = e.parent_task_id;
      if (p && !uniqueParents.has(p)) {
        uniqueParents.add(p);
        if (e.parent_critical_flag) parentsOnCritical += 1;
      }
    }
    return {
      total,
      maxDepth,
      uniqueParents: uniqueParents.size,
      parentsOnCritical,
    };
  }

  function ChainRow({ edge, i, onTraceTask }) {
    const depth = Number(edge.depth || 0);
    const indent = Math.min(depth - 1, 8) * 14;
    const parentCritical = !!edge.parent_critical_flag;
    const childCritical = !!edge.child_critical_flag;
    const relTypeColor = edge.rel_type === 'FS' ? '#015687'
      : edge.rel_type === 'SS' ? '#5FA844'
      : edge.rel_type === 'FF' ? '#b45309'
      : edge.rel_type === 'SF' ? '#6b21a8'
      : '#4b5563';
    const parentLabel = labelFor(edge.parent_task_code, edge.parent_p6_task_id, edge.parent_task_id);
    const childLabel = labelFor(edge.child_task_code, edge.child_p6_task_id, edge.child_task_id);

    return React.createElement('div', {
      style: {
        display: 'grid',
        gridTemplateColumns: '32px 180px 40px 180px 64px 64px 1fr',
        gap: 10, alignItems: 'center',
        padding: `6px 10px 6px ${10 + indent}px`,
        background: i % 2 ? '#fafafa' : 'white',
        borderBottom: '1px solid #f3f4f6', fontSize: 12,
      },
    },
      React.createElement('div', {
        style: {
          fontSize: 10, fontWeight: 700, color: '#6b7280',
          textAlign: 'center', fontFamily: 'monospace',
        },
      }, `d${depth}`),
      React.createElement('div', {
        style: {
          color: parentCritical ? '#dc2626' : '#111827',
          fontWeight: parentCritical ? 700 : 500,
        },
      },
        React.createElement('div', null, parentLabel),
        React.createElement('div', { style: { fontSize: 10, color: '#6b7280', fontWeight: 400 } },
          edge.parent_task_name || ''),
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
        style: {
          color: childCritical ? '#dc2626' : '#111827',
          fontWeight: childCritical ? 700 : 500,
        },
      },
        React.createElement('div', null, childLabel),
        React.createElement('div', { style: { fontSize: 10, color: '#6b7280', fontWeight: 400 } },
          edge.child_task_name || ''),
      ),
      React.createElement('div', { style: { fontSize: 11, color: '#4b5563' } },
        fmtDate(edge.parent_planned_finish)),
      React.createElement('div', { style: { fontSize: 11, color: '#4b5563' } },
        fmtDate(edge.child_planned_start)),
      React.createElement('div', {
        style: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, color: '#6b7280' },
      },
        React.createElement('span', { style: { flex: 1 } },
          `parent float: ${edge.parent_total_float_hours ?? '—'} h`
          + (parentCritical ? ' · parent on critical path' : '')),
        (onTraceTask && edge.parent_task_id) && React.createElement('button', {
          onClick: (ev) => {
            ev.stopPropagation();
            onTraceTask({
              taskId: edge.parent_task_id,
              taskLabel: (edge.parent_task_code || edge.parent_p6_task_id || edge.parent_task_id)
                + (edge.parent_task_name ? ' — ' + edge.parent_task_name : ''),
            });
          },
          title: 'Reseed tracer from this upstream parent',
          style: {
            fontSize: 10, padding: '2px 8px', whiteSpace: 'nowrap',
            border: '1px solid #93c5fd', borderRadius: 4,
            background: 'white', color: '#1e40af', cursor: 'pointer',
          },
        }, '🔍 Reseed'),
      ),
    );
  }

  function TracerReviewView({ taskId, maxDepth, taskLabel, onTraceTask }) {
    const hook = useTracerChain(taskId, maxDepth);
    const summary = useMemo(() => summarizeChain(hook.edges), [hook.edges]);

    if (!taskId) {
      return React.createElement('div', {
        className: 'card', style: { padding: 16, color: '#6b7280', fontSize: 13 },
      }, 'Select a task to trace its upstream constraint chain.');
    }
    if (hook.loading && hook.edges.length === 0) {
      return React.createElement('div', { className: 'card text-center p-8' },
        'Loading upstream tracer…');
    }
    if (!hook.online) {
      return React.createElement('div', {
        className: 'card', style: { borderLeft: '3px solid #dc2626' },
      },
        React.createElement('div', { style: { fontWeight: 700, color: '#991b1b' } },
          'Schedule tracer bridge offline'),
        React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 4 } },
          hook.error || 'Could not reach /api/v1/schedule/tracer. Confirm the mutation-seam server is running and the schedule.* tables are populated.'),
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
          React.createElement('h2', { className: 'text-lg font-bold resa-blue', style: { margin: 0 } }, 'Upstream constraint trace'),
          React.createElement('div', { style: { fontSize: 12, color: '#4b5563', marginTop: 2 } },
            `Traced from ${taskLabel || taskId} — bounded ancestor chain. Read-only.`),
        ),
        React.createElement('div', { style: { textAlign: 'right', fontSize: 11, color: '#6b7280' } },
          React.createElement('div', null,
            `${summary.total} edge${summary.total === 1 ? '' : 's'} · max depth ${summary.maxDepth} · ${summary.uniqueParents} unique upstream · ${summary.parentsOnCritical} on critical path`),
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
            gridTemplateColumns: '32px 180px 40px 180px 64px 64px 1fr',
            gap: 10, alignItems: 'center',
            padding: '8px 10px', borderBottom: '1px solid #e5e7eb',
            background: '#f9fafb', fontSize: 10,
            textTransform: 'uppercase', color: '#6b7280', fontWeight: 700,
            letterSpacing: '0.04em',
          },
        },
          React.createElement('div', null, 'Dep'),
          React.createElement('div', null, 'Upstream parent'),
          React.createElement('div', { style: { textAlign: 'center' } }, 'Rel'),
          React.createElement('div', null, 'Downstream child'),
          React.createElement('div', null, 'Parent fin'),
          React.createElement('div', null, 'Child start'),
          React.createElement('div', null, 'Context'),
        ),
        hook.edges.length === 0
          ? React.createElement('div', {
              style: { padding: 20, fontSize: 12, color: '#6b7280', textAlign: 'center' },
            }, 'No upstream predecessors for this task. It is at the root of its dependency chain.')
          : hook.edges.map((e, i) => React.createElement(ChainRow, {
              key: e.relationship_id || `row-${i}`,
              edge: e, i, onTraceTask,
            })),
      ),
      React.createElement('div', {
        style: { marginTop: 10, fontSize: 11, color: '#5FA844', fontWeight: 600 },
      }, 'Read-only · traversal bounded by server · no schedule writes'),
    );
  }

  window.ApexTracer = {
    TracerReviewView,
    useTracerChain,
    __internals__: {
      parseTs, fmtDate, fmtLagHours, labelFor,
      groupByDepth, summarizeChain,
      SCHEDULE_BASE, PM_ACTOR, DEFAULT_MAX_DEPTH,
    },
  };
})();