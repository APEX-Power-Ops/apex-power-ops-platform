"""SC3 field-facing terminology layer (task #129).

Spec + rulings of record: ``reference/tcc/SC3-FIELD-TERMINOLOGY-DRAFT.md``
(operator red-line 2026-06-11: Q1 "LG Pickup" = EP-internal Local Ground, never
shown; Q2 db badge = MFR; Q3 unsupported badge = N/A; Q4 symbols on Screen 2 +
the sheet; Q5 "Test Current"). The governed dictionary is
``tcc.field_terminology`` (migration 026) — the "verbiage" slice of
ARCHITECTURE Decision 013 — and every field surface (lvbreakertcc Screen 2/3,
the B2.1 tolerance sheet) reads THIS one mapping, resolved

    COALESCE(approved row @ lineage, approved row @ '*', caller's fallback)

Only ``status='approved'`` rows serve. Everything here is fail-open by design:
a missing table, query error, or empty dictionary yields ``None`` and the
caller omits the block — the UI keeps its built-in labels and vocabulary can
never 500 a serving route.

Lineage assignment is a pure name-pattern rule over the sensor's
(manufacturer, trip type, trip style) plus two data-faithful per-sensor
overrides taken from EasyPower's own element-name columns:

  * ``gfpu_name = 'Earth Leakage Pickup'`` → ``micrologic_7x_el`` — the
    Micrologic 7.0 Vigi residual-current element is earth leakage, NOT ground
    fault (STATE §134); labeling it GFPU misnames the test.
  * ``inst_name = 'Override'`` (Eaton DT 310) → the INST row is a fixed
    override, not a settable pickup.

EP's legacy ``'LG Pickup'`` caption (1,623 sensors, the Digitrip/GE/legacy
generation) is deliberately NOT a lineage signal beyond evidence: per the Q1
ruling it is EasyPower-librarian shorthand for the breaker-integral ("local")
ground element and never appears on a field surface.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

ELEMENT_KEYS = ("ltpu", "ltd", "stpu", "std", "inst", "gfpu", "gfd")

# Built-in element fallbacks — mirrors the '*' rows of migration 026 so a
# partially-seeded dictionary still yields a complete element set.
_DEFAULT_ELEMENTS = {
    "ltpu": ("LTPU", "Long-Time Pickup"),
    "ltd": ("LTD", "Long-Time Delay"),
    "stpu": ("STPU", "Short-Time Pickup"),
    "std": ("STD", "Short-Time Delay"),
    "inst": ("INST", "Instantaneous"),
    "gfpu": ("GFPU", "Ground-Fault Pickup"),
    "gfd": ("GFD", "Ground-Fault Delay"),
}

_CACHE_TTL_SECONDS = 300.0
_cache: dict = {"at": 0.0, "rows": None}


def clear_cache() -> None:
    _cache["at"] = 0.0
    _cache["rows"] = None


# ── lineage assignment (pure) ────────────────────────────────────────────────

_MICROLOGIC_IEC_RE = re.compile(r"micrologic\s*[1-7]\.[0-9]")
_DT_RE = re.compile(r"\bdt\s*[0-9]{3}")
_PR_SERIES_RE = re.compile(r"\bpr[0-9]{3}")


def resolve_lineage(
    mfr_name: Optional[str],
    trip_type_name: Optional[str],
    trip_style_name: Optional[str],
    gfpu_name: Optional[str] = None,
) -> str:
    """The per-sensor trip LINEAGE keying the terminology dictionary.

    Conservative by construction (label law L1/L4): anything unmatched serves
    the '*' default vocabulary, which is itself catalog-confirmed (the Series-B
    captions are identical to it) — so a miss can only under-decorate, never
    mislabel.
    """
    if (gfpu_name or "").strip() == "Earth Leakage Pickup":
        return "micrologic_7x_el"

    m = (mfr_name or "").strip().lower()
    t = " ".join(filter(None, [trip_type_name or "", trip_style_name or ""])).lower()

    # Digitrip lineage first: Square D / Siemens carry brand-twin "DT ..." types
    # that must NOT fall into the Micrologic / ETU buckets.
    if _DT_RE.search(t) or "digitrip" in t or "optim" in t:
        return "digitrip"
    if ("eaton" in m or "cutler" in m or "west" in m) and (
        "pxr" in t or "power defense" in t
    ):
        return "pxr"
    if any(k in m for k in ("square d", "sqd", "schneider", "merlin gerin")) and (
        _MICROLOGIC_IEC_RE.search(t)
    ):
        # The IEC Micrologic generations (2.0…7.x A/E/H/P/X, Masterpact NW/NT,
        # Compact NS/NSX, PowerPact P/R) — Ir/tr dial faces. 'Micrologic Std' /
        # 'Full' (no generation digit) are the Series-B-era ANSI units whose
        # captions equal the default vocabulary, so they intentionally miss.
        return "micrologic_iec"
    if m in ("ge", "general electric") and any(
        k in t for k in ("mvt", "versatrip", "rms-9", "power+", "entelliguard")
    ):
        return "ge_mvt_eg"
    if ("abb" in m or "sace" in m) and ("ekip" in t or _PR_SERIES_RE.search(t)):
        return "ekip_pr"
    if "siemens" in m and any(
        k in t for k in ("etu", "3wa", "3va", "sentron")
    ):
        return "siemens_etu"
    return "*"


# ── dictionary load (fail-open, cached) ──────────────────────────────────────

def _load_rows(db) -> Optional[list[dict]]:
    now = time.monotonic()
    if _cache["rows"] is not None and (now - _cache["at"]) < _CACHE_TTL_SECONDS:
        return _cache["rows"]
    try:
        result = db.execute(
            text(
                """
                SELECT namespace, lineage, term_key, label_short, label_long,
                       symbol, method_text
                FROM tcc.field_terminology
                WHERE status = 'approved'
                """
            )
        ).fetchall()
    except Exception as exc:  # fail-open: vocabulary must never break serving
        rollback = getattr(db, "rollback", None)
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass
        logger.warning("field_terminology unavailable: %s", exc)
        return None
    rows = [dict(r._mapping) if hasattr(r, "_mapping") else dict(r) for r in result]
    if rows:
        _cache["rows"] = rows
        _cache["at"] = now
    return rows or None


def _sensor_element_names(db, sensor_id: int) -> dict:
    """The per-sensor EP element-name columns driving the two data-faithful
    overrides (earth leakage / DT-310 Override). Fail-open to {}."""
    try:
        row = db.execute(
            text(
                "SELECT gfpu_name, inst_name FROM tcc.etu_sensors WHERE id = :sid"
            ),
            {"sid": sensor_id},
        ).fetchone()
    except Exception:
        rollback = getattr(db, "rollback", None)
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass
        return {}
    if row is None:
        return {}
    mapping = getattr(row, "_mapping", None)
    return dict(mapping) if mapping is not None else {}


# ── assembly (pure) ──────────────────────────────────────────────────────────

def _index(rows: list[dict]) -> dict:
    return {
        (r.get("namespace"), r.get("lineage"), r.get("term_key")): r for r in rows
    }


def _pick(idx: dict, namespace: str, lineage: str, key: str) -> Optional[dict]:
    return idx.get((namespace, lineage, key)) or idx.get((namespace, "*", key))


def assemble_terminology(
    rows: list[dict],
    lineage: str,
    inst_name: Optional[str] = None,
) -> Optional[dict]:
    """Build the served terminology block from dictionary rows (pure).

    Returns ``None`` when the dictionary is empty (fail-open) — the UI then
    keeps its built-in labels.
    """
    if not rows:
        return None
    idx = _index(rows)

    elements: dict = {}
    for key in ELEMENT_KEYS:
        row = _pick(idx, "element", lineage, key)
        if row is not None:
            elements[key] = {
                "code": row.get("label_short") or _DEFAULT_ELEMENTS[key][0],
                "label": row.get("label_long") or _DEFAULT_ELEMENTS[key][1],
                "symbol": row.get("symbol"),
                "note": row.get("method_text"),
            }
        else:
            code, label = _DEFAULT_ELEMENTS[key]
            elements[key] = {"code": code, "label": label, "symbol": None, "note": None}

    # Eaton DT 310 (DB-EP): the instantaneous is a fixed override, not a dial.
    if (inst_name or "").strip().lower() == "override":
        elements["inst"] = {
            "code": "INST",
            "label": "Override (fixed)",
            "symbol": None,
            "note": "Instantaneous is a fixed override on this trip unit — "
                    "not separately settable (EasyPower inst_name='Override').",
        }

    trust: dict = {}
    for key in ("pickup.db", "delay.db", "delay.verify", "delay.unsupported"):
        row = _pick(idx, "trust", lineage, key)
        if row is not None:
            trust[key] = {
                "badge": row.get("label_short"),
                "text": row.get("label_long"),
                "method_text": row.get("method_text"),
            }

    method_labels: dict = {}
    for (ns, lin, key), row in idx.items():
        if ns != "method" or lin not in (lineage, "*"):
            continue
        short = key.removeprefix("timing_source.")
        if short not in method_labels or lin == lineage:
            method_labels[short] = row.get("label_short")

    notes: dict = {}
    for key in ("withheld", "est", "plot_caveat", "sheet_footer"):
        row = _pick(idx, "note", lineage, key)
        if row is not None:
            notes[key] = row.get("label_long")

    plug_row = _pick(idx, "setting", lineage, "plug")
    test_row = _pick(idx, "setting", lineage, "test_current")

    return {
        "lineage": lineage,
        "elements": elements,
        "plug_label": plug_row.get("label_short") if plug_row else None,
        "test_current_label": test_row.get("label_short") if test_row else None,
        "trust": trust or None,
        "method_labels": method_labels or None,
        "notes": notes or None,
    }


# ── route entry point ────────────────────────────────────────────────────────

def build_terminology_block(db, sensor_id: int, ctx: dict) -> Optional[dict]:
    """The /settings entry point: resolve the sensor's lineage from the calc
    context (+ the per-sensor element-name overrides) and assemble the block
    from the governed dictionary. Every failure path returns ``None``."""
    try:
        names = _sensor_element_names(db, sensor_id)
        lineage = resolve_lineage(
            ctx.get("manufacturer_name"),
            ctx.get("trip_type_name"),
            ctx.get("trip_style_name"),
            gfpu_name=names.get("gfpu_name"),
        )
        rows = _load_rows(db)
        if not rows:
            return None
        return assemble_terminology(rows, lineage, inst_name=names.get("inst_name"))
    except Exception as exc:  # belt + suspenders: never break /settings
        logger.warning("terminology block failed for sensor %s: %s", sensor_id, exc)
        return None
