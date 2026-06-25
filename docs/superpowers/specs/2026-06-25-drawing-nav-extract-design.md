# drawing-nav `extract` — design (estimator-takeoff Plan 2, V1)

**Status:** design / brainstorm output, 2026-06-25 (rev3 — folds the cross-engine IRP findings, incl. the
structural producer→consumer seam fix). Feeds the hardened breaker engine `packages/estimator-takeoff`
(Plan 1, merged to main `3a14e3cc`). V1 spans the PRODUCER (`drawing-nav extract`) **and a minimal CONSUMER
contract change** the producer requires.

## 1. Goal

A `drawing-nav extract <pdf>` command that turns a real electrical drawing package (e.g. STACK PHX02A
Addendum 4 ELEC) into the breaker engine's `ExtractionArtifact` JSON — so Plan 1 runs end-to-end on real
drawings instead of a hand-built fixture. Deterministic, **legend-aware**; vision only at Gate-1 disputes.

## 2. Scope (V1 — deliberately tight)

**In:** LV power breakers on the **one-line block sheets** — primarily `E01-1x` primary/distribution blocks
(P1-110…P7-210), plus the same-shaped Reserve (`E01-10`), Mech-gallery (`E01-30/31`), House (`E01-50/51`).
Plus the **minimal engine-side change** in §3.2 (the producer is useless without it).

**Deferred (later slices):** MV mains (`E01-01/02`), panel-schedule MCBs (`E05-*`), construction-from-symbol
vision, per-sub-block split of the Reserve sheet.

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
  "profileWarnings": [],                          // V1 addition: legend-fallback notices, e.g. ["legend E00-01 unparsed — default profile assumed"]
  "apparatus": [
    {                                             // Pass-A row: clean, fully-rated (no candidateKind needed)
      "raw": "ACC-1-09-FB 800AF/800AT LSIGE",
      "tag": "ACC-1-09-FB",
      "sheet": "E01-11", "page": 11, "bbox": [886, 491, 944, 534],
      "evidence": "one-line",
      "busVoltageV": 480,                          // only when unambiguous (§4.3); else key OMITTED
      "block": "P1-110"
      // mountingHint OMITTED in V1 (set only on explicit construction evidence; never from a role suffix)
    },
    {                                             // Pass-B row: breaker-suffix token with no AF/AT (safety net)
      "raw": "DH110-UB",
      "tag": "DH110-UB",
      "sheet": "E01-30", "page": 18, "bbox": [1200, 800, 1280, 812],
      "evidence": "one-line",
      "block": "DH110",
      "candidateKind": "breaker"                   // V1 addition: SURFACING-ONLY marker (see 3.2)
      // no busVoltageV, no frame/trip → the engine must QUESTION it, not drop it
    }
  ]
}
```
`page` (required), `sheet`, `raw`, `bbox` (4-tuple, PDF points), `evidence` (∈ `EvidenceKind`) are always
present; `tag/busVoltageV/block/mountingHint/candidateKind` are optional.

### 3.2 Consumer-side change (V1) — `candidateKind` is the seam fix
**Why required:** the engine's `looksLikeBreaker`/`BREAKER_HINT` only recognizes `GB|FB` (+ MCB/MCCB/ACB/VCB/
keywords). A Pass-B candidate with any *other* profile suffix (`UB`, `GMB`, `MBB`, `MIB`, `MB`, `LB`, …) and no
AF/AT would fail `looksLikeBreaker` → `assessApparatus` returns `{signature:null, questions:[], isBreakerShaped:false}`
→ `runTakeoff` surfaces nothing → **the breaker silently vanishes** (the exact false-green class Plan 1 hardened
against). A perfect extractor still loses the row. So V1 adds a marker the engine honors.

**`candidateKind?: 'breaker'` — semantics (load-bearing, surfacing-only):**
- Add `candidateKind?: 'breaker'` to `ExtractedApparatus`.
- `assessApparatus` treats `x.candidateKind === 'breaker'` as a breaker-shaped signal: the gate becomes
  "is it NON_BREAKER? else `candidateKind==='breaker' || looksLikeBreaker(raw)`" → so an exotic-suffix Pass-B
  candidate is breaker-shaped and its missing voltage/frame/functions become **operatorQuestions**.
- It is **surfacing-only.** It must NEVER imply mounting, functions, frame, voltage, or catalog eligibility.
  `matchBreaker` is unchanged and still requires the real normalized fields → a `candidateKind:'breaker'`
  row with incomplete data resolves to `mounting:'unknown'`/no functions → `matchBreaker` returns null →
  it lands in `unmatchedCandidates` / as a question, **never a matched or priced line.**
- It does **not** override `NON_BREAKER`: a row matching a non-breaker token (SPD/PQM/ATS/…) is still excluded/
  questioned by the engine's existing rule even if mis-marked — `candidateKind` only rescues rows that are
  otherwise unrecognized, never launders an exclusion.

**Producer side:** the extractor sets `candidateKind:'breaker'` on Pass-B candidates only (profile-suffix
tokens with no AF/AT). Pass-A rows (with AF/AT) don't need it; do not set it on non-breaker tokens.

**Fidelity rule:** the TS-side contract test validates a checked-in real extractor sample against
`ExtractionArtifact` incl. `profileWarnings` and `candidateKind`.

## 4. Architecture — components (each independently testable)

```
drawing-nav extract <pdf>
  1. legend-profile      E00-01 → PackageProfile (suffix dict, exclusions, trip grammar, title hints)
  2. sheet-selector      index → in-scope LV one-line block sheets (+ normalized block + voltage from title/context)
  3. device-discovery    per sheet: PyMuPDF words → (A) AF/AT-anchored columns + (B) legend-suffix candidates
  4. field-assembly      → {raw, tag, frameA?, tripA?, functions, bbox, evidence, block, busVoltageV?, candidateKind?}
  5. location-pass       power-plan sheets → tag-only location rows (evidence='power-plan')
  6. emit                ExtractionArtifact JSON (+ profileWarnings)
