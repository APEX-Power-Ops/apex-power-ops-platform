# PM/Ops P0 Containment — Cross-Engine Review Record

> Companion to `docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-design.md`.
> Design-only lane. All review passes are **read-only**; no production access, SQL, deploy, secret change,
> connectivity repair, push, or PR was performed to produce this record.
> **Data sources (rev5.1 finding 2 clarification).** The original audit (rev1–rev4) used authorized **read-only prod** SELECTs via the hash-named MCP (`bb4a07f4`, this lane). The **rev5** grant/privilege checks were newly queried during rev5 against the **`ops_dev` DEV database** (`mcp__ops-dev`, read-only, 2026-07-14) — which mirrors the ratified `012` role boundary — **NOT** production (`fxoyniqnrlkxfligbxmg`). **No production access occurred during rev5 or rev5.1.** The "live catalog / live grants" phrasing in the initial §3 was imprecise (it meant the live *dev* DB) and is corrected below.

**Subject:** PM/Ops Phase-0 emergency-containment design packet.
**GATE_SHA (platform `main`, re-derived):** `270ca6e16a9cd3cfdd0d64b67e4b6e247f24139f` (unchanged through rev5).
**Branch / worktree:** `pm-ops/p0-containment-design` @ `/home/olares/code/apex/apex-pm-ops-p0` (isolated).
**Engines:** Claude adversarial lenses (independent, blind, non-leading) + Codex (`gpt-5.5`, `codex exec review --base`). Cross-engine pass is mandatory per the Independent Review Protocol.

---

## 1. Review history (rev1 → rev5)

Each round was read-only and grounded against the host source at GATE_SHA (and, in rounds that verified catalog facts, live read-only prod via the authorized hash-named MCP). Every round caught at least one genuine CRITICAL/HIGH that inspection alone would have shipped.

| Round | Engines | Outcome |
|---|---|---|
| **R1 → rev2** | 3 Claude lenses + Codex | CRITICAL: table-ACL revoke alone left the **3 SECURITY DEFINER apparatus RPCs** (owner postgres, EXECUTE to anon) as an unauthenticated write path → added RPC `EXECUTE` revoke + `has_function_privilege` asserts. Plus PG17 `MAINTAIN` verb, missing imports, monkeypatch-vs-import test hazard. |
| **R2 → rev3** | 3 Claude lenses + Codex | CRITICAL: `ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin` bundled in the postgres-run txn would abort the whole migration (postgres ∉ supabase_admin) → **split P0-C into `014` (postgres) + `015` (supabase_admin)**. CRITICAL: P0-D default-deny gate would 503 the existing CI suite → **conftest `PM_MUTATIONS_ENABLED=true` deliverable**. HIGH: default-priv extended to `ON FUNCTIONS`. |
| **R3 → rev4** | Claude Lens-A (P0-C SQL) + Codex | Lens-A: P0-C SQL READY, 0 findings. Codex HIGH: ADP cannot strip the built-in **PUBLIC EXECUTE** on future functions → reframed honestly + §11.6 residual (rev4 added a best-effort PUBLIC token, later removed in rev5). |
| **R4 → rev5** | 7-finding code-review (operator-ratified) + this focused cross-engine pass | The seven findings below; all ratified and folded. This record documents the rev5 focused re-review of those seven changes. |

---

## 2. rev5 finding dispositions (operator-ratified 2026-07-14)

The operator ratified all seven findings with explicit rulings; each is folded into the design and mirrored in design §12.

