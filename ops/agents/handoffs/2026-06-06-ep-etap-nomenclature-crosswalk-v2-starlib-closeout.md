# EP to ETAP nomenclature crosswalk v2 Star Library closeout

Dispatch: `2026-06-06-codex-ep-etap-nomenclature-crosswalk-v2-starlib`

Mode: prod Supabase read-only + host-local ETAP Star Library help-doc read. No DB writes, no DDL, no code wiring, and no bulk Star Library TSV committed. Host-local outputs were written under `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/`.

Generated artifacts, gitignored:

- `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/mfr_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/trip_unit_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/breaker_crosswalk.tsv`
- `.audit_workspace/etap_tcc_sources/crosswalk/v2_starlib/crosswalk_method.md`

Provenance on every row: `[ETAP Star Library List - published help docs] names-only crosswalk`.

## Pages parsed

| kind | family | page | title | rows | columns | status |
| --- | --- | --- | --- | --- | --- | --- |
| trip | ETU | LVSST.htm | Low Voltage Solid State Trip | 965 | Manufacturer, Model, Zone Selective Interlock | parsed |
| trip | TMT | Thermal_Magnetic_Trip.htm | Thermal Magnetic Trip | 910 | Manufacturer, Model | parsed |
| trip | MCP | Motor_Circuit_Protector.htm | Motor Circuit Protector Trip | 88 | Manufacturer, Model | parsed |
| trip | EMT | Electro_Magnetic_Trip.htm | Electro-Mechanical Trip | 75 | Manufacturer, Model | parsed |
| breaker | MCCB | ANSI_AC_Molded_Case_breakers.htm | AC ANSI Molded Case Circuit Breaker (MCCB) | 1538 | Manufacturer, Model | parsed |
| breaker | MCCB | IEC_AC_Molded_Case_breakers.htm | AC IEC Molded Case Circuit Breaker (MCCB) | 1222 | Manufacturer, Model | parsed |
| breaker | MCCB | ANSI_DC_Molded_Case_breakers.htm | DC ANSI Molded Case Circuit Breaker (MCCB) | 465 | Manufacturer, Model | parsed |
| breaker | MCCB | IEC_DC_Molded_Case_breakers.htm | DC IEC Molded Case Circuit Breaker (MCCB) | 368 | Manufacturer, Model | parsed |
| breaker | ICCB | ANSI_AC_Insulated_Case_breakers.htm | AC ANSI Insulated Case Circuit Breaker (ICCB) | 405 | Manufacturer, Model | parsed |
| breaker | ICCB | IEC_AC_Insulated_Case_breakers.htm | AC IEC Insulated Case Circuit Breaker (ICCB) | 19 | Manufacturer, Model | parsed |
| breaker | ICCB | ANSI_DC_Insulated_Case_breakers.htm | DC ANSI Insulated Case Circuit Breaker (ICCB) | 22 | Manufacturer, Model | parsed |
| breaker | ICCB | IEC_DC_Insulated_Case_breakers.htm | MISSING | 0 |  | missing |
| breaker | PCB | ANSI_AC_Power_Breakers.htm | AC ANSI Power Circuit Breaker (PCB) | 684 | Manufacturer, Model | parsed |
| breaker | PCB | IEC_AC_Power_breakers.htm | AC IEC Power Circuit Breaker (PCB) | 569 | Manufacturer, Model | parsed |
| breaker | PCB | ANSI_DC_Power_Breakers.htm | DC ANSI Power Circuit Breaker (PCB) | 22 | Manufacturer, Model | parsed |
| breaker | PCB | IEC_DC_Power_breakers.htm | DC IEC Power Circuit Breaker (PCB) | 44 | Manufacturer, Model | parsed |

`Electro_Magnetic_Trip.htm` title is `Electro-Mechanical Trip`, so it is the EMT list. `IEC_DC_Insulated_Case_breakers.htm` is absent on this host and was recorded as missing.

## Level 1 - manufacturer crosswalk

Tier counts:

