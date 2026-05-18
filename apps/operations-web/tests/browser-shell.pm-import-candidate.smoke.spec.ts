import { expect, test } from '@playwright/test'

test('pm import candidate route renders exception-first read-only review packet', async ({ page }) => {
  let readCalls = 0
  const mutationRequests: Array<{ url: string; authorization?: string; body: any }> = []
  let taskPlanStatus: any = {
    classification: 'no_task_plan_record',
    route: '/api/v1/reads/project-import-task-plan-status',
    task_plan_route: '/api/v1/mutations/project-import-task-plans',
    task_plan_authority: 'admitted_by_pm_lane_361_task_plan_persistence',
    project_id: 'pm-task-plan-project-miner-temp-power',
    current_candidate_match: false,
    planning_context_only: true,
    persisted_row_counts: {
      projects: 0,
      workpackages: 0,
      tasks: 0,
      apparatus: 0,
    },
  }

  await page.route('**/api/v1/mutations/**', async (route) => {
    if (route.request().url().endsWith('/api/v1/mutations/project-import-task-plans')) {
      const body = route.request().postDataJSON()
      mutationRequests.push({
        url: route.request().url(),
        authorization: route.request().headers()['authorization'],
        body,
      })
      taskPlanStatus = {
        classification: 'task_plan_persisted',
        route: '/api/v1/reads/project-import-task-plan-status',
        task_plan_route: '/api/v1/mutations/project-import-task-plans',
        task_plan_authority: 'admitted_by_pm_lane_361_task_plan_persistence',
        project_id: 'pm-task-plan-project-miner-temp-power',
        persisted_at: '2026-05-18T23:30:00.000Z',
        current_candidate_match: true,
        planning_context_only: true,
        persisted_row_counts: {
          projects: 1,
          workpackages: 1,
          tasks: 2,
          apparatus: 2,
        },
        blocked_downstream: ['approval_record_creation', 'project_import', 'assignments', 'schedule_status_mutation'],
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'accepted',
          mutation_id: 'mut-task-plan-001',
          entity_id: 'pm-task-plan-project-miner-temp-power',
          entity_type: 'pm_import_task_plan',
          action_type: 'persist_project_import_task_plan',
          new_state: {
            project_id: 'pm-task-plan-project-miner-temp-power',
            row_counts: { projects: 1, workpackages: 1, tasks: 2, apparatus: 2 },
            blocked_downstream: ['approval_record_creation', 'project_import', 'assignments', 'schedule_status_mutation'],
          },
        }),
      })
      return
    }

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
        source_freshness: {
          strategy: 'path_size_mtime_fingerprint',
          mutation_authority: 'not_admitted',
          available_count: 1,
          missing_count: 1,
          aggregate_fingerprint: 'stat-fingerprint-abc123',
          review_action: 'Refresh this candidate if any source path, file size, or modified time changes before import approval is admitted.',
          source_files: [
            {
              source_id: 'estimator_workbook',
              label: 'Estimator workbook',
              path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/Estimator R3 - Project Miner Temp Power Testing.xlsm',
              found: true,
              size_bytes: 84512,
              modified_at: '2026-05-15T14:30:00Z',
              fingerprint: 'estimator-stat-fp',
              freshness_status: 'available',
            },
            {
              source_id: 'sld_pdf',
              label: 'SLD or drawing PDF',
              path: 'C:/Users/jjswe/Desktop/Project Miner PM Planning/Miner Temp SLD-AP-BCARRASCO.pdf',
              found: false,
              size_bytes: null,
              modified_at: null,
              fingerprint: null,
              freshness_status: 'missing',
            },
          ],
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

  await page.route('**/api/v1/reads/project-import-task-plan-status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(taskPlanStatus),
    })
  })

  const response = await page.goto('/pm-review/import-candidate', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Review exceptions before import exists/i })).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power/i)).toBeVisible()
  await expect(page.getByText(/not_admitted/i)).toBeVisible()
  await expect(page.getByText(/No Approval Preview JSON is currently staged in this browser/i)).toBeVisible()
  await expect(page.getByText(/Manual task shaping remains browser-local until you explicitly persist a durable task plan/i)).toBeVisible()
  await expect(page.getByText(/Persist the current manual task shaping as durable planning rows/i)).toBeVisible()
  await expect(page.getByText('Miner Temp Power', { exact: true })).toBeVisible()
  await expect(page.getByText(/Santa Teresa, NM/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Required Decisions/i })).toBeVisible()
  await expect(page.getByText(/Does this candidate correctly represent/i)).toBeVisible()
  await expect(page.getByText(/PROJECT_DATA_ENTRY_FORMULA_ERRORS/i).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: /Warning Review/i })).toBeVisible()
  const warningReview = page.getByLabel('Warning review')
  await expect(warningReview.locator('article', { hasText: /MISSING_DESIGNATIONS/i })).toHaveCount(1)
  await expect(page.getByRole('heading', { name: /Source Freshness/i })).toBeVisible()
  await expect(page.getByText(/stat-fingerprint-abc123/i)).toBeVisible()
  await expect(page.getByText(/Estimator workbook/i)).toBeVisible()
  await expect(page.getByText(/estimator-stat-fp/i)).toBeVisible()
  await expect(page.getByText(/SLD or drawing PDF/i)).toBeVisible()
  await expect(page.getByText(/missing/i).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: /Proposed Structure/i })).toBeVisible()
  await expect(page.getByText(/7.5 .* 2 tasks .* 15 apparatus .* 37.5 hours/i)).toBeVisible()

  await warningReview.getByRole('button', { name: 'warning' }).click()
  await expect(warningReview.locator('article', { hasText: /PROJECT_DATA_ENTRY_FORMULA_ERRORS/i })).toHaveCount(1)
  await expect(warningReview.locator('article', { hasText: /MISSING_DESIGNATIONS/i })).toHaveCount(0)
  await warningReview.getByLabel('Warning code filter').selectOption('MISSING_DESIGNATIONS')
  await expect(warningReview.getByText(/No warnings match the active filter/i)).toBeVisible()
  await warningReview.getByRole('button', { name: 'all' }).click()
  await expect(warningReview.locator('article', { hasText: /MISSING_DESIGNATIONS/i })).toHaveCount(1)

  const taskShaping = page.getByLabel('Manual task shaping')
  await expect(taskShaping.getByRole('heading', { name: /Manual Task Shaping/i })).toBeVisible()
  await expect(taskShaping.getByText(/PM or Operations manager can regroup apparatus candidates/i)).toBeVisible()
  await taskShaping.getByRole('button', { name: 'Add local task group' }).click()
  await taskShaping.locator('details').first().locator('summary').click()
  const manualTaskGroup = taskShaping.locator('details').nth(1)
  await expect(manualTaskGroup).toBeVisible()
  await manualTaskGroup.locator('summary').click()
  await manualTaskGroup.getByLabel('Local task title').fill('Breaker lineup split')
  await manualTaskGroup.getByLabel('Local task designation').fill('PD-1B')

  const apparatusCard = taskShaping.locator('article', { hasText: /PD-1 02/i })
  const regroupedTaskValue = await apparatusCard.getByLabel('Local task group').locator('option').nth(1).getAttribute('value')
  expect(regroupedTaskValue).toBeTruthy()
  await apparatusCard.getByLabel('Local task group').selectOption(regroupedTaskValue || undefined)
  await apparatusCard.getByLabel('Apparatus designation').fill('PD-1B')
  await expect(taskShaping.getByText(/1 apparatus candidates have been moved away from the proposed source task/i)).toBeVisible()
  await expect(taskShaping.getByText(/1 local naming or designation overrides are staged/i)).toBeVisible()

  await page.getByLabel('PM review notes draft').fill('Check PD-1 duplicate rows before future import approval.')
  await expect(page.getByText(/56 characters retained in this browser/i)).toBeVisible()

  await taskShaping.getByRole('button', { name: 'Persist durable task plan' }).click()
  await expect(page.getByText(/Durable PM task plan persisted for this candidate as planning-only rows/i)).toBeVisible()
  await expect(page.getByText(/The current candidate already has a persisted PM task plan/i)).toBeVisible()
  await expect(page.getByText('2 tasks · 2 apparatus')).toBeVisible()
  await expect(page.getByText(/Last persisted at 2026-05-18T23:30:00.000Z/i)).toBeVisible()

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export JSON' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-review.json')
  await expect(page.getByText(/prepared from the current read-only candidate/i)).toBeVisible()

  const approvalPreviewDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Approval Preview JSON' }).click()
  const approvalPreviewDownload = await approvalPreviewDownloadPromise
  expect(approvalPreviewDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-preview.json')
  await expect(page.getByText(/staged for Approval readiness/i)).toBeVisible()
  const approvalPreviewStored = await page.evaluate(() => window.localStorage.getItem('pm-import-candidate-approval-preview:pm-import-candidate-miner-temp-power'))
  expect(approvalPreviewStored).toBeTruthy()
  expect(approvalPreviewStored).toContain('Breaker lineup split')
  expect(approvalPreviewStored).toContain('Check PD-1 duplicate rows before future import approval.')
  await expect(page.getByText(/Approval Preview JSON is already staged in this browser .* matches the current browser-local review context/i)).toBeVisible()
  await expect(page.getByText(/current with the latest browser-local review context/i)).toBeVisible()

  await page.getByLabel('PM review notes draft').fill('Check PD-1 duplicate rows before future import approval and re-export before approval readiness.')
  await expect(
    page.getByText(/Approval Preview JSON is staged in this browser, but the current browser-local review context is newer/i),
  ).toBeVisible()
  await expect(page.getByText(/stale relative to the latest browser-local review context/i)).toBeVisible()

  const proposedStructure = page.getByLabel('Proposed project structure')
  await proposedStructure.getByText(/7.5 .* 2 tasks .* 15 apparatus .* 37.5 hours/i).click()
  await expect(proposedStructure.getByText(/PD-1 - Switch MV - Fused Disconnect/i).first()).toBeVisible()
  await expect(page.getByText(/Source Updated row 6 .* line miner-line-001/i)).toBeVisible()
  await expect(page.getByText(/15 people in the current capability context/i)).toBeVisible()
  await expect(page.getByText(/343 inventory rows/i)).toBeVisible()
  await expect(page.getByText(/50 capability rows/i)).toBeVisible()
  await expect(page.getByText(/write supabase/i)).toBeVisible()
  await expect(page.getByText(/run workbook macros/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Import/i })).toHaveCount(0)

  await page.reload({ waitUntil: 'networkidle' })
  await expect(page.getByLabel('PM review notes draft')).toHaveValue(
    'Check PD-1 duplicate rows before future import approval and re-export before approval readiness.',
  )
  await expect(page.getByText(/Approval Preview JSON is staged in this browser, but the current browser-local review context is newer/i)).toBeVisible()
  const reloadedTaskShaping = page.getByLabel('Manual task shaping')
  const reloadedManualTaskGroup = reloadedTaskShaping.locator('details').nth(1)
  await expect(reloadedManualTaskGroup).toBeVisible()
  await reloadedManualTaskGroup.locator('summary').click()
  await expect(reloadedManualTaskGroup.getByLabel('Local task title')).toHaveValue('Breaker lineup split')
  await expect(reloadedManualTaskGroup.getByLabel('Local task designation')).toHaveValue('PD-1B')
  await reloadedTaskShaping.locator('details').first().locator('summary').click()
  const reloadedApparatusCard = reloadedTaskShaping.locator('article', { hasText: /PD-1 02/i })
  await expect(reloadedApparatusCard.getByLabel('Local task group')).toHaveValue(regroupedTaskValue || '')
  await expect(reloadedApparatusCard.getByLabel('Apparatus designation')).toHaveValue('PD-1B')
  await expect(page.getByText(/The current candidate already has a persisted PM task plan/i)).toBeVisible()
  expect(mutationRequests).toHaveLength(1)
  const mutation = mutationRequests[0]
  const tokenPayload = JSON.parse(Buffer.from((mutation.authorization || '').replace(/^Bearer /, ''), 'base64').toString('utf8'))
  expect(tokenPayload.actor_role).toBe('pm')
  expect(mutation.body.action_type).toBe('persist_project_import_task_plan')
  expect(mutation.body.payload.review_notes).toBe('Check PD-1 duplicate rows before future import approval.')
  expect(mutation.body.payload.manual_task_shaping.groups).toHaveLength(2)
  expect(mutation.body.payload.manual_task_shaping.apparatus).toHaveLength(2)
  expect(readCalls).toBe(2)
})
