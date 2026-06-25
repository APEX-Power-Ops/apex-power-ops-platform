# drawing-nav `extract` — design (estimator-takeoff Plan 2, V1)

**Status:** design / brainstorm output, 2026-06-25 (rev4 — folds the cross-engine IRP, incl. Codex's HIGH:
LV pricing must require a parsed frame rating). Feeds the hardened breaker engine `packages/estimator-takeoff`
(Plan 1, merged to main `3a14e3cc`). V1 spans the PRODUCER (`drawing-nav extract`) **and a minimal CONSUMER
change** the producer requires.

## 1. Goal
A `drawing-nav extract <pdf>` command that turns a real electrical drawing package (e.g. STACK PHX02A
Addendum 4 ELEC) into the breaker engine's `ExtractionArtifact` JSON — so Plan 1 runs end-to-end on real
drawings instead of a hand-built fixture. Deterministic, **legend-aware**; vision only at Gate-1 disputes.

## 2. Scope (V1 — deliberately tight)
**In:** LV power breakers on the **one-line block sheets** — `E01-1x` primary/distribution blocks
(P1-110…P7-210), plus the same-shaped Reserve (`E01-10`), Mech-gallery (`E01-30/31`), House (`E01-50/51`).
Plus the **minimal engine-side change** in §3.2 (the producer is useless without it).
**Deferred:** MV mains (`E01-01/02`), panel-schedule MCBs (`E05-*`), construction-from-symbol vision,
per-sub-block split of the Reserve sheet.
**Non-goals (permanent):** the extractor never prices, feathers, approves, or counts — it produces a candidate
inventory. The engine de-dups, matches, fails closed, surfaces questions.

## 3. The seam / contract

### 3.1 The artifact (producer output)
A single JSON `ExtractionArtifact` matching the engine's TS contract
(`packages/estimator-takeoff/src/extraction/types.ts`). Two **V1 additive contract fields**:

```jsonc
{
  "pdf": "<filename>",
  "extractedAt": "<ISO string>",
  "profileWarnings": [],                          // V1 addition: legend-fallback/unknown-title notices
  "apparatus": [
    {                                             // Pass-A row: clean, fully-rated
      "raw": "ACC-1-09-FB 800AF/800AT LSIGE", "tag": "ACC-1-09-FB",
      "sheet": "E01-11", "page": 11, "bbox": [886, 491, 944, 534],
      "evidence": "one-line", "busVoltageV": 480, "block": "P1-110"
      // mountingHint OMITTED in V1 (set only on explicit construction evidence; never from a role suffix)
    },
    {                                             // Pass-B row: breaker-suffix token with no AF/AT (safety net)
      "raw": "DH110-UB", "tag": "DH110-UB",
      "sheet": "E01-30", "page": 18, "bbox": [1200, 800, 1280, 812],
      "evidence": "one-line", "block": "DH110",
      "candidateKind": "breaker"                   // SURFACING-ONLY marker (3.2); no voltage/frame → engine QUESTIONS it
    }
  ]
}
```
`page` (required), `sheet`, `raw`, `bbox` (4-tuple PDF points), `evidence` (∈ `EvidenceKind`) always present;
`tag/busVoltageV/block/mountingHint/candidateKind` optional.

### 3.2 Consumer-side change (V1) — three parts
The producer is useless unless the engine honors the marker AND refuses to price unrated breakers. V1 adds:

**(a) `candidateKind?: 'breaker'` — SURFACING-ONLY marker.** The engine's `looksLikeBreaker`/`BREAKER_HINT`
only recognizes `GB|FB` (+ keywords); a Pass-B candidate with any other profile suffix (`UB`, `GMB`, `MBB`,
`MIB`, `MB`, `LB`, …) and no AF/AT would fail it and **vanish silently** (the Plan-1 false-green class). Fix:
add `candidateKind?: 'breaker'` to `ExtractedApparatus`; change the ONE existing gate line in `assessApparatus`
from `if (!looksLikeBreaker(x.raw)) return …` to **`if (x.candidateKind !== 'breaker' && !looksLikeBreaker(x.raw)) return …`**
(edit that single return — do NOT add a separate early branch that bypasses the downstream voltage/mounting
flow). So an exotic-suffix candidate is breaker-shaped and its missing voltage/frame/functions become
operatorQuestions. It runs AFTER the `NON_BREAKER` check (so a mis-marked SPD/ATS still excludes — never
laundered) and the marker never flows into `ApparatusSignature`/`matchBreaker`.