| tier | count |
| --- | --- |
| case | 3 |
| conditional | 2 |
| contract | 1 |
| expand | 3 |
| identity | 28 |
| label | 3 |
| none | 88 |
| punctuation | 4 |
| rebrand | 2 |
| shorthand | 1 |
| spelling | 1 |
| typo | 1 |

Full EP manufacturer map used by trip styles or breaker styles:

| ep_mfr_id | ep_mfr_name | etap_mfr_name | tier | trip_styles | breaker_styles |
| --- | --- | --- | --- | --- | --- |
| 1 | ABB | ABB | identity | 130 | 1562 |
| 2 | Allis Chalmer | Allis-Chalmers | typo | 0 | 26 |
| 4 | Brown Boveri | ITE (BBC) | label | 0 | 14 |
| 8 | Fed Pacific | Federal Pacific | conditional | 0 | 134 |
| 9 | GE | General Electric | expand | 175 | 1228 |
| 11 | ITE | ITE (BBC) | label | 18 | 224 |
| 15 | Siemens | Siemens | identity | 431 | 1648 |
| 16 | Siemens Allis | Siemens-Allis | punctuation | 0 | 63 |
| 17 | SQD | Square-D | shorthand | 0 | 1162 |
| 18 | West | Westinghouse | expand | 113 | 478 |
| 21 | Joslyn | Joslyn | identity | 1 | 0 |
| 28 | Cutler-Hammer | Cutler-Hammer | identity | 259 | 309 |
| 29 | English Elect | (none) | none | 0 | 1 |
| 33 | Siemens-Allis | Siemens-Allis | identity | 1 | 0 |
| 35 | Square D | Square-D | punctuation | 191 | 14 |
| 36 | Westinghouse | Westinghouse | identity | 0 | 20 |
| 40 | Merlin Gerin | Merlin Gerin | identity | 102 | 684 |
| 41 | Cutler Hammer | Cutler-Hammer | punctuation | 0 | 762 |
| 42 | Heinemann | Heinemann | identity | 0 | 24 |
| 43 | SACE | (none) | none | 6 | 73 |
| 44 | Trumbel | (none) | none | 0 | 2 |
| 45 | Federal Pioneer | Federal Pioneer | identity | 34 | 104 |
| 46 | Fuji | Fuji | identity | 20 | 340 |
| 47 | GTE | (none) | none | 0 | 6 |
| 48 | Roller Smith | Roller Smith | identity | 0 | 8 |
| 49 | Multilin | Multilin | identity | 2 | 0 |
| 50 | Utility Relay | Utility Relay | identity | 12 | 0 |
| 51 | Carriere | Carriere | identity | 4 | 0 |
| 52 | Satin American | satinAMERICAN | spelling | 6 | 0 |
| 61 | Toshiba | TOSHIBA | identity | 0 | 5 |
| 62 | (Generic) | (none) | none | 1 | 34 |
| 67 | Thomas&Betts | (none) | none | 0 | 4 |
| 68 | Westrip | WESTRIP | case | 6 | 0 |
| 79 | Moeller | Moeller | identity | 36 | 258 |
| 82 | Sytek | Sytek | identity | 1 | 0 |
| 84 | Schneider | Schneider Electric | expand | 17 | 348 |
| 85 | Allis-Chalmers | Allis-Chalmers | identity | 18 | 0 |
| 96 | Hyundai | Hyundai | identity | 1 | 130 |
| 97 | American | (none) | none | 0 | 10 |
| 99 | HUNDT & WEBER | (none) | none | 0 | 26 |
| 100 | CBI | (none) | none | 3 | 40 |
| 101 | Allen-Bradley | Allen-Bradley | identity | 69 | 604 |
| 102 | Fuji America | (none) | none | 0 | 30 |
| 104 | Sure-Trip | SURE-TRIP | case | 4 | 0 |
| 107 | Dorman Smith | (none) | none | 5 | 39 |
| 110 | IndustrialPower | (none) | none | 1 | 0 |
| 118 | Federal Pacific | Federal Pacific | conditional | 11 | 6 |
| 121 | Challenger | Challenger | identity | 9 | 41 |
| 122 | Mitsubishi | Mitsubishi | identity | 21 | 292 |
| 123 | Murray | (none) | none | 0 | 7 |
| 124 | Telemecanique | Telemecanique | identity | 0 | 39 |
| 125 | BBC | ITE (BBC) | label | 4 | 0 |
| 129 | Benshaw | (none) | none | 1 | 50 |
| 131 | Eaton | Eaton | identity | 185 | 892 |
| 135 | Unelec | (none) | none | 9 | 53 |
| 138 | Automation Drct | (none) | none | 0 | 5 |
| 144 | Hitachi | Hitachi | identity | 2 | 22 |
| 149 | Sylvania | SYLVANIA | case | 7 | 0 |
| 150 | Whipp & Bourne | (none) | none | 4 | 0 |
| 151 | Terasaki | Terasaki | identity | 40 | 268 |
| 159 | Generac | (none) | none | 0 | 3 |
| 162 | Caterpillar | (none) | none | 0 | 1 |
| 164 | Bryant | (none) | none | 0 | 5 |
| 166 | ERMCO | (none) | none | 0 | 6 |
| 169 | Sprecher+Schuh | (none) | none | 0 | 34 |
| 173 | Gould | (none) | none | 0 | 4 |
| 189 | Altech Corp | (none) | none | 0 | 27 |
| 192 | LS Industrial | LSIS | rebrand | 7 | 408 |
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
| 235 | SquareD | Square-D | punctuation | 0 | 57 |
| 238 | bticino | (none) | none | 27 | 129 |
| 240 | Milbank | Milbank | identity | 0 | 4 |
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
| 304 | LG Industrial | LSIS | rebrand | 1 | 20 |
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