| # | Sev | Finding | Operator ruling | Fold (design ref) |
|---|---|---|---|---|
| 1 | High | `SupabaseStore.reset()` executable outside production (env-conditional guard) | Make it **unconditionally refuse**; reset/reseed only via `MemoryStore` | §3 Change 3 — unconditional `raise`; test `test_supabase_reset_always_raises` |
| 2 | High | Readiness probed `config.engine`, not the real ops role DSNs | Probe **actual `OPS_API_DSN` / `OPS_INTAKE_WRITER_DSN`** identities, contracts, permissions | §6 per-DSN **route-critical matrix** (rev5→rev5.2): `ops_api` EXECUTE 4 recognition fns + worklist/rollup SELECT + all-5-billing denial; `ops_intake_writer` full intake/materialize/column write set + F-012-1 helper + all-9-mutation-fn denial; posture + non-`ops_fn_owner`; **not** `ops.persons` (see §5, F1) |
| 3 | High | P0-A not an authoritative snapshot (no RO txn; ACL-only enumeration; regex-only SECURITY DEFINER discovery) | Guarded **`REPEATABLE READ, READ ONLY`** txn; **effective-role closure**; **fail-closed** function/dependency discovery | §2 SQL — txn guard + fingerprint, (b)/(b2) principal×priv + `pg_auth_members` closure, (e) `pg_depend` + dynamic-SQL fail-closed |
| 4 | High | Future-function hardening internally contradictory (objective vs residual; ineffective per-schema PUBLIC revoke) | **Narrow 014 to existing-exposure containment**; remove the "best-effort PUBLIC" wording; forward-function posture = **separately measured finish line**, does not delay 014 | §4 objective + 014 stmt 3 (ADP functions `FROM anon, authenticated`) + 015 + §11.6 |
| 5 | Med | Actions "independent" but actually ordered; post-P0-D `/reset` returns 503 not 404 | Replace independence claims with an explicit **DAG** and **phase-aware `/reset` acceptance** | §1 DAG + phase-aware acceptance; §3 OpenAPI-absence invariant; §9 |
| 6 | Med | P0-D expands into learning + unsafe `startswith` prefix over-matching | **Remove learning**; **exact route-family boundary matching** | §5 `_is_pm_mutation_path` (`path == p or path.startswith(p + "/")`); `test_pm_gate_path_boundary` |
| 7 | Med | Review evidence not committed; status-note path outside repo; IRP precedent path misstated | **Commit the review record; correct all paths; record dispositions** | This file; IRP path → `docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md`; audit note → `apex-learning-lane` repo; design §8/§10/§12 |

**Preserved strengths (per the review, unchanged):** 3-RPC `EXECUTE` revocation, the `014`/`015` authority split, snapshot-derived rollbacks, `SELECT` preservation, P1 kept separate.

---

## 3. rev5 focused cross-engine review of the seven changes

**Scope:** the seven rev5 changes only (not a fresh whole-packet audit — rev1→rev4 already covered the base). Adversarial lenses were directed to try to *refute* each change against the grounded host source; Codex reviewed the `6f4b68d4` commit diff.

**Engines & method (all read-only vs `6f4b68d4`):**
- **Codex** `gpt-5.5` — `codex exec review --commit 6f4b68d4`.
- **5 Claude lenses** (opus, adversarial/refute, structured output): A = P0-C SQL; B = P0-A SQL; C = P0-B/P0-D code; D = P0-E readiness; E = whole-document coherence. Grounded via `ssh` reads of the committed blob + host source at `6f4b68d4`. 5/5 completed, 0 errors, ~542k subagent tokens.

**Consolidated findings & dispositions:**

