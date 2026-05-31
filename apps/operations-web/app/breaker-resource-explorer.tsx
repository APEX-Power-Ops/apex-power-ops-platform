'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AvailableSettingsResponse,
  BreakerFamily,
  BreakerResourcesError,
  CatalogStatusResponse,
  DelayBandOption,
  EMTFrameSearchResponse,
  EMTSectionSettingsResponse,
  EtuPlotRequest,
  EtuSearchResponse,
  TMTFrameSearchResponse,
  TMTPlotRequest,
  TMTSettingsResponse,
  fetchCatalogStatus,
  fetchEmtContext,
  fetchEmtFacets,
  fetchEmtFrames,
  fetchEmtPlot,
  fetchEmtSettings,
  fetchEtuBreakerCascade,
  fetchEtuContext,
  fetchEtuPlot,
  fetchEtuSearch,
  fetchEtuSettings,
  fetchTmtContext,
  fetchTmtFacets,
  fetchTmtFrames,
  fetchTmtPlot,
  fetchTmtSettings,
} from '../lib/breaker-resources'
import {
  BreakerFacetPanel,
  BreakerSelectionData,
  BreakerSelectionPanel,
  EmtSearchCard,
  EtuSearchCard,
  TmtSearchCard,
} from './breaker-selection-panels'

const familyLabels: Record<BreakerFamily, string> = {
  etu: 'ETU',
  tmt: 'TMT',
  emt: 'EMT',
}

const defaultQueries: Record<BreakerFamily, string> = {
  etu: '',
  tmt: '',
  emt: '',
}

function toResultId(value: number) {
  return String(value)
}

function firstFiniteNumber(values: number[]) {
  return values.find((value) => Number.isFinite(value)) ?? null
}

function firstDelayValue(options: DelayBandOption[]) {
  const defaultOption = options.find((option) => option.is_default)
  return defaultOption?.open_time ?? options[0]?.open_time ?? null
}

function optionalNumber(target: object, key: string, value: number | null) {
  if (value !== null && Number.isFinite(value)) {
    const mutableTarget = target as Record<string, number>
    mutableTarget[key] = value
  }
}

function buildEtuPlotRequest(settings: AvailableSettingsResponse, contextLabel: string | null): EtuPlotRequest | null {
  const plugRating = firstFiniteNumber(settings.plug_values)
  if (plugRating === null) {
    return null
  }

  const request: EtuPlotRequest = {
    sensor_id: settings.sensor_id,
    plug_rating: plugRating,
    maint_mode: false,
    include_nominal_curve: true,
    include_expected_markers: true,
    include_measured_markers: false,
  }

  optionalNumber(request, 'ltpu_setting', firstFiniteNumber(settings.ltpu_settings))
  optionalNumber(request, 'ltd_setting', firstDelayValue(settings.ltd_settings))
  optionalNumber(request, 'stpu_setting', firstFiniteNumber(settings.stpu_settings))
  optionalNumber(request, 'std_setting', firstDelayValue(settings.std_settings))
  optionalNumber(request, 'inst_setting', firstFiniteNumber(settings.inst_settings))
  optionalNumber(request, 'gfpu_setting', firstFiniteNumber(settings.gfpu_settings))
  optionalNumber(request, 'gfd_setting', firstDelayValue(settings.gfd_settings))

  if (contextLabel) {
    request.breaker_context_label = contextLabel
    request.breaker_context_source = 'operations_web_breaker_explorer'
  }

  return request
}

function buildTmtPlotRequest(frameId: number, settings: TMTSettingsResponse) {
  const tripClass = firstFiniteNumber(settings.available_trip_classes)
  if (tripClass === null) {
    return null
  }

  const request: TMTPlotRequest = {
    frame_id: frameId,
    trip_class: tripClass,
    include_raw_points: false,
    num_output_points: 36,
  }
  const ampRating = settings.amp_ratings.find((option) => Number.isFinite(option.rating))?.rating ?? null
  const settingValue = settings.settings.find((option) => option.value !== null && Number.isFinite(option.value))?.value ?? null
  const thermalAdjustment = firstFiniteNumber(settings.thermal_adjustments)

  optionalNumber(request, 'amp_rating', ampRating)
  optionalNumber(request, 'setting_value', settingValue)
  optionalNumber(request, 'thermal_adjustment', thermalAdjustment)

  return request
}

function buildEmtPlotRequest(settings: EMTSectionSettingsResponse | null) {
  if (!settings) {
    return null
  }

  const band = settings.bands.find((option) => option.curve_point_count > 0) ?? settings.bands[0]
  if (!band) {
    return null
  }

  return {
    section_id: settings.section_id,
    band_id: band.band_id,
  }
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof BreakerResourcesError ? error.message : fallback
}

