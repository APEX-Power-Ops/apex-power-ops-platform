# Cross-engine IRP — Overlay Evidence Publication design

Artifact under review: `docs/superpowers/specs/2026-07-12-overlay-evidence-publication-design.md`
Branch `schema-placement/overlay-publication` off `main a47161fc`.

## ROUND 1 — rev1 design (`9f9f1c75`), cross-engine + operator audit — 2026-07-12

Three independent engines audited rev1 against the grounded merged host code (`disposition_overlay.py`
OV001–OV022, `overlay.schema.json`, `disposition.schema.json`, `disposition_signing/_trust/_provenance`,
`collect_disposition`, `verify_census`, `ci/verify_committed_census.sh`, `CENSUS_RUNBOOK.md`):
**Codex** (`codex exec review --base main -m gpt-5.5`, exit 0), a **Claude grounded-audit workflow**
(5 lenses × grounded auditors → adversarial refute stage; 18 agents, 0 errors), and the **operator's**
own audit. Findings deduped and adversarially verified below; only CONFIRMED/PARTIAL are folded into rev2.

### Convergence (all three engines agree)

- **CI must reject MODIFY/DELETE of committed evidence** (immutable no-clobber). rev1's `--diff-filter=A`
  only verifies ADDED overlays; a modified/deleted committed overlay or `.sig` (and the same weakness in
  the census gate) bypasses verification. — *Codex P1, operator #1.* CONFIRMED.
- **Cross-overlay OV007 must span the FULL committed set**, not just the added set — the consumer's
  `check_conflict` is whole-cluster (flat `all_keys` over every assignment of every overlay), so a
  duplicate against an earlier-committed overlay for the same census passes rev1's added-only check and
  is only caught at preapply. — *Codex P2, operator #4, Claude CI-F1 + CC3 (CONFIRMED Important).*
- **OV010 `captured_at ≤ now` is unenforced by the artifact tooling.** `check_observation_window` (OV009)
  bounds `ended_at ≤ captured_at ≤` (not) `now`; the `captured_at > now` half is OV010, wired only into
  the cluster `load_and_merge`. rev1 claimed author+verifier enforce it. — *operator #6, Claude CC2 / VSA-2
  / WS-3 / F3 (CONFIRMED Important, 5-agent convergence).*

### Operator findings (all folded)

1. CI immutable-evidence gap (above). 2. **Census signature ≠ census acceptance** — must run the full
`verify_census.check_census` contract (schema, target-db, scope, project, repo_sha, role markers,
query-bundle, counts, query-failure), not just the signature. 3. **Source evidence hashed but not durably
verifiable** — the evidence PR commits only overlays+sidecars; CI cannot rehash `source_hash` or confirm
`source_locator`; need a committed canonical source record. 4. Cross-overlay dup (above). 5. **Author can
publish with a wrong private key** — `DISPOSITION_SIGNING_KEY` may be a valid Ed25519 key that is NOT the
pinned signer; author must compare its public fingerprint to the resolved signer and verify the generated
sidecar in-memory before publishing. 6. OV010 unimplementable by the artifact interface (above). 7.
**Canonical-path coverage** — an overlay-kind doc under another filename evades the glob; orphan sidecars
and ambiguous multiple-census matches must be rejected. 8. **Author provenance must be mandatory**
(clean checkout + expected merged SHA) before reading the key, all dimensions.

### Claude IRP — additional grounded findings (verdicts from the adversarial stage)

- **CI-F2 — null `producing_repo_sha` shell-unsafe** (CONFIRMED Important): null for the 3 FORBIDDEN dims;
  a naive extractor prints `None`, and `git merge-base --is-ancestor None HEAD` under `set -euo pipefail`
  aborts/false-FAILs those overlays. Needs null→skip (safe: step-4 re-verifies at HEAD).
