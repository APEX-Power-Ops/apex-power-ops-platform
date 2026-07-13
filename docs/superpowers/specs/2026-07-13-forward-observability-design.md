# Forward-observability packet — design (Phase 9A-OBS-DESIGN), rev 4

2026-07-13 · disposition-ledger lane · authored under operator GO "Phase 9A-OBS-DESIGN — design/spec only; no production access or mutation" · **stops for operator review.** Ratification was HELD at rev 3 on six findings (3 P1 / 3 P2); rev 4 closes them: the F10 zero-outcome **machine state** (`observed`/0 only under the full exclusion set, else `not_observed` + detail — never a prose-only caveat); the window DDL-log sweep demoted to one-way corroboration (`postgres_logs` completeness unproven); transitive dependent-closure digests in F7 plus a transient-DDL exclusion rule; ingestion-loss vs query-surface-failure routing; a valid pinned PostgREST sentinel; and the Logs Explorer dialect preflight — see §12. The pending Supabase support response folds in via §10 as an amendment (non-blocking for design revision), but **must arrive before OBS-A1**: its retention/ingestion findings determine D1/D2 viability, and its §10(iv) platform-reset answer is now LOAD-BEARING for any accepted zero (F10 leg (iii)).

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
   reset. TRANSIENT capability (mid-window GRANT/REVOKE/role-DDL touching the reset family or reset-capable roles) is
   DDL-classified and would land in the postgres log stream under the already-on `log_statement=ddl` `(PG-inference;
   §8 preflight)` — but that stream's WINDOW COMPLETENESS is unproven for this project (the 9A probe reached ~1h38m
   back; `postgres_logs` has no equivalent of the §4.5 liveness/completeness controls), so the window DDL-log sweep
   is **one-way corroboration only**: a sweep that SHOWS touching DDL is disqualifying (F10 trips), but a clean sweep
   proves nothing and is neither a sufficient nor a required exclusion leg. It may be upgraded to an evidence leg
   only if a `postgres_logs` completeness discipline mirroring F6 is established under the OBS-A1 GO (stitched
   slices, per-slice retention checks, and a verified ingestion-liveness basis for the postgres stream — candidate:
   the 9A-observed per-minute collation-warning heartbeat, itself a same-stream `(PG-inference / platform
   assumption)` to verify at execution). Transient-capability exclusion otherwise rests on the extended attestations
   in §4.4 (F10).
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
   `pg_class.oid`, an md5 of `pg_get_viewdef()`, `relacl`, AND the **transitive dependent closure** (recursive
   `pg_depend`/`pg_rewrite` walk: wrapper views/rules reading the cohort views, wrappers of wrappers, and so on),
   recorded as a canonical **closure digest** — a digest over the sorted list of (object identity, own
   `pg_get_viewdef()` md5 where applicable) — captured identically at OBS-A2; any oid/viewdef/relacl inequality OR
   closure-digest inequality trips F7. Any dependent wrapper found either has its name ADDED to the ILIKE match set
   or is named in the §4.4 stated limits — a wrapper read is tracked at `track=top` under the WRAPPER's name and
   would otherwise silently evade the cohort filter while passing every F9 predicate. `(PG-inference: queryid hashes
   relation OIDs, so DROP+CREATE splits post-DDL traffic to new queryids — oid capture is what makes F7 detectable.)`
   **Endpoint equality does NOT exclude mid-interval transients** (a wrapper created, queried, and dropped between
   snapshots enters neither endpoint closure and no name filter; a `CREATE OR REPLACE`→restore on a cohort view keeps
   its oid and endpoint viewdef equal) — the §4.4 transient-DDL exclusion rule governs zero outcomes.
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
  invocation is unloggable under `log_statement=ddl` (reset calls are SELECTs). Resets only ERASE evidence — they
  cannot fabricate calls — so F10 gates ZERO outcomes only; positive `found_consumers` stands regardless. The
  exclusion set: (i) the §4.1 item-2 reset-capable CLOSURE (ACL ∪ role-membership ∪ superusers ∪ owner) is unchanged
  between snapshots; (ii) a signed operator attestation that **no principal under operator control, direction, or
  knowledge invoked any reset OR changed reset capability (GRANT/REVOKE/role-DDL touching the reset family or
  reset-capable roles)** during [T0, Tend]; (iii) an **authoritative platform-side confirmation** — the §10(iv)
  support answer or an equivalent explicit Supabase statement — that no platform principal or automation invoked
  `pg_stat_statements_reset` (full or targeted) on this project during the window (platform reset surfaces
  demonstrably exist: the Studio Query-Performance reset control is full-scope and F1-caught, but it proves the
  class). The window DDL-log sweep is one-way corroboration per §4.1 item 2: touching DDL found ⇒ F10 trips; a clean
  sweep is neither sufficient nor required.
