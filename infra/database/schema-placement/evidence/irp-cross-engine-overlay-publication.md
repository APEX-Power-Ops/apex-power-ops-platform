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

## ROUND 2 — rev2 re-audit — *pending (folds the above; focused Codex + Claude re-audit to be appended).*
