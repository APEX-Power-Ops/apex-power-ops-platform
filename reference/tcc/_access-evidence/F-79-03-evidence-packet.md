# F-79-03 -- TMT Load-Completeness Evidence Packet (resolution record)

Status: EVIDENCE ASSEMBLED + LOCALIZATION RUN. SUPERSEDES the old F-79-03 framing
("known missing rows" / direct frame anti-join). #79 follow-on (row-set fidelity track; distinct from
F-79-04 column-carry, which is closed). Author: CC. Date: 2026-06-28.
Companion spec: `F-79-03-tmt-antijoin-runbook.md` (its frame-resolved procedure is RETIRED -- see sec 0).
Lineage authority: `reference/tcc/G1-SCHEMA-GUIDE.md` sec 4.2.

> REFRAME (operator, 2026-06-28): "Confirmed count deltas, but the row-level cause is structurally
> unresolved because the frame load lost source identity." NOT "known missing rows."
> BOUNDARY (HARD): CC/Codex supply the mechanical diff + characterization ONLY; the OPERATOR records the
> per-table classification (Access `D:\TCC_NEW.accdb` is authoritative). This is an EVIDENCE/classification
> lane -- NO migration is written from it.

## 0. Headline -- the runbook's frame-resolved procedure is RETIRED (not honestly executable)

The runbook (2026-06-26) prescribed a frame anti-join on `Access.ID == tcc.tmt_frames.id` and frame-grain
child diffs. The Phase-1 build (`access-harness-task-11-report.md`, commit `c17f0edc`, RUN LIVE) and a
direct prod schema check (2026-06-28) establish this is impossible without FABRICATION:

- `tcc.tmt_frames` columns are exactly `(id, breaker_style_id, breaker_class, size, created_at)` -- NO
  `source_id`/Access-frame-ID provenance (UNLIKE the style tables, whose `brk_*_styles.source_id`
  anti-joins to Access `BreakerXXXStyles.ID` perfectly, sec 3).
- `tcc.tmt_frames.id` is a re-sequenced load-rank surrogate (live 1..42082, 13 gaps); the harness red-team
  guard RAISES on any `<surrogate> -> tmt_frames.id` keying.
- `size` is COMPUTED (`'630.0'`) != Access `FrameDesc` (`'1600'`); 32/42238 coincide (Task-11 live).
- Every child FKs the re-sequenced `tmt_frames.id` via `frame_id`; with no honest frame correspondence,
  no child maps back to an Access `FrameSizeID`.

The bounded style-bucket localization (sec 6) was the one honest row-adjacent avenue; its result CONFIRMS
the deficit is structurally unresolvable rather than localizing it.

## 1. The deltas -- CONFIRMED LIVE (governed evidence == current prod == G1)

Governed `access_validation.tcc_count_reconciliation` (`tcc_fidelity_governed`, local PG18),
cross-checked 2026-06-28 against current prod `tcc.tmt_*` via the authorized prod MCP
(`fxoyniqnrlkxfligbxmg`): all five tcc counts equal the governed `tcc_row_count` exactly -> deltas are
real and current (029/030/031 touched only D4/D5 columns + the contract view, not tmt rows). Mirrors are
byte-faithful (`checksum_reconciliation.matches=t` x7) -> deltas are not a mirror artifact.

| tcc table        | access table              | lineage (G1 4.2) | access  | tcc (live) | delta  |
|------------------|---------------------------|------------------|--------:|-----------:|-------:|
| tmt_frames       | Breaker_TMTFrameSizes     | "1:1 load" *     |  42238  |    42069   |  -169  |
| tmt_amps         | Breaker_TMTFrameAmps      | 1:1 DLL load     |  67206  |    66960   |  -246  |
| tmt_settings     | Breaker_TMTFrameSettings  | 1:1 DLL load     |  58041  |    57983   |   -58  |
| tmt_curves       | Breaker_TMTFrameCurves    | COMPUTED (N/A)   | 1143458 |  1139025   | -4433  |
| tmt_thermal_adj  | Breaker_TMTThermalTripAdj | DERIVED          |  21790  |    14620   | -7170  |

