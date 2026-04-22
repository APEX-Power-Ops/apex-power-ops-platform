# GUIDE REGISTRY — Consolidated Study Guides
## Master status tracker for the governed study guide pipeline
## Last Updated: March 29, 2026

---

## Overview

| Metric | Count |
|--------|-------|
| Remaining legacy v2.3 surfaces | 21 |
| Guides loaded (draft in Supabase) | 34 |
| Active scaffolded guides | 0 |
| Active staged guides | 0 |
| Guides blocked (awaiting source extraction) | 0 |
| Guides planned (architecture decided, not yet scaffolded) | 0 |
| Total v2.3+ guides in pipeline | 43 |
| Old per-level guides (pre-v2.2) | ~95 (in NETA-2/3/4 folders) |

**Pipeline:** New material guides staged in `Development/staging/[topic]/`
Consolidation guides staged in `Development/Consolidation/Output/`
Old per-level guides in `NETA-2/03-Study-Guides/`, `NETA-3/03-Study-Guides/`, `NETA-4/03-Study-Guides/`

Bounded remaining-legacy inventory:

- `Development/Control-Plane/ETT-REMAINING-V2.3-GUIDE-INVENTORY-AND-ACTION-MATRIX.md` preserves the current remaining-v2.3 guide set plus retain / park / carryforward recommendations; do not treat the existence of that set as evidence for a broad new modernization wave.
- `Development/Control-Plane/ETT-V2.4-RELOAD-DECISION-MATRIX-2026-03-26.md` preserves which v2.4-capable guides are already reloaded, execute-ready, optional-later, or not yet approved for reload.
- `Development/Control-Plane/ETT-GUIDE-LIFECYCLE-OPERATING-MODEL-2026-03-26.md` preserves the current approved authoring, audit, review, load, and reload workflow.
- `Development/Control-Plane/ETT-GUIDE-ESTATE-ASSESSMENT-NORMALIZATION-PLAN-2026-03-26.md` preserves the estate-wide plan for bringing remaining v2.3 and older guides into one equivalent assessment model before additional queue actions are opened.
- `Development/Control-Plane/ETT-GUIDE-ESTATE-ASSESSMENT-MASTER-MATRIX-2026-03-26.md` is the active normalized classification surface for the current guide estate.
- `Development/Control-Plane/ETT-OLD-PER-LEVEL-GUIDE-INVENTORY-AND-TRIAGE-2026-03-26.md` routes older `NETA-2`, `NETA-3`, and `NETA-4` guide questions into archive, carryforward, domain-candidate, or family-reopen triage before any queue action is opened.
- `Development/Control-Plane/ETT-GUIDE-INTAKE-AND-QUEUE-GOVERNANCE-BOARD-2026-03-26.md` is the live routing surface for what can move now, what needs stakeholder approval, and what should remain parked.
- `Development/Control-Plane/ETT-LEGACY-FAMILY-AND-DOMAIN-REVIEW-BACKLOG-2026-03-26.md` preserves the next bounded family-review and domain-review candidates without overstating them as active queue items.

**Restart-state rule:** Treat this file as a live loaded-and-parked registry for the active ETT lane. Do not infer an active authoring queue from historical notes or older backlog wording. If a new guide topic is explicitly reactivated, update this file and `Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md` together.

---

## CONSOLIDATED GUIDE REGISTRY

### Guide #1 — Circuit Switchers (REBUILT)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/circuit-switchers/SG-CT-CIRCUIT-SWITCHERS.md` |
| **content_id** | SG-CT-CIRCUIT-SWITCHERS |
| **NETA Section** | 7.7 |
| **KSA Coverage** | CT-028 through CT-031 (L2/L3/L4) |
| **Pipeline** | New Material (scaffold + 4 CT-FILLED sections) |
| **Status** | ✅ LOADED — `status: draft` in Supabase (rebuilt from scaffold Mar 9) |
| **Supabase UUID** | a83b553a-7b73-41b6-8750-b1d993919ce7 |
| **Quality Grade** | A− |
| **Lines** | 843 |
| **Word Count** | 10,879 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 5 (cs-sf6-gas-indicator, cs-model-comparison, cs-gas-pressure-check, cs-connection-vs-contact, cs-nameplate-data) |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, 4 KSA sections (CT-028:031), field scenarios, common mistakes, quick-reference retention support, and standards reference |
| **Sources consumed** | SG-CT-CIRCUIT-SWITCHERS-SCAFFOLD.md (sections 2-8) + 4 CT-FILLED files (CT028-CT031) |
| **Key content** | SF6 gas systems, dead-tank/live-tank comparison, dielectric withstand, insulation resistance, contact resistance, minimum pickup, thermography, IEEE C37.016 |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config created 2026-03-27: `Development/staging/circuit-switchers/circuit-switchers-config.json`) |
| **Notes** | Rebuilt from scaffold + 4 Desktop Claude fills (replacing original 577-line PoC). UPDATEd existing Supabase record. CT-028:031 KSA links already existed. Bounded v2.4 review/polish completed 2026-03-26; direct review confirmed the guide already carried the required publication-layer structure. Step-2 reload metadata updated 2026-03-27; body_markdown reload pending local terminal execution via `load_guide_generic.py --apply`. |

---

### Guide #2 — Grounding Systems

| Field | Value |
|-------|-------|
| **File** | `Development/staging/grounding-systems/SG-CT-grounding-systems.md` |
| **content_id** | SG-CT-GROUNDING-SYSTEMS |
| **NETA Section** | 7.13 |
| **KSA Coverage** | CT-052 through CT-056 (L2/L3/L4) |
| **Pipeline** | Consolidation |
| **Status** | ✅ LOADED — reloaded in place 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | 5cfa72d7-ecf... |
| **Quality Grade** | A |
| **Lines** | 852 |
| **Word Count** | 10,612 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, bounded KSA body, quick-reference retention support, and learner-facing further-study guidance |
| **Verify** | GPR threshold values |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config created 2026-03-27: `Development/staging/grounding-systems/grounding-systems-config.json`; note: guide filename is lowercase `SG-CT-grounding-systems.md` but content_id is uppercase `SG-CT-GROUNDING-SYSTEMS` ? generic loader may need a rename or manual path override) |
| **Notes** | Consolidation pipeline PoC. Gold standard for format. Bounded v2.4 integration completed 2026-03-26. Step-2 reload metadata updated 2026-03-27; body_markdown reload pending local terminal execution. |

---

### Guide #3 — Cable Testing (MV, Shielded)

| Field | Value |
|-------|-------|
| **File** | `Development/Consolidation/Output/SG-CT-cable-testing.md` |
| **content_id** | SG-CT-CABLE-TESTING |
| **NETA Section** | 7.5 |
| **KSA Coverage** | CT-010 through CT-015 (L2/L3/L4) |
| **Pipeline** | Consolidation |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | e32585d3-899... |
| **Quality Grade** | A− |
| **Lines** | 726 |
| **v2.2 Sections** | ✅ All present — Field Tips confirmed at line 663 |
| **Notes** | Safety Considerations and Field Scenarios completed ahead of v2.2 schedule during autonomous build. Field Tips is the only remaining section. |

---

### Guide #4A — Relay Testing Core (SPLIT from #4)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/protective-relays/SG-CT-RELAY-TESTING-CORE.md` |
| **content_id** | SG-CT-RELAY-TESTING-CORE |
| **NETA Section** | 7.9.1, 7.9.2 |
| **KSA Coverage** | CT-036 (types, inspection), CT-037 (EM/SS testing), CT-038 (MPR core), CT-039 (coordination) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 80c6449c-1936-404e-8b1c-4601809bfcfa (reused from original #4) |
| **Lines** | 646 |
| **Word Count** | 12,132 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 4 (relay-em-induction-disk, relay-ct-shorting-block, relay-inverse-time-curve, relay-differential-principle) |
| **v2.3 Sections** | ✅ All 8 present |
| **Key content** | Three relay generations, ANSI device numbers (core set), CT/VT secondary circuits, EM/SS inspection, secondary injection (pickup/timing), 50/51/27/59/67/86/87, MPR testing (analog inputs, SCADA, digital I/O, logic, arc energy reduction, ZSI), coordination verification, CT suitability, dynamic vs steady-state, event report analysis |
| **Notes** | Split from #4 (1,014L, 20,494w) Mar 11. Motor, generator, distance, and 87T content moved to #4B. Cross-refs to #4B in overview, Section 7, Section 8. |

---

### Guide #4B — Protection Applications (SPLIT from #4)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/protective-relays/SG-CT-PROTECTION-APPLICATIONS.md` |
| **content_id** | SG-CT-PROTECTION-APPLICATIONS |
| **NETA Section** | 7.9.1, 7.9.2 |
| **KSA Coverage** | CT-036 (application-specific device types), CT-038 (application-specific electrical testing) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | dc74f73a-9bd2-5230-bd93-e867640cc8fb |
| **Lines** | 611 |
| **Word Count** | 12,764 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 3 (relay-motor-thermal-coordination [NEW], relay-rx-impedance-plane, relay-87t-dual-slope [NEW]) |
| **v2.3 Sections** | ✅ All 8 present |
| **Key content** | Motor protection (49/50P-N/87M/46/restart logic), generator protection (32/40/46/51V/78/87G), distance relay (21, R-X plane, zone testing), transformer differential (87T dual-slope, inrush discrimination, harmonic restraint) |
| **Enrichment** | 87T section enriched with EXT-TXT-002 (Patel & Chothani): dual-slope characteristic, 2nd/5th harmonic restraint, CT saturation detection |
| **Notes** | Split from #4 Mar 11. Cross-refs to #4A in overview, Section 2, Section 4, Section 7, Section 8. |

---

### Guide #5 — Transformer Testing (Power Transformers, Liquid-Filled)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/transformer-testing/SG-CT-transformer-testing.md` |
| **content_id** | SG-CT-TRANSFORMER-TESTING |
| **NETA Section** | 7.2.1, 7.2.2 |
| **KSA Coverage** | CT-005 through CT-009 (L2/L3/L4) |
| **Pipeline** | Consolidation |
| **Status** | ✅ LOADED — `status: draft` in Supabase (OLTC/DRT + condition assessment enriched Mar 11) |
| **Supabase UUID** | 99e987e1-a23... |
| **Quality Grade** | A− |
| **Lines** | 819 |
| **Word Count** | 9,252 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 5 (xfmr-winding-connections, xfmr-ir-test-configs, xfmr-excitation-three-leg-core, xfmr-drt-waveform [NEW], xfmr-dga-gas-temperature) |
| **v2.3 Sections** | ✅ All present — 5 KSA sections, 8 field scenarios, 7 common mistakes |
| **Sources consumed** | 6 study guides (100% xfmr content, no non-xfmr content found) + 6 Tier 1 extractions + 5 Tier 2 extractions + NETA-Data JSON (ATS 7.2.2: 21 V/M + 19 electrical tests) |
| **Key decisions** | DGA: fundamentals + C57.104-2019 Status 1/2/3 only; Duval/Rogers/Dornenburg/furans deferred. ATS Table 100.4 (new oil) + MTS Table 100.4 (service-aged) embedded side-by-side with 10× PF exam-trap callout. TTR connection-specific formulas (Δ-Δ/Y-Y, Δ-Y, Y-Δ) with worked example and √3 pitfall. 1991 four-condition DGA system called out in Common Mistakes as outdated. SFRA/DRT referenced as ATS optional tests, deferred to supplements. |
| **Task Doc** | `Development/TASK-VSCODE-GUIDE5-TRANSFORMER-TESTING.md` |
| **Commit msg** | `Add Guide #5: Transformer Testing (power transformers, liquid-filled) — 837L, 8132w, 0 VERIFY flags` |
| **Commit note** | EXTRACTION-CATALOG.md changes from Mar 5 cataloging task still uncommitted — bundle or separate per preference. |

---

### Guide #6 — Insulating Fluids (Mineral Oil + Natural Ester)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/insulating-fluids/SG-CT-INSULATING-FLUIDS.md` |
| **content_id** | SG-CT-INSULATING-FLUIDS |
| **NETA Section** | 7.2.B.9, 7.2.B.10 |
| **KSA Coverage** | CT-087 through CT-090, CT-101 through CT-105 (L2/L3/L4) |
| **Pipeline** | New Material + Consolidation |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | ac29c7bf-cea2-41df-891a-793bdd00a2fd |
| **KSA Links** | 31 (18 discovery + 13 manual_patch) |
| **Quality Grade** | A (target) |
| **Lines** | 987 |
| **Word Count** | 10,294 |
| **VERIFY flags** | 0 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, normalized numbered section spine, quick-reference retention support, and learner-facing further-study guidance |
| **Sources consumed** | Paul Gill Ch.4 (2,600L) + SD Myers (1,300L) + C57.106-2015 + C57.147-2018 + C57.104-2019 + C57.104-DGA-Interpretation + D923-15(2023) + D3487-16e1 + Insulating Fluid Fact Sheet |
| **Key content** | Full mineral oil test suite (BDV/PF/IFT/acid/moisture/color/visual/DBPC/furans). C57.106 Class I/II/III system with remediation pathways. Vacuum dehydration + Fuller's earth procedures. DGA: C57.104-2019 Status 1/2/3 + legacy 4-condition, Duval Triangle, Rogers Ratios, Key Gas. NE: C57.147 Tables 2-4, 9 key NE vs mineral oil differences, 7% contamination rule. D923 §5/§7/§8/§9 sampling procedures with container comparison. L4 extension: remediation engineering, oil-paper interaction, retrofilling decisions. |
| **Task Doc** | `Development/TASK-DESKTOPCLAUD-GUIDE6-INSULATING-FLUIDS.md` |
| **Notes** | Bounded v2.4 integration completed 2026-03-26 and downstream reload completed 2026-03-27 with UUID reuse. The live row matches the staged v2.4 guide body, and the packet-local loader config now uses the explicit 22-code full-KSA set that matches the guide's actual level-specific coverage, closing the earlier false missing-row residue. |

---


---

### Guide #7A — LV Switchgear, Switchboards & Panelboards

| Field | Value |
|-------|-------|
| **File** | `Development/staging/lv-switchgear/SG-CT-LV-SWITCHGEAR.md` |
| **content_id** | SG-CT-LV-SWITCHGEAR |
| **NETA Section** | 7.1.1 (LV) + 7.1.2 |
| **KSA Coverage** | CT-001 through CT-004 (L2/L3/L4) — LV portion |
| **Pipeline** | New Material (4 CT-FILLED sections + scaffold) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 783ac855-79c... |
| **Quality Grade** | A− |
| **Lines** | 1,246 |
| **Word Count** | 15,009 |
| **VERIFY flags** | 0 |
| **v2.4 Sections** | All present (Scope Note, Learning Objectives, Retention Snapshot, per-level Further Study, teaching bridges) |
| **Sources consumed** | 4 CT-FILLED files + scaffold + lv-switchgear-data-packet.json + panelboard-assemblies-data-packet.json + ATS-2025-equipment-tests.json + ATS-2025-tables-extracted.json |
| **Key corrections** | Dielectric withstand ATS-required/MTS-optional (cross-check). Control wiring IR optional, 500V/1000V, 2 MO min (cross-check). Table 100.18 severity corrected to actual ATS values. Test 6 fully rewritten by Desktop Claude (DC vs AC field practice, proportional caution). Summary table upgraded to ATS/MTS split columns. |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config created 2026-03-27: `Development/staging/lv-switchgear/lv-switchgear-config.json`) |
| **Notes** | v2.4 integration completed 2026-03-27 (instructional-deficit reopen). Supabase reload completed 2026-03-27 with UUID reuse (`783ac855-79cc-4b75-826c-4191a23fa337`); live `body_markdown` now matches the staged v2.4 guide. |

