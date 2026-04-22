# Mutation Seam — APEX Platform

Governed mutation boundary for the APEX Platform PM/work domain. All UI mutations route through this FastAPI service before reaching the database.

## Architecture Overview

**13-Stage Mutation Pipeline:**
1. Envelope validation (Pydantic)
2. Idempotency check
3. Source validation (offline vs online)
4. Mutation class validation (A/B/C)
5. Role-based access control
6. Entity load from store
7. Payload validation
8. Lifecycle transition validation
9. Apply mutation to store
10. Record audit event
11. Save idempotency key
12. Emit realtime notification (deferred)
13. Return response

**Default Store (Current Prototype Runtime):**
- Postgres-backed `seam` schema store introduced by packet UI-001e
- Same dict-like interface as the original prototype store
- Memory fallback remains available for offline/disconnected development

**Governance:**
- Class A: Online only, no caching
- Class B: Bidirectional (online + offline queue)
- Class C: Offline only, cannot be processed from offline queue

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python -m uvicorn app.main:app --reload --port 8000
```

By default the service uses the Postgres-backed seam store. If local Postgres is not reachable yet, either:

1. set `SEAM_DATABASE_URL` with valid credentials for the `apex_pm_stage` database, or
2. set `SEAM_STORE_BACKEND=memory` to run in offline prototype mode

Health check: `curl http://localhost:8000/health`

### Test

```bash
pytest tests/ -v
```

## API Endpoints

All endpoints require `Authorization: Bearer <token>` header.

### Apparatus Mutations
```
POST /api/v1/mutations/apparatus
```

### Checklist Mutations
```
POST /api/v1/mutations/checklist
```

### Hours Tracking
```
POST /api/v1/mutations/hours
```

### Issues
```
POST /api/v1/mutations/issues
```

### Health
```
GET /health
```

## Example Request

```json
{
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "mutation_class": "B",
  "action_type": "update_apparatus_status",
  "entity_id": "app-001",
  "payload": {"status": "active"},
  "reason": "Started testing",
  "source": "online",
  "client_timestamp": "2026-04-16T14:30:00Z"
}
```

## Example Response (Accepted)

```json
{
  "status": "accepted",
  "mutation_id": "mut-550e8400-e29b-41d4",
  "entity_id": "app-001",
  "entity_type": "apparatus",
  "action_type": "update_apparatus_status",
  "new_state": {
    "id": "app-001",
    "status": "active",
    "updated_at": "2026-04-16T14:30:05Z"
  },
  "audit_event_id": "audit-123456"
}
```

## Auth (Prototype)

Simple base64-encoded JSON tokens. Example payload:

```json
{
  "actor_id": "tech-001",
  "actor_role": "field_tech",
  "project_scope": ["proj-001"]
}
```

Encode and send as `Authorization: Bearer <base64-encoded-json>`

Default (no header): actor_id=tech-001, role=field_tech, scope=[proj-001]

## State Machines

### Apparatus States
```
not_started → ready / active
ready → active / not_started
active → on_hold / complete
on_hold → active / ready
complete → (terminal)
```

### Task States
```
not_started → ready / cancelled
ready → active / on_hold / cancelled
active → on_hold / awaiting_review
on_hold → ready / active
awaiting_review → active / complete
complete → (terminal)
cancelled → (terminal)
```

### Issue States
```
open → in_review / escalated
in_review → escalated / resolved
escalated → resolved / in_review
resolved → closed / open
closed → (terminal)
```

## Integration Roadmap

1. **Current:** Postgres-backed seam store with memory fallback for offline validation
2. **Next:** Land additional persisted planning context and read models on the governed seam
3. **Then:** Add realtime notification (WebSocket/Server-Sent Events)
4. **Later:** Multi-zone replication, offline sync, conflict resolution

## Directory Structure

```
mutation-seam/
├── app/
│   ├── config.py           # Settings, env vars
│   ├── main.py             # FastAPI app
│   ├── envelope/           # Request/response models
│   ├── auth/               # JWT, role guards
│   ├── db/                 # Postgres-backed seam store + memory fallback
│   ├── services/           # Mutation pipeline
│   ├── routers/            # API endpoints
│   ├── audit/              # Audit logging
│   ├── idempotency/        # Idempotency tracking
│   └── lifecycle/          # State machines
├── tests/
│   ├── conftest.py
│   └── test_envelope_validation.py
├── requirements.txt
├── .env.example
└── README.md
```

## Development Notes

- All mutations are async (futures-ready)
- Errors use standard ErrorCode enums
- Transitions validated before apply
- Audit log records both state change and actor
- Idempotency keys cached indefinitely (real system: TTL)

---

Built for the APEX Platform. See parent docs for integration context.
