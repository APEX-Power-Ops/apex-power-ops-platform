"""Tests for access_harness.projection -- pure logic, no DB connection.

The FORBIDDEN-key guard is the load-bearing test: a direct Access-surrogate
(Breaker_TMTFrameSizes.ID, or any child <table>.FrameSizeID) -> tmt_frames.id
join must be STRUCTURALLY FORBIDDEN.  tcc.tmt_frames.id is a dense re-sequenced
surrogate that does NOT preserve the Access ID, so such a join compares
unrelated integer spaces and is provenance-dishonest.  The only honest path is
style-mediated (Access StyleID -> brk_{class}_styles.source_id ->
brk_{class}_styles.id -> tmt_frames.breaker_style_id).
"""
import pytest

from access_harness.projection import (
    ForbiddenKeyError,
    ProjectionMap,
    assert_key_allowed,
    resolve_frame_join,
)


def test_direct_frame_surrogate_id_forbidden():
    with pytest.raises(ForbiddenKeyError):
        assert_key_allowed(
            ProjectionMap.for_table('Breaker_TMTFrameSizes'),
            'Breaker_TMTFrameSizes.ID',
            'tmt_frames.id',
        )


def test_direct_child_framesizeid_also_forbidden():  # Codex P1 / CX1
    for t in (
        'Breaker_TMTFrameAmps',
        'Breaker_TMTFrameSettings',
        'Breaker_TMTFrameCurves',
        'Breaker_TMTThermalTripAdj',
    ):
        with pytest.raises(ForbiddenKeyError):
            assert_key_allowed(
                ProjectionMap.for_table(t),
                f'{t}.FrameSizeID',
                'tmt_frames.id',
            )


def test_style_mediated_chain_is_class_specific():  # Codex P2 / CX2
    plan = resolve_frame_join(
        ProjectionMap.for_table('Breaker_TMTFrameSizes'), 'MCCB'
    )
    assert plan.chain == [
        'StyleID',
        'brk_mccb_styles.source_id',
        'brk_mccb_styles.id',
        'tmt_frames.breaker_style_id',
    ]


def test_real_tcc_column_names():
    assert ProjectionMap.for_table('Breaker_TMTFrameAmps').col_map['TripAmp'] == 'rating'


def test_natural_attribute_key_is_allowed():
    # an allowed pairing (e.g. amps 'rating' natural key, or a non-surrogate
    # col) -> tcc) does NOT raise
    assert_key_allowed(
        ProjectionMap.for_table('Breaker_TMTFrameAmps'),
        'Breaker_TMTFrameAmps.TripAmp',
        'tmt_amps.rating',
    )


def test_build_kinds():
    assert ProjectionMap.for_table('Breaker_TMTFrameCurves').tcc_build_kind == 'computed'
    assert ProjectionMap.for_table('Breaker_TMTThermalTripAdj').tcc_build_kind == 'derived'


# ---------------------------------------------------------------------------
# Additional coverage -- guard edge cases and the remaining interfaces.
# ---------------------------------------------------------------------------


def test_quoted_tcc_col_form_also_forbidden():
    # The forbidden tcc side may also arrive in the quoted 'tmt_frames'.'id'
    # form; both spellings must trip the guard.
    with pytest.raises(ForbiddenKeyError):
        assert_key_allowed(
            ProjectionMap.for_table('Breaker_TMTFrameSizes'),
            'Breaker_TMTFrameSizes.ID',
            "'tmt_frames'.'id'",
        )


def test_frame_id_to_non_frame_target_is_allowed():
    # A surrogate ID is only forbidden when the TARGET is tmt_frames.id.
    # Mapping the Access ID into a provenance column (source_id) is allowed.
    assert_key_allowed(
        ProjectionMap.for_table('Breaker_TMTFrameSizes'),
        'Breaker_TMTFrameSizes.ID',
        'tmt_frames.source_id',
    )


def test_natural_attribute_to_frame_id_is_allowed():
    # The guard keys off the ACCESS side being a raw surrogate.  A natural
    # attribute paired against tmt_frames.id (whatever the join intent) does
    # not match the surrogate predicate, so it does not raise here.
    assert_key_allowed(
        ProjectionMap.for_table('Breaker_TMTFrameSizes'),
        'Breaker_TMTFrameSizes.FrameDesc',
        'tmt_frames.id',
    )


def test_resolve_frame_join_all_classes():
    for cls in ('MCCB', 'ICCB', 'PCB'):
        plan = resolve_frame_join(
            ProjectionMap.for_table('Breaker_TMTFrameSizes'), cls
        )
        lc = cls.lower()
        assert plan.chain == [
            'StyleID',
            f'brk_{lc}_styles.source_id',
            f'brk_{lc}_styles.id',
            'tmt_frames.breaker_style_id',
        ]


def test_resolve_frame_join_rejects_unknown_class():
    with pytest.raises(ValueError):
        resolve_frame_join(
            ProjectionMap.for_table('Breaker_TMTFrameSizes'), 'GFCI'
        )


def test_projection_map_carries_table_identity():
    pm = ProjectionMap.for_table('Breaker_TMTFrameSizes')
    assert pm.access_table == 'Breaker_TMTFrameSizes'
    assert pm.tcc_table == 'tmt_frames'
    assert pm.tcc_build_kind == '1:1_load'


def test_for_table_rejects_unknown_table():
    with pytest.raises(KeyError):
        ProjectionMap.for_table('Breaker_Nonexistent')


def test_curves_col_map_real_names():
    cm = ProjectionMap.for_table('Breaker_TMTFrameCurves').col_map
    assert cm['Class'] == 'class'
    assert cm['Time'] == 'time_sec'
    assert cm['Amps'] == 'current_amp'


def test_thermal_adj_col_map_real_names():
    assert ProjectionMap.for_table('Breaker_TMTThermalTripAdj').col_map['Adjustment'] == 'adjustment'
