# D4/D5 population — DRY-RUN (Path B) artifacts

**DRY-RUN ONLY. NOT prod population. NOT evidence custody.**

These artifacts validate the population LOGIC for migrations `029` (D4 helper re-carry) and `030`
(D5 native_bounded raw-carry side table) on a disposable sandbox clone. **Production population MUST use
Path A**: a governed frozen-snapshot read (the Access Fidelity Harness) carrying provenance / checksum /
run_id / repeatable evidence. This dry-run is a tactical proof of logic, not the prod evidence model.

## Files
- `dry_run_direct_access_population_generator.py` — reads a FROZEN, hash-recorded copy of `D:\TCC_NEW.accdb`
  read-only (pyodbc `Mode=Read`) and emits the guarded population SQL + a fidelity report. The emitted SQL
  refuses to run unless `current_database() LIKE '%dryrun%'`.
- `dry_run_fidelity_report.md` — counts / null summaries / override-discriminator / spot-checks from the
  validated run (clone `tcc_breaker_d4d5_dryrun_20260627`, off `tcc_breaker_baseline_20260625`).

## Policy (a) — maximal raw carry (operator-ratified 2026-06-27)
030 carries one row per style with >=1 non-null D5 block. Access defaults byte-enum/tolerance cols to 0
(non-null), so `inst_override`/`ninst_override` are non-null for ~all styles (14,222 rows). **Block
non-nullness is NOT "has override"** — the real signal is `(inst_override->>'InstOvrAmps')::numeric > 0`.
Rating-only styles (13,533 of them: ICCB 367 + MCCB 10,204 + PCB 2,962) are intentionally retained; an
`InstOvrAmps>0` filter would have dropped them (Codex review-333c08d3). The same "non-null != meaningful"
caution applies to the D4 text fields (`tmt_notes` / `tmt_tcc_number`): trim/decode before treating as
present; derived booleans (`has_inst_override_amp`, etc.) belong in a decoded/serving layer AFTER the
cut-line is ratified, not in this raw-carry substrate.

## Guardrails honored
Frozen hash-recorded Access copy (sha256 `c15adaef…a16a`, byte-identical to source), read-only, disposable
`*dryrun*` clone only, `current_database()` hard guard (proven to refuse on non-dryrun DBs). Nothing touched
prod or the governed harness DBs.
