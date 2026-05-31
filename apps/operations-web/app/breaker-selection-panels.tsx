import type { ReactNode } from 'react'
import type {
  AvailableSettingsResponse,
  EMTFacetsResponse,
  EMTFrameContext,
  EMTFrameSearchResult,
  EMTPlotRequest,
  EMTPlotResponse,
  EMTSectionSettingsResponse,
  EtuBreakerCascadeResponse,
  EtuPlotRequest,
  EtuPlotResponse,
  EtuPlotTableRow,
  EtuSearchResult,
  SensorCalcContext,
  TMTFacetsResponse,
  TMTFrameContext,
  TMTFrameSearchResult,
  TMTPlotRequest,
  TMTPlotResponse,
  TMTSettingsResponse,
} from '../lib/breaker-resources'

export type BreakerSelectionData =
  | {
      family: 'etu'
      searchResult: EtuSearchResult
      context: SensorCalcContext
      settings: AvailableSettingsResponse
      breakerCascade: EtuBreakerCascadeResponse
      plot: EtuPlotResponse | null
      plotRequest: EtuPlotRequest | null
    }
  | {
      family: 'tmt'
      frame: TMTFrameSearchResult
      context: TMTFrameContext
      settings: TMTSettingsResponse
      plot: TMTPlotResponse | null
      plotRequest: TMTPlotRequest | null
    }
  | {
      family: 'emt'
      frame: EMTFrameSearchResult
      context: EMTFrameContext
      settings: EMTSectionSettingsResponse | null
      plot: EMTPlotResponse | null
      plotRequest: EMTPlotRequest | null
    }

type ChartCurve = {
  id: string
  label: string
  lineStyle: string
  points: {
    amps: number
    seconds: number
  }[]
}

type ChartMarker = {
  id: string
  label: string
  amps: number
  seconds: number | null
  renderHint: string
}

type SearchCardProps = {
  selected: boolean
}

type FacetPanelProps = {
  title: string
  total: number
  facets: TMTFacetsResponse['facets'] | EMTFacetsResponse['facets']
}

type TestPlanDisplayRow = {
  key: string
  element: string
  setting: string
  testCurrent: string
  expectedPickup: string
  limitLow: string
  limitHigh: string
  expectedTime: string
  timeLimitLow: string
  timeLimitHigh: string
  method: string
}

function formatNumber(value: number | null | undefined, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a'
  }

  const rounded = Math.round(value)
  return Math.abs(value - rounded) < 0.000001 ? String(rounded) : value.toFixed(digits)
}

function formatNullable(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') {
    return 'n/a'
  }

  return String(value)
}

function formatUnitValue(value: number | null | undefined, unit: string, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a'
  }

  return `${formatNumber(value, digits)}${unit}`
}

function formatMultiplier(value: number | null | undefined) {
  return formatUnitValue(value, 'x', 2)
}

function formatCurrent(value: number | null | undefined) {
  return formatUnitValue(value, 'A', 2)
}

function formatSeconds(value: number | null | undefined) {
  return formatUnitValue(value, 's', 3)
}

function bandLimit(expected: number | null | undefined, tolerance: number | null | undefined) {
  if (typeof expected !== 'number' || Number.isNaN(expected) || typeof tolerance !== 'number' || Number.isNaN(tolerance)) {
    return null
  }

  return expected * (1 + tolerance / 100)
}

function formatToleranceBand(
  expected: number | null | undefined,
  toleranceLow: number | null | undefined,
  toleranceHigh: number | null | undefined,
  unit = '',
) {
  const low = bandLimit(expected, toleranceLow)
  const high = bandLimit(expected, toleranceHigh)
  if (typeof expected === 'number' && !Number.isNaN(expected) && low !== null && high !== null) {
    return `${formatUnitValue(expected, unit)} -> [${formatUnitValue(low, unit)}, ${formatUnitValue(high, unit)}]`
  }

  if (typeof toleranceLow === 'number' || typeof toleranceHigh === 'number') {
    return `tolerance ${formatNumber(toleranceLow, 1)}% to ${formatNumber(toleranceHigh, 1)}%`
  }

  return 'n/a'
}

function isActiveEtuTestRow(row: EtuPlotTableRow) {
  const method = row.calc_method?.trim().toLowerCase()
  if (method === '-1' || method === 'none' || method === 'absent') {
    return false
  }

  return row.expected_current !== null || row.expected_time !== null
}

