'use client'

import { FormEvent, useState } from 'react'
import {
  RelayContextResponse,
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

const defaultCurrentMultiples = '2, 5, 10'
const slotLabels = {
  primary: 'Primary selection',
  compare: 'Compare selection',
} as const

type RelaySelectionSlot = keyof typeof slotLabels

type RelaySelectionData = {
  slot: RelaySelectionSlot
  section: RelaySectionSearchResponse['sections'][number]
  context: RelayContextResponse
  settings: RelaySettingsResponse
  plot: RelayPlotResponse | null
  currentMultiples: number[]
}

function parseCurrentMultiples(rawValue: string) {
  const parts = rawValue
    .split(',')
    .map((part) => Number(part.trim()))
    .filter((value) => Number.isFinite(value) && value > 1)

  return Array.from(new Set(parts))
}

function formatNumber(value: number | null | undefined, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a'
  }
  return value.toFixed(digits)
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
    currentMultiples,
  }
}

function renderSelectionPanel(selection: RelaySelectionData) {
  const warnings = collectSelectionWarnings(selection)
  const curve = selection.plot?.curves[0] ?? null

  return (
    <article key={selection.slot} className="resource-item relay-selection-panel">
      <div className="resource-item-row">
        <span className="resource-chip">{slotLabels[selection.slot]}</span>
        <span className="resource-chip resource-chip-muted">{selection.context.family_name}</span>
        <span className="resource-chip resource-chip-muted">{selection.context.storage_kind}</span>
        <span className="resource-chip resource-chip-muted">
          {selection.context.supported ? 'supported' : 'unsupported'}
        </span>
      </div>

      <h3>{selection.context.td_section_name ?? 'Unnamed TD-section'}</h3>
      <p>
        {selection.context.relay_type ?? 'Unnamed relay type'} ·{' '}
        {selection.context.device_function ?? 'No device function published'}
      </p>

      <div className="resource-summary relay-summary-grid relay-panel-summary">
        <div>
          <span className="resource-summary-label">TD-section source</span>
          <strong>{selection.context.td_section_source_id}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Relay device source</span>
          <strong>{selection.context.relay_device_source_id}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Preview multiples</span>
          <strong>{selection.currentMultiples.join(', ')}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Preview options</span>
          <strong>{selection.settings.preview_options.length}</strong>
        </div>
      </div>

      {warnings.length > 0 ? (
        <div className="relay-warning-block">
          {warnings.map((warning) => (
            <p key={warning} className="resource-banner resource-banner-error relay-inline-banner">
              {warning}
            </p>
          ))}
        </div>
      ) : null}

      <section className="relay-compare-section" data-relay-compare-view="context">
        <header className="relay-compare-section-header">
          <span className="relay-compare-section-eyebrow">Compare view</span>
          <h4 className="relay-compare-section-title">Context</h4>
        </header>
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">identity</span>
              <span className="resource-chip resource-chip-muted">source-faithful</span>
            </div>
            <h5>Source identity</h5>
            <dl>
              <div>
                <dt>Family</dt>
                <dd>{selection.context.family_name}</dd>
              </div>
              <div>
                <dt>Storage kind</dt>
                <dd>{selection.context.storage_kind}</dd>
              </div>
              <div>
                <dt>Manufacturer source</dt>
                <dd>{selection.context.manufacturer_source_id}</dd>
              </div>
              <div>
                <dt>Standard code</dt>
                <dd>{selection.context.standard_code ?? 'n/a'}</dd>
              </div>
            </dl>
          </article>

          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">context</span>
              <span className="resource-chip resource-chip-muted">read-only</span>
            </div>
            <h5>Context summary</h5>
            <dl>
              <div>
                <dt>Line sections</dt>
                <dd>{selection.context.line_section_count}</dd>
              </div>
              <div>
                <dt>Ranges</dt>
                <dd>{selection.context.range_count}</dd>
              </div>
              <div>
                <dt>Curve parents</dt>
                <dd>{selection.context.curve_parent_count}</dd>
              </div>
              <div>
                <dt>Voltage restraint</dt>
                <dd>{selection.context.voltage_restraint_kind ?? 'n/a'}</dd>
              </div>
            </dl>
          </article>
        </div>
      </section>

      <section className="relay-compare-section" data-relay-compare-view="settings">
        <header className="relay-compare-section-header">
          <span className="relay-compare-section-eyebrow">Compare view</span>
          <h4 className="relay-compare-section-title">Settings</h4>
        </header>
        <div className="resource-grid relay-grid">
          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">line sections</span>
              <span className="resource-chip resource-chip-muted">governed</span>
            </div>
            <h5>Resolved line sections</h5>
            {selection.context.line_sections.length > 0 ? (
              <ul className="relay-list">
                {selection.context.line_sections.slice(0, 4).map((section) => (
                  <li key={section.line_section_source_id}>
                    <strong>{section.section_name ?? 'Unnamed section'}</strong>
                    <span>
                      #{section.section_number} · pickup {formatNumber(section.pickup)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="resource-banner resource-banner-neutral relay-inline-banner">
                No resolved line sections are published for this TD-section.
              </p>
            )}
          </article>

          <article className="resource-item relay-nested-card">
            <div className="resource-item-row">
              <span className="resource-chip">preview options</span>
              <span className="resource-chip resource-chip-muted">published</span>
            </div>
            <h5>Stored preview surface</h5>
            {selection.settings.preview_options.length > 0 ? (
              <ul className="relay-list">
                {selection.settings.preview_options.slice(0, 4).map((option, index) => (
                  <li key={`${option.curve_parent_source_id}-${option.curve_ordinal ?? option.source_ordinal ?? index}`}>
                    <strong>{option.curve_name ?? option.td_desc ?? 'Stored option'}</strong>
                    <span>
                      parent {option.curve_parent_source_id}
                      {option.curve_ordinal !== null ? ` · curve ${option.curve_ordinal}` : ''}
                      {option.source_ordinal !== null ? ` · source ${option.source_ordinal}` : ''}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="resource-banner resource-banner-neutral relay-inline-banner">
                No stored preview options are published for this TD-section.
              </p>
            )}
          </article>
        </div>
      </section>

      <section className="relay-compare-section" data-relay-compare-view="preview">
        <header className="relay-compare-section-header">
          <span className="relay-compare-section-eyebrow">Compare view</span>
          <h4 className="relay-compare-section-title">Preview</h4>
        </header>
        {curve ? (
          <div className="resource-grid relay-grid">
            <article className="resource-item relay-nested-card">
              <div className="resource-item-row">
                <span className="resource-chip">preview</span>
                <span className="resource-chip resource-chip-muted">{selection.plot?.meta.status ?? 'unknown'}</span>
              </div>
              <h5>Selected curve</h5>
              <dl>
                <div>
                  <dt>Curve name</dt>
                  <dd>{curve.curve_name}</dd>
                </div>
                <div>
                  <dt>Curve parent</dt>
                  <dd>{curve.curve_parent_source_id}</dd>
                </div>
                <div>
                  <dt>Time dial</dt>
                  <dd>{curve.time_dial ?? 'n/a'}</dd>
                </div>
                <div>
                  <dt>Source ordinal</dt>
                  <dd>{curve.source_ordinal ?? 'n/a'}</dd>
                </div>
              </dl>
            </article>

            <article className="resource-item relay-nested-card">
              <div className="resource-item-row">
                <span className="resource-chip">curve points</span>
                <span className="resource-chip resource-chip-muted">preview</span>
              </div>
              <h5>Preview points</h5>
              <ul className="relay-list">
                {curve.points.slice(0, 6).map((point) => (
                  <li key={`${point.current_multiple}-${point.seconds}`}>
                    <strong>{formatNumber(point.current_multiple, 2)}x</strong>
                    <span>{formatNumber(point.seconds, 4)} s</span>
                  </li>
                ))}
              </ul>
            </article>
          </div>
        ) : (
          <p className="resource-banner resource-banner-neutral relay-inline-banner">
            No preview curve was returned for this TD-section.
          </p>
        )}
      </section>
    </article>
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

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setIsSearching(true)
    setErrorMessage(null)
    setPrimarySectionId('')
    setCompareSectionId('')
    setPrimarySelection(null)
    setCompareSelection(null)

    try {
      const searchResponse = await fetchRelaySections(query)
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
                <article
                  key={section.td_section_source_id}
                  className={`resource-item relay-search-card${isPrimary ? ' relay-search-card-primary' : ''}${isCompare ? ' relay-search-card-compare' : ''}`}
                >
                  <div className="resource-item-row">
                    <span className="resource-chip">{section.family_name}</span>
                    <span className="resource-chip resource-chip-muted">{section.storage_kind}</span>
                    <span className="resource-chip resource-chip-muted">
                      {section.supported ? 'supported' : 'unsupported'}
                    </span>
                    {isPrimary ? <span className="resource-chip">primary</span> : null}
                    {isCompare ? <span className="resource-chip">compare</span> : null}
                  </div>
                  <h3>{section.td_section_name ?? 'Unnamed TD-section'}</h3>
                  <p>
                    {section.relay_type ?? 'Unnamed relay type'} ·{' '}
                    {section.device_function ?? 'No device function published'}
                  </p>
                  <dl>
                    <div>
                      <dt>TD-section source</dt>
                      <dd>{section.td_section_source_id}</dd>
                    </div>
                    <div>
                      <dt>Relay device source</dt>
                      <dd>{section.relay_device_source_id}</dd>
                    </div>
                    <div>
                      <dt>Manufacturer source</dt>
                      <dd>{section.manufacturer_source_id}</dd>
                    </div>
                    <div>
                      <dt>Standard code</dt>
                      <dd>{section.standard_code ?? 'n/a'}</dd>
                    </div>
                  </dl>

                  {!section.supported ? (
                    <p className="resource-banner resource-banner-error relay-inline-banner">
                      Unsupported sections remain selectable for disclosure-only compare.
                    </p>
                  ) : null}
                </article>
              )
            })}
          </div>

          {primarySelection ? (
            <div className={`relay-compare-grid${compareSelection ? ' relay-compare-grid-double' : ''}`}>
              {renderSelectionPanel(primarySelection)}
              {compareSelection ? renderSelectionPanel(compareSelection) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}