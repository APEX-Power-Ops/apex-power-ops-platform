import { expect, test } from '@playwright/test'

test('breaker browser loads ETU, TMT, and EMT context settings and static curves', async ({ page }) => {
  let catalogRequests = 0
  let etuSearchRequests = 0
  let etuContextRequests = 0
  let etuSettingsRequests = 0
  let etuBreakerCascadeRequests = 0
  let etuPlotRequests = 0
  let tmtFacetRequests = 0
  let tmtFrameRequests = 0
  let tmtContextRequests = 0
  let tmtSettingsRequests = 0
  let tmtPlotRequests = 0
  let emtFacetRequests = 0
  let emtFrameRequests = 0
  let emtContextRequests = 0
  let emtSettingsRequests = 0
  let emtPlotRequests = 0

  await page.route('**/api/v1/neta/catalog/status', async (route) => {
    catalogRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        catalog: 'live',
        manufacturer_count: 63,
        sensor_count: 17831,
      }),
    })
  })

  await page.route('**/api/v1/neta/etu/search?*', async (route) => {
    etuSearchRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: 1,
        results: [
          {
            sensor_id: 3629,
            sensor_rating: 800,
            sensor_desc: '800 A',
            trip_style_id: 536,
            trip_style_name: 'Std',
            trip_type_id: 390,
            trip_type_name: 'Std',
            manufacturer_id: 62,
            manufacturer_name: '(Generic)',
            compatible_plug_values: [300, 400, 500, 600, 700, 800],
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/context/*', async (route) => {
    etuContextRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sensor_id: 3629,
        sensor_desc: '800 A',
        trip_style_id: 536,
        trip_style_name: 'Std',
        trip_type_name: 'Std',
        manufacturer_name: '(Generic)',
        rating: 800,
        resolved_equipment: {
          family: 'etu',
          family_label: 'ETU',
          resolved_id: 'sensor:3629',
          primary_label: '(Generic) · Std · Std',
          secondary_label: 'Std · 800A',
          breaker_context: {
            label: 'Std · 800A',
            source: 'trip_style_sensor_rating',
            manufacturer_name: '(Generic)',
            breaker_class: null,
            breaker_name: null,
            breaker_style_name: 'Std',
            type_name: null,
            style_name: null,
            tcc_number: null,
          },
          trip_unit: {
            manufacturer_name: '(Generic)',
            trip_type_name: 'Std',
            trip_style_name: 'Std',
            label: '(Generic) · Std · Std',
          },
          rating_context: {
            label: 'Sensor · 800 A',
            sensor_id: 3629,
            sensor_desc: '800 A',
            sensor_rating: 800,
            frame_id: null,
            frame_size: null,
            frame_desc: null,
            amp_ratings: [],
            section_id: null,
            section_name: null,
          },
        },
        has_ltpu: true,
        has_stpu: true,
        has_inst: true,
        has_gfpu: true,
        ltpu_calc: 3,
        stpu_calc: 6,
        inst_calc: 1,
        gfpu_calc: 0,
        ltpu_tol_hi: 20,
        ltpu_tol_lo: 0,
        stpu_tol_hi: 10,
        stpu_tol_lo: -10,
        inst_ovrtol_min: null,
        inst_ovrtol_max: null,
        gfpu_tol_hi: 10,
        gfpu_tol_lo: -10,
        ltpu_step: 0.1,
        stpu_step: 0.1,
        inst_step: 0.1,
        gfpu_step: 0.1,
        stpu_i2t: null,
        gfpu_i2t: null,
        ltd_func: 0,
        ltd_setting_method: 0,
        ltd_tol_hi: 50,
        ltd_tol_lo: 0,
        maint_available: false,
        maint_capable: false,
      }),
    })
  })

  await page.route('**/api/v1/neta/settings/*', async (route) => {
    etuSettingsRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        sensor_id: 3629,
        plug_values: [300, 400, 500, 600, 700, 800],
        ltpu_settings: [0.5, 0.6, 0.7],
        ltd_settings: [{ band: '1', label: '1', open_time: 2.4, clear_time: null, is_default: false }],
        std_settings: [{ band: 'Min', label: 'Min', open_time: 0.1, clear_time: 0.16, is_default: false }],
        gfd_settings: [{ band: 'Min', label: 'Min', open_time: 0.1, clear_time: 0.16, is_default: false }],
        ltd_multipliers: [1],
        stpu_settings: [1.5, 2, 2.5],
        inst_settings: [1.5, 2, 3],
        gfpu_settings: [0.2, 0.25, 0.3],
      }),
    })
  })

  await page.route('**/api/v1/neta/etu/breaker-cascade?*', async (route) => {
    etuBreakerCascadeRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        level: 'breakers',
        count: 3,
        scope: { manufacturer_id: 62, sensor_id: 3629 },
        manufacturers: [{ manufacturer_id: 62, manufacturer_name: '(Generic)', breaker_count: 3 }],
        breaker_classes: [
          { breaker_class: 'ICCB', breaker_count: 1 },
          { breaker_class: 'MCCB', breaker_count: 1 },
          { breaker_class: 'PCB', breaker_count: 1 },
        ],
        breakers: [
          {
            breaker_id: 122,
            breaker_name: 'Std',
            breaker_class: 'MCCB',
            manufacturer_id: 62,
            manufacturer_name: '(Generic)',
            style_count: 11,
          },
        ],
        breaker_styles: [],
      }),
    })
  })

  await page.route('**/api/v1/neta/plot-tcc', async (route) => {
    etuPlotRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {
          sensor_id: 3629,
          sensor_desc: '800 A',
          breaker_context_label: 'Std',
          breaker_context_source: 'operations_web_breaker_explorer',
          manufacturer: '(Generic)',
          trip_type: 'Std',
          trip_style: 'Std',
          trip_unit_manufacturer: '(Generic)',
          trip_unit_type: 'Std',
          trip_unit_style: 'Std',
          plug_rating: 300,
          maint_mode: false,
          maint_capable: false,
          maint_support_level: 'none',
          plot_disclaimer: null,
          resolved_equipment: null,
        },
        warnings: [],
        curves: [
          {
            id: 'inst_open',
            element: 'INST',
            phase: 'open',
            line_style: 'solid',
            points: [
              { amps: 450, seconds: 0.05 },
              { amps: 1800, seconds: 0.05 },
            ],
          },
        ],
        expected_markers: [
          {
            id: 'ltpu_expected',
            element: 'LTPU',
            kind: 'pickup',
            render_hint: 'vertical_marker',
            test_multiple: 1,
            expected_current: 150,
            expected_time: null,
            limit_low: 150,
            limit_high: 180,
            curve_ref: null,
            label: 'LTPU 1x',
          },
        ],
        table_rows: [
          {
            element: 'LTPU',
            kind: 'pickup',
            setting: 0.5,
            test_multiple: 1,
            expected_current: 150,
            limit_low: 150,
            limit_high: 180,
            expected_time: null,
            time_limit_low: null,
            time_limit_high: null,
            calc_method: 'plugtap',
            notes: 'ramp pickup',
          },
          {
            element: 'LTD',
            kind: 'delay',
            setting: 2.4,
            test_multiple: 3,
            expected_current: 450,
            limit_low: null,
            limit_high: null,
            expected_time: 8.5,
            time_limit_low: 8.5,
            time_limit_high: 12.75,
            calc_method: 'delay',
            notes: 'long-time delay',
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/tmt/facets?*', async (route) => {
    tmtFacetRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_matching_frames: 1,
        active_filters: { breaker_class: 'MCCB' },
        facets: [
          { name: 'breaker_class', values: ['MCCB'], cardinality: 1 },
          { name: 'frame_size', values: ['630.0'], cardinality: 1 },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/tmt/frames?*', async (route) => {
    tmtFrameRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: 1,
        frames: [
          {
            frame_id: 8038,
            breaker_style_id: 3281,
            breaker_class: 'mccb',
            frame_size: '630.0',
            manufacturer_name: 'ABB',
            breaker_name: 'Tmax [IEC]',
            breaker_style_name: 'T5V-630-TMG',
            standard: 1,
            matched_amp_rating: null,
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/tmt/context/*', async (route) => {
    tmtContextRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        frame_id: 8038,
        breaker_style_id: 3281,
        breaker_class: 'mccb',
        frame_size: '630.0',
        manufacturer_name: 'ABB',
        breaker_name: 'Tmax [IEC]',
        breaker_style_name: 'T5V-630-TMG',
        standard: 1,
        available_trip_classes: [4, 5],
        amp_rating_count: 2,
        setting_count: 2,
        thermal_adjustment_count: 1,
        resolved_equipment: {
          family: 'tmt',
          family_label: 'TMT',
          resolved_id: 'tmt_frame:8038',
          primary_label: 'ABB · Tmax [IEC]',
          secondary_label: 'T5V-630-TMG · mccb · 630.0',
          breaker_context: null,
          trip_unit: null,
          rating_context: null,
        },
      }),
    })
  })

  await page.route('**/api/v1/neta/tmt/settings/*', async (route) => {
    tmtSettingsRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        frame_id: 8038,
        available_trip_classes: [4, 5],
        amp_ratings: [{ rating: 320, max_override: null }],
        settings: [{ value: 2.5, label: '2.5X', tol_lo: -10, tol_hi: 10 }],
        thermal_adjustments: [700],
      }),
    })
  })

  await page.route('**/api/v1/neta/tmt/plot-tcc', async (route) => {
    tmtPlotRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {
          frame_id: 8038,
          breaker_style_id: 3281,
          breaker_class: 'mccb',
          frame_size: '630.0',
          manufacturer_name: 'ABB',
          breaker_name: 'Tmax [IEC]',
          breaker_style_name: 'T5V-630-TMG',
          standard: 1,
          selected_trip_class: 4,
          selected_amp_rating: 320,
          selected_max_override: null,
          selected_setting: 2.5,
          selected_setting_label: '2.5X',
          selected_setting_tol_lo: -10,
          selected_setting_tol_hi: 10,
          selected_thermal_adjustment: 700,
          selections_applied_to_curve: false,
          plot_disclaimer: 'Nominal TMT curve only.',
          resolved_equipment: null,
        },
        warnings: ['TMT selections validated and surfaced in metadata.'],
        curves: [
          {
            id: 'tmt_class_4',
            curve_family: 'TMT',
            trip_class: 4,
            line_style: 'solid',
            points: [
              { amps: 0.8, seconds: 10000 },
              { amps: 5.05, seconds: 2.95 },
            ],
          },
        ],
        raw_points: [],
      }),
    })
  })

  await page.route('**/api/v1/neta/emt/facets', async (route) => {
    emtFacetRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_matching_frames: 1,
        active_filters: {},
        facets: [
          { name: 'manufacturer_id', values: [85], cardinality: 1 },
          { name: 'trip_char', values: [5], cardinality: 1 },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/emt/frames?*', async (route) => {
    emtFrameRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: 1,
        frames: [
          {
            emt_id: 191,
            frame_id: 2953,
            manufacturer_id: 85,
            manufacturer_name: 'Allis-Chalmers',
            type_name: 'SOC Trip',
            style_name: 'LI(Max LT)',
            tcc_number: null,
            trip_char: 5,
            trip_plug: 0,
            frame_size: 250,
            frame_desc: '250',
            amp_rating_count: 1,
            section_count: 2,
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/emt/context/*', async (route) => {
    emtContextRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        emt_id: 191,
        frame_id: 2953,
        manufacturer_id: 85,
        manufacturer_name: 'Allis-Chalmers',
        type_name: 'SOC Trip',
        style_name: 'LI(Max LT)',
        tcc_number: null,
        trip_char: 5,
        trip_plug: 0,
        frame_size: 250,
        frame_desc: '250',
        amp_ratings: [250],
        sections: [
          {
            section_id: 6200,
            name: 'LT Pickup',
            sec_char: 1,
            curve_type: 0,
            pickup_calc: 0,
            pickup_setting: 1,
            step_size: 0.1,
            current_calc: 0,
            pickup_tol_lo: -10,
            pickup_tol_hi: 10,
            band_count: 1,
            pickup_count: 2,
          },
        ],
        resolved_equipment: {
          family: 'emt',
          family_label: 'EMT',
          resolved_id: 'emt_frame:2953',
          primary_label: 'Allis-Chalmers · SOC Trip · LI(Max LT)',
          secondary_label: '250',
          breaker_context: null,
          trip_unit: null,
          rating_context: null,
        },
      }),
    })
  })

  await page.route('**/api/v1/neta/emt/settings/*', async (route) => {
    emtSettingsRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        section_id: 6200,
        name: 'LT Pickup',
        sec_char: 1,
        curve_type: 0,
        pickup_calc: 0,
        pickup_setting: 1,
        step_size: 0.1,
        current_calc: 0,
        pickup_tol_lo: -10,
        pickup_tol_hi: 10,
        pickups: [
          { setting: 0.8, description: '80%' },
          { setting: 1.6, description: '160%' },
        ],
        bands: [
          {
            band_id: 12354,
            band_name: 'Max',
            ordinal: 1,
            current_at: 1,
            curve_point_count: 22,
            curve_classes: [0, 1],
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/neta/emt/plot-tcc', async (route) => {
    emtPlotRequests += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {
          emt_id: 191,
          frame_id: 2953,
          section_id: 6200,
          band_id: 12354,
          manufacturer_id: 85,
          manufacturer_name: 'Allis-Chalmers',
          type_name: 'SOC Trip',
          style_name: 'LI(Max LT)',
          tcc_number: null,
          frame_size: 250,
          frame_desc: '250',
          section_name: 'LT Pickup',
          sec_char: 1,
          curve_type: 0,
          pickup_calc: 0,
          pickup_setting: 1,
          current_calc: 0,
          band_name: 'Max',
          band_ordinal: 1,
          current_at: 1,
          available_curve_classes: [0, 1],
          selected_curve_class: null,
          selections_applied_to_curve: false,
          plot_disclaimer: 'Raw EMT point-data plot only.',
          resolved_equipment: null,
        },
        warnings: ['Multiple stored EMT curve classes returned.'],
        curves: [
          {
            id: 'emt_band_12354_class_0',
            curve_family: 'EMT',
            band_id: 12354,
            curve_class: 0,
            class_label: 'opening',
            line_style: 'solid',
            points: [
              { amps: 0.99, seconds: 1000 },
              { amps: 20.84, seconds: 6.06 },
            ],
          },
          {
            id: 'emt_band_12354_class_1',
            curve_family: 'EMT',
            band_id: 12354,
            curve_class: 1,
            class_label: 'clearing',
            line_style: 'dashed',
            points: [
              { amps: 1, seconds: 1000 },
              { amps: 23.06, seconds: 19.65 },
            ],
          },
        ],
      }),
    })
  })

  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'Browse breaker resources through ETU, TMT, and EMT routes.' }),
  ).toBeVisible()
  await expect(page.getByText('17831')).toBeVisible()
  expect(catalogRequests).toBe(1)

  await page.getByLabel('ETU search').fill('   ')
  await page.getByRole('button', { name: 'Browse ETU' }).click()
  await expect(page.getByText('Enter an ETU search term before browsing governed sensor rows.')).toBeVisible()
  expect(etuSearchRequests).toBe(0)

  await page.getByLabel('ETU search').fill('GE')
  await page.getByRole('button', { name: 'Browse ETU' }).click()
  await expect(page.locator('[data-breaker-results]')).toContainText('(Generic)')
  expect(etuSearchRequests).toBe(1)
  expect(etuContextRequests).toBe(0)

  await page.getByRole('button', { name: 'Load Context + Curve' }).click()
  await expect(page.getByText('Select an ETU result before loading context, settings, and plot data.')).toBeVisible()

  await page.getByLabel('ETU resource').selectOption('3629')
  await page.getByRole('button', { name: 'Load Context + Curve' }).click()
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="etu"] [data-breaker-curve-chart]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toContainText('Breaker matches')
  await expect(page.locator('[data-breaker-selection-panel="etu"] [data-neta-test-plan-table]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toContainText('NETA Test Plan')
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toContainText('LTPU')
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toContainText('150A')
  await expect(page.locator('[data-breaker-selection-panel="etu"]')).toContainText('8.500s')
  expect(etuContextRequests).toBe(1)
  expect(etuSettingsRequests).toBe(1)
  expect(etuBreakerCascadeRequests).toBe(1)
  expect(etuPlotRequests).toBe(1)

  await page.getByLabel('Trip Unit Type').selectOption('tmt')
  await page.getByRole('button', { name: 'Browse TMT' }).click()
  await expect(page.getByLabel('TMT resource')).toBeVisible()
  await page.getByLabel('TMT resource').selectOption('8038')
  await page.getByRole('button', { name: 'Load Context + Curve' }).click()
  await expect(page.locator('[data-breaker-selection-panel="tmt"]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="tmt"] [data-breaker-curve-chart]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="tmt"]')).toContainText('TMT selections validated')
  await expect(page.locator('[data-breaker-selection-panel="tmt"]')).toContainText('800A')
  await expect(page.locator('[data-breaker-selection-panel="tmt"]')).toContainText('720A')
  await expect(page.locator('[data-breaker-selection-panel="tmt"]')).toContainText('880A')
  expect(tmtFacetRequests).toBe(1)
  expect(tmtFrameRequests).toBe(1)
  expect(tmtContextRequests).toBe(1)
  expect(tmtSettingsRequests).toBe(1)
  expect(tmtPlotRequests).toBe(1)

  await page.getByLabel('Trip Unit Type').selectOption('emt')
  await page.getByRole('button', { name: 'Browse EMT' }).click()
  await expect(page.getByLabel('EMT resource')).toBeVisible()
  await page.getByLabel('EMT resource').selectOption('2953')
  await page.getByRole('button', { name: 'Load Context + Curve' }).click()
  await expect(page.locator('[data-breaker-selection-panel="emt"]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="emt"] [data-breaker-curve-chart]')).toBeVisible()
  await expect(page.locator('[data-breaker-selection-panel="emt"]')).toContainText('Multiple stored EMT curve classes')
  await expect(page.locator('[data-breaker-selection-panel="emt"]')).toContainText('0.72A')
  await expect(page.locator('[data-breaker-selection-panel="emt"]')).toContainText('0.88A')
  expect(emtFacetRequests).toBe(1)
  expect(emtFrameRequests).toBe(1)
  expect(emtContextRequests).toBe(1)
  expect(emtSettingsRequests).toBe(1)
  expect(emtPlotRequests).toBe(1)

  await page.screenshot({
    path: 'test-results/breaker-resource-explorer-smoke.png',
    fullPage: true,
  })
})