---

### Guide #7B — MV Switchgear (Metal-Clad & MEI)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/mv-switchgear/SG-CT-MV-SWITCHGEAR.md` |
| **content_id** | SG-CT-MV-SWITCHGEAR |
| **NETA Section** | 7.1.1 (MV) |
| **KSA Coverage** | CT-001 through CT-004 (L2/L3/L4) — MV portion |
| **Pipeline** | Consolidation (N3 #26 MV + N4 CT-001-004 MV + new L2) |
| **Status** | ✅ LOADED — `status: draft` in Supabase (updated Mar 14) |
| **Supabase UUID** | 4252b649-7721-40f0-92fb-380a4ba42346 |
| **Quality Grade** | A− |
| **Lines** | 1,177 |
| **Word Count** | 17,987 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 9 (mc-eight-features-diagram, mc-vs-mei-comparison, mc-compartment-layout, mc-four-breaker-positions, mc-shutter-operation, mc-moc-toc-contact-wiring, mei-visible-break-gap, mc-ir-test-connections, mc-breaker-cell-open) |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, bounded KSA body, publication-clean threshold handling, quick-reference retention support, and learner-facing further-study guidance |
| **Resource Audit** | RESOURCE-AUDIT-GUIDE-07-SWITCHGEAR.md (March 8, 2026) |
| **Key Sources** | C37.20.2-2022 (049), C37.20.3-2023 (050), C37.20.6 (055), Paul Gill Ch 7, Castell trapped-key interlocks |
| **KSA Links** | 39 (body_content_discovery: 29 STRONG + 10 MODERATE) |
| **Loader** | `Development/staging/mv-switchgear/load_guide_7b.py` |
| **Task Doc** | `Development/staging/mv-switchgear/TASK-VSCODE-LOAD-7B.md` |
| **Notes** | Guide assembled prior to Mar 14 IMG pass. Bounded v2.4 integration completed 2026-03-26; front matter, visible threshold placeholders, quick-reference retention framing, and learner-facing cross-reference language were cleaned without widening into a broader switchgear-family rewrite. Separate Supabase reload remains intentionally deferred. |

---

### Guide #7C — Metal-Enclosed Gas-Insulated Switchgear (MEGIS)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/gis-switchgear/SG-CT-MEGIS-SWITCHGEAR.md` |
| **content_id** | SG-CT-MEGIS-SWITCHGEAR |
| **NETA Section** | 7.1.1 (GIS tested as switchgear assembly) |
| **KSA Coverage** | CT-001 through CT-004 (L2/L3/L4) — MEGIS portion |
| **Pipeline** | New Material (4 CT-FILLED sections + scaffold) |
| **Status** | ✅ LOADED + REVIEWED — reloaded in place 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | f6efab55-e77e-4c5a-be27-be5eef48062e |
| **KSA Links** | 29 (body_content_discovery: 23 STRONG + 6 MODERATE) |
| **Quality Grade** | A− |
| **Lines** | 1,080 |
| **Word Count** | 16,842 |
| **VERIFY flags** | 0 — 2 closed (Schneider SM AirSeT, Eaton Xiria → "consult manufacturer" per calciumite rule) |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, quick-reference retention support, and learner-facing cross-reference / further-study cleanup without broadening the guide boundary |
| **Sources consumed** | IEEE C37.20.9-2019 + C37.20.9a-2024 (Table 1, Table 9, Annex C, Clauses 6.12-6.13, 7.2.5, 9), ABB ZX2/SafeRing/SafePlus manuals, Siemens 8DJH/8DA10/8DB10 documentation, NETA ATS Tables 100.1/100.18 |
| **Key corrections** | Field dielectric test = 75% of factory (Table 9), NOT 80% (Clause 7.2.12). IR test does not apply to gas-insulated bus. |
| **CT authorship** | CT-001/002: Claude Code; CT-003/004: Desktop Claude |
| **Loader** | `Development/load_guide_7c.py` |
| **Task Doc** | `Development/staging/gis-switchgear/TASK-VSCODE-ASSEMBLE-7C.md` |
| **Notes** | Bounded v2.4 integration completed 2026-03-26 and downstream reload completed 2026-03-27 with UUID reuse; the live row now matches the staged v2.4 guide body exactly. |

---

### Guide #7D — High-Voltage Gas-Insulated Substations (HV GIS)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/hv-gis/SG-CT-HV-GIS.md` |
| **content_id** | SG-CT-HV-GIS |
| **NETA Section** | 7.1.1 (GIS tested as switchgear assembly) |
| **KSA Coverage** | CT-001 through CT-004 (L3/L4) — HV GIS portion |
| **Pipeline** | New Material (4 CT-FILLED sections + scaffold) |
| **Status** | ✅ LOADED + REVIEWED — `status: draft` in Supabase |
| **Supabase UUID** | c0ff2e1e-805a-40c4-9c83-79b85318e2f9 |
| **KSA Links** | 37 (body_content_discovery: 6 STRONG + 31 MODERATE) |
| **Quality Grade** | A |
| **Lines** | 626 |
| **Word Count** | 7,802 |
| **VERIFY flags** | 0 — none found during review |
| **v2.3 Sections** | ✅ All present — 4 KSA sections (CT-001:004), field scenarios, common mistakes, QR tables |
| **Sources consumed** | IEEE C37.122-2010, C37.122.1-2014, C37.123-2023, NETA ATS Tables 100.1/100.18, Siemens 8DQ1, ABB ELK, Hitachi Energy GIS documentation |
| **Key facts** | 80% field test values correct throughout, 5 pC PD limit consistent, Level III/IV audience |
| **Loader** | `Development/load_guide_7d.py` |

---

### Guide #9A — LV Cable Testing (600V Maximum)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/cable-testing-lv/SG-CT-CABLE-TESTING-LV.md` |
| **content_id** | SG-CT-CABLE-TESTING-LV |
| **NETA Section** | 7.3.2 |
| **KSA Coverage** | CT-010, CT-012, CT-013, CT-014 (L2/L3/L4) |
| **Pipeline** | New Material (single-file, no scaffold+fill) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | c5c55501-ce2a-41d3-8faf-9f7a6664edda |
| **Quality Grade** | TBD (pending review) |
| **Lines** | 445 |
| **Word Count** | 5,693 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 2 |
| **KSA Links** | 12 (deterministic_content_id: CT-010, CT-012, CT-013, CT-014 × L2/L3/L4, all full coverage, confidence 1.0) |
| **v2.4 Sections** | ✅ All present — 4 KSA sections, field scenarios, common mistakes, QR tables |
| **Key content** | Connection resistance, IR (500V/1000V), continuity, parallel conductors, Table 100.1 Note 6, MTS 2 MΩ floor vs trending |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` + `Development/staging/cable-testing-lv/cable-testing-lv-config.json` |
| **Task Doc** | `Development/staging/cable-testing-lv/TASK-VSCODE-LV-CABLE-TESTING-LOAD.md` |
| **Notes** | CT-011 (cable accessories) excluded — belongs in planned Guide #9B. Structure map at staging/CABLE-TESTING-STRUCTURE-MAP.md. Bounded v2.4 integration and Supabase reload completed 2026-03-26; internal process residue was removed, learner-facing framing was strengthened, and the live draft UUID was reused with `CONTENT-FORMAT-SPEC v2.4` metadata. |

---

### Guide #9B — MV/HV Cable Testing

| Field | Value |
|-------|-------|
| **File** | `Development/staging/cable-testing-mv/SG-CT-CABLE-TESTING-MV.md` |
| **content_id** | SG-CT-CABLE-TESTING-MV |
| **NETA Section** | 7.3.3 |
| **KSA Coverage** | CT-010 through CT-014 (L2/L3/L4) |
| **Pipeline** | New Material (scaffold + 5 CT-FILLED sections) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 564e0422-c420-4b6e-8ebc-a8a1a9e4ca55 |
| **KSA Links** | 15 (deterministic_content_id: 5 KSAs × L2/L3/L4, all full coverage, confidence 1.0) |
| **Quality Grade** | A− |
| **Lines** | 781 |
| **Word Count** | 13,996 |
| **VERIFY flags** | 0 |
| **v2.4 Sections** | ✅ All present — 5 KSA sections (CT-010:014), field scenarios, common mistakes, QR tables, standards ref |
| **Sources consumed** | Scaffold (Desktop) + CT-010/011/012 fills (CC) + CT-013/CT-014 fills (Desktop rewrite) + cable-testing-mv-data-packet.json |
| **Key content** | VLF, tan delta, partial discharge, DC hipot, XLPE/EPR/PILC, shield bonding, IR, cable accessories, terminations, splices, separable connectors, IEEE 400 series |
| **CT authorship** | CT-010/011/012: Claude Code; CT-013/014: Desktop Claude (rewrite spliced Mar 9) |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` + `Development/staging/cable-testing-mv/cable-testing-mv-config.json` |
| **Task Docs** | `TASK-VSCODE-9B-ASSEMBLE-LOAD.md`, `TASK-VSCODE-SPLICE-DESKTOP-REWRITE.md` |
| **Notes** | Initial assembly + Supabase INSERT at 22:36 UTC. Desktop CT-013/CT-014 rewrite spliced at 23:24 UTC (commit a11f328). Metadata restored at 23:45 UTC. Bounded v2.4 integration and Supabase reload completed 2026-03-26; the live draft UUID was reused and now carries `CONTENT-FORMAT-SPEC v2.4` metadata. |

---

### Guide #9C -- Cable Fault Location

| Field | Value |
|-------|-------|
| **File** | `Development/staging/cable-fault-location/SG-CT-CABLE-FAULT-LOCATION.md` |
| **content_id** | SG-CT-CABLE-FAULT-LOCATION |
| **NETA Section** | 7.3.2 (cross-ref 7.3.3) |
| **KSA Coverage** | CT-015 (L2/L3/L4) |
| **Pipeline** | New Material (single-file, no scaffold+fill) |
| **Status** | \u2705 LOADED -- reloaded in place 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | f0670b2a-9e40-4d7b-96a1-85a550b52c79 |
| **KSA Links** | 3 (deterministic_content_id: CT-015 x L2/L3/L4, all full coverage, confidence 1.0) |
| **Quality Grade** | TBD (pending review) |
| **Lines** | 738 |
| **Word Count** | 8,367 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 1 (tdr-reflection-polarity) |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, bounded single-KSA body, quick-reference retention support, and learner-facing further-study guidance |
| **Sources consumed** | IEEE Std 1234-2019 extraction (392 lines), NETA-Equipment-Category-Standard.md, cable-testing-mv-data-packet.json |
| **Key content** | TDR, thumping, surge arc reflection, Murray/Glaser bridges, acoustic/electromagnetic pinpointing, 7 IEEE 1234 formulas, all 8 fault types, technique selection matrix |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` via `Development/staging/cable-fault-location/cable-fault-location-config.json` |
| **Notes** | Single KSA guide (CT-015 only). Scaffold notes stripped before load. Desktop authored, VS Code loaded. Bounded v2.4 integration completed 2026-03-26, and the downstream reload completed 2026-03-27 with UUID reuse; the live row now matches the staged v2.4 guide body exactly. |

---

### Guide #10A — Current Transformers

| Field | Value |
|-------|-------|
| **File** | `Development/staging/instrument-transformers/SG-IT-CURRENT-TRANSFORMERS.md` |
| **content_id** | SG-IT-CURRENT-TRANSFORMERS |
| **NETA Section** | 7.10.1 |
| **KSA Coverage** | CT-040 through CT-043 (L2/L3/L4) |
| **Pipeline** | New Material (3-workstream parallel: CC-A, CC-B, Desktop) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | dcb50ba4-9a78-475e-85c8-6a756c2b08ec |
| **Quality Grade** | A− |
| **Lines** | 1,406 |
| **Word Count** | 21,450 |
| **VERIFY flags** | 0 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, bounded KSA body, publication-clean threshold handling, quick-reference retention support, and learner-facing standards/further-study cleanup |
| **Sources consumed** | EXT-IEEE-057 (C57.13.1), EXT-IEC-002 (IEC 61869-2), EXT-MFR-037/038 (Omicron), Valence CT Testing, ABB ratings |
| **CT authorship** | CT-040: CC-A; CT-041: CC-B; CT-042/043: Desktop; Shared blocks: Desktop; Quick Ref + Scenarios: Desktop |
| **Assembly** | `assemble_10a.py` |
| **Notes** | Assembled Mar 14. Overlap boundary with #4A: this guide = CT as apparatus under test; #4A = CT from relay perspective. Bounded v2.4 integration completed 2026-03-26; learner-facing threshold placeholders and shared publication residue were removed, and the guide now honestly qualifies as `CONTENT-FORMAT-SPEC v2.4`. Reload completed 2026-03-27 via the packet-local generic-loader config with UUID reuse; the live row now matches the staged v2.4 body with `format_version: v2.4`, `line_count: 1406`, and `words: 21450`. |

---

### Guide #10B — Voltage Transformers

| Field | Value |
|-------|-------|
| **File** | `Development/staging/instrument-transformers/SG-IT-VOLTAGE-TRANSFORMERS.md` |
| **content_id** | SG-IT-VOLTAGE-TRANSFORMERS |
| **NETA Section** | 7.10.2 |
| **KSA Coverage** | CT-040 through CT-043 (L2/L3/L4) |
| **Pipeline** | New Material (3-workstream parallel: CC-A, CC-B, Desktop) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 9cdfb4e1-d704-48ef-ab01-7812ab4cdf95 |
| **Quality Grade** | A− |
| **Lines** | 1,233 |
| **Word Count** | 14,113 |
| **VERIFY flags** | 0 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, VT-specific safety/common-mistakes/field-tips cleanup, quick-reference retention support, and learner-facing further-study guidance |
| **Sources consumed** | EXT-IEC-001 (IEC 61869-3), EXT-MFR-037/038 (Omicron), ABB ratings, Paul Gill Ch. 9 |
| **CT authorship** | CT-040: CC-A; CT-041: CC-B; CT-042/043: Desktop; Shared blocks: Desktop; Quick Ref + Scenarios: Desktop |
| **Assembly** | `assemble_10b.py` |
| **Notes** | Assembled Mar 14. Bounded v2.4 integration completed 2026-03-26; visible threshold placeholders were replaced with publication-clean standards-driven wording, shared CT residue was removed from support sections, and the guide now honestly qualifies as `CONTENT-FORMAT-SPEC v2.4`. Reload completed 2026-03-27 via the packet-local generic-loader config with UUID reuse; the live row now matches the staged v2.4 body with `format_version: v2.4`, `line_count: 1233`, and `words: 14113`. |

---

### Guide #10C — Coupling-Capacitor Voltage Transformers (CCVTs)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/instrument-transformers/SG-IT-CCVT.md` |
| **content_id** | SG-IT-CCVT |
| **NETA Section** | 7.10.3 |
| **KSA Coverage** | CT-040 through CT-043 (L3/L4) |
| **Pipeline** | New Material (3-workstream parallel: CC-A, CC-B, Desktop) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 6d19a83b-2f0a-41d9-85fb-a8a90000a541 |
| **Quality Grade** | A− |
| **Lines** | 1,231 |
| **Word Count** | 16,920 |
| **VERIFY flags** | 0 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, CCVT-specific safety/common-mistakes/field-tips cleanup, quick-reference retention support, and learner-facing further-study guidance |
| **Sources consumed** | EXT-IT-003 (CVT Testing), EXT-MFR-037 (Omicron PF), EXT-MFR-038, EXT-IEEE-069 (C57.13.5) |
| **CT authorship** | CT-040: CC-A; CT-041: CC-B; CT-042/043: Desktop; Shared blocks: Desktop; Quick Ref + Scenarios: Desktop |
| **Assembly** | `assemble_10c.py` |
| **Key content** | Capacitive divider + IVT, PF test configurations (single-unit/two-unit tables), short circuit impedance, ferroresonance, subsidence transient, DFR/moisture assessment, cross-test diagnostic matrix, replacement vs remediation criteria |
| **Notes** | Assembled Mar 14. L3/L4 only. Bounded v2.4 integration completed 2026-03-26; visible IR / ratio / MTS placeholder residue was normalized into publication-clean learner-facing wording, shared family support-layer residue was removed, and the guide now honestly qualifies as `CONTENT-FORMAT-SPEC v2.4`. Reload completed 2026-03-27 via the packet-local generic-loader config with UUID reuse; the live row now matches the staged v2.4 body with `format_version: v2.4`, `line_count: 1231`, and `words: 16920`. |

---

### Guide #10D — High-Accuracy Instrument Transformers (LPITs)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/instrument-transformers/SG-IT-HIGH-ACCURACY.md` |
| **content_id** | SG-IT-HIGH-ACCURACY |
| **NETA Section** | 7.10.4 |
| **KSA Coverage** | CT-040 through CT-043 (L3/L4) |
| **Pipeline** | New Material (3-workstream parallel: CC-A, CC-B, Desktop) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 5cd61e06-34d9-42a5-a9db-a3a2adf8eebd |
| **Quality Grade** | A− |
| **Lines** | 1,037 |
| **Word Count** | 15,799 |
| **VERIFY flags** | 0 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, LPIT-specific further-study guidance, quick-reference retention support, and publication-clean boundary/cross-reference language |
| **Sources consumed** | EXT-IEC-003 (IEC 61869-6), EXT-IEEE-069 (C57.13.5), EXT-MFR-038 |
| **CT authorship** | CT-040: CC-A; CT-041: CC-B; CT-042/043: Desktop; Shared blocks: Desktop; Quick Ref + Scenarios: Desktop |
| **Assembly** | `assemble_10d.py` |
| **Key content** | Rogowski coils (integrator verification, drift), optical sensors (Faraday/Pockels), iron-core LPCTs, IEC 61869-6 harmonic accuracy classes, frequency response masks, anti-aliasing filters, EMC immunity (15 tests), delay time, LPIT failure modes, burden sensitivity at 0.1%/0.2% class |
| **Notes** | Assembled Mar 14. ATS-only (§7.10.4 MTS Reserved). Technology-by-technology structure. Conventional IT tests do not apply to most LPIT types. Bounded v2.4 cleanup completed 2026-03-26; front matter, shared-tail cleanup, and LPIT-specific further-study guidance now honestly align the guide to `CONTENT-FORMAT-SPEC v2.4`. Reload completed 2026-03-27 via the packet-local generic-loader config with UUID reuse; the live row now matches the staged v2.4 body with `format_version: v2.4`, `line_count: 1037`, and `words: 15799`. |

---

### Guide #20 — Metal-Enclosed Busways

| Field | Value |
|-------|-------|
| **File** | `Development/staging/busways/SG-CT-BUSWAYS.md` |
| **content_id** | SG-CT-BUSWAYS |
| **NETA Section** | 7.4 |
| **KSA Coverage** | CT-016 through CT-019 (L2/L3/L4) |
| **Pipeline** | v2 (demo guide — generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — reloaded 2026-03-27 in place; `status: draft` in Supabase |
| **Supabase UUID** | 23d7b204-... |
| **Quality Grade** | TBD (Desktop retrospective) |
| **Lines** | 1,265 |
| **Word Count** | 15,490 |
| **IMG tags** | 6 |
| **VERIFY flags** | 0 |
| **KSA Links** | 38 (20 STRONG + 18 MODERATE) |
| **v2.3 Sections** | ✅ All present — 4 KSA sections (CT-016:019), safety, common mistakes, quick ref, field scenarios, field tips, standards ref, further study |
| **Sources consumed** | IEEE C37.23-2015, NEMA BU 1.1-2000, IEC 61439-6:2012, NETA ATS-2025 §7.4, EXT-IEC-004, EXT-IEEE-052 |
| **Assembly** | `assemble_guide.py` (pipeline v2) |
| **Key content** | 4 bus types (nonsegregated, segregated, isolated-phase, cable bus), feeder vs plug-in, joint torque verification, IR testing per Table 100.1, dielectric withstand per Table 100.17, DLRO micro-ohm thresholds, thermographic survey, diagnostic correlation flowchart |
| **Notes** | First guide produced by pipeline v2. NETA ATS as structural backbone for CC fills. 6 IMG tags placed by insert_img_tags.py. |

---

### Guide #21 — Outdoor Bus Structures

| Field | Value |
|-------|-------|
| **File** | `Development/staging/outdoor-bus-structures/SG-CT-OUTDOOR-BUS-STRUCTURES.md` |
| **content_id** | SG-CT-OUTDOOR-BUS-STRUCTURES |
| **NETA Section** | 7.21 |
| **KSA Coverage** | CT-076 through CT-079 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — canonical v2.4 row inserted 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | c5942539-... |
| **Quality Grade** | TBD (Desktop retrospective) |
| **Lines** | 982 |
| **Word Count** | 13,634 |
| **IMG tags** | 6 |
| **VERIFY flags** | 0 pipeline markers (earlier 36 were false-positive natural `verify` uses) |
| **KSA Links** | 35 (12 full + 23 partial) |
| **v2.3 Sections** | ✅ All present — 4 KSA sections (CT-076:079), safety, common mistakes, quick ref, field scenarios, field tips, standards ref, further study |
| **Sources consumed** | IEEE 605, IEEE C37.23-2015, NETA ATS-2025 §7.21 |
| **Assembly** | `assemble_guide.py` (pipeline v2) |
| **Key content** | Rigid bus, strain bus, substation bus types, tubular/channel conductors, insulator testing, bus joint resistance, thermal expansion, seismic considerations, corona/RIV testing |
| **Notes** | Second pipeline v2 guide. Wave 1 batch. v2.4 reload now lives under canonical content_id `SG-CT-OUTDOOR-BUS-STRUCTURES`; the earlier `SG-CT-OUTDOOR-BUS` draft row was retired on 2026-03-27 after dependency cleanup. |

---

### Guide #22 — Ground-Fault Protection Systems (Low-Voltage)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/ground-fault-protection-systems-low-voltage/SG-CT-GROUND-FAULT-PROTECTION-SYSTEMS-LO.md` |
| **content_id** | SG-CT-GROUND-FAULT-PROTECTION-LV |
| **NETA Section** | 7.14 |
| **KSA Coverage** | CT-053 through CT-056 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | c8232825-... |
| **Lines** | 1,642 |
| **Word Count** | 17,782 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 |
| **v2.4 Sections** | All present (Scope Note, Learning Objectives, Retention Snapshot, per-level Further Study) |
| **Sources consumed** | EXT-MFR-039 (Eaton GFP), NETA ATS-2025 ?7.14, CC-filled scaffolds |
| **Key content** | GFP sensor types, zero-sequence vs residual, pickup/timing verification, Zone Selective Interlocking, ground-fault coordination |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (preferred) or `load_guide_22.py` |
| **Notes** | Emergency systems quartet member. First of 4 guides batch-prepped Mar 15. v2.4 integration completed 2026-03-27 (instructional-deficit reopen). Supabase reload completed 2026-03-27 with UUID reuse (`c8232825-35ca-437b-b97e-273eb20b24cb`); live `body_markdown` now matches the staged v2.4 guide. |

---

### Guide #23 — Emergency Systems: Automatic Transfer Switches

| Field | Value |
|-------|-------|
| **File** | `Development/staging/emergency-systems-automatic-transfer-switches/SG-CT-EMERGENCY-SYSTEMS-AUTOMATIC-TRANSF.md` |
| **content_id** | SG-CT-EMERGENCY-SYSTEMS-AUTOMATIC-TRANSF |
| **NETA Section** | 7.22.3 |
| **KSA Coverage** | CT-080 through CT-083 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — reloaded in place 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | b4fbe8fd-... |
| **Lines** | 1,651 |
| **Word Count** | 15,904 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, normalized numbered section spine, quick-reference retention support, and publication-clean standards / further-study cleanup |
| **Sources consumed** | EXT-MFR-040 through 047 (ASCO, Russelectric, Eaton ATS), EXT-IND-020, NETA ATS-2025 §7.22.3 |
| **Key content** | Open/closed transition, bypass-isolation, MV transfer, exerciser testing, NFPA 110 performance verification, withstand/available ratings |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_23.py` |
| **Notes** | Emergency systems quartet member. Shares extraction base with #24 Gen and #25 UPS. Bounded v2.4 integration completed 2026-03-26, and downstream reload completed 2026-03-27 with UUID reuse; the live row now matches the staged v2.4 guide body exactly. |

---

### Guide #24 — Emergency Systems: Engine Generator

| Field | Value |
|-------|-------|
| **File** | `Development/staging/emergency-systems-engine-generator/SG-CT-EMERGENCY-SYSTEMS-ENGINE-GENERATOR.md` |
| **content_id** | SG-CT-EMERGENCY-SYSTEMS-ENGINE-GENERATOR |
| **NETA Section** | 7.22.1 |
| **KSA Coverage** | CT-082 through CT-085 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — reloaded in place 2026-03-27; `status: draft` in Supabase |
| **Supabase UUID** | 1ebe3a53-e21f-4d8a-b479-d8509f2d1421 |
| **Lines** | 1,456 |
| **Word Count** | 13,293 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, learner-facing opening bridge, retention support, and companion progression guidance |
| **Sources consumed** | IEEE 43 (IR/PI/DAR), NFPA 110, NETA ATS-2025 §7.22.1, CC-filled scaffolds |
| **Key content** | IR/PI/DAR testing, protection relay verification, NFPA 110 performance testing, load bank testing, Table 100.11 temperature correction, ambient temperature derating |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config: `Development/staging/emergency-systems-engine-generator/emergency-systems-engine-generator-config.json`) |
| **Notes** | Emergency systems quartet member. Phoenix heat derating stop-and-communicate scenario. Bounded v2.4 integration completed 2026-03-27, and downstream reload completed the same day with UUID reuse; the live `body_markdown` now matches the staged v2.4 guide exactly. |

---

### Guide #25 — Emergency Systems: Uninterruptible Power Systems

| Field | Value |
|-------|-------|
| **File** | `Development/staging/emergency-systems-uninterruptible-power-systems/SG-CT-EMERGENCY-SYSTEMS-UPS.md` |
| **content_id** | SG-CT-EMERGENCY-SYSTEMS-UPS |
| **NETA Section** | 7.22.2 |
| **KSA Coverage** | CT-080 through CT-083 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | a99a97e3-4e11-4032-839c-1567e4615214 |
| **Lines** | 1,502 |
| **Word Count** | 14,245 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 |
| **v2.4 Sections** | ✅ All present |
| **Sources consumed** | EXT-IEC-62040-3 (UPS performance), EXT-UL-1778, NETA ATS-2025 §7.22.2, CC-filled scaffolds |
| **Key content** | UPS topologies (online/line-interactive/standby), battery testing (IEEE 450/1188), bypass/maintenance modes, Table 100.12, lithium-ion manufacturer-first approach |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` + `Development/staging/emergency-systems-uninterruptible-power-systems/emergency-systems-uninterruptible-power-systems-config.json` |
| **Notes** | Emergency systems quartet member. CC Table 100.12 marker resolved during assembly. Bounded v2.4 integration and Supabase reload completed 2026-03-26: live guide identity is now normalized to `SG-CT-EMERGENCY-SYSTEMS-UPS`, the new live UUID is `a99a97e3-4e11-4032-839c-1567e4615214`, and the legacy `SG-CT-EMERGENCY-SYSTEMS-UNINTERRUPTIBLE` row was marked `metadata.superseded_by=SG-CT-EMERGENCY-SYSTEMS-UPS`. |

---

### Guide #26 — Surge Protective Devices, Low-Voltage

| Field | Value |
|-------|-------|
| **File** | `Development/staging/surge-protective-devices-low-voltage/SG-CT-LV-SPD.md` |
| **content_id** | SG-CT-LV-SPD |
| **NETA Section** | 7.19.1 |
| **KSA Coverage** | CT-068 through CT-071 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 59fc1179-8abf-48a9-b994-839bdc6d2716 |
| **Lines** | 1,092 |
| **Word Count** | 14,173 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 (deterministic_content_id: CT-068–071 × L2/L3/L4) |
| **v2.4 Sections** | All present (Scope Note, Learning Objectives, Retention Snapshot, per-level Further Study, teaching bridges) |
| **Sources consumed** | IEEE C62.41.1-2002, IEEE C62.42.4-2020, IEEE C62.62-2000, IEEE C62.72a-2020, UL 1449, NETA ATS-2025 §7.19.1 |
| **Key content** | SPD types (1/2/3), UL 1449, VPR, SCCR, surge counters, LED indicators, ground connection, IEEE C62 series |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config: `Development/staging/surge-protective-devices-low-voltage/surge-protective-devices-low-voltage-config.json`) |
| **Notes** | Surge protection pair (with #27). v2.4 integration completed 2026-03-27 and Supabase reload completed the same day with UUID reuse (`59fc1179-8abf-48a9-b994-839bdc6d2716`); live `body_markdown` now matches the staged guide. |

---

### Guide #27 — Surge Arresters, Medium- and High-Voltage

| Field | Value |
|-------|-------|
| **File** | `Development/staging/surge-arresters-medium-and-high-voltage/SG-CT-MV-HV-SURGE-ARRESTERS.md` |
| **content_id** | SG-CT-MV-HV-SURGE-ARRESTERS |
| **NETA Section** | 7.19.2 |
| **KSA Coverage** | CT-068 through CT-071 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 8974e6ca-58a1-4b71-9d82-3ee7eb60fa7f |
| **Lines** | 1,336 |
| **Word Count** | 17,298 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 (deterministic_content_id: CT-068–071 × L2/L3/L4) |
| **v2.4 Sections** | All present (Scope Note, Learning Objectives, Retention Snapshot, per-level Further Study, teaching bridges) |
| **Sources consumed** | IEEE C62.11-2020, IEEE C62.22-1997, IEEE C62.22a-2013, ABB MV SA, Hitachi Energy MV SA, Siemens Station/Intermediate SA, NETA ATS-2025 §7.19.2 |
| **Key content** | MOSA, station/intermediate/distribution class, MCOV, protective level, watts-loss, insulation coordination, lightning protection, pressure relief, deadfront, Batch 6 enhancements (dual-rating, FOW two-value, temp derating, ground lead lengths) |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` (config: `Development/staging/surge-arresters-medium-and-high-voltage/surge-arresters-medium-and-high-voltage-config.json`) |
| **Notes** | Surge protection pair (with #26). Batch 6 enhancements applied before assembly. v2.4 integration completed 2026-03-27 and Supabase reload completed the same day with UUID reuse (`8974e6ca-58a1-4b71-9d82-3ee7eb60fa7f`); live `body_markdown` now matches the staged guide. |

---

### Guide #29A — Circuit Breakers, Low-Voltage (LOADED)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/circuit-breakers-lv/SG-CT-CB-LV.md` |
| **content_id** | SG-CT-CB-LV |
| **NETA Section** | 7.6.1.1.1 + 7.6.1.1.2 + 7.6.1.2 |
| **KSA Coverage** | CT-024 through CT-027 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py with shared_source) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 8219a30c-4e7c-4eaf-9ffa-5c23d2e31421 |
| **Lines** | 1,343 |
| **Word Count** | 18,650 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 (deterministic_content_id: CT-024–027 × L2/L3/L4, all full coverage, confidence 1.0) |
| **v2.4 Sections** | ✅ All present — 4 KSA sections (CT-024:027), safety, common mistakes, quick ref, field scenarios, field tips, standards ref, further study |
| **Sources consumed** | IEEE C37.20.1-2015, IEEE 3004.5-2014, UL 489, Megger CB Testing Guide, NETA ATS-2025 §7.6.1 |
| **Key content** | MCCB (Molded Case), ICCB (Insulated Case), LV Power CB. Every tech, every job. |
| **Shared pool** | `circuit-breakers-shared/` — DLRO, IR, contact resistance, timing, trip/close coil, device function numbers, safety, common mistakes |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` + `Development/staging/circuit-breakers-lv/cb-lv-config.json` |
| **Notes** | Part of CB 3-way split (with #29B MV, #29C HV). Highest-priority CB guide. Assembled + loaded Mar 18, 2026. Bounded v2.4 integration and Supabase reload completed 2026-03-26; the live draft UUID was reused and now carries `CONTENT-FORMAT-SPEC v2.4` metadata with 12 deterministic KSA links in place. |

---

### Guide #29B — Circuit Breakers, Medium-Voltage (LOADED)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/circuit-breakers-mv/SG-CT-CB-MV.md` |
| **content_id** | SG-CT-CB-MV |
| **NETA Section** | 7.6.1.3 + 7.6.3 |
| **KSA Coverage** | CT-024 through CT-027 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py with shared_source) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | f680683b-4588-4bea-b470-15cf419c0240 |
| **Lines** | 1,501 |
| **Word Count** | 18,073 |
| **VERIFY flags** | 0 |
| **KSA Links** | 0 (CT-024–027 not yet in edition_ksa_map — links pending) |
| **Format / structure** | `CONTENT-FORMAT-SPEC v2.4` present -- scope note, learning objectives, 4 KSA sections (CT-024:027), quick-reference retention support, and MV-centered further-study guidance |
| **Sources consumed** | IEEE C37.20.2-2022, IEEE C37.09-2019, IEEE C37.04-2018, Megger CB Testing Guide, NETA ATS-2025 §7.6.1.3, §7.6.3 |
| **Key content** | Air MV + Vacuum MV. Both are MV interrupting technologies in metal-clad switchgear (C37.20.2). Substation/switchgear techs. |
| **Shared pool** | `circuit-breakers-shared/` — DLRO, IR, contact resistance, timing, trip/close coil, device function numbers, safety, common mistakes |
| **Loader** | `Development/Scripts/Load/Guides/load_cb_guides.py` |
| **Notes** | Part of CB 3-way split. Air+Vacuum grouped. Assembled + loaded Mar 18, 2026. Bounded v2.4 integration completed 2026-03-26; the technical body was preserved while front matter, retention support, and learner-facing study progression were normalized. Reload completed in place on 2026-03-26 with UUID reuse. |

