# Olares Dev Residency 835 Operator Execution Prompt

Date: 2026-05-13
Status: Active repo-owned operator prompt surface
Packet: `ops/agents/packets/draft/2026-05-13-olares-dev-residency-835-bounded-ai-delegated-orchestration-status-alignment-execution.json`
Scope: execute one bounded delegated dual-lane packet after Packet 834 without reopening helper hardening, controller widening, or service admission

## Use

Copy the prompt below into the delegated execution session when you want to close Packet 835.

## Prompt

```text
Execute Olares Dev Residency 835 as a bounded delegated dual-lane packet.

Read first:
1. C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-13-olares-dev-residency-835-bounded-ai-delegated-orchestration-status-alignment-execution.json
2. C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md
3. C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md
4. C:/APEX Platform/apex-power-ops-platform/docs/operations/AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md
5. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md
6. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md
7. C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md
8. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md
9. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md
10. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md
11. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-COORDINATOR-CLOSEOUT-TEMPLATE-2026-05-13.md
12. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PACKET-TEMPLATE-2026-05-13.md
13. C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-13-olares-dev-residency-834-bounded-ai-delegated-packet-template-execution-handoff.md

Objective:
Close the next post-Packet-834 bounded delegated dual-lane packet by reusing the existing authoritative-host helper surface for a fresh Packet 835 admitted-trio live evidence tuple, while aligning the higher-level orchestration brief, parallel-readiness checklist, and workflow-first runbook to the published delegated Packet 831 through Packet 834 stack under explicit coordinator ownership.

Lane design:
1. Lane A name: helper-driven live host evidence lane
2. Lane A owned surfaces: only the Packet 835 helper-emitted artifacts under tests/canary/host-bootstrap-status/actual and tests/canary/mcp-contract/actual
3. Lane B name: orchestration entry-surface alignment lane
4. Lane B owned surfaces:
   - C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md
   - C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md
   - C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md
5. Coordinator-owned shared surfaces:
   - C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md
   - C:/APEX Platform/apex-power-ops-platform/docs/operations/AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md
   - C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md
   - C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-13-olares-dev-residency-835-bounded-ai-delegated-orchestration-status-alignment-execution-handoff.md

Execution rules:
1. Do not edit C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py or C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py in Packet 835. If the helper needs mutation, stop and close Packet 835 as ABORTED rather than reopening hardening.
2. Keep Lane A limited to the admitted apex-fs, apex-db, and apex-jobs trio plus the repo-visible Packet 835 artifact tuple.
3. Start Lane A with the focused helper check:
   & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py"
4. Only if that passes, run the live helper exactly for Packet 835:
   & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py" --packet-id 2026-05-13-olares-dev-residency-835 --output "C:/APEX Platform/apex-power-ops-platform/tests/canary/mcp-contract/actual/run-authoritative-host-packet-2026-05-13-olares-dev-residency-835.json"
5. Lane B may author only the three entry surfaces listed above and should align them to the published delegated Packet 831 through Packet 834 execution stack: current proof floor, delegated template reuse guidance, explicit helper-backed delegated posture, and bounded next-step wording.
6. Validate Lane B with a required-anchor scan for:
   - status brief: `Packet 831`, `Packet 832`, `Packet 833`, `Packet 834`, `Current delegated proof floor`, and `Immediate Next Steps`
   - readiness checklist: `Packet 834`, `Current proof floor for this cadence`, `Current delegated template stack`, and `Checklist I - First Two-Lane Rehearsal Evidence Pattern`
   - workflow-first runbook: `Current Trust Model`, `Current delegated execution posture`, `run_authoritative_host_packet.py`, and `Current Follow-On`
7. Do not let Lane B edit helper code, helper tests, or live artifact files.
8. Shared publication surfaces may be updated only by the coordinator after both lane validations are green and the host has returned to truthful not-running rest state.
9. Abort the packet if either lane needs a file outside its declared set, if the helper precheck fails, if the live helper run fails, if a new MCP service is admitted, if ai_tasks ownership is opened, or if auth, ingress, runtime posture, or business-logic scope widens.

Required outputs:
1. Lane A tuple: focused pytest command and result, live helper command and result, exact Packet 835 artifact names, and final host rest-state result.
2. Lane B tuple: touched files, validation method, validation result, and exact alignment scope.
3. Coordinator tuple: shared publication files, combined validation result, authoritative-host parity result, and final packet verdict PASS or ABORTED.
4. Explicit confirmation that no helper mutation, controller widening, service admission widening, auth change, ingress change, runtime mutation, or business-logic mutation was opened.

If Packet 835 succeeds:
1. preserve Packet 830 as the helper floor, Packet 831 as the delegated split-governance floor, Packet 832 as the delegated operator prompt template floor, Packet 833 as the delegated coordinator closeout template floor, and Packet 834 as the delegated packet-definition template floor
2. record Packet 835 as the higher-level orchestration entry-surface alignment floor on top of those preserved contracts
3. keep the next step bounded to another delegated packet with a new disjoint lane objective, not controller widening

If Packet 835 aborts:
1. stop at the first truthful blocker
2. do not repair the helper inside this packet
3. record the exact abort rule that fired and the smallest truthful next packet candidate
```