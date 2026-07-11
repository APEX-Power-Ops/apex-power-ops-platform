# Claude grounded-audit (wf_9bf40060-b7a) — disposition tranche 53507c0f

I have enough to adjudicate. Note for the record: commit `84eb2411` and the four source files are not present in any local worktree (`git rev-parse 84eb2411` fails in the canonical repo; `ls-files` returns nothing for these paths), so this is a design-only branch not checked out here. My adjudication therefore rests on the probe + adversarial evidence set (line-anchored, and in several cases execution-confirmed by the adversarial engine), not a fresh independent source read. I state that plainly in the memo.

# Correction tranche + R3 cross-engine fixes (commit 84eb2411) — schema-placement disposition-ledger tooling (Ed25519 signing gate, SP027 delete floor + structured recovery artifact, gate receipt, mandatory compat consumer, dependency_role classification, non-finite compat window). — Grounded Audit

## Verdict

**SHIP-WITH-CONDITIONS. No FATAL. No primary-gate destructive false-green.** The R3 TOCTOU repairs hold and are test-backed. One **IMPORTANT** new defect that all four probe facets missed survives verification, plus two **MEDIUM** receipt/recovery residuals and a tail of LOWs. None permits a silent destructive apply on the primary path — the observed_at/window and recovery-hash paths fail closed (either a hash mismatch or an uncaught exception, exit != 0). But two things should be closed before the census/apply hold is lifted: the `format: date-time` inertness and the overstated recovery guarantee.

**What held (verified sound — do not re-litigate):**
- The three R3 TOCTOU repairs are real. SP026 verifies the **in-hand** snapshot bytes via `verify_detached`; `build_receipt` pins the **in-hand** `doc_bytes`, not a re-read (regression test `_receipt_pure` tampers the on-disk snapshot post-capture and the receipt follows the validated bytes, `test_check_disposition.py:269-282`); `write_signed_snapshot` publishes sidecar-first with byte-identity signed==written==verified and no destructive removal.
- Accepted compat **cannot** go green without OBSERVED consumer evidence, and the resolution is manifest-independent — two enforcement layers (`disposition.schema.json:248` const `has_consumers`; SP022/SP013 keyed on `consumer_disposition`, not the manifest, `check_disposition.py:388-411`). Proven manifest-independent by `test:218` where the default `required_observations` excludes `consumer_evidence` yet SP022 still fires.
- SP015 non-finite check is reachable for **both** compat and promote (keyed on contract presence, not `action_class`, `:419-423`) and is the load-bearing backstop for `+inf`/overflow-inf, since `parse_constant` only rejects the three literal tokens `NaN`/`Infinity`/`-Infinity` (`:107-116`).
- `dependency_role` is consistent with `found_consumers` on the **live** collector path (consumer-OR across duplicate edge keys before role assignment).
- A receipt cannot be emitted on a non-green gate via `main()` (`diags` return 1, and SP026 failure returns 1, before the `receipt_out` block).
- All three offline suites are reported green by the probes (schema 46 neg/11 pos, checker semantic + e2e signature, collector 36 cases). I did not re-run them in this session (see Unverified).

## Findings (severity + grounded evidence)

### F1 — IMPORTANT — `format: date-time` is inert in this toolchain; timestamp validation silently degrades to a lenient regex
**(adversarial, NEW — missed by all four probe facets; execution-confirmed by the adversarial engine)**

`"date-time" in FormatChecker().checkers == False` because `rfc3339-validator`/isoduration is not in the locked deps (`pyproject.toml`: jsonschema/PyYAML/psycopg/cryptography only), and jsonschema **silently skips unregistered formats**. Every timestamp check therefore reduces to the `iso_datetime` regex `pattern` (`disposition.schema.json:19`), which admits calendar-invalid values (month/day/hour 00-99). Confirmed by execution: full-schema validate of `observed_at="2026-13-45T25:61:61Z"` returns NO errors. Two grounded consequences:

