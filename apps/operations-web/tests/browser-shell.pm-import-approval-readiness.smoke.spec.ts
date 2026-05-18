import { expect, test } from '@playwright/test'

test('pm import approval readiness renders read-only approval and storage gates', async ({ page }) => {
  let contractReadCalls = 0
  let storagePlanReadCalls = 0
  const mutationRequests: string[] = []

  await page.addInitScript(() => {
    window.localStorage.setItem(
      'pm-import-candidate-approval-preview:pm-import-candidate-miner-temp-power',
      JSON.stringify({
        preview_kind: 'pm_import_candidate_review_approval_preview',
        preview_version: 'pm_import_candidate_review_approval_preview_v1',
        generated_locally_at: '2026-05-18T15:45:00.000Z',
        storage: 'local_browser_only',
        local_review_evidence: {
          review_notes: 'Check PD-1 duplicate rows before future import approval.',
          manual_task_shaping: {
            summary: {
              group_count: 2,
              regrouped_apparatus_count: 1,
              designation_override_count: 1,
            },
            groups: [
              {
                group_id: 'source-task:candidate-task-0001',
                title: 'PD-1 - Switch MV - Fused Disconnect',
                designation: 'PD-1',
                apparatus_count: 1,
                planned_hours: 2.5,
              },
              {
                group_id: 'manual-task:2:test',
                title: 'Breaker lineup split',
                designation: 'PD-1B',
                apparatus_count: 1,
                planned_hours: 2.5,
              },
            ],
          },
        },
        downstream_review_context: {
          contract_role: 'Browser-local PM review context for later admitted approval persistence review only.',
        },
      }),
    )
  })

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  await page.route('**/api/v1/reads/project-import-approval-contract', async (route) => {
    contractReadCalls += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        approval_contract_id: 'pm-import-candidate-miner-temp-power-approval-persistence-contract',
        approval_contract_version: 'pm_import_approval_persistence_contract_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        candidate_version: 'pm_import_candidate_read_only_v1',
        readiness_status: 'needs_human_acceptance_before_import_packet',
        mutation_authority: 'not_admitted',
        persistence_authority: 'design_only_not_admitted',
        storage_decision: 'pending_future_packet',
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
            idempotency_key: 'pm-import:idempotency-sample-789',
            accepted_warning_codes: ['MISSING_DESIGNATIONS', 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'],
          },
          operator_attestation: 'The PM must confirm the candidate shape, source fingerprint, warning acceptance, and no-go override list before any future import mutation may be admitted.',
        },
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
          idempotency_key: 'pm-import:idempotency-sample-789',
          accepted_warning_codes: ['MISSING_DESIGNATIONS', 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'],
          accepted_no_go_overrides: ['warnings-reviewed-by-pm'],
        },
        candidate_identity: {
          candidate_id: 'pm-import-candidate-miner-temp-power',
          candidate_version: 'pm_import_candidate_read_only_v1',
          source_stat_fingerprint: 'source-fp-456',
          candidate_shape_fingerprint: 'shape-fp-123',
          idempotency_key: 'pm-import:idempotency-sample-789',
        },
        human_acceptance_policy: {
          accepted_no_go_overrides_field: 'accepted_no_go_overrides',
          required_human_acceptance_check_ids: ['warnings-reviewed-by-pm'],
          non_overridable_check_ids: ['approval-record-required', 'mutation-path-not-admitted'],
          policy: 'PM may acknowledge needs_human_acceptance checks; no_go and pending_future_admission checks remain blocked until a later packet changes authority.',
        },
        decision_payload_template: {
          candidate_id: 'pm-import-candidate-miner-temp-power',
          candidate_version: 'pm_import_candidate_read_only_v1',
          source_stat_fingerprint: 'source-fp-456',
          candidate_shape_fingerprint: 'shape-fp-123',
          idempotency_key: 'pm-import:idempotency-sample-789',
          decision: 'approve_for_import_packet',
          approved_by_actor_id: '<pm actor id>',
          approved_at_utc: '<server timestamp in future admitted mutation>',
          accepted_warning_codes: ['MISSING_DESIGNATIONS', 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'],
          accepted_no_go_overrides: ['warnings-reviewed-by-pm'],
          review_notes: '<PM review note required before persistence>',
        },
        validation_matrix: [
          {
            check_id: 'required-fields-present',
            fields: ['candidate_id', 'candidate_version', 'decision'],
            failure_action: 'reject approval packet before persistence',
          },
          {
            check_id: 'decision-is-permitted',
            permitted_decisions: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
            failure_action: 'reject approval packet before persistence',
          },
        ],
        future_mutation_contract: {
          proposed_entity_type: 'pm_import_candidate_approval',
          proposed_action: 'persist_import_approval',
          proposed_route: '/api/v1/mutations/project-import-approvals',
          current_authority: 'not_admitted',
          idempotency_policy: 'same key must be treated as a replay of the same approved candidate',
        },
        not_allowed_now: [
          'persist_approval_record',
          'write_supabase',
          'run_workbook_macros',
          'write_workbooks',
          'import_project_rows',
          'assign_work',
          'mutate_schedule',
          'change_status',
          'autonomous_ai_business_state_mutation',
        ],
      }),
    })
  })

  await page.route('**/api/v1/reads/project-import-approval-storage-plan', async (route) => {
    storagePlanReadCalls += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        storage_plan_id: 'pm-import-candidate-miner-temp-power-approval-storage-plan',
        storage_plan_version: 'pm_import_approval_storage_plan_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        candidate_version: 'pm_import_candidate_read_only_v1',
        mutation_authority: 'not_admitted',
        persistence_authority: 'storage_decision_only_not_admitted',
        selected_storage_decision: 'dedicated_insert_only_import_candidate_approval_table',
        recommended_schema: 'seam',
        recommended_table: 'seam.pm_import_candidate_approvals',
        recommended_entity_type: 'pm_import_candidate_approval',
        recommended_route: '/api/v1/mutations/project-import-approvals',
        contract_dependency: {
          approval_contract_id: 'pm-import-candidate-miner-temp-power-approval-persistence-contract',
          approval_contract_version: 'pm_import_approval_persistence_contract_read_only_v1',
        },
        record_lifecycle: {
          write_model: 'insert_once_with_idempotent_replay',
          update_policy: 'do_not_update_canonical_records; changed source or candidate shape produces a new approval record',
          delete_policy: 'no delete path in the PM runtime',
          audit_policy: 'record a separate audit event after the approval record insert succeeds',
          import_policy: 'import packet may consume an approved current record, but this storage plan does not import rows',
        },
        recommended_columns: [
          {
            name: 'approval_record_id',
            type: 'text',
            required: true,
            source: 'server generated deterministic id from candidate identity and idempotency key',
          },
          { name: 'candidate_id', type: 'text', required: true, source: 'approval payload' },
          {
            name: 'decision',
            type: 'text',
            required: true,
            source: 'approval payload',
            allowed_values: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
          },
        ],
        recommended_constraints: [
          {
            constraint_id: 'approval-record-primary-key',
            applies_to: ['approval_record_id'],
            rule: 'primary key; replay with the same idempotency key must return the same stored record',
          },
          {
            constraint_id: 'decision-is-permitted',
            applies_to: ['decision'],
            rule: 'decision must be one of the approval contract permitted decisions',
            allowed_values: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
          },
        ],
        adapter_requirements: [
          'Use an explicit approval adapter or repository instead of the generic mutation_pipeline apply step.',
          'Validate with validate_project_import_approval_payload before any insert.',
          'Do not create project, workpackage, task, apparatus, assignment, schedule, issue, or status rows in this adapter.',
        ],
        readback_requirements: [
          'Read current approval status by candidate id and current candidate identity.',
          'Do not treat audit history alone as current approval state.',
        ],
        rejected_storage_options: [
          {
            option: 'audit_log_only',
            reason: 'Audit rows are evidence of actions, not the canonical approval object an import packet should diff against.',
          },
          {
            option: 'generic_pgdict_upsert_without_adapter',
            reason: 'The generic store upserts by id; canonical approvals should be insert-only or strict idempotent replay.',
          },
        ],
        future_admission_sequence: [
          'Approve this storage decision as a packet.',
          'Add a narrow schema migration for the dedicated approval table.',
          'Add an explicit insert-only approval adapter with idempotent replay.',
          'Add a Class C PM-only POST route for approval persistence.',
        ],
        not_allowed_now: [
          'persist_approval_record',
          'write_supabase',
          'create_schema',
          'run_schema_migration',
          'run_workbook_macros',
          'write_workbooks',
          'import_project_rows',
          'assign_work',
          'mutate_schedule',
          'change_status',
          'autonomous_ai_business_state_mutation',
        ],
      }),
    })
  })

  const response = await page.goto('/pm-review/import-approval-readiness', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Review the approval gate before it can persist/i })).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power-approval-persistence-contract/i).first()).toBeVisible()
  await expect(page.getByText(/pm_import_approval_persistence_contract_read_only_v1/i).first()).toBeVisible()
  await expect(page.getByText(/pm_import_approval_storage_plan_read_only_v1/i).first()).toBeVisible()
  await expect(page.getByText(/design_only_not_admitted/i).first()).toBeVisible()
  await expect(page.getByText(/storage_decision_only_not_admitted/i).first()).toBeVisible()
  await expect(page.getByText(/Import candidate staged browser-local approval preview context at 2026-05-18T15:45:00.000Z/i)).toBeVisible()
  await expect(page.getByText(/seam\.pm_import_candidate_approvals/i).first()).toBeVisible()
  await expect(page.getByText('/api/v1/mutations/project-import-approvals').first()).toBeVisible()
  await expect(page.getByText(/audit log only/i)).toBeVisible()
  await expect(page.getByText(/write supabase/i)).toBeVisible()
  await expect(page.getByText(/run schema migration/i)).toBeVisible()
  await expect(page.getByText(/persist approval record/i)).toBeVisible()
  await expect(page.getByText(/autonomous ai business state mutation/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Candidate Review Context/i })).toBeVisible()
  await expect(page.getByText(/Check PD-1 duplicate rows before future import approval./i)).toBeVisible()
  await expect(page.getByText(/Breaker lineup split/i)).toBeVisible()
  await expect(page.getByText(/Regrouped apparatus/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Import candidate/i })).toHaveAttribute('href', '/pm-review/import-candidate')
  await expect(page.getByRole('link', { name: /Admission plan/i })).toHaveAttribute('href', '/pm-review/import-admission-plan')
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Persist/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /^Import$/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Submit/i })).toHaveCount(0)
  expect(mutationRequests).toHaveLength(0)
  expect(contractReadCalls).toBe(1)
  expect(storagePlanReadCalls).toBe(1)
})
