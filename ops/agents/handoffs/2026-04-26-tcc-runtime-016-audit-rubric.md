# TCC Runtime 016 Audit Rubric

Date: 2026-04-26
Packet: `2026-04-26-tcc-runtime-016`
Status: Active Copilot auditor rubric
Scope: Audit Claude Code execution output for the atomic-swap-prep lane only

## Purpose

This rubric defines how Copilot will audit Claude Code's returned execution report for Runtime 016.

This is not an execution packet. It is the acceptance filter for deciding whether Claude's work is:

1. accepted as complete,
2. accepted with bounded follow-up, or
3. rejected and sent back for another bounded execution pass.

Authority sources for this audit:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE3-ATOMIC-SWAP-PREP-2026-04-26.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-26-tcc-runtime-016-atomic-swap-prep-execution-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/AI-INSTANCE-TASK-PROMPT-TCC-RUNTIME-016-ATOMIC-SWAP-PREP-2026-04-26.md`
4. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-RUNTIME-016-SEQUENCING-DECISION-2026-04-26.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-RUNTIME-016-SUBSTITUTE-SELECTION-DECISION-2026-04-26.md`
7. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-RUNTIME-016-MAINT-SWAP-DECISION-2026-04-26.md`

## Mandatory Return Shape

Claude's returned execution report must contain all of the following in explicit form:

1. current step completed or blocked
2. files updated
3. validation performed
4. exact blocker if progress stopped
5. whether atomic swap is authorized
6. whether Phase 4 is authorized or still blocked

If any item is missing, the audit result is automatically `REJECTED — incomplete return contract`.

## Audit Decisions

The final auditor decision must be one of these exact states:

1. `ACCEPTED` — lane closed truthfully for the current step or full packet.
2. `ACCEPTED WITH FOLLOW-UP` — main claim is supported, but one bounded non-blocking follow-up remains.
3. `REJECTED — REWORK REQUIRED` — behavior, evidence, or scope discipline is insufficient.
4. `BLOCKED — GOVERNANCE OR TRUTH CONFLICT` — Claude stopped correctly because a decision boundary was reached.

## Automatic Fail Conditions

Reject immediately if any of the following appears:

1. Claude claims rebuilt-state proof while still relying on `6258` as if it were active rebuilt truth.
2. Claude changes Python behavior to match a lagging SQL path instead of closing the SQL gap.
3. Claude performs or implies Phase 4 acceptance work.
4. Claude performs or implies Phase 5 normalization, renaming, or cleanup work.
5. Claude executes atomic swap before TASK-013 part 2 is validated truthfully, or claims swap success without explicit post-swap validation for the touched slice.
6. Claude reports a passing outcome without naming the concrete validation commands or tests run.
7. Claude reconciles a truth conflict by editing docs only while leaving runtime behavior unresolved.
8. Claude reports success while the repo SQL surface and live DB surface are knowingly divergent and unreconciled.
9. Claude continues using the superseded pre-swap Step 1 -> Step 2 -> Step 3 order after the Runtime 016 sequencing decision was issued.
10. Claude continues to use `11442` as the general `6258` substitute after the substitute-selection decision rejected it.
11. Claude executes Step 3 by pure-renaming `tcc_etu_sensor_maint_v2` or otherwise drops the canonical MAINT runtime contract (`maint_*` / `params_json`) without an approved compatibility bridge.

## Audit Categories

Each category below is audited as `PASS`, `PASS WITH NOTE`, or `FAIL`.

The execution is not accepted if any category that is marked `required` fails.

### 1. Lane Discipline (required)

Question:

- Did Claude stay inside Runtime 016: TASK-012 part 2, TASK-013 part 2, atomic-swap decision, and focused post-swap validation only?

Pass evidence:

1. returned file list stays inside the authorized surfaces or direct support files for those surfaces
2. no Phase 4 or Phase 5 implementation claims
3. no unrelated family work

Fail signals:

1. widening into EMT, TMT, or unrelated ETU cleanup
2. renaming storage columns or broader schema cleanup
3. acceptance claims beyond the packet boundary

### 2. TASK-012 Part 2 Closure Quality (required)

Question:

- Did Claude actually close or correctly block the SQL RPC STPU override gap?

Pass evidence:

1. `fn_calculate_test_currents` or the truthful live SQL path was updated or explicitly proven already correct
2. the report names the exact override source used
3. SQL output now matches the already-proven Python contract for override amps, tolerances, and timing where applicable
4. focused validation cites the override-scoped SQL regression and the Python override tests

Pass-with-note evidence:

1. Claude correctly proves the gap is elsewhere, not in `fn_calculate_test_currents`, and names the controlling slice with evidence

Fail signals:

1. only documentation changed
2. only Python tests ran
3. no evidence that SQL returns override behavior
4. SQL parity claim is made without naming sensor fixture, expected values, or validation result

### 3. TASK-013 Part 2 Fixture Truthfulness (required)

Question:

- Did Claude replace rebuilt-state caveat bridges with truthful rebuilt-state fixture anchors?

Pass evidence:

1. re-keyed files are named explicitly
2. the new fixture anchor policy is identified explicitly, with approved split anchors or a narrower source-backed substitute justified against the decision
3. golden values were recomputed from rebuilt-state data rather than copied forward from pre-rebuild examples
4. any historical `6258` illustration that remains is clearly marked as historical only

Pass-with-note evidence:

1. Claude closes the proof-bearing test or spec surfaces first and leaves a clearly non-blocking historical illustration for later cleanup

Fail signals:

1. `6258` still stands as active rebuilt-state proof
2. replacement fixture is asserted without source-backed justification
3. docs are re-keyed but tests remain keyed to stale proof surfaces
4. golden values changed without stating how they were derived

### 4. Validation Rigor (required)

Question:

- Did Claude validate behavior at the narrowest meaningful slice after each substantive edit?

Pass evidence:

1. the first edit is followed immediately by a focused falsifying check
2. returned validations are narrow and behavior-scoped before any broad suite runs
3. post-swap validation, if swap occurred, includes focused override proof plus touched regression surfaces

Fail signals:

1. only `git diff` or prose inspection is used despite available tests
2. broad test runs are used without first running the narrowest relevant check
3. validation is missing, ambiguous, or obviously unrelated to the modified surfaces

### 5. Atomic-Swap Decision Quality (required if swap claimed, advisory if not)

Question:

- If Claude touched atomic swap, was the decision truthful and explicitly justified?

Pass evidence if swap happened:

1. Claude states why swap is now more truthful than the current `*_v2` naming state
2. swapped surfaces are named explicitly
3. post-swap validation is named explicitly
4. any downstream doc reconciliation is listed explicitly
5. the MAINT runtime contract is explicitly preserved across the swap rather than silently replaced by raw v2 column names

Pass evidence if swap did not happen:

1. Claude states clearly that swap remains blocked and gives one exact reason

Fail signals:

1. swap executed as a schedule milestone instead of as a truth decision
2. no explicit post-swap validation named
3. no exact no-go reason when blocked
4. MAINT SQL/Python consumers are left bound to a contract that no longer exists after swap

### 6. Evidence and Doc Reconciliation (required)

Question:

- Do the completion record and evidence surfaces match the actual code and validation outcome?

Pass evidence:

1. changed task packet or evidence docs are named
2. the reported behavior matches the code surface actually changed
3. the handoff state remains consistent with the claimed result

Fail signals:

1. code changed but packet completion record not updated when closure is claimed
2. docs overstate completion beyond the evidence
3. handoff and task packet disagree

### 7. Boundary Handling (required)

Question:

- When Claude hit uncertainty or a truth conflict, did it stop at the right boundary?

Pass evidence:

1. blocker is exact and local
2. no speculative policy was invented
3. evidence is preserved well enough for the next decision

Fail signals:

1. vague blocker language
2. hidden uncertainty presented as completion
3. policy invention across governance boundaries

## Evidence Minimums By Outcome

### If Claude claims TASK-012 part 2 PASS

Require all of these:

1. exact SQL surface changed or explicitly verified
2. exact override test or regression named
3. exact sensor fixture or fixtures used
4. exact reported override values or parity condition

### If Claude claims TASK-013 part 2 PASS

Require all of these:

1. exact re-keyed file list
2. exact replacement fixture anchor or split-anchor mapping
3. exact note about how rebuilt-state values were derived
4. exact touched tests or validations

### If Claude claims atomic swap PASS

Require all of these:

1. exact swapped surfaces
2. exact post-swap validations
3. exact reason swap is now truthful
4. exact Phase 4 authorization or blocker statement

### If Claude returns blocked

Require all of these:

1. exact blocker sentence
2. exact surface where work stopped
3. evidence already gathered
4. whether the next actor needs governance, source proof, or another local edit pass

## Review Workflow

When Claude returns, Copilot should audit in this order:

1. verify the mandatory return shape
2. check automatic fail conditions
3. score lane discipline
4. score the active step's substantive category first
5. score validation rigor
6. score evidence and doc reconciliation
7. decide `ACCEPTED`, `ACCEPTED WITH FOLLOW-UP`, `REJECTED — REWORK REQUIRED`, or `BLOCKED — GOVERNANCE OR TRUTH CONFLICT`

## Auditor Response Template

Use this exact structure when replying after reviewing Claude's output:

1. `Decision:` one of the four audit decisions above
2. `Active step audited:` TASK-012 part 2, TASK-013 part 2, atomic swap, or blocked state
3. `Findings:` concise numbered findings ordered by severity
4. `Accepted evidence:` exact files, validations, and claims that were supported
5. `Gaps:` exact missing proof or boundary issue, if any
6. `Next action:` one bounded instruction for Claude or one acceptance statement

## Bottom Line

Runtime 016 is accepted only if the work is truthful, narrow, validated, and explicitly bounded.

The audit standard is not whether Claude changed files. The audit standard is whether Claude proved the correct runtime truth without crossing the packet boundary.