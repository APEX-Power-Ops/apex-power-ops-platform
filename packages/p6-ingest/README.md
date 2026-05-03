# Apex P6 Ingest

This package restores the bounded `p6-ingest` runtime contract used by the
Olares workstation proof, MCP `apex-p6` bridge, and committed canary outputs.

Current posture:
- intentionally read-only and bounded to the admitted Stack Data Center fixture
- exposes a stable runtime health contract and fixture summary contract
- does not claim schedule-write behavior, database integration, or generic XER ingest

Local runtime use:
- install in editable mode from `packages/p6-ingest` with `python -m pip install -e .`
- run the bounded runtime shell with `apex-p6-runtime`
- override the listen port with `PORT` or `APEX_P6_RUNTIME_PORT`
- override the fixture path with `APEX_P6_FIXTURE_PATH` when rerunning against a relocated admitted fixture
