# AI Backbone Canary Evidence Bundle

Date: 2026-05-08
Status: Active bounded hardening checklist
Scope: minimum canary and evidence bundle for the admitted Olares AI backbone

## Purpose

This document defines the smallest truthful evidence bundle for the current admitted backbone.

It is intended to keep future scaffold or hardening work from claiming readiness based on partial or non-comparable proof.

## Minimum Backbone Evidence Bundle

The current backbone evidence bundle should include all of the following when a packet claims meaningful verification:

1. MCP tool-resolution proof for `apex-fs`, `apex-db`, and `apex-jobs`
2. a bounded filesystem read proof through `apex-fs`
3. a bounded database query proof through `apex-db`
4. `apex-jobs` run start and end proof
5. explicit proof that `promote_packet` refuses without successful `env=host` evidence
6. packet-attributed outcome notes in repo-visible packet or handoff artifacts

## MCP Boundary Rules

For the current admitted backbone, the MCP boundary rules are:

1. only `apex-fs`, `apex-db`, and `apex-jobs` are inside the current AI backbone boundary,
2. filesystem access remains bounded to the approved roots exposed by `apex-fs`,
3. database access remains bounded to the read-only or admitted query surface exposed by `apex-db`,
4. run-ledger and promotion control remain bounded to `apex-jobs`,
5. broader MCP families must not be implied by a passing backbone canary.

## Evidence Classes

Interpret evidence in this order:

1. executable verification results,
2. packet JSON validation summaries,
3. packet handoff notes,
4. surrounding descriptive docs.

If these conflict, executable verification and packet evidence win over descriptive prose.

## Minimum Commands

The current minimum executable proof for this lane is:

1. `python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id>` or the repo-local interpreter equivalent,
2. any narrower trust-boundary check added by the active packet,
3. `git diff --check` on touched files.

## Packet 172 Outcome

Packet 172 proves the current hardening lane with:

1. the existing minimal MCP trio verification,
2. a new executable promotion-refusal assertion in `verify_minimal_mcp_trio.py`,
3. explicit trust, provenance, and evidence contracts published in repo-owned docs.

## Non-Goals

This evidence bundle does not prove:

1. broader AI-service readiness,
2. host promotion readiness by itself,
3. public ingress readiness,
4. business-logic completion.