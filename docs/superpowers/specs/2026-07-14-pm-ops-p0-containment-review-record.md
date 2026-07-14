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

**Scope:** the seven rev5 changes only (not a fresh whole-packet audit — rev1→rev4 already covered the base). Adversarial lenses were directed to try to *refute* each change against the grounded host source; Codex reviewed the `850c4579..HEAD` diff.

**Status:** executed against the rev5 design commit on this branch. Findings, cross-engine delta, and verdict are recorded in the immediately-following commit on `pm-ops/p0-containment-design` (this record is committed alongside the design so the design's references resolve; the focused-review results are appended once the pass completes — read-only, no push).

_(Results appended below in the follow-up commit.)_