Union ETAP manufacturer vocabulary from parsed pages:

ABB, AEG, Allen Bradley, Allen-Bradley, Allis-Chalmers, Alsthom, BS 7671 (17th Ed.), Brown Boveri, Carling Technologies, Carriere, Challenger, Cutler-Hammer, Eaton, Electromagnetic Industries LLP, Federal Pacific, Federal Pacific Electric, Federal Pioneer, Fuji, GE Power Control, GE Power Controls, GEC Alsthom, General Electric, Heinemann, Hitachi, Hyundai, ITE, ITE (BBC), ITE-Imperial, Joslyn, K Moeller, L&T, LSIS, Merlin Gerin, Milbank, Mitsubishi, Moeller, Multilin, Nikko, Nikko Electric, Roller Smith, SPD Technologies, SURE-TRIP, SYLVANIA, Schneider Electric, Secheron, Siemens, Siemens-Allis, Square D, Square-D, Sylvania, Sytek, TOSHIBA, Telemecanique, Terasaki, Utility Relay, WESTRIP, Westinghouse, satinAMERICAN

ETAP-only manufacturers after Level 1 mapping: Allen Bradley, Alsthom, BS 7671 (17th Ed.), Brown Boveri, Carling Technologies, Electromagnetic Industries LLP, Federal Pacific Electric, GE Power Control, GE Power Controls, GEC Alsthom, ITE, ITE-Imperial, K Moeller, Nikko, Nikko Electric, SPD Technologies, Secheron, Square D, Sylvania.

EP manufacturers absent from ETAP under the v2 map: (Generic), ABB-Wylex, AMR, ASI, Altech Corp, American, Atom Power, Automation Drct, Benshaw, Bill, Bryant, CBI, Carling Tech, Caterpillar, Changshu, Chint, Commander, Crabtree, Crouse-Hinds, Delixi, Doepke, Dorman Smith, E-T-A, EEC, ERMCO, ETA, ETC, English Elect, FMX, Franklin CS, Fuji America, GEIS, GTE, GTE/Sylvania, Generac, Gewiss, Gould, HUNDT & WEBER, Hager, Havells, IndustrialPower, Jiangshu, KTE, Kohler, Legrand, Lovato, MEM, Murray, NHP, Nader, Noark, OEZ, Ottermill, P&A Power Sys, PS Electrical, People Electric, Proteus, Renmin, SACE, SPD Electrical, SREAW, Sace Bergamo, Sace-Sud, Schrack, Sensata, Sensitr, Shanghai Electr, Shihlin, Soprano, Sprecher+Schuh, Stahl, Steck, T&B, Taesung, Taian, Techna, Thomas&Betts, Tianjin Benefo, Trumbel, Trumbull, Unelec, WEG, Weidmuller, Whipp & Bourne, Xiamen Hongfa, Zhejiang BSB, bticino, c3controls.

