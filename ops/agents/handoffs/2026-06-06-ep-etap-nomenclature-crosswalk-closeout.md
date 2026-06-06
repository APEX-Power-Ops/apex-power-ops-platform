# EP to ETAP nomenclature crosswalk closeout

Dispatch: `2026-06-06-codex-ep-etap-nomenclature-crosswalk`

Mode: prod Supabase read-only + host-local ETAP taxonomy read. No DB writes, no DDL, no code wiring, no bulk ETAP data committed. Generated host-local outputs under `.audit_workspace/etap_tcc_sources/crosswalk/` and committed this aggregate closeout only.

Generated artifacts, gitignored:

- `.audit_workspace/etap_tcc_sources/crosswalk/mfr_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/trip_unit_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/breaker_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/crosswalk_method.md`

Provenance on every crosswalk row: `[ETAP-TAXONOMY 2024-118] names-only crosswalk`.

## Level 1 - manufacturer crosswalk

Tier counts:

| tier | count |
| --- | --- |
| contract | 1 |
| expand | 3 |
| identity | 12 |
| none | 118 |
| prefix | 1 |
| punctuation | 1 |
| rebrand | 1 |

Full EP manufacturer map used by trip styles or breaker styles:

| ep_mfr_id | ep_mfr_name | etap_mfr_name | tier | trip_styles | breaker_styles |
| --- | --- | --- | --- | --- | --- |
| 1 | ABB | ABB | identity | 130 | 1562 |
| 2 | Allis Chalmer | (none) | none | 0 | 26 |
| 4 | Brown Boveri | (none) | none | 0 | 14 |
| 8 | Fed Pacific | (none) | none | 0 | 134 |
| 9 | GE | General Electric | expand | 175 | 1228 |
| 11 | ITE | ITE | identity | 18 | 224 |
| 15 | Siemens | Siemens | identity | 431 | 1648 |
| 16 | Siemens Allis | (none) | none | 0 | 63 |
| 17 | SQD | (none) | none | 0 | 1162 |
| 18 | West | Westinghouse | expand | 113 | 478 |
| 21 | Joslyn | (none) | none | 1 | 0 |
| 28 | Cutler-Hammer | Cutler-Hammer | identity | 259 | 309 |
| 29 | English Elect | (none) | none | 0 | 1 |
| 33 | Siemens-Allis | Siemens-Allis | identity | 1 | 0 |
| 35 | Square D | Square-D | punctuation | 191 | 14 |
| 36 | Westinghouse | Westinghouse | identity | 0 | 20 |
| 40 | Merlin Gerin | Merlin Gerin | identity | 102 | 684 |
| 41 | Cutler Hammer | (none) | none | 0 | 762 |
| 42 | Heinemann | (none) | none | 0 | 24 |
| 43 | SACE | (none) | none | 6 | 73 |
| 44 | Trumbel | (none) | none | 0 | 2 |
| 45 | Federal Pioneer | Federal Pioneer | identity | 34 | 104 |
| 46 | Fuji | (none) | none | 20 | 340 |
| 47 | GTE | (none) | none | 0 | 6 |
| 48 | Roller Smith | (none) | none | 0 | 8 |
| 49 | Multilin | (none) | none | 2 | 0 |
| 50 | Utility Relay | (none) | none | 12 | 0 |
| 51 | Carriere | (none) | none | 4 | 0 |
| 52 | Satin American | (none) | none | 6 | 0 |
| 61 | Toshiba | (none) | none | 0 | 5 |
| 62 | (Generic) | (none) | none | 1 | 34 |
| 67 | Thomas&Betts | (none) | none | 0 | 4 |
| 68 | Westrip | (none) | none | 6 | 0 |
| 79 | Moeller | K Moeller | prefix | 36 | 258 |
| 82 | Sytek | (none) | none | 1 | 0 |
| 84 | Schneider | Schneider Electric | expand | 17 | 348 |
| 85 | Allis-Chalmers | Allis-Chalmers | identity | 18 | 0 |
| 96 | Hyundai | (none) | none | 1 | 130 |
| 97 | American | (none) | none | 0 | 10 |
| 99 | HUNDT & WEBER | (none) | none | 0 | 26 |
| 100 | CBI | (none) | none | 3 | 40 |
| 101 | Allen-Bradley | ABB | rebrand | 69 | 604 |
| 102 | Fuji America | (none) | none | 0 | 30 |
| 104 | Sure-Trip | (none) | none | 4 | 0 |
| 107 | Dorman Smith | (none) | none | 5 | 39 |
| 110 | IndustrialPower | (none) | none | 1 | 0 |
| 118 | Federal Pacific | (none) | none | 11 | 6 |
| 121 | Challenger | (none) | none | 9 | 41 |
| 122 | Mitsubishi | Mitsubishi | identity | 21 | 292 |
| 123 | Murray | (none) | none | 0 | 7 |
| 124 | Telemecanique | (none) | none | 0 | 39 |
| 125 | BBC | (none) | none | 4 | 0 |
| 129 | Benshaw | (none) | none | 1 | 50 |
| 131 | Eaton | Eaton | identity | 185 | 892 |
| 135 | Unelec | (none) | none | 9 | 53 |
| 138 | Automation Drct | (none) | none | 0 | 5 |
| 144 | Hitachi | (none) | none | 2 | 22 |
| 149 | Sylvania | (none) | none | 7 | 0 |
| 150 | Whipp & Bourne | (none) | none | 4 | 0 |
| 151 | Terasaki | (none) | none | 40 | 268 |
| 159 | Generac | (none) | none | 0 | 3 |
| 162 | Caterpillar | (none) | none | 0 | 1 |
| 164 | Bryant | (none) | none | 0 | 5 |
| 166 | ERMCO | (none) | none | 0 | 6 |
| 169 | Sprecher+Schuh | (none) | none | 0 | 34 |
| 173 | Gould | (none) | none | 0 | 4 |
| 189 | Altech Corp | (none) | none | 0 | 27 |
| 192 | LS Industrial | (none) | none | 7 | 408 |
| 193 | Kohler | (none) | none | 0 | 14 |
| 196 | Sensata | (none) | none | 0 | 11 |
| 198 | EEC | (none) | none | 0 | 16 |
| 203 | AEG | AEG | identity | 0 | 40 |
| 213 | WEG | (none) | none | 3 | 80 |
| 216 | Legrand | (none) | none | 5 | 84 |
| 222 | OEZ | (none) | none | 22 | 158 |
| 225 | Trumbull | (none) | none | 0 | 5 |
| 227 | E-T-A | (none) | none | 0 | 1 |
| 231 | Carling Tech | (none) | none | 0 | 31 |
| 235 | SquareD | (none) | none | 0 | 57 |
| 238 | bticino | (none) | none | 27 | 129 |
| 240 | Milbank | (none) | none | 0 | 4 |
| 242 | AMR | (none) | none | 0 | 1 |
| 244 | Sace-Sud | (none) | none | 0 | 6 |
| 252 | Havells | (none) | none | 0 | 9 |
| 253 | Larsen & Toubro | L&T | contract | 11 | 180 |
| 264 | Chint | (none) | none | 1 | 68 |
| 267 | Sace Bergamo | (none) | none | 0 | 1 |
| 271 | Soprano | (none) | none | 0 | 1 |
| 285 | c3controls | (none) | none | 0 | 14 |
| 291 | Taian | (none) | none | 0 | 1 |
| 292 | Hager | (none) | none | 5 | 55 |
| 296 | Proteus | (none) | none | 0 | 36 |
| 297 | Weidmuller | (none) | none | 0 | 5 |
| 302 | Gewiss | (none) | none | 0 | 29 |
| 304 | LG Industrial | (none) | none | 1 | 20 |
| 315 | Bill | (none) | none | 0 | 1 |
| 316 | ETA | (none) | none | 0 | 13 |
| 317 | MEM | (none) | none | 3 | 16 |
| 323 | Stahl | (none) | none | 0 | 14 |
| 326 | Doepke | (none) | none | 0 | 17 |
| 335 | People Electric | (none) | none | 2 | 5 |
| 336 | Changshu | (none) | none | 10 | 150 |
| 337 | SREAW | (none) | none | 0 | 12 |
| 345 | Ottermill | (none) | none | 0 | 6 |
| 348 | Sensitr | (none) | none | 16 | 0 |
| 353 | Franklin CS | (none) | none | 0 | 74 |
| 361 | Schrack | (none) | none | 2 | 44 |
| 363 | Jiangshu | (none) | none | 1 | 0 |
| 364 | Crabtree | (none) | none | 0 | 1 |
| 365 | ASI | (none) | none | 0 | 7 |
| 371 | KTE | (none) | none | 0 | 2 |
| 373 | T&B | (none) | none | 0 | 2 |
| 378 | Commander | (none) | none | 0 | 10 |
| 381 | Delixi | (none) | none | 0 | 12 |
| 391 | Crouse-Hinds | (none) | none | 0 | 1 |
| 394 | NHP | (none) | none | 2 | 23 |
| 395 | GTE/Sylvania | (none) | none | 0 | 5 |
| 396 | ABB-Wylex | (none) | none | 0 | 4 |
| 397 | ETC | (none) | none | 0 | 1 |
| 403 | Noark | (none) | none | 1 | 22 |
| 405 | Techna | (none) | none | 0 | 7 |
| 406 | FMX | (none) | none | 0 | 7 |
| 411 | Taesung | (none) | none | 0 | 3 |
| 413 | Lovato | (none) | none | 0 | 15 |
| 426 | Nader | (none) | none | 1 | 22 |
| 427 | Zhejiang BSB | (none) | none | 0 | 1 |
| 430 | Renmin | (none) | none | 0 | 6 |
| 431 | SPD Electrical | (none) | none | 0 | 1 |
| 433 | Atom Power | (none) | none | 1 | 1 |
| 436 | Steck | (none) | none | 0 | 37 |
| 440 | Shanghai Electr | (none) | none | 6 | 6 |
| 442 | P&A Power Sys | (none) | none | 0 | 16 |
| 445 | GEIS | (none) | none | 1 | 1 |
| 446 | PS Electrical | (none) | none | 6 | 0 |
| 448 | Shihlin | (none) | none | 0 | 19 |
| 450 | Tianjin Benefo | (none) | none | 1 | 4 |
| 454 | Xiamen Hongfa | (none) | none | 0 | 1 |

