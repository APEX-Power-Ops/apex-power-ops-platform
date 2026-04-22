# Flashcard Specification
## Canonical Build-Spec Surface For Flashcard Structure And Export Rules

Created: April 4, 2026
Status: Active canonical specification
Purpose: Define the canonical flashcard data contract, deck organization rules, and derived export boundaries for flashcard content in the NETA ETT workspace

---

## Scope

This specification defines how flashcards should be structured, tagged, organized, and exported.

It covers:

1. canonical deck and card data fields
2. level, category, and KSA tagging expectations
3. naming and organization of flashcard decks and published consumer surfaces
4. export boundaries for Anki-compatible and HTML-based delivery
5. quality and validation rules for flashcard authoring

It does not cover:

1. study-guide depth requirements
2. practice-test question behavior
3. general staging workflow outside the flashcard-specific parts of authoring
4. front-end styling decisions beyond what the flashcard contract must preserve

---

## Authority Relationship

This file is the canonical build-spec surface for flashcard structure and export behavior.

It should be read together with:

1. `Resources/Templates/FLASHCARD-TEMPLATE.md` for the existing template baseline and examples
2. `Resources/Catalog/TAGGING-SCHEMA.md` for KSA and metadata tagging expectations
3. `MASTER-STANDARDS.md` for naming and directory placement conventions
4. `Build-Specs/INFRASTRUCTURE-ROADMAP.md` for the historical planning context that originally called for this artifact

Interpretation:

1. this spec defines the stable canonical contract
2. the template remains a supporting implementation aid rather than a competing authority surface
3. if the template or consumer apps drift from this contract, reconcile them explicitly instead of allowing silent schema divergence

---

## Canonical Source-Of-Truth Rule

The canonical authoring surface for flashcards is structured deck data, not hand-maintained HTML.

That means:

1. card content should originate in structured JSON or another machine-readable deck format approved by this contract
2. Anki packaging, CSV export, and interactive HTML apps are derived consumer outputs
3. consumer-specific presentation fields may extend the core card object, but they must not replace required core card fields

This rule prevents card-count drift, naming drift, and schema drift across HTML apps and export targets.

---

## Required Deck Metadata

Each flashcard deck must carry metadata that identifies what it is and how it should be consumed.

Minimum required deck metadata:

1. `deck_name`
2. `deck_id`
3. `level`
4. `card_count`
5. `created`
6. `updated`

Recommended supporting metadata:

1. `description`
2. `source_summary`
3. `topic_scope`
4. `export_targets`

Rules:

1. `card_count` must match the real number of cards in the deck
2. `level` must map to the intended NETA certification level or explicitly declare a cross-level deck when justified
3. `deck_id` should stay stable once adopted so downstream exports and audits remain traceable

---

## Required Card Fields

Each flashcard must preserve a stable core object.

Minimum required card fields:

1. `id`
2. `type`
3. `level`
4. `front`
5. `back`
6. `source`

Required classification fields:

1. `category`
2. `ksa` or `ksas`
3. `tags`

Recommended enrichment fields when useful:

1. `topic`
2. `subtopic`
3. `difficulty`
4. `formula`
5. `explanation`
6. `tips`
7. `reference`

Core rule:

1. the minimum core object must remain sufficient to export a working Anki-compatible deck even if enrichment fields are absent
2. enrichment fields are additive and should improve filtering, comprehension, or HTML display without becoming mandatory for every card type

---

## Supported Card Types

The canonical supported card types are:

1. `basic`
2. `qa`
3. `cloze`
4. `image`

Rules by type:

1. `basic` should express one concept, term, or definition per card
2. `qa` should ask one bounded question with one primary answer target
3. `cloze` should use meaningful omissions rather than trivia-level blanks
4. `image` should reference a governed image path or equivalent managed asset, not an ad hoc external dependency

If a future consumer needs another type, add it to the canonical spec first instead of silently creating a one-off schema.

---

## Tagging And KSA Rules

Flashcards must align with the current tagging schema and KSA discovery model.

Required tagging behavior:

1. keep KSA identifiers aligned with the active tagging schema rather than local shorthand
2. preserve topic tags that support filtering by subject area and subdomain
3. use stable tags for equipment, test type, or standards when those distinctions matter to study value

Implementation rule:

1. flashcard records may use either `ksa` or `ksas` depending on the consumer contract, but the canonical deck source must be internally consistent within a deck
2. if a consumer requires single-value KSA handling, derive it from the canonical deck rather than weakening the canonical structure globally

---

## Naming And Organization Rules

Published flashcard HTML outputs should follow the naming rule already recorded in `MASTER-STANDARDS.md`:

1. `NETA-Level-#-Flashcards.html`

Structured deck data should use stable, machine-friendly names by level and topic.

Recommended deck organization:

1. group by level first when the deck is level-specific
2. group by topic when the deck is broad enough to need deck-level separation
3. keep a deck index or inventory when multiple decks exist for the same level

Directory rule:

1. structured deck sources should remain in governed resource or extraction namespaces
2. HTML study apps belong in flashcard consumer locations, not as the only durable source material

---

## Export And Consumer Boundaries

This spec supports multiple consumer surfaces.

Approved derived outputs:

1. Anki-compatible deck data
2. CSV exports when a consumer requires flat import format
3. interactive HTML flashcard apps

Rules:

1. exports must be reproducible from canonical structured deck data
2. derived outputs must not silently change counts, omit required cards, or rename decks in ways that break traceability
3. if an HTML app introduces additional fields such as `explanation`, `tips`, or `difficulty`, those fields should still map cleanly back to the canonical card identity

---

## Quality Rules

Every flashcard deck should satisfy these quality expectations:

1. cards are atomic and test one concept at a time
2. answers are technically correct and not materially ambiguous
3. sources are cited
4. level difficulty matches the intended audience
5. tags and KSA mappings are valid
6. counts and labels used in published apps match the real card inventory

Anti-patterns to reject:

1. cards with multiple unrelated facts on one side
2. consumer files claiming deck counts that do not match real inventory
3. HTML-only card edits that never reconcile back to the canonical source deck
4. missing or inconsistent KSA and topic tagging when the source supports them

---

## Relationship To Legacy Flashcard Apps

Legacy and development flashcard apps remain useful reference surfaces.

They demonstrate:

1. topic and subtopic filtering
2. progress and review flows
3. value from additive fields such as formula, explanation, and tips

However:

1. those consumer apps are not the canonical structure contract
2. historical filename drift such as `NETA-Level-#-Interactive-Flashcards.html` should not silently replace the published naming standard without an authority update
3. count mismatches and incomplete content in legacy apps are evidence for why a canonical structured source is required

---

## Validation Checklist

Use this checklist before treating a flashcard deck as complete:

1. required deck metadata is present and truthful
2. every card has the required core fields
3. KSA and topic tagging align with the tagging schema
4. source citations are present
5. consumer exports can be derived without card-count drift
6. published labels and filenames match governed naming rules

---

## Bottom Line

Flashcards should be authored as governed structured deck data with stable metadata, KSA-aligned tagging, and reproducible exports.

Interactive HTML apps and Anki packaging are important delivery surfaces, but they should be derived from the canonical deck contract rather than act as the source of truth.