---

### Guide #29C — Circuit Breakers, High-Voltage (LOADED)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/circuit-breakers-hv/SG-CT-CB-HV.md` |
| **content_id** | SG-CT-CB-HV |
| **NETA Section** | 7.6.2 + 7.6.4 |
| **KSA Coverage** | CT-024 through CT-027 (L2/L3/L4) |
| **Pipeline** | v2 (generate_scaffold.py + assemble_guide.py with shared_source) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | 9016a40a-3ccc-438b-b2b3-a19be0294709 |
| **Lines** | 1,609 |
| **Word Count** | 23,579 |
| **VERIFY flags** | 0 |
| **KSA Links** | 12 (deterministic_content_id: CT-024–027 × L2/L3/L4, all full coverage, confidence 1.0) |
| **Image placeholders** | 1 |
| **v2.4 Sections** | ✅ All present — 4 KSA sections (CT-024:027), safety, common mistakes, quick ref, field scenarios, field tips, standards ref, further study |
| **Sources consumed** | IEEE C37.20.3-2013, IEEE C37.09-2019, IEEE C37.10-2011, IEEE C37.122-2021, IEC 62271-series, Megger CB Testing Guide, NETA ATS-2025 §7.6.2, §7.6.4 |
| **Key content** | Oil MV/HV + SF6. Both require specialized fluid/gas analysis. Station/utility techs. |
| **Shared pool** | `circuit-breakers-shared/` — DLRO, IR, contact resistance, timing, trip/close coil, device function numbers, safety, common mistakes |
| **Loader** | `Development/Scripts/Load/Guides/load_guide_generic.py` + `Development/staging/circuit-breakers-hv/cb-hv-config.json` |
| **Notes** | Part of CB 3-way split. Oil+SF6 grouped. Assembled + loaded Mar 18, 2026. Bounded v2.4 integration and Supabase reload completed 2026-03-26; learner-facing framing was modernized, a basic visual support layer was added, and the live draft UUID was reused with `CONTENT-FORMAT-SPEC v2.4` metadata. |

