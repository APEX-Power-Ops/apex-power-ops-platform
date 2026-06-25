# estimator-takeoff Plan 2b — `drawing-nav extract` producer + real E01-11 golden e2e

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `drawing-nav extract <pdf>` command that turns a real electrical one-line PDF (STACK PHX02A Addendum 4 ELEC) into the breaker engine's `ExtractionArtifact` JSON — deterministic, legend-aware, **never guessing voltage or construction** — so the Plan-1 engine (hardened by Plan 2a) runs end-to-end on a real drawing, and prove it with a two-sided golden on E01-11.

**Architecture:** A new standalone Python package `dn_extract/` beside `drawing_nav.py` (Windows, PyMuPDF), composed of six pure-ish components (legend-profile → sheet-selector → two-pass discovery → field-assembly → location-pass → emit) orchestrated by `extract_artifact`, surfaced as an `extract` subcommand. The producer emits only the engine's contract fields and a faithful `raw` string; the engine re-parses `raw` for frame/functions/voltage. The golden's engine half is a TS test in the monorepo (consumed via the same mesh-SSH mechanic as Plan 2a).

**Tech Stack:** Python 3.12 (`C:\Users\jjswe\.local\bin\python.exe`), PyMuPDF 1.27.2.3 (`fitz`), pytest (provisioned via `uv`); TypeScript 5.5 / vitest for the engine golden. No runtime deps beyond PyMuPDF.

## Global Constraints

- **Producer lives standalone** at `C:\Users\jjswe\Tools\drawing-nav\` (NOT yet a git repo, NOT in the monorepo — spec §8 relocation is deferred). Task 1 runs `git init` there for TDD version control. Producer commits are local to that repo (push deferred/operator-gated).
- **Two execution contexts.** (1) **Producer (Tasks 1–6, Task 7a):** local Windows — edit in `C:\Users\jjswe\Tools\drawing-nav\`, run `python -m pytest`, commit to the local drawing-nav repo. NO mesh-SSH. (2) **Engine golden (Task 7c):** the monorepo on the Olares host — same mesh-SSH mechanic as Plan 2a (author in `C:\dev\estimator-takeoff-staging\packages\estimator-takeoff\`, per-file `scp`, run `pnpm`/`vitest`/`git` on host, branch `estimator-takeoff/extract`).
- **The extractor never fabricates.** Omit-and-question over guess: ambiguous/multi/zero voltage → omit `busVoltageV`; a breaker-suffix token with no AF/AT → Pass-B `candidateKind:'breaker'` (engine questions it, never prices it); legend unparsed → default profile + a `profileWarnings` entry. **No `mountingHint` is ever produced in V1** (construction is graphical).
- **Voltage rule is conservative and final (operator-ratified 2026-06-25):** exactly one distinct LV bus nominal AND no MV present → broadcast it; otherwise omit for the whole sheet. Do NOT broadcast a voltage "by vibes" on a multi-bus sheet. The only mechanical refinement is token normalization (`480V,3φ,` → `480`; transformer-ratio tokens like `480V-208/120V` are not bus labels).
- **`raw` fidelity:** a Pass-A row's `raw` must contain `<frame>AF/<trip>AT` joined with a slash (AF and AT are separate words in the PDF) so the engine's `FRAME_TRIP` parses the rating, matching the Plan-1 fixture format (`"ACC-1-09-FB 800AF/800AT LSIGE"`).
- **Contract is the seam:** the producer emits exactly the fields in `ExtractedApparatus` / `ExtractionArtifact` (incl. Plan 2a's `candidateKind?` and `profileWarnings?`). It never emits frame/functions as separate fields — those are the engine's job.
- **TDD:** failing test → run-red → minimal impl → run-green → commit. Producer suite green at each task end: `python -m pytest -q` (run from `C:\Users\jjswe\Tools\drawing-nav\`).
- **Determinism:** no wall-clock in artifacts under test — `extract_artifact(..., now=None)` omits `extractedAt`; only the CLI stamps real time.
- **Depends on Plan 2a** (the engine must already carry `candidateKind`, `profileWarnings`, and the `frameA` eligibility rule). Execute Plan 2a first.

### Host/local paths (verbatim)
- `DN=/c/Users/jjswe/Tools/drawing-nav` (producer repo, local Windows)
- `PY="C:\Users\jjswe\.local\bin\python.exe"` (drawing-nav interpreter; PyMuPDF installed)
- `STAGE=/c/dev/estimator-takeoff-staging/packages/estimator-takeoff` (engine staging mirror)
- `PKG=/home/olares/code/apex/apex-power-ops-platform/packages/estimator-takeoff` (engine on host)
- `REPO=/home/olares/code/apex/apex-power-ops-platform` (host monorepo, branch `estimator-takeoff/extract`)
- Host node PATH: `export PATH=$HOME/.nvm/versions/node/v20.20.2/bin:$PATH`
- Real PDF (en-dashes in name; read the path from the index, do not retype): `C:\Users\jjswe\Tools\drawing-nav\index_elec.json` → `["pdf"]`.

---

## File Structure

```
C:\Users\jjswe\Tools\drawing-nav\
  drawing_nav.py              # MODIFY: import dn_extract; add `extract` subparser → cmd_extract
  .gitignore                  # CREATE: _renders/, __pycache__/, *.pyc, .pytest_cache/, *.out.json
  dn_extract/
    __init__.py               # CREATE: re-export extract_artifact, PackageProfile
    profile.py                # CREATE: PackageProfile + DEFAULT_PROFILE + load_profile  [component 1]
    sheets.py                 # CREATE: in_scope, normalize_block, sheet_voltage         [component 2 + guardrail 4]
    discovery.py              # CREATE: discover(words, profile) -> (cols, candidates)    [component 3]
    assemble.py               # CREATE: assemble_column / assemble_candidate -> dict      [component 4]
    location.py               # CREATE: location_rows(words, sheet, page) -> dicts        [component 5]
    pipeline.py               # CREATE: extract_artifact(doc, ...) -> ExtractionArtifact   [component 6]
  tests/
    helpers.py                # CREATE: w(...) word-tuple factory + a tiny FakeDoc
    test_profile.py           # CREATE
    test_sheets.py            # CREATE (block normalization + voltage rule)
    test_discovery.py         # CREATE
    test_assemble.py          # CREATE
    test_location.py          # CREATE
    test_pipeline.py          # CREATE (synthetic FakeDoc end-to-end + CLI smoke)
    test_golden_e01_11.py     # CREATE (Task 7a: real PDF, skip if absent)

C:\dev\estimator-takeoff-staging\packages\estimator-takeoff\   (engine, host via mesh-SSH)
  test/fixtures/stack-phx02a-e01-11-extract.json   # CREATE (Task 7b: real extracted artifact, checked in)
  test/golden-e01-11.test.ts                       # CREATE (Task 7c: negative + injected-voltage positive)
