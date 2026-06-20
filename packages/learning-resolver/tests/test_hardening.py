"""Slice-1 resolver hardening: target-id in curated neta_procedure refs (#1), dedup exclusion (#6),
level-rerank math (#7), and list_sections for the typeahead (#4 support). The first three use a fake
connection so they are deterministic (no data coincidence); list_sections hits learning_dev (read).

Run (host, from packages/learning-resolver/):
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_hardening.py -q
"""
from learning_resolver.resolver import _curated, _level_boost, _section_match, list_sections


class FakeConn:
    """Minimal psycopg-like stand-in: execute(...).fetchall()/fetchone() return canned rows."""
    def __init__(self, rows):
        self._rows = rows
    def execute(self, sql, params=None):
        return self
    def fetchall(self):
        return self._rows
    def fetchone(self):
        return self._rows[0] if self._rows else None


def test_curated_neta_procedure_ref_includes_id():
    # _curated row: (rtype, is_primary, is_mandatory, display_order, sc_id, np_id, url, rname,
    #                sc_title, sc_slug, sc_summary, sc_level, np_title, np_section)
    row = ("procedure", True, False, 0, None, "np-uuid-1", None, None,
           None, None, None, None, "Inspect breaker", "7.2.1.1")
    out = _curated(FakeConn([row]), ["apt-1"])
    assert out[0].reference == {"kind": "neta_procedure", "section": "7.2.1.1", "id": "np-uuid-1"}


def test_section_match_excludes_curated_study_content_ids():
    # _section_match row: (sc_id, title, slug, summary, level, primary_hit, quality_tier)
    rows = [
        ("dup-sc", "Dup", "dup", "s", "II", True, "gold"),
        ("keep-sc", "Keep", "keep", "s", "II", True, "gold"),
    ]
    out = _section_match(FakeConn(rows), "7.2.1.1", exclude_sc_ids={"dup-sc"})
    assert {r.reference["id"] for r in out} == {"keep-sc"}   # the curated duplicate is removed


def test_level_boost_exact_values():
    assert _level_boost("III", "III") == 30.0   # exact
    assert _level_boost("II", "III") == 10.0    # one level off
    assert _level_boost("II", "IV") == 0.0      # two off
    assert _level_boost(None, "III") == 0.0     # unknown -> no boost


def test_list_sections_returns_known_section():
    sections = list_sections()
    assert isinstance(sections, list) and sections
    assert "7.2.1.1" in sections
