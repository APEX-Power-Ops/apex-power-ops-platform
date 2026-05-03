# Mutation Seam — Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd apps/mutation-seam
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2. Run the Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

Before starting, choose one runtime mode:

1. Persisted mode: set `SEAM_DATABASE_URL` to a valid `apex_pm_stage` Postgres DSN
2. Offline mode: set `SEAM_STORE_BACKEND=memory`

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "seam": "mutation-seam"
}
```

---

## Your First Mutation

### Get a Token
Create a base64-encoded JSON token:

```python
import base64
import json

payload = {
    "actor_id": "tech-001",
    "actor_role": "field_tech",
    "project_scope": ["proj-001"]
}

token = base64.b64encode(json.dumps(payload).encode()).decode()
print(f"Bearer {token}")
```

### Send a Mutation Request
```bash
curl -X POST http://localhost:8000/api/v1/mutations/apparatus \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
    "mutation_class": "B",
    "action_type": "update_apparatus_status",
    "entity_id": "app-001",
    "payload": {"status": "active"},
    "reason": "Starting testing",
    "source": "online",
    "client_timestamp": "2026-04-16T14:30:00Z"
  }'
```

### Expected Response (Accepted)
```json
{
  "status": "accepted",
  "mutation_id": "mut-550e8400-e29b-41d4",
  "entity_id": "app-001",
  "entity_type": "apparatus",
  "action_type": "update_apparatus_status",
  "new_state": {
    "id": "app-001",
    "name": "Main Breaker 480V",
    "neta_standard": "ATS",
    "status": "active",
    "assigned_to": null,
    "created_at": "2026-04-16T14:30:00Z",
    "updated_at": "2026-04-16T14:30:05Z"
  },
  "audit_event_id": "audit-abc123"
}
```

---

## Test the Whole Pipeline

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_envelope_validation.py::test_valid_apparatus_status_update_succeeds -v
```

### Watch Test Coverage
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html
```

---

## Explore the Demo Data

The server starts with seeded data. In memory mode the data is local to the process. In persisted mode it is served from the `seam` schema in Postgres through the same store interface. Check what's in the store:

### Python Shell
```python
from app.db.memory_store import store

# List all apparatus
print(store.apparatus.keys())
# dict_keys(['app-001', 'app-002', 'app-003', ...])

# Get one entity
print(store.apparatus['app-001'])
# {'id': 'app-001', 'name': 'Main Breaker 480V', 'status': 'not_started', ...}

# Check audit log
print(store.audit_log)
# [event1, event2, ...]
```

---

## Try Invalid Mutations

### Invalid State Transition
```bash
curl -X POST http://localhost:8000/api/v1/mutations/apparatus \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440001",
    "mutation_class": "B",
    "action_type": "update_apparatus_status",
    "entity_id": "app-001",
    "payload": {"status": "on_hold"},
    "source": "online",
    "client_timestamp": "2026-04-16T14:30:00Z"
  }'
