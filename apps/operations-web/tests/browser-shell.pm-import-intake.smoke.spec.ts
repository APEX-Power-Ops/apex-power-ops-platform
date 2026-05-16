import { expect, test } from '@playwright/test'

test('pm import intake workbench renders consolidated read-only Project Miner gates', async ({ page }) => {
  const readCalls = {
    candidate: 0,
    admissionPlan: 0,
    approvalContract: 0,
    storagePlan: 0,
  }
  const mutationRequests: string[] = []

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  await page.route('**/api/v1/reads/project-import-candidate', async (route) => {
    readCalls.candidate += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        candidate_id: 'pm-import-candidate-miner-temp-power',
        candidate_version: 'pm_import_candidate_read_only_v1',
        review_status: 'draft_review_only',
        mutation_authority: 'not_admitted',
        project: {
          name: 'Miner Temp Power',
          location: 'Santa Teresa, NM',
          drawing_package: 'SLD: E01-00, E01-01',
          issue_date: 'Dated: 03/05/2026',
          source_format: 'flat_quote',
          source_sheet: 'Updated',
        },
        source_freshness: {
          strategy: 'path_size_mtime_fingerprint',
          mutation_authority: 'not_admitted',
          available_count: 2,
          missing_count: 0,
          aggregate_fingerprint: 'stat-fingerprint-abc123',
          review_action: 'Refresh this candidate if any source path, file size, or modified time changes before import approval is admitted.',
        },
        summary: {
          workpackage_count: 7,
          task_count: 15,
          apparatus_candidate_count: 186,
          crew_count: 15,
          equipment_inventory_count: 343,
          capability_count: 50,
          warning_count: 2,
          blocker_count: 0,
          human_decision_count: 2,
        },
        warnings: [
          {
            severity: 'warning',
            code: 'PROJECT_DATA_ENTRY_FORMULA_ERRORS',
            message: '234 planning-workbook rows include formula errors.',
          },
        ],
        human_decisions: [
          {
            decision_id: 'decision-approve-candidate-for-import-planning',
            severity: 'required_before_import',
            prompt: 'Does this candidate correctly represent the project, workpackages, tasks, and apparatus?',
            recommended_action: 'Approve only after blocker and warning review is complete.',
          },
        ],
        workpackages: [
          {
            workpackage_id: 'candidate-wp-001',
            title: '7.5',
            drawing_refs: ['E01-00'],
            planned_hours: 37.5,
            task_count: 2,
            apparatus_candidate_count: 15,
          },
        ],
        review_guidance: {
          primary_review_goal: 'Confirm exceptions before any future import mutation.',
          allowed_now: ['review_candidate', 'export_json', 'record_questions'],
          not_allowed_now: ['write_supabase', 'run_workbook_macros', 'assign_work', 'change_status', 'mutate_schedule'],
        },
      }),
    })
  })

  await page.route('**/api/v1/reads/project-import-admission-plan', async (route) => {
    readCalls.admissionPlan += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        admission_plan_id: 'pm-import-candidate-miner-temp-power-admission-plan',
        admission_plan_version: 'pm_import_admission_plan_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        readiness_status: 'needs_human_acceptance_before_import_packet',
        mutation_authority: 'not_admitted',
        target_row_plan: {
          project_rows: 1,
          workpackage_rows: 7,
          task_rows: 15,
          apparatus_rows: 186,
          approval_rows: 1,
          write_authority: 'not_admitted',
        },
        no_go_checks: [
          {
            check_id: 'warnings-reviewed-by-pm',
            status: 'needs_human_acceptance',
            message: '2 warning signal(s) must be reviewed.',
          },
          {
            check_id: 'mutation-path-not-admitted',
            status: 'no_go',
            message: 'This endpoint has no import mutation authority.',
          },
        ],
        future_import_sequence: ['PM reviews candidate warnings.', 'A later packet admits approval persistence.'],
        not_allowed_now: ['persist_approval_record', 'write_supabase', 'import_project_rows', 'assign_work', 'mutate_schedule'],
      }),
    })
  })

  await page.route('**/api/v1/reads/project-import-approval-contract', async (route) => {
    readCalls.approvalContract += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        approval_contract_id: 'pm-import-candidate-miner-temp-power-approval-persistence-contract',
        approval_contract_version: 'pm_import_approval_persistence_contract_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        readiness_status: 'needs_human_acceptance_before_import_packet',
        mutation_authority: 'not_admitted',
        persistence_authority: 'design_only_not_admitted',
        approval_record_contract: {
          record_type: 'pm_import_candidate_approval',
          required_fields: ['candidate_id', 'candidate_version', 'idempotency_key', 'decision', 'review_notes'],
          permitted_decisions: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
          operator_attestation: 'The PM must confirm the candidate shape before any future import mutation may be admitted.',
        },
        future_mutation_contract: {
          proposed_route: '/api/v1/mutations/project-import-approvals',
          current_authority: 'not_admitted',
        },
        not_allowed_now: ['persist_approval_record', 'write_supabase', 'import_project_rows', 'change_status'],
      }),
    })
  })

  await page.route('**/api/v1/reads/project-import-approval-storage-plan', async (route) => {
    readCalls.storagePlan += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        storage_plan_id: 'pm-import-candidate-miner-temp-power-approval-storage-plan',
        storage_plan_version: 'pm_import_approval_storage_plan_read_only_v1',
        candidate_id: 'pm-import-candidate-miner-temp-power',
        mutation_authority: 'not_admitted',
        persistence_authority: 'storage_decision_only_not_admitted',
        selected_storage_decision: 'dedicated_insert_only_import_candidate_approval_table',
        recommended_table: 'seam.pm_import_candidate_approvals',
        recommended_entity_type: 'pm_import_candidate_approval',
        recommended_route: '/api/v1/mutations/project-import-approvals',
        adapter_requirements: ['Use an explicit approval adapter.'],
        rejected_storage_options: [
          {
            option: 'audit_log_only',
            reason: 'Audit rows are evidence, not the canonical approval object.',
          },
        ],
        future_admission_sequence: ['Add a narrow schema migration for the dedicated approval table.'],
        not_allowed_now: [
          'persist_approval_record',
          'write_supabase',
          'create_schema',
          'run_schema_migration',
          'run_workbook_macros',
          'import_project_rows',
          'autonomous_ai_business_state_mutation',
        ],
      }),
    })
  })

  const response = await page.goto('/pm-review/import-intake', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Run Project Miner intake from one workbench/i })).toBeVisible()
  await expect(page.getByText(/Project Miner Intake Workbench/i).first()).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power/i).first()).toBeVisible()
  await expect(page.getByText('Santa Teresa, NM', { exact: true })).toBeVisible()
  await expect(page.getByText(/stat-fingerprint-abc123/i)).toBeVisible()
  await expect(page.getByText(/PROJECT_DATA_ENTRY_FORMULA_ERRORS/i)).toBeVisible()
  await expect(page.getByText(/needs human acceptance before import packet/i).first()).toBeVisible()
  await expect(page.getByText(/design_only_not_admitted/i).first()).toBeVisible()
  await expect(page.getByText(/storage_decision_only_not_admitted/i).first()).toBeVisible()
  await expect(page.getByText(/seam\.pm_import_candidate_approvals/i).first()).toBeVisible()
  await expect(page.getByText('/api/v1/mutations/project-import-approvals').first()).toBeVisible()
  await expect(page.getByText(/hosted parity/i).first()).toBeVisible()
  await expect(page.getByText(/approval persistence/i).first()).toBeVisible()
  await expect(page.getByText(/write supabase/i)).toBeVisible()
  await expect(page.getByText(/persist approval record/i)).toBeVisible()
  await expect(page.getByText(/run schema migration/i)).toBeVisible()
  await expect(page.getByText(/import project rows/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /Import candidate/i })).toHaveAttribute('href', '/pm-review/import-candidate')
  await expect(page.getByRole('link', { name: /Admission plan/i })).toHaveAttribute('href', '/pm-review/import-admission-plan')
  await expect(page.getByRole('link', { name: /Approval readiness/i })).toHaveAttribute('href', '/pm-review/import-approval-readiness')
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Persist/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Submit/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Import/i })).toHaveCount(0)

  expect(mutationRequests).toHaveLength(0)
  expect(readCalls).toEqual({
    candidate: 1,
    admissionPlan: 1,
    approvalContract: 1,
    storagePlan: 1,
  })
})
