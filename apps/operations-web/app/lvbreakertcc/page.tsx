'use client'

/**
 * LV Breaker TCC — operator-facing field-tolerance tool.
 * 3-screen flow: Specifications -> Protection Settings -> TCC Curve. All three
 * screens are LIVE against the control-plane API (lib/breaker-resources):
 *   - Screen 1 — family-polymorphic (ETU / TMT / EMT) selection on the recovered
 *     SST bridge (co-equal dual-axis cross-filter).
 *   - Screen 2 — engine-served settings + NETA tolerance bands, G4 field-trust
 *     gated; delay test multiples selectable; measured field entries graded.
 *   - Screen 3 — the operator's CONFIGURED curve from /plot-tcc (the Screen-2
 *     state is lifted to the page), with NETA test-point markers, tolerance
 *     whiskers (mfr basis surfaced), and measured pass/fail overlays.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  fetchEtuBreakerCascade,
  fetchCascade,
  fetchEtuBridgeSensors,
  fetchEtuBreakerAltTrips,
  fetchEtuSettings,
  fetchEtuContext,
  fetchEtuCalculate,
  fetchEtuPlot,
  fetchTmtFrames,
  fetchTmtManufacturers,
  fetchTmtSettings,
  fetchTmtPlot,
  fetchEmtFrames,
  fetchEmtManufacturers,
  fetchEmtContext,
  fetchEmtSettings,
  type EtuBreakerCascadeResponse,
  type CascadeResponse,
  type EtuBridgeSensorsResponse,
  type AvailableSettingsResponse,
  type SensorCalcContext,
  type DelayBandOption,
  type EtuCalculateResponse,
  type EtuTestCurrentElement,
  type EtuPlotCompositeBand,
  type EtuPlotRequest,
  type EtuPlotResponse,
  type TMTFrameSearchResult,
  type ManufacturerFacetOption,
  type TMTSettingsResponse,
  type TMTPlotResponse,
  type EMTFrameSearchResult,
  type EMTFrameContext,
  type EMTSectionSettingsResponse,
} from '../../lib/breaker-resources'
import { buildSensorPool, summarizeSensorTerminal, type AltTripInfo } from '../../lib/etu-sensor-pool'
import { effectiveBreakerClass } from '../../lib/etu-cross-filter'
import { tripStyleOptionLabel, tripStylesForType } from '../../lib/trip-style-options'
import { tmtCurveAvailability } from '../../lib/tmt-curve-availability'
import {
  buildDefaultEtuPlotRequest,
  buildEtuPlotRequest,
  defaultBandValue,
  delayBasisLabel,
  type EtuChosenSettings,
} from '../../lib/etu-plot-request'
import {
  bandPolygonPoints,
  bandWidthNote,
  envelopeBasisLine,
  envelopeNote,
  envelopePolygonPoints,
} from '../../lib/tcc-band'
import { elementDisplay, plugLabel, testCurrentLabel, trustBadgeWord, trustTitle } from '../../lib/terminology'
import { FieldSheetView } from './field-sheet'

// ── families ────────────────────────────────────────────────────────────────
type Family = 'etu' | 'tmt' | 'emt'
const FAMILIES: { key: Family; label: string; sub: string }[] = [
  { key: 'etu', label: 'ETU', sub: 'Electronic Trip Unit' },
  { key: 'tmt', label: 'TMT', sub: 'Thermal-Magnetic' },
  { key: 'emt', label: 'EMT', sub: 'Electro-Mechanical' },
]

// What a completed Screen-1 selection resolves to (downstream key + nameplate labels).
type LiveSelection = {
  family: Family
  sensorId?: number // etu
  frameId?: number // tmt, emt
  sectionId?: number // emt
  breakerLabel: string
  tripLabel: string
  ratingLabel: string
  bridgeStatus?: 'matched' | 'unmatched'
  plugs: number[]
  trustNote: string
}

// Default device so Screens 2-3 land on a real LIVE selection on first load — never the
// misleading frozen sample. Square D Masterpact NW · Micrologic 6.0A (LSIG, so GF renders),
// 2500 A — verified against live /settings (real taps + GF present). The user overrides it on
// Screen 1; clearing the selection shows the honest "select equipment" prompt instead.
// Sensor 3947 = Square D Masterpact NW / Micrologic 6.0A, 2500 A frame, the
// COMPLETE-data style record (tcc trip_style 246): carries the LTD bands + the
// route-1 (I2X) STD/GFD composite bands, so the curve renders the full LSIG
// characteristic (long-time I²t · short-time + ground-fault I²t-ramp/floor composite
// · instantaneous). (The earlier 25506 record lacks the STD/GFD delay bands.)
const DEFAULT_SELECTION: LiveSelection = {
  family: 'etu',
  sensorId: 3947,
  breakerLabel: 'Square D Masterpact NW',
  tripLabel: 'Micrologic 6.0A',
  ratingLabel: 'Ir 2500 A',
  bridgeStatus: 'matched',
  plugs: [2500],
  trustNote: 'ETU per-sensor NETA pickup tolerances are field-sheet authoritative (G4).',
}

const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Request failed')

type EltKind = 'PICKUP' | 'DELAY' | 'INSTANT' | 'GROUND' | 'GF DELAY' | 'ARC MODE'

const MULT_OPTS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]
const DELAY_DEFAULT: Record<BandKey, number> = { ltd: 3, std: 1.5, gfd: 1.5 }
const fmtMult = (m: number) => `${Number.isInteger(m) ? m : m.toFixed(1)}×`

// ── log-log plot frame geometry (axes auto-fit per device via makeScale) ─────
const PLOT = { ml: 58, mt: 18, w: 600, h: 430 }

const STEPS = ['Equipment Specifications', 'Protection Settings', 'Time-Current Curve']
const KIND_CLASS: Record<EltKind, string> = {
  PICKUP: 'pill-green', DELAY: 'pill-green', INSTANT: 'pill-blue',
  GROUND: 'pill-blue', 'GF DELAY': 'pill-blue', 'ARC MODE': 'pill-amber',
}

// ──────────────────────────────────────────────────────────────────────────────
export default function LvBreakerTcc() {
  const [step, setStep] = useState(0)
  const [maint, setMaint] = useState(false)
  const [family, setFamily] = useState<Family>('etu')
  const [selection, setSelection] = useState<LiveSelection | null>(DEFAULT_SELECTION)

  // ETU Screen-2 state lives HERE (lean (a), core pass): the curve screen renders
  // the operator's actual configuration, and navigating 2 ⇄ 3 no longer resets it.
  // A sensor change resets the lane (different device, different settings).
  const [etuChosen, setEtuChosen] = useState<EtuChosen | null>(null)
  const [etuTestMult, setEtuTestMult] = useState<Record<BandKey, number>>(DELAY_DEFAULT)
  const [etuMeasured, setEtuMeasured] = useState<Record<string, string>>({})
  const etuSensorId = selection?.family === 'etu' ? selection.sensorId : null
  useEffect(() => {
    setEtuChosen(null)
    setEtuTestMult(DELAY_DEFAULT)
    setEtuMeasured({})
    setMaint(false)
  }, [etuSensorId])

  const chip = selection
    ? `${selection.breakerLabel} · ${selection.tripLabel}`
    : 'Select equipment to begin'

  return (
    <div className="tccx">
      <style>{CSS}</style>

      <header className="bar">
        <div className="brand">
          <span className="mark">⚡</span>
          <div>
            <div className="title">LV Breaker TCC</div>
            <div className="sub">NETA breaker / trip-unit test configuration</div>
          </div>
        </div>
        <div className="device-chip">
          <span className="dot" /> {chip}
        </div>
      </header>

      <nav className="steps">
        {STEPS.map((s, i) => (
          <button key={s} className={`step ${i === step ? 'on' : ''} ${i < step ? 'done' : ''}`} onClick={() => setStep(i)}>
            <span className="num">{i < step ? '✓' : i + 1}</span>{s}
          </button>
        ))}
      </nav>

      <main className="wrap">
        {step === 0 && (
          <Specifications family={family} setFamily={setFamily} selection={selection} setSelection={setSelection} />
        )}
        {step === 1 && (
          <Settings
            maint={maint} setMaint={setMaint} selection={selection}
            etuChosen={etuChosen} setEtuChosen={setEtuChosen}
            etuTestMult={etuTestMult} setEtuTestMult={setEtuTestMult}
            etuMeasured={etuMeasured} setEtuMeasured={setEtuMeasured}
          />
        )}
        {step === 2 && (
          <Curve
            selection={selection} maint={maint}
            etuChosen={etuChosen} etuTestMult={etuTestMult} etuMeasured={etuMeasured}
          />
        )}
      </main>

      <footer className="foot">
        <span>
          LV Breaker TCC · {selection ? 'live selection' : 'select equipment to begin'} — engine-served settings, tolerances &amp; curves (G4 field-trust gated)
        </span>
        <div className="nav-btns">
          <button className="btn ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>← Back</button>
          <button className="btn" disabled={step === 2} onClick={() => setStep((s) => Math.min(2, s + 1))}>Next →</button>
        </div>
      </footer>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="field">
      <span className="flabel">{label}</span>
      <span className="fvalue">{value}</span>
    </div>
  )
}

// Reusable labelled dropdown.
function Picker({ label, value, onChange, options, placeholder, disabled, busy }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  disabled?: boolean
  busy?: boolean
}) {
  return (
    <label className="pick">
      <span className="pick-l">{label}{busy ? <span className="spin" /> : null}</span>
      <select className="pick-s" value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        <option value="">{placeholder ?? 'Select…'}</option>
        {/* Key by position, not o.value: deduped trip_types can share a representative
            trip_type_id (e.g. 24 "Digitrip 310+ …" variants all map to id 218), so keying by
            value yields duplicate React keys and the keyed reconciliation fails to replace the
            stale (uncross-filtered) option list when the cross-filtered list arrives. */}
        {options.map((o, i) => (<option key={`${o.value}#${i}`} value={o.value}>{o.label}</option>))}
      </select>
    </label>
  )
}

// ── Screen 1: Specifications (LIVE) ───────────────────────────────────────────
function Specifications({ family, setFamily, selection, setSelection }: {
  family: Family
  setFamily: (f: Family) => void
  selection: LiveSelection | null
  setSelection: (s: LiveSelection | null) => void
}) {
  const onFamily = (f: Family) => {
    if (f === family) return
    setSelection(null)
    setFamily(f)
  }
  return (
    <>
      <section className="card">
        <div className="card-h"><span className="idx">1</span> Trip Family &amp; Equipment</div>
        <div className="card-b">
          <div className="fam-tabs" role="tablist">
            {FAMILIES.map((f) => (
              <button
                key={f.key}
                role="tab"
                aria-selected={family === f.key}
                className={`fam-tab ${family === f.key ? 'on' : ''}`}
                onClick={() => onFamily(f.key)}
              >
                <b>{f.label}</b><span>{f.sub}</span>
              </button>
            ))}
          </div>
          {family === 'etu' && <EtuSelector onSelect={setSelection} onClear={() => setSelection(null)} />}
          {family === 'tmt' && <TmtSelector onSelect={setSelection} onClear={() => setSelection(null)} />}
          {family === 'emt' && <EmtSelector onSelect={setSelection} onClear={() => setSelection(null)} />}
        </div>
      </section>

      {selection ? (
        <section className="summary">
          <div className="summary-h">✓ Equipment Configuration — matched &amp; ready</div>
          <div className="summary-grid">
            <div><span>Breaker</span>{selection.breakerLabel}</div>
            <div><span>Trip Unit</span>{selection.tripLabel}</div>
            <div><span>Rating</span>{selection.ratingLabel}</div>
            <div><span>Plugs</span>{selection.plugs.length ? selection.plugs.map((p) => `${p}A`).join(' · ') : '—'}</div>
          </div>
          {selection.bridgeStatus === 'unmatched' && (
            <div className="summary-warn">No SST-bridge match for this style — sensor list may be incomplete; verify against the trip-unit catalog.</div>
          )}
        </section>
      ) : (
        <section className="card soft">
          <div className="card-b muted-b">
            <p className="note">
              Pick a trip family, then narrow to the exact breaker and trip unit. ETU uses the recovered SST bridge to
              show only the sensors compatible with the chosen breaker style. Your selection carries into Protection
              Settings and the Curve.
            </p>
          </div>
        </section>
      )}
    </>
  )
}

// ETU: CO-EQUAL dual-axis selection (operator decision 2026-06-01, BG-5).
//   Axis A — Breaker:   Mfr → Class → Breaker → Frame   via /etu/breaker-cascade
//   Axis B — Trip Unit: Mfr → Type → Style              via /cascade
// Each axis passes the OTHER's selection as a bridge_xfilter cross-half, so both
// narrow each other through the recovered SST bridge. Every dropdown therefore lists
// only cross-compatible options. The compatible-sensor pool (the intersection) is the
// trip cascade's sensors[]; picking a sensor finalizes — reachable from either end.
// /cascade only emits sensors[] once a trip-style leaf is chosen, so the breaker lane
// gets its own sensor source via /etu/bridge-sensors — either terminal yields sensors.

function selectedManufacturerIds(
  rows: { manufacturer_id: number; manufacturer_ids?: number[] | null }[],
  selectedId: string,
): number[] | null {
  if (!selectedId) return null
  const representativeId = Number(selectedId)
  const row = rows.find((m) => m.manufacturer_id === representativeId)
  return row?.manufacturer_ids?.length ? row.manufacturer_ids : [representativeId]
}

function manufacturerIdsFromKey(key: string): number[] | null {
  return key ? key.split(',').map((value) => Number(value)) : null
}

function selectedMergedIds<T extends Record<string, unknown>>(
  rows: T[],
  selectedId: string,
  representativeKey: keyof T,
  idsKey: keyof T,
): number[] | null {
  if (!selectedId) return null
  const representativeId = Number(selectedId)
  const row = rows.find((candidate) => Number(candidate[representativeKey]) === representativeId)
  const rawIds = row?.[idsKey]
  if (!Array.isArray(rawIds)) return null
  const ids = rawIds.map((value) => Number(value)).filter((value) => Number.isFinite(value))
  return ids.length > 1 ? ids : null
}

