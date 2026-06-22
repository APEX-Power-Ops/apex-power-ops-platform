import { expect, test } from '@playwright/test'

test('estimator-intake page: renders tree, Approve disabled on blocking finding, no dollars', async ({ page }) => {
  const FIXED_RUN = {
    run_id: 'run-test-001',
    status: 'parsed',
    conflict_kind: null,
    source_format: 'miner_v3',
    review_payload: {
      project: {
        project_number: 'P-TEST-001',
        project_name: 'Alpha Substation Upgrade',
      },
      scopes: [
        {
          scope_name: 'High-Voltage Switchgear',
          scope_type: 'ELECTRICAL',
          sort_order: 1,
          lines: [
            {
              apparatus_type: 'Circuit Breaker',
              test_standard: 'NETA MTS 7.6',
              qty: 4,
              hrs_per_unit: 2.5,
              section: 'Distribution Panel A',
              line_uid: 'line-001',
              drawing: null,
              designation: 'CB-1',
              notes: null,
            },
            {
              apparatus_type: 'Disconnect Switch',
              test_standard: 'NETA MTS 7.2',
              qty: 2,
              hrs_per_unit: 1.0,
              section: null,
              line_uid: 'line-002',
              drawing: null,
              designation: 'DS-1',
              notes: null,
            },
          ],
        },
        {
          scope_name: 'Low-Voltage Power Distribution',
          scope_type: 'ELECTRICAL',
          sort_order: 2,
          lines: [
            {
              apparatus_type: 'Transformer',
              test_standard: 'NETA MTS 7.1',
              qty: 1,
              hrs_per_unit: 8.0,
              section: 'Main Bus',
              line_uid: 'line-003',
              drawing: 'E-101',
              designation: 'TX-1',
              notes: null,
            },
          ],
        },
      ],
    },
    findings: [
      {
        code: 'MISSING_DESIGNATION',
        severity: 'blocking',
        ok: false,
        message: 'One or more lines are missing a designation reference.',
      },
      {
        code: 'PARTIAL_HOURS_ESTIMATE',
        severity: 'info',
        ok: true,
        message: 'Hours are estimated from the standard schedule.',
      },
    ],
  }

  // Intercept the POST upload call
  await page.route('**/api/v1/ops/intake', async (route) => {
    const req = route.request()
    if (req.method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(FIXED_RUN),
      })
    } else {
      await route.continue()
    }
  })

  // Navigate to the page
  const response = await page.goto('/pm-review/estimator-intake', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  // Trigger upload via file input
  await page.setInputFiles('input[type="file"]', {
    name: 'test-workbook.xlsm',
    mimeType: 'application/vnd.ms-excel.sheet.macroEnabled.12',
    buffer: Buffer.from('fake workbook content'),
  })

  // Wait for the tree to render
  await expect(page.getByText('High-Voltage Switchgear')).toBeVisible({ timeout: 10_000 })

  // Assert tree renders - check both scope names
  await expect(page.getByText('Low-Voltage Power Distribution')).toBeVisible()

  // Assert a finding message is visible
  await expect(page.getByText('One or more lines are missing a designation reference.')).toBeVisible()

  // Assert Approve button is disabled because there is an open blocking finding
  const approveBtn = page.getByRole('button', { name: /Approve/i })
  await expect(approveBtn).toBeVisible()
  await expect(approveBtn).toBeDisabled()

  // Assert NO dollar values appear anywhere on the page
  await expect(page.locator('body')).not.toContainText('$')
})
