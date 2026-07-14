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

---

## Round 3 — operator post-merge review (runtime integrity) + hardening + cross-engine

**Trigger.** After PR #98 merged (`cf1c72f3`), the operator ran an independent post-merge review, **HELD** `P0-A READ-ONLY EVIDENCE` again, and issued `GO PM-OPS-P0A-RUNTIME-INTEGRITY ONLY` with 5 findings — target-binding still sound; the hold is runtime integrity + governance. Design-only, no production access. Branch `pm-ops/p0a-runtime-integrity` off `cf1c72f3`; 19 commits: `f03806c4` (F1–F4) → `ad13fc3c` (F5) → `1eff8890` (cross-engine panel hardening) → 16 convergence commits `43efa331`..`07eb711c` (iterative Codex xhigh rounds; log below).

### Operator findings (5) + dispositions
| ID | Sev | Finding | Disposition |
| --- | --- | --- | --- |
| F1 | High | governed-runtime check bypassable by an untracked import-shadow module (imported at load, before validation; `--untracked-files=no` hid it) | **Fixed `f03806c4`**: strip script dir from `sys.path`; DEFER `pm_ops_p0.binding`/`psycopg` import into `_load_binding()` past the gate; pristine check includes untracked (`git status --porcelain`) |
| F2 | High | "current merged main" not enforced — an ancestor could self-attest | **Fixed `f03806c4`**: fresh `git fetch origin main` + `HEAD == origin/main == --expect-repo-sha` by equality (not ancestor) |
| F3 | Med | admin DB role caller-selectable (`--expect-db-role`) | **Fixed `f03806c4`**: flag removed; `EXPECTED_DB_ROLE` source-pinned to `postgres` |
| F4 | Med | runbook exported the DSN into the operator shell | **Fixed `f03806c4`**: `infra/infisical/inject.sh prod -- …` child-only injection; no `export` (matches `CENSUS_RUNBOOK`) |
| F5 | Med | nine-category closeout was a manual checklist with no finalizer | **Fixed `ad13fc3c`**: `finalize_closeout.py` — fail-closed, SHA-256-bound, no-clobber `closeout_index.json` |

### Cross-engine review (Codex `gpt-5.5` + two adversarial opus lenses)
Reviewed the tranche vs `origin/main`. Codex empirically verified the F2 mechanism with a live temp-git experiment (confirmed `git fetch … origin main` advances the fetched tip so an ancestor HEAD is caught). Both opus lenses were prompted to **refute**, not confirm, and did — every CONFIRMED finding was folded in `1eff8890`:

| ID | Engine | Sev | Finding | Disposition |
| --- | --- | --- | --- | --- |
| A1 | opus-A | High | `git status --porcelain` obeyed a hostile repo-local `.git/config` `showUntrackedFiles=no`, re-hiding an untracked shadow | **Fixed `1eff8890`**: force `--untracked-files=all` + pin `-c status.showUntrackedFiles=normal` |
| A2 | opus-A | Med-High | nothing verified WHAT `psycopg` resolved to (a tracked / `.gitignore`-hidden / PYTHONPATH shadow could still win) | **Fixed `1eff8890`** (initial belt: trusted-source assertion + scripts_dir append) — the belt itself was then iterated by the convergence rounds below until sound: `find_spec` origin vet BEFORE import (`8c72f15c`), prefix-match against real install dirs (`2a7ba02b`), user-site dropped (`20df0e35`), trust roots from `sys.*prefix` with no shadowable import (`fd74cd8a`), scripts_dir front-insert post-assert (`5e48dffd`) |
| P1 | Codex-xhigh | High | spec `source` caller-controlled — a DB category (3/4/5/6/9) marked `operator` skipped the manifest hash binding | **Fixed `1eff8890`**: `CATEGORY_SOURCE` pins source per category → `category_source_mismatch` |
| B-A1 | opus-B | Med | finalizer category 2 accepted ANY well-formed JSON (a saved JSON error body passed) | **Fixed `1eff8890`**: `_HTTP_REQUIRED_KEYS` require a category-2 marker (`security`/`path`) |
| B-A2 | opus-B | Med | `00_provenance.json` presence-checked but not hash-bound | **Fixed `1eff8890`**: `_require_provenance` verifies its digest vs the manifest → `hash_mismatch` |
| B-A3 | opus-B | Low-Med | `.json` operator artifacts (cat 7) got no content check | **Fixed `1eff8890`**: any `.json` artifact must parse → `failed_json` |
| A6/B-caveat | opus-A/B | Low | index atomicity + tracking-ref staleness | **Fixed `1eff8890`**: read `FETCH_HEAD`; index published `partial`→hardlink→fsync-dir; manifest key by path relative to custody |

