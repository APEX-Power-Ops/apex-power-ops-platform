"""Chip 10c Phase 7 (end-to-end): .dtax file -> propose_dtax -> commit, against records_dev.

Mirrors test_ingest_end_to_end.py but drives the Doble .dtax path: we build a real .dtax by
write_dtax(read_ptm(sample)) and ingest it through propose_dtax (read_dtax + load schema + map).

Through read_dtax + the (pre-existing) ptm_transformer mapping, only the overall-PF rows whose
reconstructed measurement_name is in {ICH,ICL,ICHL,ICT} map to a datasheet target; the sample's
first overall row -> power_factor.ch.{pf_pct,capacitance}. Excitation rows arrive as phase
"PhaseA/B/C" (mapping expects "A"/"B"/"C") and TTR/WR rows arrive nameless, so they do not map
(documented mapping limits, not a read_dtax bug). We assert the pipeline commits the overall-PF
values it supports, with instrument provenance, idempotently.
"""
import os
import uuid
import zipfile
from pathlib import Path

import psycopg
import pytest

from power_test_converters.dtax import write_dtax
from power_test_converters.ptm import read_ptm
from power_test_converters.testing import write_sample_ptm

from records_import import db, ingest

from conftest import require_records_dsn

DSN = require_records_dsn()


def _build_dtax(tmp_path: Path) -> Path:
    """A real Doble .dtax = write_dtax(read_ptm(sample)). read_dtax inverts this in propose_dtax."""
    model = read_ptm(write_sample_ptm(tmp_path))
    return write_dtax(model, tmp_path / "sample.dtax")


@pytest.fixture()
def submission():
    with psycopg.connect(DSN, autocommit=True) as c:
        cls = c.execute(
            "select asset_class_id from records.asset_classes where class_code='xfmr_liquid'"
        ).fetchone()[0]
        tpl = c.execute(
            "select template_id from records.form_templates "
            "where template_code='ats_liquid_xfmr_v1' and is_current"
        ).fetchone()[0]
        aid, sid = uuid.uuid4(), uuid.uuid4()
        c.execute(
            "insert into records.assets (asset_id, asset_class_id, asset_tag, name) values (%s,%s,%s,%s)",
            (aid, cls, f"TEST-DTAX-{aid.hex[:8]}", "TEST-DTAX-XFMR"),
        )
        c.execute(
            "insert into records.form_submissions (form_submission_id, template_id, asset_id) values (%s,%s,%s)",
            (sid, tpl, aid),
        )
        yield sid
        c.execute("delete from records.form_submissions where form_submission_id=%s", (sid,))
        c.execute("delete from records.assets where asset_id=%s", (aid,))


def _count(sid):
    with psycopg.connect(DSN) as c:
        return c.execute(
            "select count(*) from records.form_field_values where form_submission_id=%s", (sid,)
        ).fetchone()[0]


def test_dtax_dry_run_proposes_without_writing(tmp_path, submission):
    dtax_path = _build_dtax(tmp_path)
    proposal = ingest.propose_dtax(DSN, submission, dtax_path)

    keys = {v.field_key for v in proposal.mapped}
    # The overall-PF "CH" row is the value this path supports through the existing mapping.
    assert {"power_factor.ch.pf_pct", "power_factor.ch.capacitance"} <= keys
    assert not proposal.unmapped, f"unexpected unmapped: {[v.field_key for v in proposal.unmapped]}"
    assert proposal.pending, "partial fill: unfilled targets remain pending"
    assert _count(submission) == 0, "dry run must not write"


def test_dtax_commit_writes_mapped_partial_and_idempotent(tmp_path, submission):
    dtax_path = _build_dtax(tmp_path)
    proposal = ingest.propose_dtax(DSN, submission, dtax_path)

    n1 = ingest.commit(DSN, submission, proposal)
    n2 = ingest.commit(DSN, submission, proposal)
    assert n1 == n2 == len(proposal.mapped)
    assert _count(submission) == len(proposal.mapped), "only mapped values written (no phantom)"

    with psycopg.connect(DSN) as c:
        pf = c.execute(
            "select value_numeric from records.form_field_values "
            "where form_submission_id=%s and field_key='power_factor.ch.pf_pct'",
            (submission,),
        ).fetchone()[0]
        assert float(pf) == 0.24
        dev = c.execute(
            "select origin_device from records.form_field_values "
            "where form_submission_id=%s and origin_device is not null limit 1",
            (submission,),
        ).fetchone()[0]
        assert "GH733Y" in dev
