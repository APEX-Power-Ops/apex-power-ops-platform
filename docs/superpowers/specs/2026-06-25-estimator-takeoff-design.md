# estimator-takeoff Skill — Design

Date: 2026-06-25
Status: Design v2.3 (planned; grounding corrections from canonical estimator-core)
Topic: A Claude skill that parses electrical drawing packages into an **evidence-preserving
quantity takeoff** mapped to the live `estimator-core` catalog — emitted as a reviewable
`EstimateDraft` (status `draft`) for the estimator, plus an evidence sidecar and open questions.

> Supersedes `2026-06-25-neta-estimate-from-drawings-design.md` (renamed `neta-estimate` →
> `estimator-takeoff` per audit; tightened to a takeoff assistant, not an estimating engine).
> **v2.1 (2nd / Codex audit):** uncataloged equipment fail-closed; voltage MV ≤ 69 kV / HV > 69 kV;
> code homes grounded to CANONICAL `apex-power-ops-platform/packages/estimator-core` (the staging
> POC has drifted); sampling deferred (no quantity mutation); sidecar field note corrected; file
> permissions normalized.
> **v2.2 (3rd / Codex on canonical):** `ScopeDraft` emission must include the REQUIRED
> `labor_allocation` (neutral default, estimator-feathered); human-supplied `custom_equipment`
> must carry `base_qty > 0` (validator requires `base_qty > 0` AND `provisional_ref_hours > 0`).
> **v2.3 (grounding on canonical, during planning):** (1) HOME RESOLVED — `packages/estimator-takeoff`
> as a **TS** package importing `@apex/estimator-core` directly (not Python in `tools/`); drawing-nav
> (Python, Windows) feeds a JSON extraction artifact. (2) EMIT RESOLVED — emit through the canonical
> **`buildNativeEnvelope(NativeEnvelopeInput)`** authoring API (catalog `{ref, qty}` lines only),
> which sets M4/N4, `labor_allocation`, `expansion_policy`, compile + validate BY CONSTRUCTION. This
> SUPERSEDES §6.4's hand-built `LineDraft` mapping and MOOTS the v2.1/v2.2 `labor_allocation` /
> `custom_equipment` line notes for V1 (the API is catalog-only ⇒ uncataloged is fail-closed for
> free). Breaker catalog: 34 canonical refs (`ref == apparatus`, `ref_hours` per ATS/MTS).
> Build plan: `docs/superpowers/plans/2026-06-25-estimator-takeoff-breaker-engine.md`.

> **Contract authority:** the live `estimator-core` in `apex-power-ops-platform` (Olares
> dev-residency) — NOT the `C:\dev\estimator-ui-staging` POC, which is divergent. All schema/field
> claims below must be re-grounded against canonical as the first plan step.

---

## 1. Problem & goal

Building a NETA testing quote from an issued drawing package means a human manually counting
apparatus across dozens of large sheets and mapping each to a catalog test-labor figure. The
**count + catalog mapping** is the slow, error-prone, valuable upstream work.

**Goal:** a narrow Claude skill — `estimator-takeoff` — that inspects drawings/schedules, counts
apparatus, identifies **voltage class**, maps to live catalog refs, organizes into scopes, and
emits a **reviewable takeoff**: an `EstimateDraft` (status `draft`) + an evidence sidecar + an
open-questions list. It does **not** price, feather, approve, or push to ops. The estimator owns
labor feel, rates, travel, adders, and final shaping.

## 2. Center of gravity (ratified)

- The **live equipment catalog × accurate, evidenced quantities** is the bedrock. Always start
  from catalog base hours. The hard job is getting **project-wide apparatus quantities + voltage
  class** right, with evidence.
- **Feathering, rates, travel, and all financial shaping live in the estimator.** The skill must
  not rebuild or pre-empt them. (Travel is literally a `cost` line — out of scope here.)
- Keep V1 simple and narrow. Do not overcomplicate.

## 3. Decisions (ratified; v2 incorporates external audit)

1. **Boundary / output:** the skill emits a reviewable **`EstimateDraft` with `status: 'draft'`**
   (never `approved`), an **evidence sidecar**, and an **open-questions** list. `estimator-core`
   prices; nothing is auto-approved or pushed to ops.
2. **Parameter source:** layered profile resolved **human > spec > default** (merge-chasing). Needs
   a small spec-parser alongside the drawing-parser.
3. **Parameter grain:** equipment-class level now; profile shaped so a per-test sub-layer can be
   added later.
4. **Gates:** two mandatory human gates — (1) inventory verify, (2) scope review.
5. **Build:** contract-first, deterministic, tested modules; thin `SKILL.md`. **Breaker vertical
   slice first.**