- **(a) Narrow destructive false-green.** A calendar-invalid `captured_at` (e.g. a future `"2027-13-45T25:61:61Z"`) **bypasses the SP014 "recovery captured before census" ordering check** — `parse_dt` raises and `except (ValueError, TypeError): pass` (`check_disposition.py:458-462`) swallows it. A *valid* future `captured_at` correctly raises SP014; the garbage future date greens. The inline comment there ("schema already enforces iso_datetime syntax") is the load-bearing but **false** premise.
- **(b) Uncaught (fail-closed) crash on the primary timestamps.** `observed_at` (`:273`), SP009 window (`:336`), and SP027 delete window (`:482`) call `parse_dt` **without** a guard, so a schema-passing calendar-invalid value raises `ValueError` that propagates out of `run()`/`main()` (main's `try` covers only input load at `:544-557`, not `run()` at `:579`). Outcome is exit != 0 (fail-closed), but it is a traceback, not a clean SP0xx — violating the module's "deterministic, diagnostics sorted" contract and inconsistent with the authors' own defensive pattern (they guarded `captured_at` but not `observed_at`/window).

The sole datetime negative test, `_neg_invalid_timestamp` (`'not-a-date'`, `test_disposition_schema.py:187`), passes on the **regex alone** and thus masks the inertness. Collector-side `_validate` (`collect_disposition.py:347-351`) shares the lenient checker, but its `observed_at` is DB-clock-derived, so safe in practice.

### F2 — MEDIUM — the recovery floor proves self-consistency, not recoverability, for an irreversible prod delete
**(delete-floor probe #1/#2/#3; execution-confirmed by the adversarial engine)**

`restore_validation_ref` is enforced by **existence only**, not content: it is validated at `check_disposition.py:449-455` by `resolve_within_roots` alone; the zero-byte guard `getsize==0` (`:442`) is applied **only** to `artifact_path`, never to `restore_validation_ref`. No bytes are read, nothing is parsed, nothing asserts it attests success — so an empty file, an unrelated in-root file, or even `rvr == artifact_path` satisfies "restore was validated." This is the *sole* signal that a restore was ever tested, and it is hollow. Compounding it: the recovery artifact is bound only to a **self-declared** sha256 co-located in the decisions doc (`:445-448`, schema recovery_artifact `:181-191`), so `artifact_path` can point at any non-empty in-root file (e.g. a README) whose own sha is declared; and `captured_at` has an upper bound (`> observed_at` rejected, `:456-462`) but **no recency floor**, so an arbitrarily stale backup passes.

Adversarial execution confirmed the composite: an accepted IRREVERSIBLE delete greens with `rvr == artifact_path`, with `rvr` = an arbitrary in-root `{}` file, with the recovery artifact = an arbitrary non-empty in-root file + self-declared sha, and with `captured_at = 2020` (stale) — all green. The code/schema comments ("proof a restore actually succeeded", `:182`, `:425-429`) **overstate** the guarantee. Test `SP014_delete_restore_ref_missing` (`test:209`) only checks that a *non-existent* rvr is rejected — nothing requires non-empty, an attestation, or independence from `artifact_path`.

### F3 — MEDIUM — receipt evidence/sig/key hashes are a fresh disk re-read, not the validated/verified bytes (intra-run validate→receipt swap window)
**(receipt-toctou probe #3)**

`build_receipt` hashes every non-doc input via `_sha256_file` — a **second read** (`:176` for snapshot_sig/verify_key; `:198` for evidence files) — the asymmetry the R3 `doc_bytes` fix was meant to eliminate, and which the docstring itself admits ("hashed from disk", `:165-168`). The recovery-artifact bytes were already read+hashed inside `semantic_check` (`:445-446`) but that `actual` value is compared to the declared sha then **discarded**, never threaded out. Failure: an attacker replaces `recovery.tar` (or `restore-ok.log`) after `semantic_check` validates it (`:446`) but before `build_receipt` hashes it (`:198`); the receipt pins the swapped bytes, apply-time rehash matches the receipt, and the swap is invisible. The check→apply window R3 closed; this residual is the intra-run validate→receipt window (width depends on the deployment FS and adversary model — narrow on a trusted local FS with no concurrent writer).

### F4 — MEDIUM — non-recovery evidence files have no decision-declared sha256 anywhere, so the fresh-read hash is the only content anchor
**(receipt-toctou probe #4)**

For `restore_validation_ref`, `evidence_refs`, `transform.validation_report`, and `telemetry_ref`, `semantic_check` only existence-checks (`:449-455`, `:486-507`); none is content-hashed against a declared value (the `_recovery_artifact` test helper carries sha256 only for `artifact_path`, `test:55-56`). So a restore-validation proof a reviewer inspected at check-time can be swapped before `build_receipt` runs, and **nothing in the pinned decisions doc commits to its content** — no cross-check can flag the divergence, and the receipt certifies the swapped bytes. The "decision-declared sha256 backstop" the docstring cites (`:167-168`) covers only the recovery artifact, and even that backstop (F2 aside) is usable only if the apply runner independently re-runs SP014 — the receipt neither carries the declared sha nor labels which flat `{ref,resolved,sha256}` entry is the recovery artifact vs restore proof vs generic ref (`:178-198`).

### F5 — LOW — signature verification is match-keyed, not fail-closed; and lives only in `main()`
**(signing-gate probe #1/#2)**

SP026 enforcement is keyed on `if args.mode == "preapply":` (`:566`) rather than a default-deny. It is unreachable today (`choices=["preapply"]`, `:534`) so every current invocation is gated, but the shape is fail-**open** for growth: a future mode added to `choices` without also being added to this guard would run the full semantic gate with **zero** signature verification. Separately, the gate lives only in `main()`; `run()`/`semantic_check()` perform no signature check, so any programmatic caller of `run()` bypasses SP026 entirely — a path the tests already exercise (`cd.run(...)`, `test:156`). Safe iff CLI `main()` is the sole trusted preapply entry point (unverified — see Unverified).

### F6 — LOW — `dependency_role` IFF invariant is documented but not enforced
**(compat-nonfinite probe #4 / adversarial #2; execution-confirmed)**

The `external_consumer IFF the edge is counted` invariant is documented (`disposition.schema.json:60` $comment) but not enforced in `build_relation_observation`. `found_consumers = len(consumer_keys)` (`collect_disposition.py:280-287`) counts an edge whenever any twin is `_is_consumer`, but the role branch checks `direction=='outbound'` **first** (`:292-300`), so an outbound edge flagged `_is_consumer=True` is counted yet labeled `outbound_dependency`. Adversarial execution: an outbound `evidence_type='source'` edge with `_is_consumer=True` yields `found_consumers=1, n_external_consumer=0` — IFF broken. Unreachable on the current census path (`out_fks` hardcodes `is_consumer=false`, `:149`) but reachable via a direct call or a future `source`/`dynamic_sql`/`manual` overlay (docstring `:38-40`). No assertion defends it.

### F7 — LOW — receipt hardening residuals (green-label, key-binding, silent omission)
**(receipt-toctou probe #2/#6/#7; adversarial #3)**

- `build_receipt` stamps `"gate":"green"` **unconditionally** (`:170`) and takes no `diags` argument; the green guarantee lives solely in `main()`'s control-flow ordering. Any future caller/flag reaching `build_receipt` without that guard emits a green-labelled receipt.
- The snapshot-sig→verify-key **binding** is implicit (gate:green + three separate file hashes, sig/key taken as second reads after verification). The receipt records neither the sidecar `public_key_sha256` fingerprint nor an explicit "verified against key X" assertion. An apply runner trusting `receipt.inputs.verify_key` rather than the out-of-band committed key could accept an attacker-signed snapshot if sig+key are swapped between verify (`:572`) and receipt hash (`:176`).
- `build_receipt` **silently omits** the sig/verify_key entry if the file disappears between verify and receipt build — guard `if p and os.path.isfile(p)` (`:174-176`) skips a vanished/rotated file with no entry and no error.
- The receipt omits per-source-relation `consumer_evidence[dim].ref` content that `semantic_check` resolves (`:498-507`) — pinned transitively via the whole-snapshot hash but not receipt-pinned.

### F8 — LOW (INERT) — SP015 exit_condition finiteness is skipped for `required=false` contracts
**(compat-nonfinite probe #3)**

SP015's exit_condition finiteness check is gated behind `cc.get('required')` truthy (`:419`). A contract with `required=false` may still carry a full `exit_condition` whose `window_hours`/`threshold` is `+inf` (via `1e999` overflow or YAML `.inf`, both passing `exclusiveMinimum:0`) and skip SP015. **Inert here** — `check_disposition.py` never consumes `exit_condition` numerics in any comparison (the telemetry exit evaluation named in the schema $comment is not implemented in this file). Forward risk only: a downstream telemetry/apply-time evaluator that reads `exit_condition` on a `required=false` contract without re-checking finiteness.

## Regression risks (from the adversarial pass)

Framing correction: the adversarial pass labels its three items "regressions," but none is a behavior *introduced* by 84eb2411 — they are latent defects newly surfaced relative to the probe set. Stated accurately:

- **F1 (date-time inertness) is the highest-value catch and was missed by every probe facet.** The compat-nonfinite probe scrutinized NaN/Inf gate numbers thoroughly but never tested calendar-invalid-but-regex-valid timestamps. This is the one item whose miss materially changes the verdict.
- **F6 (dependency_role IFF)** was left by the compat-nonfinite probe as unverified latent analysis; the adversarial engine reproduced it by a direct `build_relation_observation` call. Confirmed real, no live reach on the current census path.
- **F7 silent sig/key omission** is a distinct angle (silent omission on file disappearance) from the probe's swap-in-the-second-read-window finding; both stem from `build_receipt` re-reading sig/key from disk rather than threading verified bytes.
- **Design-only asymmetry both passes noted implicitly:** only the *snapshot* is signature-bound. `decisions_file`, `cluster_manifest`, and `entity_map` are unsigned plain JSON whose trust rests entirely on the invoker supplying git-reviewed versions. The receipt pins their hashes for the check→apply window, but nothing binds them to a reviewed baseline at *check* time. Inherent to any offline checker/linter, but an asymmetry vs the signed snapshot worth stating.

## Unverified / needs source

- **Lead-reviewer meta (grounding limit):** commit `84eb2411` and the four source files (`check_disposition.py`, `collect_disposition.py`, `disposition_signing.py`, `disposition.schema.json`) are **not present in any local worktree** — `git rev-parse 84eb2411` fails in the canonical repo and `ls-files` returns nothing for these paths. This adjudication rests on the probe/adversarial evidence set (line-anchored; adversarial items execution-confirmed by that engine), not a fresh source read in this session. No test suite was executed here.
- **Apply-runner entry point and re-validation behavior — the single biggest unknown.** Whether the apply runner invokes the CLI `main()` (which enforces SP026) or `run()`/`semantic_check()` directly (no signature check), and whether it independently re-runs the full SP014 recovery-artifact sha256 + `verify_detached` versus merely rehashing files against `receipt.inputs`. The severity of F3, F4, F5, and the F7 key-binding all collapse or persist based on this. Runner source is not in the file set (census + apply are HELD).
- **Out-of-band Infisical Ed25519 keypair** custody/validity (valid unencrypted PKCS8 Ed25519 PEM) and the value-silence of `DISPOSITION_SIGNING_KEY` injection upstream — intentionally absent from the repo; not inspectable here.
- **Integrity of the committed `--verify-key` file and the invocation command line** — the gate's entire trust reduces to these two inputs; neither is verifiable from code.
- **FS atomicity on the real census host** — `os.link` no-clobber + `os.replace` + sibling-temp fsync assume a single volume (`collect_disposition.py:526-527`); semantics differ Windows NTFS vs the Linux/Olares host where the one-shot census is expected to run.
- **Live behavior vs `fxoyniqnrlkxfligbxmg`** and the `QUERY_BUNDLE['dependents']` SQL invariant (`out_fks` always `is_consumer=false`; all consumer-flagged groups inbound) — verified by reading SQL text only, not executed against Postgres. F6's live-path safety depends on this.
- **Downstream telemetry/apply-time evaluator for `exit_condition`** (F8 forward risk) — not in the file set; the schema $comment references a "compat telemetry satisfies exit expression" check that is not implemented in `check_disposition.py`.

## Operator decisions to surface (with leans)

**D1 — Gate the unhold on closing F1 (date-time inertness)?** Lean: **YES, blocking.** It is the only item producing a genuine (if narrow) destructive false-green plus a contract-violating traceback, and the fix is cheap: pin `rfc3339-validator` to register the `date-time` format, **and** replace the swallowing `except: pass` at `:458-462` with an explicit calendar-parse that emits SP008/SP009/SP014 instead of crashing or silently passing. Add a datetime negative test that actually exercises a calendar-invalid value (the current `'not-a-date'` masks the gap). This is the one item I would hard-gate the census/apply unhold on.

**D2 — Strengthen vs merely re-document the recovery contract (F2)?** Lean: **strengthen minimally AND correct the comments.** Bind `restore_validation_ref` to a parsed success attestation, require it to be non-empty and independent of `artifact_path`, and add a `captured_at` recency floor. Correct the "proof a restore actually succeeded" / "proved" comments regardless — they currently overstate what an offline checker can guarantee. Full restore-attestation semantics could defer to the apply runner *only if* D-info confirms that runner re-validates (see below); since it is unverified, do not rely on it.

**D3 — How much receipt hardening now (F3/F4/F7)?** Lean: **do the cheap subset now, defer the redesign pending the apply-runner answer.** Cheap now: thread `semantic_check`'s already-computed recovery hash into `build_receipt` (closes the F3 intra-run window for the recovery artifact); add the `verify_key` fingerprint / explicit "verified against key X" assertion; turn the silent sig/key omission into a hard error. Defer the labeled-evidence-role redesign and declared-sha carry until the apply-runner entry point is confirmed.

**D4 — Reshape the signing gate to fail-closed now (F5)?** Lean: **yes, fold into the D1 hardening pass.** Verify unconditionally (or allowlist explicitly non-preapply modes) and either enforce a signature check in `run()` or formally document `main()` as the sole trusted preapply entry point. Low urgency (unreachable today) but near-zero cost.

**D5 — Assert the `dependency_role` IFF now (F6)?** Lean: **add the assertion now** as defense-in-depth (`outbound ⇒ not consumer`), independent of the live-path proof, which needs a DB run when census is unheld. F8 needs no code change here — just confirm no downstream evaluator reads `exit_condition` on a `required=false` contract before wiring one up.

**Decision I need from you to finalize D2/D3 severity:** confirm the apply-runner's entry point and whether it re-runs SP014 + `verify_detached`. That single fact determines whether F3/F4/F5 stay MEDIUM/LOW residuals or must be hard-closed in this tranche.