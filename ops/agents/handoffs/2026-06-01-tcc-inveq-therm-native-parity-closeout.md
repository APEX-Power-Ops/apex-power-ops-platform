# 2026-06-01 CC TCC InvEq-Therm native-parity closeout (gated item B)

## Status

**CLOSED for STD Therm; GF Therm + Ansi are bounded, documented residuals.** The G4 §5
captured-fixture gate is satisfied for STD-side INVEQ Therm by the strongest possible oracle —
**executing the native EasyPower kernel itself** — and STD-INVEQ Therm is **promoted "verify"→"db"**.

## What the gate required (from the prior CalcThermEq recovery closeout)

> "Captured EasyPower point fixtures are still required before G4 field-trust rows 6-7 Therm can be
> promoted to field-sheet-shippable."

## How it was closed — native-kernel execution oracle (not a GUI scrape, not a paraphrase)

`TccBase.dll` (x86 mixed-mode C++/CLI, `PublicKeyToken=fd790d0312e979ea`, from `D:\EasyPower\`) was
loaded **in-process under the 32-bit .NET Framework** and its recovered module functions invoked via
reflection + `System.Reflection.Pointer.Box`:

- `CTccLVBreakerCurveGF.CalcThermEq(byICalc, rTmin, rX, rTref, rIRef, rM, rIpuHi, …)`
- `CTccLVBreakerCurveSST.CalcThermEq3(…)` (the STD-side per-row evaluator, identical signature)

Harness: `output/inveq-parity/oracle/` (Program.cs + scenarios.txt; **git-ignored** — never commit the
licensed DLL/decompile). Real coefficient rows pulled read-only from `D:\TCC_NEW.accdb` via ADODB. The
captured native `(amps, time)` points are frozen as
`packages/calc-engine/tests/fixtures/inveq_therm_native_parity.json` so the regression runs in CI
without the DLL.

## Findings (all `[DLL-EXEC TccBase.dll 2026-06-01]`)

1. **The native per-point body == the managed closed form.** GF `CalcThermEq` (decomp line ~18350) and
   SST `CalcThermEq3` (~27653) both compute `T = rTref·ln(1/(1−(rM/I)^rX)) / ln(1/(1−(rM/rIRef)^rX))`,
   floored at `rTmin`, for `byICalc=0` (`num3=field16=num6=pickup`). The managed
   `_evaluate_native_therm` is this exact arithmetic.
2. **STD Therm parity = BIT-EXACT and EXHAUSTIVE.** STD `IdOpICalc ≡ 4` → `byICalc=0`. The whole STD
   Therm corpus is only **4 dial curves** (`rTmin≡rTref ∈ {0.08,0.14,0.23,0.35}`, `rX=2,rIRef=10,rM=0.9`;
   4,524 sensors each). Managed reproduces native with **maxabs = 0.0** across all 4 (GF-fn `byICalc=0`
   ≡ SST-fn `byICalc=11` → STD and GF share one evaluator). → **STD-INVEQ Therm PROMOTED to "db".**
3. **GF Therm is NOT managed-faithful — kept "verify".** GF `IdOpICalc = 1` (6,760/8,450 Therm rows) →
   `byICalc=1` → `num3 = field13 ≠ pickup`, scaling the effective `rIRef` by `num6/field13`; and every
   `rIRef < rM` GF row (e.g. 0.48) makes the managed `num3=num6` form return **None**. Bounded next step:
   recover `field13` provenance (the device current basis), thread it into the solver, re-validate via
   this oracle → then GF Therm can promote.
4. **GF Ansi: keep hard-excluded (recommended).** `CalcAnsiEqGF` is recovered (future-ready); 23 sensors
   / 100 rows / 3 styles. Status quo (excluded) is the safe default; wiring it is deferred until a real
   Federal-Pioneer GF inverse-eq job appears. **Operator decision surface.**
5. **Secondary `*ICalc=0` residual CLOSED.** Direct count: **zero** rows with any `*ICalc=0`
   (STD `IdOpICalc≡4`; GF `∈{1→6760,4→1690,8→100 Ansi}`). The pass-5 `byICalc=2→ref[12]` branch is correct
   but never exercised. `[06 §R4]` answered.

## Code changes

- `apps/control-plane-api/services/neta/delay_trust.py` — `_classify_std` route 2 → **"db"** (STD INVEQ
  Therm proven); `_classify_gfd` route 2 Therm stays "verify" (documented `byICalc=1` reason);
  `delay_trust_reason` distinguishes the STD-INVEQ-Therm db reason from direct-band. Router unchanged
  (route-driven).
- `apps/control-plane-api/tests/test_delay_trust.py` — STD route 2 → db; new InvEq-Therm db-reason
  assertion. 42/42.
- `packages/calc-engine/tests/fixtures/inveq_therm_native_parity.json` — captured native oracle (NEW).
- `packages/calc-engine/tests/test_inveq_therm_native_parity.py` — parity regression (NEW, 12 tests).
- `.gitignore` — `output/` guarded (licensed binaries/decompile never committed).
- Reference guides: `G4-CALC-GUIDE.md` (§3f new + §4 rows 6/7 + §5 + §6 + header), `00-MASTER-INDEX.md`.

## Verification

- Parity + focused calc-engine tests: **24 passed**; delay_trust unit: **42 passed**.
- Native oracle: STD bit-exact (maxabs 0.0) all 4 dials; STD-gf ≡ STD-sst; GF `byICalc=1` divergence and
  `rIRef<rM` None reproduced and test-encoded.

## Residual (bounded)

1. **GF-INVEQ Therm promotion** — gated on `field13` provenance + oracle re-validation (the 1,690+6,760
   GF Therm rows). A bounded follow-up, not a mystery.
2. **GF-INVEQ Ansi** — keep-excluded vs wire `CalcAnsiEqGF` (23 sensors). Operator decision; safe default
   in place.
3. **Reference-of-record sync** — the patched native-Therm branch lives in `packages/calc-engine`; the
   `source-domains/tcc_v5_backend` reference-of-record (APEX_RESUME §5.0a; not on this clone) is a
   separate sync item.