ETAP-only manufacturers after Level 1 mapping: Square D.

EP manufacturers absent from ETAP under the dispatched map: (Generic), ABB-Wylex, AMR, ASI, Allis Chalmer, Altech Corp, American, Atom Power, Automation Drct, BBC, Benshaw, Bill, Brown Boveri, Bryant, CBI, Carling Tech, Carriere, Caterpillar, Challenger, Changshu, Chint, Commander, Crabtree, Crouse-Hinds, Cutler Hammer, Delixi, Doepke, Dorman Smith, E-T-A, EEC, ERMCO, ETA, ETC, English Elect, FMX, Fed Pacific, Federal Pacific, Franklin CS, Fuji, Fuji America, GEIS, GTE, GTE/Sylvania, Generac, Gewiss, Gould, HUNDT & WEBER, Hager, Havells, Heinemann, Hitachi, Hyundai, IndustrialPower, Jiangshu, Joslyn, KTE, Kohler, LG Industrial, LS Industrial, Legrand, Lovato, MEM, Milbank, Multilin, Murray, NHP, Nader, Noark, OEZ, Ottermill, P&A Power Sys, PS Electrical, People Electric, Proteus, Renmin, Roller Smith, SACE, SPD Electrical, SQD, SREAW, Sace Bergamo, Sace-Sud, Satin American, Schrack, Sensata, Sensitr, Shanghai Electr, Shihlin, Siemens Allis, Soprano, Sprecher+Schuh, SquareD, Stahl, Steck, Sure-Trip, Sylvania, Sytek, T&B, Taesung, Taian, Techna, Telemecanique, Terasaki, Thomas&Betts, Tianjin Benefo, Toshiba, Trumbel, Trumbull, Unelec, Utility Relay, WEG, Weidmuller, Westrip, Whipp & Bourne, Xiamen Hongfa, Zhejiang BSB, bticino, c3controls.

