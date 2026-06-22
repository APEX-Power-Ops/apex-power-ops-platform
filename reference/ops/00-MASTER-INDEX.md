# APEX Operations (PM) Lane — Master Index & Re-Baseline

> **The single source of truth for the Operations / Project-Management lane.**
> This is the lane's orientation contract: where the PM domain actually *is*, the
> ratified target it converges toward, the laws that bind it, and the chip sequence
> that gets there. Every PM/ops chip cites and updates this file (the records-lane
> SSoT pattern). **Altitude is roadmap, not DDL** — per-chip schema design happens in
> each chip's own spec.

- **Status:** Chips 0–5 BUILT on `ops_test` (SSoT + identity + quote model + recognition ledger + progress billing + intake envelope; dev-only; operator-gated merge to main) · **nothing applied to prod**. Chip 5 **post-audit-hardened 2026-06-21**: an operator post-completion audit found 5 defects + the fix work exposed 1 latent `approve_run` bug — all fixed + regression-tested; a 2nd external (Codex) audit then found 6 more (finance leak via guard errors, patch_review races, content_type/FK/scope-name-leak boundary gaps) -- all fixed + tested (tip `2792be7c`).
- **Owner:** APEX Operations (PM) lane
- **Lane namespace (target):** `ops` (the Operations lane of `MASTER-SCHEMA.md`)
- **Supersedes (as forward plan):** `PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md`, `ERA_2_4_PACKET_B_*` (folded, not discarded — see §9)

---

## 1. Why this re-baseline exists (the ruling)

The PM domain went quiet on 2026-05-21. In the gap, the platform ratified a new
foundation — `MASTER-SCHEMA.md` (2026-06-14, "A + cheap seams", 7-reviewer audit) —
which **postdates every prior PM design doc** and was never reconciled against them.
The gather (2026-06-15) found that the master, while correct about the identity
foundation, **silently demoted the PM domain's operational entry point** (Estimator
intake + revenue recognition) to "growth-backlog," leaving the 5-phase intake
pipeline — the operator-confirmed reason the PM domain exists — with **no home in the
target schema**.

**Operator ruling (2026-06-15), which this lane is built on:**
1. **Elevate Estimator intake to first-class `ops`** (not growth-backlog).
2. **Revenue is hours-based at the apparatus grain, billed on binary apparatus completion** — each apparatus carries its labor hours plus the adders/external costs allocated down to a per-apparatus hour-value; recognition + progress billing follow actual completion (`=1`). (§5)
3. (Standing, un-contradicted) Keep the **`core` identity spine as foundation**; keep **P6/CPM scheduling in growth-backlog** but harvest its good ideas; **identity = Supabase `auth.users`**.

---

## 2. AS-IS — the verified reality (2026-06-15)

Distinguish ruthlessly between **live in governed prod** and **authored-but-not-applied**
(file-only migrations / design SQL). The records lane was bitten by treating migration
files as "applied"; the same trap is live here (`work.*` looks built, is not).

### 2a. LIVE in governed prod (`apex-power-ops` / `fxoyniqnrlkxfligbxmg`)

Verified via `information_schema` + `pg_class` row estimates this session.

| Schema | Tables | PM-relevant contents (live row estimates) |
|---|---|---|
| **`seam`** | 28 | The **heavy PM impl.** `apparatus` **184**, `assignments` 184, `tasks` 15, `workpackages` 7, `projects` 1; **`scopes` 0**, `apparatus_financials` 0, `apparatus_revenue_events` 0, `project_contract_snapshots` 0, `hours` 0. Infra: `idempotency_keys` 572, `audit_log` 392. Workflow custody (1 row each): `pm_import_candidate_approvals`, `pm_customer_delivery_events`, `pm_customer_preview_reviews`, `pm_customer_delivery_proof_reviews`, `financial_handoff_records`, `customer_completion_records`, `production_tracking_records`, `durable_field_records`. Identity: `users`/`user_roles`/`user_role_audit` 5 each. |
| **`public`** (PM core) | (subset of 75) | Lightly populated legacy concept: `projects` 1, `apparatus` 47, `apparatus_types` 87, `scopes` 4, `tasks` 12, `clients` 1, `sites` 1, `locations` 5, `employees` 5, `estimators` 2, `scope_labor_details` 6, `resource_assignments` 8; `project_financial_summaries`/`apparatus_revenue`/`scope_financial_summaries`/`equipment` 0. |
| **`schedule`** | 6 | P6/CPM stub: `projects` 1, `tasks` 4, `relationships` 3, `wbs_nodes` 3, `baseline_events` 1, `sync_log` 1. |

