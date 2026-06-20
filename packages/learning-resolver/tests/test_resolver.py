from learning_resolver.db import connect
from learning_resolver import resolver


def test_apparatus_type_ids_for_known_section(section_with_curated):
    with connect() as c:
        ids = resolver._apparatus_type_ids(c, section_with_curated)
    assert ids and all(isinstance(i, str) for i in ids)


def test_curated_tier_orders_primary_first(section_with_curated):
    with connect() as c:
        ids = resolver._apparatus_type_ids(c, section_with_curated)
        items = resolver._curated(c, ids)
    assert items, "the curated section should yield curated resources"
    assert all(r.source == "curated" for r in items)
    # is_primary resources rank ahead of non-primary; mandatory ahead of non-mandatory.
    keys = [(not r.is_primary, not r.is_mandatory) for r in items]
    assert keys == sorted(keys), "curated order must be is_primary then is_mandatory"


def test_section_match_tier(section_study_only):
    from learning_resolver import resolver
    from learning_resolver.db import connect
    with connect() as c:
        items = resolver._section_match(c, section_study_only, exclude_sc_ids=set())
    assert items, "a study-only section should yield section matches"
    assert all(r.source == "section_match" for r in items)
    # primary-section matches outrank secondary-section matches
    scores = [r.score for r in items]
    assert scores == sorted(scores, reverse=True)


def test_section_match_excludes_already_curated(section_study_only):
    from learning_resolver import resolver
    from learning_resolver.db import connect
    with connect() as c:
        full = resolver._section_match(c, section_study_only, exclude_sc_ids=set())
        first_id = full[0].reference["id"]
        pruned = resolver._section_match(c, section_study_only, exclude_sc_ids={first_id})
    assert all(r.reference["id"] != first_id for r in pruned)
    assert len(pruned) == len(full) - 1


def test_resolve_curated_before_section(section_with_curated):
    from learning_resolver import resolve
    items = resolve(section_with_curated, limit=50)
    assert items
    first_section_idx = next((i for i, r in enumerate(items) if r.source == "section_match"), len(items))
    assert all(r.source == "curated" for r in items[:first_section_idx])


def test_resolve_dedupes_study_content(section_with_curated):
    from learning_resolver import resolve
    ids = [r.reference.get("id") for r in resolve(section_with_curated, limit=200)
           if r.reference.get("kind") == "study_content"]
    ids = [i for i in ids if i]
    assert len(ids) == len(set(ids)), "a study_content must appear at most once"


def test_resolve_level_changes_order_not_membership(section_study_only):
    from learning_resolver import resolve
    base = resolve(section_study_only, limit=200)
    leveled = resolve(section_study_only, level="IV", limit=200)
    key = lambda rs: {r.reference.get("id") or r.reference.get("url") for r in rs}
    assert key(base) == key(leveled), "level must not change MEMBERSHIP (soft re-rank only)"


def test_resolve_caps_at_limit(section_with_curated):
    from learning_resolver import resolve
    assert len(resolve(section_with_curated, limit=3)) <= 3


def test_resolve_unknown_section_is_empty():
    from learning_resolver import resolve
    assert resolve("9.9.9.9-nope") == []
