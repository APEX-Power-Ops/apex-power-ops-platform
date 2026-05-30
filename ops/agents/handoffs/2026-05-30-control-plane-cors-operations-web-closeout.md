# Control-Plane CORS Operations-Web Closeout

Dispatch: `2026-05-30-cc-control-plane-cors-operations-web`
Executor: Codex
Date: 2026-05-30
Status: Complete

## Claim And Change

- Claim commit pushed: `7e53bdde` (`claim: 2026-05-30-cc-control-plane-cors-operations-web by codex`)
- Implementation commit pushed: `3d50d074` (`fix(control-plane): allow operations web CORS`)
- Touched only `apps/control-plane-api/main.py`

The control-plane FastAPI app now installs scoped CORS middleware immediately after `app = FastAPI(...)`.

Default allowed origins:

- `https://operations.apexpowerops.com`
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8765`
- `http://127.0.0.1:8765`

The list is overridable by comma-separated `CORS_ALLOWED_ORIGINS`. Wildcard origins were not used.

## Local Validation

Run with the read-only live DSN sourced only for app import:

- `PYTHONPATH=. .venv/bin/python -m pytest tests/test_health.py tests/test_catalog_status.py -q`
- Result: `8 passed, 1 warning`

Local CORS probe through `TestClient`:

| Check | Result |
| --- | --- |
| operations-web preflight to `/api/v1/neta/relay/sections` | `200` |
| preflight allow-origin | `https://operations.apexpowerops.com` |
| preflight allow-methods | `GET, POST, OPTIONS` |
| allowed-origin `GET /health` | `200`, allow-origin present |
| disallowed-origin `GET /health` | `200`, allow-origin absent |

## Deployed Validation

Render auto-deploy picked up commit `3d50d074`; polling flipped from `OPTIONS 405` to `OPTIONS 200`.

Preflight:

- command shape: `curl -i -X OPTIONS -H "Origin: https://operations.apexpowerops.com" -H "Access-Control-Request-Method: GET" https://control.apexpowerops.com/api/v1/neta/relay/sections`
- result: `HTTP/2 200`
- `access-control-allow-origin: https://operations.apexpowerops.com`
- `access-control-allow-methods: GET, POST, OPTIONS`
- `access-control-allow-credentials: true`

GET with Origin:

- command shape: `curl -i -H "Origin: https://operations.apexpowerops.com" "https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL"`
- result: `HTTP/2 200`
- `access-control-allow-origin: https://operations.apexpowerops.com`
- response body contained relay section data (`count: 50`)

POST preflight:

- command shape: `curl -i -X OPTIONS -H "Origin: https://operations.apexpowerops.com" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" https://control.apexpowerops.com/api/v1/neta/relay/plot-tcc`
- result: `HTTP/2 200`
- `access-control-allow-origin: https://operations.apexpowerops.com`
- `access-control-allow-headers: content-type`
- `access-control-allow-methods: GET, POST, OPTIONS`

Negative origin:

- command shape: `curl -i -H "Origin: https://evil.example" "https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL"`
- result: `HTTP/2 200`
- no `access-control-allow-origin` header returned

Catalog regression:

- `GET https://control.apexpowerops.com/api/v1/neta/catalog/status`
- result: `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}`

## Browser Confirmation

Playwright loaded `https://operations.apexpowerops.com`, filled relay search with `SEL`, and clicked `Search Relay Sections`.

Browser result:

- control-plane relay sections request status: `200`
- relay error banner count: `0`
- rendered search match count text: `12`
- rendered relay search cards: `12`

Observed residual console noise:

- Three unrelated operations dashboard requests under `/api/v1/ops/*` returned `500` and surfaced as CORS-looking browser errors because unhandled server errors do not carry the CORS header.
- This did not affect the relay CORS confirmation: the relay search rendered data with no relay backend banner.
- The residual `/api/v1/ops/*` 500s were not changed under this packet's single-file CORS scope.

## Boundary

No route logic, data, schema, frontend code, or dependency files were changed. Existing unrelated local residue (`pnpm-lock.yaml`, `output/`, and canary actual JSON files) was left untouched.
