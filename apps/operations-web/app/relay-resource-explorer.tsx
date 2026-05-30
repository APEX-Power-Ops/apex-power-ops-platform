'use client'

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  RelayPlotCurvePoint,
  RelayPlotRequest,
  RelayPlotResponse,
  RelayResourcesError,
  RelaySectionSearchResponse,
  RelaySettingsResponse,
  fetchRelayContext,
  fetchRelayPlot,
  fetchRelaySections,
  fetchRelaySettings,
} from '../lib/relay-resources'
import {
  RelayPrimaryDetail,
  RelaySearchCard,
  RelaySelectionData,
  RelaySelectionPanel,
  RelaySelectionSlot,
} from './relay-selection-panels'

const defaultCurrentMultiples = '2, 5, 10'

function parseCurrentMultiples(rawValue: string) {
  const parts = rawValue
    .split(',')
    .map((part) => Number(part.trim()))
    .filter((value) => Number.isFinite(value) && value > 1)

  return Array.from(new Set(parts))
}

function toSectionId(tdSectionSourceId: number) {
  return String(tdSectionSourceId)
}

function buildPlotRequest(
  tdSectionSourceId: number,
  settingsResult: RelaySettingsResponse,
  currentMultiples: number[],
): RelayPlotRequest | null {
  const previewOption = settingsResult.preview_options[0]
  if (!previewOption) {
    return null
  }

  const plotRequest: RelayPlotRequest = {
    td_section_source_id: tdSectionSourceId,
    current_multiples: currentMultiples,
    curve_parent_source_id: previewOption.curve_parent_source_id,
  }

  if (previewOption.curve_ordinal !== null) {
    plotRequest.curve_ordinal = previewOption.curve_ordinal
    plotRequest.time_dial = 1.0
  }
  if (previewOption.source_ordinal !== null) {
    plotRequest.source_ordinal = previewOption.source_ordinal
  }
  if (previewOption.time_dial !== null) {
    plotRequest.time_dial = previewOption.time_dial
  }

  return plotRequest
}

function collectSelectionWarnings(selection: RelaySelectionData) {
  const warnings = new Set<string>()

  if (!selection.section.supported) {
    warnings.add('Unsupported sections remain selectable for disclosure-only compare.')
  }

  if (selection.context.unsupported_reason) {
    warnings.add(selection.context.unsupported_reason)
  }

  if (selection.settings.unsupported_reason) {
    warnings.add(selection.settings.unsupported_reason)
  }

  if (selection.settings.preview_options.length > 1) {
    warnings.add(
      `Preview is currently showing the first published governed option out of ${selection.settings.preview_options.length} options for this TD-section.`,
    )
  }

  if (selection.plot?.meta.unsupported_reason) {
    warnings.add(selection.plot.meta.unsupported_reason)
  }

  for (const warning of selection.plot?.warnings ?? []) {
    warnings.add(warning)
  }

  if (!selection.plot && selection.settings.preview_options.length === 0) {
    warnings.add('No stored preview option is available for this TD-section in the governed API surface.')
  }

  return Array.from(warnings)
}

async function loadSelectionData(
  section: RelaySectionSearchResponse['sections'][number],
  slot: RelaySelectionSlot,
  currentMultiples: number[],
): Promise<RelaySelectionData> {
  const [contextResult, settingsResult] = await Promise.all([
    fetchRelayContext(section.td_section_source_id),
    fetchRelaySettings(section.td_section_source_id),
  ])

  const plotRequest = buildPlotRequest(section.td_section_source_id, settingsResult, currentMultiples)
  const plotResult = plotRequest ? await fetchRelayPlot(plotRequest) : null

  return {
    slot,
    section,
    context: contextResult,
    settings: settingsResult,
    plot: plotResult,
    plotRequest,
    currentMultiples,
  }
}

function formatPreviewNumber(value: number, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : 'n/a'
}

function numbersAreClose(left: number, right: number, tolerance = 0.000001) {
  return Math.abs(left - right) <= tolerance
}

function resolveBaselineTimeDial(selection: RelaySelectionData | null) {
  return (
    selection?.plot?.meta.selected_time_dial ??
    selection?.plot?.curves[0]?.time_dial ??
    selection?.plotRequest?.time_dial ??
    1
  )
}

