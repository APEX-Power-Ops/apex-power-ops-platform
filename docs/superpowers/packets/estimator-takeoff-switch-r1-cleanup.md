# Switches / Disconnects R1 cleanup packet (bounded) - RATIFIED + AS-BUILT

Lane: `estimator-takeoff/switch-r1-cleanup` off main `1f31c88e`. Dev-only; merge OPERATOR-GATED; Codex IRP before merge.
Constraint (operator, 2026-06-30): bounded; NO new family behavior unless SME-ratified. ASCII-only authored code/comments/strings.
Status: batch (a)+(c)+(b-with-guard) BUILT + GREEN; (d) PARKED SME-pending. 6 prior family goldens BYTE-IDENTICAL.

## Scope
Close the four carried R1/SME residuals from the switch family merge (PR #53). NONE was a misprice (all fail-closed).
Goal: cleanest estimator-family base before the 7th family - fix the safe Gate-2 / recognition items now; park the
labor-semantics item for SME.

## Grounding (merged state at 1f31c88e - verified, not recalled)
- `assessCore` dispatch ORDER: instrument-tx -> transformer -> gfp -> relay -> switch -> NON_BREAKER -> breaker-fallback.
  Transformer is tried BEFORE switch (normalize.ts L440 vs L459) - the root of the Pad-Mount-Vista mis-claim.
- `looksLikeTransformer` yielded ONLY on candidateKind:'switch'; a blanket isSwitchAnchored text-yield was tried + REVERTED
  (it stole real transformer rows with an accessory disconnect).
- `SWITCH_GROUPS` had `any:unknown` (all 11); a typed-but-voltageless row widened to it. `matchSwitch` default needs
  voltageClass!=undefined -> a voltageless row NEVER auto-prices. `NO_HOME_SWITCH_TYPES={vacuum}` checked FIRST.

## Dispositions

### (a) Typed-no-voltage Gate-2 candidate breadth -- BUILT (no SME; pure ergonomics)
Add 7 per-type `${type}:unknown` keys to SWITCH_GROUPS (switch-map.data.ts). A typed switch with illegible voltage now
narrows to its type's refs across voltage classes instead of all 11. No recognition change, no pricing change, NO
default (voltageless still yields no defaultRef). vacuum has NO `:unknown` key (structural gap preserved).

### (c) Load-Interrupter Switch anchor -- BUILT (synonym of already-anchored LBS; ratified "same MV device class")
Add `load[\s-]?interrupter(\s+switch)?` to SWITCH_DEVICE (normalize.ts). Matches "load interrupter" / "load-interrupter"
/ "load interrupter switch"; does NOT match a bare "interrupter". Type stays 'unknown' -> Gate-2, fail-closed; the
breaker conflict guard still wins (AF/AT + LSIG -> switch_parent_conflict).

### (b) Bare-text Pad-Mount-Vista -- BUILT (narrow vista-only yield + transformer regression guards)
Add `const VISTA = /\bvista\b/i` and, in looksLikeTransformer (after the explicit-producer checks, before the
TRANSFORMER_DEVICE claim): `if (isSwitchAnchored(x.raw) && VISTA.test(x.raw)) return false`. "Vista" is an S&C switch
product, never a transformer descriptor, so a switch-anchored vista row routes to the switch family. GATED on
isSwitchAnchored AND vista so a real pad-mount/kVA transformer (no "vista") - including one with an accessory
disconnect - stays a transformer (the exact regression the blanket yield caused).

### (d) Open-vs-enclosed labor tier + parse precedence -- PARKED (SME-gated)
Which ref/labor applies to enclosed vs open-air, and reading "enclosed" from text, is an estimating-authority
convention (labor semantics, not a mechanical fact). PARKED until the SME ratifies the open-vs-enclosed table.
SWITCH_R1_RATIFIED stays false.

## As-built changes
- packages/estimator-takeoff/src/catalog/switch-map.data.ts  (+7 per-type :unknown keys; comment update)
- packages/estimator-takeoff/src/signature/normalize.ts        (SWITCH_DEVICE load-interrupter; VISTA const; vista yield)
- packages/estimator-takeoff/test/switch-map.test.ts           (tightened the absent-voltage SF6 assertion)
- packages/estimator-takeoff/test/switch-r1-cleanup.test.ts    (NEW: full R1 slice test set)

## Tests (operator-required set - ALL implemented + passing)
- Switch (SF6) no voltage -> switch scope_pending, SF6-only candidateRefs, no provisionalDefaultRef. [pipeline + unit]
- Switch (Vacuum) no voltage -> switch_catalog_gap, NOT a breaker (matchedLines 0). [pipeline + unit]
- Load Interrupter Switch / Load-Interrupter Switch -> switch scope_pending, no auto-price; bare "interrupter" -> not a switch.
- Pad-Mount Vista / Vista Switch -> switch (vista), not transformer.
- 1500KVA Pad Mount Transformer / T-2 2500KVA PAD-MOUNT OIL XFMR / Pad-Mount Oil Transformer / XFMR+accessory-disconnect -> transformer.
- SF6 Breaker, VCB, 800AF/800AT LSIG, Vacuum Circuit Breaker -> breaker (isBreakerShaped).
- Per-type :unknown groups (7 types) + typeless->any:unknown + typed+voltage default unchanged.
- All prior family goldens BYTE-IDENTICAL.

## Gates (true-green, exit unmasked)
- pnpm --filter @apex/estimator-takeoff test -> 392 passed / 4 todo (52 files; +23 over 369).
- estimator-takeoff typecheck clean; operations-web typecheck clean. git diff: 0 fixture files changed.

## Done-definition
ASCII-only; fail-closed preserved (no auto-price added); Codex apex-jobs review-run before merge; merge OPERATOR-GATED.
On merge: sync ledger + lane memory + handoff -> R1-cleanup MERGED; (d) logged SME-pending.