- **CC1 / DAG-F4 — `producing_repo_sha` identity** (CONFIRMED Important): the author computes
  `git_head_sha(schema-pub checkout)` → the AUTHOR's HEAD, but rev1's §5 labels it the *external scanned
  repo* commit. If a plan records the external SHA, the consumer accepts (OV012 only checks 40-hex) but
  the CI ancestor/tooling-diff (valid only for a schema-pub commit) REJECTS a conformant overlay. Fix:
  `producing_repo_sha` = author's clean-merged-main HEAD; external roots+SHAs live in the source record.
- **DAG-F1 / CC4 — verifier fail-closed** (CONFIRMED Minor): the standalone verifier must replicate the
  consumer's `isinstance(doc, dict)` guard + schema-error short-circuit, else a signed non-object /
  schema-invalid committed overlay crashes instead of a coded OV008.
- **CI-F4 / DAG-F3 — intra-overlay dup** (CONFIRMED Important): the verifier + CI must run the flat OV007
  (incl. within a single overlay), so a hand-crafted non-author artifact's intra-overlay dup is caught.
- **VSA-3 — `build_sig_sidecar` returns a dict, not bytes** (factual): pin
  `json.dumps(build_sig_sidecar(...), indent=2, sort_keys=True).encode()` or every artifact fails OV001.
- **DAG-F5 — validate the signed bytes** (Minor): the author should validate `parse_overlay(_serialize(doc))`,
  round-tripping through the exact-signed-bytes parse guard, not just the in-memory dict.
- **VSA-1 — source-file value-silence** (PARTIAL→Nit): the author only `read→sha256`s the source file
  (never prints it), so the headline leak is refuted; but a dedicated `AO009` "source unreadable" code
  (path + `type(exc).__name__` only, no content, no stack trace) is cheap hardening worth folding.
- **VSA-4 — D3 replica fidelity** (Minor): copy the collector's `finally` temp-unlink; derive the path
  `<UTC>` from the SAME `captured_at` instant; add a sub-second/counter suffix to avoid same-second
  collisions.
- **WS-2 — OV016 freshness guidance** (CONFIRMED Minor): OV016 is measured at PREAPPLY `now` against
  `E = min(ended)` (the earliest-ending consumer window), not `captured_at`; the runbook must direct
  operators to collect consumer evidence together and run preapply within the age budget of the earliest
  `ended_at`.
- **WS-1 — window construction gap** (REFUTED): §5's shared "bracket the census instant / in_data_api at
  least as wide" rule already suffices; the missing per-dimension window column is a framing choice, not a
  gap. NOT folded.

### Cross-engine delta

Codex independently surfaced the two most consequential CI gaps (modify/delete immutability; committed-set
OV007) that the operator also flagged; the Claude panel converged on the same two AND added the
implementation-critical set the free-text engines did not name precisely: the null-`producing_repo_sha`
shell abort, the `producing_repo_sha` *identity* ambiguity (author-checkout vs external-repo), the
verifier fail-closed guards, the `build_sig_sidecar` dict→bytes pin, and the OV016 min-ended anchor. The
operator's audit added the two integrity requirements neither automated engine raised: full
`verify_census` acceptance of the base census, and a durably-committed source-evidence record. No engine's
finding contradicted another; the only over-reach (Claude WS-1) was killed by the adversarial stage.

### Operator ratifications

- **D1** reuse `disposition_overlay` checks. **D2** module names accepted. **D3** replicate the atomic
  helper in this packet (equivalent adversarial tests; census collector untouched). **D4** strengthen the
  author provenance to a MANDATORY clean merged checkout + required expected SHA.

### Verdict

rev1 NOT approved. Design-only posture is correct and the branch is clean, but the CI immutability/OV007
gaps, the census-acceptance and source-record integrity gaps, the signer-parity gap, and the OV010
misattribution must be folded. → **rev 2** (below), then a focused re-audit.

## ROUND 2 — rev2 (`bc37daa5`) focused re-audit — 2026-07-12

