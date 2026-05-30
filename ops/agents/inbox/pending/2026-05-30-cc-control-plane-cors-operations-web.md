---
dispatch_id: 2026-05-30-cc-control-plane-cors-operations-web
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-30-control-plane-cors-operations-web-closeout.md
---

# Control-plane CORS — unblock the hosted operations-web shell (operations.apexpowerops.com)

**Lane:** TCC Runtime 017 follow-on / platform UI-topology. **Operator authorization: GRANTED 2026-05-30.** First concrete step of **ARCHITECTURE Decision 011** (single hosted product UI = `operations.apexpowerops.com`). Follow the inbox lifecycle (claim-push BEFORE executing).

## Problem (Desktop-diagnosed)
The hosted relay explorer at `https://operations.apexpowerops.com` shows **"The governed relay backend seam could not be reached from the browser shell."** Root cause is **CORS, not the backend**:
- The control-plane API (`apps/control-plane-api/main.py`) creates `app = FastAPI(...)` with **no CORS middleware** anywhere.
- Verified live: `OPTIONS https://control.apexpowerops.com/api/v1/neta/relay/sections` → **405** (no preflight handler); `GET …?q=SEL` → **200 but with no `Access-Control-Allow-*` headers**.
- operations-web (`operations.apexpowerops.com`, Vercel) fetches the control-plane **cross-origin** (its bundle correctly bakes in `https://control.apexpowerops.com`; `lib/relay-resources.ts` → `browserEnv.controlPlaneBaseUrl`; **no** Next same-origin rewrite covers `/api/v1/neta/*`). The browser gets the 200 but blocks the JS from reading it → the catch block at `relay-resource-explorer.tsx:424/484` fires.
- `curl` succeeds (ignores CORS); the browser fails (enforces it). The data is fine — the API just never says the operations-web origin is allowed.

This affects **every** operations-web explorer that reads the control-plane (relay, apparatus, etc.), not only relay. The breaker's `neta_tcc.html` never hit this because it is **local-only** (`127.0.0.1:8765`), same-origin against a local API.

## Goal
Add **scoped** CORS middleware to the control-plane so the hosted operations-web origin (and local dev origins) can read the public catalog routes cross-origin. Render auto-deploys on push to `main`; the relay route flips from the error banner to live data with no frontend change.

## Scope (single file: `apps/control-plane-api/main.py`)
Add, right after `app = FastAPI(...)`:

```python
import os
from fastapi.middleware.cors import CORSMiddleware

_DEFAULT_CORS_ORIGINS = [
    "https://operations.apexpowerops.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8765",
    "http://127.0.0.1:8765",
]
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", ",".join(_DEFAULT_CORS_ORIGINS)).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

Notes:
- **Env-overridable** via `CORS_ALLOWED_ORIGINS` (comma-separated) so preview/new origins can be added through Render env without a code change; the hardcoded default covers prod + local today.
- Explicit origins (never `"*"` with `allow_credentials=True`). `allow_credentials=True` is safe here because origins are explicit, and keeps it robust if a governed route later sends `Authorization`.
- `GET`/`POST`/`OPTIONS` covers the catalog reads (GET) and the plot routes (POST `…/relay/plot-tcc`, `…/plot-tcc`, `…/tmt-plot`, `…/emt-plot`).
- Ensure CORS is the outermost middleware so preflight `OPTIONS` is answered with headers (FastAPI applies middleware in reverse add-order — confirm preflight returns 200/204 + headers after the change).

## Verify (post Render auto-deploy — wait for the deploy to finish)
1. **Preflight:** `curl -i -X OPTIONS -H "Origin: https://operations.apexpowerops.com" -H "Access-Control-Request-Method: GET" https://control.apexpowerops.com/api/v1/neta/relay/sections` → **200/204** with `access-control-allow-origin: https://operations.apexpowerops.com`.
2. **GET with Origin:** `curl -i -H "Origin: https://operations.apexpowerops.com" "https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL"` → **200** AND an `access-control-allow-origin` header present (was absent).
3. **Browser:** load `https://operations.apexpowerops.com`, run **Search Relay Sections** with `SEL` → live relay sections render, **no** "could not be reached" banner.
4. **Negative check:** a disallowed origin (`-H "Origin: https://evil.example"`) gets **no** allow-origin header.
5. **Regression:** `GET https://control.apexpowerops.com/api/v1/neta/catalog/status` still `200` (`live/63/17831`).

## Guardrails
- Touch **only** `main.py` (import + `add_middleware`). No route logic, no data, no schema, no other app. If a control-plane test asserts response headers / middleware, update it in the same commit; otherwise add nothing else.
- Scoped origins only. Do not use `"*"`.
- Render `autoDeploy` ships it on push to `main`; do not claim done until the **deployed** host passes checks 1–5.

## Closeout
Record the preflight + GET header output, the browser confirmation, and the regression. Then `git mv claimed/ → done/`, commit, push, return to Desktop. This unblocks the relay explorer and establishes the cross-origin pattern every future operations-web lane (incl. the breaker explorer) will reuse.
