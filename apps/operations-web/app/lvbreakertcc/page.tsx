'use client'

/**
 * TCC Calculator — UI layout/formatting MOCKUP (clean-slate; placeholder shell is NOT a constraint).
 * Self-contained: frozen sample device (Square D P-Frame PX 2500A / Micrologic 6.0H MCCB),
 * own styling (not the operations-web globals), inline-SVG log-log curve (no chart dep).
 * Purpose: react to LAYOUT/FORMATTING. Numbers are representative placeholders; real values come
 * from the validated backend (DB per-sensor tolerances + /plot-tcc) at port time.
 * Mirrors the Excel concept's 3-screen flow: Specifications -> Protection Settings -> TCC Curve.
 */

import { useState } from 'react'

// ── frozen sample (from the operator's TCC_Calculator_v5.xlsx) ──────────────
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
  base?: number          // pickup current (A) the Test @ multiple is applied to
  delay?: DelayKey       // delay element -> Test @ is a selectable multiplier
  disabled?: boolean
}

// NETA defaults: every pickup tests @ 1× (ramp to pickup); LTD @ 3×; STD/GFD @ 1.5×.
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

// Delay Test @ choices: 0.5× increments, 1×–6× (LTD spec'd to 6×; STD/GFD share the range).
const MULT_OPTS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]
const DELAY_DEFAULT: Record<DelayKey, number> = { ltd: 3, std: 1.5, gfd: 1.5 }
const fmtA = (n: number) => `${Math.round(n).toLocaleString('en-US')} A`
const fmtMult = (m: number) => `${Number.isInteger(m) ? m : m.toFixed(1)}×`

type Band = { el: string; min: string; max: string; unit: string; status: 'ready' | 'disabled' }
const BANDS: Band[] = [
  { el: 'LTPU', min: '2,025', max: '2,475', unit: 'A', status: 'ready' },
  { el: 'LTD', min: '9.6', max: '14.4', unit: 's', status: 'ready' },
  { el: 'STPU', min: '7,200', max: '8,800', unit: 'A', status: 'ready' },
  { el: 'STD', min: '0.21', max: '0.39', unit: 's', status: 'ready' },
  { el: 'INST', min: '10,880', max: '14,720', unit: 'A', status: 'ready' },
  { el: 'GFPU', min: '—', max: '—', unit: '', status: 'disabled' },
  { el: 'GFD', min: '—', max: '—', unit: '', status: 'disabled' },
  { el: 'MAINT', min: '—', max: '—', unit: '', status: 'disabled' },
]
const SETTING_BY_EL: Record<string, string> = Object.fromEntries(ELEMENTS.map((e) => [e.code, e.setting]))
const BASE_BY_EL: Record<string, number> = Object.fromEntries(ELEMENTS.filter((e) => e.base).map((e) => [e.code, e.base as number]))

// ── log-log curve geometry ──────────────────────────────────────────────────
const PLOT = { ml: 58, mt: 18, w: 600, h: 430, x0: 2, x1: 5, y0: -2, y1: 3 } // current 100..100k A · time .01..1000 s
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

