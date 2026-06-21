import os
import pytest
from learning_capture.acquisition import record_acquired_event, SOURCE_SURFACES, DATA_FIDELITIES
from learning_capture.capture import CaptureError, list_events

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"
ENV = dict(acquisition_run_id="run-T", source_surface="cli", observed_by="JS",
           evidence_ref="notes#L1", data_fidelity="rehearsal")


def test_happy_path_writes_envelope_into_payload():
    ev = record_acquired_event(user_id=USER, event_type="resource_completed",
                               study_content_id=CONTENT, neta_section="7.1", **ENV)
    assert ev.payload["acquisition_run_id"] == "run-T"
    assert ev.payload["source_surface"] == "cli"
    assert ev.payload["observed_by"] == "JS"
    assert ev.payload["evidence_ref"] == "notes#L1"
    assert ev.payload["data_fidelity"] == "rehearsal"


@pytest.mark.parametrize("missing", list(ENV))
def test_each_envelope_key_required_nonempty(missing):
    bad = dict(ENV, **{missing: "  "})
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed",
                              study_content_id=CONTENT, **bad)


def test_bad_source_surface_and_fidelity_rejected():
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT,
                              **dict(ENV, source_surface="curl"))
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT,
                              **dict(ENV, data_fidelity="real"))


def test_assessment_requires_score_and_self_requires_confidence():
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="assessment_completed",
                              study_content_id=CONTENT, **ENV)  # no score_percent
    ev = record_acquired_event(user_id=USER, event_type="assessment_completed",
                               study_content_id=CONTENT, score_percent=88, **ENV)
    assert ev.payload["score_percent"] == 88
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="self_assessment",
                              study_content_id=CONTENT, **ENV)  # no confidence


@pytest.mark.parametrize("et", ["resource_viewed", "resource_completed",
                                "assessment_completed", "self_assessment"])
def test_content_id_required_for_every_event_type(et):
    kw = dict(ENV)
    if et == "assessment_completed":
        kw["score_percent"] = 80
    if et == "self_assessment":
        kw["confidence"] = 3
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type=et, study_content_id=None, **kw)


def test_prod_isolation_guard_refuses_supabase_host(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN",
                       "host=db.fxoyniqnrlkxfligbxmg.supabase.co dbname=postgres user=postgres")
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT, **ENV)


def test_prod_isolation_guard_refuses_non_dev_dbname(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=postgres user=postgres")
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT, **ENV)
