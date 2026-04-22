# Remaining Extraction Queue — Master Inventory

## Created: 2026-03-16  
## Author: Desktop Claude  
## Purpose: Track all unextracted PDFs for future extraction batches (Batch 6+)  
## Last Updated: 2026-03-16  

---

## Summary

| Category | Unextracted | Total Sources | Coverage | Notes |
|----------|-------------|---------------|----------|-------|
| _Unsorted (C37 series) | 15 | — | N/A | Needs sort first → IEEE-Standards |
| _Unsorted (misc) | 4 | — | N/A | Needs sort/identification |
| CIGRE-References | 5 (+1 dup) | 7 | 14% | Largest coverage gap |
| Equipment-Manuals | 15 | 58 | 74% | Mostly catalogs/datasheets |
| Exam-Resources | 4 | 7 | 43% | DCOs + formulae sheet HIGH value |
| IEC-Standards | 1 | 8 | 88% | PLC textbook only |
| IEEE-Standards (sorted) | 18 | 144 | 88% | Mixed relevance |
| Industry-NETA | 8 | 44 | 82% | CB testing, study notes |
| Instrument-Transformers | 1 | 10 | 90% | CT testing guide |
| Manufacturer-Docs | 2 | 9 | 78% | Transfer switch O&M |
| NEMA | 3 | 7 | 57% | MCCB, insulators, busway |
| NETA-Standards | 1 | 10 | 90% | Older ETT edition |
| NFPA-OSHA | 2 | 17 | 88% | 1 usable (OSHA 4472); 1 DO NOT USE (Google-translated) |
| PEARL | 4 | 4 | ~0% | May be partially extracted under topic names |
| Textbooks | 35 | 82 | 57% | Many large, selective extraction only |
| UL-Standards | 1 | 2 | 50% | Whitepaper only |
| **TOTAL** | **~119** | **416** | **~71%** | Includes _Unsorted items |

*(Batch 5: 8 C62/SPD/grounding items tracked separately in TASK-CC-BATCH5-EXTRACT-LOAD.md)*

---

## BATCH 6 — C37 Circuit Breakers / Switchgear / Protection (15 items)

**Priority:** HIGH — CB, switchgear, relay, and protection standards are among the most tested NETA ETT topics.  
**Prerequisite:** Sort from `_Unsorted/` → `IEEE-Standards/`  
**ID Range:** EXT-IEEE-265 through EXT-IEEE-279

### Sort Plan

| # | Original Filename | Size | Rename To | Topic |
|---|------------------|------|-----------|-------|
| 1 | `IEEE C37.04-2018.pdf` | 5.2 MB | `IEEE-C37.04-2018-AC-HV-CB-Rating-Structure.pdf` | HV circuit breaker rating structure |
| 2 | `IEEE C37.100.1-2018.pdf` | 4.3 MB | `IEEE-C37.100.1-2018-HV-Switch-Common-Requirements.pdf` | Common requirements for HV equipment |
| 3 | `IEEE C37.108-2021.pdf` | 1.9 MB | `IEEE-C37.108-2021-Network-Transformer-Protection.pdf` | Protection of network transformers |
| 4 | `IEEE C37.112-2018.pdf` | 2.5 MB | `IEEE-C37.112-2018-Inverse-Time-Relay-Characteristics.pdf` | Inverse-time relay characteristics |
| 5 | `IEEE C37.118.2-2011.pdf` | 1.4 MB | `IEEE-C37.118.2-2011-Synchrophasor-Data-Transfer.pdf` | Synchrophasor data transfer |
| 6 | `IEEE C37.119-2016.pdf` | 3.2 MB | `IEEE-C37.119-2016-Breaker-Based-Station-Protection.pdf` | Breaker-based station protection |
| 7 | `IEEE C37.121-2020.pdf` | 1.8 MB | `IEEE-C37.121-2020-Indoor-Switchgear-5-38kV.pdf` | Switchgear indoor enclosures 5-38 kV |
| 8 | `IEEE C37.122.2-2011.pdf` | 1.2 MB | `IEEE-C37.122.2-2011-HV-GIS-Guide-Over-52kV.pdf` | Guide for HV GIS over 52 kV |
| 9 | `IEEE C37.122.3-2011.pdf` | 1.6 MB | `IEEE-C37.122.3-2011-SF6-GIS-Guide.pdf` | Guide for SF6 GIS |
| 10 | `IEEE C37.2-2008.pdf` | 2.3 MB | `IEEE-C37.2-2008-Device-Function-Numbers.pdf` | Device function numbers and contact designations |
| 11 | `IEEE C37.234-2021.pdf` | 3.9 MB | `IEEE-C37.234-2021-Relay-Bus-Protection-Guide.pdf` | Protective relay bus protection applications |
| 12 | `IEEE C37.235-2021.pdf` | 4.6 MB | `IEEE-C37.235-2021-Prime-Mover-Frequency-Control.pdf` | Prime mover frequency control guide |
| 13 | `IEEE C37.236-2013.pdf` | 2.9 MB | `IEEE-C37.236-2013-Protection-System-Testing-Guide.pdf` | Power system protection testing guide |
| 14 | `IEEE C37.30.4-2018.pdf` | 2.0 MB | `IEEE-C37.30.4-2018-HV-Switch-Pad-Guide.pdf` | HV interrupter switch pad guide |
| 15 | `IEEE C37.62-2020.pdf` | 2.6 MB | `IEEE-C37.62-2020-Padmount-Switchgear.pdf` | Standard for padmount switchgear |

