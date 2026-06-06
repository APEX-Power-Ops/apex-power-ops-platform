---
dispatch_id: 2026-06-06-codex-ep-etap-nomenclature-crosswalk-v2-starlib
target: CODEX
priority: 1
from: CC
created_at: 2026-06-06
authority: gated
predecessor: 2026-06-06-codex-ep-etap-nomenclature-crosswalk
closeout: ops/agents/handoffs/2026-06-06-ep-etap-nomenclature-crosswalk-v2-starlib-closeout.md
---

# EP→ETAP nomenclature crosswalk v2 — re-source from the ETAP Star Library List (published help docs)

**Lane:** lvbreakertcc · nomenclature normalization.
**Type:** READ-ONLY build. Prod read + host-local file read. **No DB writes. No DDL. No code wiring.** Deliverable = v2 host-local crosswalk TSVs + method doc + a closeout reporting per-level coverage **and the delta vs v1**. Persistence + serving wire-up remain separate follow-on packets.
**Must run on the WORKSTATION** — the ETAP help docs are host-local (D: drive), not in the repo.

## Why v2
v1 (`2026-06-06-codex-ep-etap-nomenclature-crosswalk`) sourced the ETAP side from the **decoded DemoLib/LibChanges TSVs**, which are a NARROW extract — it produced 86% breaker `none` and stranded most of the EP long tail. We now have the **authoritative source**: ETAP's **published "Star Library List"** help documentation (the default-library device list), which is broad, per-family, and cleanly citable as PUBLIC docs. Re-source the crosswalk from it. This supersedes v1 (keep v1 on disk for the delta).

CC has already eyeballed `LVSST.htm` + `Index.htm` and confirmed the structure + that the long tail is largely covered. Use CC's findings below as the validated baseline.

## Sources

### EP side — prod Supabase, READ-ONLY (unchanged from v1)
`tcc.manufacturers`, `tcc.trip_styles`, `tcc.brk_{mccb,iccb,pcb}_styles`; reference `tcc.trip_style_aliases` (803, for the agreement check).

### ETAP side — the Star Library List, host-local published help docs
Directory: `D:\ETAP\ETAP_EN\ETAPSETUP\cab2\fil92DB58203F124984724825A53F2ED499~\`
`Index.htm` = the "ETAP Star Library List" TOC (context). Per-family pages map 1:1 to our families:

| Our family | ETAP Star Library page(s) |
| --- | --- |
| **ETU** (LV solid-state trip) | `LVSST.htm` |
| **TMT** (thermal-magnetic trip) | `Thermal_Magnetic_Trip.htm` |
| **MCP** (motor circuit protector) | `Motor_Circuit_Protector.htm` |
| **EMT** (electro-mechanical trip) | `Electro_Magnetic_Trip.htm` *(confirm this is the EMT list via its page title; if not, find the Electro-Mechanical Trip list page)* |
| **Breaker — MCCB** | `ANSI_AC_Molded_Case_breakers.htm`, `IEC_AC_Molded_Case_breakers.htm` (+ DC: `ANSI_DC_Molded_Case_breakers.htm`, `IEC_DC_Molded_Case_breakers.htm`) |
| **Breaker — ICCB** | `ANSI_AC_Insulated_Case_breakers.htm`, `IEC_AC_Insulated_Case_breakers.htm` (+ `ANSI_DC_Insulated_Case_breakers.htm`) |
| **Breaker — PCB** | `ANSI_AC_Power_Breakers.htm`, `IEC_AC_Power_breakers.htm` (+ DC variants) |
| (Relay — OUT OF SCOPE this packet; `Relay.htm` exists for a later lane) | — |

**Confirmed parse structure (LVSST exemplar):** each page is an HTML `<table>`; rows are `<tr>` of `<td>` cells. LVSST columns = `Manufacturer | Model | <variant> | Zone Selective Interlock`. **Other pages differ** (breaker pages add frame/amp/poles/kAIC; TMT/MCP/EMT differ) — detect each page's header row and extract at minimum `Manufacturer` + `Model`, plus any frame/amp column for the breaker pages. `&#160;` = blank cell.

Prerequisite (check before claim): prod read reachable + the help-doc directory present on this host. If either is missing, leave in `pending/` and report.