**Residuals — accepted + documented (broader-compromise / operator-review scope):**
- A rewritten `remote.origin.url` defeats the origin/main cross-check → the operator-supplied `--expect-repo-sha` (computed out-of-band from real `main` at GO time) is the **authoritative** anchor; origin/main corroborates.
- The import-shadow class (untracked file / cwd / PYTHONPATH / user-site, incl. stdlib names) was initially a documented residual, but the convergence rounds **closed it at the interpreter level**: both CLIs refuse without `python -I` (ignores `PYTHONPATH`/user-site/unsafe `sys.path[0]`) AND a module-top preamble restricts `sys.path` to `sys.*prefix` roots before any shadowable import, AND `psycopg` is origin-vetted via `find_spec` before it executes. What remains requires writing into the interpreter install prefix (the venv itself) — a host compromise outside the checkout-write threat model.
- Operator-artifact **semantic** binding (right evidence per category — same-host OpenAPI pairs, deployed SHA, log time window) and **tamper baseline** are operator-review scope: the finalizer binds structure + hashes at publish, not meaning (lens-B A4; confirmed at the runbook Part C drift review).

**Value-silence:** re-confirmed by lens A across every new/changed path (git-state subprocess, fetch, `_load_binding` failure, finalizer) — stable codes + class-only logging; no DSN/host/password/driver text.

### Convergence — iterative Codex `gpt-5.5` xhigh re-reviews (16 rounds)

The tranche introduces two new fail-closed gates (the runtime-provenance guard and the finalizer), so Codex was re-run against **each hardened HEAD** until a clean pass. Every round surfaced a genuine finding — several of them regressions introduced by an earlier round's own fix — and each was folded with a regression test before the next round. Log (each row = one Codex re-review of the prior HEAD; findings folded in the named commit):

