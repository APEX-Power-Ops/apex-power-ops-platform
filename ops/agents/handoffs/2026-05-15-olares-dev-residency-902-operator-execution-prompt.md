# Packet 902 Operator Execution Prompt

Scope: execute one bounded delegated dual-lane packet after Packet 901 without reopening helper hardening, controller widening, or service admission.

Copy the prompt below into the delegated execution session when you want to close Packet 902.

---

Close the next post-Packet-901 bounded delegated dual-lane packet by reusing the existing authoritative-host helper surface for a fresh Packet 902 admitted-trio live evidence tuple, while extending the reusable delegated operator prompt template so later packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, Packet 897, Packet 899, and Packet 901 instead of leaving the reusable operator prompt pinned below the Packet 901 packet-template operator-prompt floor refresh.

1. Lane A owned surfaces: only the Packet 902 helper-emitted artifacts under tests/canary/host-bootstrap-status/actual and tests/canary/mcp-contract/actual.
2. Lane B owned surface: only `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md`.
3. Shared coordinator-owned closeout surfaces remain:
   - `PROJECT_STATUS.md`
   - `docs/operations/AI-BACKBONE-PARALLEL-HARDENING-BRIEF-2026-05-08.md`
   - `docs/operations/OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`
   - `docs/operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md`
   - `docs/operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md`
   - `docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`
   - `ops/agents/handoffs/2026-05-15-olares-dev-residency-902-bounded-ai-delegated-operator-prompt-template-packet-definition-floor-refresh-execution-handoff.md`

Guardrails:

1. Do not edit `C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py` or `C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py` in Packet 902. If the helper needs mutation, stop and close Packet 902 as ABORTED rather than reopening hardening.
2. Keep Lane A limited to the admitted `apex-fs`, `apex-db`, and `apex-jobs` trio plus the repo-visible Packet 902 artifact tuple.
3. Keep Lane B limited to the single operator-prompt-template surface listed above.
4. Do not widen controller scope, service admission, auth, ingress, runtime posture, or business logic.
5. Do not open `ai_tasks` ownership.
6. Keep the Operations Visibility lane explicitly trigger-gated `HOLD`; do not reopen it inside Packet 902.

Execution order:

1. First run the focused helper truthfulness slice exactly:
   - `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py"`
2. Only if that passes, run the live helper exactly for Packet 902:
   - `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py" --packet-id 2026-05-15-olares-dev-residency-902 --output "C:/APEX Platform/apex-power-ops-platform/tests/canary/mcp-contract/actual/run-authoritative-host-packet-2026-05-15-olares-dev-residency-902.json"`
3. Lane B may author only `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OPERATOR-PROMPT-TEMPLATE-2026-05-13.md` and should extend the reusable delegated operator prompt template so later packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, Packet 897, Packet 899, and Packet 901.
4. Validate Lane B by anchor scan against: `after Packet 901`, `Packet 897, Packet 899, and Packet 901`, `Packet 902 Extension`, and `Packet 901 packet-template operator-prompt floor refresh`.
5. Report the packet result in three tuples:
   - Lane A tuple: focused pytest command and result, live helper command and result, exact Packet 902 artifact names, final host rest-state result, and the compact helper proof summary line.
   - Lane B tuple: touched file, anchor validation result, and confirmation that no lane widened beyond its declared file.
   - Coordinator tuple: shared closeout surfaces updated only after both lane validations are green, publication result, and authoritative-host parity result.

If Packet 902 succeeds:

1. preserve Packet 902 as the current delegated operator-prompt-template packet-definition floor refresh floor, Packet 901 as the current delegated packet-template operator-prompt floor refresh floor, Packet 900 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 899 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 898 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 897 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 896 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 895 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 894 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 893 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 892 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 891 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 890 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 889 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 888 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 887 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 886 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 885 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 884 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 883 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 882 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 881 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 880 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 879 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 878 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 877 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 876 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 875 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 874 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 873 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 872 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 871 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 870 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 869 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 868 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 867 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 866 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 865 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 864 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 863 as the prior delegated packet-template operator-prompt floor refresh floor, Packet 862 as the prior delegated operator-prompt-template packet-definition floor refresh floor, Packet 861 as the current delegated packet-template operator-prompt floor extension floor, Packet 860 as the current delegated operator-prompt-template packet-definition floor extension floor, Packet 859 as the current delegated packet-template operator-prompt-routing extension floor, Packet 858 as the current delegated operator-prompt-template packet-definition-routing extension floor, Packet 857 as the current delegated packet-template prompt-contract extension floor, Packet 855 as the current delegated packet-template extension floor, Packet 854 as the current delegated checklist extension floor, Packet 853 as the current delegated closeout-template extension floor, Packet 852 as the current delegated proof-summary note floor, Packet 851 as the current delegated parity-remediation note floor, Packet 850 as the current delegated status-alignment note floor, Packet 849 as the current delegated artifact-reading note floor, Packet 848 as the current delegated lane-selection note floor, Packet 847 as the current delegated objective-selection rubric floor, Packet 845 as the current higher-level guidance realignment refresh floor, Packet 844 as the current post-guidance control realignment refresh floor, Packet 837 as the current live guidance-refresh floor, Packet 835 as the current orchestration entry floor, and Packet 836 as the current execution-plan and authority floor,
2. record Packet 902 as the reusable delegated operator-prompt-template packet-definition floor refresh on top of those preserved contracts,
3. publish only after both lane validations and the final host `not-running` rest state are confirmed.

If Packet 902 aborts:

1. do not publish partial closeout updates,
2. record the exact abort trigger,
3. leave the helper and authority boundary unchanged.
