# Chip 10 — Capture-Mode Import (instrument file → records datasheet)

> **Status: DESIGN (blueprint, NOT built) — 2026-06-17.** Supersedes the PUNCHLIST "Chip 10 —
> Instrument / format import (DEFERRED)" stub with a scoped design. This is the build-out of **Path 2**
> of the capture-mode contract ratified in STATE §235–§236 (the `instrument_import` half). No code until
> this spec is reviewed + approved. Cite `00-MASTER-INDEX.md`, `01-OFFLINE-SYNC-ARCHITECTURE.md`, the
> `field_schema` contract (`04-LV-CB-DATASHEET-SPEC.md` §2 + the capture-mode block in
> `09-IT-DATASHEET-SPEC.md` §4), and the banked converters (`packages/power-test-converters/`).

---

## 1. Goal & non-goals

**Goal.** A field tech runs a transformer/CT/etc. test on their instrument (OMICRON Testrano, Doble,
OMICRON CT Analyzer, …); the instrument's own export file is **uploaded to the office records surface
and populates the matching datasheet** — no hand-keying, no second disjoint report, one record of truth.

**In scope (this chip).**
- **File import** — DTAX / PTM / CTA / other instrument file → datasheet control values.
- **Office-side (connected) ingest** — runs server-side where the Python converters already live.
- A **mandatory review gate** before anything writes into the record of truth.
- **Provenance + trust stamping** on every imported value.

**Out of scope (designed-for, not built here).**
- **Live test-set connection** (serial/USB/BT/SDK). Designed *for* — it becomes another *source adapter*
  feeding the same reading model + mapping (see §4); not built in this chip.
- **Field-offline import.** Import is a connected office step (operator decision). The field PWA keeps
  capturing *observations* offline; instrument files fold in office-side at upload. (If a future need
  forces offline import, the desktop-companion-tool variant re-opens — recorded, not chosen.)
- **The PTM→DTAX field workaround** (`packages/power-test-converters` write path) stays a separate
  tactical tool; it is NOT part of the platform import.

---

## 2. Decisions (settled)

| # | Decision | Rationale |
|---|---|---|
| D1 | **File-import first**, live-connect later | Reuses the banked parsers; bounded; the mapping core is built source-agnostic so live-connect plugs in without rework |
| D2 | **Office ingest service** (connected, server-side) | The converters are Python; the field app is an offline JS PWA. Server-side reuses the converters as-is, no JS/WASM port, no desktop-tool to distribute |
| D3 | **Source-agnostic reading model is the durable core** | A reading is a reading whether it comes from a file or a live cable; file-parse and live-connect are interchangeable *source adapters* |
| D4 | **Mandatory review-before-commit** | The platform's field-trust law forbids blind-writing instrument data into the record of truth |
| D5 | **First slice = PTM transformer → transformer datasheet** | Only path with **zero parser risk** (`read_ptm` is validated, 5/5 green) and the richest data to exercise the whole pipeline end-to-end |

---

## 3. What is already banked (the de-risking)

`packages/power-test-converters/` — suite **5/5 green** (verified 2026-06-17):

| Format | Direction banked | Reuse for the platform import |
|---|---|---|
| **PTM** (OMICRON) | **validated *reader*** `read_ptm → PtmModel` | **READY** — nameplate + windings + bushings + tap-changer + job/asset identity + all 5 transformer tests (tan-δ PF, turns-ratio, winding-resistance, excitation, demag) + instrument provenance, defensively parsed |
| **DTAX** (Doble) | validated *writer* + exhaustive schema map (~60 `_patch_*`/`_build_*`) | **DTAX-read = an inversion** of proven schema knowledge — new code, but every container the writer fills is one a reader pulls from (not greenfield RE) |
| **CTA** (CT Analyzer) | standalone prior-art `ctan_to_powerdb.py` (PowerDB Forms folder) | **a port** into the lane package |

`PtmModel` (`model.py`) is exactly the **normalized reading model** the architecture needs — typed,
source-faithful, carrying measured **and** corrected values, correction factor, and the instrument's own
grade/assessment. The platform import reuses the **parse half**; the DTAX *write* half is irrelevant here.

---

## 4. Architecture

```
instrument file ─▶ [parse adapter]* ─▶ normalized reading model ─▶ [MAPPING]* ─▶ review gate ─▶ form_field_values
   .ptm/.dtax/.cta    PTM✓ DTAX~ CTA=port   (PtmModel; generalize)   reading→tag    confirm/adjust   (+ provenance/trust)
                                                      ▲
                                       (live test-set adapter plugs in here later — same model, same mapping)
```

Four layers; only **2, 3, 4** are new platform work (layer 1 is mostly banked):

1. **Parse adapter (per format).** file → reading model. PTM ready; DTAX-read = invert the writer;
   CTA = port. Each adapter is isolated and independently testable.
2. **Mapping layer (the new core; §5).** reading-model field → the datasheet control tagged with the
   matching `import {tool, profile}`. *Declarative*, per (tool × profile × apparatus-family).
