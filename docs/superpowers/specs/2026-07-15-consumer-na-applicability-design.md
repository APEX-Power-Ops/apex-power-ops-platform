# Consumer-evidence `not_applicable` applicability design (issue #103, Phase 1)

**Status: DESIGN-ONLY, rev 2 — HELD for operator ratification. No enforcement, schema, or test edits until ratified.**
Worktree `apex-gate-correction-consumer-na`, branch `schema-placement/gate-correction-consumer-na-applicability` off `35397326` (the merged #102 gate-correction). Grounded on the code at that commit; line refs are as read this session.
**Rev 2** folds the adversarial cross-engine review (3 opus refute-lenses + Codex gpt-5.5 xhigh; record in §11). Key deltas vs rev 1: the `external_clients` waiver now mirrors the FULL delete-precedent architecture (predicate + OV015 resolution + OV022 temporal coverage — Codex high finding), the two-layer invariant is stated precisely (a pre-existing delete/in_data_api divergence is documented), §5's mitigation wording credits the correct channel, and the SP027 predicate is adopted with its `isinstance` guard verbatim.

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

**Resolved-conclusion CHANGE actions with no destructive floor = `harden`, `promote`, `compat`, `archive`.** These are exactly the rows exposed to the seam. `delete` also enters the loop but its SP027 floor already handles `static_repo`/`external_clients` strictly (below). A non-accepted row (proposed/rejected/unknown) with a null conclusion never enters the loop; if it carries a resolved conclusion it does (correct — the claim is what's gated).

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

**SP027 (delete floor) already does the right thing** (`check_disposition.py:513–533`): `static_repo` (and database_deps/runtime_logs/operator_declaration) must be OBSERVED; `external_clients` OBSERVED, or `not_applicable` **only when `in_data_api_exposed_schema` is OBSERVED `false`**; plus a ≥30-day window. The change actions have no equivalent.

**Concrete exploit** (same class as #102): an accepted `harden` on an API-exposed table with real external consumers → set `external_clients=not_applicable` + `static_repo=not_applicable`; the forced-observed dims read `found_consumers=0`; the row greens as `no_consumer`; a receipt is written and the harden proceeds, hiding both static-code and external API consumers.

## 4. Applicability table (proposed)

Governing principle: **a resolved `consumer_disposition` is a factual claim ("no_consumer"/"has_consumers") that requires having actually LOOKED via every channel whose applicability is not disproven by observed evidence.** `not_applicable` is legitimate only when an **observed** predicate makes the channel definitionally inapplicable to the relation. Each dimension is decided on its **own** semantics — the SP027 `external_clients` waiver is **not** generalized by default (see §5).

Legend: **O** = OBSERVED required; **O / N/A\*** = observed, or not_applicable permitted **only** under the stated observed predicate; **any** = unconstrained by this gate.

| dimension | overlayable? | resolved conclusion (harden/promote/compat/archive) | delete (SP027, unchanged) | unresolved (retain-null / non-accepted-null) |
|---|---|---|---|---|
| `operator_declaration` | overlay (window) | **O** | **O** | any (SP022 loop off)† |
| `database_deps` | base-census-only | **O** | **O** | any† |
| `runtime_logs` | overlay (window) | **O** (#102) | **O** | any† |
| `static_repo` | overlay (window) | **O** — *no N/A waiver* (NEW #103) | **O** | any† |
| `external_clients` | overlay (window) | **O / N/A\*** — N/A iff `in_data_api_exposed_schema` OBSERVED `false`, with OV015 resolution + OV022 window coverage when overlay-backed (NEW #103, P2+P6) | **O / N/A\*** (same predicate + coverage; unchanged) | any† |
| `in_data_api_exposed_schema` | overlay (bool) | predicate input for the `external_clients` N/A waiver; must be OBSERVED `false` to grant it | same | — |

† For an unresolved conclusion, the SP022 loop does not fire. If the **manifest** lists `consumer_evidence` in `required_observations`, the weaker SP010 opt-in (`check_disposition.py:401–407`) still requires every dim `observed`-or-`not_applicable` — but that path is deliberately weaker (it does not assert a conclusion) and is **out of scope** for #103; it is documented here so the two paths are not conflated.

**All non-observed states are handled by the "must be OBSERVED" rows**: `not_observed`, `query_failed`, and `stale` were already rejected by the generic `if st != "observed"` fall-through; after #103 they are rejected by the explicit `static_repo`/`external_clients` branches instead (same outcome). `not_applicable` is the only state whose handling changes.

**Consequence — the generic N/A fall-through becomes dead code.** After #103 every one of the 5 `DIMS` has an explicit branch in the resolved loop, so `if st == "not_applicable": continue` (line 430) is unreachable inside the conclusion block and should be removed for clarity (policy choice P4).

## 5. Why `external_clients` gets a waiver and `static_repo` does not (the "don't auto-generalize" discipline)

- **`external_clients`** measures consumers reaching the relation through the **Data API (PostgREST) channel**. That channel exists **iff** the relation is in an API-exposed schema. When `in_data_api_exposed_schema` is OBSERVED `false`, external clients are **definitionally impossible**, so `not_applicable` is an evidence-backed state — and the predicate (`exposure observed false`) is itself independently observable/overlayable. This is precisely the SP027 waiver. Adopting it for SP022 is justified **by the dimension's semantics**, not by copying delete's rule. The waiver requires exposure OBSERVED `false` (positive evidence of non-exposure) — absent/`not_observed`/`not_applicable` exposure does **not** grant it.
  - **Naming-breadth caveat (Codex):** the dimension's fixed `source_type` is `external_client_inventory` (`disposition_overlay.py:36`) — a name broader than "Data API channel". The Data-API-scoped reading is the one the **ratified SP027 floor already encodes** (its waiver is exactly `in_data_api` observed false), and non-API external consumers (direct SQL) are covered by the always-mandatory `runtime_logs`/`database_deps` — the same decomposition #102 relied on. Ratifying P2 ratifies this reading explicitly (see §9 P2).
  - **Temporal coverage (Codex high — adopted, P6):** the delete precedent is NOT just the point predicate. For a delete invoking the waiver, the platform also requires the `in_data_api` dimension **resolved** (`_gate_required_dims` adds it, `disposition_overlay.py:391–393` → OV015) and, when an observed-false overlay backs the waiver, its observation window must **cover the derived consumer window** (OV022, `check_delete_floor_coherence`, `disposition_overlay.py:344–369`). A point-in-time "not exposed now" must not waive evidence for a window during which the relation WAS exposed. The change-action waiver therefore mirrors the **full architecture**: predicate + OV015 resolution requirement + OV022 coverage, extended from `delete_src_oids` to **all waiver-invoking rows** (resolved conclusion ∧ `external_clients=not_applicable`), with delete's existing base-census-point-observation subtlety inherited unchanged (base census observes `in_data_api` at `observed_at`, anchored within the derived window by OV017/OV021 — same trust basis as delete today, no weaker and no stronger).
- **`static_repo`** measures **static code references** in application repositories. Any extant relation *could* be referenced in code; there is **no per-relation observed predicate** that makes "static references" inapplicable. By the same reasoning #102 used for `runtime_logs` ("non-exposure does not waive it — direct consumers are still possible"), `static_repo` is **always applicable** → require OBSERVED, **no N/A waiver**. This matches SP027, which permits no `static_repo` N/A.
- **Residual limitation (noted, not fixed here — wording corrected per Lens A):** `in_data_api_exposed_schema` is per-relation direct exposure. A non-exposed table `T` reachable indirectly via an exposed **security-definer view** `V` is not caught by the exposure predicate — but it **is** caught by the always-mandatory **`database_deps`** (the V→T `pg_depend` edge yields `found_consumers ≥ 1`, and SP013 at `check_disposition.py:437–440` contradicts a `no_consumer` claim). `static_repo` (application-repo scan) does NOT see in-DB view/function bodies, and `runtime_logs` only sees them if invoked in-window — do not credit those channels for this case. The **truly residual** slip-past is a **dynamic-SQL security-definer function** (`EXECUTE 'SELECT … FROM t'`): no `pg_depend` edge, not in the app repo, runtime-visible only if it fired in-window. That blind spot is **pre-existing and platform-wide** — the shipped SP027 delete floor carries the identical predicate with the identical residual — so #103 does not widen it. A future "indirect exposure" dimension remains the tracked follow-up, explicitly out of scope.

**SP027 re-evaluation verdict:** the existing SP027 `external_clients` non-exposure waiver is **sound** and is adopted verbatim in predicate (exposure OBSERVED `false`) for the SP022 resolved-conclusion path. SP027 itself is unchanged.

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

    if dimname == "external_clients" and st != "observed":                            # NEW #103
        exposed = r.get("in_data_api_exposed_schema")
        if st == "not_applicable" and isinstance(exposed, dict) \
                and exposed.get("state") == "observed" and exposed.get("value") is False:
            continue                          # legitimate exposure-scoped N/A (no found_consumers to count)
        emit SP022 "external_clients must be OBSERVED, or not_applicable ONLY when
                    in_data_api_exposed_schema is OBSERVED false"; continue

    # (generic `if st == "not_applicable": continue` now unreachable — remove, P4)
    if st != "observed": emit SP022 (unresolved); continue
    if ce[dimname].found_consumers > 0: observed_positive = True; (SP013 no_consumer contradiction)
```
Diagnostic code stays **SP022** (same invariant family). The exposure predicate copies SP027's **`isinstance`-guarded** form verbatim (`check_disposition.py:523–526`) — the guard is load-bearing (Lens A): a present-but-JSON-null `in_data_api_exposed_schema` must deny the waiver fail-closed, not raise `AttributeError`.

### 6b. OV015 (overlay loader, narrow early-warning mirror)
OV015 must remain a **strict subset** of SP022 (fire only when SP022 also rejects) so the two layers can never disagree (one green, one red). Extend `check_cluster_completeness` (`disposition_overlay.py:417–423`) with two branches, guarded by `resolved_conclusion`:

```
exp = _base_slot(eff_rel, "in_data_api_exposed_schema")
exposure_false = (isinstance(exp, dict) and exp.get("state") == "observed" and exp.get("value") is False)
for dim in sorted(_gate_required_dims(row, manifest)):
    eff_state = _base_slot(eff_rel, dim).state
    if base not_observed and eff not_observed: emit OV015 (unresolved, no overlay)    # unchanged
    elif dim == "consumer_evidence.runtime_logs"  and eff_state == "not_applicable" and resolved_conclusion:   # #102
        emit OV015
    elif dim == "consumer_evidence.static_repo"   and eff_state == "not_applicable" and resolved_conclusion:   # NEW #103
        emit OV015 "static_repo=not_applicable is not a resolved state for a resolved consumer_disposition"
    elif dim == "consumer_evidence.external_clients" and eff_state == "not_applicable" and resolved_conclusion and not exposure_false:  # NEW #103
        emit OV015 "external_clients=not_applicable requires in_data_api_exposed_schema observed false"
```
The `external_clients` branch includes the (guarded) exposure predicate so it never fires on the **legitimate** exposure-false case that SP022 permits. `static_repo` and `external_clients` are already in `_gate_required_dims` for a resolved conclusion (via `_CONSUMER_REQUIRED_EXPANSION`, `disposition_overlay.py:389`).

### 6c. OV022 + `_gate_required_dims` extension (temporal coverage, P6 — NEW #103, from Codex high finding)
Mirror the delete-waiver architecture for **every** waiver-invoking row, and make the requirement **uniformly conditional on waiver invocation**:

```
# _gate_required_dims: replace the delete-specific in_data_api add with a waiver-scoped one
if resolved_conclusion or action_class == "delete":
    req.update(_CONSUMER_REQUIRED_EXPANSION)
if external_clients (effective) is not_applicable and (resolved_conclusion or action_class == "delete"):
    req.add("in_data_api_exposed_schema")            # required WHEN the waiver is invoked (P7 note below)

# check_delete_floor_coherence -> check_waiver_coherence: iterate (delete_src_oids | resolved_conclusion_src_oids) & external_na_oids
#   unchanged logic: when an observed-false in_data_api OVERLAY backs the waiver, its window must cover
#   the derived consumer window (OV022); no observed-false overlay -> defer (SP022/SP027 deny the waiver
#   unless the BASE census supplies exposure observed-false, anchored by OV017/OV021 — delete's existing
#   trust basis, inherited unchanged).
```

**Interaction with the pre-existing divergence (Lens B, P7):** today `_gate_required_dims` adds `in_data_api_exposed_schema` **unconditionally** for delete (`disposition_overlay.py:391–393`), so a valid delete with `external_clients` OBSERVED and `in_data_api` base-not_observed is OV015-blocked while the checker is green — a **pre-existing, fail-safe** (over-block, never a receipt leak) divergence #103 inherits but did not create. Conditioning the add on waiver-invocation (above) fixes it and implements the extension in one move. If P7 is declined, keep delete's unconditional add and extend it unconditionally to resolved conclusions — strictly more over-blocking, still fail-safe.

**Two-layer invariant (stated precisely — Lens B + Codex; must be explicit tests):**
1. **No false green (the security property):** a receipt is written only if BOTH the OV gates and the checker pass; SP022 is authoritative and rejects every non-observed state, so no N/A (or any other non-observed state) on these dims can reach a receipt.
2. **Subset on the N/A mirror (the #103 delta):** every input the NEW OV015 N/A branches reject, SP022 also rejects — adversarially verified for the proposed branches (both layers read the identical in-memory effective snapshot; `r.get(...)` on a source relation and `_base_slot(eff_rel, ...)` resolve the same slot in the CLI path, where `run()` receives the post-merge effective snapshot).
3. **What is NOT claimed:** OV015 is a *partial* early-warning mirror — `query_failed`/`stale` are SP022-red but OV015-silent **by design** (documented at `disposition_overlay.py:397+`; no receipt results, the checker still rejects). And the pre-existing delete/in_data_api over-requirement (P7) means "OV015-rejects ⟹ checker-rejects" does not hold globally today; it holds for the #103 branches, and holds globally if P7 is ratified.

## 7. Current-vs-proposed behavior & compatibility impact

| scenario (resolved conclusion) | current | proposed |
|---|---|---|
| `static_repo=not_applicable` | GREEN (seam) | **SP022 (+OV015)** |
| `external_clients=not_applicable`, `in_data_api` observed **true** | GREEN (seam) | **SP022 (+OV015)** — the exploit |
| `external_clients=not_applicable`, `in_data_api` observed **false** | GREEN | GREEN (legitimate waiver) |
| `external_clients=not_applicable`, `in_data_api` not_observed / N/A | GREEN | **SP022 (+OV015)** — waiver denied |
| `static_repo=observed` + `external_clients=observed` | GREEN | GREEN (baseline preserved) |
| unresolved retain, both N/A | GREEN | GREEN (loop off) |
| `delete` with `static_repo`/`external_clients` N/A | SP027 already red | SP027 red **and** SP022 red (consistent; no new contradiction) |

**Compat impact: low.** No disposition decisions are applied to prod (the main lane's OBS work is held on Supabase support; nothing beyond census has run). The only breakage is in-repo **fixtures/example decisions** that relied on the seam — the implementation phase must sweep `tests/` and any sample decision files and correct them to `observed` (or exposure-false for `external_clients`). This is a gate **tightening**; it cannot loosen any existing pass.

## 8. Representative boundary-test plan (NOT a Cartesian grid)

Checker (`test_check_disposition.py`, NEG unless noted), one representative action class per cell:
1. `harden`, `static_repo=not_applicable` → SP022
2. `harden`, `external_clients=not_applicable`, `in_data_api` observed **true** → SP022 (the exploit)
3. `harden`, `external_clients=not_applicable`, `in_data_api` observed **false** → **GREEN** (legitimate waiver)
4. `harden`, `external_clients=not_applicable`, `in_data_api` **not_observed** → SP022 (waiver denied)
5. `archive` (forced no_consumer), `static_repo=not_applicable` → SP022
6. `compat` (forced has_consumers), `external_clients=not_applicable` + exposed true → SP022
7. `promote`, `static_repo=observed` + `external_clients=observed` → **GREEN** (baseline)
8. `harden`, `static_repo=query_failed` → SP022 (non-observed still rejected via the new branch)
9. `delete`, `static_repo=not_applicable` → SP027 **and** SP022 (both fire; assert both codes)
10. unresolved `retain` (conclusion null), both `static_repo`/`external_clients` N/A → **GREEN**

Overlay loader (`test_overlay_loader.py`, e2e signed-overlay, assert `rc==1 && OVxxx in out && no receipt`):
11. signed `external_clients=not_applicable` overlay + `in_data_api` observed **true**, resolved conclusion → OV015, no receipt
12. signed `static_repo=not_applicable` overlay, resolved conclusion → OV015, no receipt
13. signed `external_clients=not_applicable` overlay + `in_data_api` observed **false**, resolved conclusion → **NO OV015** (legitimate; receipt allowed) — the false-positive guard
14. **Two-layer agreement**: for cases 1/2/12, assert OV015 and SP022 both reject the same input (never one-green-one-red).

Rev-2 additions (from the review):
15. **P6/OV022 coverage**: waiver invoked on a `harden`, backed by an observed-false `in_data_api` **overlay** whose window does NOT cover the derived consumer window → OV022, no receipt; the same with a covering window → green.
16. **P7 boundary**: valid `delete` with `external_clients` **OBSERVED** and `in_data_api` base-not_observed → with P7 ratified, NO OV015 (in_data_api no longer gate-required when the waiver is not invoked) AND checker green — the pre-existing divergence closed; regression-locks the waiver-conditional `_gate_required_dims`.
17. **Guard**: `in_data_api_exposed_schema` present-but-null on the source relation, `external_clients=not_applicable`, resolved conclusion → SP022 (waiver denied fail-closed, no crash).

~17 purposeful tests. Synthetic Ed25519 keys only; never the production signing key.

## 9. Open policy choices (with leans)

- **P1 — `static_repo` N/A waiver?** Lean **NO** (require OBSERVED; no observable non-applicability predicate; consistent with `runtime_logs` #102 and SP027). Alt (allow N/A with an operator-attested reason) → lean **against**: it re-badges the fail-open, and `operator_declaration` already carries the human attestation.
- **P2 — `external_clients` waiver = SP027's exposure predicate?** Lean **YES** (justified by dimension semantics, §5; requires exposure OBSERVED `false`, `isinstance`-guarded verbatim). Ratifying P2 also ratifies the **Data-API-scoped reading** of `external_clients` explicitly (its `source_type` name `external_client_inventory` is broader; direct-SQL externals are covered by mandatory `runtime_logs`/`database_deps` — Codex naming-breadth caveat, §5).
- **P3 — OV015 mirrors `static_repo` + `external_clients` N/A early?** Lean **YES** (parity with the #102 `runtime_logs` mirror; keeps the N/A mirror ⊆ SP022; preserves the no-receipt early exit). Alt (SP022-only) → simpler but loses early warning and diverges from #102.
- **P4 — remove the now-dead generic `if st == "not_applicable": continue`?** Lean **YES** — dead **inside the SP022 conclusion loop only** (all 5 dims explicitly branched there). NOT globally dead: SP010 still intentionally accepts N/A and the schema keeps the state (Codex). Minor/mechanical.
- **P5 — `advisor_findings` (6th overlay path)** is a non-consumer dimension and not part of the seam; `database_deps` is forced-observed and non-overlayable → both **out of scope**; stated for completeness.
- **P6 — temporal coverage for the change-action waiver (Codex high)?** Lean **YES**: mirror the FULL delete architecture — waiver-invoking rows get `in_data_api` gate-required (OV015) and OV022 window coverage when an observed-false overlay backs the waiver (§6c). Alt (point-in-time predicate only, rev-1 form) → lean **against**: "not exposed now" could waive evidence for a window during which the relation WAS exposed — a strictly weaker gate than the delete precedent for a less-destructive but still consumer-hiding action.
- **P7 — condition `_gate_required_dims`' `in_data_api` add on waiver invocation (fixing the pre-existing delete over-block, Lens B)?** Lean **YES**: makes the requirement uniform ("waiver invoked ⟹ exposure evidence required"), closes the documented OV015-red/checker-green divergence, and P6's extension lands in one move. Alt (keep delete unconditional, extend unconditionally) → strictly more over-blocking; fail-safe but noisier. Behavior change to existing delete handling either way — flagged for explicit ratification.

## 10. Governance / boundaries (this phase)
Design-only. No edits to `check_disposition.py`, `disposition_overlay.py`, `disposition.schema.json`, or tests. No prod access, secrets, signing, apply, push, or PR. The adversarial cross-engine review has RUN (§11) and its findings are folded into this rev 2 → **STOP for operator ratification**. Only after ratification: failing representative tests first → SP022 + OV015 (+P6/P7 overlay) implementation → diagnostics/docs → locked offline gates → cross-engine IRP → draft PR → stop before merge.

## 11. Cross-engine review record (rev 1 → rev 2)

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
