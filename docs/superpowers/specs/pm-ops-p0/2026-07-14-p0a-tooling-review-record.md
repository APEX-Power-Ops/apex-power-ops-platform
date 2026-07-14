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

**Verdict: tooling is code-review-complete and ready for the operator's separate `P0-A READ-ONLY EVIDENCE` GO.** That GO authorises running `preserve_evidence.py` against production read-only; it is not granted by this review.
