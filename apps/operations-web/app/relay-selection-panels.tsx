import {
  RelayContextResponse,
  RelayPlotRequest,
  RelayPlotResponse,
  RelaySectionSearchResponse,
  RelaySettingsResponse,
} from '../lib/relay-resources'

const slotLabels = {
  primary: 'Primary selection',
  compare: 'Compare selection',
} as const

export type RelaySelectionSlot = keyof typeof slotLabels

export type RelaySelectionData = {
  slot: RelaySelectionSlot
  section: RelaySectionSearchResponse['sections'][number]
  context: RelayContextResponse
  settings: RelaySettingsResponse
  plot: RelayPlotResponse | null
  plotRequest: RelayPlotRequest | null
  currentMultiples: number[]
}

type RelaySearchCardProps = {
  section: RelaySectionSearchResponse['sections'][number]
  isPrimary: boolean
  isCompare: boolean
}

type RelaySelectionPanelProps = {
  selection: RelaySelectionData
}

function formatNumber(value: number | null | undefined, digits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a'
  }
  return value.toFixed(digits)
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

function RelayCompareSection({
  title,
  view,
  children,
}: {
  title: string
  view: string
  children: React.ReactNode
}) {
  return (
    <section className="relay-compare-section" data-relay-compare-view={view}>
      <header className="relay-compare-section-header">
        <span className="relay-compare-section-eyebrow">Compare view</span>
        <h4 className="relay-compare-section-title">{title}</h4>
      </header>
      {children}
    </section>
  )
}

export function RelaySearchCard({ section, isPrimary, isCompare }: RelaySearchCardProps) {
  return (
    <article
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
        {section.relay_type ?? 'Unnamed relay type'} · {section.device_function ?? 'No device function published'}
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
}

export function RelayPrimaryDetail({ selection }: RelaySelectionPanelProps) {
  const totalDiscreteValues = selection.settings.ranges.reduce(
    (count, range) => count + range.discrete_values.length,
    0,
  )

  return (
    <section className="relay-detail-surface" data-relay-detail-surface="primary">
      <header className="relay-detail-header">
        <div>
          <span className="relay-compare-section-eyebrow">Primary detail</span>
          <h3 className="relay-detail-title">Primary TD-section detail</h3>
        </div>
        <p className="relay-detail-copy">
          This detail surface expands the currently selected primary relay TD-section without widening the browser beyond governed read-only relay data.
        </p>
      </header>

      <div className="resource-summary relay-summary-grid relay-panel-summary">
        <div>
          <span className="resource-summary-label">Ranges</span>
          <strong>{selection.settings.ranges.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Discrete values</span>
          <strong>{totalDiscreteValues}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Curve parents</span>
          <strong>{selection.settings.curve_parents.length}</strong>
        </div>
        <div>
          <span className="resource-summary-label">Preview inventory</span>
          <strong>{selection.settings.preview_options.length}</strong>
        </div>
      </div>

      <div className="resource-grid relay-detail-grid">
        <article className="resource-item relay-nested-card" data-relay-detail-view="ranges">
          <div className="resource-item-row">
            <span className="resource-chip">settings ranges</span>
            <span className="resource-chip resource-chip-muted">read-only</span>
          </div>
          <h5>Published range inventory</h5>
          {selection.settings.ranges.length > 0 ? (
            <ul className="relay-list">
              {selection.settings.ranges.slice(0, 4).map((range) => (
                <li key={range.range_source_id}>
                  <strong>
                    {range.parent_label ?? range.parent_kind} · range {range.range_source_id}
                  </strong>
                  <span>
                    min {formatNumber(range.min_value)} · max {formatNumber(range.max_value)} · step{' '}
                    {formatNumber(range.step_value)}
                  </span>
                  <span>discrete values {range.discrete_values.length}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="resource-banner resource-banner-neutral relay-inline-banner">
              No governed setting ranges are published for this TD-section.
            </p>
          )}
        </article>

        <article className="resource-item relay-nested-card" data-relay-detail-view="curve-parents">
          <div className="resource-item-row">
            <span className="resource-chip">curve parents</span>
            <span className="resource-chip resource-chip-muted">published</span>
          </div>
          <h5>Curve parent inventory</h5>
          {selection.settings.curve_parents.length > 0 ? (
            <ul className="relay-list">
              {selection.settings.curve_parents.slice(0, 4).map((parent) => (
                <li key={parent.curve_parent_source_id}>
                  <strong>{parent.curve_name ?? `Curve parent ${parent.curve_parent_source_id}`}</strong>
                  <span>parent {parent.curve_parent_source_id} · storage {parent.storage_kind}</span>
                  <span>
                    pickup {formatNumber(parent.min_pickup)} to {formatNumber(parent.max_pickup)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="resource-banner resource-banner-neutral relay-inline-banner">
              No governed curve parents are published for this TD-section.
            </p>
          )}
        </article>

        <article className="resource-item relay-nested-card" data-relay-detail-view="preview-options">
          <div className="resource-item-row">
            <span className="resource-chip">preview options</span>
            <span className="resource-chip resource-chip-muted">inventory</span>
          </div>
          <h5>Stored preview inventory</h5>
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
                  <span>
                    current span {formatNumber(option.current_min)} to {formatNumber(option.current_max)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="resource-banner resource-banner-neutral relay-inline-banner">
              No stored preview inventory is published for this TD-section.
            </p>
          )}
        </article>
      </div>
    </section>
  )
}

export function RelaySelectionPanel({ selection }: RelaySelectionPanelProps) {
  const warnings = collectSelectionWarnings(selection)
  const curve = selection.plot?.curves[0] ?? null

  return (
    <article className="resource-item relay-selection-panel">
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

      <RelayCompareSection title="Context" view="context">
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
      </RelayCompareSection>

      <RelayCompareSection title="Settings" view="settings">
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
      </RelayCompareSection>

      <RelayCompareSection title="Preview" view="preview">
        {curve ? (
          <div className="resource-grid relay-grid">
            <article className="resource-item relay-nested-card">
              <div className="resource-item-row">
                <span className="resource-chip">preview</span>
                <span className="resource-chip resource-chip-muted">
                  {selection.plot?.meta.status ?? 'unknown'}
                </span>
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
      </RelayCompareSection>
    </article>
  )
}
