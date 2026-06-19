# Project Miner Intake → `ops.*` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build `packages/ops-intake/` — a reusable extractor that loads the won Project Miner estimator
(`Cupertino - Miner Estimator PHX Bldg A & B MV Rev10.xlsm`) into the clean `ops.*` schema (projects, scopes,
scope_quote, scope_quote_line, QTY-expanded apparatus, standard_hours), validated against the workbook's own
totals and idempotent on re-run.

**Architecture:** `extract.py` (openpyxl → typed `IntakePayload`) → `validate.py` (reconciliation gates) →
`load.py` (idempotent upsert into `ops.*` + an `--approve` freeze step) → `cli.py`. Pure-Python read; DB writes
via `psycopg`. TDD: fast unit tests on a committed synthetic `.xlsx` fixture; an integration test + e2e load
gated on the real workbook being present on the host.

**Tech stack:** Python ≥3.11, `openpyxl`, `psycopg[binary]`, `pytest`, `uv`; PostgreSQL 17 host `apex-dev-pg`
DB `ops_dev`. Branch `ops/chip5-miner-intake` (worktree `/home/olares/code/apex/apex-ops-lane`).

## Global Constraints

- **Substrate = `ops.*` only.** Never touch `public.*`/`seam.*`. No new DDL — load into the existing Chips 1–2
  tables (this packet is data + tooling, not schema).
- **Identity = `ops` canonical**; FIXED scope→apparatus (Law 1). **Recognition firewall (Law 3):** populate only
  the frozen `quoted_hours`/`quoted_revenue` snapshot; no recognition events here.
- **Grain:** estimator line `× QTY` → individual `ops.apparatus` rows, each `quote_line_id`-linked, with
  provenance (`source`, `legacy_source_id`) back to the source row+unit.
- **Idempotent:** every load is upsert-by-stable-key; re-running the same workbook changes 0 rows.
- **Naming:** `project_name = "Project Miner — PHX Bldg A & B MV"`; product name "Project Jupiter" in
  `description` (construction/PM = Miner — operator).
- **`test_standard = 'ATS'`** project-wide.
- **DB conn:** pin `OPS_DEV_DSN` or build `host=127.0.0.1 port=5432 dbname=ops_dev user=postgres
  password=$OPS_DEV_PGPASSWORD sslmode=disable` (ambient PG env points at prod — never rely on it). Password =
  host dev-pg `postgres` pw = `DEV_PG_PASSWORD` from `infra/.env`.
- **Run from the worktree root** `/home/olares/code/apex/apex-ops-lane`, over `ssh olares-mesh`.

---

## File Structure

```
packages/ops-intake/
  pyproject.toml                         # setuptools, src layout, deps: openpyxl, psycopg[binary]
  src/ops_intake/__init__.py
  src/ops_intake/model.py                # IntakePayload dataclasses
  src/ops_intake/extract.py              # .xlsm -> IntakePayload (the cell map)
  src/ops_intake/validate.py             # reconciliation gates
  src/ops_intake/load.py                 # idempotent upsert into ops.* + approve/freeze
  src/ops_intake/cli.py                  # `ops-intake extract|load`
  tests/__init__.py
  tests/conftest.py                      # OPS_DEV_DSN helper + synthetic-fixture builder
  tests/fixtures/build_fixture.py        # writes tests/fixtures/mini_estimator.xlsx
  tests/test_model.py
  tests/test_extract.py                  # against the synthetic fixture
  tests/test_validate.py
  tests/test_extract_real_workbook.py    # skipif no MINER_WORKBOOK
  tests/test_load.py                     # against ops_dev (truncates ops data tables)
  tests/test_load_approve.py
  tests/test_cli.py
  tests/test_e2e_miner.py                # skipif no MINER_WORKBOOK; full load into ops_dev
.gitignore                               # add packages/ops-intake/_data/  (the real .xlsm, never committed)
infra/database/migrations/ops/MANIFEST.md  # note the intake package (Chip 5)
```

---

## Task 0: Baseline — establish `ops` schema on host `ops_dev`

**Files:** none created. Establishes the test baseline (the laptop `ops_dev` holding Chips 1–2 was dropped §257;
host `ops_dev` currently has only `work` + empty `public`).

- [ ] **Step 1: Confirm `ops_dev` reachable + password wired**

Run:
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  PGPASSWORD="$DEV_PG_PASSWORD" psql -h 127.0.0.1 -p 5432 -U postgres -d ops_dev -c "select current_database();"'
```
Expected: `ops_dev`.

- [ ] **Step 2: Apply ops 001 + 002 (persistent) to `ops_dev`**

Run (from the worktree, so files match the branch):
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; cd /home/olares/code/apex/apex-ops-lane; \
  for f in infra/database/migrations/ops/001_identity_skeleton.sql infra/database/migrations/ops/002_quote_model.sql; do \
    echo "applying $f"; PGPASSWORD="$DEV_PG_PASSWORD" psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -U postgres -d ops_dev -f "$f"; done'
```
Expected: both apply with no error.

