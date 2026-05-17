import { expect, type Page, test } from '@playwright/test'

test.setTimeout(70000)

const guardedPhrase = (...parts: string[]) => new RegExp(parts.join('[\\s/-]+'), 'i')

const impliedAuthorityControlNames = [
  /^Approve$/i,
  /^Persist$/i,
  /^Submit$/i,
  /^Assign$/i,
  /^Schedule$/i,
  /^Import$/i,
  /change status/i,
  /create task/i,
  /create issue/i,
  guardedPhrase('field', 'release'),
  guardedPhrase('ready', 'for', 'field'),
  guardedPhrase('field', 'ready'),
  guardedPhrase('work', 'order'),
  guardedPhrase('hosted', 'parity', 'proven'),
  guardedPhrase('production', 'ready'),
]

const unsafeAuthorityTextPhrases = [
  guardedPhrase('hosted', 'parity', 'proven'),
  guardedPhrase('packet', 'admitted'),
  guardedPhrase('ready', 'for', 'execution'),
  guardedPhrase('ready', 'for', 'field'),
  guardedPhrase('field', 'ready'),
  guardedPhrase('field', 'log', 'of', 'record'),
  guardedPhrase('go', 'no', 'go', 'passed'),
  guardedPhrase('production', 'ready'),
]

async function expectNoImpliedAuthorityControls(page: Page) {
  for (const name of impliedAuthorityControlNames) {
    await expect(page.getByRole('button', { name })).toHaveCount(0)
    await expect(page.getByRole('link', { name })).toHaveCount(0)
  }
}