function etuTestPlanRows(rows: EtuPlotTableRow[]): TestPlanDisplayRow[] {
  return rows.filter(isActiveEtuTestRow).map((row, index) => ({
    key: `${row.element}-${row.kind}-${index}`,
    element: row.element,
    setting: formatNullable(row.setting),
    testCurrent: formatMultiplier(row.test_multiple),
    expectedPickup: formatCurrent(row.expected_current),
    limitLow: formatCurrent(row.limit_low),
    limitHigh: formatCurrent(row.limit_high),
    expectedTime: formatSeconds(row.expected_time),
    timeLimitLow: formatSeconds(row.time_limit_low),
    timeLimitHigh: formatSeconds(row.time_limit_high),
    method: [row.calc_method, row.notes].filter(Boolean).join(' · ') || 'server',
  }))
}

function tmtTestPlanRows(selection: Extract<BreakerSelectionData, { family: 'tmt' }>): TestPlanDisplayRow[] {
  const expectedPickup =
    typeof selection.plot?.meta.selected_amp_rating === 'number' && typeof selection.plot.meta.selected_setting === 'number'
      ? selection.plot.meta.selected_amp_rating * selection.plot.meta.selected_setting
      : null
  const low = bandLimit(expectedPickup, selection.plot?.meta.selected_setting_tol_lo)
  const high = bandLimit(expectedPickup, selection.plot?.meta.selected_setting_tol_hi)
  const selectedSetting = selection.plot?.meta.selected_setting ?? selection.settings.settings[0]?.value ?? null
  const selectedLabel = selection.plot?.meta.selected_setting_label ?? selection.settings.settings[0]?.label ?? null

  if (
    expectedPickup === null &&
    selectedSetting === null &&
    selection.plot?.meta.selected_setting_tol_lo === null &&
    selection.plot?.meta.selected_setting_tol_hi === null
  ) {
    return []
  }

  return [
    {
      key: 'tmt-selected-setting',
      element: 'TMT pickup',
      setting: selectedLabel ?? formatNullable(selectedSetting),
      testCurrent: formatMultiplier(selectedSetting),
      expectedPickup: formatCurrent(expectedPickup),
      limitLow: formatCurrent(low),
      limitHigh: formatCurrent(high),
      expectedTime: 'n/a',
      timeLimitLow: 'n/a',
      timeLimitHigh: 'n/a',
      method: 'selected setting tolerance',
    },
  ]
}

function emtTestPlanRows(selection: Extract<BreakerSelectionData, { family: 'emt' }>): TestPlanDisplayRow[] {
  if (!selection.settings) {
    return []
  }

  const pickup = selection.settings.pickups.find((option) => typeof option.setting === 'number')?.setting ?? null
  const expectedPickup = pickup ?? (typeof selection.settings.pickup_setting === 'number' ? selection.settings.pickup_setting : null)
  const low = bandLimit(expectedPickup, selection.settings.pickup_tol_lo)
  const high = bandLimit(expectedPickup, selection.settings.pickup_tol_hi)

  if (expectedPickup === null && selection.settings.pickup_tol_lo === null && selection.settings.pickup_tol_hi === null) {
    return []
  }

  return [
    {
      key: 'emt-section-pickup',
      element: selection.settings.name ?? 'EMT pickup',
      setting: formatNullable(selection.settings.pickup_setting ?? pickup),
      testCurrent: formatMultiplier(selection.settings.current_calc),
      expectedPickup: formatCurrent(expectedPickup),
      limitLow: formatCurrent(low),
      limitHigh: formatCurrent(high),
      expectedTime: 'n/a',
      timeLimitLow: 'n/a',
      timeLimitHigh: 'n/a',
      method: 'section pickup tolerance',
    },
  ]
}

function NetaTestPlanTable({
  rows,
  caption,
}: {
  rows: TestPlanDisplayRow[]
  caption: string
}) {
  return (
    <BreakerCompareSection title="NETA Test Plan" view="neta-test-plan">
      {rows.length > 0 ? (
        <div className="breaker-test-plan-table-wrap" data-neta-test-plan-table>
          <table className="breaker-test-plan-table">
            <caption>{caption}</caption>
            <thead>
              <tr>
                <th>Element</th>
                <th>Setting</th>
                <th>Test current (xmult)</th>
                <th>Expected pickup</th>
                <th>Lo</th>
                <th>Hi</th>
                <th>Expected time</th>
                <th>Time-lo</th>
                <th>Time-hi</th>
                <th>Method</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key}>
                  <td>{row.element}</td>
                  <td>{row.setting}</td>
                  <td>{row.testCurrent}</td>
                  <td>{row.expectedPickup}</td>
                  <td>{row.limitLow}</td>
                  <td>{row.limitHigh}</td>
                  <td>{row.expectedTime}</td>
                  <td>{row.timeLimitLow}</td>
                  <td>{row.timeLimitHigh}</td>
                  <td>{row.method}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="resource-banner resource-banner-neutral relay-inline-banner">
          No per-element tolerance rows were returned for this selection.
        </p>
      )}
    </BreakerCompareSection>
  )
}

