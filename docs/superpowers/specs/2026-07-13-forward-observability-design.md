# Forward-observability packet — design (Phase 9A-OBS-DESIGN)

2026-07-13 · disposition-ledger lane · authored under operator GO "Phase 9A-OBS-DESIGN — design/spec only; no production access or mutation" · **stops for operator review; technical-authority approval only after the pending Supabase support response is folded in (§10)**

## 1. Objective and scope

Produce a **truthful `consumer_evidence.runtime_logs` overlay** for exactly the three Phase-8R-ratified cohort views —
`public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_pending_handoffs` — by **forward observation**, because
Phase 9A established (and Phase 9A-CAP confirmed) that historical direct-SQL read evidence does not exist:
`log_statement=ddl`, `log_min_duration_statement=-1`, pgAudit inactive, and the accessible log surface cannot reach a
window bracketing the current census instant.

Two tiers. **Tier A (preferred, §4): no-reset `pg_stat_statements` baseline/delta plus bounded API-gateway logs** — zero
production mutation. **Tier B (escalation only, §5): narrowly scoped pgAudit read telemetry** — production writes behind
separate enable/restore GOs. This document authorizes NOTHING; every execution step maps to its own future GO (§8).

Out of scope: the other five overlay dimensions' collection procedures (their existing runbook rows govern), the fresh
census procedure itself (CENSUS_RUNBOOK governs; this design only fixes its TIMING), and any disposition decision.

## 2. Grounding

Tiers of grounding used here, labeled throughout:
- **(a) census/9A-CAP-observed facts** — read-only observations of prod `fxoyniqnrlkxfligbxmg` on 2026-07-13 (~20:10Z):
  `log_statement=ddl` (config file); `log_min_duration_statement=-1`; `log_connections=off`; `log_duration=off`;
  pgAudit **library preloaded** in `shared_preload_libraries` but **extension NOT installed** (available 17.1) and inactive
  (`pgaudit.log=none`, `pgaudit.role` empty); `pg_stat_statements` **1.11 installed + preloaded**, `stats_reset
  2026-05-31T03:10:51Z`, 4,867 tracked of `pg_stat_statements.max=5000` (**near eviction cap**), `pg_stat_statements_info.dealloc`
  available; cohort name-match telemetry 3 entries / 3 calls per view (unattributed by design).
- **(b) repo facts at `GATE_SHA`** — `OVERLAY_COLLECTION_RUNBOOK.md` (dimension table, window discipline §3, author
  command §4), `overlay.schema.json`, `author_overlay.py` / `verify_overlay_artifact.py` contracts.
- **(c) policy anchors** — per-phase GO discipline; value-silence; `APPROVED_CUSTODY_SCHEMES = {vault, infisical}`;
  operator findings of 2026-07-13 (no `pg_stat_statements_reset()`; eviction fail-closed; support response = input, not
  prerequisite).
- **(d) PostgreSQL-semantic inferences**, labeled `(PG-inference)` — e.g. `pg_stat_statements` 1.11 per-entry
  `stats_since` / `minmax_stats_since` columns and `pg_stat_statements_info (dealloc, stats_reset)` semantics; pgAudit
  object-audit mechanics. Any (d) claim load-bearing at execution time carries a **verify-at-execution preflight** in §8.

Pin vocabulary (fixed 2026-07-13): `GATE_SHA` (origin/main, re-derived at every GO; `8678f30e` at authoring),
`BASE_SNAPSHOT_SHA256` / `CENSUS_REPO_SHA` / `QUERY_BUNDLE_SHA256` / `CENSUS_OBSERVED_AT` — after the fresh census
(§3) these four re-pin to the NEW census; the current `52962abe…` census remains valid for the already-merged Phase-8
reconciliation but is superseded for overlay binding.

## 3. Timeline invariant (why the census sits INSIDE the observed window)

```
T0 = Tier-A baseline snapshot (read-only)            ── window opens
T1 = fresh signed census (CENSUS_OBSERVED_AT_new)    ── T0 < T1
Tobs = operator-approved observation interval        ── runs after T1
Tend = end snapshot + bounded API-log export         ── window closes; T0 < T1 < Tend
```

