'use client'

/**
 * LV Breaker TCC — operator-facing field-tolerance tool.
 * 3-screen flow: Specifications -> Protection Settings -> TCC Curve.
 *
 * Stage A (this build): Screen 1 (Specifications) is LIVE — family-polymorphic
 * (ETU / TMT / EMT) selection wired to the control-plane API via lib/breaker-resources.
 *   - ETU uses the recovered SST bridge (GET /etu/bridge-sensors) to narrow a chosen
 *     breaker style to its compatible ETU sensor set (D1 / migration 006).
 *   - TMT / EMT use their existing frame/section browse routes.
 * Screens 2-3 still render the frozen SAMPLE configuration (badged) until Stage B
 * (live per-family settings/tolerances) and Stage C (live per-family curve) land.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  fetchEtuBreakerCascade,
  fetchCascade,
  fetchEtuBridgeSensors,
  fetchEtuSettings,
  fetchEtuContext,
  fetchEtuCalculate,
  fetchTmtFrames,
  fetchTmtSettings,
  fetchEmtFrames,
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
  type TMTFrameSearchResult,
  type TMTSettingsResponse,
  type EMTFrameSearchResult,
  type EMTFrameContext,
  type EMTSectionSettingsResponse,
} from '../../lib/breaker-resources'

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

const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Request failed')

// ── frozen sample (operator's TCC_Calculator_v5.xlsx) — Screens 2-3 until Stage B/C ──
const DEVICE = {
  breakerClass: 'MCCB',
  breakerMfr: 'Square D',
  breakerType: 'P Frame',
  breakerStyle: 'PX',
  frameSize: '2500 A',
  tripType: 'Solid State',
  tripMfr: 'Square D',
  tripDetail: 'Micrologic 6.0H',
  tripStyle: 'MCCB',
  sensorIr: '2500 A',
  plug: '2500 A',
  effectiveIr: '2500 A',
}

type DelayKey = 'ltd' | 'std' | 'gfd'
type Elt = {
  code: string
  label: string
  kind: 'PICKUP' | 'DELAY' | 'INSTANT' | 'GROUND' | 'GF DELAY' | 'ARC MODE'
  setting: string
  base?: number
  delay?: DelayKey
  disabled?: boolean
}

const ELEMENTS: Elt[] = [
  { code: 'LTPU', label: 'Long-Time Pickup', kind: 'PICKUP', setting: '0.90 × Ir', base: 2250 },
  { code: 'LTD', label: 'Long-Time Delay', kind: 'DELAY', setting: '12 s', base: 2250, delay: 'ltd' },
  { code: 'STPU', label: 'Short-Time Pickup', kind: 'PICKUP', setting: '3.2 × Ir', base: 8000 },
  { code: 'STD', label: 'Short-Time Delay', kind: 'DELAY', setting: '0.30 s (I²t)', base: 8000, delay: 'std' },
  { code: 'INST', label: 'Instantaneous', kind: 'INSTANT', setting: '5.1 × Ir', base: 12800 },
  { code: 'GFPU', label: 'Ground-Fault Pickup', kind: 'GROUND', setting: 'Disabled', disabled: true },
  { code: 'GFD', label: 'Ground-Fault Delay', kind: 'GF DELAY', setting: 'Disabled', delay: 'gfd', disabled: true },
  { code: 'MAINT', label: 'Maintenance / ARMS', kind: 'ARC MODE', setting: 'Disabled', disabled: true },
]

const MULT_OPTS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]
const DELAY_DEFAULT: Record<DelayKey, number> = { ltd: 3, std: 1.5, gfd: 1.5 }
const fmtA = (n: number) => `${Math.round(n).toLocaleString('en-US')} A`
const fmtMult = (m: number) => `${Number.isInteger(m) ? m : m.toFixed(1)}×`

type Unit = 'A' | 's' | ''
type Band = { el: string; nominal: number; min: number; max: number; unit: Unit; status: 'ready' | 'disabled' }
const BANDS: Band[] = [
  { el: 'LTPU', nominal: 2250, min: 2025, max: 2475, unit: 'A', status: 'ready' },
  { el: 'LTD', nominal: 12, min: 9.6, max: 14.4, unit: 's', status: 'ready' },
  { el: 'STPU', nominal: 8000, min: 7200, max: 8800, unit: 'A', status: 'ready' },
  { el: 'STD', nominal: 0.3, min: 0.21, max: 0.39, unit: 's', status: 'ready' },
  { el: 'INST', nominal: 12800, min: 10880, max: 14720, unit: 'A', status: 'ready' },
  { el: 'GFPU', nominal: 0, min: 0, max: 0, unit: '', status: 'disabled' },
  { el: 'GFD', nominal: 0, min: 0, max: 0, unit: '', status: 'disabled' },
  { el: 'MAINT', nominal: 0, min: 0, max: 0, unit: '', status: 'disabled' },
]
const fmtVal = (n: number, unit: Unit) =>
  unit === 'A' ? `${Math.round(n).toLocaleString('en-US')} A` : unit === 's' ? `${n} s` : '—'
const SETTING_BY_EL: Record<string, string> = Object.fromEntries(ELEMENTS.map((e) => [e.code, e.setting]))
const BASE_BY_EL: Record<string, number> = Object.fromEntries(ELEMENTS.filter((e) => e.base).map((e) => [e.code, e.base as number]))

// ── log-log curve geometry (sample, Stage C wires live /plot-tcc) ─────────────
const PLOT = { ml: 58, mt: 18, w: 600, h: 430, x0: 2, x1: 5, y0: -2, y1: 3 }
const px = (a: number) => PLOT.ml + ((Math.log10(a) - PLOT.x0) / (PLOT.x1 - PLOT.x0)) * PLOT.w
const py = (s: number) => PLOT.mt + ((PLOT.y1 - Math.log10(s)) / (PLOT.y1 - PLOT.y0)) * PLOT.h
const NOMINAL: [number, number][] = [
  [2475, 1000], [2700, 360], [3200, 110], [4500, 38], [6000, 16], [7600, 7.5],
  [8000, 5.5], [8200, 0.42], [11000, 0.34], [12000, 0.30], [12800, 0.30], [12800, 0.012], [60000, 0.012],
]
const bandUp = NOMINAL.map(([a, s]) => [a * 1.12, s * 1.55] as [number, number])
const bandLo = NOMINAL.map(([a, s]) => [a * 0.9, s * 0.62] as [number, number])
const toPath = (pts: [number, number][]) => pts.map(([a, s], i) => `${i ? 'L' : 'M'}${px(a).toFixed(1)},${py(s).toFixed(1)}`).join(' ')
const bandPath = `${toPath(bandUp)} L${bandLo.slice().reverse().map(([a, s]) => `${px(a).toFixed(1)},${py(s).toFixed(1)}`).join(' L')} Z`
const MARKERS = [
  { label: 'LTPU 1×', a: 2250, s: 1000, color: '#2f8f5b' },
  { label: 'LTD 3×', a: 6750, s: 12, color: '#d98324' },
  { label: 'STD 1.5×', a: 12000, s: 0.33, color: '#d24b4b' },
  { label: 'INST 1×', a: 12800, s: 0.012, color: '#7c5cc4' },
]
const X_TICKS = [100, 1000, 10000, 100000]
const Y_TICKS = [0.01, 0.1, 1, 10, 100, 1000]

const STEPS = ['Equipment Specifications', 'Protection Settings', 'Time-Current Curve']
const KIND_CLASS: Record<Elt['kind'], string> = {
  PICKUP: 'pill-green', DELAY: 'pill-green', INSTANT: 'pill-blue',
  GROUND: 'pill-blue', 'GF DELAY': 'pill-blue', 'ARC MODE': 'pill-amber',
}

// ──────────────────────────────────────────────────────────────────────────────
export default function LvBreakerTcc() {
  const [step, setStep] = useState(0)
  const [maint, setMaint] = useState(false)
  const [family, setFamily] = useState<Family>('etu')
  const [selection, setSelection] = useState<LiveSelection | null>(null)

  const chip = selection
    ? `${selection.breakerLabel} · ${selection.tripLabel}`
    : `${DEVICE.breakerMfr} ${DEVICE.breakerType} ${DEVICE.breakerStyle} · ${DEVICE.tripDetail}`

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
        {step === 1 && <Settings maint={maint} setMaint={setMaint} selection={selection} />}
        {step === 2 && <Curve selection={selection} />}
      </main>

      <footer className="foot">
        <span>
          LV Breaker TCC · {selection ? 'live selection' : 'select equipment to begin'} — protection &amp; curve data ships in Stage B/C
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
        {options.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
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
const SENSOR_CAP = 250

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

  // Axis A cascade — narrowed by the trip-axis selection (cross-half + bridge_xfilter).
  useEffect(() => {
    let active = true
    setBBusy(true); setErr(null)
    fetchEtuBreakerCascade({
      manufacturerId: bMfr ? Number(bMfr) : null,
      breakerClass: bClass || null,
      breakerId: bId ? Number(bId) : null,
      tripTypeId: tType ? Number(tType) : null,
      tripStyleId: tStyle ? Number(tStyle) : null,
      bridgeOnly: true, // ETU tab: only breakers that actually carry an electronic trip unit
      bridgeXfilter: true,
    })
      .then((r) => { if (active) setBCascade(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBBusy(false) })
    return () => { active = false }
  }, [bMfr, bClass, bId, tType, tStyle])

  // Axis B cascade — narrowed by the breaker-axis selection (cross-half + bridge_xfilter).
  // Its sensors[] is the compatible-sensor intersection (the shared terminal).
  useEffect(() => {
    let active = true
    setTBusy(true); setErr(null)
    fetchCascade({
      manufacturerId: tMfr ? Number(tMfr) : null,
      tripTypeId: tType ? Number(tType) : null,
      tripStyleId: tStyle ? Number(tStyle) : null,
      breakerClass: bClass || null,
      breakerId: bId ? Number(bId) : null,
      breakerStyleId: bStyle ? Number(bStyle) : null,
      bridgeXfilter: true,
    })
      .then((r) => { if (active) setTCascade(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setTBusy(false) })
    return () => { active = false }
  }, [tMfr, tType, tStyle, bClass, bId, bStyle])

  // Breaker-axis terminal -> sensors directly via the SST bridge, so the breaker lane
  // surfaces sensors without requiring a trip-style tap. Skip when a trip-style leaf is
  // set (then /cascade is the more specific breaker∩trip intersection).
  const [bridge, setBridge] = useState<EtuBridgeSensorsResponse | null>(null)
  const [bridgeBusy, setBridgeBusy] = useState(false)
  useEffect(() => {
    if (!bStyle || tStyle) { setBridge(null); return }
    let active = true
    setBridgeBusy(true)
    fetchEtuBridgeSensors({ breakerStyleId: Number(bStyle), breakerClass: bClass || null })
      .then((r) => { if (active) setBridge(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBridgeBusy(false) })
    return () => { active = false }
  }, [bStyle, tStyle, bClass])

  // Normalized compatible-sensor pool, from whichever terminal fired (trip-style wins as
  // the breaker∩trip intersection; else the breaker frame's bridge sensors).
  type PoolItem = { sensor_id: number; rating: number | null; desc: string; tripMfr: string; tripType: string; tripStyle: string; label: string }
  const pool = useMemo<PoolItem[]>(() => {
    const src: PoolItem[] = tStyle && tCascade
      ? tCascade.sensors.map((s) => ({
          sensor_id: s.sensor_id, rating: s.sensor_rating, desc: s.sensor_desc ?? '',
          tripMfr: s.manufacturer_name ?? '', tripType: s.trip_type_name ?? '', tripStyle: s.trip_style_name ?? '',
          label: `${s.manufacturer_name ?? ''} ${s.trip_type_name ?? ''} ${s.trip_style_name ?? ''} — ${s.sensor_desc ?? ''}${s.sensor_rating ? ` (${s.sensor_rating}A)` : ''}`.trim(),
        }))
      : bStyle && bridge
        ? bridge.sensors.map((s) => ({
            sensor_id: s.sensor_id, rating: s.sensor_rating, desc: s.sensor_description ?? '',
            tripMfr: s.tmt_sst_mfr ?? '', tripType: s.tmt_sst_type ?? '', tripStyle: s.tmt_sst_style ?? '',
            label: `${s.tmt_sst_mfr ?? ''} ${s.tmt_sst_type ?? ''} ${s.tmt_sst_style ?? ''} — ${s.sensor_description ?? ''}${s.sensor_rating ? ` (${s.sensor_rating}A)` : ''}`.trim(),
          }))
        : []
    return src.slice(0, SENSOR_CAP)
  }, [tStyle, tCascade, bStyle, bridge])

  const resolveSensor = useCallback(async (sid: string) => {
    setSensorId(sid)
    const row = pool.find((p) => String(p.sensor_id) === sid)
    if (!sid || !row) { onClear(); return }
    const bMfrName = bCascade?.manufacturers.find((m) => String(m.manufacturer_id) === bMfr)?.manufacturer_name ?? ''
    const bName = bCascade?.breakers.find((b) => String(b.breaker_id) === bId)?.breaker_name ?? ''
    const frame = bCascade?.breaker_styles.find((s) => String(s.breaker_style_id) === bStyle)?.breaker_style_name ?? ''
    const breakerLabel = [bMfrName, bClass, bName, frame].filter(Boolean).join(' ') || 'Compatible breaker (any)'
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
      tripLabel: [row.tripMfr, row.tripType, row.tripStyle].filter(Boolean).join(' '),
      ratingLabel: `${row.desc || '—'}${row.rating ? ` · Ir ${row.rating} A` : ''}`,
      bridgeStatus: 'matched',
      plugs,
      trustNote: 'ETU per-sensor NETA pickup tolerances are field-sheet authoritative (G4).',
    })
  }, [pool, bCascade, bMfr, bId, bStyle, bClass, onSelect, onClear])

  // Axis A options
  const bMfrOpts = (bCascade?.manufacturers ?? []).map((m) => ({ value: String(m.manufacturer_id), label: `${m.manufacturer_name} (${m.breaker_count})` }))
  const bClassOpts = (bCascade?.breaker_classes ?? []).map((c) => ({ value: c.breaker_class, label: `${c.breaker_class} (${c.breaker_count})` }))
  const bBreakerOpts = (bCascade?.breakers ?? []).map((b) => ({ value: String(b.breaker_id), label: `${b.breaker_name} · ${b.breaker_class}` }))
  const bStyleOpts = (bCascade?.breaker_styles ?? []).map((s) => ({ value: String(s.breaker_style_id), label: s.breaker_style_name }))
  // Axis B options
  const tMfrOpts = (tCascade?.manufacturers ?? []).map((m) => ({ value: String(m.manufacturer_id), label: `${m.manufacturer_name} (${m.trip_type_count})` }))
  const tTypeOpts = (tCascade?.trip_types ?? []).map((t) => ({ value: String(t.trip_type_id), label: t.trip_type_name }))
  const tStyleOpts = (tCascade?.trip_styles ?? []).map((t) => ({ value: String(t.trip_style_id), label: `${t.trip_style_name} (${t.sensor_count})` }))

  // shared sensor terminal
  const poolCount = tCascade?.count ?? 0 // distinct sensors compatible with the current selection (both halves)
  const sensorReady = pool.length > 0
  const sensorOpts = pool.map((p) => ({ value: String(p.sensor_id), label: p.label }))
  const anySel = !!(bMfr || bClass || bId || bStyle || tMfr || tType || tStyle)
  const sensorPlaceholder = sensorReady
    ? 'Select sensor…'
    : !anySel
      ? 'Narrow either axis to begin…'
      : poolCount === 0
        ? 'No compatible sensors'
        : 'Pick a frame or trip style to list sensors'

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
        {anySel && (
          <div className={`xf-status ${poolCount === 0 ? 'empty' : sensorReady ? 'ok' : ''}`}>
            {poolCount === 0
              ? '✗ No sensors are bridge-compatible with this combination — relax one axis.'
              : <>↔ <span className="xf-count">{poolCount.toLocaleString('en-US')}</span> compatible sensor{poolCount === 1 ? '' : 's'} — both axes narrow each other.</>}
          </div>
        )}
      </div>
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// TMT: breaker class (+ optional manufacturer text) → frame.
function TmtSelector({ onSelect, onClear }: { onSelect: (s: LiveSelection) => void; onClear: () => void }) {
  const [bClass, setBClass] = useState('')
  const [mfr, setMfr] = useState('')
  const [frames, setFrames] = useState<TMTFrameSearchResult[]>([])
  const [frameId, setFrameId] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!bClass) { setFrames([]); return }
    let active = true
    setBusy(true)
    setErr(null)
    fetchTmtFrames({ breakerClass: bClass, manufacturerName: mfr.trim() || undefined })
      .then((r) => { if (active) setFrames(r.frames) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [bClass, mfr])

  const pickFrame = (fid: string) => {
    setFrameId(fid)
    if (!fid) { onClear(); return }
    const f = frames.find((x) => String(x.frame_id) === fid)
    if (!f) { onClear(); return }
    onSelect({
      family: 'tmt',
      frameId: f.frame_id,
      breakerLabel: [f.manufacturer_name, f.breaker_class, f.breaker_name, f.breaker_style_name].filter(Boolean).join(' '),
      tripLabel: 'Thermal-Magnetic (breaker-integral)',
      ratingLabel: f.frame_size ?? '—',
      plugs: [],
      trustNote: 'TMT trip is breaker-integral; settings/tolerances ship in Stage B.',
    })
  }

  const classOpts = ['ICCB', 'MCCB', 'PCB'].map((c) => ({ value: c, label: c }))
  const frameOpts = frames.map((f) => ({
    value: String(f.frame_id),
    label: `${f.manufacturer_name ?? ''} ${f.breaker_name ?? ''} ${f.breaker_style_name ?? ''} — ${f.frame_size ?? ''}`.trim(),
  }))

  return (
    <div className="selwrap">
      <div className="selrow">
        <Picker label="Breaker Class" value={bClass} options={classOpts} placeholder="Select class…"
          onChange={(v) => { setBClass(v); setFrameId(''); onClear() }} />
        <label className="pick">
          <span className="pick-l">Manufacturer filter{busy ? <span className="spin" /> : null}</span>
          <input className="pick-s" value={mfr} placeholder="optional, e.g. Square D"
            onChange={(e) => { setMfr(e.target.value); setFrameId(''); onClear() }} />
        </label>
        <Picker label="Frame" value={frameId} options={frameOpts} placeholder={bClass ? 'Select frame…' : 'Choose a class first'}
          disabled={!frameOpts.length} onChange={pickFrame} />
      </div>
      {bClass && !busy && !frameOpts.length && <div className="sel-status">No frames matched — broaden the filter.</div>}
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// EMT: free-text frame search → frame → section.
function EmtSelector({ onSelect, onClear }: { onSelect: (s: LiveSelection) => void; onClear: () => void }) {
  const [q, setQ] = useState('')
  const [frames, setFrames] = useState<EMTFrameSearchResult[]>([])
  const [frameId, setFrameId] = useState('')
  const [ctx, setCtx] = useState<EMTFrameContext | null>(null)
  const [sectionId, setSectionId] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (q.trim().length < 2) { setFrames([]); return }
    if (debounce.current) clearTimeout(debounce.current)
    let active = true
    debounce.current = setTimeout(() => {
      setBusy(true)
      setErr(null)
      fetchEmtFrames(q.trim())
        .then((r) => { if (active) setFrames(r.frames) })
        .catch((e) => { if (active) setErr(errMsg(e)) })
        .finally(() => { if (active) setBusy(false) })
    }, 280)
    return () => { active = false; if (debounce.current) clearTimeout(debounce.current) }
  }, [q])

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
      sectionId: ctx.sections.find((s) => String(s.section_id) === sid)?.section_id,
      breakerLabel: [ctx.manufacturer_name, ctx.type_name, ctx.style_name].filter(Boolean).join(' '),
      tripLabel: `Electro-Mechanical${ctx.tcc_number ? ` · TCC ${ctx.tcc_number}` : ''}`,
      ratingLabel: `${ctx.frame_desc ?? ctx.frame_size ?? '—'}${sec?.name ? ` · ${sec.name}` : ''}`,
      plugs: [],
      trustNote: 'EMT has no stored breaker default (G0); runtime-selected catalog path.',
    })
  }

  const frameOpts = frames.map((f) => ({
    value: String(f.frame_id),
    label: `${f.manufacturer_name ?? ''} ${f.type_name ?? ''} ${f.style_name ?? ''} — ${f.frame_desc ?? f.frame_size ?? ''}`.trim(),
  }))
  const sectionOpts = (ctx?.sections ?? []).map((s) => ({ value: String(s.section_id), label: s.name ?? `Section ${s.section_id}` }))

  return (
    <div className="selwrap">
      <div className="selrow">
        <label className="pick wide">
          <span className="pick-l">Search EMT frames{busy ? <span className="spin" /> : null}</span>
          <input className="pick-s" value={q} placeholder="type ≥2 chars, e.g. AKR, Mag-Break…"
            onChange={(e) => { setQ(e.target.value); setFrameId(''); setSectionId(''); onClear() }} />
        </label>
        <Picker label="Frame" value={frameId} options={frameOpts} placeholder={frames.length ? 'Select frame…' : 'Search first'}
          disabled={!frameOpts.length} onChange={pickFrame} />
        <Picker label="Section" value={sectionId} options={sectionOpts} placeholder={ctx ? 'Select section…' : 'Choose a frame first'}
          disabled={!sectionOpts.length} onChange={pickSection} />
      </div>
      {err && <div className="sel-status err">⚠ {err}</div>}
    </div>
  )
}

// ── Screen 2: Protection Settings (sample until Stage B) ──────────────────────
function Settings({ maint, setMaint, selection }: { maint: boolean; setMaint: (v: boolean) => void; selection: LiveSelection | null }) {
  if (selection?.family === 'etu' && selection.sensorId != null) {
    return <EtuSettings maint={maint} setMaint={setMaint} selection={selection} />
  }
  if (selection?.family === 'tmt' && selection.frameId != null) {
    return <TmtSettings selection={selection} />
  }
  if (selection?.family === 'emt' && selection.sectionId != null) {
    return <EmtSettings selection={selection} />
  }
  return <SampleSettings maint={maint} setMaint={setMaint} selection={selection} />
}

// ── Screen 2 ETU (LIVE): editable settings -> /calculate -> DB-authoritative bands ──
type PickKey = 'ltpu' | 'stpu' | 'inst' | 'gfpu'
type BandKey = 'ltd' | 'std' | 'gfd'
type EtuChosen = { plug: number; ltpu?: number; stpu?: number; inst?: number; gfpu?: number; ltd?: number; std?: number; gfd?: number }
const EL_META: { code: string; label: string; kind: Elt['kind']; pick?: PickKey; band?: BandKey }[] = [
  { code: 'LTPU', label: 'Long-Time Pickup', kind: 'PICKUP', pick: 'ltpu' },
  { code: 'LTD', label: 'Long-Time Delay', kind: 'DELAY', band: 'ltd' },
  { code: 'STPU', label: 'Short-Time Pickup', kind: 'PICKUP', pick: 'stpu' },
  { code: 'STD', label: 'Short-Time Delay', kind: 'DELAY', band: 'std' },
  { code: 'INST', label: 'Instantaneous', kind: 'INSTANT', pick: 'inst' },
  { code: 'GFPU', label: 'Ground-Fault Pickup', kind: 'GROUND', pick: 'gfpu' },
  { code: 'GFD', label: 'Ground-Fault Delay', kind: 'GF DELAY', band: 'gfd' },
]
const fmtAmp = (n: number | null | undefined) => (n == null ? '—' : `${Math.round(n).toLocaleString('en-US')} A`)

function EtuSettings({ maint, setMaint, selection }: { maint: boolean; setMaint: (v: boolean) => void; selection: LiveSelection }) {
  const sensorId = selection.sensorId as number
  const [settings, setSettings] = useState<AvailableSettingsResponse | null>(null)
  const [chosen, setChosen] = useState<EtuChosen | null>(null)
  const [calc, setCalc] = useState<EtuCalculateResponse | null>(null)
  const [measured, setMeasured] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [calcBusy, setCalcBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true); setErr(null); setCalc(null); setChosen(null); setMeasured({})
    Promise.all([fetchEtuSettings(sensorId), fetchEtuContext(sensorId)])
      .then(([s]: [AvailableSettingsResponse, SensorCalcContext]) => {
        if (!active) return
        setSettings(s)
        const mid = (arr: number[]): number | undefined => (arr.length ? arr[Math.floor(arr.length / 2)] : undefined)
        const bandDefault = (bs: DelayBandOption[]): number | undefined => {
          const b = bs.find((x) => x.is_default) ?? bs[0]
          return b ? Number(b.band) : undefined
        }
        setChosen({
          plug: s.plug_values[0] ?? 0,
          ltpu: mid(s.ltpu_settings), stpu: mid(s.stpu_settings), inst: mid(s.inst_settings), gfpu: mid(s.gfpu_settings),
          ltd: bandDefault(s.ltd_settings), std: bandDefault(s.std_settings), gfd: bandDefault(s.gfd_settings),
        })
      })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [sensorId])

  useEffect(() => {
    if (!chosen || !chosen.plug) return
    let active = true
    setCalcBusy(true)
    fetchEtuCalculate({
      sensor_id: sensorId, plug_rating: chosen.plug,
      ltpu_setting: chosen.ltpu, stpu_setting: chosen.stpu, inst_setting: chosen.inst, gfpu_setting: chosen.gfpu,
      ltd_setting: chosen.ltd, std_setting: chosen.std, gfd_setting: chosen.gfd, maint_mode: maint,
    })
      .then((r) => { if (active) setCalc(r) })
      .catch((e) => { if (active) setErr(errMsg(e)) })
      .finally(() => { if (active) setCalcBusy(false) })
    return () => { active = false }
  }, [chosen, maint, sensorId])

  if (loading || !settings || !chosen) {
    return <div className="loadbox">{err ? <span className="sel-status err">⚠ {err}</span> : <><span className="spin" /> Loading sensor settings…</>}</div>
  }

  const listFor = (pk: PickKey): number[] =>
    pk === 'ltpu' ? settings.ltpu_settings : pk === 'stpu' ? settings.stpu_settings : pk === 'inst' ? settings.inst_settings : settings.gfpu_settings
  const bandsFor = (bk: BandKey): DelayBandOption[] =>
    bk === 'ltd' ? settings.ltd_settings : bk === 'std' ? settings.std_settings : settings.gfd_settings
  const elByCode = (code: string) => calc?.elements.find((e) => e.element.toUpperCase() === code)

  // NETA ATS test points (NETA_TEST_PLAN_SPEC §2/§11): pickups ramp @ 1×; each delay injects a FIXED
  // multiple of its own pickup — LTD @ 3× LTPU, STD @ 1.5× STPU, GFD @ 1.5× GFPU.
  // The /calculate engine currently echoes the selected delay BAND as `multiplier` (the band↔multiplier
  // conflation, G4), so its delay `multiplier`/`test_current` are wrong. Override the DISPLAY with the NETA
  // multiple and inject-current (= multiple × the element's pickup current). The expected trip TIME stays
  // engine-sourced under the "verify" badge (recompute-at-multiple is the gated Stage C curve work).
  const NETA_DELAY_MULT: Record<string, number> = { LTD: 3, STD: 1.5, GFD: 1.5 }
  const DELAY_PICKUP: Record<string, string> = { LTD: 'LTPU', STD: 'STPU', GFD: 'GFPU' }
  const displayTestMult = (e: EtuTestCurrentElement): number =>
    e.kind === 'delay' ? (NETA_DELAY_MULT[e.element.toUpperCase()] ?? e.multiplier) : (e.multiplier ?? 1)
  const displayTestCurrent = (e: EtuTestCurrentElement): number | null => {
    if (e.kind === 'delay') {
      const mult = NETA_DELAY_MULT[e.element.toUpperCase()]
      const pickup = elByCode(DELAY_PICKUP[e.element.toUpperCase()])?.test_current
      if (mult != null && pickup != null) return mult * pickup
    }
    return e.test_current
  }

  return (
    <>
      <div className="eq-strip">
        <div><span>Breaker</span>{selection.breakerLabel}</div>
        <div><span>Trip Unit</span>{selection.tripLabel}</div>
        <div><span>Sensor</span>{calc?.sensor_desc ?? selection.ratingLabel}</div>
        <div className="plugpick">
          <span>Plug (Ir)</span>
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
          return (
            <div key={m.code} className={`el-card ${present ? '' : 'off'}`}>
              <div className="el-h">
                <div className="el-code"><b>{m.code}</b><span>{m.label}</span></div>
                <span className={`pill ${KIND_CLASS[m.kind]}`}>{m.kind}</span>
              </div>
              <div className="el-b">
                <div className="el-row">
                  <span>Setting</span>
                  {!present ? (
                    <div className="el-mult muted">Not available</div>
                  ) : m.pick ? (
                    <select className="el-select" value={String(chosen[m.pick] ?? '')} onChange={(e) => setChosen((c) => (c ? { ...c, [m.pick!]: e.target.value ? Number(e.target.value) : undefined } : c))}>
                      {listFor(m.pick).map((v) => (<option key={v} value={v}>{v} × Ir</option>))}
                    </select>
                  ) : (
                    <select className="el-select" value={String(chosen[m.band!] ?? '')} onChange={(e) => setChosen((c) => (c ? { ...c, [m.band!]: e.target.value ? Number(e.target.value) : undefined } : c))}>
                      {bandsFor(m.band!).map((b) => (<option key={b.band} value={Number(b.band)}>{b.label}</option>))}
                    </select>
                  )}
                </div>
                <div className="el-row"><span>Test Current</span><div className="el-cur">{present && el ? fmtAmp(displayTestCurrent(el)) : '—'}</div></div>
              </div>
            </div>
          )
        })}
      </div>

      <section className="card">
        <div className="card-h">📊 NETA Tolerance Bands &amp; Field Results {calcBusy ? <span className="spin" /> : <span className="badge inline live">LIVE</span>}</div>
        <div className="bands-wrap">
          <table className="bands">
            <thead><tr><th>Element</th><th>Trust</th><th>Test @</th><th>Test Current</th><th>Min Limit</th><th>Max Limit</th><th>Measured</th><th>% Error</th><th>Status</th></tr></thead>
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
                    <td>{delay ? <span className="trust verify" title="Delay-band route fidelity pending (G4)">verify</span> : <span className="trust ok" title="DB-authoritative per-sensor tolerance">DB</span>}</td>
                    <td>{fmtMult(displayTestMult(e))}</td>
                    <td className="num">{fmtAmp(displayTestCurrent(e))}</td>
                    <td className="num">{lo == null ? '—' : delay ? `${lo} s` : fmtAmp(lo)}</td>
                    <td className="num">{hi == null ? '—' : delay ? `${hi} s` : fmtAmp(hi)}</td>
                    <td><div className="meas"><input className="meas-in" inputMode="decimal" value={raw} placeholder="—" onChange={(ev) => setMeasured((m) => ({ ...m, [e.element]: ev.target.value }))} /><span className="meas-u">{unit}</span></div></td>
                    <td className="num">{pct !== null ? <span className={`pct ${inBand ? 'ok' : 'bad'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(1)}%</span> : <span className="muted2">—</span>}</td>
                    <td>{!hasM ? <span className="status ready">● Ready</span> : inBand ? <span className="status pass">✓ PASS</span> : <span className="status fail">✗ FAIL</span>}</td>
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
        <b>NETA test points.</b> Pickups (LTPU/STPU/INST/GFPU) are ramp-tested <b>@ 1×</b> against <b>DB-authoritative per-sensor tolerances</b> (field-sheet safe). Delays inject a fixed multiple of their pickup — <b>LTD @ 3× LTPU, STD @ 1.5× STPU, GFD @ 1.5× GFPU</b> (NETA ATS) — so the <b>Test @ and inject current are correct</b>. The expected trip <b>time</b> is still <b>verify</b>-flagged: the delay-band → curve recompute at the test point lands with Stage C. {selection.trustNote}
      </div>
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

function SampleSettings({ maint, setMaint, selection }: { maint: boolean; setMaint: (v: boolean) => void; selection: LiveSelection | null }) {
  const [mult, setMult] = useState<Record<DelayKey, number>>(DELAY_DEFAULT)
  const [measured, setMeasured] = useState<Record<string, string>>({})
  const bandTestAt = (el: string) => {
    if (el === 'LTD') return `${fmtMult(mult.ltd)} (${fmtA(mult.ltd * BASE_BY_EL.LTPU)})`
    if (el === 'STD') return `${fmtMult(mult.std)} (${fmtA(mult.std * BASE_BY_EL.STPU)})`
    if (el === 'LTPU') return `1× (${fmtA(BASE_BY_EL.LTPU)})`
    if (el === 'STPU') return `1× (${fmtA(BASE_BY_EL.STPU)})`
    if (el === 'INST') return `1× (${fmtA(BASE_BY_EL.INST)})`
    return '—'
  }
  return (
    <>
      <div className="eq-strip">
        {selection ? (
          <>
            <div><span>Breaker</span>{selection.breakerLabel}</div>
            <div><span>Trip Unit</span>{selection.tripLabel}</div>
            <div><span>Rating</span>{selection.ratingLabel}</div>
            <div><span className="badge">SAMPLE</span>settings &amp; tolerances below are placeholder (Stage B)</div>
          </>
        ) : (
          <>
            <div><span>Breaker</span>{DEVICE.breakerMfr} {DEVICE.breakerType} {DEVICE.breakerStyle} {DEVICE.frameSize}</div>
            <div><span>Trip Unit</span>{DEVICE.tripMfr} {DEVICE.tripDetail}</div>
            <div><span>Sensor</span>{DEVICE.sensorIr}</div>
            <div><span className="badge">SAMPLE</span>no live selection</div>
          </>
        )}
      </div>

      <div className={`maint-banner ${maint ? 'on' : ''}`}>
        <div>
          <b>Maintenance Mode (ARMS)</b>
          <span>{maint ? 'Reduced instantaneous trip applied — markers reflect maint-mode calculations.' : 'Nominal mode. Toggle to model the reduced arc-flash trip setting.'}</span>
        </div>
        <button className={`toggle ${maint ? 'on' : ''}`} onClick={() => setMaint(!maint)} aria-label="toggle maintenance mode"><span /></button>
      </div>

      <div className="grid2 elgrid">
        {ELEMENTS.map((e) => {
          const isDelay = !!e.delay && !e.disabled
          const testCurrent = e.disabled ? '—' : e.delay ? fmtA(mult[e.delay] * (e.base ?? 0)) : fmtA(e.base ?? 0)
          return (
            <div key={e.code} className={`el-card ${e.disabled ? 'off' : ''}`}>
              <div className="el-h">
                <div className="el-code"><b>{e.code}</b><span>{e.label}</span></div>
                <span className={`pill ${KIND_CLASS[e.kind]}`}>{e.kind}</span>
              </div>
              <div className="el-b">
                <div className="el-row"><span>Setting</span><div className="el-input">{e.setting}</div></div>
                <div className="el-row two">
                  <div>
                    <span>Test @</span>
                    {e.disabled ? (
                      <div className="el-mult muted">—</div>
                    ) : isDelay ? (
                      <select className="el-select" value={mult[e.delay!]} onChange={(ev) => setMult((m) => ({ ...m, [e.delay!]: Number(ev.target.value) }))}>
                        {MULT_OPTS.map((m) => (<option key={m} value={m}>{fmtMult(m)}</option>))}
                      </select>
                    ) : (
                      <div className="el-mult">1×</div>
                    )}
                  </div>
                  <div><span>Test Current</span><div className="el-cur">{testCurrent}</div></div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <section className="card">
        <div className="card-h">📊 NETA Tolerance Bands &amp; Field Results <span className="badge inline">SAMPLE — live in Stage B</span></div>
        <div className="bands-wrap">
          <table className="bands">
            <thead><tr><th>Element</th><th>Setting</th><th>Test @</th><th>Min Limit</th><th>Max Limit</th><th>Measured</th><th>% Error</th><th>Status</th></tr></thead>
            <tbody>
              {BANDS.map((b) => {
                const disabled = b.status === 'disabled'
                const raw = measured[b.el] ?? ''
                const mv = parseFloat(raw)
                const hasM = raw.trim() !== '' && !Number.isNaN(mv)
                const pct = hasM && b.nominal ? ((mv - b.nominal) / b.nominal) * 100 : null
                const inBand = hasM ? mv >= b.min && mv <= b.max : null
                return (
                  <tr key={b.el} className={disabled ? 'row-off' : ''}>
                    <td><b>{b.el}</b></td>
                    <td>{SETTING_BY_EL[b.el] ?? '—'}</td>
                    <td>{disabled ? '—' : bandTestAt(b.el)}</td>
                    <td className="num">{disabled ? '—' : fmtVal(b.min, b.unit)}</td>
                    <td className="num">{disabled ? '—' : fmtVal(b.max, b.unit)}</td>
                    <td>{disabled ? <span className="muted2">—</span> : (
                      <div className="meas">
                        <input className="meas-in" inputMode="decimal" value={raw} placeholder="—"
                          onChange={(ev) => setMeasured((m) => ({ ...m, [b.el]: ev.target.value }))} />
                        <span className="meas-u">{b.unit}</span>
                      </div>
                    )}</td>
                    <td className="num">{!disabled && pct !== null
                      ? <span className={`pct ${inBand ? 'ok' : 'bad'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(1)}%</span>
                      : <span className="muted2">—</span>}</td>
                    <td>{disabled
                      ? <span className="status off">Disabled</span>
                      : !hasM ? <span className="status ready">● Ready</span>
                        : inBand ? <span className="status pass">✓ PASS</span>
                          : <span className="status fail">✗ FAIL</span>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <div className="method">
        <b>Test methodology.</b> Pickup elements (LTPU, STPU, INST, GFPU) use ramping tests verified at <b>1×</b> pickup.
        Delay elements use fixed-current injection: <b>LTD defaults to 3×</b> (selectable to 6× in 0.5× steps); <b>STD &amp; GFD to 1.5×</b>.
        {selection ? ` ${selection.trustNote}` : ' Select live equipment on Screen 1 to drive these from DB-authoritative per-sensor values.'}
      </div>
    </>
  )
}

// ── Screen 3: Curve (sample until Stage C) ────────────────────────────────────
function Curve({ selection }: { selection: LiveSelection | null }) {
  const legend = [
    { c: '#14507d', t: 'Nominal Curve' },
    { c: '#2f8f5b', t: 'LTPU @ 1×' },
    { c: '#d98324', t: 'LTD @ 3×' },
    { c: '#d24b4b', t: 'STD @ 1.5×' },
    { c: '#7c5cc4', t: 'INST @ 1×' },
  ]
  const stats = [
    { k: 'Test Points', v: '5 Active' },
    { k: 'Max Current', v: '12,800 A' },
    { k: 'Min Time', v: '0.01 s' },
    { k: 'Curve Type', v: 'I²t' },
  ]
  return (
    <>
      <div className="curve-grid">
        <aside className="card side">
          <div className="card-h">Device Info <span className="badge inline">SAMPLE</span></div>
          <div className="card-b">
            {selection ? (
              <>
                <Field label="Breaker" value={selection.breakerLabel} />
                <Field label="Trip Unit" value={selection.tripLabel} />
                <Field label="Rating" value={selection.ratingLabel} />
              </>
            ) : (
              <>
                <Field label="Breaker" value={`${DEVICE.breakerMfr} ${DEVICE.breakerType} ${DEVICE.breakerStyle}`} />
                <Field label="Frame" value={DEVICE.frameSize} />
                <Field label="Trip Unit" value={DEVICE.tripDetail} />
                <Field label="Sensor Rating" value={`Ir ${DEVICE.sensorIr} · plug ${DEVICE.plug}`} />
              </>
            )}
          </div>
          <div className="card-h" style={{ marginTop: 8 }}>Curve Elements</div>
          <div className="legend">
            {legend.map((l) => (<div key={l.t} className="leg"><span className="sw" style={{ background: l.c }} />{l.t}</div>))}
          </div>
        </aside>

        <section className="card plot-card">
          <div className="card-h">Trip Characteristic Curve <span className="badge inline">SAMPLE — live /plot-tcc in Stage C</span></div>
          <div className="plot-wrap">
            <svg viewBox="0 0 700 480" className="plot" role="img" aria-label="Time-current curve">
              {X_TICKS.map((t) => (
                <g key={`x${t}`}>
                  <line x1={px(t)} y1={PLOT.mt} x2={px(t)} y2={PLOT.mt + PLOT.h} className="grid" />
                  <text x={px(t)} y={PLOT.mt + PLOT.h + 16} className="axt" textAnchor="middle">{t >= 1000 ? `${t / 1000}k` : t}</text>
                </g>
              ))}
              {Y_TICKS.map((t) => (
                <g key={`y${t}`}>
                  <line x1={PLOT.ml} y1={py(t)} x2={PLOT.ml + PLOT.w} y2={py(t)} className="grid" />
                  <text x={PLOT.ml - 8} y={py(t) + 3} className="axt" textAnchor="end">{t}</text>
                </g>
              ))}
              <text x={PLOT.ml + PLOT.w / 2} y={PLOT.mt + PLOT.h + 38} className="axl" textAnchor="middle">Current (A)</text>
              <text transform={`translate(16 ${PLOT.mt + PLOT.h / 2}) rotate(-90)`} className="axl" textAnchor="middle">Time (s)</text>
              <path d={bandPath} className="band" />
              <path d={toPath(NOMINAL)} className="nominal" />
              {MARKERS.map((m) => (
                <g key={m.label}>
                  <rect x={px(m.a) - 5} y={py(m.s) - 5} width={10} height={10} transform={`rotate(45 ${px(m.a)} ${py(m.s)})`} fill={m.color} stroke="#fff" strokeWidth={1.5} />
                </g>
              ))}
            </svg>
          </div>
        </section>
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
`