Map targets absent from parsed vocabulary: none.

Moeller / K Moeller per-family finding: ANSI_AC_Molded_Case_breakers.htm:K Moeller, IEC_AC_Molded_Case_breakers.htm:K Moeller, IEC_AC_Molded_Case_breakers.htm:Moeller, IEC_AC_Power_breakers.htm:Moeller, IEC_DC_Molded_Case_breakers.htm:K Moeller, LVSST.htm:Moeller, Thermal_Magnetic_Trip.htm:K Moeller.

## Level 2 - trip-unit crosswalk

Coverage by tier:

| tier | rows | pct |
| --- | --- | --- |
| exact | 481 | 23.0% |
| core | 360 | 17.2% |
| frame | 657 | 31.4% |
| none | 597 | 28.5% |

Trip family inference counts: {'ETU': 2009, 'EMT': 52, 'MCP': 10, 'TMT': 24}.

Existing alias agreement check:

| agreement | rows |
| --- | --- |
| yes | 83 |
| no | 40 |
| na | 1972 |

Illustrative sample rows:

| trip_style_id | ep_mfr | ep_type | ep_style | etap_mfr | etap_model | page | tier | alias_agree |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | GE | ECS | LVPCB AK/AKR | General Electric | ECS | LVSST.htm | exact | na |
| 5 | GE | MVT-4 | ICCB-LI | General Electric | MVT-4 | LVSST.htm | exact | na |
| 3 | GE | MVT RMS-9 | ICCB | General Electric | MVT-9 (ICCB) | LVSST.htm | core | na |
| 4 | GE | MVT RMS-9 | MCCB | General Electric | MVT-9 (MCCB) | LVSST.htm | core | na |
| 2 | GE | Ground Break | TGSR | General Electric | Spectra RMS SE Mag-Break | LVSST.htm | frame | na |
| 58 | West | CL-R | LCL | Westinghouse | Seltronic LCL (Adj) | LVSST.htm | frame | na |
| 31 | GE | THP | Integral GF | General Electric |  | ETU | none | na |
| 39 | GE | VersaTrip MOD2 | THKS | General Electric |  | EMT | none | na |

Alias conflict list (`agrees_with_existing_alias = no`):