function countSettings(settings: AvailableSettingsResponse) {
  return (
    settings.plug_values.length +
    settings.ltpu_settings.length +
    settings.ltd_settings.length +
    settings.stpu_settings.length +
    settings.std_settings.length +
    settings.inst_settings.length +
    settings.gfpu_settings.length +
    settings.gfd_settings.length
  )
}

function collectWarnings(selection: BreakerSelectionData) {
  const warnings = new Set<string>()

  if (selection.family === 'etu') {
    for (const warning of selection.plot?.warnings ?? []) {
      warnings.add(warning)
    }
    if (!selection.plotRequest) {
      warnings.add('No complete ETU setting bundle was available for a static plot request.')
    }
    if (selection.plot && selection.plot.curves.length === 0) {
      warnings.add('The ETU plot route returned no nominal curve segments for this selection.')
    }
    return Array.from(warnings)
  }

  if (selection.family === 'tmt') {
    for (const warning of selection.plot?.warnings ?? []) {
      warnings.add(warning)
    }
    if (!selection.plotRequest) {
      warnings.add('No TMT trip class was available for a static plot request.')
    }
    if (selection.plot && selection.plot.curves.length === 0) {
      warnings.add('The TMT plot route returned no nominal curve for this frame.')
    }
    return Array.from(warnings)
  }

  for (const warning of selection.plot?.warnings ?? []) {
    warnings.add(warning)
  }
  if (!selection.settings) {
    warnings.add('No EMT section with published settings was available for this frame.')
  }
  if (selection.settings && !selection.plotRequest) {
    warnings.add('No EMT band with curve points was available for this section.')
  }
  if (selection.plot && selection.plot.curves.length === 0) {
    warnings.add('The EMT plot route returned no raw point-data curves for this band.')
  }

  return Array.from(warnings)
}

function BreakerCompareSection({
  title,
  view,
  children,
}: {
  title: string
  view: string
  children: ReactNode
}) {
  return (
    <section className="relay-compare-section" data-breaker-detail-view={view}>
      <header className="relay-compare-section-header">
        <span className="relay-compare-section-eyebrow">Breaker view</span>
        <h4 className="relay-compare-section-title">{title}</h4>
      </header>
      {children}
    </section>
  )
}

export function BreakerFacetPanel({ title, total, facets }: FacetPanelProps) {
  if (facets.length === 0) {
    return null
  }

  return (
    <aside className="breaker-facet-panel" aria-label={title}>
      <div className="resource-item-row">
        <span className="resource-chip">facets</span>
        <span className="resource-chip resource-chip-muted">{total} matching</span>
      </div>
      <h3>{title}</h3>
      <div className="breaker-facet-grid">
        {facets.slice(0, 4).map((facet) => (
          <div key={facet.name}>
            <span className="resource-summary-label">{facet.name}</span>
            <strong>{facet.cardinality}</strong>
            <p>{facet.values.slice(0, 4).map(formatNullable).join(', ') || 'n/a'}</p>
          </div>
        ))}
      </div>
    </aside>
  )
}

export function EtuSearchCard({
  result,
  selected,
}: SearchCardProps & {
  result: EtuSearchResult
}) {
  return (
    <article className={`resource-item breaker-search-card${selected ? ' breaker-search-card-selected' : ''}`}>
      <div className="resource-item-row">
        <span className="resource-chip">ETU</span>
        <span className="resource-chip resource-chip-muted">sensor {result.sensor_id}</span>
        {selected ? <span className="resource-chip">selected</span> : null}
      </div>
      <h3>{result.manufacturer_name} · {result.trip_type_name}</h3>
      <p>{result.trip_style_name} · {result.sensor_desc}</p>
      <dl>
        <div>
          <dt>Sensor rating</dt>
          <dd>{formatNumber(result.sensor_rating, 0)}</dd>
        </div>
        <div>
          <dt>Compatible plugs</dt>
          <dd>{result.compatible_plug_values.slice(0, 5).map((value) => formatNumber(value, 0)).join(', ') || 'n/a'}</dd>
        </div>
      </dl>
    </article>
  )
}

