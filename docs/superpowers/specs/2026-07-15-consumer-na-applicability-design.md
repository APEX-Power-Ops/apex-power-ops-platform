# Consumer-evidence `not_applicable` applicability design (issue #103, Phase 1)

**Status: DESIGN-ONLY — HELD for operator ratification. No enforcement, schema, or test edits until ratified.**
Worktree `apex-gate-correction-consumer-na`, branch `schema-placement/gate-correction-consumer-na-applicability` off `35397326` (the merged #102 gate-correction). Grounded on the code at that commit; line refs are as read this session.

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
| `external_clients` | overlay (window) | **O / N/A\*** — N/A iff `in_data_api_exposed_schema` OBSERVED `false` (NEW #103) | **O / N/A\*** (same predicate) | any† |
| `in_data_api_exposed_schema` | overlay (bool) | predicate input for the `external_clients` N/A waiver; must be OBSERVED `false` to grant it | same | — |

† For an unresolved conclusion, the SP022 loop does not fire. If the **manifest** lists `consumer_evidence` in `required_observations`, the weaker SP010 opt-in (`check_disposition.py:401–407`) still requires every dim `observed`-or-`not_applicable` — but that path is deliberately weaker (it does not assert a conclusion) and is **out of scope** for #103; it is documented here so the two paths are not conflated.

**All non-observed states are handled by the "must be OBSERVED" rows**: `not_observed`, `query_failed`, and `stale` were already rejected by the generic `if st != "observed"` fall-through; after #103 they are rejected by the explicit `static_repo`/`external_clients` branches instead (same outcome). `not_applicable` is the only state whose handling changes.

**Consequence — the generic N/A fall-through becomes dead code.** After #103 every one of the 5 `DIMS` has an explicit branch in the resolved loop, so `if st == "not_applicable": continue` (line 430) is unreachable inside the conclusion block and should be removed for clarity (policy choice P4).

## 5. Why `external_clients` gets a waiver and `static_repo` does not (the "don't auto-generalize" discipline)

- **`external_clients`** measures consumers reaching the relation through the **Data API (PostgREST) channel**. That channel exists **iff** the relation is in an API-exposed schema. When `in_data_api_exposed_schema` is OBSERVED `false`, external clients are **definitionally impossible**, so `not_applicable` is an evidence-backed state — and the predicate (`exposure observed false`) is itself independently observable/overlayable. This is precisely the SP027 waiver. Adopting it for SP022 is justified **by the dimension's semantics**, not by copying delete's rule. The waiver requires exposure OBSERVED `false` (positive evidence of non-exposure) — absent/`not_observed`/`not_applicable` exposure does **not** grant it.
- **`static_repo`** measures **static code references** in application repositories. Any extant relation *could* be referenced in code; there is **no per-relation observed predicate** that makes "static references" inapplicable. By the same reasoning #102 used for `runtime_logs` ("non-exposure does not waive it — direct consumers are still possible"), `static_repo` is **always applicable** → require OBSERVED, **no N/A waiver**. This matches SP027, which permits no `static_repo` N/A.
- **Residual limitation (noted, not fixed here):** `in_data_api_exposed_schema` is per-relation direct exposure. A non-exposed table reachable indirectly via an exposed security-definer view is not caught by the exposure predicate; that is a separate concern (a possible future "indirect exposure" dimension), explicitly out of scope. This is why the waiver is scoped to *direct* API exposure and paired with `static_repo`/`runtime_logs`/`database_deps` remaining mandatory — those channels catch consumers the exposure bit cannot see.

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
        exposed = r.get("in_data_api_exposed_schema", {})
        if st == "not_applicable" and exposed.get("state") == "observed" and exposed.get("value") is False:
            continue                          # legitimate exposure-scoped N/A (no found_consumers to count)
        emit SP022 "external_clients must be OBSERVED, or not_applicable ONLY when
                    in_data_api_exposed_schema is OBSERVED false"; continue

    # (generic `if st == "not_applicable": continue` now unreachable — remove, P4)
    if st != "observed": emit SP022 (unresolved); continue
    if ce[dimname].found_consumers > 0: observed_positive = True; (SP013 no_consumer contradiction)
```
Diagnostic code stays **SP022** (same invariant family). The exposure read mirrors SP027 exactly (`check_disposition.py:523–526`).

### 6b. OV015 (overlay loader, narrow early-warning mirror)
OV015 must remain a **strict subset** of SP022 (fire only when SP022 also rejects) so the two layers can never disagree (one green, one red). Extend `check_cluster_completeness` (`disposition_overlay.py:417–423`) with two branches, guarded by `resolved_conclusion`:

```
exp = _base_slot(eff_rel, "in_data_api_exposed_schema")
exposure_false = (exp.get("state") == "observed" and exp.get("value") is False)
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
The `external_clients` branch includes the exposure predicate so it never fires on the **legitimate** exposure-false case that SP022 permits — preserving OV015 ⊆ SP022. `static_repo` and `external_clients` are already in `_gate_required_dims` for a resolved conclusion (via `_CONSUMER_REQUIRED_EXPANSION`, `disposition_overlay.py:389`), so no change to `_gate_required_dims` is needed.

**Two-layer invariant (must be an explicit test):** for every input, `OV015-rejects ⟹ SP022-rejects`. The merge short-circuit (OV015 fires → `main()` returns before `run()`/SP022 → no receipt) means OV015 is the first gate; its subset property guarantees a rejected input never slips to a written receipt, and a legitimate input is never blocked early.

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

~14 purposeful tests. Synthetic Ed25519 keys only; never the production signing key.

## 9. Open policy choices (with leans)

- **P1 — `static_repo` N/A waiver?** Lean **NO** (require OBSERVED; no observable non-applicability predicate; consistent with `runtime_logs` #102 and SP027). Alt (allow N/A with an operator-attested reason) → lean **against**: it re-badges the fail-open, and `operator_declaration` already carries the human attestation.
- **P2 — `external_clients` waiver = SP027's exposure predicate?** Lean **YES** (justified by dimension semantics, §5; requires exposure OBSERVED `false`). This is the crux the operator flagged; adopted by justification, not auto-generalization.
- **P3 — OV015 mirrors `static_repo` + `external_clients` N/A early?** Lean **YES** (parity with the #102 `runtime_logs` mirror; keeps OV015 ⊆ SP022; preserves the no-receipt early exit). Alt (SP022-only) → simpler but loses early warning and diverges from #102.
- **P4 — remove the now-dead generic `if st == "not_applicable": continue`?** Lean **YES** (all 5 dims explicitly handled; dead code). Minor/mechanical.
- **P5 — `advisor_findings` (6th overlay path)** is a non-consumer dimension and not part of the seam → **out of scope**; stated for completeness.

## 10. Governance / boundaries (this phase)
Design-only. No edits to `check_disposition.py`, `disposition_overlay.py`, `disposition.schema.json`, or tests. No prod access, secrets, signing, apply, push, or PR. Next: adversarial cross-engine review of THIS design → **STOP for operator ratification**. Only after ratification: failing representative tests first → SP022 + OV015 implementation → diagnostics/docs → locked offline gates → cross-engine IRP → draft PR → stop before merge.
