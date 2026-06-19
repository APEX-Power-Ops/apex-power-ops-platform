"""DTAX-read (Chip 10c): parse a Doble DataModel-R2 (.dtax) file into a PtmModel.

The inverse of `write_dtax` — it reads the same containers the writer fills, producing the same
`PtmModel` that `read_ptm` produces, so the records-import pipeline (map -> propose -> commit)
is reused unchanged. Built incrementally per test domain; see
docs/superpowers/plans/2026-06-17 / 2026-06-19-chip10c-dtax-read.md.

Additive: this module does NOT modify the settled writer (dtax.py), model, or read_ptm.
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from power_test_converters.model import PtmModel, PtmTransformer

_NAMEPLATE = "two-winding-transformer-nameplate"


def read_dtax(path: str | Path) -> PtmModel:
    """Parse a .dtax (Doble DataModel-R2) file into a PtmModel."""
    source = Path(path)
    root = ET.parse(source).getroot()
    if root.tag != "DataModel-R2":
        raise ValueError(f"Not a Doble DataModel-R2 file: {source}")
    return PtmModel(
        source_path=source,
        transformer=_read_transformer(root),
        bushings=[],
        tap_changers=[],
        location=None,
        job=None,
        overall_power_factor=[],
        bushing_power_factor=[],
    )


def _read_transformer(root: ET.Element) -> PtmTransformer:
    nameplate = root.find(_NAMEPLATE)
    attrs = nameplate.attrib if nameplate is not None else {}
    return PtmTransformer(
        source_id="",
        serial_number=attrs.get("serial-num", ""),
        manufacturer=attrs.get("mfr", ""),
        manufacturing_year=attrs.get("year-mfg", ""),
        apparatus_id=attrs.get("special-id", ""),
    )
