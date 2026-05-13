# Packet 744 Handoff - Apex-FS Ownership Missing-README Errno-Signal Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-744`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_apex_fs_ownership_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 743 required full normalized missing-path evidence for the missing-README branch, the remaining residue in that same local slice was a broad missing-file category regex. The helper path is driven directly by Python `Path.read_text()` on a missing file, so the error surface should carry explicit `errno 2` and canonical Python file-missing phrasing.

## What Changed
- In `test_check_apex_fs_ownership_reports_probe_failure_when_expected_readme_path_is_missing`:
  - kept full normalized missing-path evidence,
  - replaced the broad missing-file category regex with explicit `detail.startswith("[errno 2]")`,
  - required the canonical `no such file or directory` phrase.

## Validation
- Focused probe:
  - `.\.venv\Scripts\python.exe -c "from pathlib import Path; p=Path(r'C:\\definitely-missing-apex-readme.md'); ..."`
  - Result: local Python emitted `[Errno 2] No such file or directory: 'C:\definitely-missing-apex-readme.md'`.
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_apex_fs_ownership_truthfulness.py -q`
  - Result: pass (`9 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 743 to Packet 744.
- Appended Packet 744 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
