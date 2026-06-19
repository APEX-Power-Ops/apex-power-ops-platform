from records_import.proposal import ProposedValue
from records_import.review import build_proposal

FS = {"sections": [
    {"key": "turns_ratio", "capture_mode": "instrument_import", "kind": "table",
     "table": {"row_dim": {"rows": [{"key": "h_x"}, {"key": "h_y"}, {"key": "x_y"}]},
               "columns": [{"tag": "measured_ratio"}, {"tag": "deviation_pct"}, {"tag": "nominal_ratio"}, {"tag": "tap"}]}},
    {"key": "excitation_current", "capture_mode": "instrument_import", "kind": "fields",
     "fields": [{"tag": "phase_a"}, {"tag": "phase_b"}, {"tag": "phase_c"}, {"tag": "pattern"}]},
    {"key": "nameplate", "kind": "fields", "fields": [{"tag": "manufacturer"}]},
]}


def test_mapped_unmapped_pending():
    proposed = [
        ProposedValue("turns_ratio.h_x.measured_ratio", "turns_ratio", value_numeric=10.0),
        ProposedValue("excitation_current.phase_a", "excitation_current", value_numeric=0.01),
        ProposedValue("turns_ratio.z_z.measured_ratio", "turns_ratio", value_numeric=1.0),  # bad row
    ]
    p = build_proposal(proposed, FS)
    keys = {v.field_key for v in p.mapped}
    assert keys == {"turns_ratio.h_x.measured_ratio", "excitation_current.phase_a"}
    assert [v.field_key for v in p.unmapped] == ["turns_ratio.z_z.measured_ratio"]
    assert "excitation_current.phase_b" in p.pending
    assert "turns_ratio.h_x.deviation_pct" in p.pending
    # non-instrument sections never appear as pending
    assert "nameplate.manufacturer" not in p.pending
    # the 'tap' column is not an importable target
    assert not any(k.endswith(".tap") for k in p.pending)


def test_pending_excludes_filled():
    proposed = [ProposedValue("excitation_current.phase_a", "excitation_current", value_numeric=0.01)]
    p = build_proposal(proposed, FS)
    assert "excitation_current.phase_a" not in p.pending
    assert "excitation_current.phase_b" in p.pending
