# Olares AI Delegated Dual-Lane Operator Prompt Template

Date: 2026-05-13
Status: Active delegated operator prompt template
Scope: reusable absolute-path copy-paste prompt skeleton for delegated dual-lane packets after Packet 831

## Purpose

Use this template when a later Olares AI/operator packet delegates one live evidence lane and one disjoint scaffold or publication lane under coordinator ownership.

The template complements `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md` by turning the ownership, validation order, abort rules, and closeout tuple into a packet-ready operator prompt with absolute paths.

## Required Replacements

Replace every placeholder before execution:

1. `{{PACKET_ID}}`: packet id such as `2026-05-13-olares-dev-residency-832`
2. `{{PACKET_FILE}}`: absolute path to the packet JSON
3. `{{LANE_B_FILE}}`: absolute path to the single Lane B owned surface
4. `{{LANE_B_SCOPE}}`: one-sentence summary of Lane B scope
5. `{{LANE_B_VALIDATION}}`: narrow validation rule for Lane B
6. `{{HANDOFF_FILE}}`: absolute path to the coordinator-owned closeout handoff

## Absolute Paths

Keep every read-first file and every command path absolute so the delegated session can copy and paste the prompt without reconstructing local path assumptions.

## Prompt Skeleton

```text
Execute {{PACKET_ID}} as a bounded delegated dual-lane packet.

Read first:
1. {{PACKET_FILE}}
2. C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md
3. C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md
4. C:/APEX Platform/apex-power-ops-platform/docs/operations/AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md
5. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md
6. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md
7. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md

Lane design:
1. Lane A name: helper-driven live host evidence lane
2. Lane A owned surfaces: only the packet-specific helper-emitted artifacts under tests/canary/host-bootstrap-status/actual and tests/canary/mcp-contract/actual
3. Lane B name: delegated scaffold lane
4. Lane B owned surface: {{LANE_B_FILE}}
5. Coordinator-owned shared surfaces: C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md and {{HANDOFF_FILE}}

Execution rules:
1. Do not edit C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py or C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py. If the helper needs mutation, stop and close the packet as ABORTED.
2. Start Lane A with the focused helper check:
   & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py
3. Only if that passes, run the live helper exactly for {{PACKET_ID}} with the packet-scoped output path under tests/canary/mcp-contract/actual.
4. Lane B may author only {{LANE_B_FILE}} and should stay limited to {{LANE_B_SCOPE}}.
5. Validate Lane B with {{LANE_B_VALIDATION}}.
6. Shared publication surfaces may be updated only by the coordinator after both lane validations are green and the host has returned to truthful not-running rest state.
7. Abort the packet if either lane needs a file outside its declared set, if the helper precheck fails, if the live helper run fails, if a new MCP service is admitted, if ai_tasks ownership is opened, or if auth, ingress, runtime posture, or business-logic scope widens.

Required outputs:
1. Lane A tuple: focused pytest command and result, live helper command and result, exact packet artifact names, and final host rest-state result.
2. Lane B tuple: touched file, validation method, validation result, and exact scaffold scope.
3. Coordinator tuple: shared publication files, combined validation result, authoritative-host parity result, and final packet verdict PASS or ABORTED.
4. Explicit confirmation that no helper mutation, controller widening, service admission widening, auth change, ingress change, runtime mutation, or business-logic mutation was opened.
```

## Packet 832 Application

Packet `2026-05-13-olares-dev-residency-832` is the first packet to publish this reusable operator prompt template on top of the Packet 831 delegated split-governance floor.