| Source | Sev | Finding | Status | Disposition |
|---|---|---|---|---|
| Codex | P1/HIGH | `has_table_privilege('public', …)` aborts the P0-A snapshot ("role public does not exist") | **REFUTED** | Direct catalog verification on the `ops_dev` **DEV** database (`mcp__ops-dev`, read-only): `has_table_privilege('public','pg_class','SELECT')`→True, `…('public','pg_statistic','SELECT')`→False. `'public'` is a valid special user name = PUBLIC pseudo-role; query (b) & (e) do NOT abort. Independently refuted by Lens B. **No change.** |
| Codex | P2/MED | Review-record results not present in the reviewed commit | **VALID** | This §3 (commit B finalizes the record). |
| Lens A | — | P0-C SQL (5 sub-checks: RPC direct-revoke completeness vs source lineage, table 7-verb + MAINTAIN, assertions 4a/4b/4c/5, objective honesty, 015 guard) | **clean** (all REFUTED_OK) | Confirms P0-C correctness; 3 RPC signatures match source-lineage CREATE defs. No change. |
| Lens B | MEDIUM | `pg_depend` discovery is **inert for PL/pgSQL** bodies → `depends_on_targets=false` for all 3 RPCs; the design's baseline expected `true` (spurious-drift risk). Join also missing `refclassid`. | **CONFIRMED** | **Folded §2:** added `refclassid='pg_class'::regclass`; reframed `pg_depend` as supplementary/inert-for-plpgsql; `name_refs_targets` is the reliable primary; baseline corrected (`depends_on_targets=false` expected). No security miss (name-match still catches all 3). |
| Lens B | LOW | "fail-closed" overstated — indirect-write-via-helper (no name token, no EXECUTE) and non-`public` exposed-schema secdef writers are not flagged | **PLAUSIBLE** | **Folded §2:** disclosed the residual coverage gap; reframed as "fail-closed-**leaning**"; noted P0-A output is operator-reviewed evidence, not an automated gate. |
| Lens C | LOW | P0-B silently breaks the dev **persisted-validation harness** (`run_persisted_validation.py`→`validate.py` POSTs `/reset`); §3 caller-analysis omitted it | **CONFIRMED** | **Folded §3:** "Dev-tooling impact (disclosed)" — intended consequence; harness must reseed via a direct DB helper. No prod impact. |
| Lens C | NOTE | `control_plane_router` `/api/v1/control-plane/*` POST mutations not covered by P0-D prefixes | **PLAUSIBLE** | **Surfaced §11.7** as an operator scope decision (ops narrowing itself misses nothing — `ops_router` is GET-only). |
| Lens D | **HIGH** | P0-E probed `SELECT ops.persons`, which **neither** `ops_api` nor `ops_intake_writer` holds (grant is `ops_fn_owner`-only) → **false-503** of a healthy service; "greening" it would breach the ratified boundary | **CONFIRMED** (verified on `ops_dev` DEV DB, read-only: both `ops.persons`→False; `ops.v_completion_recognition_worklist`→True for api, `ops.intake_runs`→True for writer) | **Folded §6:** per-role least-privilege contracts — later expanded to the full operational matrix in rev5.1 (§4, F1). |
| Lens D | NOTE | Two sequential `connect_timeout=5` probes can sum to ~10s on a degraded DB | **PLAUSIBLE** | **Noted §6** behavior note (repoint tight-timeout monitors to `/health`). Role literals + psycopg3 usage independently confirmed grounded. |
| Lens E | NOTE | §9 acceptance P0-B row retained pre-rev5 wording ("reset() guard") | **PLAUSIBLE** | **Folded §9** — unconditional `reset()` raise. All other coherence checks (DAG↔§9, path resolution, dispositions accuracy, no dangling ref, no format breakage) REFUTED_OK. |

**Cross-engine delta.** Codex surfaced the process gap (P2, this record) but its one code-level HIGH (P1) was a **false positive** refuted by direct catalog verification (and by Lens B). The **substantive defects were caught by the Claude lenses, not Codex** — the HIGH P0-E contract error (Lens D), the MEDIUM `pg_depend` inertness (Lens B), and the dev-harness break (Lens C). Both engines independently affirmed the P0-C SQL (Lens A clean; Codex raised nothing on §4) — genuine convergence on the highest-risk change.

**Verdict — rev5 focused review COMPLETE.** 1 HIGH + 1 MEDIUM + 2 LOW + 2 NOTE folded; 1 Codex HIGH refuted with evidence; Lens A clean. **No finding overturns the design's structure or any of the seven operator rulings.** After folds, the packet is internally consistent and grounded against the host at `6f4b68d4`. **Design-only throughout — no push, no PR, no production access/SQL/deploy/secret-change/connectivity-repair. P0-A..E remain separately gated; this record and rev5 authorize no execution.**