## Level 2 - trip-unit crosswalk

Coverage by tier:

| tier | rows | pct |
| --- | --- | --- |
| exact | 77 | 3.7% |
| core | 146 | 7.0% |
| frame | 893 | 42.6% |
| none | 979 | 46.7% |

Existing alias agreement check:

| agreement | rows |
| --- | --- |
| yes | 113 |
| no | 10 |
| na | 1972 |

Illustrative sample rows:

| trip_style_id | ep_mfr | ep_type | ep_style | etap_mfr | etap_model | tier | alias_agree |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | GE | MVT-Plus | LVPCB | General Electric | MVT-Plus (AKR LVPCB) | exact | yes |
| 12 | GE | MVT-Plus | ICCB | General Electric | MVT-Plus (AKR LVPCB) | core | yes |
| 1 | GE | ECS | LVPCB AK/AKR | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 2 | GE | Ground Break | TGSR | General Electric |  | none | na |
| 3 | GE | MVT RMS-9 | ICCB | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 4 | GE | MVT RMS-9 | MCCB | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 5 | GE | MVT-4 | ICCB-LI | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 6 | GE | MVT-4 | ICCB-LSI | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 7 | GE | MVT-4 | MCCB-LI | General Electric | MVT-PM (AKR LVPCB) | frame | na |
| 8 | GE | MVT-4 | MCCB-LSI | General Electric | MVT-PM (AKR LVPCB) | frame | na |

