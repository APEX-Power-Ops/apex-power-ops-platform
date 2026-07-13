# Forward-observability packet — design (Phase 9A-OBS-DESIGN), rev 3

2026-07-13 · disposition-ledger lane · authored under operator GO "Phase 9A-OBS-DESIGN — design/spec only; no production access or mutation" · **stops for operator review.** Ratification was HELD at rev 2 on three operator P1 false-green findings; rev 3 closes them (F9 text-discard gate; selective-reset epistemic cap F10; log-ingestion liveness sentinels) plus two P2s (outward API bounds; marker-role zero-write realization) and one P3 (OBS-A0 attribution wording) — see §12. The pending Supabase support response folds in via §10 as an amendment (non-blocking for design revision), but **must arrive before OBS-A1** because retention/ingestion findings directly determine D1/D2 viability.

## 1. Objective and scope

Produce a **truthful `consumer_evidence.runtime_logs` overlay** for exactly the three Phase-8R-ratified cohort views —
`public.v_active_tasks`, `public.v_agent_dashboard`, `public.v_pending_handoffs` — by **forward observation**, because
Phase 9A established (and Phase 9A-CAP confirmed) that historical direct-SQL read evidence does not exist:
`log_statement=ddl`, `log_min_duration_statement=-1`, pgAudit inactive, and the accessible log surface cannot reach a
window bracketing the current census instant.

Two tiers. **Tier A (preferred, §4): no-reset `pg_stat_statements` baseline/delta plus bounded API-gateway logs** — zero
production mutation. **Tier B (escalation only, §5): narrowly scoped pgAudit read telemetry** — production writes behind
separate enable/restore GOs. This document authorizes NOTHING; every execution step maps to its own future GO (§8).

Out of scope: the other five overlay dimensions' collection procedures (their existing runbook rows govern — but §3
imposes the window-coordination and truthful-start requirements they must satisfy), the fresh census procedure itself
(CENSUS_RUNBOOK governs; this design fixes only its TIMING), and any disposition decision.

## 2. Grounding

Tiers of grounding used here, labeled throughout:
- **(a) census/9A-CAP-observed facts** — read-only observations of prod `fxoyniqnrlkxfligbxmg` on 2026-07-13 (~20:10Z):
  `log_statement=ddl` (config file); `log_min_duration_statement=-1`; `log_connections=off`; `log_duration=off`;
  pgAudit **library preloaded** in `shared_preload_libraries` but **extension NOT installed** (available 17.1) and inactive
  (`pgaudit.log=none`, `pgaudit.role` empty); `pg_stat_statements` **1.11 installed + preloaded**, `stats_reset
  2026-05-31T03:10:51Z`, 4,867 tracked of `pg_stat_statements.max=5000` (**near eviction cap**); cohort name-match
  telemetry 3 entries / 3 calls per view (unattributed by design; see §7 for what CAN have produced these).
- **(b) repo facts at `GATE_SHA`** — `OVERLAY_COLLECTION_RUNBOOK.md`, `overlay.schema.json`, `author_overlay.py` /
  `verify_overlay_artifact.py` contracts; the census collector's catalog-only query surface (verified as a repo fact in
  the OBS-CENSUS preflight, §8).
- **(c) policy anchors** — per-phase GO discipline; value-silence; `APPROVED_CUSTODY_SCHEMES = {vault, infisical}`;
  operator findings of 2026-07-13 (no `pg_stat_statements_reset()`; eviction fail-closed; support response = input, not
  prerequisite).
- **(d) PostgreSQL-semantic inferences**, labeled `(PG-inference)`. Any (d) claim load-bearing at execution time carries
  a **verify-at-execution preflight** in §8. Key (d) claims used: `pg_stat_statements` visibility masking for
  non-`pg_read_all_stats` viewers; per-entry `stats_since` = entry-creation time, while `minmax_stats_since` = last
  minmax-only reset time (initially equal — the two are NOT synonyms; new-entry corroboration pins to `stats_since`
  exclusively); `pg_stat_statements_info` (`dealloc`, `stats_reset`) lives in shared memory and is NOT persisted across
  server starts (clean restart re-initializes `stats_reset`/`dealloc`; entries survive a clean shutdown only if
  `pg_stat_statements.save=on`; a crash empties the store); a targeted `pg_stat_statements_reset(userid, dbid, queryid)`
  moves NEITHER `stats_reset` NOR `dealloc`; queryid stability is not guaranteed across server versions and hashes
  relation OIDs (view DROP+CREATE changes queryids); pgAudit object-audit mechanics (§5).

Pin vocabulary (fixed 2026-07-13): `GATE_SHA` (origin/main, re-derived at every GO; `8678f30e` at authoring),
`BASE_SNAPSHOT_SHA256` / `CENSUS_REPO_SHA` / `QUERY_BUNDLE_SHA256` / `CENSUS_OBSERVED_AT` — after the fresh census
(§4.2) these four re-pin to the NEW census; the current `52962abe…` census remains valid for the merged Phase-8
reconciliation but is superseded for overlay binding.

## 3. Timeline invariant and window discipline

```
T0 = Tier-A baseline snapshot (read-only)            ── window opens
T1 = fresh signed census (CENSUS_OBSERVED_AT_new)    ── T0 < T1
Tobs = operator-approved observation interval        ── opens only after the census is signed
Tend = end snapshot + bounded API-log export         ── window closes; T0 < T1 < Tend
```