The runtime_logs overlay's `observation_window` is **[T0, Tend]** — truthful because the baseline/delta method measures
exactly that span. OV017 requires the derived consumer window to bracket the census instant (`S ≤ observed_at ≤ E`);
with `started_at = T0 < T1` and `ended_at = Tend > T1`, this overlay brackets by construction. **Window-coordination
requirement for the other three consumer dimensions** (`static_repo`, `external_clients`, `operator_declaration`): each
must truthfully support `started_at ≤ T1` and `ended_at ≥ T1`, collected close to Tend (OV016 freshness runs against the
earliest `ended_at`; preapply within 720 h of it). The `in_data_api_exposed_schema` overlay window must **cover**
`[S, E] = [max(started), min(ended)]` (OV022). A one-page window table is produced at Phase-10 assembly and checked
against these rules before any signing.

**Never backdate:** no window may start before the evidence source actually covers (T0 is the earliest truthful start
for Tier-A SQL evidence; API-log bounds are whatever the export's explicit `iso_timestamp_start/end` prove).

## 4. Tier A (preferred) — no-reset `pg_stat_statements` baseline/delta + bounded API-gateway logs

### 4.1 Baseline snapshot (read-only GO "OBS-A1")
Captured via the authorized governed-prod SQL surface, SELECT-only, value-silent:
1. **Environment**: `stats_reset` + `dealloc` from `pg_stat_statements_info`; tracked-entry count;
   `pg_stat_statements.max`; `pg_stat_statements.track`; `pg_stat_statements.track_utility`; `compute_query_id`;
   server version. (`track`/`compute_query_id` were NOT captured in 9A-CAP — first capture happens here; if
   `compute_query_id=off` or `track=none`, **fail closed before starting**: deltas would be meaningless.)
2. **Cohort entries** (filter server-side on `query ILIKE` any of the three names; output **never includes query text**):
   `dbid`, `userid` (numeric) + `rolname` via join, `queryid`, `toplevel`, `calls`, `rows`, `stats_since`.
   `(PG-inference: stats_since/minmax_stats_since are per-entry first-tracked timestamps in pg_stat_statements 1.11;
   verify column presence in the OBS-A1 preflight.)`
3. **Anti-eviction guard for baseline entries**: record the full baseline row-set hash so end-comparison detects any
   disappearance.
4. Baseline artifact: one JSON snapshot, hashed, stored out-of-repo; raw copy under `vault:`/`infisical:` custody.
   Client details (rolname) stay in the raw/custody copy; the committed source record later carries redacted role
   *classes* (e.g. "service role", "operator role"), not names, unless the operator declassifies.

**No `pg_stat_statements_reset()` anywhere in this packet** (operator finding 2). The baseline/delta method needs none.

### 4.2 Fresh signed census (GO "OBS-CENSUS", CENSUS_RUNBOOK verbatim)
Run AFTER OBS-A1 completes, from clean merged main; new `BASE_SNAPSHOT_SHA256`/`CENSUS_OBSERVED_AT`; published +
merged per the Phase-6/7/7M pattern. All six Phase-9 overlays bind to THIS census.

### 4.3 Observation interval (no GO needed — passive)
- **Duration**: operator decision (§9 D1). Lean: **7 days** — long enough for weekly cron/report consumers, short
  enough that OV016 (720 h) and evidence freshness stay comfortable.
- **Controlled-consumer discipline**: during [T0, Tend], deliberate queries naming the cohort views (dashboard
  browsing, ad-hoc SQL, demos) are **prohibited by default**; any exception is logged at execution time in a
  controlled-consumer log (who/when/surface/purpose — one line each) that becomes part of the source record, so
  end-deltas decompose into `controlled + uncontrolled`. Known self-noise that needs no logging `(PG-inference)`:
  the snapshot queries themselves normalize their ILIKE literals to `$N` and do not create name-matching entries;
  the census collector queries catalogs only and never selects from the views.
- Platform posture freeze: no Packet-01-style grant/DDL changes to the three views during the interval (would confound
  both the census and the deltas); the lane holds A1–A3 anyway.

### 4.4 End snapshot + delta (read-only GO "OBS-A2")
Same captures as OBS-A1, plus:
- **Delta computation** per `(dbid, userid, queryid, toplevel)`: `calls_end − calls_base` (new entries: `calls_end`
  with `stats_since ≥ T0` as corroboration).
- **`found_consumers` definition (fixed here):** the number of distinct `(userid, queryid)` pairs with positive
  uncontrolled call-delta across the three views' matching entries, **plus** distinct API-client identities from §4.5.
  Per-view assignment values follow the runbook's consumer_evidence_dim shape
  (`{"state":"observed","found_consumers":<int>,"ref":"<source-record ref>"}`).
- A zero result is reportable ONLY if every fail-closed condition in §6 passed — and even then the overlay reports
  "0 observed under the stated instruments and window", never "no consumers exist" (the record states instrument
  limits: normalized-literal blindness, `track=top` nesting blindness `(PG-inference)`, eviction cap).

### 4.5 Bounded API-gateway log component (same window, explicit bounds)
Purpose: HTTP/Data-API consumers (`/rest/v1/<view>` paths) that SQL telemetry cannot see, and vice-versa.
- **Surface** (§9 D2): lean = **operator-run Logs Explorer SQL export** over `edge_logs` with explicit
  `iso_timestamp_start=T0`, `iso_timestamp_end=Tend`, path filter on the three view names; export (JSON/CSV) handed to
  the executor as raw evidence. Alternative = Management-API analytics endpoint with an operator-injected
  `SUPABASE_ACCESS_TOKEN` via `inject.sh` (new credential path; needs explicit approval). Either way the export must
  EMBED its bounds; **bounds unavailable or unverifiable ⇒ fail closed** (GO requirement).
- If the pending support response recovers 2026-07-13 API history, that recovery only ever ADDS an earlier-window API
  annex to the source record; it cannot substitute for [T0, Tend] SQL evidence (operator finding 1).

### 4.6 Evidence assembly (feeds the eventual Phase-9 runtime_logs GO)
Normalized, redacted source record = {baseline snapshot digest, end snapshot digest, delta table (counts only),
controlled-consumer log, API-log extract with bounds, fail-closed checklist results}. Raw un-redacted material under
`vault:`/`infisical:` custody, referenced per runbook §1/§4. Author via `author_overlay.py` with the runbook §4 pins
(NEW census; `--producing-repo-sha-na-reason` since runtime_logs forbids a producing SHA), window `[T0, Tend]`,
validate-before-sign, `verify_overlay_artifact.py` GREEN, secret-scan — all under that future GO, not this design.

## 5. Tier B (escalation only) — narrowly scoped pgAudit read telemetry

**Trigger criteria (any):** Tier-A fail-closed conditions trip un-recoverably (e.g. repeated eviction churn), the
operator requires statement-time attribution that counters cannot give, or a disposition decision needs per-session
evidence. Tier B is NOT entered by default.

- **Mechanism `(PG-inference; verify at enable)`:** object-scoped audit via `pgaudit.role` — create a NOLOGIN marker
  role (e.g. `disposition_audit`), `GRANT SELECT ON` **only the three cohort views** to it, set `pgaudit.role`; pgAudit
  then logs only statements touching objects that role can read, i.e. reads of the three views — NOT global
  `pgaudit.log=read` session logging (unbounded volume).
- **Prod-write inventory (all inside GO "OBS-B-ENABLE"):** `CREATE EXTENSION pgaudit` (library already preloaded per
  9A-CAP ⇒ **no restart/reboot expected**; verify), create marker role, three grants, set `pgaudit.role` (SUSET —
  exact Supabase-permitted mechanism, `ALTER DATABASE/ROLE ... SET`, is a **verify-at-enable preflight**; if the
  managed `postgres` role cannot set it, Tier B is BLOCKED, not worked around — see
  [[feedback_supabase_prod_superuser_fidelity]]), keep `pgaudit.log_parameter=off`.
- **Volume estimate:** proportional to actual cohort reads (expected near-zero given Phase-8 static evidence); logs
  flow to the postgres log stream where retention is plan-bound — harvest within retention or continuously.
- **Sensitive-data handling:** pgAudit records statement TEXT ⇒ the log stream becomes secret-bearing (literals may
  embed identifiers); committed record = redacted extract, raw under custody; parameters logging stays off.
- **Rollback/restore (GO "OBS-B-RESTORE", separate):** clear `pgaudit.role`, revoke the three grants, drop the marker
  role, optionally `DROP EXTENSION pgaudit`; verify all settings back to the 9A-CAP baseline; harvest + redact residual
  logs first.
- Tier B still uses the §3 timeline (its window starts when auditing verifiably begins) and §4.5 API component.

## 6. Fail-closed matrix (Tier A; all ⇒ BLOCKED, no negative conclusion, report and stop)

| # | Condition | Detected by |
|---|---|---|
| F1 | `stats_reset` differs between OBS-A1 and OBS-A2 | `pg_stat_statements_info.stats_reset` |
| F2 | `dealloc` increased over the interval | `pg_stat_statements_info.dealloc` baseline vs end |
| F3 | Any baseline cohort entry missing at end | baseline row-set vs end row-set |
| F4 | `pg_stat_statements.track/track_utility/compute_query_id/max` changed, or `track=none`/`compute_query_id=off` at baseline | settings capture both ends |
| F5 | Snapshot query failure / surface unavailable | OBS-A1/OBS-A2 execution |
| F6 | API-log export bounds unavailable, unverifiable, or not covering [T0, Tend] | §4.5 export inspection |
| F7 | Uncontrolled interference (grant/DDL change to cohort views during interval) | census + `pg_stat_statements` env checks, git/lane log |
| F8 | Controlled-consumer log incomplete (a known deliberate query unlogged) | operator attestation at OBS-A2 |

F2/F3 nuance: eviction near the 4,867/5,000 cap is plausible; if tripped, remediation is a LONGER second attempt or a
Tier-B escalation decision — never loosening the guard, never a reset.

## 7. Optional pre-step — attribution probe (read-only GO "OBS-A0", operator finding 4)

Before OBS-A1, optionally attribute the existing symmetric 3-entries/3-calls pattern: expose `rolname`, `queryid`,
`toplevel`, `calls`, `stats_since` for the current name-matching entries — **no query text**. Outcome only informs
expectations (e.g. confirming they are 2026-07-13 audit traffic via `stats_since`); it feeds the controlled-consumer
ledger but gates nothing.

## 8. GO map (nothing here is authorized by this design)

| Step | GO | Access | Writes |
|---|---|---|---|
| OBS-A0 attribution probe (optional) | own GO | prod read-only | none |
| OBS-A1 baseline snapshot | own GO | prod read-only | none |
| OBS-CENSUS fresh census (+ publish/merge per 6/7/7M pattern) | own GOs | prod read-only | repo evidence |
| observation interval | none (passive) | none | none |
| OBS-A2 end snapshot + delta | own GO | prod read-only | none |
| API-log export | operator-run (lean) or own GO (token path) | platform logs read-only | none |
| runtime_logs overlay author/sign | Phase-9 runtime_logs GO | none (offline + injected key) | out-of-repo artifacts |
| remaining five overlays | five separate Phase-9 GOs | per runbook | out-of-repo artifacts |
| OBS-B-ENABLE / OBS-B-RESTORE (escalation only) | separate WRITE GOs | prod write | extension/role/grants/GUC |

Verify-at-execution preflights carried by their GOs: `stats_since`/`minmax_stats_since` column presence (OBS-A1);
`compute_query_id`/`track` values (OBS-A1); Supabase-permitted mechanism for `pgaudit.role` and no-restart assumption
(OBS-B-ENABLE).

## 9. Operator decision points (leans first)

- **D1 — interval duration:** lean **7 days**; alternatives 72 h (faster, misses weekly consumers) / 14 d (higher
  eviction-guard exposure F2/F3, later gate).
- **D2 — API-log surface:** lean **operator-run Logs Explorer export** (no new credential path); alternative
  Management-API + injected token (repeatable, scriptable, new secret path).
- **D3 — OBS-A0 attribution probe:** lean **run it** (cheap, read-only, de-noises the baseline).
- **D4 — Tier-B pre-authorization:** lean **decide only if triggered** (keep Tier B cold; its enable GO is written
  when its trigger criteria are met, folding this §5 spec).

## 10. Support-response fold-in (before technical-authority approval)

The pending Supabase ticket (recoverability of 2026-07-13 `edge_logs` / statement logs; project-specific ingestion
loss; exact retention) folds in here: (i) recovered API history → optional historical annex to the source record
(§4.5), never a substitute; (ii) confirmed ingestion loss → notes a platform-reliability caveat on §4.5 and may raise
D2 to the token path with tighter bounds verification; (iii) retention numbers → bound the API harvest cadence for D1
durations > retention. **No section's SQL-side design depends on the response** (operator finding 1).

## 11. Explicit prohibitions inherited by every execution GO

No `pg_stat_statements_reset()`. No pgAudit installation/role/GUC change outside OBS-B-ENABLE. No census before
OBS-A1. No overlay signing against the old census `52962abe…`. No query text or client identities in committed
records. No backdated windows. Signing key remains in Infisical operator custody, injected child-only. Custody
locators `vault:`/`infisical:` only. Any ambiguity, guard failure, or drift ⇒ STOP.
