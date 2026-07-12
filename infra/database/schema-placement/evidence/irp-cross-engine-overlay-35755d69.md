# Cross-engine IRP — Signed-Overlay Spec

## ROUND 3 — FOCUSED re-audit of rev4 @ 33199350 (Codex `ba41zm7qn` + Claude `w20hsch0h`)

**Claude focused re-audit: ADVANCE — all 6 operator areas CLOSED, no High/Medium gate defect (every claim host-grounded; OV021 single-signer closure independently re-derived). Codex: 2 NEW P2s (neither re-raises a prior finding). Both folded → rev5.**
- **Codex P2-1 → folded (OV022):** SP027's `external_clients` `not_applicable` waiver trusts `in_data_api_exposed_schema` observed=false, but rev4 only required that overlay's window be fresh — a DELETE could pair a 30-day consumer window with an API-exposure overlay whose window starts AFTER the API was disabled, waiving external-client evidence for a period the relation WAS exposed. FIX (**OV022**): the `in_data_api_exposed_schema` overlay window must COVER the derived consumer window (or at least `base_observed_at`) when relied on for the SP027 waiver.
- **Codex P2-2 + Claude below-bar → folded:** SP009 evaluates ALL cluster `src_rels`, but rev4 derived windows only for resolved/delete-conclusion relations → a `retain` cluster keeps its zero-width window → can never go green. FIX: derive for **every cluster-source relation SP009 evaluates**; OV018 fires for any with zero observed contributors. (retain fails SP009 today pre-overlay anyway — not a regression; not the first-cluster target.)
- **Claude below-bar → rev5/plan pins:** OV021 must be an UNCONDITIONAL preapply precheck (fires with zero overlays); absent CLI flag → coded `OV016` (deterministic diagnostics); OV021 canonical-equality = string-equality to `observed_at`; the 2 non-negotiable §9 acceptance tests (OV021-zero-overlay; remove-marker-restores-original-SP009).
- **Cross-engine delta:** Codex caught the API-exposure-window coherence gap Claude missed; Claude's exhaustive host-grounding confirmed all 6 areas + the OV021 single-signer closure and graded retain below-bar. Convergence trend across rounds: 3 HIGH → 1 HIGH → 0 HIGH + 2 P2.

---

## ROUND 2 — re-audit of rev2 @ e283be68 (Codex `b90bewrpo` + Claude Workflow `w8h9lninz`)

**Verdict: every rev1 fix genuinely CLOSED; ONE residual HIGH (cross-engine confirmed) + 2 MED + 2 LOW — all self-inflicted in the rev1→rev2 fold. Fail-CLOSED, no prod exposure. Fixed in rev3.**
- **Finding 1 (HIGH, both engines):** OV017 (`S<=base_observed_at<=E`) + retained SP009 `e<=observed_at` force `E==base_observed_at` exactly → gate never GREEN for real later-collected evidence; §9 test structurally impossible. FIX: relax SP009's `<=observed_at` on the effective-view consumer window (keep ordering `s<e` + duration); OV017 is the census anchor. Matches the ratified D2 predicate (`E<=now`, not `E<=observed_at`). Disclose as a deliberate SP009 gate change; fix §9 test + §3 prose. (Non-overlaid zero-width windows still fail `s<e` closed → no bypass; signed census can't carry a forged non-zero window.)
- **Finding 2 (MED, both engines):** `max_consumer_evidence_age_hours` can't be a new `cluster_manifest` field (schema additionalProperties:false + frozen → SP001) AND must not fail-open on absence (Invariant 7). FIX: REQUIRED CLI flag, absent/non-finite → coded reject (OV016 fires closed), receipt-bound.
- **Finding 3 (MED/LOW):** OV010 per-overlay captured_at staleness bound unnamed. FIX: reuse manifest `max_staleness_hours` (existing TA-reviewed field), `_finite()`-guarded.
- **Finding 4 (LOW):** OV018 "requires a consumer window" is a semantic-gate notion; derive/OV018 only for cluster-source relations under a resolved/delete conclusion (else over-rejects the ~113 non-overlaid).
- **Finding 5 (LOW):** §4 `uniqueItems` on object_id is not a real guard (compares whole items); intra-file uniqueness = the OV007 counter.
- **D4:** state derived `{S,E}` written as ISO-8601 strings; §5.9 re-validates effective view vs `disposition.schema.json` with rfc3339 FormatChecker.
CLOSED-confirmed (round 2): HIGH-2 (recency+coherence), HIGH-3 (evidence-readiness), all 4 Codex P2s, M7/M11/L12/L13; HIGH-1 rev1 defects reverted. Codex round-2 = same 2 P2s (Finding 1 + Finding 2). Operator ratification pending: the deliberate SP009 gate change + rev3 → full re-audit vs ratify-low-risk (D3).