**Clock source:** `T0` and `Tend` are the database `now()` values returned INSIDE the OBS-A1/OBS-A2 snapshot
transactions. API-export bounds are **outward with a strict margin**: `API_start ≤ T0 − δ` and `API_end ≥ Tend + δ`,
δ ≥ the recorded cross-clock skew bound (zero margin would let skew exclude boundary events); exported events are then
normalized (clipped) to `[T0, Tend]` at assembly time, with boundary-clipped events retained as annotations. All clock
readings are recorded in the source record so skew is inspectable.

The runtime_logs overlay's `observation_window` is **[T0, Tend]** — truthful because the baseline/delta method measures
exactly that span; with `started_at = T0 < T1` and `ended_at = Tend > T1`, OV017 bracketing holds by construction.

**Window-coordination for the other three consumer dimensions** (`static_repo`, `external_clients`,
`operator_declaration`): each needs `started_at ≤ T1 ≤ ended_at`. A point-in-time collection at Tend does NOT truthfully
support `started_at ≤ T1` by itself — each dimension needs a stated **truthful-start basis**:
- `static_repo`: scan pinned at the new `CENSUS_REPO_SHA`, plus git evidence that the scanned surfaces have no relevant
  diff between that SHA and the ref at scan time — widening the truthful window to [T1, Tscan]. (Scanning at both T1 and
  Tend is the fallback.)
- `external_clients`: change-evidence (config history / platform evidence / attestation) that the client inventory did
  not change over [T1, Tscan].
- `operator_declaration`: the attestation TEXT must explicitly cover the interval [≤ T1, Tend], not merely be signed at
  Tend.
The Phase-10 assembly produces a one-page window table with a **truthful-start-basis column per dimension** and checks:
OV009 (`started_at < ended_at ≤ captured_at`, where `captured_at` = that dimension's collection/authoring completion
time — for runtime_logs, the OBS-A2/export completion or later); OV011/OV017 (S = max(started) ≤ T1 ≤ E = min(ended),
non-empty); OV016 (preapply within 720 h of the earliest `ended_at`); OV022 (the `in_data_api_exposed_schema` window
must COVER [S, E] — formally binding for delete-disposition cases). **`in_data_api` interval coverage is made truthful
by capturing the exposure posture at BOTH ends of the interval and citing the §4.3 posture freeze + F7 no-interference
result; a single-instant capture may not claim interval coverage.**

**Never backdate:** no window may start before its evidence source actually covers — T0 is the earliest truthful start
for Tier-A SQL evidence; API-log bounds are whatever the export's verified bounds prove; the truthful-start bases above
are the only sanctioned ways a later collection reaches back.

## 4. Tier A (preferred) — no-reset `pg_stat_statements` baseline/delta + bounded API-gateway logs

### 4.1 Baseline snapshot (read-only GO "OBS-A1")
Captured via the authorized governed-prod SQL surface, SELECT-only, value-silent:
1. **Visibility preflight (gates everything; F9):** assert the executing role has cross-role statistics visibility —
   `pg_has_role(current_user, 'pg_read_all_stats', 'member')` (or superuser) — AND value-silent counts of tracked
   entries that are unreadable by the ILIKE filter each equal zero: `query = '<insufficient privilege>'`,
   `queryid IS NULL`, **and `query IS NULL`**. `(PG-inference: without pg_read_all_stats, other roles' entries are
   silently masked; separately, PostgreSQL may DISCARD stored query texts — e.g. query-text-file garbage collection —
   leaving NULL text with live queryid+counters; ILIKE against NULL matches nothing, so either condition silently
   under-selects with no error, identically at both snapshots.)` Re-asserted at OBS-A2.
