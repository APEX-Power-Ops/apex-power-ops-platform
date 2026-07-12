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

## ROUND 2b — ci-set-semantics genuine re-run + Codex pass on the tightened rev2 — *appended on completion.*