---

### Guide #30 — Rotating Machinery (AC Induction, Synchronous, DC)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/rotating-machinery/SG-CT-ROTATING-MACHINERY.md` |
| **content_id** | SG-CT-ROTATING-MACHINERY |
| **NETA Section** | 7.15.1, 7.15.2, 7.15.3 |
| **KSA Coverage** | CT codes mapped to §7.15 (L2/L3/L4) |
| **Pipeline** | v2 (generate_topic_config.py + generate_scaffold.py + assemble_guide.py) |
| **Status** | ✅ LOADED — `status: draft` in Supabase |
| **Supabase UUID** | a127e658-cb3... |
| **Lines** | 1,873 |
| **Word Count** | 17,663 |
| **VERIFY flags** | 0 |
| **v2.3 Sections** | ✅ All present — assembled guide passed validation; IMG pass complete (9 tags) |
| **Sources consumed** | IEEE 43 (4 extraction files), IEEE 95, IEEE 112, IEEE 3004.8, Megger Baker MTR105, E05 Condition Monitoring, Electric Motor Energy Efficiency Guide, Megger Insulation Testing Guide |
| **Key content** | IR/PI/DAR testing, surge comparison, partial discharge, vibration analysis, winding resistance, temperature correction (Table 100.11), AC induction motor testing, synchronous machine testing, DC motor/generator testing, bearing assessment |
| **Scoping basis** | `Development/ETT-NEXT-GUIDE-TOPIC-SCOPING-REPORT-2026-03-24.md` |
| **Notes** | Consolidated single guide covering all 3 §7.15 entries. Staging packet was generated on 2026-03-24 at `Development/staging/rotating-machinery/`, then assembled, IMG-tagged, loaded, and KSA-discovery-complete the same day. IEEE 43 is the backbone standard for motor insulation testing. Cross-references Guide #24 (Engine Generator) for generator-specific IR/PI content and Guide #4A/4B (Protective Relays) for motor protection from the relay side. Load closed with 12/12 KSA links resolved, 16/16 concept links created, 0 uncovered KSAs, and commit `04f122a8`. DC Systems (§7.18) remains the follow-on candidate. |

---

