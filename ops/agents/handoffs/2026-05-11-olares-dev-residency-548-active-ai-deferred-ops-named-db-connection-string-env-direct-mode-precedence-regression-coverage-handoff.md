# Olares Dev Residency 548 - Active AI Deferred-Ops Named DB-Connection-String-Env Direct-Mode Precedence Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-548`

## Purpose

Restore focused executable proof for the direct deferred-ops helper branch that selects SQLAlchemy direct mode from a caller-chosen `--db-connection-string-env` value before any MCP default can be used.

## Execution Result

Packet 548 is complete.

Extended `tests/test_deferred_ops_view_counts_truthfulness.py` with direct-mode precedence coverage for `tools/ai/check_deferred_ops_view_counts.py`.

The updated regression file now verifies that:

1. the helper still reports `HOLD` when authoritative deferred-operation views are empty,
2. the helper still reports `REOPEN` when any deferred-operation view has rows,
3. the helper still reports `UNAVAILABLE` when the authoritative views are absent,
4. the helper still fails on unexpected query errors,
5. the helper still supports env-driven packet ids and output artifacts,
6. the helper still prefers explicit `APEX_DB_MCP_URL` values over conflicting port defaults when `--db-url` is omitted,
7. the helper still resolves `--db-url-env` from the named environment variable and reports that source even when broader defaults are also present,
8. the helper still fails with the expected env-name error when `--db-url-env` points at an unset variable and no broader DB URL defaults remain available,
9. the helper still fails with the expected env-name error when `--db-connection-string-env` points at an unset variable even if MCP URL defaults are present,
10. the helper now explicitly records `mode: direct` with source `env:DEFERRED_OPS_DB_CONNECTION` and fails in the SQLAlchemy path rather than falling back to MCP defaults when a caller-selected connection-string env is populated.

The new regression uses an intentionally invalid SQLAlchemy URL so the direct path is exercised truthfully without introducing external database setup noise.

## Validation Notes

Focused validation stayed bounded to `tests/test_deferred_ops_view_counts_truthfulness.py`.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_deferred_ops_view_counts_truthfulness.py -q` passed,
2. file diagnostics for `tests/test_deferred_ops_view_counts_truthfulness.py` reported no issues,
3. `git diff --check -- tests/test_deferred_ops_view_counts_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-548-active-ai-deferred-ops-named-db-connection-string-env-direct-mode-precedence-regression-coverage-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/ai/check_deferred_ops_view_counts.py` behavior,
2. hold-boundary wrapper changes,
3. live database setup or direct SQL success-path coverage,
4. shared shell helper changes,
5. broader minimal-MCP or canary surfaces.

## Next Candidate

The direct deferred-ops helper now has current proof for its primary MCP branches, both named-env failure branches, and direct-mode connection-string precedence branch, so the next adjacent uncovered slice is likely either an argument-based direct connection-string branch or a comparably narrow env/error branch in another direct helper.