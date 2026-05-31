# Decision-012 Phase 4b PREP Resequence Closeout

Dispatch: `2026-05-30-cc-d012-phase4b-prep-resequence`
Executor: Codex
Date: 2026-05-31
Status: Complete. Reversible prep applied; terminal 4b drop dry-run now passes under `RESTRICT`.

## Claim

- Claim commit pushed: `4884f91c` (`claim: 2026-05-30-cc-d012-phase4b-prep-resequence by codex`)
- Live credential value was not printed.
- Packet lifecycle followed claim-push before live characterization or DDL.

## Coupling Map

Read-only catalog scan covered the 10 safe `_pre_rebuild` tables plus `public.tcc_etu_sensor_maint_v2`. Ownership was derived from `pg_depend.deptype = 'a'`; default consumers were derived from `pg_attrdef` dependencies.

| Drop-set table | Sequence owned by drop-set table | All default dependents | Kept default dependents |
| --- | --- | --- | --- |
| `public.tcc_etu_gfd_equations_pre_rebuild` | `public.tcc_etu_gfd_equations_id_seq` owned by `.id` | `public.tcc_etu_gfd_equations_pre_rebuild.id` | none |
| `public.tcc_etu_inst_curves_pre_rebuild` | `public.tcc_etu_inst_curves_id_seq` owned by `.id` | `public.tcc_etu_inst_curves_pre_rebuild.id` | none |
| `public.tcc_etu_ltd_params_pre_rebuild` | `public.tcc_etu_ltd_params_id_seq` owned by `.id` | `public.tcc_etu_ltd_params_pre_rebuild.id` | none |
| `public.tcc_etu_ltpu_multipliers_pre_rebuild` | `public.tcc_etu_ltpu_multipliers_id_seq` owned by `.id` | `public.tcc_etu_ltpu_multipliers_pre_rebuild.id` | none |
| `public.tcc_etu_plugs_pre_rebuild` | `public.tcc_etu_plugs_id_seq` owned by `.id` | `public.tcc_etu_plugs_pre_rebuild.id` | none |
| `public.tcc_etu_sensor_maint_pre_rebuild` | `public.tcc_etu_sensor_maint_id_seq` owned by `.id` | `public.tcc_etu_sensor_maint_pre_rebuild.id`; `tcc.etu_sensor_maint.id` | `tcc.etu_sensor_maint.id` |
| `public.tcc_etu_sensor_params_pre_rebuild` | `public.tcc_etu_sensor_params_id_seq` owned by `.id` | `public.tcc_etu_sensor_params_pre_rebuild.id` | none |
| `public.tcc_etu_settings_pre_rebuild` | none | none | none |
| `public.tcc_etu_std_equations_pre_rebuild` | `public.tcc_etu_std_equations_id_seq` owned by `.id` | `public.tcc_etu_std_equations_pre_rebuild.id` | none |
| `public.tcc_etu_stpu_overrides_pre_rebuild` | `public.tcc_etu_stpu_overrides_id_seq` owned by `.id` | `public.tcc_etu_stpu_overrides_pre_rebuild.id` | none |
| `public.tcc_etu_sensor_maint_v2` | none | none | none |

Couplings found:

| Sequence | Owned by drop-set | Kept dependents |
| --- | --- | --- |
| `public.tcc_etu_sensor_maint_id_seq` | `public.tcc_etu_sensor_maint_pre_rebuild.id` | `tcc.etu_sensor_maint.id = nextval('tcc_etu_sensor_maint_id_seq'::regclass)` |

Reverse informational scan found zero drop-set defaults pointing at kept-owned sequences.

## Migration

Authored and committed:

- `infra/database/migrations/tcc/003_phase4b_prep_resequence.sql`
- `infra/database/migrations/tcc/003_phase4b_prep_resequence_down.sql`
- Commit: `b38e13ea` (`db: add phase4b prep resequence migrations`)

UP sequence:

1. Guard the pre-state: `public.tcc_etu_sensor_maint_id_seq` exists, is owned by `public.tcc_etu_sensor_maint_pre_rebuild.id`, and is used by `tcc.etu_sensor_maint.id`.
2. `ALTER SEQUENCE ... OWNED BY NONE`.
3. Move the sequence into schema `tcc`.
4. Rename to `tcc.etu_sensor_maint_id_seq`.
5. Reassign ownership to `tcc.etu_sensor_maint.id`.
6. Guard the post-state and both default dependencies.