### Guide #31 — DC Systems (Batteries, Chargers, Rectifiers Context)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/dc-systems/SG-CT-DC-SYSTEMS.md` |
| **content_id** | SG-CT-DC-SYSTEMS |
| **NETA Section** | 7.18.1.1, 7.18.1.2, 7.18.1.3, 7.18.2; rectifiers 7.18.3 reserved/context-only |
| **KSA Coverage** | CT-073 through CT-076 (L2/L3/L4) |
| **Pipeline** | v2 (hand-built multi-section config + generate_scaffold.py + generate_cc_task.py) |
| **Status** | 🔄 LOADED — CC fill complete, Desktop authoring complete, assembly + IMG pass complete, Supabase loaded 2026-03-25 |
| **Supabase UUID** | 15a3a975-d944-4752-9e05-a39271f86bb3 |
| **KSA Links** | 12 (all full coverage, deterministic): CT-073?CT-076 ? L2/L3/L4 |
| **Lines** | 1,808 (assembled) |
| **Word Count** | 24,198 |
| **VERIFY flags** | 0 |
| **Image placeholders** | 8 (IMG pass complete): (1) dc-battery-chemistry-comparison, (2) dc-vla-cell-visual-inspection, (3) dc-four-wire-connection-resistance, (4) dc-capacity-test-discharge-curve, (5) dc-nicd-capacity-aging-linear, (6) dc-ohmic-trending-thresholds, (7) dc-capacity-aging-vla-vs-nicd, (8) dc-vrla-thermal-runaway-progression. All v2.3 compliant with source attributions. |
| **v2.3 Sections** | ✅ All present — 4 KSA sections (CT-073:076), 8 field scenarios, quick ref |
| **Sources consumed** | 9 extractions: EXT-IEEE-183, EXT-IEEE-238 (IEEE 450), EXT-IEEE-241 (IEEE 2030.2.1), EXT-IEEE-249 (IEEE 1188), EXT-IEEE-301 (IEEE 1189), EXT-IEEE-303 (IEEE 1106), EXT-IEC-008 (IEC 60896), EXT-MFR-149 (Megger Battery Testing Guide), EXT-MFR-150 (Megger Station Battery Best Practices) |
| **Key content** | VLA/NiCd/VRLA battery construction and maintenance; cell voltage and specific gravity interpretation; ohmic testing (NiCd-specific finding: NOT useful for SOH); charger float/equalize settings; ripple and load-sharing checks; capacity testing (rate-adjusted vs time-adjusted); NiCd float effect, carbonation, linear aging; VRLA thermal runaway; battery-room safety and ventilation |
| **CT authorship** | CT-073/074: Claude Code; CT-075/076 + field-scenarios: Desktop Claude (Cowork) |
| **Scoping basis** | `Development/ETT-NEXT-GUIDE-TOPIC-SCOPING-REPORT-2026-03-24.md` |
| **Notes** | All content files complete. 1 DESKTOP-AUTHOR marker resolved (§7.18.3 rectifier → reserved-section stub). IEEE 1106 (EXT-IEEE-303) fully integrated across NiCd sections in CT-075, CT-076, and field-scenarios. 9 extractions consumed. Assembled 2026-03-25 as SG-CT-DC-SYSTEMS.md (1,808L / 24,198W). 8 IMG tags, all v2.3 compliant. Publication-safe citation remediation removed internal extraction shorthand from the assembled guide and the corrected guide was reloaded to Supabase on 2026-03-25 while preserving the existing UUID, 12 deterministic KSA links, and 12 derived concept links. |

---

### Guide #32 -- Safety L4 Sub-Guide A: Risk Assessment & ESWC

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-risk-assessment-eswc/SG-SF-RISK-ASSESSMENT-ESWC.md` |
| **content_id** | SG-SF-RISK-ASSESSMENT-ESWC |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-001, KSA-IV-SF-002, KSA-IV-SF-003, KSA-IV-SF-004 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED -- IMG PASS COMPLETE |
| **Supabase UUID** | dfbe1b8a-ec7e-4553-b18d-7f0fc892a559 |
| **KSA Links** | 4 (all full coverage, deterministic): KSA-IV-SF-001, KSA-IV-SF-002, KSA-IV-SF-003, KSA-IV-SF-004 |
| **Lines** | assembled guide (~329 lines of authored prose including 9 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 9 (IMG pass complete): sf-risk-hierarchy-of-controls-pyramid; sf-risk-job-hazard-analysis-workflow; sf-risk-controlled-work-zone-layout; sf-risk-shock-vs-arc-flash-boundaries; sf-risk-eswc-six-step-sequence; sf-risk-live-dead-live-test-points; sf-risk-energized-work-justification-screen; sf-risk-boundary-planning-480v-scenario; sf-risk-field-briefing-reset-triggers |
| **v2.3 Sections** | All 8 sections assembled; 9 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | 12 extractions (primary + secondary): EXT-NFPA-003 (1,648L), EXT-NFPA-012 (348L), EXT-NFPA-016 (320L), EXT-NFPA-011 (286L), EXT-NETA-HANDBOOK-II-SAF1 (793L), EXT-NETA-HANDBOOK-II-SAF2 (925L), EXT-OSHA-002 (246L), EXT-OSHA-003 (220L), EXT-OSHA-005 (286L), EXT-IEEE-193 (514L), EXT-ETT-025 (283L), EXT-FLD-035 (147L). Reference sheets: L4-RS-safety-nfpa70e, L4-RS-codes-standards |
| **Key content** | Risk assessment and ESWC leadership at L4; job hazard analysis; safe-work-environment controls; shock and arc-flash protection boundaries; NFPA 70E Art. 120 ESWC leadership and energized-work justification discipline; crew safety management |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-A-ACTIVATION.md` |
| **Notes** | First Safety L4 sub-guide (Sub-Guide A of 6). Bounded activation approved only SF-001 through SF-004 for this packet, bounded authoring/assembly was completed on 2026-03-25, and the bounded IMG pass was completed the same day with 9 compliant `sf-risk-` placeholders and no new VERIFY flags. Generic guide load completed on 2026-03-25 via `Development/Scripts/Load/Guides/load_guide_generic.py`, producing 4 deterministic KSA links and 4 derived concept links. Later explicit lane decisions advanced Sub-Guides E, B, D, C, and F into separate scaffold packets that remain unassembled. Existing published safety guides (L4-SG-SF-005, L4-SG-SF-014, L4-SG-SF-019) remain in Supabase as equal-weight boundary-awareness sources. Config and scaffold were created manually because the build scripts are CT-domain-specific. |

---

### Guide #33 -- Safety L4 Sub-Guide E: Incident Energy Analysis & Field Labeling

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-incident-energy-labels/SG-SF-INCIDENT-ENERGY-LABELS.md` |
| **content_id** | SG-SF-INCIDENT-ENERGY-LABELS |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-015, KSA-IV-SF-016, KSA-IV-SF-017, KSA-IV-SF-018 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED -- PRE-LOAD REVIEW COMPLETE -- IMG PASS COMPLETE |
| **Supabase UUID** | 3b4422a4-bc87-4641-95c2-8e844c0a4505 |
| **KSA Links** | 4 (all full coverage, deterministic): KSA-IV-SF-015, KSA-IV-SF-016, KSA-IV-SF-017, KSA-IV-SF-018 |
| **Lines** | assembled guide (627 lines of authored prose including 9 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 9 (IMG pass complete): sf-ie-label-reading-checklist; sf-ie-incident-energy-to-ppe-bridge; sf-ie-missing-label-decision-path; sf-ie-method-comparison-map; sf-ie-variable-influence-diagram; sf-ie-common-errors-panel; sf-ie-borrowed-label-stop-scenario; sf-ie-working-distance-task-change-scenario; sf-ie-field-use-reminders |
| **v2.3 Sections** | All 8 sections assembled; 9 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | 9 extractions (primary + secondary): EXT-IEEE-016 (865L), EXT-NFPA-003 (1,648L), EXT-NFPA-014 (342L), EXT-NFPA-015 (431L), EXT-NFPA-017 (775L), EXT-NFPA-018 (347L), EXT-NETA-HANDBOOK-II-AF (766L), EXT-NETA-HANDBOOK-II-SAF2 (925L), EXT-ETT-025 (283L). Reference sheets: L4-RS-safety-nfpa70e, L4-RS-codes-standards |
| **Key content** | Arc-flash label interpretation; recognizing missing or stale labels; IEEE 1584 vs NFPA 70E methods; incident energy variables; working distance and clearing-time implications; stop-and-communicate judgment when field labeling is absent or unreliable |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-E-ACTIVATION.md` |
| **Notes** | Second bounded Safety L4 packet (Sub-Guide E of 6). Scope remains limited to SF-015 through SF-018 and preserves the distinction between incident-energy interpretation and the broader codes-and-standards capstone packet. Bounded authoring, assembly, publication-safe citation review, and IMG pass were completed on 2026-03-25, producing a reader-facing assembled guide with 9 compliant `sf-ie-` placeholders and no remaining VERIFY flags. Generic guide load completed on 2026-03-25 via `Development/Scripts/Load/Guides/load_guide_generic.py`, producing 4 deterministic KSA links and 7 derived concept links. Config and scaffold were created manually because the current build scripts are still CT-domain-specific. |

---

### Guide #34 -- Safety L4 Sub-Guide B: PPE & Safety Equipment Management

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-ppe-equipment-management/SG-SF-PPE-EQUIPMENT-MANAGEMENT.md` |
| **content_id** | SG-SF-PPE-EQUIPMENT-MANAGEMENT |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-006, KSA-IV-SF-007, KSA-IV-SF-008 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED 2026-03-25 via generic guide loader; reloaded in place 2026-03-27 |
| **Supabase UUID** | e2dbc4e0-2a95-4061-bf7b-584cce85af64 |
| **KSA Links** | 3 deterministic links; 7 derived concept links |
| **Lines** | assembled guide (630 lines of authored prose including 10 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 10 (IMG pass complete): sf-ppe-shock-vs-arc-flash-framework; sf-ppe-category-transition-chart; sf-ppe-rubber-glove-class-and-derating; sf-ppe-prejob-readiness-board; sf-ppe-meter-selection-decision-path; sf-ppe-project-equipment-loadout; sf-ppe-common-failures-panel; sf-ppe-expired-glove-stop-scenario; sf-ppe-project-loadout-gap-scenario; sf-ppe-field-check-reminders |
| **v2.3 Sections** | All 8 sections assembled; 10 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | 7 extractions (primary + secondary): EXT-NFPA-003 (1,648L), EXT-NFPA-014 (342L), EXT-NFPA-015 (431L), EXT-NFPA-018 (347L), EXT-NETA-HANDBOOK-II-SAF1 (793L), EXT-NETA-HANDBOOK-II-AF (766L), EXT-ETT-025 (283L). Reference sheets: L4-RS-safety-nfpa70e, L4-RS-codes-standards |
| **Key content** | Shock-boundary and arc-flash PPE framework; PPE categories and minimum arc ratings; glove classes, intervals, and protectors; crew-level PPE inspection/storage discipline; project equipment planning for hot sticks, meters, insulated tools, barriers, and backup gear |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-B-ACTIVATION.md` |
| **Notes** | Third bounded Safety L4 packet to receive a staging packet (Sub-Guide B of 6). Scope remains limited to SF-006 through SF-008 and preserves the distinction between PPE/safety-equipment management versus incident-energy interpretation and the later codes-and-standards capstone packet. Bounded authoring, assembly, publication-safe citation review, and IMG pass were completed on 2026-03-25, producing a reader-facing assembled guide with 10 compliant `sf-ppe-` placeholders and no remaining VERIFY flags. Direct generic-loader closeout completed the same day with UUID `e2dbc4e0-2a95-4061-bf7b-584cce85af64`, 3 deterministic KSA links, and 7 derived concept links. Config and scaffold were created manually because the current build scripts are still CT-domain-specific. |

---

### Guide #35 -- Safety L4 Sub-Guide D: Voltage Detection & Temporary Protective Grounding

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-voltage-detection-tpg/SG-SF-VOLTAGE-DETECTION-TPG.md` |
| **content_id** | SG-SF-VOLTAGE-DETECTION-TPG |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-012, KSA-IV-SF-013 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED 2026-03-25 via generic guide loader |
| **Supabase UUID** | 96493323-9a91-4164-9988-46965c588505 |
| **KSA Links** | 2 deterministic links; 4 derived concept links |
| **Lines** | assembled guide (589 lines of authored prose including 10 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 10 (IMG pass complete): sf-vdtpg-voltage-detector-selection-map; sf-vdtpg-live-dead-live-sequence; sf-vdtpg-induced-vs-source-voltage-logic; sf-vdtpg-ground-set-selection-check; sf-vdtpg-grounding-sequence-overview; sf-vdtpg-worker-protection-grounding-boundary; sf-vdtpg-common-failure-patterns; sf-vdtpg-meter-not-rated-stop-scenario; sf-vdtpg-wrong-stab-grounding-scenario; sf-vdtpg-field-discipline-reminders |
| **v2.3 Sections** | All 8 sections assembled; 10 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | 6 extractions (primary + secondary): EXT-NFPA-003 (1,648L), EXT-NETA-HANDBOOK-II-SAF1 (793L), EXT-NETA-HANDBOOK-II-AF (766L), EXT-ETT-025 (283L), EXT-IEEE-252 (grounding-industrial safety), EXT-NETA-ECS-2024 (temporary grounding application/removal surfaces). Reference sheets: L4-RS-safety-nfpa70e, L4-RS-codes-standards |
| **Key content** | Instrument selection and live-dead-live discipline; contact vs noncontact limitations; induced-voltage judgment; temporary grounding set selection and rating; hot-stick application/removal; worker-protection grounding boundary versus permanent grounding design |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-D-ACTIVATION.md` |
| **Notes** | Fourth bounded Safety L4 packet to receive a staging packet (Sub-Guide D of 6). Scope remains limited to SF-012 and SF-013 and preserves the explicit boundary against permanent grounding design content already covered elsewhere. Bounded authoring, assembly, publication-safe citation review, and IMG pass were completed on 2026-03-25, producing a reader-facing assembled guide with 10 compliant `sf-vdtpg-` placeholders and no remaining VERIFY flags. Direct generic-loader closeout completed the same day with UUID `96493323-9a91-4164-9988-46965c588505`, 2 deterministic KSA links, and 4 derived concept links; a later-approved in-place reload on 2026-03-27 refreshed the live row so it now matches the current staged v2.4 guide body exactly. Config and scaffold were created manually because the current build scripts are still CT-domain-specific. |