```

---

## Task 1: Scaffold + legend `PackageProfile` (component 1)

**Files:**
- Create: `C:\Users\jjswe\Tools\drawing-nav\.gitignore`, `dn_extract/__init__.py`, `dn_extract/profile.py`, `tests/helpers.py`, `tests/test_profile.py`
- Setup: `git init` in `DN`; provision pytest via `uv`

**Interfaces:**
- Produces: `PackageProfile{breaker_suffixes, non_breaker, warnings}` with `.is_breaker_suffix(tag) -> bool`; `DEFAULT_PROFILE`; `load_profile(doc, legend_page=0) -> PackageProfile`.

- [ ] **Step 1: One-time setup** — provision the repo + test runner:

```bash
cd /c/Users/jjswe/Tools/drawing-nav
git init -q && printf '_renders/\n__pycache__/\n*.pyc\n.pytest_cache/\n*.out.json\n' > .gitignore
uv pip install --python "C:\Users\jjswe\.local\bin\python.exe" pytest
python -m pytest --version    # expect: pytest 8.x
```

- [ ] **Step 2: Write the failing test** — `tests/helpers.py`:

```python
def w(x0, y0, x1, y1, text):
    """Build a PyMuPDF-style word tuple (x0,y0,x1,y1,text,block,line,wordno)."""
    return (float(x0), float(y0), float(x1), float(y1), text, 0, 0, 0)

class FakePage:
    def __init__(self, words, text=""):
        self._words = words; self._text = text
    def get_text(self, kind, clip=None):
        return self._words if kind == "words" else self._text

class FakeDoc:
    def __init__(self, pages):
        self._pages = pages
        self.name = "20260616 - PHX02A - ADDENDUM 4 - ELEC.pdf"
    def __getitem__(self, i):
        return self._pages[i]
```

  `tests/test_profile.py`:

```python
from dn_extract.profile import PackageProfile, DEFAULT_PROFILE, load_profile
from tests.helpers import FakeDoc, FakePage

def test_default_profile_recognizes_breaker_suffixes():
    assert DEFAULT_PROFILE.is_breaker_suffix("ACC-1-09-FB")
    assert DEFAULT_PROFILE.is_breaker_suffix("MSB-P1-110-GB")
    assert DEFAULT_PROFILE.is_breaker_suffix("DH110-UB")
    assert not DEFAULT_PROFILE.is_breaker_suffix("XF-1-SPD")     # SPD is not a breaker suffix
    assert not DEFAULT_PROFILE.is_breaker_suffix("BUS-1200-3-CU")

def test_load_profile_confirms_against_legend_text():
    doc = FakeDoc([FakePage([], text="LEGEND ... FB GB AF AT ...")])
    p = load_profile(doc, legend_page=0)
    assert p.warnings == ()                                      # confirmed, no warning

def test_load_profile_warns_when_legend_anchors_absent():
    doc = FakeDoc([FakePage([], text="NOTHING USEFUL HERE")])
    p = load_profile(doc, legend_page=0)
    assert p.breaker_suffixes == DEFAULT_PROFILE.breaker_suffixes  # falls back to default
    assert any("default profile assumed" in wmsg for wmsg in p.warnings)
```

- [ ] **Step 3: Run red** — `cd /c/Users/jjswe/Tools/drawing-nav && python -m pytest tests/test_profile.py -q`. Expected: FAIL (`dn_extract` not importable).

- [ ] **Step 4: Implement** — `dn_extract/__init__.py`:

```python
from .profile import PackageProfile, DEFAULT_PROFILE, load_profile
from .pipeline import extract_artifact
__all__ = ["PackageProfile", "DEFAULT_PROFILE", "load_profile", "extract_artifact"]
```

  (Note: `pipeline` is created in Task 6; until then import will fail at package import. To keep Tasks 1–5 runnable, make `__init__.py` import only `profile` for now and add `pipeline`/`extract_artifact` in Task 6.) For Task 1 write:

```python
from .profile import PackageProfile, DEFAULT_PROFILE, load_profile
__all__ = ["PackageProfile", "DEFAULT_PROFILE", "load_profile"]
```

  `dn_extract/profile.py`:

```python
"""PackageProfile — breaker-role suffixes + non-breaker exclusions for one extraction run.

V1: the built-in default profile is authoritative. load_profile() makes a best-effort
confirmation against the legend sheet (E00-01); when the legend is unreadable or its expected
anchor tokens are absent, it returns the default profile WITH a warning. Discovering NEW
suffixes from legend text is deferred (next slice)."""
from __future__ import annotations
from dataclasses import dataclass, replace

DEFAULT_BREAKER_SUFFIXES = frozenset({"FB", "GB", "GMB", "UB", "MBB", "MIB", "MCB", "MB", "LB"})
DEFAULT_NON_BREAKER = frozenset({"SPD", "PQM", "ATS", "STS", "MTS", "TX", "XFMR", "PDU", "UPS", "METER"})
_LEGEND_ANCHORS = ("FB", "GB", "AF", "AT")

@dataclass(frozen=True)
class PackageProfile:
    breaker_suffixes: frozenset = DEFAULT_BREAKER_SUFFIXES
    non_breaker: frozenset = DEFAULT_NON_BREAKER
    warnings: tuple = ()

    def is_breaker_suffix(self, tag: str) -> bool:
        seg = tag.rsplit("-", 1)[-1].upper()
        return seg in self.breaker_suffixes

DEFAULT_PROFILE = PackageProfile()

def load_profile(doc, legend_page: int = 0) -> PackageProfile:
    try:
        text = doc[legend_page].get_text("text").upper()
    except Exception:
        return replace(DEFAULT_PROFILE, warnings=("legend sheet E00-01 unreadable — default profile assumed",))
    missing = [a for a in _LEGEND_ANCHORS if a not in text]
    if missing:
        return replace(DEFAULT_PROFILE,
                       warnings=(f"legend E00-01 missing expected anchors {missing} — default profile assumed",))
    return DEFAULT_PROFILE
```

- [ ] **Step 5: Run green** — `python -m pytest tests/test_profile.py -q`. Expected: 3 passed. (Add a `conftest.py`? Not needed — run pytest from `DN` so `dn_extract` and `tests` are importable via rootdir.)

- [ ] **Step 6: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): scaffold dn_extract package + legend PackageProfile (component 1)"
```

---

## Task 2: Sheet selection + block normalization + voltage rule (component 2 + guardrail 4)

**Files:**
- Create: `dn_extract/sheets.py`, `tests/test_sheets.py`

**Interfaces:**
- Consumes: a page's `words` list.
- Produces: `in_scope(sheet_id) -> bool`; `normalize_block(title, sheet_id) -> (block:str, warnings:list[str])`; `sheet_voltage(words) -> (busV:int|None, warnings:list[str])`.

- [ ] **Step 1: Write the failing test** — `tests/test_sheets.py`:

```python
from dn_extract.sheets import in_scope, normalize_block, sheet_voltage
from tests.helpers import w

def test_in_scope_set():
    assert in_scope("E01-11") and in_scope("E01-30") and in_scope("E01-51")
    assert not in_scope("E01-01")   # MV main, deferred
    assert not in_scope("E05-10")   # panel schedule, deferred

def test_block_canonical_map_wins_and_is_title_variant_stable():
    # All title variants of E01-10 (incl. the R1-110/210 slash, em-dash, wrap) collapse identically.
    for title in ["ONE LINE DIAGRAM - RESERVE BLOCK R1-110/210",
                  "ONE  LINE   DIAGRAM — RESERVE BLOCK  R1-110/210",
                  "one line diagram - reserve block r1-110/210"]:
        assert normalize_block(title, "E01-10") == ("R1-110-210", [])
    assert normalize_block("ONE LINE DIAGRAM - PRIMARY BLOCK P1-110", "E01-11") == ("P1-110", [])
    assert normalize_block("... MECH. GALLERY DISTRIBUTION - DH110", "E01-30") == ("DH110", [])

def test_block_unlisted_sheet_falls_back_then_unknown():
    blk, warns = normalize_block("ONE LINE DIAGRAM - PRIMARY BLOCK P9-999", "E09-99")
    assert blk == "P9-999" and warns == []
    blk2, warns2 = normalize_block("SOME UNLABELED SHEET", "E09-98")
    assert blk2 == "UNKNOWN_E09-98" and warns2 and "could not normalize" in warns2[0]

def test_voltage_single_lv_bus_broadcasts():
    # E01-30-style: only "480V,3φ," tokens -> 480
    words = [w(100, 100, 140, 110, "480V,3φ,"), w(100, 200, 140, 210, "480V,3φ,")]
    assert sheet_voltage(words) == (480, [])

def test_voltage_multi_lv_bus_omits():
    # E01-11-style: 480, 480/277, 208/120 -> multiple distinct LV nominals -> omit
    words = [w(0,0,1,1,"480V"), w(0,0,1,1,"480/277V"), w(0,0,1,1,"208/120V")]
    v, warns = sheet_voltage(words)
    assert v is None and warns and "multiple LV bus labels" in warns[0]

def test_voltage_mv_present_omits():
    words = [w(0,0,1,1,"480V"), w(0,0,1,1,"13.8KV")]
    v, warns = sheet_voltage(words)
    assert v is None and warns and "MV label" in warns[0]

def test_voltage_transformer_ratio_token_is_not_a_bus_label():
    # "480V-208/120V" is a transformer descriptor, not a bus label -> ignored; single real bus 480 stays single
    words = [w(0,0,1,1,"480V"), w(0,0,1,1,"480V-208/120V")]
    assert sheet_voltage(words) == (480, [])
```

- [ ] **Step 2: Run red** — `python -m pytest tests/test_sheets.py -q`. Expected: FAIL (no `sheets` module).

- [ ] **Step 3: Implement** — `dn_extract/sheets.py`:

```python
"""Sheet selection, deterministic block normalization, and the conservative bus-voltage rule."""
from __future__ import annotations
import re

CANON_BLOCK = {
    "E01-10": "R1-110-210",
    "E01-11": "P1-110", "E01-12": "P2-110", "E01-13": "P3-110", "E01-14": "P4-110",
    "E01-15": "P5-210", "E01-16": "P6-210", "E01-17": "P7-210",
    "E01-30": "DH110", "E01-31": "DH210",
    "E01-50": "HOUSE_NON_CRITICAL", "E01-51": "HOUSE_CRITICAL",
}
IN_SCOPE_SHEETS = frozenset(CANON_BLOCK)

def in_scope(sheet_id: str) -> bool:
    return sheet_id in IN_SCOPE_SHEETS

def normalize_block(title: str, sheet_id: str):
    warnings: list[str] = []
    if sheet_id in CANON_BLOCK:                      # canonical sheet map wins (spec §4.3)
        return CANON_BLOCK[sheet_id], warnings
    key = re.sub(r"[^a-z0-9]+", "-", " ".join(title.split()).casefold()).strip("-")
    m = re.search(r"block-(p\d-\d{3}|dh\d{3}|r\d-\d{3}(?:-\d{3})?)", key) or \
        re.search(r"\b(p\d-\d{3}|dh\d{3}|r\d-\d{3})\b", key)
    if m:
        return m.group(1).upper(), warnings
    warnings.append(f"block: could not normalize title {title!r} for {sheet_id} — using UNKNOWN")
    return f"UNKNOWN_{sheet_id}", warnings

_VOLT = re.compile(r"^(\d{3,5})(?:Y)?(?:/\d{3})?V")     # bus nominal: leading L-L number, optional wye/neutral
_KV = re.compile(r"^(\d+(?:\.\d+)?)KV")

def _bus_nominal(token: str):
    t = token.upper().strip()
    if "-" in t:                                        # transformer-ratio descriptor — not a bus label
        return None
    mk = _KV.match(t)
    if mk:
        return int(float(mk.group(1)) * 1000)
    m = _VOLT.match(t)
    return int(m.group(1)) if m else None

def sheet_voltage(words):
    nominals = {n for n in (_bus_nominal(x[4]) for x in words) if n is not None}
    lv = sorted(n for n in nominals if n < 1000)
    mv = sorted(n for n in nominals if n >= 1000)
    if mv:
        return None, [f"voltage: MV label(s) {mv} present (with LV {lv}) — omitting bus voltage; operator must assert"]
    if len(lv) == 1:
        return lv[0], []
    if not lv:
        return None, ["voltage: no LV bus label found — omitting bus voltage"]
    return None, [f"voltage: multiple LV bus labels {lv} — omitting; per-bus association deferred, operator must assert"]
```

- [ ] **Step 4: Run green** — `python -m pytest tests/test_sheets.py -q`. Expected: all passed.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): sheet selection + deterministic block + conservative voltage rule (component 2)"
```

---

## Task 3: Two-pass device discovery (component 3)

**Files:**
- Create: `dn_extract/discovery.py`, `tests/test_discovery.py`

**Interfaces:**
- Consumes: `words` list + a `PackageProfile`.
- Produces: `discover(words, profile) -> (columns: list[Column], candidates: list[Candidate])` where `Column{raw, tag, bbox}` (Pass A, AF/AT-anchored) and `Candidate{tag, bbox}` (Pass B, breaker-suffix token with no AF/AT). `raw` joins AF/AT as `<frame>AF/<trip>AT`.

- [ ] **Step 1: Write the failing test** — `tests/test_discovery.py` (coordinates mirror the REAL E01-11 geometry probed from the PDF):

```python
from dn_extract.discovery import discover, Column, Candidate
from dn_extract.profile import DEFAULT_PROFILE
from tests.helpers import w

P = DEFAULT_PROFILE

def test_passA_single_column_real_geometry():
    # ACC-1-09-FB column @ x=886.4 (tag / 800AF / 800AT / LSIGE), exactly as on E01-11.
    words = [w(886.4, 491.4, 944.2, 501.0, "ACC-1-09-FB"),
             w(886.4, 502.4, 914.4, 512.0, "800AF"),
             w(886.4, 513.3, 914.4, 522.9, "800AT"),
             w(886.4, 524.1, 914.4, 533.7, "LSIGE")]
    cols, cands = discover(words, P)
    assert len(cols) == 1 and cands == []
    assert cols[0].raw == "ACC-1-09-FB 800AF/800AT LSIGE"
    assert cols[0].tag == "ACC-1-09-FB"

