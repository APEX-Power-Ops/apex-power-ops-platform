"""Phase 6 (end-to-end): model -> proposal -> commit, against the real records_dev xfmr schema.

Uses a realistic PtmModel literal (read_ptm is validated upstream by the converter's own suite, so 10a
does not rebuild a 550-line .ptm fixture; the file entry `ingest.propose` is exercised at Chip-10
integration with a committed sample). Proves: dry-run proposes without writing; commit writes only the
mapped values (partial fill) with provenance; re-commit is idempotent.
"""
import os
import uuid
from pathlib import Path

import psycopg
import pytest
from power_test_converters.model import (
    PtmModel, PtmTransformer, PtmInstrumentInfo,
    PtmTurnsRatioTest, PtmTurnsRatioMeasurement,
    PtmWindingResistanceTest, PtmWindingResistanceMeasurement,
    PtmExcitingCurrentTest, PtmExcitingCurrentMeasurement,
    PtmPowerFactorMeasurement,
)

from records_import import db, ingest

PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)
INST = PtmInstrumentInfo(test_set_name="TESTRANO 600", serial_number="GH733Y")


def _sample_model():
    ttr = PtmTurnsRatioTest(source_test_id="t1", instrument=INST, measurements=[
        PtmTurnsRatioMeasurement(measured_at="2026-06-01T10:00:00", name="H-X", phase="H-X",
                                 nominal_ratio=10.0, voltage_turns_ratio=10.02, ratio_deviation=0.2)])
    wr = PtmWindingResistanceTest(source_test_id="w1", instrument=INST, reference_temperature_c=75.0, measurements=[
        PtmWindingResistanceMeasurement(measured_at="2026-06-01T10:05:00", name="H", phase="H",
                                        resistance_measured_ohm=0.500, resistance_corrected_ohm=0.512)])
    ex = PtmExcitingCurrentTest(source_test_id="e1", instrument=INST, measurements=[
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:00", phase="A", current_corrected_a=0.011),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:01", phase="B", current_corrected_a=0.009),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:02", phase="C", current_corrected_a=0.012)])
    pf = PtmPowerFactorMeasurement(
        source_test_id="p1", source_test_name="Overall", measured_at="2026-06-01T10:15:00",
        measurement_name="ICH", measurement_type="overall", transformer_winding="",
        transformer_overall_capacitance="", mode="", test_frequency_hz=60.0, requested_voltage_v=10000.0,
        voltage_out_v=10000.0, current_measured_a=0.0, current_corrected_a=0.0, capacitance_measured_f=1.1e-9,
        watt_losses=0.0, power_factor_measured=0.31, power_factor_corrected=0.30, correction_factor=1.0,
        grade="Good", instrument=INST)
    return PtmModel(source_path=Path("x.ptm"), transformer=PtmTransformer(source_id="s"), bushings=[],
                    tap_changers=[], location=None, job=None, overall_power_factor=[pf], bushing_power_factor=[],
                    turns_ratio_tests=[ttr], winding_resistance_tests=[wr], exciting_current_tests=[ex],
                    demagnetization_tests=[])


@pytest.fixture()
def submission():
    with psycopg.connect(DSN, autocommit=True) as c:
        cls = c.execute("select asset_class_id from records.asset_classes where class_code='xfmr_liquid'").fetchone()[0]
        tpl = c.execute("select template_id from records.form_templates where template_code='ats_liquid_xfmr_v1' and is_current").fetchone()[0]
        aid, sid = uuid.uuid4(), uuid.uuid4()
        c.execute("insert into records.assets (asset_id, asset_class_id, asset_tag, name) values (%s,%s,%s,%s)",
                  (aid, cls, f"TEST-INGEST-{aid.hex[:8]}", "TEST-INGEST-XFMR"))
        c.execute("insert into records.form_submissions (form_submission_id, template_id, asset_id) values (%s,%s,%s)",
                  (sid, tpl, aid))
        yield sid
        c.execute("delete from records.form_submissions where form_submission_id=%s", (sid,))
        c.execute("delete from records.assets where asset_id=%s", (aid,))


def _count(sid):
    with psycopg.connect(DSN) as c:
        return c.execute("select count(*) from records.form_field_values where form_submission_id=%s", (sid,)).fetchone()[0]


def test_dry_run_proposes_without_writing(submission):
    schema = db.load_submission_schema(DSN, submission)
    proposal = ingest.model_to_proposal(_sample_model(), schema)
    keys = {v.field_key for v in proposal.mapped}
    assert {"winding_resistance.h.ohms", "turns_ratio.h_x.measured_ratio",
            "excitation_current.phase_a", "power_factor.ch.pf_pct"} <= keys
    assert not proposal.unmapped, f"unexpected unmapped: {[v.field_key for v in proposal.unmapped]}"
    assert proposal.pending, "partial fill: unfilled targets remain pending"
    assert _count(submission) == 0, "dry run must not write"


def test_commit_writes_mapped_partial_and_idempotent(submission):
    schema = db.load_submission_schema(DSN, submission)
    proposal = ingest.model_to_proposal(_sample_model(), schema)
    n1 = ingest.commit(DSN, submission, proposal)
    n2 = ingest.commit(DSN, submission, proposal)
    assert n1 == n2 == len(proposal.mapped)
    assert _count(submission) == len(proposal.mapped), "only mapped values written (no phantom)"
    with psycopg.connect(DSN) as c:
        dev = c.execute("select origin_device from records.form_field_values where form_submission_id=%s and origin_device is not null limit 1",
                        (submission,)).fetchone()[0]
        assert "GH733Y" in dev