---

### Guide #36 -- Safety L4 Sub-Guide C: Confined Space Supervision

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-confined-space-supervision/SG-SF-CONFINED-SPACE-SUPERVISION.md` |
| **content_id** | SG-SF-CONFINED-SPACE-SUPERVISION |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-009, KSA-IV-SF-010, KSA-IV-SF-011 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED 2026-03-25 via generic guide loader |
| **Supabase UUID** | 689a0a8e-91a8-4a88-a3cd-f7d4d61002fb |
| **KSA Links** | 3 deterministic links; 6 derived concept links |
| **Lines** | assembled guide (568 lines of authored prose including 10 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 10 (IMG pass complete): sf-cs-confined-space-hazard-map; sf-cs-hazard-recognition-decision-path; sf-cs-role-boundary-triangle; sf-cs-rescue-readiness-check; sf-cs-osha-to-field-plan-bridge; sf-cs-scope-change-stop-rule; sf-cs-common-supervision-failures; sf-cs-scope-change-scenario; sf-cs-rescue-plan-gap-scenario; sf-cs-field-discipline-reminders |
| **v2.3 Sections** | All 8 sections assembled; 10 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | 2 extractions (primary + secondary): EXT-NETA-HANDBOOK-II-SAF2 (925L), EXT-ETT-025 (283L). Reference sheets: L4-RS-safety-nfpa70e, L4-RS-codes-standards |
| **Key content** | Confined-space hazard recognition; oxygen-deficiency / enrichment thresholds; entrant, attendant, and supervisor roles; permit-required entry discipline; rescue-planning and scope-change supervision in electrical-testing contexts |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-C-ACTIVATION.md` |
| **Notes** | Fifth bounded Safety L4 packet to receive a staging packet (Sub-Guide C of 6). Scope remains limited to SF-009 through SF-011. The activation-time source sufficiency recheck remained moderate but adequate and did not justify new extraction work. Bounded authoring, assembly, publication-safe citation review, and IMG pass were completed on 2026-03-25, producing a reader-facing assembled guide with 10 compliant `sf-cs-` placeholders and no remaining VERIFY flags. Direct generic-loader closeout completed the same day with UUID `689a0a8e-91a8-4a88-a3cd-f7d4d61002fb`, 3 deterministic KSA links, and 6 derived concept links. Config and scaffold were created manually because the current build scripts are still CT-domain-specific. |

---

### Guide #37 -- Safety L4 Sub-Guide F: Codes, Standards & Manufacturer Requirements

| Field | Value |
|-------|-------|
| **File** | `Development/staging/safety-codes-standards-manufacturer-requirements/SG-SF-CODES-STANDARDS-MFR-REQ.md` |
| **content_id** | SG-SF-CODES-STANDARDS-MFR-REQ |
| **Domain** | Safety (Level IV only) |
| **KSA Coverage** | KSA-IV-SF-020, KSA-IV-SF-021, KSA-IV-SF-022, KSA-IV-SF-023 |
| **Pipeline** | Manual config + scaffold + assembled guide (domain guide -- not equipment-section-driven; generate_topic_config.py is CT-specific) |
| **Status** | LOADED 2026-03-25 via generic guide loader |
| **Supabase UUID** | 5b4a32a0-72ec-4420-84e8-2b9805b4f79d |
| **KSA Links** | 4 deterministic links; 4 derived concept links |
| **Lines** | assembled guide (819 lines of authored prose including 10 IMG tags) |
| **VERIFY flags** | 0 |
| **Image placeholders** | 10 (IMG pass complete): sf-codes-governing-authority-stack; sf-codes-task-to-authority-matrix; sf-codes-nec-vs-70e-boundary-map; sf-codes-normal-operation-screen; sf-codes-ats-vs-mts-decision-rule; sf-codes-neta-method-application-loop; sf-codes-listing-labeling-instructions-bridge; sf-codes-common-authority-failures; sf-codes-stop-and-reconcile-scenario; sf-codes-field-discipline-reminders |
| **v2.3 Sections** | All 8 sections assembled; 10 IMG tags inserted only in allowed sections (KSA Coverage, Common Mistakes, Field Scenarios, Field Tips) |
| **Sources identified** | NFPA 70E comprehensive extraction, OSHA 1910.331-335 summary extraction, NETA Handbook Series II -- Safety, Vol. 2, ANSI/NETA ATS-2025 extraction, ATS-vs-MTS comparison, NETA MTS-2023 Appendix B/C extraction, NFPA 70 selective NEC extraction, and packet reference-sheet surfaces |
| **Key content** | Standards hierarchy and authority boundaries; NEC vs NFPA 70E role clarity; ANSI/NETA task application; listing/labeling and manufacturer-instruction impacts on testing and maintenance decisions |
| **Scoping basis** | `Development/SAFETY-L4-SCOPE-DECOMPOSITION.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SAFETY-L4-SUBGUIDE-F-ACTIVATION.md` |
| **Notes** | Sixth bounded Safety L4 packet to receive a staging packet (Sub-Guide F of 6). Scope is limited to SF-020 through SF-023 and uses the already-settled 2022 Level IV authority basis from the phase-0 surfaces without reopening that question. This activation recorded the explicit lane decision to advance the final reviewed Safety L4 packet while Guides #32 through #36 remained open. Bounded authoring, assembly, publication-safe citation review, and IMG pass were completed on 2026-03-25, producing a reader-facing assembled guide with 10 compliant `sf-codes-` placeholders and no remaining VERIFY flags. Direct generic-loader closeout completed the same day with UUID `5b4a32a0-72ec-4420-84e8-2b9805b4f79d`, 4 deterministic KSA links, and 4 derived concept links. Config and scaffold were created manually because the current build scripts are still CT-domain-specific. |

---

### Guide #38 -- Capacitors / Reactors

| Field | Value |
|-------|-------|
| **File** | `Development/staging/capacitors-reactors/` |
| **content_id** | SG-CT-CAPACITORS-REACTORS |
| **NETA Section** | 7.20.1, 7.20.3.1, 7.20.3.2; capacitor control devices remain supporting context, resistors 7.20.4 remain context-only |
| **KSA Coverage** | CT-072 through CT-075 (L2/L3/L4 backbone; activation authority is the Level III `KSA-III-CT-079` through `KSA-III-CT-082` packet boundary) |
| **Pipeline** | v2 (hand-built multi-section config + scaffold packet + governed direct assembly closeout) |
| **Status** | LOADED -- merged guide preserved as carryforward source only; all three split branches loaded separately |
| **Supabase UUID** | `SG-CT-CAPACITORS` ? `9c583891-8485-4fdf-b3a8-6c1ace44e147`; `SG-CT-REACTORS-DRY-TYPE` ? `c2b8409a-ec33-4487-ba5c-6a4b294d0c5f`; `SG-CT-REACTORS-LIQUID-FILLED` ? `a844608d-dbc0-4a00-8e1e-6bed30eacec4`; merged `SG-CT-CAPACITORS-REACTORS` intentionally not loaded |
| **KSA Links** | 12 per loaded split branch (36 total) |
| **Lines** | merged guide preserved at packet root with 12 `caprx-` IMG tags; capacitors split guide loaded as `SG-CT-CAPACITORS.md` with 604 lines, 4,438 words, and 12 `cap-` IMG tags; dry-type split guide loaded as `SG-CT-REACTORS-DRY-TYPE.md` with 637 lines, 4,731 words, and 10 `rxd-` IMG tags; liquid-filled split guide loaded as `SG-CT-REACTORS-LIQUID-FILLED.md` with 593 lines, 4,086 words, and 12 `rxl-` IMG tags |
| **VERIFY flags** | 0 |
| **Image placeholders** | merged guide: 12 `caprx-`; capacitors branch: 12 `cap-`; dry-type branch: 10 `rxd-`; liquid-filled branch: 12 `rxl-` |
| **v2.3 Sections** | all 8 sections present in the preserved merged guide and in the assembled capacitors, dry-type, and liquid-filled split guides; packet-local scaffold and split staging docs remain preserved |
| **Sources identified** | Core extracted base: `EXT-IEEE-304` (IEEE 18-2012), `EXT-IEEE-305` (IEEE C57.21-2021), `EXT-IEEE-306` (IEEE 1303-2011), `EXT-FLD-004` (GE Field Test on Capacitors), `EXT-MFR-155` through `EXT-MFR-159` (capacitor-bank manufacturer stack), `EXT-MFR-030` (Trench dry-type shunt reactor datasheet), `EXT-MFR-153` and `EXT-MFR-160` (liquid-filled reactor manufacturer/spec support), `EXT-ETT-012` (Capacitor/Reactor fact sheet), plus ATS/MTS ?7.20 surfaces |
| **Key content** | Shunt power capacitor properties, discharge discipline, inspection/testing/evaluation logic, and capacitor-bank application depth; dry-type reactor inspection/testing backbone; liquid-filled reactor recognition, preservation-system inspection, dielectric/liquid testing, and readiness evaluation; resistor treatment held to context-only in the first packet |
| **Scoping basis** | `Development/TASK-ETT-HANDOFF-CAPACITORS-REACTORS.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-CAPACITORS-REACTORS-GUIDE-ACTIVATION.md` |
| **Notes** | First normal-guide activation after the Capacitors / Reactors gate rerun closed `GO`. The packet remains intentionally narrower than a full all-in `7.20` guide, but post-assembly review found that the initial single assembled guide over-merged the capacitor and reactor backbone sections at `Development/staging/capacitors-reactors/`. On 2026-03-25 the packet moved from scaffolded to assembled plus pre-load-review / IMG-pass complete through a bounded direct assembly pass using the approved extracted standards stack, after which the merged guide was preserved as carryforward source only and split staging was seeded for capacitors, dry-type reactors, and liquid-filled reactors. On 2026-03-26 governed branch-load resolution approved and loaded the capacitors branch as `SG-CT-CAPACITORS`, the dry-type reactor branch as `SG-CT-REACTORS-DRY-TYPE`, and the liquid-filled reactor branch as `SG-CT-REACTORS-LIQUID-FILLED`, each with 12 deterministic KSA links and 12 derived concept links. Capacitor control devices remain supporting context only, resistors remain context-only, the merged guide remains parked as carryforward source only, and Guide #39 later advanced through direct load closeout as the next follow-on packet. |

---

### Guide #39 -- Motor Control Centers, Low-Voltage (MCC-Centered)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/motor-control-centers-low-voltage/` |
| **content_id** | SG-CT-MOTOR-CONTROL-CENTERS |
| **NETA Section** | 7.16.2.1, with 7.16.1.1 starter procedures retained only as supporting references where the MCC section delegates outward |
| **KSA Coverage** | CT-063 through CT-066 (Level III first packet only) |
| **Pipeline** | v2 (manual config + scaffold packet + CC task handoff) |
| **Status** | LOADED -- packet complete; pre-load review and IMG pass complete; Supabase loaded 2026-03-26 |
| **Supabase UUID** | 45a8fff9-7706-4a6d-864e-a45514ddc67a |
| **KSA Links** | 4 deterministic links; 6 derived concept links |
| **Lines** | packet-local staging now includes completed KSA/shared files, `README.md`, assembled guide `SG-CT-MOTOR-CONTROL-CENTERS.md`, and the original CC task doc |
| **VERIFY flags** | 0 |
| **Image placeholders** | 6 in assembled guide; IMG pass complete |
| **v2.4 Sections** | assembled guide now exists and includes Scope Note, Learning Objectives, KSA Coverage, Safety Considerations, Common Mistakes, Quick Reference, Field Scenarios, Field Tips, Standards Reference, and Further Study |
| **Sources identified** | MCC audit-approved source stack: `EXT-IEEE-1683`, `EXT-MFR-003`, `EXT-NEMA-009`, `EXT-NEMA-010`, and `EXT-NEMA-005` |
| **Scoping basis** | `Development/TASK-ETT-HANDOFF-MOTOR-CONTROL-MCCS.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-MOTOR-CONTROL-MCCS-GUIDE-ACTIVATION.md` |
| **Notes** | Guide #39 activation executed on 2026-03-26 after the MCC pre-activation audit closed `GO`. The generic topic-config generator was intentionally bypassed because prefix fallback from `7.16.2.1` to `7.16` produced the wrong KSA cluster, zero matched extractions, and an unsafe staging slug. The live packet therefore uses a governed manual config preserving the low-voltage MCC-centered first-packet boundary at `7.16.2.1` with VFDs still parked. On 2026-03-26 the bounded authoring / pre-load pass completed packet-local fill, assembled guide creation, publication-safe citation review, and IMG pass. Later the same day the packet was loaded to Supabase via `Development/Scripts/Load/Guides/load_guide_generic.py` as UUID `45a8fff9-7706-4a6d-864e-a45514ddc67a`, producing 4 deterministic KSA links and 6 derived concept links; the follow-on `discover_ksa_links.py --apply` pass preserved 100% domain coverage. |

