# Packet 847 Operator Execution Prompt

Scope: execute one bounded delegated dual-lane packet after Packet 846 without reopening helper hardening, controller widening, or service admission.

Copy the prompt below into the delegated execution session when you want to close Packet 847.

---

Close the next post-Packet-846 bounded delegated dual-lane packet by reusing the existing authoritative-host helper surface for a fresh Packet 847 admitted-trio live evidence tuple, while landing one reusable delegated objective-selection rubric under explicit coordinator ownership.

1. Lane A owned surfaces: only the Packet 847 helper-emitted artifacts under tests/canary/host-bootstrap-status/actual and tests/canary/mcp-contract/actual.
2. Lane B owned surface: only `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OBJECTIVE-SELECTION-RUBRIC-2026-05-14.md`.
3. Shared coordinator-owned closeout surfaces remain:
   - `PROJECT_STATUS.md`
   - `docs/operations/AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md`
   - `docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`
   - `docs/operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md`
   - `docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md`
   - `docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`
   - `ops/agents/handoffs/2026-05-14-olares-dev-residency-847-bounded-ai-delegated-objective-selection-rubric-execution-handoff.md`

Guardrails:

1. Do not edit `C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py` or `C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py` in Packet 847. If the helper needs mutation, stop and close Packet 847 as ABORTED rather than reopening hardening.
2. Keep Lane A limited to the admitted `apex-fs`, `apex-db`, and `apex-jobs` trio plus the repo-visible Packet 847 artifact tuple.
3. Keep Lane B limited to the single rubric surface listed above.
4. Do not widen controller scope, service admission, auth, ingress, runtime posture, or business logic.
5. Do not open `ai_tasks` ownership.
6. Keep the Operations Visibility lane explicitly trigger-gated `HOLD`; do not reopen it inside Packet 847.

Execution order:

1. First run the focused helper truthfulness slice exactly:
   - `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py"`
2. Only if that passes, run the live helper exactly for Packet 847:
   - `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py" --packet-id 2026-05-14-olares-dev-residency-847 --output "C:/APEX Platform/apex-power-ops-platform/tests/canary/mcp-contract/actual/run-authoritative-host-packet-2026-05-14-olares-dev-residency-847.json"`
3. Lane B may author only `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OBJECTIVE-SELECTION-RUBRIC-2026-05-14.md` and should describe the reusable objective-selection rules for later delegated packets after Packet 846: selection rules, candidate classes, rejection criteria, packet selection procedure, and Packet 847 application.
4. Validate Lane B by anchor scan against: `Selection Rules`, `Candidate Classes`, `Mandatory Rejection Criteria`, `Packet Selection Procedure`, `Packet 847 Application`, and `trigger-gated HOLD`.
5. Report the packet result in three tuples:
   - Lane A tuple: focused pytest command and result, live helper command and result, exact Packet 847 artifact names, and final host rest-state result.
   - Lane B tuple: touched file, anchor validation result, and confirmation that no lane widened beyond its declared file.
   - Coordinator tuple: shared closeout surfaces updated only after both lane tuples are green, publication result, and authoritative-host parity result.

If Packet 847 succeeds:

1. preserve Packet 845 as the current higher-level guidance realignment refresh floor, Packet 844 as the current post-guidance control realignment refresh floor, Packet 837 as the current live guidance-refresh floor, Packet 835 as the current orchestration entry floor, and Packet 836 as the current execution-plan and authority floor,
2. record Packet 847 as the reusable delegated objective-selection rubric floor on top of those preserved contracts,
3. publish only after both lane validations and the final host `not-running` rest state are confirmed.

If Packet 847 aborts:

1. do not publish partial closeout updates,
2. record the exact abort trigger,
3. leave the helper and authority boundary unchanged.