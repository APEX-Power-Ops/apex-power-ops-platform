# Chip 10a — Capture-Mode Import (PTM transformer → datasheet) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import an OMICRON PTM transformer test file into a records transformer datasheet — parse (banked), map to the datasheet's instrument-fillable controls, propose the values for review, and write confirmed values to `records.form_field_values` with instrument provenance — proven end-to-end on the zero-parser-risk path.

**Architecture:** A new isolated Python package `packages/records-import/` that depends on the banked `power-test-converters` (`read_ptm → PtmModel`, validated). A *pure* mapping function turns `PtmModel` into a list of `ProposedValue`s targeting `(section, row, column)` control tags; a DB layer upserts confirmed values into `form_field_values` keyed on its `UNIQUE (form_submission_id, field_key)`; an ingest entry wires file → proposal → commit. Prerequisite: a migration makes the transformer template capture-mode-aware (the import targets), since `012` predates the capture-mode contract.

**Tech Stack:** Python 3.11+, `psycopg[binary]` (Postgres `records_dev`), `pytest`, `uv`. Reuses `power_test_converters.model` dataclasses + `read_ptm`. Mapping tables are plain Python data (declarative). ASCII-only SQL output.

**Conventions (locked here):**
- `field_key` = `"<section_key>.<row_key>.<column_tag>"` for table cells; `"<section_key>.<field_tag>"` for `fields` controls. `test_group` = `<section_key>`.
- Value selection: **corrected** value where the instrument supplies temperature/standard correction; the measured value + correction factor go in `notes`.
- Provenance: `origin_device` = instrument string (e.g. `"OMICRON TESTRANO 600 / SN GH733Y"`), `measured_at` = the reading time. **Imported ⟺ `origin_device` set.** No per-value `source` enum exists; do not add one.
- Idempotency: upsert on `(form_submission_id, field_key)` — re-import replaces, never duplicates.
- Scope: nominal/as-tested measurements (the fixture's 3-per-test). Multi-tap row expansion is out of scope for 10a (note it; don't build it).

**Connection (tests):** `host=127.0.0.1 port=5432 dbname=records_dev user=postgres password=TCC_v5_2025 sslmode=disable`; psql at `C:\Program Files\PostgreSQL\18\bin\psql.exe`; env `PGSSLMODE=disable`.

**Do NOT touch** `packages/power-test-converters/` source (it has uncommitted PTM→DTAX work) — import from it read-only.

---

## Phase 1 — Make the transformer template capture-mode-aware (the import targets)

`ats_liquid_xfmr_v1` / `ats_dry_xfmr_v1` have `capture = NULL` and no `instrument_import` sections. Add the capture block + mark the PTM-fillable sections, mirroring the IT family (`015`). Pattern: a generator emits idempotent SQL (`ON CONFLICT ... DO UPDATE`), a test asserts against `records_dev`.

### Task 1: Migration generator for the xfmr capture-mode patch

**Files:**
- Create: `infra/database/migrations/records/gen_020_xfmr_capture_mode.py`
- Create (generated): `infra/database/migrations/records/020_xfmr_capture_mode.sql`
- Create: `infra/database/migrations/records/020_xfmr_capture_mode_down.sql`
- Test: `infra/database/migrations/records/test_020_xfmr_capture_mode.py`

- [ ] **Step 1: Write the failing test**

```python
# test_020_xfmr_capture_mode.py
import json, os, subprocess
import psycopg, pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
CODES = ["ats_liquid_xfmr_v1", "ats_dry_xfmr_v1"]
PTM_SECTIONS = {"turns_ratio", "winding_resistance", "power_factor", "excitation_current"}

def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run([PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
                        "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed:\n{r.stderr}\n{r.stdout}")

@pytest.fixture(scope="module")
def conn():
    _psql("020_xfmr_capture_mode_down.sql")
    _psql("020_xfmr_capture_mode.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c

def _schema(conn, code):
    fs = conn.execute("select field_schema from records.form_templates where template_code=%s and is_current", (code,)).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs

def test_capture_block_present(conn):
    for code in CODES:
        cap = _schema(conn, code).get("capture")
        assert cap and set(cap["modes"]) >= {"field", "instrument_import", "cover_attach"} and cap["default"] == "field", code

def test_ptm_sections_marked(conn):
    for code in CODES:
        secs = {s["key"]: s for s in _schema(conn, code)["sections"]}
        for k in PTM_SECTIONS:
            assert secs[k].get("capture_mode") == "instrument_import", f"{code}.{k}"
            imp = secs[k].get("import")
            assert imp and imp.get("tool") == "ptm" and imp.get("profile"), f"{code}.{k} import hint"

def test_non_ptm_sections_untouched(conn):
    # nameplate / visual_mechanical etc. must NOT be instrument_import
    for code in CODES:
        secs = {s["key"]: s for s in _schema(conn, code)["sections"]}
        assert secs["nameplate"].get("capture_mode") != "instrument_import", code

def test_reversibility(conn):
    _psql("020_xfmr_capture_mode_down.sql")
    with psycopg.connect(DSN) as c:
        cap = _schema(c, "ats_liquid_xfmr_v1").get("capture")
        assert cap is None, "down must restore capture=null"
    _psql("020_xfmr_capture_mode_down.sql"); _psql("020_xfmr_capture_mode.sql")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:RECORDS_DEV_PGPASSWORD='TCC_v5_2025'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_020_xfmr_capture_mode.py -q`