export default function TccMockup() {
  const [step, setStep] = useState(0)
  const [maint, setMaint] = useState(false)

  return (
    <div className="tccx">
      <style>{CSS}</style>

      {/* App bar */}
      <header className="bar">
        <div className="brand">
          <span className="mark">⚡</span>
          <div>
            <div className="title">TCC Calculator</div>
            <div className="sub">NETA breaker / trip-unit test configuration</div>
          </div>
        </div>
        <div className="device-chip">
          <span className="dot" /> {DEVICE.breakerMfr} {DEVICE.breakerType} {DEVICE.breakerStyle} · {DEVICE.tripDetail}
        </div>
      </header>

      {/* Stepper */}
      <nav className="steps">
        {STEPS.map((s, i) => (
          <button key={s} className={`step ${i === step ? 'on' : ''} ${i < step ? 'done' : ''}`} onClick={() => setStep(i)}>
            <span className="num">{i < step ? '✓' : i + 1}</span>{s}
          </button>
        ))}
      </nav>

      <main className="wrap">
        {step === 0 && <Specifications />}
        {step === 1 && <Settings maint={maint} setMaint={setMaint} />}
        {step === 2 && <Curve />}
      </main>

      <footer className="foot">
        <span>LV Breaker TCC · sample configuration — values are representative (live selection &amp; calc to follow)</span>
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

function Specifications() {
  return (
    <>
      <div className="grid2">
        <section className="card">
          <div className="card-h"><span className="idx">1</span> Breaker Selection</div>
          <div className="card-b">
            <Field label="Breaker Class" value={DEVICE.breakerClass} />
            <Field label="Manufacturer" value={DEVICE.breakerMfr} />
            <Field label="Breaker Type" value={DEVICE.breakerType} />
            <Field label="Breaker Style" value={DEVICE.breakerStyle} />
            <Field label="Frame Size" value={DEVICE.frameSize} />
          </div>
        </section>
        <section className="card">
          <div className="card-h"><span className="idx">2</span> Trip Unit Selection</div>
          <div className="card-b">
            <Field label="Trip Type" value={DEVICE.tripType} />
            <Field label="Trip Manufacturer" value={DEVICE.tripMfr} />
            <Field label="Trip Type Detail" value={DEVICE.tripDetail} />
            <Field label="Trip Style" value={DEVICE.tripStyle} />
            <Field label="Sensor Rating (Ir)" value={DEVICE.sensorIr} />
          </div>
        </section>
      </div>

      <div className="grid2">
        <section className="card soft">
          <div className="card-h light">🔗 Reference Material Links</div>
          <div className="card-b muted-b">
            <a className="ref">Square D Micrologic 6.0H — instruction bulletin (PDF)</a>
            <a className="ref">P-Frame PX field test procedure</a>
            <a className="ref">NETA ATS Table 100.7 — breaker tolerances</a>
          </div>
        </section>
        <section className="card soft">
          <div className="card-h light">📝 Trip Unit Notes &amp; TCC</div>
          <div className="card-b muted-b">
            <p className="note">Micrologic 6.0H provides LTPU/LTD/STPU/STD/INST + ground-fault. ARMS maintenance mode available. Confirm plug rating matches the installed sensor before testing.</p>
          </div>
        </section>
      </div>

      <section className="summary">
        <div className="summary-h">✓ Equipment Configuration — matched &amp; ready</div>
        <div className="summary-grid">
          <div><span>Breaker</span>{DEVICE.breakerMfr} {DEVICE.breakerType} {DEVICE.breakerStyle} {DEVICE.frameSize}</div>
          <div><span>Trip Unit</span>{DEVICE.tripMfr} {DEVICE.tripDetail} {DEVICE.tripStyle}</div>
          <div><span>Sensor</span>{DEVICE.sensorIr} (plug {DEVICE.plug})</div>
          <div><span>Status</span><b className="ok-text">● Configuration valid</b></div>
        </div>
      </section>
    </>
  )
}

function Settings({ maint, setMaint }: { maint: boolean; setMaint: (v: boolean) => void }) {
  const [mult, setMult] = useState<Record<DelayKey, number>>(DELAY_DEFAULT)
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
        <div><span>Breaker</span>{DEVICE.breakerMfr} {DEVICE.breakerType} {DEVICE.breakerStyle} {DEVICE.frameSize}</div>
        <div><span>Trip Unit</span>{DEVICE.tripMfr} {DEVICE.tripDetail}</div>
        <div><span>Sensor</span>{DEVICE.sensorIr}</div>
        <div><span>Plug</span>{DEVICE.plug}</div>
        <div><span>Effective Ir</span>{DEVICE.effectiveIr}</div>
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
          const testCurrent = e.disabled
            ? '—'
            : e.delay
              ? fmtA(mult[e.delay] * (e.base ?? 0))
              : fmtA(e.base ?? 0)
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
                      <select
                        className="el-select"
                        value={mult[e.delay!]}
                        onChange={(ev) => setMult((m) => ({ ...m, [e.delay!]: Number(ev.target.value) }))}
                      >
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
        <div className="card-h">📊 NETA Tolerance Bands</div>
        <table className="bands">
          <thead><tr><th>Element</th><th>Setting</th><th>Test @</th><th>Min Limit</th><th>Max Limit</th><th>Status</th></tr></thead>
          <tbody>
            {BANDS.map((b) => (
              <tr key={b.el} className={b.status === 'disabled' ? 'row-off' : ''}>
                <td><b>{b.el}</b></td>
                <td>{SETTING_BY_EL[b.el] ?? '—'}</td>
                <td>{b.status === 'disabled' ? '—' : bandTestAt(b.el)}</td>
                <td className="num">{b.min}{b.unit && b.min !== '—' ? ` ${b.unit}` : ''}</td>
                <td className="num">{b.max}{b.unit && b.max !== '—' ? ` ${b.unit}` : ''}</td>
                <td>{b.status === 'ready'
                  ? <span className="status ready">● Ready to test</span>
                  : <span className="status off">Disabled</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="method">
        <b>Test methodology.</b> Pickup elements (LTPU, STPU, INST, GFPU) use ramping tests starting ~80% of the calculated value, verified at <b>1×</b> pickup.
        Delay elements use fixed-current injection: <b>LTD defaults to 3×</b> (selectable to 6× in 0.5× steps); <b>STD &amp; GFD to 1.5×</b>. Instantaneous elements trip in ≤ 0.03 s.
        Tolerance bands are authoritative per-sensor values; measured results fill the Status column at evaluate time.
      </div>
    </>
  )
}

function Curve() {
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
          <div className="card-h">Device Info</div>
          <div className="card-b">
            <Field label="Breaker" value={`${DEVICE.breakerMfr} ${DEVICE.breakerType} ${DEVICE.breakerStyle}`} />
            <Field label="Frame" value={DEVICE.frameSize} />
            <Field label="Trip Unit" value={DEVICE.tripDetail} />
            <Field label="Sensor Rating" value={`Ir ${DEVICE.sensorIr} · plug ${DEVICE.plug}`} />
          </div>
          <div className="card-h" style={{ marginTop: 8 }}>Curve Elements</div>
          <div className="legend">
            {legend.map((l) => (<div key={l.t} className="leg"><span className="sw" style={{ background: l.c }} />{l.t}</div>))}
          </div>
        </aside>

        <section className="card plot-card">
          <div className="card-h">Trip Characteristic Curve</div>
          <div className="plot-wrap">
            <svg viewBox="0 0 700 480" className="plot" role="img" aria-label="Time-current curve">
              {/* grid */}
              {X_TICKS.map((t) => (
                <g key={`x${t}`}>
                  <line x1={px(t)} y1={PLOT.mt} x2={px(t)} y2={PLOT.mt + PLOT.h} className="grid" />
                  <text x={px(t)} y={PLOT.mt + PLOT.h + 16} className="axt" textAnchor="middle">{t >= 1000 ? `${t / 1000}k` : t}</text>
                </g>
              ))}
              {Y_TICKS.map((t) => (
                <g key={`y${t}`}>
                  <line x1={PLOT.ml} y1={py(t)} x2={PLOT.ml + PLOT.w} y2={py(t)} className="grid" />
                  <text x={PLOT.ml - 8} y={py(t) + 3} className="axt" textAnchor="end">{t < 1 ? t : t}</text>
                </g>
              ))}
              <text x={PLOT.ml + PLOT.w / 2} y={PLOT.mt + PLOT.h + 38} className="axl" textAnchor="middle">Current (A)</text>
              <text transform={`translate(16 ${PLOT.mt + PLOT.h / 2}) rotate(-90)`} className="axl" textAnchor="middle">Time (s)</text>

              {/* tolerance band + nominal */}
              <path d={bandPath} className="band" />
              <path d={toPath(NOMINAL)} className="nominal" />

              {/* markers */}
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
.device-chip{display:flex;align-items:center;gap:8px;font-size:12.5px;background:rgba(255,255,255,.12);padding:7px 13px;border-radius:999px;}
.device-chip .dot{width:7px;height:7px;border-radius:50%;background:#5fdca0;box-shadow:0 0 0 3px rgba(95,220,160,.25);}
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
.card-b{padding:8px 18px 16px;}
.field{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:9px 0;border-bottom:1px dashed var(--line-2);}
.field:last-child{border-bottom:none;}
.flabel{font-size:12.5px;color:var(--muted);font-weight:600;}
.fvalue{font-size:13.5px;font-weight:600;color:var(--ink);background:var(--line-2);padding:5px 12px;border-radius:7px;min-width:130px;text-align:right;}
.soft .card-b{padding-top:14px;}
.muted-b{display:flex;flex-direction:column;gap:9px;}
.ref{font-size:13px;color:var(--brand-l);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:9px 12px;cursor:pointer;background:#fafdff;}
.ref:hover{border-color:var(--brand-l);}
.note{font-size:13px;color:var(--muted);line-height:1.55;margin:0;}
.summary{background:linear-gradient(100deg,#1f7a4d,#2f8f5b);color:#fff;border-radius:14px;padding:16px 20px;box-shadow:0 10px 24px rgba(47,143,91,.22);}
.summary-h{font-size:14px;font-weight:700;margin-bottom:12px;}
.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 28px;}
@media(max-width:820px){.summary-grid{grid-template-columns:1fr;}}
.summary-grid div{font-size:13.5px;display:flex;gap:10px;align-items:baseline;}
.summary-grid span{font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;opacity:.85;min-width:74px;font-weight:700;}
.ok-text{color:#d6ffe9;}
.eq-strip{display:flex;flex-wrap:wrap;gap:8px 26px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 18px;}
.eq-strip div{font-size:13px;display:flex;gap:8px;align-items:baseline;}
.eq-strip span{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;}
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
.el-mult{font-size:13.5px;font-weight:700;color:var(--brand);background:var(--brand-soft,#e6eef5);padding:8px 12px;border-radius:8px;text-align:center;}
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
.method{font-size:12.5px;color:#3a4a58;line-height:1.6;background:#eaf2fb;border:1px solid #d3e3f5;border-left:3px solid var(--brand-l);border-radius:10px;padding:13px 18px;}
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