(*) G1 4.2 labels frames a "1:1 DLL load", but sec 6 shows the tcc frame population is a TRANSFORMATION
(MCCB-faithful + PCB-derived), not a 1:1 copy -- a G1 label-correction candidate (flagged, operator's call).

## 2. tcc id-shape (a HINT only -- tcc load-rank ids, NOT Access rows)

| tcc table       | tcc rows | id range   | gaps | shape                 |
|-----------------|---------:|------------|-----:|-----------------------|
| tmt_frames      |   42069  | 1..42082   |  13  | gappy                 |
| tmt_amps        |   66960  | 1..66966   |   6  | gappy                 |
| tmt_settings    |   57983  | 1..57983   |   0  | DENSE (tail-short 58) |
| tmt_curves      | 1139025  | 1..1139025 |   0  | DENSE                 |
| tmt_thermal_adj |   14620  | 1..14628   |   8  | gappy                 |

## 3. Style-provenance hop -- CLEAN (the style layer is intact)

Governed `style_provenance_antijoin`: `Access BreakerXXXStyles.ID <-> tcc brk_xxx_styles.source_id` is a
perfect 1:1 both directions for all three classes (MCCB 10335/10335, ICCB 608/608, PCB 3279/3279; 0
missing / 0 extra). Implicit-class AMBIGUITY (recorded, `style_resolution`): of 8338 distinct frame
StyleIDs, 8080 single-class (MCCB 8074 / ICCB 6 / PCB 0), 230 ambiguous (>=2 class ID-spaces), 28 no-class.

## 4. Row-level evidence available per table (the honest ceiling)

- **tmt_amps**: the ONLY row-level anti-join the slice runs -- a FRAME-FREE rating-value multiset
  (`antijoin_vs_tcc`): missing_in_tcc 6374 / extra_in_tcc 6128, net -246 == the count delta. Coarse value
  key (no frame); large gross churn around a net of 246 = many frames share rating values.
- **tmt_frames**: see the style-bucket localization, sec 6 (no clean per-frame key).
- **tmt_settings**: NO honest row-level anti-join (natural key needs the frame correspondence).
- **tmt_curves / tmt_thermal_adj**: COUNT-ONLY by lineage (sec 5).

## 5. Lineage dispositions (G1 sec 4.2 + sec 5) -- H4 RATIFIED by operator 2026-06-28

- **tmt_curves -> H4 (ratified).** G1 4.2: "(TMT curves -- computed, not in Access)", reader N/A. tcc.tmt_curves
  is REGENERATED, not a 1:1 load of `Breaker_TMTFrameCurves`; the Access curve-table count is the WRONG
  comparand. The -4433 is H4 by construction (treating it as source-row backlog would be misleading).
- **tmt_thermal_adj -> H4 (ratified).** G1 4.2: "(thermal adj -- derived)"; G1 sec 5 already labels the
  `14,620 vs 21,790` a "derived delta, not re-characterized this pass". H4 (computed/derived comparand).

## 6. Bounded style-bucket localization for FRAMES -- RUN 2026-06-28 (cross-engine verified)

Method: key on the CLEAN style hop, `tcc.tmt_frames.breaker_style_id -> brk_<class>_styles.id ->
source_id == Access StyleID` (count delta is class-free; class only annotated). Run all-local against
`tcc_snapshot` (frame counts verified == prod: mccb 30809 / pcb 11260 = 42069). Independently
reproduced + adversarially verified (all numbers exact; interpretation SUPPORTED; wrong-join /
fan-out / benign-behavior alternatives ruled out).

GATE: per-style totals reconcile to access 42238 / tcc 42069 / net +169; membership partition reproduces
`style_resolution` exactly (8080 single / 230 ambiguous / 28 none).

RESULT -- the style hop does NOT localize the -169; it reveals a frame-load TRANSFORMATION:

- Where a StyleID is present on BOTH sides (6001 styles): counts are FAITHFUL -- 5835/6001 exactly equal,
  Pearson corr 0.97, total abs delta 1024.
- tcc MCCB frames (30809): 30809/30809 on Access-matched styles, 0 derived -- Access-faithful.
- tcc PCB frames (11260): only 848 on Access-matched styles; **10412 DERIVED** onto styles NO Access frame
  references (the DLL `FindMatchingBreakerStyles` matcher; Access is ~MCCB-keyed -- 42070/42238 frames
  resolve to an MCCB style, only 1632 to PCB).
- Access-only frames (StyleID with no tcc frame): 10191, of which **9629 on MCCB-only styles**.

DECOMPOSITION of the net -169 (tcc - access): `-10191` (access-only) `+10412` (tcc-only derived PCB)
`-390` (drift on shared styles) = `-169`. The -169 is the RESIDUAL of two offsetting ~10k populations,
NOT a 169-row truncation; a per-style (StyleID==source_id) diff cannot localize it (it is smeared across
>20k frames + the -390 shared drift). CONCLUSION: frames join amps/settings -- the row-level cause is
unresolvable from governed data; H1/H2 needs Access authority (understanding the frame->style matching rule).

## 7. Verdict table

| tcc_table       | lineage  | delta | row-level evidence                                   | operator_verdict (2026-06-28)                         |
|-----------------|----------|------:|------------------------------------------------------|-------------------------------------------------------|
| tmt_curves      | COMPUTED | -4433 | count-only (wrong comparand)                         | **H4** (ratified)                                     |
| tmt_thermal_adj | DERIVED  | -7170 | count-only (derived)                                 | **H4** (ratified)                                     |
| tmt_frames      | transform| -169  | style hop: transformation, NOT localizable (sec 6)   | confirmed delta; UNRESOLVED without Access authority  |
| tmt_amps        | 1:1 load | -246  | frame-free value churn 6374/6128 (net -246)          | confirmed delta; UNRESOLVED H1/H2 without Access auth. |
| tmt_settings    | 1:1 load |  -58  | none (frame corr. blocked); tcc DENSE 1..57983       | confirmed delta; UNRESOLVED H1/H2 without Access auth. |

## 8. Open items (operator)

1. **G1 label correction (flagged, not actioned).** G1 sec 4.2 calls frames a "1:1 DLL load"; sec 6 shows
   the tcc frame population is a transformation (MCCB-faithful carry + ~10412 derived PCB frames). Worth a
   G1 note; not edited here (canonical doc -- operator's call).
2. **Access-side characterization (optional, operator-only).** For frames/amps/settings, the only remaining
   discriminator is in `D:\TCC_NEW.accdb`: whether the un-carried Access frames (e.g. the 9629 MCCB-only-style
   frames absent from tcc) are tail-contiguous (H1) or share an exclusion property (H2), and what rule the
   DLL frame->style matcher applies. No tcc-side work can resolve this.
3. **No migration.** F-79-03 stays an evidence lane. The deltas are explained as far as governed data allows;
   curves/thermal are H4; frames/amps/settings are confirmed deltas with row-level cause unresolved.