6. **Scope-decisions-only (crisp definition):** the skill decides ONLY — scope grouping, ATS/MTS
   selection, inclusion/exclusion, drawing-derived quantity logic, and unresolved-question
   surfacing. It does NOT touch labor rates, travel, productivity, feathering, or any financial
   adjustment. (Audit caution adopted; the earlier "propose mobilization/travel adders" idea is
   REMOVED — travel/mob are financial → estimator.)
7. **Focus:** identify apparatus + **voltage class** robustly; advisory **pattern-flags** layer
   flags where hours likely deviate (never auto-applied).
8. **Neutral multipliers (audit):** the skill emits `replication_m4 = 1` and
   `adjustment_multiplier_n4 = 1`. Quantities are **explicit counts**; repeated typicals are
   **expanded into `base_qty` with evidence** (`expansion_policy: 'one_unit_per_qty'`), never hidden
   in a multiplier.
9. **No catalog bundling (audit):** reference the **live** `estimator-core` catalog seed / resolver
   API. Never copy an equipment list into the skill (drift).
10. **Unmatched is first-class & fail-closed (audits):** never silently guess a catalog ref, and
    never auto-emit an *included* line for uncataloged equipment (it would lack resolved hours).
    Output three buckets — `matched_lines`, `unmatched_candidates`, `operator_questions`.

## 4. Scope

**In (V1, breaker slice):** apparatus + voltage class (LV/MV/HV) for circuit breakers (LV
power/molded-case, MV drawout); project-wide de-duplicated counts with evidence; live catalog
mapping; the two gates; advisory pattern-flags; `EstimateDraft` (`draft`) + evidence sidecar +
questions; validation through `estimator-core`.

**Out (deferred):** pricing/feathering/travel/financials (estimator); test-procedure grain;
learning pattern hour-deltas from history (schema forward-shaped); classes beyond breakers
(transformers, switchgear assemblies, panels, cable, relays, grounding, SPDs) — one at a time after
the slice.

## 5. Architecture — component map

```
drawing package ─▶ [1] Drawing intake (drawing-nav, BUILT) → raw apparatus strings + provenance
                       ▼
                  [2] Normalize → signature {class, voltage_class, frame, trip, functions, mounting}
                       ▼
                  [3] Quantify (de-dup; per-class authoritative-source rule) → explicit counts
                       ▼
                  [4] Catalog match (LIVE seed/API) → matched_lines │ unmatched_candidates │ questions
                       ▼
                  [5] Pattern flags (advisory) attach to lines
                  ══ GATE 1: verify inventory (counts, voltage class, unmatched, flags, evidence) ══
                       ▼
project spec ──▶ [6] Spec parser → scope-decision proposals (cite clauses)
                       ▼
                  [7] Profile resolve (default ⊕ spec ⊕ human)  — scope decisions only
                  ══ GATE 2: review scope decisions ══
                       ▼
                  [8] Emit: EstimateDraft(draft) + evidence sidecar + open-questions
                       ▼
                  estimator-core validate (refs/qty) → handoff for pricing & feathering
```

Deterministic linchpins (tested code): **[3] Quantify** and **[8] Emit**. Claude supplies judgment
for reading sheets, interpreting spec clauses, and resolving ambiguity at the gates.

## 6. Data contracts

### 6.1 Apparatus signature (normalizer output)
```jsonc
{ "class": "lv_power_breaker",
  "voltage_class": "LV",            // LV (<1kV) | MV (>=1kV and <=69kV) | HV (>69kV)
  "voltage_v": 480,
  "frame_a": 4000, "trip_a": 4000,
  "functions": ["L","S","I","G"],
  "mounting": "drawout|molded_case|unknown",
  "tag": "MSB-P1-110-GB" }
```

### 6.2 Voltage-class bands (corrected per user)
- **Takeoff routing convention** (NOT a universal electrical taxonomy): **LV** < 1 kV ·
  **MV** ≥ 1 kV and ≤ 69 kV · **HV** > 69 kV — matching the local NETA extracts' ≤ 69 kV / > 69 kV
  grouping. (The earlier "<69 kV is HV" note was a typo/shorthand and is superseded.)
- Derived from bus voltage labels (`480V`, `415Y/240V`, `4160V`, `12.47kV`, `13.8kV`, `15kV`),
  transformer pri/sec, and `MEDIUM VOLTAGE SYSTEM` / `MV` / `MVS` annotations; breaker class = its
  bus class. (Data-center NETA scope is overwhelmingly LV + MV; HV is rare/utility-side.) Gate 1
  shows `voltage_class` + `voltage_v` per device.