def test_passA_split_tag_is_rejoined():
    # ACC-1-10 + -FB on two lines @ x=968.8 -> "ACC-1-10-FB".
    words = [w(968.8, 491.4, 1011.3, 500.9, "ACC-1-10"),
             w(968.8, 502.3, 984.1, 511.9, "-FB"),
             w(968.8, 511.3, 996.7, 520.9, "800AF"),
             w(968.8, 522.2, 996.7, 531.8, "800AT"),
             w(968.8, 533.0, 996.7, 542.6, "LSIGE")]
    cols, _ = discover(words, P)
    assert cols[0].tag == "ACC-1-10-FB"
    assert cols[0].raw == "ACC-1-10-FB 800AF/800AT LSIGE"

def test_conductor_decoy_produces_no_column():
    # A conductor label (no AF/AT) must not become a breaker column or a candidate.
    words = [w(700, 100, 760, 110, "1200-3-CU")]
    cols, cands = discover(words, P)
    assert cols == [] and cands == []

def test_two_adjacent_columns_are_separated():
    words = [w(886.4, 491, 944, 501, "ACC-1-09-FB"), w(886.4, 502, 914, 512, "800AF"),
             w(886.4, 513, 914, 523, "800AT"),       w(886.4, 524, 914, 534, "LSIGE"),
             w(968.8, 491, 1011, 501, "ACC-1-10-FB"), w(968.8, 511, 997, 521, "800AF"),
             w(968.8, 522, 997, 532, "800AT"),        w(968.8, 533, 997, 543, "LSIGE")]
    cols, _ = discover(words, P)
    assert len(cols) == 2
    assert {c.tag for c in cols} == {"ACC-1-09-FB", "ACC-1-10-FB"}

def test_passB_breaker_suffix_without_af_at_is_a_candidate():
    # An exotic-suffix token with no AF/AT -> Pass-B candidate (the engine questions it).
    words = [w(1200, 800, 1280, 812, "DH110-UB")]
    cols, cands = discover(words, P)
    assert cols == []
    assert len(cands) == 1 and cands[0].tag == "DH110-UB"

def test_passB_does_not_double_emit_a_consumed_tag():
    # FB token that IS the tag of a Pass-A column must not also appear as a Pass-B candidate.
    words = [w(886.4, 491, 944, 501, "ACC-1-09-FB"), w(886.4, 502, 914, 512, "800AF"),
             w(886.4, 513, 914, 523, "800AT"),       w(886.4, 524, 914, 534, "LSIGE")]
    cols, cands = discover(words, P)
    assert len(cols) == 1 and cands == []
```

- [ ] **Step 2: Run red** — `python -m pytest tests/test_discovery.py -q`. Expected: FAIL (no `discovery` module).

- [ ] **Step 3: Implement** — `dn_extract/discovery.py`:

```python
"""Two-pass breaker discovery over a page's PyMuPDF word list (pure; no PDF needed to test).

A breaker on a one-line is a vertical column at ~constant x: tag on top, then `<frame>AF`,
`<trip>AT`, then a function descriptor (LSIG…), each on its own line. AF and AT are SEPARATE
words — we re-join them as `<frame>AF/<trip>AT` so the engine's FRAME_TRIP regex parses them."""
from __future__ import annotations
from dataclasses import dataclass
import re

X_TOL = 5.0          # same-column x tolerance (pts); real one-line columns share an exact x0
TAG_SPAN = 28.0      # how far above the AF token tag fragments may sit (~2 text lines)
FUNC_SPAN = 18.0     # how far below the AT token the function descriptor may sit
PAIR_GAP = 16.0      # max y-gap between the AF line and the AT line

_AF = re.compile(r"^(\d{2,6})AF$")
_AT = re.compile(r"^(\d{2,6})AT$")
_FUNC = re.compile(r"^L[SIGE]{1,4}$")

@dataclass(frozen=True)
class Column:
    raw: str
    tag: str
    bbox: tuple

@dataclass(frozen=True)
class Candidate:
    tag: str
    bbox: tuple

def _union(ws):
    return (min(x[0] for x in ws), min(x[1] for x in ws),
            max(x[2] for x in ws), max(x[3] for x in ws))

def _join_tag(frags):
    # one-line tags wrap without separators; '-FB' continuations concat cleanly.
    return "".join(frags)

def discover(words, profile):
    W = list(words)
    cols, cands = [], []
    consumed = set()                                   # indices used by a Pass-A column

    for i, a in enumerate(W):
        ma = _AF.match(a[4])
        if not ma:
            continue
        # AT directly below, same x
        jb = next((j for j, b in enumerate(W)
                   if abs(b[0] - a[0]) <= X_TOL and 0 < (b[1] - a[1]) <= PAIR_GAP and _AT.match(b[4])), None)
        if jb is None:
            continue
        b = W[jb]
        frame = int(ma.group(1)); trip = int(_AT.match(b[4]).group(1))
        x = a[0]
        col_idx = [k for k, ww in enumerate(W) if abs(ww[0] - x) <= X_TOL]
        tag_idx = sorted((k for k in col_idx if a[1] - TAG_SPAN <= W[k][1] < a[1]), key=lambda k: W[k][1])
        func_idx = next((k for k in sorted(col_idx, key=lambda k: W[k][1])
                         if b[1] < W[k][1] <= b[1] + FUNC_SPAN and _FUNC.match(W[k][4])), None)
        tag = _join_tag([W[k][4] for k in tag_idx])
        used = tag_idx + [i, jb] + ([func_idx] if func_idx is not None else [])
        consumed.update(used)
        func = W[func_idx][4] if func_idx is not None else None
        raw = ((tag + " ") if tag else "") + f"{frame}AF/{trip}AT" + ((" " + func) if func else "")
        cols.append(Column(raw=raw.strip(), tag=tag, bbox=_union([W[k] for k in used])))

    for k, ww in enumerate(W):
        if k in consumed:
            continue
        tok = ww[4]
        if profile.is_breaker_suffix(tok) and not _AF.match(tok) and not _AT.match(tok):
            cands.append(Candidate(tag=tok, bbox=(ww[0], ww[1], ww[2], ww[3])))
    return cols, cands
```

- [ ] **Step 4: Run green** — `python -m pytest tests/test_discovery.py -q`. Expected: all passed. (If `test_two_adjacent_columns_are_separated` over-merges, tighten `X_TOL`; the real columns are ~82 pt apart so 5.0 is safe.)

- [ ] **Step 5: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): two-pass AF/AT-anchored discovery + Pass-B candidates (component 3)"
```

---

## Task 4: Field assembly → contract dicts (component 4)

**Files:**
- Create: `dn_extract/assemble.py`, `tests/test_assemble.py`