export function BreakerResourceExplorer() {
  const [family, setFamily] = useState<BreakerFamily>('etu')
  const [query, setQuery] = useState(defaultQueries.etu)
  const [tmtBreakerClass, setTmtBreakerClass] = useState('MCCB')
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatusResponse | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [isCatalogLoading, setIsCatalogLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingSelection, setIsLoadingSelection] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [etuResults, setEtuResults] = useState<EtuSearchResponse | null>(null)
  const [tmtResults, setTmtResults] = useState<TMTFrameSearchResponse | null>(null)
  const [emtResults, setEmtResults] = useState<EMTFrameSearchResponse | null>(null)
  const [tmtFacets, setTmtFacets] = useState<Awaited<ReturnType<typeof fetchTmtFacets>> | null>(null)
  const [emtFacets, setEmtFacets] = useState<Awaited<ReturnType<typeof fetchEmtFacets>> | null>(null)
  const [selection, setSelection] = useState<BreakerSelectionData | null>(null)

  useEffect(() => {
    let cancelled = false

    setIsCatalogLoading(true)
    fetchCatalogStatus()
      .then((status) => {
        if (!cancelled) {
          setCatalogStatus(status)
          setCatalogError(null)
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setCatalogStatus(null)
          setCatalogError(getErrorMessage(error, 'The governed catalog status route could not be reached.'))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsCatalogLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  const resultCount = useMemo(() => {
    if (family === 'etu') {
      return etuResults?.count ?? 0
    }
    if (family === 'tmt') {
      return tmtResults?.count ?? 0
    }
    return emtResults?.count ?? 0
  }, [emtResults, etuResults, family, tmtResults])

  function resetFamilyState(nextFamily: BreakerFamily) {
    setFamily(nextFamily)
    setQuery(defaultQueries[nextFamily])
    setSelectedId('')
    setSelection(null)
    setErrorMessage(null)
    setEtuResults(null)
    setTmtResults(null)
    setEmtResults(null)
    setTmtFacets(null)
    setEmtFacets(null)
  }

  async function handleBrowse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const normalizedQuery = query.trim()
    setErrorMessage(null)
    setSelectedId('')
    setSelection(null)
    setIsSearching(true)

    try {
      if (family === 'etu') {
        if (!normalizedQuery) {
          setEtuResults(null)
          setErrorMessage('Enter an ETU search term before browsing governed sensor rows.')
          return
        }

        const response = await fetchEtuSearch(normalizedQuery)
        setEtuResults(response)
        setTmtResults(null)
        setEmtResults(null)
        setTmtFacets(null)
        setEmtFacets(null)
        return
      }

      if (family === 'tmt') {
        const [facetsResponse, framesResponse] = await Promise.all([
          fetchTmtFacets(tmtBreakerClass),
          fetchTmtFrames({
            breakerClass: tmtBreakerClass,
            manufacturerName: normalizedQuery || undefined,
          }),
        ])
        setTmtFacets(facetsResponse)
        setTmtResults(framesResponse)
        setEtuResults(null)
        setEmtResults(null)
        setEmtFacets(null)
        return
      }

      const [facetsResponse, framesResponse] = await Promise.all([
        fetchEmtFacets(),
        fetchEmtFrames(normalizedQuery),
      ])
      setEmtFacets(facetsResponse)
      setEmtResults(framesResponse)
      setEtuResults(null)
      setTmtResults(null)
      setTmtFacets(null)
    } catch (error) {
      setEtuResults(null)
      setTmtResults(null)
      setEmtResults(null)
      setTmtFacets(null)
      setEmtFacets(null)
      setErrorMessage(getErrorMessage(error, 'The governed breaker resource routes could not be reached.'))
    } finally {
      setIsSearching(false)
    }
  }

  async function handleLoadSelection() {
    setErrorMessage(null)

    if (!selectedId) {
      const article = family === 'etu' ? 'an' : 'a'
      setErrorMessage(`Select ${article} ${familyLabels[family]} result before loading context, settings, and plot data.`)
      return
    }

    setIsLoadingSelection(true)

    try {
      if (family === 'etu') {
        const searchResult = etuResults?.results.find((result) => toResultId(result.sensor_id) === selectedId)
        if (!searchResult) {
          setErrorMessage('The selected ETU sensor is no longer present in the current browse results.')
          return
        }

        const [context, settings, breakerCascade] = await Promise.all([
          fetchEtuContext(searchResult.sensor_id),
          fetchEtuSettings(searchResult.sensor_id),
          fetchEtuBreakerCascade(searchResult.manufacturer_id, searchResult.sensor_id),
        ])
        const contextLabel = context.resolved_equipment?.breaker_context?.label ?? context.trip_style_name
        const plotRequest = buildEtuPlotRequest(settings, contextLabel)
        const plot = plotRequest ? await fetchEtuPlot(plotRequest) : null

        setSelection({
          family: 'etu',
          searchResult,
          context,
          settings,
          breakerCascade,
          plot,
          plotRequest,
        })
        return
      }

      if (family === 'tmt') {
        const frame = tmtResults?.frames.find((result) => toResultId(result.frame_id) === selectedId)
        if (!frame) {
          setErrorMessage('The selected TMT frame is no longer present in the current browse results.')
          return
        }

        const [context, settings] = await Promise.all([
          fetchTmtContext(frame.frame_id),
          fetchTmtSettings(frame.frame_id),
        ])
        const plotRequest = buildTmtPlotRequest(frame.frame_id, settings)
        const plot = plotRequest ? await fetchTmtPlot(plotRequest) : null

        setSelection({
          family: 'tmt',
          frame,
          context,
          settings,
          plot,
          plotRequest,
        })
        return
      }

      const frame = emtResults?.frames.find((result) => toResultId(result.frame_id) === selectedId)
      if (!frame) {
        setErrorMessage('The selected EMT frame is no longer present in the current browse results.')
        return
      }

      const context = await fetchEmtContext(frame.frame_id)
      const section =
        context.sections.find((candidate) => candidate.band_count > 0) ??
        context.sections.find((candidate) => candidate.pickup_count > 0) ??
        context.sections[0]
      const settings = section ? await fetchEmtSettings(section.section_id) : null
      const plotRequest = buildEmtPlotRequest(settings)
      const plot = plotRequest ? await fetchEmtPlot(plotRequest) : null

      setSelection({
        family: 'emt',
        frame,
        context,
        settings,
        plot,
        plotRequest,
      })
    } catch (error) {
      setSelection(null)
      setErrorMessage(getErrorMessage(error, 'The selected breaker resource could not be loaded from the governed routes.'))
    } finally {
      setIsLoadingSelection(false)
    }
  }

  function handleClearSelection() {
    setErrorMessage(null)
    setSelectedId('')
    setSelection(null)
  }

  function handleResetBrowse() {
    resetFamilyState(family)
  }

  return (
    <section className="resource-lane-card" data-breaker-resource-explorer>
      <div className="resource-lane-header">
        <div>
          <p className="eyebrow">Breaker Resource Browser</p>
          <h2>Browse breaker resources through ETU, TMT, and EMT routes.</h2>
        </div>
        <p className="resource-lane-copy">
          This browser slice is read-only and renders only server-returned context, settings, and static curve points.
        </p>
      </div>

      <div className="resource-summary breaker-catalog-summary">
        <div>
          <span className="resource-summary-label">Catalog</span>
          <strong>{isCatalogLoading ? 'Checking' : catalogStatus?.catalog ?? 'Unknown'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Manufacturers</span>
          <strong>{catalogStatus?.manufacturer_count ?? 'n/a'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">ETU sensors</span>
          <strong>{catalogStatus?.sensor_count ?? 'n/a'}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Active family</span>
          <strong>{familyLabels[family]}</strong>
        </div>
      </div>

      {catalogError ? <p className="resource-banner resource-banner-error">{catalogError}</p> : null}

      <form className="resource-form breaker-resource-form" onSubmit={handleBrowse}>
        <div className="breaker-control-grid">
          <label className="relay-selection-field" htmlFor="breaker-family">
            <span className="resource-field">Trip Unit Type</span>
            <select
              id="breaker-family"
              name="breakerFamily"
              value={family}
              onChange={(event) => resetFamilyState(event.target.value as BreakerFamily)}
            >
              <option value="etu">ETU sensors</option>
              <option value="tmt">TMT frames</option>
              <option value="emt">EMT frames</option>
            </select>
          </label>

          <label className="relay-selection-field" htmlFor="breaker-query">
            <span className="resource-field">
              {family === 'etu' ? 'ETU search' : family === 'tmt' ? 'TMT manufacturer' : 'EMT search'}
            </span>
            <input
              id="breaker-query"
              name="breakerQuery"
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={family === 'etu' ? 'GE, Square D, trip style' : family === 'tmt' ? 'ABB, Eaton' : 'SOC, frame, style'}
              autoComplete="off"
              spellCheck={false}
            />
          </label>

          {family === 'tmt' ? (
            <label className="relay-selection-field" htmlFor="tmt-breaker-class">
              <span className="resource-field">TMT class</span>
              <select
                id="tmt-breaker-class"
                name="tmtBreakerClass"
                value={tmtBreakerClass}
                onChange={(event) => setTmtBreakerClass(event.target.value)}
              >
                <option value="MCCB">MCCB</option>
                <option value="ICCB">ICCB</option>
                <option value="PCB">PCB</option>
              </select>
            </label>
          ) : null}

          <div className="breaker-form-actions">
            <button type="submit" disabled={isSearching}>
              {isSearching ? 'Browsing…' : `Browse ${familyLabels[family]}`}
            </button>
            <button type="button" onClick={handleResetBrowse} disabled={isSearching || isLoadingSelection}>
              Reset
            </button>
          </div>
        </div>
      </form>

      {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

      {resultCount === 0 && !errorMessage ? (
        <p className="resource-banner resource-banner-neutral">
          Browse a trip unit type, select one returned row, then load the governed context, settings, and static trip curve.
        </p>
      ) : null}

      {tmtFacets ? (
        <BreakerFacetPanel
          title="TMT facet snapshot"
          total={tmtFacets.total_matching_frames}
          facets={tmtFacets.facets}
        />
      ) : null}

      {emtFacets ? (
        <BreakerFacetPanel
          title="EMT facet snapshot"
          total={emtFacets.total_matching_frames}
          facets={emtFacets.facets}
        />
      ) : null}

      {resultCount > 0 ? (
        <div className="resource-results">
          <div className="resource-summary breaker-result-summary">
            <div>
              <span className="resource-summary-label">Browse matches</span>
              <strong>{resultCount}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Selected row</span>
              <strong>{selectedId || 'Choose explicitly'}</strong>
            </div>
            <div>
              <span className="resource-summary-label">Loaded selection</span>
              <strong>{selection ? familyLabels[selection.family] : 'None'}</strong>
            </div>
          </div>

          <div className="relay-selection-controls breaker-selection-controls">
            <label className="relay-selection-field" htmlFor="breaker-selected-resource">
              <span className="resource-field">{familyLabels[family]} resource</span>
              <select
                id="breaker-selected-resource"
                name="breakerSelectedResource"
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
              >
                <option value="">Select one row</option>
                {family === 'etu'
                  ? etuResults?.results.map((result) => (
                      <option key={result.sensor_id} value={toResultId(result.sensor_id)}>
                        {result.sensor_id} · {result.manufacturer_name} · {result.trip_type_name} · {result.sensor_desc}
                      </option>
                    ))
                  : null}
                {family === 'tmt'
                  ? tmtResults?.frames.map((frame) => (
                      <option key={frame.frame_id} value={toResultId(frame.frame_id)}>
                        {frame.frame_id} · {frame.manufacturer_name ?? 'n/a'} · {frame.breaker_name ?? 'n/a'} · {frame.frame_size ?? 'n/a'}
                      </option>
                    ))
                  : null}
                {family === 'emt'
                  ? emtResults?.frames.map((frame) => (
                      <option key={frame.frame_id} value={toResultId(frame.frame_id)}>
                        {frame.frame_id} · {frame.manufacturer_name ?? 'n/a'} · {frame.type_name ?? 'n/a'} · {frame.frame_desc ?? 'n/a'}
                      </option>
                    ))
                  : null}
              </select>
            </label>

            <div className="relay-selection-actions breaker-selection-actions">
              <button type="button" onClick={handleLoadSelection} disabled={isLoadingSelection}>
                {isLoadingSelection ? 'Loading resource…' : 'Load Context + Curve'}
              </button>
              {selectedId || selection ? (
                <button type="button" onClick={handleClearSelection} disabled={isLoadingSelection}>
                  Clear
                </button>
              ) : null}
            </div>
          </div>

          <div className="breaker-search-results" data-breaker-results>
            {family === 'etu'
              ? etuResults?.results.map((result) => (
                  <EtuSearchCard
                    key={result.sensor_id}
                    result={result}
                    selected={toResultId(result.sensor_id) === selectedId}
                  />
                ))
              : null}
            {family === 'tmt'
              ? tmtResults?.frames.map((frame) => (
                  <TmtSearchCard
                    key={frame.frame_id}
                    frame={frame}
                    selected={toResultId(frame.frame_id) === selectedId}
                  />
                ))
              : null}
            {family === 'emt'
              ? emtResults?.frames.map((frame) => (
                  <EmtSearchCard
                    key={frame.frame_id}
                    frame={frame}
                    selected={toResultId(frame.frame_id) === selectedId}
                  />
                ))
              : null}
          </div>

          {selection ? <BreakerSelectionPanel selection={selection} /> : null}
        </div>
      ) : null}
    </section>
  )
}