Alias conflict list (`agrees_with_existing_alias = no`):

| trip_style_id | ep_mfr | ep_type | ep_style | etap_mfr | etap_model | tier | basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 143 | Cutler-Hammer | Amptector II-A | LVPCB | Cutler-Hammer |  | none | no ETAP candidate matched after restrictions |
| 527 | ABB | PR221DS | MCCB-LS | ABB | PR221DS-I (IEC-T6) | core | model-core (variant/frame/standard suffix may differ) |
| 1046 | ABB | PR221DS [IEC] | MCCB-LS | ABB | PR221DS-I (IEC-T6) | core | model-core (variant/frame/standard suffix may differ) |
| 1254 | ABB | PR231/P [IEC] | MCCB-LS | ABB | PR231/P-I (IEC) | core | model-core (variant/frame/standard suffix may differ) |
| 1322 | ABB | PR231/P | MCCB-LS | ABB | PR231/P-I (IEC) | core | model-core (variant/frame/standard suffix may differ) |
| 2260 | Eaton | PXR 10 | PDG4-LI | Eaton | PXR10(PDG3) LI | exact | model-core+function-code:LI |
| 2373 | Eaton | PXR 10 | PDG4-LSI | Eaton | PXR10(PDG3) LSI | exact | model-core+function-code:LSI |
| 2475 | Eaton | PXR20 | PDG4-LSI | Eaton | PXR20(PDG3) ALSI | exact | model-core+function-code:LSI |
| 2476 | Eaton | PXR20 | PDG4-LSIG | Eaton | PXR20(PDG3) ALSIG | exact | model-core+function-code:LSIG |
| 2503 | Siemens-Allis | Static Trip II | TSIG(3T) | Siemens-Allis |  | none | no ETAP manufacturer mapping/candidates |

