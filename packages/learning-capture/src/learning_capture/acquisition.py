"""Slice 2d acquisition helper: a guarded wrapper over record_event that STRUCTURALLY enforces the
provenance envelope, so a captured event is auditable -- not byte-indistinguishable from fabricated
data. Refuses any target that is not learning_dev / learning_test, and requires every acquisition
event to be content-bound (study_content_id) so the evidence is always projection-visible. Stricter
than the base 2a record_event by design."""
from psycopg.conninfo import conninfo_to_dict

from .capture import CaptureError, record_event
from .db import dsn

SOURCE_SURFACES = frozenset({"cli", "operations-web/learning-demo", "manual-runbook"})
DATA_FIDELITIES = frozenset({"synthetic", "rehearsal", "authentic"})
_ENVELOPE = ("acquisition_run_id", "source_surface", "observed_by", "evidence_ref", "data_fidelity")


def _guard_target() -> None:
    # Parse the DSN robustly (keyword OR url form) instead of brittle substring matching.
    info = conninfo_to_dict(dsn())
    host = (info.get("host") or "").lower()
    db = (info.get("dbname") or "").lower()
    if host.endswith(".supabase.co") or "fxoyniqnrlkxfligbxmg" in f"{host} {db}":
        raise CaptureError("acquisition refuses a prod-looking target")
    if db not in ("learning_dev", "learning_test"):
        raise CaptureError(f"acquisition dbname must be learning_dev/learning_test, got {db!r}")
    if host and host not in ("127.0.0.1", "localhost"):
        raise CaptureError(f"acquisition host must be local, got {host!r}")


def record_acquired_event(*, user_id, event_type, acquisition_run_id, source_surface, observed_by,
                          evidence_ref, data_fidelity, study_content_id=None, neta_section=None,
                          score_percent=None, confidence=None):
    _guard_target()
    env = {"acquisition_run_id": acquisition_run_id, "source_surface": source_surface,
           "observed_by": observed_by, "evidence_ref": evidence_ref, "data_fidelity": data_fidelity}
    for k in _ENVELOPE:
        if not isinstance(env[k], str) or not env[k].strip():
            raise CaptureError(f"acquisition envelope key {k!r} is required and must be non-empty")
    if source_surface not in SOURCE_SURFACES:
        raise CaptureError(f"source_surface {source_surface!r} not in {sorted(SOURCE_SURFACES)}")
    if data_fidelity not in DATA_FIDELITIES:
        raise CaptureError(f"data_fidelity {data_fidelity!r} not in {sorted(DATA_FIDELITIES)}")
    if study_content_id is None:
        raise CaptureError("acquisition events must be content-bound (study_content_id required) so "
                           "the evidence is projection-visible")
    if event_type == "assessment_completed" and score_percent is None:
        raise CaptureError("assessment_completed requires score_percent")
    if event_type == "self_assessment" and confidence is None:
        raise CaptureError("self_assessment requires confidence")
    payload = dict(env)
    if score_percent is not None:
        payload["score_percent"] = score_percent
    if confidence is not None:
        payload["confidence"] = confidence
    # record_event enforces the event_type vocab, user/content existence, and score/confidence
    # ranges, and never passes occurred_at (server now() only -> no backdating). The fixed-kwarg
    # envelope means a typoed key is a TypeError, not a silently-accepted payload field.
    return record_event(user_id, event_type, study_content_id=study_content_id,
                        neta_section=neta_section, payload=payload)
