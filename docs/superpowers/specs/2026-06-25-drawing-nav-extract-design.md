# drawing-nav `extract` — design (estimator-takeoff Plan 2, V1)

**Status:** design / brainstorm output, 2026-06-25. Feeds the hardened breaker engine `packages/estimator-takeoff`
(Plan 1, merged to main `3a14e3cc`). This is the PRODUCER half of the seam Plan 1 left open.

## 1. Goal

A `drawing-nav extract <pdf>` command that turns a real electrical drawing package (e.g. STACK PHX02A
Addendum 4 ELEC) into the breaker engine's `ExtractionArtifact` JSON — so Plan 1 runs end-to-end on real
drawings instead of a hand-built fixture. It is a deterministic, **legend-aware** extractor; vision is used
only to resolve disputes at Gate 1, never as the primary reader.

## 2. Scope (V1 — deliberately tight)

**In:** LV power breakers on the **one-line block sheets** — primarily the `E01-1x` primary/distribution
blocks (P1-110…P7-210), plus the same-shaped Reserve (`E01-10`), Mech-gallery (`E01-30/31`), and House
(`E01-50/51`) one-lines. Block is taken from the sheet title.

**Deferred (later slices):** MV mains (`E01-01/02`), panel-schedule MCBs (`E05-*`), and
construction-from-symbol vision. These are not in V1.

**Non-goals (permanent for the extractor):** it never prices, feathers, approves, or counts — it produces a
candidate inventory. The engine de-dups, matches, fails closed, and surfaces questions.

## 3. The seam / output contract

The extractor emits a single JSON `ExtractionArtifact` matching the engine's TypeScript contract
(`packages/estimator-takeoff/src/extraction/types.ts`) — the only cross-language artifact:

```jsonc
{
  "pdf": "<filename>",
  "extractedAt": "<ISO string>",
  "apparatus": [
    {
      "raw": "ACC-1-09-FB 800AF/800AT LSIGE",   // joined label column text
      "tag": "ACC-1-09-FB",                      // device identity (legend-classified breaker)
      "sheet": "E01-11",
      "page": 11,
      "bbox": [886, 491, 944, 534],              // the device label column bbox (PDF points)
      "evidence": "one-line",                    // 'one-line' | 'panel-schedule' | 'switchgear-schedule' | 'power-plan'
      "busVoltageV": 480,                         // ONLY when unambiguous; else omitted
      "block": "P1-110",                          // from sheet title
      "mountingHint": "draw_out"                  // ONLY on explicit construction evidence; else omitted
    }
  ]
}
```

**Fidelity rule:** the extractor's output for a sheet must satisfy the engine's `extraction.test.ts` shape.
A TS-side contract test will validate real extractor output (a checked-in sample) against `ExtractionArtifact`.

## 4. Architecture — components (each independently testable)

```
drawing-nav extract <pdf>
  1. legend-profile      E00-01 → PackageProfile (suffix dict, exclusions, trip grammar, title hints)
  2. sheet-selector      index → the in-scope LV one-line block sheets (+ block/voltage from title/context)
  3. device-cluster      per sheet: PyMuPDF words → AF/AT-anchored vertical-column clusters
  4. field-assembly      cluster → {raw, tag, frameA, tripA, functions, bbox, evidence, block, busVoltageV?, mountingHint?}
  5. location-pass       power-plan sheets → tag-only location rows (evidence='power-plan')
  6. emit                ExtractionArtifact JSON (stdout or --out file)
```

### 4.1 Legend-profile (guardrail 1)
Parse `E00-01` (LEGEND AND ABBREVIATIONS) into a **PackageProfile** so the extractor adapts to each firm's
drawing standard rather than hard-coding STACK's:
- **breaker role suffixes** (the BREAKER IDENTIFIER block): `FB, GB, GMB, UB, MBB, MIB, MCB, MB, LB, …`
- **non-breaker / device exclusions** (abbreviations): `SPD, PQM, ATS, STS, TX, PDU, UPS, METER, …`
- **trip grammar** (the BREAKER KEY): `AF`=frame, `AT`=trip; trip-unit letters `L/S/I/G` (E→G handled by engine)
- **sheet-title conventions** for block + voltage hints
If `E00-01` can't be confidently parsed, fall back to a built-in default profile AND emit a top-level
`profileWarning` so Gate 1 knows the dictionary was assumed.

### 4.2 Device clustering (the core)
On a one-line sheet the breaker label is a **vertical text column at ~constant x**, anchored by an AF/AT pair:
```
(886,491) ACC-1-09-FB      tag (above)
(886,502) 800AF            frame  ← anchor
(886,513) 800AT            trip   ← anchor
(886,524) LSIGE            functions (below)
```
Algorithm: find `\d{2,6}AF`/`\d{2,6}AT` token pairs (same x, adjacent y) → each pair is a breaker anchor →
gather tokens within an x-tolerance band, ordered by y, into the device column → join into `raw`; the tag is
the column token whose suffix is in the profile's breaker-suffix set; `bbox` = the column's union bbox.
Conductor specs (`1200-3-CU`) and meters lack an AF/AT pair → self-excluded. Split tags (`ACC-1-10` + `-FB`)
are re-joined within the column.

