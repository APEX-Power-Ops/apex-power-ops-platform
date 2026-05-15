import { expect, test } from '@playwright/test'

test('pm import admission plan renders read-only future import gate', async ({ page }) => {
  let readCalls = 0
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  await page.route('**/api/v1/reads/project-import-admission-plan', async (route) => {
    readCalls += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        admission_plan_id: 'pm-import-candidate-miner-temp-power-admission-plan',
        admission_plan_version: 'pm_import_admission_plan_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        candidate_version: 'pm_import_candidate_read_only_v1',
        review_status: 'read_only_admission_design',
        readiness_status: 'needs_human_acceptance_before_import_packet',
        mutation_authority: 'not_admitted',
        candidate_shape_fingerprint: 'shape-fp-123',
        source_stat_fingerprint: 'source-fp-456',
        target_row_plan: {
          project_rows: 1,
          workpackage_rows: 7,
          task_rows: 15,
          apparatus_rows: 186,
          source_trace_rows: 201,
          warning_review_rows: 2,
          approval_rows: 1,
          write_authority: 'not_admitted',
        },
        warning_breakdown: {
          info: 1,
          warning: 1,
        },
        approval_record_contract: {
          record_type: 'pm_import_candidate_approval',
          storage_authority: 'not_admitted',
          required_fields: [
            'candidate_id',
            'candidate_version',
            'source_stat_fingerprint',
            'candidate_shape_fingerprint',
            'idempotency_key',
            'decision',
            'approved_by_actor_id',
            'approved_at_utc',
            'accepted_warning_codes',
            'accepted_no_go_overrides',
            'review_notes',
          ],
          permitted_decisions: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
          minimum_expected_values: {
            candidate_id: 'pm-import-candidate-miner-temp-power',
            candidate_version: 'pm_import_candidate_read_only_v1',
            source_stat_fingerprint: 'source-fp-456',
            candidate_shape_fingerprint: 'shape-fp-123',
            accepted_warning_codes: ['MISSING_DESIGNATIONS', 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'],
          },
          operator_attestation: 'The PM must confirm the candidate shape, source fingerprint, warning acceptance, and no-go override list before any future import mutation may be admitted.',
        },
        idempotency_plan: {
          strategy: 'candidate_version_source_shape_counts',
          components: {
            candidate_id: 'pm-import-candidate-miner-temp-power',
            source_stat_fingerprint: 'source-fp-456',
          },
          sample_key: 'pm-import:idempotency-sample-789',
          collision_policy: 'same key must be treated as a replay of the same approved candidate',
        },
        preview_to_import_diff_checks: [
          {
            check_id: 'candidate-id-version-match',
            compare: ['approval_record.candidate_id', 'approval_record.candidate_version'],
            expected: ['pm-import-candidate-miner-temp-power', 'pm_import_candidate_read_only_v1'],
            failure_action: 'stop import and regenerate approval packet',
          },
          {
            check_id: 'source-stat-fingerprint-match',
            compare: ['approval_record.source_stat_fingerprint', 'current_candidate.source_freshness.aggregate_fingerprint'],
            expected: 'source-fp-456',
            failure_action: 'stop import and refresh source review because source files changed',
          },
          {
            check_id: 'candidate-shape-fingerprint-match',
            compare: ['approval_record.candidate_shape_fingerprint', 'current_candidate.shape_fingerprint'],
            expected: 'shape-fp-123',
            failure_action: 'stop import and re-review workpackages, tasks, and apparatus',
          },
        ],
        no_go_checks: [
          {
            check_id: 'candidate-has-no-blockers',
            status: 'pass',
            message: '0 blocker warning(s) reported by the import candidate.',
            required_resolution: 'Resolve blocker warnings before any import mutation can be admitted.',
          },
          {
            check_id: 'warnings-reviewed-by-pm',
            status: 'needs_human_acceptance',
            message: '2 warning signal(s) must be reviewed.',
            required_resolution: 'Record warning-code acceptance in the future approval record before import.',
          },
          {
            check_id: 'approval-record-required',
            status: 'pending_future_admission',
            message: 'No server-side approval record is admitted in this tranche.',
            required_resolution: 'A later packet must admit approval persistence before import can execute.',
          },
          {
            check_id: 'mutation-path-not-admitted',
            status: 'no_go',
            message: 'This endpoint is a read-only plan and has no import mutation authority.',
            required_resolution: 'A separate packet must admit a narrow idempotent mutation before writes are possible.',
          },
        ],
        future_import_sequence: [
          'PM reviews import candidate warnings, source freshness, and proposed rows.',
          'A later packet admits approval persistence and records a PM approval record.',
          'The import packet re-reads the candidate and compares source, shape, count, and warning fingerprints.',
        ],
        not_allowed_now: [
          'persist_approval_record',
          'write_supabase',
          'run_workbook_macros',
          'import_project_rows',
          'assign_work',
          'mutate_schedule',
          'change_status',
          'autonomous_ai_business_state_mutation',
        ],
      }),
    })
  })

  const response = await page.goto('/pm-review/import-admission-plan', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Design the import gate before it can write/i })).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power-admission-plan/i)).toBeVisible()
  await expect(page.getByText(/not_admitted/i).first()).toBeVisible()
  await expect(page.getByText(/needs human acceptance before import packet/i)).toBeVisible()
  await expect(page.getByText(/pm-import:idempotency-sample-789/i).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: /Approval Record Contract/i })).toBeVisible()
  await expect(page.getByText('source stat fingerprint', { exact: true })).toBeVisible()
  await expect(page.getByText('accepted warning codes', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: /Preview-To-Import Diff Checks/i })).toBeVisible()
  await expect(page.getByText(/source stat fingerprint match/i)).toBeVisible()
  await expect(page.getByLabel('No-go checks').getByRole('heading', { name: /No-Go Checks/i })).toBeVisible()
  await expect(page.getByText(/mutation path not admitted/i)).toBeVisible()
  await expect(page.getByText(/write supabase/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Import candidate/i })).toHaveAttribute('href', '/pm-review/import-candidate')
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /^Import$/i })).toHaveCount(0)
  expect(mutationRequests).toHaveLength(0)
  expect(readCalls).toBe(1)
})