---

## ROUND 1 — Signed-Overlay Spec @ 35755d69

Audit mode, Deep. Artifact: `docs/superpowers/specs/2026-07-11-signed-overlay-evidence-design.md` on `schema-placement/signed-overlay`. Engines: Codex `gpt-5.5` xhigh (`bjzmb40u3`) + Claude grounded Workflow (5 lenses + refute + synth, `wf_bfe9e6cf-612`). Verdict: **core sound; NOT safe to build as written; HOLD confirmed.** All HIGH claims re-verified against host `check_disposition.py`.

## HIGH (Claude; host-verified)
- **HIGH-1 SP009 revision guts its anchor + drops the duration floor.** (a) `ended_at <= min(captured_at)` is a tautology given OV009 (`endedᵢ<=capturedᵢ`, derived `E=min(endedᵢ)`). (b) revised §3 omits `(e−s)/3600 >= minimum_consumer_window_hours` (host lines 338–339). Replaces the census-anchored `s<e<=observed_at` (line 336) with a no-op. → regression for every non-delete cluster.
- **HIGH-2 No recency floor on the consumer window** → a `captured_at=today` overlay with a 2016 window authorizes a DELETE. SP027 (lines 499–503) bounds duration only; OV010 bounds captured_at; `database_deps` is DB-internal-only (external-blind) and not required in-window (O-1 chose the weak option). Root cause: OV009's non-strict `ended<=captured` lets `ended` float arbitrarily below `captured`; the missing primitive is a floor on `ended_at` itself.
- **HIGH-3 operator_declaration authorization is inert single-key self-attestation.** `operator_identity`/`approval_ref` appear nowhere in the checker (grep-confirmed), are dropped at merge (`consumer_evidence_dim` is additionalProperties:false), bind to nothing. For a DELETE the whole SP027 observed set except external-blind `database_deps` is single-key self-attested; one key-holder mints a fully-authorized destructive gate.

## MEDIUM (Claude)
M4 un-plumbable per-relation min(captured_at) in the effective view · M5 zero-contributor cleared window → SP009 guard false → silent pass (fail-open regression) · M6 checker must OVERWRITE the concrete `observation_window` (not a not_observed dim), contradicting OV004/OV006 — undocumented · M7 offline registry: unseeded external $ref raises `referencing.Unresolvable` (uncaught) not coded OV008; must mandate no-retrieve Registry + coded reject · M8 OV010 bound has no source + no `_finite()` guard (repeats SP015) · M9 overlays not bound to the TA-approved manifest (no manifest overlay field; receipt advisory) · M10 SP001/FormatChecker parity on the merged view unspecified → unguarded parse_dt traceback · M11 overlay verify-then-reparse TOCTOU risk (must parse-from-verified-buffer).

## Codex P2 (contract/plumbing; opposite failure mode)
- OV015 would BLOCK every resolved-conclusion cluster by demanding an impossible `database_deps` overlay → limit OV015 to permitted-overlay-target + base-`not_observed` fields; already-observed database_deps counts satisfied.
- Receipt must bind each overlay path + overlay sha256 + `.sig` sha256 (apply-runner rehash).
- `source_hash` null needs a `source_hash_not_applicable_reason` + code (OV012 only covers producing_repo_sha).
- SP028 must be step 0 (before ANY census/overlay read).

