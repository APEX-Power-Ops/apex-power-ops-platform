# Mutation Seam Architecture

## Overview

The mutation seam is a **governed boundary** for the APEX Platform PM/work domain. Every UI mutation (field change, assignment, status update, etc.) passes through this service before reaching persistent storage.

This architecture enforces:
- Role-based access control (RBAC)
- State machine validation
- Idempotency (duplicate request safety)
- Offline/online governance
- Complete audit trails
- Eventual realtime sync

## The 13-Stage Pipeline

Every mutation follows this sequence:

### Stage 1: Envelope Validation
**Tool:** Pydantic  
**What:** Validate request structure and types.
```json
{
  "idempotency_key": "uuid",
  "mutation_class": "A|B|C",
  "action_type": "string",
  "entity_id": "string|null",
  "payload": {object},
  "reason": "string|null",
  "source": "online|offline_queue",
  "client_timestamp": "ISO8601"
}
```

**Rejects:** Missing fields, wrong types, invalid enum values.  
**Proceeds:** Valid JSON structure.

---

### Stage 2: Idempotency Check
**Tool:** `app/idempotency/store.py`  
**What:** Has this request been processed before?

**Cache key:** `idempotency_key`  
**Rejects:** Returns cached response with status=idempotent_hit.  
**Proceeds:** New mutation.

**Why:** Network failures, retries, offline sync can send duplicate mutations. Idempotency ensures we don't apply the same change twice.

---

### Stage 3: Source Validation
**Tool:** `app/services/mutation_pipeline.py` (lines 157-165)  
**What:** Enforce offline governance.

| Source | Class A | Class B | Class C |
|--------|---------|---------|---------|
| online | ✓ | ✓ | ✗ |
| offline_queue | ✗ | ✓ | ✗ |

**Rejects:** offline_queue + Class C (status=rejected, code=OFFLINE_CLASS_C_REJECTED).  
**Proceeds:** Valid source-class combo.

**Why:** Class C = "offline only." If it's in the offline queue, that's contradictory.

---

### Stage 4: Class Validation
**Tool:** `app/services/mutation_pipeline.py` (lines 167-180)  
**What:** Does declared class match governed class?

- **A**: Online-only, high-trust actions (complete checklist, log hours)
- **B**: Bidirectional, moderate-trust (update status, assign)
- **C**: Offline-only, low-trust or batch actions (TBD)

**Rule:** Declared class must be >= governed class in trust (class_order: C < B < A).

**Rejects:** Declared < governed.  
**Proceeds:** Valid class declaration.

**Why:** Declares intent to the backend. If you declare "A" but the action is "B", you're overclaiming trust.

---

### Stage 5: Role Check
**Tool:** `app/auth/role_guard.py`  
**What:** Does the actor's role allow this action?

Example:
```python
ACTION_REGISTRY["update_apparatus_status"] = {
    "allowed_roles": ["field_tech", "task_lead", "project_lead"]
}
```

**Rejects:** Role not in allowed_roles (status=rejected, code=UNAUTHORIZED_ROLE).  
**Proceeds:** Role is authorized.

---

### Stage 6: Entity Load
**Tool:** `app/services/mutation_pipeline.py` (lines 192-207)  
**What:** Fetch current state from memory store.

For updates: Load the entity.  
For creates: Start with empty state.

**Rejects:** Entity not found for updates (code=ENTITY_NOT_FOUND).  
**Proceeds:** Entity loaded.

---

### Stage 7: Payload Validation
**Tool:** `app/services/mutation_pipeline.py` (lines 209-211)  
**What:** Basic type checks on payload fields.

Currently minimal (ensures dict). Later: JSON schema per action.

**Rejects:** If payload is invalid.  
**Proceeds:** Payload is valid.

---

### Stage 8: Transition Validation
**Tool:** `app/lifecycle/transitions.py`  
**What:** For lifecycle actions, is the state transition legal?

Example (apparatus):
```python
APPARATUS_TRANSITIONS = {
    "not_started": ["ready", "active"],
    "active": ["on_hold", "complete"],
    "complete": [],  # Terminal
}
```

