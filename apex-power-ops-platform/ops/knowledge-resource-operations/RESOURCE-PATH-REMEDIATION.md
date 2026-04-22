# Supabase Source Path Remediation
## Date: 2026-03-24
## Status: ACTIVE

---

## Summary

- Auto-fix rows ready to apply: 0
- Manual-review rows remaining: 2
- review:historical-source-retired: 2

## Manual Review Rows

| Content ID | Reason | Old Path | Suggested Path | Notes |
|------------|--------|----------|----------------|-------|
| EXT-IEEE-030 | historical-source-retired | Resources/Testing Resources/Other Specs/Power Transformers/Standards/C57.13-1993.pdf | — | Original 1993 source PDF was removed during Testing Resources triage as superseded by the 2016 library edition; decide whether to retain stale metadata, clear source_path, or point to an archived evidence store. |
| EXT-IEEE-040 | historical-source-retired | Resources/Source-PDFs/IEEE-Standards/ANSI IEEE C37.20.1-2002 Standard for Metal-Enclosed Low-Voltage Power....pdf | — | Original 2002 source PDF is no longer present in the canonical source library; do not remap this extraction to the 2015 edition because the extraction remains a retained historical reference. |

## Decision Notes

- `alias-only` means the folder rename alone fixes the row and the canonical file exists on disk.
- `explicit-remap` means the original filename no longer matches disk, but the correct canonical file has been verified locally.
- `historical-source-retired` means the extraction remains valid, but the original source PDF is no longer present in the canonical library and should not be silently repointed to a newer edition.
- Manual-review rows remain because the exact historical source is absent, ambiguous, or should potentially be retired rather than rewritten.