---

## 4. rev5.1 — operator review corrections + narrow re-review

The operator issued a **HOLD-for-rev5.1** verdict (6 findings) after rev5. rev5.1 is one **docs-only** correction commit; each finding is folded and mirrored in the design's rev5.1 revision note.

| # | Sev | Finding | Ruling / correction | Fold (design ref) |
|---|---|---|---|---|
| F1 | High | P0-E verified one readable relation per role, not the operational contract — readiness could green while every POST fails (writer needs INSERT/UPDATE; api needs EXECUTE on 4 recognition fns) | Reuse migration `012`'s positive+negative assertions: writer intake writes, api recognition EXECUTE, no `ops_fn_owner` membership, no superuser/bypass, forbidden-write checks | §6 `_OPS_API_CONTRACT_SQL` / `_OPS_WRITER_CONTRACT_SQL` full matrix |
| F2 | High | Review record contradicts the production-access hold ("no prod access" vs "live catalog/grants") | Record actual authorization/timestamp/source; the rev5 checks were **`ops_dev` DEV DB** (`mcp__ops-dev`, read-only, 2026-07-14), **not** prod — no breach; wording corrected | §3 rows + this record's header |
| F3 | Med | P0-A "project fingerprint" is only a schema fingerprint — a clone/branch passes | Require `--expect-project-ref fxoyniqnrlkxfligbxmg`; value-silently validate DSN host/pooler user; in-band db/user markers | §2 Deliverable + guard comment |
| F4 | Med | `/api/v1/control-plane/*` are NOT unauthenticated — the router applies `Depends(get_current_user)` (401 on missing bearer); should stay out of P0-D | **Do not add the prefix**; rewrite §11.7 as an authenticated, separately-governed surface; retract the rev5 surfacing | §11.7 rewritten |
| F5 | Med | Readiness returns `str(exc)` — leaks hosts/roles/schema | Log detail server-side; return stable codes (`connection_failed`/`contract_missing`) | §6 both endpoints (`code:` fields, server-side `log.exception`) |
| F6 | Low | Review record retains stale `SELECT ops.persons` disposition wording | Correct it | §2 disposition row + §3 rows |

**No new defect** was found by the operator in the urgent three-RPC revocation or the `014`/`015` authority split.

### Narrow cross-engine re-review (per operator directive: P0-A target binding + P0-E complete permission matrix only)

**Method:** Codex `gpt-5.5` (`codex exec review --uncommitted`) + focused Claude lens(es), read-only, over the rev5.1 working tree (base `a3125580`), scoped strictly to the two changed areas.

**Consolidated narrow findings & dispositions (all within the two scoped areas):**

| Source | Sev | Finding | Status | Disposition |
|---|---|---|---|---|
| Codex | P1/HIGH | Writer `write_contract` omits `UPDATE ops.intake_runs` (012 grants `insert, update, select`) — could green while UPDATE-run-status POSTs fail | **CONFIRMED** | **Folded:** added `UPDATE` to `write_contract`. |
| Codex | P1/HIGH | `no_recognition_exec` checks only 2 of the 4 recognition fns — an over-granted writer on `revoke`/`approve_and_recognize` slips through | **CONFIRMED** | **Folded:** now denies all 4 recognition fns. |
| P0-E lens | LOW | Same 2-of-4 recognition-fn coverage asymmetry | **PLAUSIBLE** (converges with Codex P1b) | **Folded** (all 4). |
| P0-E lens | NOTE×5 | 4 recognition-fn signatures byte-for-byte match 012; enum-qualified `approve_and_recognize` resolves; writer positive+negatives don't false-503 a correct role; posture/`pg_has_role`/`has_function_privilege` are readable from the role's own session; **both readiness endpoints leak no host/role/schema/DSN string (finding 5 clean)** | **REFUTED_OK** | Confirms the matrix + finding-5 error handling. |
| P0-A lens | MEDIUM | Pooler branch validated user `postgres.<ref>` but not host; substring match is suffix-injectable (`db.<ref>.supabase.co.evil.tld`) | **PLAUSIBLE** | **Folded:** structured/anchored DSN parse + pooler-host `*.pooler.supabase.com` requirement. |
| P0-A lens | LOW | Value-silence scoped to pre-connect refusal only; psycopg connect-path `OperationalError` can leak host/port/user | **PLAUSIBLE** | **Folded:** value-silence extended end-to-end (stable code + server-side log on the connect/query path). |
| P0-A lens | NOTE | In-band markers can't corroborate the project on managed Supabase (`current_database()`='postgres'; `inet_server_addr()`=node IP; `current_user` generic) — DSN parse is single-point-of-truth | **PLAUSIBLE** | **Folded:** disclosed; residual accepted. |
| P0-A lens | NOTE | Core of finding 3 (fingerprint-secondary, value-free refusal) | **REFUTED_OK** | Direction stands. |

