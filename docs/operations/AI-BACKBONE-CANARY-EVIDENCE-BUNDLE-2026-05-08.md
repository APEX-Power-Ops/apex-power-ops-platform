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

1. `python tools/ai/verify_minimal_mcp_trio.py --packet-id <packet-id>` or the repo-local interpreter equivalent,
2. any narrower trust-boundary check added by the active packet,
3. `git diff --check` on touched files.

## Example Evidence Bundle Shape

The smallest truthful repo-visible capture for a packet-scoped canary run should show the same contract elements the verifier checks.

Example validation summary shape:

```json
{
	"packet_id": "<packet-id>",
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
		}
	},
	"result": "PASS"
}
```

Minimum capture rules for that bundle:

1. include the exact verifier command or equivalent execution surface,
2. include the filesystem tool-resolution and bounded read proof,
3. include the database tool-resolution and bounded read-only query proof,
4. include the refusal proof for missing `env=host` evidence,
5. include the run id and env class for the recorded `apex-jobs` run,
6. include the truthful final result and attach it to the packet or handoff record.

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
5. reference any attached packet-local evidence artifact when one exists.

Optional emitted verifier artifact:

1. `tools/ai/verify_minimal_mcp_trio.py --output <path>` may write a repo-visible JSON artifact,
2. the preferred repo-owned lane for that artifact is `tests/canary/mcp-contract/actual/`, which already holds MCP contract proof,
3. a concrete example path is `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json`,
4. do not overwrite `tests/canary/mcp-contract/actual/mcp-tool-lists.json`, because that remains the separate canary runner output,
5. when packet JSON is in scope, that artifact should be referenced from `output_artifacts`,
6. the emitted JSON does not replace the handoff validation summary; it supports it.

If the packet JSON lane is not being updated for the active slice, the handoff becomes the minimum required routing surface for the same evidence.

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