**Rejects:** Invalid transition (code=TRANSITION_INVALID).  
**Proceeds:** Valid transition (or not a lifecycle action).

---

### Stage 9: Apply Mutation
**Tool:** `app/services/mutation_pipeline.py` (lines 244-265)  
**What:** Update the in-memory store.

For updates:
```python
to_state = entity_store[entity_id].copy()
to_state.update(request.payload)
to_state["updated_at"] = now
entity_store[entity_id] = to_state
```

For creates:
```python
to_state = {
    "id": new_id,
    **request.payload,
    "created_at": now,
    "updated_at": now,
}
entity_store[new_id] = to_state
```

**Rejects:** Never (previous stages filter all invalid mutations).  
**Proceeds:** State applied.

---

### Stage 10: Audit Event
**Tool:** `app/audit/logger.py`  
**What:** Record the mutation to the audit log.

Captures:
- Actor (id, role)
- Action (type, entity, mutation class)
- State change (from → to)
- Timing (client, server)
- Reason

Example audit entry:
```json
{
  "id": "audit-abc123",
  "mutation_id": "mut-def456",
  "actor_id": "tech-001",
  "actor_role": "field_tech",
  "action_type": "update_apparatus_status",
  "entity_id": "app-001",
  "from_state": {"status": "not_started"},
  "to_state": {"status": "active"},
  "reason": "Starting testing",
  "server_timestamp": "2026-04-16T14:30:05Z"
}
```

**Rejects:** Never.  
**Proceeds:** Audit event recorded, event ID returned.

---

### Stage 11: Save Idempotency
**Tool:** `app/idempotency/store.py`  
**What:** Cache the response for future duplicate requests.

```python
save_idempotency(request.idempotency_key, response)
```

Prototype: Cached forever. Production: TTL (24h?).

**Rejects:** Never.  
**Proceeds:** Response cached.

---

### Stage 12: Realtime Notification (Deferred)
**Tool:** TBD (WebSocket / Server-Sent Events)  
**What:** Notify subscribed clients of the change.

Currently: TODO (stubbed in mutation_pipeline.py line 279).