Expected: FAIL — `020_xfmr_capture_mode_down.sql: No such file or directory`.

- [ ] **Step 3: Write the generator** (mutates field_schema in-place via jsonb, idempotent)

The generator reads each template's current `field_schema`, sets `capture`, and for each of the four PTM sections sets `capture_mode` + `import`. Profiles: `turns_ratio→TX_TTR`, `winding_resistance→TX_WR`, `power_factor→TX_PF`, `excitation_current→TX_EXC`.

```python
# gen_020_xfmr_capture_mode.py
import json, os, psycopg
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "020_xfmr_capture_mode.sql")
DSN = "host=127.0.0.1 port=5432 dbname=records_dev user=postgres password=TCC_v5_2025 sslmode=disable"
CODES = ["ats_liquid_xfmr_v1", "ats_dry_xfmr_v1"]
CAPTURE = {"modes": ["field", "instrument_import", "cover_attach"], "default": "field"}
PROFILE = {"turns_ratio": "TX_TTR", "winding_resistance": "TX_WR", "power_factor": "TX_PF", "excitation_current": "TX_EXC"}

def patch(fs):
    fs = dict(fs); fs["capture"] = CAPTURE
    out = []
    for s in fs["sections"]:
        s = dict(s)
        if s["key"] in PROFILE:
            s["capture_mode"] = "instrument_import"
            s["import"] = {"tool": "ptm", "profile": PROFILE[s["key"]]}
        out.append(s)
    fs["sections"] = out
    return fs

def main():
    lines = ["-- GENERATED by gen_020_xfmr_capture_mode.py - do not edit by hand.",
             "-- Adds capture + instrument_import wiring to the xfmr templates (PTM targets).",
             "BEGIN;", "SET client_encoding TO 'UTF8';", ""]
    with psycopg.connect(DSN) as c:
        for code in CODES:
            fs = c.execute("select field_schema from records.form_templates where template_code=%s and is_current", (code,)).fetchone()[0]
            fs = json.loads(fs) if isinstance(fs, str) else fs
            payload = json.dumps(patch(fs), ensure_ascii=True, separators=(",", ":")).replace("'", "''")
            lines += [f"UPDATE records.form_templates SET field_schema='{payload}'::jsonb, updated_at=now()",
                      f"  WHERE template_code='{code}' AND is_current;", ""]
    lines.append("COMMIT;")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
```