## LOW (Claude)
L12 unversioned schema `$id`, overlays carry no schema content-hash (drift) · L13 §9 can't catch shallow-copy aliasing (mandate deepcopy + unmutated-base test) · L14 OV015 under-enumerates (omits SP027 floor + SP009 prereq) · L15 intra-overlay assignment uniqueness unspecified · L16 OV006 undefined for query_failed/stale base slots.

## Operator decisions — RATIFIED 2026-07-11
- **D1 authorization (Q1→Other):** Overlays are EVIDENCE-ONLY. `operator_declaration` = attestation/provenance dim, NOT authorization. THREE separate controls: (1) overlay signature = evidence integrity; (2) manifest TA approval = technical acceptance; (3) apply-runner per-action operator write-GO (bound to target project + action + manifest-hash + gate-receipt-hash + exact-SQL-hash + expiry/nonce) = execution authorization — a FUTURE apply-runner packet, out of scope here. GREEN checker = "evidence readiness," NOT permission to execute DDL. Preserve operator_identity + attestation_ref as PROVENANCE (overlay + receipt), never as authorization. A signer holding every valid overlay STILL cannot produce an execution-authorized DELETE receipt. NO second key / approval-registry in this packet. Replace all "checker authorizes DELETE" language with "checker establishes evidence readiness."
- **D2 recency (Q2→recency + database_deps-in-window):** derived-window predicate (contributors non-empty; S=max(started), E=min(ended)): `S<E`; `E<=min(captured)`; `E<=now`; `now-E<=max_consumer_evidence_age_hours` (finite+positive); `E-S>=minimum_consumer_window_hours`; `S<=base_observed_at<=E`. DELETE also `E-S>=720h`. Keep external_clients as the external signal (flag single-source). NO new census dimension, NO disposition.schema.json mutation. Fresh signed census still required when SP008 says stale.
- **D3 process (Q3→revise + re-IRP):** revise spec, re-run FULL cross-engine IRP; no writing-plans until the revised spec has NO unresolved HIGH.
- **Revision checklist (fold ALL):** SP028 step-0; read-once + parse exact verified bytes; reject zero contributors; only checker-derived window update (overlays still can't assign observation_window); keep SP009 ordering+duration; reject stale even when captured_at current; `_finite()` on every age/duration/staleness param; registry+format failures → coded OV diagnostics (no uncaught); bind overlay schema $id+version+content-SHA in receipt; bind each overlay path+raw-SHA+sig-SHA+signer+source-hash; add source_hash_not_applicable_reason (required iff source_hash null); OV015 fix (base-observed database_deps satisfies; only unresolved permitted-overlay-targets need overlays); operator_identity/attestation_ref = provenance not authz; a signer with every valid overlay cannot produce an execution-authorized DELETE receipt.
- **Adversarial tests (add to §9):** decade-old window on a fresh overlay; database_deps observed outside derived window; empty contributor set; NaN/Inf recency; replayed overlay vs a DIFFERENT census; duplicate-equal assignments; verify-then-file-swap; valid operator overlay WITHOUT manifest TA approval; valid overlays+manifest but NO operator execution authorization; DELETE window < 30d.

---

## ROUND 3 — FOCUSED DELTA PROOF of rev5 @ 1916e607 (range `33199350..1916e607`; Claude host-grounded, independent of the Codex recommendation)

Operator directed an independent focused proof of the rev-5 delta (OV022 + all-cluster window derivation + OV021 unconditional) against 10 obligations before ratifying — *"folding ≠ independently proving closed."* Every obligation verified against BOTH the real spec text AND the live `infra/database/schema-placement/check_disposition.py` on the overlay worktree (off main `7c9a97ca`). **Verdict: CLEAN — 0 High, 0 Medium gate defect. rev-5 RATIFIED.** Three LOW clarity/correctness items carried into the writing-plan as Global Constraints + pinned negative tests (none is a gate-bypass; every one is fail-closed).

**Grounding anchors (real `check_disposition.py`):**
- SP027 block is **delete-gated**: `L435  if row.get("action_class") == "delete" and row.get("decision_status") == "accepted"`.
- external_clients waiver: `L493  if ext.get("state") == "not_applicable"` → `L494-496 requires in_data_api_exposed_schema {state:"observed", value is False}` else SP027.
- consumer dims OBSERVED `L489-491`; 720h delete floor `L500-503`.
- Overlay `observation_window {started_at, ended_at}` is a **top-level field on EVERY overlay document** (§4 contract), so the observed_bool `in_data_api` overlay carries one → OV022 is well-founded (not referencing a non-existent field). `(dimension, object_id)` uniqueness via the **OV007 loader counter** → the "exact assignment" lookup is unique.

| # | Obligation | Verdict | Evidence / plan-pin |
|---|---|---|---|
| 1 | OV022 only for delete ∧ external_clients not_applicable ∧ in_data_api observed-false | **CONFIRMED** | `L435` delete-gate + `L493` not_applicable + `L494-496` observed-false; OV022 text ties to "SP027 delete floor relies on the external_clients not_applicable waiver". Plan-pin **T1**: state explicitly OV022 is NOT evaluated when external_clients is observed. |
| 2 | Window from the exact `(in_data_api, object_id)` overlay assignment, not any exposure overlay | **CONFIRMED** | §4 one-dimension-per-overlay + OV007 `(dim,object_id)` uniqueness → unique doc-level `observation_window` lookup keyed by the assigned object_id. Pin test **T-obl2**. |
| 3 | Coverage inclusive: `started_at ≤ S ∧ ended_at ≥ E` | **CONFIRMED** | Delta text verbatim: `started_at <= S` and `ended_at >= E`. |
| 4 | Missing provenance / missing exposure overlay / stale / partial → fail-closed | **CONFIRMED** | missing in_data_api overlay → SP027 fires (state not observed-false); stale → OV010 per-overlay `captured_at`; partial coverage → OV022; absent provenance marker → original SP009. Pin tests **T-obl4a/b**. |
| 5 | external_clients observed → OV022 not invoked | **CONFIRMED** (fail-closed over-reject risk only, not a gate-bypass) | OV022 keyed to the not_applicable waiver; the observed path never relies on it. Plan-pin **T1** + negative test **T-obl5**. |
| 6 | Every unique cluster-source relation derived once, retain included | **CONFIRMED** | Delta: "for every cluster-source relation … retain included"; SP009 runs on every `src_rel`. |
| 7 | Duplicate src objects across decisions → no dup derivation / no conflicting markers | **CONFIRMED** (idempotent) | `derived_window_object_ids` is a **set** (marker dedup); same object_id → same contributors → identical window. Plan-pin **T3**: derive once per UNIQUE object_id; pin idempotency test **T-obl7**. |
| 8 | Non-cluster relations untouched | **CONFIRMED** | Delta: non-cluster keep zero-width default, not over-rejected; `copy.deepcopy`, base census never mutated. |
| 9 | Valid retain fixtures reach evidence-ready green | **CONFIRMED** | §9 pinned test: retain + covering overlays → green. |
| 10 | OV021 runs with zero overlay inputs | **CONFIRMED** | Delta: "UNCONDITIONAL … runs even with zero `--overlay` inputs"; §9 pinned test present. |

**Cross-engine delta.** Codex's focused pass (operator-relayed recommendation) found no new High/Medium and judged both changes correctly scoped + fail-closed except the intended retain-reachability alignment. Claude's independent host-grounded proof confirms all 10 against the real SP027 code and adds three LOW plan-pins (OV022 trigger-scoping crispness, exact-assignment lookup test, unique-object_id dedup) plus the full negative-test matrix. Convergence across rounds: **3 → 1 → 0 High; focused delta = 0/0.**

**Plan-pinned negative tests (writing-plan §9).** OV022-fires-when-window-not-covering · external_clients-observed→no-OV022 · missing-in_data_api-overlay→SP027 · stale-in_data_api-overlay→OV010 · window-sourced-from-the-specific-assignment · retain-no-overlay→OV018 · retain-with-covering→green · duplicate-src-object→single-derivation-one-marker · OV021-zero-overlay · remove-marker→original-SP009.

**Three LOW spec-clarity items → writing-plan Global Constraints (not spec-blocking; carried to the binding build contract):** T1 (OV022 evaluated only for a delete-conclusion source relation whose external_clients overlay resolves to `not_applicable`; observed → not evaluated); T2 (window looked up from the `(in_data_api_exposed_schema, object_id)` assignment via OV007 uniqueness); T3 (window derived once per **unique** source object_id; the provenance set dedups markers).

---

## ROUND 4 — PLAN cross-engine audit + focused re-audit (2026-07-12)

The writing-plans deliverable (`docs/superpowers/plans/2026-07-11-signed-overlay-evidence-tooling.md`) went through a cross-engine plan audit → revision → cross-engine re-audit.

**Operator cross-engine plan audit of rev1 (`5477d706`): layering RATIFIED (unconditional loader model); plan NOT build-ready — 3 HIGH / 5 MED / 1 LOW + contributor-map-local.** All folded → **rev2 `4f2b2fce`**:
- **F1 (High)** raw docs consumed before SP001 → `validate_documents` extracted; `main()` validates the raw docs (SP001+kind) **before** the overlay loader; effective view re-validated by `run()`.
- **F2 (High)** OV009 not per-overlay → `check_observation_window()` (started<ended, ended≤captured, ended≤now) on all six dims incl. the Data-API overlay OV022 relies on.
- **F3 (High)** receipt binding incomplete → per-overlay binds path, raw+sidecar SHA-256, sidecar path, signer key_id+SPKI, dimension+object_ids+count, source_hash, schema hashes.
- **F4 (Med)** validate vs hash read different bytes → read-once `OverlayContract` (bytes+hashes+registry+validator); schemas never reopened.
- **F5 (Med)** fixtures not schema-valid / incoherent times → `_zero_census` reuses `tcd._snapshot/_rel` (all required fields); one canonical coherent fixture clock.
- **F6 (Med)** suites absent from CI → `test_overlay_schema` + `test_overlay_loader` added to the governed `suites` job.
- **F7 (Med)** OV015 unimplemented/untested → `check_cluster_completeness()` + dedicated `ov015_missing_gate_required_dimension` test.
- **F8 (Med)** offline-registry test false proof → real unseeded-`$ref` → `Unresolvable` → coded-OV008 test; no network.
- **F9 (Low)** null-reason not IFF → OV019/OV012 reject reason-with-non-null-hash too.
- **#9** contrib map on effective → passed as a separate local `contrib_by_oid` dict, never stashed on the effective view.

**Focused re-audit (instruction #10) — cross-engine.** Claude focused self-review = folds real + internally consistent (traced the fixture clock, every OV-code test↔impl path, the `OverlayContract`/`contrib_by_oid`/receipt threading, and the `semantic_check`/`run`/`build_receipt` signature deltas vs the real `check_disposition.py`; no stale API references). Codex (`codex exec review --base main`, `-m gpt-5.5`, sandbox-bypassed — the apex-jobs front door was blocked on Infisical `APEX_JOBS_PGPASSWORD`, operator custody) = **2 NEW P2s** (neither re-raising F1–F9), both folded → **rev3**:
- **P2-1:** OV022 emitted for a MISSING `in_data_api` overlay short-circuits `load_and_merge` before `run()` can fire SP027 — contradicting the ratified "missing→SP027" matrix. FIX: OV022 records the window **only** for an observed-false overlay and **defers** (missing/observed-true → SP027 denies the waiver at the semantic gate). Task 5 unit (`missing_in_data_api_defers_to_SP027`) + Task 8 e2e (g/h).
- **P2-2:** absent/non-finite `max_consumer_evidence_age_hours` checked after the per-relation OV018 short-circuit → a zero-contributor relation masks the missing flag. FIX: the recency-policy `OV016` is a **deterministic precheck at the top of `derive_windows`**, before any per-relation contributor check.

**Cross-engine delta:** Codex caught the OV022/SP027 diagnostic-coherence gap and the OV016 ordering mask that Claude's self-review missed; Claude's grounding confirmed all nine folds + the fixture/threading consistency vs the real host code. Plan convergence: 9 findings → 2 P2s → 0. **Verdict: build-ready pending the operator GO.** Implementation, evidence collection, DB access, production, A1–A3, and the apply runner remain HELD.
