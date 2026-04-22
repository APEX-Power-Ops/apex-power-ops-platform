# RESOURCE AUDIT REPORT — Next Guide Topics
## Generated: 2026-03-18

---

## TOPIC 1: Motors (NETA ATS 7.15)

### NETA-Data Status
| Section | Title | VM Tests | EL Tests |
|---------|-------|----------|----------|
| 7.15.1 | AC Induction Motors and Generators | 11 | 16 |
| 7.15.2 | Synchronous Motors and Generators | 11 | 26 |
| 7.15.3 | DC Motors and Generators | 10 | 10 |

**All three sections fully populated in NETA JSON with complete VM + EL test items.**

### Table A — Extracted and in Supabase (usable by CC now)

| content_id | Title | Lines | Relevance |
|---|---|---|---|
| EXT-IEEE-179 | IEEE 43 — Complete Motor Insulation Testing Guide | 676L | **CORE** — primary IR/PI standard for rotating machines |
| EXT-IEEE-178 | Minimum Insulation Resistance Values — Rotating Machinery | 129L | **CORE** — acceptance criteria tables |
| EXT-IEEE-180 | Polarization Index (PI) Interpretation — Rotating Machinery | 284L | **CORE** — PI interpretation guidance |
| EXT-IEEE-018 / EXT-IEEE-154 | IEEE 112-2004 — Induction Motor Testing | 899L | **CORE** — primary induction motor test procedure |
| EXT-IEEE-032 | IEEE 95-2002 — Insulation Testing of AC Electric Machinery | 543L | **HIGH** — complementary to IEEE 43 for AC machines |
| EXT-IEEE-232 | IEEE 3004.8 — Motor Protection Industrial/Commercial | 724L | HIGH — motor protection schemes |
| EXT-IEEE-260 | IEEE C62.21-2003 — Surge Arresters on Rotating Machinery | 770L | MED — surge protection for motors/generators |
| EXT-ATS-024 | Rotating Machinery Testing — Vibration & IR | 234L | **CORE** — NETA ATS table extraction |
| EXT-MTS-003 | MTS-2023 Table 100.10 — Rotating Machinery Vibration Limits | 548L | HIGH — maintenance vibration acceptance criteria |
| EXT-MTS-004 | Rotating Machinery Insulation Resistance Testing | 218L | HIGH — maintenance IR testing |
| EXT-FLD-012 | Megger Baker MTR105 — Low Voltage Motor Testing | 511L | HIGH — practical LV motor test guide |
| EXT-TXT-016 | Paul Gill — Motor & Generator Testing Field Methods | 610L | **CORE** — field test procedures |
| EXT-ETT-003 | Rotating Machinery Fact Sheet | 137L | MED — study aid |
| EXT-IND-018 / EXT-TXT-022 | E05 — Condition Monitoring of Rotating Machines (2020) | 1,123L | HIGH — modern CM techniques |
| EXT-IND-025 | Electric Motor Energy Efficiency Reference Guide | 398L | LOW — energy efficiency focus |
| EXT-IND-026 | Electrical Motors and VFDs — Energy Efficiency Guide | 710L | LOW — VFD/efficiency focus |
| EXT-FLD-019 | Relay Testing Handbook Vol. 3 — Motor Relay Testing | 1,122L | MED — motor relay testing |

**Supabase total: 17 extractions (some duplicated content_ids) — ~9,700L**

### Local .md Files — Sync Status