**Interfaces:**
- Consumes: a `Column`/`Candidate` (Task 3) + sheet context `(sheet_id, page, block, busV)`.
- Produces: `assemble_column(col, sheet, page, block, busV) -> dict` and `assemble_candidate(cand, sheet, page, block, busV) -> dict`, each a valid `ExtractedApparatus`. Pass-A carries `raw` (with AF/AT) and `busVoltageV` when known; Pass-B carries `candidateKind:'breaker'`, no frame, and the broadcast `busVoltageV` if the sheet has one (the engine's frameA rule still refuses to price it).

- [ ] **Step 1: Write the failing test** — `tests/test_assemble.py`:

```python
from dn_extract.assemble import assemble_column, assemble_candidate
from dn_extract.discovery import Column, Candidate

def test_assemble_passA_emits_contract_row():
    col = Column(raw="ACC-1-09-FB 800AF/800AT LSIGE", tag="ACC-1-09-FB", bbox=(886.4, 491.4, 944.2, 533.7))
    row = assemble_column(col, "E01-11", 11, "P1-110", 480)
    assert row == {
        "raw": "ACC-1-09-FB 800AF/800AT LSIGE", "tag": "ACC-1-09-FB",
        "sheet": "E01-11", "page": 11, "bbox": [886.4, 491.4, 944.2, 533.7],
        "evidence": "one-line", "busVoltageV": 480, "block": "P1-110",
    }
    assert "mountingHint" not in row and "candidateKind" not in row     # never in V1 Pass-A

def test_assemble_passA_omits_voltage_when_none():
    col = Column(raw="X-1-FB 400AF/400AT LSI", tag="X-1-FB", bbox=(0, 0, 1, 1))
    row = assemble_column(col, "E01-11", 11, "P1-110", None)
    assert "busVoltageV" not in row

def test_assemble_passB_marks_candidate_and_keeps_voltage_for_engine_to_refuse():
    cand = Candidate(tag="LP-1-MCB", bbox=(0, 0, 1, 1))
    row = assemble_candidate(cand, "E01-50", 20, "HOUSE_NON_CRITICAL", 480)
    assert row["candidateKind"] == "breaker"
    assert row["raw"] == "LP-1-MCB" and row["tag"] == "LP-1-MCB"
    assert row["busVoltageV"] == 480          # carried; the engine's frameA rule still won't price it (no AF/AT)
    assert "mountingHint" not in row
```

- [ ] **Step 2: Run red** — `python -m pytest tests/test_assemble.py -q`. Expected: FAIL.

- [ ] **Step 3: Implement** — `dn_extract/assemble.py`:

```python
"""Field assembly: discovery outputs + sheet context -> ExtractedApparatus dicts (the engine contract).

Emits ONLY contract fields. Never emits mountingHint (construction is graphical in V1).
frame/trip/functions live inside `raw`; the engine re-parses them."""
from __future__ import annotations

def _bbox(b):
    return [round(float(v), 1) for v in b]

def assemble_column(col, sheet, page, block, busV):
    row = {"raw": col.raw, "sheet": sheet, "page": page, "bbox": _bbox(col.bbox), "evidence": "one-line"}
    if col.tag:
        row["tag"] = col.tag
    if busV is not None:
        row["busVoltageV"] = busV
    if block:
        row["block"] = block
    # stable key order to match the fixture/contract: raw, tag, sheet, page, bbox, evidence, busVoltageV, block
    return {k: row[k] for k in ("raw", "tag", "sheet", "page", "bbox", "evidence", "busVoltageV", "block") if k in row}

def assemble_candidate(cand, sheet, page, block, busV):
    row = {"raw": cand.tag, "tag": cand.tag, "sheet": sheet, "page": page,
           "bbox": _bbox(cand.bbox), "evidence": "one-line", "candidateKind": "breaker"}
    if busV is not None:
        row["busVoltageV"] = busV
    if block:
        row["block"] = block
    order = ("raw", "tag", "sheet", "page", "bbox", "evidence", "busVoltageV", "block", "candidateKind")
    return {k: row[k] for k in order if k in row}
```

- [ ] **Step 4: Run green** — `python -m pytest tests/test_assemble.py -q`. Expected: all passed.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): field assembly -> ExtractedApparatus contract dicts (component 4)"
```

---

## Task 5: Location pass (component 5)

> **Trimmable:** this is the most deferrable task — the E01-11 golden does not exercise it. Keep it if you want the engine's location-association (`evidence:'power-plan'`) path covered on real packages; cut it (and its line in `pipeline`) if the slice needs to stay minimal. Spec §4.4 lists it as a V1 component, so it's included by default.

**Files:**
- Create: `dn_extract/location.py`, `tests/test_location.py`

**Interfaces:**
- Consumes: a power-plan page's `words` + `(sheet_id, page)` + a `PackageProfile`.
- Produces: `location_rows(words, sheet, page, profile) -> list[dict]` — tag-only rows with `evidence:'power-plan'`, no `busVoltageV`, no `block`. The engine associates them by tag to an authoritative one-line row and never counts a power-plan-only device.

- [ ] **Step 1: Write the failing test** — `tests/test_location.py`:

```python
from dn_extract.location import location_rows
from dn_extract.profile import DEFAULT_PROFILE
from tests.helpers import w

def test_location_rows_are_tag_only_power_plan():
    words = [w(644, 1668, 686, 1678, "ACC-1-09-FB"),    # a breaker tag on a power plan
             w(10, 10, 60, 20, "RECEPTACLE"),           # noise, not a breaker tag
             w(700, 700, 760, 712, "1200-3-CU")]        # conductor, not a breaker tag
    rows = location_rows(words, "E02-03D", 38, DEFAULT_PROFILE)
    assert rows == [{"raw": "ACC-1-09-FB", "tag": "ACC-1-09-FB", "sheet": "E02-03D",
                     "page": 38, "bbox": [644.0, 1668.0, 686.0, 1678.0], "evidence": "power-plan"}]
```

- [ ] **Step 2: Run red** — `python -m pytest tests/test_location.py -q`. Expected: FAIL.

- [ ] **Step 3: Implement** — `dn_extract/location.py`:

```python
"""Location pass: breaker-tagged words on power-plan sheets -> tag-only rows (evidence='power-plan')."""
from __future__ import annotations

def location_rows(words, sheet, page, profile):
    rows = []
    for x0, y0, x1, y1, text, *_ in words:
        if profile.is_breaker_suffix(text):
            rows.append({"raw": text, "tag": text, "sheet": sheet, "page": page,
                         "bbox": [round(float(x0), 1), round(float(y0), 1),
                                  round(float(x1), 1), round(float(y1), 1)], "evidence": "power-plan"})
    return rows
```

- [ ] **Step 4: Run green** — `python -m pytest tests/test_location.py -q`. Expected: passed.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): power-plan location pass (component 5)"
```

---

## Task 6: Pipeline + emit + `extract` CLI subcommand (component 6)

**Files:**
- Create: `dn_extract/pipeline.py`, `tests/test_pipeline.py`
- Modify: `dn_extract/__init__.py` (add `extract_artifact`), `drawing_nav.py` (add `extract` subparser)

