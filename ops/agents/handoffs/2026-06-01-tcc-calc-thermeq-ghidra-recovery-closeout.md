# 2026-06-01 CC TCC CalcThermEq recovery closeout

## Status

Partially closed with code patch. The native Therm formula is recovered and the managed solver is patched. The field-sheet trust promotion still needs captured EasyPower point fixtures.

## Binary recovery

The Drive artifact `TccBase.dll` was directly downloadable and exports the target methods:

- `CTccLVBreakerCurveGF.CalcThermEq`
- `CTccLVBreakerCurveGF.CalcAnsiEqGF`
- `SetTherm_*`
- `SetAnsi_*`

The larger `EasyPower.exe` direct noninteractive download hit Google Drive's virus-warning page, so recovery proceeded from `TccBase.dll`, which contains the exported evaluator bodies. Host tooling used for inspection: `mono-utils`, `.NET SDK 8`, and `ilspycmd` 9.1.0.7988.

## Formula verdict

`CalcThermEq` uses both `rIref` and `rM`, so the prior managed formula was wrong when it ignored c4/c5.

Recovered normalized Therm form:

```text
T = rTref * ln(1 / (1 - (rM / I_norm)^rX))
    / ln(1 / (1 - (rM / rIref)^rX))

floor = rTmin
```

The managed coefficient mapping is:

- `c1 = rTmin`
- `c2 = rX`
- `c3 = rTref`
- `c4 = rIref`
- `c5 = rM`
- `c6 = unused for Therm`

`CalcAnsiEqGF` was also recovered:

```text
I_adj = (I_norm / (1 + rTol)) - C
T = A + B / I_adj + D / I_adj^2 + E / I_adj^3
floor = Tmin
```

ANSI remains intentionally excluded until the runtime has a family-aware ANSI solver path with captured parity fixtures.

## Code changes

- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_curves.py`
  - Adds a native Therm branch for rows shaped as `rTmin/rX/rTref/rIref/rM`.
  - Keeps legacy IEEE fallback for non-Therm rows.
- `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_delay_routing.py`
  - Adds `gf_inveq_is_excluded_ansi`.
  - Threads `id_open_eq` through `dispatch_gfd_delay` and `route_delay_curve`.
  - Keeps GF ANSI InvEq rows withheld with an INV-7 diagnostic.
- Tests updated in:
  - `packages/calc-engine/tests/test_source_faithful_adapters.py`
  - `packages/calc-engine/tests/test_etu_delay_routing.py`
- Reference guides updated:
  - `reference/tcc/00-MASTER-INDEX.md`
  - `reference/tcc/G2-RULES-GUIDE.md`
  - `reference/tcc/G4-CALC-GUIDE.md`

## Verification

- Focused tests:
  - `12 passed`
- Broader targeted TCC slices:
  - `97 passed, 1 skipped, 1 warning`
- Live ETU SQL parity:
  - PASS across 3 seeded scenarios; evaluate warnings 0.
- Live relay SQL parity:
  - PASS across 6 seeded scenarios; warnings 0; failures 0.

## Residual

Captured EasyPower point fixtures are still required before G4 field-trust rows 6-7 Therm can be promoted to field-sheet-shippable. ANSI has a recovered formula but remains excluded until the project deliberately chooses to wire and fixture that path.
