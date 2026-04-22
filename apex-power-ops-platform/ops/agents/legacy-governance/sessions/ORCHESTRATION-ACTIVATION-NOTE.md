# APEX Orchestration Layer — Activation Note
## Date: March 19, 2026

The AI Orchestration layer (schema files 10 + 11) is now **FULLY OPERATIONAL**.

### What happened
- Originally deployed Dec 24, 2025 with 6 tables, 3 views, 3 triggers
- 4 of 12 functions were never pushed (fail_task, handoff_task, acknowledge_handoff, register_content)
- Shelved for 87 days after a Desktop Claude instance dismissed it without evaluation
- Rediscovered Mar 19, 2026 during discussion about Anthropic Dispatch
- Missing functions deployed via 2 Supabase migrations
- `claude-code` added to agent enum (replaces codex-max for current workflow)

### Current state
- **12/12 functions** deployed and verified
- **6 agents:** desktop-claude, claude-code, vs-code-claude, codex-max, human, local-ai
- **1 orphan task** from Dec 24 (Build Operations Dashboard MVP — can be cleaned up)
- **0 handoffs** (system is ready, no traffic yet)

### Protocol
See `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` for full session start protocol.

Every instance, every session:
1. `SELECT agent_heartbeat('agent-name', 'working', 'Starting session');`
2. `SELECT * FROM get_pending_handoffs('agent-name');`
3. `SELECT * FROM get_my_tasks('agent-name');`

### Integration with NETA ETT workspace
The orchestration layer serves both APEX Platform and NETA ETT Study Material workspaces.
Primary use case: extraction task handoffs between Desktop Claude and Claude Code.
Protocol doc and schema live here; task execution happens in the NETA workspace.
