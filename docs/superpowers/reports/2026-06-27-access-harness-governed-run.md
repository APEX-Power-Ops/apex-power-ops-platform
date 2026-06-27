# Access Fidelity Harness -- Governed Mirror Run (Phase 1) -- Evidence Record

Date: 2026-06-27 (America/Phoenix)
Lane context: Path-A governed-materialization slice merged to main `6e288120` (PR #42).
Purpose: the durable, provenance-stamped, checksum-validated `access_raw` that the breaker
029/030 D4/D5 population SQL is generated FROM (D-C: generate-from-governed, not direct Access).
HR1: the harness records structural evidence only (counts / checksums / booleans); it makes NO
behavioral interpretation. Access/engine authority remains operator-side.

## Execution context
- Checkout: Windows worktree `C:\dev\apex-access-harness`, HEAD `ade8a209`; `git diff ade8a209 origin/main`
  was EMPTY -> the run code was byte-identical to merged main `6e288120` (no drift).
- Dependency framing (honest): LOCAL Access (frozen, read-only) + LOCAL governed Postgres
  (`tcc_fidelity_governed`, PG18) + READ-ONLY host viewer snapshot over the mesh.
- Commands: `provision-governed` (fresh create + DDL) -> `--governed run-all` (exit 0).
- Fence: post-run readback confirmed `current_database() = tcc_fidelity_governed`.
- No 029/030 write occurred; this run only materializes + validates the governed mirror.

## provision-governed
- `tcc_fidelity_governed`: CREATED FRESH (did not pre-exist -> no stale-schema-drift path).
- Applied `001_schemas.sql`. Exit 0.
- Post-provision schema sanity (P3) PASS: `access_meta.tables.checksum`,
  `access_validation.checksum_reconciliation`, `access_meta.materialized_owner` all present;
  `load_state` CHECK admits inventoried_only / extracting / loaded / checksummed / failed.

## extraction_run (provenance)
| field | value |
|---|---|
| run_id | `c15adaef-20260608T210440` |
| source_path | `D:\TCC_NEW.accdb` (250,884,096 bytes) |
| frozen_copy_path | `D:\_access_frozen\TCC_NEW_20260608T210440_c15adaef.accdb` |
| source_sha256 | `c15adaefa57ed1bbc10d82c24842c5d9fc89e5d2b6992f50c0aeba764a59a16a` |
| driver | ACEODBC.DLL 12.00.0000 |
| read_only | True |
| harness_version | 0.1.0 |
| extracted_at | 2026-06-27 16:02:17 (America/Phoenix) |

## tcc_snapshot (read-only host bridge)
| field | value |
|---|---|
| snapshot_id | `c15adaef-20260608T210440-tcc-40067d1d` |
| host | 100.64.0.1 |
| db_name | tcc_breaker_viewer_20260625 |
| role | tcc_breaker_ro (READ-ONLY) |
| captured_at | 2026-06-27 16:05:52 (America/Phoenix) |

## Loaded tables (access-side row counts = G1 Master Reference / Access truth)
| table | rows | load_state | checksum (sha256) |
|---|---|---|---|
| Breaker_TMTFrameSizes | 42238 | checksummed | `72446369b7bc55c9c7802e9d394f5c5e6322a02b0a38f5867c2e3f5c3e2481bc` |
| Breaker_TMTFrameAmps | 67206 | checksummed | `087148c352446e26776637af168fea3a6bfba8aab48081132fd06a3b660da265` |
| Breaker_TMTFrameSettings | 58041 | checksummed | `fef6916d5cde27e8ebcfbd2e5cba11896b76b60888fc4ff3c64e3f2492f93394` |
| Breaker_TMTThermalTripAdj | 21790 | checksummed | `934c17e82dad0cf843932cf2eca6dd7f7fb60b14ce85424a4fc9bef82dfddc64` |
| BreakerICCBStyles | 608 | checksummed | `132de0305eaad195b0ebce4f944a19d0da87b96739f7a1908a16892f7d3bb539` |
| BreakerMCCBStyles | 10335 | checksummed | `485ef989fd8dcf51da104be4316ff6ef4b8013ab389b93f4da70c71f95f7a006` |
| BreakerPCBStyles | 3279 | checksummed | `8458772933c817977f66bc359c56b21b7e9ff173c64138dc2f9bfe2434566734` |

Loaded: 7 tables. Inventoried: 79 tables. Style D5 total = 608 + 10335 + 3279 = 14222 (matches the
prior direct-Access dry-run).

## checksum_reconciliation -- access_checksum == staging_checksum, matches = TRUE for ALL 7
| table | matches |
|---|---|
| BreakerICCBStyles | True |
| BreakerMCCBStyles | True |
| BreakerPCBStyles | True |
| Breaker_TMTFrameAmps | True |
| Breaker_TMTFrameSettings | True |
| Breaker_TMTFrameSizes | True |
| Breaker_TMTThermalTripAdj | True |

The fail-closed `assert_style_parents_faithful` gate did NOT raise (run exited 0): the three style
parents round-trip byte-faithful.

## key_quality (style parents)
| table | candidate_key | is_unique | distinct | total |
|---|---|---|---|---|
| BreakerICCBStyles | [ID] | True | 608 | 608 |
| BreakerMCCBStyles | [ID] | True | 10335 | 10335 |
| BreakerPCBStyles | [ID] | True | 3279 | 3279 |

ID is a clean unique key on each style parent -- a sound basis for the D4/D5 carry key.

## Verdict
Phase 1 PASS. A durable, provenance-stamped, per-table-checksummed `access_raw` persists in
`tcc_fidelity_governed`, with the 3 style parents proven byte-faithful (matches=True) and uniquely
keyed. The Path-A prerequisite for prod 029/030 population is MET, live. No 029/030 SQL was applied.

## Next (separate operator go each)
Phase 2 (build-only): swap the D4/D5 generator's source from direct Access to governed
`access_raw."Breaker*Styles"` in `tcc_fidelity_governed`; emit provenance-stamped 029/030 data SQL
(header = run_id + snapshot_id + Access sha256 + per-table counts + checksums + matches); fail closed
on wrong source DB / missing-or-ambiguous run_id / style reconciliation not True / key_quality not
unique / required columns absent; preserve policy (a) (carry raw override blocks verbatim, do NOT
filter on InstOvrAmps > 0); dry-run on a FRESH dated clone off `tcc_breaker_baseline_20260625` (NOT
the 79audit clone); Codex + opus review. THEN separate gos: 029 DDL -> governed 029 data -> 030 DDL
-> governed 030 data -> author 031 against the populated state. F-79-03 row-level frame anti-join
stays a separate, parked Access-evidence track.