### Recommended Tier Split

**Tier 1 — HIGH (direct ETT test relevance):**
- C37.04 (CB ratings), C37.112 (relay curves), C37.119 (breaker station protection), C37.121 (indoor MV switchgear), C37.2 (device numbers), C37.234 (bus protection), C37.236 (protection testing), C37.62 (padmount switchgear)

**Tier 2 — MEDIUM (enrichment/broader knowledge):**
- C37.100.1 (HV common reqs), C37.108 (network XFMR protection), C37.122.2 (HV GIS), C37.122.3 (SF6 GIS), C37.235 (frequency control), C37.118.2 (synchrophasor), C37.30.4 (HV switch pad)

---

## BATCH 7 — Exam Resources + NETA Industry + Instrument Transformers (14 items)

**Priority:** HIGH — exam resources (DCOs, formulae) are directly test-relevant. Industry CB/instrument testing guides support guide production.  
**ID Range:** Mixed — see individual items

### Exam-Resources (4 items)

| # | Filename | Size | Proposed ID | Notes |
|---|----------|------|-------------|-------|
| 1 | `NETA Certification Exams - Detailed Content Outlines (DCOs).pdf` | 1.0 MB | EXT-NETA-006 | ⭐ **Critical** — exam content outlines |
| 2 | `Official Electrical Formulae Sheet.pdf` | 0.1 MB | EXT-IND-021 | ⭐ **Critical** — exam formula reference |
| 3 | `NETA Practice Exam Instructions.pdf` | 1.0 MB | EXT-NETA-007 | Exam administration context |
| 4 | `MCQs-Fiber-Optics-Communications-PinoyBIX.pdf` | 0.3 MB | EXT-IND-022 | Low relevance — fiber optics MCQs |

### Industry-NETA (8 items)

| # | Filename | Size | Proposed ID | Notes |
|---|----------|------|-------------|-------|
| 5 | `Circuit Breaker Testing Guide_3586.pdf` | 1.0 MB | EXT-IND-023 | CB testing guide |
| 6 | `Circuit-Breaker-Testing.pdf` | 0.4 MB | — | May duplicate item 5 — check before assigning ID |
| 7 | `CCVTs testing Anaheim Seminar 2016.pdf` | 3.8 MB | EXT-IND-024 | CCVT testing seminar paper |
| 8 | `Fundamentals of Electricity Facts Sheet.pdf` | 0.7 MB | EXT-IND-025 | Electricity fundamentals |
| 9 | `NECA301-16_P.pdf` | 1.4 MB | EXT-IND-026 | NECA standard (electrical installation) |
| 10 | `NETA Third Party Testing Article.pdf` | 0.4 MB | EXT-IND-027 | Testing article |
| 11 | `NETA III Some help.docx` | <0.1 MB | — | Study notes — review for inclusion |
| 12 | `NETA III (2).docx` | <0.1 MB | — | Study notes — review for inclusion |

### Instrument-Transformers (1 item)

