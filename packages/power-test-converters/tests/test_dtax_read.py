"""Chip 10c — DTAX-read round-trip tests.

read_dtax inverts the DataModel-R2 schema that write_dtax emits, producing the same PtmModel
that read_ptm produces. We validate by round-trip: build a model (via the proven read_ptm sample),
write_dtax it (no template — programmatic build), read_dtax it back, assert reconstruction.
"""
from __future__ import annotations

from pathlib import Path

from power_test_converters.dtax import write_dtax
from power_test_converters.dtax_read import read_dtax
from power_test_converters.ptm import read_ptm

# Reuse the proven sample .ptm builder from the sibling writer test (same tests dir, on sys.path).
from test_ptm_to_dtax import _write_sample_ptm


def test_read_dtax_roundtrips_transformer_nameplate(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))
    dtax_path = write_dtax(model, tmp_path / "out.dtax")

    result = read_dtax(dtax_path)

    assert result.transformer.serial_number == model.transformer.serial_number == "45120269-001-08"
    assert result.transformer.manufacturer == model.transformer.manufacturer == "Square D"
    assert result.transformer.apparatus_id == model.transformer.apparatus_id == "XFM-1001"
