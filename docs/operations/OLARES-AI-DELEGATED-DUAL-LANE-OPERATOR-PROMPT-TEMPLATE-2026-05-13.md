# Olares AI Delegated Dual-Lane Operator Prompt Template

Date: 2026-05-13
Status: Active delegated operator prompt template
Scope: reusable absolute-path copy-paste prompt skeleton for delegated dual-lane packets after Packet 899

## Purpose

Use this template when a later Olares AI/operator packet delegates one live evidence lane and one disjoint scaffold or publication lane under coordinator ownership while reusing the Packet 831 split checklist as extended by Packet 854, the Packet 833 closeout template as extended by Packet 853, and the Packet 834 packet-definition template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, Packet 897, and Packet 899.

The template complements `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md` by turning the ownership, validation order, abort rules, closeout tuple, and current delegated note stack into a packet-ready operator prompt with absolute paths.

## Required Replacements

Replace every placeholder before execution:

1. `{{PACKET_ID}}`: packet id such as `2026-05-13-olares-dev-residency-832`
2. `{{PACKET_FILE}}`: absolute path to the packet JSON
3. `{{LANE_B_FILE}}`: absolute path to the single Lane B owned surface
4. `{{LANE_B_SCOPE}}`: one-sentence summary of Lane B scope
5. `{{LANE_B_VALIDATION}}`: narrow validation rule for Lane B
6. `{{COORDINATOR_SHARED_FILES}}`: absolute-path bullet list of coordinator-owned publication surfaces beyond `PROJECT_STATUS.md`
7. `{{HANDOFF_FILE}}`: absolute path to the coordinator-owned closeout handoff

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
8. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-COORDINATOR-CLOSEOUT-TEMPLATE-2026-05-13.md
9. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PACKET-TEMPLATE-2026-05-13.md
10. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-OBJECTIVE-SELECTION-RUBRIC-2026-05-14.md
11. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-LANE-SELECTION-NOTE-2026-05-14.md
12. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-ARTIFACT-READING-NOTE-2026-05-14.md
13. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-STATUS-ALIGNMENT-NOTE-2026-05-14.md
14. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PARITY-REMEDIATION-NOTE-2026-05-14.md
15. C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-PROOF-SUMMARY-NOTE-2026-05-14.md

Lane design:
1. Lane A name: helper-driven live host evidence lane
2. Lane A owned surfaces: only the packet-specific helper-emitted artifacts under tests/canary/host-bootstrap-status/actual and tests/canary/mcp-contract/actual
3. Lane B name: delegated scaffold lane
4. Lane B owned surface: {{LANE_B_FILE}}
5. Coordinator-owned shared surfaces:
   - C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md
{{COORDINATOR_SHARED_FILES}}

Execution rules:
1. Do not edit C:/APEX Platform/apex-power-ops-platform/tools/ai/run_authoritative_host_packet.py or C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py. If the helper needs mutation, stop and close the packet as ABORTED.
2. Start Lane A with the focused helper check:
   & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest C:/APEX Platform/apex-power-ops-platform/tests/test_run_authoritative_host_packet_truthfulness.py
3. Only if that passes, run the live helper exactly for {{PACKET_ID}} with the packet-scoped output path under tests/canary/mcp-contract/actual.
4. Lane B may author only {{LANE_B_FILE}} and should stay limited to {{LANE_B_SCOPE}}.
5. Validate Lane B with {{LANE_B_VALIDATION}}.
6. When the packet reuses the delegated template stack, treat split wording as the Packet 831 checklist extended by Packet 854, coordinator closeout wording as the Packet 833 template extended by Packet 853, and packet-definition wording as the Packet 834 template extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, Packet 897, and Packet 899.
7. Shared publication surfaces may be updated only by the coordinator after both lane validations are green and the host has returned to truthful not-running rest state.
8. Abort the packet if either lane needs a file outside its declared set, if the helper precheck fails, if the live helper run fails, if a new MCP service is admitted, if ai_tasks ownership is opened, if a trigger-gated HOLD lane is reopened without new authoritative evidence, or if auth, ingress, runtime posture, or business-logic scope widens.

