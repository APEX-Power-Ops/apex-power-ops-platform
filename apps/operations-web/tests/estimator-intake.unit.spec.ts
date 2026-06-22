import { expect, test } from '@playwright/test'

import {
  buildTree,
  treeToReviewPayload,
  workbookContentType,
  type IntakeFinding,
  type LineNode,
  type ReviewPayload,
  type ScopeNode,
  type TaskNode,
} from '../lib/estimator-intake'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const DOLLAR_KEYS = [
  'onsite_labor',
  'offsite_labor',
  'travel',
  'outside_services',
  'unit_multiplier',
  'pct_adjust',
  'blended_rate',
  'quoted_revenue',
  'scope_quote',
  'diagnostic_detail',
] as const

function hasDollarKey(obj: unknown, depth = 0): boolean {
  if (depth > 10 || obj === null || typeof obj !== 'object') return false
  for (const k of DOLLAR_KEYS) {
    if (k in (obj as Record<string, unknown>)) return true
  }
  return Object.values(obj as Record<string, unknown>).some((v) =>
    Array.isArray(v)
      ? v.some((item) => hasDollarKey(item, depth + 1))
      : hasDollarKey(v, depth + 1),
  )
}

/** Minimal review_payload that matches the ops-intake engine output shape */
const REVIEW_PAYLOAD = {
  project: {
    project_number: 'P-001',
    project_name: 'Test Project',
  },
  scopes: [
    {
      scope_name: 'Switchgear',
      scope_type: 'SWITCHGEAR',
      sort_order: 0,
      quote: {
        onsite_labor: 50000,
        offsite_labor: 0,
        travel: 5000,
        outside_services: 0,
        unit_multiplier: 1.0,
        pct_adjust: 1.0,
        total_quoted_hours: 120,
      },
      lines: [
        {
          apparatus_type: 'LV Breaker',
          test_standard: 'NETA ATS 7.6.1',
          qty: 3,
          hrs_per_unit: 4.0,
          section: 'Protective Devices',
          line_uid: 'uid-001',
        },
        {
          apparatus_type: 'Transformer',
          test_standard: 'NETA ATS 7.2.1',
          qty: 1,
          hrs_per_unit: 8.0,
          section: 'Protective Devices',
          line_uid: 'uid-002',
        },
        {
          apparatus_type: 'Cable',
          test_standard: 'NETA ATS 7.3.2',
          qty: 10,
          hrs_per_unit: 1.5,
          section: null,
          line_uid: 'uid-003',
        },
      ],
    },
    {
      scope_name: 'Motors',
      scope_type: 'MOTORS',
      sort_order: 1,
      quote: {
        onsite_labor: 20000,
        offsite_labor: 0,
        travel: 0,
        outside_services: 0,
        unit_multiplier: 1.0,
        pct_adjust: 1.0,
        total_quoted_hours: 40,
      },
      lines: [
        {
          apparatus_type: 'Motor',
          test_standard: 'NETA ATS 7.15',
          qty: 4,
          hrs_per_unit: 6.0,
          section: 'Rotating Equipment',
          line_uid: 'uid-004',
        },
      ],
    },
  ],
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test('buildTree returns one ScopeNode per scope in order', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  expect(tree).toHaveLength(2)
  expect(tree[0].scopeName).toBe('Switchgear')
  expect(tree[1].scopeName).toBe('Motors')
})

test('buildTree groups lines under tasks by section', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  const switchgear = tree[0]

  const taskNames = switchgear.tasks.map((t: TaskNode) => t.taskName)
  expect(taskNames).toContain('Protective Devices')
  expect(taskNames).toContain('__ungrouped__')

  const pdTask = switchgear.tasks.find((t: TaskNode) => t.taskName === 'Protective Devices')!
  expect(pdTask.lines).toHaveLength(2)

  const ungrouped = switchgear.tasks.find((t: TaskNode) => t.taskName === '__ungrouped__')!
  expect(ungrouped.lines).toHaveLength(1)
  expect(ungrouped.lines[0].apparatusType).toBe('Cable')
})

test('buildTree LineNode exposes hoursPerUnit and totalHours', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  const switchgear = tree[0]
  const pdTask = switchgear.tasks.find((t: TaskNode) => t.taskName === 'Protective Devices')!
  const breaker = pdTask.lines.find((l: LineNode) => l.apparatusType === 'LV Breaker')!

  expect(breaker.hoursPerUnit).toBe(4.0)
  expect(breaker.qty).toBe(3)
  expect(breaker.totalHours).toBeCloseTo(12.0)
})

test('buildTree LineNode totalHours = qty x hoursPerUnit', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  for (const scope of tree) {
    for (const task of scope.tasks) {
      for (const line of task.lines) {
        expect(line.totalHours).toBeCloseTo(line.qty * line.hoursPerUnit, 4)
      }
    }
  }
})

test('buildTree ScopeNode contains NO dollar fields anywhere in the serialized tree', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  const serialized = JSON.parse(JSON.stringify(tree))
  expect(hasDollarKey(serialized)).toBe(false)
})

