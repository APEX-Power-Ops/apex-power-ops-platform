# Olares AI Delegated Dual-Lane Objective Selection Rubric

Date: 2026-05-14
Status: Active delegated objective-selection rubric
Scope: reusable selector for choosing the next bounded delegated dual-lane packet objective after Packet 846

## Purpose

Use this rubric when the current AI/operator stack has already preserved the helper floor, template stack, publication hygiene, and authoritative-host parity, but the next bounded delegated packet still needs a concrete disjoint objective instead of a generic "fresh delegated packet" placeholder.

This rubric complements `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md`, `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md`, `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-COORDINATOR-CLOSEOUT-TEMPLATE-2026-05-13.md`, and `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PACKET-TEMPLATE-2026-05-13.md` by making the missing decision step explicit: which single Lane B scaffold objective should the next delegated packet carry while Lane A reuses the unchanged authoritative-host helper surface.

## Selection Rules

Choose the next delegated packet objective in this order:

1. Reject any candidate that reopens solved publication, host-parity, helper-hardening, auth, ingress, runtime, controller, or service-admission work.
2. Reject any candidate that requires Lane B to own more than one primary scaffold surface unless a later bounded packet explicitly widens that rule.
3. Prefer candidates that convert a recurring generic instruction into a reusable repo-owned surface.
4. Prefer docs, checklist, template, rubric, contract-note, and coordinator-owned decision surfaces over shared implementation edits.
5. Keep the Operations Visibility lane trigger-gated `HOLD` unless authoritative live-row evidence changes or a separately admitted consumer path changes the truthful interpretation of zero rows.
6. Prefer objectives that make the next delegated packet easier to define, execute, or close out without weakening the admitted helper contract.

## Candidate Classes

Score later candidate objectives against these classes:

1. reusable selection surfaces:
   - objective-selection rubric
   - lane-selection note
   - coordinator routing surface
2. reusable delegated governance surfaces:
   - checklist extension
   - prompt extension
   - closeout extension
   - packet-definition extension
3. reusable evidence interpretation surfaces:
   - artifact-reading note
   - parity-remediation note
   - proof-summary note
4. bounded status-alignment surfaces:
   - one higher-level guidance surface family
   - one active control surface family

## Mandatory Rejection Criteria

Do not select a delegated objective if it:

1. depends on changing `tools/ai/run_authoritative_host_packet.py` or `tests/test_run_authoritative_host_packet_truthfulness.py`,
2. requires a new MCP service beyond `apex-fs`, `apex-db`, and `apex-jobs`,
3. opens `ai_tasks` ownership,
4. depends on live Operations Visibility row growth that has not been observed,
5. turns a bounded delegated packet into a generic planning or migration lane,
6. needs more than one disjoint Lane B owner file without a separately declared widening packet.

## Packet Selection Procedure

When choosing the next delegated packet:

1. name the preserved floors first: Packet 845 guidance, Packet 844 control, Packet 837 live guidance, Packet 835 orchestration entry, and Packet 836 execution plan plus authority,
2. state the Operations Visibility lane explicitly as trigger-gated `HOLD`,
3. list two or three candidate Lane B objectives,
4. reject any candidate that violates the mandatory rejection criteria,
5. select the smallest remaining objective that creates a reusable future control surface,
6. route the packet through the published Packet 831 checklist plus the Packet 832, Packet 833, and Packet 834 templates.

## Packet 847 Application

Packet `2026-05-14-olares-dev-residency-847` is the first delegated packet to publish this rubric after Packet 846 closed publication and authoritative-host parity. Its Lane B objective is this rubric itself, because the current stack had already restored host parity and proof cadence but still lacked a reusable repo-owned way to turn "fresh delegated packet" guidance into a concrete next objective without reopening controller scope.