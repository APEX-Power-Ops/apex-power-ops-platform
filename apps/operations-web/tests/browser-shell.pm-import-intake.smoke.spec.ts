import { expect, type Page, test } from '@playwright/test'

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
  await expect(page.getByText(/import project rows/i)).toBeVisible()
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
  await routeLinkDisclosure.locator('summary').click()
  await expect(routeLinkDisclosure).not.toHaveAttribute('open', '')
  await expect(routeLinks.getByLabel('PM intake route link groups')).toBeHidden()
  const routeLinkDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|route-link/i.test(key)))
  expect(routeLinkDisclosureStateKeys).toEqual([])
  await routeLinkDisclosure.locator('summary').click()
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
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button')).toHaveCount(4)
  await expect(outputActionRail.getByLabel('Executor output actions').getByRole('button')).toHaveCount(1)
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button')).toHaveCount(5)
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
  await outputActionDisclosure.locator('summary').click()
  await expect(outputActionDisclosure).not.toHaveAttribute('open', '')
  await expect(outputActionRail.getByLabel('PM intake output action groups')).toBeHidden()
  const outputDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|output-action/i.test(key)))
  expect(outputDisclosureStateKeys).toEqual([])
  await outputActionDisclosure.locator('summary').click()
  await expect(outputActionDisclosure).toHaveAttribute('open', '')
  await expect(outputActionRail.getByLabel('PM intake output action groups')).toBeVisible()
  await expect(outputActionRail.getByLabel('Review output actions').getByRole('button')).toHaveCount(4)
  await expect(outputActionRail.getByLabel('Executor output actions').getByRole('button')).toHaveCount(1)
  await expect(outputActionRail.getByLabel('Field prep output actions').getByRole('button')).toHaveCount(5)
  await expect(outputActionRail.getByLabel('Refresh action').getByRole('button')).toHaveCount(1)
  await expect(page.getByLabel('PM intake output status rail')).toHaveCount(0)
  await expectNoImpliedAuthorityControls(page)
  const helperPanelStack = page.getByLabel('PM intake helper panel stack')
  const intakeTriagePanels = helperPanelStack.getByLabel('Intake triage helper panels')
  await expect(intakeTriagePanels.getByRole('heading', { name: 'Intake Triage Panels', exact: true })).toBeVisible()
  await expect(intakeTriagePanels.locator('#pm-command-center')).toHaveCount(1)
  await expect(intakeTriagePanels.locator('#pm-meeting-readout')).toHaveCount(1)
  await expect(intakeTriagePanels.locator('#pm-constraint-radar')).toHaveCount(1)
  const dailyActionPanels = helperPanelStack.getByLabel('Daily action helper panels')
  await expect(dailyActionPanels.getByRole('heading', { name: 'Daily Action Panels', exact: true })).toBeVisible()
  await expect(dailyActionPanels.locator('#pm-daily-review-script')).toHaveCount(1)
  await expect(dailyActionPanels.locator('#pm-start-here')).toHaveCount(1)
  await expect(dailyActionPanels.locator('#pm-output-selector')).toHaveCount(1)
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
  await intakeTriageDisclosure.locator('summary').click()
  await expect(intakeTriageDisclosure).not.toHaveAttribute('open', '')
  await expect(intakeTriagePanels.locator('#pm-command-center')).toBeHidden()
  const helperCollapseStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure/i.test(key)))
  expect(helperCollapseStateKeys).toEqual([])
  await intakeTriageDisclosure.locator('summary').click()
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
  await expect(approvalPrepDetail.getByLabel('Local approval decision draft')).toHaveCount(1)
  const executorCloseoutDetail = detailWorkbench.getByLabel('Executor closeout detail panels')
  await expect(executorCloseoutDetail.getByRole('heading', { name: 'Executor Closeout Detail', exact: true })).toBeVisible()
  await expect(executorCloseoutDetail.locator('#executor-closeout')).toHaveCount(1)
  const fieldPrepDetail = detailWorkbench.getByLabel('Field prep detail panels')
  await expect(fieldPrepDetail.getByRole('heading', { name: 'Field Prep Detail', exact: true })).toBeVisible()
  await expect(fieldPrepDetail.getByLabel('Local field readiness checklist')).toHaveCount(1)
  await expect(fieldPrepDetail.getByLabel('Local field questions draft')).toHaveCount(1)
  await expect(fieldPrepDetail.locator('#field-prep')).toHaveCount(1)
  await expect(fieldPrepDetail.getByLabel('Local field prep coverage snapshot')).toHaveCount(1)
  await expect(fieldPrepDetail.getByLabel('Local field prep conversation agenda')).toHaveCount(1)
  await expect(fieldPrepDetail.getByLabel('Local field observation scratchpad')).toHaveCount(1)
  const authorityBoundaryDetail = detailWorkbench.getByLabel('Authority boundary detail panels')
  await expect(authorityBoundaryDetail.getByRole('heading', { name: 'Authority Boundary Detail', exact: true })).toBeVisible()
  await expect(authorityBoundaryDetail.locator('#approval-readiness')).toHaveCount(1)
  await expect(authorityBoundaryDetail.locator('#guardrails')).toHaveCount(1)
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
  const pmIntakeSnapshotItems = pmIntakeSnapshotDisclosure.getByLabel('Local PM intake snapshot items')
  await expect(pmIntakeSnapshotItems).toBeVisible()
  await expect(pmIntakeSnapshotItems.locator('article')).toHaveCount(6)
  await pmIntakeSnapshotDisclosure.locator('summary').click()
  await expect(pmIntakeSnapshotDisclosure).not.toHaveAttribute('open', '')
  await expect(pmIntakeSnapshotItems).toBeHidden()
  const snapshotDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|snapshot/i.test(key)))
  expect(snapshotDisclosureStateKeys).toEqual([])
  await pmIntakeSnapshotDisclosure.locator('summary').click()
  await expect(pmIntakeSnapshotDisclosure).toHaveAttribute('open', '')
  await expect(pmIntakeSnapshotItems).toBeVisible()
  await expect(pmIntakeSnapshotItems.locator('article')).toHaveCount(6)
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
  const commandCenter = page.getByLabel('Local PM intake command center')
  await expect(commandCenter.getByRole('heading', { name: /Local PM Intake Command Center/i })).toBeVisible()
  await expect(commandCenter.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(commandCenter.getByText(/Compact top-of-page scan for the current local PM move/i)).toBeVisible()
  await expect(commandCenter.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state/i)).toBeVisible()
  await expect(commandCenter.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write/i)).toBeVisible()
  await expect(commandCenter.locator('a').filter({ hasText: /^Do now/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(commandCenter.locator('a').filter({ hasText: /^Ask next/ })).toHaveAttribute('href', '#field-prep')
  await expect(commandCenter.locator('a').filter({ hasText: /^Prepare handoff context/ })).toHaveAttribute('href', '#pm-output-selector')
  await expect(commandCenter.locator('a').filter({ hasText: /^Still blocked/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(commandCenter.getByText(/Miner Temp Power: start with source and exception review. Source fingerprint stat-fingerprint-abc123; review checklist has 0 of 7 local checks marked and exceptions are 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(commandCenter.getByText(/Field prep queue is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(commandCenter.getByText(/Use the output selector after local decision notes, field questions, observation notes, or executor closeout evidence exist/i)).toBeVisible()
  await expect(commandCenter.getByText(/6 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const meetingReadout = page.getByLabel('Local PM intake meeting readout')
  await expect(meetingReadout.getByRole('heading', { name: /Local PM Intake Meeting Readout/i })).toBeVisible()
  await expect(meetingReadout.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(meetingReadout.getByText(/Conversation-ready local summary for PM, lead, customer, or field review/i)).toBeVisible()
  await expect(meetingReadout.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state/i)).toBeVisible()
  await expect(meetingReadout.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, or production write/i)).toBeVisible()
  await expect(meetingReadout.locator('a').filter({ hasText: /^Project readout/ })).toHaveAttribute('href', '#project-packet')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Review posture/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Field ask/ })).toHaveAttribute('href', '#field-prep')
  await expect(meetingReadout.locator('a').filter({ hasText: /^Boundary statement/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(meetingReadout.getByText(/Miner Temp Power in Santa Teresa, NM: 7 workpackages, 15 tasks, and 186 apparatus candidates are loaded from source fingerprint stat-fingerprint-abc123/i)).toBeVisible()
  await expect(meetingReadout.getByText(/Exceptions are 0 covered, 4 open, 2 blocked and local review notes have not started/i)).toBeVisible()
  await expect(meetingReadout.getByText(/Field prep is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(meetingReadout.getByText(/6 of 6 approval-persistence gates remain blocked; project import remains not admitted; executor closeout evidence is 0 of 8/i)).toBeVisible()
  const constraintRadar = page.getByLabel('Local PM intake constraint radar')
  await expect(constraintRadar.getByRole('heading', { name: /Local PM Intake Constraint Radar/i })).toBeVisible()
  await expect(constraintRadar.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(constraintRadar.getByText(/Constraint scan for source\/review, field-prep, executor\/hosted, and future write-authority boundaries/i)).toBeVisible()
  await expect(constraintRadar.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, claim hosted parity, or mutate production state/i)).toBeVisible()
  await expect(constraintRadar.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, durable field record, production tracking row, workbook macro path, workbook writeback, or production write/i)).toBeVisible()
  await expect(constraintRadar.locator('a').filter({ hasText: /^Source and review constraints/ })).toHaveAttribute('href', '#import-exception-register')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Field-prep constraints/ })).toHaveAttribute('href', '#field-prep')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Executor and hosted constraints/ })).toHaveAttribute('href', '#executor-closeout')
  await expect(constraintRadar.locator('a').filter({ hasText: /^Future write authority constraints/ })).toHaveAttribute('href', '#approval-readiness')
  await expect(constraintRadar.getByText(/Source fingerprint stat-fingerprint-abc123; review checklist has 0 of 7 local checks marked; exceptions are 0 covered, 4 open, 2 blocked; local review notes have not started/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Field prep is 0 complete \/ 1 next \/ 4 blocked. Field questions present: no; field observations present: no/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Executor closeout evidence is 0 of 8; hosted parity remains an external executor boundary and is not claimed here/i)).toBeVisible()
  await expect(constraintRadar.getByText(/6 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench/i)).toBeVisible()
  const startHere = page.getByLabel('Local PM intake start here')
  await expect(startHere.getByRole('heading', { name: /Local PM Intake Start Here/i })).toBeVisible()
  await expect(startHere.getByText('browser-local')).toBeVisible()
  await expect(startHere.getByText(/Top-level focus for this intake session, derived from the existing workbench state/i)).toBeVisible()
  await expect(startHere.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, call live services, or mutate production state/i)).toBeVisible()
  await expect(startHere.getByText(/links to existing local sections and exports only; it creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write/i)).toBeVisible()
  await expect(startHere.getByRole('link', { name: /First local move/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(startHere.getByRole('link', { name: /Exception attention/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(startHere.getByRole('link', { name: /Field-prep focus/i })).toHaveAttribute('href', '#field-prep')
  await expect(startHere.getByRole('link', { name: /Useful local export/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(startHere.getByRole('link', { name: /Blocked future authority/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(startHere.getByText(/Review source and exceptions: Start with source freshness and warning review before relying on the candidate shape/i)).toBeVisible()
  await expect(startHere.getByText(/Import exception register: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(startHere.getByText(/Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(startHere.getByText(/Use Export PM Brief first when the next review needs compact candidate, gate, and guardrail context/i)).toBeVisible()
  await expect(startHere.getByText(/6 of 6 approval-persistence gates remain blocked. Snapshot posture: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  const dailyScript = page.getByLabel('Local PM intake daily review script')
  await expect(dailyScript.getByRole('heading', { name: /Local PM Intake Daily Review Script/i })).toBeVisible()
  await expect(dailyScript.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(dailyScript.getByText(/First 5 minutes of browser-local review, derived from the existing workbench state/i)).toBeVisible()
  await expect(dailyScript.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write/i)).toBeVisible()
  await expect(dailyScript.getByRole('link', { name: /Minute 0: Confirm source context/i })).toHaveAttribute('href', '#project-packet')
  await expect(dailyScript.getByRole('link', { name: /Minute 1: Scan exceptions/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(dailyScript.getByRole('link', { name: /Minute 2: Capture local draft notes/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(dailyScript.getByRole('link', { name: /Minute 3: Check field-prep questions/i })).toHaveAttribute('href', '#field-prep')
  await expect(dailyScript.getByRole('link', { name: /Minute 4: Name blocked future authority/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(dailyScript.getByText(/Miner Temp Power: source fingerprint stat-fingerprint-abc123; candidate authority remains not admitted/i)).toBeVisible()
  await expect(dailyScript.getByText(/Import exception register: 0 covered, 4 open, 2 blocked/i)).toBeVisible()
  await expect(dailyScript.getByText(/Local decision draft has not started; capture decision value, review notes, and local-only attestation before any future persistence packet/i)).toBeVisible()
  await expect(dailyScript.getByText(/Field prep queue: 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(dailyScript.getByText(/0 of 8 local closeout evidence checks are marked; 6 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const outputSelector = page.getByLabel('Local PM intake output selector')
  await expect(outputSelector.getByRole('heading', { name: /Local PM Intake Output Selector/i })).toBeVisible()
  await expect(outputSelector.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(outputSelector.getByText(/Browser-local chooser for existing outputs already on this workbench/i)).toBeVisible()
  await expect(outputSelector.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write/i)).toBeVisible()
  await expect(outputSelector.getByRole('link', { name: /PM Brief/i })).toHaveAttribute('href', '#pm-intake-snapshot')
  await expect(outputSelector.getByRole('link', { name: /Approval Preview JSON/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(outputSelector.getByRole('link', { name: /Executor Handoff/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(outputSelector.getByRole('link', { name: /Field Kickoff Brief/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByRole('link', { name: /Field Prep Packet/i })).toHaveAttribute('href', '#field-prep')
  await expect(outputSelector.getByText(/Future write packet/i)).toHaveCount(0)
  await expect(outputSelector.getByText(/Use PM Brief when the next review needs compact candidate, gate, and guardrail context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Approval Preview JSON should wait on local decision value, review notes, local-only attestation, and checklist evidence for useful later-packet context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Executor Handoff should wait on local closeout evidence checks when the next packet needs returned executor context/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Kickoff Brief is most useful after field questions or readiness evidence are captured; current field prep queue is 0 complete \/ 1 next \/ 4 blocked/i)).toBeVisible()
  await expect(outputSelector.getByText(/Field Prep Packet is the bundled field-prep artifact when the next conversation needs questions, coverage, agenda, readiness evidence, and observation context; current field prep queue is 0 complete \/ 1 next \/ 4 blocked/i)).toBeVisible()
  const handoffGuide = page.getByLabel('Local PM intake handoff guide')
  const handoffGuideDisclosure = page.locator('details[aria-label="Local PM intake handoff guide"]')
  await expect(handoffGuideDisclosure).toHaveAttribute('open', '')
  await expect(handoffGuide.getByRole('heading', { name: /Local PM Intake Handoff Guide/i })).toBeVisible()
  await expect(handoffGuide.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(handoffGuide.getByText(/Browser-local guide for the next context lane/i)).toBeVisible()
  await expect(handoffGuide.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write/i)).toBeVisible()
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide items')).toBeVisible()
  await expect(handoffGuide.getByRole('link')).toHaveCount(5)
  await expect(handoffGuide.getByRole('link', { name: /Jason local review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(handoffGuide.getByRole('link', { name: /Field conversation prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(handoffGuide.getByRole('link', { name: /Bounded executor context/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(handoffGuide.getByRole('link', { name: /Hosted parity executor boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByRole('link', { name: /Future approval-persistence packet boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await handoffGuideDisclosure.locator('summary').click()
  await expect(handoffGuideDisclosure).not.toHaveAttribute('open', '')
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide items')).toBeHidden()
  const handoffGuideDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|handoff-guide/i.test(key)))
  expect(handoffGuideDisclosureStateKeys).toEqual([])
  await handoffGuideDisclosure.locator('summary').click()
  await expect(handoffGuideDisclosure).toHaveAttribute('open', '')
  await expect(handoffGuide.getByLabel('Local PM intake handoff guide items')).toBeVisible()
  await expect(handoffGuide.getByRole('link')).toHaveCount(5)
  await expect(handoffGuide.getByRole('link', { name: /Jason local review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(handoffGuide.getByRole('link', { name: /Field conversation prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(handoffGuide.getByRole('link', { name: /Bounded executor context/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(handoffGuide.getByRole('link', { name: /Hosted parity executor boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByRole('link', { name: /Future approval-persistence packet boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(handoffGuide.getByText(/Use the workbench for Jason review while exceptions are 0 covered, 4 open, 2 blocked and local decision draft has not started/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Field prep queue is 0 complete \/ 1 next \/ 4 blocked. Capture field questions draft: Capture drawing\/source, access\/safety, material, customer, or PM follow-up questions before the kickoff brief is used/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Keep executor context local until review notes, local decision context, or closeout evidence are present/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Hosted Vercel and Render parity remain external executor lanes; this local workbench claims no hosted parity/i)).toBeVisible()
  await expect(handoffGuide.getByText(/6 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  const workflowMap = page.getByLabel('Local PM intake workflow map')
  const workflowMapDisclosure = page.locator('details[aria-label="Local PM intake workflow map"]')
  await expect(workflowMapDisclosure).toHaveAttribute('open', '')
  await expect(workflowMap.getByRole('heading', { name: /Local PM Intake Workflow Map/i })).toBeVisible()
  await expect(workflowMap.getByText('browser-local')).toBeVisible()
  await expect(workflowMap.getByText(/Visual map of the current intake path from source review through field-prep context, executor closeout, and still-blocked future write authority/i)).toBeVisible()
  await expect(workflowMap.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, or production write/i)).toBeVisible()
  await expect(workflowMap.getByLabel('Local PM intake workflow map items')).toBeVisible()
  await expect(workflowMap.getByRole('link')).toHaveCount(7)
  await expect(workflowMap.getByRole('link', { name: /Source intake/i })).toHaveAttribute('href', '#project-packet')
  await expect(workflowMap.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(workflowMap.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(workflowMap.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(workflowMap.getByRole('link', { name: /Executor closeout/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(workflowMap.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(workflowMap.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await workflowMapDisclosure.locator('summary').click()
  await expect(workflowMapDisclosure).not.toHaveAttribute('open', '')
  await expect(workflowMap.getByLabel('Local PM intake workflow map items')).toBeHidden()
  const workflowMapDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|workflow-map/i.test(key)))
  expect(workflowMapDisclosureStateKeys).toEqual([])
  await workflowMapDisclosure.locator('summary').click()
  await expect(workflowMapDisclosure).toHaveAttribute('open', '')
  await expect(workflowMap.getByLabel('Local PM intake workflow map items')).toBeVisible()
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
  await expect(workflowMap.getByText(/6 of 6 approval-persistence gates remain blocked until a later packet admits that path/i)).toBeVisible()
  await expect(workflowMap.getByText(/Project import remains not admitted for project, workpackage, task, apparatus, assignment, schedule, and status rows/i)).toBeVisible()
  const openItems = page.getByLabel('Local PM intake open items lens')
  const openItemsDisclosure = page.locator('details[aria-label="Local PM intake open items lens"]')
  await expect(openItemsDisclosure).toHaveAttribute('open', '')
  await expect(openItems.getByRole('heading', { name: /Local PM Intake Open Items Lens/i })).toBeVisible()
  await expect(openItems.getByText('browser-local')).toBeVisible()
  await expect(openItems.getByText(/Exception-first lens for local attention items and future authority blockers/i)).toBeVisible()
  await expect(openItems.getByText(/creates no localStorage key, export artifact, backend route, schema, approval record, task, issue, work authorization, or production write/i)).toBeVisible()
  await expect(openItems.getByLabel('Local PM intake open items lens items')).toBeVisible()
  await expect(openItems.getByRole('link')).toHaveCount(6)
  await expect(openItems.getByRole('link', { name: /Exception review/i })).toHaveAttribute('href', '#import-exception-register')
  await expect(openItems.getByRole('link', { name: /Decision draft/i })).toHaveAttribute('href', '#pm-operating-queue')
  await expect(openItems.getByRole('link', { name: /Field prep/i })).toHaveAttribute('href', '#field-prep')
  await expect(openItems.getByRole('link', { name: /Executor closeout evidence/i })).toHaveAttribute('href', '#executor-closeout')
  await expect(openItems.getByRole('link', { name: /Approval persistence boundary/i })).toHaveAttribute('href', '#approval-readiness')
  await expect(openItems.getByRole('link', { name: /Project import boundary/i })).toHaveAttribute('href', '#guardrails')
  await openItemsDisclosure.locator('summary').click()
  await expect(openItemsDisclosure).not.toHaveAttribute('open', '')
  await expect(openItems.getByLabel('Local PM intake open items lens items')).toBeHidden()
  const openItemsDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|open-items/i.test(key)))
  expect(openItemsDisclosureStateKeys).toEqual([])
  await openItemsDisclosure.locator('summary').click()
  await expect(openItemsDisclosure).toHaveAttribute('open', '')
  await expect(openItems.getByLabel('Local PM intake open items lens items')).toBeVisible()
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
  await expect(openItems.getByText(/6 of 6 approval-persistence gates remain blocked until a later packet admits that path/i)).toBeVisible()
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
  await quickJumpDisclosure.locator('summary').click()
  await expect(quickJumpDisclosure).not.toHaveAttribute('open', '')
  await expect(quickJumpSectionLinks).toBeHidden()
  const quickJumpDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|quick-jump/i.test(key)))
  expect(quickJumpDisclosureStateKeys).toEqual([])
  await quickJumpDisclosure.locator('summary').click()
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
  await expect(page.getByLabel('Project packet and source freshness').getByRole('heading', { name: /Project Packet/i })).toBeVisible()
  const pmIntakeSnapshot = page.getByLabel('Local PM intake snapshot')
  await expect(pmIntakeSnapshot.getByRole('heading', { name: /Local PM Intake Snapshot/i })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('browser-local')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText(/Compact scan view for exception posture, decision draft, field-prep context, next local action, hosted parity, and future write boundaries/i)).toBeVisible()
  await expect(pmIntakeSnapshot.getByText(/does not approve, persist, import, assign, schedule, change status, create tasks, create issues, or mutate production state/i)).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('0 covered, 4 open, 2 blocked', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Exception review snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Decision draft snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Field prep snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Next local action snapshot', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Approval persistence boundary', { exact: true })).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('Hosted parity boundary', { exact: true })).toBeVisible()
  const operatingQueue = page.getByLabel('Local PM operating queue')
  const operatingQueueDisclosure = page.locator('details#pm-operating-queue[aria-label="Local PM operating queue"]')
  await expect(operatingQueueDisclosure).toHaveAttribute('open', '')
  const operatingQueueItems = operatingQueueDisclosure.getByLabel('Local PM operating queue items')
  await expect(operatingQueueItems).toBeVisible()
  await expect(operatingQueueItems.locator('article')).toHaveCount(6)
  await expect(operatingQueue.getByRole('heading', { name: /Local PM Operating Queue/i })).toBeVisible()
  await expect(operatingQueue.getByText('browser-local')).toBeVisible()
  await expect(operatingQueue.getByText('0 complete / 1 next / 5 blocked')).toBeVisible()
  await expect(operatingQueue.getByText('Review source and exceptions', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Prepare local decision draft', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Export review artifacts', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Hosted parity executor closeout', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Approval persistence implementation', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText('Project import packet', { exact: true })).toBeVisible()
  await expect(operatingQueue.getByText(/Local queue for today's intake work/i)).toBeVisible()
  await expect(operatingQueue.getByText(/without approving, persisting, importing, assigning, scheduling, changing status, or mutating production state/i)).toBeVisible()
  await operatingQueueDisclosure.locator(':scope > summary').click()
  await expect(operatingQueueDisclosure).not.toHaveAttribute('open', '')
  await expect(operatingQueueItems).toBeHidden()
  const operatingQueueDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|operating-queue/i.test(key)))
  expect(operatingQueueDisclosureStateKeys).toEqual([])
  await operatingQueueDisclosure.locator(':scope > summary').click()
  await expect(operatingQueueDisclosure).toHaveAttribute('open', '')
  await expect(operatingQueueItems).toBeVisible()
  await expect(operatingQueueItems.locator('article')).toHaveCount(6)
  const exceptionRegister = page.getByLabel('Local import exception decision register')
  const exceptionRegisterDisclosure = page.locator('details#import-exception-register[aria-label="Local import exception decision register"]')
  await expect(exceptionRegisterDisclosure).toHaveAttribute('open', '')
  const exceptionRegisterItems = exceptionRegisterDisclosure.getByLabel('Local import exception decision register items')
  await expect(exceptionRegisterItems).toBeVisible()
  await expect(exceptionRegisterItems.locator('article')).toHaveCount(6)
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
  await expect(exceptionRegisterItems).toBeHidden()
  const exceptionRegisterDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|import-exception-register/i.test(key)))
  expect(exceptionRegisterDisclosureStateKeys).toEqual([])
  await exceptionRegisterDisclosure.locator(':scope > summary').click()
  await expect(exceptionRegisterDisclosure).toHaveAttribute('open', '')
  await expect(exceptionRegisterItems).toBeVisible()
  await expect(exceptionRegisterItems.locator('article')).toHaveCount(6)
  const workflowGates = page.getByLabel('Workflow gates')
  const workflowGatesDisclosure = page.locator('details#workflow-gates[aria-label="Workflow gates"]')
  await expect(workflowGatesDisclosure).toHaveAttribute('open', '')
  const workflowGateItems = workflowGatesDisclosure.getByLabel('Workflow gate items')
  await expect(workflowGateItems).toBeVisible()
  await expect(workflowGateItems.locator('article')).toHaveCount(6)
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
  await expect(workflowGateItems).toBeHidden()
  const workflowGatesDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|workflow-gates/i.test(key)))
  expect(workflowGatesDisclosureStateKeys).toEqual([])
  await workflowGatesDisclosure.locator(':scope > summary').click()
  await expect(workflowGatesDisclosure).toHaveAttribute('open', '')
  await expect(workflowGateItems).toBeVisible()
  await expect(workflowGateItems.locator('article')).toHaveCount(6)
  const exceptionDecisionDetail = page.locator('details[aria-label="Exception review and PM decision detail"]')
  await expect(exceptionDecisionDetail).toHaveAttribute('open', '')
  const exceptionDecisionItems = exceptionDecisionDetail.locator('[aria-label="Exception and PM decision detail cards"]')
  await expect(exceptionDecisionItems).toBeVisible()
  await expect(exceptionDecisionItems.locator(':scope > article')).toHaveCount(2)
  await expect(exceptionDecisionItems.getByRole('heading', { name: 'Exception Review', exact: true })).toBeVisible()
  await expect(exceptionDecisionItems.getByRole('heading', { name: 'PM Decisions', exact: true })).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('PROJECT_DATA_ENTRY_FORMULA_ERRORS')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('234 planning-workbook rows include formula errors.')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('decision approve candidate for import planning')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('Does this candidate correctly represent the project, workpackages, tasks, and apparatus?')).toBeVisible()
  await expect(exceptionDecisionDetail.getByText('Approve only after blocker and warning review is complete.')).toBeVisible()
  await exceptionDecisionDetail.locator(':scope > summary').click()
  await expect(exceptionDecisionDetail).not.toHaveAttribute('open', '')
  await expect(exceptionDecisionItems).toBeHidden()
  const exceptionDecisionDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|exception-review|pm-decision/i.test(key)))
  expect(exceptionDecisionDisclosureStateKeys).toEqual([])
  await exceptionDecisionDetail.locator(':scope > summary').click()
  await expect(exceptionDecisionDetail).toHaveAttribute('open', '')
  await expect(exceptionDecisionItems).toBeVisible()
  await expect(exceptionDecisionItems.locator(':scope > article')).toHaveCount(2)
  const admissionApprovalContract = page.locator('details[aria-label="Admission and approval contract"]')
  await expect(admissionApprovalContract).toHaveAttribute('open', '')
  const admissionApprovalContractCards = admissionApprovalContract.locator('[aria-label="Admission and approval contract cards"]')
  await expect(admissionApprovalContractCards).toBeVisible()
  await expect(admissionApprovalContractCards.locator(':scope > article')).toHaveCount(2)
  await expect(admissionApprovalContractCards.getByRole('heading', { name: 'Admission Shape', exact: true })).toBeVisible()
  await expect(admissionApprovalContractCards.getByRole('heading', { name: 'Approval Contract', exact: true })).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm-import-candidate-miner-temp-power-admission-plan')).toBeVisible()
  await expect(admissionApprovalContract.getByText('project rows: 1; workpackage rows: 7; task rows: 15; apparatus rows: 186; approval rows: 1; write authority: not_admitted')).toBeVisible()
  await expect(admissionApprovalContract.locator('div').filter({ hasText: /^No-go checks2$/ })).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm-import-candidate-miner-temp-power-approval-persistence-contract')).toBeVisible()
  await expect(admissionApprovalContract.getByText('pm_import_candidate_approval', { exact: true })).toBeVisible()
  await expect(admissionApprovalContract.getByText('design_only_not_admitted')).toBeVisible()
  await expect(admissionApprovalContract.getByText('seam.pm_import_candidate_approvals')).toBeVisible()
  await expect(admissionApprovalContract.getByText('/api/v1/mutations/project-import-approvals')).toBeVisible()
  await admissionApprovalContract.locator(':scope > summary').click()
  await expect(admissionApprovalContract).not.toHaveAttribute('open', '')
  await expect(admissionApprovalContractCards).toBeHidden()
  const admissionApprovalContractDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|admission|approval-contract/i.test(key)))
  expect(admissionApprovalContractDisclosureStateKeys).toEqual([])
  await admissionApprovalContract.locator(':scope > summary').click()
  await expect(admissionApprovalContract).toHaveAttribute('open', '')
  await expect(admissionApprovalContractCards).toBeVisible()
  await expect(admissionApprovalContractCards.locator(':scope > article')).toHaveCount(2)
  const checklist = page.locator('details[aria-label="Local review checklist"]')
  await expect(checklist).toHaveAttribute('open', '')
  const checklistControls = checklist.locator('[aria-label="Review checklist controls"]')
  await expect(checklistControls).toBeVisible()
  await expect(checklistControls.locator('label')).toHaveCount(7)
  await expect(checklist.getByRole('heading', { name: /Local Review Checklist/i })).toBeVisible()
  await expect(checklist.getByText(/Browser-local review prep only/i)).toBeVisible()
  await expect(checklist.getByText('0 of 7')).toBeVisible()
  await expect(checklist.getByRole('button', { name: 'Clear checklist' })).toBeDisabled()
  await checklist.locator(':scope > summary').click()
  await expect(checklist).not.toHaveAttribute('open', '')
  await expect(checklistControls).toBeHidden()
  const reviewChecklistDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|local-review-checklist/i.test(key)))
  expect(reviewChecklistDisclosureStateKeys).toEqual([])
  await checklist.locator(':scope > summary').click()
  await expect(checklist).toHaveAttribute('open', '')
  await expect(checklistControls).toBeVisible()
  await checklist.getByRole('checkbox', { name: /Source freshness reviewed/i }).check()
  await checklist.getByRole('checkbox', { name: /Warnings reviewed/i }).check()
  await expect(checklist.getByText('2 of 7')).toBeVisible()
  await expect(checklist.getByRole('button', { name: 'Clear checklist' })).toBeEnabled()
  const approvalDraft = page.getByLabel('Local approval decision draft')
  await expect(approvalDraft.getByRole('heading', { name: /Local Approval Decision Draft/i })).toBeVisible()
  await expect(approvalDraft.getByText(/local review prep/i)).toBeVisible()
  await approvalDraft.getByLabel(/Decision draft/i).selectOption('return_for_revision')
  await approvalDraft.getByLabel(/Review notes draft/i).fill('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
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
  await expect(constraintRadar.getByText(/4 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Use the workbench for Jason review while exceptions are 4 covered, 0 open, 2 blocked and local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Existing Executor Handoff context has 0 of 8 local closeout evidence checks marked plus local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(workflowMap.getByText(/Import exception register: 4 covered, 0 open, 2 blocked/i)).toBeVisible()
  await expect(workflowMap.getByText(/Local decision draft has a decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(openItems.getByText(/Local exception attention is covered, but 2 future boundary item\(s\) remain blocked/i)).toBeVisible()
  await expect(openItems.getByText(/Local decision value, review notes, and local-only attestation are present/i)).toBeVisible()
  const closeoutIntake = page.getByLabel('Local executor closeout intake')
  await expect(closeoutIntake.getByRole('heading', { name: /Local Executor Closeout Intake/i })).toBeVisible()
  await expect(closeoutIntake.getByText(/Browser-local audit prep for external executor returns/i)).toBeVisible()
  await expect(closeoutIntake.getByText(/does not accept, approve, persist, deploy, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await expect(closeoutIntake.getByText('0 of 8')).toBeVisible()
  await expect(closeoutIntake.getByText('Source commit recorded', { exact: true })).toBeVisible()
  await expect(closeoutIntake.getByText('Validation results captured', { exact: true })).toBeVisible()
  await expect(closeoutIntake.getByText('Guardrails confirmed', { exact: true })).toBeVisible()
  await closeoutIntake.getByRole('checkbox', { name: /Source commit recorded/i }).check()
  await closeoutIntake.getByRole('checkbox', { name: /Validation results captured/i }).check()
  await expect(closeoutIntake.getByText('2 of 8')).toBeVisible()
  await expect(dailyScript.getByText(/2 of 8 local closeout evidence checks are marked; 4 of 6 approval-persistence gates remain blocked and project import remains not admitted/i)).toBeVisible()
  await expect(outputSelector.getByText(/Executor Handoff has 2 of 8 local closeout evidence checks marked for returned executor context/i)).toBeVisible()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 2 of 8; field questions: no; field observations: no/i)).toBeVisible()
  await expect(meetingReadout.getByText(/4 of 6 approval-persistence gates remain blocked; project import remains not admitted; executor closeout evidence is 2 of 8/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Executor closeout evidence is 2 of 8; hosted parity remains an external executor boundary and is not claimed here/i)).toBeVisible()
  await expect(handoffGuide.getByText(/Existing Executor Handoff context has 2 of 8 local closeout evidence checks marked plus local decision draft has decision value, review notes, and local-only attestation/i)).toBeVisible()
  await expect(workflowMap.getByText(/2 of 8 local closeout checks marked for returned executor evidence/i)).toBeVisible()
  await expect(openItems.getByText(/2 of 8 local closeout evidence checks are marked/i)).toBeVisible()
  const fieldReadiness = page.getByLabel('Local field readiness checklist')
  await expect(fieldReadiness.getByRole('heading', { name: /Local Field Readiness Checklist/i })).toBeVisible()
  await expect(fieldReadiness.getByText(/Browser-local prep evidence for PM, lead, and field review conversations/i)).toBeVisible()
  await expect(fieldReadiness.getByText(/does not authorize work, approve, persist, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await expect(fieldReadiness.getByText('0 of 8')).toBeVisible()
  await expect(fieldReadiness.getByText('Drawing and source questions captured', { exact: true })).toBeVisible()
  await expect(fieldReadiness.getByText('Safety planning questions captured', { exact: true })).toBeVisible()
  await expect(fieldReadiness.getByText('Field authority boundary acknowledged', { exact: true })).toBeVisible()
  const fieldPrepQueue = page.getByLabel('Local field prep queue')
  await expect(fieldPrepQueue.getByRole('heading', { name: /Local Field Prep Queue/i })).toBeVisible()
  await expect(fieldPrepQueue.getByText('browser-local')).toBeVisible()
  await expect(fieldPrepQueue.getByText(/Derived queue for field-prep conversations/i)).toBeVisible()
  await expect(fieldPrepQueue.getByText(/without creating tasks, issues, assignments, schedules, status updates, approval records, import rows, or production writes/i)).toBeVisible()
  await expect(fieldPrepQueue.getByText('0 complete / 1 next / 4 blocked')).toBeVisible()
  await expect(fieldPrepQueue.getByText('Capture field questions draft', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Mark field readiness prep evidence', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Export field kickoff prep brief', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Confirm field authority boundary', { exact: true })).toBeVisible()
  await expect(fieldPrepQueue.getByText('Production execution tracking', { exact: true })).toBeVisible()
  const fieldPrepCoverage = page.getByLabel('Local field prep coverage snapshot')
  await expect(fieldPrepCoverage.getByRole('heading', { name: /Local Field Prep Coverage Snapshot/i })).toBeVisible()
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
  const fieldPrepAgenda = page.getByLabel('Local field prep conversation agenda')
  await expect(fieldPrepAgenda.getByRole('heading', { name: /Local Field Prep Conversation Agenda/i })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('derived', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText(/Browser-local agenda derived from the coverage snapshot/i)).toBeVisible()
  await expect(fieldPrepAgenda.getByText(/without creating tasks, issues, work authorization, assignments, schedules, status updates, approval records, import rows, durable field records, production tracking rows, or production writes/i)).toBeVisible()
  await expect(fieldPrepAgenda.getByText('0 context, 5 ask, 0 confirm, 2 blocked')).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Source and drawing coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Access and safety coverage', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Field authority boundary conversation', { exact: true })).toBeVisible()
  await expect(fieldPrepAgenda.getByText('Production tracking boundary', { exact: true })).toBeVisible()
  await fieldReadiness.getByRole('checkbox', { name: /Drawing and source questions captured/i }).check()
  await fieldReadiness.getByRole('checkbox', { name: /Safety planning questions captured/i }).check()
  await expect(fieldReadiness.getByText('2 of 8')).toBeVisible()
  const fieldQuestions = page.getByLabel('Local field questions draft')
  await expect(fieldQuestions.getByRole('heading', { name: /Local Field Questions Draft/i })).toBeVisible()
  await expect(fieldQuestions.getByText('local only')).toBeVisible()
  await expect(fieldQuestions.getByText(/Browser-local question notes for PM, lead, and field prep conversations/i)).toBeVisible()
  await expect(fieldQuestions.getByText(/These notes do not create tasks/i)).toBeVisible()
  await expect(fieldQuestions.getByText(/production writes/i)).toBeVisible()
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
  const fieldObservations = page.getByLabel('Local field observation scratchpad')
  await expect(fieldObservations.getByRole('heading', { name: /Local Field Observation Scratchpad/i })).toBeVisible()
  await expect(fieldObservations.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(fieldObservations.getByText(/Browser-local observation notes for PM, lead, and field conversations/i)).toBeVisible()
  await expect(fieldObservations.getByText(/do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes/i)).toBeVisible()
  await fieldObservations.getByLabel(/Observation date or shift note/i).fill('Day-one temp power prep conversation before field mobilization.')
  await fieldObservations.getByLabel(/Observer \/ source/i).fill('PM call with lead and customer site contact.')
  await fieldObservations.getByLabel(/Access and safety observations/i).fill('Escort and LOTO review need confirmation before field reliance.')
  await expect(fieldObservations.getByRole('button', { name: 'Clear field observations' })).toBeEnabled()
  await expect(commandCenter.getByText(/Local handoff context exists from decision draft: yes; closeout checks: 2 of 8; field questions: yes; field observations: yes/i)).toBeVisible()
  await expect(constraintRadar.getByText(/Field prep is 2 complete \/ 2 next \/ 1 blocked. Field questions present: yes; field observations present: yes/i)).toBeVisible()
  await expect(fieldPrepCoverage.getByText('2 covered, 0 partial, 3 open, 2 blocked')).toBeVisible()
  await expect(fieldPrepAgenda.getByText('2 context, 3 ask, 1 confirm, 1 blocked')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('3 covered, 1 open, 2 blocked', { exact: true })).toBeVisible()
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
  const readiness = page.getByLabel('Approval persistence readiness gates')
  await expect(readiness.getByRole('heading', { name: /Approval Persistence Readiness/i })).toBeVisible()
  await expect(readiness.getByText('2 of 6 ready')).toBeVisible()
  await expect(readiness.getByText('Approval preview context', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Review checklist evidence', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Hosted parity closeout', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Schema authority', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Approval persistence authority', { exact: true })).toBeVisible()
  await expect(readiness.getByText('Import mutation authority', { exact: true })).toBeVisible()
  await expect(
    readiness.getByText(
      'PM Lane 049 authored the schema and adapter admission design. Hosted parity, schema authority, approval persistence authority, and import mutation authority remain blocked until later packets explicitly admit them.',
      { exact: true },
    ),
  ).toBeVisible()
  await expect(readiness.getByText(/does not approve, persist, import, assign, schedule, change status, or mutate production state/i)).toBeVisible()
  await expect(operatingQueue.getByText('2 complete / 1 next / 3 blocked')).toBeVisible()
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
  expect(handoff).toContain('Do not treat this handoff as approval, persistence authority, import authority, hosted parity proof, or task creation.')
  expect(handoff).toContain('- Candidate: pm-import-candidate-miner-temp-power')
  expect(handoff).toContain('- Candidate authority: not_admitted')
  expect(handoff).toContain('- Checklist checked: 2 of 7')
  expect(handoff).toContain('- Closeout checks: 2 of 8')
  expect(handoff).toContain('- Decision draft: return_for_revision')
  expect(handoff).toContain('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  expect(handoff).toContain('## Operating Queue')
  expect(handoff).toContain('Export review artifacts: Use the PM brief and approval preview JSON as browser-local context for the next admitted packet.')
  expect(handoff).toContain('Hosted parity executor closeout: PM Lane 041A/041B still need executor closeout before hosted parity can be claimed.')
  expect(handoff).toContain('Approval persistence implementation: PM Lane 049 is design-only; schema and adapter implementation still need an explicit later packet.')
  expect(handoff).toContain('Project import packet: Project, workpackage, task, and apparatus rows remain blocked until approval persistence is explicitly admitted and validated in a later packet.')
  expect(handoff).toContain('## PM Intake Snapshot')
  expect(handoff).toContain('PM intake snapshot: 3 covered, 1 open, 2 blocked.')
  expect(handoff).toContain('Exception review snapshot: covered')
  expect(handoff).toContain('Field prep snapshot: covered')
  expect(handoff).toContain('Approval persistence boundary: blocked')
  expect(handoff).toContain('## PM Constraint Radar')
  expect(handoff).toContain('Source and review constraints: context - Source fingerprint stat-fingerprint-abc123; review checklist has 2 of 7 local checks marked; exceptions are 4 covered, 0 open, 2 blocked; local review notes are captured.')
  expect(handoff).toContain('Field-prep constraints: attention - Field prep is 2 complete / 2 next / 1 blocked. Field questions present: yes; field observations present: yes.')
  expect(handoff).toContain('Executor and hosted constraints: attention - Executor closeout evidence is 2 of 8; hosted parity remains an external executor boundary and is not claimed here.')
  expect(handoff).toContain('Future write authority constraints: blocked - 4 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench.')
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
  expect(handoff).toContain('## Approval Persistence Blockers')
  expect(handoff).toContain('Schema authority: PM Lane 049 authored the schema and adapter admission design, but no SQL execution or schema migration is admitted.')
  expect(handoff).toContain('## Future Surfaces Are Not Admitted')
  expect(handoff).toContain('- Future approval route: /api/v1/mutations/project-import-approvals')
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
  await outputStatusDisclosure.locator('summary').click()
  await expect(outputStatusDisclosure).not.toHaveAttribute('open', '')
  await expect(outputStatusRail.getByLabel('PM intake output status groups')).toBeHidden()
  const outputStatusDisclosureStateKeys = await page.evaluate(() => Object.keys(window.localStorage).filter((key) => key.startsWith('pm-import-intake-') && /collapse|disclosure|output-status/i.test(key)))
  expect(outputStatusDisclosureStateKeys).toEqual([])
  await outputStatusDisclosure.locator('summary').click()
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
  expect(pmIntakeSnapshotExport).toContain('PM intake snapshot: 3 covered, 1 open, 2 blocked.')
  expect(pmIntakeSnapshotExport).toContain('Exception review snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Decision draft snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Field prep snapshot: covered')
  expect(pmIntakeSnapshotExport).toContain('Next local action snapshot: open')
  expect(pmIntakeSnapshotExport).toContain('Approval persistence boundary: blocked')
  expect(pmIntakeSnapshotExport).toContain('Hosted parity boundary: blocked')
  expect(pmIntakeSnapshotExport).toContain('## Future Surfaces Are Not Admitted')
  expect(pmIntakeSnapshotExport).toContain('- Future approval route: /api/v1/mutations/project-import-approvals')
  expect(pmIntakeSnapshotExport).toContain('## Not Allowed')
  expect(pmIntakeSnapshotExport).toContain('- write supabase')
  expect(pmIntakeSnapshotExport).toContain('- persist approval record')
  expect(pmIntakeSnapshotExport).toContain('- import project rows')
  expect(pmIntakeSnapshotExport).toContain('Use this snapshot as scan-level PM review synthesis only.')
  expect(pmIntakeSnapshotExport).toContain('Keep approval persistence and project import blocked until a later packet explicitly admits the required write path.')
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
  expect(exceptionRegisterExport).toContain('Keep approval persistence and project import blocked until a later packet explicitly admits the required write path.')
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
  expect(fieldBrief).toContain('Do not treat it as a work authorization, schedule, assignment, status update, hosted parity proof, approval record, import packet, or task creation.')
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
  expect(fieldBrief).toContain('## Future Surfaces Are Not Admitted')
  expect(fieldBrief).toContain('- Future approval route: /api/v1/mutations/project-import-approvals')
  expect(fieldBrief).toContain('## Not Allowed')
  expect(fieldBrief).toContain('- write supabase')
  expect(fieldBrief).toContain('- persist approval record')
  expect(fieldBrief).toContain('- import project rows')
  expect(fieldBrief).toContain('Do not create assignments, schedules, status changes, approval records, schema, SQL, or import rows from this brief.')
  expect(fieldBrief).toContain('Do not claim hosted parity from this local export.')
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
  expect(fieldObservationNotes).toContain('Do not treat them as work authorization, assignment, schedule, status update, approval record, import packet, task creation, issue creation, hosted parity proof, or production tracking.')
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
  expect(fieldPrepPacket).toContain('## Future Surfaces Are Not Admitted')
  expect(fieldPrepPacket).toContain('- Future approval route: /api/v1/mutations/project-import-approvals')
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
  expect(brief).toContain('- Future approval route: /api/v1/mutations/project-import-approvals')
  expect(brief).toContain('## Not Allowed Now')
  expect(brief).toContain('- write supabase')
  expect(brief).toContain('- persist approval record')
  expect(brief).toContain('- import project rows')
  expect(brief).toContain('## Local Review Checklist')
  expect(brief).toContain('Checklist progress: 2 of 7 checked.')
  expect(brief).toContain('[x] Source freshness reviewed')
  expect(brief).toContain('[x] Warnings reviewed')
  expect(brief).toContain('[ ] Hosted parity acknowledged')
  expect(brief).toContain('## Local Approval Decision Draft')
  expect(brief).toContain('Draft present: yes.')
  expect(brief).toContain('- Decision draft: return_for_revision')
  expect(brief).toContain('- Local-only attestation checked: yes')
  expect(brief).toContain('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  expect(brief).toContain('## Approval Persistence Readiness')
  expect(brief).toContain('Readiness gates ready: 2 of 6.')
  expect(brief).toContain('Approval preview context: ready')
  expect(brief).toContain('Review checklist evidence: ready')
  expect(brief).toContain('Hosted parity closeout: blocked')
  expect(brief).toContain('Schema authority: blocked')
  expect(brief).toContain('Approval persistence authority: blocked')
  expect(brief).toContain('Import mutation authority: blocked')
  expect(brief).toContain('## PM Operating Queue')
  expect(brief).toContain('Queue status: 2 complete, 1 next, 3 blocked.')
  expect(brief).toContain('Review source and exceptions: complete')
  expect(brief).toContain('Prepare local decision draft: complete')
  expect(brief).toContain('Export review artifacts: next')
  expect(brief).toContain('Hosted parity executor closeout: blocked')
  expect(brief).toContain('Approval persistence implementation: blocked')
  expect(brief).toContain('Project import packet: blocked')
  expect(brief).toContain('## Local PM Intake Snapshot')
  expect(brief).toContain('PM intake snapshot: 3 covered, 1 open, 2 blocked.')
  expect(brief).toContain('Exception review snapshot: covered')
  expect(brief).toContain('Next local action snapshot: open')
  expect(brief).toContain('Hosted parity boundary: blocked')
  expect(brief).toContain('## Local PM Constraint Radar')
  expect(brief).toContain('Source and review constraints: context - Source fingerprint stat-fingerprint-abc123; review checklist has 2 of 7 local checks marked; exceptions are 4 covered, 0 open, 2 blocked; local review notes are captured.')
  expect(brief).toContain('Field-prep constraints: attention - Field prep is 2 complete / 2 next / 1 blocked. Field questions present: yes; field observations present: yes.')
  expect(brief).toContain('Executor and hosted constraints: attention - Executor closeout evidence is 2 of 8; hosted parity remains an external executor boundary and is not claimed here.')
  expect(brief).toContain('Future write authority constraints: blocked - 4 of 6 approval-persistence gates remain blocked; project import remains not admitted; future write authority remains outside this browser-local workbench.')
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
  await expect(checklist.getByRole('checkbox', { name: /Source freshness reviewed/i })).not.toBeChecked()
  await expect(checklist.getByRole('checkbox', { name: /Warnings reviewed/i })).not.toBeChecked()
  await approvalDraft.getByRole('button', { name: 'Clear decision draft' }).click()
  await expect(approvalDraft.getByLabel(/Decision draft/i)).toHaveValue('')
  await expect(approvalDraft.getByLabel(/Review notes draft/i)).toHaveValue('')
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
  await expect(readiness.getByText('0 of 6 ready')).toBeVisible()
  await expect(operatingQueue.getByText('0 complete / 1 next / 5 blocked')).toBeVisible()
  await expect(pmIntakeSnapshot.getByText('0 covered, 4 open, 2 blocked', { exact: true })).toBeVisible()
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
  })
})
