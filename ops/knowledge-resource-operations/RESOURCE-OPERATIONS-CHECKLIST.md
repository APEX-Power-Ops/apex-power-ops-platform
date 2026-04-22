# Resource Operations Checklist
## Intake, Extraction, and Supabase Path Correction
### Version 1.0 | March 25, 2026

---

## Purpose

This is the short operator-facing checklist for repeatable resource work.

Use it together with:

- `MASTER-STANDARDS.md`
- `Development/RESOURCE-GOVERNANCE-AUDIT.md`
- `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md`

---

## A. New Source Intake

Use this when adding or recovering a source PDF.

1. Place the new file in `Resources/Source-PDFs/_Unsorted/` if it is not yet classified.
2. Check for an existing duplicate or newer canonical copy before promotion.
3. Rename the file using the governed naming pattern.
4. Move it into one canonical active category under `Resources/Source-PDFs/`.
5. Do not use or recreate legacy active paths such as `IEEE-Standards/`, `NETA-Standards/`, `Manufacturer-Docs/`, or `Testing Resources/`.
6. Regenerate `Resources/RESOURCE-MANIFEST-RAW.json` after structural changes.
7. Regenerate `Resources/RESOURCE-MANIFEST.json` after structural changes.
8. Update any coverage or intake notes if the new source changes extraction priorities.

## B. New Extraction Creation

Use this when producing a curated extraction from a governed source.

1. Confirm the source file exists at a canonical `Resources/Source-PDFs/...` path.
2. Check `Resources/Extractions/` and `EXTRACTION-CATALOG.md` for an existing extraction.
3. Assign or confirm the correct content ID.
4. Follow `Process-Guides/RESOURCE-EXTRACTION-GUIDE.md` for structure and quality rules.
5. Save the extraction to a canonical extraction category or an approved governed legacy folder.
6. Update `EXTRACTION-CATALOG.md` when the workflow requires it.
7. Treat the extraction as disk-complete only; do not count it as a Supabase record until the reviewed load step happens.

## C. Supabase Source Path Correction

Use this when auditing or correcting `study_content.source_path`.

1. Audit against the current canonical active source library, not against memory or historical aliases.
2. Verify the local file exists before applying any remap.
3. Use canonical repo-relative `Resources/...` paths only.
4. Do not silently repoint a historical extraction to a newer edition just because the filename looks similar.
5. If the original source is no longer present in the active governed library, classify it as `historical-source-retired` instead of guessing.
6. Regenerate `Development/RESOURCE-PATH-STATUS.md` after a correction pass.
7. Regenerate `Development/RESOURCE-PATH-REMEDIATION.md` after a correction pass.
8. Record any residual cases explicitly as verified remaps, alias-only fixes, or retired historical-source cases.

## D. Final Closeout Check

Before considering the run complete:

1. Canonical source location is correct.
2. Manifest files are current.
3. Extraction placement is governed and documented.
4. Supabase path writes use canonical repo-relative paths only.
5. Any unresolved historical-source cases are classified explicitly.
6. Updated audit/status docs reflect the latest run.