function isTcpSelection(selection: RelaySelectionData | null) {
  return selection?.settings.family_name === 'tcp' || selection?.settings.storage_kind === 'points'
}

function collectPositivePoints(plot: RelayPlotResponse | null) {
  return (plot?.curves[0]?.points ?? []).filter((point) => point.current_multiple > 0 && point.seconds > 0)
}

type TripEnvelopePreviewProps = {
  baselinePlot: RelayPlotResponse | null
  candidatePlot: RelayPlotResponse | null
  loading: boolean
  errorMessage: string | null
  markers: number[]
  onAddMarker: (currentMultiple: number) => void
  onClearMarkers: () => void
}

function TripEnvelopePreview({
  baselinePlot,
  candidatePlot,
  loading,
  errorMessage,
  markers,
  onAddMarker,
  onClearMarkers,
}: TripEnvelopePreviewProps) {
  const svgRef = useRef<SVGSVGElement | null>(null)
  const chart = useMemo(() => {
    const baselinePoints = collectPositivePoints(baselinePlot)
    const candidatePoints = collectPositivePoints(candidatePlot)
    const allPoints = [...baselinePoints, ...candidatePoints]

    if (allPoints.length === 0) {
      return null
    }

    const xValues = allPoints.map((point) => point.current_multiple)
    const yValues = allPoints.map((point) => point.seconds)
    let minX = Math.min(...xValues)
    let maxX = Math.max(...xValues)
    let minY = Math.min(...yValues)
    let maxY = Math.max(...yValues)

    if (numbersAreClose(minX, maxX)) {
      minX = Math.max(0.1, minX * 0.8)
      maxX = maxX * 1.2
    }
    if (numbersAreClose(minY, maxY)) {
      minY = Math.max(0.01, minY * 0.8)
      maxY = maxY * 1.2
    }

    const minLogX = Math.log10(minX)
    const maxLogX = Math.log10(maxX)
    const minLogY = Math.log10(minY)
    const maxLogY = Math.log10(maxY)
    const width = 640
    const height = 280
    const pad = 34

    const xFor = (value: number) => {
      const ratio = (Math.log10(value) - minLogX) / (maxLogX - minLogX)
      return pad + ratio * (width - pad * 2)
    }
    const yFor = (value: number) => {
      const ratio = (Math.log10(value) - minLogY) / (maxLogY - minLogY)
      return height - pad - ratio * (height - pad * 2)
    }
    const pathFor = (points: RelayPlotCurvePoint[]) =>
      points.map((point) => `${xFor(point.current_multiple)},${yFor(point.seconds)}`).join(' ')

    return {
      width,
      height,
      pad,
      minLogX,
      maxLogX,
      baselinePath: pathFor(baselinePoints),
      candidatePath: pathFor(candidatePoints),
      xFor,
      yFor,
      xMin: minX,
      xMax: maxX,
      yMin: minY,
      yMax: maxY,
    }
  }, [baselinePlot, candidatePlot])

  return (
    <section className="relay-what-if-panel" data-relay-what-if-panel="preview">
      <header className="relay-compare-section-header">
        <span className="relay-compare-section-eyebrow">Trip envelope</span>
        <h3 className="relay-compare-section-title">Baseline / What-if Overlay</h3>
      </header>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      <div className="relay-overlay-legend" aria-label="Relay trip envelope curves">
        <span className="relay-legend-item relay-legend-baseline">Baseline</span>
        <span className="relay-legend-item relay-legend-candidate">What-if</span>
        <span className="relay-legend-item relay-legend-marker">Fault marker</span>
        {loading ? <span className="relay-legend-item relay-legend-loading">Recalculating</span> : null}
      </div>

      {chart ? (
        <svg
          ref={svgRef}
          className="relay-envelope-chart"
          viewBox={`0 0 ${chart.width} ${chart.height}`}
          role="img"
          aria-label="Relay trip envelope overlay"
          onClick={(event) => {
            const bounds = event.currentTarget.getBoundingClientRect()
            const ratio = Math.min(Math.max((event.clientX - bounds.left) / bounds.width, 0), 1)
            const currentMultiple = 10 ** (chart.minLogX + ratio * (chart.maxLogX - chart.minLogX))
            onAddMarker(Number(currentMultiple.toFixed(2)))
          }}
        >
          <line x1={chart.pad} y1={chart.height - chart.pad} x2={chart.width - chart.pad} y2={chart.height - chart.pad} />
          <line x1={chart.pad} y1={chart.pad} x2={chart.pad} y2={chart.height - chart.pad} />
          <text x={chart.pad} y={chart.height - 8}>{formatPreviewNumber(chart.xMin, 1)}x</text>
          <text x={chart.width - chart.pad - 42} y={chart.height - 8}>{formatPreviewNumber(chart.xMax, 1)}x</text>
          <text x={8} y={chart.pad}>{formatPreviewNumber(chart.yMax, 2)}s</text>
          <text x={8} y={chart.height - chart.pad}>{formatPreviewNumber(chart.yMin, 2)}s</text>
          {chart.baselinePath ? <polyline className="relay-envelope-baseline" points={chart.baselinePath} /> : null}
          {chart.candidatePath ? <polyline className="relay-envelope-candidate" points={chart.candidatePath} /> : null}
          {markers.map((marker, index) => {
            if (marker < chart.xMin || marker > chart.xMax) {
              return null
            }
            const x = chart.xFor(marker)
            return (
              <g key={`${marker}-${index}`} className="relay-envelope-marker">
                <line x1={x} y1={chart.pad} x2={x} y2={chart.height - chart.pad} />
                <text x={x + 5} y={chart.pad + 16}>{formatPreviewNumber(marker, 2)}x</text>
              </g>
            )
          })}
        </svg>
      ) : (
        <p className="resource-banner resource-banner-neutral relay-inline-banner">
          No preview curve is available for the selected TD-section.
        </p>
      )}

      {markers.length > 0 ? (
        <div className="relay-marker-strip">
          <span className="resource-summary-label">Fault markers</span>
          <strong>{markers.map((marker) => `${formatPreviewNumber(marker, 2)}x`).join(', ')}</strong>
          <button type="button" onClick={onClearMarkers}>
            Clear Markers
          </button>
        </div>
      ) : null}
    </section>
  )
}

