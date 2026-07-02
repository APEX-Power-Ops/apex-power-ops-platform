"""Phase 5 (integration): db layer - load a submission's template schema + idempotent upsert.

Creates a throwaway asset + submission on records_dev, writes, asserts, re-writes (idempotent), and
tears down (delete asset cascades the submission + field values).
"""
import os
import uuid

import psycopg
import pytest

from records_import import db
from records_import.proposal import ProposedValue

from conftest import require_records_dsn

DSN = require_records_dsn()


@pytest.fixture()
def submission():
    with psycopg.connect(DSN, autocommit=True) as c:
        cls = c.execute("select asset_class_id from records.asset_classes where class_code='xfmr_liquid'").fetchone()[0]
        tpl = c.execute("select template_id from records.form_templates where template_code='ats_liquid_xfmr_v1' and is_current").fetchone()[0]
        aid, sid = uuid.uuid4(), uuid.uuid4()
        c.execute("insert into records.assets (asset_id, asset_class_id, asset_tag, name) values (%s,%s,%s,%s)",
                  (aid, cls, f"TEST-IMPORT-{aid.hex[:8]}", "TEST-IMPORT-XFMR"))  # uq_assets_tag is UNIQUE
        c.execute("insert into records.form_submissions (form_submission_id, template_id, asset_id) values (%s,%s,%s)",
                  (sid, tpl, aid))
        yield sid
        # form_submissions->assets is NOT ON DELETE CASCADE; drop the submission first
        # (it cascades form_field_values), then the asset.
        c.execute("delete from records.form_submissions where form_submission_id=%s", (sid,))
        c.execute("delete from records.assets where asset_id=%s", (aid,))


def _rows(c, sid):
    return {r[0]: r for r in c.execute(
        "select field_key, value_numeric, unit, origin_device, test_group, measured_at, notes "
        "from records.form_field_values where form_submission_id=%s", (sid,)).fetchall()}


def test_upsert_writes_and_is_idempotent(submission):
    pv = [ProposedValue("winding_resistance.h.ohms", "winding_resistance", value_numeric=0.512, unit="ohm",
                        origin_device="TESTRANO 600 / SN GH733Y", measured_at="2026-06-01T10:00:00",
                        notes="measured=0.5 ohm (corrected to ref temp)")]
    n1 = db.write_values(DSN, submission, pv)
    n2 = db.write_values(DSN, submission, pv)  # second time must not duplicate
    assert n1 == n2 == 1
    with psycopg.connect(DSN) as c:
        rows = _rows(c, submission)
        r = rows["winding_resistance.h.ohms"]
        assert float(r[1]) == 0.512 and r[2] == "ohm"
        assert r[3] == "TESTRANO 600 / SN GH733Y"
        assert r[4] == "winding_resistance"
        cnt = c.execute("select count(*) from records.form_field_values where form_submission_id=%s and field_key='winding_resistance.h.ohms'",
                        (submission,)).fetchone()[0]
        assert cnt == 1, "idempotent upsert on (submission, field_key)"


def test_upsert_updates_on_reimport(submission):
    db.write_values(DSN, submission, [ProposedValue("winding_resistance.h.ohms", "winding_resistance", value_numeric=0.500)])
    db.write_values(DSN, submission, [ProposedValue("winding_resistance.h.ohms", "winding_resistance", value_numeric=0.512, unit="ohm")])
    with psycopg.connect(DSN) as c:
        rows = _rows(c, submission)
        assert float(rows["winding_resistance.h.ohms"][1]) == 0.512 and rows["winding_resistance.h.ohms"][2] == "ohm"


def test_load_field_schema(submission):
    fs = db.load_submission_schema(DSN, submission)
    assert any(s["key"] == "winding_resistance" for s in fs["sections"])
    assert fs.get("capture")  # migration 020 made it capture-mode-aware