Conflict count: 10. Full row-level conflict detail is present in the host-local `trip_unit_crosswalk.tsv` by filtering `agrees_with_existing_alias = no`.

## Level 3 - breaker crosswalk

Coverage by class and tier:

| class | tier | rows | pct |
| --- | --- | --- | --- |
| MCCB | exact | 386 | 3.7% |
| MCCB | core | 352 | 3.4% |
| MCCB | frame | 596 | 5.8% |
| MCCB | none | 9001 | 87.1% |
| ICCB | exact | 32 | 5.3% |
| ICCB | core | 0 | 0.0% |
| ICCB | frame | 58 | 9.5% |
| ICCB | none | 518 | 85.2% |
| PCB | exact | 196 | 6.0% |
| PCB | core | 55 | 1.7% |
| PCB | frame | 346 | 10.6% |
| PCB | none | 2682 | 81.8% |

Overall breaker tier counts:

| tier | rows | pct |
| --- | --- | --- |
| exact | 614 | 4.3% |
| core | 407 | 2.9% |
| frame | 1000 | 7.0% |
| none | 12201 | 85.8% |

Illustrative sample rows:

| class | breaker_style_id | ep_mfr | ep_frame | ep_r_cont_current | etap_mfr | etap_model | etap_amp_or_size | tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MCCB | 28 | ABB | S7H | 1200 | ABB | S7H | 1200 | exact |
| MCCB | 294 | GE | TEB |  | General Electric | TEB | 10 | core |
| MCCB | 32 | ABB | S3H-225 |  | ABB | Ts3 225 H | 225 | frame |
| MCCB | 1 | ABB | DSM |  | ABB |  |  | none |
| MCCB | 34 | ABB | S3L-225 |  | ABB | Ts3 225 H | 225 | frame |
| MCCB | 35 | ABB | S3N-225 |  | ABB | Ts3 225 H | 225 | frame |
| MCCB | 36 | ABB | S4N | 250 | ABB | S4N | 250 | exact |
| MCCB | 37 | ABB | S4H | 250 | ABB | S4H | 250 | exact |
| MCCB | 38 | ABB | S4L | 250 | ABB | S4L | 250 | exact |
| MCCB | 39 | ABB | S5N | 400 | ABB | S5N | 400 | exact |

## Anomalies and review notes

- ETAP carries both `Square D` and `Square-D`. Leaf-row observation in the supplied taxonomy files: `Square D` = 70, `Square-D` = 363. The dispatched Level 1 map sends EP `Square D` to `Square-D` and does not collapse the ETAP spelling split.
- The dispatch-provided map was treated as closed. Obvious-looking EP shorthand not in the map, including `SQD`, `Cutler Hammer`, and `Fed Pacific`, remained tier `none` rather than being invented as aliases.
- ETAP-only manufacturers after the EP map include: Square D.
- EP manufacturers absent from ETAP are listed in Level 1 and remain unmapped in downstream rows.
- Trip rows with multiple same-tier ETAP candidates: 1116. Breaker rows with multiple same-tier ETAP candidates: 1306. Candidate alternates are retained in the host-local TSV `alt_candidates` fields.
- Breaker AC/DC filtering used EP `ac_dc_code` as a deterministic two-value code: `0 -> AC`, `1 -> DC`; rows with no code would not be AC/DC-restricted.

## Verdict

Level 1 has strong coverage for canonical and dispatched EP manufacturer names, but the closed-map rule intentionally leaves shorthand/long-tail EP manufacturers unmapped. Level 2 has usable ETAP-taxonomy trip-unit coverage with alias conflicts isolated for review. Level 3 coverage is materially lower because breaker matching is restricted by manufacturer, standard, class, AC/DC, and frame/amp name agreement; it is suitable as a review artifact, not a persistence-ready alias population without CC review.