| trip_style_id | ep_mfr | ep_type | ep_style | etap_mfr | etap_model | page | tier | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | GE | MVT-Plus | ICCB | General Electric | MVT-9 (ICCB) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 13 | GE | MVT-Plus | LVPCB | General Electric | MVT-9 (LVPCB) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 15 | GE | MVT-PM | ICCB | General Electric | MVT-9 (ICCB) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 16 | GE | MVT-PM | LVPCB | General Electric | MVT-9 (LVPCB) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 57 | West | Amptector II-A | LVPCB | Westinghouse |  | EMT | none | no Star Library candidate matched after restrictions; family=EMT (contains electro-mechanical/static legacy cue) |
| 132 | Siemens | Static Trip II | LI | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 133 | Siemens | Static Trip II | LIG | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 134 | Siemens | Static Trip II | LS | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 135 | Siemens | Static Trip II | LSG | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 136 | Siemens | Static Trip II | LSI | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 137 | Siemens | Static Trip II | LSIG | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 138 | Siemens | Static Trip III | LVPCB | Siemens |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 143 | Cutler-Hammer | Amptector II-A | LVPCB | Cutler-Hammer |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |
| 256 | GE | MVT-PM | MCCB | General Electric | MVT-9 (MCCB) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 419 | Siemens | ETU 745 L(SIG) | WL FS I | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 420 | Siemens | ETU 745 L(SIG) | WL FS II | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 421 | Siemens | ETU 745 L(SIG) | WL FS III | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 527 | ABB | PR221DS | MCCB-LS | ABB |  | TMT | none | no Star Library candidate matched after restrictions; family=TMT (contains thermal-magnetic cue) |
| 740 | ABB | PR222DS | MCCB-LSIG | ABB | PR222DS/P-LSIG (IEC-T4) | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 1046 | ABB | PR221DS [IEC] | MCCB-LS | ABB |  | TMT | none | no Star Library candidate matched after restrictions; family=TMT (contains thermal-magnetic cue) |
| 1047 | ABB | PR222DS [IEC] | MCCB-LSIG | ABB | PR222DS/P-LSIG (IEC-T4) | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 1096 | Siemens | ETU 745 L(SIG) | ICCB WL FS I | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1097 | Siemens | ETU 745 L(SIG) | ICCB WL FS II-S | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1098 | Siemens | ETU 745 L(SIG) | ICCBWL FS III-L | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1099 | Siemens | ETU 745 L(SIG) | ICCB WL FS II-L | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1100 | Siemens | ETU 745 L(SIG) | ICCB WL FS II-C | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1101 | Siemens | ETU 745 L(SIG) | ICCBWL FS III-C | Siemens | ETU745 (I^2t) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1199 | ABB | PR221DS-I | MCP | ABB |  | MCP | none | no Star Library candidate matched after restrictions; family=MCP (contains MCP/motor-protector/magnetic-only cue) |
| 1201 | ABB | PR231/P-I | MCP | ABB |  | MCP | none | no Star Library candidate matched after restrictions; family=MCP (contains MCP/motor-protector/magnetic-only cue) |
| 1254 | ABB | PR231/P [IEC] | MCCB-LS | ABB | PR231/P-I (IEC) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 1322 | ABB | PR231/P | MCCB-LS | ABB | PR231/P-I (IEC) | LVSST.htm | core | model-core; family=ETU (default solid-state/electronic trip page) |
| 1327 | GE | MVT-PM (RMS-9D) | LVPCB-LSIG | General Electric | MVT-9 (ICCB) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 1328 | GE | MVT-PM (RMS-9D) | LVPCB-LI/G | General Electric | MVT-9 (ICCB) | LVSST.htm | frame | token-overlap+number; family=ETU (default solid-state/electronic trip page) |
| 2260 | Eaton | PXR 10 | PDG4-LI | Eaton | PXR10(PDG3) LI | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2373 | Eaton | PXR 10 | PDG4-LSI | Eaton | PXR10(PDG3) LSI | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2466 | Eaton | PXR20 | PDG3-LSI | Eaton | PXR10(PDG3) LSI | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2467 | Eaton | PXR20 | PDG3-LSIG | Eaton | PXR20(PDC5) ALSIG | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2475 | Eaton | PXR20 | PDG4-LSI | Eaton | PXR10(PDG4) LSI | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2476 | Eaton | PXR20 | PDG4-LSIG | Eaton | PXR20(PDC5) ALSIG | LVSST.htm | exact | model-core+function-code; family=ETU (default solid-state/electronic trip page) |
| 2503 | Siemens-Allis | Static Trip II | TSIG(3T) | Siemens-Allis |  | EMT | none | no Star Library manufacturer/family candidates; family=EMT (contains electro-mechanical/static legacy cue) |

Conflict count: 40. Full row-level conflict detail is in the host-local `trip_unit_crosswalk.tsv`.

## Level 3 - breaker crosswalk

Coverage by class and tier:

| class | tier | rows | pct |
| --- | --- | --- | --- |
| MCCB | exact | 1374 | 13.3% |
| MCCB | core | 1017 | 9.8% |
| MCCB | frame | 1546 | 15.0% |
| MCCB | none | 6398 | 61.9% |
| ICCB | exact | 143 | 23.5% |
| ICCB | core | 31 | 5.1% |
| ICCB | frame | 85 | 14.0% |
| ICCB | none | 349 | 57.4% |
| PCB | exact | 622 | 19.0% |
| PCB | core | 273 | 8.3% |
| PCB | frame | 440 | 13.4% |
| PCB | none | 1944 | 59.3% |