## CC's validated baseline (use; don't blindly re-derive)
The **distinct ETAP manufacturer vocabulary extracted from the family pages is the AUTHORITY** for which mfr names exist — build the EP→ETAP mfr map by matching EP `mfr_name` against that extracted vocabulary, using the normalization map below for known shorthand/expansions. If a map target is NOT found in the extracted vocabulary, flag it (don't force it).

LVSST distinct manufacturers (confirmed by CC) include: `ABB, AEG, Allen-Bradley, Alsthom, Carriere, Cutler-Hammer, Eaton, Electromagnetic Industries LLP, Federal Pioneer, Fuji, GEC Alsthom, General Electric, Hyundai, ITE (BBC), Joslyn, LSIS, Merlin Gerin, Mitsubishi, Moeller, Multilin, satinAMERICAN, Schneider Electric, Siemens, SPD Technologies, Square-D, SURE-TRIP, SYLVANIA, Sytek, Terasaki, Utility Relay, Westinghouse, WESTRIP`. The breaker/TMT/MCP/EMT pages will add more (e.g. Siemens-Allis, Allis-Chalmers, L&T, Toshiba, OEZ, etc. — extract the real union).

**Corrected EP→ETAP manufacturer normalization map** (supersedes v1; v1's `Allen-Bradley→ABB` was WRONG):

| EP `mfr_name` | → ETAP | note |
| --- | --- | --- |
| GE | General Electric | expand |
| West | Westinghouse | expand |
| Schneider | Schneider Electric | expand |
| Square D / SQD / SquareD | Square-D | shorthand/punctuation |
| Cutler Hammer | Cutler-Hammer | punctuation |
| Siemens Allis | Siemens-Allis | punctuation (confirm in breaker/TMT pages) |
| Allis Chalmer | Allis-Chalmers | EP typo (confirm presence) |
| LS Industrial / LG Industrial | LSIS | rebrand |
| BBC / Brown Boveri | ITE (BBC) | ETAP's literal string |
| ITE | ITE (BBC) | ETAP labels ITE as "ITE (BBC)" |
| Satin American | satinAMERICAN | spelling |
| Sure-Trip | SURE-TRIP | case |
| Westrip | WESTRIP | case |
| Sylvania | SYLVANIA | case |
| Larsen & Toubro | L&T | contract (confirm presence) |
| Moeller | Moeller | LVSST uses "Moeller"; **report what each breaker page uses** ("K Moeller" appeared in the decoded lib) — record per-family if they differ |
| **Allen-Bradley** | **Allen-Bradley** | **IDENTITY (corrected from v1 rebrand→ABB)** |
| Fed Pacific / Federal Pacific | (none) | ETAP carries `Federal Pioneer`, not Federal Pacific — leave `none` unless a page actually lists Federal Pacific |

Everything else: exact-match (case/punctuation-normalized) against the extracted ETAP vocabulary → `identity`; no match → `none` (leave EP as-is, do not invent).

## Method (same tiers + no-fabrication as v1; now family-aware)
- **Level 1 — manufacturer** (`v2_starlib/mfr_crosswalk.tsv`): extract the union ETAP mfr vocabulary from all in-scope pages; map every EP mfr per above; columns `ep_mfr_id, ep_mfr_name, etap_mfr_name, tier, match_basis, ep_trip_style_count, ep_breaker_style_count, provenance`. Report ETAP-only mfrs and EP-absent-from-ETAP.
- **Level 2 — trip-unit** (`v2_starlib/trip_unit_crosswalk.tsv`): match each EP `trip_styles` row against ETAP rows **from the family page matching its kind** (ETU/solid-state→LVSST; thermal-mag→TMT page; MCP→MCP page; EM→EMT page — infer the EP trip_style's family from its `type`/`style`/`sensor_type` and document the rule). Match EP `(type, style)` against ETAP `(model, variant)`; tiers `exact/core/frame/none` (document the core-token normalization). Keep the existing-alias agreement check (`agrees_with_existing_alias` yes/no/na) and the conflict list. Columns as v1 + `etap_family_page`.
- **Level 3 — breaker** (`v2_starlib/breaker_crosswalk.tsv`): match each EP `brk_*_styles` row against the breaker page set for its class (MCCB→Molded Case pages, ICCB→Insulated Case, PCB→Power) and standard (ANSI/IEC). Match EP `frame` against ETAP `model` (+ amp where present). Tiers as v1. Columns as v1 + `etap_source_page`.
- One row per EP entity; multiple candidates → best + `n_candidates` + `alt_candidates`. **Never invent a name.**
- Write `v2_starlib/crosswalk_method.md` documenting the page list actually parsed, the per-page column detection, the family-inference rule, and the tokenization/tier rules.

## §146 source discipline
The Star Library List is **published ETAP help documentation** — public and citable; this is the cleanest provenance in the lane (no decrypted library involved). Output is **names / identifiers only** (manufacturer/model/variant strings) — no curve points, equations, bands, settings, or numeric values (the help pages are device lists; do not pull any TCC/rating curve numbers even if present). Provenance tag on every row: `[ETAP Star Library List — published help docs] names-only crosswalk`.

## Output (host-local, gitignored)
Write under `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/`: `mfr_crosswalk.tsv`, `trip_unit_crosswalk.tsv`, `breaker_crosswalk.tsv`, `crosswalk_method.md`. **Leave v1 outputs in place** for the delta.

## Closeout (committed) — AGGREGATE ONLY
At `ops/agents/handoffs/2026-06-06-ep-etap-nomenclature-crosswalk-v2-starlib-closeout.md`:
- Which pages were parsed + per-page row counts + detected columns.
- **Level 1:** tier counts; the full EP mfr map (names only); the union ETAP vocabulary; ETAP-only and EP-absent lists; the `Moeller`/`K Moeller` per-family finding.
- **Level 2:** trip coverage by tier (counts + %); alias agree/conflict counts + the conflict list; 5–10 samples.
- **Level 3:** breaker coverage by tier per class; 5–10 samples.
- **DELTA vs v1:** per level, how much `none` dropped / matched rose (this is the headline — quantify the lift).
- Anomalies (EMT page identity, any EP mfr still `none`, multi-candidate counts).
- One-line verdict per level.
- **NO bulk dump, NO curve/rating numbers, NO secrets.**

## Boundaries
- READ-ONLY prod. No writes/DDL/code. Host-local file READ only; outputs to gitignored `.audit_workspace/.../crosswalk/v2_starlib/`.
- §146 source discipline (above) — published-doc names only.
- PUBLIC repo + no secrets in closeout/chat.
- Inbox lifecycle: `git mv pending→claimed` + push before running; closeout to the `closeout:` path; then `git mv claimed→done` + push.

## Acceptance
v2 TSVs + method doc exist host-local; closeout carries per-level coverage, the **delta vs v1**, the corrected mfr map, the alias-conflict list, and anomalies. CC reviews, then authors the persistence + serving wire-up follow-on with `[ETAP Star Library List]` provenance.