- **Zero-outcome MACHINE state (closes the rev-3 prose-caveat false green):** any epistemic caveat must be carried in
  the dimension record's `state` field, never in prose — `check_disposition.py` accepts every `observed`/0 dimension
  toward a resolved `no_consumer` conclusion regardless of surrounding text. Rule, in the `consumer_evidence_dim`
  vocabulary (`observed` ⇒ integer `found_consumers` + non-empty `ref`; any other state ⇒ `found_consumers: null`,
  `ref: null`, non-empty `detail`): with (i)+(ii)+(iii) all satisfied and every §6 row green, the runtime_logs
  dimension may be authored `state: observed, found_consumers: 0`. With (iii) missing but (i)+(ii) clean, it MUST be
  authored `state: not_observed` with `detail` = "0 observed under stated instruments; platform-side selective-reset
  exclusion unavailable" — never `observed`/0; under SP022 a resolved `no_consumer` conclusion is then impossible by
  construction, which is the intended fail-closed consequence. The same rule applies when (ii) is absent (detail
  names the missing operator attestation) and when the transient-DDL exclusion below is unavailable (detail:
  "transient dependent-closure exclusion unavailable"). Closure drift under (i) or touching DDL in the sweep is an
  interference SIGNAL ⇒ F10 BLOCKED outright (nothing authored; report and stop).
- **Transient-DDL exclusion (feeds F7; closes the wrapper interval-drift gap):** F7's endpoint comparison cannot see
  a mid-interval transient (§4.1 item 5). Exclusion requires ONE of: (a) trustworthy DDL evidence — the
  `postgres_logs` DDL stream for the window WITH the §4.1 item-2 completeness discipline established — showing no
  CREATE/ALTER/DROP touching the cohort views or their dependent closure; or (b) a signed operator attestation that
  no principal under operator control, direction, or knowledge executed such DDL during [T0, Tend]. Platform-side
  wrapper DDL is carried as a stated limit, not a machine gate (no known platform surface creates dependents on user
  relations — structurally unlike resets, where the Studio control demonstrates a platform surface). Absent both (a)
  and (b), a zero outcome follows the machine-state rule above (`not_observed` + detail). DDL evidence that SHOWS
  touching DDL ⇒ F7 BLOCKED.
- **Stated instrument limits carried in the source record:** normalized-literal blindness; `track=top` nesting
  blindness; the near-cap eviction regime; **any name-indirect read** — wrapper views/rules (tracked, but under the
  wrapper's name; mitigated by the §4.1 item-5 `pg_depend` sweep), SQL-level `PREPARE`/`EXECUTE` (attribution
  semantics = §8 preflight), function-mediated reads (PostgREST `/rest/v1/rpc/<fn>`, `pg_cron`, app functions —
  invisible to BOTH instruments: the URL lacks the view name and the nested SELECT is untracked at `track=top`);
  utility-wrapped reads if `track_utility=off` (§4.1 item 3); and **ingestion liveness proven only at sentinel cadence
  on the sentinel path — sampled or load-shed loss correlated with traffic bursts is not excluded** (the pgss
  instrument, which has no ingestion pipeline, is the volume-insensitive cross-check). (Tier B's object-level audit IS
  executor-level and does catch nested reads of granted views — part of the escalation rationale.) A zero result is
  authorable as `observed`/0 ONLY if every §6 condition passed AND the zero-outcome machine-state rule above
  authorizes it — and even then the source record reports "0 observed under the stated instruments and window",
  never "no consumers exist".

### 4.5 Bounded API-gateway log component (same window, verified bounds AND completeness)
Purpose: HTTP/Data-API consumers that SQL telemetry cannot fully attribute, and vice-versa (subject to the joint blind
class above).
- **Filter**: the **full request URL including query string** (and request body for POST-with-select variants where the
  log surface records it) — a path-only filter misses PostgREST **embedded reads**
  (`/rest/v1/<other>?select=...,v_active_tasks(...)`) where the view name appears only in the query string. Per-view
  attribution follows the matched name.
