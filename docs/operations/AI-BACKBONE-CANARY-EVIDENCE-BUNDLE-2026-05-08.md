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
6. explicit positive-gate promotion proof when the packet claims promotion-eligible host evidence
7. packet-attributed outcome notes in repo-visible packet or handoff artifacts

## MCP Boundary Rules

For the current admitted backbone, the MCP boundary rules are:

1. only `apex-fs`, `apex-db`, and `apex-jobs` are inside the current AI backbone boundary,
2. filesystem access remains bounded to the approved roots exposed by `apex-fs`,
3. database access remains bounded to the read-only or admitted query surface exposed by `apex-db`,
4. run-ledger and promotion control remain bounded to `apex-jobs`,
5. broader MCP families must not be implied by a passing backbone canary.

### Filesystem Boundary Contract

`apex-fs` currently exposes exactly two admitted mounts:

1. `workspace`, sourced from `APEX_MCP_WORKSPACE_ROOT`,
2. `data`, sourced from `APEX_MCP_DATA_ROOT`.

Current filesystem posture:

1. only `list_roots`, `list_directory`, and `read_text_file` are admitted,
2. no write, rename, or delete tool is inside the current backbone,
3. resolved paths must stay inside the selected root.

Example allowed filesystem proof:

```json
{
	"name": "read_text_file",
	"arguments": {
		"root": "workspace",
		"relativePath": "README.md",
		"maxBytes": 120
	}
}
```

Example refusal detail for a path escape attempt:

```text
Path escapes workspace root: ../../../secrets.txt
```

### Database Boundary Contract

`apex-db` currently exposes exactly three admitted tools:

1. `list_tables`,
2. `describe_table`,
3. `query`.

Current database posture:

1. `list_tables` and `describe_table` are metadata reads,
2. `query` accepts only read-only `SELECT` or `WITH` SQL,
3. mutating SQL is explicitly rejected,
4. passing canary proof does not imply write or migration authority.

Example allowed database proof:

```json
{
	"name": "query",
	"arguments": {
		"sql": "select 1 as ok"
	}
}
```

Expected refusal details for out-of-bounds SQL:

```text
Only SELECT and WITH queries are allowed.
Mutating SQL is not allowed by apex-db.
```

## Evidence Classes

Interpret evidence in this order:

1. executable verification results,
2. packet JSON validation summaries,
3. packet handoff notes,
4. surrounding descriptive docs.

If these conflict, executable verification and packet evidence win over descriptive prose.

## Minimum Commands

The current minimum executable proof for this lane is:

1. `python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id>` or the repo-local interpreter equivalent, with `--profile strict-db-query` when the packet intentionally raises the bounded database-proof floor,
2. any narrower trust-boundary check added by the active packet,
3. `git diff --check` on touched files.

## Example Evidence Bundle Shape

The smallest truthful repo-visible capture for a packet-scoped canary run should show the same contract elements the verifier checks.

Example validation summary shape:

```json
{
	"packet_id": "<packet-id>",
	"profile": "baseline",
	"command": "python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id>",
	"checks": {
		"fs_tools": {
			"status": "pass",
			"tools": ["list_roots", "list_directory", "read_text_file"]
		},
		"fs_read": {
			"status": "pass",
			"preview": "# Apex Power Ops"
		},
		"db_tools": {
			"status": "pass",
			"tools": ["list_tables", "describe_table", "query"]
		},
		"db_query": {
			"status": "pass",
			"result": {
				"rowCount": 1,
				"rows": [{"ok": 1}]
			}
		},
		"jobs_tools": {
			"status": "pass",
			"tools": ["start_run", "end_run", "list_runs", "promote_packet"]
		},
		"jobs_promote_guard": {
			"status": "pass",
			"packet_id": "<packet-id>-promote-guard-ab12cd34",
			"detail": "Packet <packet-id>-promote-guard-ab12cd34 cannot be promoted: no successful env=host run is on record."
		},
		"jobs_start_run": {
			"status": "pass",
			"run": {
				"run_id": "run_sandbox_123",
				"env": "sandbox",
				"service": "ai-workflow",
				"packet_id": "<packet-id>",
				"status": "running",
				"created_at": "2026-05-10T19:00:00Z"
			}
		},
		"jobs_end_run": {
			"status": "pass",
			"run": {
				"run_id": "run_sandbox_123",
				"env": "sandbox",
				"service": "ai-workflow",
				"packet_id": "<packet-id>",
				"status": "success",
				"created_at": "2026-05-10T19:00:00Z",
				"notes": "minimal-mcp-trio verification",
				"completed_at": "2026-05-10T19:00:10Z"
			}
		},
		"jobs_list_runs": {
			"status": "pass",
			"result": {
				"runs": [
					{
						"run_id": "run_sandbox_123",
						"env": "sandbox",
						"service": "ai-workflow",
						"packet_id": "<packet-id>",
						"status": "success",
						"created_at": "2026-05-10T19:00:00Z",
						"notes": "minimal-mcp-trio verification",
						"completed_at": "2026-05-10T19:00:10Z"
					}
				]
			}
		}
	},
	"result": "PASS"
}
```

Minimum capture rules for that bundle:

1. include the exact verifier command or equivalent execution surface,
2. include the emitted verifier `profile` so later closeout prose does not have to infer which strictness floor ran,
3. include the filesystem tool-resolution and bounded read proof,
4. include the database tool-resolution and bounded read-only query proof,
5. include the refusal proof for missing `env=host` evidence,
6. include the run id and env class for the recorded `apex-jobs` run,
7. include one `list_runs` visibility proof showing the closed run is queryable from the ledger,
8. when the packet claims promotion-eligible host evidence, include the host success run id plus the `promote_packet` result artifact,
9. include the truthful final result and attach it to the packet or handoff record.
10. when `tools/ai/run_authoritative_host_packet.py` is the execution surface, accept the helper summary only if the imported bootstrap, verifier, promotion, and coordinator-summary artifacts all match the same packet id, remain `PASS` locally, preserve the imported bootstrap `tool` value truthfully for the expected repo-owned bootstrap surface, preserve the imported bootstrap `command` value parseably and truthfully for the expected packet-scoped bootstrap invocation plus output path, preserve the imported bootstrap `output_artifact` value truthfully for the expected bootstrap artifact path, preserve the imported bootstrap `implementation_root` value truthfully for the expected host repo root, preserve the same accepted host run id through `host_success_runs` and `supporting_run_ids`, preserve the same host-success run-id set between the imported promotion artifact and the coordinator summary, keep every promoted supporting run id backed by the recorded successful host runs, keep the accepted host-success support on `env=host` and the same service as the accepted host run, keep the top-level promotion `env` plus `service` tuple aligned with that same accepted host env/service across both the imported promotion artifact and the coordinator summary, keep the imported verifier `command` value parseable and truthful for the expected packet-scoped verifier invocation plus output and profile arguments, keep copied promotion and coordinator-summary `artifact_path` values truthful for the copied files, keep copied promotion and coordinator-summary `tool` values truthful for the expected repo-owned helper surfaces, and keep copied promotion and coordinator-summary `command` values parseable and truthful for the expected packet-scoped repo helper invocation plus artifact arguments.

## Evidence Routing Contract

When the packet JSON lane is in use, route AI backbone canary evidence through the existing packet fields rather than only describing it in prose.

Packet JSON minimum routing:

1. place the verifier command in `validation_commands`,
2. place the packet-level outcome in `validation_results` or `validation_disposition`,
3. place any emitted verifier artifact in `output_artifacts`,
4. place the matching handoff path in `handoff_note` when a handoff is authored for the packet.

Handoff minimum routing:

1. restate `packet_id` and final outcome in the execution or validation section,
2. include the exact verifier command or equivalent execution surface,
3. include the refusal proof for missing `env=host` evidence,
4. include the run id and env class whenever `apex-jobs` participated,
5. include the `list_runs` proof or equivalent ledger-visibility evidence when the verifier emitted it,
6. include the successful host run id and promotion result when the packet claims promotion-eligible host evidence,
7. reference any attached packet-local evidence artifact when one exists.

Optional emitted verifier artifact:

1. `tools/ai/verify_minimal_mcp_trio.py --output <path>` may write a repo-visible JSON artifact,
2. the preferred repo-owned lane for that artifact is `tests/canary/mcp-contract/actual/`, which already holds MCP contract proof,
3. a concrete example path is `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json`,
4. do not overwrite `tests/canary/mcp-contract/actual/mcp-tool-lists.json`, because that remains the separate canary runner output,
5. when packet JSON is in scope, that artifact should be referenced from `output_artifacts`,
6. the emitted JSON does not replace the handoff validation summary; it supports it.

Optional emitted promotion artifact:

1. `tools/ai/capture_apex_jobs_promotion.py --output <path>` may write a repo-visible JSON artifact for the positive promotion-gate path,
2. the preferred repo-owned lane for that artifact is also `tests/canary/mcp-contract/actual/`,
3. a concrete example path is `tests/canary/mcp-contract/actual/apex-jobs-promotion-<packet-id>.json`,
4. that helper artifact should be used only when the packet is claiming a successful matching `env=host` run and promotion result,
5. the emitted JSON should preserve top-level provenance fields for the helper surface, including the tool identity, packet id, env class, service, command, final result, and the primary host run plus promotion records,
6. when `--output` is used, the emitted JSON should also preserve the repo-visible artifact path so later closeout surfaces can reference the exact file without inference,
7. when packet JSON is in scope, that artifact should be referenced from `output_artifacts`,
8. the emitted JSON does not replace the handoff validation summary; it supports it.

Optional emitted coordinator summary artifact:

1. `tools/ai/build_ai_packet_evidence_summary.py --verify-artifact <path> [--promotion-artifact <path>] --output <path>` may write a repo-visible packet summary artifact for later coordinator-owned closeouts,
2. the preferred repo-owned lane for that artifact is also `tests/canary/mcp-contract/actual/`,
3. a concrete example path is `tests/canary/mcp-contract/actual/ai-packet-evidence-summary-<packet-id>.json`,
4. the helper must reject mismatched packet ids or non-`PASS` source artifacts instead of silently composing an incoherent summary,
5. when a promotion artifact is supplied, the emitted JSON should preserve the verifier tuple and the promotion tuple together under one packet-scoped summary,
6. when packet JSON is in scope, that artifact should be referenced from `output_artifacts`,
7. the emitted JSON does not replace the handoff validation summary; it supports it.

Optional emitted authoritative-host helper summary artifact:

1. `tools/ai/run_authoritative_host_packet.py --output <path>` may write a repo-visible packet helper artifact when the current-head authoritative-host chain is being driven through the helper surface,
2. the preferred repo-owned lane for that artifact is also `tests/canary/mcp-contract/actual/`,
3. a concrete example path is `tests/canary/mcp-contract/actual/run-authoritative-host-packet-<packet-id>.json`,
4. the helper must reject imported bootstrap, verifier, promotion, or coordinator-summary artifacts when they diverge from the requested packet id, lose `PASS` state, drift away from the accepted host run id carried through `host_success_runs` and `supporting_run_ids`, preserve a different host-success run-id set between the promotion artifact and the coordinator summary, claim promoted supporting run ids that are not backed by the recorded successful host runs, preserve supporting runs outside `env=host` or outside the accepted host service, preserve a top-level promotion `env` plus `service` tuple that no longer matches the accepted host run, preserve a coordinator-summary promotion record `promoted_at` timestamp that no longer matches the imported promotion artifact, or preserve a promotion/coordinator top-level `artifact_path` that no longer identifies the copied file truthfully instead of reporting helper-level success,
5. a truthful helper `PASS` should preserve enough top-level parity fields to show the local acceptance decision directly, including the host git head, host status count, preflight status, verifier result and profile, host promotion run id, host run env, host service, promotion `promoted_at`, host-success run ids, promotion supporting-run ids, coordinator promotion `promoted_at`, coordinator host-success run ids, and coordinator-summary result; the imported promotion artifact and coordinator summary should also continue to expose the matching top-level promotion `env`, `service`, promotion-record `promoted_at`, and self `artifact_path` values that the helper accepted,
6. when packet JSON is in scope, that artifact should be referenced from `output_artifacts`,
7. the emitted JSON does not replace the handoff validation summary; it supports it.

