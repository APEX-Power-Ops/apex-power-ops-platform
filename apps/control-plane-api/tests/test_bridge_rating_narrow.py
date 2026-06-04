"""TDD for the SST-bridge rating-narrow (#75 / STATE §145).

The breaker's continuous rating (`r_cont_current`, carried from Access in migration
011) is the field EasyPower uses to pick the ONE sensor within a borrowed SST
trip-style. The narrow surfaces only the sensor whose rating matches it — but is
SAFE BY CONSTRUCTION: when no sensor matches exactly, it falls back to the full set
(never hides the right sensor).
"""
from services.neta.schemas import EtuBridgeSensor
from services.neta.router import narrow_bridge_sensors_by_rating


def _sensor(sensor_id: int, rating: int) -> EtuBridgeSensor:
    return EtuBridgeSensor(
        breaker_class="mccb", breaker_id=1, breaker_style_id=1,
        trip_style_id=1, sensor_id=sensor_id, sensor_rating=rating,
    )


class TestNarrowBridgeSensorsByRating:
    def test_exact_single_match_narrows_to_one(self):
        sensors = [_sensor(1, 800), _sensor(2, 1200), _sensor(3, 1600)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, 1200)
        assert narrowed is True
        assert [s.sensor_id for s in out] == [2]

    def test_no_exact_match_returns_full_set(self):
        # rcc=1000 matches no sensor rating -> safe fall back to all, not narrowed
        sensors = [_sensor(1, 800), _sensor(2, 1200), _sensor(3, 1600)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, 1000)
        assert narrowed is False
        assert [s.sensor_id for s in out] == [1, 2, 3]

    def test_none_rating_returns_full_set(self):
        sensors = [_sensor(1, 800), _sensor(2, 1200)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, None)
        assert narrowed is False
        assert [s.sensor_id for s in out] == [1, 2]

    def test_duplicate_ratings_keep_all_matching(self):
        # a style with two sensor variants at the same rating -> keep both (still a reduction)
        sensors = [_sensor(1, 800), _sensor(2, 1600), _sensor(3, 1600)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, 1600)
        assert narrowed is True
        assert [s.sensor_id for s in out] == [2, 3]

    def test_empty_sensor_set(self):
        out, narrowed = narrow_bridge_sensors_by_rating([], 800)
        assert narrowed is False
        assert out == []

    def test_out_of_range_high_returns_full_set(self):
        # the 230 out-of-range cases (#74): rcc far above any sensor -> full set, not narrowed
        sensors = [_sensor(1, 60), _sensor(2, 225)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, 2500)
        assert narrowed is False
        assert [s.sensor_id for s in out] == [1, 2]

    def test_float_rcc_matches_int_rating(self):
        # r_cont_current is numeric (e.g. 800.0); sensor_rating is int 800 -> match
        sensors = [_sensor(1, 800), _sensor(2, 1200)]
        out, narrowed = narrow_bridge_sensors_by_rating(sensors, 800.0)
        assert narrowed is True
        assert [s.sensor_id for s in out] == [1]
