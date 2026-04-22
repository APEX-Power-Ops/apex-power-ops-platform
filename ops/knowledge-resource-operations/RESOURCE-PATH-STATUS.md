# Supabase Source Path Audit
## Date: 2026-03-24
## Status: ACTIVE

---

## Summary

- Supabase study_content rows audited: 873
- Rows still using renamed Source-PDFs aliases: 1
- Alias rows that resolve on disk after folder normalization only: 0
- Alias rows still unresolved after normalization: 1
- Rows still pointing into legacy Testing Resources: 1

## Canonical Source-PDFs Folders

- Resources/Source-PDFs/IEEE/
- Resources/Source-PDFs/IEC/
- Resources/Source-PDFs/UL/
- Resources/Source-PDFs/NETA/
- Resources/Source-PDFs/Equipment-Manuals/
- Resources/Source-PDFs/Textbooks/

## Legacy Path Buckets

### Resources/Source-PDFs/IEEE-Standards/

- Rows: 1
- Canonical prefix: Resources/Source-PDFs/IEEE/
- Resolve on disk after alias rewrite: 0/1
- Sample rows:
  - EXT-IEEE-040 -> Resources/Source-PDFs/IEEE-Standards/ANSI IEEE C37.20.1-2002 Standard for Metal-Enclosed Low-Voltage Power....pdf

### Resources/Testing Resources/

- Rows: 1
- Canonical prefix: none — requires manual remap or retirement
- Sample rows:
  - EXT-IEEE-030 -> Resources/Testing Resources/Other Specs/Power Transformers/Standards/C57.13-1993.pdf

## Stale After Alias Normalization

These rows still fail after folder normalization, which means the filename or deeper subpath no longer matches disk.

- EXT-IEEE-040
  - raw: Resources/Source-PDFs/IEEE-Standards/ANSI IEEE C37.20.1-2002 Standard for Metal-Enclosed Low-Voltage Power....pdf
  - normalized: Resources/Source-PDFs/IEEE/ANSI IEEE C37.20.1-2002 Standard for Metal-Enclosed Low-Voltage Power....pdf

## Operational Guidance

- Active pipeline scripts should normalize renamed Source-PDFs aliases before reading or classifying local files.
- Testing Resources paths should be treated as legacy metadata, not as canonical current-library paths.
- Non-standard field guides may legitimately normalize into non-standards categories such as Resources/Source-PDFs/Textbooks/ when a triage move has already been executed and indexed in the resource manifest.
- Supabase rows that still fail after alias normalization need targeted filename-level remediation.