| # | Filename | Size | Proposed ID | Notes |
|---|----------|------|-------------|-------|
| 13 | `Testing-CT.pdf` | 2.9 MB | EXT-IND-028 | CT testing guide — directly relevant |

### NETA-Standards (1 item)

| # | Filename | Size | Proposed ID | Notes |
|---|----------|------|-------------|-------|
| 14 | `NETA ETT 2018.pdf` | 15.5 MB | EXT-NETA-008 | Older ETT edition — selective extraction for comparison |

---

## BATCH 8 — CIGRE + Remaining IEEE (Sorted) + _Unsorted Misc (~27 items)

**Priority:** MEDIUM  
**ID Range:** Mixed

### CIGRE-References (5 items)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `CIGRE-Green-Book-Switching-Equipment-Ito-2019.pdf` | 31.0 MB | EXT-CIGRE-002 | HV switching reference — selective extraction |
| `CIGRE-TB-568-Transformer-Inrush-Currents.pdf` | 7.7 MB | EXT-CIGRE-003 | Transformer inrush |
| `CIGRE-TB-757.pdf` | 29.7 MB | EXT-CIGRE-004 | Unknown topic — identify first |
| `CIGRE-TB-797-Sheath-Bonding-Systems.pdf` | 3.8 MB | EXT-CIGRE-005 | Cable sheath bonding |
| `CIGRE-TB-812.pdf` | 17.2 MB | EXT-CIGRE-006 | Unknown topic — identify first |
| ~~`485740143-CIGRE-812.pdf`~~ | 17.2 MB | — | **DUPLICATE of TB-812 — delete** |

### IEEE-Standards — Sorted but Not Extracted (18 items)

Items sorted by relevance:

**HIGH relevance (extract in this batch):**

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `IEEE C2-2023 - National Electrical Safety Code (NESC).pdf` | 11.9 MB | EXT-IEEE-280 | NESC — selective extraction (large) |
| `IEEE-1189-2007-VRLA-Battery-Selection.pdf` | 0.4 MB | EXT-IEEE-281 | VRLA battery selection guide |
| `IEEE-1861-2014-Onsite-Acceptance-Tests-1000kV.pdf` | 3.2 MB | EXT-IEEE-282 | UHV acceptance tests |
| `IEEE-3001.2-2017-Electrical-Service-Requirements.pdf` | 2.9 MB | EXT-IEEE-283 | Service requirements |
| `IEEE-3001.11-2017-Controllers-Automation.pdf` | 4.4 MB | EXT-IEEE-284 | Controllers/automation |
| `IEEE-387-2017-Diesel-Generators-Nuclear-Stations.pdf` | 1.8 MB | EXT-IEEE-285 | Diesel generator standards |
| `IEEE-C37.22-1997-MV-Indoor-Switch-Ratings.pdf` | 0.1 MB | EXT-IEEE-286 | MV switch ratings (C37-adjacent) |
| `IEEE-C37.242-2013-PMU-Testing-Installation.pdf` | 2.1 MB | EXT-IEEE-287 | PMU testing/installation |
| `IEC-61850-Communication-Networks-Overview.pdf` | 1.0 MB | EXT-IEC-008 | IEC 61850 overview (misfiled under IEEE) |
| `IEC-62040-1-1-2002-UPS-Safety-Requirements.pdf` | 0.5 MB | EXT-IEC-009 | UPS safety requirements |

**MEDIUM relevance (extract if time/effort permits):**

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `IEEE C2-2023 - NESC Handbook.pdf` | 201.0 MB | — | Massive — selective extraction only if needed beyond NESC std |
| `IEEE-100-Dictionary-of-Standards-Terms.pdf` | 11.8 MB | — | Reference dictionary — selective extraction of key test terms |
| `IEEE-1729-2014-Distribution-System-Analysis.pdf` | 2.3 MB | EXT-IEEE-288 | Distribution analysis |
| `IEEE-C93.3-2017-Power-Line-Carrier-Line-Traps.pdf` | 1.1 MB | EXT-IEEE-289 | Line traps — niche |

**LOW relevance (skip or defer):**

