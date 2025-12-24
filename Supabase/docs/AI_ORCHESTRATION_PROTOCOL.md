# RESA AI Orchestration Protocol
## Agent Coordination and Task Management
### Version 1.0 | December 24, 2025

---

## 🎯 OVERVIEW

This document defines how AI agents coordinate work through the Supabase task queue. The system enables parallel development with clear handoffs, quality gates, and state tracking.

---

## 🤖 AGENT ROLES

| Agent | Primary Role | Capabilities | Best For |
|-------|--------------|--------------|----------|
| **desktop-claude** | Orchestrator | Complex reasoning, QC, strategy, decisions | Architecture, reviews, coordination |
| **codex-max** | Executor | Bulk creation, pattern replication, assembly | Batch work, templates, staging |
| **vs-code-claude** | Surgeon | Precision edits, analysis, debugging | Code fixes, file surgery, analysis |
| **local-ai** | Processor | Embeddings, preprocessing, summarization | Background batch jobs, RAG |
| **human** | Director | Approvals, direction, funding decisions | Strategy, priorities, sign-off |

---

## 📋 TASK LIFECYCLE

```
                    ┌─────────────┐
                    │   PENDING   │ ← Task created, ready for claiming
                    └──────┬──────┘
                           │
                    Agent claims
                           │
                    ┌──────▼──────┐
                    │   CLAIMED   │ ← Agent working on task
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
     │   BLOCKED   │ │  REVIEW   │ │   FAILED    │
     │             │ │           │ │             │
     │ Waiting on  │ │ Needs QC  │ │   Error     │
     │ dependency  │ │           │ │ occurred    │
     └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
            │              │              │
            │        QC Approved          │
            │              │         Retry?
            │        ┌─────▼─────┐        │
            └───────►│  COMPLETE │◄───────┘
                     └───────────┘
```

---

## 🔄 CORE WORKFLOWS

### Workflow 1: Simple Task Execution

```
1. Desktop Claude creates task → PENDING
2. Codex claims task → CLAIMED  
3. Codex completes work → COMPLETE
```

**Supabase calls:**
```sql
-- Desktop Claude creates
SELECT create_task('Build reference sheet', 'create', 'neta-4', 'reference-sheets');

-- Codex claims next available
SELECT * FROM claim_task('codex-max', 'neta-4');

-- Codex completes
SELECT complete_task(task_id, 'codex-max', '{"lines": 450, "file": "Sheet.html"}');
```

---

### Workflow 2: Task with QC

```
1. Codex completes creation → REVIEW
2. Desktop Claude audits → COMPLETE or → CLAIMED (revisions needed)
3. If revisions: Codex fixes → REVIEW again
```

**Task creation with QC gate:**
```sql
SELECT create_task(
    'Build Protection Coordination Reference',
    'create',
    'neta-4',
    'reference-sheets',
    'Create reference sheet following Symmetrical Components template',
    'normal',
    'codex-max',
    '{"template": "Symmetrical-Components-Reference.html"}',
    ARRAY['NETA-4/02-Reference-Sheets/Protection-Coordination-Reference.html'],
    '{"require_qc": true, "min_lines": 400, "max_lines": 600}'
);
```

---

### Workflow 3: Multi-Step Pipeline

```
1. Desktop Claude: Create spec → handoff → Codex
2. Codex: Stage content → handoff → Desktop Claude
3. Desktop Claude: QC audit → handoff → Codex (if revisions)
4. Codex: Run assembler → COMPLETE
5. Desktop Claude: Move to production
```

**Using dependencies:**
```sql
-- Step 1: Spec
SELECT create_task('Write import pipeline spec', 'document', 'resa', 'import') 
    RETURNING id; -- Returns task_id_1

-- Step 2: Build (depends on Step 1)
SELECT create_task('Build import pipeline', 'create', 'resa', 'import',
    p_depends_on := ARRAY[task_id_1]);
```

---

## 📨 HANDOFF PROTOCOL

### When to Handoff vs. Complete

| Situation | Action |
|-----------|--------|
| Work is done, no follow-up needed | `complete_task()` |
| Work is done, another agent continues | `handoff_task()` |
| Work failed, need different approach | `fail_task()` + create new task |
| Work blocked on external factor | Update status to 'blocked' |

### Handoff Message Format

```sql
SELECT handoff_task(
    'desktop-claude',           -- from
    'codex-max',                -- to
    task_id,
    'Reference sheet specs complete. Template at NETA-4/02-Reference-Sheets/Symmetrical-Components-Reference.html. Create 7 sheets per CODEX-REFERENCE-SHEET-TASK.md. Report line counts when done.',
    ARRAY['Development/NETA-4/Reference-Sheets/CODEX-REFERENCE-SHEET-TASK.md']
);
```

### Acknowledging Handoffs

