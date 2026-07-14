# pm_ops_p0 — PM/Ops Phase-0 containment tooling

Operator-run tooling for the PM/Ops P0 emergency-containment lane. See the design
packet `docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-design.md` (§2 P0-A,
§6 P0-E).

## Modules

| Module | Purpose |
| --- | --- |
| `binding.py` | Shared **target-binding discipline**: `bind_target(dsn, expect_ref) -> params` (parse via `psycopg.conninfo.conninfo_to_dict`, reject reroute vectors, anchored host/user match, force `sslmode=verify-full`), `scrubbed_pg_env()`, `assert_bound_connection()`, and **`connect_bound(dsn, expect_ref)`** — the single-call context manager that bundles bind + scrub + connect + re-check. Both P0-A and the future P0-E readiness probes should use `connect_bound` so a caller cannot get only part of the protection. |
| `preserve_evidence.py` | P0-A read-only evidence capture. Requires `--expect-project-ref`; runs a single guarded `REPEATABLE READ, READ ONLY` transaction; writes custody artifacts + a SHA-256 manifest. |

**Evidence scope.** `preserve_evidence.py` captures the **database** evidence subset (design §2 items 3/4/5/6/9: ACL/RLS, effective-role closure, SECURITY DEFINER discovery, default privileges, counts, rollback inputs). The deployed-OpenAPI / `/reset`-route-state / backend-classification / Render-log items (§2 items 1/2/7/8) are captured separately by the operator / HTTP tooling — this script is not the whole evidence set.

## Runtime

- **Python ≥ 3.11**, **psycopg ≥ 3.1** (v3 — the module uses `psycopg.conninfo.conninfo_to_dict` and `Connection.info`, which do not exist in psycopg2). The repo-root `.venv` already provides psycopg 3.x; the deployed mutation-seam service (psycopg2) is **not** modified — this is a host-run operator tool, not part of the Render service.
- Run tooling and tests with the repo-root virtualenv, e.g.
  `/home/olares/code/apex/apex-power-ops-platform/.venv/bin/python`.

## Tests (offline — no live database)

```
<repo>/.venv/bin/python -m pytest apps/mutation-seam/scripts/pm_ops_p0/tests -q
```

Each test file is also directly runnable (`python tests/test_binding.py`) and
self-locates the package on `sys.path`. The suite exercises the reject/accept
matrix, value-silence, env-scrub, the post-connect re-check (via a stub
connection), argument parsing, the refusal path, custody permissions, the
SHA-256 manifest, and SQL parity — **none of it connects to a database.**

## Safety

- **No production access without an explicit per-action operator GO.** The
  `P0-A TOOLING ONLY` GO authorises building and offline-testing this tooling
  only. Running `preserve_evidence.py` against production is gated behind a
  separate `P0-A READ-ONLY EVIDENCE` GO.
- **Value-silence is end-to-end.** DSNs, passwords, hosts, and raw driver
  errors are never printed or logged; failures surface as stable codes only.
- Custody artifacts land under `/home/olares/custody/pm-ops-p0/<UTC>/`
  (dir `0700`, files `0400`) with a SHA-256 manifest.
