"""
SC3 field-facing terminology layer (task #129; reference/tcc/SC3-FIELD-TERMINOLOGY-DRAFT.md).

Verifies:
    services.neta.terminology.resolve_lineage — the pure trip-lineage assignment
    rule (name patterns + the two data-faithful per-sensor overrides);
    assemble_terminology — dictionary-row -> display-block assembly with
    lineage -> '*' fallback, the DT-310 Override exception, and the ruled
    trust/method/note vocabulary (Q1–Q5, operator 2026-06-11);
    GET /settings/{sensor_id} — serves the terminology block when the governed
    tcc.field_terminology dictionary is reachable, and fails OPEN (block simply
    omitted, 200) when it is not.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from config import get_db
from main import app
from services.neta import terminology
from services.neta.terminology import assemble_terminology, resolve_lineage

from test_settings_route import _FakeSettingsDb, _MappingRow, _Result


# ── the lineage rule (pure) ─────────────────────────────────────────────────

def test_lineage_micrologic_iec_flagship_3833():
    assert resolve_lineage("Square D", "MASTERPACT NW", "MICROLOGIC 6.0A") == "micrologic_iec"


def test_lineage_micrologic_iec_via_compact_nsx_generation():
    assert resolve_lineage("Square D", "Micrologic 6.2E", "Micrologic 6.2E") == "micrologic_iec"


def test_lineage_earth_leakage_per_sensor_override_wins():
    # Micrologic 7.0 (Vigi): the element is earth leakage, NOT ground fault (§134).
    assert (
        resolve_lineage("Square D", "Micrologic 7.0", "Micrologic 7.0", gfpu_name="Earth Leakage Pickup")
        == "micrologic_7x_el"
    )


def test_lineage_sqd_branded_dt_is_digitrip_not_micrologic():
    assert resolve_lineage("Square D", "DT 810D", "DT 810D LSG") == "digitrip"


def test_lineage_series_b_era_uses_default_vocabulary():
    # 'Micrologic Std'/'Full' (no generation digit) = the Series-B-era ANSI units
    # whose catalog captions equal the default labels (0602CT9201R201).
    assert resolve_lineage("Square D", "Micrologic Std", "MX 250-800") == "*"


def test_lineage_pxr():
    assert resolve_lineage("Eaton", "PXR 25", "PDG3 LSI") == "pxr"


def test_lineage_ge_mvt_and_entelliguard():
    assert resolve_lineage("GE", "MVT-PM", "MVT-PM 9D") == "ge_mvt_eg"
    assert resolve_lineage("GE", "Entelliguard TU", "Entelliguard") == "ge_mvt_eg"


def test_lineage_ekip_pr():
    assert resolve_lineage("ABB", "Ekip Dip", "XT2 LSIG") == "ekip_pr"
    assert resolve_lineage("ABB", "PR221DS [IEC]", "PR221DS-LS T1") == "ekip_pr"


def test_lineage_siemens_etu_but_not_legacy_static():
    assert resolve_lineage("Siemens", "ETU 350", "ETU 350 LSI") == "siemens_etu"
    # SB-TL is the legacy static lineage — plain-English faceplates, default vocab.
    assert resolve_lineage("Siemens", "SB-TL", "SB-TL") == "*"


def test_lineage_legacy_static_default():
    assert resolve_lineage("West", "Seltronic", "Seltronic LS") == "*"
    assert resolve_lineage("West", "Amptector I-A", "LSG") == "*"


# ── assembly (pure; dictionary rows as served from tcc.field_terminology) ───

def _dict_rows():
    """A minimal approved-row set mirroring migration 026's shape."""
    rows = []

    def el(lineage, key, short, label, symbol=None, note=None):
        rows.append({
            "namespace": "element", "lineage": lineage, "term_key": key,
            "label_short": short, "label_long": label, "symbol": symbol,
            "method_text": note, "basis": "test", "status": "approved",
        })

    for key, label in [
        ("ltpu", "Long-Time Pickup"), ("ltd", "Long-Time Delay"),
        ("stpu", "Short-Time Pickup"), ("std", "Short-Time Delay"),
        ("inst", "Instantaneous"), ("gfpu", "Ground-Fault Pickup"),
        ("gfd", "Ground-Fault Delay"),
    ]:
        el("*", key, key.upper() if key != "inst" else "INST", label)
    el("micrologic_iec", "ltpu", "LTPU", "Long-Time Pickup", symbol="Ir")
    el("micrologic_iec", "ltd", "LTD", "Long-Time Delay", symbol="tr")
    el("micrologic_7x_el", "gfpu", "EL", "Earth-Leakage Pickup", symbol="IΔn",
       note="Earth-leakage (residual current) element — not a ground-fault overcurrent test.")
    rows.extend([
        {"namespace": "trust", "lineage": "*", "term_key": "delay.unsupported",
         "label_short": "N/A", "label_long": "No certified trip time — record measured; accept per manufacturer TCC",
         "symbol": None, "method_text": "No certified trip time.", "basis": "test", "status": "approved"},
        {"namespace": "trust", "lineage": "*", "term_key": "delay.db",
         "label_short": "MFR", "label_long": "Manufacturer time band (validated)",
         "symbol": None, "method_text": None, "basis": "test", "status": "approved"},
        {"namespace": "method", "lineage": "*", "term_key": "timing_source.band_table",
         "label_short": "Manufacturer delay band (per-sensor)", "label_long": None,
         "symbol": None, "method_text": None, "basis": "test", "status": "approved"},
        {"namespace": "setting", "lineage": "*", "term_key": "plug",
         "label_short": "Rating plug (In)", "label_long": "Rating plug (In)",
         "symbol": "In", "method_text": None, "basis": "test", "status": "approved"},
        {"namespace": "setting", "lineage": "*", "term_key": "test_current",
         "label_short": "Test Current", "label_long": "Test Current (x pickup)",
         "symbol": None, "method_text": None, "basis": "test", "status": "approved"},
        {"namespace": "note", "lineage": "*", "term_key": "sheet_footer",
         "label_short": "footer", "label_long": "Acceptance values are manufacturer tolerances.",
         "symbol": None, "method_text": None, "basis": "test", "status": "approved"},
    ])
    return rows


