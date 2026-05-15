import { expect, test } from '@playwright/test'

test('pm import candidate route renders exception-first read-only review packet', async ({ page }) => {
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

  await page.route('**/api/v1/reads/project-import-candidate', async (route) => {
    readCalls += 1
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
        source_bundle: {
          estimator_workbook_path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/Estimator R3 - Project Miner Temp Power Testing.xlsm',
          estimator_workbook_found: true,
          sld_pdf_path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/Miner Temp SLD-AP-BCARRASCO.pdf',
          sld_pdf_found: true,
          capability_workbook_found: true,
          project_data_entry: {
            path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm',
            formula_error_row_count: 234,
          },
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
        human_decisions: [
          {
            decision_id: 'decision-approve-candidate-for-import-planning',
            severity: 'required_before_import',
            prompt: 'Does this candidate correctly represent the project, workpackages, tasks, and apparatus that should be staged for import?',
            recommended_action: 'Approve only after blocker and warning review is complete.',
          },
          {
            decision_id: 'decision-warning-001',
            severity: 'warning',
            warning_code: 'PROJECT_DATA_ENTRY_FORMULA_ERRORS',
            prompt: '234 planning-workbook rows include formula errors across 3510 cells.',
            recommended_action: 'Treat the tracker as lineage evidence only until formula errors are understood.',
          },
        ],
        warnings: [
          {
            severity: 'info',
            code: 'MISSING_DESIGNATIONS',
            message: '1 estimator line items do not have explicit designations.',
            review_action: 'Review task naming and apparatus naming before approving the candidate.',
          },
          {
            severity: 'warning',
            code: 'PROJECT_DATA_ENTRY_FORMULA_ERRORS',
            message: '234 planning-workbook row(s) include formula errors across 3510 cell(s).',
            review_action: 'Treat the tracker as lineage evidence only until formula errors are understood.',
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
            tasks: [
              {
                task_id: 'candidate-task-0001',
                title: 'PD-1 - Switch MV - Fused Disconnect',
                apparatus_type: 'Switch MV - Fused Disconnect',
                designation: 'PD-1',
                quantity: 2,
                drawing_ref: 'E01-00',
                planned_hours: 5,
                source_ref: {
                  estimator_workbook_path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/Estimator R3 - Project Miner Temp Power Testing.xlsm',
                  source_format: 'flat_quote',
                  source_sheet: 'Updated',
                  source_row: 6,
                  line_id: 'miner-line-001',
                  drawing_ref: 'E01-00',
                },
                apparatus_candidates: [
                  {
                    candidate_id: 'miner-app-0001',
                    display_name: 'PD-1 01',
                    source_row: 6,
                    source_line_id: 'miner-line-001',
                  },
                  {
                    candidate_id: 'miner-app-0002',
                    display_name: 'PD-1 02',
                    source_row: 6,
                    source_line_id: 'miner-line-001',
                  },
                ],
              },
            ],
          },
        ],
        review_guidance: {
          primary_review_goal: 'Confirm exceptions, traceability gaps, duplicate-looking rows, and candidate grouping before any future import mutation.',
          allowed_now: ['review_candidate', 'export_json', 'record_questions'],
          not_allowed_now: ['write_supabase', 'run_workbook_macros', 'auto_assign_work', 'change_status', 'mutate_schedule'],
        },
      }),
    })
  })

  const response = await page.goto('/pm-review/import-candidate', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Review exceptions before import exists/i })).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power/i)).toBeVisible()
  await expect(page.getByText(/not_admitted/i)).toBeVisible()
  await expect(page.getByText('Miner Temp Power', { exact: true })).toBeVisible()
  await expect(page.getByText(/Santa Teresa, NM/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Required Decisions/i })).toBeVisible()
  await expect(page.getByText(/Does this candidate correctly represent/i)).toBeVisible()
  await expect(page.getByText(/PROJECT_DATA_ENTRY_FORMULA_ERRORS/i).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: /Warning Review/i })).toBeVisible()
  await expect(page.getByText(/MISSING_DESIGNATIONS/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Proposed Structure/i })).toBeVisible()
  await expect(page.getByText(/7.5 .* 2 tasks .* 15 apparatus .* 37.5 hours/i)).toBeVisible()

  await page.getByText(/7.5 .* 2 tasks .* 15 apparatus .* 37.5 hours/i).click()
  await expect(page.getByText(/PD-1 - Switch MV - Fused Disconnect/i)).toBeVisible()
  await expect(page.getByText(/Source Updated row 6 .* line miner-line-001/i)).toBeVisible()
  await expect(page.getByText(/15 people in the current capability context/i)).toBeVisible()
  await expect(page.getByText(/343 inventory rows/i)).toBeVisible()
  await expect(page.getByText(/50 capability rows/i)).toBeVisible()
  await expect(page.getByText(/write supabase/i)).toBeVisible()
  await expect(page.getByText(/run workbook macros/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Import/i })).toHaveCount(0)
  expect(mutationRequests).toHaveLength(0)
  expect(readCalls).toBe(1)
})
