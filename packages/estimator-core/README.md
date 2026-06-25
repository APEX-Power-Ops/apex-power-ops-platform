# @apex/estimator-core

The contract-first core of the Apex-hosted estimator. Pure, dependency-light TypeScript
(`node:crypto` only). Spec: `docs/spec/ESTIMATOR_SPEC_2026-06-22.md` (§9 steps 1–3).

## What this package is

- **Catalog** (`src/catalog`) — `core.equipment_models` modelled as a typed seed
  (`equipment-models.seed.json`, extracted from the real `tblEquipment`) + a merge-chasing
  resolver. Mirrors the future Postgres table 1:1 so promotion is mechanical.
- **Pricing** (`src/pricing`) — versioned rate cards + cost defaults (baseline `2026-01-23`).
- **Schema** (`src/schema`) — `EstimateDraft` (mutable authoring) and `EstimateEnvelope v1`
  (immutable compiled value) + the closed enums.
- **Compile** (`src/compile`) — the shared deterministic resolver: M4 quantity materialization,
  N4 scope adjustment, the P14/P19/P26/P33→P3→P4 rounding cascade, labor penny-allocation,
  service adjusted basis, and the economic-content `content_hash`.
- **Validate** (`src/validate`) — the envelope validator: the line_kind CHECK matrix + the
  invariants that make this the single producer-agnostic convergence gate.
- **Corpus** (`src/corpus`) — the golden-workbook regression corpus: the acceptance gate.

## Precision model

All money math is BigInt fixed-point. Hours scale ×10⁶; multipliers/percentages/markup ×10⁴;
rates are integer ¢/hr. Rounding is half-up away from zero, applied ONLY at the four cost-block
totals and the adjusted scope total. Per-type labor cents are largest-remainder-allocated so they
sum exactly to the block. Tolerance: ±1¢/block + ±1¢/adjusted scope total.

## Corpus provenance

The master workbook `Estimator PHX 012326` is a blank template (all cost units = 0), so the V1
corpus is hand-constructed worked examples that use the AUTHENTIC catalog ref-hours and the
AUTHENTIC rate card, with expected outputs computed by hand from the traced cell formulas. Real
filled samples drop into `src/corpus/cases/*.json` as they become available.

## Out of scope (downstream, gated)

Physical Postgres `core.*`/`ops.*` schema + RLS + role-projection/field-redaction; approve →
`ops.*` mapping + `JobNumberResolver` + the `(project_number, quote_version)` constraint/lock;
the native UI; re-pointing Chip-5 intake to emit the envelope; §8.B product features.

## Commands

```bash
pnpm install                 # from repo root, once
pnpm --filter @apex/estimator-core test       # full suite
pnpm --filter @apex/estimator-core typecheck
```

## Test environment requirement (Windows)

Vitest builds via Rollup, which loads a platform-native binary
(`@rollup/rollup-win32-x64-msvc`). On Windows with this repo on an **exFAT** drive, an antivirus / endpoint-protection
product — Windows Defender, or **HP Wolf Pro Security / Sure Sense** on HP business
machines — may **false-positive quarantine** that binary, so `vitest` fails to start. Rollup does
**not** auto-fall-back to its WASM build. Durable fix (pick one):

1. **Recommended:** clone/move the repo to an **NTFS** drive (e.g. `C:`), or
2. add an **antivirus / EDR exclusion** (a Defender exclusion, or the equivalent in HP Wolf Pro Security / your AV) for the repo directory.

The repo carries no Rollup workaround — the fix is environment-level. On a correctly-configured
machine, `pnpm install` then the test command runs cleanly. (The 61/61 suite was verified on an
affected machine via a temporary, uncommitted local `node_modules/rollup` patch.)