Focused cross-engine re-audit over the five revised areas (CI set semantics, full census acceptance,
source-evidence binding, signer parity, temporal-policy boundary): **Codex** (`codex exec review --base
main`, exit 0) + a **Claude focused-audit workflow** (5 lenses → adversarial verify; 10 agents, 0 errors).

### Round-1 closure assessment (grounded, per lens)

- **Temporal-policy boundary: CLOSED.** rev2's OV009/OV010 attribution verified verbatim against
  `check_observation_window` (no `captured_at ≤ now` bound) and the inline OV010; the verifier's
  future-half check + manifest-staleness deferral are correctly scoped; the §6 OV016 min-ended guidance is
  accurate vs `derive_windows`.
- **Signer parity: CLOSED.** `public_key_fingerprint` and `ResolvedSigner.spki_sha256` verified to be the
  same lowercase-hex SPKI-sha256 encoding (directly `==`-comparable); AO007 + AO012 close operator #5.
- **Full census acceptance: CLOSED for author + standalone verifier** (param set threads correctly;
  sig-before-parse ordering matches `verify_census.main`); **CI path had a residual** (OCA-1 below).
- **Source-evidence binding: mechanism sound, two residuals** (SB1/SB2 below). CC1/DAG-F4
  (`producing_repo_sha` = author HEAD; external roots in the record) confirmed CLOSED.
- **CI set semantics:** the dedicated lens agent returned a degenerate placeholder (recorded honestly; not
  counted as coverage). The area was independently probed by the other four lenses + Codex; a genuine
  re-run of this lens executes against the tightened spec (round-2b below).

### Round-2 findings (adversarially verified) — ALL FOLDED in the same-day tightening

- **SRC-IMMUT (Codex P2 + three independent CONFIRMED-Important verdicts): committed `evidence/source/`
  records were outside the §4.2 step-1 immutability globs and only rehashed on the added-overlay path** —
  a later PR could modify/delete a source record backing an already-committed signed overlay, and the
  step-3 early-exit skipped everything when no overlay was added. FOLDED: `evidence/source/**` added to the
  `--diff-filter=MD` set; steps 1–2 run unconditionally before the early exit.
