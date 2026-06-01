---
dispatch_id: 2026-06-01-cc-tcc-calc-thermeq-ghidra-recovery
target: CC
priority: 2
from: Desktop
created_at: 2026-06-01
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-06-01-tcc-calc-thermeq-ghidra-recovery-closeout.md
---

# Recover native `CalcThermEq` (+`CalcAnsiEqGF`) from EasyPower.exe — close the InvEq Therm parity half (D-11(b))

**Lane:** TCC Master Reference — calc-engine parity. **Spec of record:** `reference/tcc/G4-CALC-GUIDE.md` §3d/§3e/§5 + the **field-trust matrix** §4 rows 6/7; deferred-work ledger `reference/tcc/G2-RULES-GUIDE.md` **D-11**. **This is the second half of §98 lean 1** — the first half (the ANSI hard-exclude) landed 2026-06-01 in `etu_delay_routing.py`; this closes the remaining Therm-parity question. **Local + bounded** (`EasyPower.exe` is on disk; Ghidra installed). Cite the guide sections you touch and fix them first per the SSoT Law.

## Why
The managed `IEEEInverseTimeSolver` (`source-domains/tcc_v5_backend/services/calc_engine/etu_curves.py:405-446`) evaluates `T = (c1/(I^c2−1)+c3+c6)·TD` and **silently ignores coeffs c4/c5** (= native `rIref`/`rM`). Two consequences (G4 §3e, verified live 2026-06-01):
- **Therm (31,070 rows: STD 22,620 + GF 8,450):** STD `rIref`=10 vs GF `rIref`=1, yet managed output is identical (c4 ignored). If native `CalcThermEq` **uses** `rIref`/`rM`, the managed Therm curve is *wrong*, not merely unvalidated. This is **D-11(b)** and the **#1 calc gap** (risk R1) — InvEq sensors cannot ship a field TD window until it closes.
- **ANSI (100 rows / 23 sensors / 3 trip styles, `IdOpEq=1`):** the C37.112 exponent lives in the **c5 slot** (e.g. `IdOp5=1.05`) which the solver ignores → empty/wrong curve. Currently **hard-excluded** (lean 1). Recovering `CalcAnsiEqGF` is what would let those 23 sensors be *re-introduced* with a correct solver instead of excluded.

The native evaluator math is **absent from the decomp** (only empty `[NativeCppClass]` stubs); passes 1–5 recovered the *loader/dispatch* only. Independent `[DLL]` corroboration of the 5/6-float split: `GFInverseEqDelayData.cs` declares `sTherm`=40B / `sAnsi`=48B (+1 float).

## Do
1. **Claim** (git mv pending→claimed, push) before starting.
2. **Ghidra-headless** on `D:\EasyPower\EasyPower.exe` (Ghidra 12.0.4 at `C:\Users\jjswe\Tools\ghidra\...`, `support\analyzeHeadless.bat`). **Seed** from the pass-5 anchors: populator `FUN_01207bf0`, translator `FUN_01208640`, and the §12 binding matrix in `…/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`. **Bound the run to 2 functions:** `CalcThermEq` (+ `CalcAnsiEqGF` if a job needs the ANSI cohort) + ≤4 setters for slot order.
3. **Resolve the c4/c5 question:** does native `CalcThermEq` consume `rIref` (c4) / `rM` (c5)? Capture the exact formula form.
4. **Confirm-or-patch** `IEEEInverseTimeSolver._evaluate`: if native uses c4/c5, patch the managed formula to match (gated by new parity tests); if it provably does not, the managed Therm form is *confirmed correct* and Therm moves **BOUNDED→PROVEN**.
5. **Parity tests:** add row-for-row parity tests vs EasyPower-captured curve points (a small representative Therm cohort) alongside `tests/test_etu_delay_routing.py` / the InvEq representative tests. (For ANSI: if `CalcAnsiEqGF` is recovered, add an ANSI solver path + tests, then lift the lean-1 exclude with a real path rather than a stub.)
6. **Guide updates first (SSoT Law):** G4 §3d/§3e/§5 + field-trust matrix rows 6/7 (Therm BOUNDED→PROVEN; ANSI excluded→solved-or-still-excluded), G2 **D-11** (close (b) or record the proven formula), 00 §5 open-validation register.

## Acceptance
- The native `CalcThermEq` formula form is recovered + recorded with `[DLL]` provenance; the c4/c5 question is answered.
- The managed solver is confirmed-correct or patched-to-match, with row-for-row parity tests on a real EasyPower-captured Therm cohort (no synthetic-only fixtures).
- G4/G2/00 updated per the SSoT Law; D-11(b) closed (Therm PROVEN) or its residual precisely re-stated.
- If `CalcAnsiEqGF` recovered: the 23 ANSI sensors get a correct solver path + tests and the lean-1 dispatch-layer exclude is lifted (or explicitly kept with the recovered reason). Full regression green.

## Guardrails
- **RE of EasyPower's own owned binary for interoperability** — the established pass-1..5 posture. **NOT a DRM circumvention** (contrast the ETAP `*OTI-EncryptLibData*` boundary, which stays untouched). No third-party encrypted data is decrypted.
- Kernel (`etu_curves.py`) changes are **gated by parity tests** — do not alter the numerical engine without a passing real-cohort parity proof. Scoped `git add`. The calc engine lives in the **outer** repo (`C:\APEX Platform`, branch `clean-main`); the guides in `apex-power-ops-platform`.
- DSN/keys out-of-band; no `.env*` contents; PUBLIC repo — no client/job identifiers.

## Closeout
Record: the recovered `CalcThermEq` (+`CalcAnsiEqGF`) formula form, the c4/c5 verdict, the managed confirm-or-patch, the parity cohort + results, commit hash(es), and the guide sections amended. Then `git mv` claimed→done, commit, push.