**Two live anomalies that *are* the design tension made physical:**
- **`seam.apparatus` = 184 rows, `seam.scopes` = 0 rows.** The revenue anchor (scope) is empty beneath the apparatus meant to bind to it — scope insert is blocked by a null `quoted_amount` in the frozen Lane 501 contract. The revenue model has never run end-to-end.
- **Two live apparatus identities** (`public.apparatus` 47 / `seam.apparatus` 184) + **three project identities** (`public`/`seam`/`schedule.projects`). This is the `MASTER-SCHEMA.md` §9 overlap, confirmed live.

### 2b. AUTHORED-BUT-NOT-APPLIED (file-only — NOT in prod)

| Artifact | What it is | Disposition |
|---|---|---|
| **`work.*`** (8 tables, 16 enums, views) + **`org.*`** (4 tables) + **`pm.idempotency_keys`** | The **April P6/CPM branch.** `work_package`-centric ("replaces legacy scopes"), full CPM scheduling (WBS, FS/SS/SF/FF deps + lag, early/late dates + float, P6 ids), normalized org (clients/sites/business-units/contracts), period-truth progress snapshots. Targets local `apex_pm_stage`; FKs to `org`/`identity`/`asset` are typed-but-deferred (D-010 style); `identity.*` referenced by `008` was never even authored. **No revenue, no Estimator intake.** | **Superseded** as the lane's primary model (`MASTER-SCHEMA.md` §9 calls `work` *"retired"*). **Harvest** org + work_package lifecycle vocab + provenance columns into `ops`; P6/CPM stays growth-backlog. |
| **`pm_core.*`** (3 tables + 4 enums) | **Packet B — design-only SQL, never created.** The intake-evidence envelope: `intake_runs` / `intake_source_files` / `intake_validation_findings`. Actor FKs → `auth.users`; cross-schema project refs nullable soft-UUID. Gated behind a "Packet A RLS" approval. | **Absorbed** — the seed of the `ops` intake substrate (Chip 2). The only authored intake substrate that exists. |

### 2c. The binding *contract* (resolved, but homeless)