| Filename | Size | Notes |
|----------|------|-------|
| `IEEE-488.1-1987-GPIB-Digital-Interface.pdf` | 3.3 MB | Vintage GPIB — minimal NETA relevance |
| `IEEE-488.2-1987-GPIB-Codes-Formats.pdf` | 1.9 MB | Vintage GPIB — minimal NETA relevance |
| `VHDL-2008-Hardware-Description-Language.pdf` | 6.1 MB | Hardware description language — not NETA relevant |
| `VuSpec-Catalog-IEEE-Power-Switchgear-...pdf` | 0.2 MB | Catalog, not a standard — skip |

### _Unsorted Misc (4 items)

| Filename | Size | Notes |
|----------|------|-------|
| `027498267.pdf` | ? | ⚠️ Needs identification |
| `464303109-InsulationCoordination.pdf` | ? | Insulation coordination — relevant |
| `501900163-powerexamsample.pdf` | ? | Power exam sample — extract for practice questions |
| `699639898-FE-Electrical-Study-Guide.pdf` | ? | FE study guide — broader engineering context |

---

## BATCH 9 — Equipment-Manuals + Manufacturer-Docs + NEMA + UL (~21 items)

**Priority:** MEDIUM-LOW  
**ID Range:** EXT-MFR-048+, EXT-IND-029+

### Equipment-Manuals (15 items)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `Vertiv-PowerUPS-9000-1250kVA-UM.pdf` | 24.9 MB | EXT-MFR-048 | UPS user manual — selective extraction |
| `Vertiv-Liebert-EXL-S1-250-1200kVA-Guide-Spec.pdf` | 6.0 MB | EXT-MFR-049 | UPS guide spec |
| `Vertiv-PowerUPS-9000-480V-Site-Planning.pdf` | 0.3 MB | EXT-MFR-050 | UPS site planning |
| `Russelectric-RTS03-Transfer-Switch-OM-Manual.pdf` | 1.6 MB | EXT-MFR-051 | Transfer switch O&M |
| `Powell-NDC-LV-DC-Switchgear-Manual.pdf` | 1.3 MB | EXT-MFR-052 | LV DC switchgear |
| `S&C-Power-Fuses-SMD-Series-Selection-Guide.pdf` | 3.1 MB | EXT-MFR-053 | Power fuse selection |
| `R-Series-MV-Contactors-R1400-R1700-R2100-Catalog.pdf` | 2.5 MB | EXT-MFR-054 | MV contactor catalog |
| `MV-Fuse-Links-Catalogue-2008.pdf` | 0.7 MB | EXT-MFR-055 | MV fuse catalog |
| `Comoso-Enclosed-Control-Volume-10-Catalog.pdf` | 6.3 MB | EXT-MFR-056 | Enclosed control catalog |
| `Eaton-Cooper-Cleer-SecTER-600A-MV-Cabinet.pdf` | 0.4 MB | EXT-MFR-057 | MV cabinet datasheet |
| `Eaton-Cooper-Pole-Mounted-Capacitor-Racks.pdf` | 1.0 MB | EXT-MFR-058 | Capacitor rack installation |
| `Federal-Pacific-Pad-Mounted-Capacitor-Banks.pdf` | 0.3 MB | EXT-MFR-059 | Pad-mount capacitor bank |
| `Safe-Capacity-Test-Battery-WP.pdf` | 0.8 MB | EXT-IND-029 | Battery capacity testing WP |
| `LiIon-Batteries-DataCenter-Emergence-WP.pdf` | 0.6 MB | EXT-IND-030 | Li-ion data center WP |
| `Transformer-Catalogue-EN-Digital.pdf` | 19.4 MB | — | Generic catalog — skip unless needed |

### Manufacturer-Docs (2 items)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `Eaton-TS-101-Transfer-Switch-Reference.pdf` | 0.2 MB | EXT-MFR-060 | Transfer switch reference |
| `Russelectric-RTS03-Bypass-Isolation-ATS-OM.pdf` | 1.8 MB | EXT-MFR-061 | Bypass isolation ATS O&M |

### NEMA (3 items)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `ANSI-NEMA-AB-4-2023-Guidelines-Inspection-MCCB.pdf` | 0.9 MB | EXT-IND-031 | MCCB inspection (2023 edition; 2017 already extracted) |
| `ANSI-NEMA-C29-10-2017-Porcelain-Insulators.pdf` | 0.7 MB | EXT-IND-032 | Porcelain insulators |
| `NEMA-BU-1-1-Installation-Maintenance-Busways.pdf` | 0.7 MB | EXT-IND-033 | Busway installation and maintenance |