If the packet JSON lane is not being updated for the active slice, the handoff becomes the minimum required routing surface for the same evidence.

## Packet 172 Outcome

Packet 172 proves the current hardening lane with:

1. the existing minimal MCP trio verification,
2. a new executable promotion-refusal assertion in `verify_minimal_mcp_trio.py`,
3. explicit trust, provenance, and evidence contracts published in repo-owned docs.

Packet 787 proves the next evidence-attachment alignment lane with:

1. an updated canary evidence bundle example that reflects the current verifier output,
2. explicit routing guidance that `jobs_list_runs` ledger-visibility proof belongs in the packet or handoff evidence path when emitted,
3. no widening of the admitted MCP trio, queue ownership, or runtime scope.

Packet 788 proves the next named validation-profile lane with:

1. a repo-owned profile contract for `baseline` and `strict-db-query`,
2. a verifier payload that now emits the selected `profile`,
3. evidence-routing guidance that captures verifier strictness without widening the admitted boundary.

Packet 789 proves the next wrapper-routing and strict-artifact lane with:

1. named validation profiles are now routable through the PowerShell and Bash minimal-trio verify wrappers,
2. the first repo-visible `strict-db-query` verifier artifact is captured at `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-789.json`,
3. the admitted boundary, runtime scope, and queue ownership remain unchanged.

Packet 790 proves the next authoritative-host strict-profile lane with:

1. the governed host wrapper path can start the admitted trio from a truthful `not-running` baseline,
2. the authoritative host can emit a `strict-db-query` verifier artifact at `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-790.json`,
3. the host wrapper can return to a truthful `not-running` rest state after the packet completes.

Packet 791 proves the next promotion-eligible authoritative-host strict-profile lane with:

1. the authoritative host can pair a same-packet `strict-db-query` verifier artifact with a successful `env=host` run,
2. the reusable helper `tools/ai/capture_apex_jobs_promotion.py` can capture the positive gate artifact at `tests/canary/mcp-contract/actual/apex-jobs-promotion-2026-05-13-olares-dev-residency-791.json`,
3. the promotion gate remains bounded and truthful because the positive artifact exists only after matching host evidence is recorded.

Packet 796 proves the next positive-gate provenance-attachment lane with:

1. the helper artifact now exposes the top-level host run record, matching host-success runs, and promotion record directly instead of leaving later closeouts to pull those facts only from nested check payloads,
2. the helper artifact now preserves the helper tool identity and the repo-visible artifact path when `--output` is used,
3. the admitted boundary, host gate, and queue ownership remain unchanged.

Packet 797 proves the next coordinator-summary and second two-lane rehearsal lane with:

1. the new helper `tools/ai/build_ai_packet_evidence_summary.py` can compose one packet-scoped summary from the verifier artifact and the positive-gate promotion artifact,
2. the helper works against both the legacy nested promotion artifact shape and the richer Packet 796 top-level promotion provenance shape,
3. a repo-visible coordinator summary artifact is now captured at `tests/canary/mcp-contract/actual/ai-packet-evidence-summary-2026-05-13-olares-dev-residency-791.json` without widening the admitted boundary.

## Non-Goals

This evidence bundle does not prove:

1. broader AI-service readiness,
2. host promotion readiness by itself without the matching positive-gate artifact,
3. public ingress readiness,
4. business-logic completion.