### 6.3 Quantify — de-dup rule (the linchpin)
- One **authoritative counting source** per class. Breakers: **one-lines + switchgear/panel
  schedules** are authoritative; **power plans are locations only — never add to the count.**
- Aggregate identical signatures into explicit counts; retain every contributing source on the
  count. Typicals ("typ. of 5") are **expanded into the count with evidence**, not multiplied.
- Golden test guards against double-counting across sheet types.

### 6.4 What the skill emits → real `estimator-core` schema
- `EstimateDraft` (`status: 'draft'`) → one `Revision` → `ScopeDraft[]` → `LineDraft[]`.
- **Scope = one `ScopeDraft` per electrical block** (one-lines delineate P1-110, P2-110, Reserve,
  MV system). `neta_standard` = ATS|MTS (scope decision). `replication_m4 = 1`,
  `adjustment_multiplier_n4 = 1` (neutral). **`labor_allocation` is REQUIRED on `ScopeDraft`**
  (canonical `draft.ts`; dereferenced by `compile.ts`) — the skill emits a documented **neutral
  default** (single primary labor type at `pct_of_app: 1.0`, or the rate-card default split) purely
  so the draft validates/compiles; the labor split itself is the estimator's to feather, not a
  skill decision.
- **Matched apparatus →** `line_kind: 'catalog'`, `equipment_model_ref` set, `base_qty` = explicit
  count, `expansion_policy: 'one_unit_per_qty'`, `included: true`. Out-of-scope class →
  `included: false` + `exclusion_reason`.
- **Uncataloged apparatus → fail closed; never an auto-emitted line.** `estimator-core` requires an
  *included* `custom_equipment` line to carry `provisional_token` **and** `provisional_ref_hours > 0`
  (resolved hours). The skill must not invent hours, so uncataloged-but-identified equipment goes to
  `unmatched_candidates` + a catalog-add request and is surfaced at Gate 1 — **not** an included
  draft line. It becomes an included `custom_equipment` line ONLY if a human supplies provisional
  hours at the gate (then: `line_kind:'custom_equipment'`, `included:true`, `base_qty > 0`,
  `provisional_token`, `provisional_ref_hours > 0`, `provisional_attrs`, `equipment_fingerprint`,
  `catalog_request_ref` — the validator requires BOTH `base_qty > 0` AND `provisional_ref_hours > 0`).
  Never a guessed `catalog` ref.
- **The skill emits NO `service` and NO `cost` (travel/outside_services) lines** — those are the
  estimator's financial domain.
- `line_uid` is the stable join key to the evidence sidecar.

### 6.5 Evidence sidecar (audit) — `takeoff.evidence.json`
`LineDraft`'s only human-text fields (`designation` / `notes` / `description`) are unstructured —
none holds structured takeoff evidence — so evidence lives in a sidecar joined by `line_uid`:
```jsonc
{ "line_uid": "P1-110:r3",
  "source_refs": [ { "sheet": "E01-11", "page": 11, "revision": "ADD 4",
                     "callout": "MSB-P1-110-GB", "grid_area": null,
                     "schedule_row": null, "bbox": [757,1185,818,1194],
                     "evidence": "one-line" } ],
  "confidence": "high",            // high | medium | low
  "assumptions": [] }
```

### 6.6 Three-bucket output (audit)
```jsonc
{ "matched_lines":        [ /* LineDraft + sidecar, catalog refs resolved */ ],
  "unmatched_candidates": [ /* signature + best-guess class, NO catalog ref, why-unmatched */ ],
  "operator_questions":   [ /* ambiguities needing a human ruling before drafting */ ] }
```

### 6.7 Scope profile (light, layered — scope decisions only)
```jsonc
{ "project": { "test_standard": "ATS", "_prov": {"test_standard":{"source":"default"}} },
  "classes": {
    "lv_power_breaker":   { "in_scope": true, "catalog_model_ref": "<live id>" },
    "mv_drawout_breaker": { "in_scope": true, "catalog_model_ref": "<live id>" } } }
```
Resolution **human > spec > default** per key; provenance `{value, source, spec_clause?, rationale?}`
on every non-default value powers Gate 2 citations. No `labor_multiplier`/rate/travel knobs —
feathering is the estimator's. **Sampling is deferred for breaker V1:** `base_qty` always equals the
full physical count — the skill never mutates quantity to express a scope decision. If sampling is
needed later, it is modeled as an explicit inclusion/exclusion with evidence, not a silent qty
reduction.

### 6.8 Pattern flags (advisory; never change numbers)
Curated `patterns.json` of `signal → note`, attached to lines, shown at Gate 1, carried into
`notes`/sidecar for the feathering human: MV class → higher band; ground-fault function (`G`) →
added GF testing; drawout mounting → primary injection + cell/contact work; large identical lot →
efficiency (feather hrs/unit down). **Deferred:** learn magnitudes from historical estimates; the
flag schema is shaped for it.