`ESTIMATOR_ARCHITECTURE.md` (Phase A complete, operator-decision queue **empty**) is the
canonical PM **intake contract** — but it deliberately names **no target tables** ("intent
only, names assigned by future Era 2 substrate"). Its resolved laws are authoritative
requirements this lane must honor:
- Estimator `.xlsm` is the **import source of truth**; Excel owns compute; platform consumes **output cell values**, never reimplements formulas.
- Capture **P3** (unadjusted) + **P4** (adjusted = P3·M4·N4, operationally primary) + **M4** + **N4** per scope.
- Capture **labor hours** (per scope, split to apparatus) — the **revenue unit** (§5); live scaffolds `seam.hours` + `public.scope_labor_details`.
- **Apparatus→scope binding is FIXED** (the revenue-recognition anchor); PM has full authority over *task-level* groupings within a scope but **cannot move apparatus between scopes** ([[reference-pm-hybrid-intake-authority-2026-05-25]]).
- **5-phase workflow** (canonical): upload → extract → PM reviews/edits → approve → operational ([[reference-pm-project-intake-workflow-2026-05-25]]).
- `source_format` discriminator (`decomposed_scope_sheet` | `flat_quote` | `unsupported`) — reject not-yet-ready quotes at the boundary.

---

## 3. TO-BE — the amended `ops` target

The three models on the table are not a pick-one: they are different **concerns**, and the
master got the *ordering* half-right. The amendment is to elevate the operational heart.

| Concern | Model | Disposition in `ops` |
|---|---|---|
| **Identity** (apparatus-instance on the spine) | C — `MASTER-SCHEMA ops` | **Foundation, kept.** Apparatus-instance FKs `core.equipment_models` (soft-UUID now → hard FK at co-location). |
| **Intake + revenue** (scope-anchored, apparatus-grain, hours-based) | B — `seam` + `pm_core` | **Elevated to first-class `ops`** (the ruling). The 5-phase intake + hours-based binary-completion progress billing. |
| **Scheduling / execution** (work_package + CPM) | A — `work.*` | **Growth-backlog, deferred.** Harvest `org`, work_package lifecycle, provenance into `ops` design now; build P6/CPM when a real consumer arrives. |

**`ops` primary object:** the **apparatus-instance**, bound to a **scope**, under a **project** —
honoring both the identity spine (C) and the revenue anchor (B). The **scope→apparatus
binding is a hard invariant** (§4).

**Canonical-winner leans (to confirm at Chip 1):** `seam` is the heavier-referenced impl
(184 vs 47 apparatus; the revenue/audit/idempotency disciplines live here) → `ops` converges
*onto* the seam model's patterns, absorbing public's one superior idea (the **non-null
apparatus→scope binding**, which seam left nullable) and work's normalized `org`.

---

## 4. Laws & invariants (this lane is bound by these)

1. **Scope→apparatus binding is FIXED** (revenue-recognition anchor). PM authority is task-level within a scope; never cross-scope apparatus moves. Enforced structurally in `ops` (the integrity target public got right, seam left loose).
2. **Identity = Supabase `auth.users`.** `seam.users`/`user_roles` become legacy read-model; new actor refs FK `auth.users`.
3. **Recognition firewall.** Revenue is **never** an operational-row column (the `public.scopes.actual_revenue` / `public.apparatus.actual_revenue` anti-pattern is rejected). Revenue lives in a dedicated, append-only recognition ledger + frozen contract snapshot (seam's discipline, made mandatory).
4. **Field-trust on money (G4 analog).** A recognized/billable amount is only emitted when its basis is present (a frozen quote + a completion event); missing basis = withhold, never fabricate.
5. **Soft-UUID seam to `core`.** The `core.equipment_models` spine (D-003) stays deferred; `ops` apparatus carries a nullable `equipment_model_ref` until a chip forces the join (records-lane pattern).
6. **Migration invariants (`MASTER-SCHEMA.md` §7) are HARD** for any convergence step: schema-qualify cross-schema refs / pin `search_path`; re-create RLS + grants on any namespace move (default-deny returns *zero rows, HTTP 200* otherwise); parity-check served row-count, not "table exists"; ordered teardown. **`lvbreakertcc` never breaks.**
7. **Estimator owns compute.** Platform consumes output values; never reimplements workbook formulas.

---

## 5. The revenue / progress-billing model (the operational heart)

**Operator model (2026-06-15, "for projects like this"): hours-based, apparatus-grain, binary completion.**
Revenue is **not** a directly-quoted dollar line — it is driven by **labor hours per apparatus**,
with all **adders (the M4/N4 multipliers) and external costs broken down to a per-apparatus
hour-equivalent value**, so every dollar resolves to "hours on an apparatus." Billing and
recognition then **follow actual apparatus completion** — binary (`=1`).

```
VALUE-PER-APPARATUS (frozen at intake)
   apparatus_hours            base labor hours to complete this apparatus (Estimator scope sheet)
 + allocated_adder_hours      project adders (M4/N4) + external costs, broken down to a
                              per-apparatus hour-equivalent — non-labor cost rides on hours
 × bill_rate                  ⇒ per-apparatus billable VALUE                  → project_contract_snapshots (frozen)
        │
        ▼
COMPLETION (field, BINARY)    apparatus complete = 1 (tested / produced / delivered), else 0
                                                                             → production_tracking / customer_completion records
        │
        ▼
RECOGNITION (append-only)     recognized = completion(0|1) × per-apparatus value
                              project % complete = Σ completed value ÷ Σ total value
                                                                             → apparatus_revenue_events (+ apparatus_financials, hours)
        │
        ▼
PROGRESS BILL                 recognized-but-unbilled rolls into a progress bill
                              (application for payment) — tracks what's actually completed   → (new ops billing object)
```

**Why hours-denominated:** nothing front-loads — adders + external costs are earned only as
the apparatus they ride on completes; project progress = completed-hours-value ÷ total-hours-value;
**hours are the common denominator** across estimate, progress, and bill (the natural unit for
a testing firm). Maps to the live `seam.hours` + `scope_labor_details` scaffolds.

**Resolved / open:**
- **D-OPS-1 — completion grain: BINARY per apparatus (`=1`). RESOLVED** (operator). A `completion_factor` column is reserved for any future partial case; the MVP is all-or-nothing.
- **D-OPS-2 — recognition timing: event-driven append-only ledger.** Lean stands (matches `seam.apparatus_revenue_events`; audit + immutability).
- **D-OPS-3 — progress-bill object: snapshot-at-issue, cadence-agnostic.** Lean stands ("application for payment").
- **D-OPS-4 — quote→apparatus value: HOURS-based.** Per apparatus = (base hours + allocated adder/external hours) × rate. **Allocation method** — lean: total adder/external ÷ total project hours = a per-hour loading applied to each apparatus's hours — **confirmed against a real Estimator workbook at Chip 2.**
- **D-OPS-7 — hours as the revenue unit (NEW).** Schema carries apparatus-level hours (base + allocated) as first-class, not only dollars. Confirm the Estimator exposes per-apparatus (vs per-scope) hours, or define the scope→apparatus hours split, at Chip 2.

---

## 5a. AS-BUILT model — verified 2026-06-15 against the real Estimator + Tracker

The operator-provided **Project Miner** workbooks (Estimator quote + Tracker execution) were
reverse-engineered; they **confirm the §5 model end-to-end** and pin the mechanics. This is
now ground truth (supersedes inference where they differ). Sources: `C:\Users\jjswe\Desktop\Project Miner PM Planning\` (the Estimator master + two real quotes; the `RESA Power - Project Data Entry MASTER` tracker + the Garney populated instance; the operator's `Supabase Public Schema.md`).

**Quote side (Estimator):** a scope sheet = one quotable scope = one adjusted total
`P4 = P3 × M4 × N4`; project value = Σ P4. Apparatus lines carry **hours only**
(`Hrs/Line = QTY × Hrs/Unit`), where `Hrs/Unit` is looked up from a **standard-hours catalog**
(`tblEquipment`) by **apparatus type × test standard (ATS'25 vs MTS'23)**. Dollars attach at
scope grain (labor categories draw from the scope hour-pool; travel/outside-services are
explicit dollar lines). Per-apparatus revenue is *derivable* (hour-share) but not native to the quote.

**Execution/billing side (Tracker — where per-apparatus billing actually happens):**
- Billing unit = **task line = (apparatus × NETA test)**; the billable basis is **quoted `Apparatus Hours`** — **actual hours are tracked for variance but do NOT drive revenue.**
- **Binary completion gate** `Z = IF(date-done OR STATUS=COMPLETED, 1, 0)`; **every dollar column × Z** → line bills $0 until done, full value books on completion (= progress billing as work finishes). Confirms "apparatus completion = 1".
- **Adders/external costs fold into the per-apparatus-hour rate** (confirms the ruling exactly): time adders = `%hours × rate` (commute, PM, badging, travel, final report); fixed costs (travel $, M&E $) = `lump ÷ total scope hours = $/app-hr`, allocated per line by hours. Nothing invoiced separately.
- Rate config is **per-scope** (`Scope_Labor_Rates`: base rate + adder %s + fixed-$/app-hr + multiplier). Completion is **reported at apparatus grain** (`Project Summary`: % = completed apparatus ÷ total).

**Schema implications:**
1. **D-OPS-5 canonical winner — REVISED.** The live **`public.*`** PM core already models this faithfully (`apparatus` scope_id-NOT-NULL + quoted_hours/actual_hours/quoted_revenue · `apparatus_revenue` recognized/percent · `apparatus_types` default_hours + neta_section_ats/mts = the std-hours catalog · `scope_labor_details` · `scopes` · `project/scope_financial_summaries`). Closer to the as-built system than `seam`. **Converge onto public's conceptual PM model, applying seam's disciplines** (append-only recognition events, idempotency, audit, RLS).
2. **New first-class entities:** the **standard-hours catalog** (apparatus_type × {ATS|MTS} → hours); the **per-scope rate/adder config**; the **NETA task line** (apparatus × test) = the billing/completion unit.
3. **Law 3 nuance.** The frozen **quote** legitimately rides on the apparatus (`quoted_hours`/`quoted_revenue`); the **recognized** amount is what must be an append-only event ledger, not a mutable column. Quote-on-apparatus = correct; recognition-as-mutable-column = the anti-pattern.

**RESOLVED — D-OPS-8 (recognition GRAIN) = APPARATUS** (operator, 2026-06-15): *"we only recognize revenue when each apparatus is completed."* The **apparatus is the recognition unit** — all-or-nothing per apparatus, not per test-line. An apparatus recognizes its full quoted revenue when its testing is complete; partial tests earn nothing until the apparatus is done. (Simpler than the Tracker's per-test-line gating; the operator chose apparatus-grain for the platform.)

**RESOLVED — revenue categories + blended rate** (operator, 2026-06-15, with the scope cost-engine screenshot):
- Revenue is **tracked in 4 categories**: **Onsite Labor · Offsite Labor · Travel · Outside Services** (the scope sheet's four cost sub-tables, `P14`/`P19`/`P26`/`P33`). Maps to the existing `public.apparatus_revenue.revenue_type`.
- The **per-apparatus-hour rate is a SINGLE blended adjusted value** = scope adjusted total `P4` ÷ scope total apparatus hours `J3` (screenshot scope: `$101,146.13 ÷ 400.5 hrs ≈ $252.55/app-hr` — one number already absorbing the 110% labor loading, travel, and outside services). We do **not** allocate each category per-apparatus — one blended rate suffices.
- Per-apparatus **quoted revenue** = `apparatus_hours × blended_rate`; recognized on apparatus completion. The **4-category split** of recognized revenue is derived by the scope's category proportions. This collapses D-OPS-4/7 to: capture the scope's 4-category totals + total hours → derive the blended rate; everything per-apparatus rides that one rate.

---

## 6. Gap analysis (master target vs reality)

| # | Gap | Severity |
|---|---|---|
| G1 | **Estimator intake has no home in `MASTER-SCHEMA`** (neither `records` nor `ops` models it). | **Blocking** — closed by this re-baseline's §3 amendment. |
| G2 | **`ops` namespace does not exist**; three project + two apparatus identities live unconverged. | Foundational — Chip 1. |
| G3 | **`core.equipment_models` spine unbuilt** (D-003). | Deferred — soft-UUID seam (Law 5); built when a chip forces it. |
| G4 | **Revenue model never ran end-to-end** (`seam.scopes` 0 rows; all financial + hours tables empty). | The Chip 2–4 build proves it. |
| G5 | **Identity-source contradiction** (`seam.users` vs `auth.users`) resolved on paper, not in data. | Closed by Law 2. |
| G6 | **Intake extraction code does not exist** (Estimator `.xlsm` parser; the 5-phase flow). | **CLOSED — Chip 5.** `ops-intake` package (openpyxl extractor + validate + envelope + approve) exists and is tested. The governed envelope (`intake_runs`/`source_files`/`validation_findings`, mig 007) wraps it; `approve_run` is the sole `ops.*` domain writer; host-gated API + pm-review UI complete the 5-phase flow. |

---

## 7. Chip sequence (proposed roadmap — operator picks the first to build)

Each chip is reversible, validated on a dev DB before prod, behind §4 Law 6. The records-lane
cadence (design → spec → plan → TDD → chip-sized PR into `main`).

- **Chip 0 — Re-baseline SSoT** (this file). **DONE** — `df5fa2bc`.
- **Chip 1 — `ops` identity skeleton.** `ops` schema + 7 enums + projects/scopes/apparatus/tasks (public/seam conceptual model); FIXED scope→apparatus binding (NOT NULL + immutability trigger); soft `equipment_model_ref` seam. Dev DB **`ops_dev`** (local PG). **DONE** — `5c2442db`, 9/9 TDD, reversible.
- **Chip 2 — Quote model.** Standard-hours catalog (DEFAULT-only) + **`scope_quote_line`** (per-project `hrs_per_unit`, line-level — D-OPS-7) + `scope_quote` (4 categories + generated P3/P4/blended_rate + J3 trigger) + apparatus quote columns + `v_apparatus_quote`. **DONE** — 10/10 TDD, reversible. *(Intake envelope / Packet B re-scoped → Chip 5.)*
- **Chip 3 — Apparatus revenue + completion + recognition ledger.** §5: per-apparatus hours-value, **binary apparatus completion** (D-OPS-8), append-only recognition events. **DONE** — 33/33 TDD, reversible. (Dev-only `ops_test`; NOT deployed; see D-OPS-10/D-OPS-11.)
- **Chip 4 — Progress billing.** §5 final layer: the billing-application object (snapshot of recognized-unbilled). **DONE** — 63+ tests, reversible (Chips 1-3 survive DOWN); sub-cent parity fix; full firewall assertion; dev-only `ops_test`; operator-gated merge.
- **Chip 5 — Intake envelope / lifecycle / UI (extractor pre-existing). DONE + post-audit-hardened** — tip `5abacdda`, dev-only `ops_test`, operator-gated merge. mig 007 envelope tables + `ops-intake` parse/approve package (xlsm AND DataverseExport-JSON intake) + host-gated control-plane API (5 routes, finance-redacted) + `operations-web` pm-review page (upload → review tree → approve, no dollars). Built `00ddc4d2` (16 SDD tasks); an **operator post-completion audit** then caught 5 defects — all FIXED + regression-tested: project_number parsed from the workbook Job# (was hard-coded Miner → multi-project now real), UI sends a valid-UUID actor + extension-derived content_type, `treeToReviewPayload` preserves server-pinned fields, `get_run` returns only current-version findings, JSON intake implemented — plus a **latent `approve_run` ambiguous-id bug** the new foreign-source test exposed (the re-approve path no prior test hit). A 2nd external audit (Codex) then found 6 more issues -- all fixed + regression-tested: a finance LEAK via guard error messages (now value-free + a generic API 400), patch_review lost-update/patch-vs-approve races (FOR UPDATE + status predicate + RunNotActive), API content_type validation (422), a scope-name dollar leak in finding messages (reference by index), the .json file-picker, and unknown-actor FK -> clean 400. A 3rd full external audit (Codex, WITH live-DB probes) then adversarially audited all 16 tasks and found ONLY 1 issue -- guard exception text still embedded a workbook scope name (a '$'-named scope leaked into the package-level ValueError; the API already masked it) -- FIXED (a _ve() $-stripping helper across every guard + test). Codex verdicts: tasks 1-3,4-8,10-16 Pass; 9 fixed. Green: 47 pkg + 10 mig + 17 API + UI typecheck/12 unit/1 smoke; `git diff --check` clean. Decisions in D-OPS-12.
- **Chip N (interleaved, late) — Convergence/migration.** The deferred D-012 collapse of `public`/`seam`/`schedule`→`ops` (build spine → backfill soft-UUIDs → dual-write → flip readers → drop loser), behind §4 Law 6.

---

## 8. Open decisions (consolidated)

| ID | Decision | Lean / status | Settle at |
|---|---|---|---|
| D-OPS-1 | Completion grain | **RESOLVED: binary (`=1`)**; `completion_factor` reserved | — |
| D-OPS-2 | Recognition timing | event-driven append-only ledger | Chip 3 spec |
| D-OPS-3 | Progress-bill object & cadence | **RESOLVED: snapshot-at-issue, cadence-agnostic** (Chip 4 built) | — |
| D-OPS-4 | Quote→apparatus value | **RESOLVED: single blended rate** = scope P4 ÷ scope hours; per-apparatus = hours × blended rate (§5a) | Chip 2 |
| D-OPS-5 | Canonical winner | **REVISED: public's conceptual PM model + seam's disciplines** (see §5a; was seam-based) | Chip 1 spec |
| D-OPS-6 | Dev DB | fresh `ops_dev` (local PG) | Chip 1 |
| D-OPS-7 | Hours — per-project, line-level | **catalog = DEFAULT only** (operator 2026-06-15); binding `hrs_per_unit` on `scope_quote_line`, overridable per project; apparatus inherit. **BUILT Chip 2.** | done |
| D-OPS-8 | Recognition **grain** | **RESOLVED: APPARATUS** — recognize when each apparatus complete (all-or-nothing); not per test-line | — |
| D-OPS-9 | Revenue categories | **RESOLVED: 4** — Onsite Labor · Offsite Labor · Travel · Outside Services (→ `apparatus_revenue.revenue_type`) | Chip 3 |
| D-OPS-10 | Substrate fork — Chip 3 recognition on clean `ops.*` | **RESOLVED 2026-06-20:** Chip 3 recognition is built on the clean `ops.*` substrate (durable preferred), NOT the deployed `seam.apparatus_revenue_events`. `public`/`seam` = concept-reference only; a later bounded packet bridges `ops.*` recognition → the deployed `/pm-review` surface at the appropriate convergence chip. | Chip 3 |
| D-OPS-11 | Chip 3 recognition rules | **RESOLVED 2026-06-20:** apparatus-grain; gated by lead approval (`approve_and_recognize`) + `status='Complete'`; assessment-independent; active-row-only (apparatus/scope/project); frozen valid quote basis required; both obligation clearances (`provided`/`not_applicable`) required; hard `ops.persons(person_id)` actor FK; append-only firewall (no mutable recognized-$ columns on apparatus); reverse-first lifecycle protection (apparatus/scope/project cannot be deactivated/cancelled while open recognition exists). | Chip 3 |
| D-OPS-12 | Chip 5 intake architecture | **RESOLVED 2026-06-21** (built + tested). Key decisions: **(1) Parse/envelope/approve separation** — `create_run` (parse → classify → supersede → conflict-check → persist to envelope only; zero `ops.*` domain writes) is strictly separated from `approve_run` (identity-gated, the sole `ops.*` domain writer). **(2) No operational writes before approve** — `ops.projects`/`scopes`/`tasks`/`apparatus`/`scope_quote*`/`standard_hours` untouched until `approve_run`; asserted by a "domain tables count == 0 after create_run" test. **(3) Revision-refusal on conflict** — `create_run` refuses if `recognized` conflict exists; `recognized` = EXISTS any `ops.revenue_recognition_event` row for the project (membership, never `net > 0`); additional refused states: `billed` (open billing application) + `frozen` (run already approved). **(4) N4 mandatory for `.xlsm`** — `source_format = decomposed_scope_sheet` requires N4 present; absent N4 = blocking finding. **(5) Supersede lifecycle** — at most one `active` run per project at any time; `create_run` supersedes the prior active run before inserting the new one; enforced by `uq_intake_one_active` partial unique. **(6) Full-replacement materialization** — `approve_run` deletes `ops.*` rows `WHERE source = 'ops-intake'` (cascade) then re-inserts the full tree under a project lock; apparatus are QTY-expanded at approve time, not during parse. **(7) Findings finance-redaction** — `intake_validation_findings` carries PM-safe `message` (no dollar values) and finance-only `diagnostic_detail`; the API and UI return only `message`. **(8) Global lock order (verified partial order across Chips 3/4/5):** `advisory(project_number) → intake_run row FOR UPDATE → billing_application → project → revenue_recognition_event → apparatus`. Chip 5 acquires `advisory(project_number) → intake_run FOR UPDATE → project → apparatus`; Chip 4 billing acquires `billing_application`; Chip 3 recognition acquires `project → recognition_event → apparatus`. Future writers MUST respect this ordering to avoid deadlock. **(9) `source = 'ops-intake'` ownership marker + foreign-source refusal** — rows materialized by `approve_run` are stamped `source = 'ops-intake'`; full-replacement deletes `WHERE source = 'ops-intake'` only (never the generic `legacy_source_id IS NOT NULL`); `approve_run` refuses a project that has any scope with `source != 'ops-intake'` (foreign-source refusal). **(10) Miner-coexistence (operator decision 2026-06-21)** — legacy Project Miner rows (source `miner_rev10.xlsm`) are frozen and out-of-lifecycle; `approve_run` refuses any project bearing non-`ops-intake` scope rows; NO auto-backfill of Miner data into the intake lifecycle. **(11) `line_uid`** — stable parse-time payload line identity (a deterministic key embedded in the parsed payload, distinct from the DB-synthesized `legacy_source_id`); used as the cross-scope guard key in `patch_review`. **(12) standard_hours catalog write removed from intake** — `approve_run` does NOT write to `ops.standard_hours`; the catalog is reference data managed independently (operator decision 2026-06-21). **(13) JSON intake** — `create_run` branches on `content_type`: `.xlsm` via openpyxl, `.json` via `parse_json_payload` (the DataverseExport shape: `project.projectNumber`/`client`/`site`/`scopes[].financials`/`apparatus[]`), minting the same `line_uid` scheme; a parse failure yields a GOVERNED rejected envelope (a persisted run + blocking finding), never a 500. **(14) project identity is DERIVED, never hard-coded** — `project_number` comes from the workbook Job# / JSON `projectNumber`; the original build hard-coded the Miner identity (every upload collapsed to one project) — fixed + regression-tested in the 2026-06-21 post-audit hardening, along with the UI real-run path, the review round-trip allowlist preservation, current-version finding filtering, and a latent `approve_run` ambiguous-id bug on the re-approve path. | Chip 5 |

*Operator-level (governance): the §3 amendment (elevate intake) + the §5 hours-based binary-completion model — **RATIFIED 2026-06-15**. Remaining operator calls ride with each chip spec.*

---

## 9. Provenance & sources

- **Live AS-IS (§2a):** `information_schema` + `pg_class` queries, governed prod `fxoyniqnrlkxfligbxmg`, 2026-06-15.
- **Ratified foundation:** `.claude/PLATFORM/MASTER-SCHEMA.md` (§1–§9) + `ARCHITECTURE.md` Decisions 010/012/013/014.
- **Folded prior PM design:** `.claude/PLATFORM/PM_SCHEMA_FOUNDATION_PLAN_v2_2026-05-26.md` (public-vs-seam verdict, the recognition-firewall + open-decision list) · `ERA_2_4_PACKET_B_PM_CORE_INTAKE_ENVELOPE_DESIGN_2026-05-26.md` (+ `ERA_2_4_PACKET_B_SQL/`) · `ESTIMATOR_ARCHITECTURE.md` (the intake contract, incl. P3/P4/M4/N4 + labor hours) · the file-only `infra/database/migrations/work/` + `org/` (the April P6/CPM branch; `PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md` is its authority doc).
- **Intake + revenue laws:** memories [[reference-pm-project-intake-workflow-2026-05-25]] + [[reference-pm-hybrid-intake-authority-2026-05-25]]; the §5 hours-based binary-completion model is the operator's 2026-06-15 ruling.
- **Live seam column dump (for chip-level work):** saved at `…\tool-results\mcp-bb4a07f4-…-execute_sql-1781537523044.txt` (60 KB; the full `seam.*` column definitions, not needed at roadmap altitude).

---

*End — Operations (PM) lane re-baseline v1 (draft for review; nothing applied). On approval: commit to `reference/ops/`, then pick the first chip → its design/spec/plan/TDD pass.*