| File | Status | Supabase content_id |
|---|---|---|
| IEEE-43-Motor-Testing-Complete.md | EXISTS-BOTH | EXT-IEEE-179 |
| IEEE-43-Minimum-IR-Values.md | EXISTS-BOTH | EXT-IEEE-178 |
| IEEE-43-PI-Interpretation.md | **EXISTS-LOCAL-ONLY** | — (may be EXT-IEEE-180 but filename doesn't match) |
| IEEE-43-Temperature-Correction.md | EXISTS-BOTH | EXT-IEEE-181 |
| IEEE-95-Motor-Insulation-Testing.md | EXISTS-BOTH | EXT-IEEE-032 |
| ATS-2025-100.10-100.11-Rotating-Machinery.md | EXISTS-BOTH | EXT-ATS-024 (mapped via MTS) |
| ATS-2025-100.9-Motors.md | **EXISTS-LOCAL-ONLY** | — (no matching SB row found) |
| Paul-Gill-10-Motor-Testing-Field-Methods.md | EXISTS-BOTH | EXT-TXT-016 |
| MTS-2023-100.11-Rotating-Machinery-IR.md | EXISTS-BOTH | EXT-MTS-003/004 |
| E05-Condition-Monitoring-Rotating-Machines-2020.md | EXISTS-BOTH | EXT-IND-018 |

### Table B — Source PDFs Present, Not Yet Extracted

| Filename | Location | Priority | Why |
|---|---|---|---|
| IEEE-115-Synchronous-Machine-Testing.pdf | IEEE/ | **HIGH** | Primary test standard for synchronous machines (7.15.2) — 26 EL items in section |
| IEEE-Tutorial-2011-Synchronous-Generator-Protection.pdf | IEEE/ | MED | Supplementary protection concepts |
| ElectricMotorGuide.pdf | Textbooks/ | LOW | General reference, likely overlaps existing |
| IEEE-C37.102-2006-Generator-Protection.pdf | IEEE/ | LOW | Generator protection (tangential to motor testing) |

### Table C — Missing — Not in corpus at all

| Resource | What it covers | Priority |
|---|---|---|
| **IEEE 522** — Testing Turn Insulation of Form-Wound Stator Coils | Surge comparison test for stator windings | **HIGH** — critical for surge test EL items |
| **NEMA MG 1** — Motors and Generators | Nameplate data, performance standards, ratings | **HIGH** — foundational reference for all motor types |
| IEEE 303-1984 — Test Procedures for DC Machines | DC motor acceptance criteria | MED — relevant to 7.15.3 (10 EL items) |
| IEEE 1566-2015 — Adjustable Speed Drive Systems | ASD performance testing | LOW — more relevant to Topic 3 (VFDs) |

### Coverage Assessment: **STRONG**

Motor topic has the deepest extraction base of all four candidates: 17+ Supabase rows, IEEE 43 fully extracted (IR, PI, temp correction), IEEE 112 extracted, Megger Baker guide, Paul Gill field methods, NETA ATS/MTS tables, and condition monitoring textbook. All three NETA sections (7.15.1–7.15.3) are fully populated with VM+EL items.

### Extraction Recommendation
1. **IEEE 115 — Synchronous Machine Testing** (HIGH) — needed for 7.15.2 which has 26 EL items, the most complex subsection
2. Upload `IEEE-43-PI-Interpretation.md` and `ATS-2025-100.9-Motors.md` to Supabase (local-only files)

### Gaps
- IEEE 522 (surge test) and NEMA MG 1 (motor nameplate standards) would materially improve the guide but are not in the corpus at all. Consider acquiring.

---

## TOPIC 2: Capacitors / Reactors (NETA ATS 7.20)

### NETA-Data Status
| Section | Title | VM Tests | EL Tests |
|---------|-------|----------|----------|
| 7.20.1 | Capacitors | 7 | 4 |
| 7.20.2 | Capacitor Control Devices | RESERVED | — |
| 7.20.3.1 | Reactors (Shunt/Current-Limiting) Dry-Type | 8 | 5 |
| 7.20.3.2 | Reactors (Shunt/Current-Limiting) Liquid-Filled | 15 | 8 |
| 7.20.4 | Resistors | 11 | 4 |

**Note:** 7.20.2 is RESERVED in ATS-2025 (no test items). Section scope is broader than initially listed — includes 7.20.3.x (reactors) and 7.20.4 (resistors).

### Table A — Extracted and in Supabase (usable by CC now)

| content_id | Title | Lines | Relevance |
|---|---|---|---|
| EXT-ETT-012 | Capacitor Reactor Fact Sheet | 141L | MED — study aid overview |
| EXT-FLD-004 / EXT-MFR-080 | Field Test on Capacitors — GE GET-2002E | 313L | **CORE** — primary capacitor field test reference |
| EXT-MFR-022 | CCVT — Installation Manual | 2,072L | LOW — coupling capacitor VTs, different from power caps |
| EXT-MFR-030 | Trench Dry-Type Shunt Reactors 500kV Datasheet | 352L | MED — dry-type reactor specs |
| EXT-IEEE-207 | IEEE C57.113-2023 — PD Measurement (Transformers & Shunt Reactors) | 594L | MED — PD testing for liquid-filled reactors |
| EXT-IEEE-211 | IEEE C57.125-2015 — Transformer/Shunt Reactor Failure Investigation | 336L | LOW — failure investigation |
| EXT-MFR-037 | Omicron — Power Factor Testing: CCVTs, PTs, CTs | 754L | MED — PF test methods (tangential) |
| EXT-MTS-012 | MTS-2023 Table 100.3 — Power Factor/DF (Maintenance) | 759L | HIGH — maintenance PF/DF acceptance tables |
| EXT-ATS-034 | Power Factor and Dissipation Factor Testing | 589L | HIGH — ATS PF/DF extraction |
| EXT-TXT-007 | Paul Gill — Power Factor & Dissipation Factor Testing | 3,404L | HIGH — comprehensive PF/DF field guide |

**Supabase total: 10 extractions — ~9,300L**

### Local .md Files — Sync Status

| File | Status | Supabase content_id |
|---|---|---|
| CCVT-Coupling-Capacitor-Installation-Manual.md | EXISTS-BOTH | EXT-MFR-022 |
| Trench-Dry-Type-Shunt-Reactors-500kV-Datasheet.md | EXISTS-BOTH | EXT-MFR-030 |
| Capacitor-Reactor-Fact-Sheet.md | EXISTS-BOTH | EXT-ETT-012 |
| Capacitor-Field-Testing-Guide.md | EXISTS-BOTH | EXT-FLD-004/MFR-080 |

### Table B — Source PDFs Present, Not Yet Extracted

| Filename | Location | Priority | Why |
|---|---|---|---|
| **IEEE-18-2012-Shunt-Power-Capacitors.pdf** | **IEEE/** | **CRITICAL** | Core acceptance test standard for power capacitors — ratings, testing, tolerances *(sorted from _Unsorted/ on 2026-03-18)* |
| IEEE-1303-1994-Substation-Capacitor-Banks.pdf | IEEE/ | **HIGH** | Shunt cap bank installation, protection, testing |
| IEEE-C57.21-1990-Shunt-Reactors.pdf | IEEE/ | **HIGH** | Primary shunt reactor requirements standard |
| IEEE-C57.16-1996-Current-Limiting-Reactors.pdf | IEEE/ | **HIGH** | Series reactor requirements for 7.20.3.x |
| IEEE-C37.015-1993-Shunt-Reactor-Switching.pdf | IEEE/ | MED | Reactor switching transients |
| IEEE-C37.66-2021-Oil-Filled-Capacitor-Switches.pdf | IEEE/ | MED | Current edition cap switch standard |
| IEEE-C37.66-1969-Oil-Filled-Capacitor-Switches.pdf | IEEE/ | LOW | Superseded |
| Eaton-Cooper-Pole-Mounted-Capacitor-Racks.pdf | Equipment-Manuals/ | LOW | MFR installation guide |
| Federal-Pacific-Pad-Mounted-Capacitor-Banks.pdf | Equipment-Manuals/ | LOW | MFR installation |
| Capacitor Field Testing.pdf | Equipment-Manuals/ | MED | May overlap with EXT-FLD-004/MFR-080 — verify |

### Table C — Missing — Not in corpus at all

| Resource | What it covers | Priority |
|---|---|---|
| **IEEE 1036** — Application Guide for Shunt Capacitors | Application, protection, and design guidance | **HIGH** — practical field application guidance |

> **UPDATE 2026-03-18:** IEEE 18-2012 located in _Unsorted/ and moved to `Source-PDFs/IEEE/IEEE-18-2012-Shunt-Power-Capacitors.pdf`. CRITICAL gap resolved — now ready for extraction.

### Coverage Assessment: **THIN**

Capacitor/reactor topic has a thin extraction base but the critical IEEE 18 gap is now resolved. IEEE 18-2012 (793 KB, 83 pages) covers capacitor ratings, tolerances, testing, and acceptance criteria — the core standard for power capacitor acceptance testing. Multiple IEEE reactor standards (C57.21, C57.16) are available as PDFs but unextracted. The NETA sections exist with test items (7.20.1: 7VM/4EL, 7.20.3.x: up to 15VM/8EL) but reference material to explain those tests needs extraction. Section 7.20.2 is RESERVED.

### Extraction Recommendation
1. **IEEE 18-2012 — Shunt Power Capacitors** (CRITICAL) — core acceptance test standard, NOW AVAILABLE for extraction
2. **IEEE C57.21-1990 — Shunt Reactors** (HIGH) — needed for 7.20.3.2 (15 VM + 8 EL items)
3. **IEEE C57.16-1996 — Current-Limiting Reactors** (HIGH) — needed for 7.20.3.x
4. **IEEE 1303-1994 — Substation Capacitor Banks** (HIGH) — only IEEE cap bank standard in corpus

### Gaps
- ~~IEEE 18 CRITICAL gap~~ — **RESOLVED** (sorted to `IEEE/IEEE-18-2012-Shunt-Power-Capacitors.pdf` on 2026-03-18)
- IEEE 1036 (application guide) would also significantly improve coverage.

---

## TOPIC 3: VFDs / MCCs (NETA ATS 7.16)

### NETA-Data Status
| Section | Title | VM Tests | EL Tests |
|---------|-------|----------|----------|
| 7.16.1.1 | Motor Starters, Low-Voltage | 9 | 5 |
| 7.16.1.2 | Motor Starters, Medium-Voltage | 12 | 17 |
| 7.16.2.1 | Motor Control Centers, Low-Voltage | REFS-ONLY (4 refs) | — |
| 7.16.2.2 | Motor Control Centers, Medium-Voltage | REFS-ONLY (4 refs) | — |

**Note:** MCC sections (7.16.2.x) contain only references to other sections (e.g., "test per 7.16.1.x, 7.5.x, 7.2.x"). This is because MCCs are assemblies — testing is done on component level (starters, breakers, bus).

### Table A — Extracted and in Supabase (usable by CC now)

| content_id | Title | Lines | Relevance |
|---|---|---|---|
| EXT-ETT-004 | VFD Fact Sheet | 86L | MED — study aid |
| EXT-IND-011 | VFD Panel Configuration & Troubleshooting | 380L | HIGH — practical VFD field reference |
| EXT-IND-026 | Electrical Motors and VFDs — Energy Efficiency Guide | 710L | MED — VFD application/efficiency |
| EXT-IEEE-1683 | IEEE 1683-2014 — Guide for Motor Control Centers | 731L | **CORE** — primary MCC standard |
| EXT-MFR-003 | Eaton Freedom 2100 MCC — Installation & Maintenance | 3,045L | **CORE** — practical MCC installation/maintenance |
| EXT-MFR-014 | Siemens 81000 MV Vacuum Contactor 5-7kV — IOM | 3,591L | HIGH — MV contactor/starter reference |
| EXT-NEMA-004 | NEMA AB 4-2017 — Inspection of MCCBs | 1,016L | HIGH — MCCB inspection for MCC units |
| EXT-NEMA-005 | NEMA ICS 2-2000 — Controllers, Contactors | 553L | HIGH — controller/contactor standards |
| EXT-MFR-045 | Eaton ATC-900 Bypass Isolation Contactor ATS FAQ | 167L | LOW — ATS-specific |

**Supabase total: 9 extractions — ~10,300L**

### Local .md Files — Sync Status

| File | Status | Supabase content_id |
|---|---|---|
| IEEE-1683-2014-Motor-Control-Centers-Guide.md | EXISTS-BOTH | EXT-IEEE-1683 |
| VFD-Fact-Sheet.md | EXISTS-BOTH | EXT-ETT-004 |
| VFD-Panel-Configuration-Troubleshooting.md | EXISTS-BOTH | EXT-IND-011 |
| Motors-VFD-EE-Guide.md | EXISTS-BOTH | EXT-IND-026 |
| Motor-Control-Center-Installation-Maintenance.md | EXISTS-BOTH | EXT-MFR-003 |
| NEMA-AB-4-2023-Guidelines-Inspection-MCCB-Delta.md | EXISTS-BOTH | EXT-NEMA-004 |
| NEMA-ICS-2-2000-R2020-Controllers-Contactors.md | EXISTS-BOTH | EXT-NEMA-005 |

### Table B — Source PDFs Present, Not Yet Extracted

| Filename | Location | Priority | Why |
|---|---|---|---|
| 839209488-NEMA-ICS-18-MCC.pdf | _Unsorted/ | **HIGH** | Primary MCC application standard — essential for 7.16.2.x |
| ANSI-NEMA-AB-4-2023-Guidelines-Inspection-MCCB.pdf | NEMA/ | LOW | 2023 edition — may overlap with EXT-NEMA-004 (2017 + delta already extracted) |
| acmcc.pdf | Textbooks/Worksheets-Kuphaldt-ECC/ | LOW | Kuphaldt educational worksheet — motor control circuits (139KB, basic) |

### Table C — Missing — Not in corpus at all

| Resource | What it covers | Priority |
|---|---|---|
| **IEEE 1566-2015** — Performance of Adjustable Speed Drive Systems | VFD/ASD performance testing and acceptance | **HIGH** — the primary IEEE VFD testing standard |
| **NEMA ICS-7** (if exists) or equivalent VFD application standard | VFD application and commissioning | MED |
| NEMA MCC-1 / NEMA ICS 18 | MCC application (PDF exists in _Unsorted — extract it) | — |

### acmcc.pdf Location
Found at two locations:
- `Resources/All-About-Circuits/Worksheets/acmcc.pdf` (139,270 bytes)
- `Resources/Source-PDFs/Textbooks/Worksheets-Kuphaldt-ECC/acmcc.pdf` (139,270 bytes)

**Content:** Tony Kuphaldt's "All About Circuits" worksheet on AC motor control circuits. Basic educational material — LOW priority for extraction.

### IEEE 519 (Harmonics) — Extraction Status
- **EXT-IEEE-246**: IEEE 519-2014 Harmonic Control — EXISTS-BOTH in Supabase
- **IEEE-519-1992-Harmonics-Power-Quality.md**: EXISTS-LOCAL extraction file also present
- **Relevance:** HIGH for VFD harmonic impact discussion in guide

### Coverage Assessment: **ADEQUATE**

VFD/MCC topic has a solid core with IEEE 1683 (MCC guide), Eaton MCC manual, NEMA ICS-2/AB-4, and Siemens MV contactor manual. VFD-specific content is thinner — mainly the fact sheet and panel configuration guide. The critical unextracted item is NEMA ICS-18 (MCC standard) in _Unsorted/. MCC sections in NETA are reference-only (point to component test sections), which reduces the extraction burden. IEEE 519 harmonics extraction exists for VFD harmonic discussion.

### Extraction Recommendation
1. **NEMA ICS-18 MCC** (HIGH) — `_Unsorted/839209488-NEMA-ICS-18-MCC.pdf` — critical MCC application standard
2. Consider NEMA AB-4-2023 diff against existing 2017 extraction if significant delta

### Gaps
- IEEE 1566-2015 (ASD performance testing) is not in corpus. Would improve VFD testing depth but is not critical since VFD testing in NETA is primarily functional/commissioning.

---

## TOPIC 4: DC Systems / Batteries (NETA ATS 7.18)

### NETA-Data Status
| Section | Title | VM Tests | EL Tests |
|---------|-------|----------|----------|
| 7.18.1.1 | Batteries, Flooded Lead-Acid (Vented) | 12 | 7 |
| 7.18.1.2 | Batteries, Vented Nickel-Cadmium | 11 | 6 |
| 7.18.1.3 | Batteries, Valve-Regulated Lead-Acid (VRLA) | 10 | 8 |
| 7.18.2 | Chargers | 8 | 9 |
| 7.18.3 | Rectifiers | RESERVED | — |

**Four active sections + one RESERVED. Battery sections well-populated with VM + EL items.**

### Table A — Extracted and in Supabase (usable by CC now)

| content_id | Title | Lines | Relevance |
|---|---|---|---|
| EXT-IEEE-183 | IEEE 450 & 1188 — Complete Battery Testing Guide | 728L | **CORE** — combined battery testing reference |
| EXT-IEEE-238 | IEEE 450-2020 — Vented Lead-Acid Battery Maintenance | 957L | **CORE** — primary VLA battery standard |
| EXT-IEEE-249 | IEEE 1188-2005 — VRLA Battery Maintenance | 789L | **CORE** — primary VRLA battery standard |
| EXT-IEEE-247 | IEEE 484-2019 — Installation Vented Lead-Acid Batteries | 513L | HIGH — VLA installation design |
| EXT-IEEE-248 | IEEE 485-2020 — Sizing Lead-Acid Batteries | 898L | HIGH — battery sizing calculations |
| EXT-IEEE-1184 / EXT-IEEE-155 | IEEE 1184-2022 — Batteries for UPS Systems | 942L | HIGH — UPS battery requirements |
| EXT-IEEE-241 | IEEE 2030.2.1-2019 — Battery Energy Storage Systems | 690L | MED — BESS (modern systems) |
| EXT-IEEE-064 / EXT-IEEE-162 | IEEE 1679.1-2017 — Lithium-Ion Battery Characterization | 225L | MED — Li-Ion evaluation |
| EXT-GOV-002 | FIST 3-6 — Storage Batteries: Maintenance & Principles | 1,285L | **CORE** — Bureau of Reclamation battery field guide |
| EXT-MFR-004 | Pacific Chloride SCR FLX Series Battery Charger IOM | 2,071L | HIGH — practical charger reference |
| EXT-MFR-036 / EXT-MFR-086 | Lithium-Ion Battery U6A4 O&M Manual | 224L | MED — Li-Ion specific |
| EXT-MFR-008 / EXT-MFR-098 | Vertiv EnergyCore Li-Ion Battery Cabinet IOM | 182L | MED — Li-Ion cabinet |
| EXT-MFR-012 / EXT-MFR-100 | Vertiv UPS & Battery Systems — Consolidated Supplementary | 128L | LOW — supplementary |
| EXT-LIB-WP-001 / EXT-MFR-143 | Considerations for Li-Ion Batteries in UPS | 407L | MED — Li-Ion in UPS |

**Supabase total: 14+ extractions (with duplicates) — ~10,000L**

### Local .md Files — Sync Status

| File | Status | Supabase content_id |
|---|---|---|
| FIST-3-6-Storage-Battery-Maintenance.md | EXISTS-BOTH | EXT-GOV-002 |
| SCR-FLX-Series-Battery-Charger-IOM.md | EXISTS-BOTH | EXT-MFR-004 |
| EXT-IEEE-238-IEEE-450-2020-Battery-Maintenance-Testing.md | EXISTS-BOTH | EXT-IEEE-238 |
| EXT-IEEE-241-IEEE-2030.2.1-2019-Battery-Energy-Storage.md | EXISTS-BOTH | EXT-IEEE-241 |
| EXT-IEEE-247-IEEE-484-2019-Vented-Lead-Acid-Batteries.md | EXISTS-BOTH | EXT-IEEE-247 |
| EXT-IEEE-248-IEEE-485-Sizing-Lead-Acid-Batteries.md | EXISTS-BOTH | EXT-IEEE-248 |
| EXT-IEEE-249-IEEE-1188-2005-VRLA-Battery-Maintenance.md | EXISTS-BOTH | EXT-IEEE-249 |
| IEEE-1184-2022-Batteries-UPS-Systems.md | EXISTS-BOTH | EXT-IEEE-1184 |
| IEEE-1679.1-2017-Characterization-Evaluation-LiIon-Batteries.md | EXISTS-BOTH | EXT-IEEE-064 |
| IEEE-450-1188-Battery-Testing.md | EXISTS-BOTH | EXT-IEEE-183 |
| LiIon-Battery-U6A4-OandM-Manual.md | EXISTS-BOTH | EXT-MFR-036 |
| Vertiv-Energycore-LiIon-Battery-Cabinet.md | EXISTS-BOTH | EXT-MFR-008 |
| Vertiv-UPS-Battery-Supplementary.md | EXISTS-BOTH | EXT-MFR-012 |

**All 13 local files are EXISTS-BOTH — fully synced.**

### Table B — Source PDFs Present, Not Yet Extracted

| Filename | Location | Priority | Why |
|---|---|---|---|
| **IEEE-1106-2015-NiCd-Battery-Maintenance.pdf** | **IEEE/** | **CRITICAL** | Primary NiCd battery maintenance/testing standard — 83 pages, covers maintenance procedures, capacity testing, electrolyte management for NiCd batteries *(sorted from _Unsorted/ on 2026-03-18)* |
| Megger-Battery-Testing-Guide.pdf | Textbooks/ | **HIGH** | Practical battery field testing guide — fills "how to test" gap |
| Megger-Station-Battery-Testing-Best-Practices-2011.pdf | Textbooks/ | **HIGH** | Station battery best practices — complements Megger guide above |
| IEEE-1189-2007-VRLA-Battery-Selection.pdf | IEEE/ | MED | Battery selection guide for VRLA |
| IEC-60896-21-22-VRLA-Battery-Standards-Paper.pdf | Textbooks/ | LOW | IEC counterpart to IEEE 1188 — supplementary |
| IEEE-C57.12.58-1991-Semiconductor-Rectifier-Transformer-Guide.pdf | IEEE/ | LOW | Rectifier transformers — 7.18.3 is RESERVED so low urgency |
| IEEE-C57.18.10-1998-Semiconductor-Rectifier-Transformers.pdf | IEEE/ | LOW | Same — rectifier section is RESERVED |
| Safe-Capacity-Test-Battery-WP.pdf | Equipment-Manuals/ | MED | Battery capacity testing white paper |
| Lead-Acid-Battery-Maintenance-Testing-Webinar.pdf | Textbooks/ | LOW | Webinar summary — may overlap existing |
| Understanding-Battery-Maintenance-2018.pdf | Textbooks/ | LOW | General maintenance — overlaps IEEE 450 |

### Table C — Missing — Not in corpus at all

| Resource | What it covers | Priority |
|---|---|---|
| IEEE 1679 (main, not 1679.1) | Battery health assessment framework | MED — broader assessment framework |

> **UPDATE 2026-03-18:** IEEE 1106-2015 located in _Unsorted/ and moved to `Source-PDFs/IEEE/IEEE-1106-2015-NiCd-Battery-Maintenance.pdf`. CRITICAL NiCd gap resolved — now ready for extraction.

### Coverage Assessment: **STRONG** (Lead-Acid) / **THIN** (Nickel-Cadmium)

Battery topic has excellent coverage for lead-acid (VLA + VRLA) with IEEE 450, 1188, 484, 485 all extracted, plus FIST 3-6 field guide and charger manual. Li-Ion coverage is adequate with IEEE 1679.1 and manufacturer manuals. The NiCd gap is now resolved with IEEE 1106-2015 (2,668 KB, 83 pages) available for extraction. Charger coverage (7.18.2) is solid via EXT-MFR-004. Rectifier section (7.18.3) is RESERVED in ATS-2025.

### Extraction Recommendation
1. **IEEE 1106-2015 — NiCd Battery Maintenance** (CRITICAL) — primary NiCd standard, NOW AVAILABLE for extraction
2. **Megger Battery Testing Guide** (HIGH) — practical field testing procedures
3. **Megger Station Battery Testing Best Practices** (HIGH) — companion to above
4. **IEEE 1189-2007 — VRLA Selection** (MED) — adds battery selection guidance

### Gaps
- ~~IEEE 1106 CRITICAL gap~~ — **RESOLVED** (sorted to `IEEE/IEEE-1106-2015-NiCd-Battery-Maintenance.pdf` on 2026-03-18)
- Consider acquiring IEEE 1679 (main) if full battery health assessment framework needed.

---

## SUMMARY COMPARISON

| Topic | Supabase Rows | Local .md | Unextracted PDFs | Critical Gaps | NETA EL Items | Coverage |
|---|---|---|---|---|---|---|
| **1. Motors (7.15)** | 17 | 10 (2 local-only) | 4 | 2 (IEEE 522, NEMA MG 1) | 52 | **STRONG** |
| **2. Capacitors/Reactors (7.20)** | 10 | 4 (all synced) | 10 | 1 (IEEE 1036) | 21+reserved | **THIN → ADEQUATE** *(IEEE 18 gap resolved)* |
| **3. VFDs/MCCs (7.16)** | 9 | 7 (all synced) | 3 | 1 (IEEE 1566) | 22+refs | **ADEQUATE** |
| **4. DC Systems/Batteries (7.18)** | 14+ | 13 (all synced) | 10 | 1 (IEEE 1679) | 38+reserved | **STRONG** *(IEEE 1106 gap resolved)* |

### Recommended Build Order (by resource readiness)

1. **Motors (7.15)** — STRONG coverage, most extraction depth, only needs IEEE 115 extraction
2. **DC Systems/Batteries (7.18)** — STRONG, NiCd gap now resolved with IEEE 1106-2015; extract it and Megger guides then ready to build
3. **VFDs/MCCs (7.16)** — ADEQUATE, needs NEMA ICS-18 extraction; MCC sections are reference-only which simplifies scope
4. **Capacitors/Reactors (7.20)** — ADEQUATE (upgraded from THIN), IEEE 18 now available; needs most extraction work but no longer has critical gaps

### Priority Extractions Before Any Build

| # | Item | Topic | Priority |
|---|---|---|---|
| 1 | **IEEE 18-2012 — Shunt Power Capacitors** | Capacitors | **CRITICAL** |
| 2 | **IEEE 1106-2015 — NiCd Battery Maintenance** | Batteries | **CRITICAL** |
| 3 | IEEE 115 — Synchronous Machine Testing | Motors | HIGH |
| 4 | NEMA ICS-18 (from _Unsorted/) | VFDs/MCCs | HIGH |
| 5 | Megger Battery Testing Guide | Batteries | HIGH |
| 6 | Megger Station Battery Best Practices | Batteries | HIGH |
| 7 | IEEE C57.21 — Shunt Reactors | Capacitors | HIGH |
| 8 | IEEE C57.16 — Current-Limiting Reactors | Capacitors | HIGH |
| 9 | IEEE 1303 — Substation Capacitor Banks | Capacitors | HIGH |
| 10 | Upload local-only files to Supabase (IEEE-43-PI, ATS-100.9-Motors) | Motors | MED |

### Bonus: IEEE 3002.7-2018 — Industrial Power Systems Analysis
Also sorted from `_Unsorted/` to `IEEE/IEEE-3002.7-2018-Industrial-Power-Systems-Analysis.pdf` (7,314 KB). Covers protection coordination analysis for industrial/commercial power systems. Not directly tied to any of the 4 candidate topics but potentially useful for future protection-related guides.
