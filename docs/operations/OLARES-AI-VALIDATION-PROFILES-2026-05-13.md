# Olares AI Validation Profiles

Date: 2026-05-13
Status: Active bounded verifier and wrapper hardening
Scope: named validation-profile surface for the admitted minimal MCP trio verifier and its operator wrappers

## Purpose

This document defines the named validation profiles for `tools/ai/verify_minimal_mcp_trio.py`.

The goal is to let later packets and operator evidence name the verifier strictness they relied on without widening the admitted MCP boundary or inventing packet-local meanings for the same helper.

## Active Profiles

### `baseline`

`baseline` is the default verifier posture.

Contract:

1. require tool-resolution proof for `apex-fs`, `apex-db`, and `apex-jobs`,
2. require bounded filesystem read proof,
3. require `apex-jobs` promotion-refusal, start, end, and `list_runs` visibility proof,
4. allow the bounded `apex-db` query check to degrade instead of failing the whole verifier when that one query cannot complete,
5. emit `"profile": "baseline"` in the verifier summary.

Example command:

```text
python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id>
```

Wrapper examples:

```text
pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId <packet-id>
bash tools/ai/run-minimal-mcp-trio.sh verify <packet-id>
```

### `strict-db-query`

`strict-db-query` keeps the same admitted MCP surface but raises the verifier floor for the bounded database proof.

Contract:

1. inherit every `baseline` check,
2. treat any failure in the bounded `select 1 as ok` query as a verifier failure,
3. emit `"profile": "strict-db-query"` in the verifier summary.

Example command:

```text
python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id> --profile strict-db-query
```

Wrapper examples:

```text
pwsh -NoProfile -File tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId <packet-id> -ValidationProfile strict-db-query
bash tools/ai/run-minimal-mcp-trio.sh verify <packet-id> strict-db-query
```

## Backward Compatibility

The legacy `--require-db-query` flag remains supported.

Current compatibility rule:

1. `--require-db-query` maps to the `strict-db-query` behavior,
2. explicit `--profile`, `-ValidationProfile`, or the Bash profile positional argument is preferred in new packet, handoff, and evidence examples,
3. the emitted verifier payload is the canonical source of which profile actually ran.

## Evidence Expectations

When a packet claims verifier proof through this helper:

1. the emitted JSON should keep the `profile` field alongside `packet_id`, `command`, and `checks`,
2. packet or handoff closeout should name `strict-db-query` explicitly when it is the validation floor,
3. `baseline` should remain the truthful default unless the stricter profile was intentionally selected,
4. Packet `2026-05-13-olares-dev-residency-789` is the first repo-visible strict-profile artifact captured through a wrapper surface at `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-789.json`.

## Boundaries Preserved

This profile surface does not:

1. admit any new MCP service,
2. widen runtime or queue ownership,
3. change the `apex-jobs` promotion gate,
4. change workstation or host secret-boundary rules.