export function RelayResourceExplorer() {
  const [query, setQuery] = useState('SEL')
  const [currentMultiplesInput, setCurrentMultiplesInput] = useState(defaultCurrentMultiples)
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingSelection, setIsLoadingSelection] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [sections, setSections] = useState<RelaySectionSearchResponse | null>(null)
  const [primarySectionId, setPrimarySectionId] = useState('')
  const [compareSectionId, setCompareSectionId] = useState('')
  const [primarySelection, setPrimarySelection] = useState<RelaySelectionData | null>(null)
  const [compareSelection, setCompareSelection] = useState<RelaySelectionData | null>(null)
  const [candidatePickupMultiplier, setCandidatePickupMultiplier] = useState(1)
  const [candidateTimeDial, setCandidateTimeDial] = useState(1)
  const [candidateVoltageThresholdMultiplier, setCandidateVoltageThresholdMultiplier] = useState(1)
  const [candidatePlot, setCandidatePlot] = useState<RelayPlotResponse | null>(null)
  const [candidateErrorMessage, setCandidateErrorMessage] = useState<string | null>(null)
  const [isLoadingCandidate, setIsLoadingCandidate] = useState(false)
  const [faultMarkers, setFaultMarkers] = useState<number[]>([])

  const baselineTimeDial = resolveBaselineTimeDial(primarySelection)
  const candidateTimeDialDisabled = isTcpSelection(primarySelection)
  const candidateDirty = Boolean(
    primarySelection?.plotRequest &&
      (!numbersAreClose(candidatePickupMultiplier, 1) ||
        !numbersAreClose(candidateVoltageThresholdMultiplier, 1) ||
        (!candidateTimeDialDisabled && !numbersAreClose(candidateTimeDial, baselineTimeDial))),
  )

  useEffect(() => {
    const nextBaselineTimeDial = resolveBaselineTimeDial(primarySelection)
    setCandidatePickupMultiplier(1)
    setCandidateTimeDial(nextBaselineTimeDial)
    setCandidateVoltageThresholdMultiplier(1)
    setCandidatePlot(null)
    setCandidateErrorMessage(null)
    setIsLoadingCandidate(false)
    setFaultMarkers([])
  }, [primarySelection])

  useEffect(() => {
    const plotRequest = primarySelection?.plotRequest
    if (!plotRequest || !candidateDirty) {
      setCandidatePlot(null)
      setCandidateErrorMessage(null)
      setIsLoadingCandidate(false)
      return
    }

    const timeoutId = window.setTimeout(async () => {
      const candidate_overrides: RelayPlotRequest['candidate_overrides'] = {}
      if (!numbersAreClose(candidatePickupMultiplier, 1)) {
        candidate_overrides.pickup_multiplier = candidatePickupMultiplier
      }
      if (!candidateTimeDialDisabled && !numbersAreClose(candidateTimeDial, baselineTimeDial)) {
        candidate_overrides.time_dial = candidateTimeDial
      }
      if (!numbersAreClose(candidateVoltageThresholdMultiplier, 1)) {
        candidate_overrides.voltage_threshold_multiplier = candidateVoltageThresholdMultiplier
      }

      setIsLoadingCandidate(true)
      setCandidateErrorMessage(null)

      try {
        const response = await fetchRelayPlot({
          ...plotRequest,
          candidate_overrides,
        })
        setCandidatePlot(response)
      } catch (error) {
        setCandidatePlot(null)
        if (error instanceof RelayResourcesError) {
          setCandidateErrorMessage(error.message)
        } else {
          setCandidateErrorMessage('The governed relay backend seam could not recalculate the what-if envelope.')
        }
      } finally {
        setIsLoadingCandidate(false)
      }
    }, 350)

    return () => window.clearTimeout(timeoutId)
  }, [
    baselineTimeDial,
    candidateDirty,
    candidatePickupMultiplier,
    candidateTimeDial,
    candidateTimeDialDisabled,
    candidateVoltageThresholdMultiplier,
    primarySelection,
  ])

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const normalizedQuery = query.trim()

    setErrorMessage(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)

    if (!normalizedQuery) {
      setSections(null)
      setErrorMessage('Enter a relay search term before searching governed relay sections.')
      return
    }

    setIsSearching(true)

    try {
      const searchResponse = await fetchRelaySections(normalizedQuery)
      setSections(searchResponse)
    } catch (error) {
      setSections(null)
      if (error instanceof RelayResourcesError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('The governed relay backend seam could not be reached from the browser shell.')
      }
    } finally {
      setIsSearching(false)
    }
  }

  async function handleLoadSelection() {
    if (!sections || sections.count === 0) {
      setErrorMessage('Search the governed relay catalog before loading relay details.')
      return
    }

    const currentMultiples = parseCurrentMultiples(currentMultiplesInput)
    if (currentMultiples.length === 0) {
      setErrorMessage('Enter relay current multiples greater than 1, separated by commas.')
      setPrimarySelection(null)
      setCompareSelection(null)
      return
    }

    if (!primarySectionId) {
      setErrorMessage('Select a primary TD-section before loading relay details.')
      return
    }

    if (compareSectionId && compareSectionId === primarySectionId) {
      setErrorMessage('Compare selection must stay distinct from the primary TD-section.')
      return
    }

    const primarySection = sections.sections.find(
      (section) => toSectionId(section.td_section_source_id) === primarySectionId,
    )
    const compareSection = sections.sections.find(
      (section) => toSectionId(section.td_section_source_id) === compareSectionId,
    )

    if (!primarySection) {
      setErrorMessage('The selected primary TD-section is no longer available in the current search results.')
      return
    }

    setIsLoadingSelection(true)
    setErrorMessage(null)

    try {
      const [loadedPrimary, loadedCompare] = await Promise.all([
        loadSelectionData(primarySection, 'primary', currentMultiples),
        compareSection ? loadSelectionData(compareSection, 'compare', currentMultiples) : Promise.resolve(null),
      ])

      setPrimarySelection(loadedPrimary)
      setCompareSelection(loadedCompare)
    } catch (error) {
      setPrimarySelection(null)
      setCompareSelection(null)
      if (error instanceof RelayResourcesError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('The governed relay backend seam could not be reached from the browser shell.')
      }
    } finally {
      setIsLoadingSelection(false)
    }
  }

  function handleClearSelection() {
    setErrorMessage(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)
  }

  function handleResetSearchCriteria() {
    setQuery('SEL')
    setCurrentMultiplesInput(defaultCurrentMultiples)
    setErrorMessage(null)
    setSections(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)
  }

  function handleAddFaultMarker(currentMultiple: number) {
    setFaultMarkers((previousMarkers) => [...previousMarkers.slice(-4), currentMultiple])
  }

  const hasSelectionState = Boolean(primarySectionId || compareSectionId || primarySelection || compareSelection)
  const timeDialSliderMin = Math.max(0.05, baselineTimeDial * 0.5)
  const timeDialSliderMax = Math.max(timeDialSliderMin + 0.01, baselineTimeDial * 1.5)

  return (
    <section className="resource-lane-card">
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Tranche 5 Browser Consumer</p>
          <h2>Browse relay TD-sections through the governed control-plane routes.</h2>
        </div>
        <p className="resource-lane-copy">
          This browser slice stays read-only, preserves relay family identity, and surfaces unsupported behavior instead of hiding it.
        </p>
      </div>

      <form className="resource-form" onSubmit={handleSearch}>
        <div className="relay-form-grid">
          <label className="resource-field" htmlFor="relay-search-query">
            Relay search
          </label>
          <label className="resource-field" htmlFor="relay-current-multiples">
            Preview multiples
          </label>
        </div>
        <div className="resource-form-row relay-form-row">
          <input
            id="relay-search-query"
            name="relayQuery"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="SEL, GE, IEC, feeder"
            autoComplete="off"
            spellCheck={false}
          />
          <input
            id="relay-current-multiples"
            name="relayCurrentMultiples"
            type="text"
            value={currentMultiplesInput}
            onChange={(event) => setCurrentMultiplesInput(event.target.value)}
            placeholder="2, 5, 10"
            autoComplete="off"
            spellCheck={false}
          />
          <button type="submit" disabled={isSearching}>
            {isSearching ? 'Searching…' : 'Search Relay Sections'}
          </button>
          <button type="button" onClick={handleResetSearchCriteria} disabled={isSearching || isLoadingSelection}>
            Reset Relay Search
          </button>
        </div>
      </form>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {!sections && !errorMessage ? (
        <p className="resource-banner resource-banner-neutral">
          Search the governed relay catalog to choose one TD-section, then optionally add one compare section before loading any read-only relay context, settings, or preview data.
        </p>
      ) : null}

      {sections && sections.count === 0 ? (
        <p className="resource-banner resource-banner-neutral">
          No supported relay TD-sections matched the current search. Adjust the search term and try again.
        </p>
      ) : null}

      {sections && sections.count > 0 ? (
        <div className="resource-results">
          <div className="resource-summary relay-summary-grid relay-search-summary-grid">
            <div>
              <span className="resource-summary-label">Search matches</span>
              <strong>{sections.count}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Primary TD-section</span>
              <strong>{primarySectionId || 'Choose explicitly'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Compare TD-section</span>
              <strong>{compareSectionId || 'Optional'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Preview multiples</span>
              <strong>{currentMultiplesInput}</strong>
            </div>
          </div>

          <div className="relay-selection-controls">
            <label className="relay-selection-field" htmlFor="relay-primary-section">
              <span className="resource-field">Primary TD-section</span>
              <select
                id="relay-primary-section"
                name="relayPrimarySection"
                value={primarySectionId}
                onChange={(event) => {
                  const nextPrimary = event.target.value
                  setPrimarySectionId(nextPrimary)
                  if (nextPrimary === compareSectionId) {
                    setCompareSectionId('')
                  }
                }}
              >
                <option value="">Select one TD-section</option>
                {sections.sections.map((section) => (
                  <option key={section.td_section_source_id} value={toSectionId(section.td_section_source_id)}>
                    {section.td_section_source_id} · {section.td_section_name ?? 'Unnamed TD-section'} ·{' '}
                    {section.family_name} / {section.storage_kind}
                  </option>
                ))}
              </select>
            </label>

            <label className="relay-selection-field" htmlFor="relay-compare-section">
              <span className="resource-field">Compare TD-section</span>
              <select
                id="relay-compare-section"
                name="relayCompareSection"
                value={compareSectionId}
                onChange={(event) => setCompareSectionId(event.target.value)}
              >
                <option value="">No compare selection</option>
                {sections.sections.map((section) => (
                  <option
                    key={section.td_section_source_id}
                    value={toSectionId(section.td_section_source_id)}
                    disabled={toSectionId(section.td_section_source_id) === primarySectionId}
                  >
                    {section.td_section_source_id} · {section.td_section_name ?? 'Unnamed TD-section'} ·{' '}
                    {section.family_name} / {section.storage_kind}
                  </option>
                ))}
              </select>
            </label>

            <div className="relay-selection-actions">
              <button type="button" onClick={handleLoadSelection} disabled={isLoadingSelection}>
                {isLoadingSelection ? 'Loading selections…' : 'Load Selected Sections'}
              </button>
              {hasSelectionState ? (
                <button type="button" onClick={handleClearSelection} disabled={isLoadingSelection}>
                  Clear Relay Selection
                </button>
              ) : null}
            </div>
          </div>

          {!primarySelection ? (
            <p className="resource-banner resource-banner-neutral relay-inline-banner">
              Select a primary TD-section before the browser treats any relay preview as current.
            </p>
          ) : null}

          <div className="relay-search-results">
            {sections.sections.map((section) => {
              const sectionId = toSectionId(section.td_section_source_id)
              const isPrimary = sectionId === primarySectionId
              const isCompare = sectionId === compareSectionId

              return (
                <RelaySearchCard
                  key={section.td_section_source_id}
                  section={section}
                  isPrimary={isPrimary}
                  isCompare={isCompare}
                />
              )
            })}
          </div>

          {primarySelection ? (
            <>
              <RelayPrimaryDetail selection={primarySelection} />
              <section className="relay-what-if-panel" data-relay-what-if-panel="controls">
                <header className="relay-compare-section-header">
                  <span className="relay-compare-section-eyebrow">Read-only what-if</span>
                  <h3 className="relay-compare-section-title">Candidate Settings</h3>
                </header>
                <div className="relay-slider-grid">
                  <label className="relay-slider-field" htmlFor="relay-pickup-multiplier">
                    <span className="resource-field">Pickup multiplier</span>
                    <input
                      id="relay-pickup-multiplier"
                      type="range"
                      min="0.5"
                      max="1.5"
                      step="0.01"
                      value={candidatePickupMultiplier}
                      onChange={(event) => setCandidatePickupMultiplier(Number(event.target.value))}
                    />
                    <strong>{formatPreviewNumber(candidatePickupMultiplier, 2)}x</strong>
                  </label>
                  <label className="relay-slider-field" htmlFor="relay-time-dial">
                    <span className="resource-field">Time dial</span>
                    <input
                      id="relay-time-dial"
                      type="range"
                      min={timeDialSliderMin}
                      max={timeDialSliderMax}
                      step="0.01"
                      value={candidateTimeDial}
                      disabled={candidateTimeDialDisabled}
                      onChange={(event) => setCandidateTimeDial(Number(event.target.value))}
                    />
                    <strong>
                      {candidateTimeDialDisabled
                        ? 'stored TCP row'
                        : `${formatPreviewNumber(candidateTimeDial, 2)} s`}
                    </strong>
                  </label>
                  <label className="relay-slider-field" htmlFor="relay-voltage-threshold">
                    <span className="resource-field">Voltage threshold</span>
                    <input
                      id="relay-voltage-threshold"
                      type="range"
                      min="0.5"
                      max="1.5"
                      step="0.01"
                      value={candidateVoltageThresholdMultiplier}
                      onChange={(event) => setCandidateVoltageThresholdMultiplier(Number(event.target.value))}
                    />
                    <strong>{formatPreviewNumber(candidateVoltageThresholdMultiplier, 2)}x</strong>
                  </label>
                </div>
                <div className="relay-candidate-status">
                  <span className="resource-chip">{candidateDirty ? 'candidate active' : 'baseline'}</span>
                  <span className="resource-chip resource-chip-muted">ephemeral</span>
                  {candidatePlot?.meta.candidate_applied ? (
                    <span className="resource-chip resource-chip-muted">server recalculated</span>
                  ) : null}
                </div>
              </section>
              <TripEnvelopePreview
                baselinePlot={primarySelection.plot}
                candidatePlot={candidatePlot}
                loading={isLoadingCandidate}
                errorMessage={candidateErrorMessage}
                markers={faultMarkers}
                onAddMarker={handleAddFaultMarker}
                onClearMarkers={() => setFaultMarkers([])}
              />
              <div className={`relay-compare-grid${compareSelection ? ' relay-compare-grid-double' : ''}`}>
                <RelaySelectionPanel selection={primarySelection} />
                {compareSelection ? <RelaySelectionPanel selection={compareSelection} /> : null}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