3. **Identity match (§6).** route the file to the right asset/job/template, or let the tech pick.
4. **Review gate + write (§7–§8).** show proposed values vs targets; on confirm, write to
   `form_field_values` stamped `imported` + provenance.

---

## 5. The mapping contract

The `field_schema` **already declares the targets**: instrument-fillable sections carry
`capture_mode: instrument_import` + an `import {tool, profile}` hint, and each control's `tag` is the
import target id (e.g. the IT CT sheet: `{tool: ct_analyzer, profile: CT_ExcitationCurve}`; the xfmr
sheet's PF section: `{tool: dtax, profile: TX_PFDF}`). The importer never invents targets — it fills
declared ones.

A **mapping table**, keyed by `(tool, profile, apparatus_family)`, declares:
- **scalar** reading-model field → control `tag` (direct).
- **measurement-series** (the reading model's per-phase / per-tap / per-position measurements) →
  **table-section rows**, aligned by a key (phase + tap + winding/position). This row-alignment is the
  one genuinely fiddly part and gets explicit fixtures.
- **value selection**: which of measured / corrected the control wants (default: corrected where the
  instrument provides temperature/standard correction; both retained in provenance).

Declarative (data, not code) so each family's mapping is reviewable + testable in isolation, and adding
a format/family is a table + a parser, never a rewrite.

---

## 6. Identity match

The reading model carries identifiers (`PtmJob.work_order`, `PtmTransformer.serial_number` /
`apparatus_id` / `asset_system_code`, tester, execution date). Resolution order:
1. **Explicit** — the tech uploads the file *into* an open datasheet/job (one file → one known target).
   The simple, default path.
2. **Matched** — batch upload routes by `serial` / `work_order` → `records.assets` / the job, surfacing
   any ambiguous/unmatched for manual resolution (never auto-guess).

First slice implements **(1)**; (2) is an additive follow-up.

---

## 7. Trust & provenance (field-trust integration)

Every imported value lands marked — never silently merged with hand-entry:
- `source = imported` (vs `field` / `manual`), the **instrument** (set serial, SW version, **cal date**),
  the **measured vs corrected** pair + correction factor, and the **instrument's own grade/assessment**.
- The review gate shows this provenance alongside each proposed value.
- Acceptance/pass-fail is still computed against the datasheet's `tolerance_source` window
  (`neta_table` / `mfr`) — the import supplies the *reading*, not the verdict.
- **Partial fill is first-class:** a file fills the controls it covers; the rest stays pending for field
  or manual entry. Coverage shows imported / pending / hand-entered distinctly.

---

## 8. Review gate & write

1. Upload → parse → map → **proposal**: a diff-style view of (control ← proposed value + provenance),
   including unmapped readings and unfilled controls.
2. Tech/office **confirms or adjusts** per value (adjustments recorded as overrides with reason).
3. On commit → `form_field_values` rows written with the provenance of §7; submission `as_found`/
   `as_left` respected; sync per `01-OFFLINE-SYNC-ARCHITECTURE.md`.
4. Re-import is idempotent on `(submission, control, source_file)` — re-uploading replaces, with an
   audit trail, never duplicates.

---

## 9. First slice (acceptance)

**PTM transformer file → `ats_liquid_xfmr_v1` / `ats_dry_xfmr_v1`.** Proves the whole pipeline on the
zero-parser-risk path:
- `read_ptm` (banked) → PtmModel → **new** mapping table `(ptm, *, transformer)` → review proposal →
  write to `form_field_values` with provenance.
- **Done = TDD-green:** a real `.ptm` fixture maps onto the transformer datasheet's PF / turns-ratio /
  winding-resistance / excitation controls (scalars + table-row alignment), every value carries
  provenance, the review proposal lists mapped + unmapped + pending, partial fill verified, re-import
  idempotent.

---

## 10. Build sequencing (proposed chips)

1. **10a — mapping engine + ingest endpoint + review proposal** (no UI), first slice = PTM-transformer;
   TDD against a `.ptm` fixture. *The vertical slice.*
2. **10b — review-gate UI** on the office surface (proposal → confirm/adjust → commit).
3. **10c — DTAX-read adapter** (invert the writer's schema map) → Doble files in.
4. **10d — CTA-read port** → CT Analyzer → the IT/CT datasheets.
5. **10e — batch identity-match** (§6.2).
6. **(later) live test-set source adapter** — reuses the mapping core unchanged.

---

## 11. Open build-time questions (resolve at 10a)

- **`form_field_values` provenance columns** — reuse the existing provenance/sync-contract columns, or
  add an `import_source` sidecar? (Lean: reuse; confirm the column set covers instrument + cal-date +
  measured/corrected.)
- **Ingest surface** — a records-backend endpoint vs the office provisioning app (Chip 5) owning it.
- **PTM packaging** — confirm `.ptm` container handling end-to-end on a real customer export (the
  banked test uses a fixture; validate on a true field file).
- **Mapping authorship** — who owns/edits the per-family mapping tables (engineering vs a config the PM
  can adjust). Lean: engineering-owned, versioned with the template.