2. **Reset-capability surface capture (feeds F10):** enumerate, value-silently, the full reset-capable closure at both
   snapshots: {roles holding EXECUTE on the `pg_stat_statements_reset` function family per `pg_proc` ACLs} ∪ {the
   transitive `pg_auth_members` closure of those roles} ∪ {all `rolsuper` roles} ∪ {the functions' `proowner`}
   `(PG-inference: superusers and owners execute regardless of ACL; grants reach every member)`. This does not detect
   an invocation (reset calls are SELECTs and are not logged under `log_statement=ddl`); it bounds WHO could have
   reset. F10's third leg (window DDL-log sweep) covers TRANSIENT capability: GRANT/REVOKE/role-DDL touching the reset
   family or reset-capable roles is DDL-classified and lands in the postgres log stream under the already-on
   `log_statement=ddl` `(PG-inference; §8 preflight)` — sweep it for the window.
3. **Environment capture (both snapshots; feeds F4):** `stats_reset` + `dealloc` (`pg_stat_statements_info`);
   tracked-entry count; `pg_stat_statements.max`; `pg_stat_statements.track`; `pg_stat_statements.track_utility`;
   `pg_stat_statements.save`; `compute_query_id`; `server_version`; installed `pg_stat_statements` extension version;
   `pg_postmaster_start_time()`; re-assert `shared_preload_libraries` contains `pg_stat_statements`.
   **Acceptance set:** `compute_query_id IN ('on','auto')` passes ('auto' is valid because the library is confirmed
   preloaded); `'off'`/`'regress'` or `track = 'none'` ⇒ fail closed before starting. `track_utility` must be captured
   and handled: `'on'` ⇒ utility entries are tracked and the §4.4 classification governs them; `'off'` ⇒ proceed ONLY
   with a mandatory stated-limit line added to §4.4 (utility-wrapped reads — `COPY (SELECT …)`, `DECLARE CURSOR` — are
   wholly untracked `(PG-inference)`).
4. **Cohort entries** (filter server-side on `query ILIKE` any of the three names; output **never includes query
   text**): `dbid`, `userid` (numeric) + `rolname` via join, `queryid`, `toplevel`, `calls`, `rows`, `stats_since`,
   **`minmax_stats_since`** (required by the F3 comparison), a server-side, value-silent **class flag** per entry
   (**read-shaped = first significant keyword ∈ {SELECT, WITH, TABLE, VALUES, "("}**; anything else = utility-shaped —
   a prefix-only `select%` test would misclassify CTE and parenthesized reads), and **three server-side per-view match
   booleans**
   (`matched_v_active_tasks`, `matched_v_agent_dashboard`, `matched_v_pending_handoffs` — one per cohort view name)
   so the §4.4 per-view `found_consumers(V)` attribution, including multi-view statements, is computable from the
   snapshot alone. Flags and booleans are exported, never the text.
5. **Per-view object-state capture (feeds F7 + the name-indirection limit):** for each of the three views,
   `pg_class.oid`, an md5 of `pg_get_viewdef()`, `relacl`, AND the `pg_depend` dependents (wrapper views/rules reading
   the cohort views) — captured identically at OBS-A2; any oid/viewdef/relacl inequality trips F7. Any dependent
   wrapper found either has its name ADDED to the ILIKE match set or is named in the §4.4 stated limits — a wrapper
   read is tracked at `track=top` under the WRAPPER's name and would otherwise silently evade the cohort filter while
   passing every F9 predicate. `(PG-inference: queryid hashes relation OIDs, so DROP+CREATE splits post-DDL traffic to
   new queryids — oid capture is what makes F7 detectable.)`
6. **Self-noise post-check (§8 preflight):** after the capture, re-run the filter and assert the snapshot's own
   statement did not enter the matched set `(PG-inference: its ILIKE literals normalize to $N)`.
7. Baseline artifact: one JSON snapshot, hashed, stored out-of-repo; raw copy (including `rolname` values) under
   `vault:`/`infisical:` custody. Committed source records carry redacted role *classes* (e.g. "service role",
   "operator role"), never role names, unless the operator declassifies.

**No `pg_stat_statements_reset()` anywhere in this packet** — full, targeted, or minmax-only (operator finding 2). The
baseline/delta method needs none.

### 4.2 Fresh signed census (GO "OBS-CENSUS", CENSUS_RUNBOOK verbatim)
Run AFTER OBS-A1 completes, from clean merged main; new `BASE_SNAPSHOT_SHA256`/`CENSUS_OBSERVED_AT`; published +
merged per the Phase-6/7/7M pattern. All six Phase-9 overlays bind to THIS census. Preflight (repo fact): verify the
collector's query surface at `GATE_SHA` touches catalogs only; if any query selects from the cohort views, it must be
logged as a controlled consumer instead.

### 4.3 Observation interval (passive; exceptions rule below)
- **Duration**: operator decision (§9 D1). Lean: **7 days**. Longer windows raise BOTH eviction exposure (F2/F3) AND
  the probability of a routine platform restart tripping F1 `(PG-inference: any server start re-initializes
  stats_reset — the observed 2026-05-31 value plausibly marks the last restart, i.e. ~6 weeks between restarts, but
  Supabase maintenance can restart within any week)`. The **churn-rate viability estimator**: the `dealloc` difference
  between OBS-A0 and OBS-A1 (readings days apart) projects eviction risk over the candidate duration — if the
  projection is nonzero, pick the shorter window or pre-stage Tier B.
- **Controlled-consumer discipline**: during [T0, Tend], deliberate queries naming the cohort views are **prohibited by
  default**. Exceptions: an exception executed by the operator (or a third party the operator directs) requires a
  controlled-consumer log entry; an exception executed by the executor/agent additionally requires its own operator GO.
  Every exception (i) is logged one-line-each (who/when/surface/purpose) and (ii) **executes under a dedicated marker
  role** so it lands in `pg_stat_statements` under a distinct `userid` — decomposition of deltas is then BY KEY, not by
  arithmetic subtraction. **Zero-write realization:** Tier A creates no roles. Exceptions are PROHIBITED unless an
  existing suitable marker role (distinct from every serving role, usable by the operator) is verified at the OBS-A1
  preflight; if none exists, creating one is a separate production-write GO ("OBS-MARKER-ROLE") that must land BEFORE
  T0 — with no such role and no such GO, the prohibition is absolute and any deliberate cohort query during the window
  is an F8 trip. Raw ledger entries (real identities) go under `vault:`/`infisical:` custody; the committed source
  record carries redacted role classes per the §4.1 rule, preserving the one-line-per-exception structure.
- Known self-noise needing no ledger entry: the snapshot queries themselves (§4.1 item 5 verifies) and the census
  collector (§4.2 preflight verifies — a repo fact, not an inference).
- **Platform posture freeze**: no grant/DDL/exposure changes to the three views during [T0, Tend] (would confound the
  census, the deltas, and the `in_data_api` interval-coverage argument); the lane holds A1–A3 anyway. F7 verifies.

### 4.4 End snapshot + delta (read-only GO "OBS-A2")
Same captures as OBS-A1 (visibility preflight re-asserted), plus delta computation per identity
`(dbid, userid, queryid, toplevel)`:
- Surviving identities: require `stats_since` unchanged AND `calls_end ≥ calls_base` (else F3); delta = `calls_end −
  calls_base`.
- New identities: `stats_since ≥ T0` corroborates window-created entries (pinned to `stats_since` exclusively; a changed
  `minmax_stats_since` on a baseline identity is treated as a partial-reset indicator ⇒ F3).
- **Classification before counting:** only read-shaped entries (class flag, §4.1 item 4) count toward consumers;
  utility-shaped matches (e.g. EXPLAIN) are reported as annotated window events; DDL-shaped matches double as F7
  signals. **Every annotated window event must be explicitly adjudicated (consumer / not-consumer, with basis) before
  an ACCEPTED zero-consumer conclusion** — an unadjudicated annotation blocks acceptance.
- **`found_consumers` is defined PER VIEW** (assignments are keyed by `object_id`): for view V,
  `found_consumers(V) = |distinct (userid, queryid) with positive uncontrolled read-shaped call-delta among entries
  whose normalized text matches V's name| + |distinct API-client identities with ≥ 1 request touching V in [T0, Tend]
  per §4.5|`. An entry or request matching multiple cohort views counts toward EACH matched view. SQL-side and API-side
  identities are NOT deduplicated across components (a PostgREST request also lands in `pg_stat_statements` under the
  authenticator role): `found_consumers` is therefore a deliberate, declared **upper bound** on distinct consumers. A
  cross-view aggregate may appear in the source-record summary but is never an assignment value. Any delta key
  containing BOTH controlled (marker-role) and unattributed calls cannot occur by construction (distinct userid); if a
  non-marker key's delta is partially explained by a ledger entry that failed to use the marker role, the WHOLE delta
  counts as uncontrolled (resolves toward `found_consumers > 0`) and F8 additionally trips for ledger-discipline
  failure.
- **Selective-reset epistemic cap (F10):** a targeted `pg_stat_statements_reset(userid, dbid, queryid)` against an
  identity CREATED AFTER T0 erases that identity before Tend while moving neither `stats_reset` nor `dealloc` — it is
  invisible to F1–F3 by construction `(PG-inference: only a full discard updates the global stats_reset)`, and its
  invocation is unloggable under `log_statement=ddl` (reset calls are SELECTs). Tier A therefore may NOT produce an
  **accepted zero-consumer conclusion** unless selective reset is excluded for the window to the extent it CAN be: (i)
  the §4.1 item-2 reset-capable CLOSURE (ACL ∪ role-membership ∪ superusers ∪ owner) is unchanged between snapshots;
  (ii) the window DDL-log sweep shows no GRANT/REVOKE/role-DDL touching the reset family or reset-capable roles; and
  (iii) a signed operator attestation states that **no principal under operator control, direction, or knowledge**
  invoked any reset during [T0, Tend]. Platform-side principals (e.g. `supabase_admin`, Supabase automation, the
  Studio Query-Performance reset control — that one is full-scope and F1-caught, but it demonstrates platform reset
  surfaces exist) are OUTSIDE the attestation's epistemic reach: until the §10 support answer addresses
  platform-invoked resets, even the attested path carries a residual platform-actor line in the accepted-zero record.
  Absent (i)–(iii), a zero result is reportable only as "0 observed; selective reset not independently excluded" and
  cannot support an accepted delete/harden decision on its own (F10).
- **Stated instrument limits carried in the source record:** normalized-literal blindness; `track=top` nesting
  blindness; the near-cap eviction regime; **any name-indirect read** — wrapper views/rules (tracked, but under the
  wrapper's name; mitigated by the §4.1 item-5 `pg_depend` sweep), SQL-level `PREPARE`/`EXECUTE` (attribution
  semantics = §8 preflight), function-mediated reads (PostgREST `/rest/v1/rpc/<fn>`, `pg_cron`, app functions —
  invisible to BOTH instruments: the URL lacks the view name and the nested SELECT is untracked at `track=top`);
  utility-wrapped reads if `track_utility=off` (§4.1 item 3); and **ingestion liveness proven only at sentinel cadence
  on the sentinel path — sampled or load-shed loss correlated with traffic bursts is not excluded** (the pgss
  instrument, which has no ingestion pipeline, is the volume-insensitive cross-check). (Tier B's object-level audit IS
  executor-level and does catch nested reads of granted views — part of the escalation rationale.) A zero result is
  reportable ONLY if every §6 condition passed — and even then the overlay reports "0 observed under the stated
  instruments and window", never "no consumers exist".

### 4.5 Bounded API-gateway log component (same window, verified bounds AND completeness)
Purpose: HTTP/Data-API consumers that SQL telemetry cannot fully attribute, and vice-versa (subject to the joint blind
class above).
- **Filter**: the **full request URL including query string** (and request body for POST-with-select variants where the
  log surface records it) — a path-only filter misses PostgREST **embedded reads**
  (`/rest/v1/<other>?select=...,v_active_tasks(...)`) where the view name appears only in the query string. Per-view
  attribution follows the matched name.
- **Surface** (§9 D2): lean = **operator-run Logs Explorer SQL export** over `edge_logs` with explicit
  `iso_timestamp_start/end`; alternative = Management-API analytics endpoint with an operator-injected
  `SUPABASE_ACCESS_TOKEN` via `inject.sh` (new credential path; needs explicit approval).
- **Completeness requirements (F6 — bounds alone are NOT enough; all clauses evaluate at the STITCHED-UNION level when
  harvesting in slices):** (i) verified **outward** bounds with a strict skew margin — `API_start ≤ T0 − δ`,
  `API_end ≥ Tend + δ`, where δ ≥ the recorded cross-clock skew bound (with zero margin, skew CAN exclude a boundary
  event) — evaluated over the UNION of slice bounds; events are normalized to [T0, Tend] at assembly, and
  boundary-clipped events are retained as annotations rather than dropped; (ii) extract-completeness evidence —
  per-slice returned row count strictly below the export/row cap (Supabase documents a 1,000-row result cap on Logs
  Explorer results), or exhaustive-pagination proof, plus a count-query cross-check computed per-slice-then-union;
  (iii) a **retention-horizon check at each export** — each slice's retention horizon must be earlier than that
  SLICE's start (a whole-window `horizon ≤ T0` test would wrongly block the exact stitched-harvest scenario the next
  clause mandates); (iv) when the D1 duration approaches the (known or unknown) retention horizon, schedule
  **intermediate harvests** (e.g. daily or mid-window): adjacent slices must OVERLAP with verified continuity,
  deduplicated on a named key (the `edge_logs` event id; else timestamp + request id); (v) **log-ingestion liveness
  sentinels** — extract completeness proves completeness relative to the Logs Explorer dataset, NOT that every request
  reached that dataset (this project just experienced an API-log backend failure). **Sentinel spec:** each sentinel is
  a PostgREST **data-path** request — `GET /rest/v1/<dedicated non-cohort relation>?marker=<uuid>` — so it traverses
  the SAME service route and lands in the SAME log dataset as cohort-relevant traffic and is recovered via the SAME
  export query template (a health/auth-endpoint sentinel proves nothing about the data path). Marker = fresh UUID in
  the URL query string (the field the full-URL filter reliably records). Issuance ledger per sentinel: issue
  timestamp, marker, HTTP response status (a client-side send failure is ledgered as such — still blocking, but
  classified distinctly from ingestion loss). Recovery predicate: the marker appears in the exported rows within a
  stated timestamp tolerance. Denominator = the issuance ledger against the D1-fixed schedule (a silently-unissued
  sentinel is itself a ledger gap ⇒ F6). Sentinels are issued at window start, periodically (cadence fixed in D1), and
  at window end; EVERY scheduled sentinel must be ledgered AND recovered, else F6 blocks. Sentinels bound sustained
  outages at cadence granularity only — the volume-correlated-loss residual is a §4.4 stated limit. Any requirement
  unmet ⇒ F6.