### 4.3 Field assembly + guardrails
- **tag / raw / frameA / tripA / functions** — from the column tokens (deterministic).
- **block** (guardrail 4) — from the sheet title (`PRIMARY BLOCK P1-110` → `P1-110`; `RESERVE BLOCK R1-110/210`,
  `MECH. GALLERY DISTRIBUTION - DH110`; for named distributions with no block code, use the sheet's descriptor).
- **busVoltageV** (guardrail 4) — set ONLY when unambiguous, by a deterministic sheet-level rule: if the sheet
  carries **exactly one** LV bus-voltage label (<1000 V, e.g. `480/277V` → 480), assign that value to every
  clustered breaker on the sheet; if the sheet carries **more than one** distinct voltage label (e.g. an MV
  incoming + an LV bus, or two LV buses), **omit** `busVoltageV` for all of them → the engine raises a
  "missing voltage" question per device. (Per-device spatial bus association is deferred — omit beats guess.)
- **mountingHint** (guardrails 2 & 3) — **never** from a role suffix. Set only from explicit construction
  evidence: schedule text saying molded/ICCB/draw-out, a confident symbol classification (deferred), or a
  Gate-1 human correction. Otherwise **absent** → the engine's `mountingBasis` baseline/question path stays
  honest (≥800AF+G→draw_out baseline labelled `estimating_baseline`; everything else unmatched + a question).
- **evidence** = `one-line` for these sheets.

### 4.4 Location pass (guardrail 5)
Power-plan sheets (`E02-*`) carry device tags at physical locations, no ratings. Emit them as
`evidence: 'power-plan'`, tag-only, **no busVoltageV**. The engine associates them BY TAG to an authoritative
one-line row (preserving the location source) and NEVER counts a device seen only on a power plan.

## 5. Data flow

`drawing-nav extract Addendum4.pdf --out takeoff.json` → scp `takeoff.json` to the host →
`runTakeoff(artifact)` → `{ matchedLines, unmatchedCandidates, operatorQuestions }` → `emitEnvelope` →
priced `EstimateEnvelope`. The first real end-to-end run: the P1-110 one-line → matched breakers + the
honest unmatched/question set.

## 6. Error handling (fail-open-to-question, never fabricate)

The extractor's bias mirrors the engine's: when a field can't be determined honestly, **omit it and let the
engine surface a question** — never guess. Specifically: ambiguous voltage → omit; unparseable column →
emit `raw` + bbox with whatever parsed (engine raises a frame/trip-parse question); legend unparsed →
default profile + `profileWarning`; a tagged row that matches no breaker suffix and no exclusion → emit it
anyway (the engine fail-closes non-breakers). The extractor must not drop a breaker-shaped column silently.

## 7. Testing

- **Legend-profile unit tests** — `E00-01` text → expected suffix/exclusion/trip-grammar profile.
- **Clustering unit tests** — synthetic word lists (the stacked-column convention, split tags, a conductor
  decoy, two columns close together) → expected device clusters.
- **Block/voltage title tests** — the real `E01-1x` titles → expected block; single-LV-bus → 480V, mixed → omit.
- **Contract test (TS side)** — a checked-in real extractor sample conforms to `ExtractionArtifact`.
- **Golden end-to-end** — `extract` the real `E01-11` (P1-110) → JSON → engine `runTakeoff` → assert the known
  breakers (MSB-P1-110-GB 4000AF main, the ACC/MDP/MERDP feeders) land matched, the small/ambiguous ones land
  in unmatched/questions, and the envelope emits with no error findings. This is the real-data proof.

## 8. Code home

The extractor extends the existing **`drawing-nav`** tool (`C:\Users\jjswe\Tools\drawing-nav\drawing_nav.py`,
Windows/Python/PyMuPDF) with an `extract` subcommand — it is already built, proven on this set, and owns the
PDF vector-text layer. The spec/plan governance docs live in the canonical monorepo
(`apex-power-ops-platform/docs/superpowers/`), consistent with Plan 1. **Open decision (deferred):** whether
to relocate drawing-nav into the monorepo (`tools/`) for SSoT vs. leave it standalone — not required for V1.

## 9. Out of scope → later slices (tracked)

MV mains extraction; panel-schedule (`E05-*`) MCB extraction; construction-from-symbol vision; the spec-parser
+ Gate-2 scope profile; the full Gate-1/Gate-2 UI (this V1 emits JSON for the existing two-gate review, with
`find --render` crops as the dispute tool); SKILL.md orchestration tying drawing-nav (Windows) ↔ engine (Olares).