```

Response (status "not_started" → "on_hold" is invalid):
```json
{
  "status": "rejected",
  "mutation_id": "mut-...",
  "entity_id": "app-001",
  "entity_type": "apparatus",
  "action_type": "update_apparatus_status",
  "new_state": {},
  "error": {
    "code": "TRANSITION_INVALID",
    "message": "Cannot transition apparatus from not_started to on_hold",
    "detail": {
      "from_state": "not_started",
      "to_state": "on_hold"
    }
  }
}
```

### Unauthorized Role
```bash
# Create token with "viewer" role (not allowed)
TOKEN=$(python3 -c "
import base64, json
payload = {'actor_id': 'user-001', 'actor_role': 'viewer', 'project_scope': ['proj-001']}
print('Bearer ' + base64.b64encode(json.dumps(payload).encode()).decode())
")

curl -X POST http://localhost:8000/api/v1/mutations/apparatus \
  -H "Content-Type: application/json" \
  -H "Authorization: $TOKEN" \
  -d '{ ... }'
```

Response:
```json
{
  "status": "rejected",
  "error": {
    "code": "UNAUTHORIZED_ROLE",
    "message": "Role viewer not authorized; requires one of ['field_tech', 'task_lead', 'project_lead']"
  }
}
```

---

## Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/api/v1/mutations/apparatus` | POST | Apparatus mutations |
| `/api/v1/mutations/checklist` | POST | Checklist mutations |
| `/api/v1/mutations/hours` | POST | Hours tracking |
| `/api/v1/mutations/issues` | POST | Issues mutations |

---

## Available Actions

| Action | Class | Entity | Allowed Roles |
|--------|-------|--------|---------------|
| `update_apparatus_status` | B | apparatus | field_tech, task_lead, project_lead |
| `assign_apparatus` | B | apparatus | task_lead, project_lead |
| `unassign_apparatus` | B | apparatus | field_tech, task_lead, project_lead |
| `complete_checklist_item` | A | checklist_item | field_tech |
| `reopen_checklist_item` | B | checklist_item | task_lead, project_lead |
| `log_hours` | A | hours | field_tech |
| `create_issue` | A | issue | field_tech, task_lead |
| `update_issue_status` | B | issue | task_lead, project_lead |

---

## Next Steps

### 1. Try Checklist Completion
```json
{
  "idempotency_key": "...",
  "mutation_class": "A",
  "action_type": "complete_checklist_item",
  "entity_id": "item-001",
  "payload": {"completed": true},
  "source": "online",
  "client_timestamp": "2026-04-16T14:30:00Z"
}
```

### 2. Try Hours Logging
```json
{
  "idempotency_key": "...",
  "mutation_class": "A",
  "action_type": "log_hours",
  "entity_id": null,
  "payload": {"hours": 8.5, "apparatus_id": "app-001", "date": "2026-04-16"},
  "source": "online",
  "client_timestamp": "2026-04-16T14:30:00Z"
}
```

### 3. Add a New Action
1. Add to `ACTION_REGISTRY` in `app/services/mutation_pipeline.py`
2. Create/update router in `app/routers/`
3. Write tests in `tests/`
4. Document in this file

### 4. Connect to Supabase
When ready to use real persistence:
1. Replace `app.db.memory_store` with Supabase client
2. Update `_get_store_for_entity_type()` to fetch from Supabase
3. Add realtime subscriptions (Stage 12)

---

## Troubleshooting

### "Module not found: fastapi"
```bash
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### "Test fixtures failing"
```bash
# Ensure you're in the project root
cd apps/mutation-seam
pytest tests/
```

### "Token validation failing"
Ensure token is properly base64-encoded JSON:
```python
import base64, json
payload = {"actor_id": "tech-001", "actor_role": "field_tech", "project_scope": ["proj-001"]}
token = base64.b64encode(json.dumps(payload).encode()).decode()
# Pass as: Authorization: Bearer <token>
```

---

## IDE Setup

### VS Code
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "editor.defaultFormatter": "charliermarsh.ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit",
    "source.organizeImports.ruff": "explicit"
  }
}
```

### PyCharm
- Mark `app/` as Sources Root
- Set Python Interpreter to `.venv`
- Enable pytest in Settings

---

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app entry point |
| `app/services/mutation_pipeline.py` | 13-stage pipeline orchestrator |
| `app/envelope/request.py` | Mutation request model |
| `app/envelope/response.py` | Mutation response model |
| `app/db/memory_store.py` | In-memory data store |
| `app/auth/jwt.py` | Token extraction & auth |
| `app/lifecycle/transitions.py` | State machines |
| `tests/test_envelope_validation.py` | Basic pipeline tests |
| `tests/test_pipeline_integration.py` | Full flow tests |

---

## Questions?

- See `ARCHITECTURE.md` for deep dives
- See `README.md` for API reference
- Check tests for examples
- Contact: jason@resa-power.com

Happy testing!