- **Surface** (§9 D2): lean = **operator-run Logs Explorer SQL export** over the project's **verified log dataset**
  with explicit `iso_timestamp_start/end`. **Dialect preflight first:** Supabase projects differ — newer projects
  default to a ClickHouse-backed shared `logs` table while older ones use BigQuery-style per-source tables such as
  `edge_logs` (supabase.com/docs/guides/telemetry/logs) — so D2 must identify the active dialect and VALIDATE the
  exact count/export/sentinel-recovery templates against it over a trivial bounded window before pinning them.
  Alternative = Management-API analytics endpoint with an operator-injected `SUPABASE_ACCESS_TOKEN` via `inject.sh`
  (new credential path; needs explicit approval) — an alternate QUERY surface over the SAME log store: it can remedy
  a dashboard/query-surface failure, never ingestion loss (events that never entered the store are unrecoverable by
  any client; mid-window ingestion loss surfaces as unrecovered sentinels ⇒ F6, and the remediation is a NEW window
  from a new T0 after platform remediation, per §6 — never a query-surface switch).
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
  deduplicated on a named key (the verified dataset's event id per the D2 dialect preflight — e.g. the `edge_logs`
  event id; else timestamp + request id); (v) **log-ingestion liveness
  sentinels** — extract completeness proves completeness relative to the Logs Explorer dataset, NOT that every request
  reached that dataset (this project just experienced an API-log backend failure). **Sentinel spec:** each sentinel is
  a PostgREST **data-path** request against a **pinned, preflight-verified target**: the D2/OBS-A1 preflight pins ONE
  Data-API-exposed non-cohort relation and one verified-existing, type-compatible column, yielding a VALID PostgREST
  read — canonical form `GET /rest/v1/<pinned_relation>?<pinned_column>=eq.<fresh-uuid>&limit=1`, where the fresh
  random UUID guarantees an empty result (a bare `?marker=<uuid>` is NOT generally a valid PostgREST filter, and a
  recovered 400/401 would prove routing, not the data path). The request traverses the SAME service route, lands in
  the SAME log dataset as cohort-relevant traffic, and is recovered via the SAME export query template (a health/
  auth-endpoint sentinel proves nothing about the data path). Marker = the fresh UUID in the URL query string (the
  field the full-URL filter reliably records). **Issuance success predicate: HTTP 2xx/206 with the expected
  empty-result body class** — a non-2xx response does NOT count as issued-and-serviced and is ledgered as a
  service-path failure (distinct class, still blocking); a client-side send failure is ledgered as such (also
  blocking, classified distinctly from ingestion loss). The pinning preflight (exposure + column existence + one
  successful probe request, itself ledgered) is read-only. Recovery predicate: the marker appears in the exported
  rows within a stated timestamp tolerance. Denominator = the issuance ledger against the D1-fixed schedule (a silently-unissued
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
`captured_at` = OBS-A2/export completion or later, **dimension state per the §4.4 zero-outcome machine-state rule**
(`observed`/0 only with the full F10 + transient-DDL exclusion set; else `not_observed` with `found_consumers: null`,
`ref: null`, and the required `detail`), validate-before-sign, `verify_overlay_artifact.py` GREEN,
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

## 6. Fail-closed matrix (Tier A; any tripped row ⇒ BLOCKED, no negative conclusion, report and stop — F10's missing-exclusion branch instead forces the §4.4 `not_observed` machine state)

| # | Condition | Detected by |
|---|---|---|
| F1 | `stats_reset` differs between OBS-A1 and OBS-A2 | `pg_stat_statements_info.stats_reset` |
| F2 | `dealloc` **changed in either direction** over the interval | `pg_stat_statements_info.dealloc` baseline vs end |
| F3 | Per-identity integrity violated: any baseline cohort identity `(dbid, userid, queryid, toplevel)` missing at end, OR its `stats_since` changed, OR `calls_end < calls_base`, OR `minmax_stats_since` changed on a baseline identity | structured per-identity comparison (replaces any opaque row-set hash) |
| F4 | Any environment value changed between snapshots — `track`, `track_utility`, `save`, `compute_query_id`, `max`, `server_version`, pgss extension version, `pg_postmaster_start_time()` — or baseline values outside the §4.1 acceptance set | settings capture both ends |
| F5 | Snapshot query failure / surface unavailable | OBS-A1/OBS-A2 execution |
| F6 | Evaluated at the STITCHED-UNION level: union of slice bounds not outward-with-margin of [T0, Tend] (`API_start ≤ T0−δ`, `API_end ≥ Tend+δ`), OR per-slice extract completeness unproven (1,000-row cap / pagination / per-slice-then-union count cross-check), OR any slice's retention horizon later than that slice's start, OR slice overlap/continuity/dedup unverified, OR **any scheduled liveness sentinel unledgered or unrecovered** | §4.5 export inspection + sentinel ledger |
| F7 | Cohort-view object state changed: `pg_class.oid`, `pg_get_viewdef()` md5, or `relacl` differs between snapshots, OR the **transitive dependent-closure digest** differs, OR available DDL evidence shows CREATE/ALTER/DROP touching the cohort views or their dependent closure during the window. Endpoint equality alone cannot exclude mid-interval transients — the §4.4 transient-DDL exclusion rule governs zero outcomes | §4.1 item 5 capture both ends + §4.4 transient-DDL rule |
| F8 | Controlled-consumer ledger incomplete, an exception executed without the marker role (its key's delta then counts wholly as uncontrolled), or an exception occurred with no verified marker role in existence | operator attestation + marker-role audit at OBS-A2 |
| F9 | Executing role lacks cross-role statistics visibility (`pg_read_all_stats`), or ANY unreadable entry — `<insufficient privilege>`, `queryid IS NULL`, or **`query IS NULL`** (discarded text) — observed in either snapshot | §4.1 item 1 preflight, re-asserted at OBS-A2 |
| F10 | **Interference signals ⇒ BLOCKED:** the reset-capable CLOSURE (ACL ∪ role membership ∪ superusers ∪ owner) changed between snapshots, OR the (corroboration-only) window DDL-log sweep shows GRANT/REVOKE/role-DDL touching the reset family or reset-capable roles. **Missing exclusions ⇒ machine-fail-closed, not BLOCKED:** absence of the extended operator attestation (§4.4 leg ii) or of the authoritative platform-reset confirmation (§4.4 leg iii) forces any zero outcome to `state: not_observed` + detail per the §4.4 machine-state rule; `observed`/0 requires legs (i)+(ii)+(iii) all satisfied | §4.1 item 2 capture both ends + attestations + §4.4 machine-state rule |

**Restart/crash analysis `(PG-inference; fail-closure holds under either persistence interpretation)`:** a clean
restart re-initializes `pg_stat_statements_info` ⇒ F1 trips (entries themselves survive if `save=on`); a crash empties
the statistics ⇒ F1 + F3 trip; an in-place version change ⇒ F4 trips (and queryids may re-hash — why F4 includes
versions and postmaster start time rather than relying on incidental F1/F3 coverage).

**Remediation direction:** if F2/F3 trip, the correct retry is a **SHORTER window** (e.g. 72 h) or a Tier-B escalation
decision — never a longer attempt (eviction probability grows with duration), never a loosened guard, never a reset.
Use the §4.3 churn-rate estimator before committing any retry duration. If F6 trips on **ingestion loss** (unrecovered
sentinels), the retry is a NEW window from a new T0 after platform remediation — switching query surfaces cannot
recover events that never entered the log store (§4.5).

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
(OBS-A1 — underpins the corroboration-only DDL-log sweep); `postgres_logs` completeness-basis assessment (OBS-A1 —
determines whether the DDL sweep can be upgraded from corroboration to an evidence leg, §4.1 item 2); Logs Explorer
dialect discovery + template validation (D2 — ClickHouse shared `logs` vs BigQuery-style `edge_logs`, §4.5);
sentinel-target pinning (exposure + column existence + one ledgered probe; D2/OBS-A1, §4.5);
census-collector catalog-only verification (OBS-CENSUS);
Supabase-permitted mechanism for database-wide `pgaudit.role`, no-restart assumption, and all-backends propagation
(OBS-B-ENABLE — drafted only from the §5-mandated separate Tier-B write design).

## 9. Operator decision points (leans first)

- **D1 — interval duration (operator-directed sequencing; do NOT precommit):** run OBS-A0 first, obtain a meaningful
  churn sample AND confirmed log retention (support response or measured), then choose: **7 days ONLY if projected
  `dealloc = 0` over the window AND sentinel coverage is viable**; otherwise **72 h**, or STOP and reassess. The
  sentinel cadence is fixed with this decision.
- **D2 — API-log surface (operator-directed):** **operator-run Logs Explorer** — dialect preflight FIRST (identify
  ClickHouse shared `logs` vs BigQuery-style `edge_logs`; validate the exact count/export/sentinel-recovery templates
  against the live dialect over a trivial bounded window), then pinned query/count templates, outward bounds
  (`API_start ≤ T0`, `API_end ≥ Tend`), result-cap proof (documented 1,000-row cap), retention proof, and liveness
  sentinels — all per §4.5. The Management-API token path remains the fallback for QUERY-SURFACE inadequacy only; it
  cannot remedy ingestion loss (§4.5).
- **D3 — OBS-A0 attribution probe (operator-directed):** run it, under its own read-only GO, with the corrected §7
  attribution framing (evidence, not definitive provenance).
- **D4 — Tier B (operator-directed):** keep COLD. If triggered, a **separate write design** is required first (§5),
  covering pgAudit's best-effort boundary, sentinel reads, pool recycling, fresh-census rebinding, and restoration —
  noting Tier-B entry costs a second census + publish cycle and re-binding of all six overlays.

## 10. Support-response fold-in (amendment path; NOT a design prerequisite — but an OBS-A1 gate)

The pending Supabase ticket (recoverability of 2026-07-13 `edge_logs` / statement logs; project-specific ingestion
loss; exact retention) folds in as an amendment when it arrives, and **must arrive before OBS-A1 executes** — its
retention and ingestion findings directly determine D1/D2 viability (window length, harvest cadence, sentinel
cadence): (i) recovered API history → optional historical annex to the source record, never a substitute; (ii) the
answer must DISTINGUISH query-surface failure from ingestion loss: a dashboard/query-surface failure may raise D2 to
the token path (an alternate query surface over the SAME store); CONFIRMED ingestion loss is unrecoverable by any
query surface — pre-T0 loss caveats the optional annex only, while loss overlapping a live or planned window ⇒ BLOCK,
wait for platform remediation, then restart from a NEW T0 (full §3 re-run including a fresh census, §4.2); (iii)
retention numbers → bound the §4.5 intermediate-harvest cadence and D1 durations; (iv) **platform-invoked-reset
question (add to the ticket thread):** whether Supabase platform principals or automation ever invoke
`pg_stat_statements_reset` (full or targeted) on this project — this answer is now LOAD-BEARING: F10 leg (iii)
requires it (or an equivalent explicit Supabase statement) before any `observed`/0 authoring of runtime_logs; absent
it, zero outcomes land `not_observed` per the §4.4 machine-state rule. No section's SQL-side design depends on the
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

**Rev 3 focused round:** the ordered focused cross-engine re-review ran over F9, selective resets, log
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

**Rev 4 (this revision):** operator review HELD rev-3 ratification on six findings (3 P1 / 3 P2), all folded. **P1**
F10's prose caveat still produced a machine-accepted zero (`check_disposition.py` accepts any `observed`/0 dimension
toward `no_consumer`) — closed by the §4.4 zero-outcome MACHINE-state rule: `observed`/0 requires closure stability +
the EXTENDED operator attestation (resets AND reset-capability changes) + an authoritative platform-side reset
confirmation (§10(iv), now load-bearing); any missing exclusion forces `state: not_observed` + `detail`
(`found_consumers`/`ref` null per `consumer_evidence_dim`), which SP022 makes non-green by construction; interference
signals still BLOCK outright. **P1** the transient-capability leg relied on unproven `postgres_logs` completeness —
the window DDL-log sweep is demoted to ONE-WAY corroboration (dirty sweep disqualifies; clean sweep proves nothing),
upgradeable to an evidence leg only behind an established `postgres_logs` completeness discipline (stitched slices +
per-slice retention + verified liveness basis). **P1** wrapper dependency discovery unprotected against interval
drift — §4.1 item 5 now captures the TRANSITIVE dependent closure as a canonical digest at both endpoints (added to
F7), and a transient-DDL exclusion rule (trustworthy DDL evidence under the completeness discipline, or a scoped
operator no-DDL attestation) governs zero outcomes, with platform-side wrapper DDL carried as a stated limit. **P2**
confirmed ingestion loss was mis-routed to the Management-API fallback — the token path now addresses QUERY-SURFACE
failure only; ingestion loss overlapping a live/planned window blocks and restarts from a new T0 + fresh census
(§4.5/§6/§10(ii)). **P2** the `?marker=<uuid>` sentinel was not a guaranteed-valid PostgREST read — replaced by a
pinned, preflight-verified relation/column with `?<col>=eq.<uuid>&limit=1`, an HTTP 2xx/206 + empty-result issuance
predicate, and marker recovery (non-2xx = service-path failure, still blocking). **P2** Logs Explorer dialect must be
discovered before pinning templates — D2 gains a dialect preflight (ClickHouse shared `logs` vs BigQuery-style
`edge_logs`) validating count/export/sentinel-recovery templates against the live dialect.

**Rev 4 focused delta round:** [to be recorded after the ordered focused delta review over the six rev-4 closures.]
