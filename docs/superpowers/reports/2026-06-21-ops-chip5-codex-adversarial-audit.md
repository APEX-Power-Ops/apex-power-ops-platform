# Ops Chip 5 Codex Adversarial Audit Report

Date: 2026-06-21
Auditor: Codex
Scope: Ops Chip 5 Estimator Intake Envelope, SDD tasks 1-16, current host branch state

## Scope Audited

Host worktree:

```text
/home/olares/code/apex/apex-ops-chip5
```

Branch state audited:

```text
ops/chip5-intake-envelope
HEAD a2d397bb
code tip 2792be7c
origin/main base 94db4727
```

Controlling audit brief:

```text
.superpowers/sdd/CODEX_AUDIT_BRIEF.md
```

No files were modified in the host worktree during the audit.

## Finding

### Important: Package Guard Exceptions Still Leak Dollar-Bearing Identifiers

Files:

```text
packages/ops-intake/src/ops_intake/envelope.py:134-137
packages/ops-intake/src/ops_intake/envelope.py:175-179
```

Requirement violated:

Guard errors must be value-free. Finance redaction applies to guard error messages, not only findings/API responses.

Current state:

The API review route correctly converts guard `ValueError` exceptions to a generic PM-safe 400 response. However, the package-level guard exception text still includes raw `scope_name` / `line_uid` identifiers. If a workbook-controlled identifier contains dollar-looking text, that text can appear in direct package exceptions, logs, or any future caller that does not apply the API's generic masking.

Repro output from the audit probe:

```text
direct_guard_msg scope 'X $9' quote field 'onsite_labor' is not editable has_dollar= True has_values= False
```

Impact:

PM UI/API paths are protected today, but the lower-level package contract is not fully finance-redaction-safe. This is a future-surface/logging leak risk.

Recommended fix:

Remove raw `scope_name` and `line_uid` values from guard exception strings, or replace them with stable non-source-derived indexes such as `scope #1` / `line #1`. Keep raw source identifiers only in finance-only diagnostic channels when needed.

## Validation Run

All declared suites passed at current host tip.

```text
package:   46 passed, 2 skipped
migration: 10 passed
API:       17 passed, 3 deprecation warnings
UI:        typecheck passed, 12 unit passed, build passed, 1 smoke passed
```

Additional probe evidence:

```text
distinct_project_numbers AUDIT-A AUDIT-B True
missing_identity rejected parse_error False
json_scope_dollar_messages ... False
domain_after_create all six domain tables = 0, standard_hours = 0
patch_approved_exception RunNotActive True
post_approve_counts standard_hours = 0
```

Git hygiene:

```text
host worktree clean
git diff --check clean
```

## Task Verdicts

Tasks 1-3: Pass.

Tasks 4-8: Pass.

Task 9: Issue. The default-deny review guard is functionally correct, and API masking is correct, but direct package guard exception text is not fully dollar-free for dollar-bearing source identifiers.

Tasks 10-16: Pass.

## Merge Guidance

The branch is broadly hardened and the primary suites are green. Before merge, fix the package-level guard exception text so the lower-level package contract matches the API/UI finance-redaction contract.