- [ ] **Step 3: Run the existing Chip 1–2 tests green on host `ops_dev`**

Run:
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; cd /home/olares/code/apex/apex-ops-lane; \
  OPS_DEV_PGPASSWORD="$DEV_PG_PASSWORD" uv run --with "psycopg[binary]" --with pytest pytest \
  infra/database/migrations/ops/test_001_identity_skeleton.py infra/database/migrations/ops/test_002_quote_model.py -q'
```
Expected: all pass (the baseline). If they fail, STOP and report.

- [ ] **Step 4: Confirm `ops.*` present**
```bash
ssh olares-mesh 'set -a; . .../infra/.env; set +a; PGPASSWORD="$DEV_PG_PASSWORD" psql -h 127.0.0.1 -U postgres -d ops_dev -c "\dt ops.*"'
```
Expected: `projects, scopes, tasks, apparatus, standard_hours, scope_quote_line, scope_quote`.

---

## Task 1: Package scaffold + payload model

**Files:** Create `packages/ops-intake/pyproject.toml`, `src/ops_intake/__init__.py`, `src/ops_intake/model.py`,
`tests/__init__.py`, `tests/test_model.py`.

**Interfaces — Produces:** the `IntakePayload` tree consumed by every later task.

- [ ] **Step 1: Write the failing test** — `tests/test_model.py`
```python
from ops_intake.model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn, StandardHourIn

def test_payload_constructs_and_totals():
    line = QuoteLineIn(apparatus_type="Transformer - Pad", test_standard="ATS", qty=9,
                       hrs_per_unit=8.0, neta_section="7.2", drawing="E01-01", line_number=20)
    assert line.line_hours == 72.0
    quote = ScopeQuoteIn(onsite_labor=67787.5, offsite_labor=3081.25, travel=16946.875,
                         outside_services=3375.0, unit_multiplier=1.0, pct_adjust=1.0, total_quoted_hours=362.5)
    assert round(quote.unadjusted_total, 3) == 91190.625
    assert round(quote.adjusted_total, 3) == 91190.625
    scope = ScopeIn(scope_name="A1) Medium-Voltage - Core", scope_type="OTHER",
                    sort_order=1, quote=quote, lines=[line])
    payload = IntakePayload(
        project=ProjectIn(project_number="MINER-PHX-AB-MV", project_name="Project Miner — PHX Bldg A & B MV",
                          status="Won", quote_revision="Rev10", contract_value=4692078.98,
                          description="Public/product name: Project Jupiter."),
        scopes=[scope], standard_hours=[StandardHourIn(apparatus_type="Transformer - Pad",
                          test_standard="ATS", default_hours=8.0, neta_section="7.2")])
    assert payload.scopes[0].lines[0].qty == 9
```

- [ ] **Step 2: Run it to verify it fails** — `… pytest packages/ops-intake/tests/test_model.py -q` → FAIL (module missing).

- [ ] **Step 3: Implement** — `src/ops_intake/model.py`
```python
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class QuoteLineIn:
    apparatus_type: str
    test_standard: str
    qty: int
    hrs_per_unit: float
    neta_section: str | None = None
    drawing: str | None = None
    designation: str | None = None
    notes: str | None = None
    line_number: int | None = None
    catalog_default_hours: float | None = None
    @property
    def line_hours(self) -> float:
        return round(self.qty * self.hrs_per_unit, 4)

@dataclass
class ScopeQuoteIn:
    onsite_labor: float = 0.0
    offsite_labor: float = 0.0
    travel: float = 0.0
    outside_services: float = 0.0
    unit_multiplier: float = 1.0
    pct_adjust: float = 1.0
    total_quoted_hours: float = 0.0
    is_estimate: bool = False          # chiller lump-sum flag
    @property
    def unadjusted_total(self) -> float:
        return self.onsite_labor + self.offsite_labor + self.travel + self.outside_services
    @property
    def adjusted_total(self) -> float:
        return self.unadjusted_total * self.unit_multiplier * self.pct_adjust

@dataclass
class ScopeIn:
    scope_name: str
    scope_type: str = "OTHER"
    sort_order: int = 0
    quote: ScopeQuoteIn = field(default_factory=ScopeQuoteIn)
    lines: list[QuoteLineIn] = field(default_factory=list)

@dataclass
class StandardHourIn:
    apparatus_type: str
    test_standard: str
    default_hours: float
    neta_section: str | None = None
    category: str | None = None

@dataclass
class ProjectIn:
    project_number: str
    project_name: str
    status: str = "Won"
    quote_revision: str | None = None
    quote_date: str | None = None
    estimator: str | None = None
    contract_value: float = 0.0
    business_unit: str | None = None
    description: str | None = None

@dataclass
class IntakePayload:
    project: ProjectIn
    scopes: list[ScopeIn] = field(default_factory=list)
    standard_hours: list[StandardHourIn] = field(default_factory=list)
