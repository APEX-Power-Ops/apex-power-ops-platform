# SC3 — Field-Facing Terminology Mapping `[RULED + BUILT]`

**Status:** v3 (2026-06-11) — **Q1–Q5 RULED + the build SHIPPED** (apex `1352d5c9`; migration `026`
applied to prod = `tcc.field_terminology`, 67 approved rows). The §5.5-step-1 catalog read CLOSED the
PROPOSED rows pre-seed (pdftotext 2026-06-11): Digitrip captions per IL70C1037H05 + Digitrip RMS
Units; GE per GEH-5369 (full plain-English set incl. Long Time Delay); **Series B (0602CT9201R201)
captions are IDENTICAL to the '*' defaults** (upgrading the default's basis); Siemens WL guide
confirms IR/tR/Isd/tsd/Ii/Ig/tg. The ONLY symbols left unshipped = **PXR INST/GFPU/GFD** (plain
captions serve symbol-less per L4 until a PD-doc confirm). Serving: `/settings` carries the
`terminology` block (fail-open); Screen 2 renders lineage captions + dial symbols; badges
MFR/VERIFY/N/A; `Rating plug (In)`; bridge display-parity fields live (Part IV). BE
`services/neta/terminology.py` (+17 tests) · FE `lib/terminology.ts` (+8 tests).

**RULINGS (operator, 2026-06-11):** Q1 = "Local Ground" read **agreed** — no surface ever shows
"LG"; `Ground Fault` stands everywhere outside 1b (earth leakage). Q2 = db badge **`MFR`**.
Q3 = unsupported badge **`N/A`**. Q4 = delegated → **CC call: symbols show on BOTH Screen 2 rows
and the sheet** (the page is the screen↔faceplate matching surface). Q5 = **"Test Current"**.
**Lane:** field-tolerances MVP, stage SC3 (`apps/operations-web/TCC_FIELD_TOLERANCES_MVP_SPEC_2026-05-31.md`); task #129.
**Ratified scope (operator, 2026-06-11):** the **test-facing vocabulary layer** — (A) element/dial-symbol
labels, (B) trust/method/honesty phrasing, (C) family-specific setting labels — plus (D) the
bridge-path display-consistency fix. The **product-name long tail** ("Micrologic Std",
"Elect. Trip 1.0×3 spellings") stays in the existing catalog-resolution lane (crosswalk workbook +
`CATALOG-INDEX.csv`), not here. Dictionary home = **governed-but-narrow `tcc.*` verbiage table**
(the "verbiage" slice of ARCHITECTURE Decision 013, WITHOUT triggering the full contract build —
held MVP decision 5 honored). GF naming = **curated per-family map**, DB names as evidence.
**SSoT Law note:** this is review material (evidence tier). On promotion, its approved content folds
into the G-guides + the dictionary seed migration, and the 00-index row flips DRAFT → validated.

**Audience definition (the test for every row):** a NETA technician standing at the gear with the
breaker nameplate, the trip-unit faceplate, and the tolerance sheet. The sheet must read in the
vocabulary on the faceplate and the NETA form — not in EasyPower schema vocabulary, not in our
G4-internal vocabulary.

---

## 0. Design laws (inherited from the EP→ETAP normalization benchmark, §181–190)

- **L1 — Field-trust gates labels.** Every shipped label carries a basis tier (below). Rows at
  `PROPOSED` ship only after upgrade (catalog read or operator confirmation). No guessed vocabulary
  reaches the screen or the sheet — the same law that shelved the frame-tier ETAP guesses.
- **L2 — Verbatim-data law.** Band/dial OPTION labels (`ltd_desc`/`std_desc`/`gfd_desc`/`eq_desc`)
  serve **verbatim** — the census proves EP transcribed the dial faces (`Min/Int/Max`, `0.1–0.4`,
  `Off`, `150ms`, `I^4T-n`, `SGF-n`, `C-10…`), so rewriting them would *reduce* nameplate fidelity.
  Normalization happens in the PRESENTATION layer (element labels, units, method text), never by
  rewriting `tcc.*` band rows. (Same-value duplicates are already collapsed by
  `_dedupe_delay_settings` on `open_time`.)
- **L3 — One dictionary, every consumer.** Screen 2, Screen 3, the B2.1 sheet, and any future
  datasheet surface read the SAME mapping (this is the "verbiage" component of Decision 013).
  A sheet that words a value differently than the page violates the basis-identity law's
  terminology sibling.
- **L4 — NETA element codes stay the row identity.** `LTPU/LTD/STPU/STD/INST/GFPU/GFD` remain the
  primary element keys everywhere (they are the NETA-form vocabulary and survive mixed-fleet
  sheets). Vendor dial symbols are **additive** — `LTPU (Ir)` — never a replacement.
- **L5 — Honesty phrasing translates, never softens.** Withheld stays withheld; flagged stays
  flagged. SC3 changes the words, not the gates.

**Basis tiers used in the tables:**
`[VENDOR-DOC]` = catalog/manual-cited (doc named) · `[DB-EP]` = EasyPower's own per-sensor/band
vocabulary, data-faithful (column named) · `[NETA-STD]` = NETA ATS/industry-standard test
vocabulary · `PROPOSED` = drafted, needs catalog read or operator confirmation before shipping.

---

## 1. Part I — element vocabulary per trip-family lineage

Element identity is per-LINEAGE (vendor faceplate generation), not per EP `trip_type` row. The
serving dictionary keys on a `lineage` assigned from `(manufacturer_display, trip_type/style name)`
patterns (assignment table in §5.3). Evidence columns from the 2026-06-11 prod census
(`etu_sensors.{ltpu,ltd,stpu,inst,gfpu}_name` + band-label vocab per family).

### 1a. Schneider / Square D / Merlin Gerin — Micrologic (IEC generations: A/E/P/H on Masterpact NW/NT, Compact NS/NSX)

Basis: `[VENDOR-DOC]` `MICROLOGIC-6.0A.md` (validated 2026-06-03, Schneider manual
`micrologic_20_70a_eng`) — the dial faces are Ir/tr/Isd/tsd/Ii/Ig/tg. Served units already match
(3833 live: LTPU ×In, STPU ×Ir, INST ×In, GFPU ×In).

| NETA code | Current UI label | Faceplate term | Proposed display | Basis |
|---|---|---|---|---|
| LTPU | Long-Time Pickup | **Ir** (= dial × In) | `LTPU — Long-Time Pickup (Ir)` | `[VENDOR-DOC]` |
| LTD | Long-Time Delay | **tr** @ 6×Ir | `LTD — Long-Time Delay (tr @ 6×Ir)` | `[VENDOR-DOC]` |
| STPU | Short-Time Pickup | **Isd** (× Ir) | `STPU — Short-Time Pickup (Isd)` | `[VENDOR-DOC]` |
| STD | Short-Time Delay | **tsd** (I²t ON/OFF) | `STD — Short-Time Delay (tsd)` | `[VENDOR-DOC]` |
| INST | Instantaneous | **Ii** (× In) | `INST — Instantaneous (Ii)` | `[VENDOR-DOC]` |
| GFPU | Ground-Fault Pickup | **Ig** | `GFPU — Ground-Fault Pickup (Ig)` | `[VENDOR-DOC]` |
| GFD | Ground-Fault Delay | **tg** (I²t ON/OFF) | `GFD — Ground-Fault Delay (tg)` | `[VENDOR-DOC]` |

### 1b. Micrologic 7.0 (earth leakage — Vigi) — **correction, not decoration**

The 72 sensors EP itself names **"Earth Leakage Pickup"** (`etu_sensors.gfpu_name`, exactly the
Micrologic 7.0 census rows; STATE §134/§66: 7.0 replaces ground fault with Vigi residual-current
protection). The current hard-coded "Ground-Fault Pickup" label **misnames the element** — earth
leakage (IΔn/tΔ, RCD-class) is a different protection with a different field test method.

| NETA code | Current UI label | Faceplate term | Proposed display | Basis |
|---|---|---|---|---|
| GFPU | Ground-Fault Pickup ✗ | **IΔn** (earth leakage) | `EL — Earth-Leakage Pickup (IΔn)` | `[DB-EP]` gfpu_name + `[VENDOR-DOC]` §134 |
| GFD | Ground-Fault Delay ✗ | **tΔ** | `EL Delay (tΔ)` | same |

Sheet note for this lineage: "Earth-leakage (residual current) element — NOT a ground-fault
overcurrent test; verify per the manufacturer's Vigi test procedure."
**Detection rule (data-faithful, zero guess):** `gfpu_name = 'Earth Leakage Pickup'`.

### 1c. Square D MicroLogic Series B / Full / Std (legacy ANSI — SE/ME/PE frames; the MVP demo family)

Basis: catalog **0602CT9201R201** ("Micrologic Series B", 2022) is filed in `CATALOG-INDEX.csv`;
the SE manual 48040-495-07 was operator-sourced in §199. Faceplate uses plain-English dial names
(no IEC symbols). Confirm exact dial captions at red-line or first catalog read.

| NETA code | Faceplate term (to confirm) | Proposed display | Basis |
|---|---|---|---|
| LTPU | Long Time Pickup (× plug) | `LTPU — Long Time Pickup` | PROPOSED (0602CT9201R201) |
| LTD | Long Time Delay (band) | `LTD — Long Time Delay (band)` | PROPOSED |
| STPU | Short Time Pickup (× LTPU) | `STPU — Short Time Pickup` | PROPOSED |
| STD | Short Time Delay (Flat/I²t) | `STD — Short Time Delay` | PROPOSED |
| INST | Instantaneous (× plug) | `INST — Instantaneous` | PROPOSED |
| GFPU | Ground Fault Pickup | `GFPU — Ground Fault Pickup` | PROPOSED |
| GFD | Ground Fault Delay (Flat/I²t) | `GFD — Ground Fault Delay` | PROPOSED |

### 1d. Eaton Power Defense PXR (10/20/20D/25)

Basis: `[VENDOR-DOC]` `EATON-POWER-DEFENSE-PXR.md` (validated 2026-06-04 from TD012064–068EN) —
Eaton adopted the IEC symbol set on PXR: **Ir** (LD pickup basis), LD time in seconds, **Isd**
(1.5–12×), **tsd**, with selectable I²t/I⁴t LD and flat/I²t SD.

| NETA code | Faceplate term | Proposed display | Basis |
|---|---|---|---|
| LTPU | **Ir** (Long Delay, × In) | `LTPU — Long Delay Pickup (Ir)` | `[VENDOR-DOC]` |
| LTD | Long Delay Time (s, I²t/I⁴t) | `LTD — Long Delay Time` | `[VENDOR-DOC]` |
| STPU | **Isd** (× Ir) | `STPU — Short Delay Pickup (Isd)` | `[VENDOR-DOC]` |
| STD | **tsd** (Flat/I²t) | `STD — Short Delay Time (tsd)` | `[VENDOR-DOC]` |
| INST | **Ii** | `INST — Instantaneous (Ii)` | PROPOSED (symbol confirm) |
| GFPU | **Ig** | `GFPU — Ground Fault Pickup (Ig)` | PROPOSED (symbol confirm) |
| GFD | **tg** (Flat/I²t) | `GFD — Ground Fault Delay (tg)` | PROPOSED (symbol confirm) |

### 1e. Digitrip lineage (Westinghouse / Cutler-Hammer / Eaton RMS 310–1150 + OPTIM; EP "DT …" families incl. Square D-branded DT)

Basis: Digitrip RMS docs filed (IL70C1037H05 "520 Manual", "Digitrip RMS Units"). DB evidence:
`ltd_name = "LT Delay (s)"` across the whole lineage (the LTD dial is in **seconds**) and
`gfpu_name = "LG Pickup"` (see the **open question** §6-Q1 — EP's "LG" vocabulary). Faceplates
read plain-English "Long Delay / Short Delay / Inst / Ground Fault".

| NETA code | Faceplate term (to confirm) | Proposed display | Basis |
|---|---|---|---|
| LTPU | Long Delay Setting (× In plug) | `LTPU — Long Delay Setting` | PROPOSED (IL70C1037H05) |
| LTD | Long Delay Time (s @ 6×) | `LTD — Long Delay Time (s)` | `[DB-EP]` ltd_name + PROPOSED |
| STPU | Short Delay Pickup (× setting) | `STPU — Short Delay Pickup` | PROPOSED |
| STD | Short Delay Time (Flat/I²t) | `STD — Short Delay Time` | PROPOSED |
| INST | Instantaneous | `INST — Instantaneous` | PROPOSED |
| GFPU | Ground Fault Pickup | `GFPU — Ground Fault Pickup` | PROPOSED (vs "LG" — Q1) |
| GFD | Ground Fault Time | `GFD — Ground Fault Time` | PROPOSED |

Per-sensor exception banked: **Eaton DT 310 `inst_name = "Override"`** (24 sensors) — the INST is
a non-settable override; the sheet row should read `INST — Override (fixed)` and not offer a
setting. Detection: `inst_name = 'Override'`. `[DB-EP]`

### 1f. GE lineage (MicroVersaTrip / MVT-Plus / MVT-PM / RMS-9 / Power+ / VersaTrip MOD2 → EntelliGuard TU)

Basis: GEH-5369 (MicroVersaTrip RMS-9 Programmer) + GEH-6270/1SQC930017M0201 (EntelliGuard TU)
filed. DB evidence: `gfpu_name = "LG Pickup"` lineage-wide; M-Pact LTD bands carry **C-curve
designations** (`C-10…C-16`) alongside numerics — serve verbatim per L2.

| NETA code | Faceplate term (to confirm) | Proposed display | Basis |
|---|---|---|---|
| LTPU | Long Time Pickup (× plug X) | `LTPU — Long Time Pickup` | PROPOSED (GEH-5369) |
| LTD | Long Time Delay (band/C-curve) | `LTD — Long Time Delay (band)` | PROPOSED |
| STPU | Short Time Pickup (× LT setting) | `STPU — Short Time Pickup` | PROPOSED |
| STD | Short Time Delay (band, I²t in/out) | `STD — Short Time Delay` | PROPOSED |
| INST | Instantaneous | `INST — Instantaneous` | PROPOSED |
| GFPU | Ground Fault Pickup | `GFPU — Ground Fault Pickup` | PROPOSED (vs "LG" — Q1) |
| GFD | Ground Fault Delay (band) | `GFD — Ground Fault Delay` | PROPOSED |

### 1g. ABB SACE — Ekip / PR-series (PR121/PR221/PR331/Ekip Dip/Touch/G/Hi-Touch)

Basis: `[VENDOR-DOC]` Ekip Dip Settings Guide 1SXU210266G0201 (filed) + local
`860995673-Ekip-Dip.pdf` (per-element tolerance tables banked §205). ABB names the protection
FUNCTIONS L/S/I/G with thresholds **I1/I2/I3/I4** and times **t1/t2/t4**. DB evidence: the
`ltpu_name=I1/Ir1`, `stpu_name=I2/Ir2`, `inst_name=I3/Ir3` census tail.

| NETA code | Faceplate term | Proposed display | Basis |
|---|---|---|---|
| LTPU | **L — I1** (× In) | `LTPU — L threshold (I1)` | `[VENDOR-DOC]` + `[DB-EP]` |
| LTD | **t1** (@ 3×I1, curve) | `LTD — L time (t1)` | `[VENDOR-DOC]` |
| STPU | **S — I2** (× In) | `STPU — S threshold (I2)` | `[VENDOR-DOC]` + `[DB-EP]` |
| STD | **t2** (Flat/I²t) | `STD — S time (t2)` | `[VENDOR-DOC]` |
| INST | **I — I3** (× In) | `INST — I threshold (I3)` | `[VENDOR-DOC]` + `[DB-EP]` |
| GFPU | **G — I4** (× In) | `GFPU — G threshold (I4)` | `[VENDOR-DOC]` |
| GFD | **t4** (Flat/I²t) | `GFD — G time (t4)` | `[VENDOR-DOC]` |

### 1h. Siemens — Sentron WL / 3WA / 3VA (ETU 3xx–7xx) + Sensitrip III/IV

Basis: WL Selection & Application Guide + 3WA manual filed. IEC symbol set (IR/tR or Ir/tr, Isd,
tsd, Ii, Ig, tg). DB evidence: `ltd_name = "tr"` on ETU 350/560 (×329 sensors) — EP itself uses
the symbol. Sensitrip: datasheets operator-supplied §198 (per-class LI/LIG/LSI/LSIG corrected);
plain-English dials.

| NETA code | Faceplate term | Proposed display | Basis |
|---|---|---|---|
| LTPU | **Ir** (× In) | `LTPU — Long-Time Pickup (Ir)` | PROPOSED (WL guide) |
| LTD | **tr** | `LTD — Long-Time Delay (tr)` | `[DB-EP]` ltd_name + PROPOSED |
| STPU | **Isd** | `STPU — Short-Time Pickup (Isd)` | PROPOSED |
| STD | **tsd** | `STD — Short-Time Delay (tsd)` | PROPOSED |
| INST | **Ii** | `INST — Instantaneous (Ii)` | PROPOSED |
| GFPU | **Ig** | `GFPU — Ground-Fault Pickup (Ig)` | PROPOSED |
| GFD | **tg** | `GFD — Ground-Fault Delay (tg)` | PROPOSED |

### 1i. Legacy static lineage (Amptector I-A/II-A, Seltronic, SB-TL, Sensitrip III, SelecTrip, Power Shield, …)

Faceplates already read plain English ("LONG DELAY PICKUP/TIME", "SHORT DELAY", "GROUND") with
**Min/Int/Max** time positions — the band-label census confirms EP transcribed them. **No change
proposed**: current NETA-form labels are already the faceplate vocabulary. `[DB-EP]` verbatim.
No catalogs filed yet for Amptector/Seltronic/140U — catalog sourcing goes to the existing
worklist only if a job needs deeper confirmation.

### 1j. Default lineage (everything unassigned)

Current labels stand: `LTPU — Long-Time Pickup` etc. `[NETA-STD]`. No symbol suffix (never guess
one — L1).

---

## 2. Part II — trust / method / honesty phrasing (the sheet's Method column + page badges)

All rows **PROPOSED** by design — tone/wording is the operator's domain call (Q2–Q4). The gates do
not change (L5); only the words. Engineering citations (G4 §, fixture names, route names) move to
the secondary line (tooltip / sheet footnote), never deleted — they are the audit trail.

### 2a. Trust badges (Screen 2 table, Screen 3 legend, sheet rows)

| Tier (G4) | Current badge | Current tooltip lead | Proposed badge | Proposed field phrasing (primary line) |
|---|---|---|---|---|
| pickup (always db) | `DB` | "DB-authoritative per-sensor tolerance" | `MFR` | "Manufacturer per-device tolerance (device library)" |
| delay `db` | `DB` | "Direct-band delay — numerically validated row-for-row (G4)" | `MFR` | "Manufacturer time band for this sensor + setting (validated)" |
| delay `verify` | `verify` | "…captured-fixture validation pending (G4)" | `VERIFY` | "Reference only — confirm against the manufacturer TCC before acceptance" |
| delay `unsupported` | `n/a` + "withheld" | "Delay solver not implemented — expected trip time withheld (G4)" | `—` | "No certified trip time — record measured; accept per manufacturer TCC" |

(The `verify` tier is currently EMPTY for delay elements — §214 — but the vocabulary ships anyway:
the tier can repopulate, e.g. future families.)

### 2b. Timing-source / Method labels (`delayBasisLabel`, sheet Method column)

| `timing_source` | Current label | Proposed field label |
|---|---|---|
| `ltd_reference_window` | "mfr tolerance (DS2)" | "Manufacturer LTD tolerance (device library)" |
| `ltd_reference_window_generic` | "generic estimate — no mfr tolerance on file" | "Estimated band −30%/+0% — **no manufacturer tolerance on file** (flagged)" |
| `band_table` | "mfr band (per-sensor DB)" | "Manufacturer delay band (per-sensor)" |
| `i2x_*` | "validated I²t surface" | "Manufacturer I²t characteristic (validated)" |
| `curve_interpolation` | "curve envelope (open/clear)" | "Manufacturer curve band (open/clear)" |
| `maint_profile` | "maintenance-mode profile" | "Maintenance-mode (ARMS) profile" |

### 2c. Cell markers + notes

| Surface | Current | Proposed |
|---|---|---|
| withheld time cell (page) | "withheld" | keep "withheld" (it is honest and short) + footnote symbol |
| withheld time cell (sheet) | — | "— ²" with footnote: "No certified expected time for this element; record the measured value; acceptance per the manufacturer TCC." |
| generic-LTD marker | "est" superscript | "est*" + footnote: "Estimated −30/+0% band; no manufacturer tolerance on file." |
| plot caveat | "nominal illustration" | "Published curve (nominal) — acceptance is the envelope/table values" |
| envelope legend | "field-acceptance corridor" | keep (already field-correct) |
| maint warning | (server text) | "Maintenance mode (ARMS) ON — curves show normal mode; test points reflect maintenance settings" (confirm exact server wording at implementation) |

### 2d. Sheet footer (the law line, every B2.1 page)

> "Acceptance values are **manufacturer tolerances** per the device library; NETA ATS Table 100.7
> values are used **only where labeled** as fallback. Pickup tolerances are per-device. Withheld
> times are deliberate: no certified basis exists — use the manufacturer TCC."

(Phrasing operator-owned; the NETA=mfr law itself is `feedback_neta_acceptance_equals_mfr_tolerances`.)

---

## 3. Part III — family-specific setting labels

### 3a. The "Plug (Ir)" mislabel — **bug-grade finding**

Screen 2's eq-strip labels the plug selector **"Plug (Ir)"** (`page.tsx` ~1007). On the flagship
family the plug is **In** (the rating plug / sensor-tap), and **Ir = LTPU-dial × In** — live 3833:
plug values 400–1200 A with LTPU dial 0.4–1.0 ×In. Calling the plug "Ir" inverts the two most
load-bearing symbols on the faceplate. `[VENDOR-DOC]` MICROLOGIC-6.0A.md §1.

| Surface | Current | Proposed | Basis |
|---|---|---|---|
| plug selector | `Plug (Ir)` | `Rating plug (In)` | `[VENDOR-DOC]` |
| per-lineage override | — | none known where plug ≠ In; dictionary supports it if found | — |
| sensor chip | `Sensor` | keep `Sensor` (+ description verbatim) | `[DB-EP]` |
| pickup option units | `× Ir` / `× In` / `A` (server-driven) | keep (already per-family-correct) | validated |
| delay test selector | `Test @` ×-multiple | `Test @ (× pickup)` — confirm wording | `[NETA-STD]` |

### 3b. Element-row composition rule

Row template per L4: `CODE — Lineage label (symbol)`; code chip stays the visual key. Where the
lineage has no confirmed symbol → no parenthetical (1j).

---

## 4. Part IV — selection-surface consistency fix (ratified item D)

`/etu/bridge-sensors` serves the trip triple **raw** (`tmt_sst_mfr/type/style` — `vw_breaker_sst_bridge`
strings) with no display fields, while the cascade path serves `manufacturer_display` +
`trip_model_display`. The breaker-axis sensor dropdown can therefore show EP vocabulary the
trip-axis dropdown has already normalized.

**Spec:** add `tmt_sst_mfr_display` / `tmt_sst_model_display` to the bridge response — same
COALESCE chain as `/cascade` (`trip_style_aliases` pick → `trip_model_aliases` → raw), joined at
serving (no DB change, isolated to the endpoint per DURABLE 23); frontend `etu-sensor-pool.ts`
prefers the display fields (same pattern as `breaker_model_display` there today). TDD: one BE test
(display fields present + COALESCE order), one FE unit test (label uses display when present).

---

## 5. Part V — the dictionary mechanism (governed-narrow; ratified lean 2)

### 5.1 Table (one migration, hash-checked seed per the §183 recipe)

```sql
CREATE TABLE tcc.field_terminology (
  id          serial PRIMARY KEY,
  namespace   text NOT NULL,   -- 'element' | 'trust' | 'method' | 'setting' | 'note'
  lineage     text NOT NULL,   -- 'micrologic_iec' | 'micrologic_7x_el' | 'micrologic_series_b'
                               -- | 'pxr' | 'digitrip' | 'ge_mvt_eg' | 'ekip_pr' | 'siemens_etu'
                               -- | 'legacy_static' | '*' (default)
  term_key    text NOT NULL,   -- e.g. 'ltpu' | 'trust.db.delay' | 'timing_source.band_table' | 'plug'
  label_short text NOT NULL,   -- badge / chip / column-header form
  label_long  text,            -- row / tooltip primary line
  symbol      text,            -- faceplate symbol ('Ir', 't1', 'IΔn'…), additive per L4
  method_text text,            -- sheet Method-column sentence (namespace 'method'/'trust')
  basis       text NOT NULL,   -- 'VENDOR-DOC:<doc>' | 'DB-EP:<column>' | 'NETA-STD' | 'PROPOSED'
  status      text NOT NULL DEFAULT 'draft',  -- 'draft' | 'approved'  (serving uses approved only)
  UNIQUE (namespace, lineage, term_key)
);
```

Serving resolution: `COALESCE(approved row @ lineage, approved row @ '*', hard-coded current
label)` — fails open to today's strings, so a missing row can never blank a label. `status`
enforces the red-line gate **in data**: the seed lands as `draft`; the operator's approvals flip
rows to `approved`; only `approved` serves. PROPOSED-basis rows cannot be `approved` (CHECK or
review discipline — operator call which).

### 5.2 Consumers (L3)

1. `/settings` + `/calculate` gain an `element_display` block (code, label_long, symbol, plug
   label) resolved per sensor's lineage → Screen 2 renders it (EL_META becomes the '*' fallback).
2. `/plot-tcc` legend/basis labels + trust badges resolve through namespaces 'trust'/'method'.
3. **B2.1 sheet generator reads the same rows** — the sheet inherits SC3 for free; no second
   vocabulary ever exists.

### 5.3 Lineage assignment

A pattern rule over `(manufacturer_display, trip type/style name)` — e.g. mfr Schneider/Square
D/Merlin Gerin + name ~ 'micrologic|masterpact|compact ns' minus the Series-B set → `micrologic_iec`;
`gfpu_name='Earth Leakage Pickup'` → `micrologic_7x_el` (overrides); Eaton + ~'pxr|power defense'
→ `pxr`; West/C-H/Eaton/SqD + ~'^DT |digitrip|optim' → `digitrip`; GE + ~'mvt|versatrip|rms-9|
power\+|entelliguard|m-pact' → `ge_mvt_eg`; ABB + ~'ekip|pr[123]' → `ekip_pr`; Siemens + ~'etu|wl|
3wa|3va|sentron' → `siemens_etu`; the §1i name set → `legacy_static`; else `*`. The assignment
ships as a SQL function or view column (testable), **not** scattered string checks. Exact pattern
set finalized at implementation; per-sensor `*_name` columns drive only the two banked exceptions
(1b earth-leakage, 1e DT-310 Override).

### 5.4 Explicitly NOT in this build

No full D-013 contract materialization (held decision 5) · no band-row rewrites (L2) · no
product-name aliases (stays in catalog-resolution) · no relay vocabulary (relaytcc inherits the
mechanism later via Chips 4–6).

### 5.5 Implementation order (after red-line)

1. Catalog-confirmation pass on PROPOSED rows the operator doesn't settle by hand (the filed docs:
   0602CT9201R201, IL70C1037H05, GEH-5369/6270, WL guide; PyMuPDF render → read).
2. Migration: `tcc.field_terminology` + seed (approved rows only ship `approved`).
3. Serving: element_display block + trust/method resolution (TDD; fail-open).
4. Frontend: Screen 2/3 consume; "Rating plug (In)" fix; bridge display fix (Part IV).
5. Live-verify (3833 Micrologic symbols; a Digitrip sensor; the 7.0 earth-leakage rename;
   DT-310 Override row) + SSoT fold (G4 cross-ref + 00-index DRAFT→validated) + B2.1 consumes.

---

## 6. Open questions for the operator (the genuinely-domain calls)

- **Q1 — EP's "LG Pickup".** 1,623 sensors (Digitrip lineage + GE MVT/VersaTrip/RMS-9/Power+ +
  Siemens SB-TL/Sensitrip III) carry `gfpu_name = "LG Pickup"`. Faceplates in those families say
  "Ground Fault". What does EasyPower's "LG" denote in your read (its setting dialogs use it) —
  and should any surface ever show "LG", or is `Ground Fault` correct everywhere outside 1b?
  Draft assumes the latter.
  **Evidence run 2026-06-11 (Access `D:\TCC_NEW.accdb`, operator-requested join
  `DatSensor → DatStyle → DatSection1GfGFP`; extract `.audit_workspace/sc3_terminology/LG_pickup_sensors_gfp.csv`):**
  - Census: `SEC1GF_NAME` has exactly 3 values ever — GF Pickup 16,136 / **LG Pickup 1,623** /
    Earth Leakage Pickup 72. LG = **purely the legacy ANSI switchboard generation** (all
    West/C-H/SqD/Eaton DT/Digitrip variants, GE MVT-4/9/Plus/PM/Enhanced + VersaTrip (MOD2) +
    RMS-9/Power+/SST/SelecTrip/TA9VT, Siemens SB-TL/SB-EC/Sensitrip III, Westrip, SqD
    Powerlogic 810D; + 5 Chint NA outliers). 1,553 LG sensors carry GFP tap rows (9,945);
    70 have none (MVT-Enhanced 20, SB-TL 18, Powerlogic 810D 12, VersaTrip MOD2 11, Power+ 9).
  - **The discriminating contrast: Square D Ground Censor / GC-200 — a SEPARATE ground-CT
    system — is named `GF Pickup`,** while every breaker-INTEGRAL ground element of that same
    era is `LG Pickup`. Modern integral units (Micrologic/PXR/Ekip/EG-TU) are all `GF Pickup`,
    so the distinction was maintained only within the legacy generation.
  - No structural discriminator otherwise: pickup-calc bases overlap (LG ⊂ {-1,0,1,7});
    `GFP_DESC` = the literal faceplate dials in both populations (Digitrip lettered taps
    `A(0.25)…K`, GE fractions `0.2…`/`0.3X`); `DatSection1GfGFP.Mode` is **not read by the
    decompiled DeviceLibrary** (`ReadGroundSettings` selects only GFP_DESC+GFP_SETTING) —
    vestigial; Mode=1 exists only on Micrologic 6.0X (450 rows) + Utility Relay AC-PRO/II (126),
    all GF-named. No DVL description; the string "LG Pickup" appears in no code — it is typed
    library data (the per-sensor settings-dialog caption).
  - **CC read:** "LG" = EP-librarian shorthand, best supported as **"Local Ground"** — the
    breaker-integral ('local') ground element, as opposed to a separate ground-relay system
    (the Ground Censor pattern) — applied only to the legacy ANSI generation. It is not
    faceplate vocabulary anywhere → no field surface should show "LG"; `Ground Fault` stands
    everywhere outside 1b. The real nameplate match for these families lives in the GFP tap
    labels (`A(0.25)`…), which already serve verbatim per L2. **Operator ruling still owns
    this row.**
- **Q2 — badge word for db.** `MFR` proposed (alternatives: keep `DB`; `LIB`; `CERT`). The sheet
  prints it in every row — your call.
- **Q3 — badge word for unsupported.** `—` + footnote proposed (alternative: `N/A`, current).
- **Q4 — symbol placement.** Symbols on Screen 2 rows AND the sheet (draft assumes both), or
  sheet-only to keep the page compact?
- **Q5 — "Test @" wording** on the sheet: "Test current (× pickup)" vs "Inject @". Draft assumes
  the former.

## 7. Red-line protocol

Mark this file directly (or dictate): per-row **approve / edit / reject**. Anything `PROPOSED`
needs either your confirmation (you know these faceplates) or the §5.5-step-1 catalog read before
it can serve. On your pass: seed migration encodes exactly the approved rows; everything else
stays `draft` and invisible.
