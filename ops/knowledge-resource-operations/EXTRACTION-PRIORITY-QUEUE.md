# Source Document Extraction Priority Queue
## PDF & Reference Material Status — March 2026

---

## Tracking Correction — March 24, 2026

- This file remains the governed human queue for extraction-task prioritization, but it is not a full filesystem inventory of everything under `Resources/Extractions/`.
- IEEE 1106-2015 (NiCd battery maintenance) is now extracted as `EXT-IEEE-303` at `Resources/Extractions/IEEE/IEEE-1106-2015-NiCd-Battery-Maintenance.md`.
- The earlier March 8 summary line that treated **IEEE C62.22-2009** as the only remaining ETT-relevant gap is still incomplete, but for a different reason now: `C62.22-2009` remains an exam-edition acquisition gap, while the IEEE 1106 extraction dependency has been closed.

---

## Purpose

This document tracks which source PDFs have been extracted, which have not, and the priority order for remaining work. It serves as the authoritative queue for extraction tasks and feeds directly into Phase 5 Supabase migration planning.

**Total source documents on disk:** ~302 PDFs, 133 DOCX, 33 PPTX, 5 EPUB
**Documents with extractions:** ~85 source documents -> 222 extraction files
**Recently closed ETT extraction dependency:** IEEE 1106-2015 (NiCd battery maintenance) — extracted as `EXT-IEEE-303`
**Open exam-edition acquisition gap:** IEEE C62.22-2009 — PDF not on disk
**Last updated:** March 24, 2026 (tracking correction: IEEE 1106 extraction now complete for Guide #31 DC Systems; March 8 queue body retained below as historical detail until a full queue refresh is performed.)

---

## ✅ EXTRACTED — NEW ACQUISITIONS (March 7, 2026) — ALL 4/4 COMPLETE

Exam-reference edition updates + HV insulation textbook. Task file: `Development/TASK-CC-EXTRACT-EXAM-EDITION-UPDATES.md`

| # | Document | Extraction File | Content ID | Lines | Words | Status |
|---|----------|----------------|------------|------:|------:|--------|
| **E1** | IEEE C62.11-2020 (Surge Arresters) | `Extractions/IEEE/IEEE-C62.11-2020-Surge-Arresters.md` | **EXT-IEEE-051** | 1,417 | 11,255 | ✅ COMPLETE |
| **E2** | IEEE C37.23-2015 (Metal-Enclosed Bus) | `Extractions/IEEE/IEEE-C37.23-2015-Metal-Enclosed-Bus.md` | **EXT-IEEE-052** | 1,050 | 10,697 | ✅ COMPLETE |
| **E3** | James & Su — HV Insulation Condition Assessment (2008) | `Extractions/Textbooks/James-Su-HV-Insulation-Condition-Assessment.md` | **EXT-IND-016** | 1,529 | 9,815 | ✅ COMPLETE |
| **E4** | Glover, Sarma & Overbye — Power Systems Analysis 5e (selective) | `Extractions/Textbooks/Glover-Power-System-Analysis-Selective.md` | **EXT-IND-017** | 875 | 4,168 | ✅ COMPLETE |

**Total: 4,871 lines, 35,935 words across 4 extraction files.**

**Exam-reference edition gaps status:**
- ✅ IEEE C62.11-2020 — EXTRACTED as EXT-IEEE-051 (1,417 lines). Supersedes 1999 OCR extraction.
- ✅ IEEE C37.23-2015 — EXTRACTED as EXT-IEEE-052 (1,050 lines). Supersedes EXT-IEEE-037 (1987).
- ❌ IEEE C62.22-2009 — PDF NOT found. Only 1997 edition on disk. **GAP STILL OPEN.**

**Cross-references added:** Notes pointing to new extractions added to IEEE-C62.11-1999-Surge-Arresters.md, IEEE-C37.23-1987-Metal-Enclosed-Bus.md, and Stevenson (EXT-IND-013).

**Also obtained but NOT requiring extraction (equipment manuals — 32 files):**
Manufacturer manuals moved to `Source-PDFs/Equipment-Manuals/` for reference. See `Development/NEW-PDF-CATALOG-MAR8.md` for full inventory (45 items total).

**Also registered in standards-registry.json (no extraction needed):**
- IEEE C62.92.1-2016 (Neutral Grounding Part I) — not exam-referenced
- IEEE C93.3-2017 (Power Line Carrier Line Traps) — not exam-referenced
- IEEE C37.63-2013 (Automatic Line Sectionalizers) — not exam-referenced
- NEMA 250-2020 (Enclosures for Electrical Equipment) — EXT-NEMA-006
- NEMA ICS 2-2000 (R2020) (Controllers and Contactors) — EXT-NEMA-005
- IEC 62040-1-1:2002 (UPS Safety Requirements) — not exam-referenced

---

## Extraction Status Summary

| Status | Count | Notes |
|--------|-------|-------|
| ✅ Fully extracted | 80 | ATS, MTS, ETT, ECS, Paul Gill, NFPA 70E, OSHA (×2), SD-Meyers, Formulae Sheet, NETA Ref List, Red Book, GE GEI-48907, Megger LR, Megger IR, NETA Exam Content Outline, NETA Study Guide 2023, NETA Quiz Questions, NETA Handbook III Vol 3, IEEE 400.3-2022, IEEE C57.19.00-2004, IEEE C57.93-2019, IEEE C57.113-2023, OMICRON CB Testing, PG&E TD-3322M, **ETT NETA (28 files)**, **former mixed intake complete (10 files)**, **H1-H8: IEEE 519, 242, 80, 142, C57.12.00, C57.12.90, C57.13, C57.15, 95, 315, 644**, **NECA/FOA 301-2016, Demystifying Fiber Test Methods**, **M-tier complete: EXT-FLD-001→011 (11 files)**, **Exam-edition batch: C62.11-2020, C37.23-2015, James & Su, Glover (selective)** |
| ⚠️ Partially extracted | 3 | PEARL L2 (4/12 ch.), IEEE Color Books (8/12), ATS/MTS section PDFs (covered by full) |
| ❌ Not extracted (CRITICAL) | 1 | C4 already completed — only row kept for reference |
| ❌ Not extracted (HIGH) | 0 | All HIGH items complete (H1-H8) |
| ❌ Not extracted (MEDIUM) | 4 | Partially extracted, manufacturer manuals |
| ❌ Not extracted (LOW) | ~12 | Tangential, dated, or redundant |
| ⬜ Bulk reference (no extraction needed) | ~150+ | Individual ATS/MTS table PDFs, DOCX section files — already covered by full standard extractions |

---

## ✅ COMPLETED EXTRACTIONS

| # | Source Document | Extraction Location | Files | Quality |
|---|----------------|---------------------|-------|---------|
| 1 | ANSI/NETA ATS-2025 | `Extractions/NETA-Standards/` + `ATS-2025/` | 21 + 2 (JSON/MD) | ⭐ HIGH |
| 2 | ANSI/NETA MTS-2023 | `Extractions/NETA-Standards/` + `MTS-2023/` | 18 + 2 (JSON/MD) | ⭐ HIGH |
| 3 | ANSI/NETA ETT-2022 | `Extractions/NETA-Standards/` + `ETT-2022/` | 4 + 1 (JSON) | ⭐ HIGH |
| 4 | ANSI/NETA ECS-2024 | `Extractions/NETA-Standards/` | 1 (JSON) | ✅ GOOD |
| 5 | Paul Gill — EPEMT | `Extractions/Paul-Gill/CURATED/` + `RAW/` | 15 + 15 | ⭐ GOLD |
| 6 | NFPA 70E-2024 | `Extractions/NFPA-70E/` | 7 | ✅ GOOD |
| 7 | OSHA 1910 (Gen Industry) | `Extractions/OSHA/` | 3 | ✅ GOOD |
| 8 | OSHA 1926 (Construction) | `Extractions/OSHA/` | 2 | ✅ GOOD |
| 9 | SD-Meyers Fluid Testing eBook | `Extractions/SD-Meyers/` | 1 | ⭐ GOLD |
| 10 | Official Electrical Formulae Sheet | `Extractions/Exam-Resources/` | 1 | ⚠️ MINIMAL |
| 11 | PEARL Level 2 Handbook | `Extractions/PEARL/` | 4 (of ~12 chapters) | ⚠️ PARTIAL |
| 12 | IEEE Color Books (12 PDFs) | `Extractions/IEEE/` | 8 summaries | ⚠️ PARTIAL |
| 13 | NETA ETT Exam Reference List | `Extractions/Exam-Resources/NETA-ETT-Exam-Reference-List-2023.md` | 1 | ⭐ HIGH |
| 14 | IEEE 141-1993 (Red Book) | `Extractions/IEEE/IEEE-141-Red-Book-Equipment-Guide.md` | 1 (6 chapters) | ⭐ HIGH |
| 15 | GE GEI-48907 (GFP) | `Extractions/Manufacturer/GE-GEI-48907-Ground-Fault-Protection.md` | 1 | ⭐ HIGH |
| 16 | Megger Low Resistance Testing | `Extractions/Megger/Megger-Low-Resistance-Testing-Guide.md` | 1 | ⭐ HIGH |
| 17 | Megger Insulation Testing (67p) | `Extractions/Megger/Megger-Insulation-Testing-Complete-Guide.md` | 1 | ⭐ HIGH |
| 18 | NETA Exam Content Outline | `Extractions/Exam-Resources/NETA-ETT-Exam-Content-Outline.md` | 1 | ⭐ HIGH |
| 19 | NETA Study Guide 2023 | `Extractions/Exam-Resources/NETA-ETT-Study-Guide-2023.md` | 1 | ⭐ HIGH |
| 20 | NETA Quiz Questions | `Extractions/Exam-Resources/NETA-ETT-Quiz-Questions-2023.md` | 1 | ⭐ HIGH |
| 21 | NETA Handbook Series III, Vol 3 | `Extractions/NETA-Handbooks/NETA-Handbook-Series-III-Vol3.md` | 1 | ⭐ HIGH |
| 22 | IEEE 400.3-2022 (PD Cable Testing) | `Extractions/IEEE/IEEE-400.3-2022-PD-Cable-Testing.md` | 1 | ⭐ HIGH |
| 23 | IEEE C57.19.00-2004 (Bushings) | `Extractions/IEEE/IEEE-C57.19.00-2004-Bushings.md` | 1 | ⭐ HIGH |
| 24 | IEEE C57.93-2019 (Transformer Install/Maint) | `Extractions/IEEE/IEEE-C57.93-2019-Transformer-Install-Maint.md` | 1 | ⭐ HIGH |
| 25 | IEEE C57.113-2023 (Transformer PD) | `Extractions/IEEE/IEEE-C57.113-2023-Transformer-PD.md` | 1 | ⭐ HIGH |
| 26 | OMICRON HV CB Testing Systematic | `Extractions/Manufacturer/OMICRON-HV-CB-Testing-Systematic.md` | 1 | ⭐ HIGH |
| 27 | PG&E TD-3322M CB Maintenance | `Extractions/Manufacturer/PGE-TD-3322M-CB-Maintenance.md` | 1 | ⭐ HIGH |
| | **ETT Study Aids — Phase 1: Gap Closure** | | | |
| 28 | ETT Busways/Outdoor Bus Fact Sheet | `Extractions/ETT-Study-Aids/Busways-Outdoor-Bus-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 29 | ETT Network Protector Fact Sheet | `Extractions/ETT-Study-Aids/Network-Protector-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 30 | ETT Rotating Machinery Fact Sheet | `Extractions/ETT-Study-Aids/Rotating-Machinery-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 31 | ETT VFD Fact Sheet | `Extractions/ETT-Study-Aids/VFD-Fact-Sheet.md` | 1 | ⭐ HIGH |
| | **ETT Study Aids — Phase 2: Practice Exams** | | | |
| 32 | ETT L2 Practice Exam | `Extractions/ETT-Study-Aids/L2-Practice-Exam.md` | 1 | ⭐ HIGH |
| 33 | ETT L2 Practice Exam Answer Key | `Extractions/ETT-Study-Aids/L2-Practice-Exam-Answer-Key.md` | 1 | ⭐ HIGH |
| 34 | ETT L2/L3 Study Guide | `Extractions/ETT-Study-Aids/L2-L3-Study-Guide.md` | 1 | ⭐ HIGH |
| 35 | ETT L2/L3 Study Guide Answer Key | `Extractions/ETT-Study-Aids/L2-L3-Study-Guide-Answer-Key.md` | 1 | ⭐ HIGH |
| 36 | ETT L3 Math Help | `Extractions/ETT-Study-Aids/L3-Math-Help.md` | 1 | ⭐ HIGH |
| 37 | ETT Math Study Guide Answers | `Extractions/ETT-Study-Aids/Math-Study-Guide-Answers.md` | 1 | ⭐ HIGH |
| | **ETT Study Aids — Phase 3: Depth** | | | |
| 38 | ETT Cable Insulation Fact Sheet | `Extractions/ETT-Study-Aids/Cable-Insulation-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 39 | ETT Capacitor/Reactor Fact Sheet | `Extractions/ETT-Study-Aids/Capacitor-Reactor-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 40 | ETT Circuit Breakers Fact Sheet | `Extractions/ETT-Study-Aids/Circuit-Breakers-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 41 | ETT Current Testing Fact Sheet | `Extractions/ETT-Study-Aids/Current-Testing-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 42 | ETT Emergency Systems Fact Sheet | `Extractions/ETT-Study-Aids/Emergency-Systems-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 43 | ETT Electrical Fundamentals Fact Sheet | `Extractions/ETT-Study-Aids/Electrical-Fundamentals-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 44 | ETT Fuse Class Fact Sheet | `Extractions/ETT-Study-Aids/Fuse-Class-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 45 | ETT Ground Fault Systems Fact Sheet | `Extractions/ETT-Study-Aids/Ground-Fault-Systems-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 46 | ETT Instrument Transformers Fact Sheet | `Extractions/ETT-Study-Aids/Instrument-Transformers-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 47 | ETT Insulating Fluid Fact Sheet | `Extractions/ETT-Study-Aids/Insulating-Fluid-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 48 | ETT AC Insulation Testing Fact Sheet | `Extractions/ETT-Study-Aids/AC-Insulation-Testing-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 49 | ETT DC Insulation Testing Fact Sheet | `Extractions/ETT-Study-Aids/DC-Insulation-Testing-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 50 | ETT Protective Relaying Fact Sheet | `Extractions/ETT-Study-Aids/Protective-Relaying-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 51 | ETT Resistance Testing Fact Sheet | `Extractions/ETT-Study-Aids/Resistance-Testing-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 52 | ETT Safety Fact Sheet | `Extractions/ETT-Study-Aids/Safety-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 53 | ETT System Test Analysis Fact Sheet | `Extractions/ETT-Study-Aids/System-Test-Analysis-Fact-Sheet.md` | 1 | ⭐ HIGH |
| 54 | ETT Transformer Fact Sheet | `Extractions/ETT-Study-Aids/Transformer-Fact-Sheet.md` | 1 | ⭐ HIGH |
| | **ETT Study Aids — Phase 4: CCVT** | | | |
| 55 | ETT CCVT Testing Fact Sheet | `Extractions/ETT-Study-Aids/CCVT-Testing-Fact-Sheet.md` | 1 | ⭐ HIGH |

**ETT NETA Supabase:** All 28 files loaded with content IDs `EXT-001` through `EXT-028`. 1,182 new KSA-content links discovered (total: 4,132). `study_content` table: 301 rows.

| | **Former Mixed Intake — Depth Enhancement (Feb 28, 2026)** | | | |
| 56 | IEEE 1584-2018 (Arc-Flash Calculations) | `Extractions/IEEE/IEEE-1584-2018-Arc-Flash-Calculations.md` | 1 | ⭐ HIGH |
| 57 | IEEE 62.2-2004 (Diagnostic Machinery Testing) | `Extractions/IEEE/IEEE-62.2-2004-Diagnostic-Machinery-Testing.md` | 1 | ⭐ HIGH |
| 58 | IEEE 112-2004 (Induction Motor Testing) | `Extractions/IEEE/IEEE-112-2004-Induction-Motor-Testing.md` | 1 | ⭐ HIGH |
| 59 | IEEE 575-1988 (Cable Shield Bonding) | `Extractions/IEEE/IEEE-575-1988-Cable-Shield-Bonding.md` | 1 | ⭐ HIGH |
| 60 | Symmetrical Fault Analysis (Short Circuit Study) | `Extractions/Industry-Guides/Symmetrical-Fault-Analysis-Short-Circuit.md` | 1 | ⭐ HIGH |

| 61 | IEEE 3001.8-2013 (Instrumentation & Metering) | `Extractions/IEEE/IEEE-3001.8-2013-Instrumentation-Metering.md` | 1 | ⭐ HIGH |
| 62 | IEC 62196-1:2003 (EV Charging Connectors) | `Extractions/Industry-Guides/IEC-62196-1-2003-EV-Charging-Connectors.md` | 1 | ⭐ HIGH |
| 63 | IEEE C37.41-2008 (HV Fuse Design Tests) | `Extractions/IEEE/IEEE-C37.41-2008-HV-Fuse-Design-Tests.md` | 1 | ⭐ HIGH |
| 64 | IEEE C57.104-1991 (DGA Guide — Original) | `Extractions/IEEE/IEEE-C57.104-1991-DGA-Guide-Original.md` | 1 | ⭐ HIGH |
| 65 | IEEE C57.104-2019 (DGA Guide — Current) | `Extractions/IEEE/IEEE-C57.104-2019-DGA-Guide-Current.md` | 1 | ⭐ HIGH |

**Former mixed intake Supabase:** All 10 files loaded with content IDs `EXT-IEEE-016` through `EXT-IEEE-023` + `EXT-IND-001` + `EXT-IND-002`. 196 total new KSA links. `study_content` table: 311 rows. Coverage: SF 100%, CT 99% (4 gaps), ET 100%, SC 100%.

| | **IEEE C37 Batch — March 1, 2026** | | | |
| 66 | IEEE C37.016-2018 (AC HV Circuit Switchers) | `Extractions/IEEE/IEEE-C37.016-2018-Circuit-Switchers.md` | 1 — `EXT-IEEE-035` | ⭐ HIGH |
| 67 | IEEE C37.104-2022 (Automatic Reclosing) | `Extractions/IEEE/IEEE-C37.104-2022-Automatic-Reclosing.md` | 1 — `EXT-IEEE-036` | ⭐ HIGH |
| 68 | IEEE C37.230-2020 (Distribution Line Protection) | `Extractions/IEEE/IEEE-C37.230-2020-Distribution-Protection.md` | 1 — `EXT-IEEE-037` | ⭐ HIGH |
| 69 | IEEE C37.246-2017 (Transmission-Generation Protection) | `Extractions/IEEE/IEEE-C37.246-2017-Transmission-Generation-Protection.md` | 1 — `EXT-IEEE-038` | ⭐ HIGH |
| 70 | IEEE C37.37-1996 (Air Switch Loading Guide) | `Extractions/IEEE/IEEE-C37.37-1996-Air-Switch-Loading.md` | 1 — `EXT-IEEE-039` | ⭐ HIGH |

**C37 Batch:** 5 standards extracted and loaded to Supabase (EXT-IEEE-035 through EXT-IEEE-039). KSA relevance: CT-028–CT-031 (circuit switchers), Component Testing (reclosing, distribution protection, air switches), Systems & Commissioning (protection coordination, generation interconnections).

---

## ✅ UNEXTRACTED — CRITICAL (Tier 1) — ALL COMPLETED

All direct exam preparation materials have been extracted as of February 28, 2026.

| # | Document | Status | Output Location |
|---|----------|--------|----------------|
| **C1** | NETA Exam Content Outline | ✅ EXTRACTED + LOADED | `Extractions/Exam-Resources/NETA-ETT-Exam-Content-Outline.md` — Supabase: `EXT-NETA-EXAM-OUTLINE` |
| **C2** | NETA Study Guide 2023 | ✅ EXTRACTED + LOADED | `Extractions/Exam-Resources/NETA-ETT-Study-Guide-2023.md` — Supabase: `EXT-NETA-STUDY-GUIDE` |
| **C3** | NETA Quiz Questions | ✅ EXTRACTED (not loaded — goes to `study_questions` table later) | `Extractions/Exam-Resources/NETA-ETT-Quiz-Questions-2023.md` |
| **C4** | ~~NETA ETT Exam Reference List~~ | ✅ COMPLETED (prior sprint) | `Extractions/Exam-Resources/NETA-ETT-Exam-Reference-List-2023.md` |
| **C5** | NETA Handbook Series III, Vol 3 | ✅ EXTRACTED + LOADED | `Extractions/NETA-Handbooks/NETA-Handbook-Series-III-Vol3.md` — Supabase: `EXT-NETA-HANDBOOK-III` |

**Discovery scan results:** 82 new KSA-content links inserted (37 STRONG + 45 MODERATE). Coverage: SF 100%, CT 92% (27 gaps remain), ET 100%, SC 100%.

---

## ❌ UNEXTRACTED — HIGH (Tier 2)

IEEE standards and key references that fill identified KSA gaps.

| # | Document | Location | KSA Gap Addressed | Levels | Est. Effort |
|---|----------|----------|-------------------|--------|-------------|
| ~~**H1**~~ | ~~IEEE 519-1992 (Power Quality/Harmonics)~~ | `Extractions/IEEE/IEEE-519-1992-Harmonics-Power-Quality.md` | ✅ EXTRACTED + LOADED — 713 lines, `EXT-IEEE-024`. Enriches: ET-017, ET-027, ET-028 | III | ~~3-4 hrs~~ |
| ~~**H2**~~ | ~~IEEE 242-2001 (Buff Book — Protection & Coordination)~~ | `Extractions/IEEE/IEEE-242-2001-Buff-Book-Protection-Coordination.md` | ✅ EXTRACTED + LOADED — 1,633 lines, `EXT-IEEE-025`. Protection coordination, TCC analysis | III | ~~3-4 hrs~~ |
| ~~**H3**~~ | ~~IEEE 80-2000 (Substation Grounding)~~ | `Extractions/IEEE/IEEE-80-2000-Substation-Grounding.md` | ✅ EXTRACTED + LOADED — 904 lines, `EXT-IEEE-026`. Substation ground grid design + testing | III | ~~4-6 hrs~~ |
| ~~**H4**~~ | ~~IEEE 142-2007 (Green Book — Grounding)~~ | `Extractions/IEEE/IEEE-142-2007-Green-Book-Grounding.md` | ✅ EXTRACTED + LOADED — 948 lines, `EXT-IEEE-027`. Updated grounding | III | ~~2-3 hrs~~ |
| ~~**H5**~~ | ~~IEEE C57.xx collection (4 standards)~~ | `Extractions/IEEE/` | ✅ EXTRACTED + LOADED — C57.12.00 (1,244 lines, `EXT-IEEE-028`), C57.12.90 (1,217 lines, `EXT-IEEE-029`), C57.13 (1,284 lines, `EXT-IEEE-030`), C57.15 (1,351 lines, `EXT-IEEE-031`) | III | ~~6-8 hrs~~ |
| ~~**H6**~~ | ~~IEEE 95 (Motor Insulation)~~ | `Extractions/IEEE/IEEE-95-Motor-Insulation-Testing.md` | ✅ EXTRACTED + LOADED — 543 lines, `EXT-IEEE-032`. Motor hi-pot, I-V curves, insulation testing | III | ~~2-3 hrs~~ |
| ~~**H7**~~ | ~~IEEE 315-1975 (Graphic Symbols)~~ | `Extractions/IEEE/IEEE-315-1975-Graphic-Symbols.md` | ✅ EXTRACTED + LOADED — 1,030 lines, `EXT-IEEE-033`. Schematic literacy symbol catalog, class designation letters | II, III, IV | ~~2-3 hrs~~ |
| ~~**H8**~~ | ~~IEEE 644-2008 (EMF Measurement)~~ | `Extractions/IEEE/IEEE-644-2008-EMF-Measurement.md` | ✅ EXTRACTED + LOADED — 492 lines, `EXT-IEEE-034`. EMF measurement procedures | III | ~~1-2 hrs~~ |
| ~~**H9**~~ | ~~IEEE 3001.8-2013 (Instrumentation & Metering)~~ | `Extractions/IEEE/IEEE-3001.8-2013-Instrumentation-Metering.md` | ✅ EXTRACTED + LOADED — 684 lines, `EXT-IEEE-020`. Gap closure: KSA-IV-CT-044 to 047 | IV | ~~1-2 hrs~~ |
| ~~**H10**~~ | ~~IEC 62196-1:2003 (EV Charging Connectors)~~ | `Extractions/Industry-Guides/IEC-62196-1-2003-EV-Charging-Connectors.md` | ✅ EXTRACTED + LOADED — 910 lines, `EXT-IND-002`. Gap closure: KSA-IV-CT-110 to 113 | IV | ~~2-3 hrs~~ |
| ~~**H11**~~ | ~~IEEE C37.41-2008 (HV Fuse Design Tests)~~ | `Extractions/IEEE/IEEE-C37.41-2008-HV-Fuse-Design-Tests.md` | ✅ EXTRACTED + LOADED — 717 lines, `EXT-IEEE-021`. Partial gap closure: KSA-IV-CT-109 | IV | ~~2-3 hrs~~ |

**Total estimated effort: 2-3 hours remaining (H1-H6+H8 complete: 10,329 lines extracted, only H7 remains)**

---

## ❌ UNEXTRACTED — MEDIUM (Tier 3)

Manufacturer guides and supplementary field references. Valuable for Field-Tip and Calculation-Example content.

| # | Document | Location | Content Value | Est. Effort |
|---|----------|----------|---------------|-------------|
| **M1** | ~~Megger Guide to Insulation Testing~~ | `Source-PDFs/NEW/` | ✅ COMPLETED — `Extractions/Megger/Megger-Insulation-Testing-Complete-Guide.md` | ~~2-3 hrs~~ |
| **M2** | ~~Megger Guide to Low Resistance Testing~~ | `Source-PDFs/NEW/` | ✅ COMPLETED — `Extractions/Megger/Megger-Low-Resistance-Testing-Guide.md` | ~~1-2 hrs~~ |
| **M3** | ~~Guide to Transformer Resistance Testing~~ | `Extractions/Megger/Megger-Transformer-Resistance-Testing-Guide.md` | ✅ EXTRACTED + LOADED — 489 lines, `EXT-FLD-001`. Winding resistance practical guide | ~~1-2 hrs~~ |
| **M4** | ~~Protective Relay Manual~~ | `Extractions/Manufacturer/Protective-Relay-Course-Manual.md` | ✅ EXTRACTED + LOADED — 608 lines, `EXT-FLD-007`. Relay testing reference — complements Paul Gill Ch. 9 | ~~3-4 hrs~~ |
| **M5** | ~~Transformers Manual~~ | `Extractions/Manufacturer/Transformers-Course-Manual.md` | ✅ EXTRACTED + LOADED — 586 lines, `EXT-FLD-002`. Transformer testing field reference | ~~2-3 hrs~~ |
| **M6** | ~~L&MV Circuit Breaker Maintenance~~ | `Extractions/Manufacturer/LMVV-Circuit-Breaker-Maintenance-Manual.md` | ✅ EXTRACTED + LOADED — 666 lines, `EXT-FLD-008`. Breaker maintenance procedures | ~~2-3 hrs~~ |
| **M7** | ~~Ground Fault Protection System Manual~~ | `Source-PDFs/NEW/` | ✅ COMPLETED — `Extractions/Manufacturer/GE-GEI-48907-Ground-Fault-Protection.md` | ~~1-2 hrs~~ |
| **M8** | ~~Electrical Diagram Analysis~~ | `Extractions/Manufacturer/Electrical-Diagram-Analysis-Manual.md` | ✅ EXTRACTED + LOADED — 592 lines, `EXT-FLD-009`. Schematic reading skills — Level II foundation | ~~1-2 hrs~~ |
| **M9** | ~~Getting Down to Earth~~ | `Extractions/Megger/Megger-Getting-Down-to-Earth-Grounding-Guide.md` | ✅ EXTRACTED + LOADED — 490 lines, `EXT-FLD-010`. Grounding reference (classic Megger guide) | ~~2-3 hrs~~ |
| **M10** | ~~VIDAR DC Vacuum Integrity Testing~~ | `Extractions/Megger/Megger-VIDAR-Vacuum-Integrity-Testing.md` | ✅ EXTRACTED + LOADED — 213 lines, `EXT-FLD-003`. MV vacuum breaker testing — niche but exam-relevant | ~~1 hr~~ |
| **M11** | ~~Capacitor Field Testing~~ | `Extractions/Manufacturer/Capacitor-Field-Testing-Guide.md` | ✅ EXTRACTED + LOADED — 313 lines, `EXT-FLD-004`. Power factor capacitor testing | ~~1 hr~~ |
| **M12** | ~~A Stitch in Time (insulation testing)~~ | Historical provenance only | ✅ SUPERSEDED — covered by M1 (67-page expanded edition) | ~~2-3 hrs~~ |
| **M13** | ~~The Art and Science of Protective Relaying~~ | `Extractions/Manufacturer/Art-Science-Protective-Relaying.md` | ✅ EXTRACTED + LOADED — 826 lines, `EXT-FLD-011`. Definitive GE relay reference (357 pages, 15 chapters) | ~~3-4 hrs~~ |
| **M14** | ~~Oil Sample Definitions-Recommendations~~ | `Extractions/Manufacturer/Oil-Sample-Definitions-Recommendations.md` | ✅ EXTRACTED + LOADED — 581 lines, `EXT-FLD-005`. Supplements SD-Meyers extraction | ~~1 hr~~ |
| **M15** | ~~XFMR TESTING~~ | `Extractions/Manufacturer/XFMR-Testing-Field-Notes.md` | ✅ EXTRACTED + LOADED — 464 lines, `EXT-FLD-006`. BPA transformer testing field guide | ~~1 hr~~ |

**Total estimated effort: 24-36 hours**

---

## ✅ EXTRACTED — MEDIUM+ (Tier 2.5 — Former Mixed Intake) — ALL 10/10 COMPLETE Feb 28, 2026

All 10 items (5 depth + 2 gap-closure + 1 partial gap + 2 DGA depth) extracted and loaded to Supabase. 196 total new KSA links discovered.

| # | Document | Location | Content Value | Status |
|---|----------|----------|---------------|--------|
| **N1** | IEEE 1584-2018 (Arc-Flash Hazard Calculations) | `Extractions/IEEE/IEEE-1584-2018-Arc-Flash-Calculations.md` | 864 lines, `EXT-IEEE-016` | ✅ EXTRACTED + LOADED |
| **N2** | IEEE 62.2-2004 (Diagnostic Field Testing Machinery) | `Extractions/IEEE/IEEE-62.2-2004-Diagnostic-Machinery-Testing.md` | 825 lines, `EXT-IEEE-017` | ✅ EXTRACTED + LOADED |
| **N3** | IEEE 112-2004 (Polyphase Induction Motor Testing) | `Extractions/IEEE/IEEE-112-2004-Induction-Motor-Testing.md` | 898 lines, `EXT-IEEE-018` | ✅ EXTRACTED + LOADED |
| **N4** | IEEE 575-1988 (Cable Shield & Sheath Bonding) | `Extractions/IEEE/IEEE-575-1988-Cable-Shield-Bonding.md` | 816 lines, `EXT-IEEE-019` | ✅ EXTRACTED + LOADED |
| **N5** | Symmetrical Fault Analysis (Short Circuit Study) | `Extractions/Industry-Guides/Symmetrical-Fault-Analysis-Short-Circuit.md` | 912 lines, `EXT-IND-001` | ✅ EXTRACTED + LOADED |
| ~~N6~~ | ~~IEEE 3001.8-2013 (Instrumentation & Metering)~~ | `Source-PDFs/IEEE/` | **Promoted to H9** -- Gap closure: KSA-IV-CT-044 to 047 | ~~PROMOTED~~ |
| ~~N7~~ | ~~IEC 62196-1:2003 (EV Charging Connectors)~~ | `Source-PDFs/IEEE/` | **Promoted to H10** -- Gap closure: KSA-IV-CT-110 to 113 | ~~PROMOTED~~ |
| ~~**N8**~~ | ~~IEEE C37.41-2008 (HV Fuse Design Tests)~~ | `Extractions/IEEE/IEEE-C37.41-2008-HV-Fuse-Design-Tests.md` | ✅ EXTRACTED + LOADED — 717 lines, `EXT-IEEE-021` (promoted to H11) | ✅ COMPLETE |
| **N9** | IEEE C57.104-1991 (DGA Guide — original) | `Extractions/IEEE/IEEE-C57.104-1991-DGA-Guide-Original.md` | ✅ EXTRACTED + LOADED — 632 lines, `EXT-IEEE-022` | ✅ COMPLETE |
| **N10** | IEEE C57.104-2019 (DGA Guide — current) | `Extractions/IEEE/IEEE-C57.104-2019-DGA-Guide-Current.md` | ✅ EXTRACTED + LOADED — 687 lines, `EXT-IEEE-023` | ✅ COMPLETE |

**Total extracted: 6,351 lines across 10 files (all former mixed intake items complete). Supabase: 311 rows. KSA coverage: SF 100%, CT 99% (4 gaps), ET 100%, SC 100%.**

---

## ❌ UNEXTRACTED — LOW (Tier 4)

Tangential, dated, or largely redundant with existing extractions.

| # | Document | Location | Notes |
|---|----------|----------|-------|
| L1 | PEARL Level 1 Handbook | `Source-PDFs/PEARL/` | Pre-NETA foundation level |
| L2 | PEARL Level 3 Handbook | `Source-PDFs/PEARL/` | Some overlap with existing L3 content |
| L3 | PEARL Level 1 Exam Info Guide | `Source-PDFs/PEARL/` | Exam format info only |
| L4 | NETA Practice Exam Instructions | `Source-PDFs/Exam-Resources/` | Procedural — low content value |
| L5 | dcos2_22_17.pdf | `Source-PDFs/Exam-Resources/` | **Unknown content — needs identification** |
| L6 | OSHA 4472 | `Source-PDFs/NFPA-OSHA/` | Supplemental OSHA guide |
| L7 | NFPA 99-18 | `Source-PDFs/NFPA-OSHA/` | Healthcare facility electrical — very low ETT relevance |
| L8 | NFPA 70E-2012 | Historical provenance only | Outdated — 2024 edition already extracted |
| L9 | PerUnitCalculations.pdf | Historical provenance only | Per-unit calcs — L3/L4 relevant but narrow |
| L10 | ~~IEEE 112, 115 (motor standards)~~ | Historical provenance only | IEEE 112 now in former mixed intake batch (N3); IEEE 115 low priority |
| L11 | Doble Training (16 seminar PDFs) | Historical provenance only | Transformer PF/DGA training — supplements Paul Gill Ch. 3-5 |
| L12 | EIT exam materials (14 PDFs) | Historical provenance only | FE exam prep — negligible NETA overlap |

---

## ⚠️ PARTIALLY EXTRACTED — Completion Needed

| # | Document | Current State | Remaining Work | Est. Effort |
|---|----------|---------------|----------------|-------------|
| **P1** | PEARL Level 2 Handbook | 4 chapters extracted | ~8 chapters remain (Test Equipment through Systems) | 4-6 hrs |
| **P2** | IEEE Color Books (12 PDFs) | 8 summary files + Red Book equipment guide | 3 books missing: Gray (241), Emerald (1100), White (602) — Red (141) now extracted | 1-2 hrs |
| **P3** | NFPA 70E-2024 | 7 files (3 tables + 4 articles) | Missing: Article 120 complete ESWC, Article 110, additional tables | 2-3 hrs |
| **P4** | Official Electrical Formulae Sheet | 1 minimal extraction | Needs full formula-by-formula structured extraction | 2-3 hrs |

**Total estimated effort: 10-15 hours**

---

## ⬜ NO EXTRACTION NEEDED

These files are covered by existing extractions or serve reference-only purposes:

| Category | Count | Reason |
|----------|-------|--------|
| ATS 2025 Table Extraction PDFs | 50 | Individual table PDFs — covered by 21 ATS-2025 markdown extractions |
| MTS 2023 Table Extraction PDFs | 57 | Individual table PDFs — covered by 18 MTS-2023 markdown extractions |
| NETA ATS .docx section files | 68 | Section-level Word docs — covered by full ATS standard extraction |
| NETA MTS .docx section files | 65 | Section-level Word docs — covered by full MTS standard extraction |
| Testing Resources/Classes (.pptx) | 33 | PowerPoint training slides — assess if needed later |
| Epub files | 5 | Circuit analysis basics — foundation only, low priority |
| ANSI/NETA ECS-2024 (duplicate) | 1 | Duplicate in NFPA & OSHA folder — already extracted from NETA-Standards copy |

---

## Recommended Extraction Sequence

### Sprint 1: Exam Materials (Tier 1 — CRITICAL) ✅ COMPLETED Feb 28, 2026
**Goal:** Extract all direct exam preparation materials
**Documents:** C1–C5 — ALL EXTRACTED
**Actual effort:** ~10-12 hours (C1, C2, C3, C5 extracted; C4 was already done)
**Impact:** 82 new KSA-content links discovered. C1 exam structure mapped. C3 provides 200+ practice questions. C5 revealed maintenance handbook (not arc-flash as previously thought).

### Sprint 2: Completion + KSA Gap Fill
**Goal:** Complete partial extractions + fill highest-KSA-impact IEEE standards  
**Documents:** P1–P4 (completions) + H1 (IEEE 519) + H2 (IEEE 242)  
**Effort:** 16-22 hours  
**Impact:** Closes harmonics/PQ/protection KSA gaps, completes PEARL and NFPA-70E

### Sprint 3: IEEE Standards Deep Dive
**Goal:** Fill remaining IEEE standard gaps  
**Documents:** H3–H8  
**Effort:** 18-25 hours  
**Impact:** Comprehensive IEEE coverage for Supabase `extractions` table

### Sprint 4: Field Reference Library
**Goal:** Extract manufacturer/field guides for practical content  
**Documents:** M1–M15  
**Effort:** 24-36 hours  
**Impact:** Rich Field-Tip and Calculation-Example content for study guides

### Sprint 5: Remaining & Cleanup
**Goal:** Assess and extract remaining low-priority sources  
**Documents:** L1–L12 (selective)  
**Effort:** 10-20 hours  
**Impact:** Completeness; identify L5 (unknown PDF)

---

## Cross-Reference: KSA Equipment Gaps vs. Source Availability

| Equipment Gap | KSAs Affected | Source Available? | Priority Doc |
|---------------|---------------|-------------------|-------------|
| VFDs/Drives | CT-069 to CT-072 (L3) | ❌ No PDF source identified | Need to acquire |
| Batteries/DC Systems | CT-073 to CT-076 (L3) | ❌ No PDF source identified (IEEE 450 not on disk) | Need to acquire |
| Voltage Regulators | CT-048 to CT-051 (L3) | ⚠️ IEEE C57.15 in C57.xx collection (H5) | Sprint 3 |
| SCADA/DCS | SC-002 (L3) | ❌ No PDF source identified | Need to acquire |
| Harmonics/PQ | ET-017, ET-027, ET-028 (L3) | ✅ IEEE 519-1992 on disk (H1) | Sprint 2 |
| Protection & Coordination | TCC analysis (L3/L4) | ✅ IEEE 242-2001 on disk (H2) | Sprint 2 |

**Sources to acquire (not on disk):**
- IEEE 450-2020 (Battery testing) — covers CT-073 to CT-076
- IEEE 1547 or manufacturer VFD testing guide — covers CT-069 to CT-072
- IEC 61850 or SCADA reference — covers SC-002

---

## Supabase Migration Impact

When `source_documents` and `extractions` tables are created (Phase 5 schema), this document provides the canonical data for:

| Table | Source | Rows |
|-------|--------|------|
| `source_documents` | All documents listed above | ~61 unique sources |
| `extractions` / `study_content` | Completed extractions | 335 rows |
| `ksa_extraction_links` | KSA tags from extraction files | ~4,915 junction links |

---

*Created: 2026-02-27 — VS Code Claude (Opus 4.6)*
*Updated: 2026-03-01 — Claude Code (Opus 4.6) — C37 batch (5 standards) extracted and added*
*Updated: 2026-03-07 — VS Code Copilot (Opus 4.6) — 45 new PDFs cataloged/sorted, 4 extractions COMPLETE (EXT-IEEE-051 1,417 lines, EXT-IEEE-052 1,050 lines, EXT-IND-016 1,529 lines, EXT-IND-017 875 lines = 4,871 total), 2 exam-ref edition gaps closed*
*Update this document when extractions are completed or new source materials are acquired.*
