# P0-A Tooling — Cross-Engine Code Review Record

**Subject.** `apps/mutation-seam/scripts/pm_ops_p0/` (`binding.py`, `preserve_evidence.py`, tests, README) — the design-only P0-A tooling for the PM/Ops emergency-containment lane. Built under the operator's `P0-A TOOLING ONLY` GO (implement + offline-test only; NO production access).

**Base / commits.** Branch `pm-ops/p0a-tooling` off merged design `c22235d8`. Reviewed commit chain:
- `be997bd4` — tooling (initial)
- `93cbab63` — folds review round 1 findings
- `694abe62` — folds Codex delta finding (short-write integrity)

**Mode / depth.** Audit, Deep (security-critical: `bind_target` is the gate preventing a connection to the wrong project; value-silence protects credentials). Offline throughout — no live DB touched by the review or the tests.

## Engines (independence-by-construction + engine-diversity + adversarial + source-grounded)
1. **Codex `gpt-5.5`** (cross-engine, mandatory) — `codex exec review --commit` over three rounds (`be997bd4`, `93cbab63`, `694abe62`).
2. **Claude adversarial lens A** — security gate + value-silence (binding.py bypass hunting, env-override vectors, exception/log leak tracing, test rigor).
3. **Claude adversarial lens B** — SQL fidelity vs design §2 + read-only choreography + custody/refusal ordering + the P0-E factoring gap.

Each Claude lens read the committed files at the pinned SHA and the authoritative design §2/§6 via `git show`; both were prompted to refute, not confirm.

## Convergent verdict
All three engines independently concluded: **the P0-A gate is SOUND — no DSN that is not genuinely bound to project `fxoyniqnrlkxfligbxmg` can pass `bind_target` and yield a usable wrong-project connection** (reconstruct-and-reconnect drops injected keywords; forced `sslmode=verify-full` fails an IP reroute at the TLS cert; refusal precedes any socket; read-only choreography and value-silence correct). No Critical/High defect blocks the eventual `P0-A READ-ONLY EVIDENCE` GO. Findings were defense-in-depth + a forward-looking P0-E gap.

## Findings and dispositions
| ID | Sev | Finding | Disposition |
| --- | --- | --- | --- |
| A-HIGH-1 / B-M1 | High* | P0-E's §6 sample calls only `bind_target`+`connect` — drops env-scrub + post-connect re-check (mitigated by `verify-full`, but diverges from the stated "identical binding") | **Fixed `93cbab63`**: added `connect_bound()` single-call helper (bind+scrub+connect+recheck, lock-serialised); P0-A uses it. **Surfaced to operator**: P0-E must adopt `connect_bound`. *(High as a design contract gap, not a P0-A bypass.)* |
| A-MED-1 / B-L3 | Med | `assert_bound_connection` checked `host` only; pooler host is shared/multi-tenant (near-inert as a project bind) | **Fixed `93cbab63`**: pooler form now asserts tenant user `postgres.<ref>`; docstring states `verify-full` is the authoritative IP defense, host/user are name-level cross-checks (`hostaddr` not equality-checked — rotating IPs) |
| A-MED-2 | Med | post-connect reject test's `hostaddr` arg was vacuous; accept test accepted pooler w/o user | **Fixed `93cbab63`**: tests updated to the user-aware contract (+ pooler-wrong-user reject) |
| A-MED-3 | Med | `preserve_evidence` value-silence paths untested | **Fixed `93cbab63`**: `test_main_value_silent_when_collection_raises` (sentinel host never in stdout/logs) |
| B-M2 | Med | `collect_evidence` connect/execute choreography untested (offline-testable) | **Fixed `93cbab63`**: mock-connection tests — exact execute order, env scrubbed at connect, host re-check gates before any query |
| A-LOW-1 | Low | SSL trust-anchor env vars not scrubbed (`verify-full` trust store is load-bearing) | **Fixed `93cbab63`**: scrub `PGSSLROOTCERT`/`PGSSLCERT`/`PGSSLKEY` too |
| Codex-P2 / B-L5 | Med/Low | custody `mkdir`/`write` at default umask then `chmod` — transient exposure window; parents left world-traversable | **Fixed `93cbab63`**: atomic create (`umask 0o077` + `mkdir 0o700` + `O_EXCL 0o400`) |
| B-L4 | Low | `_Q_E` dropped §2's disclosed "residual coverage gap" note; snapshot prepended markers query | **Fixed `93cbab63`**: verbatim `_Q_E` note restored; `p0a_sql_text()` = byte-faithful §2 block (markers captured separately) |
| A-LOW-2 | Low | `scrubbed_pg_env` mutates global `os.environ` — thread-unsafe in a concurrent path | **Fixed `93cbab63`**: `connect_bound` serialises the scrub+connect window under a lock |
| Codex-delta-P2 | Med | `os.write()` short-write could truncate an evidence file while the manifest records the full hash and the run reports PASS | **Fixed `694abe62`**: write-until-complete loop + multi-MB round-trip regression test |
| A-LOW-3 | Low | pooler single-label rule may false-reject a hypothetical future multi-label pooler host | **Accepted** — fails **closed** (availability, not security); noted for maintenance |
| A-LOW-4 | Low | minor test under-constraint (empty-host code not pinned; not all scrubbed vars covered) | **Fixed `93cbab63`**: env-scrub test now drives the full `PG_ENV_OVERRIDES` list |
| A-INFO | Info | script captures the DB evidence subset (§2 items 3/4/5/6/9); OpenAPI/reset-route/backend/Render-log (items 1/2/7/8) are operator/HTTP captures | **Documented** in README ("Evidence scope") |