## 7. The two gates

**Gate 1 — Inventory verify.** Table: class · voltage class · frame/trip · qty · source(sheet+bbox)
· mapped ref/`custom`/`unmatched` · confidence · flags. Plus **⚠ uncertain / likely-missing**:
low-confidence reads, `unmatched_candidates`, `operator_questions`, and a completeness cross-check
against the sheet index. Render the source crop via `drawing-nav find --render` for disputes. Human
corrects → frozen `inventory.json` + sidecar.

**Gate 2 — Scope review.** Resolved profile as a diff: each value + source; spec-derived values cite
**clause + snippet**; flags unmappable requirements and default-vs-spec conflicts. Human tunes →
frozen `profile.resolved.json`. Scope decisions only.

## 8. Code homes & language seam

*Python owns "drawings → takeoff"; TS (`estimator-core`) owns "draft → priced."*

**Authorities (to confirm as the first plan step — not yet grounded in any single repo):**
- **Contract authority:** the LIVE `estimator-core` in **`apex-power-ops-platform/packages/estimator-core`**
  (Olares dev-residency). `C:\dev\estimator-ui-staging` is the **divergent POC** and must not be the
  source of truth.
- **Extraction authority:** `drawing-nav` at `C:\Users\jjswe\Tools\drawing-nav\` (Python, BUILT,
  local Windows — operates on local drawing PDFs).
- **Not yet decided:** where the new `estimator-takeoff` Python modules and `SKILL.md` live —
  co-located in `apex-power-ops-platform` (versioned with `estimator-core`, reachable on Olares) vs.
  local `C:\Users\jjswe\Tools\` alongside `drawing-nav`. This is an explicit plan decision; the two
  repos + Windows/Olares split must be reconciled, not assumed.

**Intended shape (pending the home decision):**
- `drawing-nav` (Python, BUILT) — extraction.
- **`estimator-takeoff`** (Python, NEW) — normalize / quantify / catalog-match / pattern-flags /
  profile-resolve / emit. **References the LIVE canonical `estimator-core` catalog seed/resolver —
  never a bundled copy** — and shells to its validator. Every draft validated through `estimator-core`
  before handoff, so contract drift is caught immediately.
- **`estimator-takeoff/SKILL.md`** (NEW) — thin orchestration + NETA default profile + the two gates.
- canonical `estimator-core` (TS) — pricing/validation authority at the seam.

## 9. Testing

- **Golden corpus** like `estimator-core`'s: STACK PHX02A breakers → known inventory → known draft +
  sidecar → known priced output.
- Unit tests concentrate on **[3] Quantify** (de-dup across sheet types) and **[4] Catalog match**
  (incl. the unmatched/`custom_equipment` paths — assert it never invents a `catalog` ref).
- Voltage-class fixtures from the real one-lines (LV blocks + MV tie).

## 10. Core workflow (audit) & vertical-slice chips

Workflow: **inspect → count → map → organize into scopes → emit draft + evidence sidecar + questions
→ validate refs/qty before handoff.**

Chips:
0. **Ground authorities** — re-verify `LineDraft` + validator against CANONICAL
   `apex-power-ops-platform/packages/estimator-core` (not the POC), confirm the `drawing-nav`
   authority, and decide + create the `estimator-takeoff` code homes. Normalize spec-file perms.
1. **Contracts** — scope-profile schema + NETA breaker default profile + the emit-mapping to
   `EstimateDraft`/`ScopeDraft`/`LineDraft` + breaker rating-band→catalog-model table (resolved
   against the live seed) + `patterns.json` seed + evidence-sidecar schema.
2. **`estimator-takeoff` core** — normalize + voltage-class + quantify(de-dup) + catalog-match
   (3 buckets) for breakers, on the real ELEC one-lines; unit + golden tests.
3. **Gate 1** — inventory table + uncertain/missing + render-crop-on-dispute + flags + sidecar.
4. **Spec-parser + Gate 2** — breaker-relevant clause extraction → scope proposals + citations;
   profile resolve.
5. **Emit → estimator-core validate → handoff**; golden end-to-end on STACK breakers.

## 11. Open items / deferred

- Learning pattern hour-deltas from historical estimates (V2).
- Test-procedure grain (V2 sub-layer).
- Classes beyond breakers (one at a time).
- Exact handoff mechanism into the estimator (estimator-ui import vs ops Chip-5-style intake) —
  resolve when the estimator's native intake path settles. The skill stops at a validated `draft` +
  sidecar + questions; it never pushes to ops.