test('pm import intake workbench renders consolidated read-only Project Miner gates', async ({ page }) => {
  const readCalls = {
    candidate: 0,
    admissionPlan: 0,
    approvalContract: 0,
    storagePlan: 0,
    approvalStatus: 0,
  }
  const mutationRequests: string[] = []

  await page.route('**/api/v1/**', async (route) => {
    throw new Error(`Unexpected unmocked API request: ${route.request().url()}`)
  })

  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'mutation route should not be called' }),
    })
  })

  await page.route('**/api/v1/reads/project-import-candidate', async (route) => {
    expect(route.request().method()).toBe('GET')
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
    expect(route.request().method()).toBe('GET')
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
    expect(route.request().method()).toBe('GET')
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
    expect(route.request().method()).toBe('GET')
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

  await page.route('**/api/v1/reads/project-import-approval-status', async (route) => {
    expect(route.request().method()).toBe('GET')
    readCalls.approvalStatus += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        classification: 'no_approval_record',
        current_candidate_match: false,
        candidate_id: 'pm-import-candidate-miner-temp-power',
        candidate_version: 'pm_import_candidate_read_only_v1',
        source: 'seam.pm_import_candidate_approvals',
        route: '/api/v1/reads/project-import-approval-status',
        approval_storage_available: true,
        approval_record_count_for_candidate: 0,
        audit_log_used_for_current_status: false,
        import_authority: 'not_admitted',
      }),
    })
  })

  const response = await page.goto('/pm-review/import-intake', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Run Project Miner intake from one workbench/i })).toBeVisible()
  await expect(page.getByText(/Project Miner Intake Workbench/i).first()).toBeVisible()
  await expect(page.getByText(/pm-import-candidate-miner-temp-power/i).first()).toBeVisible()
  await expect(page.getByText('Santa Teresa, NM', { exact: true })).toBeVisible()
  await expect(page.getByText(/stat-fingerprint-abc123/i).first()).toBeVisible()
  await expect(page.getByText(/PROJECT_DATA_ENTRY_FORMULA_ERRORS/i).first()).toBeVisible()
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
  await expect(page.getByText('import project rows', { exact: true })).toBeVisible()
  const routeLinks = page.getByLabel('PM intake route links')
  const routeLinkDisclosure = page.locator('details[aria-label="PM intake route links"]')
  await expect(routeLinkDisclosure).toHaveAttribute('open', '')
  await expect(routeLinks.getByRole('heading', { name: 'Route Links', exact: true })).toBeVisible()
  await expect(routeLinks.getByLabel('PM intake route link groups')).toBeVisible()
  await expect(routeLinks.getByLabel('Shell route links').getByRole('heading', { name: 'Shell', exact: true })).toBeVisible()
  await expect(routeLinks.getByLabel('Shell route links').getByRole('link')).toHaveCount(1)
  await expect(routeLinks.getByLabel('Intake Reads route links').getByRole('heading', { name: 'Intake Reads', exact: true })).toBeVisible()
  await expect(routeLinks.getByLabel('Intake Reads route links').getByRole('link')).toHaveCount(3)
  await expect(routeLinks.getByLabel('PM Workfront route links').getByRole('heading', { name: 'PM Workfront', exact: true })).toBeVisible()
  await expect(routeLinks.getByLabel('PM Workfront route links').getByRole('link')).toHaveCount(1)
  await routeLinkDisclosure.locator(':scope > summary').click()
  await expect(routeLinkDisclosure).not.toHaveAttribute('open', '')
  await expect(routeLinks.getByLabel('PM intake route link groups')).toBeHidden()
  const routeLinkDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|route-link/i.test(key)))
  expect(routeLinkDisclosureStateKeys).toEqual([])
  await routeLinkDisclosure.locator(':scope > summary').click()
  await expect(routeLinkDisclosure).toHaveAttribute('open', '')
  await expect(routeLinks.getByLabel('PM intake route link groups')).toBeVisible()
  await expect(routeLinks.getByLabel('Shell route links').getByRole('link')).toHaveCount(1)
  await expect(routeLinks.getByLabel('Intake Reads route links').getByRole('link')).toHaveCount(3)
  await expect(routeLinks.getByLabel('PM Workfront route links').getByRole('link')).toHaveCount(1)
  await expect(routeLinks.getByRole('link', { name: 'Return to shell', exact: true })).toHaveAttribute('href', '/')
  await expect(routeLinks.getByRole('link', { name: 'Import candidate', exact: true })).toHaveAttribute('href', '/pm-review/import-candidate')
  await expect(routeLinks.getByRole('link', { name: 'Admission plan', exact: true })).toHaveAttribute('href', '/pm-review/import-admission-plan')
  await expect(routeLinks.getByRole('link', { name: 'Approval readiness', exact: true })).toHaveAttribute('href', '/pm-review/import-approval-readiness')
  await expect(routeLinks.getByRole('link', { name: 'PM workfront', exact: true })).toHaveAttribute('href', '/pm-review/workfront')
  for (const target of ['/', '/pm-review/import-candidate', '/pm-review/import-admission-plan', '/pm-review/import-approval-readiness', '/pm-review/workfront']) {
    await expect(routeLinks.locator(`a[href="${target}"]`)).toHaveCount(1)
  }
  const outputActionRail = page.getByLabel('PM intake output action rail')
  const outputActionDisclosure = page.locator('details[aria-label="PM intake output action rail"]')
  await expect(outputActionDisclosure).toHaveAttribute('open', '')
  await expect(outputActionRail.getByRole('heading', { name: 'Output Actions', exact: true })).toBeVisible()
  await expect(outputActionRail.getByRole('heading', { name: 'Review Outputs', exact: true })).toBeVisible()
  await expect(outputActionRail.getByRole('heading', { name: 'Executor Output', exact: true })).toBeVisible()
  await expect(outputActionRail.getByRole('heading', { name: 'Field Prep Outputs', exact: true })).toBeVisible()
  await expect(outputActionRail.getByRole('heading', { name: 'Refresh', exact: true })).toBeVisible()
  await expect(outputActionRail.getByLabel('PM intake output action groups')).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output subgroups')).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('heading', { name: 'Field Prep Basics' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('heading', { name: 'Admission Drafts' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('heading', { name: 'Pilot Launch Outputs' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button')).toHaveCount(4)
  await expect(outputActionRail.getByLabel('Executor output actions').getByRole('button')).toHaveCount(1)
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button')).toHaveCount(19)
  await expect(outputActionRail.getByLabel('Field prep basics output actions').getByRole('button')).toHaveCount(6)
  await expect(outputActionRail.getByLabel('Admission draft output actions').getByRole('button')).toHaveCount(8)
  await expect(outputActionRail.getByLabel('Pilot launch output actions').getByRole('button')).toHaveCount(5)
  await expect(outputActionRail.getByLabel('Field prep basics output actions').getByRole('button')).toHaveText([
    'Export Field Kickoff Brief',
    'Export Field Observation Notes',
    'Export Field Prep Coverage Snapshot',
    'Export Field Prep Conversation Agenda',
    'Export Field Prep Packet',
    'Export Field Start Preflight',
  ])
  await expect(outputActionRail.getByLabel('Admission draft output actions').getByRole('button')).toHaveText([
    'Export Field Execution Gate Design',
    'Export Lead Field Assignment Draft',
    'Export Field Authorization Assignment Draft',
    'Export Schedule Status Controls Draft',
    'Export Durable Field Record Draft',
    'Export Production Tracking Draft',
    'Export Customer Reporting Draft',
    'Export Financial Handoff Draft',
  ])
  await expect(outputActionRail.getByLabel('Pilot launch output actions').getByRole('button')).toHaveText([
    'Export Pilot Launch Binder',
    'Export Pilot Launch Daily Brief',
    'Export Pilot Launch Standup Card',
    'Export Pilot Launch Capture Sheet',
    'Export Pilot Launch Follow-Up Packet',
  ])
  await expect(outputActionRail.getByLabel('Refresh action').getByRole('button')).toHaveCount(1)
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button', { name: 'Export PM Brief' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button', { name: 'Export Approval Preview JSON' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button', { name: 'Export PM Intake Snapshot' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button', { name: 'Export Import Exception Register' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Executor output actions').getByRole('button', { name: 'Export Executor Handoff' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Kickoff Brief' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Observation Notes' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Prep Coverage Snapshot' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Prep Conversation Agenda' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Prep Packet' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Start Preflight' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Execution Gate Design' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Lead Field Assignment Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Field Authorization Assignment Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Schedule Status Controls Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Durable Field Record Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Production Tracking Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Customer Reporting Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Financial Handoff Draft' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Pilot Launch Binder' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Pilot Launch Daily Brief' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Pilot Launch Standup Card' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Pilot Launch Capture Sheet' })).toBeVisible()
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button', { name: 'Export Pilot Launch Follow-Up Packet' })).toBeVisible()
  await outputActionDisclosure.locator(':scope > summary').click()
  await expect(outputActionDisclosure).not.toHaveAttribute('open', '')
  await expect(outputActionRail.getByLabel('PM intake output action groups')).toBeHidden()
  const outputDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|output-action/i.test(key)))
  expect(outputDisclosureStateKeys).toEqual([])
  await outputActionDisclosure.locator(':scope > summary').click()
  await expect(outputActionDisclosure).toHaveAttribute('open', '')
  await expect(outputActionRail.getByLabel('PM intake output action groups')).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button')).toHaveCount(4)
  await expect(outputActionRail.getByLabel('Executor output actions').getByRole('button')).toHaveCount(1)
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button')).toHaveCount(19)
  await expect(outputActionRail.getByLabel('Field prep basics output actions').getByRole('button')).toHaveCount(6)
  await expect(outputActionRail.getByLabel('Admission draft output actions').getByRole('button')).toHaveCount(8)
  await expect(outputActionRail.getByLabel('Pilot launch output actions').getByRole('button')).toHaveCount(5)
  await expect(outputActionRail.getByLabel('Refresh action').getByRole('button')).toHaveCount(1)
  await expect(page.getByLabel('PM intake output status rail')).toHaveCount(0)
  await expectNoImpliedAuthorityControls(page)
  const helperPanelStack = page.getByLabel('PM intake helper panel stack')
  const intakeTriagePanels = helperPanelStack.getByLabel('Intake triage helper panels')
  await expect(intakeTriagePanels.getByRole('heading', { name: 'Intake Triage Panels', exact: true })).toBeVisible()
  await expect(intakeTriagePanels.locator('details#pm-command-center[aria-label="Local PM intake command center"]')).toHaveCount(1)
  await expect(intakeTriagePanels.locator('details#pm-meeting-readout[aria-label="Local PM intake meeting readout"]')).toHaveCount(1)
  await expect(intakeTriagePanels.locator('details#pm-constraint-radar[aria-label="Local PM intake constraint radar"]')).toHaveCount(1)
  const dailyActionPanels = helperPanelStack.getByLabel('Daily action helper panels')
  await expect(dailyActionPanels.getByRole('heading', { name: 'Daily Action Panels', exact: true })).toBeVisible()
  await expect(dailyActionPanels.locator('details#pm-daily-review-script[aria-label="Local PM intake daily review script"]')).toHaveCount(1)
  await expect(dailyActionPanels.locator('details#pm-start-here[aria-label="Local PM intake start here"]')).toHaveCount(1)
  await expect(dailyActionPanels.locator('details#pm-output-selector[aria-label="Local PM intake output selector"]')).toHaveCount(1)
  await expect(dailyActionPanels.locator('#pm-handoff-guide')).toHaveCount(1)
  const workflowReviewPanels = helperPanelStack.getByLabel('Workflow review helper panels')
  await expect(workflowReviewPanels.getByRole('heading', { name: 'Workflow Review Panels', exact: true })).toBeVisible()
  await expect(workflowReviewPanels.locator('#pm-workflow-map')).toHaveCount(1)
  await expect(workflowReviewPanels.locator('#pm-open-items')).toHaveCount(1)
  for (const label of [
    'Intake triage helper panels',
    'Daily action helper panels',
    'Workflow review helper panels',
  ]) {
    await expect(page.locator(`details[aria-label="${label}"]`)).toHaveAttribute('open', '')
  }
  const intakeTriageDisclosure = page.locator('details[aria-label="Intake triage helper panels"]')
  await intakeTriageDisclosure.locator(':scope > summary').click()
  await expect(intakeTriageDisclosure).not.toHaveAttribute('open', '')
  await expect(intakeTriagePanels.locator('#pm-command-center')).toBeHidden()
  const helperCollapseStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure/i.test(key)))
  expect(helperCollapseStateKeys).toEqual([])
  await intakeTriageDisclosure.locator(':scope > summary').click()
  await expect(intakeTriageDisclosure).toHaveAttribute('open', '')
  await expect(intakeTriagePanels.locator('#pm-command-center')).toBeVisible()
  const detailWorkbench = page.getByLabel('PM intake detail workbench')
  const reviewSnapshotDetail = detailWorkbench.getByLabel('Review snapshot detail panels')
  await expect(reviewSnapshotDetail.getByRole('heading', { name: 'Review Snapshot Detail', exact: true })).toBeVisible()
  await expect(reviewSnapshotDetail.locator('#pm-intake-snapshot')).toHaveCount(1)
  await expect(reviewSnapshotDetail.locator('#pm-operating-queue')).toHaveCount(1)
  const sourceExceptionDetail = detailWorkbench.getByLabel('Source and exception detail panels')
  await expect(sourceExceptionDetail.getByRole('heading', { name: 'Source and Exception Detail', exact: true })).toBeVisible()
  await expect(sourceExceptionDetail.locator('#project-packet')).toHaveCount(1)
  await expect(sourceExceptionDetail.locator('#import-exception-register')).toHaveCount(1)
  await expect(sourceExceptionDetail.locator('#workflow-gates')).toHaveCount(1)
  await expect(sourceExceptionDetail.locator('details[aria-label="Exception review and PM decision detail"]')).toHaveCount(1)
  const approvalPrepDetail = detailWorkbench.getByLabel('Approval prep detail panels')
  await expect(approvalPrepDetail.getByRole('heading', { name: 'Approval Prep Detail', exact: true })).toBeVisible()
  await expect(approvalPrepDetail.locator('details[aria-label="Admission and approval contract"]')).toHaveCount(1)
  await expect(approvalPrepDetail.locator('details[aria-label="Local review checklist"]')).toHaveCount(1)
  await expect(approvalPrepDetail.locator('details[aria-label="Local approval decision draft"]')).toHaveCount(1)
  await expect(approvalPrepDetail.locator('details[aria-label="Local approval submission dry run"]')).toHaveCount(1)
  const executorCloseoutDetail = detailWorkbench.getByLabel('Executor closeout detail panels')
  await expect(executorCloseoutDetail.getByRole('heading', { name: 'Executor Closeout Detail', exact: true })).toBeVisible()
  await expect(executorCloseoutDetail.locator('details#executor-closeout[aria-label="Local executor closeout intake"]')).toHaveCount(1)
  const fieldPrepDetail = detailWorkbench.getByLabel('Field prep detail panels')
  await expect(fieldPrepDetail.getByRole('heading', { name: 'Field Prep Detail', exact: true })).toBeVisible()
  await expect(fieldPrepDetail.locator('details[aria-label="Local field readiness checklist"]')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('details[aria-label="Local field questions draft"]')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('details#field-prep[aria-label="Local field prep queue"]')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('details[aria-label="Local field prep coverage snapshot"]')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('details[aria-label="Local field prep conversation agenda"]')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('details[aria-label="Local field observation scratchpad"]')).toHaveCount(1)
  const authorityBoundaryDetail = detailWorkbench.getByLabel('Authority boundary detail panels')
  await expect(authorityBoundaryDetail.getByRole('heading', { name: 'Authority Boundary Detail', exact: true })).toBeVisible()
  await expect(authorityBoundaryDetail.locator('details#approval-readiness[aria-label="Approval persistence readiness gates"]')).toHaveCount(1)
  await expect(authorityBoundaryDetail.locator('details#guardrails[aria-label="Current PM next actions and guardrails"]')).toHaveCount(1)
  for (const label of [
    'Review snapshot detail panels',
    'Source and exception detail panels',
    'Approval prep detail panels',
    'Executor closeout detail panels',
    'Field prep detail panels',
    'Authority boundary detail panels',
  ]) {
    await expect(page.locator(`details[aria-label="${label}"]`)).toHaveAttribute('open', '')
  }
  const reviewSnapshotDisclosure = page.locator('details[aria-label="Review snapshot detail panels"]')
  await reviewSnapshotDisclosure.locator(':scope > summary').click()
  await expect(reviewSnapshotDisclosure).not.toHaveAttribute('open', '')
  await expect(reviewSnapshotDetail.locator('#pm-intake-snapshot')).toBeHidden()
  const collapseStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|detail|disclosure/i.test(key)))
  expect(collapseStateKeys).toEqual([])
  await reviewSnapshotDisclosure.locator(':scope > summary').click()
  await expect(reviewSnapshotDisclosure).toHaveAttribute('open', '')
  await expect(reviewSnapshotDetail.locator('#pm-intake-snapshot')).toBeVisible()
  const pmIntakeSnapshotDisclosure = reviewSnapshotDetail.locator('details#pm-intake-snapshot[aria-label="Local PM intake snapshot"]')
  await expect(pmIntakeSnapshotDisclosure).toHaveAttribute('open', '')
  const pmIntakeSnapshotControls = pmIntakeSnapshotDisclosure.getByLabel('PM intake snapshot controls')
  await expect(pmIntakeSnapshotControls).toBeVisible()
  const pmIntakeSnapshotGroupsEarly = pmIntakeSnapshotDisclosure.getByLabel('Local PM intake snapshot groups')
  await expect(pmIntakeSnapshotGroupsEarly).toBeVisible()
  const reviewPostureSnapshotGroupEarly = pmIntakeSnapshotDisclosure.getByLabel('Review Posture snapshot group')
  const fieldReadinessPostureSnapshotGroupEarly = pmIntakeSnapshotDisclosure.getByLabel('Field Readiness Posture snapshot group')
  const authorityBoundaryPostureSnapshotGroupEarly = pmIntakeSnapshotDisclosure.getByLabel('Authority Boundary Posture snapshot group')
  await expect(reviewPostureSnapshotGroupEarly.getByLabel('Review Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(fieldReadinessPostureSnapshotGroupEarly.getByLabel('Field Readiness Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(authorityBoundaryPostureSnapshotGroupEarly.getByLabel('Authority Boundary Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(pmIntakeSnapshotGroupsEarly.locator('article')).toHaveCount(6)
  await pmIntakeSnapshotDisclosure.locator(':scope > summary').click()
  await expect(pmIntakeSnapshotDisclosure).not.toHaveAttribute('open', '')
  await expect(pmIntakeSnapshotControls).toBeHidden()
  await expect(pmIntakeSnapshotGroupsEarly).toBeHidden()
  const snapshotDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|snapshot/i.test(key)))
  expect(snapshotDisclosureStateKeys).toEqual([])
  await pmIntakeSnapshotDisclosure.locator(':scope > summary').click()
  await expect(pmIntakeSnapshotDisclosure).toHaveAttribute('open', '')
  await expect(pmIntakeSnapshotControls).toBeVisible()
  await expect(pmIntakeSnapshotGroupsEarly).toBeVisible()
  await expect(reviewPostureSnapshotGroupEarly.getByLabel('Review Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(fieldReadinessPostureSnapshotGroupEarly.getByLabel('Field Readiness Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(authorityBoundaryPostureSnapshotGroupEarly.getByLabel('Authority Boundary Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(pmIntakeSnapshotGroupsEarly.locator('article')).toHaveCount(6)
  for (const heading of [
    'Review Snapshot Detail',
    'Source and Exception Detail',
    'Approval Prep Detail',
    'Executor Closeout Detail',
    'Field Prep Detail',
    'Authority Boundary Detail',
  ]) {
    await expect(detailWorkbench.getByRole('heading', { name: heading, exact: true })).toBeVisible()
  }
  const unsafeAuthorityTextMatches = await page.locator('main').evaluate((main, patterns) => {
    const text = (main as HTMLElement).innerText
    return patterns.filter((pattern) => new RegExp(pattern, 'i').test(text))
  }, unsafeAuthorityTextPhrases.map((pattern) => pattern.source))
  expect(unsafeAuthorityTextMatches).toEqual([])
  const commandCenter = page.locator('details#pm-command-center[aria-label="Local PM intake command center"]')
  await expect(commandCenter).toHaveAttribute('open', '')
  await expect(commandCenter.getByRole('heading', { name: /Local PM Intake Command Center/i })).toBeVisible()
  const commandCenterControls = commandCenter.locator(':scope > div').first()
  await expect(commandCenterControls).toBeVisible()
  await expect(commandCenterControls.locator('a')).toHaveCount(4)
  await expect(commandCenter.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(commandCenter.getByText(/Compact top-of-page scan for the current local PM move/i)).toBeVisible()
  await expect(commandCenter.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state/i)).toBeVisible()
  await expect(commandCenter.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write/i)).toBeVisible()
  await commandCenter.locator(':scope > summary').click()
  await expect(commandCenter).not.toHaveAttribute('open', '')
  await expect(commandCenterControls).toBeHidden()
  const commandCenterDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|command-center/i.test(key)))
  expect(commandCenterDisclosureStateKeys).toEqual([])
  await commandCenter.locator(':scope > summary').click()
  await expect(commandCenter).toHaveAttribute('open', '')
  await expect(commandCenterControls).toBeVisible()
  await expect(commandCenter.locator('a').filter({ hasText: /^Do now/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(commandCenter.locator('a').filter({ hasText: /^Ask next/ })).toHaveAttribute('href', '#field-prep')
  await expect(commandCenter.locator('a').filter({ hasText: /^Prepare handoff context/ })).toHaveAttribute('href', '#pm-output-selector')
  await expect(commandCenter.locator('a').filter({ hasText: /^Still blocked/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(commandCenter.getByText(/Miner Temp Power: start with source and exception review. Source fingerprint stat-fingerprint-abc123; review checklist has 0 of 7 local checks marked and exceptions are 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(commandCenter.getByText(/Field prep queue is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(commandCenter.getByText(/Use the output selector after local decision notes, field questions, observation notes, or executor closeout evidence exist/i)).toBeVisible()
  await expect(commandCenter.getByText(/4 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const meetingReadout = page.locator('details#pm-meeting-readout[aria-label="Local PM intake meeting readout"]')
  await expect(meetingReadout).toHaveAttribute('open', '')
  await expect(meetingReadout.getByRole('heading', { name: /Local PM Intake Meeting Readout/i })).toBeVisible()
  const meetingReadoutControls = meetingReadout.locator(':scope > div').first()
  await expect(meetingReadoutControls).toBeVisible()
  await expect(meetingReadoutControls.locator('a')).toHaveCount(4)
  await expect(meetingReadout.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(meetingReadout.getByText(/Conversation-ready local summary for PM, lead, customer, or field review/i)).toBeVisible()
  await expect(meetingReadout.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state/i)).toBeVisible()
  await expect(meetingReadout.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write/i)).toBeVisible()
  await meetingReadout.locator(':scope > summary').click()
  await expect(meetingReadout).not.toHaveAttribute('open', '')
  await expect(meetingReadoutControls).toBeHidden()
  const meetingReadoutDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|meeting-readout/i.test(key)))
  expect(meetingReadoutDisclosureStateKeys).toEqual([])
  await meetingReadout.locator(':scope > summary').click()
  await expect(meetingReadout).toHaveAttribute('open', '')
  await expect(meetingReadoutControls).toBeVisible()
  await expect(meetingReadout.locator('a').filter({ hasText: /^Project readout/ })).toHaveAttribute('href', '#project-packet')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Review posture/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Field ask/ })).toHaveAttribute('href', '#field-prep')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Boundary statement/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(meetingReadout.getByText(/Miner Temp Power in Santa Teresa, NM: 7 workpackages, 15 tasks, and 186 apparatus candidates are loaded from source fingerprint stat-fingerprint-abc123/i)).toBeVisible()
  await expect(meetingReadout.getByText(/Exceptions are 0 covered, 4 open, 2 blocked and local review notes have not started/i)).toBeVisible()
  await expect(meetingReadout.getByText(/Field prep is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(meetingReadout.getByText(/4 of 6 approval-persistence gates remain blocked; project import remains not admitted; executor closeout evidence is 0 of 8/i)).toBeVisible()
  const constraintRadar = page.locator('details#pm-constraint-radar[aria-label="Local PM intake constraint radar"]')
  await expect(constraintRadar).toHaveAttribute('open', '')
  await expect(constraintRadar.getByRole('heading', { name: /Local PM Intake Constraint Radar/i })).toBeVisible()
  const constraintRadarControls = constraintRadar.locator(':scope > div').first()
  await expect(constraintRadarControls).toBeVisible()
  await expect(constraintRadarControls.locator('a')).toHaveCount(4)
  await expect(constraintRadar.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(constraintRadar.getByText(/Constraint scan for source\/review, field-prep, executor\/hosted, and future write-authority boundaries/i)).toBeVisible()
  await expect(constraintRadar.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, perform hosted writes, or mutate production state/i)).toBeVisible()
  await expect(constraintRadar.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, workbook macro path, workbook writeback, or production write/i)).toBeVisible()
  await constraintRadar.locator(':scope > summary').click()
  await expect(constraintRadar).not.toHaveAttribute('open', '')
  await expect(constraintRadarControls).toBeHidden()
  const constraintRadarDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|constraint-radar/i.test(key)))
  expect(constraintRadarDisclosureStateKeys).toEqual([])
  await constraintRadar.locator(':scope > summary').click()
  await expect(constraintRadar).toHaveAttribute('open', '')
  await expect(constraintRadarControls).toBeVisible()
  await expect(constraintRadar.locator('a').filter({ hasText: /^Source and review constraints/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Field-prep constraints/ })).toHaveAttribute('href', '#field-prep')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Executor and hosted constraints/ })).toHaveAttribute('href', '#executor-closeout')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Future write authority constraints/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(constraintRadar.getByText(/Source fingerprint stat-fingerprint-abc123; review checklist has 0 of 7 local checks marked; exceptions are 0 covered, 4 open, 2 blocked; local review notes have not started/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Field prep is 0 complete \/ 1 next \/ 4 blocked. Field questions present: no; field observations present: no/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Executor closeout intake is 0 of 8; hosted read, schema, approval status, and bounded MCP proof are green while closeout checks remain audit-prep context only/i)).toBeVisible()
  await expect(constraintRadar.getByText(/4 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench/i)).toBeVisible()
  const startHere = page.locator('details#pm-start-here[aria-label="Local PM intake start here"]')
  await expect(startHere).toHaveAttribute('open', '')
  await expect(startHere.getByRole('heading', { name: /Local PM Intake Start Here/i })).toBeVisible()
  const startHereControls = startHere.locator(':scope > div').first()
  await expect(startHereControls).toBeVisible()
  await expect(startHereControls.locator('a')).toHaveCount(5)
  await expect(startHere.getByText('browser-local')).toBeVisible()
  await expect(startHere.getByText(/Top-level focus for this intake session, derived from the existing workbench state/i)).toBeVisible()
  await expect(startHere.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, or mutate production state/i)).toBeVisible()
  await expect(startHere.getByText(/links to existing local sections and exports only; it creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write/i)).toBeVisible()
  await startHere.locator(':scope > summary').click()
  await expect(startHere).not.toHaveAttribute('open', '')
  await expect(startHereControls).toBeHidden()
  const startHereDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|start-here/i.test(key)))
  expect(startHereDisclosureStateKeys).toEqual([])
  await startHere.locator(':scope > summary').click()
  await expect(startHere).toHaveAttribute('open', '')
  await expect(startHereControls).toBeVisible()
  await expect(startHere.getByRole('link', { name: /First local move/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(startHere.getByRole('link', { name: /Exception attention/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(startHere.getByRole('link', { name: /Field-prep focus/i })).toHaveAttribute('href', '#field-prep')
  await expect(startHere.getByRole('link', { name: /Useful local export/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(startHere.getByRole('link', { name: /Blocked future authority/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(startHere.getByText(/Review source and exceptions: Start with source freshness and warning review before relying on the candidate shape/i)).toBeVisible()
  await expect(startHere.getByText(/Import exception register: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(startHere.getByText(/Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(startHere.getByText(/Use Export PM Brief first when the next review needs compact candidate, gate, and guardrail context/i)).toBeVisible()
  await expect(startHere.getByText(/4 of 6 approval-persistence gates remain blocked. Snapshot posture: 1 covered, 4 open, 1 blocked/i)).toBeVisible()
  const dailyScript = page.locator('details#pm-daily-review-script[aria-label="Local PM intake daily review script"]')
  await expect(dailyScript).toHaveAttribute('open', '')
  await expect(dailyScript.getByRole('heading', { name: /Local PM Intake Daily Review Script/i })).toBeVisible()
  const dailyScriptControls = dailyScript.locator(':scope > div').first()
  await expect(dailyScriptControls).toBeVisible()
  await expect(dailyScriptControls.locator('a')).toHaveCount(5)
  await expect(dailyScript.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(dailyScript.getByText(/First 5 minutes of browser-local review, derived from the existing workbench state/i)).toBeVisible()
  await expect(dailyScript.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write/i)).toBeVisible()
  await dailyScript.locator(':scope > summary').click()
  await expect(dailyScript).not.toHaveAttribute('open', '')
  await expect(dailyScriptControls).toBeHidden()
  const dailyScriptDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|daily-review-script|daily-script/i.test(key)))
  expect(dailyScriptDisclosureStateKeys).toEqual([])
  await dailyScript.locator(':scope > summary').click()
  await expect(dailyScript).toHaveAttribute('open', '')
  await expect(dailyScriptControls).toBeVisible()
  await expect(dailyScript.getByRole('link', { name: /Minute 0: Confirm source context/i })).toHaveAttribute('href', '#project-packet')
  await expect(dailyScript.getByRole('link', { name: /Minute 1: Scan exceptions/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(dailyScript.getByRole('link', { name: /Minute 2: Capture local draft notes/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(dailyScript.getByRole('link', { name: /Minute 3: Check field-prep questions/i })).toHaveAttribute('href', '#field-prep')
  await expect(dailyScript.getByRole('link', { name: /Minute 4: Name blocked future authority/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(dailyScript.getByText(/Miner Temp Power: source fingerprint stat-fingerprint-abc123; candidate authority remains not admitted/i)).toBeVisible()
  await expect(dailyScript.getByText(/Import exception register: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(dailyScript.getByText(/Local decision draft has not started; capture decision value, review notes, and local-only attestation before any future persistence packet/i)).toBeVisible()
  await expect(dailyScript.getByText(/Field prep queue: 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(dailyScript.getByText(/0 of 8 local closeout evidence checks are marked; 4 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const outputSelector = page.locator('details#pm-output-selector[aria-label="Local PM intake output selector"]')
  await expect(outputSelector).toHaveAttribute('open', '')
  await expect(outputSelector.getByRole('heading', { name: /Local PM Intake Output Selector/i })).toBeVisible()
  const outputSelectorControls = outputSelector.locator(':scope > div').first()
  await expect(outputSelectorControls).toBeVisible()
  await expect(outputSelectorControls.locator('a')).toHaveCount(24)
  await expect(outputSelector.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(outputSelector.getByText(/Browser-local chooser for existing outputs already on this workbench/i)).toBeVisible()
  await expect(outputSelector.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write/i)).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Output selector groups')).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Review Outputs selector group').getByRole('heading', { name: 'Review Outputs', exact: true })).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Executor Output selector group').getByRole('heading', { name: 'Executor Output', exact: true })).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Field Prep Basics selector group').getByRole('heading', { name: 'Field Prep Basics', exact: true })).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Admission Drafts selector group').getByRole('heading', { name: 'Admission Drafts', exact: true })).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Pilot Launch Outputs selector group').getByRole('heading', { name: 'Pilot Launch Outputs', exact: true })).toBeVisible()
  await expect(outputSelectorControls.getByLabel('Review Outputs selector outputs').getByRole('link')).toHaveCount(4)
  await expect(outputSelectorControls.getByLabel('Executor Output selector outputs').getByRole('link')).toHaveCount(1)
  await expect(outputSelectorControls.getByLabel('Field Prep Basics selector outputs').getByRole('link')).toHaveCount(6)
  await expect(outputSelectorControls.getByLabel('Admission Drafts selector outputs').getByRole('link')).toHaveCount(8)
  await expect(outputSelectorControls.getByLabel('Pilot Launch Outputs selector outputs').getByRole('link')).toHaveCount(5)
  await outputSelector.locator(':scope > summary').click()
  await expect(outputSelector).not.toHaveAttribute('open', '')
  await expect(outputSelectorControls).toBeHidden()
  const outputSelectorDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|output-selector|selector|favorite/i.test(key)))
  expect(outputSelectorDisclosureStateKeys).toEqual([])
  await outputSelector.locator(':scope > summary').click()
  await expect(outputSelector).toHaveAttribute('open', '')
  await expect(outputSelectorControls).toBeVisible()
  await expect(outputSelector.getByRole('link', { name: /PM Brief/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(outputSelector.getByRole('link', { name: /Approval Preview JSON/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(outputSelector.getByRole('link', { name: /PM Intake Snapshot/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(outputSelector.getByRole('link', { name: /Import Exception Register/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(outputSelector.getByRole('link', { name: /Executor Handoff/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(outputSelector.getByRole('link', { name: /Field Kickoff Brief/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Observation Notes/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Prep Coverage Snapshot/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Prep Conversation Agenda/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Prep Packet/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Start Preflight/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Execution Gate Design/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(outputSelector.getByRole('link', { name: /Lead Field Assignment Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Authorization Assignment Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Schedule Status Controls Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Durable Field Record Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Production Tracking Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Customer Reporting Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Financial Handoff Draft/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Pilot Launch Binder/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Pilot Launch Daily Brief/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Pilot Launch Standup Card/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Pilot Launch Capture Sheet/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Pilot Launch Follow-Up Packet/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByText(/Future write packet/i)).toHaveCount(0)
  await expect(outputSelector.getByText(/Use PM Brief when the next review needs compact candidate, gate, and guardrail context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Approval Preview JSON should wait on local decision value, review notes, local-only attestation, and checklist evidence for useful later-packet context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Executor Handoff should wait on local closeout evidence checks when the next packet needs returned executor context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Kickoff Brief is most useful after field questions or readiness evidence are captured; current field prep queue is 0 complete \/ 1 next \/ 4 blocked/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Prep Packet is the bundled field-prep artifact when the next conversation needs questions, coverage, agenda, readiness evidence, and observation context; current field prep queue is 0 complete \/ 1 next \/ 4 blocked/i)).toBeVisible()
  const handoffGuide = page.getByLabel('Local PM intake handoff guide')
  const handoffGuideDisclosure = page.locator('details[aria-label="Local PM intake handoff guide"]')
  const handoffGuideControls = handoffGuide.getByLabel('Handoff guide controls')
  await expect(handoffGuideDisclosure).toHaveAttribute('open', '')
  await expect(handoffGuideControls).toBeVisible()
  await expect(handoffGuide.getByRole('heading', { name: /Local PM Intake Handoff Guide/i })).toBeVisible()
  await expect(handoffGuide.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(handoffGuide.getByText(/Browser-local guide for the next context lane/i)).toBeVisible()
  await expect(handoffGuide.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted write claim, or production write/i)).toBeVisible()
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide groups')).toBeVisible()
  await expect(handoffGuide.getByLabel('Review Context handoff guide group').getByRole('heading', { name: 'Review Context', exact: true })).toBeVisible()
  await expect(handoffGuide.getByLabel('Field And Executor Context handoff guide group').getByRole('heading', { name: 'Field And Executor Context', exact: true })).toBeVisible()
  await expect(handoffGuide.getByLabel('Approval Boundary Context handoff guide group').getByRole('heading', { name: 'Approval Boundary Context', exact: true })).toBeVisible()
  await expect(handoffGuide.getByLabel('Review Context handoff guide items').getByRole('link')).toHaveCount(1)
  await expect(handoffGuide.getByLabel('Field And Executor Context handoff guide items').getByRole('link')).toHaveCount(2)
  await expect(handoffGuide.getByLabel('Approval Boundary Context handoff guide items').getByRole('link')).toHaveCount(2)
  await expect(handoffGuide.getByRole('link')).toHaveCount(5)
  await expect(handoffGuide.getByRole('link', { name: /Jason local review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(handoffGuide.getByRole('link', { name: /Field conversation prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(handoffGuide.getByRole('link', { name: /Bounded executor context/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(handoffGuide.getByRole('link', { name: /Hosted readiness context/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByRole('link', { name: /Future approval-persistence packet boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await handoffGuideDisclosure.locator(':scope > summary').click()
  await expect(handoffGuideDisclosure).not.toHaveAttribute('open', '')
  await expect(handoffGuideControls).toBeHidden()
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide groups')).toBeHidden()
  const handoffGuideDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|handoff-guide|handoff/i.test(key)))
  expect(handoffGuideDisclosureStateKeys).toEqual([])
  await handoffGuideDisclosure.locator(':scope > summary').click()
  await expect(handoffGuideDisclosure).toHaveAttribute('open', '')
  await expect(handoffGuideControls).toBeVisible()
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide groups')).toBeVisible()
  await expect(handoffGuide.getByLabel('Review Context handoff guide items').getByRole('link')).toHaveCount(1)
  await expect(handoffGuide.getByLabel('Field And Executor Context handoff guide items').getByRole('link')).toHaveCount(2)
  await expect(handoffGuide.getByLabel('Approval Boundary Context handoff guide items').getByRole('link')).toHaveCount(2)
  await expect(handoffGuide.getByRole('link')).toHaveCount(5)
  await expect(handoffGuide.getByRole('link', { name: /Jason local review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(handoffGuide.getByRole('link', { name: /Field conversation prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(handoffGuide.getByRole('link', { name: /Bounded executor context/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(handoffGuide.getByRole('link', { name: /Hosted readiness context/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByRole('link', { name: /Future approval-persistence packet boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByText(/Use the workbench for Jason review while exceptions are 0 covered, 4 open, 2 blocked and local decision draft has not started/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Field prep queue is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Keep executor context local until review notes, local decision context, or closeout evidence are present/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Hosted Vercel, Render, approval status readback, and bounded MCP proof are green; this local workbench still grants no browser write authority/i)).toBeVisible()
  await expect(handoffGuide.getByText(/4 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const workflowMap = page.getByLabel('Local PM intake workflow map')
  const workflowMapDisclosure = page.locator('details[aria-label="Local PM intake workflow map"]')
  const workflowMapControls = workflowMap.getByLabel('Workflow map controls')
  await expect(workflowMapDisclosure).toHaveAttribute('open', '')
  await expect(workflowMapControls).toBeVisible()
  await expect(workflowMap.getByRole('heading', { name: /Local PM Intake Workflow Map/i })).toBeVisible()
  await expect(workflowMap.getByText('browser-local')).toBeVisible()
  await expect(workflowMap.getByText(/Visual map of the current intake path from source review through field-prep context, executor closeout, and still-blocked future write authority/i)).toBeVisible()
  await expect(workflowMap.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write/i)).toBeVisible()
  await expect(workflowMap.getByLabel('Local PM intake workflow map groups')).toBeVisible()
  await expect(workflowMap.getByRole('heading', { name: 'Intake Review Path', exact: true })).toBeVisible()
  await expect(workflowMap.getByRole('heading', { name: 'Field And Executor Path', exact: true })).toBeVisible()
  await expect(workflowMap.getByRole('heading', { name: 'Future Authority Boundaries', exact: true })).toBeVisible()
  const intakeReviewPathWorkflowMapGroup = workflowMap.getByLabel('Intake Review Path workflow map group')
  const fieldExecutorPathWorkflowMapGroup = workflowMap.getByLabel('Field And Executor Path workflow map group')
  const futureAuthorityBoundariesWorkflowMapGroup = workflowMap.getByLabel('Future Authority Boundaries workflow map group')
  await expect(intakeReviewPathWorkflowMapGroup.getByLabel('Intake Review Path workflow map items').getByRole('link')).toHaveCount(3)
  await expect(fieldExecutorPathWorkflowMapGroup.getByLabel('Field And Executor Path workflow map items').getByRole('link')).toHaveCount(2)
  await expect(futureAuthorityBoundariesWorkflowMapGroup.getByLabel('Future Authority Boundaries workflow map items').getByRole('link')).toHaveCount(2)
  await expect(workflowMap.getByRole('link')).toHaveCount(7)
  await expect(workflowMap.getByRole('link', { name: /Source intake/i })).toHaveAttribute('href', '#project-packet')
  await expect(workflowMap.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(workflowMap.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(workflowMap.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(workflowMap.getByRole('link', { name: /Executor closeout/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(workflowMap.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(workflowMap.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await workflowMapDisclosure.locator(':scope > summary').click()
  await expect(workflowMapDisclosure).not.toHaveAttribute('open', '')
  await expect(workflowMapControls).toBeHidden()
  await expect(workflowMap.getByLabel('Local PM intake workflow map groups')).toBeHidden()
  const workflowMapDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|workflow-map/i.test(key)))
  expect(workflowMapDisclosureStateKeys).toEqual([])
  await workflowMapDisclosure.locator(':scope > summary').click()
  await expect(workflowMapDisclosure).toHaveAttribute('open', '')
  await expect(workflowMapControls).toBeVisible()
  await expect(workflowMap.getByLabel('Local PM intake workflow map groups')).toBeVisible()
  await expect(intakeReviewPathWorkflowMapGroup.getByLabel('Intake Review Path workflow map items').getByRole('link')).toHaveCount(3)
  await expect(fieldExecutorPathWorkflowMapGroup.getByLabel('Field And Executor Path workflow map items').getByRole('link')).toHaveCount(2)
  await expect(futureAuthorityBoundariesWorkflowMapGroup.getByLabel('Future Authority Boundaries workflow map items').getByRole('link')).toHaveCount(2)
  await expect(workflowMap.getByRole('link')).toHaveCount(7)
  await expect(workflowMap.getByRole('link', { name: /Source intake/i })).toHaveAttribute('href', '#project-packet')
  await expect(workflowMap.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(workflowMap.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(workflowMap.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(workflowMap.getByRole('link', { name: /Executor closeout/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(workflowMap.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(workflowMap.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await expect(workflowMap.getByText(/Source fingerprint stat-fingerprint-abc123 is loaded for the current candidate/i)).toBeVisible()
  await expect(workflowMap.getByText(/Import exception register: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(workflowMap.getByText(/Decision draft has not started/i)).toBeVisible()
  await expect(workflowMap.getByText(/Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(workflowMap.getByText(/0 of 8 local closeout checks marked for returned executor evidence/i)).toBeVisible()
  await expect(workflowMap.getByText(/4 of 6 approval-persistence gates remain blocked until a later packet admits that path/i)).toBeVisible()
  await expect(workflowMap.getByText(/Project import remains not admitted for project, workpackage, task, apparatus, assignment, schedule, and status rows/i)).toBeVisible()
  const openItems = page.getByLabel('Local PM intake open items lens')
  const openItemsDisclosure = page.locator('details[aria-label="Local PM intake open items lens"]')
  const openItemsControls = openItems.getByLabel('Open items lens controls')
  await expect(openItemsDisclosure).toHaveAttribute('open', '')
  await expect(openItemsControls).toBeVisible()
  await expect(openItems.getByRole('heading', { name: /Local PM Intake Open Items Lens/i })).toBeVisible()
  await expect(openItems.getByText('browser-local')).toBeVisible()
  await expect(openItems.getByText(/Exception-first lens for local attention items and future authority blockers/i)).toBeVisible()
  await expect(openItems.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, work authorization, or production write/i)).toBeVisible()
  await expect(openItems.getByLabel('Local PM intake open items lens groups')).toBeVisible()
  await expect(openItems.getByRole('heading', { name: 'Local Attention Items', exact: true })).toBeVisible()
  await expect(openItems.getByRole('heading', { name: 'Executor Evidence Context', exact: true })).toBeVisible()
  await expect(openItems.getByRole('heading', { name: 'Future Authority Blockers', exact: true })).toBeVisible()
  const localAttentionItemsOpenItemsGroup = openItems.getByLabel('Local Attention Items open items lens group')
  const executorEvidenceContextOpenItemsGroup = openItems.getByLabel('Executor Evidence Context open items lens group')
  const futureAuthorityBlockersOpenItemsGroup = openItems.getByLabel('Future Authority Blockers open items lens group')
  await expect(localAttentionItemsOpenItemsGroup.getByLabel('Local Attention Items open items lens items').getByRole('link')).toHaveCount(3)
  await expect(executorEvidenceContextOpenItemsGroup.getByLabel('Executor Evidence Context open items lens items').getByRole('link')).toHaveCount(1)
  await expect(futureAuthorityBlockersOpenItemsGroup.getByLabel('Future Authority Blockers open items lens items').getByRole('link')).toHaveCount(2)
  await expect(openItems.getByRole('link')).toHaveCount(6)
  await expect(openItems.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(openItems.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(openItems.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(openItems.getByRole('link', { name: /Executor closeout evidence/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(openItems.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(openItems.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await openItemsDisclosure.locator(':scope > summary').click()
  await expect(openItemsDisclosure).not.toHaveAttribute('open', '')
  await expect(openItemsControls).toBeHidden()
  await expect(openItems.getByLabel('Local PM intake open items lens groups')).toBeHidden()
  const openItemsDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|open-items/i.test(key)))
  expect(openItemsDisclosureStateKeys).toEqual([])
  await openItemsDisclosure.locator(':scope > summary').click()
  await expect(openItemsDisclosure).toHaveAttribute('open', '')
  await expect(openItemsControls).toBeVisible()
  await expect(openItems.getByLabel('Local PM intake open items lens groups')).toBeVisible()
  await expect(localAttentionItemsOpenItemsGroup.getByLabel('Local Attention Items open items lens items').getByRole('link')).toHaveCount(3)
  await expect(executorEvidenceContextOpenItemsGroup.getByLabel('Executor Evidence Context open items lens items').getByRole('link')).toHaveCount(1)
  await expect(futureAuthorityBlockersOpenItemsGroup.getByLabel('Future Authority Blockers open items lens items').getByRole('link')).toHaveCount(2)
  await expect(openItems.getByRole('link')).toHaveCount(6)
  await expect(openItems.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(openItems.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(openItems.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(openItems.getByRole('link', { name: /Executor closeout evidence/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(openItems.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(openItems.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await expect(openItems.getByText(/4 local exception item\(s\) still need attention; 2 future boundary item\(s\) remain blocked/i)).toBeVisible()
  await expect(openItems.getByText(/Decision value, review notes, and local-only attestation still need local draft context/i)).toBeVisible()
  await expect(openItems.getByText(/1 field-prep item\(s\) are next; 4 field-prep item\(s\) are blocked/i)).toBeVisible()
  await expect(openItems.getByText(/0 of 8 local closeout evidence checks are marked/i)).toBeVisible()
  await expect(openItems.getByText(/4 of 6 approval-persistence gates remain blocked until a later packet admits that path/i)).toBeVisible()
  await expect(openItems.getByText(/Project import remains not admitted for project, workpackage, task, apparatus, assignment, schedule, and status rows/i)).toBeVisible()
  const quickJumpRail = page.getByLabel('PM intake quick jump rail')
  const quickJumpDisclosure = page.locator('details#pm-quick-jump-rail[aria-label="PM intake quick jump rail"]')
  await expect(page.locator('#pm-quick-jump-rail')).toHaveCount(1)
  await expect(quickJumpDisclosure).toHaveAttribute('open', '')
  await expect(quickJumpRail.getByRole('heading', { name: /PM Intake Quick Jump Rail/i })).toBeVisible()
  await expect(quickJumpRail.getByText('browser-local')).toBeVisible()
  await expect(quickJumpRail.getByText(/Fast local navigation for the current intake workbench/i)).toBeVisible()
  await expect(quickJumpRail.getByText(/do not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, or mutate production state/i)).toBeVisible()
  const quickJumpRailOrder = await page.evaluate(() => {
    const summary = document.querySelector('[aria-label="Project Miner intake summary"]')
    const rail = document.querySelector('#pm-quick-jump-rail')
    const commandCenter = document.querySelector('#pm-command-center')
    return Boolean(
      summary
      && rail
      && commandCenter
      && (summary.compareDocumentPosition(rail) & Node.DOCUMENT_POSITION_FOLLOWING)
      && (rail.compareDocumentPosition(commandCenter) & Node.DOCUMENT_POSITION_FOLLOWING),
    )
  })
  expect(quickJumpRailOrder).toBe(true)
  const quickJumpSectionLinks = quickJumpRail.getByLabel('PM intake section links')
  await expect(quickJumpSectionLinks.getByLabel('Daily Review quick jump links').getByRole('heading', { name: 'Daily Review', exact: true })).toBeVisible()
  await expect(quickJumpSectionLinks.getByLabel('Daily Review quick jump links').getByRole('link')).toHaveCount(5)
  await expect(quickJumpSectionLinks.getByLabel('Outputs and Handoff quick jump links').getByRole('heading', { name: 'Outputs and Handoff', exact: true })).toBeVisible()
  await expect(quickJumpSectionLinks.getByLabel('Outputs and Handoff quick jump links').getByRole('link')).toHaveCount(2)
  await expect(quickJumpSectionLinks.getByLabel('Review Flow quick jump links').getByRole('heading', { name: 'Review Flow', exact: true })).toBeVisible()
  await expect(quickJumpSectionLinks.getByLabel('Review Flow quick jump links').getByRole('link')).toHaveCount(5)
  await expect(quickJumpSectionLinks.getByLabel('Source, Field, and Guardrails quick jump links').getByRole('heading', { name: 'Source, Field, and Guardrails', exact: true })).toBeVisible()
  await expect(quickJumpSectionLinks.getByLabel('Source, Field, and Guardrails quick jump links').getByRole('link')).toHaveCount(6)
  await quickJumpDisclosure.locator(':scope > summary').click()
  await expect(quickJumpDisclosure).not.toHaveAttribute('open', '')
  await expect(quickJumpSectionLinks).toBeHidden()
  const quickJumpDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|quick-jump/i.test(key)))
  expect(quickJumpDisclosureStateKeys).toEqual([])
  await quickJumpDisclosure.locator(':scope > summary').click()
  await expect(quickJumpDisclosure).toHaveAttribute('open', '')
  await expect(quickJumpSectionLinks).toBeVisible()
  await expect(quickJumpSectionLinks.getByLabel('Daily Review quick jump links').getByRole('link')).toHaveCount(5)
  await expect(quickJumpSectionLinks.getByLabel('Outputs and Handoff quick jump links').getByRole('link')).toHaveCount(2)
  await expect(quickJumpSectionLinks.getByLabel('Review Flow quick jump links').getByRole('link')).toHaveCount(5)
  await expect(quickJumpSectionLinks.getByLabel('Source, Field, and Guardrails quick jump links').getByRole('link')).toHaveCount(6)
  await expect(quickJumpRail.getByRole('link', { name: /Command Center/i })).toHaveAttribute('href', '#pm-command-center')
  await expect(quickJumpRail.getByRole('link', { name: /Meeting Readout/i })).toHaveAttribute('href', '#pm-meeting-readout')
  await expect(quickJumpRail.getByRole('link', { name: /Constraint Radar/i })).toHaveAttribute('href', '#pm-constraint-radar')
  await expect(quickJumpRail.getByRole('link', { name: /Start Here/i })).toHaveAttribute('href', '#pm-start-here')
  await expect(quickJumpRail.getByRole('link', { name: /Daily Script/i })).toHaveAttribute('href', '#pm-daily-review-script')
  await expect(quickJumpRail.getByRole('link', { name: /Output Selector/i })).toHaveAttribute('href', '#pm-output-selector')
  await expect(quickJumpRail.getByRole('link', { name: /Handoff Guide/i })).toHaveAttribute('href', '#pm-handoff-guide')
  await expect(quickJumpRail.getByRole('link', { name: /Workflow Map/i })).toHaveAttribute('href', '#pm-workflow-map')
  await expect(quickJumpRail.getByRole('link', { name: /Open Items/i })).toHaveAttribute('href', '#pm-open-items')
  await expect(quickJumpRail.getByRole('link', { name: /Snapshot/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(quickJumpRail.getByRole('link', { name: /Operating Queue/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(quickJumpRail.getByRole('link', { name: /Exception Register/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(quickJumpRail.getByRole('link', { name: /Project Packet/i })).toHaveAttribute('href', '#project-packet')
  await expect(quickJumpRail.getByRole('link', { name: /Workflow Gates/i })).toHaveAttribute('href', '#workflow-gates')
  await expect(quickJumpRail.getByRole('link', { name: /Approval Readiness/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(quickJumpRail.getByRole('link', { name: /Field Prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(quickJumpRail.getByRole('link', { name: /Executor Closeout/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(quickJumpRail.getByRole('link', { name: /Guardrails/i })).toHaveAttribute('href', '#guardrails')
  for (const target of [
    '#pm-command-center',
    '#pm-meeting-readout',
    '#pm-constraint-radar',
    '#pm-start-here',
    '#pm-daily-review-script',
    '#pm-output-selector',
    '#pm-handoff-guide',
    '#pm-workflow-map',
    '#pm-open-items',
    '#pm-intake-snapshot',
    '#pm-operating-queue',
    '#import-exception-register',
    '#project-packet',
    '#workflow-gates',
    '#approval-readiness',
    '#field-prep',
    '#executor-closeout',
    '#guardrails',
  ]) {
    await expect(quickJumpRail.locator(`a[href="${target}"]`)).toHaveCount(1)
  }
  for (const target of [
    '#pm-quick-jump-rail',
    '#pm-command-center',
    '#pm-meeting-readout',
    '#pm-constraint-radar',
    '#pm-start-here',
    '#pm-daily-review-script',
    '#pm-output-selector',
    '#pm-handoff-guide',
    '#pm-workflow-map',
    '#pm-open-items',
    '#pm-intake-snapshot',
    '#pm-operating-queue',
    '#import-exception-register',
    '#project-packet',
    '#workflow-gates',
    '#approval-readiness',
    '#field-prep',
    '#executor-closeout',
    '#guardrails',
  ]) {
    await expect(page.locator(target)).toHaveCount(1)
  }
  await quickJumpRail.getByRole('link', { name: /Snapshot/i }).click()
  await expect(page).toHaveURL(/#pm-intake-snapshot$/)
  await quickJumpRail.getByRole('link', { name: /Guardrails/i }).click()
  await expect(page).toHaveURL(/#guardrails$/)
  const guardrails = page.locator('details#guardrails[aria-label="Current PM next actions and guardrails"]')
  await expect(guardrails).toHaveAttribute('open', '')
  await expect(guardrails.getByRole('heading', { name: 'Current PM Next Actions and Guardrails', exact: true })).toBeVisible()
  const guardrailsBodyControls = guardrails.locator('[aria-label="Current PM guardrails body controls"]')
  await expect(guardrailsBodyControls).toBeVisible()
  const guardrailsControls = guardrailsBodyControls.locator('[aria-label="Current PM guardrails controls"]')
  await expect(guardrailsControls).toBeVisible()
  await expect(guardrailsControls.locator('article')).toHaveCount(2)
  await expect(guardrailsControls.getByRole('heading', { name: 'Current PM Next Actions', exact: true })).toBeVisible()
  await expect(guardrailsControls.getByRole('heading', { name: 'Not Allowed Now', exact: true })).toBeVisible()
  await expect(guardrailsControls.getByText(/Review candidate exceptions, source freshness, and required human decisions/i)).toBeVisible()
  await expect(guardrailsControls.getByText(/Keep browser approval submission and project import blocked until later packets explicitly admit those writes/i)).toBeVisible()
  await expect(guardrailsControls.getByText('write supabase', { exact: true })).toBeVisible()
  await guardrails.locator(':scope > summary').click()
  await expect(guardrails).not.toHaveAttribute('open', '')
  await expect(guardrailsBodyControls).toBeHidden()
  await expect(guardrailsControls).toBeHidden()
  const guardrailsDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|guardrails/i.test(key)))
  expect(guardrailsDisclosureStateKeys).toEqual([])
  await guardrails.locator(':scope > summary').click()
  await expect(guardrails).toHaveAttribute('open', '')
  await expect(guardrailsBodyControls).toBeVisible()
  await expect(guardrailsControls).toBeVisible()
  await expect(page.getByLabel('Project packet and source freshness').getByRole('heading', { name: /Project Packet/i })).toBeVisible()
  const pmIntakeSnapshot = page.getByLabel('Local PM intake snapshot')
  await expect(pmIntakeSnapshot.getByRole('heading', { name: /Local PM Intake Snapshot/i })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('browser-local')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText(/Compact scan view for exception posture, decision draft, field-prep context, next local action, hosted parity, and future write boundaries/i)).toBeVisible()
  await expect(pmIntakeSnapshot.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state/i)).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('1 covered, 4 open, 1 blocked', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByLabel('Local PM intake snapshot groups')).toBeVisible()
  await expect(pmIntakeSnapshot.getByRole('heading', { name: 'Review Posture', exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByRole('heading', { name: 'Field Readiness Posture', exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByRole('heading', { name: 'Authority Boundary Posture', exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByLabel('Review Posture snapshot group').getByLabel('Review Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(pmIntakeSnapshot.getByLabel('Field Readiness Posture snapshot group').getByLabel('Field Readiness Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(pmIntakeSnapshot.getByLabel('Authority Boundary Posture snapshot group').getByLabel('Authority Boundary Posture snapshot items').locator('article')).toHaveCount(2)
  await expect(pmIntakeSnapshot.getByLabel('Local PM intake snapshot groups').locator('article')).toHaveCount(6)
  await expect(pmIntakeSnapshot.getByText('Exception review snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Decision draft snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Field prep snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Next local action snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Approval persistence boundary', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Hosted parity boundary', { exact: true })).toBeVisible()
  const operatingQueue = page.getByLabel('Local PM operating queue')
  const operatingQueueDisclosure = page.locator('details#pm-operating-queue[aria-label="Local PM operating queue"]')
  await expect(operatingQueueDisclosure).toHaveAttribute('open', '')
  const operatingQueueControls = operatingQueueDisclosure.getByLabel('PM operating queue controls')
  await expect(operatingQueueControls).toBeVisible()
  const operatingQueueGroups = operatingQueueDisclosure.getByLabel('Local PM operating queue groups')
  await expect(operatingQueueGroups).toBeVisible()
  await expect(operatingQueue.getByRole('heading', { name: 'Local Review Moves', exact: true })).toBeVisible()
  await expect(operatingQueue.getByRole('heading', { name: 'Approval Submission Boundary', exact: true })).toBeVisible()
  await expect(operatingQueue.getByRole('heading', { name: 'Future Import Boundary', exact: true })).toBeVisible()
  await expect(operatingQueue.getByLabel('Local Review Moves operating queue group').getByLabel('Local Review Moves operating queue items').locator('article')).toHaveCount(3)
  await expect(operatingQueue.getByLabel('Approval Submission Boundary operating queue group').getByLabel('Approval Submission Boundary operating queue items').locator('article')).toHaveCount(3)
  await expect(operatingQueue.getByLabel('Future Import Boundary operating queue group').getByLabel('Future Import Boundary operating queue items').locator('article')).toHaveCount(1)
  await expect(operatingQueueGroups.locator('article')).toHaveCount(7)
  await expect(operatingQueue.getByRole('heading', { name: /Local PM Operating Queue/i })).toBeVisible()
  await expect(operatingQueue.getByText('browser-local')).toBeVisible()
  await expect(operatingQueue.getByText('1 complete / 1 next / 5 blocked')).toBeVisible()
  await expect(operatingQueue.getByText('Review source and exceptions', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Prepare local decision draft', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Export review artifacts', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Hosted approval gate complete', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Browser approval submission packet', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Approval row creation', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Project import packet', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText(/Local queue for today's intake work/i)).toBeVisible()
  await expect(operatingQueue.getByText(/without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state/i)).toBeVisible()
  await operatingQueueDisclosure.locator(':scope > summary').click()
  await expect(operatingQueueDisclosure).not.toHaveAttribute('open', '')
  await expect(operatingQueueControls).toBeHidden()
  await expect(operatingQueueGroups).toBeHidden()
  const operatingQueueDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|operating-queue/i.test(key)))
  expect(operatingQueueDisclosureStateKeys).toEqual([])
  await operatingQueueDisclosure.locator(':scope > summary').click()
  await expect(operatingQueueDisclosure).toHaveAttribute('open', '')
  await expect(operatingQueueControls).toBeVisible()
  await expect(operatingQueueGroups).toBeVisible()
  await expect(operatingQueueGroups.locator('article')).toHaveCount(7)
  const exceptionRegister = page.getByLabel('Local import exception decision register')
  const exceptionRegisterDisclosure = page.locator('details#import-exception-register[aria-label="Local import exception decision register"]')
  await expect(exceptionRegisterDisclosure).toHaveAttribute('open', '')
  const exceptionRegisterControls = exceptionRegisterDisclosure.getByLabel('Import exception register controls')
  await expect(exceptionRegisterControls).toBeVisible()
  const exceptionRegisterGroups = exceptionRegisterDisclosure.getByLabel('Local import exception decision register groups')
  await expect(exceptionRegisterGroups).toBeVisible()
  await expect(exceptionRegister.getByRole('heading', { name: 'Source Review Signals', exact: true })).toBeVisible()
  await expect(exceptionRegister.getByRole('heading', { name: 'PM Decision Context', exact: true })).toBeVisible()
  await expect(exceptionRegister.getByRole('heading', { name: 'Admission Boundary', exact: true })).toBeVisible()
  await expect(exceptionRegister.getByLabel('Source Review Signals import exception group').getByLabel('Source Review Signals import exception items').locator('article')).toHaveCount(2)
  await expect(exceptionRegister.getByLabel('PM Decision Context import exception group').getByLabel('PM Decision Context import exception items').locator('article')).toHaveCount(2)
  await expect(exceptionRegister.getByLabel('Admission Boundary import exception group').getByLabel('Admission Boundary import exception items').locator('article')).toHaveCount(2)
  await expect(exceptionRegisterGroups.locator('article')).toHaveCount(6)
  await expect(exceptionRegister.getByRole('heading', { name: /Local Import Exception Decision Register/i })).toBeVisible()
  await expect(exceptionRegister.getByText('browser-local')).toBeVisible()
  await expect(exceptionRegister.getByText(/Derived exception register for candidate warnings, human decision prompts, admission no-go checks, local review evidence, and local decision draft context/i)).toBeVisible()
  await expect(exceptionRegister.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state/i)).toBeVisible()
  await expect(exceptionRegister.getByText('0 covered, 4 open, 2 blocked')).toBeVisible()
  await expect(exceptionRegister.getByText('Source freshness evidence', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('Candidate warning signals', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('Human decision prompts', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('Admission no-go checks', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('Local decision draft evidence', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('Future write boundary', { exact: true })).toBeVisible()
  await exceptionRegisterDisclosure.locator(':scope > summary').click()
  await expect(exceptionRegisterDisclosure).not.toHaveAttribute('open', '')
  await expect(exceptionRegisterControls).toBeHidden()
  await expect(exceptionRegisterGroups).toBeHidden()
  const exceptionRegisterDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|import-exception-register/i.test(key)))
  expect(exceptionRegisterDisclosureStateKeys).toEqual([])
  await exceptionRegisterDisclosure.locator(':scope > summary').click()
  await expect(exceptionRegisterDisclosure).toHaveAttribute('open', '')
  await expect(exceptionRegisterControls).toBeVisible()
  await expect(exceptionRegisterGroups).toBeVisible()
  await expect(exceptionRegisterGroups.locator('article')).toHaveCount(6)
  const workflowGates = page.getByLabel('Workflow gates')
  const workflowGatesDisclosure = page.locator('details#workflow-gates[aria-label="Workflow gates"]')
  await expect(workflowGatesDisclosure).toHaveAttribute('open', '')
  const workflowGatesControls = workflowGatesDisclosure.getByLabel('Workflow gates controls')
  await expect(workflowGatesControls).toBeVisible()
  const workflowGateGroups = workflowGatesDisclosure.getByLabel('Workflow gate groups')
  await expect(workflowGateGroups).toBeVisible()
  await expect(workflowGates.getByRole('heading', { name: 'Source Review Gates', exact: true })).toBeVisible()
  await expect(workflowGates.getByRole('heading', { name: 'Approval Readiness Gates', exact: true })).toBeVisible()
  await expect(workflowGates.getByRole('heading', { name: 'Future Import Boundary', exact: true })).toBeVisible()
  await expect(workflowGates.getByLabel('Source Review Gates workflow gate group').getByLabel('Source Review Gates workflow gate items').locator('article')).toHaveCount(2)
  await expect(workflowGates.getByLabel('Approval Readiness Gates workflow gate group').getByLabel('Approval Readiness Gates workflow gate items').locator('article')).toHaveCount(3)
  await expect(workflowGates.getByLabel('Future Import Boundary workflow gate group').getByLabel('Future Import Boundary workflow gate items').locator('article')).toHaveCount(1)
  await expect(workflowGateGroups.locator('article')).toHaveCount(6)
  await expect(workflowGates.getByRole('heading', { name: /Workflow Gates/i })).toBeVisible()
  await expect(workflowGates.getByText('read-only')).toBeVisible()
  await expect(workflowGates.getByText('Source intake', { exact: true })).toBeVisible()
  await expect(workflowGates.getByText('Candidate review', { exact: true })).toBeVisible()
  await expect(workflowGates.getByText('Admission gate', { exact: true })).toBeVisible()
  await expect(workflowGates.getByText('Approval readiness', { exact: true })).toBeVisible()
  await expect(workflowGates.getByText('Hosted parity', { exact: true })).toBeVisible()
  await expect(workflowGates.getByText('Future import', { exact: true })).toBeVisible()
  await workflowGatesDisclosure.locator(':scope > summary').click()
  await expect(workflowGatesDisclosure).not.toHaveAttribute('open', '')
  await expect(workflowGatesControls).toBeHidden()
  await expect(workflowGateGroups).toBeHidden()
  const workflowGatesDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|workflow-gates/i.test(key)))
  expect(workflowGatesDisclosureStateKeys).toEqual([])
  await workflowGatesDisclosure.locator(':scope > summary').click()
  await expect(workflowGatesDisclosure).toHaveAttribute('open', '')
  await expect(workflowGatesControls).toBeVisible()
  await expect(workflowGateGroups).toBeVisible()
  await expect(workflowGateGroups.locator('article')).toHaveCount(6)
  const exceptionDecisionDetail = page.locator('details[aria-label="Exception review and PM decision detail"]')
  await expect(exceptionDecisionDetail).toHaveAttribute('open', '')
  const exceptionDecisionControls = exceptionDecisionDetail.getByLabel('Exception review and PM decision detail controls')
  await expect(exceptionDecisionControls).toBeVisible()
  const exceptionDecisionGroups = exceptionDecisionDetail.locator('[aria-label="Exception and PM decision detail groups"]')
  await expect(exceptionDecisionGroups).toBeVisible()
  await expect(exceptionDecisionGroups.locator(':scope > section')).toHaveCount(2)
  await expect(exceptionDecisionDetail.getByRole('heading', { name: 'Exception Signals', exact: true })).toBeVisible()
  await expect(exceptionDecisionDetail.getByRole('heading', { name: 'PM Decision Context', exact: true })).toBeVisible()
  await expect(exceptionDecisionDetail.getByLabel('Exception Signals detail group').getByLabel('Exception Signals detail cards').locator(':scope > article')).toHaveCount(1)
  await expect(exceptionDecisionDetail.getByLabel('PM Decision Context detail group').getByLabel('PM Decision Context detail cards').locator(':scope > article')).toHaveCount(1)
  await expect(exceptionDecisionGroups.locator('.notes-card')).toHaveCount(2)
  await expect(exceptionDecisionGroups.getByRole('heading', { name: 'Exception Review', exact: true })).toBeVisible()
  await expect(exceptionDecisionGroups.getByRole('heading', { name: 'PM Decisions', exact: true })).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('PROJECT_DATA_ENTRY_FORMULA_ERRORS')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('234 planning-workbook rows include formula errors.')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('decision approve candidate for import planning')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('Does this candidate correctly represent the project, workpackages, tasks, and apparatus?')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('Approve only after blocker and warning review is complete.')).toBeVisible()
  await exceptionDecisionDetail.locator(':scope > summary').click()
  await expect(exceptionDecisionDetail).not.toHaveAttribute('open', '')
  await expect(exceptionDecisionControls).toBeHidden()
  await expect(exceptionDecisionGroups).toBeHidden()
  const exceptionDecisionDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|exception-review|pm-decision/i.test(key)))
  expect(exceptionDecisionDisclosureStateKeys).toEqual([])
  await exceptionDecisionDetail.locator(':scope > summary').click()
  await expect(exceptionDecisionDetail).toHaveAttribute('open', '')
  await expect(exceptionDecisionControls).toBeVisible()
  await expect(exceptionDecisionGroups).toBeVisible()
  await expect(exceptionDecisionGroups.locator(':scope > section')).toHaveCount(2)
  await expect(exceptionDecisionGroups.locator('.notes-card')).toHaveCount(2)
  const admissionApprovalContract = page.locator('details[aria-label="Admission and approval contract"]')
  await expect(admissionApprovalContract).toHaveAttribute('open', '')
  const admissionApprovalContractControls = admissionApprovalContract.getByLabel('Admission and approval contract controls')
  await expect(admissionApprovalContractControls).toBeVisible()
  const admissionApprovalContractGroups = admissionApprovalContract.locator('[aria-label="Admission and approval contract groups"]')
  await expect(admissionApprovalContractGroups).toBeVisible()
  await expect(admissionApprovalContractGroups.locator(':scope > section')).toHaveCount(3)
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Admission Shape Context', exact: true })).toBeVisible()
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Approval Contract Context', exact: true })).toBeVisible()
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Approval Status Context', exact: true })).toBeVisible()
  const admissionShapeContextGroup = admissionApprovalContractGroups.getByLabel('Admission Shape Context contract group')
  const approvalContractContextGroup = admissionApprovalContractGroups.getByLabel('Approval Contract Context contract group')
  const approvalStatusContextGroup = admissionApprovalContractGroups.getByLabel('Approval Status Context contract group')
  await expect(admissionShapeContextGroup.getByLabel('Admission Shape Context contract cards').locator(':scope > article')).toHaveCount(1)
  await expect(approvalContractContextGroup.getByLabel('Approval Contract Context contract cards').locator(':scope > article')).toHaveCount(1)
  await expect(approvalStatusContextGroup.getByLabel('Approval Status Context contract cards').locator(':scope > article')).toHaveCount(1)
  await expect(admissionApprovalContractGroups.locator('.notes-card')).toHaveCount(3)
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Admission Shape', exact: true })).toBeVisible()
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Approval Contract', exact: true })).toBeVisible()
  await expect(admissionApprovalContractGroups.getByRole('heading', { name: 'Approval Status Readback', exact: true })).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm-import-candidate-miner-temp-power-admission-plan')).toBeVisible()
  await expect(admissionApprovalContract.getByText('project rows: 1; workpackage rows: 7; task rows: 15; apparatus rows: 186; approval rows: 1; write authority: not_admitted')).toBeVisible()
  await expect(admissionShapeContextGroup.getByText('No-go checks')).toBeVisible()
  await expect(admissionShapeContextGroup.locator('dd').filter({ hasText: /^2$/ })).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm-import-candidate-miner-temp-power-approval-persistence-contract')).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm_import_candidate_approval', { exact: true })).toBeVisible()
  await expect(admissionApprovalContract.getByText('design_only_not_admitted')).toBeVisible()
  await expect(admissionApprovalContract.getByText('seam.pm_import_candidate_approvals')).toBeVisible()
  await expect(admissionApprovalContract.getByText('/api/v1/mutations/project-import-approvals')).toBeVisible()
  await expect(admissionApprovalContract.getByText('no approval record')).toBeVisible()
  await expect(admissionApprovalContract.getByText('/api/v1/reads/project-import-approval-status')).toBeVisible()
  await expect(approvalStatusContextGroup.getByText(/Status readback only\. This panel does not approve, persist, import, assign, schedule, change status, or mutate production state\./i)).toBeVisible()
  await admissionApprovalContract.locator(':scope > summary').click()
  await expect(admissionApprovalContract).not.toHaveAttribute('open', '')
  await expect(admissionApprovalContractControls).toBeHidden()
  await expect(admissionApprovalContractGroups).toBeHidden()
  const admissionApprovalContractDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|admission|approval-contract/i.test(key)))
  expect(admissionApprovalContractDisclosureStateKeys).toEqual([])
  await admissionApprovalContract.locator(':scope > summary').click()
  await expect(admissionApprovalContract).toHaveAttribute('open', '')
  await expect(admissionApprovalContractControls).toBeVisible()
  await expect(admissionApprovalContractGroups).toBeVisible()
  await expect(admissionApprovalContractGroups.locator(':scope > section')).toHaveCount(3)
  await expect(admissionApprovalContractGroups.locator('.notes-card')).toHaveCount(3)
  const checklist = page.locator('details[aria-label="Local review checklist"]')
  await expect(checklist).toHaveAttribute('open', '')
  const checklistBodyControls = checklist.getByLabel('Local review checklist controls')
  await expect(checklistBodyControls).toBeVisible()
  const checklistControls = checklistBodyControls.getByLabel('Review checklist controls')
  await expect(checklistControls).toBeVisible()
  const reviewChecklistNames = [
    'Source freshness reviewed',
    'Warnings reviewed',
    'PM decisions captured',
    'Admission no-go checks reviewed',
    'Approval storage understood',
    'Hosted parity acknowledged',
    'Write guardrails confirmed',
  ]
  const checklistGroups = checklistControls.getByLabel('Review checklist groups')
  await expect(checklistGroups).toBeVisible()
  await expect(checklistGroups.locator(':scope > section')).toHaveCount(3)
  await expect(checklistGroups.getByRole('heading', { name: 'Source Review Evidence', exact: true })).toBeVisible()
  await expect(checklistGroups.getByRole('heading', { name: 'Approval Readiness Evidence', exact: true })).toBeVisible()
  await expect(checklistGroups.getByRole('heading', { name: 'Write Boundary Confirmation', exact: true })).toBeVisible()
  const sourceReviewEvidenceGroup = checklistGroups.getByLabel('Source Review Evidence checklist group')
  const approvalReadinessEvidenceGroup = checklistGroups.getByLabel('Approval Readiness Evidence checklist group')
  const writeBoundaryConfirmationGroup = checklistGroups.getByLabel('Write Boundary Confirmation checklist group')
  await expect(sourceReviewEvidenceGroup.getByLabel('Source Review Evidence checklist items').locator('label')).toHaveCount(3)
  await expect(sourceReviewEvidenceGroup.getByLabel('Source Review Evidence checklist items').getByRole('checkbox')).toHaveCount(3)
  await expect(approvalReadinessEvidenceGroup.getByLabel('Approval Readiness Evidence checklist items').locator('label')).toHaveCount(3)
  await expect(approvalReadinessEvidenceGroup.getByLabel('Approval Readiness Evidence checklist items').getByRole('checkbox')).toHaveCount(3)
  await expect(writeBoundaryConfirmationGroup.getByLabel('Write Boundary Confirmation checklist items').locator('label')).toHaveCount(1)
  await expect(writeBoundaryConfirmationGroup.getByLabel('Write Boundary Confirmation checklist items').getByRole('checkbox')).toHaveCount(1)
  await expect(checklistGroups.locator('label')).toHaveCount(7)
  await expect(checklistControls.getByRole('checkbox')).toHaveCount(7)
  for (const name of reviewChecklistNames) {
    await expect(checklist.getByRole('checkbox', { name })).toHaveCount(1)
  }
  await expect(checklist.getByRole('heading', { name: /Local Review Checklist/i })).toBeVisible()
  await expect(checklist.getByText(/Browser-local review prep only/i)).toBeVisible()
  await expect(checklist.getByText('0 of 7')).toBeVisible()
  await expect(checklist.getByRole('button', { name: 'Clear checklist' })).toBeDisabled()
  await checklist.locator(':scope > summary').click()
  await expect(checklist).not.toHaveAttribute('open', '')
  await expect(checklistBodyControls).toBeHidden()
  await expect(checklistControls).toBeHidden()
  await expect(checklistGroups).toBeHidden()
  const reviewChecklistDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|local-review-checklist/i.test(key)))
  expect(reviewChecklistDisclosureStateKeys).toEqual([])
  await checklist.locator(':scope > summary').click()
  await expect(checklist).toHaveAttribute('open', '')
  await expect(checklistBodyControls).toBeVisible()
  await expect(checklistControls).toBeVisible()
  await expect(checklistGroups).toBeVisible()
  await expect(checklistGroups.locator(':scope > section')).toHaveCount(3)
  await expect(checklistGroups.locator('label')).toHaveCount(7)
  await checklist.getByRole('checkbox', { name: /Source freshness reviewed/i }).check()
  await checklist.getByRole('checkbox', { name: /Warnings reviewed/i }).check()
  await expect(checklist.getByText('2 of 7')).toBeVisible()
  await expect(checklist.getByRole('button', { name: 'Clear checklist' })).toBeEnabled()
  const approvalDraft = page.locator('details[aria-label="Local approval decision draft"]')
  await expect(approvalDraft).toHaveAttribute('open', '')
  const approvalDraftBodyControls = approvalDraft.locator('[aria-label="Local approval decision draft controls"]')
  await expect(approvalDraftBodyControls).toBeVisible()
  const approvalDraftControls = approvalDraftBodyControls.locator('[aria-label="Approval draft controls"]')
  await expect(approvalDraftControls).toBeVisible()
  const approvalDraftGroups = approvalDraftControls.locator('[aria-label="Approval decision draft groups"]')
  await expect(approvalDraftGroups).toBeVisible()
  await expect(approvalDraftGroups.locator(':scope > section')).toHaveCount(3)
  await expect(approvalDraftGroups.locator('label')).toHaveCount(3)
  const decisionValueContextGroup = approvalDraftGroups.locator('[aria-label="Decision Value Context approval draft group"]')
  const reviewNotesContextGroup = approvalDraftGroups.locator('[aria-label="Review Notes Context approval draft group"]')
  const localAttestationContextGroup = approvalDraftGroups.locator('[aria-label="Local Attestation Context approval draft group"]')
  await expect(decisionValueContextGroup.getByRole('heading', { name: 'Decision Value Context' })).toBeVisible()
  await expect(reviewNotesContextGroup.getByRole('heading', { name: 'Review Notes Context' })).toBeVisible()
  await expect(localAttestationContextGroup.getByRole('heading', { name: 'Local Attestation Context' })).toBeVisible()
  await expect(decisionValueContextGroup.locator('[aria-label="Decision Value Context approval draft items"] label')).toHaveCount(1)
  await expect(reviewNotesContextGroup.locator('[aria-label="Review Notes Context approval draft items"] label')).toHaveCount(1)
  await expect(localAttestationContextGroup.locator('[aria-label="Local Attestation Context approval draft items"] label')).toHaveCount(1)
  await expect(approvalDraftGroups.locator('select')).toHaveCount(1)
  await expect(approvalDraftGroups.locator('textarea')).toHaveCount(1)
  await expect(approvalDraftGroups.getByRole('checkbox', { name: /Local-only draft attestation/i })).toHaveCount(1)
  await expect(approvalDraft.getByRole('heading', { name: /Local Approval Decision Draft/i })).toBeVisible()
  await expect(approvalDraft.getByText(/local review prep/i)).toBeVisible()
  await expect(approvalDraft.getByRole('button', { name: 'Clear decision draft' })).toBeDisabled()
  const approvalDraftDecisionSelect = approvalDraft.locator('select')
  const approvalDraftNotes = approvalDraft.locator('textarea').first()
  await approvalDraft.locator(':scope > summary').click()
  await expect(approvalDraft).not.toHaveAttribute('open', '')
  await expect(approvalDraftBodyControls).toBeHidden()
  await expect(approvalDraftControls).toBeHidden()
  await expect(approvalDraftGroups).toBeHidden()
  const approvalDraftDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|approval-draft|approval-decision-draft/i.test(key)))
  expect(approvalDraftDisclosureStateKeys).toEqual([])
  await approvalDraft.locator(':scope > summary').click()
  await expect(approvalDraft).toHaveAttribute('open', '')
  await expect(approvalDraftBodyControls).toBeVisible()
  await expect(approvalDraftControls).toBeVisible()
  await expect(approvalDraftGroups).toBeVisible()
  await expect(approvalDraftGroups.locator(':scope > section')).toHaveCount(3)
  await expect(approvalDraftGroups.locator('label')).toHaveCount(3)
  await approvalDraftDecisionSelect.selectOption('return_for_revision')
  await approvalDraftNotes.fill('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  await approvalDraft.getByRole('checkbox', { name: /Local-only draft attestation/i }).check()
  await expect(approvalDraft.getByRole('button', { name: 'Clear decision draft' })).toBeEnabled()
  await expect(exceptionRegister.getByText('4 covered, 0 open, 2 blocked')).toBeVisible()
  await expect(startHere.getByText(/Export review artifacts: Use the PM brief and approval preview JSON as browser-local context for the next admitted packet/i)).toBeVisible()
  await expect(startHere.getByText(/Import exception register: 4 covered, 0 open, 2 blocked/i)).toBeVisible()
  await expect(dailyScript.getByText(/Import exception register: 4 covered, 0 open, 2 blocked/i)).toBeVisible()
  await expect(dailyScript.getByText(/Local decision draft has decision value, review notes, and local-only attestation for this browser-local review/i)).toBeVisible()
  await expect(outputSelector.getByText(/Approval Preview JSON has local decision draft context and 2 of 7 review checks for a later admitted approval-persistence packet/i)).toBeVisible()
  await expect(commandCenter.locator('a').filter({ hasText: /^Do now/ })).toHaveAttribute('href', '#pm-output-selector')
  await expect(commandCenter.locator('a').filter({ hasText: /^Prepare handoff context/ })).toHaveAttribute('href', '#pm-handoff-guide')
  await expect(commandCenter.getByText(/Local review context is captured; use the output selector to choose the existing local artifact for the next conversation or packet context/i)).toBeVisible()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 0 of 8; field questions: no; field observations: no/i)).toBeVisible()
  await expect(meetingReadout.locator('a').filter({ hasText: /^Review posture/ })).toHaveAttribute('href', '#pm-output-selector')
  await expect(meetingReadout.getByText(/Local review notes are captured; exceptions are 4 covered, 0 open, 2 blocked for later packet context/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Source fingerprint stat-fingerprint-abc123; review checklist has 2 of 7 local checks marked; exceptions are 4 covered, 0 open, 2 blocked; local review notes are captured/i)).toBeVisible()
  await expect(constraintRadar.getByText(/2 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Use the workbench for Jason review while exceptions are 4 covered, 0 open, 2 blocked and local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Existing Executor Handoff context has 0 of 8 local closeout evidence checks marked plus local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(workflowMap.getByText(/Import exception register: 4 covered, 0 open, 2 blocked/i)).toBeVisible()
  await expect(workflowMap.getByText(/Local decision draft has a decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(openItems.getByText(/Local exception attention is covered, but 2 future boundary item\(s\) remain blocked/i)).toBeVisible()
  await expect(openItems.getByText(/Local decision value, review notes, and local-only attestation are present/i)).toBeVisible()
  const approvalDryRun = page.locator('details[aria-label="Local approval submission dry run"]')
  await expect(approvalDryRun).toHaveAttribute('open', '')
  const approvalDryRunBodyControls = approvalDryRun.locator('[aria-label="Local approval submission dry run controls"]')
  await expect(approvalDryRunBodyControls).toBeVisible()
  const approvalDryRunControls = approvalDryRunBodyControls.locator('[aria-label="Approval dry run controls"]')
  await expect(approvalDryRunControls).toBeVisible()
  await expect(approvalDryRun.getByRole('heading', { name: /Local Approval Submission Dry Run/i })).toBeVisible()
  await expect(approvalDryRun.getByText(/Builds the future approval POST envelope in this browser for review only/i)).toBeVisible()
  await expect(approvalDryRun.getByText(/Live approval POST, first approval-row creation, and project import remain blocked/i)).toBeVisible()
  await expect(approvalDryRun.getByText('4 ready, 1 needs review, 1 blocked')).toBeVisible()
  const approvalDryRunGroups = approvalDryRunControls.locator('[aria-label="Approval dry run groups"]')
  await expect(approvalDryRunGroups).toBeVisible()
  await expect(approvalDryRunGroups.locator(':scope > section')).toHaveCount(3)
  const dryRunReadinessContextGroup = approvalDryRunGroups.locator('[aria-label="Dry Run Readiness Context approval dry run group"]')
  const futureRequestBoundaryContextGroup = approvalDryRunGroups.locator('[aria-label="Future Request Boundary Context approval dry run group"]')
  const localArtifactActionsContextGroup = approvalDryRunGroups.locator('[aria-label="Local Artifact Actions Context approval dry run group"]')
  await expect(dryRunReadinessContextGroup.getByRole('heading', { name: 'Dry Run Readiness Context' })).toBeVisible()
  await expect(futureRequestBoundaryContextGroup.getByRole('heading', { name: 'Future Request Boundary Context' })).toBeVisible()
  await expect(localArtifactActionsContextGroup.getByRole('heading', { name: 'Local Artifact Actions Context' })).toBeVisible()
  const approvalDryRunReadiness = dryRunReadinessContextGroup.getByLabel('Approval dry run readiness checkpoint')
  await expect(approvalDryRunReadiness).toBeVisible()
  await expect(approvalDryRunReadiness.locator(':scope > article')).toHaveCount(6)
  const approvalDryRunBoundaryCards = futureRequestBoundaryContextGroup.getByLabel('Approval dry run future request boundary cards')
  await expect(approvalDryRunBoundaryCards).toBeVisible()
  await expect(approvalDryRunBoundaryCards.locator(':scope > article')).toHaveCount(3)
  const approvalDryRunActions = localArtifactActionsContextGroup.getByLabel('Approval dry run local artifact actions')
  await expect(approvalDryRunActions).toBeVisible()
  await expect(approvalDryRunActions.getByRole('button')).toHaveText([
    'Build Local Approval Dry Run',
    'Export Dry Run Envelope',
    'Export Readiness Checkpoint',
    'Export Review Bundle',
    'Export Live Gate Preflight',
    'Clear dry run',
  ])
  await expect(approvalDryRunReadiness.getByText('Candidate source context')).toBeVisible()
  await expect(approvalDryRunReadiness.getByText(/Source freshness and warnings are checked locally/i)).toBeVisible()
  await expect(approvalDryRunReadiness.getByText(/Decision draft is return for revision/i)).toBeVisible()
  await expect(approvalDryRunReadiness.getByText(/no-go check\(s\) exist; mark admission no-go review/i)).toBeVisible()
  await expect(approvalDryRunReadiness.getByText(/The exact PM Lane 142 live-write admission phrase/i)).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Build Local Approval Dry Run' })).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Export Dry Run Envelope' })).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Export Readiness Checkpoint' })).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Export Review Bundle' })).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Export Live Gate Preflight' })).toBeVisible()
  await expect(approvalDryRun.getByRole('button', { name: 'Clear dry run' })).toBeDisabled()
  await approvalDryRun.locator(':scope > summary').click()
  await expect(approvalDryRun).not.toHaveAttribute('open', '')
  await expect(approvalDryRunBodyControls).toBeHidden()
  await expect(approvalDryRunGroups).toBeHidden()
  const approvalDryRunDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|approval-dry-run|approval-submission-dry-run/i.test(key)))
  expect(approvalDryRunDisclosureStateKeys).toEqual([])
  await approvalDryRun.locator(':scope > summary').click()
  await expect(approvalDryRun).toHaveAttribute('open', '')
  await expect(approvalDryRunGroups).toBeVisible()
  await expect(approvalDryRunReadiness).toBeVisible()
  await expect(approvalDryRunBoundaryCards).toBeVisible()
  await expect(approvalDryRunActions).toBeVisible()
  await approvalDryRun.getByRole('button', { name: 'Build Local Approval Dry Run' }).click()
  await expect(approvalDryRun.getByRole('status')).toContainText(/no network request was sent/i)
  const approvalDryRunPreview = approvalDryRun.getByTestId('local-approval-dry-run-preview')
  await expect(approvalDryRunPreview).toContainText('"dry_run_kind": "pm_import_candidate_browser_approval_dry_run"')
  await expect(approvalDryRunPreview).toContainText('"route": "/api/v1/mutations/project-import-approvals"')
  await expect(approvalDryRunPreview).toContainText('"route_not_called_by_this_screen": true')
  await expect(approvalDryRunPreview).toContainText('"live_post_performed": false')
  await expect(approvalDryRunPreview).toContainText('"approval_row_created": false')
  await expect(approvalDryRunPreview).toContainText('"decision": "return_for_revision"')
  await expect(approvalDryRunPreview).toContainText('"accepted_warning_codes"')
  await expect(approvalDryRun.getByRole('button', { name: 'Clear dry run' })).toBeEnabled()
  expect(mutationRequests).toHaveLength(0)
  const dryRunDownloadPromise = page.waitForEvent('download')
  await approvalDryRun.getByRole('button', { name: 'Export Dry Run Envelope' }).click()
  const dryRunDownload = await dryRunDownloadPromise
  expect(dryRunDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-dry-run-envelope.json')
  const dryRunStream = await dryRunDownload.createReadStream()
  expect(dryRunStream).not.toBeNull()
  const dryRunChunks: Buffer[] = []
  for await (const chunk of dryRunStream!) {
    dryRunChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const dryRunEnvelope = JSON.parse(Buffer.concat(dryRunChunks).toString('utf8'))
  expect(dryRunEnvelope).toMatchObject({
    dry_run_kind: 'pm_import_candidate_browser_approval_dry_run',
    dry_run_version: 'pm_lane_142a_local_mock_v1',
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_mock_only: true,
      live_post_performed: false,
      approval_row_created: false,
      hosted_deploy_performed: false,
    },
    intended_request: {
      method: 'POST',
      route: '/api/v1/mutations/project-import-approvals',
      route_not_called_by_this_screen: true,
      server_write_performed: false,
    },
    payload: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      decision: 'return_for_revision',
      review_notes: 'Reviewed formula warnings; return for revision until source workbook errors are resolved.',
      local_attestation: true,
      accepted_warning_codes: ['PROJECT_DATA_ENTRY_FORMULA_ERRORS'],
      approval_status_before_dry_run: {
        classification: 'no_approval_record',
        approval_record_count_for_candidate: 0,
        current_candidate_match: false,
      },
    },
    local_validation: {
      decision_draft_complete: true,
      checklist_checked_count: 2,
      checklist_checked_items: ['source_freshness_reviewed', 'exceptions_reviewed'],
      warning_acceptance_ready: true,
      no_go_acknowledgement_ready: false,
      write_guardrail_confirmed: false,
    },
  })
  expect(dryRunEnvelope.generated_locally_at).toEqual(expect.any(String))
  expect(dryRunEnvelope.blocked_boundaries).toEqual(expect.arrayContaining(['live_approval_post', 'approval_row_creation', 'project_import']))
  await expect(approvalDryRun.getByRole('status')).toContainText(/Local approval dry run envelope exported/i)
  expect(mutationRequests).toHaveLength(0)
  const readinessDownloadPromise = page.waitForEvent('download')
  await approvalDryRun.getByRole('button', { name: 'Export Readiness Checkpoint' }).click()
  const readinessDownload = await readinessDownloadPromise
  expect(readinessDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-dry-run-readiness.json')
  const readinessStream = await readinessDownload.createReadStream()
  expect(readinessStream).not.toBeNull()
  const readinessChunks: Buffer[] = []
  for await (const chunk of readinessStream!) {
    readinessChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const readinessExport = JSON.parse(Buffer.concat(readinessChunks).toString('utf8'))
  expect(readinessExport).toMatchObject({
    readiness_kind: 'pm_import_candidate_approval_dry_run_readiness',
    readiness_version: 'pm_lane_145_local_readiness_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    readiness_summary: {
      ready_count: 4,
      needs_review_count: 1,
      blocked_count: 1,
      summary: '4 ready, 1 needs review, 1 blocked',
    },
    approval_status_readback: {
      classification: 'no_approval_record',
      current_candidate_match: false,
      approval_record_count_for_candidate: 0,
      import_authority: 'not_admitted',
      route: '/api/v1/reads/project-import-approval-status',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_review_only: true,
      future_route: '/api/v1/mutations/project-import-approvals',
      project_import_authority: 'not_admitted',
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
  })
  expect(readinessExport.generated_locally_at).toEqual(expect.any(String))
  expect(readinessExport.readiness_items).toHaveLength(6)
  expect(readinessExport.readiness_items.map((item: { id: string; status: string }) => `${item.id}:${item.status}`)).toEqual([
    'candidate-source-context:ready',
    'source-warning-review:ready',
    'local-decision-draft:ready',
    'admission-no-go-review:needs_review',
    'approval-status-readback:ready',
    'live-write-authority:blocked',
  ])
  expect(readinessExport.blocked_boundaries).toEqual(expect.arrayContaining(['live_approval_post', 'approval_row_creation', 'project_import']))
  await expect(approvalDryRun.getByRole('status')).toContainText(/Local approval dry run readiness exported/i)
  expect(mutationRequests).toHaveLength(0)
  const reviewBundleDownloadPromise = page.waitForEvent('download')
  await approvalDryRun.getByRole('button', { name: 'Export Review Bundle' }).click()
  const reviewBundleDownload = await reviewBundleDownloadPromise
  expect(reviewBundleDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-review-bundle.json')
  const reviewBundleStream = await reviewBundleDownload.createReadStream()
  expect(reviewBundleStream).not.toBeNull()
  const reviewBundleChunks: Buffer[] = []
  for await (const chunk of reviewBundleStream!) {
    reviewBundleChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const reviewBundle = JSON.parse(Buffer.concat(reviewBundleChunks).toString('utf8'))
  expect(reviewBundle).toMatchObject({
    bundle_kind: 'pm_import_candidate_approval_local_review_bundle',
    bundle_version: 'pm_lane_146_local_review_bundle_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    included_artifacts: {
      dry_run_envelope_file: 'pm-import-candidate-miner-temp-power-approval-dry-run-envelope.json',
      readiness_checkpoint_file: 'pm-import-candidate-miner-temp-power-approval-dry-run-readiness.json',
      review_bundle_file: 'pm-import-candidate-miner-temp-power-approval-review-bundle.json',
    },
    dry_run_envelope: {
      dry_run_kind: 'pm_import_candidate_browser_approval_dry_run',
      dry_run_version: 'pm_lane_142a_local_mock_v1',
      payload: {
        candidate_id: 'pm-import-candidate-miner-temp-power',
        decision: 'return_for_revision',
        review_notes: 'Reviewed formula warnings; return for revision until source workbook errors are resolved.',
      },
    },
    readiness_checkpoint: {
      readiness_kind: 'pm_import_candidate_approval_dry_run_readiness',
      readiness_version: 'pm_lane_145_local_readiness_v1',
      readiness_summary: {
        ready_count: 4,
        needs_review_count: 1,
        blocked_count: 1,
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_review_only: true,
      bundle_export_only: true,
      future_route: '/api/v1/mutations/project-import-approvals',
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
    required_live_write_gate: 'I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.',
  })
  expect(reviewBundle.generated_locally_at).toEqual(expect.any(String))
  expect(reviewBundle.review_sequence).toHaveLength(4)
  expect(reviewBundle.blocked_boundaries).toEqual(expect.arrayContaining(['live_approval_post', 'approval_row_creation', 'project_import']))
  await expect(approvalDryRun.getByRole('status')).toContainText(/Local approval review bundle exported/i)
  expect(mutationRequests).toHaveLength(0)
  const preflightDownloadPromise = page.waitForEvent('download')
  await approvalDryRun.getByRole('button', { name: 'Export Live Gate Preflight' }).click()
  const preflightDownload = await preflightDownloadPromise
  expect(preflightDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-live-gate-preflight.json')
  const preflightStream = await preflightDownload.createReadStream()
  expect(preflightStream).not.toBeNull()
  const preflightChunks: Buffer[] = []
  for await (const chunk of preflightStream!) {
    preflightChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const preflight = JSON.parse(Buffer.concat(preflightChunks).toString('utf8'))
  expect(preflight).toMatchObject({
    preflight_kind: 'pm_import_candidate_approval_live_gate_preflight',
    preflight_version: 'pm_lane_147_local_live_gate_preflight_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    preflight_summary: {
      ready_count: 3,
      needs_review_count: 1,
      blocked_count: 2,
      summary: '3 ready, 1 needs review, 2 blocked',
      live_gate_status: 'blocked_until_exact_phrase',
    },
    approval_review_bundle: {
      bundle_kind: 'pm_import_candidate_approval_local_review_bundle',
      bundle_version: 'pm_lane_146_local_review_bundle_v1',
      dry_run_envelope: {
        dry_run_kind: 'pm_import_candidate_browser_approval_dry_run',
        payload: {
          candidate_id: 'pm-import-candidate-miner-temp-power',
          decision: 'return_for_revision',
        },
      },
      readiness_checkpoint: {
        readiness_version: 'pm_lane_145_local_readiness_v1',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_preflight_only: true,
      future_route: '/api/v1/mutations/project-import-approvals',
      live_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      server_write_performed: false,
    },
    required_live_write_gate: 'I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.',
  })
  expect(preflight.generated_locally_at).toEqual(expect.any(String))
  expect(preflight.preflight_items.map((item: { id: string; status: string }) => `${item.id}:${item.status}`)).toEqual([
    'candidate-identity:ready',
    'local-review-bundle:ready',
    'approval-status-readback:ready',
    'admission-no-go-posture:needs_review',
    'live-write-admission:blocked',
    'downstream-import-boundary:blocked',
  ])
  expect(preflight.blocked_boundaries).toEqual(expect.arrayContaining(['live_approval_post', 'approval_row_creation', 'project_import']))
  await expect(approvalDryRun.getByRole('status')).toContainText(/Local approval live-gate preflight exported/i)
  expect(mutationRequests).toHaveLength(0)
  const closeoutIntake = page.locator('details#executor-closeout[aria-label="Local executor closeout intake"]')
  await expect(closeoutIntake).toHaveAttribute('open', '')
  const closeoutBodyControls = closeoutIntake.locator('[aria-label="Local executor closeout intake controls"]')
  await expect(closeoutBodyControls).toBeVisible()
  const closeoutControls = closeoutBodyControls.locator('[aria-label="Executor closeout controls"]')
  await expect(closeoutControls).toBeVisible()
  const closeoutGroups = closeoutControls.locator('[aria-label="Local executor closeout intake groups"]')
  await expect(closeoutGroups).toBeVisible()
  await expect(closeoutGroups.locator(':scope > section')).toHaveCount(3)
  await expect(closeoutGroups.locator('label')).toHaveCount(8)
  const sourceHostedEvidenceGroup = closeoutGroups.locator('[aria-label="Source and Hosted Evidence executor closeout group"]')
  const validationVerdictEvidenceGroup = closeoutGroups.locator('[aria-label="Validation and Verdict Evidence executor closeout group"]')
  const guardrailsNextActionGroup = closeoutGroups.locator('[aria-label="Guardrails and Next Action executor closeout group"]')
  await expect(sourceHostedEvidenceGroup.getByRole('heading', { name: 'Source and Hosted Evidence' })).toBeVisible()
  await expect(validationVerdictEvidenceGroup.getByRole('heading', { name: 'Validation and Verdict Evidence' })).toBeVisible()
  await expect(guardrailsNextActionGroup.getByRole('heading', { name: 'Guardrails and Next Action' })).toBeVisible()
  await expect(sourceHostedEvidenceGroup.locator('[aria-label="Source and Hosted Evidence executor closeout items"] label')).toHaveCount(3)
  await expect(validationVerdictEvidenceGroup.locator('[aria-label="Validation and Verdict Evidence executor closeout items"] label')).toHaveCount(3)
  await expect(guardrailsNextActionGroup.locator('[aria-label="Guardrails and Next Action executor closeout items"] label')).toHaveCount(2)
  await expect(closeoutIntake.getByRole('heading', { name: /Local Executor Closeout Intake/i })).toBeVisible()
  await expect(closeoutIntake.getByText(/Browser-local audit prep for external executor returns/i)).toBeVisible()
  await expect(closeoutIntake.getByText(/does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await expect(closeoutIntake.getByText('0 of 8')).toBeVisible()
  await expect(closeoutIntake.getByRole('button', { name: 'Clear closeout intake' })).toBeDisabled()
  await closeoutIntake.locator(':scope > summary').click()
  await expect(closeoutIntake).not.toHaveAttribute('open', '')
  await expect(closeoutBodyControls).toBeHidden()
  await expect(closeoutControls).toBeHidden()
  await expect(closeoutGroups).toBeHidden()
  const closeoutDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|executor-closeout|closeout-intake/i.test(key)))
  expect(closeoutDisclosureStateKeys).toEqual([])
  await closeoutIntake.locator(':scope > summary').click()
  await expect(closeoutIntake).toHaveAttribute('open', '')
  await expect(closeoutBodyControls).toBeVisible()
  await expect(closeoutControls).toBeVisible()
  await expect(closeoutGroups).toBeVisible()
  await expect(closeoutGroups.locator(':scope > section')).toHaveCount(3)
  await expect(closeoutGroups.locator('label')).toHaveCount(8)
  await expect(closeoutIntake.getByText('Source commit recorded', { exact: true })).toBeVisible()
  await expect(closeoutIntake.getByText('Validation results captured', { exact: true })).toBeVisible()
  await expect(closeoutIntake.getByText('Guardrails confirmed', { exact: true })).toBeVisible()
  await closeoutIntake.getByRole('checkbox', { name: /Source commit recorded/i }).check()
  await closeoutIntake.getByRole('checkbox', { name: /Validation results captured/i }).check()
  await expect(closeoutIntake.getByText('2 of 8')).toBeVisible()
  await expect(dailyScript.getByText(/2 of 8 local closeout evidence checks are marked; 2 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  await expect(outputSelector.getByText(/Executor Handoff has 2 of 8 local closeout evidence checks marked for returned executor context/i)).toBeVisible()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 2 of 8; field questions: no; field observations: no/i)).toBeVisible()
  await expect(meetingReadout.getByText(/2 of 6 approval-persistence gates remain blocked; project import remains not admitted; executor closeout evidence is 2 of 8/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Executor closeout intake is 2 of 8; hosted read, schema, approval status, and bounded MCP proof are green while closeout checks remain audit-prep context only/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Existing Executor Handoff context has 2 of 8 local closeout evidence checks marked plus local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(workflowMap.getByText(/2 of 8 local closeout checks marked for returned executor evidence/i)).toBeVisible()
  await expect(openItems.getByText(/2 of 8 local closeout evidence checks are marked/i)).toBeVisible()
  const fieldReadiness = page.locator('details[aria-label="Local field readiness checklist"]')
  await expect(fieldReadiness).toHaveAttribute('open', '')
  await expect(fieldReadiness.getByRole('heading', { name: /Local Field Readiness Checklist/i })).toBeVisible()
  const fieldReadinessBodyControls = fieldReadiness.locator('[aria-label="Local field readiness checklist controls"]')
  await expect(fieldReadinessBodyControls).toBeVisible()
  const fieldReadinessControls = fieldReadinessBodyControls.locator('[aria-label="Field readiness controls"]')
  await expect(fieldReadinessControls).toBeVisible()
  const fieldReadinessGroups = fieldReadinessControls.locator('[aria-label="Local field readiness checklist groups"]')
  await expect(fieldReadinessGroups).toBeVisible()
  await expect(fieldReadinessGroups.locator(':scope > section')).toHaveCount(4)
  await expect(fieldReadinessGroups.locator('label')).toHaveCount(8)
  const sourceScopeReadinessGroup = fieldReadinessGroups.locator('[aria-label="Source and Scope Readiness field readiness group"]')
  const siteAccessSafetyReadinessGroup = fieldReadinessGroups.locator('[aria-label="Site Access and Safety Readiness field readiness group"]')
  const crewMaterialStagingReadinessGroup = fieldReadinessGroups.locator('[aria-label="Crew Material and Staging Readiness field readiness group"]')
  const customerAuthorityBoundaryGroup = fieldReadinessGroups.locator('[aria-label="Customer Constraints and Authority Boundary field readiness group"]')
  await expect(sourceScopeReadinessGroup.getByRole('heading', { name: 'Source and Scope Readiness' })).toBeVisible()
  await expect(siteAccessSafetyReadinessGroup.getByRole('heading', { name: 'Site Access and Safety Readiness' })).toBeVisible()
  await expect(crewMaterialStagingReadinessGroup.getByRole('heading', { name: 'Crew Material and Staging Readiness' })).toBeVisible()
  await expect(customerAuthorityBoundaryGroup.getByRole('heading', { name: 'Customer Constraints and Authority Boundary' })).toBeVisible()
  await expect(sourceScopeReadinessGroup.locator('[aria-label="Source and Scope Readiness field readiness items"] label')).toHaveCount(2)
  await expect(siteAccessSafetyReadinessGroup.locator('[aria-label="Site Access and Safety Readiness field readiness items"] label')).toHaveCount(2)
  await expect(crewMaterialStagingReadinessGroup.locator('[aria-label="Crew Material and Staging Readiness field readiness items"] label')).toHaveCount(2)
  await expect(customerAuthorityBoundaryGroup.locator('[aria-label="Customer Constraints and Authority Boundary field readiness items"] label')).toHaveCount(2)
  await expect(fieldReadiness.getByText(/Browser-local prep evidence for PM, lead, and field review conversations/i)).toBeVisible()
  await expect(fieldReadiness.getByText(/does not authorize work, approve, persist, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await expect(fieldReadiness.getByText('0 of 8')).toBeVisible()
  await expect(fieldReadiness.getByRole('button', { name: 'Clear field readiness' })).toBeDisabled()
  await fieldReadiness.locator(':scope > summary').click()
  await expect(fieldReadiness).not.toHaveAttribute('open', '')
  await expect(fieldReadinessBodyControls).toBeHidden()
  await expect(fieldReadinessControls).toBeHidden()
  await expect(fieldReadinessGroups).toBeHidden()
  const fieldReadinessDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-readiness/i.test(key)))
  expect(fieldReadinessDisclosureStateKeys).toEqual([])
  await fieldReadiness.locator(':scope > summary').click()
  await expect(fieldReadiness).toHaveAttribute('open', '')
  await expect(fieldReadinessBodyControls).toBeVisible()
  await expect(fieldReadinessControls).toBeVisible()
  await expect(fieldReadinessGroups).toBeVisible()
  await expect(fieldReadinessGroups.locator(':scope > section')).toHaveCount(4)
  await expect(fieldReadinessGroups.locator('label')).toHaveCount(8)
  await expect(fieldReadiness.getByText('Drawing and source questions captured', { exact: true })).toBeVisible()
  await expect(fieldReadiness.getByText('Safety planning questions captured', { exact: true })).toBeVisible()
  await expect(fieldReadiness.getByText('Field authority boundary acknowledged', { exact: true })).toBeVisible()
  const fieldPrepQueue = page.locator('details#field-prep[aria-label="Local field prep queue"]')
  await expect(fieldPrepQueue).toHaveAttribute('open', '')
  await expect(fieldPrepQueue.getByRole('heading', { name: /Local Field Prep Queue/i })).toBeVisible()
  const fieldPrepQueueBodyControls = fieldPrepQueue.locator('[aria-label="Local field prep queue controls"]')
  await expect(fieldPrepQueueBodyControls).toBeVisible()
  const fieldPrepQueueControls = fieldPrepQueueBodyControls.locator('[aria-label="Field prep queue controls"]')
  await expect(fieldPrepQueueControls).toBeVisible()
  const fieldPrepQueueGroups = fieldPrepQueueControls.locator('[aria-label="Local field prep queue groups"]')
  await expect(fieldPrepQueueGroups).toBeVisible()
  await expect(fieldPrepQueueGroups.locator(':scope > section')).toHaveCount(3)
  await expect(fieldPrepQueueGroups.getByRole('heading', { name: 'Field Prep Inputs' })).toBeVisible()
  await expect(fieldPrepQueueGroups.getByRole('heading', { name: 'Kickoff Artifact' })).toBeVisible()
  await expect(fieldPrepQueueGroups.getByRole('heading', { name: 'Authority And Production Boundary' })).toBeVisible()
  await expect(fieldPrepQueueGroups.locator('[aria-label="Field Prep Inputs field prep queue group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepQueueGroups.locator('[aria-label="Kickoff Artifact field prep queue group"]').locator('article')).toHaveCount(1)
  await expect(fieldPrepQueueGroups.locator('[aria-label="Authority And Production Boundary field prep queue group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepQueueControls.locator('article')).toHaveCount(5)
  await expect(fieldPrepQueue.getByText('browser-local')).toBeVisible()
  await expect(fieldPrepQueue.getByText(/Derived queue for field-prep conversations/i)).toBeVisible()
  await expect(fieldPrepQueue.getByText(/without creating tasks, issues, assignments, schedules, status updates, approval records, import rows, or production writes/i)).toBeVisible()
  await expect(fieldPrepQueue.getByText('0 complete / 1 next / 4 blocked')).toBeVisible()
  await expect(fieldPrepQueue.getByText('Capture field questions draft', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Mark field readiness prep evidence', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Export field kickoff prep brief', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Confirm field authority boundary', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Production execution tracking', { exact: true })).toBeVisible()
  await fieldPrepQueue.locator(':scope > summary').click()
  await expect(fieldPrepQueue).not.toHaveAttribute('open', '')
  await expect(fieldPrepQueueBodyControls).toBeHidden()
  const fieldPrepQueueDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-prep-queue/i.test(key)))
  expect(fieldPrepQueueDisclosureStateKeys).toEqual([])
  await fieldPrepQueue.locator(':scope > summary').click()
  await expect(fieldPrepQueue).toHaveAttribute('open', '')
  await expect(fieldPrepQueueBodyControls).toBeVisible()
  await expect(fieldPrepQueueGroups).toBeVisible()
  const fieldPrepCoverage = page.locator('details[aria-label="Local field prep coverage snapshot"]')
  await expect(fieldPrepCoverage).toHaveAttribute('open', '')
  await expect(fieldPrepCoverage.getByRole('heading', { name: /Local Field Prep Coverage Snapshot/i })).toBeVisible()
  const fieldPrepCoverageBodyControls = fieldPrepCoverage.locator('[aria-label="Local field prep coverage snapshot controls"]')
  await expect(fieldPrepCoverageBodyControls).toBeVisible()
  const fieldPrepCoverageControls = fieldPrepCoverageBodyControls.locator('[aria-label="Field prep coverage controls"]')
  await expect(fieldPrepCoverageControls).toBeVisible()
  const fieldPrepCoverageGroups = fieldPrepCoverageControls.locator('[aria-label="Local field prep coverage snapshot groups"]')
  await expect(fieldPrepCoverageGroups).toBeVisible()
  await expect(fieldPrepCoverageGroups.locator(':scope > section')).toHaveCount(3)
  await expect(fieldPrepCoverageGroups.getByRole('heading', { name: 'Source And Access Context' })).toBeVisible()
  await expect(fieldPrepCoverageGroups.getByRole('heading', { name: 'Resource And Staging Context' })).toBeVisible()
  await expect(fieldPrepCoverageGroups.getByRole('heading', { name: 'Authority And Production Boundary' })).toBeVisible()
  await expect(fieldPrepCoverageGroups.locator('[aria-label="Source And Access Context field prep coverage group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepCoverageGroups.locator('[aria-label="Resource And Staging Context field prep coverage group"]').locator('article')).toHaveCount(3)
  await expect(fieldPrepCoverageGroups.locator('[aria-label="Authority And Production Boundary field prep coverage group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepCoverageControls.locator('article')).toHaveCount(7)
  await expect(fieldPrepCoverage.getByText('derived', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText(/Browser-local coverage snapshot derived from existing local prep state/i)).toBeVisible()
  await expect(fieldPrepCoverage.getByText(/without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes/i)).toBeVisible()
  await expect(fieldPrepCoverage.getByText('0 covered, 0 partial, 5 open, 2 blocked')).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Source and drawing coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Access and safety coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Crew and equipment coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Material and staging coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Customer constraint coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Field authority boundary', { exact: true })).toBeVisible()
  await expect(fieldPrepCoverage.getByText('Production tracking boundary', { exact: true })).toBeVisible()
  await fieldPrepCoverage.locator(':scope > summary').click()
  await expect(fieldPrepCoverage).not.toHaveAttribute('open', '')
  await expect(fieldPrepCoverageBodyControls).toBeHidden()
  const fieldPrepCoverageDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-prep-coverage/i.test(key)))
  expect(fieldPrepCoverageDisclosureStateKeys).toEqual([])
  await fieldPrepCoverage.locator(':scope > summary').click()
  await expect(fieldPrepCoverage).toHaveAttribute('open', '')
  await expect(fieldPrepCoverageBodyControls).toBeVisible()
  await expect(fieldPrepCoverageGroups).toBeVisible()
  const fieldPrepAgenda = page.locator('details[aria-label="Local field prep conversation agenda"]')
  await expect(fieldPrepAgenda).toHaveAttribute('open', '')
  await expect(fieldPrepAgenda.getByRole('heading', { name: /Local Field Prep Conversation Agenda/i })).toBeVisible()
  const fieldPrepAgendaBodyControls = fieldPrepAgenda.locator('[aria-label="Local field prep conversation agenda controls"]')
  await expect(fieldPrepAgendaBodyControls).toBeVisible()
  const fieldPrepAgendaControls = fieldPrepAgendaBodyControls.locator('[aria-label="Field prep agenda controls"]')
  await expect(fieldPrepAgendaControls).toBeVisible()
  const fieldPrepAgendaGroups = fieldPrepAgendaControls.locator('[aria-label="Local field prep conversation agenda groups"]')
  await expect(fieldPrepAgendaGroups).toBeVisible()
  await expect(fieldPrepAgendaGroups.locator(':scope > section')).toHaveCount(3)
  await expect(fieldPrepAgendaGroups.getByRole('heading', { name: 'Source And Access Conversation' })).toBeVisible()
  await expect(fieldPrepAgendaGroups.getByRole('heading', { name: 'Resource And Staging Conversation' })).toBeVisible()
  await expect(fieldPrepAgendaGroups.getByRole('heading', { name: 'Authority And Production Boundary' })).toBeVisible()
  await expect(fieldPrepAgendaGroups.locator('[aria-label="Source And Access Conversation field prep agenda group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepAgendaGroups.locator('[aria-label="Resource And Staging Conversation field prep agenda group"]').locator('article')).toHaveCount(3)
  await expect(fieldPrepAgendaGroups.locator('[aria-label="Authority And Production Boundary field prep agenda group"]').locator('article')).toHaveCount(2)
  await expect(fieldPrepAgendaControls.locator('article')).toHaveCount(7)
  await expect(fieldPrepAgenda.getByText('derived', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText(/Browser-local agenda derived from the coverage snapshot/i)).toBeVisible()
  await expect(fieldPrepAgenda.getByText(/without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes/i)).toBeVisible()
  await expect(fieldPrepAgenda.getByText('0 context, 5 ask, 0 confirm, 2 blocked')).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Source and drawing coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Access and safety coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Field authority boundary conversation', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Production tracking boundary', { exact: true })).toBeVisible()
  await fieldPrepAgenda.locator(':scope > summary').click()
  await expect(fieldPrepAgenda).not.toHaveAttribute('open', '')
  await expect(fieldPrepAgendaBodyControls).toBeHidden()
  const fieldPrepAgendaDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-prep-agenda/i.test(key)))
  expect(fieldPrepAgendaDisclosureStateKeys).toEqual([])
  await fieldPrepAgenda.locator(':scope > summary').click()
  await expect(fieldPrepAgenda).toHaveAttribute('open', '')
  await expect(fieldPrepAgendaBodyControls).toBeVisible()
  await expect(fieldPrepAgendaGroups).toBeVisible()
  await fieldReadiness.getByRole('checkbox', { name: /Drawing and source questions captured/i }).check()
  await fieldReadiness.getByRole('checkbox', { name: /Safety planning questions captured/i }).check()
  await expect(fieldReadiness.getByText('2 of 8')).toBeVisible()
  const fieldQuestions = page.locator('details[aria-label="Local field questions draft"]')
  await expect(fieldQuestions).toHaveAttribute('open', '')
  await expect(fieldQuestions.getByRole('heading', { name: /Local Field Questions Draft/i })).toBeVisible()
  const fieldQuestionsBodyControls = fieldQuestions.locator('[aria-label="Local field questions draft controls"]')
  await expect(fieldQuestionsBodyControls).toBeVisible()
  const fieldQuestionsControls = fieldQuestionsBodyControls.locator('[aria-label="Field questions controls"]')
  const fieldQuestionsGroups = fieldQuestionsControls.locator('[aria-label="Local field questions draft groups"]')
  await expect(fieldQuestionsGroups).toBeVisible()
  await expect(fieldQuestionsGroups.locator('section')).toHaveCount(3)
  await expect(fieldQuestionsGroups.getByRole('heading', { name: 'Source and Site Questions' })).toBeVisible()
  await expect(fieldQuestionsGroups.getByRole('heading', { name: 'Crew Material and Staging Questions' })).toBeVisible()
  await expect(fieldQuestionsGroups.getByRole('heading', { name: 'Customer Constraints and PM Follow-up' })).toBeVisible()
  await expect(fieldQuestionsGroups.locator('[aria-label="Source and Site Questions field questions group"]').locator('label')).toHaveCount(2)
  await expect(fieldQuestionsGroups.locator('[aria-label="Crew Material and Staging Questions field questions group"]').locator('label')).toHaveCount(2)
  await expect(fieldQuestionsGroups.locator('[aria-label="Customer Constraints and PM Follow-up field questions group"]').locator('label')).toHaveCount(2)
  await expect(fieldQuestionsControls.locator('label')).toHaveCount(6)
  await expect(fieldQuestions.getByText('local only')).toBeVisible()
  await expect(fieldQuestions.getByText(/Browser-local question notes for PM, lead, and field prep conversations/i)).toBeVisible()
  await expect(fieldQuestions.getByText(/These notes do not create tasks/i)).toBeVisible()
  await expect(fieldQuestions.getByText(/production writes/i)).toBeVisible()
  await expect(fieldQuestions.getByRole('button', { name: 'Clear field questions' })).toBeDisabled()
  await fieldQuestions.locator(':scope > summary').click()
  await expect(fieldQuestions).not.toHaveAttribute('open', '')
  await expect(fieldQuestionsBodyControls).toBeHidden()
  const fieldQuestionsDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-questions/i.test(key)))
  expect(fieldQuestionsDisclosureStateKeys).toEqual([])
  await fieldQuestions.locator(':scope > summary').click()
  await expect(fieldQuestions).toHaveAttribute('open', '')
  await expect(fieldQuestionsBodyControls).toBeVisible()
  await expect(fieldQuestionsGroups).toBeVisible()
  await fieldQuestions.getByLabel(/Drawing\/source questions/i).fill('Confirm latest one-line drawings match the temp power candidate shape.')
  await fieldQuestions.getByLabel(/Site access and safety questions/i).fill('Confirm escort, access hours, and LOTO review questions before field discussion.')
  await expect(fieldQuestions.getByRole('button', { name: 'Clear field questions' })).toBeEnabled()
  await expect(startHere.getByText(/Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(startHere.getByText(/Use Export Field Prep Packet when the next conversation needs field-prep context/i)).toBeVisible()
  await expect(dailyScript.getByText(/Field prep queue: 2 complete \/ 2 next \/ 1 blocked. Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Kickoff Brief is most useful after field questions or readiness evidence are captured; current field prep queue is 2 complete \/ 2 next \/ 1 blocked/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Prep Packet is the bundled field-prep artifact when the next conversation needs questions, coverage, agenda, readiness evidence, and observation context; current field prep queue is 2 complete \/ 2 next \/ 1 blocked/i)).toBeVisible()
  await expect(commandCenter.getByText(/Field prep queue is 2 complete \/ 2 next \/ 1 blocked. Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 2 of 8; field questions: yes; field observations: no/i)).toBeVisible()
  await expect(meetingReadout.getByText(/Field prep is 2 complete \/ 2 next \/ 1 blocked. Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Field prep is 2 complete \/ 2 next \/ 1 blocked. Field questions present: yes; field observations present: no/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Field prep queue is 2 complete \/ 2 next \/ 1 blocked. Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(workflowMap.getByText(/Export field kickoff prep brief: Use the Field Kickoff Brief as local conversation prep for PM, lead, and field review/i)).toBeVisible()
  await expect(fieldPrepQueue.getByText('2 complete / 2 next / 1 blocked')).toBeVisible()
  await expect(openItems.getByText(/2 field-prep item\(s\) are next; 1 field-prep item\(s\) are blocked/i)).toBeVisible()
  const fieldObservations = page.locator('details[aria-label="Local field observation scratchpad"]')
  await expect(fieldObservations).toHaveAttribute('open', '')
  await expect(fieldObservations.getByRole('heading', { name: /Local Field Observation Scratchpad/i })).toBeVisible()
  const fieldObservationBodyControls = fieldObservations.locator('[aria-label="Local field observation scratchpad controls"]')
  await expect(fieldObservationBodyControls).toBeVisible()
  const fieldObservationControls = fieldObservationBodyControls.locator('[aria-label="Field observation scratchpad controls"]')
  const fieldObservationGroups = fieldObservationControls.locator('[aria-label="Local field observation scratchpad groups"]')
  await expect(fieldObservationGroups).toBeVisible()
  await expect(fieldObservationGroups.locator(':scope > section')).toHaveCount(3)
  await expect(fieldObservationGroups.getByRole('heading', { name: 'Source And Area Observation' })).toBeVisible()
  await expect(fieldObservationGroups.getByRole('heading', { name: 'Access And Resource Observation' })).toBeVisible()
  await expect(fieldObservationGroups.getByRole('heading', { name: 'PM Follow-up And Authority Boundary' })).toBeVisible()
  await expect(fieldObservationGroups.locator('[aria-label="Source And Area Observation field observation group"]').locator('label')).toHaveCount(3)
  await expect(fieldObservationGroups.locator('[aria-label="Access And Resource Observation field observation group"]').locator('label')).toHaveCount(2)
  await expect(fieldObservationGroups.locator('[aria-label="PM Follow-up And Authority Boundary field observation group"]').locator('label')).toHaveCount(1)
  await expect(fieldObservationControls.locator('label')).toHaveCount(6)
  await expect(fieldObservations.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(fieldObservations.getByText(/Browser-local observation notes for PM, lead, and field conversations/i)).toBeVisible()
  await expect(fieldObservations.getByText(/do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes/i)).toBeVisible()
  await fieldObservations.locator(':scope > summary').click()
  await expect(fieldObservations).not.toHaveAttribute('open', '')
  await expect(fieldObservationBodyControls).toBeHidden()
  const fieldObservationDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|field-observations/i.test(key)))
  expect(fieldObservationDisclosureStateKeys).toEqual([])
  await fieldObservations.locator(':scope > summary').click()
  await expect(fieldObservations).toHaveAttribute('open', '')
  await expect(fieldObservationBodyControls).toBeVisible()
  await expect(fieldObservationGroups).toBeVisible()
  await fieldObservations.getByLabel(/Observation date or shift note/i).fill('Day-one temp power prep conversation before field mobilization.')
  await fieldObservations.getByLabel(/Observer \/ source/i).fill('PM call with lead and customer site contact.')
  await fieldObservations.getByLabel(/Access and safety observations/i).fill('Escort and LOTO review need confirmation before field reliance.')
  await expect(fieldObservations.getByRole('button', { name: 'Clear field observations' })).toBeEnabled()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 2 of 8; field questions: yes; field observations: yes/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Field prep is 2 complete \/ 2 next \/ 1 blocked. Field questions present: yes; field observations present: yes/i)).toBeVisible()
  await expect(fieldPrepCoverage.getByText('2 covered, 0 partial, 3 open, 2 blocked')).toBeVisible()
  await expect(fieldPrepAgenda.getByText('2 context, 3 ask, 1 confirm, 1 blocked')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('4 covered, 1 open, 1 blocked', { exact: true })).toBeVisible()
  const localState = await page.evaluate(() => ({
    checklist: window.localStorage.getItem('pm-import-intake-review-checklist:pm-import-candidate-miner-temp-power'),
    draft: window.localStorage.getItem('pm-import-intake-approval-draft:pm-import-candidate-miner-temp-power'),
    closeout: window.localStorage.getItem('pm-import-intake-executor-closeout:pm-import-candidate-miner-temp-power'),
    fieldReadiness: window.localStorage.getItem('pm-import-intake-field-readiness:pm-import-candidate-miner-temp-power'),
    fieldQuestions: window.localStorage.getItem('pm-import-intake-field-questions:pm-import-candidate-miner-temp-power'),
    fieldObservations: window.localStorage.getItem('pm-import-intake-field-observations:pm-import-candidate-miner-temp-power'),
    fieldPrepCoverage: window.localStorage.getItem('pm-import-intake-field-prep-coverage:pm-import-candidate-miner-temp-power'),
    fieldPrepAgenda: window.localStorage.getItem('pm-import-intake-field-prep-agenda:pm-import-candidate-miner-temp-power'),
    fieldPrepPacket: window.localStorage.getItem('pm-import-intake-field-prep-packet:pm-import-candidate-miner-temp-power'),
    importExceptionRegister: window.localStorage.getItem('pm-import-intake-import-exception-register:pm-import-candidate-miner-temp-power'),
    pmIntakeSnapshot: window.localStorage.getItem('pm-import-intake-pm-intake-snapshot:pm-import-candidate-miner-temp-power'),
    commandCenter: window.localStorage.getItem('pm-import-intake-command-center:pm-import-candidate-miner-temp-power'),
    meetingReadout: window.localStorage.getItem('pm-import-intake-meeting-readout:pm-import-candidate-miner-temp-power'),
    constraintRadar: window.localStorage.getItem('pm-import-intake-constraint-radar:pm-import-candidate-miner-temp-power'),
    quickJumpRail: window.localStorage.getItem('pm-import-intake-quick-jump-rail:pm-import-candidate-miner-temp-power'),
    startHere: window.localStorage.getItem('pm-import-intake-start-here:pm-import-candidate-miner-temp-power'),
    dailyScript: window.localStorage.getItem('pm-import-intake-daily-review-script:pm-import-candidate-miner-temp-power'),
    outputSelector: window.localStorage.getItem('pm-import-intake-output-selector:pm-import-candidate-miner-temp-power'),
    handoffGuide: window.localStorage.getItem('pm-import-intake-handoff-guide:pm-import-candidate-miner-temp-power'),
    workflowMap: window.localStorage.getItem('pm-import-intake-workflow-map:pm-import-candidate-miner-temp-power'),
    openItems: window.localStorage.getItem('pm-import-intake-open-items:pm-import-candidate-miner-temp-power'),
  }))
  expect(localState.checklist).toContain('source_freshness_reviewed')
  expect(localState.checklist).toContain('exceptions_reviewed')
  expect(localState.draft).toContain('return_for_revision')
  expect(localState.draft).toContain('Reviewed formula warnings')
  expect(localState.closeout).toContain('source_commit_recorded')
  expect(localState.closeout).toContain('validation_results_captured')
  expect(localState.fieldReadiness).toContain('drawing_source_questions_captured')
  expect(localState.fieldReadiness).toContain('safety_planning_questions_captured')
  expect(localState.fieldQuestions).toContain('Confirm latest one-line drawings match the temp power candidate shape.')
  expect(localState.fieldQuestions).toContain('Confirm escort, access hours, and LOTO review questions before field discussion.')
  expect(localState.fieldObservations).toContain('Day-one temp power prep conversation before field mobilization.')
  expect(localState.fieldObservations).toContain('PM call with lead and customer site contact.')
  expect(localState.fieldPrepCoverage).toBeNull()
  expect(localState.fieldPrepAgenda).toBeNull()
  expect(localState.fieldPrepPacket).toBeNull()
  expect(localState.importExceptionRegister).toBeNull()
  expect(localState.pmIntakeSnapshot).toBeNull()
  expect(localState.commandCenter).toBeNull()
  expect(localState.meetingReadout).toBeNull()
  expect(localState.constraintRadar).toBeNull()
  expect(localState.quickJumpRail).toBeNull()
  expect(localState.startHere).toBeNull()
  expect(localState.dailyScript).toBeNull()
  expect(localState.outputSelector).toBeNull()
  expect(localState.handoffGuide).toBeNull()
  expect(localState.workflowMap).toBeNull()
  expect(localState.openItems).toBeNull()
  const readiness = page.locator('details#approval-readiness[aria-label="Approval persistence readiness gates"]')
  await expect(readiness).toHaveAttribute('open', '')
  await expect(readiness.getByRole('heading', { name: /Approval Persistence Readiness/i })).toBeVisible()
  const readinessBodyControls = readiness.locator('[aria-label="Approval persistence readiness body controls"]')
  await expect(readinessBodyControls).toBeVisible()
  const readinessControls = readinessBodyControls.locator('[aria-label="Approval persistence readiness controls"]')
  await expect(readinessControls).toBeVisible()
  const readinessGateGroups = readinessControls.locator('[aria-label="Approval persistence readiness gate groups"]')
  await expect(readinessGateGroups).toBeVisible()
  await expect(readinessGateGroups.locator(':scope > section')).toHaveCount(3)
  const localReviewContext = readinessGateGroups.locator('[aria-label="Local Review Context approval persistence readiness group"]')
  const hostedPersistenceSurface = readinessGateGroups.locator('[aria-label="Hosted Persistence Surface approval persistence readiness group"]')
  const blockedFutureWriteAuthority = readinessGateGroups.locator('[aria-label="Blocked Future Write Authority approval persistence readiness group"]')
  await expect(localReviewContext.getByRole('heading', { name: 'Local Review Context', exact: true })).toBeVisible()
  await expect(localReviewContext.locator('article')).toHaveCount(2)
  await expect(localReviewContext.getByText('Approval preview context', { exact: true })).toBeVisible()
  await expect(localReviewContext.getByText('Review checklist evidence', { exact: true })).toBeVisible()
  await expect(hostedPersistenceSurface.getByRole('heading', { name: 'Hosted Persistence Surface', exact: true })).toBeVisible()
  await expect(hostedPersistenceSurface.locator('article')).toHaveCount(2)
  await expect(hostedPersistenceSurface.getByText('Hosted schema gate', { exact: true })).toBeVisible()
  await expect(hostedPersistenceSurface.getByText('Hosted approval route gate', { exact: true })).toBeVisible()
  await expect(blockedFutureWriteAuthority.getByRole('heading', { name: 'Blocked Future Write Authority', exact: true })).toBeVisible()
  await expect(blockedFutureWriteAuthority.locator('article')).toHaveCount(2)
  await expect(blockedFutureWriteAuthority.getByText('Browser approval submit authority', { exact: true })).toBeVisible()
  await expect(blockedFutureWriteAuthority.getByText('Import mutation authority', { exact: true })).toBeVisible()
  await expect(readinessControls.locator('article')).toHaveCount(7)
  await expect(readiness.getByText('4 of 6 ready')).toBeVisible()
  await expect(readiness.getByRole('heading', { name: 'Approval Status Readback', exact: true })).toBeVisible()
  await expect(readiness.getByText('approval table readback')).toBeVisible()
  await expect(readiness.getByText('Approval preview context', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Review checklist evidence', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Hosted schema gate', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Hosted approval route gate', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Browser approval submit authority', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Import mutation authority', { exact: true })).toBeVisible()
  await expect(
    readiness.getByText(
      'PM Lane 138 closed the hosted schema gate with zero approval rows, and the bounded Supabase MCP read path is restored. Browser approval submission and import mutation remain blocked until later packets explicitly admit them.',
      { exact: true },
    ),
  ).toBeVisible()
  await expect(readiness.getByText(/does not approve, persist, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await readiness.locator(':scope > summary').click()
  await expect(readiness).not.toHaveAttribute('open', '')
  await expect(readinessBodyControls).toBeHidden()
  await expect(readinessControls).toBeHidden()
  await expect(readinessGateGroups).toBeHidden()
  const approvalReadinessDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|approval-readiness|persistence-readiness/i.test(key)))
  expect(approvalReadinessDisclosureStateKeys).toEqual([])
  await readiness.locator(':scope > summary').click()
  await expect(readiness).toHaveAttribute('open', '')
  await expect(readinessBodyControls).toBeVisible()
  await expect(readinessControls).toBeVisible()
  await expect(readinessGateGroups).toBeVisible()
  await expect(readinessGateGroups.locator(':scope > section')).toHaveCount(3)
  await expect(operatingQueue.getByText('3 complete / 1 next / 3 blocked')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Executor Handoff' })).toBeEnabled()
  const handoffDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Executor Handoff' }).click()
  const handoffDownload = await handoffDownloadPromise
  expect(handoffDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-executor-handoff.md')
  const handoffStream = await handoffDownload.createReadStream()
  expect(handoffStream).not.toBeNull()
  const handoffChunks: Buffer[] = []
  for await (const chunk of handoffStream!) {
    handoffChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const handoff = Buffer.concat(handoffChunks).toString('utf8')
  expect(handoff).toContain('# Project Miner Intake Executor Handoff')
  expect(handoff).toContain('Generated locally from the read-only PM intake workbench.')
  expect(handoff).toContain('grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, or mutate production state.')
  expect(handoff).toContain('## Bounded Instruction')
  expect(handoff).toContain('Do not treat this handoff as approval, persistence authority, import authority, hosted write proof, or task creation.')
  expect(handoff).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(handoff).toContain('- Candidate authority: not_admitted')
  expect(handoff).toContain('- Checklist checked: 2 of 7')
  expect(handoff).toContain('- Closeout checks: 2 of 8')
  expect(handoff).toContain('- Decision draft: return_for_revision')
  expect(handoff).toContain('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  expect(handoff).toContain('## Operating Queue')
  expect(handoff).toContain('Export review artifacts: Use the PM brief and approval preview JSON as browser-local context for the next admitted packet.')
  expect(handoff).toContain('Browser approval submission packet: A later packet must admit the browser approval control, live POST evidence, idempotent row creation, and rollback/return handling.')
  expect(handoff).toContain('Approval row creation: The approval table is empty by proof; this workbench must not create the first hosted approval row.')
  expect(handoff).toContain('Project import packet: Project, workpackage, task, and apparatus rows remain blocked until approval submission has been admitted and audited in a separate packet.')
  expect(handoff).toContain('## PM Intake Snapshot')
  expect(handoff).toContain('PM intake snapshot: 4 covered, 1 open, 1 blocked.')
  expect(handoff).toContain('Exception review snapshot: covered')
  expect(handoff).toContain('Field prep snapshot: covered')
  expect(handoff).toContain('Approval persistence boundary: blocked')
  expect(handoff).toContain('## PM Constraint Radar')
  expect(handoff).toContain('Source and review constraints: context - Source fingerprint stat-fingerprint-abc123; review checklist has 2 of 7 local checks marked; exceptions are 4 covered, 0 open, 2 blocked; local review notes are captured.')
  expect(handoff).toContain('Field-prep constraints: attention - Field prep is 2 complete / 2 next / 1 blocked. Field questions present: yes; field observations present: yes.')
  expect(handoff).toContain('Executor and hosted constraints: attention - Executor closeout intake is 2 of 8; hosted read, schema, approval status, and bounded MCP proof are green while closeout checks remain audit-prep context only.')
  expect(handoff).toContain('Future write authority constraints: blocked - 2 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench.')
  expect(handoff).toContain('## Import Exception Decision Register')
  expect(handoff).toContain('Import exception register: 4 covered, 0 open, 2 blocked.')
  expect(handoff).toContain('Source freshness evidence: covered')
  expect(handoff).toContain('Candidate warning signals: covered')
  expect(handoff).toContain('Admission no-go checks: blocked')
  expect(handoff).toContain('## Executor Closeout Intake')
  expect(handoff).toContain('This intake checklist is browser-local audit prep only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state.')
  expect(handoff).toContain('Checked closeout evidence:')
  expect(handoff).toContain('Source commit recorded: Executor return names the exact source branch and commit tested.')
  expect(handoff).toContain('Validation results captured: Executor return includes exact validation commands and exact results without summarizing failures as success.')
  expect(handoff).toContain('Open closeout evidence:')
  expect(handoff).toContain('Guardrails confirmed: Executor return confirms no widened service, DNS, auth, ingress, secret, SQL, schema, approval, import, assignment, schedule, status, or AI mutation.')
  expect(handoff).toContain('## Remaining Approval Submission Blockers')
  expect(handoff).toContain('Browser approval submit authority: No browser approval button, approval POST wiring, or live approval-row creation is admitted until a later packet owns that UI submission path.')
  expect(handoff).toContain('Import mutation authority: Project, workpackage, task, and apparatus import remain blocked until a later packet admits import after an approved approval record exists.')
  expect(handoff).toContain('## Hosted Approval Surface And Remaining Blocks')
  expect(handoff).toContain('- Hosted approval route: /api/v1/mutations/project-import-approvals')
  expect(handoff).toContain('## Not Allowed')
  expect(handoff).toContain('- write supabase')
  expect(handoff).toContain('- persist approval record')
  expect(handoff).toContain('- import project rows')
  expect(handoff).toContain('Preserve zero mutation calls for review-only work.')
  await expect(page.getByText(/Executor handoff prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  const outputStatusRail = page.getByLabel('PM intake output status rail')
  await expect(outputStatusRail).toBeVisible()
  const outputStatusDisclosure = page.locator('details[aria-label="PM intake output status rail"]')
  await expect(outputStatusDisclosure).toHaveAttribute('open', '')
  await expect(outputStatusRail.getByRole('heading', { name: 'Output Status', exact: true })).toBeVisible()
  await expect(outputStatusRail.getByLabel('PM intake output status groups')).toBeVisible()
  const executorOutputStatus = outputStatusRail.getByLabel('Executor output status')
  await expect(executorOutputStatus.getByRole('heading', { name: 'Executor Output Status', exact: true })).toBeVisible()
  await expect(executorOutputStatus.getByText(/Executor handoff prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(outputStatusRail.getByLabel('Review output status')).toHaveCount(0)
  await expect(outputStatusRail.getByLabel('Field prep output status')).toHaveCount(0)
  await outputStatusDisclosure.locator(':scope > summary').click()
  await expect(outputStatusDisclosure).not.toHaveAttribute('open', '')
  await expect(outputStatusRail.getByLabel('PM intake output status groups')).toBeHidden()
  const outputStatusDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|output-status/i.test(key)))
  expect(outputStatusDisclosureStateKeys).toEqual([])
  await outputStatusDisclosure.locator(':scope > summary').click()
  await expect(outputStatusDisclosure).toHaveAttribute('open', '')
  await expect(outputStatusRail.getByLabel('PM intake output status groups')).toBeVisible()
  await expect(outputStatusRail.getByLabel('Executor output status').getByRole('heading', { name: 'Executor Output Status', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export PM Intake Snapshot' })).toBeEnabled()
  const pmIntakeSnapshotDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export PM Intake Snapshot' }).click()
  const pmIntakeSnapshotDownload = await pmIntakeSnapshotDownloadPromise
  expect(pmIntakeSnapshotDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pm-intake-snapshot.md')
  const pmIntakeSnapshotStream = await pmIntakeSnapshotDownload.createReadStream()
  expect(pmIntakeSnapshotStream).not.toBeNull()
  const pmIntakeSnapshotChunks: Buffer[] = []
  for await (const chunk of pmIntakeSnapshotStream!) {
    pmIntakeSnapshotChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pmIntakeSnapshotExport = Buffer.concat(pmIntakeSnapshotChunks).toString('utf8')
  expect(pmIntakeSnapshotExport).toContain('# Project Miner Local PM Intake Snapshot')
  expect(pmIntakeSnapshotExport).toContain('Generated locally from the read-only PM intake workbench.')
  expect(pmIntakeSnapshotExport).toContain('browser-local review synthesis only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.')
  expect(pmIntakeSnapshotExport).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(pmIntakeSnapshotExport).toContain('- Candidate authority: not_admitted')
  expect(pmIntakeSnapshotExport).toContain('- Source freshness: stat-fingerprint-abc123')
  expect(pmIntakeSnapshotExport).toContain('## Snapshot Summary')
  expect(pmIntakeSnapshotExport).toContain('PM intake snapshot: 4 covered, 1 open, 1 blocked.')
  expect(pmIntakeSnapshotExport).toContain('Exception review snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Decision draft snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Field prep snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Next local action snapshot: open')
  expect(pmIntakeSnapshotExport).toContain('Approval persistence boundary: blocked')
  expect(pmIntakeSnapshotExport).toContain('Hosted parity boundary: covered')
  expect(pmIntakeSnapshotExport).toContain('## Hosted Approval Surface And Remaining Blocks')
  expect(pmIntakeSnapshotExport).toContain('- Hosted approval route: /api/v1/mutations/project-import-approvals')
  expect(pmIntakeSnapshotExport).toContain('## Not Allowed')
  expect(pmIntakeSnapshotExport).toContain('- write supabase')
  expect(pmIntakeSnapshotExport).toContain('- persist approval record')
  expect(pmIntakeSnapshotExport).toContain('- import project rows')
  expect(pmIntakeSnapshotExport).toContain('Use this snapshot as scan-level PM review synthesis only.')
  expect(pmIntakeSnapshotExport).toContain('Keep browser approval submission and project import blocked until a later packet explicitly admits the required write path.')
  await expect(page.getByText(/PM intake snapshot prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Import Exception Register' })).toBeEnabled()
  const exceptionRegisterDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Import Exception Register' }).click()
  const exceptionRegisterDownload = await exceptionRegisterDownloadPromise
  expect(exceptionRegisterDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-import-exception-register.md')
  const exceptionRegisterStream = await exceptionRegisterDownload.createReadStream()
  expect(exceptionRegisterStream).not.toBeNull()
  const exceptionRegisterChunks: Buffer[] = []
  for await (const chunk of exceptionRegisterStream!) {
    exceptionRegisterChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const exceptionRegisterExport = Buffer.concat(exceptionRegisterChunks).toString('utf8')
  expect(exceptionRegisterExport).toContain('# Project Miner Local Import Exception Decision Register')
  expect(exceptionRegisterExport).toContain('Generated locally from the read-only PM intake workbench.')
  expect(exceptionRegisterExport).toContain('browser-local review synthesis only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.')
  expect(exceptionRegisterExport).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(exceptionRegisterExport).toContain('- Candidate authority: not_admitted')
  expect(exceptionRegisterExport).toContain('- Source freshness: stat-fingerprint-abc123')
  expect(exceptionRegisterExport).toContain('## Register Summary')
  expect(exceptionRegisterExport).toContain('Import exception register: 4 covered, 0 open, 2 blocked.')
  expect(exceptionRegisterExport).toContain('Source freshness evidence: covered')
  expect(exceptionRegisterExport).toContain('Candidate warning signals: covered')
  expect(exceptionRegisterExport).toContain('Human decision prompts: covered')
  expect(exceptionRegisterExport).toContain('Admission no-go checks: blocked')
  expect(exceptionRegisterExport).toContain('Local decision draft evidence: covered')
  expect(exceptionRegisterExport).toContain('Future write boundary: blocked')
  expect(exceptionRegisterExport).toContain('## Warning Signals')
  expect(exceptionRegisterExport).toContain('PROJECT_DATA_ENTRY_FORMULA_ERRORS: 234 planning-workbook rows include formula errors.')
  expect(exceptionRegisterExport).toContain('## Human Decision Prompts')
  expect(exceptionRegisterExport).toContain('Does this candidate correctly represent the project, workpackages, tasks, and apparatus?')
  expect(exceptionRegisterExport).toContain('## Admission No-Go Checks')
  expect(exceptionRegisterExport).toContain('warnings reviewed by pm: needs human acceptance - 2 warning signal(s) must be reviewed.')
  expect(exceptionRegisterExport).toContain('mutation path not admitted: no go - This endpoint has no import mutation authority.')
  expect(exceptionRegisterExport).toContain('## Local Decision Draft')
  expect(exceptionRegisterExport).toContain('- Decision draft: return_for_revision')
  expect(exceptionRegisterExport).toContain('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  expect(exceptionRegisterExport).toContain('## Not Allowed')
  expect(exceptionRegisterExport).toContain('- write supabase')
  expect(exceptionRegisterExport).toContain('- persist approval record')
  expect(exceptionRegisterExport).toContain('- import project rows')
  expect(exceptionRegisterExport).toContain('Use this register as exception-review synthesis only.')
  expect(exceptionRegisterExport).toContain('Keep browser approval submission and project import blocked until a later packet explicitly admits the required write path.')
  await expect(page.getByText(/Import exception register prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  const reviewOutputStatus = outputStatusRail.getByLabel('Review output status')
  await expect(reviewOutputStatus.getByRole('heading', { name: 'Review Output Status', exact: true })).toBeVisible()
  await expect(reviewOutputStatus.getByText(/PM intake snapshot prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(reviewOutputStatus.getByText(/Import exception register prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Kickoff Brief' })).toBeEnabled()
  const fieldBriefDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Kickoff Brief' }).click()
  const fieldBriefDownload = await fieldBriefDownloadPromise
  expect(fieldBriefDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-kickoff-brief.md')
  const fieldBriefStream = await fieldBriefDownload.createReadStream()
  expect(fieldBriefStream).not.toBeNull()
  const fieldBriefChunks: Buffer[] = []
  for await (const chunk of fieldBriefStream!) {
    fieldBriefChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldBrief = Buffer.concat(fieldBriefChunks).toString('utf8')
  expect(fieldBrief).toContain('# Project Miner Field Kickoff Prep Brief')
  expect(fieldBrief).toContain('Generated locally from the read-only PM intake workbench.')
  expect(fieldBrief).toContain('field-prep context only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, or mutate production state.')
  expect(fieldBrief).toContain('Do not treat it as a work authorization, schedule, assignment, status update, hosted write proof, approval record, import packet, or task creation.')
  expect(fieldBrief).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(fieldBrief).toContain('- Candidate authority: not_admitted')
  expect(fieldBrief).toContain('- Workpackages: 7')
  expect(fieldBrief).toContain('- Tasks: 15')
  expect(fieldBrief).toContain('- Apparatus candidates: 186')
  expect(fieldBrief).toContain('## Workpackage Preview')
  expect(fieldBrief).toContain('## Field Prep Questions')
  expect(fieldBrief).toContain('Review warnings and human-decision prompts with PM before using the candidate shape for field planning.')
  expect(fieldBrief).toContain('## Local Review Evidence')
  expect(fieldBrief).toContain('- Review checklist: 2 of 7 checked')
  expect(fieldBrief).toContain('- Executor closeout intake: 2 of 8 checked')
  expect(fieldBrief).toContain('- Field readiness prep: 2 of 8 checked')
  expect(fieldBrief).toContain('- Decision draft: return_for_revision')
  expect(fieldBrief).toContain('Checked review evidence:')
  expect(fieldBrief).toContain('Source freshness reviewed: Source paths, modified times, and aggregate fingerprint were checked before relying on this candidate.')
  expect(fieldBrief).toContain('Checked executor closeout evidence:')
  expect(fieldBrief).toContain('Source commit recorded: Executor return names the exact source branch and commit tested.')
  expect(fieldBrief).toContain('Checked field readiness prep:')
  expect(fieldBrief).toContain('Drawing and source questions captured: Open drawing, estimator, or Project Data Entry source questions are captured for PM and lead review before field reliance.')
  expect(fieldBrief).toContain('Safety planning questions captured: JHA, PPE, LOTO, energization, and temp-power safety questions are captured for field discussion before any work authorization.')
  expect(fieldBrief).toContain('Open field readiness prep:')
  expect(fieldBrief).toContain('Field authority boundary acknowledged: This checklist is field-prep evidence only and does not authorize work, create tasks, assign resources, schedule work, change status, or write production state.')
  expect(fieldBrief).toContain('## Local Field Questions Draft')
  expect(fieldBrief).toContain('Draft present: yes.')
  expect(fieldBrief).toContain('This browser-local questions draft is prep context only. It does not create tasks, issues, work authorization, assignments, schedule state, status updates, approval records, import packets, or production writes.')
  expect(fieldBrief).toContain('Drawing/source questions: Confirm latest one-line drawings match the temp power candidate shape.')
  expect(fieldBrief).toContain('Site access and safety questions: Confirm escort, access hours, and LOTO review questions before field discussion.')
  expect(fieldBrief).toContain('## Local Field Observation Scratchpad')
  expect(fieldBrief).toContain('Scratchpad present: yes.')
  expect(fieldBrief).toContain('This browser-local observation scratchpad is field-prep context only. It does not create tasks, issues, work authorization, assignments, schedule state, status updates, approval records, import packets, or production writes.')
  expect(fieldBrief).toContain('Observation date or shift note: Day-one temp power prep conversation before field mobilization.')
  expect(fieldBrief).toContain('Observer / source: PM call with lead and customer site contact.')
  expect(fieldBrief).toContain('Access and safety observations: Escort and LOTO review need confirmation before field reliance.')
  expect(fieldBrief).toContain('## Local Field Prep Queue')
  expect(fieldBrief).toContain('Field prep queue: 2 complete, 2 next, 1 blocked.')
  expect(fieldBrief).toContain('Capture field questions draft: complete')
  expect(fieldBrief).toContain('Mark field readiness prep evidence: complete')
  expect(fieldBrief).toContain('Export field kickoff prep brief: next')
  expect(fieldBrief).toContain('Confirm field authority boundary: next')
  expect(fieldBrief).toContain('Production execution tracking: blocked')
  expect(fieldBrief).toContain('## Local Field Prep Coverage Snapshot')
  expect(fieldBrief).toContain('Coverage snapshot: 2 covered, 0 partial, 3 open, 2 blocked.')
  expect(fieldBrief).toContain('Source and drawing coverage: covered')
  expect(fieldBrief).toContain('Access and safety coverage: covered')
  expect(fieldBrief).toContain('Crew and equipment coverage: open')
  expect(fieldBrief).toContain('Field authority boundary: blocked')
  expect(fieldBrief).toContain('Production tracking boundary: blocked')
  expect(fieldBrief).toContain('## Local Field Prep Conversation Agenda')
  expect(fieldBrief).toContain('Conversation agenda: 2 context, 3 ask, 1 confirm, 1 blocked.')
  expect(fieldBrief).toContain('Source and drawing coverage: context')
  expect(fieldBrief).toContain('Access and safety coverage: context')
  expect(fieldBrief).toContain('Crew and equipment coverage: ask')
  expect(fieldBrief).toContain('Field authority boundary conversation: confirm')
  expect(fieldBrief).toContain('Production tracking boundary: blocked')
  expect(fieldBrief).toContain('## Hosted Approval Surface And Remaining Blocks')
  expect(fieldBrief).toContain('- Hosted approval route: /api/v1/mutations/project-import-approvals')
  expect(fieldBrief).toContain('## Not Allowed')
  expect(fieldBrief).toContain('- write supabase')
  expect(fieldBrief).toContain('- persist approval record')
  expect(fieldBrief).toContain('- import project rows')
  expect(fieldBrief).toContain('Do not create assignments, schedules, status changes, approval records, schema, SQL, or import rows from this brief.')
  expect(fieldBrief).toContain('Do not treat this local export as browser approval submission authority or hosted write evidence.')
  await expect(page.getByText(/Field kickoff prep brief prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Observation Notes' })).toBeEnabled()
  const fieldObservationDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Observation Notes' }).click()
  const fieldObservationDownload = await fieldObservationDownloadPromise
  expect(fieldObservationDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-observation-notes.md')
  const fieldObservationStream = await fieldObservationDownload.createReadStream()
  expect(fieldObservationStream).not.toBeNull()
  const fieldObservationChunks: Buffer[] = []
  for await (const chunk of fieldObservationStream!) {
    fieldObservationChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldObservationNotes = Buffer.concat(fieldObservationChunks).toString('utf8')
  expect(fieldObservationNotes).toContain('# Project Miner Local Field Observation Notes')
  expect(fieldObservationNotes).toContain('Generated locally from the read-only PM intake workbench.')
  expect(fieldObservationNotes).toContain('browser-local field-prep context only and grant no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, or mutate production state.')
  expect(fieldObservationNotes).toContain('## Field-Prep Boundary')
  expect(fieldObservationNotes).toContain('Do not treat them as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, hosted write proof, or production tracking.')
  expect(fieldObservationNotes).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(fieldObservationNotes).toContain('- Candidate authority: not_admitted')
  expect(fieldObservationNotes).toContain('## Observation Scratchpad')
  expect(fieldObservationNotes).toContain('Scratchpad present: yes.')
  expect(fieldObservationNotes).toContain('Observation date or shift note: Day-one temp power prep conversation before field mobilization.')
  expect(fieldObservationNotes).toContain('Observer / source: PM call with lead and customer site contact.')
  expect(fieldObservationNotes).toContain('Access and safety observations: Escort and LOTO review need confirmation before field reliance.')
  expect(fieldObservationNotes).toContain('## Local Field Prep Context')
  expect(fieldObservationNotes).toContain('- Field readiness prep: 2 of 8 checked')
  expect(fieldObservationNotes).toContain('- Field questions draft present: yes')
  expect(fieldObservationNotes).toContain('- Field prep queue: 2 complete, 2 next, 1 blocked')
  expect(fieldObservationNotes).toContain('Production execution tracking: blocked')
  expect(fieldObservationNotes).toContain('## Not Allowed')
  expect(fieldObservationNotes).toContain('- write supabase')
  expect(fieldObservationNotes).toContain('- persist approval record')
  expect(fieldObservationNotes).toContain('- import project rows')
  expect(fieldObservationNotes).toContain('Keep production execution tracking blocked until a later packet explicitly admits the required write path.')
  await expect(page.getByText(/Field observation notes prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Prep Coverage Snapshot' })).toBeEnabled()
  const fieldPrepCoverageDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Prep Coverage Snapshot' }).click()
  const fieldPrepCoverageDownload = await fieldPrepCoverageDownloadPromise
  expect(fieldPrepCoverageDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-prep-coverage-snapshot.md')
  const fieldPrepCoverageStream = await fieldPrepCoverageDownload.createReadStream()
  expect(fieldPrepCoverageStream).not.toBeNull()
  const fieldPrepCoverageChunks: Buffer[] = []
  for await (const chunk of fieldPrepCoverageStream!) {
    fieldPrepCoverageChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldPrepCoverageExport = Buffer.concat(fieldPrepCoverageChunks).toString('utf8')
  expect(fieldPrepCoverageExport).toContain('# Project Miner Local Field Prep Coverage Snapshot')
  expect(fieldPrepCoverageExport).toContain('Generated locally from the read-only PM intake workbench.')
  expect(fieldPrepCoverageExport).toContain('browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.')
  expect(fieldPrepCoverageExport).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(fieldPrepCoverageExport).toContain('- Candidate authority: not_admitted')
  expect(fieldPrepCoverageExport).toContain('- Workpackages: 7')
  expect(fieldPrepCoverageExport).toContain('- Tasks: 15')
  expect(fieldPrepCoverageExport).toContain('- Apparatus candidates: 186')
  expect(fieldPrepCoverageExport).toContain('## Coverage Snapshot')
  expect(fieldPrepCoverageExport).toContain('Coverage snapshot: 2 covered, 0 partial, 3 open, 2 blocked.')
  expect(fieldPrepCoverageExport).toContain('Source and drawing coverage: covered')
  expect(fieldPrepCoverageExport).toContain('Access and safety coverage: covered')
  expect(fieldPrepCoverageExport).toContain('Material and staging coverage: open')
  expect(fieldPrepCoverageExport).toContain('Production tracking boundary: blocked')
  expect(fieldPrepCoverageExport).toContain('## Field Prep Queue Summary')
  expect(fieldPrepCoverageExport).toContain('Field prep queue: 2 complete, 2 next, 1 blocked.')
  expect(fieldPrepCoverageExport).toContain('- Field observation scratchpad present: yes')
  expect(fieldPrepCoverageExport).toContain('- Production execution tracking: blocked')
  expect(fieldPrepCoverageExport).toContain('## Not Allowed')
  expect(fieldPrepCoverageExport).toContain('- write supabase')
  expect(fieldPrepCoverageExport).toContain('- persist approval record')
  expect(fieldPrepCoverageExport).toContain('- import project rows')
  expect(fieldPrepCoverageExport).toContain('Use this as conversation prep only.')
  await expect(page.getByText(/Field prep coverage snapshot prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Prep Conversation Agenda' })).toBeEnabled()
  const fieldPrepAgendaDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Prep Conversation Agenda' }).click()
  const fieldPrepAgendaDownload = await fieldPrepAgendaDownloadPromise
  expect(fieldPrepAgendaDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-prep-conversation-agenda.md')
  const fieldPrepAgendaStream = await fieldPrepAgendaDownload.createReadStream()
  expect(fieldPrepAgendaStream).not.toBeNull()
  const fieldPrepAgendaChunks: Buffer[] = []
  for await (const chunk of fieldPrepAgendaStream!) {
    fieldPrepAgendaChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldPrepAgendaExport = Buffer.concat(fieldPrepAgendaChunks).toString('utf8')
  expect(fieldPrepAgendaExport).toContain('# Project Miner Local Field Prep Conversation Agenda')
  expect(fieldPrepAgendaExport).toContain('Generated locally from the read-only PM intake workbench.')
  expect(fieldPrepAgendaExport).toContain('browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.')
  expect(fieldPrepAgendaExport).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(fieldPrepAgendaExport).toContain('- Candidate authority: not_admitted')
  expect(fieldPrepAgendaExport).toContain('## Conversation Agenda')
  expect(fieldPrepAgendaExport).toContain('Conversation agenda: 2 context, 3 ask, 1 confirm, 1 blocked.')
  expect(fieldPrepAgendaExport).toContain('Source and drawing coverage: context')
  expect(fieldPrepAgendaExport).toContain('Access and safety coverage: context')
  expect(fieldPrepAgendaExport).toContain('Material and staging coverage: ask')
  expect(fieldPrepAgendaExport).toContain('Field authority boundary conversation: confirm')
  expect(fieldPrepAgendaExport).toContain('Production tracking boundary: blocked')
  expect(fieldPrepAgendaExport).toContain('## Coverage Context')
  expect(fieldPrepAgendaExport).toContain('Coverage snapshot: 2 covered, 0 partial, 3 open, 2 blocked.')
  expect(fieldPrepAgendaExport).toContain('## Not Allowed')
  expect(fieldPrepAgendaExport).toContain('- write supabase')
  expect(fieldPrepAgendaExport).toContain('- persist approval record')
  expect(fieldPrepAgendaExport).toContain('- import project rows')
  expect(fieldPrepAgendaExport).toContain('Use this as conversation prep only.')
  await expect(page.getByText(/Field prep conversation agenda prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Prep Packet' })).toBeEnabled()
  const fieldPrepPacketDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Prep Packet' }).click()
  const fieldPrepPacketDownload = await fieldPrepPacketDownloadPromise
  expect(fieldPrepPacketDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-prep-packet.md')
  const fieldPrepPacketStream = await fieldPrepPacketDownload.createReadStream()
  expect(fieldPrepPacketStream).not.toBeNull()
  const fieldPrepPacketChunks: Buffer[] = []
  for await (const chunk of fieldPrepPacketStream!) {
    fieldPrepPacketChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldPrepPacket = Buffer.concat(fieldPrepPacketChunks).toString('utf8')
  expect(fieldPrepPacket).toContain('# Project Miner Local Field Prep Packet')
  expect(fieldPrepPacket).toContain('Generated locally from the read-only PM intake workbench.')
  expect(fieldPrepPacket).toContain('browser-local conversation prep only and grants no authority to approve, persist, import, assign, schedule, change status, create schema, run SQL, call live services, create tasks, create issues, create durable field records, write production tracking rows, or mutate production state.')
  expect(fieldPrepPacket).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(fieldPrepPacket).toContain('- Candidate authority: not_admitted')
  expect(fieldPrepPacket).toContain('- Source freshness: stat-fingerprint-abc123')
  expect(fieldPrepPacket).toContain('- Workpackages: 7')
  expect(fieldPrepPacket).toContain('- Tasks: 15')
  expect(fieldPrepPacket).toContain('- Apparatus candidates: 186')
  expect(fieldPrepPacket).toContain('## Field Prep Queue')
  expect(fieldPrepPacket).toContain('Field prep queue: 2 complete, 2 next, 1 blocked.')
  expect(fieldPrepPacket).toContain('Capture field questions draft: complete')
  expect(fieldPrepPacket).toContain('Production execution tracking: blocked')
  expect(fieldPrepPacket).toContain('## Field Prep Coverage Snapshot')
  expect(fieldPrepPacket).toContain('Coverage snapshot: 2 covered, 0 partial, 3 open, 2 blocked.')
  expect(fieldPrepPacket).toContain('Source and drawing coverage: covered')
  expect(fieldPrepPacket).toContain('Access and safety coverage: covered')
  expect(fieldPrepPacket).toContain('Production tracking boundary: blocked')
  expect(fieldPrepPacket).toContain('## Field Prep Conversation Agenda')
  expect(fieldPrepPacket).toContain('Conversation agenda: 2 context, 3 ask, 1 confirm, 1 blocked.')
  expect(fieldPrepPacket).toContain('Field authority boundary conversation: confirm')
  expect(fieldPrepPacket).toContain('## Field Readiness Evidence')
  expect(fieldPrepPacket).toContain('Field readiness checks: 2 of 8 checked.')
  expect(fieldPrepPacket).toContain('Drawing and source questions captured: Open drawing, estimator, or Project Data Entry source questions are captured for PM and lead review before field reliance.')
  expect(fieldPrepPacket).toContain('## Field Questions Draft')
  expect(fieldPrepPacket).toContain('Draft present: yes.')
  expect(fieldPrepPacket).toContain('Drawing/source questions: Confirm latest one-line drawings match the temp power candidate shape.')
  expect(fieldPrepPacket).toContain('Site access and safety questions: Confirm escort, access hours, and LOTO review questions before field discussion.')
  expect(fieldPrepPacket).toContain('## Field Observation Scratchpad')
  expect(fieldPrepPacket).toContain('Scratchpad present: yes.')
  expect(fieldPrepPacket).toContain('Observation date or shift note: Day-one temp power prep conversation before field mobilization.')
  expect(fieldPrepPacket).toContain('Observer / source: PM call with lead and customer site contact.')
  expect(fieldPrepPacket).toContain('## Review And Closeout Context')
  expect(fieldPrepPacket).toContain('- Review checklist: 2 of 7 checked')
  expect(fieldPrepPacket).toContain('- Executor closeout intake: 2 of 8 checked')
  expect(fieldPrepPacket).toContain('- Decision draft value: return_for_revision')
  expect(fieldPrepPacket).toContain('## Hosted Approval Surface And Remaining Blocks')
  expect(fieldPrepPacket).toContain('- Hosted approval route: /api/v1/mutations/project-import-approvals')
  expect(fieldPrepPacket).toContain('## Not Allowed')
  expect(fieldPrepPacket).toContain('- write supabase')
  expect(fieldPrepPacket).toContain('- persist approval record')
  expect(fieldPrepPacket).toContain('- import project rows')
  expect(fieldPrepPacket).toContain('Use this packet as conversation prep only.')
  expect(fieldPrepPacket).toContain('Keep production execution tracking blocked until a later packet explicitly admits the required write path.')
  await expect(page.getByText(/Field prep packet prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  const fieldPrepOutputStatus = outputStatusRail.getByLabel('Field prep output status')
  await expect(fieldPrepOutputStatus.getByRole('heading', { name: 'Field Prep Output Status', exact: true })).toBeVisible()
  await expect(fieldPrepOutputStatus.getByText(/Field kickoff prep brief prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(fieldPrepOutputStatus.getByText(/Field observation notes prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(fieldPrepOutputStatus.getByText(/Field prep coverage snapshot prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(fieldPrepOutputStatus.getByText(/Field prep conversation agenda prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(fieldPrepOutputStatus.getByText(/Field prep packet prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Start Preflight' })).toBeEnabled()
  const fieldStartPreflightDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Start Preflight' }).click()
  const fieldStartPreflightDownload = await fieldStartPreflightDownloadPromise
  expect(fieldStartPreflightDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-start-preflight.json')
  const fieldStartPreflightStream = await fieldStartPreflightDownload.createReadStream()
  expect(fieldStartPreflightStream).not.toBeNull()
  const fieldStartPreflightChunks: Buffer[] = []
  for await (const chunk of fieldStartPreflightStream!) {
    fieldStartPreflightChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldStartPreflight = JSON.parse(Buffer.concat(fieldStartPreflightChunks).toString('utf8'))
  expect(fieldStartPreflight).toMatchObject({
    preflight_kind: 'pm_import_candidate_field_start_preflight',
    preflight_version: 'pm_lane_148_local_field_start_preflight_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    preflight_summary: {
      ready_count: 3,
      needs_review_count: 0,
      blocked_count: 2,
      summary: '3 ready, 0 needs review, 2 blocked',
      field_start_status: 'blocked_until_field_authority_and_tracking_packet',
    },
    field_prep_queue_summary: {
      complete_count: 2,
      next_count: 2,
      blocked_count: 1,
      summary: '2 complete, 2 next, 1 blocked',
    },
    field_prep_coverage_summary: {
      covered_count: 2,
      partial_count: 0,
      open_count: 3,
      blocked_count: 2,
      summary: '2 covered, 0 partial, 3 open, 2 blocked',
    },
    field_prep_agenda_summary: {
      context_count: 2,
      ask_count: 3,
      confirm_count: 1,
      blocked_count: 1,
      summary: '2 context, 3 ask, 1 confirm, 1 blocked',
    },
    field_prep_packet_context: {
      field_prep_packet_file: 'pm-import-candidate-miner-temp-power-field-prep-packet.md',
      field_kickoff_brief_file: 'pm-import-candidate-miner-temp-power-field-kickoff-brief.md',
      field_observation_notes_file: 'pm-import-candidate-miner-temp-power-field-observation-notes.md',
      coverage_snapshot_file: 'pm-import-candidate-miner-temp-power-field-prep-coverage-snapshot.md',
      conversation_agenda_file: 'pm-import-candidate-miner-temp-power-field-prep-conversation-agenda.md',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_preflight_only: true,
      field_start_authority: 'not_admitted',
      future_approval_route: '/api/v1/mutations/project-import-approvals',
      assignment_performed: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
  })
  expect(fieldStartPreflight.generated_locally_at).toEqual(expect.any(String))
  expect(fieldStartPreflight.preflight_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'field-questions-context:ready',
    'field-readiness-evidence:ready',
    'field-observation-context:ready',
    'field-authority-boundary:blocked',
    'production-tracking-boundary:blocked',
  ])
  expect(fieldStartPreflight.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'assignment_schedule_status_writes',
    'durable_field_record_creation',
    'production_tracking_writes',
    'project_import',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Field start preflight prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Execution Gate Design' })).toBeEnabled()
  const fieldExecutionGateDesignDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Execution Gate Design' }).click()
  const fieldExecutionGateDesignDownload = await fieldExecutionGateDesignDownloadPromise
  expect(fieldExecutionGateDesignDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-execution-gate-design.json')
  const fieldExecutionGateDesignStream = await fieldExecutionGateDesignDownload.createReadStream()
  expect(fieldExecutionGateDesignStream).not.toBeNull()
  const fieldExecutionGateDesignChunks: Buffer[] = []
  for await (const chunk of fieldExecutionGateDesignStream!) {
    fieldExecutionGateDesignChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldExecutionGateDesign = JSON.parse(Buffer.concat(fieldExecutionGateDesignChunks).toString('utf8'))
  expect(fieldExecutionGateDesign).toMatchObject({
    gate_kind: 'pm_import_candidate_field_execution_gate_design',
    gate_version: 'pm_lane_149_local_field_execution_gate_design_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_start_preflight_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-field-start-preflight.json',
      ready_count: 3,
      needs_review_count: 0,
      blocked_count: 2,
      summary: '3 ready, 0 needs review, 2 blocked',
      field_start_status: 'blocked_until_field_authority_and_tracking_packet',
    },
    gate_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 6,
      summary: '1 ready, 0 needs review, 6 blocked',
      execution_gate_status: 'blocked_until_approval_import_and_field_tracking_packets',
    },
    proposed_future_routes: {
      approval_route: '/api/v1/mutations/project-import-approvals',
      project_import_route: 'not_admitted',
      lead_ops_route: '/lead-ops',
      field_tech_route: '/field-tech',
      pm_workfront_route: '/pm-review/workfront',
      durable_field_record_route: 'not_admitted',
      production_tracking_route: 'not_admitted',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_design_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_work_authorized: false,
      assignment_performed: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
  })
  expect(fieldExecutionGateDesign.generated_locally_at).toEqual(expect.any(String))
  expect(fieldExecutionGateDesign.gate_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'field-start-preflight-context:ready',
    'approval-first-row-gate:blocked',
    'project-import-gate:blocked',
    'lead-assignment-gate:blocked',
    'schedule-status-gate:blocked',
    'durable-field-record-gate:blocked',
    'production-tracking-gate:blocked',
  ])
  expect(fieldExecutionGateDesign.minimum_admission_packets.map((item: { id: string }) => item.id)).toEqual([
    'approval-first-row',
    'project-import',
    'field-authorization-and-assignment',
    'schedule-status-controls',
    'durable-field-record-and-production-tracking',
  ])
  expect(fieldExecutionGateDesign.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'assignment_schedule_status_writes',
    'durable_field_record_creation',
    'production_tracking_writes',
    'live_approval_post',
    'first_approval_row_creation',
    'lead_assignment_writes',
    'schedule_status_mutations',
    'durable_field_record_writes',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Field execution gate design prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Lead Field Assignment Draft' })).toBeEnabled()
  const leadFieldAssignmentDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Lead Field Assignment Draft' }).click()
  const leadFieldAssignmentDraftDownload = await leadFieldAssignmentDraftDownloadPromise
  expect(leadFieldAssignmentDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-lead-field-assignment-draft.json')
  const leadFieldAssignmentDraftStream = await leadFieldAssignmentDraftDownload.createReadStream()
  expect(leadFieldAssignmentDraftStream).not.toBeNull()
  const leadFieldAssignmentDraftChunks: Buffer[] = []
  for await (const chunk of leadFieldAssignmentDraftStream!) {
    leadFieldAssignmentDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const leadFieldAssignmentDraft = JSON.parse(Buffer.concat(leadFieldAssignmentDraftChunks).toString('utf8'))
  expect(leadFieldAssignmentDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_lead_field_assignment_draft',
    draft_version: 'pm_lane_150_local_lead_field_assignment_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    draft_summary: {
      ready_count: 3,
      needs_review_count: 0,
      blocked_count: 5,
      summary: '3 ready, 0 needs review, 5 blocked',
      assignment_status: 'blocked_until_import_field_authorization_and_assignment_packet',
    },
    field_start_preflight_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-field-start-preflight.json',
      ready_count: 3,
      needs_review_count: 0,
      blocked_count: 2,
      summary: '3 ready, 0 needs review, 2 blocked',
      field_start_status: 'blocked_until_field_authority_and_tracking_packet',
    },
    field_execution_gate_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-field-execution-gate-design.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 6,
      summary: '1 ready, 0 needs review, 6 blocked',
      execution_gate_status: 'blocked_until_approval_import_and_field_tracking_packets',
    },
    local_prep_context: {
      field_prep_queue_summary: '2 complete, 2 next, 1 blocked',
      field_prep_coverage_summary: '2 covered, 0 partial, 3 open, 2 blocked',
      field_prep_agenda_summary: '2 context, 3 ask, 1 confirm, 1 blocked',
      source_files: {
        field_prep_packet_file: 'pm-import-candidate-miner-temp-power-field-prep-packet.md',
        field_start_preflight_file: 'pm-import-candidate-miner-temp-power-field-start-preflight.json',
        field_execution_gate_design_file: 'pm-import-candidate-miner-temp-power-field-execution-gate-design.json',
        field_kickoff_brief_file: 'pm-import-candidate-miner-temp-power-field-kickoff-brief.md',
        field_observation_notes_file: 'pm-import-candidate-miner-temp-power-field-observation-notes.md',
        coverage_snapshot_file: 'pm-import-candidate-miner-temp-power-field-prep-coverage-snapshot.md',
        conversation_agenda_file: 'pm-import-candidate-miner-temp-power-field-prep-conversation-agenda.md',
      },
    },
    proposed_assignment_draft: {
      assignment_kind: 'lead_field_assignment',
      assigned_lead: null,
      assigned_crew: null,
      assignment_source: 'not_admitted',
      requires_pm_selection: true,
      requires_imported_workpackage_rows: true,
      requires_field_authorization_packet: true,
      requires_schedule_status_packet: true,
      requires_durable_field_record_packet: true,
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_work_authorized: false,
      lead_selected: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
  })
  expect(leadFieldAssignmentDraft.generated_locally_at).toEqual(expect.any(String))
  expect(leadFieldAssignmentDraft.assignment_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'field-context-package:ready',
    'field-questions-and-observations:ready',
    'lead-review-agenda:ready',
    'approval-before-assignment:blocked',
    'import-before-assignment:blocked',
    'field-authorization-before-work:blocked',
    'schedule-status-authority:blocked',
    'durable-record-and-production-authority:blocked',
  ])
  expect(leadFieldAssignmentDraft.proposed_handoff_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'review_local_context:ready',
    'complete_first_approval_row_gate:blocked',
    'admit_project_import_packet:blocked',
    'admit_field_authorization_and_assignment_packet:blocked',
    'admit_schedule_status_and_tracking_packets:blocked',
  ])
  expect(leadFieldAssignmentDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'assignment_schedule_status_writes',
    'durable_field_record_creation',
    'production_tracking_writes',
    'live_approval_post',
    'first_approval_row_creation',
    'lead_assignment_writes',
    'crew_assignment_writes',
    'field_authorization_write',
    'schedule_status_write',
    'durable_field_record_writes',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Lead field assignment draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Field Authorization Assignment Draft' })).toBeEnabled()
  const fieldAuthorizationAssignmentDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Field Authorization Assignment Draft' }).click()
  const fieldAuthorizationAssignmentDraftDownload = await fieldAuthorizationAssignmentDraftDownloadPromise
  expect(fieldAuthorizationAssignmentDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-field-authorization-assignment-draft.json')
  const fieldAuthorizationAssignmentDraftStream = await fieldAuthorizationAssignmentDraftDownload.createReadStream()
  expect(fieldAuthorizationAssignmentDraftStream).not.toBeNull()
  const fieldAuthorizationAssignmentDraftChunks: Buffer[] = []
  for await (const chunk of fieldAuthorizationAssignmentDraftStream!) {
    fieldAuthorizationAssignmentDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const fieldAuthorizationAssignmentDraft = JSON.parse(Buffer.concat(fieldAuthorizationAssignmentDraftChunks).toString('utf8'))
  expect(fieldAuthorizationAssignmentDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_field_authorization_assignment_admission_draft',
    draft_version: 'pm_lane_151_local_field_authorization_assignment_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    admission_draft_summary: {
      ready_count: 2,
      needs_review_count: 0,
      blocked_count: 6,
      summary: '2 ready, 0 needs review, 6 blocked',
      admission_status: 'blocked_until_approval_import_and_explicit_field_authorization_packet',
    },
    field_execution_gate_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-field-execution-gate-design.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 6,
      summary: '1 ready, 0 needs review, 6 blocked',
      execution_gate_status: 'blocked_until_approval_import_and_field_tracking_packets',
    },
    lead_field_assignment_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-lead-field-assignment-draft.json',
      ready_count: 3,
      needs_review_count: 0,
      blocked_count: 5,
      summary: '3 ready, 0 needs review, 5 blocked',
      assignment_status: 'blocked_until_import_field_authorization_and_assignment_packet',
    },
    proposed_admission_packet: {
      packet_kind: 'field_authorization_and_assignment',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import'],
      required_before: ['field_execution', 'schedule_status_mutation', 'durable_field_record', 'production_tracking'],
      proposed_routes: {
        field_authorization_route: 'not_admitted',
        lead_assignment_route: 'not_admitted',
        crew_assignment_route: 'not_admitted',
        schedule_status_route: 'not_admitted',
        durable_field_record_route: 'not_admitted',
        production_tracking_route: 'not_admitted',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_admission_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_selected: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_performed: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
  })
  expect(fieldAuthorizationAssignmentDraft.generated_locally_at).toEqual(expect.any(String))
  expect(fieldAuthorizationAssignmentDraft.admission_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'field-execution-gate-context:ready',
    'lead-field-assignment-draft-context:ready',
    'approval-first-row-prerequisite:blocked',
    'project-import-prerequisite:blocked',
    'field-authorization-contract:blocked',
    'assignment-write-contract:blocked',
    'schedule-status-prerequisite:blocked',
    'durable-record-production-prerequisite:blocked',
  ])
  expect(fieldAuthorizationAssignmentDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_approval_first_row_gate:blocked',
    'complete_project_import_gate:blocked',
    'admit_field_authorization_contract:blocked',
    'admit_assignment_write_contract:blocked',
    'keep_downstream_tracking_blocked:blocked',
  ])
  expect(fieldAuthorizationAssignmentDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'crew_assignment_writes',
    'field_authorization_write',
    'field_authorization_contract_write',
    'lead_assignment_contract_write',
    'crew_assignment_contract_write',
    'assignment_audit_write',
    'assignment_readback_route',
    'schedule_status_write',
    'durable_field_record_writes',
    'production_tracking_writes',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Field authorization assignment draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Schedule Status Controls Draft' })).toBeEnabled()
  const scheduleStatusControlsDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Schedule Status Controls Draft' }).click()
  const scheduleStatusControlsDraftDownload = await scheduleStatusControlsDraftDownloadPromise
  expect(scheduleStatusControlsDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-schedule-status-controls-draft.json')
  const scheduleStatusControlsDraftStream = await scheduleStatusControlsDraftDownload.createReadStream()
  expect(scheduleStatusControlsDraftStream).not.toBeNull()
  const scheduleStatusControlsDraftChunks: Buffer[] = []
  for await (const chunk of scheduleStatusControlsDraftStream!) {
    scheduleStatusControlsDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const scheduleStatusControlsDraft = JSON.parse(Buffer.concat(scheduleStatusControlsDraftChunks).toString('utf8'))
  expect(scheduleStatusControlsDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_schedule_status_controls_admission_draft',
    draft_version: 'pm_lane_152_local_schedule_status_controls_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    control_draft_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      control_status: 'blocked_until_field_authorization_assignment_and_schedule_status_packet',
    },
    field_authorization_assignment_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-field-authorization-assignment-draft.json',
      ready_count: 2,
      needs_review_count: 0,
      blocked_count: 6,
      summary: '2 ready, 0 needs review, 6 blocked',
      admission_status: 'blocked_until_approval_import_and_explicit_field_authorization_packet',
    },
    proposed_schedule_status_packet: {
      packet_kind: 'schedule_status_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment'],
      required_before: ['durable-field-record', 'production-tracking'],
      proposed_routes: {
        schedule_plan_route: 'not_admitted',
        status_update_route: 'not_admitted',
        schedule_readback_route: 'not_admitted',
        status_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_control_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      schedule_performed: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      server_write_performed: false,
    },
  })
  expect(scheduleStatusControlsDraft.generated_locally_at).toEqual(expect.any(String))
  expect(scheduleStatusControlsDraft.control_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'field-authorization-assignment-context:ready',
    'approval-import-field-prerequisites:blocked',
    'schedule-plan-contract:blocked',
    'status-transition-contract:blocked',
    'lead-field-review-contract:blocked',
    'audit-readback-contract:blocked',
    'durable-record-production-boundary:blocked',
    'hosted-ui-mutation-boundary:blocked',
  ])
  expect(scheduleStatusControlsDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_field_authorization_assignment_gate:blocked',
    'admit_schedule_plan_contract:blocked',
    'admit_status_transition_contract:blocked',
    'prove_hosted_readback_without_downstream_writes:blocked',
    'keep_durable_and_production_tracking_blocked:blocked',
  ])
  expect(scheduleStatusControlsDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_mutations',
    'schedule_status_write',
    'schedule_plan_contract_write',
    'status_transition_contract_write',
    'schedule_status_mutation_route',
    'schedule_status_audit_write',
    'schedule_status_readback_route',
    'hosted_schedule_status_ui_controls',
    'durable_field_record_writes',
    'production_tracking_writes',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Schedule status controls draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Durable Field Record Draft' })).toBeEnabled()
  const durableFieldRecordDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Durable Field Record Draft' }).click()
  const durableFieldRecordDraftDownload = await durableFieldRecordDraftDownloadPromise
  expect(durableFieldRecordDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-durable-field-record-draft.json')
  const durableFieldRecordDraftStream = await durableFieldRecordDraftDownload.createReadStream()
  expect(durableFieldRecordDraftStream).not.toBeNull()
  const durableFieldRecordDraftChunks: Buffer[] = []
  for await (const chunk of durableFieldRecordDraftStream!) {
    durableFieldRecordDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const durableFieldRecordDraft = JSON.parse(Buffer.concat(durableFieldRecordDraftChunks).toString('utf8'))
  expect(durableFieldRecordDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_durable_field_record_admission_draft',
    draft_version: 'pm_lane_153_local_durable_field_record_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    durable_record_draft_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 8,
      summary: '1 ready, 0 needs review, 8 blocked',
      durable_record_status: 'blocked_until_schedule_status_and_durable_field_record_packet',
    },
    schedule_status_controls_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-schedule-status-controls-draft.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      control_status: 'blocked_until_field_authorization_assignment_and_schedule_status_packet',
    },
    proposed_durable_field_record_packet: {
      packet_kind: 'durable_field_record_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls'],
      required_before: ['production-tracking', 'customer-or-billing-reporting'],
      proposed_routes: {
        field_record_create_route: 'not_admitted',
        field_record_update_route: 'not_admitted',
        field_record_readback_route: 'not_admitted',
        field_record_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_durable_record_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      customer_report_created: false,
      billing_export_created: false,
      server_write_performed: false,
    },
  })
  expect(durableFieldRecordDraft.generated_locally_at).toEqual(expect.any(String))
  expect(durableFieldRecordDraft.durable_record_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'schedule-status-controls-context:ready',
    'approval-import-field-schedule-prerequisites:blocked',
    'durable-field-record-storage-contract:blocked',
    'daily-field-record-required-fields:blocked',
    'field-evidence-attachment-contract:blocked',
    'pm-lead-review-contract:blocked',
    'audit-readback-reconciliation-contract:blocked',
    'production-tracking-boundary:blocked',
    'hosted-ui-mutation-boundary:blocked',
  ])
  expect(durableFieldRecordDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_schedule_status_controls_gate:blocked',
    'admit_durable_field_record_contract:blocked',
    'admit_field_evidence_and_review_contract:blocked',
    'prove_hosted_readback_without_production_tracking:blocked',
    'keep_production_customer_billing_and_payroll_outputs_blocked:blocked',
  ])
  expect(durableFieldRecordDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'schedule_status_mutation_route',
    'durable_field_record_writes',
    'durable_field_record_contract_write',
    'field_daily_record_write',
    'field_evidence_attachment_write',
    'durable_field_record_mutation_route',
    'durable_field_record_audit_write',
    'durable_field_record_readback_route',
    'hosted_durable_field_record_ui_controls',
    'production_tracking_writes',
    'production_tracking_contract_write',
    'production_quantity_tracking_write',
    'customer_reporting_export',
    'billing_or_payroll_export',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Durable field record draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Production Tracking Draft' })).toBeEnabled()
  const productionTrackingDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Production Tracking Draft' }).click()
  const productionTrackingDraftDownload = await productionTrackingDraftDownloadPromise
  expect(productionTrackingDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-production-tracking-draft.json')
  const productionTrackingDraftStream = await productionTrackingDraftDownload.createReadStream()
  expect(productionTrackingDraftStream).not.toBeNull()
  const productionTrackingDraftChunks: Buffer[] = []
  for await (const chunk of productionTrackingDraftStream!) {
    productionTrackingDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const productionTrackingDraft = JSON.parse(Buffer.concat(productionTrackingDraftChunks).toString('utf8'))
  expect(productionTrackingDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_production_tracking_admission_draft',
    draft_version: 'pm_lane_154_local_production_tracking_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    production_tracking_draft_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      production_tracking_status: 'blocked_until_durable_field_record_and_production_tracking_packet',
    },
    durable_field_record_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-durable-field-record-draft.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 8,
      summary: '1 ready, 0 needs review, 8 blocked',
      durable_record_status: 'blocked_until_schedule_status_and_durable_field_record_packet',
    },
    proposed_production_tracking_packet: {
      packet_kind: 'production_tracking_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record'],
      required_before: ['customer-or-billing-reporting', 'payroll-export', 'customer-facing-completion-evidence'],
      proposed_routes: {
        production_quantity_update_route: 'not_admitted',
        production_labor_update_route: 'not_admitted',
        production_apparatus_update_route: 'not_admitted',
        production_tracking_readback_route: 'not_admitted',
        production_tracking_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_production_tracking_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_report_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      server_write_performed: false,
    },
  })
  expect(productionTrackingDraft.generated_locally_at).toEqual(expect.any(String))
  expect(productionTrackingDraft.production_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'durable-field-record-context:ready',
    'approval-import-field-schedule-durable-prerequisites:blocked',
    'production-quantity-contract:blocked',
    'labor-apparatus-progress-contract:blocked',
    'pm-lead-production-review-contract:blocked',
    'audit-readback-reconciliation-contract:blocked',
    'customer-billing-payroll-boundary:blocked',
    'hosted-ui-mutation-boundary:blocked',
  ])
  expect(productionTrackingDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_durable_field_record_gate:blocked',
    'admit_production_quantity_contract:blocked',
    'admit_labor_apparatus_progress_contract:blocked',
    'prove_hosted_readback_without_customer_reporting:blocked',
    'keep_customer_billing_payroll_and_completion_outputs_blocked:blocked',
  ])
  expect(productionTrackingDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'durable_field_record_contract_write',
    'field_daily_record_write',
    'field_evidence_attachment_write',
    'durable_field_record_mutation_route',
    'durable_field_record_readback_route',
    'production_tracking_writes',
    'production_tracking_contract_write',
    'production_quantity_tracking_write',
    'production_tracking_mutation_route',
    'production_tracking_audit_write',
    'production_tracking_readback_route',
    'hosted_production_tracking_ui_controls',
    'production_labor_tracking_write',
    'production_apparatus_progress_write',
    'customer_reporting_export',
    'billing_or_payroll_export',
    'customer_completion_evidence_export',
    'payroll_export',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Production tracking draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Customer Reporting Draft' })).toBeEnabled()
  const customerReportingDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Customer Reporting Draft' }).click()
  const customerReportingDraftDownload = await customerReportingDraftDownloadPromise
  expect(customerReportingDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-customer-reporting-draft.json')
  const customerReportingDraftStream = await customerReportingDraftDownload.createReadStream()
  expect(customerReportingDraftStream).not.toBeNull()
  const customerReportingDraftChunks: Buffer[] = []
  for await (const chunk of customerReportingDraftStream!) {
    customerReportingDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const customerReportingDraft = JSON.parse(Buffer.concat(customerReportingDraftChunks).toString('utf8'))
  expect(customerReportingDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_customer_reporting_admission_draft',
    draft_version: 'pm_lane_155_local_customer_reporting_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    customer_reporting_draft_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      customer_reporting_status: 'blocked_until_production_tracking_and_customer_reporting_packet',
    },
    production_tracking_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-production-tracking-draft.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      production_tracking_status: 'blocked_until_durable_field_record_and_production_tracking_packet',
    },
    proposed_customer_reporting_packet: {
      packet_kind: 'customer_reporting_and_completion_evidence_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record', 'production-tracking'],
      required_before: ['billing-export', 'payroll-export', 'accounting-records'],
      proposed_routes: {
        customer_report_create_route: 'not_admitted',
        completion_evidence_create_route: 'not_admitted',
        customer_report_readback_route: 'not_admitted',
        customer_report_history_route: 'not_admitted',
        lead_ops_route: '/lead-ops',
        field_tech_route: '/field-tech',
        pm_workfront_route: '/pm-review/workfront',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_customer_reporting_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_reporting_route_created: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_delivery_performed: false,
      billing_export_created: false,
      payroll_export_created: false,
      server_write_performed: false,
    },
  })
  expect(customerReportingDraft.generated_locally_at).toEqual(expect.any(String))
  expect(customerReportingDraft.reporting_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'production-tracking-context:ready',
    'approval-import-field-production-prerequisites:blocked',
    'customer-report-contract:blocked',
    'completion-evidence-contract:blocked',
    'pm-customer-review-contract:blocked',
    'audit-readback-reconciliation-contract:blocked',
    'billing-payroll-boundary:blocked',
    'hosted-ui-mutation-boundary:blocked',
  ])
  expect(customerReportingDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_production_tracking_gate:blocked',
    'admit_customer_report_contract:blocked',
    'admit_completion_evidence_contract:blocked',
    'prove_hosted_readback_without_billing_or_payroll:blocked',
    'keep_billing_payroll_and_accounting_outputs_blocked:blocked',
  ])
  expect(customerReportingDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'durable_field_record_contract_write',
    'production_tracking_contract_write',
    'production_tracking_mutation_route',
    'production_tracking_readback_route',
    'customer_reporting_export',
    'customer_completion_evidence_export',
    'customer_reporting_contract_write',
    'customer_report_write',
    'customer_completion_evidence_write',
    'customer_reporting_mutation_route',
    'customer_reporting_audit_write',
    'customer_reporting_readback_route',
    'hosted_customer_reporting_ui_controls',
    'billing_or_payroll_export',
    'billing_export_contract_write',
    'payroll_export_contract_write',
    'accounting_record_write',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Customer reporting draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Financial Handoff Draft' })).toBeEnabled()
  const financialHandoffDraftDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Financial Handoff Draft' }).click()
  const financialHandoffDraftDownload = await financialHandoffDraftDownloadPromise
  expect(financialHandoffDraftDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-financial-handoff-draft.json')
  const financialHandoffDraftStream = await financialHandoffDraftDownload.createReadStream()
  expect(financialHandoffDraftStream).not.toBeNull()
  const financialHandoffDraftChunks: Buffer[] = []
  for await (const chunk of financialHandoffDraftStream!) {
    financialHandoffDraftChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const financialHandoffDraft = JSON.parse(Buffer.concat(financialHandoffDraftChunks).toString('utf8'))
  expect(financialHandoffDraft).toMatchObject({
    draft_kind: 'pm_import_candidate_financial_handoff_admission_draft',
    draft_version: 'pm_lane_156_local_financial_handoff_admission_draft_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    financial_handoff_draft_summary: {
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 8,
      summary: '1 ready, 0 needs review, 8 blocked',
      financial_handoff_status: 'blocked_until_customer_reporting_and_financial_handoff_packet',
    },
    customer_reporting_draft_summary: {
      file_name: 'pm-import-candidate-miner-temp-power-customer-reporting-draft.json',
      ready_count: 1,
      needs_review_count: 0,
      blocked_count: 7,
      summary: '1 ready, 0 needs review, 7 blocked',
      customer_reporting_status: 'blocked_until_production_tracking_and_customer_reporting_packet',
    },
    proposed_financial_handoff_packet: {
      packet_kind: 'billing_payroll_accounting_boundary_controls',
      authority_status: 'not_admitted',
      required_after: ['approval-first-row', 'project-import', 'field-authorization-and-assignment', 'schedule-status-controls', 'durable-field-record', 'production-tracking', 'customer-reporting-and-completion-evidence'],
      required_before: ['billing-export', 'payroll-export', 'invoice-creation', 'accounting-posting', 'external-finance-system-sync'],
      proposed_routes: {
        billing_export_create_route: 'not_admitted',
        payroll_export_create_route: 'not_admitted',
        invoice_record_create_route: 'not_admitted',
        accounting_record_create_route: 'not_admitted',
        financial_handoff_readback_route: 'not_admitted',
        financial_handoff_history_route: 'not_admitted',
        pm_workfront_route: '/pm-review/workfront',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_financial_handoff_draft_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      schedule_status_route_created: false,
      durable_field_record_route_created: false,
      durable_field_record_created: false,
      field_daily_record_created: false,
      production_tracking_route_created: false,
      production_tracking_performed: false,
      production_quantity_created: false,
      production_labor_created: false,
      production_apparatus_progress_created: false,
      customer_reporting_route_created: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_delivery_performed: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
  })
  expect(financialHandoffDraft.generated_locally_at).toEqual(expect.any(String))
  expect(financialHandoffDraft.financial_handoff_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'customer-reporting-context:ready',
    'approval-import-field-production-customer-prerequisites:blocked',
    'billing-export-contract:blocked',
    'payroll-export-contract:blocked',
    'invoice-accounting-boundary:blocked',
    'labor-reconciliation-boundary:blocked',
    'customer-release-boundary:blocked',
    'audit-readback-reconciliation-contract:blocked',
    'hosted-finance-mutation-boundary:blocked',
  ])
  expect(financialHandoffDraft.proposed_packet_sequence.map((item: { step: string, status: string }) => `${item.step}:${item.status}`)).toEqual([
    'complete_customer_reporting_gate:blocked',
    'admit_billing_export_contract:blocked',
    'admit_payroll_export_contract:blocked',
    'admit_invoice_accounting_boundary_contract:blocked',
    'prove_readback_without_external_finance_sync:blocked',
    'keep_external_finance_and_payroll_processing_blocked:blocked',
  ])
  expect(financialHandoffDraft.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'durable_field_record_contract_write',
    'production_tracking_contract_write',
    'customer_reporting_contract_write',
    'customer_report_write',
    'customer_completion_evidence_write',
    'billing_export_contract_write',
    'payroll_export_contract_write',
    'accounting_record_write',
    'financial_handoff_contract_write',
    'financial_handoff_mutation_route',
    'financial_handoff_audit_write',
    'financial_handoff_readback_route',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'payroll_record_write',
    'labor_reconciliation_write',
    'customer_billing_delivery',
    'finance_system_integration',
    'hosted_financial_handoff_ui_controls',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Financial handoff draft prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Pilot Launch Binder' })).toBeEnabled()
  const pilotLaunchBinderDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Pilot Launch Binder' }).click()
  const pilotLaunchBinderDownload = await pilotLaunchBinderDownloadPromise
  expect(pilotLaunchBinderDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pilot-launch-binder.json')
  const pilotLaunchBinderStream = await pilotLaunchBinderDownload.createReadStream()
  expect(pilotLaunchBinderStream).not.toBeNull()
  const pilotLaunchBinderChunks: Buffer[] = []
  for await (const chunk of pilotLaunchBinderStream!) {
    pilotLaunchBinderChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pilotLaunchBinder = JSON.parse(Buffer.concat(pilotLaunchBinderChunks).toString('utf8'))
  expect(pilotLaunchBinder).toMatchObject({
    binder_kind: 'pm_import_candidate_pilot_launch_binder',
    binder_version: 'pm_lane_157_local_pilot_launch_binder_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    field_shape: {
      workpackage_count: 7,
      task_count: 15,
      apparatus_candidate_count: 186,
      crew_count: 15,
      equipment_inventory_count: 343,
    },
    pilot_launch_binder_summary: {
      ready_count: 10,
      needs_review_count: 0,
      blocked_count: 3,
      summary: '10 ready, 0 needs review, 3 blocked',
      launch_status: 'local_binder_ready_live_writes_blocked',
    },
    source_artifact_summaries: {
      approval_live_gate_preflight: {
        live_gate_status: 'blocked_until_exact_phrase',
      },
      financial_handoff_draft: {
        financial_handoff_status: 'blocked_until_customer_reporting_and_financial_handoff_packet',
      },
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_binder_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
  })
  expect(pilotLaunchBinder.generated_locally_at).toEqual(expect.any(String))
  expect(pilotLaunchBinder.source_artifact_manifest).toHaveLength(10)
  expect(pilotLaunchBinder.source_artifact_manifest.map((item: { artifact_id: string, local_status: string }) => `${item.artifact_id}:${item.local_status}`)).toEqual([
    'approval-live-gate-preflight:ready',
    'field-start-preflight:ready',
    'field-execution-gate-design:ready',
    'lead-field-assignment-draft:ready',
    'field-authorization-assignment-draft:ready',
    'schedule-status-controls-draft:ready',
    'durable-field-record-draft:ready',
    'production-tracking-draft:ready',
    'customer-reporting-draft:ready',
    'financial-handoff-draft:ready',
  ])
  expect(pilotLaunchBinder.binder_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'approval-live-gate-preflight:ready',
    'field-start-preflight:ready',
    'field-execution-gate-design:ready',
    'lead-field-assignment-draft:ready',
    'field-authorization-assignment-draft:ready',
    'schedule-status-controls-draft:ready',
    'durable-field-record-draft:ready',
    'production-tracking-draft:ready',
    'customer-reporting-draft:ready',
    'financial-handoff-draft:ready',
    'live-approval-row-authority:blocked',
    'project-import-authority:blocked',
    'field-production-customer-finance-authority:blocked',
  ])
  expect(pilotLaunchBinder.next_packet_options.map((item: { option: string, status: string }) => `${item.option}:${item.status}`)).toEqual([
    'approval-first-row-execution-gate:blocked_until_exact_pm_lane_142_phrase',
    'project-import-mutation-design:blocked_until_approval_row_proof',
    'field-execution-write-paths:blocked_until_import_and_field_authorization_packets',
  ])
  expect(pilotLaunchBinder.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'durable_field_record_contract_write',
    'production_tracking_contract_write',
    'customer_reporting_contract_write',
    'financial_handoff_contract_write',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'accounting_record_write',
    'finance_system_integration',
    'pilot_launch_binder_server_write',
    'browser_batch_submit',
    'project_launch_write_path',
    'executor_autonomous_business_state',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Pilot launch binder prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Pilot Launch Daily Brief' })).toBeEnabled()
  const pilotLaunchDailyBriefDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Pilot Launch Daily Brief' }).click()
  const pilotLaunchDailyBriefDownload = await pilotLaunchDailyBriefDownloadPromise
  expect(pilotLaunchDailyBriefDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pilot-launch-daily-brief.json')
  const pilotLaunchDailyBriefStream = await pilotLaunchDailyBriefDownload.createReadStream()
  expect(pilotLaunchDailyBriefStream).not.toBeNull()
  const pilotLaunchDailyBriefChunks: Buffer[] = []
  for await (const chunk of pilotLaunchDailyBriefStream!) {
    pilotLaunchDailyBriefChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pilotLaunchDailyBrief = JSON.parse(Buffer.concat(pilotLaunchDailyBriefChunks).toString('utf8'))
  expect(pilotLaunchDailyBrief).toMatchObject({
    brief_kind: 'pm_import_candidate_pilot_launch_daily_brief',
    brief_version: 'pm_lane_159_local_pilot_launch_daily_brief_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    daily_brief_summary: {
      review_only_count: 2,
      blocked_count: 5,
      summary: '2 review-only, 5 blocked',
      brief_status: 'local_daily_brief_available_live_writes_blocked',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_daily_brief_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
  })
  expect(pilotLaunchDailyBrief.generated_locally_at).toEqual(expect.any(String))
  expect(pilotLaunchDailyBrief.daily_brief_items.map((item: { id: string, status: string }) => `${item.id}:${item.status}`)).toEqual([
    'approval-live-gate:blocked',
    'field-start-context-review:review_only',
    'lead-and-crew-readiness-review:review_only',
    'schedule-status-review:blocked',
    'daily-field-record-review:blocked',
    'production-customer-review:blocked',
    'financial-handoff-review:blocked',
  ])
  expect(pilotLaunchDailyBrief.source_artifact_manifest).toHaveLength(10)
  expect(pilotLaunchDailyBrief.blocked_next_packet_options.map((item: { option: string, status: string }) => `${item.option}:${item.status}`)).toEqual([
    'approval-first-row-execution-gate:blocked_until_exact_pm_lane_142_phrase',
    'project-import-mutation-design:blocked_until_approval_row_proof',
    'field-execution-write-paths:blocked_until_import_and_field_authorization_packets',
  ])
  expect(pilotLaunchDailyBrief.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'durable_field_record_contract_write',
    'production_tracking_contract_write',
    'customer_reporting_contract_write',
    'financial_handoff_contract_write',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'accounting_record_write',
    'finance_system_integration',
    'pilot_launch_daily_brief_server_write',
    'daily_brief_business_state_write',
    'field_daily_plan_write',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Pilot launch daily brief prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Pilot Launch Standup Card' })).toBeEnabled()
  const pilotLaunchStandupCardDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Pilot Launch Standup Card' }).click()
  const pilotLaunchStandupCardDownload = await pilotLaunchStandupCardDownloadPromise
  expect(pilotLaunchStandupCardDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pilot-launch-standup-card.json')
  const pilotLaunchStandupCardStream = await pilotLaunchStandupCardDownload.createReadStream()
  expect(pilotLaunchStandupCardStream).not.toBeNull()
  const pilotLaunchStandupCardChunks: Buffer[] = []
  for await (const chunk of pilotLaunchStandupCardStream!) {
    pilotLaunchStandupCardChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pilotLaunchStandupCard = JSON.parse(Buffer.concat(pilotLaunchStandupCardChunks).toString('utf8'))
  expect(pilotLaunchStandupCard).toMatchObject({
    standup_card_kind: 'pm_import_candidate_pilot_launch_standup_card',
    standup_card_version: 'pm_lane_160_local_pilot_launch_standup_card_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    source_daily_brief: {
      file_name: 'pm-import-candidate-miner-temp-power-pilot-launch-daily-brief.json',
      brief_kind: 'pm_import_candidate_pilot_launch_daily_brief',
      brief_version: 'pm_lane_159_local_pilot_launch_daily_brief_v1',
      brief_status: 'local_daily_brief_available_live_writes_blocked',
      summary: '2 review-only, 5 blocked',
    },
    launch_day_summary: {
      role_card_count: 4,
      capture_prompt_count: 3,
      no_go_count: 4,
      card_status: 'local_standup_card_available_live_writes_blocked',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_standup_card_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      server_write_performed: false,
    },
  })
  expect(pilotLaunchStandupCard.generated_locally_at).toEqual(expect.any(String))
  expect(pilotLaunchStandupCard.source_artifact_manifest).toHaveLength(10)
  expect(pilotLaunchStandupCard.standup_sequence).toHaveLength(4)
  expect(pilotLaunchStandupCard.role_cards.map((item: { role_id: string, status: string }) => `${item.role_id}:${item.status}`)).toEqual([
    'pm:lead_conversation_only',
    'field_lead:context_review_only',
    'customer_or_site_contact:expectation_alignment_only',
    'executor_ai_relay:evidence_collection_only',
  ])
  expect(pilotLaunchStandupCard.no_go_checks.map((item: { check_id: string, status: string }) => `${item.check_id}:${item.status}`)).toEqual([
    'approval-live-write-not-admitted:no_go',
    'project-import-not-admitted:no_go',
    'field-direction-not-admitted:no_go',
    'customer-finance-output-not-admitted:no_go',
  ])
  expect(pilotLaunchStandupCard.capture_prompts.map((item: { prompt_id: string, capture_mode: string }) => `${item.prompt_id}:${item.capture_mode}`)).toEqual([
    'open-decisions:local_prompt_only',
    'field-start-blockers:local_prompt_only',
    'next-packet-selection:local_prompt_only',
  ])
  expect(pilotLaunchStandupCard.next_packet_options.map((item: { option: string, status: string }) => `${item.option}:${item.status}`)).toEqual([
    'approval-first-row-execution-gate:blocked_until_exact_pm_lane_142_phrase',
    'project-import-mutation-design:blocked_until_approval_row_proof',
    'field-execution-write-paths:blocked_until_import_and_field_authorization_packets',
  ])
  expect(pilotLaunchStandupCard.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'customer_reporting_contract_write',
    'financial_handoff_contract_write',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'accounting_record_write',
    'finance_system_integration',
    'pilot_launch_standup_card_server_write',
    'standup_card_business_state_write',
    'meeting_action_item_write',
    'field_direction_write',
    'customer_commitment_write',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Pilot launch standup card prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Pilot Launch Capture Sheet' })).toBeEnabled()
  const pilotLaunchCaptureSheetDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Pilot Launch Capture Sheet' }).click()
  const pilotLaunchCaptureSheetDownload = await pilotLaunchCaptureSheetDownloadPromise
  expect(pilotLaunchCaptureSheetDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pilot-launch-capture-sheet.json')
  const pilotLaunchCaptureSheetStream = await pilotLaunchCaptureSheetDownload.createReadStream()
  expect(pilotLaunchCaptureSheetStream).not.toBeNull()
  const pilotLaunchCaptureSheetChunks: Buffer[] = []
  for await (const chunk of pilotLaunchCaptureSheetStream!) {
    pilotLaunchCaptureSheetChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pilotLaunchCaptureSheet = JSON.parse(Buffer.concat(pilotLaunchCaptureSheetChunks).toString('utf8'))
  expect(pilotLaunchCaptureSheet).toMatchObject({
    capture_sheet_kind: 'pm_import_candidate_pilot_launch_capture_sheet',
    capture_sheet_version: 'pm_lane_161_local_pilot_launch_capture_sheet_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    source_standup_card: {
      file_name: 'pm-import-candidate-miner-temp-power-pilot-launch-standup-card.json',
      standup_card_kind: 'pm_import_candidate_pilot_launch_standup_card',
      standup_card_version: 'pm_lane_160_local_pilot_launch_standup_card_v1',
      card_status: 'local_standup_card_available_live_writes_blocked',
      capture_prompt_count: 3,
      no_go_count: 4,
    },
    capture_sheet_summary: {
      section_count: 5,
      handoff_rule_count: 4,
      no_go_count: 4,
      sheet_status: 'local_capture_sheet_available_live_writes_blocked',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      local_pilot_launch_capture_sheet_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_commitment_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      meeting_note_persisted: false,
      owner_assignment_created: false,
      server_write_performed: false,
    },
  })
  expect(pilotLaunchCaptureSheet.generated_locally_at).toEqual(expect.any(String))
  expect(pilotLaunchCaptureSheet.source_artifact_manifest).toHaveLength(10)
  expect(pilotLaunchCaptureSheet.capture_sections.map((item: { section_id: string, capture_mode: string, captured_value: string | null }) => `${item.section_id}:${item.capture_mode}:${item.captured_value === null ? 'blank' : 'filled'}`)).toEqual([
    'pm-decisions-to-review:local_prompt_only:blank',
    'field-start-blockers:local_prompt_only:blank',
    'customer-site-questions:local_prompt_only:blank',
    'executor-ai-relay-followup:local_prompt_only:blank',
    'next-packet-recommendation:local_prompt_only:blank',
  ])
  expect(pilotLaunchCaptureSheet.handoff_rules).toHaveLength(4)
  expect(pilotLaunchCaptureSheet.inherited_no_go_checks.map((item: { check_id: string, status: string }) => `${item.check_id}:${item.status}`)).toEqual([
    'approval-live-write-not-admitted:no_go',
    'project-import-not-admitted:no_go',
    'field-direction-not-admitted:no_go',
    'customer-finance-output-not-admitted:no_go',
  ])
  expect(pilotLaunchCaptureSheet.next_packet_options.map((item: { option: string, status: string }) => `${item.option}:${item.status}`)).toEqual([
    'approval-first-row-execution-gate:blocked_until_exact_pm_lane_142_phrase',
    'project-import-mutation-design:blocked_until_approval_row_proof',
    'field-execution-write-paths:blocked_until_import_and_field_authorization_packets',
  ])
  expect(pilotLaunchCaptureSheet.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'customer_reporting_contract_write',
    'financial_handoff_contract_write',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'accounting_record_write',
    'finance_system_integration',
    'pilot_launch_standup_card_server_write',
    'standup_card_business_state_write',
    'meeting_action_item_write',
    'pilot_launch_capture_sheet_server_write',
    'capture_sheet_business_state_write',
    'meeting_note_persistence',
    'owner_assignment_write',
    'field_direction_write',
    'customer_commitment_write',
  ]))
  await expect(fieldPrepOutputStatus.getByText(/Pilot launch capture sheet prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export Pilot Launch Follow-Up Packet' })).toBeEnabled()
  const pilotLaunchFollowupPacketDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Pilot Launch Follow-Up Packet' }).click()
  const pilotLaunchFollowupPacketDownload = await pilotLaunchFollowupPacketDownloadPromise
  expect(pilotLaunchFollowupPacketDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-pilot-launch-follow-up-packet.json')
  const pilotLaunchFollowupPacketStream = await pilotLaunchFollowupPacketDownload.createReadStream()
  expect(pilotLaunchFollowupPacketStream).not.toBeNull()
  const pilotLaunchFollowupPacketChunks: Buffer[] = []
  for await (const chunk of pilotLaunchFollowupPacketStream!) {
    pilotLaunchFollowupPacketChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const pilotLaunchFollowupPacket = JSON.parse(Buffer.concat(pilotLaunchFollowupPacketChunks).toString('utf8'))
  expect(pilotLaunchFollowupPacket).toMatchObject({
    follow_up_packet_kind: 'pm_import_candidate_pilot_launch_follow_up_packet',
    follow_up_packet_version: 'pm_lane_162_local_pilot_launch_follow_up_packet_v1',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      candidate_version: 'pm_import_candidate_read_only_v1',
      project_name: 'Miner Temp Power',
      source_fingerprint: 'stat-fingerprint-abc123',
    },
    source_capture_sheet: {
      file_name: 'pm-import-candidate-miner-temp-power-pilot-launch-capture-sheet.json',
      capture_sheet_kind: 'pm_import_candidate_pilot_launch_capture_sheet',
      capture_sheet_version: 'pm_lane_161_local_pilot_launch_capture_sheet_v1',
      sheet_status: 'local_capture_sheet_available_live_writes_blocked',
      section_count: 5,
    },
    follow_up_summary: {
      review_return_section_count: 5,
      orchestration_review_slot_count: 3,
      inherited_no_go_count: 4,
      packet_status: 'local_follow_up_packet_available_live_writes_blocked',
    },
    authority_boundary: {
      mutation_authority: 'not_admitted',
      persistence_authority: 'not_admitted',
      local_pilot_launch_follow_up_packet_only: true,
      copy_paste_review_return_only: true,
      live_approval_post_performed: false,
      approval_row_created: false,
      project_import_performed: false,
      field_authorization_created: false,
      field_work_authorized: false,
      lead_assignment_created: false,
      crew_assignment_created: false,
      owner_assignment_created: false,
      schedule_plan_created: false,
      status_change_performed: false,
      durable_field_record_created: false,
      production_tracking_performed: false,
      customer_report_created: false,
      customer_completion_evidence_created: false,
      customer_commitment_created: false,
      financial_handoff_route_created: false,
      billing_export_created: false,
      payroll_export_created: false,
      invoice_record_created: false,
      accounting_record_created: false,
      external_finance_sync_created: false,
      meeting_note_persisted: false,
      action_item_persisted: false,
      review_return_persisted: false,
      executor_assignment_created: false,
      due_date_assignment_created: false,
      hosted_service_mutated: false,
      server_write_performed: false,
    },
  })
  expect(pilotLaunchFollowupPacket.generated_locally_at).toEqual(expect.any(String))
  expect(pilotLaunchFollowupPacket.source_artifact_manifest).toHaveLength(10)
  expect(pilotLaunchFollowupPacket.review_return_sections.map((item: { section_id: string, return_mode: string, returned_value: string | null }) => `${item.section_id}:${item.return_mode}:${item.returned_value === null ? 'blank' : 'filled'}`)).toEqual([
    'decisions-to-return:copy_paste_review_only:blank',
    'blockers-to-return:copy_paste_review_only:blank',
    'customer-site-questions-to-return:copy_paste_review_only:blank',
    'executor-ai-relay-to-return:copy_paste_review_only:blank',
    'next-packet-recommendation-to-return:copy_paste_review_only:blank',
  ])
  expect(pilotLaunchFollowupPacket.orchestration_review_slots.map((item: { slot_id: string, slot_status: string }) => `${item.slot_id}:${item.slot_status}`)).toEqual([
    'vs-code-codex-review:review_context_only',
    'desktop-codex-closeout-review:review_context_only',
    'sidecar-scout-review:review_context_only',
  ])
  expect(pilotLaunchFollowupPacket.review_return_rules).toHaveLength(6)
  expect(pilotLaunchFollowupPacket.inherited_no_go_checks.map((item: { check_id: string, status: string }) => `${item.check_id}:${item.status}`)).toEqual([
    'approval-live-write-not-admitted:no_go',
    'project-import-not-admitted:no_go',
    'field-direction-not-admitted:no_go',
    'customer-finance-output-not-admitted:no_go',
  ])
  expect(pilotLaunchFollowupPacket.next_packet_options.map((item: { option: string, status: string }) => `${item.option}:${item.status}`)).toEqual([
    'approval-first-row-execution-gate:blocked_until_exact_pm_lane_142_phrase',
    'project-import-mutation-design:blocked_until_approval_row_proof',
    'field-execution-write-paths:blocked_until_import_and_field_authorization_packets',
  ])
  expect(pilotLaunchFollowupPacket.blocked_boundaries).toEqual(expect.arrayContaining([
    'write_supabase',
    'persist_approval_record',
    'import_project_rows',
    'field_work_authorization',
    'lead_assignment_writes',
    'schedule_status_write',
    'customer_reporting_contract_write',
    'financial_handoff_contract_write',
    'billing_export_write',
    'payroll_export_write',
    'invoice_record_write',
    'accounting_record_write',
    'finance_system_integration',
    'pilot_launch_capture_sheet_server_write',
    'capture_sheet_business_state_write',
    'pilot_launch_follow_up_packet_server_write',
    'follow_up_packet_business_state_write',
    'copy_paste_packet_submission',
    'review_return_persistence',
    'meeting_note_persistence',
    'action_item_persistence',
    'owner_assignment_write',
    'due_date_assignment_write',
    'field_direction_write',
    'customer_commitment_write',
    'executor_delegation_write',
    'desktop_codex_output_publication',
    'hosted_service_mutation',
  ]))
  const followupPacketStorageKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => /follow.?up.?packet/i.test(key)))
  expect(followupPacketStorageKeys).toEqual([])
  await expect(fieldPrepOutputStatus.getByText(/Pilot launch follow-up packet prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  expect(mutationRequests).toHaveLength(0)
  await expect(page.getByRole('button', { name: 'Export Approval Preview JSON' })).toBeEnabled()
  const previewDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export Approval Preview JSON' }).click()
  const previewDownload = await previewDownloadPromise
  expect(previewDownload.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-approval-packet-preview.json')
  const previewStream = await previewDownload.createReadStream()
  expect(previewStream).not.toBeNull()
  const previewChunks: Buffer[] = []
  for await (const chunk of previewStream!) {
    previewChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const preview = JSON.parse(Buffer.concat(previewChunks).toString('utf8'))
  expect(preview).toMatchObject({
    preview_kind: 'pm_import_candidate_approval_packet_preview',
    preview_version: 'pm_import_candidate_approval_packet_preview_v1',
    mutation_authority: 'not_admitted',
    persistence_authority: 'design_only_not_admitted',
    candidate_identity: {
      candidate_id: 'pm-import-candidate-miner-temp-power',
      source_fingerprint: 'stat-fingerprint-abc123',
      warning_count: 2,
      blocker_count: 0,
    },
    approval_contract: {
      record_type: 'pm_import_candidate_approval',
      permitted_decisions: ['approve_for_import_packet', 'return_for_revision', 'reject_candidate'],
    },
    storage_plan: {
      recommended_table: 'seam.pm_import_candidate_approvals',
      recommended_route: '/api/v1/mutations/project-import-approvals',
    },
    local_review_evidence: {
      checklist_checked_count: 2,
      checklist_total_count: 7,
      checklist_checked_items: ['source_freshness_reviewed', 'exceptions_reviewed'],
      decision_draft: {
        decision: 'return_for_revision',
        review_notes: 'Reviewed formula warnings; return for revision until source workbook errors are resolved.',
        local_attestation: true,
        draft_complete: true,
      },
    },
    future_packet_boundary: {
      target_route: '/api/v1/mutations/project-import-approvals',
      target_table: 'seam.pm_import_candidate_approvals',
      not_allowed_now: expect.arrayContaining(['write_supabase', 'persist_approval_record', 'import_project_rows']),
    },
  })
  expect(preview.generated_locally_at).toEqual(expect.any(String))
  await expect(page.getByText(/Approval packet preview prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export PM Brief' })).toBeEnabled()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export PM Brief' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('pm-import-candidate-miner-temp-power-intake-brief.md')
  const stream = await download.createReadStream()
  expect(stream).not.toBeNull()
  const chunks: Buffer[] = []
  for await (const chunk of stream!) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  const brief = Buffer.concat(chunks).toString('utf8')
  expect(brief).toContain('# Project Miner PM Intake Brief')
  expect(brief).toContain('Generated locally from the read-only PM intake workbench.')
  expect(brief).toContain('This brief is not approval, persistence, import, assignment, schedule, status, or production state.')
  expect(brief).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(brief).toContain('- Candidate authority: not_admitted')
  expect(brief).toContain('- Source freshness: stat-fingerprint-abc123')
  expect(brief).toContain('PROJECT_DATA_ENTRY_FORMULA_ERRORS')
  expect(brief).toContain('- Hosted approval route: /api/v1/mutations/project-import-approvals')
  expect(brief).toContain('## Not Allowed Now')
  expect(brief).toContain('- write supabase')
  expect(brief).toContain('- persist approval record')
  expect(brief).toContain('- import project rows')
  expect(brief).toContain('## Local Review Checklist')
  expect(brief).toContain('Checklist progress: 2 of 7 checked.')
  for (const line of [
    '[x] Source freshness reviewed',
    '[x] Warnings reviewed',
    '[ ] PM decisions captured',
    '[ ] Admission no-go checks reviewed',
    '[ ] Approval storage understood',
    '[ ] Hosted parity acknowledged',
    '[ ] Write guardrails confirmed',
  ]) {
    expect(brief).toContain(line)
  }
  expect(brief).toContain('## Local Approval Decision Draft')
  expect(brief).toContain('Draft present: yes.')
  expect(brief).toContain('- Decision draft: return_for_revision')
  expect(brief).toContain('- Local-only attestation checked: yes')
  expect(brief).toContain('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  expect(brief).toContain('## Approval Persistence Readiness')
  expect(brief).toContain('Readiness gates ready: 4 of 6.')
  expect(brief).toContain('Approval preview context: ready')
  expect(brief).toContain('Review checklist evidence: ready')
  expect(brief).toContain('Hosted schema gate: ready')
  expect(brief).toContain('Hosted approval route gate: ready')
  expect(brief).toContain('Browser approval submit authority: blocked')
  expect(brief).toContain('Import mutation authority: blocked')
  expect(brief).toContain('## PM Operating Queue')
  expect(brief).toContain('Queue status: 3 complete, 1 next, 3 blocked.')
  expect(brief).toContain('Review source and exceptions: complete')
  expect(brief).toContain('Prepare local decision draft: complete')
  expect(brief).toContain('Export review artifacts: next')
  expect(brief).toContain('Hosted approval gate complete: complete')
  expect(brief).toContain('Browser approval submission packet: blocked')
  expect(brief).toContain('Approval row creation: blocked')
  expect(brief).toContain('Project import packet: blocked')
  expect(brief).toContain('## Local PM Intake Snapshot')
  expect(brief).toContain('PM intake snapshot: 4 covered, 1 open, 1 blocked.')
  expect(brief).toContain('Exception review snapshot: covered')
  expect(brief).toContain('Next local action snapshot: open')
  expect(brief).toContain('Hosted parity boundary: covered')
  expect(brief).toContain('## Local PM Constraint Radar')
  expect(brief).toContain('Source and review constraints: context - Source fingerprint stat-fingerprint-abc123; review checklist has 2 of 7 local checks marked; exceptions are 4 covered, 0 open, 2 blocked; local review notes are captured.')
  expect(brief).toContain('Field-prep constraints: attention - Field prep is 2 complete / 2 next / 1 blocked. Field questions present: yes; field observations present: yes.')
  expect(brief).toContain('Executor and hosted constraints: attention - Executor closeout intake is 2 of 8; hosted read, schema, approval status, and bounded MCP proof are green while closeout checks remain audit-prep context only.')
  expect(brief).toContain('Future write authority constraints: blocked - 2 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench.')
  expect(brief).toContain('## Local Import Exception Decision Register')
  expect(brief).toContain('Import exception register: 4 covered, 0 open, 2 blocked.')
  expect(brief).toContain('Candidate warning signals: covered')
  expect(brief).toContain('Admission no-go checks: blocked')
  expect(brief).toContain('## Local Field Prep Queue')
  expect(brief).toContain('Field prep queue: 2 complete, 2 next, 1 blocked.')
  expect(brief).toContain('Capture field questions draft: complete')
  expect(brief).toContain('Export field kickoff prep brief: next')
  expect(brief).toContain('Production execution tracking: blocked')
  expect(brief).toContain('## Local Field Prep Coverage Snapshot')
  expect(brief).toContain('Coverage snapshot: 2 covered, 0 partial, 3 open, 2 blocked.')
  expect(brief).toContain('Source and drawing coverage: covered')
  expect(brief).toContain('Access and safety coverage: covered')
  expect(brief).toContain('Crew and equipment coverage: open')
  expect(brief).toContain('Field authority boundary: blocked')
  expect(brief).toContain('Production tracking boundary: blocked')
  expect(brief).toContain('## Local Field Prep Conversation Agenda')
  expect(brief).toContain('Conversation agenda: 2 context, 3 ask, 1 confirm, 1 blocked.')
  expect(brief).toContain('Source and drawing coverage: context')
  expect(brief).toContain('Access and safety coverage: context')
  expect(brief).toContain('Crew and equipment coverage: ask')
  expect(brief).toContain('Field authority boundary conversation: confirm')
  expect(brief).toContain('Production tracking boundary: blocked')
  expect(brief).toContain('## Local Executor Closeout Intake')
  expect(brief).toContain('Closeout checks: 2 of 8 checked.')
  expect(brief).toContain('[x] Source commit recorded')
  expect(brief).toContain('[x] Validation results captured')
  expect(brief).toContain('[ ] Guardrails confirmed')
  expect(brief).toContain('## Local Field Readiness Checklist')
  expect(brief).toContain('Field readiness checks: 2 of 8 checked.')
  expect(brief).toContain('[x] Drawing and source questions captured')
  expect(brief).toContain('[x] Safety planning questions captured')
  expect(brief).toContain('[ ] Field authority boundary acknowledged')
  expect(brief).toContain('## Local Field Questions Draft')
  expect(brief).toContain('Draft present: yes.')
  expect(brief).toContain('This browser-local field questions draft is prep context only. It is not a task, issue, work authorization, approval, persistence, import, assignment, schedule, status, or production state.')
  expect(brief).toContain('Drawing/source questions: Confirm latest one-line drawings match the temp power candidate shape.')
  expect(brief).toContain('Site access and safety questions: Confirm escort, access hours, and LOTO review questions before field discussion.')
  expect(brief).toContain('## Local Field Observation Scratchpad')
  expect(brief).toContain('Scratchpad present: yes.')
  expect(brief).toContain('This browser-local observation scratchpad is field-prep context only. It is not a task, issue, work authorization, approval, persistence, import, assignment, schedule, status, or production state.')
  expect(brief).toContain('Observation date or shift note: Day-one temp power prep conversation before field mobilization.')
  expect(brief).toContain('Observer / source: PM call with lead and customer site contact.')
  expect(brief).toContain('Access and safety observations: Escort and LOTO review need confirmation before field reliance.')
  await expect(page.getByText(/PM brief prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(reviewOutputStatus.getByText(/Approval packet preview prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await expect(reviewOutputStatus.getByText(/PM brief prepared from pm-import-candidate-miner-temp-power without a server write/i)).toBeVisible()
  await checklist.getByRole('button', { name: 'Clear checklist' }).click()
  await expect(checklist.getByText('0 of 7')).toBeVisible()
  for (const name of reviewChecklistNames) {
    await expect(checklist.getByRole('checkbox', { name })).not.toBeChecked()
  }
  await approvalDraft.getByRole('button', { name: 'Clear decision draft' }).click()
  await expect(approvalDraftDecisionSelect).toHaveValue('')
  await expect(approvalDraftNotes).toHaveValue('')
  await expect(approvalDraft.getByRole('checkbox', { name: /Local-only draft attestation/i })).not.toBeChecked()
  await expect(approvalDraft.getByRole('button', { name: 'Clear decision draft' })).toBeDisabled()
  await closeoutIntake.getByRole('button', { name: 'Clear closeout intake' }).click()
  await expect(closeoutIntake.getByText('0 of 8')).toBeVisible()
  await expect(closeoutIntake.getByRole('checkbox', { name: /Source commit recorded/i })).not.toBeChecked()
  await expect(closeoutIntake.getByRole('checkbox', { name: /Validation results captured/i })).not.toBeChecked()
  await fieldReadiness.getByRole('button', { name: 'Clear field readiness' }).click()
  await expect(fieldReadiness.getByText('0 of 8')).toBeVisible()
  await expect(fieldReadiness.getByRole('checkbox', { name: /Drawing and source questions captured/i })).not.toBeChecked()
  await expect(fieldReadiness.getByRole('checkbox', { name: /Safety planning questions captured/i })).not.toBeChecked()
  await fieldQuestions.getByRole('button', { name: 'Clear field questions' }).click()
  await expect(fieldQuestions.getByLabel(/Drawing\/source questions/i)).toHaveValue('')
  await expect(fieldQuestions.getByLabel(/Site access and safety questions/i)).toHaveValue('')
  await expect(fieldQuestions.getByRole('button', { name: 'Clear field questions' })).toBeDisabled()
  await fieldObservations.getByRole('button', { name: 'Clear field observations' }).click()
  await expect(fieldObservations.getByLabel(/Observation date or shift note/i)).toHaveValue('')
  await expect(fieldObservations.getByLabel(/Observer \/ source/i)).toHaveValue('')
  await expect(fieldObservations.getByLabel(/Access and safety observations/i)).toHaveValue('')
  await expect(fieldObservations.getByRole('button', { name: 'Clear field observations' })).toBeDisabled()
  await expect(readiness.getByText('2 of 6 ready')).toBeVisible()
  await expect(operatingQueue.getByText('1 complete / 1 next / 5 blocked')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('1 covered, 4 open, 1 blocked', { exact: true })).toBeVisible()
  await expect(exceptionRegister.getByText('0 covered, 4 open, 2 blocked')).toBeVisible()
  await expect(fieldPrepQueue.getByText('0 complete / 1 next / 4 blocked')).toBeVisible()
  await expect(fieldPrepCoverage.getByText('0 covered, 0 partial, 5 open, 2 blocked')).toBeVisible()
  await expect(fieldPrepAgenda.getByText('0 context, 5 ask, 0 confirm, 2 blocked')).toBeVisible()
  const resetLocalState = await page.evaluate(() => ({
    checklist: window.localStorage.getItem('pm-import-intake-review-checklist:pm-import-candidate-miner-temp-power'),
    draft: window.localStorage.getItem('pm-import-intake-approval-draft:pm-import-candidate-miner-temp-power'),
    closeout: window.localStorage.getItem('pm-import-intake-executor-closeout:pm-import-candidate-miner-temp-power'),
    fieldReadiness: window.localStorage.getItem('pm-import-intake-field-readiness:pm-import-candidate-miner-temp-power'),
    fieldQuestions: window.localStorage.getItem('pm-import-intake-field-questions:pm-import-candidate-miner-temp-power'),
    fieldObservations: window.localStorage.getItem('pm-import-intake-field-observations:pm-import-candidate-miner-temp-power'),
    pmIntakeSnapshot: window.localStorage.getItem('pm-import-intake-pm-intake-snapshot:pm-import-candidate-miner-temp-power'),
    fieldPrepCoverage: window.localStorage.getItem('pm-import-intake-field-prep-coverage:pm-import-candidate-miner-temp-power'),
    fieldPrepAgenda: window.localStorage.getItem('pm-import-intake-field-prep-agenda:pm-import-candidate-miner-temp-power'),
    fieldPrepPacket: window.localStorage.getItem('pm-import-intake-field-prep-packet:pm-import-candidate-miner-temp-power'),
    importExceptionRegister: window.localStorage.getItem('pm-import-intake-import-exception-register:pm-import-candidate-miner-temp-power'),
    quickJumpRail: window.localStorage.getItem('pm-import-intake-quick-jump-rail:pm-import-candidate-miner-temp-power'),
    commandCenter: window.localStorage.getItem('pm-import-intake-command-center:pm-import-candidate-miner-temp-power'),
    meetingReadout: window.localStorage.getItem('pm-import-intake-meeting-readout:pm-import-candidate-miner-temp-power'),
    constraintRadar: window.localStorage.getItem('pm-import-intake-constraint-radar:pm-import-candidate-miner-temp-power'),
    startHere: window.localStorage.getItem('pm-import-intake-start-here:pm-import-candidate-miner-temp-power'),
    dailyScript: window.localStorage.getItem('pm-import-intake-daily-review-script:pm-import-candidate-miner-temp-power'),
    outputSelector: window.localStorage.getItem('pm-import-intake-output-selector:pm-import-candidate-miner-temp-power'),
    handoffGuide: window.localStorage.getItem('pm-import-intake-handoff-guide:pm-import-candidate-miner-temp-power'),
    workflowMap: window.localStorage.getItem('pm-import-intake-workflow-map:pm-import-candidate-miner-temp-power'),
    openItems: window.localStorage.getItem('pm-import-intake-open-items:pm-import-candidate-miner-temp-power'),
  }))
  expect(resetLocalState).toEqual({ checklist: null, draft: null, closeout: null, fieldReadiness: null, fieldQuestions: null, fieldObservations: null, pmIntakeSnapshot: null, fieldPrepCoverage: null, fieldPrepAgenda: null, fieldPrepPacket: null, importExceptionRegister: null, quickJumpRail: null, commandCenter: null, meetingReadout: null, constraintRadar: null, startHere: null, dailyScript: null, outputSelector: null, handoffGuide: null, workflowMap: null, openItems: null })
  await expect(page.getByRole('button', { name: /Approve/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Persist/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Submit/i })).toHaveCount(0)
  await expect(page.getByRole('button', { name: /^Import$/i })).toHaveCount(0)
  await expectNoImpliedAuthorityControls(page)

  expect(mutationRequests).toHaveLength(0)
  expect(readCalls).toEqual({
    candidate: 1,
    admissionPlan: 1,
    approvalContract: 1,
    storagePlan: 1,
    approvalStatus: 1,
  })
})