def test_assemble_lineage_symbols_with_default_fallback():
    block = assemble_terminology(_dict_rows(), "micrologic_iec")
    assert block["lineage"] == "micrologic_iec"
    assert block["elements"]["ltpu"] == {
        "code": "LTPU", "label": "Long-Time Pickup", "symbol": "Ir", "note": None,
    }
    # stpu has no micrologic_iec row in this fixture -> falls back to '*' (no symbol).
    assert block["elements"]["stpu"]["label"] == "Short-Time Pickup"
    assert block["elements"]["stpu"]["symbol"] is None
    assert block["plug_label"] == "Rating plug (In)"
    assert block["test_current_label"] == "Test Current"
    assert block["trust"]["delay.unsupported"]["badge"] == "N/A"
    assert block["method_labels"]["band_table"] == "Manufacturer delay band (per-sensor)"
    assert block["notes"]["sheet_footer"].startswith("Acceptance values")


def test_assemble_earth_leakage_correction():
    block = assemble_terminology(_dict_rows(), "micrologic_7x_el")
    gfpu = block["elements"]["gfpu"]
    assert gfpu["code"] == "EL"
    assert gfpu["label"] == "Earth-Leakage Pickup"
    assert gfpu["symbol"] == "IΔn"
    assert "not a ground-fault overcurrent test" in gfpu["note"]
    # gfd falls back to '*' here (fixture has no 7x gfd row).
    assert block["elements"]["gfd"]["label"] == "Ground-Fault Delay"


def test_assemble_dt310_override_exception():
    block = assemble_terminology(_dict_rows(), "digitrip", inst_name="Override")
    inst = block["elements"]["inst"]
    assert inst["label"] == "Override (fixed)"
    assert "not separately settable" in inst["note"]


def test_assemble_returns_none_on_empty_dictionary():
    assert assemble_terminology([], "micrologic_iec") is None


# ── route integration: /settings serves the block; fails open without it ────

class _TerminologyFakeDb(_FakeSettingsDb):
    """The settings fake + the SC3 queries (sensor element names + dictionary)."""

    def __init__(self, *args, terminology_rows=None, sensor_names=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._terminology_rows = terminology_rows or []
        self._sensor_names = sensor_names or {}

    def execute(self, statement, params=None):
        sql = str(statement)
        if "FROM tcc.field_terminology" in sql:
            return _Result([_MappingRow(mapping=row) for row in self._terminology_rows])
        if "gfpu_name" in sql and "FROM tcc.etu_sensors" in sql:
            return _Result(_MappingRow(mapping=self._sensor_names))
        return super().execute(statement, params)


_SETTINGS_PAYLOAD = {
    "plug_values": [400, 600, 800, 1000, 1200],
    "ltpu_settings": [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 1.0],
    "ltd_settings": [],
    "ltd_multipliers": [],
    "stpu_settings": [1.5, 2, 3, 4, 5, 6, 8, 10],
    "inst_settings": [2, 3, 4, 6, 8, 10, 12, 15],
    "gfpu_settings": [0.2, 0.3, 0.4],
}

_CTX = {
    "manufacturer_name": "Square D",
    "trip_type_name": "MASTERPACT NW",
    "trip_style_name": "MICROLOGIC 6.0A",
    "ltpu_step": None, "stpu_step": None, "inst_step": None, "gfpu_step": None,
    "maint_inst_step": None, "maint_gfpu_step": None,
}


def test_settings_route_serves_terminology_block():
    terminology.clear_cache()
    client = TestClient(app)
    fake_db = _TerminologyFakeDb(
        settings_payload=_SETTINGS_PAYLOAD,
        context_mapping=_CTX,
        terminology_rows=_dict_rows(),
        sensor_names={"gfpu_name": "GF Pickup", "inst_name": "Inst Pickup"},
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/3833")
        assert resp.status_code == 200
        term = resp.json().get("terminology")
        assert term is not None
        assert term["lineage"] == "micrologic_iec"
        assert term["elements"]["ltpu"]["symbol"] == "Ir"
        assert term["plug_label"] == "Rating plug (In)"
    finally:
        app.dependency_overrides.pop(get_db, None)
        terminology.clear_cache()


def test_settings_route_fails_open_without_dictionary():
    # The plain settings fake raises on the SC3 queries -> the block is simply
    # omitted and the route still serves 200 (vocabulary can never 500 serving).
    terminology.clear_cache()
    client = TestClient(app)
    fake_db = _FakeSettingsDb(settings_payload=_SETTINGS_PAYLOAD, context_mapping=_CTX)
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/3833")
        assert resp.status_code == 200
        assert resp.json().get("terminology") is None
    finally:
        app.dependency_overrides.pop(get_db, None)
        terminology.clear_cache()