```sql
-- Codex checks for incoming work
SELECT * FROM get_pending_handoffs('codex-max');

-- Codex acknowledges receipt
SELECT acknowledge_handoff(handoff_id, 'codex-max');
```

---

## 🚦 PRIORITY LEVELS

| Priority | Use When | SLA |
|----------|----------|-----|
| `critical` | Production down, blocking multiple streams | Immediate |
| `high` | Blocking current sprint, user waiting | Same session |
| `normal` | Standard work queue | Next available |
| `low` | Nice to have, not urgent | When bandwidth allows |
| `background` | Maintenance, cleanup, optimization | Whenever |

---

## ✅ QUALITY GATES

### Standard Gates by Task Type

| Task Type | Gates |
|-----------|-------|
| `create` | Line count range, template match, citations present |
| `enhance` | Before/after diff, no regression, additions validated |
| `review` | Checklist complete, issues documented |
| `assemble` | All inputs present, output validates, no errors |
| `deploy` | Tests pass, backup exists, rollback plan |

### Gate Definition Example

```json
{
    "require_qc": true,
    "min_lines": 400,
    "max_lines": 600,
    "must_have": ["citations", "print_styles", "tables"],
    "template_match": "Symmetrical-Components-Reference.html",
    "reviewer": "desktop-claude"
}
```

---

## 📊 STATUS DASHBOARD QUERIES

### Current Work in Progress

```sql
SELECT * FROM v_active_tasks;
```

### Agent Status

```sql
SELECT * FROM v_agent_dashboard;
```

### Pending Handoffs

```sql
SELECT * FROM v_pending_handoffs;
```

### Project Progress

```sql
SELECT 
    project,
    COUNT(*) FILTER (WHERE status = 'complete') AS done,
    COUNT(*) FILTER (WHERE status IN ('pending', 'claimed')) AS active,
    COUNT(*) AS total
FROM ai_tasks
GROUP BY project;
```

---

## 🔗 MCP INTEGRATION

### Desktop Claude Supabase Access

With Supabase MCP connector, Desktop Claude can:

```
// Check for pending tasks
Query: SELECT * FROM v_active_tasks WHERE assigned_to = 'desktop-claude'

// Create a task
Query: SELECT create_task('Build dashboard component', 'create', 'resa', 'dashboard')

// Complete a task
Query: SELECT complete_task('uuid-here', 'desktop-claude', '{"result": "success"}')
```

### Session Start Protocol

Every session, agent should:

1. **Heartbeat**: `SELECT agent_heartbeat('desktop-claude', 'working', 'Starting session')`
2. **Check handoffs**: `SELECT * FROM get_pending_handoffs('desktop-claude')`
3. **Review queue**: `SELECT * FROM get_my_tasks('desktop-claude')`

---

## 📁 CONTENT REGISTRY

### Registering New Content

```sql
SELECT register_content(
    'NETA-4/02-Reference-Sheets/Protection-Coordination-Reference.html',
    'Protection-Coordination-Reference.html',
    'reference-sheet',
    'neta-4',
    'L4',
    'complete',
    487,
    task_id
);
```

### Querying Content Status

```sql
SELECT * FROM content_registry 
WHERE project = 'neta-4' AND content_type = 'reference-sheet';
```

---

## 🚀 QUICK START: FIRST TASK

### 1. Deploy Schema
```powershell
# Run in Supabase SQL Editor
10_ai_orchestration.sql
11_ai_orchestration_functions.sql
```

### 2. Create First Task
```sql
SELECT create_task(
    'Build Operations Dashboard MVP',
    'create',
    'resa',
    'dashboard',
    'Create project list, scope detail, and apparatus grid views',
    'high',
    NULL,  -- Unassigned, goes to queue
    '{"pages": ["projects", "scopes", "apparatus"]}',
    ARRAY['src/app/dashboard/'],
    '{"require_qc": true}'
);
```

### 3. Claim and Execute
```sql
-- Agent claims
SELECT * FROM claim_task('codex-max', 'resa');

-- Agent completes
SELECT complete_task(task_id, 'codex-max', '{"pages_created": 3}');
```

---

## 📋 APPENDIX: Task Type Reference

| Type | Description | Typical Agent |
|------|-------------|---------------|
| `create` | Build new content from scratch | codex-max |
| `enhance` | Improve existing content | desktop-claude or codex |
| `review` | QC audit, validation | desktop-claude |
| `assemble` | Combine staged pieces | codex-max |
| `migrate` | Move between systems | codex-max |
| `document` | Create documentation | desktop-claude |
| `test` | Run validation/tests | vs-code-claude |
| `deploy` | Push to production | human approval → codex |

---

*Protocol Version 1.0 - December 24, 2025*
*Created by Desktop Claude for RESA Development Acceleration*
