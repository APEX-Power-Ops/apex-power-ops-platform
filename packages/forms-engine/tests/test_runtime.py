from pathlib import Path

from apex_forms_engine.contract import get_runtime_status


def test_runtime_status_matches_bounded_contract(monkeypatch, tmp_path: Path) -> None:
    templates_path = tmp_path / "templates"
    artifacts_path = tmp_path / "artifacts"
    templates_path.mkdir()
    artifacts_path.mkdir()

    monkeypatch.setenv("FORMS_ENGINE_TEMPLATES_PATH", str(templates_path))
    monkeypatch.setenv("FORMS_ENGINE_ARTIFACTS_PATH", str(artifacts_path))

    status = get_runtime_status()

    assert status["service"] == "forms-engine"
    assert status["status"] == "ok"
    assert status["port"] == 8080
    assert status["templatesPath"].endswith("/templates")
    assert status["templatesPathExists"] is True
    assert status["artifactsPath"].endswith("/artifacts")
    assert status["expectedArtifacts"] == []
    assert status["oidc"] == {
        "issuerUrl": "https://auth.olares.local",
        "clientId": "forms-engine-placeholder",
    }