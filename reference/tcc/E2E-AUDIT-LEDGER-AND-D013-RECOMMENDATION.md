# E2E Selection-Validation Audit — Ledger Summary + D-013 Recommendation

*Deliverable of the Access ↔ Supabase ↔ Breaker-UI audit (brief: `E2E-SELECTION-VALIDATION-AUDIT.md`). Completed structural sweep 2026-06-13. **READ-ONLY audit — no code/prod/migration changes were made.***

> **One-line answer to "should we do the DB normalization (D-013) now?": NO — the evidence is conclusive against it.** The operator's "many, many inconsistencies" decompose into **one real ~2-line frontend bug (F02)**, **legitimate-but-confusing product modeling (F01)**, and **a few bounded data-completeness items** — on top of a **provably bit-exact, faithful data substrate (F07)**. The one layer that genuinely needed a governed contract — terminology — **already has one** (F05), and it works. Fix F02, clear the small backlog in place, and re-open D-013 only when a *second* consumer actually arrives.

---

## 1. The ledger (7 findings, full detail in `.audit_workspace/e2e_audit/F0*.md`)

| # | Axis | Bucket | Disposition | Severity | D-013? |
|---|------|--------|-------------|----------|--------|
| **F01** | Manufacturer "duplication" | — | **Mostly legitimate** (breaker-mfr + retrofit/cross-brand + corporate lineage) | LOW | No |
| **F02** | ETU cascade cross-filter | (iii) frontend-trapped | **THE real bug** — `breaker_class` omitted → cross-class leak | **HIGH** | No (≈2-line fix) |
| **F03** | Frame ↔ sensor rating | (i) data-fidelity | Grain nuance + Terasaki AGR-11 63,000 A pocket | LOW–MED | Partial |
| **F04** | Trip-style class fidelity | (i) data tail | §107–117 lane **stuck**; 25 internal-heterogeneity + ~3 under-model + 3 orphans | LOW | No |
| **F05** | Settings / terminology | — | **No defect — the D-013 exemplar already shipped** (`tcc.field_terminology`) | NONE | N/A (is one) |
| **F06** | TMT + EMT family scoping | (i) data-completeness | **F02-immune by construction**; EMT pristine; 1,923 curveless-but-selectable TMT frames | LOW–MED | No |
| **F07** | Cross-layer content (Access↔Supabase) | — | **Provably bit-exact spine; ZERO accidental divergence** | NONE | No |

### Bucket tally (the gate input)
- **bucket (ii) serving-divergence — the D-013 target:** essentially **none found.** The cascade view is clean (2095/2095 single-match); the class label is a defensible `BOOL_OR` union; terminology serving is exemplary.
- **bucket (iii) frontend-trapped:** **exactly one — F02**, a localized ~2-line propagation miss (the #23/DURABLE-20 class-qualifier was added to the bridge call but not to the two cascade effects). Not a contract-shaped problem.
- **bucket (i) data-fidelity/completeness:** a **bounded backlog** — F03 (AGR-11 rating), F06 (1,923 curveless TMT frames), F04 tail (3 orphan styles, ~3 under-model). All fixable in place.

## 2. Why the substrate is *proven* clean (F07 — the decisive input)
Cross-boundary set-algebra + value hashing established, conclusively (not probabilistically):
- **ID spine bit-exact** — matching **count AND id-sum** on the partition below the Access max id (sensors 17831/Σ298,999,775; styles 2094/Σ2,723,207; mfrs 450/Σ102,181). A drop+swap cannot preserve both ⇒ Supabase ⊇ Access exactly; the +1 style / +46 sensors are clean tail-appends matching the migration record.
- **Manufacturer names byte-faithful** (450/450).
- **`style` text 2083/2094 identical** — all 11 diffs are class-faithful renames (migrations 022/025); **`type` 2092/2094** — the 2 diffs are migration 025 (Ekip 1501/1503) exactly.
- **Zero accidental divergence anywhere.** The "inconsistencies" are *not* a data-substrate problem.

## 3. D-013 recommendation — **DEFER (keep logged); act targeted**

The D-013 premise was "*the first consumer is itself suffering the absent contract → pull the build forward.*" **The audit disproves that premise.** lvbreakertcc is not suffering from an absent contract; it is suffering from **one propagation bug** plus some **legitimate modeling confusion**, over a **clean substrate**. Building a full canonical-contract now would solve a problem the evidence shows does not exist at the scale that would justify the cost — and would risk regressing the validated §104–§216 serving lane.

**Recommended sequence (all in-place, no contract rebuild):**
1. **Fix F02 now** (the operator's actual bug). TDD the ~2-line change in `apps/operations-web/app/lvbreakertcc/page.tsx` — both cascade effects → `breakerClass: bClass || bIdClass || null`, add `bIdClass` to both dep arrays → deploy → live-verify breaker 18 no longer leaks `MICROLOGIC 6.0`. *(Optional backend defense-in-depth: require/auto-resolve class under `bridge_xfilter`.)*
2. **Clear the bounded data backlog in place:** F06 (suppress or backfill the 1,923 curveless TMT frames — a ~1-line curve-aware `HAVING` guard), F03 (correct the AGR-11 rating vs catalog), F04 (3 orphan style rows incl. the mis-filed Siprotec relay; verify ABB "Ekip E LSIG").
3. **Keep D-013 logged, re-open at consumer #2.** When the datasheet generator / second app actually materializes, the **terminology contract (F05) is the proven template** to extend — that is the right, evidence-driven trigger, and the substrate will be ready.

## 4. Scope note
Structural sweep = 100% of rows across all 4 axes (SQL/OLEDB set-algebra + value hashing). The **UI deep-drive prong** (brief §6, task #133 — stratified ~15–20 Playwright paths) was **not** re-run this pass; the operator's symptom (F02) was already live-proven in the prior session (`/cascade?breaker_id=18&bridge_xfilter=true` → leaked 6.0), so the deep-drive would be confirmatory. It remains available as an optional final validation.