export function TmtSearchCard({
  frame,
  selected,
}: SearchCardProps & {
  frame: TMTFrameSearchResult
}) {
  return (
    <article className={`resource-item breaker-search-card${selected ? ' breaker-search-card-selected' : ''}`}>
      <div className="resource-item-row">
        <span className="resource-chip">TMT</span>
        <span className="resource-chip resource-chip-muted">frame {frame.frame_id}</span>
        {selected ? <span className="resource-chip">selected</span> : null}
      </div>
      <h3>{frame.manufacturer_name ?? 'Unknown manufacturer'} · {frame.breaker_name ?? 'Unknown breaker'}</h3>
      <p>{frame.breaker_style_name ?? 'Unnamed frame'} · {frame.breaker_class ?? 'class n/a'}</p>
      <dl>
        <div>
          <dt>Frame size</dt>
          <dd>{formatNullable(frame.frame_size)}</dd>
        </div>
        <div>
          <dt>Matched amp</dt>
          <dd>{formatNumber(frame.matched_amp_rating, 0)}</dd>
        </div>
      </dl>
    </article>
  )
}

export function EmtSearchCard({
  frame,
  selected,
}: SearchCardProps & {
  frame: EMTFrameSearchResult
}) {
  return (
    <article className={`resource-item breaker-search-card${selected ? ' breaker-search-card-selected' : ''}`}>
      <div className="resource-item-row">
        <span className="resource-chip">EMT</span>
        <span className="resource-chip resource-chip-muted">frame {frame.frame_id}</span>
        {selected ? <span className="resource-chip">selected</span> : null}
      </div>
      <h3>{frame.manufacturer_name ?? 'Unknown manufacturer'} · {frame.type_name ?? 'Unknown type'}</h3>
      <p>{frame.style_name ?? 'Unnamed style'} · {frame.frame_desc ?? 'frame n/a'}</p>
      <dl>
        <div>
          <dt>Sections</dt>
          <dd>{frame.section_count}</dd>
        </div>
        <div>
          <dt>Trip char</dt>
          <dd>{formatNullable(frame.trip_char)}</dd>
        </div>
      </dl>
    </article>
  )
}

function buildChart(
  curves: ChartCurve[],
  markers: ChartMarker[],
) {
  const curvePoints = curves.flatMap((curve) =>
    curve.points.filter((point) => point.amps > 0 && point.seconds > 0),
  )
  const markerPoints = markers
    .filter((marker) => marker.amps > 0 && marker.seconds !== null && marker.seconds > 0)
    .map((marker) => ({ amps: marker.amps, seconds: marker.seconds as number }))
  const domainPoints = [...curvePoints, ...markerPoints]

  if (domainPoints.length === 0) {
    return null
  }

  const markerAmps = markers.filter((marker) => marker.amps > 0).map((marker) => marker.amps)
  const xValues = [...domainPoints.map((point) => point.amps), ...markerAmps]
  const yValues = domainPoints.map((point) => point.seconds)
  let minX = Math.min(...xValues)
  let maxX = Math.max(...xValues)
  let minY = Math.min(...yValues)
  let maxY = Math.max(...yValues)

  if (Math.abs(minX - maxX) <= 0.000001) {
    minX = Math.max(0.01, minX * 0.8)
    maxX = maxX * 1.2
  }
  if (Math.abs(minY - maxY) <= 0.000001) {
    minY = Math.max(0.001, minY * 0.8)
    maxY = maxY * 1.2
  }

  const width = 680
  const height = 300
  const pad = 40
  const minLogX = Math.log10(minX)
  const maxLogX = Math.log10(maxX)
  const minLogY = Math.log10(minY)
  const maxLogY = Math.log10(maxY)
  const xFor = (value: number) => {
    const ratio = (Math.log10(value) - minLogX) / (maxLogX - minLogX)
    return pad + ratio * (width - pad * 2)
  }
  const yFor = (value: number) => {
    const ratio = (Math.log10(value) - minLogY) / (maxLogY - minLogY)
    return height - pad - ratio * (height - pad * 2)
  }
  const pointsFor = (points: ChartCurve['points']) =>
    points
      .filter((point) => point.amps > 0 && point.seconds > 0)
      .map((point) => `${xFor(point.amps)},${yFor(point.seconds)}`)
      .join(' ')

  return {
    width,
    height,
    pad,
    minX,
    maxX,
    minY,
    maxY,
    xFor,
    yFor,
    pointsFor,
  }
}

