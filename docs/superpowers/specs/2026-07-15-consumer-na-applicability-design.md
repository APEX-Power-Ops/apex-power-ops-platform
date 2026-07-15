# Consumer-evidence `not_applicable` applicability design (issue #103, Phase 1)

**Status: rev 3.2 — RATIFIED (operator, 2026-07-15, §11d). Implementation authorized under the offline guardrails; STOP at the draft PR.**
**Rev 3.2** applies the operator's AMEND-ONCE-THEN-RATIFY ruling on rev 3.1 (§11d): the carve-out is scoped by **state as well as status** (`not_applicable` + accepted delete ONLY — other non-observed states on accepted delete keep today's SP022+SP027 dual diagnostic); the test matrix pins the state/action/status conjuncts (cases 3/5/6/11) and is labeled NEW-NEG vs PRESERVE (not all twelve start red); minor wording amendments folded.
**Rev 3.1** folded the bounded delta review (Codex gpt-5.5 xhigh, §11c): the SP022 delete carve-out is scoped to **accepted** delete (`decision_status == "accepted"`, matching SP027's exact gate at `check_disposition.py:465`) — an unscoped carve-out would have loosened non-accepted delete rows carrying voluntary resolved conclusions; tests 11–12 added.
Worktree `apex-gate-correction-consumer-na`, branch `schema-placement/gate-correction-consumer-na-applicability` off `35397326` (the merged #102 gate-correction). Grounded on the code at that commit; line refs are as read this session.
**Rev 3** applies the operator's ratification ruling on rev 2 (record in §11): **P2 REJECTED as written** — `external_clients` is the platform's broad external/integration-inventory dimension, not a Data-API-only signal, so `in_data_api=false` does not make it inapplicable; **no new N/A waiver is introduced**. `external_clients` must be OBSERVED for resolved **non-delete** conclusions; the existing accepted-delete SP027 exception (and its current OV022 behavior) is preserved verbatim, with its broader semantic question recorded separately (§6c). **P6 removed** (its temporal-coverage claim was falsified: a base-census exposure-false observation bypasses OV022 entirely — verified; moot once the waiver is rejected). **P7 deferred** to a separate correction. **P3 amended**: OV015 narrowly mirrors BOTH N/A states for resolved non-delete conclusions. Test plan cut to 10.
**Rev 2** folded the adversarial cross-engine review (3 opus refute-lenses + Codex gpt-5.5 xhigh; record in §11).

Sibling of the #102 `runtime_logs` gate-correction. #102 closed the `runtime_logs=not_applicable` fail-open in the SP022 conclusion loop. This packet closes the **remaining two** dimensions that the same loop still greens on `not_applicable`: `static_repo` and `external_clients`.

---

## 1. Precise vocabulary (no ambiguous "six consumer dimensions")

- **`check_disposition.DIMS`** (`check_disposition.py:33`) = **5 consumer-evidence dimensions**: `static_repo`, `database_deps`, `runtime_logs`, `external_clients`, `operator_declaration`.
- **`disposition_overlay.DIMENSIONS`** (`disposition_overlay.py:30`) = **6 permitted overlay paths**: `in_data_api_exposed_schema`, `advisor_findings`, `consumer_evidence.static_repo`, `consumer_evidence.runtime_logs`, `consumer_evidence.external_clients`, `consumer_evidence.operator_declaration`.
- **`CONSUMER_CONTRIB_DIMS`** (`disposition_overlay.py:39`) = **4 window-contributing** consumer dims: `static_repo`, `runtime_logs`, `external_clients`, `operator_declaration`. These are the only consumer dims that are overlay-capable.
- **`database_deps` is base-census-only**: it is a `DIMS` member (a consumer dim the SP022 loop requires OBSERVED) but is **not** in `DIMENSIONS`, so it cannot be supplied by a signed overlay — its observed value comes from the base census (`pg_depend`/`dependent_objects`), and `_gate_required_dims` filters it out via `& _PERMITTED_OVERLAY_TARGETS`, so OV015 never names it.
- Overlay paths carry a `consumer_evidence.` prefix; `DIMS`/checker names do not. `_base_slot` (`disposition_overlay.py:216`) resolves the prefix.

## 2. Which action classes reach the gate

The SP022 conclusion loop fires for **any** row whose `consumer_disposition ∈ {no_consumer, has_consumers}` (`check_disposition.py:414`) — it is **conclusion-based, not status-gated**. The schema forces a resolved conclusion for these **accepted** action classes:

| action_class (accepted) | schema-forced `consumer_disposition` | schema ref | enters SP022 loop | SP027 delete floor |
|---|---|---|---|---|
| `harden`  | `∈ {no_consumer, has_consumers}` | schema:273–274 | yes | — |
| `promote` | `∈ {no_consumer, has_consumers}` | schema:250–253 | yes | — |
| `compat`  | `= has_consumers` (const)        | schema:263–264 | yes | — |
| `archive` | `= no_consumer` (const)          | schema:268–269 | yes | — |
| `delete`  | `= no_consumer` (const)          | schema:283–284 | yes | **yes** (check_disposition.py:513–533) |
| `retain`  | none forced (may be null/unresolved) | schema:278–279 | only if the author *voluntarily* sets a resolved value | — |

**The rows exposed to the seam are ALL rows carrying a resolved conclusion outside the accepted-delete floor**: the schema-forced change actions (`harden`, `promote`, `compat`, `archive`), a `retain` that **voluntarily** asserts a resolved conclusion, and a **non-accepted `delete` row** (proposed/rejected) that voluntarily carries one — SP027 is gated `accepted`-only (`check_disposition.py:465`), so it never sees those. Accepted `delete` also enters the loop but its SP027 floor already handles `static_repo`/`external_clients` strictly (below). A row with a null conclusion never enters the loop (correct — the claim is what's gated).

## 3. The seam (current behavior, grounded)

SP022 conclusion loop, per source relation, over `DIMS` (`check_disposition.py:414–441`):

```
operator_declaration : st != observed            -> SP022 (must be OBSERVED)        [line 421-423]
database_deps        : st != observed            -> SP022 (must be OBSERVED)        [line 424-426]
runtime_logs         : st != observed            -> SP022 (must be OBSERVED, #102)  [line 427-429]
if st == "not_applicable": continue    # <-- SEAM: reached only by static_repo, external_clients   [line 430-431]
if st != "observed": SP022 (unresolved)                                             [line 432-434]
# observed -> SP013 count agreement
```

So for a resolved conclusion, **`static_repo=not_applicable` and `external_clients=not_applicable` are accepted unconditionally** — `external_clients` with **no exposure predicate**.

**Scope qualifier (Codex):** this pair is the whole remaining N/A seam **for resolved SP022 conclusions** — not the whole applicability surface. The SP010 manifest opt-in (`check_disposition.py:401–407`) intentionally accepts observed-or-N/A without asserting a conclusion, and an accepted `retain` with a null conclusion never enters the loop; both are documented in §4† and remain out of scope. `advisor_findings` (overlay path, not a `DIMS` member) and `database_deps` (a `DIMS` member, already forced-observed, not overlayable) are sibling *surfaces*, not this seam — explicitly out of scope (§9 P5).

**SP027 — the currently ratified delete floor** (`check_disposition.py:513–533`; its semantics remain disputed, §6c): `static_repo` (and database_deps/runtime_logs/operator_declaration) must be OBSERVED; `external_clients` OBSERVED, or `not_applicable` **only when `in_data_api_exposed_schema` is OBSERVED `false`**; plus a ≥30-day window. Gated to **accepted** delete only. The change actions have no equivalent.

**Concrete exploit** (same class as #102): an accepted `harden` on an API-exposed table with real external consumers → set `external_clients=not_applicable` + `static_repo=not_applicable`; the forced-observed dims read `found_consumers=0`; the row greens as `no_consumer`; a receipt is written and the harden proceeds, hiding both static-code and external API consumers.

## 4. Applicability table (proposed)

Governing principle: **a resolved `consumer_disposition` is a factual claim ("no_consumer"/"has_consumers") that requires having actually LOOKED via every channel whose applicability is not disproven by observed evidence.** Rev 3 finds **no dimension has such a disproving predicate for the change actions**: the SP027 `external_clients` exposure waiver is NOT generalized (rejected P2, §5) — it survives only where it is already ratified, on accepted `delete`.

Legend: **O** = OBSERVED required; **any** = unconstrained by this gate. The table applies to **every** resolved conclusion, including a `retain` that voluntarily asserts one (conclusion-based, not action-gated).

| dimension | overlayable? | resolved conclusion outside the accepted-delete floor (harden/promote/compat/archive/voluntary-retain/**non-accepted delete**) | **accepted delete** (SP027 + current OV022, preserved verbatim) | unresolved (retain-null / non-accepted-null) |
|---|---|---|---|---|
| `operator_declaration` | overlay (window) | **O** | **O** | any (SP022 loop off)† |
| `database_deps` | base-census-only | **O** | **O** | any† |
| `runtime_logs` | overlay (window) | **O** (#102) | **O** | any† |
| `static_repo` | overlay (window) | **O** — *no N/A waiver* (NEW #103) | **O** (SP027; NEW: SP022 also fires — consistent, no contradiction) | any† |
| `external_clients` | overlay (window) | **O** — *no N/A waiver* (NEW #103, P2 rejected) | **O, or N/A iff `in_data_api` OBSERVED `false`** — the ratified SP027 exception, unchanged; SP022 skips ONLY the N/A state here (other non-observed states get SP022 and SP027, today's dual diagnostic) | any† |
| `in_data_api_exposed_schema` | overlay (bool) | not consulted by SP022 (no waiver to grant) | predicate input for the accepted-delete SP027 exception (unchanged) | — |

† For an unresolved conclusion, the SP022 loop does not fire. If the **manifest** lists `consumer_evidence` in `required_observations`, the weaker SP010 opt-in (`check_disposition.py:401–407`) still requires every dim `observed`-or-`not_applicable` — but that path is deliberately weaker (it does not assert a conclusion) and is **out of scope** for #103; it is documented here so the two paths are not conflated.

**All non-observed states are handled by the "must be OBSERVED" rows**: `not_observed`, `query_failed`, and `stale` were already rejected by the generic `if st != "observed"` fall-through; after #103 they are rejected by the explicit `static_repo`/`external_clients` branches instead (same outcome). `not_applicable` is the only state whose handling changes.

**Consequence — the generic N/A fall-through becomes dead code.** After #103 every one of the 5 `DIMS` has an explicit branch in the resolved loop, so `if st == "not_applicable": continue` (line 430) is unreachable inside the conclusion block and should be removed for clarity (policy choice P4).

## 5. Why NEITHER dimension gets a new N/A waiver (P2 rejected — the "don't auto-generalize" discipline, applied to my own rev-1/2 proposal)

- **`external_clients` — the exposure waiver is REJECTED for change actions (operator ruling, verified against the platform's own definitions).** Rev 1/2 defined the dimension as Data-API-only traffic, making `in_data_api=false` a disproving predicate. The platform's authoritative sources define it **more broadly**:
  - `OVERLAY_COLLECTION_RUNBOOK.md:37` — "**External API-client / integration inventory**", evidenced by a *committed inventory* (not a traffic probe).
  - Signed-overlay design residual **R-1** (`2026-07-11-signed-overlay-evidence-design.md:224`) — the single overlay-supplied signal for **external/HTTP consumers**, with `database_deps` explicitly **DB-internal-blind**.
  - The definer-view reconciliation evidence enumerates its concrete referents: **dashboards, reporting tools, integrations, MCP clients, desktop-agent polling patterns** (`evidence/definer-view-reconciliation-2026-07-13.md:101, 269, 332`).

  A **dormant direct-SQL or BI integration** is a real member of that inventory: it is invisible to `database_deps` (DB-internal-blind by design), NOT proven absent by a bounded `runtime_logs` window (dormant = no in-window traffic), and unrelated to PostgREST exposure. So `in_data_api=false` does **not** make the inventory dimension definitionally inapplicable — the rev-1/2 waiver would have silently redefined `external_client_inventory` as `data_api_clients`. **Ruling: require OBSERVED for every resolved non-delete conclusion.** The already-ratified SP027 exception on accepted `delete` is preserved verbatim (its broader semantic question is recorded in §6c, not re-litigated in this packet).
- **`static_repo`** measures **static code references** in application repositories. Any extant relation *could* be referenced in code; there is **no per-relation observed predicate** that makes "static references" inapplicable. By the same reasoning #102 used for `runtime_logs` ("non-exposure does not waive it — direct consumers are still possible"), `static_repo` is **always applicable** → require OBSERVED, **no N/A waiver**. This matches SP027, which permits no `static_repo` N/A.
- **Residual limitation (noted, not fixed here — wording corrected per Lens A):** `in_data_api_exposed_schema` is per-relation direct exposure. A non-exposed table `T` reachable indirectly via an exposed **security-definer view** `V` is not caught by the exposure predicate — but it **is** caught by the always-mandatory **`database_deps`** (the V→T `pg_depend` edge yields `found_consumers ≥ 1`, and SP013 at `check_disposition.py:437–440` contradicts a `no_consumer` claim). `static_repo` (application-repo scan) does NOT see in-DB view/function bodies, and `runtime_logs` only sees them if invoked in-window — do not credit those channels for this case. The **truly residual** slip-past is a **dynamic-SQL security-definer function** (`EXECUTE 'SELECT … FROM t'`): no `pg_depend` edge, not in the app repo, runtime-visible only if it fired in-window. That blind spot is **pre-existing and platform-wide** — the shipped SP027 delete floor carries the identical predicate with the identical residual — so #103 does not widen it. A future "indirect exposure" dimension remains the tracked follow-up, explicitly out of scope.

**SP027 re-evaluation verdict (rev 3):** the existing accepted-`delete` SP027 exception is **temporarily preserved as ratified legacy behavior** — its predicate, its current OV022 behavior, and its green regression (`tests/test_check_disposition.py:346` `_delete_external_na_unexposed`) are all unchanged by this packet. It is NOT endorsed as semantically sound: the same inventory-breadth argument that rejects P2 applies to it, and it additionally carries a verified temporal bypass (§6c). Its correction would invalidate a ratified exception and its tests, so it is **recorded as a separate SP027 policy question**, not folded here. The stronger alternative (require `external_clients=observed` for delete too) is defensible but belongs to that explicit SP027 correction packet.

## 6. Normative predicates / pseudocode

### 6a. SP022 (checker, authoritative) — resolved-conclusion loop
Replace the seam (lines 430–431) with explicit `static_repo` and `external_clients` branches, keeping the three existing forced-observed branches ahead of them:

```
for dimname in DIMS:                       # static_repo, database_deps, runtime_logs, external_clients, operator_declaration
    st = ce[dimname].state
    if dimname == "operator_declaration" and st != "observed": emit SP022; continue   # unchanged
    if dimname == "database_deps"        and st != "observed": emit SP022; continue   # unchanged
    if dimname == "runtime_logs"         and st != "observed": emit SP022; continue   # unchanged (#102)

    if dimname == "static_repo" and st != "observed":                                 # NEW #103
        emit SP022 "static_repo must be OBSERVED for a resolved consumer_disposition;
                    static-code consumers are possible on any relation, so non-applicability
                    cannot be asserted (no not_applicable waiver)"; continue

    if dimname == "external_clients" and st != "observed":                            # NEW #103 (rev 3.2)
        if (
            st == "not_applicable"
            and row.get("action_class") == "delete"
            and row.get("decision_status") == "accepted"
        ):
            continue        # ONLY the preserved SP027 exception (state+status+action scoped):
                            # accepted delete + not_applicable -> SP027 alone evaluates the ratified
                            # exposure-false waiver (check_disposition.py:522), preserving the green
                            # regression (_delete_external_na_unexposed) byte-for-byte.
                            # Any OTHER non-observed state on an accepted delete (not_observed/
                            # query_failed/stale) gets SP022 here AND SP027 — exactly today's behavior
                            # (rev-3.1's status-only carve-out dropped the SP022 diagnostic; operator
                            # Finding 1). A non-accepted delete row carrying a voluntary resolved
                            # conclusion always gets SP022 (SP027 never runs on it, schema:227/283;
                            # bounded-review High, rev 3.1).
        emit SP022 "external_clients must be OBSERVED for a resolved consumer_disposition;
                    the inventory covers non-API integrations (dashboards, BI, MCP, direct SQL),
                    so Data-API non-exposure does not make it inapplicable"; continue

    # (generic `if st == "not_applicable": continue` now unreachable — remove, P4)
    if st != "observed": emit SP022 (unresolved); continue
    if ce[dimname].found_consumers > 0: observed_positive = True; (SP013 no_consumer contradiction)
```
Diagnostic code stays **SP022** (same invariant family). SP022 consults **no exposure predicate** (rev 3: there is no waiver to grant); `in_data_api_exposed_schema` is read only by SP027's unchanged delete branch. Ownership is exact: accepted delete + N/A → SP027 alone (the ratified exception); accepted delete + other non-observed states → SP022 **and** SP027 (today's dual diagnostic, preserved); every other row with a resolved conclusion → SP022. No row is owned by neither layer, and no existing diagnostic is removed.

### 6b. OV015 (overlay loader, narrow early-warning mirror — P3 as amended)
The NEW OV015 branches must remain a **strict subset** of the checker's rejections (fire only on inputs the checker also rejects). Extend `check_cluster_completeness` (`disposition_overlay.py:417–423`) with two branches, guarded by `resolved_conclusion` **and non-delete** (matching the amended P3: "reject both N/A states for resolved non-delete conclusions"):

```
non_delete = (row.get("action_class") != "delete")
for dim in sorted(_gate_required_dims(row, manifest)):
    eff_state = _base_slot(eff_rel, dim).state
    if base not_observed and eff not_observed: emit OV015 (unresolved, no overlay)    # unchanged
    elif dim == "consumer_evidence.runtime_logs"  and eff_state == "not_applicable" and resolved_conclusion:   # #102 (unchanged; runtime_logs has no delete exception)
        emit OV015
    elif dim == "consumer_evidence.static_repo"   and eff_state == "not_applicable" and resolved_conclusion and non_delete:   # NEW #103
        emit OV015 "static_repo=not_applicable is not a resolved state for a resolved consumer_disposition"
    elif dim == "consumer_evidence.external_clients" and eff_state == "not_applicable" and resolved_conclusion and non_delete:  # NEW #103
        emit OV015 "external_clients=not_applicable is not a resolved state for a resolved non-delete consumer_disposition"
```
No exposure predicate is consulted (rev 3: there is no waiver). The `non_delete` guard keeps the mirror silent on every delete row, so the preserved delete exception (`external_clients=N/A` + exposure false) is never early-blocked; delete-row N/A misuses are rejected checker-side with no receipt — by SP027 on accepted delete, and by SP022's strict branch on a non-accepted delete row carrying a resolved conclusion (rev 3.1) — the mirror is partial there by design, exactly as it already is for `query_failed`/`stale`. (A delete `static_repo=N/A` is likewise SP027+SP022-red without an early mirror.) `static_repo` and `external_clients` are already in `_gate_required_dims` for a resolved conclusion (via `_CONSUMER_REQUIRED_EXPANSION`, `disposition_overlay.py:389`).

### 6c. P6 removed, P7 deferred — and the recorded SP027 semantic question
- **P6 (rev-2 "temporal coverage") is REMOVED.** Its claim to close the interval gap was **falsified** (operator finding, ground-verified): OV022 only ever evaluates rows whose `external_clients` N/A arrives **via overlay** — `external_na_oids` is built solely from parsed overlay docs (`disposition_overlay.py:502, 548`), and OV022 defers when no observed-false exposure *overlay* window exists (`:343, :363`). A schema-valid **base census** carrying `external_clients=not_applicable` + `in_data_api=observed false` never enters OV022 at all, passes semantic enforcement today (green regression `tests/test_check_disposition.py:346`), and its exposure observation proves only the census instant — not the surrounding consumer window. Base-only exposure therefore **cannot establish temporal coverage**, and rev-2's P6 would have been advertised as closing a gap it did not close. With P2 rejected there is no new waiver to guard, so P6 is removed rather than repaired.
- **P7 (waiver-conditional `_gate_required_dims`) is DEFERRED to a separate correction.** It is under-specified — `_gate_required_dims(row, manifest)` (`disposition_overlay.py:378`) receives no effective per-relation state, so the proposed condition cannot be computed at its call site without a signature/plumbing change — and it **loosens** a currently fail-safe delete over-block, contradicting this packet's "cannot loosen any existing pass" guarantee (§7). It is not needed to close the #103 false-green. The pre-existing OV015-red/checker-green delete divergence remains documented, fail-safe, and untouched.
- **Recorded SP027 semantic question (separate packet; NOT changed here):** the accepted-delete `external_clients` exposure exception carries (a) the same inventory-breadth objection that rejected P2, and (b) the verified base-census temporal bypass above (including OV022's `:363` defer comment "SP027 denies it", which is inaccurate for the base-census path — SP027 grants it). Correcting it would invalidate a ratified exception and its tests (`_delete_external_na_unexposed`), so it must be an **explicit SP027 policy correction** with its own ratification, not a rider on #103.

**Two-layer invariant (stated precisely; must be explicit tests via SEPARATE layer calls — the full CLI stops after OV015):**
1. **No false green (the security property, scoped precisely):** for every row carrying a **resolved conclusion**, a receipt is written only if BOTH the OV gates and the checker pass; SP022/SP027 are authoritative and reject every non-observed `static_repo`/`external_clients` state, **modulo exactly one carve-out: `external_clients=not_applicable` on an accepted delete, which the ratified SP027 exposure-false exception governs**. No other N/A on these dims can reach a receipt.
2. **Subset on the NEW N/A mirror branches:** every input they reject, the checker also rejects (both fire on resolved non-delete N/A, which SP022 rejects unconditionally in rev 3 — no predicate divergence is possible because neither layer consults one).
3. **What is NOT claimed:** OV015 is a *partial* early-warning mirror — `query_failed`/`stale`, delete-row N/A misuses, and delete `static_repo=N/A` are checker-red but mirror-silent by design (no receipt results either way). The pre-existing delete/in_data_api over-requirement (P7, deferred) means "OV015-rejects ⟹ checker-rejects" does not hold globally today; it does hold for the #103 branches.

## 7. Current-vs-proposed behavior & compatibility impact

| scenario (resolved conclusion) | current | proposed (rev 3) |
|---|---|---|
| non-delete, `static_repo=not_applicable` | GREEN (seam) | **SP022 (+OV015)** |
| non-delete, `external_clients=not_applicable`, `in_data_api` observed **true** | GREEN (seam) | **SP022 (+OV015)** — the exploit |
| non-delete, `external_clients=not_applicable`, `in_data_api` observed **false** | GREEN (seam) | **SP022 (+OV015)** — **rev-3 change**: no waiver for change actions |
| non-delete, `external_clients` = not_observed / query_failed / stale | SP022 (generic fall-through) | SP022 (explicit branch; same outcome) |
| `static_repo=observed` + `external_clients=observed` | GREEN | GREEN (baseline preserved) |
| voluntarily resolved `retain`, either dim N/A | GREEN (seam) | **SP022** (conclusion-based; reaches it) |
| unresolved retain, both N/A | GREEN | GREEN (loop off) |
| **accepted** `delete`, `external_clients=not_applicable` + exposure observed **false** | GREEN (SP027 exception) | **GREEN — preserved verbatim** (the state+status-scoped carve-out defers exactly this to SP027; regression `:346` untouched) |
| **accepted** `delete`, `external_clients` = not_observed / query_failed / stale | SP022 (generic fall-through) **and** SP027 | **SP022 and SP027 — preserved** (rev 3.2: the carve-out is N/A-only, so today's dual diagnostic survives; rev 3.1 would have dropped the SP022 half) |
| **accepted** `delete`, `static_repo=not_applicable` | SP027 red | SP027 red **and** SP022 red (consistent; no contradiction) |
| **non-accepted** `delete` row w/ voluntary resolved conclusion, `external_clients` = N/A / not_observed / query_failed / stale | N/A: GREEN (seam); others: SP022 (generic fall-through) | **SP022 (all four states)** — the carve-out is accepted-delete-scoped, so SP027-unseen rows stay SP022-owned (rev 3.1; an unscoped carve-out would have LOOSENED the three non-N/A states) |

**Compat impact: low.** No disposition decisions are applied to prod (the main lane's OBS work is held on Supabase support; nothing beyond census has run). The only breakage is in-repo **fixtures/example decisions** that relied on the seam — the implementation phase must sweep `tests/` and any sample decision files and correct them to `observed`. This is a **pure gate tightening**: with P7 deferred and no new waiver introduced, no input that fails today passes under rev 3 — the "cannot loosen any existing pass" guarantee holds (it did NOT hold under rev-2's P7, one reason P7 was deferred).

## 8. Representative boundary-test plan (NOT a Cartesian grid)

Legend: **[NEW-NEG]** = must be RED against the unmodified enforcement (locks the fix); **[PRESERVE]** = must be GREEN before AND after (locks no-loosening / no-over-block).

Checker (`test_check_disposition.py`):
1. **[NEW-NEG]** `harden`, `static_repo=not_applicable` → SP022
2. **[NEW-NEG]** `harden`, `external_clients=not_applicable`, `in_data_api` observed **false** → SP022 — **the rev-3 boundary** (the case rev 1/2 would have greened; locks "no waiver for change actions")
3. **[PRESERVE]** **accepted** `delete`, `external_clients=not_observed` → SP022 **and** SP027 (today's dual diagnostic; locks the **state** conjunct of the carve-out — a state-blind carve-out would drop the SP022 half — operator Finding 2 restructure; non-delete `external_clients=not_observed` → SP022 is already proven by existing coverage)
4. **[NEW-NEG]** **voluntarily resolved `retain`** (`no_consumer`), `external_clients=not_applicable` → SP022 (conclusion-based enforcement reaches it — operator test correction)
5. **[NEW-NEG]** accepted `delete`, `static_repo=not_applicable` → SP027 **and** SP022 (both fire; assert both codes; SP022 half is new)
6. **[PRESERVE]** accepted `delete`, `external_clients=not_applicable` + `in_data_api` observed **false** → **GREEN** (the ratified SP027 exception — `_delete_external_na_unexposed` analog; locks the exception survives; kept SEPARATE from case 5 per the operator correction)
7. **[PRESERVE]** unresolved `retain` (conclusion null), both dims N/A → **GREEN** (loop off)
11. **[NEW-NEG]** **proposed** `delete` row carrying a voluntary resolved conclusion, `external_clients=not_applicable` → **SP022** (SP016 may also be present — assert SP022 ∈ codes, not exact-set) — locks the **status** conjunct (a status-blind carve-out would green this, since SP027 never runs on non-accepted rows; rev-3.1's original `not_observed` variant started green and proved nothing — operator Finding 2)

Cases 3, 5, 6, 11 together pin all three conjuncts of the carve-out (state, action, status).

Overlay loader (`test_overlay_loader.py`, e2e signed-overlay, assert `rc==1 && OV015 in out && no receipt` unless noted):
8. **[NEW-NEG]** **voluntarily resolved `retain`** + signed `static_repo=not_applicable` overlay → OV015, no receipt (proves the mirror is conclusion-based, not action-gated — operator amendment; harden coverage of the same branch comes via case 10)
9. **[NEW-NEG]** signed `external_clients=not_applicable` overlay + `in_data_api` observed **false**, resolved `harden` → OV015, no receipt (mirror fires for non-delete even with exposure false — no waiver; the deliberate counterpart of checker case 6's delete-green)
10. **[NEW-NEG]** **Two-layer agreement via SEPARATE layer calls** (the full CLI stops after OV015, so it cannot witness both layers — operator test correction): for the inputs of cases 1 and 2, invoke the loader's completeness gate and `semantic_check` independently on the same effective input; assert **both** reject.
12. **[PRESERVE]** loader-level delete-waiver over-block guard: **accepted** `delete`, `external_clients=not_applicable`, `in_data_api` observed **false** with a covering overlay window, all other consumer dims observed → **NO OV015, green/receipt path intact** — locks the `non_delete` guard (a missing guard would emit OV015 and early-block the preserved ratified exception).

12-case matrix: 8 NEW-NEG (red first) + 4 PRESERVE (green throughout). **Not all twelve start red — land the matrix first, then confirm every NEW-NEG case red and every PRESERVE case green against the unmodified enforcement before implementing.** Synthetic Ed25519 keys only; never the production signing key.

## 9. Policy set — RATIFIED (operator, 2026-07-15)

**Final ruling (§11d): P1 ratified · P2 rejection ratified · P3 ratified as amended · P4–P5 ratified · P6 removal ratified · P7 deferral ratified · separate SP027 policy-debt packet confirmed.** Implementation is authorized on the rev-3.2 text, stopping at the draft PR.

| # | policy | ruling (operator review of rev 2) | rev-3 embodiment |
|---|---|---|---|
| P1 | `static_repo`: OBSERVED for every resolved conclusion, no N/A waiver | **Ratified** | §6a branch; tests 1/4(analog)/5 |
| P2 | `external_clients` exposure waiver for change actions | **REJECTED as written** — do not silently redefine `external_client_inventory` as `data_api_clients` | §5 rejection rationale (verified sources); OBSERVED required for resolved non-delete conclusions incl. voluntary retain; delete's ratified SP027 exception preserved verbatim; tests 2/4/6 |
| P3 | OV015 early N/A mirrors | **Ratified, amended**: reject BOTH N/A states for resolved **non-delete** conclusions | §6b (`non_delete` guard, no exposure predicate); tests 8/9 |
| P4 | remove the SP022-loop-dead generic N/A fall-through | **Ratified** (dead in that loop only; SP010 keeps N/A globally) | §6a explicit branches |
| P5 | `advisor_findings`/`database_deps` out of scope | **Ratified** | §3 qualifier |
| P6 | temporal coverage for a change-action waiver | **Removed** — coverage claim falsified (base-census bypass, verified); moot with P2 rejected | §6c record |
| P7 | waiver-conditional `_gate_required_dims` | **Deferred** to a separate correction — under-specified signature, and it loosens a fail-safe over-block | §6c record |
| — | broader SP027 delete-exception semantics (inventory breadth + base-census temporal bypass + inaccurate `:363` defer comment) | **Recorded separately**; explicit SP027 policy-correction packet with its own ratification | §6c third bullet + §5 verdict |

## 10. Governance / boundaries (this phase)
**RATIFIED (§11d) — implementation phase authorized.** Guardrails: offline only; no prod access, secrets, or signing; no schema edits; no further design-wide IRP (the implementation gets its planned cross-engine IRP). Sequence: **land the 12-case matrix first — confirm every NEW-NEG case red and every PRESERVE case green against the unmodified enforcement** — then SP022 + OV015 implementation → diagnostics/docs/fixture sweep → locked offline gates → cross-engine IRP of the implementation → **draft PR → STOP** (merge is a separate operator GO).

## 11. Review record

### 11d. Operator ratification of rev 3.1 → rev 3.2 (2026-07-15) — AMEND ONCE, THEN RATIFY

Verdict: policy architecture sound, no false-green remains; two Medium findings + minor text amendments, all folded here as rev 3.2:

| # | sev | finding | disposition |
|---|---|---|---|
| 1 | Med | the rev-3.1 carve-out was status-scoped but **state-blind** — it delegated ALL non-observed `external_clients` states on accepted delete to SP027, silently dropping the SP022 diagnostic that fires today on `not_observed`/`query_failed`/`stale` (fail-closed, but removes a diagnostic) | **Adopted** — carve-out now `st == "not_applicable" AND action_class == "delete" AND decision_status == "accepted"` (§6a); §7 dual-diagnostic row added |
| 2 | Med | test 11 (proposed delete + `not_observed`) starts green (SP022 already fires) — it would not detect a missing status conjunct | **Adopted** — case 11 → proposed delete + resolved conclusion + `not_applicable` → SP022 (SP016 tolerated); case 3 → accepted delete + `not_observed` → SP022 and SP027 [PRESERVE]; case 8 → voluntarily resolved retain + static_repo overlay (conclusion-based OV015); cases 3/5/6/11 pin the state/action/status conjuncts |
| — | minor | column rename (accepted delete); §2 exposed-rows wording; no-false-green invariant scoped modulo the accepted-delete N/A exception; `row.get(...)` in pseudocode; "currently ratified delete floor" phrasing; "not all twelve should fail" test-sequencing language; overlay case 8 retain variant | **All adopted** |

**Final ratification ruling:** P1 ✓ · P2-rejection ✓ · P3-as-amended ✓ · P4 ✓ · P5 ✓ · P6-removal ✓ · P7-deferral ✓ · separate SP027 policy-debt packet ✓. Implementation authorized to the draft-PR boundary; no further design-wide IRP; the implementation retains its planned cross-engine IRP. Operator verified head `7565bcf7`, clean worktree, doc-only delta from `35397326`.

### 11c. Bounded delta review of rev 2 → rev 3 (Codex gpt-5.5 xhigh, single pass, 2026-07-15)

Scoped to `git diff 2dd7443d f7722734` on this document, verified against the enforcement code. Verdict: **Not CLEAN** — 2 findings, both author-verified against the cited lines and folded as **rev 3.1**:

| # | sev | finding | disposition |
|---|---|---|---|
| 1 | High | the rev-3 SP022 delete carve-out (`action_class=="delete"` → defer to SP027) is **broader than SP027's gate** — SP027 runs only for `decision_status=="accepted"` (`check_disposition.py:465`), while the conclusion loop is status-blind (`:414`) and the schema lets any row carry a resolved conclusion (`schema:227`); a proposed/rejected delete row with `external_clients=not_observed/query_failed/stale` would be skipped by both layers — a **loosening**, falsifying §7's pure-tightening claim | **Adopted** — carve-out scoped to `action_class=="delete" and decision_status=="accepted"` (§6a); §7 row added; test 11 |
| 2 | Med | the 10-test plan never exercises the loader on the **valid** accepted-delete waiver path, so a missing `non_delete` guard (OV015 over-blocking the ratified exception) would pass all tests | **Adopted** — test 12 (accepted delete + exposure-false covering overlay → NO OV015) |

Codex additionally confirmed: the amended OV015 branches are a strict subset of checker rejections, and the §6c base-census-bypass record is accurate (`external_state` populated only from parsed overlays, `disposition_overlay.py:503/548`).

### 11b. Operator ratification review of rev 2 → rev 3 (2026-07-15)

Operator review verdict: do **not** ratify rev 2 as a complete P1–P7 package. Five findings, **all ground-verified by the author against the cited files before folding** (runbook:37; signed-overlay design:224 R-1; reconciliation:101/269/332; `_delete_external_na_unexposed` at tests:346; `disposition_overlay.py:343/363/378/502/548; rev-2 §7):

| # | sev | finding | disposition in rev 3 |
|---|---|---|---|
| 1 | High | **P2 narrows `external_clients` without authority** — the platform defines it as the broad external/integration inventory (dashboards, BI, MCP clients, desktop polling); a dormant direct-SQL/BI integration is invisible to `database_deps` and not disproven by a bounded runtime window, so `in_data_api=false` does not make the dimension inapplicable | **Adopted** — P2 rejected; OBSERVED required for resolved non-delete conclusions; §5 rewritten with the verified sources |
| 2 | High | **P6 retained a point-in-time temporal bypass** — `external_na_oids` is overlay-derived only, so a base-census `external_clients=N/A` + exposure-false never enters OV022 (and passes today per regression `:346`); base-only exposure proves an instant, not the window | **Adopted** — P6 removed (moot with P2 rejected); bypass + the inaccurate `:363` defer comment recorded in §6c as part of the separate SP027 question |
| 3 | Med | **P7 under-specified and out of tranche** — `_gate_required_dims(row, manifest)` has no effective per-relation state; and P7 loosens a fail-safe over-block, contradicting rev-2 §7's "cannot loosen any existing pass" | **Adopted** — P7 deferred; §7 guarantee restored (rev 3 is a pure tightening) |
| 4 | Low | test-plan corrections: add voluntarily resolved retain; two-layer agreement via separate layer calls (CLI stops after OV015); split delete `static_repo=N/A` from the permitted delete `external_clients=N/A`+exposure-false; drop P6 cases | **Adopted** — §8 rewritten, 10 tests |
| 5 | — | shortest-safe implementation shape (items 1–6) + bounded delta review (item 7) | **Adopted** — §4/§6/§8/§10 |

### 11a. Cross-engine review record (rev 1 → rev 2)

**Engines:** 3 independent opus adversarial refute-lenses (A predicate-reach, B two-layer consistency, C completeness — each instructed to refute, grounded read-only on the host bytes at `81d29278`) + **Codex gpt-5.5, reasoning effort xhigh** (direct `codex exec` on the host worktree; design review, so the diff-taking `exec review --base` form did not apply). 4/4 ran; 9 findings, all grounded; load-bearing ones re-verified by the author against the code before folding.

| # | source | sev | finding | disposition in rev 2 |
|---|---|---|---|---|
| 1 | Codex | high | change-action waiver under-reaches temporally: delete precedent = predicate + OV015 resolution + OV022 window coverage; rev-1 had only the point predicate | **Adopted** → §5 temporal bullet, §6c, P6 (lean YES), tests 15 |
| 2 | Lens B | med | blanket "layers never disagree" falsified by pre-existing delete/in_data_api over-requirement (OV015-red/checker-green; fail-safe) | **Adopted** → invariant restated precisely (§6c), P7 (lean YES), test 16 |
| 3 | Lens A | med | §5 credited the wrong channels for the security-definer-view case (it is caught by `database_deps`/SP013, not static_repo/runtime_logs); residual = dynamic-SQL functions, pre-existing platform-wide | **Adopted** → §5 residual bullet rewritten |
| 4 | Codex | med | "OV015 ⊆ SP022" ≠ "never disagree": query_failed/stale are SP022-red/OV015-silent by design; scope the slot-resolution equivalence to the CLI path | **Adopted** → §6c invariant items 2–3 |
| 5 | Codex | med | "whole seam" claim needs the qualifier "for resolved SP022 conclusions" (SP010 opt-in + null-conclusion retain are separate paths) | **Adopted** → §3 scope qualifier |
| 6 | Lens A | low | §6a "mirrors SP027 exactly" was false: missing `isinstance` guard → present-but-null exposure would crash instead of failing closed | **Adopted** → §6a/§6b guarded verbatim, test 17 |
| 7 | Codex | low | `advisor_findings`/`database_deps` are sibling surfaces, keep explicitly out of scope | **Adopted** → §3 qualifier, P5 |
| 8 | Codex | low | N/A fall-through is dead only inside the SP022 loop, not globally (SP010 keeps N/A) | **Adopted** → P4 rewording |
| 9 | Lens B | low (positive) | the #103 OV015 N/A branches themselves preserve the subset property under adversarial probing (base-vs-effective, dict-vs-nondict, missing slot, exposure-false paths) | Recorded; no change needed |

**Cross-engine delta:** Codex surfaced the highest-severity finding (temporal coverage — an architecture-level under-reach a code-local read misses); the opus lenses surfaced the pre-existing two-layer divergence and the channel-attribution error. Complementary, as intended. Lens C (completeness) independently converged with Codex on the seam enumeration being complete for resolved conclusions.