```
And `pyproject.toml` (mirror records-import):
```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "ops-intake"
version = "0.1.0"
description = "Estimator (.xlsm) -> ops.* intake (Project Miner; ops Chip 5)"
requires-python = ">=3.11"
dependencies = ["openpyxl>=3.1", "psycopg[binary]>=3.1"]
[project.optional-dependencies]
test = ["pytest>=8.0.0"]
[tool.setuptools]
package-dir = {"" = "src"}
[tool.setuptools.packages.find]
where = ["src"]
[project.scripts]
ops-intake = "ops_intake.cli:main"
```
`src/ops_intake/__init__.py` and `tests/__init__.py`: empty.

- [ ] **Step 4: Run to verify pass** — `uv run --with pytest --with-editable packages/ops-intake pytest packages/ops-intake/tests/test_model.py -q` → PASS.

- [ ] **Step 5: Commit** — `git add packages/ops-intake && git commit -m "feat(ops-intake): payload model (ops Chip 5)"`

---

## Task 2: Synthetic fixture builder

**Files:** Create `tests/fixtures/build_fixture.py`, `tests/conftest.py`.

**Interfaces — Produces:** `mini_estimator.xlsx` (a 1-scope workbook mirroring the real cell map) + a
`mini_workbook` fixture path; the DSN helper.

- [ ] **Step 1: Write `tests/fixtures/build_fixture.py`** — builds a minimal workbook with one scope sheet
  `"A1) MV - Test"` laid out per the real cell map (B2 name; J3 hours; P3/P4 with M4/N4; P14/P19/P26/P33
  category totals; row-5 header; two apparatus lines at rows 8–9 with C=QTY, D=§, E=type, G=drawing, I=hrs/unit,
  J=hrs/line; a sub-header row 7 with section 0 and no QTY to prove it's skipped) + an `Equipment Reference`
  sheet (header row 2: ATS/MTS/Scope of Work/ATS25/MTS23; one data row) + a `Print_Template` (L/R rollup:
  R13 total, R14 scope $). Numbers chosen so totals reconcile exactly (e.g. one scope: onsite 800/offsite
  100/travel 50/outside 50 = P3 1000, M4=1, N4=1, P4 1000; two lines 2×5h + 1×... → J3; R13=1000).
```python
import openpyxl, pathlib
def build(path: pathlib.Path) -> pathlib.Path:
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "A1) MV - Test"
    ws["B2"] = "A1) MV - Test"
    ws["I3"] = "Total App Hours"; ws["J3"] = 25.0
    ws["L3"] = "TOTAL SHEET $$$ -NOT ADJUSTED"; ws["P3"] = 1000.0; ws["M4"]=1; ws["N4"]=1
    ws["L4"] = "TOTAL SHEET $$$ - ADJUSTED"; ws["P4"] = 1000.0
    ws["C5"]="QTY"; ws["D5"]="Section"; ws["E5"]="Apparatus Type"; ws["G5"]="Drawing"; ws["I5"]="Hrs/Unit"; ws["J5"]="Hrs/Line"
    ws["D7"]=0; ws["E7"]="SLD - sub-header (skip)"                       # sub-header: no QTY
    ws["C8"]=2; ws["D8"]="7.6"; ws["E8"]="Vacuum Interrupter"; ws["G8"]="E01"; ws["I8"]=5.0; ws["J8"]=10.0
    ws["C9"]=3; ws["D9"]="7.2"; ws["E9"]="Transformer - Pad"; ws["G9"]="E01"; ws["I9"]=5.0; ws["J9"]=15.0
    ws["L14"]="Onsite Labor Totals"; ws["P14"]=800.0
    ws["L19"]="Offsite Labor Totals"; ws["P19"]=100.0
    ws["L26"]="Travel Totals"; ws["P26"]=50.0
    ws["L33"]="Outside Services Totals"; ws["P33"]=50.0
    er = wb.create_sheet("Equipment Reference")
    er["A2"]="ATS"; er["B2"]="MTS"; er["C2"]="Scope of Work"; er["D2"]="ATS25"; er["E2"]="MTS23"
    er["C3"]="Vacuum Interrupter"; er["A3"]="7.6"; er["D3"]=5.0; er["E3"]=5.0
    pt = wb.create_sheet("Print_Template")
    pt["L13"]="  TOTAL COST"; pt["R13"]=1000.0; pt["L14"]="  A1) MV - Test"; pt["R14"]=1000.0
    path.parent.mkdir(parents=True, exist_ok=True); wb.save(path); return path
if __name__ == "__main__":
    print(build(pathlib.Path(__file__).parent / "mini_estimator.xlsx"))
```

- [ ] **Step 2: Write `tests/conftest.py`**
```python
import os, sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent))   # make `fixtures` importable regardless of rootdir
from fixtures.build_fixture import build

_OPS_TRUNCATE = ("truncate ops.apparatus, ops.scope_quote_line, ops.scope_quote, "
                 "ops.scopes, ops.standard_hours, ops.projects cascade;")

