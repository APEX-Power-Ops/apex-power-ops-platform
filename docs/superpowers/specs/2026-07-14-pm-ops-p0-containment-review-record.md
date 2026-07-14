# PM/Ops P0 Containment — Cross-Engine Review Record

> Companion to `docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-design.md`.
> Design-only lane. All review passes are **read-only**; no production access, SQL, deploy, secret change,
> connectivity repair, push, or PR was performed to produce this record.

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
| 2 | High | Readiness probed `config.engine`, not the real ops role DSNs | Probe **actual `OPS_API_DSN` / `OPS_INTAKE_WRITER_DSN`** identities, contracts, permissions | §6 `_probe_role` (psycopg per-DSN; `current_user`=`ops_api`/`ops_intake_writer`, `ops` USAGE + `SELECT ops.persons`, not-superuser, no `UPDATE public.apparatus`) |
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
| Codex | P1/HIGH | `has_table_privilege('public', …)` aborts the P0-A snapshot ("role public does not exist") | **REFUTED** | Direct catalog verification on live PG: `has_table_privilege('public','pg_class','SELECT')`→True, `…('public','pg_statistic','SELECT')`→False. `'public'` is a valid special user name = PUBLIC pseudo-role; query (b) & (e) do NOT abort. Independently refuted by Lens B. **No change.** |
| Codex | P2/MED | Review-record results not present in the reviewed commit | **VALID** | This §3 (commit B finalizes the record). |
| Lens A | — | P0-C SQL (5 sub-checks: RPC direct-revoke completeness vs source lineage, table 7-verb + MAINTAIN, assertions 4a/4b/4c/5, objective honesty, 015 guard) | **clean** (all REFUTED_OK) | Confirms P0-C correctness; 3 RPC signatures match source-lineage CREATE defs. No change. |
| Lens B | MEDIUM | `pg_depend` discovery is **inert for PL/pgSQL** bodies → `depends_on_targets=false` for all 3 RPCs; the design's baseline expected `true` (spurious-drift risk). Join also missing `refclassid`. | **CONFIRMED** | **Folded §2:** added `refclassid='pg_class'::regclass`; reframed `pg_depend` as supplementary/inert-for-plpgsql; `name_refs_targets` is the reliable primary; baseline corrected (`depends_on_targets=false` expected). No security miss (name-match still catches all 3). |
| Lens B | LOW | "fail-closed" overstated — indirect-write-via-helper (no name token, no EXECUTE) and non-`public` exposed-schema secdef writers are not flagged | **PLAUSIBLE** | **Folded §2:** disclosed the residual coverage gap; reframed as "fail-closed-**leaning**"; noted P0-A output is operator-reviewed evidence, not an automated gate. |
| Lens C | LOW | P0-B silently breaks the dev **persisted-validation harness** (`run_persisted_validation.py`→`validate.py` POSTs `/reset`); §3 caller-analysis omitted it | **CONFIRMED** | **Folded §3:** "Dev-tooling impact (disclosed)" — intended consequence; harness must reseed via a direct DB helper. No prod impact. |
| Lens C | NOTE | `control_plane_router` `/api/v1/control-plane/*` POST mutations not covered by P0-D prefixes | **PLAUSIBLE** | **Surfaced §11.7** as an operator scope decision (ops narrowing itself misses nothing — `ops_router` is GET-only). |
| Lens D | **HIGH** | P0-E probed `SELECT ops.persons`, which **neither** `ops_api` nor `ops_intake_writer` holds (grant is `ops_fn_owner`-only) → **false-503** of a healthy service; "greening" it would breach the ratified boundary | **CONFIRMED** (verified live: both `ops.persons`→False; `ops.v_completion_recognition_worklist`→True for api, `ops.intake_runs`→True for writer) | **Folded §6:** per-role least-privilege contracts — `ops.v_completion_recognition_worklist` (ops_api), `ops.intake_runs` (writer). |
| Lens D | NOTE | Two sequential `connect_timeout=5` probes can sum to ~10s on a degraded DB | **PLAUSIBLE** | **Noted §6** behavior note (repoint tight-timeout monitors to `/health`). Role literals + psycopg3 usage independently confirmed grounded. |
| Lens E | NOTE | §9 acceptance P0-B row retained pre-rev5 wording ("reset() guard") | **PLAUSIBLE** | **Folded §9** — unconditional `reset()` raise. All other coherence checks (DAG↔§9, path resolution, dispositions accuracy, no dangling ref, no format breakage) REFUTED_OK. |

**Cross-engine delta.** Codex surfaced the process gap (P2, this record) but its one code-level HIGH (P1) was a **false positive** refuted by direct catalog verification (and by Lens B). The **substantive defects were caught by the Claude lenses, not Codex** — the HIGH P0-E contract error (Lens D), the MEDIUM `pg_depend` inertness (Lens B), and the dev-harness break (Lens C). Both engines independently affirmed the P0-C SQL (Lens A clean; Codex raised nothing on §4) — genuine convergence on the highest-risk change.

**Verdict — rev5 focused review COMPLETE.** 1 HIGH + 1 MEDIUM + 2 LOW + 2 NOTE folded; 1 Codex HIGH refuted with evidence; Lens A clean. **No finding overturns the design's structure or any of the seven operator rulings.** After folds, the packet is internally consistent and grounded against the host at `6f4b68d4`. **Design-only throughout — no push, no PR, no production access/SQL/deploy/secret-change/connectivity-repair. P0-A..E remain separately gated; this record and rev5 authorize no execution.**