function BreakerStaticCurveChart({
  title,
  curves,
  markers = [],
}: {
  title: string
  curves: ChartCurve[]
  markers?: ChartMarker[]
}) {
  const chart = buildChart(curves, markers)

  return (
    <section className="breaker-curve-panel" data-breaker-curve-panel>
      <header className="relay-compare-section-header">
        <span className="relay-compare-section-eyebrow">Static trip curve</span>
        <h3 className="relay-compare-section-title">{title}</h3>
      </header>
      <div className="breaker-curve-legend">
        {curves.slice(0, 5).map((curve, index) => (
          <span key={curve.id} className={`breaker-legend-item breaker-legend-${index % 5}`}>
            {curve.label}
          </span>
        ))}
        {markers.length > 0 ? <span className="breaker-legend-item breaker-marker-legend">expected markers</span> : null}
      </div>
      {chart ? (
        <svg
          className="breaker-curve-chart"
          viewBox={`0 0 ${chart.width} ${chart.height}`}
          role="img"
          aria-label={title}
          data-breaker-curve-chart
        >
          <line x1={chart.pad} y1={chart.height - chart.pad} x2={chart.width - chart.pad} y2={chart.height - chart.pad} />
          <line x1={chart.pad} y1={chart.pad} x2={chart.pad} y2={chart.height - chart.pad} />
          <text x={chart.pad} y={chart.height - 10}>{formatNumber(chart.minX, 2)}A</text>
          <text x={chart.width - chart.pad - 54} y={chart.height - 10}>{formatNumber(chart.maxX, 2)}A</text>
          <text x={8} y={chart.pad}>{formatNumber(chart.maxY, 2)}s</text>
          <text x={8} y={chart.height - chart.pad}>{formatNumber(chart.minY, 2)}s</text>
          {curves.map((curve, index) => {
            const points = chart.pointsFor(curve.points)
            if (!points) {
              return null
            }

            return (
              <polyline
                key={curve.id}
                className={`breaker-curve-line breaker-curve-line-${index % 5}`}
                points={points}
                style={{
                  strokeDasharray:
                    curve.lineStyle === 'dashed' ? '8 6' : curve.lineStyle === 'dotted' ? '2 6' : undefined,
                }}
              />
            )
          })}
          {markers.map((marker) => {
            if (marker.amps <= 0 || marker.amps < chart.minX || marker.amps > chart.maxX) {
              return null
            }

            const x = chart.xFor(marker.amps)
            if (marker.seconds !== null && marker.seconds > 0) {
              const y = chart.yFor(marker.seconds)
              return (
                <g key={marker.id} className="breaker-curve-marker">
                  <circle cx={x} cy={y} r="4.5" />
                  <text x={x + 7} y={Math.max(chart.pad + 12, y - 7)}>{marker.label}</text>
                </g>
              )
            }

            return (
              <g key={marker.id} className="breaker-curve-marker">
                <line x1={x} y1={chart.pad} x2={x} y2={chart.height - chart.pad} />
                <text x={x + 5} y={chart.pad + 16}>{marker.label}</text>
              </g>
            )
          })}
        </svg>
      ) : (
        <p className="resource-banner resource-banner-neutral relay-inline-banner">
          No positive server-returned curve points are available for this static plot.
        </p>
      )}
    </section>
  )
}

