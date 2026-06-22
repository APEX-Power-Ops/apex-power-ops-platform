import { expect, test } from '@playwright/test'

import {
  buildTree,
  type IntakeFinding,
  type LineNode,
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