Also create `020_xfmr_capture_mode_down.sql` (restore `capture=null` + strip the 4 sections' import wiring). Simplest correct down: re-run the original `012` template builder is overkill — instead the down strips the added keys:

```sql
-- 020_xfmr_capture_mode_down.sql
BEGIN;
UPDATE records.form_templates
SET field_schema = (field_schema - 'capture'),
    updated_at = now()
WHERE template_code IN ('ats_liquid_xfmr_v1','ats_dry_xfmr_v1') AND is_current;
-- strip capture_mode/import from the 4 PTM sections by rebuilding the sections array
UPDATE records.form_templates t
SET field_schema = jsonb_set(t.field_schema, '{sections}', (
      SELECT jsonb_agg(CASE WHEN s->>'key' IN ('turns_ratio','winding_resistance','power_factor','excitation_current')
                            THEN (s - 'capture_mode' - 'import') ELSE s END)
      FROM jsonb_array_elements(t.field_schema->'sections') s)),
    updated_at = now()
WHERE template_code IN ('ats_liquid_xfmr_v1','ats_dry_xfmr_v1') AND is_current;
COMMIT;
```

- [ ] **Step 4: Generate + run the test**

Run: `uv run --no-project python infra/database/migrations/records/gen_020_xfmr_capture_mode.py`
Then: `$env:RECORDS_DEV_PGPASSWORD='TCC_v5_2025'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_020_xfmr_capture_mode.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Update MANIFEST row 20 + commit**

Add a MANIFEST.md row 20 (one line, mirroring rows 15-19). Then:
```bash
git add infra/database/migrations/records/gen_020_xfmr_capture_mode.py infra/database/migrations/records/020_xfmr_capture_mode.sql infra/database/migrations/records/020_xfmr_capture_mode_down.sql infra/database/migrations/records/test_020_xfmr_capture_mode.py infra/database/migrations/records/MANIFEST.md
git commit -m "records Chip 10a: make xfmr templates capture-mode-aware (PTM import targets)"
```

---

## Phase 2 — Scaffold the `records-import` package

### Task 2: Package skeleton + a smoke test that imports the banked model

**Files:**
- Create: `packages/records-import/pyproject.toml`
- Create: `packages/records-import/src/records_import/__init__.py`
- Test: `packages/records-import/tests/test_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
def test_imports_banked_model():
    from power_test_converters.model import PtmModel  # banked, read-only reuse
    from records_import import __version__
    assert __version__
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests/test_smoke.py -q`
Expected: FAIL — `records_import` not found.

- [ ] **Step 3: Create the package**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "records-import"
version = "0.1.0"
description = "Capture-mode import: instrument file -> records datasheet"
requires-python = ">=3.11"
dependencies = ["power-test-converters", "psycopg[binary]>=3.1"]
[project.optional-dependencies]
test = ["pytest>=8.0.0"]
[tool.setuptools]
package-dir = {"" = "src"}
[tool.setuptools.packages.find]
where = ["src"]
```

```python
# src/records_import/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 4: Run to verify it passes**

Run the same command as Step 2. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/pyproject.toml packages/records-import/src/records_import/__init__.py packages/records-import/tests/test_smoke.py
git commit -m "records Chip 10a: scaffold records-import package"
```

---

## Phase 3 — The mapping core (pure function: PtmModel -> ProposedValue[])

### Task 3: `ProposedValue` + the `(ptm, transformer)` mapping

**Files:**
- Create: `packages/records-import/src/records_import/proposal.py` (the `ProposedValue` dataclass)
- Create: `packages/records-import/src/records_import/mappings/ptm_transformer.py`
- Test: `packages/records-import/tests/test_ptm_transformer_mapping.py`

`ProposedValue` carries everything a `form_field_values` row needs.

- [ ] **Step 1: Write the failing test** (uses `PtmModel` literals — no file)

```python
# tests/test_ptm_transformer_mapping.py
from power_test_converters.model import (
    PtmModel, PtmTransformer, PtmInstrumentInfo,
    PtmTurnsRatioTest, PtmTurnsRatioMeasurement,
    PtmWindingResistanceTest, PtmWindingResistanceMeasurement,
    PtmExcitingCurrentTest, PtmExcitingCurrentMeasurement,
    PtmPowerFactorMeasurement,
)
from pathlib import Path
from records_import.mappings.ptm_transformer import map_ptm_transformer

def _model():
    inst = PtmInstrumentInfo(test_set_name="TESTRANO 600", serial_number="GH733Y")
    tr = PtmTurnsRatioTest(source_test_id="t1", instrument=inst, measurements=[
        PtmTurnsRatioMeasurement(measured_at="2026-06-01T10:00:00", name="H-X", phase="H-X",
                                 nominal_ratio=10.0, voltage_turns_ratio=10.02, ratio_deviation=0.2),
    ])
    wr = PtmWindingResistanceTest(source_test_id="w1", instrument=inst, reference_temperature_c=75.0, measurements=[
        PtmWindingResistanceMeasurement(measured_at="2026-06-01T10:05:00", name="H", phase="H",
                                        resistance_measured_ohm=0.500, resistance_corrected_ohm=0.512),
    ])
    ex = PtmExcitingCurrentTest(source_test_id="e1", instrument=inst, measurements=[
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:00", phase="A", current_corrected_a=0.011),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:01", phase="B", current_corrected_a=0.009),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:02", phase="C", current_corrected_a=0.011),
    ])
    pf = PtmPowerFactorMeasurement(source_test_id="p1", source_test_name="Overall", measured_at="2026-06-01T10:15:00",
                                   measurement_name="ICH", measurement_type="overall", transformer_winding="",
                                   transformer_overall_capacitance="", mode="", test_frequency_hz=60.0,
                                   requested_voltage_v=10000.0, voltage_out_v=10000.0, current_measured_a=0.0,
                                   current_corrected_a=0.0, capacitance_measured_f=1.1e-9, watt_losses=0.0,
                                   power_factor_measured=0.31, power_factor_corrected=0.30, correction_factor=1.0,
                                   grade="Good", instrument=inst)
    return PtmModel(source_path=Path("x.ptm"), transformer=PtmTransformer(source_id="s"), bushings=[],
                    tap_changers=[], location=None, job=None, overall_power_factor=[pf], bushing_power_factor=[],
                    turns_ratio_tests=[tr], winding_resistance_tests=[wr], exciting_current_tests=[ex],
                    demagnetization_tests=[])

def _by_key(rows):
    return {r.field_key: r for r in rows}

def test_turns_ratio_maps_to_h_x_row():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["turns_ratio.h_x.measured_ratio"].value_numeric == 10.02
    assert rows["turns_ratio.h_x.deviation_pct"].value_numeric == 0.2

def test_winding_resistance_uses_corrected_and_temp():
    rows = _by_key(map_ptm_transformer(_model()))
    r = rows["winding_resistance.h.ohms"]
    assert r.value_numeric == 0.512 and r.unit == "ohm"
    assert "measured=0.5" in (r.notes or "")  # measured retained in notes
    assert rows["winding_resistance.h.temp"].value_numeric == 75.0

def test_excitation_phase_fields():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["excitation_current.phase_a"].value_numeric == 0.011
    assert rows["excitation_current.phase_c"].value_numeric == 0.011

def test_power_factor_ich_maps_to_ch_row():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["power_factor.ch.pf_pct"].value_numeric == 0.30

def test_every_row_carries_provenance():
    for r in map_ptm_transformer(_model()):
        assert r.origin_device and "GH733Y" in r.origin_device
        assert r.measured_at and r.value_kind == "numeric"
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests/test_ptm_transformer_mapping.py -q`
Expected: FAIL — `records_import.mappings.ptm_transformer` not found.

- [ ] **Step 3: Implement `ProposedValue` + the mapping**

```python
# src/records_import/proposal.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ProposedValue:
    field_key: str           # "<section>.<row>.<col>" | "<section>.<field>"
    test_group: str          # section key
    value_numeric: float | None = None
    value_text: str | None = None
    value_kind: str = "numeric"
    unit: str | None = None
    measured_at: str | None = None
    origin_device: str | None = None
    notes: str | None = None
```

```python
# src/records_import/mappings/ptm_transformer.py
"""Declarative (ptm, *, transformer) mapping: PtmModel -> ProposedValue[].
Targets the ats_liquid_xfmr_v1 / ats_dry_xfmr_v1 instrument_import sections (migration 020):
  turns_ratio (rows h_x/h_y/x_y), winding_resistance (rows h/x/y),
  power_factor (rows ch/cl/chl/ct/bushing), excitation_current (fields phase_a/b/c).
Nominal/as-tested only (10a); multi-tap row expansion is out of scope.
"""
from __future__ import annotations
from power_test_converters.model import PtmModel
from records_import.proposal import ProposedValue

# PTM winding-pair / measurement-name -> datasheet row key
_TTR_ROW = {"H-X": "h_x", "H-Y": "h_y", "X-Y": "x_y"}
_WR_ROW = {"H": "h", "X": "x", "Y": "y"}
_PF_ROW = {"ICH": "ch", "ICL": "cl", "ICHL": "chl", "ICT": "ct"}
_EXC_FIELD = {"A": "phase_a", "B": "phase_b", "C": "phase_c"}

def _device(inst) -> str | None:
    if inst is None:
        return None
    name = (inst.test_set_name or "OMICRON").strip()
    return f"{name} / SN {inst.serial_number}".strip(" /") if inst.serial_number else name

def map_ptm_transformer(model: PtmModel) -> list[ProposedValue]:
    out: list[ProposedValue] = []
    # turns ratio
    for test in model.turns_ratio_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            row = _TTR_ROW.get((m.name or m.phase or "").upper())
            if not row:
                continue
            for col, val in (("measured_ratio", m.voltage_turns_ratio),
                             ("deviation_pct", m.ratio_deviation),
                             ("nominal_ratio", m.nominal_ratio)):
                if val is not None:
                    out.append(ProposedValue(f"turns_ratio.{row}.{col}", "turns_ratio",
                                             value_numeric=val, measured_at=m.measured_at, origin_device=dev))
    # winding resistance (corrected; measured -> notes; ref temp)
    for test in model.winding_resistance_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            row = _WR_ROW.get((m.name or m.phase or "").upper())
            if not row:
                continue
            if m.resistance_corrected_ohm is not None:
                notes = None if m.resistance_measured_ohm is None else f"measured={m.resistance_measured_ohm} ohm (corrected to ref temp)"
                out.append(ProposedValue(f"winding_resistance.{row}.ohms", "winding_resistance",
                                         value_numeric=m.resistance_corrected_ohm, unit="ohm",
                                         measured_at=m.measured_at, origin_device=dev, notes=notes))
            if test.reference_temperature_c is not None:
                out.append(ProposedValue(f"winding_resistance.{row}.temp", "winding_resistance",
                                         value_numeric=test.reference_temperature_c, unit="degC",
                                         measured_at=m.measured_at, origin_device=dev))
    # power factor (overall + bushing); corrected PF + capacitance
    for m in (model.overall_power_factor + model.bushing_power_factor):
        row = _PF_ROW.get((m.measurement_name or "").upper())
        if not row:
            continue
        dev = _device(m.instrument)
        if m.power_factor_corrected is not None:
            out.append(ProposedValue(f"power_factor.{row}.pf_pct", "power_factor",
                                     value_numeric=m.power_factor_corrected, unit="pct",
                                     measured_at=m.measured_at, origin_device=dev))
        if m.capacitance_measured_f is not None:
            out.append(ProposedValue(f"power_factor.{row}.capacitance", "power_factor",
                                     value_numeric=m.capacitance_measured_f, unit="F",
                                     measured_at=m.measured_at, origin_device=dev))
    # excitation current (phase fields)
    for test in model.exciting_current_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            field = _EXC_FIELD.get((m.phase or "").upper())
            if field and m.current_corrected_a is not None:
                out.append(ProposedValue(f"excitation_current.{field}", "excitation_current",
                                         value_numeric=m.current_corrected_a, unit="A",
                                         measured_at=m.measured_at, origin_device=dev))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run the Step-2 command. Expected: PASS (5 tests). Fix the `_PF_ROW`/`_TTR_ROW` keys against any failing assertion (the fixture uses `ICH`/`H-X`/`H`).

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/src/records_import/proposal.py packages/records-import/src/records_import/mappings/ packages/records-import/tests/test_ptm_transformer_mapping.py
git commit -m "records Chip 10a: PtmModel -> ProposedValue mapping (transformer)"
```

---

## Phase 4 — The review proposal (mapped / unmapped / pending)

### Task 4: `build_proposal(model, field_schema)` classifies coverage

**Files:**
- Create: `packages/records-import/src/records_import/review.py`
- Test: `packages/records-import/tests/test_review_proposal.py`

A `Proposal` lists `mapped` (ProposedValue whose target tag exists in the template's instrument_import sections), `unmapped` (proposed targets not found in the schema — a mapping/template drift signal), and `pending` (instrument_import control tags in the schema that no reading filled).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_review_proposal.py
from records_import.review import build_proposal
from records_import.proposal import ProposedValue

FS = {"sections": [
    {"key": "turns_ratio", "capture_mode": "instrument_import", "kind": "table",
     "table": {"row_dim": {"rows": [{"key": "h_x"}, {"key": "h_y"}, {"key": "x_y"}]},
               "columns": [{"tag": "measured_ratio"}, {"tag": "deviation_pct"}, {"tag": "nominal_ratio"}, {"tag": "tap"}]}},
    {"key": "excitation_current", "capture_mode": "instrument_import", "kind": "fields",
     "fields": [{"tag": "phase_a"}, {"tag": "phase_b"}, {"tag": "phase_c"}, {"tag": "pattern"}]},
    {"key": "nameplate", "kind": "fields", "fields": [{"tag": "manufacturer"}]},
]}

def test_mapped_and_pending_and_unmapped():
    proposed = [
        ProposedValue("turns_ratio.h_x.measured_ratio", "turns_ratio", value_numeric=10.0),
        ProposedValue("excitation_current.phase_a", "excitation_current", value_numeric=0.01),
        ProposedValue("turns_ratio.z_z.measured_ratio", "turns_ratio", value_numeric=1.0),  # bad row -> unmapped
    ]
    p = build_proposal(proposed, FS)
    keys = {v.field_key for v in p.mapped}
    assert "turns_ratio.h_x.measured_ratio" in keys and "excitation_current.phase_a" in keys
    assert [v.field_key for v in p.unmapped] == ["turns_ratio.z_z.measured_ratio"]
    # pending = declared instrument_import targets not filled (e.g. phase_b, deviation_pct, ...) but NOT nameplate.manufacturer
    assert "excitation_current.phase_b" in p.pending and "turns_ratio.h_x.deviation_pct" in p.pending
    assert "nameplate.manufacturer" not in p.pending
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests/test_review_proposal.py -q`
Expected: FAIL — `records_import.review` not found.

- [ ] **Step 3: Implement**

```python
# src/records_import/review.py
from __future__ import annotations
from dataclasses import dataclass, field
from records_import.proposal import ProposedValue

@dataclass
class Proposal:
    mapped: list[ProposedValue] = field(default_factory=list)
    unmapped: list[ProposedValue] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)

def _instrument_target_keys(field_schema: dict) -> set[str]:
    keys: set[str] = set()
    for s in field_schema.get("sections", []):
        if s.get("capture_mode") != "instrument_import":
            continue
        sk = s["key"]
        if s.get("kind") == "table":
            tbl = s.get("table", {})
            rows = [r["key"] for r in tbl.get("row_dim", {}).get("rows", [])]
            cols = [c["tag"] for c in tbl.get("columns", []) if c.get("tag") not in (None, "tap")]
            for r in rows:
                for c in cols:
                    keys.add(f"{sk}.{r}.{c}")
        else:
            for f in s.get("fields", []):
                keys.add(f"{sk}.{f['tag']}")
    return keys

def build_proposal(proposed: list[ProposedValue], field_schema: dict) -> Proposal:
    targets = _instrument_target_keys(field_schema)
    p = Proposal()
    filled: set[str] = set()
    for v in proposed:
        if v.field_key in targets:
            p.mapped.append(v); filled.add(v.field_key)
        else:
            p.unmapped.append(v)
    p.pending = sorted(targets - filled)
    return p
```

- [ ] **Step 4: Run to verify it passes** — Step-2 command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/src/records_import/review.py packages/records-import/tests/test_review_proposal.py
git commit -m "records Chip 10a: review proposal (mapped/unmapped/pending)"
```

---

## Phase 5 — DB layer: read schema, upsert form_field_values (idempotent)

### Task 5: `db.py` — load a submission's template schema + upsert confirmed values

**Files:**
- Create: `packages/records-import/src/records_import/db.py`
- Test: `packages/records-import/tests/test_db_write.py` (integration; hits `records_dev`)

- [ ] **Step 1: Write the failing test** (creates a throwaway asset + submission, writes, asserts, re-writes idempotent, tears down)

```python
# tests/test_db_write.py
import os, uuid, psycopg, pytest
from records_import.proposal import ProposedValue
from records_import import db

PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"

@pytest.fixture()
def submission():
    with psycopg.connect(DSN, autocommit=True) as c:
        cls = c.execute("select asset_class_id from records.asset_classes where class_code='xfmr_liquid'").fetchone()[0]
        tpl = c.execute("select template_id from records.form_templates where template_code='ats_liquid_xfmr_v1' and is_current").fetchone()[0]
        aid = uuid.uuid4(); sid = uuid.uuid4()
        c.execute("insert into records.assets (asset_id, asset_class_id, name) values (%s,%s,'TEST-IMPORT-XFMR')", (aid, cls))
        c.execute("insert into records.form_submissions (form_submission_id, template_id, asset_id) values (%s,%s,%s)", (sid, tpl, aid))
        yield sid
        c.execute("delete from records.assets where asset_id=%s", (aid,))  # cascades submission + values

def _rows(c, sid):
    return {r[0]: r for r in c.execute(
        "select field_key, value_numeric, unit, origin_device, test_group from records.form_field_values where form_submission_id=%s", (sid,)).fetchall()}

def test_upsert_writes_and_is_idempotent(submission):
    pv = [ProposedValue("winding_resistance.h.ohms", "winding_resistance", value_numeric=0.512, unit="ohm",
                        origin_device="TESTRANO 600 / SN GH733Y", measured_at="2026-06-01T10:00:00")]
    db.write_values(DSN, submission, pv)
    db.write_values(DSN, submission, pv)  # second time must not duplicate
    with psycopg.connect(DSN) as c:
        rows = _rows(c, submission)
        assert rows["winding_resistance.h.ohms"][1] == 0.512
        assert rows["winding_resistance.h.ohms"][3] == "TESTRANO 600 / SN GH733Y"
        cnt = c.execute("select count(*) from records.form_field_values where form_submission_id=%s and field_key='winding_resistance.h.ohms'", (submission,)).fetchone()[0]
        assert cnt == 1, "idempotent upsert"

def test_load_field_schema(submission):
    fs = db.load_submission_schema(DSN, submission)
    assert any(s["key"] == "winding_resistance" for s in fs["sections"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:RECORDS_DEV_PGPASSWORD='TCC_v5_2025'; uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests/test_db_write.py -q`
Expected: FAIL — `records_import.db` has no `write_values`.

- [ ] **Step 3: Implement**

```python
# src/records_import/db.py
from __future__ import annotations
import json
import psycopg
from records_import.proposal import ProposedValue

def load_submission_schema(dsn: str, submission_id) -> dict:
    with psycopg.connect(dsn) as c:
        fs = c.execute(
            "select t.field_schema from records.form_submissions s "
            "join records.form_templates t on t.template_id = s.template_id "
            "where s.form_submission_id = %s", (submission_id,)).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs

def write_values(dsn: str, submission_id, values: list[ProposedValue]) -> int:
    sql = (
        "insert into records.form_field_values "
        "(form_submission_id, field_key, test_group, value_kind, value_numeric, value_text, unit, measured_at, origin_device, notes) "
        "values (%(sid)s, %(field_key)s, %(test_group)s, %(value_kind)s, %(value_numeric)s, %(value_text)s, %(unit)s, %(measured_at)s, %(origin_device)s, %(notes)s) "
        "on conflict (form_submission_id, field_key) do update set "
        "value_kind=excluded.value_kind, value_numeric=excluded.value_numeric, value_text=excluded.value_text, "
        "unit=excluded.unit, measured_at=excluded.measured_at, origin_device=excluded.origin_device, "
        "test_group=excluded.test_group, notes=excluded.notes, updated_at=now()")
    n = 0
    with psycopg.connect(dsn, autocommit=True) as c:
        for v in values:
            c.execute(sql, {"sid": submission_id, "field_key": v.field_key, "test_group": v.test_group,
                            "value_kind": v.value_kind, "value_numeric": v.value_numeric, "value_text": v.value_text,
                            "unit": v.unit, "measured_at": v.measured_at, "origin_device": v.origin_device, "notes": v.notes})
            n += 1
    return n
```

- [ ] **Step 4: Run to verify it passes** — Step-2 command. Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/src/records_import/db.py packages/records-import/tests/test_db_write.py
git commit -m "records Chip 10a: db layer - load schema + idempotent upsert"
```

---

## Phase 6 — Ingest entry: file -> proposal -> commit (end-to-end)

### Task 6: `ingest.py` ties it together + an integration test on a real `.ptm`

**Files:**
- Create: `packages/records-import/src/records_import/ingest.py`
- Create: `packages/records-import/tests/conftest.py` (copies the converter's `_write_sample_ptm` helper so the integration test has a real `.ptm` — do NOT import the converter's private test module)
- Test: `packages/records-import/tests/test_ingest_end_to_end.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ingest_end_to_end.py
import os, uuid, psycopg, pytest
from records_import import ingest
from tests.conftest import write_sample_ptm   # the copied helper

PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"

@pytest.fixture()
def submission():
    with psycopg.connect(DSN, autocommit=True) as c:
        cls = c.execute("select asset_class_id from records.asset_classes where class_code='xfmr_liquid'").fetchone()[0]
        tpl = c.execute("select template_id from records.form_templates where template_code='ats_liquid_xfmr_v1' and is_current").fetchone()[0]
        aid = uuid.uuid4(); sid = uuid.uuid4()
        c.execute("insert into records.assets (asset_id, asset_class_id, name) values (%s,%s,'TEST-INGEST')", (aid, cls))
        c.execute("insert into records.form_submissions (form_submission_id, template_id, asset_id) values (%s,%s,%s)", (sid, tpl, aid))
        yield sid
        c.execute("delete from records.assets where asset_id=%s", (aid,))

def test_dry_run_proposes_without_writing(tmp_path, submission):
    ptm = write_sample_ptm(tmp_path)
    proposal = ingest.propose(DSN, submission, ptm)            # parse+map+classify, NO write
    assert proposal.mapped and "winding_resistance.h.ohms" in {v.field_key for v in proposal.mapped}
    with psycopg.connect(DSN) as c:
        assert c.execute("select count(*) from records.form_field_values where form_submission_id=%s", (submission,)).fetchone()[0] == 0

def test_commit_writes_mapped_and_is_idempotent(tmp_path, submission):
    ptm = write_sample_ptm(tmp_path)
    proposal = ingest.propose(DSN, submission, ptm)
    n1 = ingest.commit(DSN, submission, proposal)
    n2 = ingest.commit(DSN, submission, proposal)
    assert n1 == n2 and n1 == len(proposal.mapped)
    with psycopg.connect(DSN) as c:
        total = c.execute("select count(*) from records.form_field_values where form_submission_id=%s", (submission,)).fetchone()[0]
        assert total == len(proposal.mapped)                   # partial fill: only mapped, no phantom
        dev = c.execute("select origin_device from records.form_field_values where form_submission_id=%s limit 1", (submission,)).fetchone()[0]
        assert "GH733Y" in dev
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:RECORDS_DEV_PGPASSWORD='TCC_v5_2025'; uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests/test_ingest_end_to_end.py -q`
Expected: FAIL — `records_import.ingest`/`conftest.write_sample_ptm` missing.

- [ ] **Step 3: Create the fixture helper + the ingest entry**

For `conftest.py`: open `packages/power-test-converters/tests/test_ptm_to_dtax.py`, copy the `_write_sample_ptm` helper (and any private helpers it calls) verbatim into `packages/records-import/tests/conftest.py`, renamed `write_sample_ptm` (public). This duplicates a *test fixture* (allowed) without touching the converter source.

```python
# src/records_import/ingest.py
from __future__ import annotations
from power_test_converters.ptm import read_ptm
from records_import.mappings.ptm_transformer import map_ptm_transformer
from records_import.review import build_proposal, Proposal
from records_import import db

def propose(dsn: str, submission_id, ptm_path) -> Proposal:
    model = read_ptm(ptm_path)
    proposed = map_ptm_transformer(model)
    schema = db.load_submission_schema(dsn, submission_id)
    return build_proposal(proposed, schema)

def commit(dsn: str, submission_id, proposal: Proposal) -> int:
    return db.write_values(dsn, submission_id, proposal.mapped)
```

- [ ] **Step 4: Run to verify it passes** — Step-2 command. Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/src/records_import/ingest.py packages/records-import/tests/conftest.py packages/records-import/tests/test_ingest_end_to_end.py
git commit -m "records Chip 10a: ingest entry - propose (dry-run) + commit, end-to-end on a real .ptm"
```

---

## Phase 7 — Reconcile: docs, MANIFEST, PUNCHLIST, PR

### Task 7: As-built doc + land the slice

**Files:**
- Create: `reference/records/15-CHIP10A-AS-BUILT.md` (one page: what shipped, the field_key convention, the provenance convention, the §11 resolutions, what's deferred — multi-tap, DTAX/CTA, the UI)
- Modify: `reference/records/PUNCHLIST.md` (Chip 10 → 10a DONE, 10b next), `infra/database/migrations/records/MANIFEST.md` (note migration 020)
- Modify: `reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md` (mark §10 build-step 10a DONE)

- [ ] **Step 1:** Run the whole records-import suite green:

`uv run --no-project --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import pytest packages/records-import/tests -q` → all PASS.

- [ ] **Step 2:** Write the as-built doc + update PUNCHLIST/MANIFEST/spec (concise).
- [ ] **Step 3:** Commit + push a `records/chip10a-import` branch + open a PR (title `records Chip 10a: capture-mode import vertical slice (PTM transformer)`), body summarizing the slice + that it's dev-only on `records_dev`.

```bash
git add reference/records/15-CHIP10A-AS-BUILT.md reference/records/PUNCHLIST.md reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md infra/database/migrations/records/MANIFEST.md
git commit -m "records Chip 10a: as-built doc + tracker reconcile"
git push -u origin records/chip10a-import
```

---

## Notes / deferred (not in 10a)

- **Multi-tap row expansion** — 10a maps nominal/as-tested measurements to the fixed rows; tap-series → multiple rows is a follow-up.
- **DTAX-read (10c) / CTA (10d)** — additive mapping tables + parsers keyed `(dtax|cta, *, family)`; same engine.
- **Review-gate UI (10b)** — this slice exposes `propose()`/`commit()` as a library; the office surface wires them.
- **Acceptance/assessment** — the importer supplies readings only; pass/fail vs `tolerance_source` is computed elsewhere (spec §7). `assessment` stays default.
- **Identity match (10e)** — 10a takes an explicit `submission_id`; serial/work-order routing is later.
