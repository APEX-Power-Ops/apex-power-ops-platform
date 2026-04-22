"""
Schedule bridge package — packet UI-002a.

This package owns the read-only P6 schedule-context bridge:

* `loader`   — imports P6 data (via PyP6Xer if a .xer file is present,
               else from a JSON fixture) into the `schedule.*` tables.
* `queries`  — read-only SQL helpers used by the schedule router.
* `fixtures` — small hand-authored JSON extracts used by local smoke runs.

The seam boundary is preserved: the schedule package does NOT write to
`seam.*` and the mutation pipeline does NOT write to `schedule.*`.
"""