DOWN reverses the same metadata path and restores ownership to `public.tcc_etu_sensor_maint_pre_rebuild.id`. It is valid before the terminal 4b drop.

## Dry-Run And Apply

UP dry-run initially caught the expected PostgreSQL ownership rule: a sequence must be in the same schema as the table it is linked to. The migration was corrected to detach ownership before schema move, then reattach ownership after rename.

Corrected UP dry-run result:

| Check | Result |
| --- | --- |
| Sequence | `tcc.etu_sensor_maint_id_seq` |
| Owner | `tcc.etu_sensor_maint.id` |
| Defaults | `public.tcc_etu_sensor_maint_pre_rebuild.id` and `tcc.etu_sensor_maint.id` both resolve to `nextval('tcc.etu_sensor_maint_id_seq'::regclass)` |
| Transaction | rolled back |

Live apply result: `BEGIN` / guard `DO` / four `ALTER SEQUENCE` statements / post-guard `DO` / `COMMIT` all succeeded.

Post-apply confirmation:

| Check | Result |
| --- | --- |
| Sequence location | `tcc.etu_sensor_maint_id_seq` |
| Sequence owner | `tcc.etu_sensor_maint.id` |
| Canonical default | `tcc.etu_sensor_maint.id -> nextval('tcc.etu_sensor_maint_id_seq'::regclass)` |
| Pre-rebuild default | `public.tcc_etu_sensor_maint_pre_rebuild.id -> nextval('tcc.etu_sensor_maint_id_seq'::regclass)` |

DOWN dry-run after apply succeeded and rolled back, proving the reversible path restores `public.tcc_etu_sensor_maint_id_seq` ownership to `public.tcc_etu_sensor_maint_pre_rebuild.id`.

## 4b Drop Dry-Run

A temporary explicit `infra/database/migrations/tcc/004_phase4b_drop_backcompat.sql` artifact was authored locally and discarded after proof. It included:

- 60 back-compat views: 39 `public.tcc_*`, 20 `work.tcc_relay_*`, plus `work.tcc_relays`.
- 11 drop-set tables: 10 safe `_pre_rebuild` tables plus `public.tcc_etu_sensor_maint_v2`.
- `DROP VIEW ... RESTRICT` and `DROP TABLE ... RESTRICT`.
- Final guard for dropped-set absence, must-keep presence, `tcc.etu_sensor_maint_id_seq`, and 60 `tcc` base tables.

Dry-run result: PASS. All 60 `DROP VIEW ... RESTRICT` and 11 `DROP TABLE ... RESTRICT` statements completed in the transaction; final guard passed; transaction rolled back.

Rollback confirmation:

| Check | Result |
| --- | ---: |
| Drop-set views still present | 60 |
| Drop-set tables still present | 11 |
| Must-keep objects missing | 0 |
| `tcc` base tables present | 60 |

No new blocker surfaced.

## Post-Prep Gates

| Gate | Result |
| --- | --- |
| ETU parity | PASS: 3 seeded scenarios, evaluate warnings `0` |
| Relay parity | PASS: 6 seeded scenarios; families `bsl`, `iec`, `meq`, `pcd`, `swz`, `tcp`; warnings `0`; failures `0` |
| `GET /api/v1/neta/catalog/status` | PASS: HTTP `200`; `catalog=live`, `manufacturer_count=63`, `sensor_count=17831` |
| `GET /api/v1/neta/settings/29442` | PASS: HTTP `200`; plug `1`, LTPU `6`, STPU `15`, INST `20`, GFPU `7` |
| `GET /api/v1/neta/context/29442` | PASS: HTTP `200`; Chint / `NA` |
| `GET /api/v1/neta/relay/sections?supported_only=true&limit=3` | PASS: HTTP `200`; count `3`, first TD section `82782` |

## Boundary

- No view or table drop was committed in this dispatch.
- No row changes, app changes, package changes, or lockfile changes were made.
- The temporary 004 drop artifact was deleted and not committed.
- Next gated move is the terminal 4b drop re-run (`004_phase4b_drop_backcompat`) with Desktop go/no-go.
