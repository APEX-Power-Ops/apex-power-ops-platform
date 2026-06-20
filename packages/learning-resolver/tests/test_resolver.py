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


def test_section_match_quality_tier_tiebreak():
    """FIX 1: quality_tier tiebreak within primary/secondary bands.

    Section 7.2 has published section-match rows with BOTH quality_tier='complete'
    and quality_tier='draft', all as primary-section matches.  The spec requires that
    within the same primary/secondary band, a higher-quality item must not be
    out-ranked by a lower-quality one.

    This is the MIXED-QUALITY SECTION case: live data confirmed via DB query
    (7.2 has 15 complete + 1 draft primary rows as of 2026-06-20).

    Scoring: primary_hit -> score = 550 + quality_boost; secondary -> 500 + quality_boost
    quality_boost: complete=10, draft(or None)=0.
    So a complete primary (560) > draft primary (550) > complete secondary (510) > draft secondary (500).
    This test asserts that within the set of primary-hit rows, a complete item scores
    strictly higher than a draft item.
    """
    section = "7.2"
    with connect() as c:
        items = resolver._section_match(c, section, exclude_sc_ids=set())

    assert items, "section 7.2 must yield study content matches"

    # Scores must be sorted descending overall.
    scores = [r.score for r in items]
    assert scores == sorted(scores, reverse=True), "section_match results must be sorted by score desc"

    # The primary/secondary boundary is a gap of 50; quality tier adds at most 10 within a band.
    # Confirm that ALL primary-hit items score >= 550 and all secondary-hit items score < 550.
    # (primary_hit => score = 550 or 560; secondary => 500 or 510)
    section_base = resolver._SECTION_BASE  # 500
    primary_threshold = section_base + 50   # 550 -- minimum score for a primary hit with quality=0

    # Partition by primary vs secondary using score >= primary_threshold.
    primary_items = [r for r in items if r.score >= primary_threshold]
    secondary_items = [r for r in items if r.score < primary_threshold]

    # Confirm we have the mixed-quality data we expect.
    primary_scores = {r.score for r in primary_items}
    # complete primary: 560, draft primary: 550 -- both tiers must appear given live data.
    assert len(primary_scores) > 1, (
        "Expected mixed quality_tier in primary hits for section 7.2; "
        "check that live data still includes at least one 'draft' quality primary row"
    )

    # The highest-scoring primary items must be complete (560), not draft (550).
    max_primary_score = max(r.score for r in primary_items)
    complete_boost = resolver._QUALITY_BOOST.get("complete", 0.0)
    assert max_primary_score == primary_threshold + complete_boost, (
        f"Top primary score should be {primary_threshold + complete_boost} (complete tier), "
        f"got {max_primary_score}"
    )

    # If secondary items exist, none should outscore a primary item.
    if secondary_items:
        max_secondary = max(r.score for r in secondary_items)
        min_primary = min(r.score for r in primary_items)
        assert min_primary > max_secondary, (
            "No secondary item should outscore a primary item (quality boost must not bridge the gap)"
        )