### UL-Standards (1 item)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `UL-1008-7th-Edition-WCR-Whitepaper.pdf` | 1.0 MB | EXT-IND-034 | UL 1008 whitepaper |

---

## BATCH 10 — Textbooks + PEARL + NFPA-OSHA Remaining (~42 items)

**Priority:** LOW — textbooks require selective extraction (many are 20+ MB, 300+ pages). Extract high-value chapters only per V2.0 §2.4 selective extraction protocol.

### PEARL (4 items — verify extraction status first)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `Level-1-Handbook-PEARL.pdf` | 1.2 MB | — | ⚠️ Check if `PEARL-01..04` extractions cover content |
| `Level-2-Handbook-PEARL.pdf` | 1.1 MB | — | Same as above |
| `Level-3-Handbook-PEARL.pdf` | 0.8 MB | — | Same as above |
| `PEARL-Level-1-Exam-Info-Guide.pdf` | 0.1 MB | — | Exam info guide |

### NFPA-OSHA (2 usable items)

| Filename | Size | Notes |
|----------|------|-------|
| `OSHA 4472.pdf` | 2.7 MB | OSHA publication — extract |
| ~~`NFPA-101-2024-TRADUCIDA-...-DO-NOT-USE.pdf`~~ | 25.4 MB | ⛔ Google-translated — **DO NOT EXTRACT** |

### Textbooks — HIGH Value (extract first)

| Filename | Size | Proposed ID | Notes |
|----------|------|-------------|-------|
| `ArcFlash-Handbook-FINAL-online.pdf` | 3.5 MB | EXT-IND-035 | ⭐ Arc flash handbook — direct ETT relevance |
| `Condition-Assessment-of-HV-Equipment.pdf` | 2.3 MB | EXT-IND-036 | HV condition assessment — direct testing relevance |
| `Condition-Monitoring-Electrical-Equipment.pdf` | 2.0 MB | EXT-IND-037 | Condition monitoring — direct testing relevance |
| `Intro to Power Transformer Testing_LowVoltage_SFRA.pdf` | 3.5 MB | EXT-IND-038 | Transformer testing — direct ETT relevance |
| `Lead-Acid-Battery-Maintenance-Testing-Webinar.pdf` | 7.3 MB | EXT-IND-039 | Battery maintenance/testing |
| `Megger-Station-Battery-Testing-Best-Practices-2011.pdf` | 2.1 MB | EXT-MFR-062 | Megger battery testing best practices |
| `Understanding-Battery-Maintenance-2018.pdf` | 2.1 MB | EXT-IND-040 | Battery maintenance guide |
| `Substation-Protection-and-Maintenance-using-ETAP.pdf` | 10.3 MB | EXT-IND-041 | ETAP substation P&M — selective extraction |

### Textbooks — MEDIUM Value

| Filename | Size | Notes |
|----------|------|-------|
| `Badri-Ram-Power-System-Protection.pdf` | 26.0 MB | Protection textbook — selective extraction of relay/protection chapters |
| `Abood-Fuller-Protection-Relaying-SCADA-CAD-2024.pdf` | 39.8 MB | Protection/SCADA — selective extraction |
| `Fundamentals-of-Electrical-Power-Systems-2020.pdf` | 17.6 MB | Power systems fundamentals |
| `Handbook for Electricity Metering 9th Edition.pdf` | 6.8 MB | Metering handbook |
| `ElectricMotorGuide.pdf` | 1.3 MB | Motor guide |
| `Electrical-System-Identification-Reference-Chart.pdf` | 0.5 MB | System ID ref chart |
| `ELECTRICAL CALCULATIONS BOOK SIMPLIFIED...pdf` | 2.7 MB | Electrical calculations |
| `Krueger-Diagnostic-Meas-Fault-Investigation-PT-...pdf` | 6.8 MB | Diagnostic measurements conference paper |
| `Article-Brandon's-Notes-on-Different-Transformer-Types-2021-ENU.pdf` | 1.0 MB | Transformer types notes |
| `IEC-60896-21-22-VRLA-Battery-Standards-Paper.pdf` | 0.3 MB | VRLA battery standards paper |
| `CIGRE-WG21-17-Cable-Installation-Techniques-2001.pdf` | 1.8 MB | Cable installation (misfiled under Textbooks) |
| `Training-Manual-Solar-PV-Systems.pdf` | 5.2 MB | Solar PV training |
| `Werstiuk-Relay-Testing-Handbook-Generator-Ch26-Excerpt-87-Elements.pdf` | 3.5 MB | Ch26 excerpt (main volumes already extracted) |
| `Information Bulletin 210-110.pdf` | 3.7 MB | Info bulletin — identify source |

