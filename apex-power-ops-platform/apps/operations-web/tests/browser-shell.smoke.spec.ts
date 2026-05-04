import { expect, test } from '@playwright/test'

test('root shell renders and blocks invalid apparatus IDs before backend fetch', async ({
  page,
}) => {
  let relayContextRequests = 0

  await page.route('**/api/v1/neta/relay/sections?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: 1,
        sections: [
          {
            manufacturer_source_id: 10,
            relay_type: 'SEL-351',
            relay_device_source_id: 1001,
            device_function: 'Phase OC',
            device_ordinal: 1,
            standard_code: 1,
            dftype_code: 1,
            voltage_restraint_kind: null,
            td_section_source_id: 101,
            td_section_name: 'SEL-51A phase overcurrent',
            family_code: 2,
            family_name: 'iec',
            storage_kind: 'constants',
            supported: true,
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/relay/context/*', async (route) => {
    relayContextRequests += 1
    await route.abort()
  })

  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'Operations Web now has a real frontend boundary.' }),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Validation Surface' })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Browse relay TD-sections through the governed control-plane routes.' }),
  ).toBeVisible()

  await page.getByLabel('Apparatus UUID').fill('invalid-id')
  await page.getByRole('button', { name: 'Load Resources' }).click()

  await expect(
    page.getByText('Enter a valid apparatus UUID to read the governed backend study-resource seam.'),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Search Relay Sections' }).click()
  await page.getByLabel('Primary TD-section').selectOption('101')
  await page.getByLabel('Preview multiples').fill('bad-input')
  await page.getByRole('button', { name: 'Load Selected Sections' }).click()

  await expect(
    page.getByText('Enter relay current multiples greater than 1, separated by commas.'),
  ).toBeVisible()
  expect(relayContextRequests).toBe(0)
})

test('relay browser requires explicit selection before loading bounded compare details', async ({ page }) => {
  let relayContextRequests = 0
  let relaySettingsRequests = 0
  let relayPlotRequests = 0

  await page.route('**/api/v1/neta/relay/sections?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: 2,
        sections: [
          {
            manufacturer_source_id: 10,
            relay_type: 'SEL-351',
            relay_device_source_id: 1001,
            device_function: 'Phase OC',
            device_ordinal: 1,
            standard_code: 1,
            dftype_code: 1,
            voltage_restraint_kind: null,
            td_section_source_id: 101,
            td_section_name: 'SEL-51A phase overcurrent',
            family_code: 2,
            family_name: 'iec',
            storage_kind: 'constants',
            supported: true,
          },
          {
            manufacturer_source_id: 20,
            relay_type: 'Legacy relay',
            relay_device_source_id: 2002,
            device_function: 'Ground OC',
            device_ordinal: 2,
            standard_code: 2,
            dftype_code: 3,
            voltage_restraint_kind: null,
            td_section_source_id: 202,
            td_section_name: 'Legacy unsupported TD-section',
            family_code: 8,
            family_name: 'lrm',
            storage_kind: 'constants',
            supported: false,
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/relay/context/*', async (route) => {
    relayContextRequests += 1
    const tdSectionSourceId = Number(route.request().url().split('/').pop())
    const payload = tdSectionSourceId === 101
      ? {
          manufacturer_source_id: 10,
          relay_type: 'SEL-351',
          relay_device_source_id: 1001,
          device_function: 'Phase OC',
          device_ordinal: 1,
          standard_code: 1,
          dftype_code: 1,
          voltage_restraint_kind: null,
          td_section_source_id: 101,
          td_section_name: 'SEL-51A phase overcurrent',
          family_code: 2,
          family_name: 'iec',
          storage_kind: 'constants',
          supported: true,
          unsupported_reason: null,
          line_section_count: 1,
          range_count: 2,
          curve_parent_count: 1,
          preview_option_count: 2,
          line_sections: [
            {
              line_section_source_id: 5001,
              section_number: 1,
              section_name: 'Phase OC section',
              pickup: 2.5,
              secondary_i_code: null,
              amps_calc_mode: null,
              use_toc_multiplier: false,
            },
          ],
        }
      : {
          manufacturer_source_id: 20,
          relay_type: 'Legacy relay',
          relay_device_source_id: 2002,
          device_function: 'Ground OC',
          device_ordinal: 2,
          standard_code: 2,
          dftype_code: 3,
          voltage_restraint_kind: null,
          td_section_source_id: 202,
          td_section_name: 'Legacy unsupported TD-section',
          family_code: 8,
          family_name: 'lrm',
          storage_kind: 'constants',
          supported: false,
          unsupported_reason: 'Unsupported family remains explicit in the governed API.',
          line_section_count: 1,
          range_count: 1,
          curve_parent_count: 0,
          preview_option_count: 0,
          line_sections: [
            {
              line_section_source_id: 9001,
              section_number: 2,
              section_name: 'Ground OC section',
              pickup: 3.1,
              secondary_i_code: null,
              amps_calc_mode: null,
              use_toc_multiplier: false,
            },
          ],
        }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    })
  })

  await page.route('**/api/v1/neta/relay/settings/*', async (route) => {
    relaySettingsRequests += 1
    const tdSectionSourceId = Number(route.request().url().split('/').pop())
    const payload = tdSectionSourceId === 101
      ? {
          td_section_source_id: 101,
          family_code: 2,
          family_name: 'iec',
          storage_kind: 'constants',
          supported: true,
          unsupported_reason: null,
          line_sections: [
            {
              line_section_source_id: 5001,
              section_number: 1,
              section_name: 'Phase OC section',
              pickup: 2.5,
              secondary_i_code: null,
              amps_calc_mode: null,
              use_toc_multiplier: false,
            },
          ],
          ranges: [],
          curve_parents: [
            {
              curve_parent_source_id: 7001,
              storage_kind: 'constants',
              curve_name: 'IEC Very Inverse',
              curve_parent_ordinal: 1,
              min_pickup: 1,
              max_pickup: 10,
              is_discrete: false,
              step_size: null,
              horizontal_amps_code: null,
              preview_option_count: 2,
            },
          ],
          preview_options: [
            {
              curve_parent_source_id: 7001,
              storage_kind: 'constants',
              curve_name: 'IEC Very Inverse',
              curve_ordinal: 1,
              source_ordinal: null,
              time_dial: 1,
              td_desc: null,
              point_count: null,
              current_min: null,
              current_max: null,
              coefficients: { v_k: 13.5, v_e: 1 },
            },
            {
              curve_parent_source_id: 7001,
              storage_kind: 'constants',
              curve_name: 'IEC Alternate',
              curve_ordinal: 2,
              source_ordinal: null,
              time_dial: 1,
              td_desc: null,
              point_count: null,
              current_min: null,
              current_max: null,
              coefficients: { v_k: 20, v_e: 2 },
            },
          ],
        }
      : {
          td_section_source_id: 202,
          family_code: 8,
          family_name: 'lrm',
          storage_kind: 'constants',
          supported: false,
          unsupported_reason: 'Unsupported family remains explicit in the governed API.',
          line_sections: [
            {
              line_section_source_id: 9001,
              section_number: 2,
              section_name: 'Ground OC section',
              pickup: 3.1,
              secondary_i_code: null,
              amps_calc_mode: null,
              use_toc_multiplier: false,
            },
          ],
          ranges: [],
          curve_parents: [],
          preview_options: [],
        }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    })
  })

  await page.route('**/api/v1/neta/relay/plot-tcc', async (route) => {
    relayPlotRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {
          td_section_source_id: 101,
          relay_device_source_id: 1001,
          manufacturer_source_id: 10,
          relay_type: 'SEL-351',
          device_function: 'Phase OC',
          td_section_name: 'SEL-51A phase overcurrent',
          family_code: 2,
          family_name: 'iec',
          storage_kind: 'constants',
          supported: true,
          status: 'supported',
          unsupported_reason: null,
          selected_curve_parent_source_id: 7001,
          selected_curve_name: 'IEC Very Inverse',
          selected_curve_ordinal: 1,
          selected_source_ordinal: null,
          selected_time_dial: 1,
          selected_td_desc: null,
          plot_disclaimer: 'Preview uses the governed relay API output.',
        },
        warnings: [],
        curves: [
          {
            id: 'curve-101',
            family_name: 'iec',
            storage_kind: 'constants',
            curve_name: 'IEC Very Inverse',
            curve_parent_source_id: 7001,
            curve_ordinal: 1,
            source_ordinal: null,
            time_dial: 1,
            td_desc: null,
            points: [
              { current_multiple: 2, seconds: 13.5 },
              { current_multiple: 5, seconds: 4.2 },
              { current_multiple: 10, seconds: 1.5 },
            ],
          },
        ],
      }),
    })
  })

  await page.goto('/')

  await page.getByRole('button', { name: 'Search Relay Sections' }).click()
  await expect(
    page.getByText('Select a primary TD-section before the browser treats any relay preview as current.'),
  ).toBeVisible()
  expect(relayContextRequests).toBe(0)
  expect(relaySettingsRequests).toBe(0)
  expect(relayPlotRequests).toBe(0)

  await page.getByRole('button', { name: 'Load Selected Sections' }).click()
  await expect(page.getByText('Select a primary TD-section before loading relay details.')).toBeVisible()
  expect(relayContextRequests).toBe(0)

  await page.getByLabel('Primary TD-section').selectOption('101')
  await page.getByLabel('Compare TD-section').selectOption('202')
  await page.getByRole('button', { name: 'Load Selected Sections' }).click()

  await expect(page.locator('.relay-selection-panel').getByText('Primary selection', { exact: true })).toBeVisible()
  await expect(page.locator('.relay-selection-panel').getByText('Compare selection', { exact: true })).toBeVisible()
  await expect(
    page.getByText('Preview is currently showing the first published governed option out of 2 options for this TD-section.'),
  ).toBeVisible()
  await expect(
    page.getByText('Unsupported sections remain selectable for disclosure-only compare.'),
  ).toHaveCount(2)
  await expect(page.getByText('Unsupported family remains explicit in the governed API.')).toBeVisible()

  const panels = page.locator('.relay-selection-panel')
  await expect(panels).toHaveCount(2)

  for (const view of ['context', 'settings', 'preview'] as const) {
    await expect(
      page.locator('.relay-selection-panel [data-relay-compare-view="' + view + '"]'),
    ).toHaveCount(2)
  }

  const primaryPanel = panels.nth(0)
  const comparePanel = panels.nth(1)
  const primaryDetail = page.locator('[data-relay-detail-surface="primary"]')

  await expect(primaryDetail).toBeVisible()
  await expect(primaryDetail.getByRole('heading', { name: 'Primary TD-section detail' })).toBeVisible()
  await expect(
    primaryDetail.locator('[data-relay-detail-view="curve-parents"] strong', { hasText: 'IEC Very Inverse' }),
  ).toBeVisible()
  await expect(primaryDetail.locator('[data-relay-detail-view="preview-options"]')).toContainText('curve 1')

  await expect(primaryPanel.locator('[data-relay-compare-view="context"] dd', { hasText: 'iec' })).toBeVisible()
  await expect(primaryPanel.locator('[data-relay-compare-view="context"] dd', { hasText: 'constants' })).toBeVisible()
  await expect(primaryPanel.getByText('101', { exact: true }).first()).toBeVisible()
  await expect(primaryPanel.locator('[data-relay-compare-view="settings"] strong', { hasText: 'Phase OC section' })).toBeVisible()
  await expect(primaryPanel.locator('[data-relay-compare-view="preview"] dd', { hasText: 'IEC Very Inverse' })).toBeVisible()

  await expect(comparePanel.locator('[data-relay-compare-view="context"] dd', { hasText: 'lrm' })).toBeVisible()
  await expect(comparePanel.getByText('202', { exact: true }).first()).toBeVisible()
  await expect(
    comparePanel.locator('[data-relay-compare-view="settings"] strong', { hasText: 'Ground OC section' }),
  ).toBeVisible()
  await expect(
    comparePanel.locator('[data-relay-compare-view="preview"]').getByText(
      'No preview curve was returned for this TD-section.',
    ),
  ).toBeVisible()

  expect(relayContextRequests).toBe(2)
  expect(relaySettingsRequests).toBe(2)
  expect(relayPlotRequests).toBe(1)
})

test('re-homed browser surfaces render their expected headings in a real browser', async ({ page }) => {
  const integrationResponse = await page.goto('/integration-dashboard/index.html')
  expect(integrationResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Cross-Surface Integration Test Dashboard/)

  const leadResponse = await page.goto('/lead-ops/index.html')
  expect(leadResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX Lead Surface/)

  const pmDriversResponse = await page.goto('/pm-review/index.html')
  expect(pmDriversResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Drivers Review/)

  const pmApprovalResponse = await page.goto('/pm-review/approval-surface.html')
  expect(pmApprovalResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Approval Surface/)

  const pmScheduleResponse = await page.goto('/pm-review/schedule.html')
  expect(pmScheduleResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Schedule Review/)

  const pmTracerResponse = await page.goto('/pm-review/tracer.html')
  expect(pmTracerResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Upstream Tracer Review/)

  const pmVarianceResponse = await page.goto('/pm-review/variance.html')
  expect(pmVarianceResponse?.ok()).toBeTruthy()
  await expect(page).toHaveTitle(/APEX PM Variance Review/)
})