---

### Guide #40 -- Switches (Level III, Standards-Led First Packet)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/switches/SG-CT-SWITCHES.md` |
| **content_id** | SG-CT-SWITCHES |
| **NETA Section** | 7.5.1.1, 7.5.1.2, 7.5.1.3, 7.5.2, 7.5.3, bounded as one Level III first packet under the 7.5 switches family |
| **KSA Coverage** | CT-018 through CT-021 (Level III first packet only) |
| **Pipeline** | v2 (governed manual multi-section config + scaffold packet + CC task handoff) |
| **Status** | LOADED -- assembled, pre-load review complete, IMG pass complete, Supabase load complete |
| **Supabase UUID** | 3be48f39-56bb-4a4a-a6a6-1fffb88d877d (new) |
| **KSA Links** | 4 deterministic links (CT-018?021 x L3) |
| **Lines** | assembled guide created with retained packet-local staging files, shared utilities, `README.md`, `STATUS.md`, config, and the CC task doc |
| **VERIFY flags** | 0 |
| **Image placeholders** | 6 (`sw-` IMG pass complete) |
| **v2.4 Sections** | assembled guide present; all core v2.4 sections completed for the pre-load handoff |
| **Sources identified** | Primary startup stack: IEEE C37.20.4-2013, IEEE C37.30.1-2011, and ANSI C37.32-2002; chosen manufacturer support source: Series 95 Switches Product Catalog; reserve source and RL27 remain deferred |
| **Scoping basis** | `Development/TASK-ETT-HANDOFF-SWITCHES-L4.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SWITCHES-GUIDE-ACTIVATION.md` |
| **Notes** | Guide #40 activation executed on 2026-03-26 after the switches pre-activation audit closed `GO` and retired the stale `Switches L4` shorthand. The packet intentionally stays Level III and standards-led under the 7.5 switches family without widening into circuit switchers, reclosers, or broad pad-mounted switchgear. A governed manual config was used so the first packet could preserve the approved multi-section boundary and Level III-only KSA span before the canonical scaffold and CC-task generators were run. Later the same day the bounded authoring / pre-load pass completed assembled guide creation, publication-safe citation cleanup, and a 6-tag `sw-` IMG pass. The separate load closeout then completed via `Development/Scripts/Load/Guides/load_guide_generic.py`, creating UUID `3be48f39-56bb-4a4a-a6a6-1fffb88d877d`, 4 deterministic KSA links, and 6 derived concept links; the follow-on discovery pass inserted 0 additional links and preserved 100% domain coverage. |

---

### Guide #41 -- Variable Frequency Drives / Adjustable Speed Drives (Standards-Led First Packet)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/variable-frequency-drives/SG-CT-VFDS.md` |
| **content_id** | SG-CT-VFDS |
| **NETA Section** | 7.17 |
| **KSA Coverage** | CT-069 through CT-072 (Level III first packet only) |
| **Pipeline** | v2 (governed manual config + scaffold packet + CC task handoff) |
| **Status** | LOADED -- assembled, pre-load review complete, IMG pass complete, Supabase load complete |
| **Supabase UUID** | 4f2d5e19-1050-4240-a70b-56da76a6343b (new) |
| **KSA Links** | 4 deterministic links (CT-069-072 x L3) |
| **Lines** | assembled guide created with retained packet-local staging files, shared utilities, `README.md`, `STATUS.md`, config, and the CC task doc |
| **VERIFY flags** | 0 |
| **Image placeholders** | 8 (`vfd-` IMG pass complete) |
| **v2.4 Sections** | assembled guide present; all core v2.4 sections completed for the pre-load handoff |
| **Sources identified** | Primary startup stack: IEEE Std 1566-2015, Carrier VFD-09SI, and Honeywell 63-7062; supporting sources: ABB ACS880 quick-start guidance, IEEE 519, and the VFD support references already approved in the activation packet |
| **Scoping basis** | `Development/TASK-ETT-HANDOFF-VFDS.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-VFDS-GUIDE-ACTIVATION.md` |
| **Notes** | Guide #41 activation executed on 2026-03-26 after the VFD pre-activation audit rerun closed `GO`. The packet intentionally stays Level III and standards-led under NETA `7.17` without widening back into MCCs, starters, or a broader motor-control family guide. A governed manual config was used because the stock topic-config generator fell back to `CT-063` and mixed levels. On 2026-03-27 the bounded authoring / pre-load pass completed packet-local review, publication-safe citation cleanup, and an 8-tag `vfd-` IMG pass. The separate load closeout then completed via `Development/Scripts/Load/Guides/load_guide_generic.py`, creating UUID `4f2d5e19-1050-4240-a70b-56da76a6343b`, 4 deterministic KSA links, and 6 derived concept links; the follow-on `discover_ksa_links.py --apply` pass inserted 53 additional body-discovery links from the current orphaned-content set and preserved 100% domain coverage. |

---

### Guide #42 -- Electric Vehicle Charging Systems (Level II-Led Standards-First Packet)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/ev-charging-systems/SG-EVCS-EV-CHARGING-SYSTEMS.md` |
| **content_id** | SG-EVCS-EV-CHARGING-SYSTEMS |
| **NETA Section** | N/A -- governed domain guide |
| **KSA Coverage** | Domain-specific first-packet span: `EVCS-01` through `EVCS-04` (Level II-led with Level III supporting context) |
| **Pipeline** | v2 (governed manual config + scaffold packet + CC task handoff) |
| **Status** | LOADED -- assembled, pre-load review complete, IMG pass complete, Supabase load complete |
| **Supabase UUID** | b72f8c60-7222-4fa6-919a-71c25c05580f (new) |
| **KSA Links** | 26 body-content-discovery links; 8 deterministic links via canonical 2026 CT EV charging KSAs; 4 derived EVCS concept links |
| **Lines** | assembled guide created with retained packet-local staging files, shared utilities, `README.md`, `STATUS.md`, config, and the CC task doc |
| **VERIFY flags** | 0 |
| **Image placeholders** | 8 (`evcs-` IMG pass complete) |
| **v2.4 Sections** | assembled guide present; all core v2.4 sections completed for the pre-load handoff |
| **Sources identified** | 20-source primary stack: NEC Article 625 (EXT-NFPA-022), UL 2202 (EXT-UL-002), SAE J1772/J3068 (EXT-SAE-001/002/003), IEC 61851-23/24 (EXT-IEC-011/013), IEC 62196 Parts 1-3 (EXT-IEC-014/015/016), IEEE 2030.1.1 (EXT-IEEE-304), ISO 15118-1 (EXT-ISO-001), IEC 62752 (EXT-IEC-012), CharIN (EXT-IND-021), Tesla NACS (EXT-IND-022), manufacturer stack (EXT-MFR-164/165/166/168), textbook (EXT-TXT-044). **Source-limit rule:** exact UL 2594 and UL 2251 text was not obtained; see packet README. |
| **Scoping basis** | `Development/Control-Plane/ETT-EV-CHARGING-DOMAIN-PRE-ACTIVATION-AUDIT-2026-03-27.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-EV-CHARGING-DOMAIN-ACTIVATION-2026-03-27.md` |
| **Notes** | First governed domain guide in the ETT pipeline. Domain admission cleared through `Development/Control-Plane/ETT-DOMAIN-INTAKE-EV-CHARGING-2026-03-27.md`. Pre-activation audit closed `GO` on 2026-03-27 under an explicit source-limit rule: exact UL 2594 and UL 2251 text was not obtained despite substantial sourcing effort across four PDF triage batches, but the current standards-family stack (NEC, SAE, IEC, IEEE, ISO, NACS, manufacturer) is strong enough for an educational standards-first packet. The packet boundary remains Level II-led; Level III material is supporting context only. The guide does not widen into V2G, microgrid, or utility-interconnection domain territory. A governed manual config was used because the stock `generate_topic_config.py` requires a NETA section number and this is a cross-standards domain guide. On 2026-03-27 the separate downstream authoring / pre-load pass completed direct-from-scaffold assembly, publication-safe citation cleanup, and an 8-tag `evcs-` IMG pass while preserving the source-limit rule. The separate load handoff then completed as a new Supabase row with UUID `b72f8c60-7222-4fa6-919a-71c25c05580f`, and post-load discovery inserted 26 body-content-discovery links. On 2026-03-28 the governed manual config and generic loader were updated so the authored packet-local IDs `EVCS-01` through `EVCS-04` now map through the canonical 2026 EV charging KSA set `KSA-II-CT-086` through `KSA-II-CT-089` and `KSA-III-CT-099` through `KSA-III-CT-102`, producing 8 deterministic KSA links and 4 derived EVCS concept links without forcing a fake body-level CT remap. |

---

### Guide #43 -- SCADA / IEC 61850 Automation (Level IV-Led Domain Packet)

| Field | Value |
|-------|-------|
| **File** | `Development/staging/scada-iec61850-automation/SG-SCADA-IEC61850-AUTOMATION.md` |
| **content_id** | SG-SCADA-IEC61850-AUTOMATION |
| **NETA Section** | N/A -- governed domain guide |
| **KSA Coverage** | Domain-specific first-packet span: `SCADA-01` through `SCADA-04` (Level IV-led with lower-level SCADA surfaces held as carryforward context only) |
| **Pipeline** | v2 (governed manual config + scaffold packet + CC task handoff) |
| **Status** | LOADED -- assembled, pre-load review complete, IMG pass complete, Supabase load complete |
| **Supabase UUID** | ff5c55c9-575f-4191-8de4-cb6bcf0aefbc (new) |
| **KSA Links** | 17 body-content-discovery links; 0 deterministic links; 0 derived concept links |
| **Lines** | assembled guide present with retained packet-local staging files, `STATUS.md`, `README.md`, config, scaffold, and CC task doc |
| **VERIFY flags** | 0 |
| **Image placeholders** | 9 (`scada-` IMG pass complete) |
| **v2.4 Sections** | assembled guide present; all core v2.4 sections completed for the pre-load handoff |
| **Sources identified** | Standards-first lead stack: `EXT-IEEE-242`, `EXT-IEEE-042`, `EXT-CIGRE-002`, `EXT-CIGRE-002-SUPP`, `EXT-IEEE-309`, `EXT-MFR-169`, `EXT-CIGRE-003`; bounded support depth: `EXT-IEC-006`, `EXT-IEC-007`, `EXT-TXT-045`, `EXT-CIGRE-004`; carryforward inputs: legacy L4 SCADA guide plus archived L4 staging markdown |
| **Scoping basis** | `Development/Control-Plane/ETT-SCADA-IEC61850-DOMAIN-PRE-ACTIVATION-AUDIT-2026-03-29.md` |
| **Activation authority** | `Development/Control-Plane/AI-INSTANCE-TASK-PROMPT-ETT-SCADA-IEC61850-DOMAIN-ACTIVATION-2026-03-29.md` |
| **Notes** | First SCADA / IEC 61850 governed domain packet in the ETT pipeline. Domain admission cleared through `Development/Control-Plane/ETT-DOMAIN-INTAKE-SCADA-IEC61850-2026-03-28.md`, and the pre-activation audit closed `GO` on 2026-03-29 for one bounded Level IV-led packet centered on IEC 61850 workflow, deterministic messaging, time synchronization, cyber-hygiene / hardening, and commissioning / acceptance decision gates. Activation executed on 2026-03-29, and the bounded downstream authoring / pre-load pass also executed the same day, producing the assembled guide, publication-safe citation cleanup, and a 9-tag `scada-` IMG pass without widening the packet. The separate load handoff then completed on 2026-03-29 as new Supabase row `ff5c55c9-575f-4191-8de4-cb6bcf0aefbc`, and the normal post-load discovery pass inserted 17 body-content-discovery links for this guide. Deterministic SCADA links resolved `0/8` and derived concept links resolved `0` because packet-local governed-domain IDs `SCADA-01` through `SCADA-04` do not yet have a bounded canonical live mapping; that is a separate governed follow-on rather than a failed load. A governed manual config was used because the stock `generate_topic_config.py` is section-driven and does not cleanly represent this cross-standards domain packet. Preserve the audit nuance that the core CIGRE Green Book extract used for authoring is available in the governed local source base while live content-store cleanup for that core extract is still pending; that remains a non-blocking governance cleanup item. Lower-level SCADA reference sheets and practice tests remain companion context only, and the legacy L4 guide plus archived staging markdown remain carryforward inputs rather than the final body. |

---

## STATUS KEY

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete — all sections, Supabase loaded |
| ⚠️ LOADED | Guide file exists, not yet loaded to Supabase |
| 🔄 DRAFT | File exists, incomplete or not yet reviewed |
| ⬜ QUEUED | Task doc written, authoring not started |
| 📋 PLANNED | Topic selected + architecture decided, no staging yet |
| ❌ BLOCKED | Cannot proceed until dependency resolved |

---

## ACTIVE PIPELINE STATE

The active ETT guide pipeline now has no blocked normal guide topic. The
reviewed follow-on packets were activated under explicit lane decisions before
prose authoring began. Guide #38's merged guide is preserved as carryforward
source, its three split branches are now separately loaded, Guide #39 has
completed load closeout and is parked, Guide #40 has now completed its
separate load closeout and is parked, Guide #41 has now completed its
separate VFD load closeout and is parked, Guide #42 has now completed
authoring, pre-load review, IMG pass, and separate load closeout and is now
parked as loaded with an explicit EV-domain KSA-modeling caveat, and Guide #43
has now also completed its separate domain-guide load closeout and is parked
as loaded with an explicit SCADA domain-linking caveat.