| Folded in | Sev | Finding |
| --- | --- | --- |
| `43efa331` | P1a/P1b | HTTP shape accepted ANY one marker (`{"path":"/reset","error":…}` passed cat 2) → require ALL markers; script categories not filename-pinned (any manifest file satisfied any category) → `CATEGORY_SCRIPT_ARTIFACTS` exact-set pin |
| `5e48dffd` | P2 | `_load_binding` APPENDED scripts_dir → a foreign PYTHONPATH `pm_ops_p0` could bind while provenance hashed this repo's `binding.py` → dedup + front-insert (post-assert); closeout index omitted the provenance/manifest hashes → recorded |
| `8c72f15c` | P1/P2 | `import psycopg` executed BEFORE the trust assertion (a shadow runs at import time) → `find_spec` origin vet pre-import; operator artifacts indexed by BASENAME (subdir collision) → custody-relative paths |
| `a3539fa5` | P1 | the git preflight subprocess inherited the injected app environment (DSN visible to git hooks/credential helpers) → scrubbed allow-list env for all git calls |
| `93479a66` | P1b/P2 | the scrub still passed `GIT_DIR`/`GIT_CONFIG`/`XDG_*` redirect vars (preflight could be repointed at an attacker repo) → dropped; cat 2 accepted any route → exact `/reset`; cat 1 satisfied by ONE OpenAPI → both-host minimum |
| `2a7ba02b` | P2 | psycopg trust used a SUBSTRING check (`/tmp/site-packages/psycopg.py` passed) → prefix-match against real install dirs; the same file listed twice satisfied a multi-capture minimum → duplicate reject |
| `20df0e35` | P2 | `getusersitepackages()` (user-writable) was a trusted root → dropped; `/reset` evidence without a proven POST method → required |
| `fd74cd8a` | P1 | the trust-root derivation itself imported `sysconfig`/`site` — themselves shadowable (empirically demonstrated) → roots derived from `sys.*prefix` attributes only, no import |
| `ac6d2ad7` | P2 | an operator category was satisfiable by a manifest-listed DB artifact → `operator_artifact_is_db`; provenance was hash-checked but its CONTENT (schema-2 governed-run attestation) unverified → `provenance_attestation_invalid` |
| `ddc19777` | P2 | alias paths (`x.json` vs `./x.json`) double-counted toward minimums → resolved-path dedup; manifest-listed files no category references were not byte-verified → full-bundle verify; symlinked provenance accepted → rejected |
| `3b68fffd` | P2 | the cwd (`""` entry) survived the sys.path preamble; a symlinked `manifest.sha256` (hashes stored outside the bundle) accepted → both rejected |
| `2ab86255` | P1/P3 | a PYTHONPATH-planted stdlib shadow still executed before the preamble → CLIs now REFUSE without `python -I` (isolated mode; `interpreter_not_isolated`); absolute artifact paths could bypass `relative_to` → rejected |
| `1a8e7e0a` | P1/P2 | the preamble ran AFTER shadowable stdlib imports → moved to module top (prefix-only, `sys`+`os` only, before any other import); one operator capture satisfied two operator categories → cross-category dedup |
| `c5623eea` | P2 | `git fetch origin main` could resolve a lightweight TAG named `main` → fetch `refs/heads/main` explicitly; cat 7/8 accepted arbitrary text/JSON → marker binding; the finalizer lacked the preamble + `-I` gate → added |
| `dc386466` | P2 | cat 7 required only `backend` (Part B/C also define the inference `source`) → both required; cat 8 accepted a route JSON or a `GET /reset` line as access-log evidence → POST + `/reset` + not-JSON shape |
| `07eb711c` | P2 | `_verify_manifest_bundle` byte-verified only what the manifest still LISTED — a tampered/regenerated manifest could DROP a fixed output no category references (`00_p0a_snapshot.sql`, `01_markers.txt`) and still pass → `REQUIRED_SCRIPT_ARTIFACTS` ⊆ manifest keys, else `incomplete_manifest` |

**Convergence achieved:** Codex xhigh re-review of `07eb711c` — **clean** ("No actionable correctness issues"). The loop was honest-to-termination: no round was skipped, and the record was not finalized until the clean pass existed.

**Value-silence:** re-confirmed across every new/changed path (git-state subprocess, fetch, `_load_binding` failure, both CLI gates, the finalizer) — stable value-free codes + class-only logging; no DSN/host/password/driver text.

**Operator to confirm live at the evidence GO (unchanged):** P6 (`verify-full`/`sslrootcert` on the direct host) · P7 (Supavisor transaction-mode `BEGIN…COMMIT`). Run **only from clean merged `main`** — now enforced by pristine (untracked-inclusive, config-proof) + `HEAD == FETCH_HEAD(refs/heads/main) == --expect-repo-sha`, under `python -I`, with child-only Infisical injection.

**Verdict (round 3): the runtime-integrity tranche is code-review-complete at `07eb711c`.** Offline suite **94/94**, `ruff check` + `ruff format` clean, LF-verified. All 5 operator findings fixed; the cross-engine panel (Codex + 2 adversarial opus lenses) plus 16 iterative Codex xhigh convergence rounds folded; final Codex pass clean; residuals accepted + documented above. Ready for the governed PR + squash merge (green CI, no admin bypass), then **STOP** for the operator's separate `P0-A READ-ONLY EVIDENCE` GO — which authorises running `preserve_evidence.py` against production read-only and is not granted by this review. No production access, SQL, HTTP evidence collection, deploy, secret change, or connectivity repair at any point in this tranche.