**(b) LV pricing eligibility requires a parsed frame rating (Codex HIGH fix, operator-ratified).** The LV
`matchBreaker` rules currently match `panelboard`/`molded_case` on **mounting alone** — so an unrated `MCB`
candidate (no AF/AT) that picks up a sheet-broadcast `busVoltageV` could be **priced** (`MCB`→`panelboard`→
`Circuit Breaker LV - Panelboard MCB`). Counterexample: `raw:'LP-1-MCB', candidateKind:'breaker', busVoltageV:480`.
**Fix: every LV `BREAKER_MAP` rule additionally requires `s.frameA !== undefined`**, on top of the fields it
already requires (G for LSIG, functions for LS/LSI). The ratified invariant:
> **LV pricing requires parsed voltage + mounting + frame rating + any rule-specific fields. MV is separate
> (keys on `mvType`; no `frameA` requirement).**
Consequence: `LP-1-MCB` (no `frameA`) → no LV match → unmatched + a question, **never priced**; a real
`400AF/400AT MCB` (480 V, panelboard) → has `frameA` → eligible. Existing LS/LSI power-breaker protections
unchanged. (The synthetic `breaker-map.test` base gains a `frameA`.)

**(c) `profileWarnings` propagation.** Add `profileWarnings?: string[]` to `ExtractionArtifact`; `runTakeoff`
reads `artifact.profileWarnings` and appends each to `operatorQuestions` (context `legend/profile`) so
legend-fallback / unknown-title warnings reach Gate 1 instead of being dead metadata.

**Producer side:** the extractor sets `candidateKind:'breaker'` on Pass-B candidates only (profile-suffix
tokens with no AF/AT); never on non-breaker tokens. **Fidelity rule:** the TS contract test validates a
checked-in real extractor sample against `ExtractionArtifact` incl. `profileWarnings` and `candidateKind`.

## 4. Architecture — components (each independently testable)
```
1. legend-profile   E00-01 → PackageProfile (suffix dict, exclusions, trip grammar, title hints)
2. sheet-selector   index → in-scope LV one-line block sheets (+ normalized block + voltage from title/context)
3. device-discovery per sheet: PyMuPDF words → (A) AF/AT-anchored columns + (B) legend-suffix candidates
4. field-assembly   → {raw, tag, frameA?, tripA?, functions, bbox, evidence, block, busVoltageV?, candidateKind?}
5. location-pass    power-plan sheets → tag-only location rows (evidence='power-plan')
6. emit             ExtractionArtifact JSON (+ profileWarnings)
```

### 4.1 Legend-profile (guardrail 1)
Parse `E00-01` into a **PackageProfile**: breaker role suffixes (`FB, GB, GMB, UB, MBB, MIB, MCB, MB, LB, …`);
non-breaker exclusions (`SPD, PQM, ATS, STS, TX, PDU, UPS, METER, …`); trip grammar (`AF`/`AT`, `L/S/I/G`);
sheet-title block/voltage hints. Unparseable → built-in default profile + a `profileWarnings` entry.

### 4.2 Device discovery — two passes (no silent drops)
A breaker label is a **vertical column at ~constant x**, anchored by an AF/AT pair.
- **Pass A — AF/AT-anchored:** find `\d{2,6}AF`/`\d{2,6}AT` pairs (same x, adjacent y); gather the same-x
  column → `raw`; tag = column token whose suffix ∈ profile breaker set; parse `frameA/tripA/functions`;
  `bbox` = column union. Conductors (`1200-3-CU`)/meters lack AF/AT → excluded.
- **Pass B — legend-suffix candidates:** tokens whose suffix ∈ profile breaker set but NOT in a Pass-A column
  → emit `raw` + `tag` + `bbox` + **`candidateKind:'breaker'`**, no frame/trip. The engine surfaces it via
  §3.2(a) and refuses to price it via §3.2(b). **No breaker-suffix token is silently dropped, and none is
  priced without a rating.** Split tags re-joined within a column/candidate.

### 4.3 Field assembly + guardrails
- **block** (guardrail 4) — normalized from the sheet title to a **stable key**, deterministically, in this
  order of operations: 1. join the title's tokens (vector text may split/wrap them), 2. collapse whitespace,
  3. case-fold, 4. replace any run of non-alphanumeric with a single `-`, 5. **exact-match the canonical map
  below (this wins)**; only if unlisted, fall back to a `BLOCK <code>` token from the title; else
  `UNKNOWN_<sheetId>` + a `profileWarnings` note.

  | Sheet(s) | Title | `block` |
  |----------|-------|---------|
  | E01-11…E01-17 | PRIMARY BLOCK P*n*-1*x*0 | `P1-110` … `P7-210` |
  | E01-10 | RESERVE BLOCK R1-110/210 | `R1-110-210` (covers both; per-sub-block split deferred) |
  | E01-30 / E01-31 | MECH. GALLERY DISTRIBUTION — DH110 / DH210 | `DH110` / `DH210` |
  | E01-50 | HOUSE DISTRIBUTION — NON-CRITICAL | `HOUSE_NON_CRITICAL` |
  | E01-51 | HOUSE DISTRIBUTION — CRITICAL | `HOUSE_CRITICAL` |

  (Determinism unit-tested with punctuation/spacing/em-dash/line-wrap title variants, incl. the `R1-110/210` slash.)
