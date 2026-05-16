import { expect, test } from '@playwright/test'

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
  const operatingQueue = page.getByLabel('Local PM operating queue')
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
  const checklist = page.getByLabel('Local review checklist')
  await expect(checklist.getByRole('heading', { name: /Local Review Checklist/i })).toBeVisible()
  await expect(checklist.getByText(/Browser-local review prep only/i)).toBeVisible()
  await expect(checklist.getByText('0 of 7')).toBeVisible()
  await checklist.getByRole('checkbox', { name: /Source freshness reviewed/i }).check()
  await checklist.getByRole('checkbox', { name: /Warnings reviewed/i }).check()
  await expect(checklist.getByText('2 of 7')).toBeVisible()
  const approvalDraft = page.getByLabel('Local approval decision draft')
  await expect(approvalDraft.getByRole('heading', { name: /Local Approval Decision Draft/i })).toBeVisible()
  await expect(approvalDraft.getByText(/local review prep/i)).toBeVisible()
  await approvalDraft.getByLabel(/Decision draft/i).selectOption('return_for_revision')
  await approvalDraft.getByLabel(/Review notes draft/i).fill('Reviewed formula warnings; return for revision until source workbook errors are resolved.')
  await approvalDraft.getByRole('checkbox', { name: /Local-only draft attestation/i }).check()
  await expect(approvalDraft.getByRole('button', { name: 'Clear decision draft' })).toBeEnabled()
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
  await expect(fieldPrepQueue.getByText('2 complete / 2 next / 1 blocked')).toBeVisible()
  const fieldObservations = page.getByLabel('Local field observation scratchpad')
  await expect(fieldObservations.getByRole('heading', { name: /Local Field Observation Scratchpad/i })).toBeVisible()
  await expect(fieldObservations.getByText('browser-local', { exact: true })).toBeVisible()
  await expect(fieldObservations.getByText(/Browser-local observation notes for PM, lead, and field conversations/i)).toBeVisible()
  await expect(fieldObservations.getByText(/do not create tasks, issues, work authorization, assignments, schedules, status updates, approval records, imports, or production writes/i)).toBeVisible()
  await fieldObservations.getByLabel(/Observation date or shift note/i).fill('Day-one temp power prep conversation before field mobilization.')
  await fieldObservations.getByLabel(/Observer \/ source/i).fill('PM call with lead and customer site contact.')
  await fieldObservations.getByLabel(/Access and safety observations/i).fill('Escort and LOTO review need confirmation before field reliance.')
  await expect(fieldObservations.getByRole('button', { name: 'Clear field observations' })).toBeEnabled()
  const localState = await page.evaluate(() => ({
    checklist: window.localStorage.getItem('pm-import-intake-review-checklist:pm-import-candidate-miner-temp-power'),
    draft: window.localStorage.getItem('pm-import-intake-approval-draft:pm-import-candidate-miner-temp-power'),
    closeout: window.localStorage.getItem('pm-import-intake-executor-closeout:pm-import-candidate-miner-temp-power'),
    fieldReadiness: window.localStorage.getItem('pm-import-intake-field-readiness:pm-import-candidate-miner-temp-power'),
    fieldQuestions: window.localStorage.getItem('pm-import-intake-field-questions:pm-import-candidate-miner-temp-power'),
    fieldObservations: window.localStorage.getItem('pm-import-intake-field-observations:pm-import-candidate-miner-temp-power'),
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
  expect(brief).toContain('## Local Field Prep Queue')
  expect(brief).toContain('Field prep queue: 2 complete, 2 next, 1 blocked.')
  expect(brief).toContain('Capture field questions draft: complete')
  expect(brief).toContain('Export field kickoff prep brief: next')
  expect(brief).toContain('Production execution tracking: blocked')
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
  await expect(fieldPrepQueue.getByText('0 complete / 1 next / 4 blocked')).toBeVisible()
  const resetLocalState = await page.evaluate(() => ({
    checklist: window.localStorage.getItem('pm-import-intake-review-checklist:pm-import-candidate-miner-temp-power'),
    draft: window.localStorage.getItem('pm-import-intake-approval-draft:pm-import-candidate-miner-temp-power'),
    closeout: window.localStorage.getItem('pm-import-intake-executor-closeout:pm-import-candidate-miner-temp-power'),
    fieldReadiness: window.localStorage.getItem('pm-import-intake-field-readiness:pm-import-candidate-miner-temp-power'),
    fieldQuestions: window.localStorage.getItem('pm-import-intake-field-questions:pm-import-candidate-miner-temp-power'),
    fieldObservations: window.localStorage.getItem('pm-import-intake-field-observations:pm-import-candidate-miner-temp-power'),
  }))
  expect(resetLocalState).toEqual({ checklist: null, draft: null, closeout: null, fieldReadiness: null, fieldQuestions: null, fieldObservations: null })
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