### Textbooks — LOW Value / Defer

| Filename | Size | Notes |
|----------|------|-------|
| `American ElectriciansHandbook15th Edition.pdf` | 23.1 MB | General reference — very large, low extraction priority |
| `Circuit Analysis For Dummies_3_1.pdf` | 8.5 MB | Introductory — low extraction priority |
| `Circuit Analysis Simplified_1.pdf` | 1.1 MB | Introductory — low extraction priority |
| `Corsi-Voltage-Control-and-Protection-Power-Systems.pdf` | 46.0 MB | Very large — specialized voltage control |
| `Industrial Instrumention.pdf` | 60.9 MB | Very large — general instrumentation |
| `Alhelou-Grid-Forming-Power-Inverters-2023.pdf` | 37.5 MB | Grid-forming inverters — niche |
| `Meegahapola-Hybrid-AC-DC-Power-Grids-2022.pdf` | 11.6 MB | Hybrid grids — niche |
| `Power-Grids-With-Renewable-Energy.pdf` | 33.2 MB | Renewable energy — niche |
| `Ultra-High-Voltage-ACDC-Power-Transmission-Zhou.pdf` | 29.3 MB | UHV transmission — niche |
| `Full.pdf` | 22.0 MB | ⚠️ Ambiguous filename — identify first |
| `NEPLAN-V555-Exciter-Models-Reference.pdf` | 3.3 MB | Exciter models — niche software reference |
| `Predl-Part1-Issue11.pdf` | 0.5 MB | Unknown — identify first |
| `Transformers Manual.pdf` | 4.9 MB | Generic transformer manual |
| `Safe-Capacity-Test-Battery-WP.pdf` | 0.8 MB | *(also listed under Equipment-Manuals — track in Batch 9 only)* |

---

## Process Notes

1. **Inclusion criteria:** Per project guidance, include ALL content regardless of direct ETT KSA relevance. Mark relevance level but do not exclude items based on test scope alone.
2. **V2.0 standard:** All extractions must follow `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` V2.0 guidelines. "Curate, Don't Dump."
3. **Selective extraction for large documents:** Documents >100 pages → extract high-value chapters only per V2.0 §2.4. Document what was extracted AND what was skipped.
4. **Legacy re-extraction candidates:** Three C62 standards (C62.11-1999, C62.11-2020, C62.22-1997) plus several Equipment-Manual items have legacy non-EXT extractions. These are NOT unextracted but may benefit from future V2.0 re-extraction. Track separately.
5. **Duplicates identified:** `485740143-CIGRE-812.pdf` duplicates `CIGRE-TB-812.pdf` — delete during Batch 8 sort.
6. **DO NOT EXTRACT:** `NFPA-101-2024-TRADUCIDA-Google-Translate-DO-NOT-USE.pdf` — Google-translated, unreliable.
7. **IDs are provisional** — adjust at extraction time if conflicts arise or if items turn out to be different from expected.

---

## Batch Execution Priority

```
Batch 5 (C62/SPD/Grounding)  ← CURRENT — see TASK-CC-BATCH5-EXTRACT-LOAD.md
  ↓
Batch 6 (C37 CB/Switchgear/Protection)  ← NEXT
  ↓
Batch 7 (Exam Resources + NETA Industry + CT Testing)
  ↓
Batch 8 (CIGRE + Remaining IEEE + _Unsorted Misc)
  ↓
Batch 9 (Equipment-Manuals + Manufacturer + NEMA + UL)
  ↓
Batch 10 (Textbooks + PEARL + NFPA Remaining)
```
