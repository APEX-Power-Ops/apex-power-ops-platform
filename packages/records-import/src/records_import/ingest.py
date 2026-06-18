"""Ingest entry: instrument file (or parsed model) -> review proposal -> committed values.

Office-side, connected (spec 14, D2). The mapping core is source-agnostic: `model_to_proposal` takes a
parsed reading model + the datasheet field_schema and returns a classified Proposal; `propose` is the
file convenience (read_ptm + load the submission's schema); `commit` writes the confirmed (mapped)
values. A live test-set adapter later feeds the same `model_to_proposal`.
"""
from __future__ import annotations

from power_test_converters.ptm import read_ptm

from records_import import db
from records_import.mappings.ptm_transformer import map_ptm_transformer
from records_import.review import Proposal, build_proposal


def model_to_proposal(model, field_schema: dict) -> Proposal:
    """Pure: parsed PtmModel + datasheet schema -> classified Proposal (no DB, no file)."""
    return build_proposal(map_ptm_transformer(model), field_schema)


def propose(dsn: str, submission_id, ptm_path) -> Proposal:
    """File entry: parse the .ptm, load the submission's template schema, classify. No write."""
    model = read_ptm(ptm_path)
    schema = db.load_submission_schema(dsn, submission_id)
    return model_to_proposal(model, schema)


def commit(dsn: str, submission_id, proposal: Proposal) -> int:
    """Write the confirmed (mapped) values into form_field_values (idempotent upsert)."""
    return db.write_values(dsn, submission_id, proposal.mapped)