test('buildTree LineNode has no dollar fields individually', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  for (const scope of tree) {
    for (const task of scope.tasks) {
      for (const line of task.lines) {
        const serialized = JSON.parse(JSON.stringify(line)) as Record<string, unknown>
        for (const k of DOLLAR_KEYS) {
          expect(serialized).not.toHaveProperty(k)
        }
      }
    }
  }
})

test('IntakeFinding view-model has message but no diagnostic_detail', () => {
  const finding: IntakeFinding = {
    code: 'RECOGNIZED_CONFLICT',
    severity: 'blocking',
    ok: false,
    message: 'Project has recognized revenue; approve is blocked.',
  }
  expect(finding.message).toBeDefined()
  const serialized = JSON.parse(JSON.stringify(finding)) as Record<string, unknown>
  expect(serialized).not.toHaveProperty('diagnostic_detail')
})

test('buildTree handles scope with no lines gracefully', () => {
  const payload = {
    project: { project_number: 'P-002', project_name: 'Empty' },
    scopes: [
      {
        scope_name: 'Empty Scope',
        scope_type: 'OTHER',
        sort_order: 0,
        quote: {},
        lines: [],
      },
    ],
  }
  const tree = buildTree(payload)
  expect(tree).toHaveLength(1)
  expect(tree[0].tasks).toHaveLength(0)
})

test('buildTree Motors scope has correct line structure', () => {
  const tree = buildTree(REVIEW_PAYLOAD)
  const motors = tree[1]
  expect(motors.tasks).toHaveLength(1)
  const rotTask = motors.tasks[0]
  expect(rotTask.taskName).toBe('Rotating Equipment')
  expect(rotTask.lines).toHaveLength(1)
  expect(rotTask.lines[0].apparatusType).toBe('Motor')
  expect(rotTask.lines[0].totalHours).toBeCloseTo(24.0)
})

test('ScopeNode type is assignable', () => {
  const node: ScopeNode = {
    scopeName: 'Test',
    scopeType: 'OTHER',
    sortOrder: 0,
    tasks: [],
  }
  expect(node.scopeName).toBe('Test')
})

test('treeToReviewPayload preserves all pinned fields, overlays only section + hrs_per_unit', () => {
  // Server-pinned fields the allowlist requires preserved: the scope `quote` and the line `line_number`
  // (deliberately untyped on RawScope/RawLine, but present at runtime). The lossy rebuild dropped them
  // and a real Save-Review 400'd; this round-trip proves the deep-clone+overlay preserves them.
  const original: ReviewPayload = {
    project: { project_number: 'P1', project_name: 'N', client_name: 'C' },
    scopes: [
      {
        scope_name: 'A',
        scope_type: 'ATS',
        sort_order: 1,
        quote: { onsite_labor: 1000, offsite_labor: 0, travel: 0, outside_services: 0,
                 unit_multiplier: 1, pct_adjust: 1, total_quoted_hours: 7 },
        lines: [
          { apparatus_type: 'X', test_standard: 'ATS', qty: 2, hrs_per_unit: 2.0,
            section: 'old', line_uid: 'A:row1', line_number: 1, neta_section: '7.1' },
          { apparatus_type: 'Y', test_standard: 'ATS', qty: 3, hrs_per_unit: 1.0,
            section: 'old', line_uid: 'A:row2', line_number: 2, neta_section: '7.2' },
        ],
      },
    ],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any

  const tree = buildTree(original)
  // Edit row1: change hours AND move it to a NEW task (a section change == task regroup).
  for (const t of tree[0].tasks) {
    for (const l of t.lines) {
      if (l.lineUid === 'A:row1') { l.hoursPerUnit = 9.5; l.section = 'NEW TASK' }
    }
  }
  const out = treeToReviewPayload(tree, original)

  const expected = JSON.parse(JSON.stringify(original))
  expected.scopes[0].lines[0].section = 'NEW TASK'
  expected.scopes[0].lines[0].hrs_per_unit = 9.5
  // Deep-equality: EVERYTHING except the two overlaid fields must match byte-for-byte (incl. quote,
  // line_number, neta_section -- the fields the old rebuild silently dropped).
  expect(out).toEqual(expected)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const outScope = out.scopes[0] as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const origScope = original.scopes[0] as any
  expect(outScope.quote).toEqual(origScope.quote)            // scope dollar basis preserved
  expect(outScope.lines[0].line_number).toBe(1)              // line_number preserved
  expect(outScope.lines[1].hrs_per_unit).toBe(1.0)           // untouched line unchanged
})

test('workbookContentType derives from the file extension, not the browser MIME', () => {
  expect(workbookContentType('estimator.xlsm')).toBe('xlsm')
  expect(workbookContentType('ESTIMATOR.XLSX')).toBe('xlsm')
  expect(workbookContentType('export.json')).toBe('json')
  expect(workbookContentType('notes.txt')).toBeNull()
  expect(workbookContentType('noextension')).toBeNull()
})
