# Breaker Sandbox + Codex Background Lane — Design Spec

**Date:** 2026-06-25
**Lane:** `lvbreaker/breaker-sandbox` (apex-power-ops-platform)
**Status:** DESIGN — awaiting operator sign-off before substrate build
**Origin:** Operator asked for a path to let the breaker (lvbreakertcc) lane progress in the
background via Codex, working against breaker data in an Olares DB, with **zero risk to the online
(prod Supabase) data**. This spec folds in a Codex cross-engine review (5 findings, all accepted).

---

## Goal

Stand up an air-gapped breaker-data substrate on the Olares host so Codex can run a bounded,
low-risk audit/work lane against a copy of the breaker catalog — never reaching prod, by
construction.

## Global Constraints (verbatim intent; load-bearing)

- **Prod `tcc.*` is the persisted PROJECTION; Access `TCC_NEW.accdb` is the BEHAVIORAL source of
  truth.** → The sandbox is sufficient for projection / contract / UI / serving-layer work. It is
  **NOT** sufficient for calc-engine *behavioral* rulings; those need the Access fixtures read-only
  and are **out of scope** for this lane.
- **No prod credentials on Olares.** The host today holds only `DEV_PG_PASSWORD` (the air gap).
  Seed via an **operator-side dump streamed into the host restore** — the prod credential never
  lands in host env, files, shell history, or Codex context. If a prod cred ever must touch the
  host: temporary read-only role with `VALID UNTIL`, `0600` env file, deleted immediately, with
  no-lingering-file/process verification.
- **Frozen baseline + disposable clones** — never one writable sandbox (safe from prod ≠ safe from
  agent churn).
- **Role scoping is PROVEN, not assumed** — run the `has_database_privilege` matrix; document the
  real result, including the PUBLIC-CONNECT residual (Postgres has no DENY).
- **A snapshot manifest is mandatory.**
- **Codex prompt fence:** no prod, no Supabase, no network DB except the clone DSN; produce
  findings + candidate patches only.
- **Promotion gate:** any prod change happens ONLY by the operator via the existing governed
  prod-write packet. Codex never writes prod.

## Provenance (read-only prod probe, 2026-06-25)

- Source: governed prod Supabase project `fxoyniqnrlkxfligbxmg` (apex-power-ops), Postgres 17.6.
- Schema `tcc`: **91 tables, 2 views, 30 sequences, 190 indexes**; total ~813 MB.
- Bulk: `relay_curve_points_tcp` (1.57M rows / 453 MB) + `relay_ranges` + `relay_discrete_values`
  ≈ 566 MB — the **relay** catalog, inert for breaker work but included for completeness.
- Breaker projection family (`etu_*`, `tmt_*`, `emt_*`) ≈ 250 MB.
- **Drift note:** repo docs describe `tcc.*` as ~60 tables; prod has 91. Logged here; reconcile the
  docs separately (not a blocker for seeding).

---

## Architecture

### Databases (on host `apex-dev-pg`, PG17)

1. **`tcc_breaker_baseline_20260625`** — one-way restore of the full prod `tcc` schema. **Frozen
   read-only.** Provenance-stamped. The single source the clones derive from.
2. **`tcc_breaker_codex_<task>_<date>`** — disposable writable clones created with
   `CREATE DATABASE … TEMPLATE tcc_breaker_baseline_20260625`. Dropped/recreated freely. First
   clone: `tcc_breaker_codex_79audit_20260625`.

### Roles

- **`tcc_breaker_ro`** — `CONNECT` + `SELECT` on the baseline; no write.
- **`tcc_breaker_rw`** — full privileges on clones **only**; no access to the baseline beyond read.
- `REVOKE CONNECT FROM PUBLIC` on baseline + clones.
- **Proof step:** after role creation, run
  ```sql
  select datname, has_database_privilege('tcc_breaker_rw', datname, 'CONNECT')
  from pg_database where datistemplate=false order by datname;
  ```
  Document the result. Expected residual: the role can CONNECT to sibling dev DBs via PUBLIC default
  but holds **zero object privileges** there; the operative guards are (a) object-level privileges,
  (b) the clone-only DSN handed to Codex, (c) the prompt fence.
- MCP entry `breaker-baseline` (read-only) for operator/CC visibility.

### Seed procedure

- **Operator (their machine, cred from Vault):**
  ```bash
  pg_dump --no-owner --no-privileges --schema=tcc -Fc "$PROD_RO_DSN" -f tcc_baseline_20260625.dump
  scp tcc_baseline_20260625.dump olares-mesh:/tmp/
  ```
- **CC (host):** create baseline DB → `pg_restore --no-owner --no-privileges -d
  tcc_breaker_baseline_20260625 /tmp/tcc_baseline_20260625.dump` (inside `apex-dev-pg`) → freeze →
  write `SNAPSHOT_MANIFEST.md` → delete the dump from `/tmp`.

### `SNAPSHOT_MANIFEST.md` contents

Source project ref + schema + UTC timestamp; dump command shape; object counts by relkind
(91/2/30/190); row counts for key tables (the `etu_*`/`tmt_*` list); sha256 of the dump file;
credential-disposal proof (no prod cred written to host); the 60→91 drift note.

---

## Codex lane

- Runs `codex exec` on the host, `-s workspace-write`, `-C <clone worktree>`; the only DB reachable
  is the clone (DSN = `tcc_breaker_codex_79audit_20260625` via `tcc_breaker_rw`).
- **First direction — #79 lvbreakertcc contract audit (projection scope):** verify the lvbreakertcc
  serving contract row-by-row against the TCC Master Reference + the live clone columns; characterize
  the parked **TMT F-010/011** safety hazard; emit a findings report + candidate patch SQL applied to
  the clone.
- **Prompt fence (verbatim intent):** no prod, no Supabase, no network DB except the clone DSN;
  projection/contract scope only — defer behavioral calc-engine rulings and flag where Access
  fixtures would be required; produce findings + candidate patches only.
- **Outputs:** `findings-79.md` + `candidate-patches/*.sql` (against the clone, never prod).

## Review + promotion

CC + operator review the findings; any prod-bound change goes through the existing governed
prod-write packet. Codex output is advisory + clone-local.

## Division of labor

- **CC:** build baseline+clone DBs, roles, manifest, setup scripts, the Codex harness + bounded
  prompt; restore the dump; review.
- **Operator:** the single prod-touching step (the read-only dump) + spec sign-off + prod promotion.
- **Codex:** execute the bounded #79 audit inside the clone.

## Open items

- Schema-doc drift (60→91) — reconcile repo docs separately.
- Behavioral-authority boundary (Access `TCC_NEW.accdb`) — calc rulings out of scope for this lane.
- Orchestration cadence — first run as a one-shot `codex exec` to prove the lane; graduate to an
  apex-jobs durable background job if it recurs.