- **SB1 (CONFIRMED Important): `source_locator` path-base self-contradiction** ("repo-relative" prose vs
  the concrete schema-placement-relative `evidence/source/…` value; git root is 3 levels up, so a literal
  reading false-FAILs the CI rehash). FOLDED: one explicit base — schema-placement-directory-relative,
  resolved as `$SP/<locator>` (the census gate's convention) — stated in Global Constraints, §3.3, §5.
- **OCA-1 (PARTIAL → Minor): the overlay CI self-sourced the census `repo_sha` (and left the query-bundle
  source unspecified), making CN006/CN007 self-referential** — bounded because the census is separately
  gated when ADDED, content-matched by hash, and immutable, but not stated. FOLDED: §4.2 step 4 now mirrors
  `verify_committed_census.sh` — ancestor-of-HEAD + tooling-diff on the census `repo_sha`, HEAD-computed
  `--expect-query-bundle-sha256`, pinned constants for project/db/schemas/markers.
- **OCA-2 (Minor):** census parse pinned to `verify_census.load_snapshot_from_bytes` (dup-key/non-finite
  guards; sig-before-parse) in §3.4/§4.1. FOLDED.
- **SB3 (Minor):** NA-reason case is a **pair** (no source record; `source_locator` names the out-of-band
  custody locator) — the always-a-triple wording corrected in §3.5/§3.7/§5. FOLDED.
- **SB4 (Minor):** kind-scan scoped to `.json` files (non-JSON source records opaque; a JSON
  `kind=evidence_overlay` hidden under `evidence/source/` FAILs). FOLDED into §4.2 step 2.
- **SP-2/SP-3 (Minor/Nit):** key-load failure held to AO009-grade value-silence; the fingerprint parity is
  an explicit coded check, never a bare `assert`. FOLDED into §3.5.

### Cross-engine delta (round 2)

Codex's single P2 (source-record immutability) was independently CONFIRMED by three Claude adversarial
verdicts from different lenses — the strongest convergence of the round. Claude's panel additionally
surfaced the path-base contradiction (SB1) and the self-referential census binding (OCA-1) that Codex did
not; Codex surfaced nothing the panel missed. No contradictions between engines.

### Verdict

All round-1 findings CLOSED (grounded) after the tightening; all round-2 findings FOLDED same-day. One
coverage caveat recorded honestly: the ci-set-semantics lens is re-executed against the tightened text as
round-2b, appended below. → Operator approval gate.

## ROUND 2b — ci-set-semantics genuine re-run + Codex pass on the tightened rev2 (`c656e435`) — 2026-07-12

**Codex (`--base main` @ `c656e435`, exit 0): two P2 consistency residuals from the tightening itself —
both FOLDED.** (1) The NA-case `source_locator` had no input (CLI was `--source-file` xor NA-reason while
"COMPUTED never typed" left the custody locator sourceless) → added `--source-custody-locator`, required
iff NA-reason, classed as operator *semantics* (AO004 covers the three-way exclusivity). (2) §10 still said
"repo-relative", reintroducing the SB1 path-base contradiction in the rationale section → corrected; the
schema-placement-relative base is now stated consistently in Global Constraints, §3.3, §5, and §10.

**Claude ci-set-semantics genuine re-run (replacing the round-2 degenerate lens agent): grounded across
all six probes, with EMPIRICAL reproduction — six findings, ALL FOLDED:**

- **CI2b-1 (Important, reproduced on git 2.43):** git's default rename detection reports rename+modify as
  status `R`, which `--diff-filter=MD` (step 1) AND `--diff-filter=A` (step 3) both silently ignore — a
  git-native bypass of the immutability fold (reproduced: R097/R100/R099 for overlay/sig/source-record;
  the specced MD and A commands returned EMPTY). A file→symlink typechange (`T`) likewise evaded MD.
  FOLDED: step 1 is now `git diff --no-renames --name-status`, **FAIL unless every entry is status `A`**
  (rejects M/D/T/R/C/U/B); renames decompose to `A`+`D` (D fails, A re-enters the added set); non-regular
  modes (`120000`/`160000`) under `evidence/` FAIL via `git ls-files -s`.
- **CI2b-2 (Important):** `source_locator` (a schema-level free string) was rehashed with no path
  constraint — a validly-signed overlay could point it at a mutable non-glob file (e.g. `evidence/*.md`)
  or a symlink, divorcing `source_hash` from committed content after the adding PR. FOLDED: step 4 now
  normalizes the locator (reject absolute/`..`), requires it under `evidence/source/` as a committed
  regular blob inside the step-1-protected set, before hashing.
- **CI2b-3 (Minor):** the `.json`-extension kind-scan admitted `.JSON`/extension-less/"opaque" hidden
  overlays. FOLDED: content-sniff every added file under `evidence/` (strict parse regardless of
  extension/case); parsed `kind=evidence_overlay` off-path FAILs; sig-pairing scope pinned to
  `evidence/overlay-*.json.sig`.
- **CI2b-4 (Minor):** a byte-identical duplicate census would pass the census gate yet make every bound
  overlay permanently ambiguous (>1 match) while immutability forbids deleting either copy. FOLDED:
  step 2 FAILs any ADDED census whose `sha256(bytes)` equals an already-committed census.
- **CI2b-5 (Nit):** stale "step 5 re-verifies at HEAD" cross-reference → corrected to "the
  `verify_overlay_artifact.py` run later in this step enforces OV012 at HEAD".
- **CI2b-6 (Nit):** "abort on ambiguous merge-base" was unimplementable with plain `git merge-base`
  (prints one best candidate) → specified `git merge-base --all`, FAIL unless exactly one line. (The
  agent also verified fail-closed fetch is viable under `persist-credentials:false` — the repo is public.)

**Verdict (cross-engine, round 2b):** the rename/typechange bypass (CI2b-1) and the unconstrained-locator
divorce (CI2b-2) were the last Important-class gaps; both are folded with empirically-pinned mechanisms
and matrix rows. Codex and Claude findings were disjoint and non-contradictory; every round-1, round-2,
and round-2b finding is now folded into the spec. → operator review.

## ROUND 2c — OPERATOR review of the round-2b text (`e211594a`) — 2026-07-12

**Operator finding (Important, reproduced): source-only PRs pass — an orphan `evidence/source/**` record
can be added with NO overlay referencing it.** Step 1 admits an added source record as status `A`; step 3
exits early when zero overlays are added; the source↔overlay linkage was only ever checked from the
overlay side (the step-4 rehash, added-overlays only). Reproduced by the operator with a committed
source-only addition (`A evidence/source/orphan.source.txt`, empty added-overlay set). Since source
records exist only *per overlay* (§5), a source-only PR must fail.

**FOLDED (strong form):** §4.2 step 2 gains an **unconditional source-record orphan guard** — the set of
`source_locator` values is built from EVERY committed overlay at HEAD with non-null `source_hash`
(`git ls-files`), and every committed regular blob under `evidence/source/**` must be referenced by
**exactly one** such overlay (orphan or multiply-referenced → FAIL); running before the step-3 early exit,
it fails a source-only PR even with zero added overlays. §11 matrix row + negative test
`source_record_without_overlay_fails` added. (Exactly-one is by construction: each overlay publishes its
own uniquely-named record; the referenced-bytes==`source_hash` check is unchanged in step 4.)

**Operator disposition:** everything else checked ALIGNED — branch boundary, design-only scope, full
census acceptance, signer parity, rename-proof immutability, locator constraints, held downstream phases.
Approval contingent on this single fold, now applied. **Phase 2 APPROVED by the operator @ `8f6d41c4`**
(design-only; unlocks Phase-3 planning ONLY; rider: source-orphan guard = first-class plan task,
`source_record_without_overlay_fails` failing first, + orphan/multiply-referenced/traversal/non-regular/
hash-mismatch source-record negatives).

## ROUND 3 — Phase-3 TDD plan (`f2a01f55`) cross-engine plan audit — 2026-07-12

Artifact: `docs/superpowers/plans/2026-07-12-overlay-evidence-publication-tooling.md` (13 tasks,
negative-tests-first, complete code per step). Engines: **Codex** (`review --base 8f6d41c4`, exit 0) +
**Claude 3-lens grounded panel** (embedded-code-vs-merged-contracts / spec+rider fidelity / test-validity
+ e2e-harness; 8 agents, adversarial verify on every material finding).

**Codex: no actionable defect** — and it EMPIRICALLY EXECUTED the plan's riskiest recipe on the host
(`_zero_census` + the Task-1 `acceptance_census` overrides → schema-valid, 0 errors; full `check_census`
→ 0 diags), de-risking the fixture assumption the plan itself flags.

**Claude panel — verified findings, ALL FOLDED same-day:**
- **E2E-1 (CONFIRMED, independently reproduced): non-bare scratch origin** — `git push` back to a
  non-bare origin is refused (`receive.denyCurrentBranch`), breaking the four push-first tamper cases.
  FOLDED: `_scratch` builds a seed tree → **bare** `origin.git` → work clone.
- **ECMC-1 / SPEC-1 / SPEC-2 / E2E-2 (CONFIRMED/PARTIAL, Important): §11 matrix rows without tests** —
  census non-ancestor binding, TOOLING-drift-since-census, AO012 in-memory-sidecar negative, the
  null-`producing_repo_sha` FORBIDDEN-dim path, verifier census-side OV001, and the gate's
  rehash/verifier-rejection wiring were implemented but never driven RED. FOLDED: +1 author case
  (`sidecar_inmemory_failure_AO012`), +1 verifier case (`main_tampered_census_OV001_census_locus`),
  **+6 gate e2e cases** (`census_nonancestor`, `tooling_drift_since_census`,
  `forbidden_dim_null_producing_green`, `source_hash_mismatch`, `modify_committed_source_record`
  — the SRC-IMMUT headline at the gate level — and `added_overlay_bad_signature`); suite now 30 cases.
- **ECMC-4 / SPEC-3 / E2E-5 (Minor): `|| true` masked git failures** in the gate's immutability/mode
  pipelines (fail-OPEN on git error — this repo's own false-green lesson). FOLDED: removed; `set -euo
  pipefail` + awk-exits-0 semantics documented in the script.
- **ECMC-3 / SPEC-7 / E2E-4 (Minor): interface-map drift** (`assemble_overlay` kwargs, `verify_artifact`
  signature, `canonical_names` suffix wording). FOLDED: map corrected + authority demoted to "task
  bodies govern on conflict".
- **ECMC-2 / SPEC-6 (Minor): unflagged strengthening** — kind-sniff/census-uniqueness run over the WHOLE
  committed tree (spec said ADDED set) and a third suite joins the loop. FOLDED as explicit **Plan
  decision #6** with the supersede-not-edit ratchet note (verified green on the current tree).
- **E2E-3 / E2E-6 (Minor/Nit):** rename-case now asserts the `immutability` FAIL line (anti-vacuity);
  dead-code line removed; Task-9 RED mechanism description corrected. SPEC-4 (fixture dates) judged a
  non-issue: all fixture instants are in the past relative to any future run.

**Cross-engine delta (round 3):** disjoint and complementary — Codex validated the fixture recipe by
execution but raised no findings; the Claude panel's harness lens found the one Critical-class harness
break (E2E-1, reproduced) plus the coverage matrix gaps. No contradictions.

**Verdict: plan BUILD-READY at the post-fold commit** — rider honored (Task 7 first-class,
`source_record_without_overlay_fails` first), every confirmed audit finding folded, matrix coverage now
test-backed end-to-end. STOP: build (Phase 4), push/PR (Phase 5), and all downstream remain HELD.

## ROUND 3 — OPERATOR RATIFICATION of the Phase-3 plan (`cace5568`) — 2026-07-12

**Phase 3 APPROVED @ `cace5568`.** Operator audit: no Critical or Important blockers. Independently
verified: worktree clean on `schema-placement/overlay-publication` at `cace5568`; `main`/`origin/main`
untouched at `a47161fc`; diff limited to the Phase-2 spec, Phase-3 plan, and this record; `git diff
--check` clean. GO-requirement satisfaction confirmed (negative-first TDD; separate author/verifier/CI/
runbook tasks; exact files + function boundaries; read-once bytes; source-pinned signer verification;
no-clobber + partial-publication tests; 8+3-suite regression; whole-branch review before PR; the
round-2c source-orphan rider first-class in Task 7 and re-exercised at gate level in Task 9).

**Operator Minor (build-time fold, not approval-blocking):** in Task 8, add an `isinstance(doc, dict)`
guard before `overlay_docs.append((p, doc))` in `overlay_ci_checks.py` — as planned, a canonical
`evidence/overlay-*.json` that strict-parses to a list/scalar would fail closed via `AttributeError`
inside `orphan_check` rather than a stable `FAIL:` line. To be folded during the Task-8 build WITH a
small RED test.

**All six flagged Plan decisions ACCEPTED as written.** Phase-4 recommendation: subagent-driven build
(one fresh implementer per task, per-task review; NOT inline batching — the author/verifier/gate/runbook
surfaces are separable and the shell-git harness is high-risk). Phase 4 remains gated on its own explicit
GO; no live evidence, no production signing key, no DB/prod, no push/PR/merge.