Overall breaker tier counts:

| tier | rows | pct |
| --- | --- | --- |
| exact | 2139 | 15.0% |
| core | 1321 | 9.3% |
| frame | 2071 | 14.6% |
| none | 8691 | 61.1% |

Illustrative sample rows:

| class | breaker_style_id | ep_mfr | ep_frame | etap_mfr | etap_model | page | tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MCCB | 1 | ABB | DSM | ABB | DSM | ANSI_AC_Molded_Case_breakers.htm | exact |
| MCCB | 4 | ABB | ESB2 | ABB | ESB2 | ANSI_AC_Molded_Case_breakers.htm | exact |
| MCCB | 50 | ABB | S3N MCP(3-25AT) | ABB | S3N_MCP (3-25A) | ANSI_AC_Molded_Case_breakers.htm | core |
| MCCB | 82 | Cutler Hammer | LA 400 | Cutler-Hammer | HLA-400 | ANSI_AC_Molded_Case_breakers.htm | core |
| MCCB | 2 | ABB | EHB | ABB | EHB4 | ANSI_AC_Molded_Case_breakers.htm | frame |
| MCCB | 3 | ABB | ESB | ABB | ESB2 | ANSI_AC_Molded_Case_breakers.htm | frame |
| MCCB | 23 | ABB | SEB | ABB |  |  | none |
| MCCB | 24 | ABB | SEM-E5 | ABB |  |  | none |

## Delta vs v1

| level | v1_none | v2_none | none_drop | v1_matched | v2_matched | matched_lift |
| --- | --- | --- | --- | --- | --- | --- |
| manufacturer | 118 | 88 | 30 | 19 | 49 | 30 |
| trip_unit | 979 | 597 | 382 | 1116 | 1498 | 382 |
| breaker | 12201 | 8691 | 3510 | 2021 | 5531 | 3510 |

## Anomalies and review notes

- EMT page identity confirmed by page title: `Electro_Magnetic_Trip.htm` is titled `Electro-Mechanical Trip`.
- Missing page: `IEC_DC_Insulated_Case_breakers.htm`.
- EP manufacturers still `none`: (Generic), ABB-Wylex, AMR, ASI, Altech Corp, American, Atom Power, Automation Drct, Benshaw, Bill, Bryant, CBI, Carling Tech, Caterpillar, Changshu, Chint, Commander, Crabtree, Crouse-Hinds, Delixi, Doepke, Dorman Smith, E-T-A, EEC, ERMCO, ETA, ETC, English Elect, FMX, Franklin CS, Fuji America, GEIS, GTE, GTE/Sylvania, Generac, Gewiss, Gould, HUNDT & WEBER, Hager, Havells, IndustrialPower, Jiangshu, KTE, Kohler, Legrand, Lovato, MEM, Murray, NHP, Nader, Noark, OEZ, Ottermill, P&A Power Sys, PS Electrical, People Electric, Proteus, Renmin, SACE, SPD Electrical, SREAW, Sace Bergamo, Sace-Sud, Schrack, Sensata, Sensitr, Shanghai Electr, Shihlin, Soprano, Sprecher+Schuh, Stahl, Steck, T&B, Taesung, Taian, Techna, Thomas&Betts, Tianjin Benefo, Trumbel, Trumbull, Unelec, WEG, Weidmuller, Whipp & Bourne, Xiamen Hongfa, Zhejiang BSB, bticino, c3controls.
- Trip rows with multiple same-tier candidates: 1067. Breaker rows with multiple same-tier candidates: 1973. Alternates are retained in host-local `alt_candidates`.
- Parsed breaker pages exposed `Manufacturer` and `Model` only in this Star Library help set; no dedicated frame/amp columns were detected.

## Verdict

Level 1: v2 materially improves manufacturer normalization by using the broader published Star Library vocabulary and corrected map. Level 2: v2 improves Star-backed trip-unit matching but keeps conflicts explicit for CC review. Level 3: v2 dramatically lowers breaker `none` rows versus v1 because the published breaker lists cover far more long-tail manufacturers and models, though high-cardinality frame variants still need review before persistence.