Required outputs:
1. Lane A tuple: focused pytest command and result, live helper command and result, exact packet artifact names, final host rest-state result, and the compact accepted helper proof summary line.
2. Lane B tuple: touched file, validation method, validation result, and exact scaffold scope.
3. Coordinator tuple: shared publication files, combined validation result, authoritative-host parity result, and final packet verdict PASS or ABORTED.
4. Explicit confirmation that no helper mutation, controller widening, service admission widening, auth change, ingress change, runtime mutation, or business-logic mutation was opened.
```

## Packet 832 Application

Packet `2026-05-13-olares-dev-residency-832` is the first packet to publish this reusable operator prompt template on top of the Packet 831 delegated split-governance floor.

## Packet 856 Extension

Packet `2026-05-14-olares-dev-residency-856` extends this reusable operator prompt template so later delegated packets explicitly read the current delegated note stack, carry the compact accepted helper proof summary line in Lane A outputs, treat coordinator-owned publication files as a replaceable family instead of only `PROJECT_STATUS.md` plus one handoff, and route split, closeout, and packet-definition wording through the Packet 854, Packet 853, and Packet 855 template contracts instead of relying on coordinator memory outside the prompt.

## Packet 858 Extension

Packet `2026-05-14-olares-dev-residency-858` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855 and Packet 857 instead of preserving the older pre-Packet-857 prompt contract inside the operator prompt.

## Packet 860 Extension

Packet `2026-05-14-olares-dev-residency-860` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, and Packet 859 instead of leaving the reusable operator prompt pinned below the Packet 859 packet-template operator-prompt-routing floor.

## Packet 862 Extension

Packet `2026-05-14-olares-dev-residency-862` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, and Packet 861 instead of leaving the reusable operator prompt pinned below the Packet 861 packet-template operator-prompt floor.

## Packet 864 Extension

Packet `2026-05-14-olares-dev-residency-864` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, and Packet 863 instead of leaving the reusable operator prompt pinned below the Packet 863 packet-template operator-prompt floor refresh.

## Packet 866 Extension

Packet `2026-05-14-olares-dev-residency-866` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, and Packet 865 instead of leaving the reusable operator prompt pinned below the Packet 865 packet-template operator-prompt floor refresh.

## Packet 868 Extension

Packet `2026-05-14-olares-dev-residency-868` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, and Packet 867 instead of leaving the reusable operator prompt pinned below the Packet 867 packet-template operator-prompt floor refresh.

## Packet 870 Extension

Packet `2026-05-14-olares-dev-residency-870` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, and Packet 869 instead of leaving the reusable operator prompt pinned below the Packet 869 packet-template operator-prompt floor refresh.

## Packet 872 Extension

Packet `2026-05-14-olares-dev-residency-872` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, and Packet 871 instead of leaving the reusable operator prompt pinned below the Packet 871 packet-template operator-prompt floor refresh.

## Packet 874 Extension

Packet `2026-05-14-olares-dev-residency-874` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, and Packet 873 instead of leaving the reusable operator prompt pinned below the Packet 873 packet-template operator-prompt floor refresh.

## Packet 876 Extension

Packet `2026-05-14-olares-dev-residency-876` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, and Packet 875 instead of leaving the reusable operator prompt pinned below the Packet 875 packet-template operator-prompt floor refresh.

## Packet 878 Extension

Packet `2026-05-14-olares-dev-residency-878` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, and Packet 877 instead of leaving the reusable operator prompt pinned below the Packet 877 packet-template operator-prompt floor refresh.

## Packet 880 Extension

Packet `2026-05-14-olares-dev-residency-880` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, and Packet 879 instead of leaving the reusable operator prompt pinned below the Packet 879 packet-template operator-prompt floor refresh.

## Packet 882 Extension

Packet `2026-05-14-olares-dev-residency-882` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, and Packet 881 instead of leaving the reusable operator prompt pinned below the Packet 881 packet-template operator-prompt floor refresh.

## Packet 884 Extension

Packet `2026-05-14-olares-dev-residency-884` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, and Packet 883 instead of leaving the reusable operator prompt pinned below the Packet 883 packet-template operator-prompt floor refresh.

## Packet 886 Extension

Packet `2026-05-14-olares-dev-residency-886` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, and Packet 885 instead of leaving the reusable operator prompt pinned below the Packet 885 packet-template operator-prompt floor refresh.

## Packet 888 Extension

Packet `2026-05-15-olares-dev-residency-888` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, and Packet 887 instead of leaving the reusable operator prompt pinned below the Packet 887 packet-template operator-prompt floor refresh.

## Packet 890 Extension

Packet `2026-05-15-olares-dev-residency-890` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, and Packet 889 instead of leaving the reusable operator prompt pinned below the Packet 889 packet-template operator-prompt floor refresh.

## Packet 892 Extension

Packet `2026-05-15-olares-dev-residency-892` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, and Packet 891 instead of leaving the reusable operator prompt pinned below the Packet 891 packet-template operator-prompt floor refresh.

## Packet 894 Extension

Packet `2026-05-15-olares-dev-residency-894` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, and Packet 893 instead of leaving the reusable operator prompt pinned below the Packet 893 packet-template operator-prompt floor refresh.

## Packet 896 Extension

Packet `2026-05-15-olares-dev-residency-896` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, and Packet 895 instead of leaving the reusable operator prompt pinned below the Packet 895 packet-template operator-prompt floor refresh.

## Packet 898 Extension

Packet `2026-05-15-olares-dev-residency-898` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, and Packet 897 instead of leaving the reusable operator prompt pinned below the Packet 897 packet-template operator-prompt floor refresh.

## Packet 900 Extension

Packet `2026-05-15-olares-dev-residency-900` extends this reusable operator prompt template so later delegated packets explicitly route packet-definition wording through the Packet 834 template as extended by Packet 855, Packet 857, Packet 859, Packet 861, Packet 867, Packet 869, Packet 871, Packet 873, Packet 875, Packet 877, Packet 879, Packet 881, Packet 883, Packet 885, Packet 887, Packet 889, Packet 891, Packet 893, Packet 895, Packet 897, and Packet 899 instead of leaving the reusable operator prompt pinned below the Packet 899 packet-template operator-prompt floor refresh.