- **busVoltageV** (guardrail 4) — deterministic rule over **all** voltage labels on the sheet (LV *and* MV):
  exactly one voltage label AND it is LV (<1000 V) → assign to every breaker on the sheet; **more than one**
  distinct label (MV incoming + LV bus), or **zero** labels → **omit** for all → engine missing-voltage
  question. Prevents broadcasting 480 V onto an MV device. (Producer must actually detect MV labels.)
- **frameA/tripA/functions** — Pass-A from column tokens; Pass-B has none.
- **mountingHint** — **OMITTED in V1.** Never from a role suffix. Only from explicit construction evidence
  (none produced in V1). The engine's `mountingBasis` baseline/question path stays honest.
- **evidence** = `one-line`.

### 4.4 Location pass (guardrail 5)
Power-plan sheets (`E02-*`): tag-only rows, `evidence:'power-plan'`, no `busVoltageV`. The engine associates
by tag to an authoritative one-line row (preserving the location source) and NEVER counts a power-plan-only device.

## 5. Data flow
`drawing-nav extract Addendum4.pdf --out takeoff.json` → scp to host → `runTakeoff` → 3 buckets →
`emitEnvelope` → priced envelope. First real run: P1-110 one-line → matched breakers + honest unmatched/questions.

## 6. Error handling (fail-open-to-question, never fabricate, never price unrated)
Omit-and-question over guess: ambiguous/zero/multi voltage → omit; breaker-suffix token with no AF/AT → Pass-B
`candidateKind:'breaker'` (engine questions it, never prices it without a frame); legend unparsed → default
profile + `profileWarnings` (propagated to questions). **Surfacing guarantee (precise):** every *breaker
candidate* — a breaker-suffix token (Pass A/B) or an AF/AT-bearing column — is surfaced (matched, unmatched,
or questioned). A token that is **neither** a breaker suffix nor a recognized exclusion is simply not emitted
as apparatus (it is not a breaker); the engine does not — and is not expected to — question every unknown token.

## 7. Testing

**Engine (TS consumer change) — minimum rev4 set:**
- **MCB pricing leak closed** — `runTakeoff` on `{raw:'LP-1-MCB', candidateKind:'breaker', busVoltageV:480,
  evidence:'one-line', no AF/AT}` → NOT in `matchedLines`; surfaces an operatorQuestion (and/or unmatched). Never priced.
- **Real rated MCB still matches** — `400AF/400AT` panelboard/molded MCB with `busVoltageV:480` → matched + priced.
- **Orphan exotic suffix still surfaces** — `DH110-UB` (`candidateKind:'breaker'`, no AF/AT, no voltage, tag
  matching nothing counted) → an operatorQuestion (neither vanishes nor folds into a location).
- **profileWarnings surfaced** — an artifact with `profileWarnings:['…']` → those strings appear in
  `runTakeoff(...).operatorQuestions`.
- **frameA eligibility unit tests** — `matchBreaker({…LV, mounting:'panelboard', frameA:undefined})` → null;
  with `frameA` present → the panelboard ref; same for `molded_case`; draw-out/EO/insulated LSIG·LS/LSI rules
  also require `frameA`. The synthetic `breaker-map.test` `base` gains a `frameA`.
- **No regression** — the existing 55 tests + the Plan-1 golden still pass (gate edit is additive; fixture
  devices all carry `frameA`).
- Contract test (`packages/estimator-takeoff/test/extraction.test.ts`) asserts `profileWarnings` is `string[]`
  when present and `candidateKind` ∈ {`'breaker'`, undefined}; new fixture `test/fixtures/stack-phx02a-extract.json`.

**Extractor (Python):**
- Legend-profile → expected profile; unparseable → default + `profileWarnings`.
- Discovery: stacked column, split tags, conductor decoy (no row), two close columns, AND a breaker-suffix
  token with no AF/AT → a Pass-B `candidateKind:'breaker'` candidate.
- Block-normalization determinism — title variants (incl. `R1-110/210` slash) → identical key.
- Voltage — single-voltage Primary-Block sheet → 480 broadcast (cannot pass by accident); LV+MV sheet → omitted;
  zero labels → omitted.

**Golden end-to-end:** `extract` the real `E01-11` → JSON → engine → known mains/feeders matched, ambiguous
ones in unmatched/questions, envelope emits with no error findings. Real-data proof.

## 8. Code home
Producer: extend `drawing-nav` (`C:\Users\jjswe\Tools\drawing-nav\drawing_nav.py`, Windows/Python/PyMuPDF) with
an `extract` subcommand. Consumer change (the §3.2 three parts + tests) lands in the monorepo. Both on branch
`estimator-takeoff/extract` (off main). **Open decision (deferred):** relocate drawing-nav into the monorepo
(`tools/`) vs. standalone — not required for V1.

## 9. Out of scope → later slices (tracked)
MV mains; panel-schedule (`E05-*`) MCBs; construction-from-symbol vision; per-sub-block Reserve split; the
spec-parser + Gate-2 scope profile; full Gate-1/2 UI (V1 emits JSON for the two-gate review, `find --render`
crops as dispute tool); SKILL.md orchestration (drawing-nav ↔ engine).
