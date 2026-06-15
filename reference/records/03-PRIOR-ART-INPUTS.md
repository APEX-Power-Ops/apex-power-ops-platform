# NETA Records — Prior Art & Inputs Register

> **A register of preserved early attempts and raw inputs — none authoritative.**
> These are host-only materials (outside the repo) kept to review, resume, or build
> upon later. **Nothing here is an official source.** Promote anything into the lane
> only through a chip, with explicit review; until then it is reference-only.

- **Status:** LIVING — opened 2026-06-14
- **Owner:** APEX NETA Records lane
- **Rule:** off-repo paths are **not committed** (large / non-authoritative / early). This
  file is the only committed trace; the materials stay on the operator workstation.

---

## Register

| Input (host path) | What it is | Feeds | Authority |
|---|---|---|---|
| `D:\PDB\` | Legacy field-test datastore export + live DB mirror | `02-LEGACY-BASELINE.md` (capability floor); Chip 9 migration | Baseline only (see `02`) — not a target |
| `C:\Users\jjswe\Downloads\NETA Procedures bundle.zip` (~17 MB) | Collection of numbered NETA procedure PDFs by section (e.g. `7-16-2-1` MCC, `7-27` Arc Energy Reduction) + nested `NETA_Procedures_Individual_PDFs.zip` | Chip 2 (template seed / field-coverage); `asset_classes` + `neta_section` | Non-authoritative early collection — confirm against official NETA before use |
| `C:\Users\jjswe\Downloads\RESA_Report_Scripts.zip` (~31 KB, 9 files) | Early report builders — `build_pilot_report.py`, `build_proc_pdf.py`, `build_individuals.py`, `build_report_template.js`, `build_nebius_report.py`, `lock_template.py`, `fix_fields.py` | **D-FORMS** report-generation domain (`00` §6); Chip 7 | One of several early report-gen variants — input to the D-FORMS consolidation, not a chosen engine |
| `D:\apex-power-ops-platform\` | Early **non-git** snapshot of a platform structure (`.claude`, `ops`, `packages`, `spec`, `REPO_PASSPORT.md`); Apr–May 2026 | General prior-art; possible salvage for `packages/` / `spec/` ideas | Superseded by this repo — review-only, do not re-import wholesale |

---

## Handling rules

1. **Do not import wholesale.** Treat each as an extraction lane: review, then move only
   approved slices into the repo through a chip (mirrors `AGENTS.md` source-domain rules).
2. **Re-verify before trusting.** Early bundles may be stale or partial; the NETA PDFs in
   particular must be checked against official NETA editions before seeding templates.
3. **D-FORMS gate.** `RESA_Report_Scripts` and the existing `forms-engine` /
   `power-test-converters` / `neta-forms` variants are all *inputs* to the held D-FORMS
   decision (`00` §6) — none is the chosen report engine yet.
4. **Keep this register current.** Add new preserved inputs here as they surface; mark
   any item retired once its useful content has been promoted or discarded.