function EtuSelector({ onSelect, onClear }: { onSelect: (s: LiveSelection) => void; onClear: () => void }) {
  // Axis A — breaker
  const [bMfr, setBMfr] = useState('')
  const [bClass, setBClass] = useState('')
  const [bId, setBId] = useState('')
  const [bStyle, setBStyle] = useState('')
  // Axis B — trip unit
  const [tMfr, setTMfr] = useState('')
  const [tType, setTType] = useState('')
  const [tStyle, setTStyle] = useState('')
  // shared terminal
  const [sensorId, setSensorId] = useState('')

  const [bCascade, setBCascade] = useState<EtuBreakerCascadeResponse | null>(null)
  const [tCascade, setTCascade] = useState<CascadeResponse | null>(null)
  const [bBusy, setBBusy] = useState(false)
  const [tBusy, setTBusy] = useState(false)
  const [resolving, setResolving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const dropSensor = useCallback(() => { setSensorId(''); onClear() }, [onClear])
  const bMfrIds = useMemo(
    () => selectedManufacturerIds(bCascade?.manufacturers ?? [], bMfr),
    [bCascade, bMfr],
  )
  const tMfrIds = useMemo(
    () => selectedManufacturerIds(tCascade?.manufacturers ?? [], tMfr),
    [tCascade, tMfr],
  )
  const bMfrIdsKey = bMfrIds?.join(',') ?? ''
  const tMfrIdsKey = tMfrIds?.join(',') ?? ''
  const bBreakerIds = useMemo(
    () => selectedMergedIds(bCascade?.breakers ?? [], bId, 'breaker_id', 'breaker_ids'),
    [bCascade, bId],
  )
  // The chosen breaker's class — breaker_id / breaker_style_id are per-class serials that
  // COLLIDE across ICCB/MCCB/PCB, so the bridge fetch must always carry the class even when
  // the operator skipped the class dropdown (#23 / DURABLE cross-class id collision).
  const bIdClass = useMemo(
    () => bCascade?.breakers.find((b) => String(b.breaker_id) === bId)?.breaker_class ?? null,
    [bCascade, bId],
  )
  const bStyleIds = useMemo(
    () => selectedMergedIds(bCascade?.breaker_styles ?? [], bStyle, 'breaker_style_id', 'style_ids'),
    [bCascade, bStyle],
  )
  const tTypeIds = useMemo(
    () => selectedMergedIds(tCascade?.trip_types ?? [], tType, 'trip_type_id', 'trip_type_ids'),
    [tCascade, tType],
  )
  const tStyleIds = useMemo(
    () => selectedMergedIds(tCascade?.trip_styles ?? [], tStyle, 'trip_style_id', 'style_ids'),
    [tCascade, tStyle],
  )
  const bBreakerIdsKey = bBreakerIds?.join(',') ?? ''
  const bStyleIdsKey = bStyleIds?.join(',') ?? ''
  const tTypeIdsKey = tTypeIds?.join(',') ?? ''
  const tStyleIdsKey = tStyleIds?.join(',') ?? ''

  // Axis A cascade — narrowed by the trip-axis selection (cross-half + bridge_xfilter).
  useEffect(() => {
    let active = true
    setBBusy(true); setErr(null)
    const breakerManufacturerIds = manufacturerIdsFromKey(bMfrIdsKey)
    const tripManufacturerIds = manufacturerIdsFromKey(tMfrIdsKey)
    fetchEtuBreakerCascade({
      manufacturerIds: breakerManufacturerIds,
      breakerClass: effectiveBreakerClass(bClass, bIdClass),
      breakerId: bBreakerIdsKey ? null : bId ? Number(bId) : null,
      breakerIds: manufacturerIdsFromKey(bBreakerIdsKey),
      breakerStyleId: bStyleIdsKey ? null : bStyle ? Number(bStyle) : null,
      breakerStyleIds: manufacturerIdsFromKey(bStyleIdsKey),
      tripManufacturerIds,
      tripTypeId: tTypeIdsKey ? null : tType ? Number(tType) : null,
      tripTypeIds: manufacturerIdsFromKey(tTypeIdsKey),
      tripStyleId: tStyleIdsKey ? null : tStyle ? Number(tStyle) : null,
      tripStyleIds: manufacturerIdsFromKey(tStyleIdsKey),
      bridgeOnly: true, // ETU tab: only breakers that actually carry an electronic trip unit
      bridgeXfilter: true,
    })
      .then((r) => { if (active) setBCascade(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBBusy(false) })
    return () => { active = false }
  }, [bMfrIdsKey, bClass, bIdClass, bId, bBreakerIdsKey, bStyle, bStyleIdsKey, tMfrIdsKey, tType, tTypeIdsKey, tStyle, tStyleIdsKey])

  // Axis B cascade — narrowed by the breaker-axis selection (cross-half + bridge_xfilter).
  // Its sensors[] is the compatible-sensor intersection (the shared terminal).
  useEffect(() => {
    let active = true
    setTBusy(true); setErr(null)
    const tripManufacturerIds = manufacturerIdsFromKey(tMfrIdsKey)
    const breakerManufacturerIds = manufacturerIdsFromKey(bMfrIdsKey)
    fetchCascade({
      manufacturerIds: tripManufacturerIds,
      tripTypeId: tTypeIdsKey ? null : tType ? Number(tType) : null,
      tripTypeIds: manufacturerIdsFromKey(tTypeIdsKey),
      tripStyleId: tStyleIdsKey ? null : tStyle ? Number(tStyle) : null,
      tripStyleIds: manufacturerIdsFromKey(tStyleIdsKey),
      breakerManufacturerIds,
      breakerClass: effectiveBreakerClass(bClass, bIdClass),
      breakerId: bBreakerIdsKey ? null : bId ? Number(bId) : null,
      breakerIds: manufacturerIdsFromKey(bBreakerIdsKey),
      breakerStyleId: bStyleIdsKey ? null : bStyle ? Number(bStyle) : null,
      breakerStyleIds: manufacturerIdsFromKey(bStyleIdsKey),
      bridgeXfilter: true,
    })
      .then((r) => { if (active) setTCascade(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setTBusy(false) })
    return () => { active = false }
  }, [tMfrIdsKey, tType, tTypeIdsKey, tStyle, tStyleIdsKey, bMfrIdsKey, bClass, bIdClass, bId, bBreakerIdsKey, bStyle, bStyleIdsKey])

  // Breaker-axis terminal -> sensors directly via the SST bridge, so the breaker lane
  // surfaces sensors without requiring a trip-style tap. Fires the moment a breaker is
  // picked (breaker grain: the union of every frame's bridged sensors, rating-narrowed
  // per frame by the backend) and re-narrows to one frame once a Frame Size is chosen.
  // Skip when a trip-style leaf is set (then /cascade is the more specific breaker∩trip
  // intersection).
  const [bridge, setBridge] = useState<EtuBridgeSensorsResponse | null>(null)
  const [bridgeBusy, setBridgeBusy] = useState(false)
  useEffect(() => {
    if ((!bStyle && !bId) || tStyle) { setBridge(null); return }
    let active = true
    setBridgeBusy(true)
    const bridgeClass = effectiveBreakerClass(bClass, bIdClass)
    fetchEtuBridgeSensors(
      bStyle
        ? {
            breakerStyleId: bStyleIdsKey ? null : Number(bStyle),
            breakerStyleIds: manufacturerIdsFromKey(bStyleIdsKey),
            breakerClass: bridgeClass,
          }
        : { breakerId: Number(bId), breakerClass: bridgeClass },
    )
      .then((r) => { if (active) setBridge(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBridgeBusy(false) })
    return () => { active = false }
  }, [bStyle, bStyleIdsKey, bId, tStyle, bClass, bIdClass])

  // Alt-trip (retrofit/upgrade) set for the chosen breaker — keyed by trip_style_id so the
  // sensor pool can tag a trip "(retrofit · LSIG)" and disambiguate same-named variants.
  // Breaker-grained (uniform across the breaker's frames), so fetch on the breaker pick;
  // it tags rows from either selection axis.
  const [altTrips, setAltTrips] = useState<Record<number, AltTripInfo>>({})
  useEffect(() => {
    if (!bId && !bStyle) { setAltTrips({}); return }
    let active = true
    const cls = effectiveBreakerClass(bClass, bIdClass)
    fetchEtuBreakerAltTrips(
      bId ? { breakerId: Number(bId), breakerClass: cls } : { breakerStyleId: Number(bStyle), breakerClass: cls },
    )
      .then((r) => {
        if (!active) return
        const map: Record<number, AltTripInfo> = {}
        for (const a of r.alt_trips) map[a.trip_style_id] = { relation: a.relation, protectionClass: a.protection_class }
        setAltTrips(map)
      })
      .catch(() => { if (active) setAltTrips({}) })
    return () => { active = false }
  }, [bId, bStyle, bClass, bIdClass])

  // Normalized compatible-sensor pool, from whichever terminal fired (trip-style wins as
  // the breaker∩trip intersection; else the breaker's bridge sensors — breaker grain unions
  // every frame, frame grain narrows to one). Pure logic lives in lib/etu-sensor-pool.
  const pool = useMemo(
    () => buildSensorPool({ tStyle, tCascade, bStyle, bId, bridge, altTrips }),
    [tStyle, tCascade, bStyle, bId, bridge, altTrips],
  )

  const resolveSensor = useCallback(async (sid: string) => {
    setSensorId(sid)
    const row = pool.find((p) => String(p.sensor_id) === sid)
    if (!sid || !row) { onClear(); return }
    const bMfrRow = bCascade?.manufacturers.find((m) => String(m.manufacturer_id) === bMfr)
    const bMfrName = bMfrRow?.manufacturer_display ?? bMfrRow?.manufacturer_name ?? ''
    const bName = bCascade?.breakers.find((b) => String(b.breaker_id) === bId)?.breaker_name ?? ''
    // At breaker grain the frame is carried on the chosen sensor row (row.frame/styleId),
    // so the nameplate stays complete even when no Frame Size dropdown was touched.
    const styleKey = bStyle || (row.styleId != null ? String(row.styleId) : '')
    const bStyleRow = bCascade?.breaker_styles.find((s) => String(s.breaker_style_id) === styleKey)
    const frame = row.frame ?? bStyleRow?.breaker_model_display ?? bStyleRow?.breaker_style_name ?? ''
    const breakerLabel = [bMfrName, bClass || bIdClass || '', bName, frame].filter(Boolean).join(' ') || 'Compatible breaker (any)'
    setResolving(true)
    let plugs: number[] = []
    try {
      const settings = await fetchEtuSettings(row.sensor_id)
      plugs = settings.plug_values ?? []
    } catch {
      plugs = []
    }
    setResolving(false)
    onSelect({
      family: 'etu',
      sensorId: row.sensor_id,
      breakerLabel,
      tripLabel: row.tripLabel,
      ratingLabel: `${row.desc || '—'}${row.rating ? ` · Ir ${row.rating} A` : ''}`,
      bridgeStatus: 'matched',
      plugs,
      trustNote: 'ETU per-sensor NETA pickup tolerances are field-sheet authoritative (G4).',
    })
  }, [pool, bCascade, bMfr, bId, bStyle, bClass, onSelect, onClear])

  // Axis A options
  const bMfrOpts = (bCascade?.manufacturers ?? []).map((m) => ({ value: String(m.manufacturer_id), label: `${m.manufacturer_display ?? m.manufacturer_name} (${m.breaker_count})` }))
  const bClassOpts = (bCascade?.breaker_classes ?? []).map((c) => ({ value: c.breaker_class, label: `${c.breaker_class} (${c.breaker_count})` }))
  const bBreakerOpts = (bCascade?.breakers ?? []).map((b) => ({ value: String(b.breaker_id), label: `${b.breaker_name} · ${b.breaker_class}` }))
  const bStyleOpts = (bCascade?.breaker_styles ?? []).map((s) => ({
    value: String(s.breaker_style_id),
    label: s.breaker_model_display ?? s.breaker_style_name,
  }))
  // Axis B options
  const tMfrOpts = (tCascade?.manufacturers ?? []).map((m) => ({ value: String(m.manufacturer_id), label: `${m.manufacturer_display ?? m.manufacturer_name} (${m.trip_type_count})` }))
  const tTypeOpts = (tCascade?.trip_types ?? []).map((t) => ({ value: String(t.trip_type_id), label: t.trip_model_display ?? t.trip_type_name }))
  // Trip STYLE = protection class (LSI/LSIG/LIG…); the model lives in Trip TYPE. (task #106)
  // Scope the Style options to the selected Trip Type, else a foreign-type style
  // (e.g. a GE WavePro's native "MVT-PM LSIG") leaks in next to the EntelliGuard
  // "LSIG" as a duplicate class and, when picked, gives an empty type∩style
  // intersection ("No compatible sensors"). No type selected → show all.
  const tStyleOpts = tripStylesForType(tCascade?.trip_styles ?? [], tType ? tTypeIds : null)
    .map((t) => ({ value: String(t.trip_style_id), label: tripStyleOptionLabel(t) }))

  // shared sensor terminal — count tracks the SAME source the dropdown lists, so the
  // status line and the dropdown always agree (no more "8 compatible" over an empty list).
  const anySel = !!(bMfr || bClass || bId || bStyle || tMfr || tType || tStyle)
  const terminal = summarizeSensorTerminal({ tStyle, tCascade, bStyle, bId, bridge }, pool, anySel)
  const sensorReady = terminal.state === 'ready'
  const sensorOpts = pool.map((p) => ({ value: String(p.sensor_id), label: p.label }))
  const sensorPlaceholder =
    terminal.state === 'ready'
      ? 'Select sensor…'
      : terminal.state === 'idle'
        ? 'Narrow either axis to begin…'
        : terminal.state === 'empty'
          ? 'No compatible sensors'
          : 'Pick a breaker, frame, or trip style to list sensors'

  return (
    <div className="selwrap">
      <div className="axes">
        <div className="axis brk">
          <div className="axis-h"><span className="ax-ic">⬛</span> Breaker {bBusy ? <span className="spin" /> : null}</div>
          <Picker label="Manufacturer" value={bMfr} options={bMfrOpts} placeholder="All manufacturers"
            onChange={(v) => { setBMfr(v); setBClass(''); setBId(''); setBStyle(''); dropSensor() }} />
          <Picker label="Breaker Class" value={bClass} options={bClassOpts} placeholder="All classes"
            onChange={(v) => { setBClass(v); setBId(''); setBStyle(''); dropSensor() }} />
          <Picker label="Breaker" value={bId} options={bBreakerOpts} placeholder="Select breaker…" disabled={!bBreakerOpts.length}
            onChange={(v) => { setBId(v); setBStyle(''); dropSensor() }} />
          <Picker label="Frame Size" value={bStyle} options={bStyleOpts} placeholder="Select frame…" disabled={!bStyleOpts.length}
            onChange={(v) => { setBStyle(v); dropSensor() }} />
        </div>

        <div className="axis trp">
          <div className="axis-h"><span className="ax-ic">⚙</span> Trip Unit {tBusy ? <span className="spin" /> : null}</div>
          <Picker label="Trip Manufacturer" value={tMfr} options={tMfrOpts} placeholder="All manufacturers"
            onChange={(v) => { setTMfr(v); setTType(''); setTStyle(''); dropSensor() }} />
          <Picker label="Trip Type" value={tType} options={tTypeOpts} placeholder="All types" disabled={!tTypeOpts.length}
            onChange={(v) => { setTType(v); setTStyle(''); dropSensor() }} />
          <Picker label="Trip Style" value={tStyle} options={tStyleOpts} placeholder="All styles" disabled={!tStyleOpts.length}
            onChange={(v) => { setTStyle(v); dropSensor() }} />
        </div>
      </div>

      <div className="sensor-term">
        <Picker label="Compatible Sensor (SST bridge intersection)" value={sensorId} options={sensorOpts} busy={resolving || bridgeBusy}
          placeholder={sensorPlaceholder} disabled={!sensorReady} onChange={resolveSensor} />
        {anySel && terminal.state !== 'idle' && (
          <div className={`xf-status ${terminal.state === 'empty' ? 'empty' : terminal.state === 'ready' ? 'ok' : ''}`}>
            {terminal.state === 'empty'
              ? '✗ No sensors are bridge-compatible with this combination — relax one axis.'
              : terminal.state === 'narrow'
                ? <>↔ <span className="xf-count">{terminal.count.toLocaleString('en-US')}</span> reachable — pick a breaker, frame, or trip style to list them.</>
                : <>↔ <span className="xf-count">{terminal.count.toLocaleString('en-US')}</span> compatible sensor{terminal.count === 1 ? '' : 's'}{terminal.capped ? ' (first 250 shown)' : ''} — both axes narrow each other.</>}
          </div>
        )}
        {bridge?.rating_warning && (
          <div role="alert" style={{ marginTop: 8, padding: '8px 10px', borderRadius: 6,
               background: '#FEF3C7', border: '1px solid #F59E0B', color: '#92400E',
               fontSize: 13, lineHeight: 1.35 }}>
            ⚠ {bridge.rating_warning}
          </div>
        )}
      </div>
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// TMT: breaker class → manufacturer → frame (guided dropdowns; no free-text).
function TmtSelector({ onSelect, onClear }: { onSelect: (s: LiveSelection) => void; onClear: () => void }) {
  const [bClass, setBClass] = useState('')
  const [mfrs, setMfrs] = useState<ManufacturerFacetOption[]>([])
  const [mfrId, setMfrId] = useState('')
  const [frames, setFrames] = useState<TMTFrameSearchResult[]>([])
  const [frameId, setFrameId] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  // class → manufacturers
  useEffect(() => {
    if (!bClass) { setMfrs([]); return }
    let active = true
    setBusy(true)
    setErr(null)
    fetchTmtManufacturers(bClass)
      .then((r) => { if (active) setMfrs(r.manufacturers) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [bClass])

  const tmtMfrIds = useMemo(() => selectedManufacturerIds(mfrs, mfrId), [mfrs, mfrId])
  const tmtMfrIdsKey = tmtMfrIds?.join(',') ?? ''

  // manufacturer → frames
  useEffect(() => {
    if (!bClass || !mfrId) { setFrames([]); return }
    let active = true
    setBusy(true)
    setErr(null)
    fetchTmtFrames({ breakerClass: bClass, manufacturerIds: manufacturerIdsFromKey(tmtMfrIdsKey), limit: 200 })
      .then((r) => { if (active) setFrames(r.frames) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [bClass, mfrId, tmtMfrIdsKey])

  const pickFrame = (fid: string) => {
    setFrameId(fid)
    if (!fid) { onClear(); return }
    const f = frames.find((x) => String(x.frame_id) === fid)
    if (!f) { onClear(); return }
    onSelect({
      family: 'tmt',
      frameId: f.frame_id,
      breakerLabel: [
        f.manufacturer_name,
        f.breaker_class,
        f.breaker_name,
        f.breaker_model_display ?? f.breaker_style_name,
      ].filter(Boolean).join(' '),
      tripLabel: 'Thermal-Magnetic (breaker-integral)',
      ratingLabel: f.frame_size ?? '—',
      plugs: [],
      trustNote: 'TMT trip is breaker-integral; settings/tolerances ship in Stage B.',
    })
  }

  const classOpts = ['ICCB', 'MCCB', 'PCB'].map((c) => ({ value: c, label: c }))
  const mfrOpts = mfrs.map((m) => ({
    value: String(m.manufacturer_id),
    label: `${m.manufacturer_display ?? m.manufacturer_name ?? `Mfr ${m.manufacturer_id}`} (${m.frame_count})`,
  }))
  const frameOpts = frames.map((f) => ({
    value: String(f.frame_id),
    label: `${f.breaker_name ?? ''} ${f.breaker_model_display ?? f.breaker_style_name ?? ''} — ${f.frame_size ?? ''}`.trim(),
  }))

  return (
    <div className="selwrap">
      <div className="selrow">
        <Picker label="Breaker Class" value={bClass} options={classOpts} placeholder="Select class…"
          onChange={(v) => { setBClass(v); setMfrId(''); setFrameId(''); onClear() }} />
        <Picker label="Manufacturer" busy={busy} value={mfrId} options={mfrOpts}
          placeholder={bClass ? 'Select manufacturer…' : 'Choose a class first'}
          disabled={!mfrOpts.length} onChange={(v) => { setMfrId(v); setFrameId(''); onClear() }} />
        <Picker label="Frame" value={frameId} options={frameOpts} placeholder={mfrId ? 'Select frame…' : 'Choose a manufacturer first'}
          disabled={!frameOpts.length} onChange={pickFrame} />
      </div>
      {bClass && mfrId && !busy && !frameOpts.length && <div className="sel-status">No frames for this manufacturer.</div>}
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// EMT: manufacturer → frame → section (guided dropdowns; no free-text).
function EmtSelector({ onSelect, onClear }: { onSelect: (s: LiveSelection) => void; onClear: () => void }) {
  const [mfrs, setMfrs] = useState<ManufacturerFacetOption[]>([])
  const [mfrId, setMfrId] = useState('')
  const [frames, setFrames] = useState<EMTFrameSearchResult[]>([])
  const [frameId, setFrameId] = useState('')
  const [ctx, setCtx] = useState<EMTFrameContext | null>(null)
  const [sectionId, setSectionId] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  // load manufacturers once
  useEffect(() => {
    let active = true
    setBusy(true)
    setErr(null)
    fetchEmtManufacturers()
      .then((r) => { if (active) setMfrs(r.manufacturers) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [])

  const emtMfrIds = useMemo(() => selectedManufacturerIds(mfrs, mfrId), [mfrs, mfrId])
  const emtMfrIdsKey = emtMfrIds?.join(',') ?? ''

  // manufacturer → frames
  useEffect(() => {
    if (!mfrId) { setFrames([]); return }
    let active = true
    setBusy(true)
    setErr(null)
    fetchEmtFrames('', { manufacturerIds: manufacturerIdsFromKey(emtMfrIdsKey), limit: 200 })
      .then((r) => { if (active) setFrames(r.frames) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [mfrId, emtMfrIdsKey])

  const pickFrame = async (fid: string) => {
    setFrameId(fid)
    setSectionId('')
    setCtx(null)
    onClear()
    if (!fid) return
    try {
      const c = await fetchEmtContext(Number(fid))
      setCtx(c)
    } catch (e) {
      setErr(errMsg(e))
    }
  }

  const pickSection = (sid: string) => {
    setSectionId(sid)
    if (!sid || !ctx) { onClear(); return }
    const sec = ctx.sections.find((s) => String(s.section_id) === sid)
    onSelect({
      family: 'emt',
      frameId: ctx.frame_id,
      sectionId: sec?.section_id,
      breakerLabel: [ctx.manufacturer_name, ctx.type_name, ctx.style_name].filter(Boolean).join(' '),
      tripLabel: `Electro-Mechanical${ctx.tcc_number ? ` · TCC ${ctx.tcc_number}` : ''}`,
      ratingLabel: `${ctx.frame_desc ?? ctx.frame_size ?? '—'}${sec?.name ? ` · ${sec.name}` : ''}`,
      plugs: [],
      trustNote: 'EMT has no stored breaker default (G0); runtime-selected catalog path.',
    })
  }

  const mfrOpts = mfrs.map((m) => ({
    value: String(m.manufacturer_id),
    label: `${m.manufacturer_display ?? m.manufacturer_name ?? `Mfr ${m.manufacturer_id}`} (${m.frame_count})`,
  }))
  const frameOpts = frames.map((f) => ({
    value: String(f.frame_id),
    label: `${f.type_name ?? ''} ${f.style_name ?? ''} — ${f.frame_desc ?? f.frame_size ?? ''}`.trim(),
  }))
  const sectionOpts = (ctx?.sections ?? []).map((s) => ({ value: String(s.section_id), label: s.name ?? `Section ${s.section_id}` }))

  return (
    <div className="selwrap">
      <div className="selrow">
        <Picker label="Manufacturer" busy={busy} value={mfrId} options={mfrOpts}
          placeholder={mfrs.length ? 'Select manufacturer…' : busy ? 'Loading…' : 'No manufacturers'}
          disabled={!mfrOpts.length} onChange={(v) => { setMfrId(v); setFrameId(''); setSectionId(''); onClear() }} />
        <Picker label="Frame" value={frameId} options={frameOpts} placeholder={mfrId ? 'Select frame…' : 'Choose a manufacturer first'}
          disabled={!frameOpts.length} onChange={pickFrame} />
        <Picker label="Section" value={sectionId} options={sectionOpts} placeholder={ctx ? 'Select section…' : 'Choose a frame first'}
          disabled={!sectionOpts.length} onChange={pickSection} />
      </div>
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// Honest empty state for Screens 2-3 when the operator has cleared the selection — no fabricated
// settings/curve is ever shown (replaces the old frozen SAMPLE render).
function SelectPrompt({ kind }: { kind: 'settings' | 'curve' }) {
  return (
    <div className="loadbox">
      <span className="sel-status">
        ↑ Select equipment on <b>Equipment Specifications</b> to load the live{' '}
        {kind === 'settings' ? 'protection settings' : 'time-current curve'}.
      </span>
    </div>
  )
}

// ── Screen 2: Protection Settings dispatcher ──────────────────────────────────
function Settings({ maint, setMaint, selection, etuChosen, setEtuChosen, etuTestMult, setEtuTestMult, etuMeasured, setEtuMeasured }: {
  maint: boolean
  setMaint: (v: boolean) => void
  selection: LiveSelection | null
  etuChosen: EtuChosen | null
  setEtuChosen: (v: EtuChosen | null | ((c: EtuChosen | null) => EtuChosen | null)) => void
  etuTestMult: Record<BandKey, number>
  setEtuTestMult: (v: Record<BandKey, number> | ((t: Record<BandKey, number>) => Record<BandKey, number>)) => void
  etuMeasured: Record<string, string>
  setEtuMeasured: (v: Record<string, string> | ((m: Record<string, string>) => Record<string, string>)) => void
}) {
  if (selection?.family === 'etu' && selection.sensorId != null) {
    return (
      <EtuSettings
        maint={maint} setMaint={setMaint} selection={selection}
        chosen={etuChosen} setChosen={setEtuChosen}
        testMult={etuTestMult} setTestMult={setEtuTestMult}
        measured={etuMeasured} setMeasured={setEtuMeasured}
      />
    )
  }
  if (selection?.family === 'tmt' && selection.frameId != null) {
    return <TmtSettings selection={selection} />
  }
  if (selection?.family === 'emt' && selection.sectionId != null) {
    return <EmtSettings selection={selection} />
  }
  return <SelectPrompt kind="settings" />
}

// ── Screen 2 ETU (LIVE): editable settings -> /calculate -> DB-authoritative bands ──
type PickKey = 'ltpu' | 'stpu' | 'inst' | 'gfpu'
type BandKey = 'ltd' | 'std' | 'gfd'
// Same shape as the lib's EtuChosenSettings — the lifted Screen-2 state the curve
// request is built from. Delay band values are the option's open_time (numeric).
type EtuChosen = EtuChosenSettings
const EL_META: { code: string; label: string; kind: EltKind; pick?: PickKey; band?: BandKey }[] = [
  { code: 'LTPU', label: 'Long-Time Pickup', kind: 'PICKUP', pick: 'ltpu' },
  { code: 'LTD', label: 'Long-Time Delay', kind: 'DELAY', band: 'ltd' },
  { code: 'STPU', label: 'Short-Time Pickup', kind: 'PICKUP', pick: 'stpu' },
  { code: 'STD', label: 'Short-Time Delay', kind: 'DELAY', band: 'std' },
  { code: 'INST', label: 'Instantaneous', kind: 'INSTANT', pick: 'inst' },
  { code: 'GFPU', label: 'Ground-Fault Pickup', kind: 'GROUND', pick: 'gfpu' },
  { code: 'GFD', label: 'Ground-Fault Delay', kind: 'GF DELAY', band: 'gfd' },
]
const fmtAmp = (n: number | null | undefined) => (n == null ? '—' : `${Math.round(n).toLocaleString('en-US')} A`)

function EtuSettings({ maint, setMaint, selection, chosen, setChosen, testMult, setTestMult, measured, setMeasured }: {
  maint: boolean
  setMaint: (v: boolean) => void
  selection: LiveSelection
  // Lifted Screen-2 state (lean (a)): owned by the page so the curve screen
  // renders the same configuration and 2 ⇄ 3 navigation never resets it.
  chosen: EtuChosen | null
  setChosen: (v: EtuChosen | null | ((c: EtuChosen | null) => EtuChosen | null)) => void
  // Operator-selectable delay test current (× the element's pickup). NETA defaults:
  // LTD 3×, STD/GFD 1.5×. LTD 6× = the band reference where the expected trip time
  // equals the dial setting and is practically measurable.
  testMult: Record<BandKey, number>
  setTestMult: (v: Record<BandKey, number> | ((t: Record<BandKey, number>) => Record<BandKey, number>)) => void
  measured: Record<string, string>
  setMeasured: (v: Record<string, string> | ((m: Record<string, string>) => Record<string, string>)) => void
}) {
  const sensorId = selection.sensorId as number
  const [settings, setSettings] = useState<AvailableSettingsResponse | null>(null)
  const [calc, setCalc] = useState<EtuCalculateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [calcBusy, setCalcBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  // B2.1: the print-ready field tolerance sheet (renders the served values).
  const [sheetOpen, setSheetOpen] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null); setCalc(null)
    Promise.all([fetchEtuSettings(sensorId), fetchEtuContext(sensorId)])
      .then(([s]: [AvailableSettingsResponse, SensorCalcContext]) => {
        if (!active) return
        setSettings(s)
        // Default the selection only when the operator hasn't configured this
        // sensor yet (the page resets the lifted state on sensor change) —
        // returning from Screen 3 must not clobber their configuration. The
        // functional read avoids any stale render-captured snapshot.
        const mid = (arr: number[]): number | undefined => (arr.length ? arr[Math.floor(arr.length / 2)] : undefined)
        setChosen((current) => current ?? {
          plug: s.plug_values[0] ?? 0,
          ltpu: mid(s.ltpu_settings), stpu: mid(s.stpu_settings), inst: mid(s.inst_settings), gfpu: mid(s.gfpu_settings),
          ltd: defaultBandValue(s.ltd_settings), std: defaultBandValue(s.std_settings), gfd: defaultBandValue(s.gfd_settings),
        })
      })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sensorId])

  useEffect(() => {
    if (!chosen || !chosen.plug) return
    let active = true
    setCalcBusy(true)
    fetchEtuCalculate({
      sensor_id: sensorId, plug_rating: chosen.plug,
      ltpu_setting: chosen.ltpu, stpu_setting: chosen.stpu, inst_setting: chosen.inst, gfpu_setting: chosen.gfpu,
      ltd_setting: chosen.ltd, std_setting: chosen.std, gfd_setting: chosen.gfd,
      ltd_test_multiple: testMult.ltd, std_test_multiple: testMult.std, gfd_test_multiple: testMult.gfd,
      maint_mode: maint,
    })
      .then((r) => { if (active) setCalc(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setCalcBusy(false) })
    return () => { active = false }
  }, [chosen, maint, sensorId, testMult])

  if (loading || !settings || !chosen) {
    return <div className="loadbox">{err ? <span className="sel-status err">⚠ {err}</span> : <><span className="spin" /> Loading sensor settings…</>}</div>
  }

  const listFor = (pk: PickKey): number[] =>
    pk === 'ltpu' ? settings.ltpu_settings : pk === 'stpu' ? settings.stpu_settings : pk === 'inst' ? settings.inst_settings : settings.gfpu_settings
  const bandsFor = (bk: BandKey): DelayBandOption[] =>
    bk === 'ltd' ? settings.ltd_settings : bk === 'std' ? settings.std_settings : settings.gfd_settings
  // Per-element pickup option label. The unit comes from the backend (driven by the
  // sensor's calc method): LTPU may be amperes ("A") or a multiple of In/Ir per family.
  const pickLabel = (pk: PickKey, v: number): string => {
    const u = settings.units?.[pk]
    if (u === 'A') return `${v} A`
    if (u) return `${v} ${u.replace(/^x /, '× ')}`
    return `${v} × Ir`
  }
  const elByCode = (code: string) => calc?.elements.find((e) => e.element.toUpperCase() === code)

  // NETA ATS test points (NETA_TEST_PLAN_SPEC §2/§11): pickups ramp @ 1×; each delay injects a
  // multiple of its own pickup — LTD @ 3× LTPU (default), STD @ 1.5× STPU, GFD @ 1.5× GFPU. The
  // delay test current is now operator-selectable (testMult); /calculate returns the correct
  // multiplier, inject current, and — for LTD — the expected trip time recomputed at that multiple
  // via the I²t reference window (t = setting·(6/N)²; setting = the trip time at 6× Ir), agreeing
  // with the Screen-3 curve. So read multiplier / test_current / delay_seconds straight off the row.

  // G4 per-sensor delay-route trust (backend services/neta/delay_trust.py): /calculate now
  // carries `trust` per delay element. Direct-band (route 0) + LTD → DB; INVEQ Therm (route 2)
  // → verify; I2X / GE-TU / GF-INVEQ-Ansi → unsupported, and the engine WITHHOLDS the expected
  // time (only the inject current stays field-valid). Pickups remain DB-authoritative.
  const delayTrust = (e: EtuTestCurrentElement): string => (e.trust ?? 'verify').toLowerCase()
  const isWithheld = (e: EtuTestCurrentElement): boolean => e.kind === 'delay' && delayTrust(e) === 'unsupported'
  // SC3 ruled badges (Q2 MFR / Q3 N/A): field phrasing leads the tooltip, the
  // engineering trust_reason stays appended as the audit trail.
  const term = settings.terminology
  const trustCell = (e: EtuTestCurrentElement) => {
    if (e.kind !== 'delay') {
      return <span className="trust ok" title={trustTitle('pickup.db', 'DB-authoritative per-sensor tolerance', term)}>{trustBadgeWord('pickup.db', term)}</span>
    }
    const t = delayTrust(e)
    if (t === 'db') {
      return <span className="trust ok" title={trustTitle('delay.db', e.trust_reason ?? 'Direct-band delay — numerically validated row-for-row (G4)', term)}>{trustBadgeWord('delay.db', term)}</span>
    }
    if (t === 'unsupported') {
      return <span className="trust no" title={trustTitle('delay.unsupported', e.trust_reason ?? 'Delay solver not implemented — expected trip time withheld (G4)', term)}>{trustBadgeWord('delay.unsupported', term)}</span>
    }
    return <span className="trust verify" title={trustTitle('delay.verify', e.trust_reason ?? 'Final confirmation pending (G4 §4)', term)}>{trustBadgeWord('delay.verify', term)}</span>
  }
  // A delay band built from the flagged generic −30/+0 estimate (no per-manufacturer
  // LTD tolerance on file) vs a real DB-sourced per-mfr band (G4 §4 / L5).
  const isGenericDelayBand = (e: EtuTestCurrentElement): boolean =>
    e.kind === 'delay' && (e.notes ?? '').includes('_generic')
  const fmtSec = (v: number): string => (Number.isInteger(v) ? `${v}` : v.toFixed(2))
  const limitCell = (val: number | null, e: EtuTestCurrentElement) => {
    if (isWithheld(e)) return <span className="muted2">withheld</span>
    if (val == null) return '—'
    if (e.kind !== 'delay') return fmtAmp(val)
    const t = `${fmtSec(val)} s`
    return isGenericDelayBand(e)
      ? <span title="Generic ±estimate — no per-manufacturer delay tolerance on file (G4 L5)">{t} <span className="muted2">est</span></span>
      : t
  }

  return (
    <>
      <div className="eq-strip">
        <div><span>Breaker</span>{selection.breakerLabel}</div>
        <div><span>Trip Unit</span>{selection.tripLabel}</div>
        <div><span>Sensor</span>{calc?.sensor_desc ?? selection.ratingLabel}</div>
        <div className="plugpick">
          {/* SC3 Part III 3a: the plug sets In (Ir = LTPU dial × In) — "Plug (Ir)"
              inverted the two symbols on the flagship family. */}
          <span>{plugLabel(settings.terminology)}</span>
          <select className="el-select" value={String(chosen.plug)} onChange={(e) => setChosen((c) => (c ? { ...c, plug: Number(e.target.value) } : c))}>
            {settings.plug_values.map((p) => (<option key={p} value={p}>{p} A</option>))}
          </select>
        </div>
        <div><span className="badge live">LIVE</span>DB-authoritative</div>
      </div>

      <div className={`maint-banner ${maint ? 'on' : ''}`}>
        <div>
          <b>Maintenance Mode (ARMS)</b>
          <span>{!calc?.maint_capable ? 'This trip unit reports no maintenance mode.' : maint ? 'Reduced instantaneous trip applied.' : 'Nominal mode. Toggle to model the reduced arc-flash trip.'}</span>
        </div>
        <button className={`toggle ${maint ? 'on' : ''}`} disabled={!calc?.maint_capable} onClick={() => setMaint(!maint)} aria-label="toggle maintenance mode"><span /></button>
      </div>

      <div className="grid2 elgrid">
        {EL_META.map((m) => {
          const present = m.pick ? listFor(m.pick).length > 0 : m.band ? bandsFor(m.band).length > 0 : false
          const el = elByCode(m.code)
          // SC3 (task #129): lineage vocabulary from tcc.field_terminology — the
          // faceplate caption + dial symbol (Q4: shown on Screen 2 AND the sheet);
          // EL_META stays the fail-open fallback.
          const disp = elementDisplay((m.pick ?? m.band) as string, m.code, m.label, settings.terminology)
          return (
            <div key={m.code} className={`el-card ${present ? '' : 'off'}`}>
              <div className="el-h">
                <div className="el-code" title={disp.note ?? undefined}>
                  <b>{disp.code}</b>
                  <span>{disp.label}{disp.symbol ? ` · ${disp.symbol}` : ''}</span>
                </div>
                <span className={`pill ${KIND_CLASS[m.kind]}`}>{m.kind}</span>
              </div>
              <div className="el-b">
                <div className="el-row">
                  <span>Setting</span>
                  {!present ? (
                    <div className="el-mult muted">Not available</div>
                  ) : m.pick ? (
                    <select className="el-select" value={String(chosen[m.pick] ?? '')} onChange={(e) => setChosen((c) => (c ? { ...c, [m.pick!]: e.target.value ? Number(e.target.value) : undefined } : c))}>
                      {listFor(m.pick).map((v) => (<option key={v} value={v}>{pickLabel(m.pick!, v)}</option>))}
                    </select>
                  ) : (
                    <select className="el-select" value={String(chosen[m.band!] ?? '')} onChange={(e) => setChosen((c) => (c ? { ...c, [m.band!]: e.target.value ? Number(e.target.value) : undefined } : c))}>
                      {/* The option VALUE is the band's open_time — numeric for every
                          source (band tables and route-2 InvEq dials alike) and the
                          value the backend float-matches; Number(band) is NaN for
                          textual band-table labels. */}
                      {bandsFor(m.band!).map((b, i) => (<option key={`${b.band}#${i}`} value={b.open_time}>{b.label}</option>))}
                    </select>
                  )}
                </div>
                {present && m.band ? (
                  <div className="el-row">
                    <span>{testCurrentLabel(settings.terminology)} ×</span>
                    <select
                      className="el-select"
                      value={testMult[m.band]}
                      onChange={(e) => setTestMult((t) => ({ ...t, [m.band!]: Number(e.target.value) }))}
                      title={m.band === 'ltd' ? 'Long-time delay test current. 6× = the band reference where expected time equals the dial setting.' : 'Delay test current (× pickup).'}
                    >
                      {MULT_OPTS.map((mm) => (<option key={mm} value={mm}>{fmtMult(mm)}</option>))}
                    </select>
                  </div>
                ) : null}
                <div className="el-row"><span>Test Current</span><div className="el-cur">{present && el ? fmtAmp(el.test_current) : '—'}</div></div>
              </div>
            </div>
          )
        })}
      </div>

      <section className="card">
        <div className="card-h">
          📊 NETA Tolerance Bands &amp; Field Results {calcBusy ? <span className="spin" /> : <span className="badge inline live">LIVE</span>}
          <button
            className="btn ghost sheet-btn"
            disabled={!calc?.elements?.length}
            title={calc?.elements?.length ? 'Open the print-ready field tolerance sheet (B2.1)' : 'Adjust settings first — the sheet renders the computed test plan'}
            onClick={() => setSheetOpen(true)}
          >🖨 Field Sheet</button>
        </div>
        <div className="bands-wrap">
          <table className="bands">
            <thead><tr><th>Element</th><th>Trust</th><th>Test ×</th><th>Test Current</th><th>Min Limit</th><th>Max Limit</th><th>Measured</th><th>% Error</th><th>Status</th></tr></thead>
            <tbody>
              {(calc?.elements ?? []).map((e) => {
                const delay = e.kind === 'delay'
                const lo = delay ? e.time_limit_low : e.limit_low
                const hi = delay ? e.time_limit_high : e.limit_high
                const expected = delay ? e.delay_seconds : e.test_current
                const unit = delay ? 's' : 'A'
                const raw = measured[e.element] ?? ''
                const mv = parseFloat(raw)
                const hasM = raw.trim() !== '' && !Number.isNaN(mv)
                const pct = hasM && expected ? ((mv - expected) / expected) * 100 : null
                const inBand = hasM && lo != null && hi != null ? mv >= lo && mv <= hi : null
                return (
                  <tr key={e.element}>
                    <td><b>{e.element}</b></td>
                    <td>{trustCell(e)}</td>
                    <td>{fmtMult(e.multiplier)}</td>
                    <td className="num">{fmtAmp(e.test_current)}</td>
                    <td className="num">{limitCell(lo, e)}</td>
                    <td className="num">{limitCell(hi, e)}</td>
                    <td><div className="meas"><input className="meas-in" inputMode="decimal" value={raw} placeholder="—" disabled={isWithheld(e)} onChange={(ev) => setMeasured((m) => ({ ...m, [e.element]: ev.target.value }))} /><span className="meas-u">{unit}</span></div></td>
                    <td className="num">{pct !== null ? <span className={`pct ${inBand ? 'ok' : 'bad'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(1)}%</span> : <span className="muted2">—</span>}</td>
                    <td>{isWithheld(e) ? <span className="status off">withheld</span> : !hasM ? <span className="status ready">● Ready</span> : inBand ? <span className="status pass">✓ PASS</span> : <span className="status fail">✗ FAIL</span>}</td>
                  </tr>
                )
              })}
              {!calc?.elements.length && (
                <tr><td colSpan={9} className="muted2" style={{ padding: '16px 18px' }}>{calcBusy ? 'Calculating…' : 'Adjust settings to compute the test plan.'}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {err && <div className="sel-status err">⚠ {err}</div>}
      {calc?.warnings?.length ? <div className="sel-status warn">{calc.warnings.join(' · ')}</div> : null}

      <div className="method">
        <b>NETA test points.</b> Pickups (LTPU/STPU/INST/GFPU) ramp-test <b>@ 1×</b> against <b>DB-authoritative per-sensor tolerances</b> (field-safe). Each delay injects a <b>selectable multiple of its pickup</b> (the <b>Test @</b> dropdown) — NETA defaults <b>LTD 3× LTPU, STD/GFD 1.5×</b> — and the <b>inject current is always field-correct</b> (the proven pickup × your chosen multiple). For <b>long-time delay</b> the expected trip <b>time follows the I²t law</b> t = setting·(6/N)²: the stored band setting is the trip time at <b>6× Ir</b>, so testing at <b>6×</b> gives a time equal to the dial setting (the practical, directly-measurable point), while 3× is four times longer. The <b>delay time tolerance band</b> (Min/Max Limit) is the <b>per-manufacturer DB value</b> (`DS2_TOL`, matched to the I²t curve type) when on file; where none exists it falls back to a generic ±estimate, marked <b>est</b>. The expected <b>time</b> stays <b>gated per the G4 field-trust matrix</b>: <b>MFR</b> = manufacturer-validated — direct bands, LTD, the <b>inverse-equation routes (bit-exact vs the native EasyPower kernel, incl. GF-ANSI #120)</b> and the <b>I²t flat/ramp/composite surfaces (#72)</b>; <b>N/A</b> = unknown-shape I²t / GE-trip-unit routes whose solver is not built, so the time is <b>withheld</b> (the inject current stays valid). Time tolerance bands use the <b>manufacturer&apos;s values</b> where on file — NETA acceptance is based on manufacturer tolerances; the generic ±estimate appears only where none exists, marked <b>est</b>. {selection.trustNote}
      </div>

      {sheetOpen && calc && (
        <FieldSheetView
          input={{
            selection: {
              breakerLabel: selection.breakerLabel,
              tripLabel: selection.tripLabel,
              ratingLabel: selection.ratingLabel,
            },
            sensorId,
            settings,
            chosen,
            testMult,
            measured,
            maint,
            calc,
          }}
          onClose={() => setSheetOpen(false)}
        />
      )}
    </>
  )
}

// ── Screen 2 TMT (LIVE, bounded): thermal-magnetic settings + magnetic ±tol (DB) ──
// Bounded surface (G4): the magnetic pickup ±tolerance is DB-sourced (per-setting tol_lo/tol_hi);
// the thermal long-time band/time is curve-governed (Stage C). Test points are NETA procedure × the
// definitional pickups (thermal LT @ 3× rating; magnetic INST @ 1× ramp).
function TmtSettings({ selection }: { selection: LiveSelection }) {
  const frameId = selection.frameId as number
  const [settings, setSettings] = useState<TMTSettingsResponse | null>(null)
  const [tripClass, setTripClass] = useState<number | null>(null)
  const [ampRating, setAmpRating] = useState<number | null>(null)
  const [magSetting, setMagSetting] = useState<number | null>(null)
  const [thermalAdj, setThermalAdj] = useState<number | null>(null)
  const [measured, setMeasured] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null); setMeasured({})
    fetchTmtSettings(frameId)
      .then((s) => {
        if (!active) return
        setSettings(s)
        setTripClass(s.available_trip_classes[0] ?? null)
        setAmpRating(s.amp_ratings[0]?.rating ?? null)
        setMagSetting(s.settings[Math.floor(s.settings.length / 2)]?.value ?? s.settings[0]?.value ?? null)
        setThermalAdj(s.thermal_adjustments[0] ?? null)
      })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [frameId])

  if (loading || !settings) {
    return <div className="loadbox">{err ? <span className="sel-status err">⚠ {err}</span> : <><span className="spin" /> Loading TMT frame…</>}</div>
  }

  const setting = settings.settings.find((s) => s.value === magSetting) ?? null
  const thermalPickup = ampRating
  const magPickup = magSetting != null && ampRating != null ? magSetting * ampRating : null
  const tolLo = setting?.tol_lo ?? null
  const tolHi = setting?.tol_hi ?? null
  const magMin = magPickup != null && tolLo != null ? magPickup * (1 + tolLo / 100) : null
  const magMax = magPickup != null && tolHi != null ? magPickup * (1 + tolHi / 100) : null
  const thermalTest = thermalPickup != null ? 3 * thermalPickup : null

  const ampOpts = settings.amp_ratings.map((a) => ({ value: String(a.rating), label: `${a.rating} A${a.max_override ? ` (max ${a.max_override})` : ''}` }))
  const magOpts = settings.settings.filter((s) => s.value != null).map((s) => ({ value: String(s.value), label: s.label ?? `${s.value}×` }))
  const classOpts = settings.available_trip_classes.map((c) => ({ value: String(c), label: `Class ${c}` }))
  const adjOpts = settings.thermal_adjustments.map((t) => ({ value: String(t), label: String(t) }))

  type TmtRow = { code: string; label: string; pickup: number | null; mult: number; testCur: number | null; min: number | null; max: number | null; trust: 'DB' | 'verify'; unit: 'A' }
  const rows: TmtRow[] = [
    { code: 'LT', label: 'Thermal (Long-Time)', pickup: thermalPickup, mult: 3, testCur: thermalTest, min: null, max: null, trust: 'verify', unit: 'A' },
    { code: 'INST', label: 'Magnetic (Instantaneous)', pickup: magPickup, mult: 1, testCur: magPickup, min: magMin, max: magMax, trust: 'DB', unit: 'A' },
  ]

  return (
    <>
      <div className="eq-strip">
        <div><span>Breaker</span>{selection.breakerLabel}</div>
        <div><span>Trip Unit</span>{selection.tripLabel}</div>
        <div><span>Frame</span>{selection.ratingLabel}</div>
        <div><span className="badge">BOUNDED</span>settings + magnetic ±tol DB-sourced</div>
      </div>

      <section className="card">
        <div className="card-h">Thermal-Magnetic Settings</div>
        <div className="card-b">
          <div className="selrow">
            <Picker label="Trip Class" value={String(tripClass ?? '')} options={classOpts} onChange={(v) => setTripClass(v ? Number(v) : null)} />
            <Picker label="Amp Rating (thermal)" value={String(ampRating ?? '')} options={ampOpts} onChange={(v) => setAmpRating(v ? Number(v) : null)} />
            <Picker label="Magnetic Setting" value={String(magSetting ?? '')} options={magOpts} onChange={(v) => setMagSetting(v ? Number(v) : null)} />
            {adjOpts.length ? <Picker label="Thermal Adj." value={String(thermalAdj ?? '')} options={adjOpts} onChange={(v) => setThermalAdj(v ? Number(v) : null)} /> : null}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-h">📊 NETA Test Plan &amp; Field Results <span className="badge inline">BOUNDED</span></div>
        <div className="bands-wrap">
          <table className="bands">
            <thead><tr><th>Element</th><th>Trust</th><th>Pickup</th><th>Test @</th><th>Test Current</th><th>Min Limit</th><th>Max Limit</th><th>Measured</th><th>% Error</th><th>Status</th></tr></thead>
            <tbody>
              {rows.map((r) => {
                const raw = measured[r.code] ?? ''
                const mv = parseFloat(raw)
                const hasM = raw.trim() !== '' && !Number.isNaN(mv)
                const pct = hasM && r.pickup ? ((mv - r.pickup) / r.pickup) * 100 : null
                const inBand = hasM && r.min != null && r.max != null ? mv >= r.min && mv <= r.max : null
                const bandKnown = r.min != null && r.max != null
                return (
                  <tr key={r.code}>
                    <td><b>{r.code}</b><div className="el-sub">{r.label}</div></td>
                    <td>{r.trust === 'DB' ? <span className="trust ok" title="Magnetic pickup ±tolerance is DB-sourced">DB</span> : <span className="trust verify" title="Thermal long-time band is curve-governed (Stage C)">verify</span>}</td>
                    <td className="num">{fmtAmp(r.pickup)}</td>
                    <td>{fmtMult(r.mult)}</td>
                    <td className="num">{fmtAmp(r.testCur)}</td>
                    <td className="num">{r.min == null ? '—' : fmtAmp(r.min)}</td>
                    <td className="num">{r.max == null ? '—' : fmtAmp(r.max)}</td>
                    <td><div className="meas"><input className="meas-in" inputMode="decimal" value={raw} placeholder="—" onChange={(ev) => setMeasured((m) => ({ ...m, [r.code]: ev.target.value }))} /><span className="meas-u">A</span></div></td>
                    <td className="num">{pct !== null ? <span className={`pct ${inBand ? 'ok' : 'bad'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(1)}%</span> : <span className="muted2">—</span>}</td>
                    <td>{!hasM ? <span className="status ready">● Ready</span> : !bandKnown ? <span className="status off">band: verify</span> : inBand ? <span className="status pass">✓ PASS</span> : <span className="status fail">✗ FAIL</span>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {err && <div className="sel-status err">⚠ {err}</div>}

      <div className="method">
        <b>Thermal-Magnetic (bounded).</b> The <b>magnetic</b> instantaneous pickup ({magSetting}× rating) carries a <b>DB-sourced ±tolerance</b> ({tolLo ?? '−?'}% / +{tolHi ?? '?'}%) — field-usable. The <b>thermal</b> long-time element picks up at the amp rating and is NETA-tested @ <b>3×</b> (300%); its time/band is <b>curve-governed</b> and lands with the live curve (Stage C). Test currents = NETA procedure × the definitional pickups. {selection.trustNote}
      </div>
    </>
  )
}

// ── Screen 2 EMT (LIVE, context-only): per-section pickup options + ±tol% ──────
// Context display (G4): EMT pickup setting + ±tolerance are DB-sourced, but the EMT pickup→test-current
// calc is not yet validated against the engine, so no computed amps / PASS-FAIL here (deliberately bounded).
function EmtSettings({ selection }: { selection: LiveSelection }) {
  const sectionId = selection.sectionId as number
  const [settings, setSettings] = useState<EMTSectionSettingsResponse | null>(null)
  const [pickup, setPickup] = useState<number | null>(null)
  const [bandId, setBandId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null)
    fetchEmtSettings(sectionId)
      .then((s) => {
        if (!active) return
        setSettings(s)
        setPickup(s.pickups[0]?.setting ?? s.pickup_setting ?? null)
        setBandId(s.bands[0]?.band_id ?? null)
      })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [sectionId])

  if (loading || !settings) {
    return <div className="loadbox">{err ? <span className="sel-status err">⚠ {err}</span> : <><span className="spin" /> Loading EMT section…</>}</div>
  }

  const pickupOpts = settings.pickups.filter((p) => p.setting != null).map((p) => ({ value: String(p.setting), label: p.description ?? String(p.setting) }))
  const bandOpts = settings.bands.map((b) => ({ value: String(b.band_id), label: b.band_name ?? `Band ${b.band_id}` }))
  const tolLo = settings.pickup_tol_lo
  const tolHi = settings.pickup_tol_hi

  return (
    <>
      <div className="eq-strip">
        <div><span>Breaker</span>{selection.breakerLabel}</div>
        <div><span>Trip Unit</span>{selection.tripLabel}</div>
        <div><span>Section</span>{settings.name ?? selection.ratingLabel}</div>
        <div><span className="badge">CONTEXT</span>settings + ±tol DB-sourced</div>
      </div>

      <section className="card">
        <div className="card-h">Electro-Mechanical — {settings.name ?? 'Section'} <span className="badge inline">CONTEXT</span></div>
        <div className="card-b">
          <div className="selrow">
            <Picker label="Pickup Setting" value={String(pickup ?? '')} options={pickupOpts} placeholder="Select pickup…" disabled={!pickupOpts.length} onChange={(v) => setPickup(v ? Number(v) : null)} />
            <Picker label="Time Band" value={String(bandId ?? '')} options={bandOpts} placeholder={bandOpts.length ? 'Select band…' : 'No bands'} disabled={!bandOpts.length} onChange={(v) => setBandId(v ? Number(v) : null)} />
          </div>
          <div className="tol-strip">
            <div><span>Selected pickup</span><b>{pickup ?? '—'}</b></div>
            <div><span>Pickup tolerance</span><b>{tolLo != null && tolHi != null ? `${tolLo}% / +${tolHi}%` : '—'}</b></div>
            <div><span>Bands</span><b>{settings.bands.length}</b></div>
            <div><span>Pickup options</span><b>{settings.pickups.length}</b></div>
          </div>
        </div>
      </section>

      {err && <div className="sel-status err">⚠ {err}</div>}

      <div className="method">
        <b>Electro-Mechanical (context only).</b> The section's <b>pickup setting and ±tolerance</b> are DB-sourced. EMT is selected per <b>section</b> (the protection element) on Screen 1; the pickup → test-current conversion and the live curve are not yet engine-validated, so computed test currents + PASS/FAIL are deliberately withheld here (bounded) and land with Stage C. {selection.trustNote}
      </div>
    </>
  )
}

// ── Screen 3: Curve dispatcher ────────────────────────────────────────────────
function Curve({ selection, maint, etuChosen, etuTestMult, etuMeasured }: {
  selection: LiveSelection | null
  maint: boolean
  etuChosen: EtuChosen | null
  etuTestMult: Record<BandKey, number>
  etuMeasured: Record<string, string>
}) {
  if (selection?.family === 'etu' && selection.sensorId != null) {
    return (
      <EtuCurve
        selection={selection} maint={maint}
        chosen={etuChosen} testMult={etuTestMult} measured={etuMeasured}
      />
    )
  }
  if (selection?.family === 'tmt' && selection.frameId != null) {
    return <TmtCurve selection={selection} />
  }
  if (selection?.family === 'emt' && selection.sectionId != null) {
    return <EmtCurve selection={selection} />
  }
  return <SelectPrompt kind="curve" />
}

// ── Screen 3 TMT (LIVE, bounded): nominal thermal class curve from /tmt/plot-tcc ──
// The TMT plot returns the nominal class curve in PER-UNIT (× rating); the engine surfaces the
// amp-rating/setting selections in metadata but does NOT apply them to the plotted shape (its
// disclaimer). We scale per-unit × the selected thermal amp rating for an absolute nominal curve —
// consistent with the TMT Screen-2 model (magnetic pickup = setting × rating). Nominal illustration.
function TmtCurve({ selection }: { selection: LiveSelection }) {
  const frameId = selection.frameId as number
  const [plot, setPlot] = useState<TMTPlotResponse | null>(null)
  const [noCurveNote, setNoCurveNote] = useState<string | null>(null)
  const [ampRating, setAmpRating] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null); setPlot(null); setNoCurveNote(null)
    fetchTmtSettings(frameId)
      .then((s) => {
        const avail = tmtCurveAvailability(s.available_trip_classes)
        const amp = s.amp_ratings[0]?.rating ?? 0
        if (active) setAmpRating(amp)
        if (!avail.hasCurve) {
          // Magnetic-only / switch / electronic device: no thermal-magnetic curve to plot
          // (E2E audit F06). Withhold honestly instead of rendering a blank plot.
          if (active) setNoCurveNote(avail.note)
          return null
        }
        const cls = s.available_trip_classes[0]
        const setting = s.settings[Math.floor(s.settings.length / 2)]?.value ?? s.settings[0]?.value ?? undefined
        return fetchTmtPlot({ frame_id: frameId, trip_class: cls, amp_rating: amp || undefined, setting_value: setting ?? undefined, include_raw_points: false })
      })
      .then((r) => { if (active && r) setPlot(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [frameId])

  if (loading) return <div className="loadbox"><span className="spin" /> Generating curve…</div>
  if (noCurveNote) return (
    <section className="card">
      <div className="card-h">Trip Characteristic Curve <span className="badge inline">no thermal curve</span></div>
      <div className="card-b">
        <div className="sel-status warn" style={{ marginBottom: 10 }}>⚠ {noCurveNote}</div>
        <Field label="Breaker" value={selection.breakerLabel} />
        <Field label="Trip Unit" value={selection.tripLabel} />
        <Field label="Frame" value={selection.ratingLabel} />
      </div>
    </section>
  )
  if (err || !plot) return <div className="loadbox"><span className="sel-status err">⚠ {err ?? 'No curve data'}</span></div>

  const scale = ampRating || 1
  const curves = plot.curves ?? []
  // Pre-scale per-unit points to absolute amps, then auto-fit the log-log axes to the
  // device's envelope (same makeScale treatment as the ETU chart) so the class curve
  // fills the plot instead of floating inside a fixed 100 A–100 kA / 0.01–1000 s frame.
  const scaledCurves = curves.map((c) => ({ ...c, points: c.points.map((p) => ({ amps: p.amps * scale, seconds: p.seconds })) }))
  const allAmps = scaledCurves.flatMap((c) => c.points.map((p) => p.amps)).filter((a) => a > 0)
  const allTimes = scaledCurves.flatMap((c) => c.points.map((p) => p.seconds)).filter((t) => t > 0)
  const sc = makeScale(allAmps, allTimes)
  const stats = [
    { k: 'Curves', v: String(curves.length) },
    { k: 'Amp Rating', v: ampRating ? `${ampRating} A` : '—' },
    { k: 'Max Current', v: allAmps.length ? `${Math.round(Math.max(...allAmps)).toLocaleString('en-US')} A` : '—' },
    { k: 'Class', v: String(plot.meta.selected_trip_class ?? '—') },
  ]

  return (
    <>
      <div className="curve-grid">
        <aside className="card side">
          <div className="card-h">Device Info <span className="badge inline">BOUNDED</span></div>
          <div className="card-b">
            <Field label="Breaker" value={selection.breakerLabel} />
            <Field label="Trip Unit" value={selection.tripLabel} />
            <Field label="Frame" value={selection.ratingLabel} />
            <Field label="Amp Rating" value={ampRating ? `${ampRating} A` : '—'} />
          </div>
          <div className="card-h" style={{ marginTop: 8 }}>Curve Elements</div>
          <div className="legend"><div className="leg"><span className="sw" style={{ background: '#14507d' }} />Thermal class curve</div></div>
        </aside>

        <section className="card plot-card">
          <div className="card-h">Trip Characteristic Curve <span className="badge inline">BOUNDED · nominal class curve</span></div>
          <div className="plot-wrap">
            <svg viewBox="0 0 700 500" className="plot" role="img" aria-label="Time-current curve">
              {sc.xTicks.map((t) => (
                <g key={`x${t}`}>
                  <line x1={sc.px(t)} y1={PLOT.mt} x2={sc.px(t)} y2={PLOT.mt + PLOT.h} className="grid" />
                  <text x={sc.px(t)} y={PLOT.mt + PLOT.h + 16} className="axt" textAnchor="middle">{fmtAmpTick(t)}</text>
                </g>
              ))}
              {sc.yTicks.map((t) => (
                <g key={`y${t}`}>
                  <line x1={PLOT.ml} y1={sc.py(t)} x2={PLOT.ml + PLOT.w} y2={sc.py(t)} className="grid" />
                  <text x={PLOT.ml - 8} y={sc.py(t) + 3} className="axt" textAnchor="end">{fmtSecTick(t)}</text>
                </g>
              ))}
              <text x={PLOT.ml + PLOT.w / 2} y={PLOT.mt + PLOT.h + 38} className="axl" textAnchor="middle">Current (A)</text>
              <text transform={`translate(16 ${PLOT.mt + PLOT.h / 2}) rotate(-90)`} className="axl" textAnchor="middle">Time (s)</text>
              {scaledCurves.map((c) => (
                <path key={c.id} d={sc.livePath(c.points)} fill="none" stroke="#14507d" strokeWidth={2.6} strokeLinejoin="round" strokeLinecap="round" />
              ))}
            </svg>
          </div>
        </section>
      </div>

      {plot.warnings?.length ? <div className="sel-status warn">{plot.warnings.join(' · ')}</div> : null}
      <div className="method">
        <b>Nominal class curve (bounded).</b> Rendered from the engine (`/tmt/plot-tcc`) as the nominal thermal class curve, scaled to absolute amps by the selected amp rating ({ampRating || '—'} A). Per the engine, the amp-rating / setting / thermal-adjustment selections are surfaced but <b>not yet applied to the plotted shape</b>, and the magnetic step isn't overlaid — use the <b>NETA test plan</b> (Protection Settings) for field values. {selection.trustNote}
      </div>

      <div className="stats">
        {stats.map((s) => (<div key={s.k} className="stat"><span>{s.k}</span><b>{s.v}</b></div>))}
      </div>
    </>
  )
}

// ── Screen 3 EMT (context-only): curve withheld (pickup→current calc not engine-validated) ──
function EmtCurve({ selection }: { selection: LiveSelection }) {
  return (
    <>
      <div className="curve-grid">
        <aside className="card side">
          <div className="card-h">Device Info <span className="badge inline">CONTEXT</span></div>
          <div className="card-b">
            <Field label="Breaker" value={selection.breakerLabel} />
            <Field label="Trip Unit" value={selection.tripLabel} />
            <Field label="Section" value={selection.ratingLabel} />
          </div>
        </aside>

        <section className="card plot-card">
          <div className="card-h">Trip Characteristic Curve <span className="badge inline">CONTEXT — curve pending Stage C</span></div>
          <div className="card-b" style={{ minHeight: 220, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
            <div style={{ maxWidth: 460 }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>📈</div>
              <p className="note">
                The stored EMT curve data is per-unit of pickup, and the EMT pickup → test-current conversion
                isn't engine-validated yet — so an absolute time-current curve is <b>deliberately withheld</b> here
                (same bounded posture as the EMT settings on Screen 2). It lands with the Stage C engine work.
                Use the section's pickup setting + ±tolerance on Protection Settings for field values.
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}

// ── Screen 3 ETU (LIVE): the operator's configured curve from /plot-tcc ────────
// Renders the lifted Screen-2 state (plug, pickups, delay bands, test multiples,
// maintenance mode, measured entries) — falling back to nominal defaults only when
// the operator jumps straight here. Delay times follow the G4 field-trust matrix
// (withheld exactly as on Screen 2); tolerance bands surface their basis per the
// NETA = manufacturer-tolerances law.
const CURVE_COLORS: Record<string, string> = {
  ltpu: '#2f8f5b', lt: '#2f8f5b', ltd: '#d98324', stpu: '#1d6fb8', std: '#d24b4b',
  inst: '#7c5cc4', gfpu: '#0d8f8f', gfd: '#b06fc4', nominal: '#14507d',
}

// Decade-snapped log-log scale fit to the actual curve envelope — replaces the fixed
// 100 A–100 kA / 0.01–1000 s domain so a device fills the plot instead of floating in a corner.
// Snaps each axis out to whole decades, guarantees a minimum span so a sparse curve still reads,
// and returns the matching px/py/clamp/path closures + decade tick lists.
function makeScale(amps: number[], times: number[], minXDecades = 2, minYDecades = 3) {
  const a = amps.filter((n) => n > 0 && Number.isFinite(n))
  const t = times.filter((n) => n > 0 && Number.isFinite(n))
  let x0 = a.length ? Math.floor(Math.log10(Math.min(...a))) : 1
  let x1 = a.length ? Math.ceil(Math.log10(Math.max(...a))) : 5
  let y0 = t.length ? Math.floor(Math.log10(Math.min(...t))) : -2
  let y1 = t.length ? Math.ceil(Math.log10(Math.max(...t))) : 3
  if (x1 - x0 < minXDecades) x1 = x0 + minXDecades
  if (y1 - y0 < minYDecades) y1 = y0 + minYDecades
  const sx = (n: number) => PLOT.ml + ((Math.log10(n) - x0) / (x1 - x0)) * PLOT.w
  const sy = (s: number) => PLOT.mt + ((y1 - Math.log10(s)) / (y1 - y0)) * PLOT.h
  const cX = (n: number) => Math.max(PLOT.ml, Math.min(PLOT.ml + PLOT.w, sx(n)))
  const cY = (s: number) => Math.max(PLOT.mt, Math.min(PLOT.mt + PLOT.h, sy(s)))
  const path = (pts: { amps: number; seconds: number }[]) =>
    pts.filter((p) => p.amps > 0 && p.seconds > 0)
      .map((p, i) => `${i ? 'L' : 'M'}${cX(p.amps).toFixed(1)},${cY(p.seconds).toFixed(1)}`).join(' ')
  const decades = (lo: number, hi: number) => { const out: number[] = []; for (let d = lo; d <= hi; d++) out.push(10 ** d); return out }
  return { px: sx, py: sy, clampX: cX, clampY: cY, livePath: path, xTicks: decades(x0, x1), yTicks: decades(y0, y1) }
}
const fmtAmpTick = (a: number) => (a >= 1000 ? `${+(a / 1000).toPrecision(3)}k` : `${a}`)
const fmtSecTick = (s: number) => (s >= 1 ? `${s}` : `${+s.toPrecision(2)}`)

function trustBadge(trust: string | null | undefined, reason?: string | null) {
  // SC3 ruled badge words (Q2 MFR / Q3 N/A) — mirrors tcc.field_terminology's
  // '*' trust rows; lib/terminology.ts TRUST_BADGE_FALLBACK is the same set.
  if (!trust) return null
  const t = trust.toLowerCase()
  const title = reason ?? ''
  if (t === 'db') return <span className="trust ok" title={title}>MFR</span>
  if (t === 'unsupported') return <span className="trust no" title={title}>N/A</span>
  return <span className="trust verify" title={title}>VERIFY</span>
}

function EtuCurve({ selection, maint, chosen, testMult, measured }: {
  selection: LiveSelection
  maint: boolean
  chosen: EtuChosen | null
  testMult: Record<BandKey, number>
  measured: Record<string, string>
}) {
  const sensorId = selection.sensorId as number
  const [plot, setPlot] = useState<EtuPlotResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  // Composite band is the field view (default); per-element curves stay
  // available as a diagnostic layer behind this toggle.
  const [showElements, setShowElements] = useState(false)
  // Acceptance envelope (#124) — the lane's headline, default ON.
  const [showEnvelope, setShowEnvelope] = useState(true)
  // The operator's Screen-2 configuration drives the curve; nominal defaults only
  // when they jumped straight here (the page resets state on sensor change).
  const fromSettings = chosen != null && chosen.plug > 0

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null); setPlot(null)
    const request: Promise<EtuPlotRequest> = fromSettings
      ? Promise.resolve(buildEtuPlotRequest({ sensorId, chosen: chosen as EtuChosen, testMult, maint, measured }))
      : fetchEtuSettings(sensorId).then((s) => buildDefaultEtuPlotRequest(sensorId, s))
    request
      .then(fetchEtuPlot)
      .then((r) => { if (active) setPlot(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [sensorId, chosen, testMult, maint, measured, fromSettings])

  if (loading) return <div className="loadbox"><span className="spin" /> Generating curve…</div>
  if (err || !plot) return <div className="loadbox"><span className="sel-status err">⚠ {err ?? 'No curve data'}</span></div>

  const curves = plot.curves ?? []
  // Composite boundary bands (#122, G4 §3g): the classic staircase assembled
  // server-side. When the engine serves none, the per-element curves render
  // unconditionally (the pre-composite behavior).
  const bands = plot.composite_bands ?? []
  const showPerElement = showElements || bands.length === 0
  const bandColor = (b: EtuPlotCompositeBand) => (b.family === 'gf' ? '#b06fc4' : '#14507d')
  const bandNotes = bands
    .map((b) => ({ id: b.id, note: bandWidthNote(b) }))
    .filter((n): n is { id: string; note: string } => n.note != null)
  // Acceptance envelope (#124): the per-sensor mfr tolerances applied along
  // the served curves — the field-acceptance corridor, NOT the published pair.
  const envelopes = plot.envelope_bands ?? []
  const envColor = (family: string) => (family === 'gf' ? '#8a4ba0' : '#2c7fb8')
  const envelopeNotes = envelopes
    .map((b) => ({ id: b.id, note: envelopeNote(b) }))
    .filter((n): n is { id: string; note: string } => n.note != null)
  const envelopeBasisLines = envelopes.flatMap((b) =>
    b.element_basis.map((eb) => ({ key: `${b.id}-${eb.element}`, basis: eb })))
  const rowsByEl = new Map((plot.table_rows ?? []).map((r) => [r.element, r]))
  const delayMarkers = (plot.expected_markers ?? []).filter(
    (m) => m.kind === 'delay' && m.expected_current > 0 && m.expected_time != null && (m.expected_time as number) > 0,
  )
  const pickupMarkers = (plot.expected_markers ?? []).filter(
    (m) => m.kind === 'pickup' && m.expected_current > 0,
  )
  const measuredMarkers = (plot.measured_markers ?? [])
  const colorFor = (el: string) => CURVE_COLORS[(el ?? '').toLowerCase()] ?? '#14507d'
  const legendItems = Array.from(new Map(curves.map((c) => [c.element, { c: colorFor(c.element), t: c.element.toUpperCase() }])).values())
  const delayRows = (plot.table_rows ?? []).filter((r) => r.kind === 'delay')
  const allAmps = curves.flatMap((c) => c.points.map((p) => p.amps)).filter((a) => a > 0)
  const allTimes = curves.flatMap((c) => c.points.map((p) => p.seconds)).filter((t) => t > 0)
  // Auto-fit the log-log axes to the device envelope incl. markers, tolerance
  // whiskers, and measured points so nothing renders off-frame.
  const scale = makeScale(
    [
      ...allAmps,
      ...delayMarkers.map((m) => m.expected_current),
      ...pickupMarkers.flatMap((m) => [m.expected_current, m.limit_low ?? 0, m.limit_high ?? 0]),
      ...measuredMarkers.map((m) => m.measured_current ?? 0),
    ],
    [
      ...allTimes,
      ...delayMarkers.map((m) => m.expected_time as number),
      ...delayMarkers.flatMap((m) => {
        const r = rowsByEl.get(m.element)
        return [r?.time_limit_low ?? 0, r?.time_limit_high ?? 0]
      }),
      ...measuredMarkers.map((m) => m.measured_time ?? 0),
    ],
  )
  const measuredCount = measuredMarkers.length
  const stats = [
    { k: 'Curves', v: String(curves.length) },
    { k: 'Test Points', v: String(delayMarkers.length + pickupMarkers.length) },
    { k: 'Measured', v: measuredCount ? `${measuredCount} (${plot.meta.overall_pass == null ? '—' : plot.meta.overall_pass ? 'PASS' : 'FAIL'})` : '—' },
    { k: 'Plug', v: `${plot.meta.plug_rating} A` },
  ]
  const passColor = (ok: boolean) => (ok ? '#2f8f5b' : '#d24b4b')

  return (
    <>
      <div className="curve-grid">
        <aside className="card side">
          <div className="card-h">Device Info <span className="badge inline live">LIVE</span></div>
          <div className="card-b">
            <Field label="Breaker" value={selection.breakerLabel} />
            <Field label="Trip Unit" value={selection.tripLabel} />
            <Field label="Sensor" value={plot.meta.sensor_desc || selection.ratingLabel} />
            <Field label="Plug (Ir)" value={`${plot.meta.plug_rating} A`} />
            <Field label="Settings" value={fromSettings ? `Protection Settings${maint ? ' · MAINT' : ''}` : 'Nominal defaults'} />
          </div>
          {bands.length ? (
            <>
              <div className="card-h" style={{ marginTop: 8 }}>Composite Band</div>
              <div className="legend">
                {bands.map((b) => (
                  <div key={b.id} className="leg">
                    <span className="sw" style={{ background: bandColor(b) }} />
                    {b.family === 'gf' ? 'Ground fault' : 'Phase'} (min-trip / total-clear)
                  </div>
                ))}
                {bandNotes.map((n) => (
                  <div key={n.id} className="leg muted2" title={n.note}>⚠ {n.note}</div>
                ))}
                <label className="leg" style={{ cursor: 'pointer', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    checked={showElements}
                    onChange={(e) => setShowElements(e.target.checked)}
                    style={{ marginRight: 6 }}
                  />
                  Show per-element curves
                </label>
              </div>
            </>
          ) : null}
          {envelopes.length ? (
            <>
              <div className="card-h" style={{ marginTop: 8 }}>Acceptance Envelope</div>
              <div className="legend">
                <label className="leg" style={{ cursor: 'pointer', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    checked={showEnvelope}
                    onChange={(e) => setShowEnvelope(e.target.checked)}
                    style={{ marginRight: 6 }}
                  />
                  Show tolerance envelope
                </label>
                {envelopes.map((b) => (
                  <div key={`env-${b.id}`} className="leg">
                    <span className="sw" style={{ background: envColor(b.family), opacity: 0.6 }} />
                    {b.family === 'gf' ? 'Ground fault' : 'Phase'} field-acceptance corridor
                  </div>
                ))}
                {envelopeBasisLines.map(({ key, basis }) => (
                  <div key={key} className="leg muted2" title={`Tolerance basis for ${basis.element}: pickup from the per-sensor DB tolerance; time per ${basis.time_source ?? '—'}`}>
                    {envelopeBasisLine(basis)}
                  </div>
                ))}
                {envelopeNotes.map((n) => (
                  <div key={`env-note-${n.id}`} className="leg muted2" title={n.note}>⚠ {n.note}</div>
                ))}
              </div>
            </>
          ) : null}
          <div className="card-h" style={{ marginTop: 8 }}>Curve Elements</div>
          <div className="legend">
            {legendItems.length ? legendItems.map((l) => {
              const row = rowsByEl.get(l.t)
              return (
                <div key={l.t} className="leg">
                  <span className="sw" style={{ background: l.c }} />{l.t}
                  {row?.kind === 'delay' ? <>&nbsp;{trustBadge(row.trust, row.trust_reason)}</> : null}
                </div>
              )
            }) : <div className="leg muted2">No curve segments</div>}
          </div>
          {delayRows.length ? (
            <>
              <div className="card-h" style={{ marginTop: 8 }}>Time Tolerance Basis</div>
              <div className="legend">
                {delayRows.map((r) => (
                  <div key={`basis-${r.element}`} className="leg muted2" title={r.trust_reason ?? ''}>
                    {r.element}: {r.trust === 'unsupported' ? 'withheld — no certified basis' : delayBasisLabel(r.notes) ?? '—'}
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </aside>

        <section className="card plot-card">
          <div className="card-h">Trip Characteristic Curve <span className="badge inline live">{fromSettings ? 'LIVE · your settings' : 'LIVE · nominal defaults'}</span></div>
          <div className="plot-wrap">
            <svg viewBox="0 0 700 500" className="plot" role="img" aria-label="Time-current curve">
              {scale.xTicks.map((t) => (
                <g key={`x${t}`}>
                  <line x1={scale.px(t)} y1={PLOT.mt} x2={scale.px(t)} y2={PLOT.mt + PLOT.h} className="grid" />
                  <text x={scale.px(t)} y={PLOT.mt + PLOT.h + 16} className="axt" textAnchor="middle">{fmtAmpTick(t)}</text>
                </g>
              ))}
              {scale.yTicks.map((t) => (
                <g key={`y${t}`}>
                  <line x1={PLOT.ml} y1={scale.py(t)} x2={PLOT.ml + PLOT.w} y2={scale.py(t)} className="grid" />
                  <text x={PLOT.ml - 8} y={scale.py(t) + 3} className="axt" textAnchor="end">{fmtSecTick(t)}</text>
                </g>
              ))}
              <text x={PLOT.ml + PLOT.w / 2} y={PLOT.mt + PLOT.h + 38} className="axl" textAnchor="middle">Current (A)</text>
              <text transform={`translate(16 ${PLOT.mt + PLOT.h / 2}) rotate(-90)`} className="axl" textAnchor="middle">Time (s)</text>
              {/* Acceptance envelope (#124): the field-acceptance corridor —
                  per-sensor mfr PU tolerances along the amps axis + the
                  time-tolerance basis (LTD) along the seconds axis. Rendered
                  BEHIND the published band: the band stays the primary
                  visual, the envelope is the acceptance overlay. */}
              {showEnvelope ? envelopes.map((b) => {
                const stroke = envColor(b.family)
                const poly = envelopePolygonPoints(b) // [] unless BOTH boundaries exist
                const min = b.min_points ?? []
                const max = b.max_points ?? []
                return (
                  <g key={b.id}>
                    {poly.length ? (
                      <path d={`${scale.livePath(poly)} Z`} fill={stroke} opacity={0.07} stroke="none" />
                    ) : null}
                    {min.length ? (
                      <path d={scale.livePath(min)} fill="none" stroke={stroke} strokeWidth={1.2} strokeDasharray="2 3" strokeLinejoin="round" opacity={0.75}>
                        <title>{`${b.family === 'gf' ? 'Ground-fault' : 'Phase'} acceptance envelope — minimum`}</title>
                      </path>
                    ) : null}
                    {max.length ? (
                      <path d={scale.livePath(max)} fill="none" stroke={stroke} strokeWidth={1.2} strokeDasharray="2 3" strokeLinejoin="round" opacity={0.75}>
                        <title>{`${b.family === 'gf' ? 'Ground-fault' : 'Phase'} acceptance envelope — maximum`}</title>
                      </path>
                    ) : null}
                  </g>
                )
              }) : null}
              {/* Composite boundary bands (G4 §3g): shaded min-trip→total-clear
                  polygon per family — phase staircase + the GF crossing band.
                  Off-frame extents (1e6 s asymptote top, right-edge cap) clamp
                  to the plot frame via the scale's clamped path builder. */}
              {bands.map((b) => {
                const fill = bandColor(b)
                const poly = bandPolygonPoints(b) // [] unless BOTH boundaries exist
                const open = b.open_points ?? []
                const clear = b.clear_points ?? []
                return (
                  <g key={b.id}>
                    {poly.length ? (
                      <path d={`${scale.livePath(poly)} Z`} fill={fill} opacity={0.14} stroke="none" />
                    ) : null}
                    {open.length ? (
                      <path d={scale.livePath(open)} fill="none" stroke={fill} strokeWidth={2.6} strokeLinejoin="round" strokeLinecap="round" opacity={0.95}>
                        <title>{`${b.family === 'gf' ? 'Ground-fault' : 'Phase'} band — minimum trip (open)`}</title>
                      </path>
                    ) : null}
                    {clear.length ? (
                      <path d={scale.livePath(clear)} fill="none" stroke={fill} strokeWidth={1.6} strokeDasharray="6 4" strokeLinejoin="round" opacity={0.7}>
                        <title>{`${b.family === 'gf' ? 'Ground-fault' : 'Phase'} band — total clear`}</title>
                      </path>
                    ) : null}
                  </g>
                )
              })}
              {showPerElement ? curves.map((c) => (
                <path key={c.id} d={scale.livePath(c.points)} fill="none" stroke={colorFor(c.element)} strokeWidth={bands.length ? 1.6 : 2.4} strokeLinejoin="round" strokeLinecap="round" opacity={bands.length ? 0.65 : 0.92} />
              )) : null}
              {/* Pickup test points: vertical marker at the expected pickup with the
                  DB tolerance band as a horizontal whisker lane above the axis. */}
              {pickupMarkers.map((m, i) => {
                const x = scale.clampX(m.expected_current)
                const laneY = PLOT.mt + PLOT.h - 12 - i * 12
                const lo = m.limit_low != null && m.limit_low > 0 ? scale.clampX(m.limit_low) : null
                const hi = m.limit_high != null && m.limit_high > 0 ? scale.clampX(m.limit_high) : null
                return (
                  <g key={m.id} opacity={0.9}>
                    <line x1={x} y1={PLOT.mt} x2={x} y2={PLOT.mt + PLOT.h} stroke={colorFor(m.element)} strokeWidth={1.2} strokeDasharray="5 4" opacity={0.55} />
                    {lo != null && hi != null ? (
                      <g stroke={colorFor(m.element)} strokeWidth={1.6}>
                        <line x1={lo} y1={laneY} x2={hi} y2={laneY} />
                        <line x1={lo} y1={laneY - 4} x2={lo} y2={laneY + 4} />
                        <line x1={hi} y1={laneY - 4} x2={hi} y2={laneY + 4} />
                      </g>
                    ) : null}
                    <title>{`${m.element} 1× — ${Math.round(m.expected_current).toLocaleString('en-US')} A${lo != null && hi != null ? ` (limits ${Math.round(m.limit_low as number).toLocaleString('en-US')}–${Math.round(m.limit_high as number).toLocaleString('en-US')} A)` : ''}`}</title>
                  </g>
                )
              })}
              {/* Delay test points: diamond at the expected time with the time
                  tolerance band as a vertical whisker. */}
              {delayMarkers.map((m) => {
                const x = scale.clampX(m.expected_current)
                const y = scale.clampY(m.expected_time as number)
                const row = rowsByEl.get(m.element)
                const lo = row?.time_limit_low != null && row.time_limit_low > 0 ? scale.clampY(row.time_limit_low) : null
                const hi = row?.time_limit_high != null && row.time_limit_high > 0 ? scale.clampY(row.time_limit_high) : null
                return (
                  <g key={m.id}>
                    {lo != null && hi != null ? (
                      <g stroke={colorFor(m.element)} strokeWidth={1.6} opacity={0.85}>
                        <line x1={x} y1={lo} x2={x} y2={hi} />
                        <line x1={x - 5} y1={lo} x2={x + 5} y2={lo} />
                        <line x1={x - 5} y1={hi} x2={x + 5} y2={hi} />
                      </g>
                    ) : null}
                    <rect x={x - 5} y={y - 5} width={10} height={10}
                      transform={`rotate(45 ${x} ${y})`}
                      fill={colorFor(m.element)} stroke="#fff" strokeWidth={1.5}>
                      <title>{`${m.element} ${fmtMult(m.test_multiple)} — ${Math.round(m.expected_current).toLocaleString('en-US')} A, ${(m.expected_time as number).toFixed(3)} s${row?.time_limit_low != null && row?.time_limit_high != null ? ` (band ${row.time_limit_low}–${row.time_limit_high} s)` : ''}${row ? ` · ${delayBasisLabel(row.notes) ?? ''}` : ''}`}</title>
                    </rect>
                  </g>
                )
              })}
              {/* Measured results: pickups as vertical pass/fail lines, delay trips
                  as pass/fail dots at the inject current. */}
              {measuredMarkers.map((m) => {
                if (m.kind === 'pickup' && m.measured_current != null && m.measured_current > 0) {
                  const x = scale.clampX(m.measured_current)
                  return (
                    <line key={m.id} x1={x} y1={PLOT.mt} x2={x} y2={PLOT.mt + PLOT.h}
                      stroke={passColor(m.passed)} strokeWidth={2} strokeDasharray="7 4">
                      <title>{`${m.element} measured ${Math.round(m.measured_current).toLocaleString('en-US')} A — ${m.passed ? 'PASS' : 'FAIL'}${m.deviation_pct != null ? ` (${m.deviation_pct >= 0 ? '+' : ''}${m.deviation_pct.toFixed(1)}%)` : ''}`}</title>
                    </line>
                  )
                }
                if (m.kind === 'delay' && m.measured_time != null && m.measured_time > 0 && m.measured_current != null && m.measured_current > 0) {
                  return (
                    <circle key={m.id} cx={scale.clampX(m.measured_current)} cy={scale.clampY(m.measured_time)} r={5.5}
                      fill={passColor(m.passed)} stroke="#fff" strokeWidth={1.5}>
                      <title>{`${m.element} measured ${m.measured_time} s — ${m.passed ? 'PASS' : 'FAIL'}${m.deviation_pct != null ? ` (${m.deviation_pct >= 0 ? '+' : ''}${m.deviation_pct.toFixed(1)}%)` : ''}`}</title>
                    </circle>
                  )
                }
                return null
              })}
            </svg>
          </div>
        </section>
      </div>

      {plot.warnings?.length ? <div className="sel-status warn">{plot.warnings.join(' · ')}</div> : null}
      <div className="method">
        <b>{fromSettings ? 'Configured curve.' : 'Nominal defaults.'}</b> Rendered live from the engine (`/plot-tcc`) at {fromSettings ? <>your <b>Protection Settings</b> — plug, pickups, delay bands, test multiples{maint ? ', maintenance mode' : ''}</> : <>the sensor&apos;s nominal defaults — configure on <b>Protection Settings</b> to render your test plan</>}. The <b>shaded band</b> is the composite trip boundary assembled per the native engine&apos;s plot semantics (G4 §3g): a vertical pickup asymptote, each delay element clipped at its handoff to the next, and the instantaneous floor running to the plot edge — solid = <b>minimum trip</b>, dashed = <b>total clear</b>; ground fault draws as its own crossing band. Per-element curves remain available behind the legend toggle for diagnosis. Delay curves and times follow the <b>G4 field-trust matrix</b>: <b>DB</b> = direct-band + LTD + the native-validated inverse equations (bit-exact vs the EasyPower kernel); <b>verify</b> = I²t composite (native spot-check pending); <b>n/a</b> = withheld. Time tolerance whiskers use the <b>manufacturer&apos;s values</b> where on file (NETA acceptance = mfr tolerances) — the basis per element is listed beside the legend. Markers sit at the NETA test points; measured entries from Screen 2 overlay as pass/fail markers.{plot.meta.plot_disclaimer ? ` ${plot.meta.plot_disclaimer}` : ''}
      </div>

      <div className="stats">
        {stats.map((s) => (<div key={s.k} className="stat"><span>{s.k}</span><b>{s.v}</b></div>))}
      </div>
    </>
  )
}

const CSS = `
.tccx{--bg:#eef2f6;--surface:#fff;--ink:#0f1f2e;--muted:#5b6b7a;--brand:#14507d;--brand-d:#0d3a5f;--brand-l:#1d6fb8;--green:#2f8f5b;--green-s:#e3f3ea;--amber:#d28a1e;--amber-s:#fbf0d8;--red:#d24b4b;--line:#e2e8ef;--line-2:#eef2f6;
 position:fixed;inset:0;overflow:auto;background:var(--bg);color:var(--ink);
 font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;}
.tccx *{box-sizing:border-box;}
.bar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 28px;
 background:linear-gradient(100deg,var(--brand-d),var(--brand));color:#fff;}
.brand{display:flex;align-items:center;gap:14px;}
.mark{font-size:22px;width:40px;height:40px;display:grid;place-items:center;background:rgba(255,255,255,.14);border-radius:10px;}
.title{font-size:18px;font-weight:700;letter-spacing:.2px;}
.sub{font-size:12px;opacity:.8;margin-top:1px;}
.device-chip{display:flex;align-items:center;gap:8px;font-size:12.5px;background:rgba(255,255,255,.12);padding:7px 13px;border-radius:999px;max-width:46vw;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}
.device-chip .dot{width:7px;height:7px;border-radius:50%;background:#5fdca0;box-shadow:0 0 0 3px rgba(95,220,160,.25);flex:none;}
.steps{display:flex;gap:6px;padding:14px 28px 0;flex-wrap:wrap;}
.step{display:flex;align-items:center;gap:9px;border:1px solid var(--line);background:var(--surface);color:var(--muted);
 padding:9px 16px;border-radius:10px;font-size:13.5px;font-weight:600;cursor:pointer;transition:.15s;}
.step:hover{border-color:var(--brand-l);color:var(--brand);}
.step .num{width:21px;height:21px;border-radius:50%;display:grid;place-items:center;font-size:12px;background:var(--line);color:var(--muted);}
.step.on{background:var(--brand);border-color:var(--brand);color:#fff;box-shadow:0 6px 16px rgba(20,80,125,.25);}
.step.on .num{background:rgba(255,255,255,.25);color:#fff;}
.step.done .num{background:var(--green);color:#fff;}
.wrap{padding:22px 28px;max-width:1080px;margin:0 auto;display:flex;flex-direction:column;gap:18px;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
@media(max-width:820px){.grid2{grid-template-columns:1fr;}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:0 1px 2px rgba(15,31,46,.04);overflow:hidden;}
.card-h{font-size:13.5px;font-weight:700;color:var(--brand-d);padding:13px 18px;border-bottom:1px solid var(--line-2);display:flex;align-items:center;gap:9px;background:#fafbfd;}
.card-h.light{color:var(--brand);}
.idx{width:20px;height:20px;border-radius:6px;background:var(--brand);color:#fff;display:grid;place-items:center;font-size:12px;font-weight:700;}
.card-b{padding:14px 18px 16px;}
.field{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:9px 0;border-bottom:1px dashed var(--line-2);}
.field:last-child{border-bottom:none;}
.flabel{font-size:12.5px;color:var(--muted);font-weight:600;}
.fvalue{font-size:13.5px;font-weight:600;color:var(--ink);background:var(--line-2);padding:5px 12px;border-radius:7px;min-width:130px;text-align:right;}
.soft .card-b{padding-top:14px;}
.muted-b{display:flex;flex-direction:column;gap:9px;}
.note{font-size:13px;color:var(--muted);line-height:1.55;margin:0;}
/* family tabs */
.fam-tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;}
.fam-tab{flex:1;min-width:140px;display:flex;flex-direction:column;gap:1px;align-items:flex-start;border:1px solid var(--line);background:#fafbfd;border-radius:11px;padding:11px 15px;cursor:pointer;transition:.15s;}
.fam-tab b{font-size:15px;color:var(--ink);letter-spacing:.3px;}
.fam-tab span{font-size:11.5px;color:var(--muted);}
.fam-tab:hover{border-color:var(--brand-l);}
.fam-tab.on{border-color:var(--brand);background:#eaf2fb;box-shadow:inset 0 0 0 1px var(--brand);}
.fam-tab.on b{color:var(--brand-d);}
/* selectors */
.selwrap{display:flex;flex-direction:column;gap:12px;}
.selrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;}
.pick{display:flex;flex-direction:column;gap:5px;}
.pick.wide{grid-column:1 / -1;}
.pick-l{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;display:flex;align-items:center;gap:7px;}
.pick-s{width:100%;font-size:13.5px;font-weight:600;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 11px;cursor:pointer;}
.pick-s:focus{outline:2px solid var(--brand-l);outline-offset:-1px;border-color:var(--brand-l);}
.pick-s:disabled{background:var(--line-2);color:#9aa7b3;cursor:default;}
.spin{width:11px;height:11px;border-radius:50%;border:2px solid var(--line);border-top-color:var(--brand);display:inline-block;animation:sp .7s linear infinite;}
@keyframes sp{to{transform:rotate(360deg);}}
.sel-status{font-size:12.5px;color:var(--muted);background:var(--line-2);border-radius:8px;padding:9px 12px;}
.sel-status.warn{color:#8a5a00;background:var(--amber-s);border:1px solid var(--amber);}
.sel-status.err{color:#fff;background:var(--red);}
/* co-equal dual axes */
.axes{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
@media(max-width:820px){.axes{grid-template-columns:1fr;}}
.axis{border:1px solid var(--line);border-radius:12px;padding:13px 15px;background:#fafbfd;display:flex;flex-direction:column;gap:11px;}
.axis.brk{border-top:3px solid var(--brand-l);}
.axis.trp{border-top:3px solid var(--green);}
.axis-h{display:flex;align-items:center;gap:9px;font-size:12px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;color:var(--brand-d);}
.ax-ic{width:22px;height:22px;border-radius:6px;display:grid;place-items:center;color:#fff;font-size:12px;flex:none;}
.axis.brk .ax-ic{background:var(--brand-l);}
.axis.trp .ax-ic{background:var(--green);}
.sensor-term{border:1px solid var(--brand-l);border-radius:12px;padding:13px 15px;background:#eef5fb;display:flex;flex-direction:column;gap:9px;}
.sensor-term .pick-l{color:var(--brand-d);}
.xf-status{font-size:12px;font-weight:600;color:var(--muted);}
.xf-status.ok{color:var(--brand-d);}
.xf-status.empty{color:#8a2a2a;}
.xf-count{font-weight:800;color:var(--brand);font-variant-numeric:tabular-nums;}
.summary{background:linear-gradient(100deg,#1f7a4d,#2f8f5b);color:#fff;border-radius:14px;padding:16px 20px;box-shadow:0 10px 24px rgba(47,143,91,.22);}
.summary-h{font-size:14px;font-weight:700;margin-bottom:12px;}
.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 28px;}
@media(max-width:820px){.summary-grid{grid-template-columns:1fr;}}
.summary-grid div{font-size:13.5px;display:flex;gap:10px;align-items:baseline;}
.summary-grid span{font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;opacity:.85;min-width:64px;font-weight:700;}
.summary-warn{margin-top:12px;font-size:12.5px;background:rgba(255,255,255,.16);border-radius:8px;padding:9px 12px;}
.eq-strip{display:flex;flex-wrap:wrap;gap:8px 26px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 18px;}
.eq-strip div{font-size:13px;display:flex;gap:8px;align-items:baseline;}
.eq-strip span{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;}
.badge{background:var(--amber);color:#fff;border-radius:5px;padding:2px 7px;font-size:10px;letter-spacing:.5px;font-weight:800;}
.badge.inline{margin-left:auto;}
.badge.live{background:var(--green);}
.loadbox{display:flex;align-items:center;gap:10px;justify-content:center;padding:44px;color:var(--muted);font-size:13.5px;font-weight:600;}
.plugpick{display:flex;align-items:center;gap:8px;}
.plugpick .el-select{width:auto;min-width:88px;}
.trust{font-size:10px;font-weight:800;letter-spacing:.4px;padding:2px 7px;border-radius:5px;display:inline-block;}
.trust.ok{color:var(--green);background:var(--green-s);}
.trust.verify{color:#8a5a00;background:var(--amber-s);}
.trust.no{color:#b42318;background:#fde8e6;}
.maint-banner{display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid var(--line);border-radius:12px;padding:13px 18px;background:var(--surface);}
.maint-banner.on{background:var(--amber-s);border-color:var(--amber);}
.maint-banner b{font-size:13.5px;}
.maint-banner span{display:block;font-size:12.5px;color:var(--muted);margin-top:2px;}
.toggle{width:46px;height:26px;border-radius:999px;border:none;background:var(--line);position:relative;cursor:pointer;transition:.18s;flex:none;}
.toggle span{position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);transition:.18s;}
.toggle.on{background:var(--amber);}
.toggle.on span{left:23px;}
.elgrid{gap:14px;}
.el-card{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;border-left:3px solid var(--brand-l);}
.el-card.off{opacity:.55;border-left-color:var(--line);}
.el-h{display:flex;align-items:center;justify-content:space-between;padding:11px 15px;border-bottom:1px solid var(--line-2);background:#fafbfd;}
.el-code{display:flex;flex-direction:column;}
.el-code b{font-size:15px;letter-spacing:.3px;}
.el-code span{font-size:11.5px;color:var(--muted);}
.pill{font-size:10.5px;font-weight:800;letter-spacing:.6px;padding:4px 10px;border-radius:999px;color:#fff;}
.pill-green{background:var(--green);}
.pill-blue{background:var(--brand-l);}
.pill-amber{background:var(--amber);}
.el-b{padding:12px 15px;display:flex;flex-direction:column;gap:10px;}
.el-row span{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;display:block;margin-bottom:4px;}
.el-row.two{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.el-input{border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:13.5px;font-weight:600;background:#fff;}
.el-mult{font-size:13.5px;font-weight:700;color:var(--brand);background:#e6eef5;padding:8px 12px;border-radius:8px;text-align:center;}
.el-mult.muted{color:#9aa7b3;background:var(--line-2);}
.el-select{width:100%;font-size:13.5px;font-weight:700;color:var(--brand);background:#fff;border:1px solid var(--brand-l);border-radius:8px;padding:7px 10px;cursor:pointer;}
.el-select:focus{outline:2px solid var(--brand-l);outline-offset:-1px;}
.el-cur{font-size:13.5px;font-weight:700;padding:8px 12px;border-radius:8px;background:var(--line-2);text-align:center;}
.bands{width:100%;border-collapse:collapse;font-size:13px;}
.bands th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);padding:11px 18px;border-bottom:1px solid var(--line);background:#fafbfd;}
.bands td{padding:11px 18px;border-bottom:1px solid var(--line-2);}
.bands td.num{font-variant-numeric:tabular-nums;font-weight:600;}
.bands tr:last-child td{border-bottom:none;}
.row-off td{color:#9aa7b3;}
.status{font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;display:inline-block;}
.status.ready{color:var(--green);background:var(--green-s);}
.status.off{color:#9aa7b3;background:var(--line-2);}
.status.pass{color:#fff;background:var(--green);}
.status.fail{color:#fff;background:var(--red);}
.bands-wrap{overflow-x:auto;}
.meas{display:flex;align-items:center;gap:6px;}
.meas-in{width:84px;border:1px solid var(--line);border-radius:7px;padding:6px 9px;font-size:13px;font-weight:600;font-variant-numeric:tabular-nums;background:#fff;}
.meas-in:focus{outline:2px solid var(--brand-l);outline-offset:-1px;border-color:var(--brand-l);}
.meas-u{font-size:11px;color:var(--muted);font-weight:700;}
.pct{font-weight:700;}
.pct.ok{color:var(--green);}
.pct.bad{color:var(--red);}
.muted2{color:#9aa7b3;}
.method{font-size:12.5px;color:#3a4a58;line-height:1.6;background:#eaf2fb;border:1px solid #d3e3f5;border-left:3px solid var(--brand-l);border-radius:10px;padding:13px 18px;}
.el-sub{font-size:11px;color:var(--muted);font-weight:600;margin-top:2px;}
.tol-strip{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:14px;padding-top:13px;border-top:1px solid var(--line-2);}
.tol-strip div{display:flex;flex-direction:column;gap:3px;}
.tol-strip span{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;}
.tol-strip b{font-size:15px;color:var(--ink);}
.curve-grid{display:grid;grid-template-columns:248px 1fr;gap:18px;}
@media(max-width:820px){.curve-grid{grid-template-columns:1fr;}}
.side .card-h{margin-top:0;}
.legend{padding:12px 18px 16px;display:flex;flex-direction:column;gap:10px;}
.leg{display:flex;align-items:center;gap:11px;font-size:13px;font-weight:600;}
.sw{width:26px;height:11px;border-radius:3px;flex:none;}
.plot-wrap{padding:14px;}
.plot{width:100%;height:auto;display:block;}
.grid{stroke:#e7edf3;stroke-width:1;}
.axt{font-size:11px;fill:var(--muted);}
.axl{font-size:12px;fill:var(--ink);font-weight:700;}
.band{fill:rgba(29,111,184,.13);stroke:none;}
.nominal{fill:none;stroke:var(--brand);stroke-width:2.6;stroke-linejoin:round;stroke-linecap:round;}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
@media(max-width:820px){.stats{grid-template-columns:1fr 1fr;}}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;border-top:3px solid var(--brand);}
.stat span{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;display:block;}
.stat b{font-size:19px;margin-top:4px;display:block;}
.foot{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 28px 28px;max-width:1080px;margin:0 auto;font-size:12px;color:var(--muted);}
.nav-btns{display:flex;gap:10px;}
.btn{border:none;background:var(--brand);color:#fff;font-weight:700;font-size:13px;padding:10px 20px;border-radius:9px;cursor:pointer;}
.btn:hover{background:var(--brand-d);}
.btn.ghost{background:transparent;color:var(--brand);border:1px solid var(--line);}
.btn:disabled{opacity:.4;cursor:default;}

/* ── B2.1 field tolerance sheet (print-first; light theme regardless of app theme) ── */
.sheet-btn{float:right;padding:6px 14px;font-size:12px;}
.sheet-overlay{position:fixed;inset:0;z-index:60;overflow:auto;background:rgba(10,14,20,.72);padding:26px 16px 60px;}
.sheet-actions{display:flex;gap:10px;justify-content:flex-end;max-width:1080px;margin:0 auto 12px;}
.sheet-card{max-width:1080px;margin:0 auto;background:#fff;color:#16181c;border-radius:10px;padding:26px 30px;box-shadow:0 18px 60px rgba(0,0,0,.5);font-size:12px;line-height:1.45;}
.sheet-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:2px solid #16181c;padding-bottom:10px;}
.sheet-title{font-size:17px;font-weight:800;}
.sheet-sub{font-size:11px;color:#555;margin-top:2px;}
.sheet-meta{text-align:right;font-size:11px;color:#444;}
.sheet-id{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:6px 22px;padding:10px 0 4px;}
.sheet-id span{display:block;font-size:9.5px;text-transform:uppercase;letter-spacing:.5px;color:#666;font-weight:700;}
.sheet-id b{font-size:12.5px;}
.sheet-maint{margin:8px 0 2px;padding:7px 12px;border:1.5px solid #b45309;background:#fef3c7;color:#92400e;font-weight:700;border-radius:6px;font-size:11.5px;}
.sheet-fill{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:12px 0 14px;}
.sheet-fill span{display:block;font-size:9.5px;text-transform:uppercase;letter-spacing:.5px;color:#666;font-weight:700;margin-bottom:14px;}
.sheet-fill i{display:block;border-bottom:1px solid #444;height:1px;}
.sheet-table{width:100%;border-collapse:collapse;font-size:11px;}
.sheet-table th{border:1px solid #333;background:#eef1f5;padding:6px 7px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.3px;}
.sheet-table th.wide{min-width:80px;}
.sheet-table td{border:1px solid #333;padding:6px 7px;vertical-align:top;}
.sheet-table td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;}
.sheet-table td.el{white-space:nowrap;}
.sheet-table td.meth{font-size:10px;color:#333;max-width:210px;}
.sheet-table td.badge-cell{font-weight:800;font-size:10px;}
.sheet-table td.fill{min-width:64px;}
.sheet-table tr.wh td{color:#777;}
.sheet-table tr{page-break-inside:avoid;}
.sheet-elnotes{margin-top:10px;font-size:10.5px;color:#333;}
.sheet-warn{margin-top:8px;font-size:10.5px;color:#92400e;}
.sheet-notes{margin-top:10px;font-size:10.5px;color:#333;}
.sheet-notes div{margin-top:2px;}
.sheet-law{margin-top:12px;padding-top:8px;border-top:1.5px solid #16181c;font-size:10.5px;font-weight:600;}
.sheet-gen{margin-top:6px;font-size:9.5px;color:#777;}
@media print{
  @page{size:letter landscape;margin:10mm;}
  body *{visibility:hidden;}
  .sheet-overlay,.sheet-overlay *{visibility:visible;}
  .no-print,.no-print *{visibility:hidden!important;display:none!important;}
  .sheet-overlay{position:absolute;inset:auto;left:0;top:0;width:100%;background:#fff;padding:0;overflow:visible;}
  .sheet-card{box-shadow:none;border-radius:0;max-width:none;padding:0;}
}
`