**Interfaces:**
- Consumes: an open `fitz.Document` (or `FakeDoc`).
- Produces: `extract_artifact(doc, *, pages=None, profile=None, now=None) -> dict` — a full `ExtractionArtifact`. `pages` is an optional iterable of 0-based page numbers (filter); `now` (ISO str) sets `extractedAt` (omitted when `None` for deterministic tests). CLI: `drawing-nav extract <pdf> [--page N] [--out FILE]`.

- [ ] **Step 1: Write the failing test** — `tests/test_pipeline.py`:

```python
from dn_extract.pipeline import extract_artifact
from dn_extract.profile import DEFAULT_PROFILE
from tests.helpers import FakeDoc, FakePage, w

def _e01_11_page():
    words = [w(886.4, 491.4, 944.2, 501.0, "ACC-1-09-FB"), w(886.4, 502.4, 914.4, 512.0, "800AF"),
             w(886.4, 513.3, 914.4, 522.9, "800AT"),       w(886.4, 524.1, 914.4, 533.7, "LSIGE"),
             w(100, 100, 140, 110, "480V"), w(100, 200, 140, 210, "208/120V")]   # multi-bus -> omit
    title = "ONE LINE DIAGRAM - PRIMARY BLOCK P1-110 03.31.2026"
    text = f"SHEET E01-11 {title}"
    return FakePage(words, text=text)

def test_pipeline_multi_bus_sheet_omits_voltage_and_surfaces_warning():
    doc = FakeDoc([FakePage([], text="FB GB AF AT"), _e01_11_page()])   # page0 legend, page1 E01-11
    art = extract_artifact(doc, pages=[1])
    assert art["pdf"].endswith(".pdf")
    assert "extractedAt" not in art                              # deterministic (now=None)
    rows = art["apparatus"]
    assert len(rows) == 1 and rows[0]["tag"] == "ACC-1-09-FB"
    assert "busVoltageV" not in rows[0]                          # multi-bus -> omitted
    assert rows[0]["block"] == "P1-110"
    assert any("multiple LV bus labels" in ww for ww in art["profileWarnings"])

def test_pipeline_stamps_extractedAt_when_now_supplied():
    doc = FakeDoc([FakePage([], text="FB GB AF AT"), _e01_11_page()])
    art = extract_artifact(doc, pages=[1], now="2026-06-25T00:00:00")
    assert art["extractedAt"] == "2026-06-25T00:00:00"
```

  (Note: `extract_artifact` must read each page's sheet id/title. Reuse `drawing_nav.sheet_meta` for real `fitz` pages; for `FakePage` the test supplies `text="SHEET E01-11 ..."` so the same parser works on the fake.)

- [ ] **Step 2: Run red** — `python -m pytest tests/test_pipeline.py -q`. Expected: FAIL.

- [ ] **Step 3: Implement** — `dn_extract/pipeline.py`:

```python
"""Orchestrate the components into a single ExtractionArtifact dict."""
from __future__ import annotations
import os
from .profile import load_profile
from .sheets import in_scope, normalize_block, sheet_voltage
from .discovery import discover
from .assemble import assemble_column, assemble_candidate
from .location import location_rows

# imported lazily to avoid a hard fitz dependency when testing with FakeDoc
def _sheet_meta(page):
    from drawing_nav import sheet_meta
    return sheet_meta(page)

def _is_power_plan(title):
    return "POWER PLAN" in (title or "").upper()

def extract_artifact(doc, *, pages=None, profile=None, now=None):
    profile = profile or load_profile(doc)
    warnings = list(profile.warnings)
    apparatus = []
    n = getattr(doc, "page_count", None) or len(getattr(doc, "_pages", []))
    for page in range(n):
        if pages is not None and page not in pages:
            continue
        pg = doc[page]
        sid, title = _sheet_meta(pg)
        words = pg.get_text("words")
        if in_scope(sid):
            block, bw = normalize_block(title, sid); warnings += bw
            busV, vw = sheet_voltage(words); warnings += vw
            cols, cands = discover(words, profile)
            apparatus += [assemble_column(c, sid, page, block, busV) for c in cols]
            apparatus += [assemble_candidate(c, sid, page, block, busV) for c in cands]
        elif _is_power_plan(title):
            apparatus += location_rows(words, sid, page, profile)

    art = {"pdf": os.path.basename(doc.name), "apparatus": apparatus}
    if warnings:
        # de-dupe preserving order
        seen = set(); art["profileWarnings"] = [x for x in warnings if not (x in seen or seen.add(x))]
    if now is not None:
        art["extractedAt"] = now
    return art
```

  Update `dn_extract/__init__.py` to also export `extract_artifact` (add the import line back).

  Add to `drawing_nav.py` — a new command (after `cmd_ocr`, before `main`):

```python
# -------------------------------------------------------------------------- extract
def cmd_extract(a):
    from datetime import datetime
    from dn_extract.pipeline import extract_artifact
    d = open_pdf(a.pdf)
    pages = [a.page] if a.page is not None else None
    now = None if a.no_timestamp else datetime.now().isoformat(timespec="seconds")
    art = extract_artifact(d, pages=pages, now=now)
    payload = json.dumps(art, indent=2)
    if a.out:
        Path(a.out).write_text(payload, encoding="utf-8")
        print(f"wrote {a.out}  ({len(art['apparatus'])} apparatus, "
              f"{len(art.get('profileWarnings', []))} warnings)")
    else:
        print(payload)
```

  And register it in `main()` (next to the other subparsers):

```python
    s = sub.add_parser("extract"); s.add_argument("pdf")
    s.add_argument("--page", type=int)
    s.add_argument("--out")
    s.add_argument("--no-timestamp", action="store_true")
    s.set_defaults(func=cmd_extract)
```

- [ ] **Step 4: Run green** — `python -m pytest -q` (full suite). Expected: all passed across tasks 1–6.

- [ ] **Step 5: CLI smoke (real PDF, sanity only)** — confirm the command runs end-to-end on one sheet:

```bash
cd /c/Users/jjswe/Tools/drawing-nav
PDF=$(python -c "import json;print(json.load(open('index_elec.json'))['pdf'])")
python drawing_nav.py extract "$PDF" --page 11 --no-timestamp --out e01-11.out.json
python -c "import json;a=json.load(open('e01-11.out.json'));print('rows',len(a['apparatus']),'warns',len(a.get('profileWarnings',[])))"
```
Expected: a row count in the dozens and ≥1 warning (multi-bus). (`*.out.json` is gitignored.)

- [ ] **Step 6: Commit**

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "feat(extract): pipeline + emit + drawing-nav extract subcommand (component 6)"
```

---

## Task 7: Real E01-11 golden e2e (producer proof + engine consumption)

Three sub-deliverables: **7a** a real-PDF producer golden (Windows, local), **7b** the checked-in fixture, **7c** the engine golden (host, mesh-SSH) proving the negative (auto) and positive (operator-voltage-in-test) seam.

**Files:**
- Create: `tests/test_golden_e01_11.py` (producer, local)
- Create: `STAGE/test/fixtures/stack-phx02a-e01-11-extract.json` (engine fixture)
- Create: `STAGE/test/golden-e01-11.test.ts` (engine golden, host)

**Interfaces:**
- Consumes: real E01-11 (page 11) of the Addendum-4 PDF; the Plan-2a-hardened engine (`runTakeoff`, `emitEnvelope`, `candidateKind`, `profileWarnings`, frameA rule).
- Produces: a real `ExtractionArtifact` fixture; proof that (negative) the multi-bus auto extraction surfaces every breaker without silent drops and emits no priced envelope, and (positive) the SAME real geometry prices a real draw-out LSIG main and emits an envelope once an operator supplies voltage.

### 7a — Producer real-data golden (local Windows)

- [ ] **Step 1: Write the failing test** — `tests/test_golden_e01_11.py`:

```python
import json, os, pathlib, pytest
fitz = pytest.importorskip("fitz")
from dn_extract.pipeline import extract_artifact

IDX = pathlib.Path(__file__).resolve().parents[1] / "index_elec.json"
PDF = json.load(open(IDX))["pdf"] if IDX.exists() else ""
pytestmark = pytest.mark.skipif(not (PDF and os.path.exists(PDF)), reason="real Addendum-4 PDF not present")

def _art():
    return extract_artifact(fitz.open(PDF), pages=[11])

def test_e01_11_extracts_breaker_inventory_on_block_p1_110():
    art = _art()
    rows = [r for r in art["apparatus"] if r["sheet"] == "E01-11"]
    assert len(rows) >= 20                                   # dozens of real breaker columns
    assert all(r["block"] == "P1-110" for r in rows)
    assert all(r["evidence"] == "one-line" for r in rows)

def test_e01_11_is_a_conservative_multi_bus_negative():
    art = _art()
    assert all("busVoltageV" not in r for r in art["apparatus"])   # multi-bus -> omitted everywhere
    assert any("multiple LV bus labels" in wmsg for wmsg in art["profileWarnings"])

def test_e01_11_real_anchor_devices_present_with_ratings_in_raw():
    rows = {r.get("tag"): r for r in _art()["apparatus"]}
    assert "ACC-1-09-FB" in rows
    assert "800AF/800AT" in rows["ACC-1-09-FB"]["raw"]             # rating joined for the engine
    assert "LSIGE" in rows["ACC-1-09-FB"]["raw"]
```

- [ ] **Step 2: Run red** — `python -m pytest tests/test_golden_e01_11.py -q`. Expected: FAIL only if a real assertion is wrong (the module imports fine). If the PDF is present it runs; tune `>= 20` to the real count observed in Task 6 Step 5 (do not assert a brittle exact count — assert a floor).

- [ ] **Step 3: Make green** — these pass against the real extractor from Tasks 1–6; adjust only the floor/anchor assertions to the observed real output (the anchors `ACC-1-09-FB … 800AF/800AT … LSIGE` are confirmed present on E01-11). Commit:

```bash
cd /c/Users/jjswe/Tools/drawing-nav && git add -A && git commit -q -m "test(extract): real E01-11 producer golden (multi-bus negative + anchor devices)"
```

### 7b — Generate and check in the engine fixture

- [ ] **Step 4: Produce the real artifact into the engine staging fixtures dir** (deterministic — no timestamp):

```bash
cd /c/Users/jjswe/Tools/drawing-nav
PDF=$(python -c "import json;print(json.load(open('index_elec.json'))['pdf'])")
mkdir -p /c/dev/estimator-takeoff-staging/packages/estimator-takeoff/test/fixtures
python drawing_nav.py extract "$PDF" --page 11 --no-timestamp \
  --out /c/dev/estimator-takeoff-staging/packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11-extract.json
python -c "import json;a=json.load(open(r'C:\dev\estimator-takeoff-staging\packages\estimator-takeoff\test\fixtures\stack-phx02a-e01-11-extract.json'));print('fixture rows',len(a['apparatus']))"
```
Expected: a fixture with the real E01-11 rows, `busVoltageV` absent, `profileWarnings` present.

### 7c — Engine golden (host, mesh-SSH)

- [ ] **Step 5: PULL the current host package into staging** (edit committed truth; one writer):

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && tar -C packages/estimator-takeoff --exclude=node_modules -cf - ." | tar -C /c/dev/estimator-takeoff-staging/packages/estimator-takeoff -xf -
```
(Do this BEFORE writing the test so 2a's merged changes are present locally. Re-add the fixture from Step 4 if the pull overwrote the fixtures dir.)

- [ ] **Step 6: Write the failing test** — `STAGE/test/golden-e01-11.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { runTakeoff, emitEnvelope } from '../src/emit/emit'
import type { ExtractionArtifact } from '../src/extraction/types'

const fixture = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/stack-phx02a-e01-11-extract.json', import.meta.url)), 'utf8'),
) as ExtractionArtifact

describe('golden: real E01-11 (STACK PHX02A Addendum 4)', () => {
  it('e01_11_auto_multibus_surfaces_questions_no_matches', () => {
    expect(fixture.apparatus.every((a) => a.busVoltageV === undefined)).toBe(true)   // conservative omit
    const r = runTakeoff(fixture)
    expect(r.matchedLines).toHaveLength(0)                                            // nothing priced without voltage
    expect(r.operatorQuestions.length).toBeGreaterThan(0)                            // surfaced as questions
    expect(() => emitEnvelope(r, { projectNumber: 'GOLDEN' })).toThrow(/zero matched lines/)
  })

  it('e01_11_with_operator_voltage_assertion_emits_drawout_lsig', () => {
    // Operator Gate-1 voltage assertion (the extractor correctly refused to guess this on a multi-bus sheet).
    // V1 demonstration: assert the dominant 480V main bus; per-device voltage association is a later slice.
    const asserted: ExtractionArtifact = {
      ...fixture,
      apparatus: fixture.apparatus.map((a) => ({ ...a, busVoltageV: 480 })),
    }
    const r = runTakeoff(asserted)
    expect(r.matchedLines.length).toBeGreaterThan(0)
    expect(r.matchedLines.some((m) => m.ref === 'Circuit Breaker LV - Draw-Out (LSIG)')).toBe(true)
    const env = emitEnvelope(r, { projectNumber: 'GOLDEN' })                         // must not throw
    expect(env).toBeDefined()
  })
})
```

- [ ] **Step 7: scp the fixture + test to host, run red, then green** — per-file transport (never whole-dir):

```bash
scp /c/dev/estimator-takeoff-staging/packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11-extract.json \
    olares-mesh:/home/olares/code/apex/apex-power-ops-platform/packages/estimator-takeoff/test/fixtures/
scp /c/dev/estimator-takeoff-staging/packages/estimator-takeoff/test/golden-e01-11.test.ts \
    olares-mesh:/home/olares/code/apex/apex-power-ops-platform/packages/estimator-takeoff/test/
ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && export PATH=\$HOME/.nvm/versions/node/v20.20.2/bin:\$PATH && pnpm --filter @apex/estimator-takeoff test golden-e01-11"
```
Expected: 2 passed. If the positive case finds zero draw-out LSIG matches, verify the fixture's `ACC-1-09-FB`-class rows carry `800AF/800AT … LSIGE` in `raw` (frame ≥ 800 + a ground function is what triggers the draw-out estimating baseline → the LSIG ref).

- [ ] **Step 8: Typecheck + commit on host**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && export PATH=\$HOME/.nvm/versions/node/v20.20.2/bin:\$PATH && pnpm --filter @apex/estimator-takeoff typecheck && pnpm --filter @apex/estimator-takeoff test"
ssh olares-mesh "cd /home/olares/code/apex/apex-power-ops-platform && git add packages/estimator-takeoff/test/golden-e01-11.test.ts packages/estimator-takeoff/test/fixtures/stack-phx02a-e01-11-extract.json && git commit -m 'test(estimator-takeoff): real E01-11 golden — multi-bus negative + operator-voltage positive seam'"
```
Expected: full engine suite green (55 Plan-1 + Plan-2a additions + 2 golden); typecheck clean.

---

## Self-Review

**1. Spec coverage (rev4):**
- §3.1 artifact shape / §3.2 producer side (`candidateKind` on Pass-B only; never on non-breakers; `profileWarnings`) → Tasks 4, 6; contract honored, frame/functions only inside `raw`.
- §4.1 legend-profile → Task 1 (default-authoritative + best-effort confirm + warning; legend-suffix *augmentation* explicitly deferred).
- §4.2 two-pass discovery (AF/AT columns + Pass-B suffix candidates; conductor decoy excluded; split tags rejoined; no silent drops) → Task 3.
- §4.3 field assembly + block normalization (canonical map wins, determinism over title variants incl. the `R1-110/210` slash) + voltage rule (single LV & no MV → broadcast; else omit; transformer-ratio tokens excluded; `480V,3φ,`→480) → Tasks 2, 4.
- §4.4 location pass → Task 5 (flagged trimmable).
- §6 fail-open-to-question (omit voltage, Pass-B candidate, default-profile warning) → Tasks 2/3/4/6.
- §7 testing — engine min set lands in Plan 2a; the **golden e2e** is Task 7. **Deviation from §7, operator-ratified 2026-06-25:** §7 names "extract the real E01-11 → known mains/feeders matched → envelope emits." Real data shows E01-11 is **multi-bus**, so the conservative voltage rule (correctly) omits voltage there → 0 matched under pure auto. Resolution: E01-11 is the **negative** golden (auto → surfaced questions, no envelope); the **positive** golden injects the operator's 480V assertion into the SAME real artifact in-test (Task 7c). No in-scope sheet is both single-bus and has matchable breakers (the ≥800AF+G mains live on the multi-bus primary blocks; the single-bus mech-gallery sheets carry only sub-800AF LSI feeders), so a pure-auto real-data priced envelope is not achievable in V1 — it is the headline of the deferred operator-voltage-assertion slice.

**2. Placeholder scan:** none — every step carries the exact file, code, command, and expected output. Task 7a's count floor (`>= 20`) and anchor tuning are explicitly "assert a floor, confirm against observed real output," not a placeholder.

**3. Type/contract consistency:** emitted keys (`raw, tag, sheet, page, bbox, evidence, busVoltageV, block, candidateKind`) match `ExtractedApparatus` exactly; `profileWarnings`/`extractedAt` match `ExtractionArtifact`; `raw` format (`<tag> <frame>AF/<trip>AT <functions>`) matches the Plan-1 fixture and the engine's `FRAME_TRIP`; the golden's `'Circuit Breaker LV - Draw-Out (LSIG)'` ref matches `breaker-map.data.ts`; `runTakeoff`/`emitEnvelope`/`emitEnvelope … zero matched lines` match `emit.ts`.

**4. Decision log (this slice):** voltage rule unchanged (conservative, operator-ratified); no `mountingHint` in V1; no CLI voltage override in V1 (test injection only); `--assert-voltage <sheet>:<block>=<V>` (persisted as evidence, never inferred) is the next slice; drawing-nav stays standalone (relocation into monorepo `tools/` deferred).

## Cross-engine review dispositions (Codex, post-execution 2026-06-25)

A Codex adversarial pass (fail-closed + test-honesty lenses) over the producer seam returned 7 findings. Triaged against real E01-11 data:

**Applied (committed):**
- *Discovery hardening* (Findings 3/4/6): nearest-unconsumed-AT pairing + consumed-reuse guard; tag-join excludes AF/AT/function tokens (stacked-breaker safety); Pass-B suppresses bare-suffix fragments (`MCB`/`MBB`/`-FB`) — verified real on E01-11 (5→2 clean candidates). +3 adversarial geometry tests. Producer commit `42addd2`.
- *Engine `NON_BREAKER` alignment* (Finding 2, bounded form): added `STS` so the engine backstop matches the producer profile. Engine commit `a3ca260a`.
- *Golden honesty* (Findings 1/7): positive golden now asserts the matched line's `mountingBasis === 'estimating_baseline'` (construction is a provenance-surfaced ASSUMPTION, not read evidence); negative golden asserts a real surfacing floor (≥20 questions), not merely non-empty.

**Rejected with rationale (challenged Codex):**
- *Finding 2's proposed fix* ("reject any tag containing a non-breaker token") — would false-drop **15 real UPS-system breakers** on E01-11 (`UPS-…-MIB/MOB/MBB/LBB`, where `UPS` is a *system prefix*, not a device type). Replaced with the precise one-token `STS` alignment above.
- *Finding 1's "remove the estimating baseline"* — the `≥800AF+G → draw_out` baseline is a **pre-existing, intentional Plan-1 design** that surfaces `mountingBasis:'estimating_baseline'` into the envelope (the estimator sees construction was ASSUMED and can override). Removing it is an operator-level product decision, out of this slice's scope.

**Deferred (bounded follow-ups, documented):**
- *Finding 5 — split `kV` tokens* (`13.8` + `KV` as separate words): not exhibited in this package (real kV labels are single tokens, verified); multi-token voltage assembly rides the geometric per-device voltage slice.
- *UPS-prefix over-exclusion*: the engine's word-boundary `NON_BREAKER` treats `UPS-…-MIB` (a real breaker) as a non-breaker → surfaced for confirmation rather than priced (fail-closed, but imprecise). Pre-existing; device-type-vs-prefix disambiguation is a separate engine design item.

## Execution Handoff

Plan 2b depends on Plan 2a (the engine must already carry `candidateKind`, `profileWarnings`, and the frameA rule). Recommended order: **execute Plan 2a first** (engine seam), then Plan 2b Tasks 1–6 (producer, local Windows), then Task 7 (golden, spanning local producer + host engine). Recommended execution: **Subagent-Driven** — fresh implementer + reviewer per task. Producer tasks run entirely local (`python -m pytest`, local git); only Task 7c uses the mesh-SSH host mechanic. Cross-engine (Codex) review at the discovery + voltage seams is load-bearing.