\* High severity reflects the design-contract divergence for the future P0-E consumer, not an exploitable bypass of the P0-A tooling under review.

## Operator to confirm live at the `P0-A READ-ONLY EVIDENCE` GO (not code changes)
- **P6** — `sslmode=verify-full` with no `sslrootcert`: confirm the direct `db.<ref>.supabase.co` cert chains to the host trust store, else use the pooler form or supply an operator `sslrootcert`. Fails **closed** either way (no evidence, no wrong connection).
- **P7** — Supavisor pooler transaction-mode: confirm the multi-statement `BEGIN … READ ONLY / SELECTs / COMMIT` + `transaction_read_only` guard behave as expected on port 6543.

## Final state
Codex round 3 (`694abe62`): **clean, no findings**. Offline suite **38/38**, `ruff check` + `ruff format` clean, files LF-verified. No production access, SQL, deploy, secret change, or connectivity repair was performed at any point.

**Verdict (round 1): tooling is code-review-complete.** See round 2 for the operator's evidence-integrity review and the hardening tranche.

---

## Round 2 — operator review (evidence integrity + governance) + hardening tranche

**Trigger.** The operator independently reviewed the tooling and **HELD** `P0-A READ-ONLY EVIDENCE` with 6 findings — target-binding confirmed sound (no wrong-project bypass); the hold was evidence integrity + governance. An authorized bounded hardening tranche + governed PR was directed.

**Commits.** `be997bd4`..`924674ea` (round 1) → `b7b59934` (hardening tranche) → `40c93ce5` (Codex delta fix).

| ID | Sev | Finding | Disposition |
| --- | --- | --- | --- |
| Op-1 | High | secdef query captured effective booleans, not `proacl`/grantor/grantee/grant-option — cannot generate the exact RPC-grant rollback P0-C requires | **Fixed `b7b59934`**: query (f) — raw `proacl` + `aclexplode`; artifact `08_secdef_function_acl.txt` |
| Op-2 | High | evidence not bound to governed tooling (any checkout; no repo SHA / hashes / provenance) | **Fixed `b7b59934`**: `--expect-repo-sha` required + clean-merged-main gate + `00_provenance.json` (repo/tool/query hashes, versions, timestamps, DSN env name) |
| Op-3 | Med | DB authority not enforced (direct-host DSN accepts any user; `current_user` only recorded) | **Fixed `b7b59934`**: `--expect-db-role` (default `postgres`) + parameterized `current_user` guard → `db_role_mismatch` before any evidence read |
| Op-4 | Med | only the DB subset of P0-A; no parent runbook binding all 9 categories | **Fixed `b7b59934`**: `P0A_RUNBOOK.md` + 9-category closeout index; "script alone ≠ P0-A done" |
| Op-5 | Med | dependency + CI governance missing (psycopg3 undeclared; no workflow) | **Fixed `b7b59934`**: pinned `requirements.txt` + path-filtered CI (pytest + ruff, `persist-credentials:false`) |
| Op-6 | Low | custody per-file, not bundle-atomic or durable (no fsync; partial final dir on crash) | **Fixed `b7b59934`**: `.partial-<clock>` → fsync files/manifest/dir → `os.rename` → fsync parent |
| Codex-r2-P2 | Med | `on_main=None` (origin/main unresolvable) skipped the refusal, bypassing the documented merged-to-main guarantee | **Fixed `40c93ce5`**: fail closed → `origin_main_unresolvable`; only a verified-merged HEAD proceeds |

**Cross-engine (round 2).** Codex `gpt-5.5` reviewed `b7b59934` → the one P2 above (fixed). Offline suite **48/48**, ruff clean.

**Operator to confirm live at the evidence GO (unchanged):** P6 (`verify-full`/`sslrootcert` on the direct host) · P7 (Supavisor transaction-mode `BEGIN…COMMIT`). Run **only from clean merged `main`** (now enforced by the tooling).

**Verdict (round 2): hardening tranche complete; ready for the governed PR + merge, then STOP for the operator's separate `P0-A READ-ONLY EVIDENCE` GO.** That GO authorises running `preserve_evidence.py` against production read-only; it is not granted by this review.