```

### 4.1 Legend-profile (guardrail 1)
Parse `E00-01` into a **PackageProfile** (adapts to each firm's standard):
- **breaker role suffixes** (BREAKER IDENTIFIER): `FB, GB, GMB, UB, MBB, MIB, MCB, MB, LB, …`
- **non-breaker exclusions** (abbreviations): `SPD, PQM, ATS, STS, TX, PDU, UPS, METER, …`
- **trip grammar** (BREAKER KEY): `AF`=frame, `AT`=trip; `L/S/I/G` (E→G handled by engine)
- **sheet-title block/voltage hints**
If `E00-01` can't be parsed confidently → built-in default profile + a `profileWarnings` entry.

### 4.2 Device discovery — two passes (no silent drops)
A breaker label is a **vertical column at ~constant x**, anchored by an AF/AT pair.
- **Pass A — AF/AT-anchored (primary):** find `\d{2,6}AF`/`\d{2,6}AT` pairs (same x, adjacent y); gather the
  same-x column → `raw`; tag = column token whose suffix ∈ profile breaker-suffix set; parse
  `frameA/tripA/functions`; `bbox` = column union. Conductors (`1200-3-CU`)/meters lack AF/AT → excluded.
- **Pass B — legend-suffix candidates (safety net):** tokens whose suffix ∈ profile breaker-suffix set but NOT
  captured by Pass A → emit `raw` + `tag` + `bbox` + **`candidateKind:'breaker'`**, no frame/trip. This gives a
  tagged-but-unrated breaker a discovery path; the engine (via §3.2) questions it. **No breaker-suffix token
  is silently dropped — by producer (Pass B) AND consumer (`candidateKind`).**
Split tags (`ACC-1-10` + `-FB`) re-joined within a column/candidate.

### 4.3 Field assembly + guardrails
- **tag / raw / frameA / tripA / functions** — Pass-A from column tokens; Pass-B has no frame/trip.
- **block** (guardrail 4) — normalized from the sheet title to a **stable key**, deterministically:
  1. join the title's tokens (vector text may split it), 2. collapse whitespace, 3. case-fold,
  4. replace any run of non-alphanumeric with a single `-` for codes / `_` for descriptors, 5. exact-match the
  canonical map:

  | Sheet(s) | Title | `block` |
  |----------|-------|---------|
  | E01-11…E01-17 | PRIMARY BLOCK P*n*-1*x*0 | `P1-110` … `P7-210` |
  | E01-10 | RESERVE BLOCK R1-110/210 | `R1-110-210` (covers both; per-sub-block split deferred) |
  | E01-30 / E01-31 | MECH. GALLERY DISTRIBUTION — DH110 / DH210 | `DH110` / `DH210` |
  | E01-50 | HOUSE DISTRIBUTION — NON-CRITICAL | `HOUSE_NON_CRITICAL` |
  | E01-51 | HOUSE DISTRIBUTION — CRITICAL | `HOUSE_CRITICAL` |

  A `BLOCK <code>` token in the title is preferred (→ uppercased code); else the canonical UPPER_SNAKE key.
  Unknown title → `UNKNOWN_<sheetId>` + a `profileWarnings` note. (Determinism is unit-tested with title variants.)
- **busVoltageV** (guardrail 4) — deterministic sheet-level rule over **all** voltage labels on the sheet (LV
  *and* MV): if the sheet carries **exactly one** voltage label and it is LV (<1000 V, e.g. `480/277V`→480),
  assign it to every breaker on the sheet; if the sheet carries **more than one** distinct voltage label
  (e.g. an MV incoming + the LV bus, the normal Primary-Block case once MV is present), or **zero** voltage
  labels, **omit** `busVoltageV` for all → the engine raises a missing-voltage question per device. This
  prevents broadcasting 480 V onto an MV device. (Per-device spatial bus association is deferred — omit > guess.)
- **mountingHint** (guardrails 2 & 3) — **OMITTED in V1.** Never from a role suffix. Populated only by explicit
  construction evidence (schedule text molded/ICCB/draw-out · confident symbol classification [deferred] ·
  Gate-1 human correction) — none produced in V1. The engine's `mountingBasis` baseline/question path stays honest.
- **evidence** = `one-line`.

### 4.4 Location pass (guardrail 5)
Power-plan sheets (`E02-*`): tag-only rows, `evidence:'power-plan'`, no `busVoltageV`. The engine associates
them BY TAG to an authoritative one-line row (preserving the location source) and NEVER counts a power-plan-only
device.

## 5. Data flow
`drawing-nav extract Addendum4.pdf --out takeoff.json` → scp to host → `runTakeoff` → 3 buckets → `emitEnvelope`
→ priced envelope. First real run: P1-110 one-line → matched breakers + honest unmatched/questions.

## 6. Error handling (fail-open-to-question, never fabricate)
Omit-and-question over guess: ambiguous/zero/multi voltage → omit; breaker-suffix token with no AF/AT → Pass-B
`candidateKind:'breaker'` candidate (engine questions it via §3.2); legend unparsed → default profile +
`profileWarnings`; a token matching neither a breaker suffix nor an exclusion → emit anyway (engine fail-closes).
No breaker-suffix token is dropped on either side of the seam.

## 7. Testing

**Engine (TS, consumer change):**
- `candidateKind` surfacing — `assessApparatus({raw:'DH110-UB', candidateKind:'breaker', no busVoltageV})` →
  `isBreakerShaped:true`, a missing-voltage question, `signature:null`.
- **Orphan-suffix golden (req 3 / finding 3)** — `runTakeoff` on an artifact whose only `DH110-UB`
  (`candidateKind:'breaker'`, no AF/AT, no voltage) has a tag matching NOTHING counted → it produces an
  **operatorQuestion** (proves it neither vanishes nor folds into a location).
- **Surfacing-only invariant (req 4)** — a `candidateKind:'breaker'` row with incomplete data never appears in
  `matchedLines` and never reaches the envelope (assert `matchedLines` excludes it; it's an unmatched/question).
- `candidateKind` does not override `NON_BREAKER` — a `candidateKind:'breaker'` row whose raw is an SPD/ATS
  still excludes/questions, never matches.
- Contract test (`packages/estimator-takeoff/test/extraction.test.ts` — the real sibling-`test/` file) asserts
  `profileWarnings` is `string[]` when present and `candidateKind` ∈ {`'breaker'`, undefined}; new fixture
  `test/fixtures/stack-phx02a-extract.json`.

**Extractor (Python):**
- Legend-profile: `E00-01` → expected profile; unparseable → default + `profileWarnings`.
- Discovery: stacked column, split tags, conductor decoy (no row), two close columns (two devices), AND a
  breaker-suffix token with no AF/AT → a Pass-B `candidateKind:'breaker'` candidate.
- **Block normalization determinism (req 5 / finding 5)** — 2–3 punctuation/spacing/em-dash/line-wrapped
  variants of each real title → identical key.
- **Voltage (req 6 / finding 4)** — an explicit **single-voltage Primary-Block** sheet → 480 broadcast (cannot
  pass by accident); a sheet with LV+MV labels → omitted; zero voltage labels → omitted.

**Golden end-to-end:** `extract` the real `E01-11` → JSON → engine → known mains/feeders matched, ambiguous ones
in unmatched/questions, the envelope emits with no error findings. Real-data proof.

## 8. Code home
Producer: extend `drawing-nav` (`C:\Users\jjswe\Tools\drawing-nav\drawing_nav.py`, Windows/Python/PyMuPDF) with
an `extract` subcommand. Consumer change (`candidateKind?: 'breaker'` + `profileWarnings?: string[]` on
`ExtractedApparatus`/`ExtractionArtifact`, the `assessApparatus` gate, + tests) lands in the monorepo. Both on
branch `estimator-takeoff/extract` (off main). **Open decision (deferred):** relocate drawing-nav into the
monorepo (`tools/`) vs. standalone — not required for V1.

## 9. Out of scope → later slices (tracked)
MV mains; panel-schedule (`E05-*`) MCBs; construction-from-symbol vision; per-sub-block Reserve split; the
spec-parser + Gate-2 scope profile; full Gate-1/2 UI (V1 emits JSON for the existing two-gate review, `find
--render` crops as dispute tool); SKILL.md orchestration (drawing-nav ↔ engine).