**Cross-engine delta.** Codex and the P0-E lens **converged** on writer-contract completeness (add `UPDATE`; deny all 4 recognition fns) — the two P1s. The P0-A lens (Claude) independently hardened the DSN binding (structured parse, pooler-host, end-to-end value-silence, marker disclosure) that Codex did not examine. The exec-contract signatures, enum resolution, and finding-5 leak-freedom were affirmed by the Claude P0-E lens.

**Verdict — narrow re-review COMPLETE.** The two scoped areas were checked by both engines; the review surfaced targeted refinements (Codex 2× P1 + three P0-A hardenings), **all folded into this same rev5.1 commit**. After folds, the P0-A target binding and the P0-E full permission matrix are complete and grounded against migration `012`. Per the operator directive, **the audit loop stops here.** **Design-only throughout — no push, no PR, no production/prod-DB access, SQL, deploy, secret-change, or connectivity-repair. P0-A..E remain separately gated; rev5.1 authorizes no execution.**

---

## 5. rev5.2 — operator review corrections + focused parser/matrix re-review

The operator issued a second **HOLD** (4 findings) after rev5.1, holding P0-A pending a bounded rev5.2. rev5.2 is one **docs-only** correction commit, grounded on migration `012` (DDL) — **no live DB query** (per operator directive; task 5).

| # | Sev | Finding | Correction | Fold (design ref) |
|---|---|---|---|---|
| F1 | High | P0-E still not the full contract — writer positive checked only `ops.intake_runs`; negatives only 4 (of 9) writer fns and none of the api's 5 billing fns | Route-critical matrix: full 012 positive grants (intake+materialize+project/apparatus col+core+helper) + **complete** negatives (writer all 9 mutation fns; api all 5 billing fns; F-012-1 helper; status/provenance/DELETE) | §6 `_OPS_API_CONTRACT_SQL` / `_OPS_WRITER_CONTRACT_SQL` |
| F2 | Med | DSN binding underspecified vs libpq overrides (`hostaddr`, `service`, multi-host, URI query) | Parse with `psycopg.conninfo.conninfo_to_dict`; reject `hostaddr`/`service`/multi-host/multi-port/empty-ambiguous + URI-query overrides before the anchored host/user rules | §2 Project binding |
| F3 | Med | "End-to-end value silence" conflicted with raw exception logging | Ordinary logs = stable code + exception **class** only (P0-A + both readiness endpoints); raw diagnostics require restricted custody + secret scan | §2 + §6 (`log.warning(..., type(exc).__name__)`) |
| F4 | Low | Stale `INSERT+SELECT` prose (behavior note + review record) omitting `UPDATE`/full matrix | Corrected to the route-critical matrix | §6 behavior note + §2 row above |

**No new defect** was found in reset containment, the three-RPC revocation, or the `014`/`015` split; `fafe5e26` was clean/docs-only/unpushed.

