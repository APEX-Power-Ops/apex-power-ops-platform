# Estimator-Takeoff Relay Family (V1) - Design

Status: SPEC (operator-ratified packet 002; this folds the ratified D1-D4 + 4 findings). Date: 2026-06-29.
Lane: estimator-takeoff/relay-family-admission (off main 4f05495f). Dev-only; merge operator-gated.
Packet: docs/superpowers/packets/estimator-takeoff-family-relays.md (Part 6 decisions + Part 9 ratification).
Predecessors (reused, must stay byte-identical): breaker engine (signature-deterministic) + transformer slice (scope_pending machinery, merged PR #49).

**Goal:** Admit the RELAY apparatus family into `packages/estimator-takeoff` as a bounded V1 slice - the second scope-driven family - so a recognized protective relay is counted per device and routed to a Gate-2 application-tier scope decision, never auto-priced, with breaker and transformer behavior untouched.

**Architecture:** Reuse the transformer slice's scope-driven machinery (discriminated-union signature, `scope_pending` disposition, candidate ref-GROUP, R1-provisional defaults, kind-prefixed `deviceId`, cross-family guards). Add a third signature `kind: 'relay'`, a device-first relay recognizer/parser, and an application-tier match table. Relays differ from transformers in three engine-visible ways, each a ratified guardrail: voltage is optional/contextual (never gates), recognition is device-first (ANSI numbers are attributes, never countable devices), and the provisional default may be absent (no-default scope_pending).

**Tech stack:** TypeScript, Vitest, pnpm workspace; host build over `ssh olares-mesh`.

## Global Constraints

- **ASCII-only** in all authored SQL/comments AND engine-emitted strings (questions, findings, scope questions, notes). Verbatim source DATA may be UTF-8. (No em-dashes in engine strings.)
- **Breaker AND transformer goldens byte-identical** after every task. Two prior families now regression-guard the third.
- **No new catalog refs and no new hours.** V1 uses the existing 9 NETA-7.9 relay refs only (D1 V1-policy). Catalog gaps are surfaced (`catalog_gap`), never fabricated.
- **Relays never auto-price.** Every recognized relay -> `scope_pending` (group + optional provisional default) or `catalog_gap`. There is no "matched" relay line in V1.
- **Gates (verified on host):** `pnpm --filter @apex/estimator-takeoff test`; `pnpm --filter @apex/estimator-takeoff typecheck`; `pnpm --filter './apps/operations-web' typecheck` (the cross-package gate; `--filter apex-operations-web` matches NOTHING - false-green trap).
- **Cross-engine (Codex) IRP** before merge; merge operator-gated (admin-rebase PR).
- **R1 (estimating authority) stays PROVISIONAL** (`R1_RATIFIED=false`) until the estimator confirms the role->tier mapping; transformers' fail-closed precedent applies (never auto-priced, so provisional is safe).

## The V1 Contract

1. **Recognize protective relays positively, DEVICE-FIRST.** A relay DEVICE is established by an anchor - a producer `candidateKind:'relay'`, OR a relay device/model token (`RELAY`/`PROTECTIVE RELAY`/known model families) together with a device identity (tag). ANSI function numbers (50, 51, 87, 87T, 27, 59, 81, 86, 79, 25, ...) are parsed ONLY as role attributes of an established relay device. A standalone ANSI number with no device anchor is NEVER counted as a relay (falls through to the existing `unrecognized_apparatus_row` path).
2. **Voltage is optional/contextual.** A relay carries an optional bus-voltage context for provenance/display but voltage never drives the tier and NEVER gates recognition. The relay assess path must not emit `missing_voltage`.
3. **Never auto-price.** A recognized relay is `scope_pending`: a candidate application-tier ref-GROUP plus, where the dominant protective role is legible from the drawing, a PROVISIONAL default tier; where the role is illegible, NO default (the operator picks at Gate-2). A recognized relay whose role maps to an orphan device type with no priced tier home (D1: 86/79/25/27/59/81 standalone) is `catalog_gap` (surfaced, never fabricated).
4. **Breaker + transformer paths untouched.** `ApparatusSignature` is a discriminated union on `kind`; every breaker/transformer-field reader narrows on `kind`; a relay can never reach `matchBreaker` or `matchTransformer` or a priced line.
5. **Element enumeration is OUT of scope.** The estimate is per device, by application tier. Per-protective-element calibration (the records/field lane, the AZ21 case) never enters the takeoff.

## Component Design (engine seams, grounded @ 4f05495f)

### 1. Extraction (`extraction/types.ts`, `extraction/parse.ts`)
Widen `ExtractedApparatus.candidateKind` from `'breaker' | 'transformer'` to `'breaker' | 'transformer' | 'relay'`; widen the `parse.ts` validation (currently rejects anything but breaker/transformer at the candidateKind guard) to accept `'relay'`. No other extraction change.

### 2. Signature types (`signature/types.ts`) - the voltage-optional guardrail
- Change `BaseSignature.voltageClass: VoltageClass` to `voltageClass?: VoltageClass` (optional).
- Re-declare `voltageClass: VoltageClass` (required) on `BreakerSignature` and `TransformerSignature` (interface override narrows optional->required; breaker/transformer keep voltage required, zero behavior change).
- Add `RelaySignature extends BaseSignature { kind: 'relay'; technology: RelayTechnology; ansiFunctions?: string[]; model?: string; role?: RelayRole; voltageClass?: VoltageClass /* contextual, may be absent */ }`. RelaySignature carries NO breaker/transformer fields (the family-leak lesson from the transformer build).
- `export type RelayTechnology = 'em' | 'microprocessor' | 'unknown'`.
- `export type RelayRole = 'overcurrent' | 'feeder' | 'motor' | 'bus_differential' | 'differential' | 'line' | 'generator' | 'multifunction_meter' | 'electromechanical' | 'unknown'` (one role per the 9 priced tiers, plus `unknown` for illegible).
- `export type ApparatusSignature = BreakerSignature | TransformerSignature | RelaySignature`.

### 3. Recognition + parse (`signature/normalize.ts`) - device-first + never-missing-voltage
- `RELAY_DEVICE` token (ASCII regex): `RELAY`, `PROTECTIVE RELAY`, and a bounded set of common model families (e.g. `SEL-?\d`, `MULTILIN`, `BECKWITH`, `BASLER`, `MICOM`); plus `candidateKind:'relay'`.
- `looksLikeRelay(x)` = (`candidateKind==='relay'`) OR (`RELAY_DEVICE` matches `x.raw` AND `x.tag` is present). DEVICE-FIRST: ANSI presence alone does NOT make `looksLikeRelay` true. Guard against transformer-accessory false positives ("fault pressure relay", "sudden pressure relay" on a transformer row): if `looksLikeTransformer(x)` is true, transformer wins (the relay branch is checked AFTER transformer in `assessCore`, mirroring how transformer is checked before breaker).
- `parseRelayTechnology(raw)`: `microprocessor` for model families / `MICROPROCESSOR` / `uP`; `em` for `ELECTROMECHANICAL`/`EM`/`SOLID.?STATE`; else `unknown`. (Drives the EM tier vs function tiers per D1 convention.)
- `parseAnsiFunctions(raw)`: extract ANSI device numbers (e.g. `\b(2[0-9]|3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9]|8[0-9])[A-Z]?\b` bounded to a known ANSI set) ONLY from an already-recognized relay device's raw; returned as `ansiFunctions` ATTRIBUTES. Never used to create or count a device.
- `parseRelayModel(raw)`: capture a model token if present (evidence/display only).
- `assessRelay(x)`: build a `RelaySignature` with `voltageClass = classifyVoltage(x.busVoltageV)` (MAY be undefined - NOT gated; no `missing_voltage`), `voltageV = x.busVoltageV`, `voltageBasis` derived `detected`/`none`, `technology`, `ansiFunctions`, `model`, `role` from `deriveRole(ansiFunctions, raw, technology)`. Assessment code `relay_recognized`.
- Conflict guard: a relay device carrying a breaker frame/trip (`FRAME_TRIP`) -> `relay_breaker_conflict` question (mirror `transformer_breaker_conflict`), signature null.
- `assessCore` order: `looksLikeTransformer` -> `looksLikeRelay` -> `NON_BREAKER` -> breaker. Relay MUST precede `NON_BREAKER`: a `Multifunction (w Meter)` relay row carries the `METER` token, which `NON_BREAKER` would otherwise swallow as `non_breaker_excluded`. Relay follows transformer so transformer accessories (`fault pressure relay`, `sudden pressure relay`) stay with the transformer.
- New `AssessmentCode` members: `relay_recognized`, `relay_breaker_conflict`.

### 4. Match (`catalog/relay-map.ts` + `catalog/relay-map.data.ts`) - R1 provisional, optional default
- `relay-map.data.ts`: the 9 priced tier refs VERBATIM from the estimator-core seed (exact strings, incl. `Protective Relay - (Bus Differential)` and `Protective Relay - (Line Protection)` with the " - "), grouped as `RELAY_TIERS` (all 9). A provisional `ROLE_TO_TIER` map (R1) from `RelayRole` -> ref, marked `R1_RATIFIED = false`. An `ORPHAN_ANSI` set (86, 79, 25, 27, 59, 81 as standalone-dominant) used to route to `catalog_gap` per D1.
- `matchRelay(sig): RelayScopeMatch | null` where `interface RelayScopeMatch { group: string[]; defaultRef?: string; scopeQuestion: string }`:
  - role legible and mapped to a tier -> `{ group: RELAY_TIERS, defaultRef: ROLE_TO_TIER[role], scopeQuestion }` (provisional default; never auto-priced).
  - clearly a relay device but role `unknown`/illegible -> `{ group: RELAY_TIERS, scopeQuestion }` with NO `defaultRef` (the no-default case).
  - dominant role is an orphan device type (ORPHAN_ANSI) with no tier home -> `null` (-> `catalog_gap`).
- `em` technology with a single legible function -> the `Protective Relay (Electromechanical)` tier as the provisional default (D1 convention: legacy EM uses the cheap tier; a microprocessor single-function relay uses its function tier).

### 5. Quantify (`quantify/quantify.ts`)
Add an explicit `s.kind === 'relay'` branch to `specKey` BEFORE the transformer branch (so the transformer branch's `s.coolant`/`s.voltageClass` reads stay narrowed and the un-narrowed `voltageClass` read at line 15 no longer applies to relays): key = `[s.kind, s.role ?? '-', s.technology, s.model ?? '-', s.voltageClass ?? '-', s.source.block ?? '-']`. `deviceId` already kind-prefixes (`relay:TAG`), preventing cross-family bucketing. `unit_of_issue: each`.

### 6. Disposition + contract (`buckets/types.ts`, `emit/emit.ts`, `runner/run.ts`, `runner/report.ts`) - no-default guardrail
- Widen `ScopePendingLine.provisionalDefaultRef: string` to `provisionalDefaultRef?: string` (optional). Readers default appropriately; operations-web does not read it (verified), but the cross-package typecheck gate is mandatory. (Alternative - a distinct no-default shape - rejected as higher surface; widening is minimal and `ApparatusDisposition.provisionalDefaultRef` is already optional.)
- Add codes: `OperatorQuestionCode` += `relay_scope_pending`, `relay_catalog_gap`, `relay_breaker_conflict`; `DispositionReasonCode` += `relay_scope_pending`, `relay_catalog_gap`, `relay_breaker_conflict`; `TakeoffFinding.code` union += `relay_catalog_gap`.
- `emit/emit.ts`: in the per-row match loop dispatch on `sig.kind` (breaker -> matchBreaker, transformer -> matchTransformer, relay -> matchRelay). A relay `RelayScopeMatch` -> `scope_pending` ScopePendingLine + disposition, stamping `candidateRefs=group`, `provisionalDefaultRef=match.defaultRef` (may be undefined), `r1Ratified=false`, `scopeQuestion`. A `null` match -> `catalog_gap` finding + disposition. Breaker + transformer emit blocks byte-identical.
- `runner/run.ts` + `runner/report.ts`: the zero-matched guard already counts `scopePendingLines`; relay scope_pending rows make a relay-only extraction a `partial_preview` (not clean, not "nothing to price"), exactly as transformer-only does. Report `scopePending[]` carries relay rows with optional default.

## Recognition signal + role mapping (the crux, expanded)

Device-first rule (D3): establish the relay device, THEN read ANSI as role evidence.
- Anchor present (candidateKind/RELAY_DEVICE token) + tag -> relay device.
- `deriveRole(ansiFunctions, raw, technology)` provisional mapping (R1, illustrative, estimator confirms):
  - `87T` (or `transformer differential`) -> `differential`
  - `87B` / `bus` -> `bus_differential`
  - generator cluster (e.g. 40 + 32 + 46 + 87G / `GENERATOR`) -> `generator`
  - line/distance (21 / `LINE` / `DISTANCE`) -> `line`
  - motor cluster (49 + 50 + 51 + 46 / `MOTOR`) -> `motor`
  - 50/51 only / `OVERCURRENT` -> `overcurrent`
  - `FEEDER` context -> `feeder`
  - multifunction + metering (`METER` / many functions + `MFR`) -> `multifunction_meter`
  - single function + `em` technology -> `electromechanical`
  - none of the above legible -> `unknown` (no-default scope_pending)
  - orphan-dominant (86/79/25/27/59/81 standalone) -> catalog_gap

Every outcome is `scope_pending` or `catalog_gap`; none auto-prices. The role map is PROVISIONAL (R1).

## R1 (estimating authority) - provisional

`R1_RATIFIED = false`. `ROLE_TO_TIER` (legible-role -> provisional default tier) is the R1 surface, presented as `provisionalDefaultRef` + `r1Ratified:false` (a Gate-2 suggestion, never authoritative). Relays never auto-price in V1, so this is fail-closed. The estimator confirms the role->tier mapping and the EM-vs-microprocessor convention (D1), then flips `R1_RATIFIED=true`. The orphan device list (86/79/25/27/59/81) awaits estimator/SME catalog decision (D1).

## Testing (TDD; operator-pinned tests in bold)

- **no-voltage relay:** a relay row with no `busVoltageV` -> `scope_pending`/`catalog_gap`, NEVER `missing_voltage`.
- **standalone-ANSI non-count:** a row that is a bare ANSI number with no device anchor -> NOT counted as a relay (unrecognized).
- **exact-ref validation:** a test asserts every ref in `relay-map.data.ts` exists VERBATIM in the live estimator-core seed (string-keyed match safety).
- **no-default scope_pending:** an illegible-role relay device -> `scope_pending` with `candidateRefs` set and `provisionalDefaultRef` undefined.
- **breaker AND transformer goldens byte-identical.**
- Recognition: device-first anchor cases; relay model families; `relay_breaker_conflict` on a relay carrying AF/AT.
- Parse: technology (em vs microprocessor), ANSI-as-attributes, fail-closed unknown role.
- Match: each legible role -> correct provisional tier; illegible -> no default; orphan -> catalog_gap.
- Quantify: two relays differing only in role/technology get separate lines; relay/breaker/transformer same tag not cross-bucketed.
- Cross-family guards: a relay can never reach `matchBreaker` or `matchTransformer`; a transformer/breaker row never produces a relay line.
- Disposition/runner: relay-only extraction -> `partial_preview`; relay `scope_pending` carried in the report (with and without default).
- Golden: a real relaying-derived fixture (mixed: an 87T differential, a feeder microprocessor relay, a bare illegible relay, plus a breaker and a transformer) -> breaker prices, transformer scope_pending, relay scope_pending (one with default, one without), `partial_preview`; Gate-2 stand-in resolves a relay tier and prices via estimator-core.

## Out of scope (V2)

Ground Fault Protection Device LV (firm 7.14, adjacent family); network-protector relays; instrument-transformer-adjacent devices; coupling to the live `tcc.relay_*` catalog (1,442 relays) for model->variant->role auto-hinting; per-protective-element enumeration and per-element pricing (records/field lane); the Gate-2 resolution UI; NETA firm-section reconciliation (none needed - firm 7.9 == canonical 7.9).