- If the pending support response recovers 2026-07-13 API history, that recovery only ever ADDS an earlier-window API
  annex to the source record; it cannot substitute for [T0, Tend] SQL evidence (operator finding 1).

### 4.6 Evidence assembly (feeds the eventual Phase-9 runtime_logs GO)
Normalized, redacted source record = {baseline snapshot digest, end snapshot digest, per-view delta table (counts +
class flags only), controlled-consumer ledger (redacted role classes), API-log extract with bounds + completeness
evidence, clock readings, fail-closed checklist results, stated instrument limits}. Raw un-redacted material under
`vault:`/`infisical:` custody, referenced per runbook §1/§4. Author via `author_overlay.py` with the runbook §4 pins
(NEW census; `--producing-repo-sha-na-reason` since runtime_logs forbids a producing SHA), window `[T0, Tend]`,
`captured_at` = OBS-A2/export completion or later, validate-before-sign, `verify_overlay_artifact.py` GREEN,
secret-scan — all under that future GO, not this design.

## 5. Tier B (escalation only) — narrowly scoped pgAudit read telemetry

**Trigger criteria (any):** (1) **two consecutive Tier-A attempts tripped by F2/F3** (eviction/interference), or an
explicit operator declaration that Tier A is exhausted; (2) the operator requires statement-time attribution that
counters cannot give; (3) a disposition decision needs per-session evidence. Criteria 2–3 are operator-initiated by
definition. Tier B is NOT entered by default.

