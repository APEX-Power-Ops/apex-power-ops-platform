import pathlib, subprocess
REPO = pathlib.Path(__file__).resolve().parents[3]
GUARD = REPO / "scripts" / "learning" / "redaction_check.sh"


def _check(text, tmp_path):
    f = tmp_path / "packet.md"; f.write_text(text, encoding="utf-8")
    return subprocess.run(["bash", str(GUARD), str(f)], capture_output=True, text=True)


def test_rejects_email_and_passes_clean(tmp_path):
    assert _check("observed_by: jane.doe@apexpowerops.com", tmp_path).returncode != 0
    assert _check("observed_by: JS  evidence_ref: runbook#run01", tmp_path).returncode == 0


def test_operator_denylist_file_rejects_named_terms(tmp_path, monkeypatch):
    deny = tmp_path / "deny.txt"; deny.write_text("Jane Doe\n", encoding="utf-8")
    monkeypatch.setenv("REDACTION_DENYLIST", str(deny))
    assert _check("the rehearsal subject was Jane Doe", tmp_path).returncode != 0