**Rejects:** Never (async, doesn't block response).  
**Proceeds:** Event queued for realtime subscribers.

---

### Stage 13: Return Response
**Tool:** FastAPI / Pydantic  
**What:** Return the MutationResponse to the client.

```json
{
  "status": "accepted",
  "mutation_id": "mut-550e8400",
  "entity_id": "app-001",
  "entity_type": "apparatus",
  "action_type": "update_apparatus_status",
  "new_state": { ... },
  "audit_event_id": "audit-123456"
}
```

---

## Response Statuses

| Status | Meaning | Idempotency | Stage |
|--------|---------|-------------|-------|
| `accepted` | Mutation applied | New | 13 |
| `rejected` | Mutation failed validation | New or cached | 2-11 |
| `conflict` | Concurrent mutation detected | New | Future |
| `idempotent_hit` | Duplicate request | Cached | 2 |

---

## In-Memory Store (Prototype)

**Purpose:** Fast iteration without Supabase setup.

**Stores:**
- `apparatus: {id → entity}`
- `checklist_items: {id → entity}`
- `hours: {id → entity}`
- `issues: {id → entity}`
- `assignments: {id → entity}`
- `tasks: {id → entity}`
- `workpackages: {id → entity}`
- `snapshots: {id → entity}`
- `idempotency_keys: {key → response_dict}`
- `audit_log: [event, ...]`

**Seeded with:**
- 1 project (proj-001)
- 2 workpackages (wp-001, wp-002)
- 4 tasks (2 per WP)
- 6 apparatus (mixed statuses, standards)
- 12 checklist items (2 per apparatus)
- 2 assignments (for tech-001)

**Reset:** Between test runs via pytest fixture.

---

## Governance Model

### Mutation Classes

**Class A (Online Only, High Trust)**
- Examples: `complete_checklist_item`, `log_hours`
- Who: Field technicians
- Cannot be batched/queued offline
- Most immediate

**Class B (Bidirectional, Moderate Trust)**
- Examples: `update_apparatus_status`, `assign_apparatus`
- Who: Task leads, technicians
- Can be queued offline, synced later
- Most common

**Class C (Offline Only, Low Trust)**
- Examples: TBD (batch operations, imports)
- Who: Administrators
- Must be processed offline
- Deferred

---

## Action Registry

Maps action_type → metadata:

```python
ACTION_REGISTRY = {
    "update_apparatus_status": {
        "governed_class": "B",
        "allowed_roles": ["field_tech", "task_lead", "project_lead"],
        "entity_type": "apparatus",
        "is_lifecycle": True,
    },
    ...
}
```

Add actions here to unlock them in the pipeline.

---

## State Machines

### Apparatus
```
not_started → [ready, active]
ready → [active, not_started]
active → [on_hold, complete]
on_hold → [active, ready]
complete → (terminal)
```

### Task
```
not_started → [ready, cancelled]
ready → [active, on_hold, cancelled]
active → [on_hold, awaiting_review]
on_hold → [ready, active]
awaiting_review → [active, complete]
complete → (terminal)
cancelled → (terminal)
```

### Issue
```
open → [in_review, escalated]
in_review → [escalated, resolved]
escalated → [resolved, in_review]
resolved → [closed, open]
closed → (terminal)
```

---

## Error Codes

| Code | Meaning | Stage |
|------|---------|-------|
| `IDEMPOTENCY_DUPLICATE` | Cached duplicate | 2 |
| `INVALID_ENVELOPE` | Bad structure | 1 |
| `INVALID_PAYLOAD` | Bad data | 7 |
| `ENTITY_NOT_FOUND` | No such entity | 6 |
| `UNAUTHORIZED_ROLE` | Wrong role | 5 |
| `UNAUTHORIZED_SCOPE` | Wrong project | 5 |
| `OFFLINE_CLASS_C_REJECTED` | Bad source-class | 3 |
| `INVALID_MUTATION_CLASS` | Bad class decl | 4 |
| `TRANSITION_INVALID` | Bad state change | 8 |
| `TRANSITION_CONFLICT` | State changed | 8 |
| `PRECONDITION_FAILED` | Dependency missing | Future |
| `ASSIGNMENT_CONFLICT` | Already assigned | Future |
| `WITHDRAWAL_BLOCKED` | Active tasks | Future |
| `CONCURRENT_MUTATION` | Race detected | Future |

---

## Integration Timeline

### Current (Prototype)
- In-memory stores
- FastAPI seam
- 13-stage pipeline
- RBAC + state machines
- Audit logging
- Idempotency

### Phase 2 (Month 2)
- Connect to Supabase
- Real persistence
- Migrations

### Phase 3 (Month 3)
- Realtime notifications (WebSocket)
- Multi-zone sync
- Offline queue + replay

### Phase 4 (Month 4+)
- Conflict resolution strategies
- Multi-tenant isolation
- Distributed tracing
- Performance optimization

---

## Testing Strategy

### Unit Tests
- Envelope validation (Pydantic)
- Role checks
- Transition validation
- Audit logging

### Integration Tests
- Full pipeline (request → response)
- State sequences
- Idempotency hits
- Multiple mutations

### Contract Tests (TBD)
- UI ↔ Seam API
- Seam → Supabase (when connected)

---

## Notes for Developers

1. **Always add to ACTION_REGISTRY** before expecting an action to work.
2. **Idempotency is automatic**—client provides key, backend caches response.
3. **State machines are strict**—invalid transitions are rejected before apply.
4. **Audit log is immutable**—every mutation is recorded (production: read-only DB table).
5. **In-memory store resets between tests**—each test runs against fresh data.
6. **Future realtime** should emit JSON events, not rebuild state. Keep it lightweight.

---

_For questions or updates, see APEX Platform docs or contact jason@resa-power.com._
