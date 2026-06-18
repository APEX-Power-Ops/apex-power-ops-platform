"""DB layer (records_dev): load a submission's template field_schema + upsert confirmed values.

The upsert keys on form_field_values' UNIQUE (form_submission_id, field_key) -> re-import replaces,
never duplicates (spec 14, section 8). Imported values carry origin_device (the instrument) +
measured_at + notes; "imported" is implied by origin_device being set.
"""
from __future__ import annotations

import json

import psycopg

from records_import.proposal import ProposedValue


def load_submission_schema(dsn: str, submission_id) -> dict:
    with psycopg.connect(dsn) as c:
        fs = c.execute(
            "select t.field_schema from records.form_submissions s "
            "join records.form_templates t on t.template_id = s.template_id "
            "where s.form_submission_id = %s", (submission_id,)
        ).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs


_UPSERT = (
    "insert into records.form_field_values "
    "(form_submission_id, field_key, test_group, value_kind, value_numeric, value_text, unit, "
    " measured_at, origin_device, notes) "
    "values (%(sid)s, %(field_key)s, %(test_group)s, %(value_kind)s, %(value_numeric)s, %(value_text)s, "
    " %(unit)s, %(measured_at)s, %(origin_device)s, %(notes)s) "
    "on conflict (form_submission_id, field_key) do update set "
    " test_group=excluded.test_group, value_kind=excluded.value_kind, value_numeric=excluded.value_numeric, "
    " value_text=excluded.value_text, unit=excluded.unit, measured_at=excluded.measured_at, "
    " origin_device=excluded.origin_device, notes=excluded.notes, updated_at=now()"
)


def write_values(dsn: str, submission_id, values: list[ProposedValue]) -> int:
    n = 0
    with psycopg.connect(dsn, autocommit=True) as c:
        for v in values:
            c.execute(_UPSERT, {
                "sid": submission_id, "field_key": v.field_key, "test_group": v.test_group,
                "value_kind": v.value_kind, "value_numeric": v.value_numeric, "value_text": v.value_text,
                "unit": v.unit, "measured_at": v.measured_at, "origin_device": v.origin_device, "notes": v.notes,
            })
            n += 1
    return n
