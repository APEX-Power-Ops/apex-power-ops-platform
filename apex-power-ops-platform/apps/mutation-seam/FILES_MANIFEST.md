# Mutation Seam — Files Manifest

Complete file inventory for the mutation seam backend.

## Configuration Files

| File | Purpose | Size |
|------|---------|------|
| `requirements.txt` | Python dependencies | 128 B |
| `.env.example` | Environment variables template | 133 B |
| `pyproject.toml` | Modern Python package config | 1.8 KB |
| `.gitignore` | Git ignore patterns | 1.4 KB |
| `Makefile` | Development commands | 1.1 KB |

## Documentation

| File | Purpose | Size |
|------|---------|------|
| `README.md` | Main documentation & API reference | 4.6 KB |
| `ARCHITECTURE.md` | 13-stage pipeline deep dive | 11.1 KB |
| `QUICKSTART.md` | Get-started guide with examples | 8.3 KB |
| `FILES_MANIFEST.md` | This file | - |

## Application Code

### Core Application
| File | Purpose | Size |
|------|---------|------|
| `app/__init__.py` | Package marker | 0 B |
| `app/main.py` | FastAPI app + CORS + routers | 1.3 KB |
| `app/config.py` | Settings, env vars, constants | 954 B |

### Envelope (Request/Response Models)
| File | Purpose | Size |
|------|---------|------|
| `app/envelope/__init__.py` | Package marker | 0 B |
| `app/envelope/request.py` | MutationRequest Pydantic model | 1.9 KB |
| `app/envelope/response.py` | MutationResponse, ErrorDetail, ConflictDetail | 2.8 KB |
| `app/envelope/errors.py` | ErrorCode enum + error_response() helper | 3.1 KB |

### Database (In-Memory Store)
| File | Purpose | Size |
|------|---------|------|
| `app/db/__init__.py` | Package marker | 0 B |
| `app/db/memory_store.py` | MemoryStore class + singleton + seed_demo_data() | 5.6 KB |

### Authentication & Authorization
| File | Purpose | Size |
|------|---------|------|
| `app/auth/__init__.py` | Package marker | 0 B |
| `app/auth/jwt.py` | get_current_actor() dependency, Actor dataclass | 2.2 KB |
| `app/auth/role_guard.py` | check_role(), check_scope() guards | 843 B |

### Idempotency
| File | Purpose | Size |
|------|---------|------|
| `app/idempotency/__init__.py` | Package marker | 0 B |
| `app/idempotency/store.py` | check_idempotency(), save_idempotency() | 952 B |

### Audit Logging
| File | Purpose | Size |
|------|---------|------|
| `app/audit/__init__.py` | Package marker | 0 B |
| `app/audit/logger.py` | record_audit_event() function | 1.4 KB |

### Lifecycle & State Machines
| File | Purpose | Size |
|------|---------|------|
| `app/lifecycle/__init__.py` | Package marker | 0 B |
| `app/lifecycle/transitions.py` | State machine defs + validate_transition() | 1.8 KB |

### Services
| File | Purpose | Size |
|------|---------|------|
| `app/services/__init__.py` | Package marker | 0 B |
| `app/services/mutation_pipeline.py` | 13-stage pipeline + ACTION_REGISTRY | 9.8 KB |

### Routers (API Endpoints)
| File | Purpose | Size |
|------|---------|------|
| `app/routers/__init__.py` | Package marker | 0 B |
| `app/routers/apparatus.py` | POST /api/v1/mutations/apparatus | 888 B |
| `app/routers/checklist.py` | POST /api/v1/mutations/checklist | 840 B |
| `app/routers/hours.py` | POST /api/v1/mutations/hours | 781 B |
| `app/routers/issues.py` | POST /api/v1/mutations/issues | 793 B |
| `app/routers/health.py` | GET /health | 381 B |

### Realtime (Placeholder)
| File | Purpose | Size |
|------|---------|------|
| `app/realtime/__init__.py` | Package marker (future use) | 0 B |

## Tests

| File | Purpose | Size |
|------|---------|------|
| `tests/__init__.py` | Package marker | 0 B |
| `tests/conftest.py` | Pytest fixtures, store reset, token helpers | 1.5 KB |
| `tests/test_envelope_validation.py` | Envelope, idempotency, auth, health tests | 6.3 KB |
| `tests/test_pipeline_integration.py` | State machines, audit, transitions tests | 6.2 KB |

## Directory Structure

```
mutation-seam/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── config.py                 # Settings
│   ├── main.py                   # FastAPI app
│   ├── envelope/                 # Request/response models
│   │   ├── __init__.py
│   │   ├── request.py
│   │   ├── response.py
│   │   └── errors.py
│   ├── db/                       # Data layer
│   │   ├── __init__.py
│   │   └── memory_store.py
│   ├── auth/                     # Authentication & authorization
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   └── role_guard.py
│   ├── idempotency/              # Duplicate request prevention
│   │   ├── __init__.py
│   │   └── store.py
│   ├── audit/                    # Audit logging
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── lifecycle/                # State machines
│   │   ├── __init__.py
│   │   └── transitions.py
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   └── mutation_pipeline.py
│   ├── routers/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── apparatus.py
│   │   ├── checklist.py
│   │   ├── hours.py
│   │   ├── issues.py
│   │   └── health.py
│   └── realtime/                 # Future realtime features
│       └── __init__.py
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_envelope_validation.py
│   └── test_pipeline_integration.py
├── requirements.txt              # Python dependencies
├── .env.example                  # Env var template
├── .gitignore                    # Git ignore
├── pyproject.toml                # Package config
├── Makefile                      # Dev commands
├── README.md                     # Main docs
├── ARCHITECTURE.md               # Deep dive
├── QUICKSTART.md                 # Getting started
└── FILES_MANIFEST.md             # This file

```

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total files | 40 |
| Python modules | 27 |
| Test files | 2 |
| Documentation files | 4 |
| Config files | 5 |
| Total lines of code (est.) | ~2,500 |
| Total lines of docs (est.) | ~1,500 |

## File Purposes at a Glance

### Must-Read (In Order)
1. `README.md` — API reference & quick overview
2. `QUICKSTART.md` — Get running in 5 minutes
3. `ARCHITECTURE.md` — Understand the 13-stage pipeline
4. `app/services/mutation_pipeline.py` — Core logic

### Most Important Code Files
1. `app/main.py` — FastAPI app setup
2. `app/services/mutation_pipeline.py` — Mutation orchestration
3. `app/db/memory_store.py` — Data storage
4. `app/envelope/request.py` — Request validation
5. `app/lifecycle/transitions.py` — State machines

### Important Patterns
- **Envelopes:** request.py, response.py, errors.py
- **State Machines:** transitions.py (add new states here)
- **Actions:** ACTION_REGISTRY in mutation_pipeline.py (add actions here)
- **Auth:** jwt.py + role_guard.py (customize tokens here)

### Tests to Reference
- `tests/test_envelope_validation.py` — Basic request/response flow
- `tests/test_pipeline_integration.py` — Full state machine examples

---

## Next: Connecting to Supabase

When ready to use real persistence:

1. Replace `app/db/memory_store.py` with Supabase client
2. Update `mutation_pipeline.py`'s `_get_store_for_entity_type()`
3. Add migrations to Supabase schema
4. Add realtime subscriptions in `app/realtime/`
5. Update requirements.txt with `supabase-py`

See `ARCHITECTURE.md` Phase 2 for timeline.

---

_Last updated: 2026-04-16_  
_Total lines written: ~2,500 Python + ~1,500 documentation_