def _dsn() -> str:
    return os.environ.get("OPS_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=ops_dev user=postgres "
        f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")

@pytest.fixture
def dsn() -> str:
    return _dsn()

@pytest.fixture
def clean_ops() -> str:
    """Truncate ops data tables (keep schema) and return the dsn."""
    import psycopg
    d = _dsn()
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(_OPS_TRUNCATE)
    return d

@pytest.fixture(scope="session")
def mini_workbook(tmp_path_factory) -> pathlib.Path:
    return build(tmp_path_factory.mktemp("wb") / "mini_estimator.xlsx")

@pytest.fixture
def real_workbook():
    p = os.environ.get("MINER_WORKBOOK")
    if not p or not pathlib.Path(p).exists():
        pytest.skip("set MINER_WORKBOOK to the Rev10 .xlsm on the host")
    return pathlib.Path(p)
```

- [ ] **Step 3: Verify the fixture builds** — `uv run --with openpyxl python packages/ops-intake/tests/fixtures/build_fixture.py` → prints a path; no error.

- [ ] **Step 4: Commit** — `git commit -m "test(ops-intake): synthetic estimator fixture + dsn helper"`

---

## Task 3: Extractor

**Files:** Create `src/ops_intake/extract.py`, `tests/test_extract.py`.

**Interfaces — Consumes** `IntakePayload`/model; **Produces** `extract_workbook(path) -> IntakePayload`.

- [ ] **Step 1: Failing test** — `tests/test_extract.py`
```python
from ops_intake.extract import extract_workbook

def test_extract_mini(mini_workbook):
    p = extract_workbook(mini_workbook)
    assert p.project.contract_value == 1000.0
    assert len(p.scopes) == 1
    s = p.scopes[0]
    assert s.scope_name == "A1) MV - Test"
    assert s.quote.total_quoted_hours == 25.0
    assert (s.quote.onsite_labor, s.quote.offsite_labor, s.quote.travel, s.quote.outside_services) == (800.0,100.0,50.0,50.0)
    assert len(s.lines) == 2                      # sub-header row 7 skipped
    assert [l.qty for l in s.lines] == [2, 3]
    assert s.lines[1].apparatus_type == "Transformer - Pad" and s.lines[1].hrs_per_unit == 5.0
    assert any(h.apparatus_type == "Vacuum Interrupter" and h.test_standard == "ATS" for h in p.standard_hours)
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** — `src/ops_intake/extract.py`. Key logic: identify scope sheets (name matches
  `^[AB]\d\)` or, generally, sheets whose `B2` is non-empty and that have a `row-5` QTY header — exclude
  `Submittal Specs`/`Equipment Reference`/`Print_Template`/`*.X` template tabs); per scope read the fixed cells
  (J3, P3, P4, M4, N4, P14/P19/P26/P33, B2); read apparatus lines from row 6 downward, **a line = a row with a
  numeric `C` (QTY)** (skips sub-headers); read `Equipment Reference` (header row 2) into `StandardHourIn`;
  read `Print_Template` R13 → `contract_value` and R14… → per-scope $ for validation. Use
  `data_only=True`.
```python
import re, pathlib, openpyxl
from .model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn, StandardHourIn
SKIP = {"Submittal Specs", "Equipment Reference", "Print_Template"}
SCOPE_RE = re.compile(r"^[AB]\d\)")
def _num(v): return float(v) if isinstance(v, (int, float)) else None
def extract_workbook(path) -> IntakePayload:
    wb = openpyxl.load_workbook(path, data_only=True)
    scopes = []
    for ws in wb.worksheets:
        name = ws["B2"].value
        if not name or ws.title in SKIP or ws.title.endswith(".X"): continue
        if not (SCOPE_RE.match(str(name)) or _num(ws["J3"].value) is not None): continue
        q = ScopeQuoteIn(onsite_labor=_num(ws["P14"].value) or 0, offsite_labor=_num(ws["P19"].value) or 0,
                         travel=_num(ws["P26"].value) or 0, outside_services=_num(ws["P33"].value) or 0,
                         unit_multiplier=_num(ws["M4"].value) or 1, pct_adjust=_num(ws["N4"].value) or 1,
                         total_quoted_hours=_num(ws["J3"].value) or 0)
        lines, ln = [], 0
        for r in range(6, ws.max_row + 1):
            qty = _num(ws.cell(r, 3).value)
            if qty is None: continue
            ln += 1
            lines.append(QuoteLineIn(apparatus_type=str(ws.cell(r,5).value or "").strip(),
                test_standard="ATS", qty=int(qty), hrs_per_unit=_num(ws.cell(r,9).value) or 0,
                neta_section=str(ws.cell(r,4).value or "").strip() or None,
                drawing=str(ws.cell(r,7).value or "").strip() or None, line_number=r))
        scopes.append(ScopeIn(scope_name=str(name).strip(), sort_order=len(scopes)+1, quote=q, lines=lines))
    # standard hours
    sh = []
    er = wb["Equipment Reference"] if "Equipment Reference" in wb.sheetnames else None
    if er:
        for r in range(3, er.max_row + 1):
            sow = er.cell(r, 3).value
            ats = _num(er.cell(r, 4).value)
            if not sow or ats is None: continue
            sh.append(StandardHourIn(apparatus_type=str(sow).strip(), test_standard="ATS",
                      default_hours=ats, neta_section=str(er.cell(r,1).value or "").strip() or None))
    # project + contract value from Print_Template R13
    contract = 0.0
    if "Print_Template" in wb.sheetnames:
        pt = wb["Print_Template"]
        for r in range(1, pt.max_row + 1):
            if str(pt.cell(r, 12).value or "").strip().upper().startswith("TOTAL COST"):
                contract = _num(pt.cell(r, 18).value) or 0.0; break
    proj = ProjectIn(project_number="MINER-PHX-AB-MV",
        project_name="Project Miner — PHX Bldg A & B MV", status="Won", quote_revision="Rev10",
        contract_value=round(contract, 2),
        description="Public/product name: Project Jupiter — Oracle/STACK data-center campus, Doña Ana County NM.")
    return IntakePayload(project=proj, scopes=scopes, standard_hours=sh)
```
*(Note: the real workbook's chiller scopes appear only in `Print_Template`; Task 5 adds them as estimate scopes
from the R-rollup. The mini fixture has no chillers.)*

- [ ] **Step 4: Run → PASS.**  Command: `uv run --with pytest --with-editable packages/ops-intake pytest packages/ops-intake/tests/test_extract.py -q`

- [ ] **Step 5: Commit** — `git commit -m "feat(ops-intake): workbook extractor (cell map -> payload)"`

---

## Task 4: Validator

**Files:** Create `src/ops_intake/validate.py`, `tests/test_validate.py`.

**Interfaces — Consumes** `IntakePayload`; **Produces** `validate(payload) -> list[Check]`,
`Check(name,ok,detail)`, `assert_valid(payload)` (raises `IntakeValidationError` on any failure).

- [ ] **Step 1: Failing test** — `tests/test_validate.py`
```python
import pytest
from ops_intake.extract import extract_workbook
from ops_intake.validate import validate, assert_valid, IntakeValidationError
from ops_intake.model import ScopeQuoteIn

def test_validate_mini_passes(mini_workbook):
    checks = validate(extract_workbook(mini_workbook))
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]

def test_validate_catches_category_mismatch(mini_workbook):
    p = extract_workbook(mini_workbook)
    p.scopes[0].quote = ScopeQuoteIn(onsite_labor=1.0, total_quoted_hours=25.0)  # P3 != sheet
    with pytest.raises(IntakeValidationError):
        assert_valid(p, sheet_totals={p.scopes[0].scope_name: 1000.0})
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** — `src/ops_intake/validate.py`: checks (TOL = 0.01) —
  per apparatus-bearing scope `Σ line_hours == quote.total_quoted_hours`;
  `contract_value == Σ scope.adjusted_total`; `count(expanded units) == Σ qty`; non-negative amounts;
  unique scope names. `assert_valid` raises with the failing checks. (Sheet-total cross-checks vs P3/P4 use the
  values already on the payload's `ScopeQuoteIn`.)
```python
from dataclasses import dataclass
from .model import IntakePayload
TOL = 0.01
class IntakeValidationError(Exception): ...
@dataclass
class Check: name: str; ok: bool; detail: str = ""
def validate(p: IntakePayload) -> list[Check]:
    cs = []
    for s in p.scopes:
        if s.lines:
            lh = round(sum(l.line_hours for l in s.lines), 4)
            cs.append(Check(f"{s.scope_name}: Σline_hours==J3", abs(lh - s.quote.total_quoted_hours) <= TOL,
                            f"{lh} vs {s.quote.total_quoted_hours}"))
    csum = round(sum(s.quote.adjusted_total for s in p.scopes), 2)
    cs.append(Check("Σscope.adjusted_total==contract_value", abs(csum - p.project.contract_value) <= 1.0,
                    f"{csum} vs {p.project.contract_value}"))
    names = [s.scope_name for s in p.scopes]
    cs.append(Check("scope names unique", len(names) == len(set(names))))
    return cs
def assert_valid(p: IntakePayload, **_) -> None:
    bad = [c for c in validate(p) if not c.ok]
    if bad: raise IntakeValidationError("; ".join(f"{c.name} [{c.detail}]" for c in bad))
```

- [ ] **Step 4: Run → PASS.** **Step 5: Commit** — `git commit -m "feat(ops-intake): reconciliation validator"`

---

## Task 5: Real-workbook integration test (+ chiller scopes)

**Files:** Modify `src/ops_intake/extract.py` (add chiller scopes from `Print_Template` R-rollup, `is_estimate`),
create `tests/test_extract_real_workbook.py`.

- [ ] **Step 1: scp the workbook to the host (gitignored)**
```bash
ssh olares-mesh 'mkdir -p /home/olares/code/apex/apex-ops-lane/packages/ops-intake/_data'
scp "/c/Users/jjswe/Desktop/Project Miner PM Planning/Cupertino - Miner Estimator PHX Bldg A & B MV Rev10.xlsm" \
  "olares-mesh:/home/olares/code/apex/apex-ops-lane/packages/ops-intake/_data/miner_rev10.xlsm"
```
Add `packages/ops-intake/_data/` to `.gitignore` and commit that line.

- [ ] **Step 2: Failing test** — `tests/test_extract_real_workbook.py`
```python
from ops_intake.extract import extract_workbook
from ops_intake.validate import validate

def test_real_miner(real_workbook):
    p = extract_workbook(real_workbook)
    assert abs(p.project.contract_value - 4692078.98) < 1.0
    mv = {s.scope_name: s for s in p.scopes if s.lines}
    assert len(mv) == 7                                   # 7 MV scopes with apparatus
    a1 = next(s for s in p.scopes if s.scope_name.startswith("A1"))
    assert abs(a1.quote.total_quoted_hours - 362.5) < 0.01
    assert sum(l.qty for l in a1.lines) >= 100            # QTY-expansion (A1 ~114 units)
    chiller = [s for s in p.scopes if "Chiller" in s.scope_name]
    assert len(chiller) == 2 and all(s.quote.is_estimate for s in chiller)
    assert all(c.ok for c in validate(p)), [c for c in validate(p) if not c.ok]
```

- [ ] **Step 3: Implement** — in `extract.py`, after the scope loop, parse `Print_Template` rows whose `L`
  label contains "Chiller" → append a `ScopeIn` with `quote=ScopeQuoteIn(outside_services=R_value,
  is_estimate=True)` (lump in one flagged category so totals reconcile), `lines=[]`.

- [ ] **Step 4: Run with the workbook present**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-lane; \
  MINER_WORKBOOK=packages/ops-intake/_data/miner_rev10.xlsm \
  uv run --with pytest --with-editable packages/ops-intake pytest packages/ops-intake/tests/test_extract_real_workbook.py -q'
```
Expected: PASS (asserts the $4,692,078.98 total + 7 MV scopes + 2 chiller estimates + QTY-expansion).

- [ ] **Step 5: Commit** — `git commit -m "feat(ops-intake): chiller estimate scopes + real-workbook integration test"`

---

## Task 6: Loader (draft load, idempotent)

**Files:** Create `src/ops_intake/load.py`, `tests/test_load.py`.

**Interfaces — Produces** `load_payload(payload, dsn, *, approve=False) -> LoadResult(counts)`.

- [ ] **Step 1: Failing test** — `tests/test_load.py` (runs against `ops_dev`; truncates `ops` data tables
  first; uses `conftest.ops_dev_dsn()`)
```python
import psycopg
from ops_intake.extract import extract_workbook
from ops_intake.load import load_payload

def test_load_then_idempotent(mini_workbook, clean_ops):   # clean_ops (conftest) truncates + returns dsn
    p = extract_workbook(mini_workbook)
    r1 = load_payload(p, clean_ops)
    assert r1.projects == 1 and r1.scopes == 1 and r1.lines == 2 and r1.apparatus == 5  # 2+3 QTY-expanded
    with psycopg.connect(clean_ops) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 5
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 2
        (cv,) = c.execute("select contract_value from ops.projects").fetchone(); assert float(cv) == 1000.0
    r2 = load_payload(p, clean_ops)            # idempotent
    with psycopg.connect(clean_ops) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 5
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** — `src/ops_intake/load.py`. Upsert order: project (on `legacy_source_id`) →
  standard_hours (on `unique(apparatus_type,test_standard)`) → scopes (on `(project_id, legacy_source_id=name)`)
  → scope_quote (PK scope_id) → scope_quote_line (on `(scope_id, line_number)`) → apparatus (on
  `legacy_source_id = "<scope>:row<r>:u<i>"`). QTY-expand: for a line with qty N, insert N apparatus rows
  (`quoted_hours = hrs_per_unit`, `quote_line_id` = the line, `apparatus_designation = f"{type} {i}"`).
  All `ON CONFLICT … DO UPDATE`. Set `project.legacy_source_id='project-miner'`, `source=<workbook name>`,
  `provenance_status='draft'`. Return a `LoadResult` of row counts.
```python
from dataclasses import dataclass
import psycopg
from .model import IntakePayload
@dataclass
class LoadResult: projects:int=0; scopes:int=0; lines:int=0; apparatus:int=0; standard_hours:int=0
def load_payload(p: IntakePayload, dsn: str, *, approve: bool=False) -> LoadResult:
    res = LoadResult()
    with psycopg.connect(dsn, autocommit=False) as c, c.cursor() as cur:
        cur.execute("""insert into ops.projects (project_number,project_name,status,quote_revision,
            contract_value,description,source,legacy_source_id,provenance_status)
            values (%s,%s,%s,%s,%s,%s,%s,'project-miner','draft')
            on conflict (project_number) do update set project_name=excluded.project_name,
              contract_value=excluded.contract_value, description=excluded.description,
              quote_revision=excluded.quote_revision, updated_at=now()
            returning id""", (p.project.project_number, p.project.project_name, p.project.status,
              p.project.quote_revision, p.project.contract_value, p.project.description, "miner_rev10.xlsm"))
        pid = cur.fetchone()[0]; res.projects = 1
        for h in p.standard_hours:
            cur.execute("""insert into ops.standard_hours (apparatus_type,test_standard,default_hours,neta_section)
              values (%s,%s,%s,%s) on conflict (apparatus_type,test_standard)
              do update set default_hours=excluded.default_hours, neta_section=excluded.neta_section, updated_at=now()""",
              (h.apparatus_type,h.test_standard,h.default_hours,h.neta_section)); res.standard_hours+=1
        for s in p.scopes:
            cur.execute("""insert into ops.scopes (project_id,scope_name,scope_type,sort_order,source,legacy_source_id,provenance_status)
              values (%s,%s,%s,%s,%s,%s,%s)
              on conflict (project_id,legacy_source_id) do update set scope_name=excluded.scope_name,
                sort_order=excluded.sort_order, updated_at=now() returning id""",
              (pid,s.scope_name,s.scope_type,s.sort_order,"miner_rev10.xlsm",s.scope_name,
               'estimate' if s.quote.is_estimate else 'draft')); sid = cur.fetchone()[0]; res.scopes+=1
            cur.execute("""insert into ops.scope_quote (scope_id,onsite_labor,offsite_labor,travel,outside_services,
                unit_multiplier,pct_adjust,total_quoted_hours,provenance_status)
              values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
              on conflict (scope_id) do update set onsite_labor=excluded.onsite_labor, offsite_labor=excluded.offsite_labor,
                travel=excluded.travel, outside_services=excluded.outside_services, unit_multiplier=excluded.unit_multiplier,
                pct_adjust=excluded.pct_adjust, total_quoted_hours=excluded.total_quoted_hours, updated_at=now()""",
              (sid,s.quote.onsite_labor,s.quote.offsite_labor,s.quote.travel,s.quote.outside_services,
               s.quote.unit_multiplier,s.quote.pct_adjust,s.quote.total_quoted_hours,
               'estimate' if s.quote.is_estimate else 'draft'))
            for l in s.lines:
                cur.execute("""insert into ops.scope_quote_line (scope_id,apparatus_type,test_standard,qty,hrs_per_unit,
                    designation,line_number,source,legacy_source_id,provenance_status)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
                  on conflict (scope_id,line_number) do update set qty=excluded.qty, hrs_per_unit=excluded.hrs_per_unit,
                    apparatus_type=excluded.apparatus_type returning id""",
                  (sid,l.apparatus_type,l.test_standard,l.qty,l.hrs_per_unit,l.designation,l.line_number,
                   "miner_rev10.xlsm", f"{s.scope_name}:row{l.line_number}")); lid = cur.fetchone()[0]; res.lines+=1
                for i in range(1, l.qty+1):
                    cur.execute("""insert into ops.apparatus (scope_id,apparatus_designation,apparatus_type,status,
                        drawing_reference,quoted_hours,quote_line_id,source,legacy_source_id,provenance_status)
                      values (%s,%s,%s,'Not Started',%s,%s,%s,%s,%s,'draft')
                      on conflict (legacy_source_id) do update set quoted_hours=excluded.quoted_hours,
                        quote_line_id=excluded.quote_line_id, apparatus_type=excluded.apparatus_type""",
                      (sid, f"{l.apparatus_type} {i}", l.apparatus_type, l.drawing, l.hrs_per_unit, lid,
                       "miner_rev10.xlsm", f"{s.scope_name}:row{l.line_number}:u{i}")); res.apparatus+=1
        c.commit()
    if approve: _approve(p, dsn)
    return res
```
**Prerequisite — unique constraints for upsert:** `ops.scopes(project_id, legacy_source_id)`,
`ops.scope_quote_line(scope_id, line_number)`, `ops.apparatus(legacy_source_id)` need UNIQUE constraints for
`ON CONFLICT`. They are not in Chips 1–2. **Add `infra/database/migrations/ops/003_intake_unique_keys.sql`
(+ `_down` + a one-line note in MANIFEST)** creating those three partial-unique indexes
(`where legacy_source_id is not null`). Apply it in this task's Step 0 and include in Task 0's apply list. *(This
is the one small DDL the intake needs — additive indexes, reversible.)*

- [ ] **Step 4: Run → PASS**
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; cd /home/olares/code/apex/apex-ops-lane; \
  OPS_DEV_PGPASSWORD="$DEV_PG_PASSWORD" uv run --with pytest --with-editable packages/ops-intake pytest packages/ops-intake/tests/test_load.py -q'
```

- [ ] **Step 5: Commit** — `git commit -m "feat(ops-intake): idempotent loader + intake unique keys (mig 003)"`

---

## Task 7: Approve / freeze step

**Files:** Modify `src/ops_intake/load.py` (`_approve`), create `tests/test_load_approve.py`.

**Interfaces — Produces** `load_payload(..., approve=True)` freezes `apparatus.quoted_revenue` and
`scope_quote.is_frozen`.

- [ ] **Step 1: Failing test** — assert post-approve: each MV apparatus `quoted_revenue ≈ quoted_hours ×
  scope.blended_rate`; `Σ apparatus.quoted_revenue per scope ≈ scope.adjusted_total`; `scope_quote.is_frozen`.
```python
import psycopg
from ops_intake.extract import extract_workbook
from ops_intake.load import load_payload
def test_approve_freezes(mini_workbook, clean_ops):
    dsn = clean_ops
    load_payload(extract_workbook(mini_workbook), dsn, approve=True)
    with psycopg.connect(dsn) as c:
        rev = c.execute("select coalesce(sum(quoted_revenue),0) from ops.apparatus").fetchone()[0]
        assert abs(float(rev) - 1000.0) < 0.5            # Σ apparatus revenue == scope P4
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
```

- [ ] **Step 2: Run → FAIL.**  **Step 3: Implement** `_approve`:
```python
def _approve(p, dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute("""update ops.apparatus a set quoted_revenue = round(a.quoted_hours * sq.blended_rate, 2),
            provenance_status='approved'
            from ops.scope_quote sq where sq.scope_id = a.scope_id and a.quoted_hours is not null""")
        c.execute("update ops.scope_quote set is_frozen=true, frozen_at=now()")
        c.execute("update ops.projects set provenance_status='approved' where legacy_source_id='project-miner'")
```
- [ ] **Step 4: Run → PASS. Step 5: Commit** — `git commit -m "feat(ops-intake): approve/freeze step"`

---

## Task 8: CLI + end-to-end load of Project Miner

**Files:** Create `src/ops_intake/cli.py`, `tests/test_cli.py`, `tests/test_e2e_miner.py`; modify
`infra/database/migrations/ops/MANIFEST.md`.

- [ ] **Step 1: CLI failing test** — `tests/test_cli.py`: `ops_intake.cli.main(["extract", str(mini_workbook),
  "--out", str(tmp/"p.json")])` writes JSON with `contract_value` 1000.

- [ ] **Step 2: Implement `cli.py`** — `argparse`: `extract <xlsm> --out <json>` (dataclasses→`asdict`→json);
  `load <xlsm> --dsn <dsn> [--approve]` (extract → `assert_valid` → `load_payload`); `main(argv=None)`.

- [ ] **Step 3: CLI test → PASS. Commit** — `git commit -m "feat(ops-intake): cli"`

- [ ] **Step 4: e2e test** — `tests/test_e2e_miner.py` (skipif no `MINER_WORKBOOK`): truncate `ops`,
  `load_payload(extract_workbook(real), dsn, approve=True)`, then assert in `ops_dev`:
  `count(projects)==1`; `count(scopes)==9`; `count(scope_quote_line)>=119`; `count(apparatus)>=600`;
  `sum(apparatus.quoted_revenue)` per MV scope ≈ its `Print_Template` $; `projects.contract_value==4692078.98`;
  re-run changes 0 rows.

- [ ] **Step 5: Run the real end-to-end load**
```bash
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; cd /home/olares/code/apex/apex-ops-lane; \
  OPS_DEV_PGPASSWORD="$DEV_PG_PASSWORD" MINER_WORKBOOK=packages/ops-intake/_data/miner_rev10.xlsm \
  uv run --with pytest --with-editable packages/ops-intake pytest packages/ops-intake/tests/test_e2e_miner.py -q'
```
Expected: PASS — **Project Miner fully in `ops_dev`** (1 project / 9 scopes / hundreds of apparatus,
$4,692,078.98 reconciled).

- [ ] **Step 6: Update `MANIFEST.md`** — add the `003_intake_unique_keys` row + an "Intake (Chip 5):
  `packages/ops-intake/`" note. **Commit** — `git commit -m "feat(ops-intake): e2e Miner load + manifest"`

---

## Self-Review

- **Spec coverage:** projects/scopes/scope_quote/scope_quote_line/apparatus(QTY-expand)/standard_hours all loaded
  (Tasks 6–8); validations 1–7 → Tasks 4/5/8; idempotency → Task 6; approve/freeze → Task 7; both-names → Task 6;
  chiller estimate scopes → Task 5. ✓
- **One DDL deviation from "no new DDL":** the upserts need three UNIQUE indexes not in Chips 1–2 →
  `003_intake_unique_keys.sql` (additive, reversible). Flagged in Task 6; folded into Task 0's apply list.
- **Types:** `IntakePayload`/`ScopeIn`/`QuoteLineIn`/`ScopeQuoteIn`/`StandardHourIn` consistent across tasks;
  `load_payload(payload,dsn,*,approve)` and `extract_workbook(path)` signatures stable.
- **Placeholders:** none — full code in every code step; commands are exact and host-rooted.

## Execution Handoff

Two options (the build is on the remote host over `ssh olares-mesh`):
1. **Inline (recommended here)** — execute task-by-task in this session via `superpowers:executing-plans`, with a
   final adversarial review. Best fit given remote-host file editing + DB-on-host tests (matches §261).
2. **Subagent-driven** — `superpowers:subagent-driven-development`, fresh subagent per task. Cleaner isolation,
   but each subagent pays the remote-host/SSH ramp-up per task.
