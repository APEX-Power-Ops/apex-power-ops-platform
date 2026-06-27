# Access Fidelity Harness

Mirrors a Microsoft Access database into Postgres and produces **structural
fidelity evidence** comparing the Access source against the governed `tcc.*`
schema -- with **zero behavioral interpretation** (HR1: the harness records what
differs, never whether a difference is "correct", "expected", or "a gap").

Phase 1 ships the breaker/TMT slice end to end and the live **F-79-03**
structural evidence (`access-harness run-all`).

## Build / run on Windows

The Access path (ACE OLE DB + the `Microsoft Access Driver` via pyodbc) is
**Windows-only**.  Build and run on Windows; the integration tests skip with a
clear reason off-Windows or when a prerequisite is absent.

```sh
# from infra/database/access-harness/
uv run pytest -q                                   # full suite
uv run pytest tests/test_acceptance_f79_03.py -v -s  # the F-79-03 acceptance (live, ~2.5 min)
uv run python -m access_harness.cli --help
```

## Environment

| variable | purpose |
| --- | --- |
| `ACCESS_HARNESS_SUPERUSER_DSN` | local Postgres superuser DSN (the target db is in the DSN; `tcc_fidelity_test` is derived for the test fence) |
| `TCC_BREAKER_RO_PW` | host `tcc_breaker_ro` SELECT-only password (the governed tcc over the LarePass mesh, `100.64.0.1:5432`). The host connection is built from psycopg **kwargs, never a URI** (the password has URL-breaking characters). |
| `ACCESS_HARNESS_FROZEN_DIR` | directory for content-addressed frozen `.accdb` copies (default `D:\_access_frozen`) |
| `ACCESS_HARNESS_ACCDB` / `--accdb` | the source `.accdb` path (default `D:\TCC_NEW.accdb`) |

The password is never printed or logged.

## Subcommands

```
access-harness [--accdb PATH] [--frozen-dir DIR] [--with-curves] <command>
```

| command | what it does |
| --- | --- |
| `freeze` | stream-hash + copy the `.accdb` to a content-addressed frozen file |
| `extract` | freeze + driver preflight + record an `access_meta.extraction_run` |
| `load` | data-load the breaker/TMT slice into `access_raw` |
| `inventory` | inventory **all** tables (`access_meta.*`); data-load only the slice |
| `snapshot-tcc --run-id R` | pull the TMT + style tables read-only into `tcc_snapshot.*` (curves/thermal = count-only) |
| `validate --run-id R --snapshot-id S` | reconcile counts + anti-joins + style-resolution into `access_validation.*` |
| `golden-capture` | Phase-1 golden capture (fail-closed, opt-in; diff deferred to Phase 2) |
| `run-all` | the full slice pipeline (freeze -> extract -> load -> inventory -> snapshot-tcc -> validate) |

The breaker/TMT slice data-loaded into `access_raw`:
`Breaker_TMTFrameSizes`, `Breaker_TMTFrameAmps`, `Breaker_TMTFrameSettings`,
`Breaker_TMTThermalTripAdj`, `BreakerMCCBStyles`, `BreakerICCBStyles`,
`BreakerPCBStyles`.  `Breaker_TMTFrameCurves` is **count-only** by default
(~1.14M rows -- its count produces the F-79-03 evidence; the data-load is not
required).  Pass `--with-curves` to data-load it anyway.

## The F-79-03 evidence (`access_validation.*`)

| table | evidence |
| --- | --- |
| `tcc_count_reconciliation` | access_raw vs tcc count + delta, all 5 TMT tables |
| `antijoin_vs_tcc` | amps numeric-normalised rating-value anti-join; curves/thermal count-only |
| `style_resolution` | the implicit-class **ambiguity** recorded as counts (single / ambiguous / no-class) |
| `style_provenance_antijoin` | the cleanly-keyable `Access ID <-> tcc source_id` per class |
| `row_count_reconciliation` | access vs harness-staging load fidelity |

## Test fence

`tests/conftest.py` HARD-FENCES the `pg` fixture to `tcc_fidelity_test` (it
asserts `current_database()` before any DDL and never touches
`tcc_fidelity_staging`).  The live F-79-03 acceptance
(`tests/test_acceptance_f79_03.py`) uses the same fence and **skips with a clear
reason** (never a silent no-op) when the DSN, the `.accdb`, or the host tcc is
absent.

## Provenance honesty (do not relax)

* The metadata path **never** uses `cursor.columns()` / `primaryKeys()` /
  `foreignKeys()` (unreliable on the ACE driver) -- see `extract.py`.
* A direct Access-surrogate -> `tcc.tmt_frames.id` join is **structurally
  forbidden** (`projection.assert_key_allowed` raises `ForbiddenKeyError`): the
  tcc surrogate is dense re-sequenced and does not preserve the Access ID.
* The row-level **frame-resolved** anti-join is a documented **deferral**: the
  tcc `size` is a computed representation that does not equal the Access
  `FrameDesc`, and the Access frame's breaker class is implicit (a `StyleID` can
  span multiple Access style classes).  That ambiguity is recorded as a count in
  `style_resolution` -- the harness never picks a class or fabricates a
  resolution.