function EtuSelectionPanel({
  selection,
}: {
  selection: Extract<BreakerSelectionData, { family: 'etu' }>
}) {
  const curves = (selection.plot?.curves ?? []).map((curve) => ({
    id: curve.id,
    label: `${curve.element} ${curve.phase}`,
    lineStyle: curve.line_style,
    points: curve.points,
  }))
  const markers = (selection.plot?.expected_markers ?? []).map((marker) => ({
    id: marker.id,
    label: marker.label,
    amps: marker.expected_current,
    seconds: marker.expected_time,
    renderHint: marker.render_hint,
  }))
  const compatiblePlugValues =
    selection.settings.plug_values.length > 0
      ? selection.settings.plug_values
      : selection.searchResult.compatible_plug_values
  const tccNumber =
    selection.context.resolved_equipment?.breaker_context?.tcc_number ??
    selection.plot?.meta.resolved_equipment?.breaker_context?.tcc_number ??
    null

  return (
    <>
      <div className="resource-summary relay-summary-grid relay-panel-summary">
        <div>
          <span className="resource-summary-label">Plug values</span>
          <strong>{selection.settings.plug_values.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Setting options</span>
          <strong>{countSettings(selection.settings)}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Breaker matches</span>
          <strong>{selection.breakerCascade.count}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Curve segments</span>
          <strong>{selection.plot?.curves.length ?? 0}</strong>
        </div>
      </div>

      <div className="resource-summary breaker-confirmation-summary" data-breaker-selection-confirmation>
        <div>
          <span className="resource-summary-label">Manufacturer</span>
          <strong>{selection.context.manufacturer_name}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Trip type</span>
          <strong>{selection.context.trip_type_name}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Trip style</span>
          <strong>{selection.context.trip_style_name}</strong>
        </div>
        <div>
          <span className="resource-summary-label">TCC number</span>
          <strong>{formatNullable(tccNumber)}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Sensor</span>
          <strong>
            {selection.context.sensor_desc} / {formatNumber(selection.context.rating ?? selection.searchResult.sensor_rating, 0)}A
          </strong>
        </div>
        <div>
          <span className="resource-summary-label">Compatible plugs</span>
          <strong>{compatiblePlugValues.slice(0, 8).map((value) => formatNumber(value, 0)).join(', ') || 'n/a'}</strong>
        </div>
      </div>

      <BreakerStaticCurveChart title="ETU server plot" curves={curves} markers={markers} />

      <NetaTestPlanTable
        rows={etuTestPlanRows(selection.plot?.table_rows ?? [])}
        caption="Server-returned pickup and time-delay tolerances for this ETU selection."
      />

      <BreakerCompareSection title="Context" view="context">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">sensor</span>
              <span className="resource-chip resource-chip-muted">read-only</span>
            </div>
            <h5>Trip unit identity</h5>
            <dl>
              <div>
                <dt>Manufacturer</dt>
                <dd>{selection.context.manufacturer_name}</dd>
              </div>
              <div>
                <dt>Trip type</dt>
                <dd>{selection.context.trip_type_name}</dd>
              </div>
              <div>
                <dt>Trip style</dt>
                <dd>{selection.context.trip_style_name}</dd>
              </div>
              <div>
                <dt>Rating</dt>
                <dd>{formatNumber(selection.context.rating, 0)}</dd>
              </div>
            </dl>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">elements</span>
              <span className="resource-chip resource-chip-muted">calc flags</span>
            </div>
            <h5>Available elements</h5>
            <dl>
              <div>
                <dt>LTPU / STPU</dt>
                <dd>{selection.context.has_ltpu ? 'LTPU' : 'no LTPU'} · {selection.context.has_stpu ? 'STPU' : 'no STPU'}</dd>
              </div>
              <div>
                <dt>INST / GFPU</dt>
                <dd>{selection.context.has_inst ? 'INST' : 'no INST'} · {selection.context.has_gfpu ? 'GFPU' : 'no GFPU'}</dd>
              </div>
              <div>
                <dt>Maint mode</dt>
                <dd>{selection.context.maint_capable ? 'capable' : 'not capable'}</dd>
              </div>
            </dl>
          </article>
        </div>
      </BreakerCompareSection>

      <BreakerCompareSection title="Settings" view="settings">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">pickup</span>
              <span className="resource-chip resource-chip-muted">published</span>
            </div>
            <h5>Pickup options</h5>
            <ul className="relay-list">
              <li>
                <strong>LTPU</strong>
                <span>{selection.settings.ltpu_settings.slice(0, 6).map((value) => formatNumber(value, 2)).join(', ') || 'n/a'}</span>
              </li>
              <li>
                <strong>STPU</strong>
                <span>{selection.settings.stpu_settings.slice(0, 6).map((value) => formatNumber(value, 2)).join(', ') || 'n/a'}</span>
              </li>
              <li>
                <strong>INST</strong>
                <span>{selection.settings.inst_settings.slice(0, 6).map((value) => formatNumber(value, 2)).join(', ') || 'n/a'}</span>
              </li>
              <li>
                <strong>GFPU</strong>
                <span>{selection.settings.gfpu_settings.slice(0, 6).map((value) => formatNumber(value, 2)).join(', ') || 'n/a'}</span>
              </li>
            </ul>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">delay bands</span>
              <span className="resource-chip resource-chip-muted">server</span>
            </div>
            <h5>Delay options</h5>
            <ul className="relay-list">
              <li>
                <strong>LTD</strong>
                <span>{selection.settings.ltd_settings.slice(0, 4).map((band) => `${band.label} ${formatNumber(band.open_time, 2)}s`).join(', ') || 'n/a'}</span>
              </li>
              <li>
                <strong>STD</strong>
                <span>{selection.settings.std_settings.slice(0, 4).map((band) => `${band.label} ${formatNumber(band.open_time, 2)}s`).join(', ') || 'n/a'}</span>
              </li>
              <li>
                <strong>GFD</strong>
                <span>{selection.settings.gfd_settings.slice(0, 4).map((band) => `${band.label} ${formatNumber(band.open_time, 2)}s`).join(', ') || 'n/a'}</span>
              </li>
            </ul>
          </article>
        </div>
      </BreakerCompareSection>
    </>
  )
}

function TmtSelectionPanel({
  selection,
}: {
  selection: Extract<BreakerSelectionData, { family: 'tmt' }>
}) {
  const curves = (selection.plot?.curves ?? []).map((curve) => ({
    id: curve.id,
    label: `Class ${curve.trip_class}`,
    lineStyle: curve.line_style,
    points: curve.points,
  }))

  return (
    <>
      <div className="resource-summary relay-summary-grid relay-panel-summary">
        <div>
          <span className="resource-summary-label">Trip classes</span>
          <strong>{selection.settings.available_trip_classes.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Amp ratings</span>
          <strong>{selection.settings.amp_ratings.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Settings</span>
          <strong>{selection.settings.settings.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Thermal adj.</span>
          <strong>{selection.settings.thermal_adjustments.length}</strong>
        </div>
      </div>

      <BreakerStaticCurveChart title="TMT nominal server plot" curves={curves} />

      <NetaTestPlanTable
        rows={tmtTestPlanRows(selection)}
        caption="Available TMT tolerance fields surfaced as a NETA pickup band equivalent."
      />

      <BreakerCompareSection title="Context" view="context">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">frame</span>
              <span className="resource-chip resource-chip-muted">read-only</span>
            </div>
            <h5>Breaker frame</h5>
            <dl>
              <div>
                <dt>Manufacturer</dt>
                <dd>{formatNullable(selection.context.manufacturer_name)}</dd>
              </div>
              <div>
                <dt>Breaker</dt>
                <dd>{formatNullable(selection.context.breaker_name)}</dd>
              </div>
              <div>
                <dt>Frame</dt>
                <dd>{formatNullable(selection.context.breaker_style_name)}</dd>
              </div>
              <div>
                <dt>Class / size</dt>
                <dd>{formatNullable(selection.context.breaker_class)} · {formatNullable(selection.context.frame_size)}</dd>
              </div>
            </dl>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">selected</span>
              <span className="resource-chip resource-chip-muted">metadata</span>
            </div>
            <h5>Plot selection</h5>
            <dl>
              <div>
                <dt>Trip class</dt>
                <dd>{formatNullable(selection.plot?.meta.selected_trip_class)}</dd>
              </div>
              <div>
                <dt>Amp rating</dt>
                <dd>{formatNumber(selection.plot?.meta.selected_amp_rating, 0)}</dd>
              </div>
              <div>
                <dt>Setting</dt>
                <dd>{formatNullable(selection.plot?.meta.selected_setting_label ?? selection.plot?.meta.selected_setting)}</dd>
              </div>
              <div>
                <dt>Thermal adj.</dt>
                <dd>{formatNumber(selection.plot?.meta.selected_thermal_adjustment, 0)}</dd>
              </div>
            </dl>
          </article>
        </div>
      </BreakerCompareSection>

      <BreakerCompareSection title="Settings" view="settings">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">amp ratings</span>
              <span className="resource-chip resource-chip-muted">published</span>
            </div>
            <h5>Frame ratings</h5>
            <ul className="relay-list">
              {selection.settings.amp_ratings.slice(0, 6).map((option) => (
                <li key={option.rating}>
                  <strong>{formatNumber(option.rating, 0)}A</strong>
                  <span>max override {formatNumber(option.max_override, 0)}</span>
                </li>
              ))}
            </ul>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">setting values</span>
              <span className="resource-chip resource-chip-muted">published</span>
            </div>
            <h5>Trip settings</h5>
            <ul className="relay-list">
              {selection.settings.settings.slice(0, 6).map((option, index) => (
                <li key={`${option.value ?? 'null'}-${index}`}>
                  <strong>{option.label ?? formatNumber(option.value, 2)}</strong>
                  <span>{formatToleranceBand(option.value, option.tol_lo, option.tol_hi, 'x')}</span>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </BreakerCompareSection>
    </>
  )
}

function EmtSelectionPanel({
  selection,
}: {
  selection: Extract<BreakerSelectionData, { family: 'emt' }>
}) {
  const curves = (selection.plot?.curves ?? []).map((curve) => ({
    id: curve.id,
    label: curve.class_label ?? `Class ${formatNullable(curve.curve_class)}`,
    lineStyle: curve.line_style,
    points: curve.points,
  }))

  return (
    <>
      <div className="resource-summary relay-summary-grid relay-panel-summary">
        <div>
          <span className="resource-summary-label">Amp ratings</span>
          <strong>{selection.context.amp_ratings.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Sections</span>
          <strong>{selection.context.sections.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Pickups</span>
          <strong>{selection.settings?.pickups.length ?? 0}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Bands</span>
          <strong>{selection.settings?.bands.length ?? 0}</strong>
        </div>
      </div>

      <BreakerStaticCurveChart title="EMT raw point-data server plot" curves={curves} />

      <NetaTestPlanTable
        rows={emtTestPlanRows(selection)}
        caption="Available EMT section pickup tolerance fields surfaced as a NETA pickup band equivalent."
      />

      <BreakerCompareSection title="Context" view="context">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">frame</span>
              <span className="resource-chip resource-chip-muted">read-only</span>
            </div>
            <h5>EMT frame</h5>
            <dl>
              <div>
                <dt>Manufacturer</dt>
                <dd>{formatNullable(selection.context.manufacturer_name)}</dd>
              </div>
              <div>
                <dt>Type / style</dt>
                <dd>{formatNullable(selection.context.type_name)} · {formatNullable(selection.context.style_name)}</dd>
              </div>
              <div>
                <dt>Frame</dt>
                <dd>{formatNullable(selection.context.frame_desc)}</dd>
              </div>
              <div>
                <dt>TCC number</dt>
                <dd>{formatNullable(selection.context.tcc_number)}</dd>
              </div>
            </dl>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">section</span>
              <span className="resource-chip resource-chip-muted">selected</span>
            </div>
            <h5>Selected section</h5>
            <dl>
              <div>
                <dt>Section</dt>
                <dd>{formatNullable(selection.settings?.name)}</dd>
              </div>
              <div>
                <dt>Section id</dt>
                <dd>{formatNullable(selection.settings?.section_id)}</dd>
              </div>
              <div>
                <dt>Band</dt>
                <dd>{formatNullable(selection.plot?.meta.band_name)} · {formatNullable(selection.plot?.meta.band_id)}</dd>
              </div>
              <div>
                <dt>Curve classes</dt>
                <dd>{selection.plot?.meta.available_curve_classes.join(', ') || 'n/a'}</dd>
              </div>
            </dl>
          </article>
        </div>
      </BreakerCompareSection>

      <BreakerCompareSection title="Settings" view="settings">
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">sections</span>
              <span className="resource-chip resource-chip-muted">inventory</span>
            </div>
            <h5>Frame sections</h5>
            <ul className="relay-list">
              {selection.context.sections.slice(0, 5).map((section) => (
                <li key={section.section_id}>
                  <strong>{section.name ?? `Section ${section.section_id}`}</strong>
                  <span>
                    bands {section.band_count} · pickups {section.pickup_count} ·{' '}
                    {formatToleranceBand(section.pickup_setting, section.pickup_tol_lo, section.pickup_tol_hi)}
                  </span>
                </li>
              ))}
            </ul>
          </article>
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">bands</span>
              <span className="resource-chip resource-chip-muted">published</span>
            </div>
            <h5>Section bands</h5>
            {selection.settings ? (
              <ul className="relay-list">
                {selection.settings.bands.slice(0, 5).map((band) => (
                  <li key={band.band_id}>
                    <strong>{band.band_name ?? `Band ${band.band_id}`}</strong>
                    <span>points {band.curve_point_count} · classes {band.curve_classes.join(', ') || 'n/a'}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="resource-banner resource-banner-neutral relay-inline-banner">
                No EMT section settings are published for this frame.
              </p>
            )}
          </article>
        </div>
      </BreakerCompareSection>
    </>
  )
}

export function BreakerSelectionPanel({ selection }: { selection: BreakerSelectionData }) {
  const warnings = collectWarnings(selection)
  const title =
    selection.family === 'etu'
      ? selection.context.resolved_equipment?.primary_label ?? selection.context.sensor_desc
      : selection.family === 'tmt'
        ? selection.context.resolved_equipment?.primary_label ?? selection.context.breaker_name ?? `Frame ${selection.context.frame_id}`
        : selection.context.resolved_equipment?.primary_label ?? selection.context.type_name ?? `Frame ${selection.context.frame_id}`
  const subtitle =
    selection.family === 'etu'
      ? selection.context.resolved_equipment?.secondary_label ?? `Sensor ${selection.context.sensor_id}`
      : selection.family === 'tmt'
        ? selection.context.resolved_equipment?.secondary_label ?? `Frame ${selection.context.frame_id}`
        : selection.context.resolved_equipment?.secondary_label ?? `Frame ${selection.context.frame_id}`

  return (
    <article className="resource-item breaker-selection-panel" data-breaker-selection-panel={selection.family}>
      <div className="resource-item-row">
        <span className="resource-chip">{selection.family.toUpperCase()}</span>
        <span className="resource-chip resource-chip-muted">context</span>
        <span className="resource-chip resource-chip-muted">settings</span>
        <span className="resource-chip resource-chip-muted">static plot</span>
      </div>
      <h3>{title}</h3>
      <p>{subtitle}</p>

      {warnings.length > 0 ? (
        <div className="relay-warning-block">
          {warnings.map((warning) => (
            <p key={warning} className="resource-banner resource-banner-error relay-inline-banner">
              {warning}
            </p>
          ))}
        </div>
      ) : null}

      {selection.family === 'etu' ? <EtuSelectionPanel selection={selection} /> : null}
      {selection.family === 'tmt' ? <TmtSelectionPanel selection={selection} /> : null}
      {selection.family === 'emt' ? <EmtSelectionPanel selection={selection} /> : null}
    </article>
  )
}
