import { expect, test } from '@playwright/test'
import {
  actionFlags,
  CLEARANCE_VALUES,
  ATTEST_COPY,
  type WorklistRow,
} from '../lib/recognition'

function row(over: Partial<WorklistRow>): WorklistRow {
  return {
    apparatus_id: 'a1', apparatus_designation: 'A-1', scope_id: 's1', project_id: 'p1',
    project_number: 'PN-1', status: 'In Progress', quoted_hours: 10, quoted_revenue: 1500,
    attestation_id: null, attested_by: null, attested_at: null, attest_reason: null,
    net_recognized: 0, is_recognized: false, recognized_event_id: null,
    can_attest: false, can_recognize: false, can_revoke: false, can_reverse: false,
    ...over,
  }
}

test('actionFlags passes the view flags through verbatim', () => {
  const f = actionFlags(row({ can_attest: true }))
  expect(f).toEqual({ canAttest: true, canRecognize: false, canRevoke: false, canReverse: false })
})

test('recognized row exposes only reverse', () => {
  const f = actionFlags(row({ is_recognized: true, can_reverse: true }))
  expect(f).toEqual({ canAttest: false, canRecognize: false, canRevoke: false, canReverse: true })
})

test('clearance enum is exactly provided|not_applicable', () => {
  expect([...CLEARANCE_VALUES].sort()).toEqual(['not_applicable', 'provided'])
})

test('attest copy is for-recognition, never production complete', () => {
  expect(ATTEST_COPY).toContain('for recognition')
  expect(ATTEST_COPY.toLowerCase()).not.toContain('production complete')
})