### Focused parser/matrix re-review (per operator directive: parser + matrix only; NO broad audit, NO live DB query)

**Method:** Codex `gpt-5.5` (`codex exec review --uncommitted`) + focused Claude lens(es), read-only over the rev5.2 working tree (base `fafe5e26`), scoped strictly to the DSN parser contract and the route-critical matrix, grounded on migration `012` (DDL only).

**Consolidated focused findings & dispositions (matrix + parser only; all folded into this same rev5.2 commit):**

| Source | Sev | Finding | Status | Disposition |
|---|---|---|---|---|
| Matrix lens | NOTE | Every 012-grounded POSITIVE + all fn signatures (incl. both `issue_billing_application` overloads, the enum-qualified `approve_and_recognize`) + the has_table/has_column split are correct — **no false-503, no missing route positive, no signature error** | **REFUTED_OK** | Confirms the positive matrix + signatures. |
| Matrix lens | MEDIUM | `NOT has_table_privilege(...,'public.apparatus','UPDATE')` is **not** 012-grounded — depends on the PUBLIC-inherited ACL; ops roles inherit any PUBLIC grant, so pre-P0-C it would **false-503** a correctly-provisioned ops role, coupling P0-E to P0-C ordering | **PLAUSIBLE** | **Folded:** removed the `public.apparatus` check from both role matrices (behavior note documents that public-write containment is P0-C's job). |
| Codex P1a / lens LOW | HIGH/LOW | Writer positive checked only 3 columns; 012 grants all **14 `projects` UPDATE** columns + projects/apparatus INSERT | **CONFIRMED** | **Folded:** `projects_write` now requires all 14 UPDATE columns (unnest, mirrors 012 foreach) + table-level `projects`/`apparatus` INSERT. |
| Codex P1b / lens LOW | HIGH/LOW | api negative missed `scope_quote_line` + **DELETE** across the 5 scoping tables | **CONFIRMED** | **Folded:** api `no_forbidden_write` = `NOT EXISTS` I/U/D over all 5 scoping tables + apparatus fabricate/status/provenance. |
| Codex P2 / lens LOW | MED/LOW | Writer billing negative checked only `billing_application`; 012 denies I/U/D on all **3** billing tables + recognition/attestation | **CONFIRMED** | **Folded:** writer `no_forbidden_write` = `NOT EXISTS` I/U/D over the **5** recognition/billing tables + the 5-table DELETE set + apparatus.status. |
| **DSN lens** | **HIGH** | `conninfo_to_dict` parses only the **string**; libpq merges `PGHOSTADDR`/`PGSERVICE`/`PGHOST`/`PGPORT` from the **environment** at connect → an env-supplied `hostaddr`/`service` reroutes the actual connection while the string passes every reject; "single point of truth" over-claimed | **CONFIRMED** | **Folded:** scrub PG\* env, pass explicit params, require `sslmode=verify-full`, re-validate `Connection.info` post-connect; claim reframed to "the parameter set libpq actually connects with." |
| DSN lens | LOW | The pre-connect `conninfo_to_dict` parse of a malformed DSN can raise a libpq error whose message quotes a DSN token; not explicitly wrapped | **PLAUSIBLE** | **Folded:** parse wrapped in the value-silence (stable code, never raw). |
| DSN lens | NOTE×2 | URI-query expansion closes `?hostaddr=`; anchored pooler/direct host matching rejects suffix-injection | **REFUTED_OK** | Confirms those vectors closed. |

**Cross-engine delta.** Codex and the matrix lens **converged** on the negative-completeness gaps (writer/api I/U/D coverage). The matrix lens uniquely caught the `public.apparatus` **false-503 / P0-C-coupling** (a correctness risk, not just completeness) and independently affirmed all positives + signatures. The DSN lens uniquely caught the **PG\*-environment reroute** (HIGH) that neither Codex nor the string-level checks surfaced.

**Verdict — focused parser/matrix re-review COMPLETE.** All findings folded into this same rev5.2 commit; the matrix now mirrors 012's positive grants and `[5a]` negatives completely (14 projects columns; full 5-table I/U/D sets), the non-012 `public.apparatus` false-503 is removed, and the DSN binding is hardened against env-var reroute. **(SUPERSEDED by §6/rev5.3** — this rev5.2 matrix still tested column-scoped `projects`/`apparatus` INSERT with `has_table_privilege`, which returns false for column-only grants and would false-503; the rev5.2 focused-review lens asserted the opposite and was **wrong**. Corrected in rev5.3 with `has_column_privilege` and an objective parity test.) Grounded on migration 012 (DDL) — **no live DB query** (per operator directive). Per the operator directive, **the audit loop stops here.** **Design-only throughout — no push, no PR, no production/prod-DB access, SQL, deploy, secret-change, or connectivity-repair. P0-A..E remain separately gated; rev5.2 authorizes no execution.**

---

## 6. rev5.3 — narrow P0-E correction (`has_column_privilege` + DSN binding) + static parity test

The operator's rev5.2→5.3 review found **3** findings and **lifted the P0-A design hold** (the rev5.2 DSN direction is adequate for an offline implementation checkpoint). rev5.3 is a docs+test narrow P0-E correction — **no broad review round**; a deterministic static parity test replaces subjective review. **Critical lesson recorded:** rev5.2's focused-review *lens* asserted `has_table_privilege` succeeds for column-scoped grants — **wrong**. PostgreSQL returns **false** (that is precisely what `has_any_column_privilege` exists for), as `IRP_OPUS_2026-07-01` MEDIUM records (live-reproduced). The cross-engine lens was confidently wrong; the operator caught it against the repo's own IRP. The matrix is now guarded by an **objective parity test**, not a subjective review.

| # | Sev | Finding | Fold |
|---|---|---|---|
| F1 | High | Writer positive tested column-scoped `projects`/`apparatus` INSERT with `has_table_privilege` → would **false-503** a correct role | `has_column_privilege` for all **15 projects** + **11 apparatus** INSERT columns + all **3 scope_quote** UPDATE columns |
| F2 | High | P0-E did not bind the serving DSNs to the prod project — a dev/branch DSN satisfies the matrix for the wrong project | `bind_target(dsn, expect_ref='fxoyniqnrlkxfligbxmg')` (shared P0-A discipline) on **both** serving DSNs in `_probe_ops` |
| F3 | Med | API negative omitted the 5 recognition/billing tables + apparatus DELETE; table-level checks miss column-scoped drift | api negative covers the full **11-table** write surface; forbidden I/U via `has_any_column_privilege`, DELETE via `has_table_privilege` |

**Task 4 — static parity test** (`docs/superpowers/specs/pm-ops-p0/test_p0e_matrix_parity.py`). Offline, no live DB. Derives the authoritative column/table/fn sets from migration 012's grant DDL and asserts the design matrix mirrors them exactly and uses the correct privilege functions. **Result: 25/25 checks PASS** — all 5 column sets == 012; no `has_table_privilege` on column-scoped INSERT; `has_any_column_privilege` on the forbidden negatives; all 9 mutation fns + both `issue_billing_application` overloads + the F-012-1 helper; api names all 11 write tables.

**Task 5 — claim correction.** The rev5.2 "complete matrix" claim (§5) was **premature** (it rested on the incorrect lens). It is corrected here: the matrix mirrors migration 012 exactly, now **backed by the passing parity test**, not a subjective review.

**Verdict — rev5.3 COMPLETE.** 3 findings folded; parity test green (25/25). **Docs + offline test only — no push, no PR, no production/prod-DB access, no live query.** The operator lifted the P0-A design hold and **authorized the sequence**: governed design PR + merge → `P0-A TOOLING ONLY` (implement + offline-test the evidence script, no prod) → separate `P0-A READ-ONLY EVIDENCE` GO after code review → P0-B → urgent P0-C `014` (`015` separate) → P0-D → corrected P0-E.