| Metric | Count |
|--------|-------|
| Active assembled guides | 0 |
| Active scaffolded guides | 0 |
| Active staged guides | 0 |
| Active blocked guides | 0 |
| Active planned guides | 0 |

The guide pipeline was explicitly reopened on 2026-03-24 based on the decision-grade scoping report `Development/ETT-NEXT-GUIDE-TOPIC-SCOPING-REPORT-2026-03-24.md`.

Guide #30 is fully assembled, IMG-tagged, loaded, and parked. Guide #31 (DC Systems) has now completed CC fill, Desktop authoring, assembly, IMG pass, and Supabase load and should be treated as parked unless a follow-up correction pass is explicitly opened. Guide #38 (Capacitors / Reactors) is now a resolved split packet: the merged guide remains carryforward-only, and the capacitors, dry-type, and liquid-filled split branches are loaded separately. Guide #39 (Motor Control Centers, Low-Voltage) has now completed authoring, assembly, IMG pass, Supabase load, and KSA discovery closeout and should be treated as parked unless a follow-up correction pass is explicitly opened. Guide #40 (Switches) has now completed authoring, assembly, IMG pass, Supabase load, and post-load discovery closeout and should be treated as parked unless a follow-up correction pass is explicitly opened. Guide #41 (Variable Frequency Drives / Adjustable Speed Drives) has now completed authoring, assembly, IMG pass, Supabase load, and post-load discovery closeout and should also be treated as parked unless a follow-up correction pass is explicitly opened. Guide #42 (Electric Vehicle Charging Systems) has now completed authoring, publication-safe citation review, IMG pass, separate Supabase load, and post-load discovery closeout under the EV source-limit rule and should be treated as parked unless a distinct EV domain-modeling follow-up is later approved. Guide #43 (SCADA / IEC 61850 Automation) has now completed authoring, publication-safe citation review, IMG pass, separate Supabase load, and post-load discovery closeout under an explicit SCADA domain-linking caveat and should be treated as parked unless a distinct SCADA domain-mapping follow-up is later approved.

Most recent newly loaded topics:

- Guide #43 -- SCADA / IEC 61850 Automation (Level IV-Led Domain Packet) (`SG-SCADA-IEC61850-AUTOMATION`) -- LOADED 2026-03-29 via `load_guide_generic.py`; 9 compliant `scada-` IMG tags; UUID `ff5c55c9-575f-4191-8de4-cb6bcf0aefbc` (new); follow-on `discover_ksa_links.py --apply` inserted 17 body-content-discovery links for this guide, while deterministic SCADA links resolved `0/8` and derived concept links resolved `0` because packet-local `SCADA-01` through `SCADA-04` mapping is not yet canonically defined.

- Guide #42 -- Electric Vehicle Charging Systems (Level II-Led Standards-First Packet) (`SG-EVCS-EV-CHARGING-SYSTEMS`) -- LOADED 2026-03-27 via `load_guide_generic.py`; 8 compliant `evcs-` IMG tags; UUID `b72f8c60-7222-4fa6-919a-71c25c05580f` (new); follow-on `discover_ksa_links.py --apply` inserted 26 body-content-discovery links, and a 2026-03-28 domain-model repair then mapped packet-local `EVCS-01` through `EVCS-04` to canonical 2026 EV charging KSAs, producing 8 deterministic KSA links and 4 derived EVCS concept links.

- Guide #41 -- Variable Frequency Drives / Adjustable Speed Drives (Standards-Led First Packet) (`SG-CT-VFDS`) -- LOADED 2026-03-27 via `load_guide_generic.py`; 8 compliant `vfd-` IMG tags; UUID `4f2d5e19-1050-4240-a70b-56da76a6343b`; 4 deterministic KSA links and 6 derived concept links; discovery pass inserted 53 additional body-discovery links from the current orphaned-content set.

- Guide #40 -- Switches (Level III, Standards-Led First Packet) (`SG-CT-SWITCHES`) -- LOADED 2026-03-26 via `load_guide_generic.py`; 6 compliant `sw-` IMG tags; UUID `3be48f39-56bb-4a4a-a6a6-1fffb88d877d`; 4 deterministic KSA links and 6 derived concept links; discovery pass inserted 0 additional links.

- Guide #39 -- Motor Control Centers, Low-Voltage (MCC-Centered) (`SG-CT-MOTOR-CONTROL-CENTERS`) -- LOADED 2026-03-26 via `load_guide_generic.py`; 6 compliant `mcc-` IMG tags; UUID `45a8fff9-7706-4a6d-864e-a45514ddc67a`; 4 deterministic KSA links and 6 derived concept links.

- Guide #38 split branch -- Capacitors (`SG-CT-CAPACITORS`) -- LOADED 2026-03-26 via `load_guide_generic.py`; 12 compliant `cap-` IMG tags; UUID `9c583891-8485-4fdf-b3a8-6c1ace44e147`.
- Guide #38 split branch -- Reactors, Dry-Type (`SG-CT-REACTORS-DRY-TYPE`) -- LOADED 2026-03-26 via `load_guide_generic.py`; 10 compliant `rxd-` IMG tags; UUID `c2b8409a-ec33-4487-ba5c-6a4b294d0c5f`.
- Guide #38 split branch -- Reactors, Liquid-Filled (`SG-CT-REACTORS-LIQUID-FILLED`) -- LOADED 2026-03-26 via `load_guide_generic.py`; 12 compliant `rxl-` IMG tags; UUID `a844608d-dbc0-4a00-8e1e-6bed30eacec4`.

- Guide #32 -- Safety L4 Sub-Guide A: Risk Assessment & Electrically Safe Work Condition (SF-001 through SF-004) -- LOADED 2026-03-25 via `load_guide_generic.py`; 9 compliant `sf-risk-` IMG tags; UUID `dfbe1b8a-ec7e-4553-b18d-7f0fc892a559`.
- Guide #33 -- Safety L4 Sub-Guide E: Incident Energy Analysis & Field Labeling (SF-015 through SF-018) -- LOADED 2026-03-25 via `load_guide_generic.py`; 9 compliant `sf-ie-` IMG tags; UUID `3b4422a4-bc87-4641-95c2-8e844c0a4505`.
- Guide #34 -- Safety L4 Sub-Guide B: PPE & Safety Equipment Management (SF-006 through SF-008) -- LOADED 2026-03-25 via `load_guide_generic.py`; 10 compliant `sf-ppe-` IMG tags; UUID `e2dbc4e0-2a95-4061-bf7b-584cce85af64`.
- Guide #35 -- Safety L4 Sub-Guide D: Voltage Detection & Temporary Protective Grounding (SF-012 through SF-013) -- LOADED 2026-03-25 via `load_guide_generic.py`; 10 compliant `sf-vdtpg-` IMG tags; UUID `96493323-9a91-4164-9988-46965c588505`.
- Guide #36 -- Safety L4 Sub-Guide C: Confined Space Supervision (SF-009 through SF-011) -- LOADED 2026-03-25 via `load_guide_generic.py`; 10 compliant `sf-cs-` IMG tags; UUID `689a0a8e-91a8-4a88-a3cd-f7d4d61002fb`.
- Guide #37 -- Safety L4 Sub-Guide F: Codes, Standards & Manufacturer Requirements (SF-020 through SF-023) -- LOADED 2026-03-25 via `load_guide_generic.py`; 10 compliant `sf-codes-` IMG tags; UUID `5b4a32a0-72ec-4420-84e8-2b9805b4f79d`.

Current active scaffolded topic:

- none; Guide #43 completed the full bounded packet cycle through separate load closeout on 2026-03-29

Current active assembled / pre-load-complete topic:

- none; no guide is currently parked between authoring closeout and separate load handoff

Remaining parked candidates (not yet scoped for activation):

- none; VFDs (?7.17) advanced out of the parked queue on 2026-03-26 and completed the full bounded packet cycle through load closeout on 2026-03-27

---

## PENDING ACTIONS ON EXISTING GUIDES

| Guide | Action | Task Doc | Priority |
|-------|--------|----------|----------|
| #1 Circuit Switchers | ✅ REBUILT — scaffold + 4 fills, SF6 content updated | `TASK-VSCODE-CIRCUIT-SWITCHERS-ASSEMBLE.md` | COMPLETE |
| #2 Grounding Systems | Verify GPR threshold values | — | MEDIUM |
| ✅ CT L3 gaps | Manual patch — KSA-III-CT-028–031 → SG-CT-CIRCUIT-SWITCHERS (CT 100%) | `TASK-VSCODE-CT-L3-GAP-PATCH.md` | COMPLETE |
| ✅ #1–5 | All 5 loaded to Supabase (status: draft) | `TASK-VSCODE-GUIDE-LOAD-ALL-FIVE.md` | COMPLETE |
| ✅ #6 Insulating Fluids | Loaded to Supabase + 31 KSA links (18 discovery + 13 manual_patch) | `_patch_insulating_fluids_ksa.py` | COMPLETE |
| ✅ #7A LV Switchgear | discover_ksa_links.py — 39 links inserted (19 STRONG, 20 MODERATE) | `discover_ksa_links.py --apply` | COMPLETE |
| ✅ #1 + #2 + #3 + #5 | DATA-TABLE marker retrofit (10 markers, commit `45cf894`) | `TASK-VSCODE-DATA-TABLE-MARKER-RETROFIT.md` | COMPLETE |
| ✅ #4 Protective Relays | RTH update pass — Device 21, motor/gen protection, 20,894w | `TASK-VSCODE-GUIDE4-UPDATE-PASS.md` | COMPLETE |
| ✅ #7C MEGIS | REVIEWED — 2 VERIFY closed (consult manufacturer), reloaded to Supabase | `load_guide_7c.py --apply` | COMPLETE |
| ✅ #7D HV GIS | REVIEWED — 0 issues, loaded to Supabase + 37 KSA links discovered | `load_guide_7d.py --apply` | COMPLETE |
| ✅ #1 Circuit Switchers | REBUILT — scaffold + 4 fills assembled, loaded (UPDATE), 787L/10,551w | `load_guide_8.py --apply` | COMPLETE |
| ✅ #9A LV Cable Testing | Loaded NEW — 420L/5,373w, 18 KSA links discovered (1S/17M) | `load_guide_9a.py --apply` | COMPLETE |
| ✅ #10A–D IT Guides | All 4 loaded — 4,542L/67,309w, 137 KSA links (81S/56M), Issue #2 closed | `TASK-VSCODE-LOAD-IT-GUIDES.md` | COMPLETE |
| ✅ #7B MV Switchgear | Loaded to Supabase (UPDATE) + 39 KSA links (29S/10M), v2.3 metadata | `TASK-VSCODE-LOAD-7B.md` | COMPLETE |
| ✅ #20 Busways | Loaded to Supabase — 1,223L/14,344w, 38 KSA links (20S/18M), pipeline v2 demo | `TASK-VSCODE-LOAD-BUSWAYS.md` | COMPLETE |
| ✅ #21 Outdoor Bus | Loaded to Supabase — 940L/12,569w, 35 KSA links (12F/23P), pipeline v2 Wave 1 | CC load | COMPLETE |
| ✅ #22 GFP | Loaded to Supabase — 1,598L/16,840w, 12 KSA links, emergency quartet | `load_guide_22.py` | COMPLETE |
| ✅ #23 ATS | Loaded to Supabase — 1,592L/15,151w, 12 KSA links, emergency quartet | `load_guide_23.py` | COMPLETE |
| ✅ #24 Gen | Loaded to Supabase — 1,373L/12,665w, 12 KSA links, emergency quartet | `load_guide_24.py` | COMPLETE |
| ✅ #25 UPS | Loaded to Supabase — 1,486L/14,224w, 12 KSA links, emergency quartet | `load_guide_25.py` | COMPLETE |
| ✅ #26 LV SPD | Loaded to Supabase — 1,051L/12,789w, 12 KSA links | `load_guide_26.py` | COMPLETE |
| ✅ #27 MV/HV SA | Loaded to Supabase — 1,294L/16,078w, 12 KSA links | `load_guide_27.py` | COMPLETE |
| ? Batch 2 Extractions | 13 PDFs sorted/extracted/loaded ? 9 new Supabase records (EXT-TXT-032?038, EXT-EXAM-003/004), D1/D5 prose-filtered | `TASK-CC-TRIAGE-UNSORTED-BATCH2.md` | COMPLETE |

---

## NOTES

**Current section-order reference:**
Use `Development/CONTENT-FORMAT-SPEC-v2.3.md` as the live guide-authoring standard. Individual registry entries may preserve historical section-version notes from the time a guide was assembled.

**Quality Grade Scale:**
- **A** — All sections complete, authoritative values, field scenarios grounded in data packet, no audit flags
- **A−** — All sections complete, minor pending verification items or one section needing polish
- **B+** — Complete but missing one minor section or has known content gaps
- **B** — Drafted, multiple gaps or awaiting significant addition
- **TBD** — Not yet reviewed

**Related Documents:**
- `Development/MASTER-TOPIC-ACTION-LIST.md` — Full KSA gap analysis (114 gaps mapped)
- `Development/CONTENT-FORMAT-SPEC-v2.3.md` — Authoritative live guide format spec
- `Development/MIGRATION-PLAYBOOK.md` — Consolidation workflow
- `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md` — Active VS Code task queue
- `Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md` — Current ETT content lane resume
- `Development/Audits/AUDIT-ETT-CONTENT-CONTINUITY-RESTORE-2026-03-24.md` — Bounded continuity restore note
- `Development/TASK-CC-TRIAGE-UNSORTED-BATCH2.md` ? Batch 2 unsorted PDF triage (13 PDFs, Groups A/C/D/E, Phase 3a enrichment + prose-fil