- **Census rebind on entry (structural):** Tier-B triggers fire at/after OBS-A2 — after the OBS-CENSUS census — so a
  Tier-B audit window cannot bracket that census instant. **Tier-B entry requires a full §3 re-run**: pgAudit enable
  defines a new T0; a NEW fresh signed census (re-pinning `BASE_SNAPSHOT_SHA256`/`CENSUS_OBSERVED_AT`) is taken inside
  the audit window; ALL SIX overlays re-bind to that new census. This second census+publish cycle is a real cost —
  priced into decision D4.
- **Mechanism `(PG-inference; verify at enable)`:** object-scoped audit via `pgaudit.role` — create a NOLOGIN marker
  role (e.g. `disposition_audit`), `GRANT SELECT ON` **only the three cohort views** to it, and set `pgaudit.role`
  **database-wide** (`ALTER DATABASE ... SET`) so it applies to sessions of ALL serving roles — NOT per-role (`ALTER
  ROLE <r> SET` audits only that role's sessions) and NOT global `pgaudit.log=read` session logging (unbounded volume).
  pgAudit's object audit is executor-level: it catches nested/function-mediated reads of the granted views — closing
  Tier A's joint blind class.
- **Propagation `(PG-inference; enable-preflight)`:** `ALTER DATABASE ... SET` affects **new sessions only**. Long-lived
  pooled backends (PostgREST/Supavisor pools, pg_cron workers) keep the old empty setting indefinitely — precisely the
  standing consumers Tier B exists to observe. The OBS-B-ENABLE GO must therefore (i) verify effectiveness across ALL
  serving backends (compare `pg_stat_activity` session starts against the enable time) and (ii) include an explicitly
  GO-gated pool-recycle / backend-termination step (a disruption line-item in that GO). **The Tier-B window opens only
  when the oldest surviving backend postdates enable.** Tier-B fail-closed row: any backend observed with a pre-enable
  session start and no audit coverage ⇒ a Tier-B zero is not reportable.
- **Prod-write inventory (all inside GO "OBS-B-ENABLE"):** `CREATE EXTENSION pgaudit` (library already preloaded per
  9A-CAP ⇒ no restart expected; verify), marker role, three grants, the database-wide `pgaudit.role` setting (SUSET —
  the exact Supabase-permitted mechanism is a verify-at-enable preflight; if the managed `postgres` role cannot set it,
  Tier B is BLOCKED, not worked around), `pgaudit.log_parameter` stays off. The GO text must explicitly acknowledge
  that pgAudit captures statement TEXT into the postgres log stream as a **bounded, custody-handled exception** to the
  never-emit rule (§11).
- **Volume estimate:** proportional to actual cohort reads (expected near-zero given Phase-8 static evidence); logs
  land in the plan-retention-bound postgres log stream.
- **Best-effort boundary (fail-closed):** pgAudit is documented as best-effort — it does not guarantee every committed
  statement leaves a durable audit record (see the pgAudit caveats). A Tier-B zero is therefore subject to the same
  liveness discipline as §4.5: periodic **audited-read sentinels** (marker-role SELECTs against the cohort views, each
  ledgered as controlled) must EACH appear in the harvested audit stream; any missing sentinel ⇒ the Tier-B window
  fails closed. The marker role thus serves double duty: controlled-consumer keying and audit-liveness probing.
- **Harvest:** mid-interval log harvest is a recurring, secret-bearing, production-log read — it has its own §8 row and
  GO (which may authorize a bounded recurring cadence, informed by the §10(iii) retention numbers). Committed record =
  redacted extract; raw under custody; parameters logging off.
- **Separate write design required:** per operator direction (D4), OBS-B-ENABLE may not be drafted from this section
  alone — Tier-B entry requires a dedicated write-design packet covering the best-effort boundary, sentinel reads, pool
  recycling, fresh-census rebinding, and restoration, reviewed before any enable GO.
- **Rollback/restore (GO "OBS-B-RESTORE", separate; limited to reverting to the 9A-CAP baseline):** harvest + redact
  residual logs first; clear `pgaudit.role`, revoke the three grants, drop the marker role, optionally `DROP EXTENSION
  pgaudit`; verify all settings match the 9A-CAP baseline.

## 6. Fail-closed matrix (Tier A; any row ⇒ BLOCKED, no negative conclusion, report and stop)

| # | Condition | Detected by |
|---|---|---|
| F1 | `stats_reset` differs between OBS-A1 and OBS-A2 | `pg_stat_statements_info.stats_reset` |
| F2 | `dealloc` **changed in either direction** over the interval | `pg_stat_statements_info.dealloc` baseline vs end |
| F3 | Per-identity integrity violated: any baseline cohort identity `(dbid, userid, queryid, toplevel)` missing at end, OR its `stats_since` changed, OR `calls_end < calls_base`, OR `minmax_stats_since` changed on a baseline identity | structured per-identity comparison (replaces any opaque row-set hash) |
| F4 | Any environment value changed between snapshots — `track`, `track_utility`, `save`, `compute_query_id`, `max`, `server_version`, pgss extension version, `pg_postmaster_start_time()` — or baseline values outside the §4.1 acceptance set | settings capture both ends |
| F5 | Snapshot query failure / surface unavailable | OBS-A1/OBS-A2 execution |
| F6 | Evaluated at the STITCHED-UNION level: union of slice bounds not outward-with-margin of [T0, Tend] (`API_start ≤ T0−δ`, `API_end ≥ Tend+δ`), OR per-slice extract completeness unproven (1,000-row cap / pagination / per-slice-then-union count cross-check), OR any slice's retention horizon later than that slice's start, OR slice overlap/continuity/dedup unverified, OR **any scheduled liveness sentinel unledgered or unrecovered** | §4.5 export inspection + sentinel ledger |
| F7 | Cohort-view object state changed during interval: `pg_class.oid`, `pg_get_viewdef()` md5, or `relacl` differs between snapshots (grant/DDL interference; also corroborable from the DDL log stream — `log_statement=ddl` is already on) | §4.1 item 5 capture both ends |
| F8 | Controlled-consumer ledger incomplete, an exception executed without the marker role (its key's delta then counts wholly as uncontrolled), or an exception occurred with no verified marker role in existence | operator attestation + marker-role audit at OBS-A2 |
| F9 | Executing role lacks cross-role statistics visibility (`pg_read_all_stats`), or ANY unreadable entry — `<insufficient privilege>`, `queryid IS NULL`, or **`query IS NULL`** (discarded text) — observed in either snapshot | §4.1 item 1 preflight, re-asserted at OBS-A2 |
| F10 | Selective-reset exclusion unavailable: the reset-capable CLOSURE (ACL ∪ role membership ∪ superusers ∪ owner) changed between snapshots, OR the window DDL-log sweep shows GRANT/REVOKE/role-DDL touching the reset family or reset-capable roles, OR the operator's scoped no-reset attestation ("no principal under operator control, direction, or knowledge") for [T0, Tend] is absent — an ACCEPTED zero-consumer conclusion is prohibited (zero reportable only with the §4.4 epistemic caveat; platform-actor residual carried until the §10 platform-reset answer) | §4.1 item 2 capture both ends + DDL-log sweep + operator attestation |

**Restart/crash analysis `(PG-inference; fail-closure holds under either persistence interpretation)`:** a clean
restart re-initializes `pg_stat_statements_info` ⇒ F1 trips (entries themselves survive if `save=on`); a crash empties
the statistics ⇒ F1 + F3 trip; an in-place version change ⇒ F4 trips (and queryids may re-hash — why F4 includes
versions and postmaster start time rather than relying on incidental F1/F3 coverage).

**Remediation direction:** if F2/F3 trip, the correct retry is a **SHORTER window** (e.g. 72 h) or a Tier-B escalation
decision — never a longer attempt (eviction probability grows with duration), never a loosened guard, never a reset.
Use the §4.3 churn-rate estimator before committing any retry duration.

## 7. Optional pre-step — attribution probe (read-only GO "OBS-A0", operator finding 4)

Before OBS-A1, optionally attribute the existing symmetric 3-entries/3-calls pattern: expose `rolname`, `queryid`,
`toplevel`, `calls`, `stats_since` for the current name-matching entries — **no query text**; `rolname` output goes
under custody per the §4.3 ledger rule. Interpretation note (attribution evidence, NOT definitive provenance):
constant-normalization makes it UNLIKELY that catalog/ILIKE-style tooling produced these entries — statements carrying
the view names as **identifiers** (actual SELECTs from the views, or utility statements naming them) are the expected
producers — but PostgreSQL notes that representative texts may retain constants in some circumstances (especially
under high deallocation churn), so the probe's output informs expectations only. `stats_since` dates the entries. The
probe also yields the first `dealloc` reading for the §4.3 churn estimator. It gates nothing.

## 8. GO map (nothing here is authorized by this design)

| Step | GO | Access | Prod writes | Artifacts |
|---|---|---|---|---|
| OBS-A0 attribution probe (optional) | own GO | prod read-only | none | probe output (custody) |
| OBS-MARKER-ROLE (only if §4.3 exceptions are wanted AND no suitable role exists) | separate WRITE GO, lands before T0 | prod write | one NOLOGIN-derived marker role | — |
| OBS-A1 baseline snapshot (+ start liveness sentinel) | own GO | prod read-only + one sentinel HTTP request | none | snapshot JSON out-of-repo + custody copy |
| OBS-CENSUS fresh census (+ publish/merge per 6/7/7M pattern) | own GOs | prod read-only | none | repo evidence (census triple) |
| observation interval (+ periodic liveness sentinels) | none (passive; exceptions per §4.3 rule; sentinel cadence fixed in D1 — operator-run or bounded standing authorization in the OBS-A1 GO) | sentinel HTTP requests only | none | controlled-consumer ledger + sentinel ledger (custody) |
| OBS-A2 end snapshot + delta (+ end liveness sentinel) | own GO | prod read-only + one sentinel HTTP request | none | snapshot + delta out-of-repo + custody copy |
| API-log export | operator-run (lean) or own GO (token path) | platform logs read-only | none | export + completeness + sentinel-recovery evidence (custody) |
| runtime_logs overlay author/sign | Phase-9 runtime_logs GO | none (offline + injected key) | none | out-of-repo overlay triple |
| remaining five overlays | five separate Phase-9 GOs | per runbook | none | out-of-repo overlay triples |
| OBS-B-ENABLE (escalation only) | separate WRITE GO | prod write | extension/role/grants/GUC + gated pool recycle | — |
| Tier-B log harvest (escalation only) | own GO (may authorize bounded recurring cadence) | platform logs read-only | none | redacted extracts + custody raw |
| OBS-B-RESTORE (escalation only) | separate WRITE GO | prod write | revert to 9A-CAP baseline only | residual harvest (custody) |

**Verify-at-execution preflights carried by their GOs:** cross-role statistics visibility + zero-unreadable-entries
(`<insufficient privilege>` / `queryid IS NULL` / `query IS NULL`) (OBS-A1, re-asserted OBS-A2); reset-capability ACL
surface capture (OBS-A1/OBS-A2, feeds F10); marker-role existence check (OBS-A1 — absent role ⇒ §4.3 exceptions
prohibited); `stats_since`/`minmax_stats_since` column presence and semantics (OBS-A1); `compute_query_id`/`track`
acceptance set incl. `track_utility` handling (OBS-A1); snapshot self-noise post-check (OBS-A1/OBS-A2); SQL-level
`PREPARE`/`EXECUTE` attribution semantics under pgss 1.11 (OBS-A1 — determines whether prepared reads surface under
the underlying statement text or a utility entry); GRANT/REVOKE/role-DDL classification under `log_statement=ddl`
(OBS-A1 — underpins the F10 DDL-log sweep); census-collector catalog-only verification (OBS-CENSUS);
Supabase-permitted mechanism for database-wide `pgaudit.role`, no-restart assumption, and all-backends propagation
(OBS-B-ENABLE — drafted only from the §5-mandated separate Tier-B write design).

## 9. Operator decision points (leans first)

- **D1 — interval duration (operator-directed sequencing; do NOT precommit):** run OBS-A0 first, obtain a meaningful
  churn sample AND confirmed log retention (support response or measured), then choose: **7 days ONLY if projected
  `dealloc = 0` over the window AND sentinel coverage is viable**; otherwise **72 h**, or STOP and reassess. The
  sentinel cadence is fixed with this decision.
- **D2 — API-log surface (operator-directed):** **operator-run Logs Explorer** with pinned query/count templates,
  outward bounds (`API_start ≤ T0`, `API_end ≥ Tend`), result-cap proof (documented 1,000-row cap), retention proof,
  and liveness sentinels — all per §4.5. The Management-API token path remains the fallback if Logs Explorer cannot
  satisfy those requirements.
- **D3 — OBS-A0 attribution probe (operator-directed):** run it, under its own read-only GO, with the corrected §7
  attribution framing (evidence, not definitive provenance).
- **D4 — Tier B (operator-directed):** keep COLD. If triggered, a **separate write design** is required first (§5),
  covering pgAudit's best-effort boundary, sentinel reads, pool recycling, fresh-census rebinding, and restoration —
  noting Tier-B entry costs a second census + publish cycle and re-binding of all six overlays.

## 10. Support-response fold-in (amendment path; NOT a design prerequisite — but an OBS-A1 gate)

The pending Supabase ticket (recoverability of 2026-07-13 `edge_logs` / statement logs; project-specific ingestion
loss; exact retention) folds in as an amendment when it arrives, and **must arrive before OBS-A1 executes** — its
retention and ingestion findings directly determine D1/D2 viability (window length, harvest cadence, sentinel
cadence): (i) recovered API history → optional historical annex to the source record, never a substitute; (ii)
confirmed ingestion loss → platform-reliability caveat on §4.5, may raise D2 to the token path with tighter bounds
verification and denser sentinels; (iii) retention numbers → bound the §4.5 intermediate-harvest cadence and D1
durations; (iv) **platform-invoked-reset question (add to the ticket thread):** whether Supabase platform principals
or automation ever invoke `pg_stat_statements_reset` (full or targeted) on this project — the answer bounds the F10
platform-actor residual that the operator attestation cannot reach. No section's SQL-side design depends on the
response (operator finding 1); design revision and review are never blocked on it.

## 11. Explicit prohibitions inherited by every execution GO

No `pg_stat_statements_reset()` — full, targeted, or minmax-only. No pgAudit installation/role/GUC change outside GO
OBS-B-ENABLE or GO OBS-B-RESTORE (restore limited to reverting to the 9A-CAP baseline). No census before OBS-A1
completes; the observation interval may not rely on any period before OBS-CENSUS completes (Tobs opens only after the
fresh census is signed). No overlay signing against the old census `52962abe…`. **No query text on any model-visible
or committed surface** (Tier B's statement-text capture into the custody-handled log stream is the sole bounded
exception, and only when its enable GO explicitly accepts it); no client identities in committed records (custody +
role-class redaction per §4.1/§4.3). No backdated windows (§3 truthful-start bases are the only reach-back). No
deliberate cohort queries during the interval except per the §4.3 exception rule. Signing key remains in Infisical
operator custody, injected child-only. Custody locators `vault:`/`infisical:` only. Any ambiguity, guard failure, or
drift ⇒ STOP.

## 12. Review record

**Rev 2** (`f7083c4a`): rev 1 (`d4766525`) was reviewed by a four-lens adversarial panel (pg-semantics, fail-closed,
window-coherence, governance — 31 findings: 4 critical, 11 important, 16 minor) and a Codex cross-engine pass (1 P2).
ALL folded; the load-bearing corrections: F9 statistics-visibility gate; partial-reset detection via per-identity
`stats_since` + call monotonicity in F3; F2 made directionless; restart/crash persistence analysis + expanded F4;
API-export completeness/retention-horizon requirements in F6; F7 made actually detectable (oid/viewdef/relacl capture);
per-view `found_consumers` partitioning (Codex P2 + panel convergence); marker-role controlled-consumer decomposition;
truthful-start bases for the other consumer dimensions; Tier-B database-wide scope, backend-propagation gating,
census-rebind-on-entry, harvest GO row, and restore-exception wording.

**Rev 3** (this revision): operator audit HELD ratification at rev 2 on six findings, all folded — **P1** F9 extended to
`query IS NULL` (PostgreSQL may discard stored texts while preserving queryid+counters; ILIKE misses NULL silently);
**P1** selective-reset epistemic cap: post-T0 identities can be created, called, and targeted-reset invisibly to
F1–F3, so an ACCEPTED zero-consumer conclusion now requires the F10 exclusion (reset-capability ACL surface stable +
signed operator no-reset attestation), else zero carries an explicit non-exclusion caveat; **P1** log-ingestion
liveness sentinels (extract completeness ≠ ingestion completeness — this project just saw an API-log backend failure):
non-secret non-cohort sentinels at start/periodic/end, every one recovered or F6 blocks, mirrored in Tier B as
audited-read sentinels against pgAudit's documented best-effort boundary; **P2** API bounds made OUTWARD
(`API_start ≤ T0`, `API_end ≥ Tend`, events normalized to [T0, Tend]) resolving the §3-vs-F6 contradiction; **P2**
marker-role zero-write realization (exceptions prohibited unless a suitable existing role is verified; creation =
separate OBS-MARKER-ROLE write GO before T0); **P3** OBS-A0 reframed as attribution evidence, not definitive
provenance. D1–D4 rewritten to the operator's direction (no precommitted duration; probe → churn + retention → 7 d
only if projected `dealloc=0` and sentinel-viable, else 72 h or stop).

**Rev 3 focused round (this text):** the ordered focused cross-engine re-review ran over F9, selective resets, log
liveness, and window alignment. Codex: 2 findings (P1 `minmax_stats_since` missing from the §4.1 capture that F3
consumes; P2 per-view match booleans required for `found_consumers(V)`), both folded. Claude focused reviewer: every
rev-3 correction closes its named mechanism; 12 adjacent residuals (9 important, 3 minor, 0 critical), all folded —
name-indirect reads (pg_depend dependent sweep + widened stated limits + PREPARE/EXECUTE preflight); read-shape
classifier fixed (first-keyword set, not `select%` prefix) + mandatory adjudication of annotated events before an
accepted zero; `track_utility` added to the acceptance set; reset-capable CLOSURE widened (ACL ∪ membership ∪
superusers ∪ owner) + F10 DDL-log-sweep third leg + attestation scoped to operator reach with a platform-actor
residual and a §10 platform-reset ticket question; sentinels pinned to the PostgREST data path with a full issuance/
recovery spec; volume-correlated-loss residual added to stated limits (pgss = the volume-insensitive cross-check); F6
restated at the stitched-union level (resolving the rev-3-introduced contradiction with §4.5(iv) harvesting) with
per-slice retention checks, overlap/dedup keys, and outward-with-margin bounds (δ ≥ recorded skew).
