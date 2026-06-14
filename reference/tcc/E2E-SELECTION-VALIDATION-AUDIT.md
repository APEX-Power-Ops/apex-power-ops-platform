# E2E Selection-Validation Audit — Access ↔ Supabase ↔ Breaker UI

*Task brief / governed spec. Created 2026-06-12. Status: Phase 0 grounded, execution pending operator vehicle-confirm.*
*Home: `reference/tcc/`. Re-run after every EasyPower (EP) re-import. **READ-ONLY lane — reads + reports, never mutates.***

> **Host-bound.** Only the field host (CC) reaches all three layers: the Access source is local on `D:\` (OLEDB), and driving the *deployed* UI needs the local Playwright. A cloud Codex agent can do the Supabase↔UI legs at best — **this is a CC-host task, do not queue it to cloud Codex.**

---

## 1. Objective

Walk every selection surface across the three layers and emit **one categorized inconsistency ledger**. The ledger is the deliverable; its **bucket mix decides the D-013-now call** (§7).

The operator reports "many, many inconsistencies embedded in the UI." This audit characterizes them systematically rather than chasing them ad hoc — *characterize before fixing* (the §184 verify-the-defect-before-chasing durable; the §197–§205 lane discipline).

## 2. The three layers + the cross-layer key spine (Phase 0 — VERIFIED 2026-06-12)

The EP id survives as the Postgres PK (no separate source-id column on `etu_sensors`), so a record joins Access→Supabase **by id directly**. The intra-Supabase wiring is non-obvious and was mapped, not assumed:

| Axis | Access (`D:\TCC_NEW.accdb`) | Supabase (`fxoyniqnrlkxfligbxmg`) | UI / API |
|---|---|---|---|
| Manufacturer | `Manufacturers` (450) | `tcc.manufacturers.id` (450) + `tcc.mfr_aliases` (display) | `/cascade` manufacturer_id/name |
| Trip **Type** | `DatStyle.[TYPE]` text — **no own table** | `tcc.trip_styles.type` text **+ reconstructed** `tcc.trip_types(id,manufacturer_id,name)` (558 = distinct (mfg,type)) | `/cascade` trip_type_id/name |
| Trip **Style** | `DatStyle` row (2094) | `tcc.trip_styles.id` (2095) + protection class derived from element flags | `/cascade` trip_style_id + `protection_class` |
| Sensor | `DatSensor.SensorID` (17831) | `tcc.etu_sensors.id` (17877) | `/cascade` sensor_id, rating, desc |
| Elements / settings | `DatSection1Sett/Mult/Gf*`, `DatSection2LTD`, `DatSection3*`, `DatSection4Inst*` | `tcc.etu_sensors.*` cols + 17 child band tables + `tcc.field_terminology` | `/settings`, `/calculate` |
| Valid combos (breaker→trip→sensor) | `BreakerPCB/MCCB/ICCB(+Styles)`, `Breaker_TMTFrame*`, `EMT_*`, `MOC*` | `tcc.vw_breaker_sst_bridge` + `tcc.breaker_alt_trip_bridge` | `/etu/breaker-cascade`, `/etu/bridge-sensors` |

**The fragile seam:** `public.vw_trip_unit_cascade` re-links style→type by **string equality** —
`LEFT JOIN tcc.trip_types tt ON tt.manufacturer_id = m.id AND tt.name = ts.type`.
Currently clean (2095/2095 single-match, 0 NULL, 0 fan-out), but case/whitespace drift on a future re-import would silently NULL the Type, and duplicate type-names would fan a sensor into multiple cascade rows. **Recurring structural watch-point.**

### Phase 0 baseline reconciliation (counts)
- Manufacturers 450 = 450 ✓ · trip_types 558 = 558 distinct (mfg,type) ✓ · cascade 17877 = sensors 17877 ✓ (no fan-out).
- trip_styles **+1** (2094→2095) = the §176 build-new-trip `GE/M-Pact/'M-PRO 17 Plus'` (id 2586).
- sensors **+46** (17831→17877) = §171/§173/§178/§180 plug-fill clones + §176 built sensors.
- **→ the id spine is intact; divergences are explained by known intentional corrections. The inconsistencies live in the derivation/display/cross-filter layers, not the id spine.** (Each +1/+46 row still gets individually verified against the migration record in §132.)

## 3. The correction-subtraction principle (design refinement, Phase 0)

The Access↔Supabase **content** diff is noisy: migrations 018–026 deliberately mutated the source (GF-suppress flag flips, `-LI`→`-LIG` style renames, plug-fill clones, the built trip). A naive content diff drowns in these false positives. So every content finding is dispositioned against the **intentional-correction ground truth** — the `tcc.*_backup_*` snapshot tables + the 013–026 migration ledger:

- `verified-clean` — Access == Supabase (modulo display alias).
- `intentional-correction` — diverges, but matches a migration/backup record. **Not a defect.**
- `accidental-divergence` — diverges with no correction record. **The real findings.**

## 4. What "validate selections throughout" checks (per axis)

Each row traced Access → Supabase → serving view → UI option:

| Surface | Divergences it catches |
|---|---|
| Manufacturer | alias display vs Access mfr vs UI dropdown; dup-collapse correctness (#89) |
| Trip Type (model) | the string-seam health; cross-filter narrowing (§195 dup-key class); model-name normalization |
| Trip Style (class) | protection-class fidelity L/S/I/G (the §196–§205 lane); cross-type leaks (§200) |
| Sensor | rating/description; phantom / missing options; SST-bridge + retrofit valid-combinations (#74, §192) |
| Settings / terminology | SC3 captions, dial symbols, MFR/VERIFY/N·A badges, `Rating plug (In)`, lineage resolution (§215) |
| Cross-filter integrity | every axis ∩ every other — the recurring leak family (§195/§196/§200) |

## 5. Categorization rubric (every ledger row)

`finding_id · axis · layer_origin {access | supabase-view | frontend} · bucket {data-fidelity | serving-divergence | frontend-trapped} · disposition {verified-clean | intentional-correction | accidental-divergence} · severity · description · evidence (ids/queries/screens) · d013_relevant {y/n} · proposed_remediation`

- **bucket (i) data-fidelity** → fix in EP tables (the §197–§205 pattern).
- **bucket (ii) serving-divergence** → the D-013 contract's target.
- **bucket (iii) frontend-trapped** → label/scoping logic in `page.tsx`/`lib/*` → also a D-013 target (contract pulls it down).

## 6. Method (stratified, host-bound)

- **Structural — 100% of rows (cheap, all SQL/OLEDB set-algebra):** Access-set vs Supabase-set vs serving-view output across every axis. Subtract known corrections (§3). Catches missing/phantom/mislabeled/fan-out at scale.
- **UI deep-drive — stratified ~15–20 paths (Playwright on the deployed page):** chosen to hit every known risk pattern — each mfr family · each protection class · native + retrofit · all 8 terminology lineages · §200-style collisions. Capture rendered dropdown options + settings/terminology/sheet vs the served payloads vs Supabase. Stepwise-driven cascades (DURABLE 40).
- **Execution vehicle:** Workflow fan-out (parallel layer/family readers → cross-layer diff → ledger synthesis) **or** inline staged — *operator's call (token cost).* 

## 7. Output + the D-013 gate

- Raw ledger + layer snapshots → `.audit_workspace/e2e_audit/` (host-local, gitignored).
- Summary + the **evidence-based D-013-now recommendation** → `reference/tcc/` (this folder).
- **The gate:** mostly bucket (ii)+(iii) ⇒ pull the D-013 canonical-contract build forward (the first consumer is itself suffering the absent contract; "wait for consumer #2" was the wrong gate). Mostly bucket (i) ⇒ fix-in-place, keep D-013 deferred. The operator rules from the ledger.

## 8. Guardrails

Read-only (no `apply_migration`, no writes). `execute_sql` is the authorized read path. Access via OLEDB on `D:\` (read-only). No secrets in any committed artifact. Scoped `git add` only. §146 boundary intact (no ETAP curve decryption; this lane doesn't touch curves).
