from apex_calc_engine.services.calc_engine.etu_delay_routing import (
    GFInvEqFamily,
    delay_calc_name,
    dispatch_gfd_delay,
    dispatch_gf_inveq_row,
    dispatch_std_delay,
    gf_inveq_family,
    route_delay_curve,
    std_inveq_icalc_integrity_ok,
)


class _FakeSolver:
    def __init__(self):
        self.calls = []

    def generate_curve(self, **kwargs):
        self.calls.append(kwargs)
        return [{"amps": 100.0, "seconds": 1.0}]


def test_delay_calc_names_and_std_dispatch_contract():
    assert delay_calc_name(0) == "NONE"
    assert delay_calc_name(1) == "I2X"
    assert delay_calc_name(2) == "INVEQ"
    assert delay_calc_name(99) == "UNKNOWN"
    assert delay_calc_name(None) == "UNKNOWN"

    assert dispatch_std_delay(0).solver_path == "flat"
    assert dispatch_std_delay(1).solver_path == "i2x_band"
    assert dispatch_std_delay(2).solver_path == "ieee_inverse_time"
    assert dispatch_std_delay(4).supported is False


def test_std_inveq_integrity_and_gf_native_dispatch_helpers():
    assert std_inveq_icalc_integrity_ok(10, 10, 4, 4) is True
    assert std_inveq_icalc_integrity_ok(10, 10, 4, None) is False

    assert gf_inveq_family(0) == GFInvEqFamily.THERM
    assert gf_inveq_family(1) == GFInvEqFamily.ANSI

    dispatch = dispatch_gf_inveq_row(
        in_out=2,
        gfp_enabled=True,
        id_open_eq=1,
        fd_open_i_calc=0,
        fd_clear_i_calc=1,
        id_open_i_calc=0,
        id_clear_i_calc=1,
    )

    assert dispatch.family == GFInvEqFamily.ANSI
    assert dispatch.block_kind == "inverse"
    assert dispatch.byicalc_per_subblock["fd_open"] == 2
    assert dispatch.active_setters[0][1].startswith("SetAnsi")


def test_route_delay_curve_dispatches_inveq_to_solver():
    solver = _FakeSolver()

    result = route_delay_curve(
        solver=solver,
        delay_calc_code=2,
        path="std",
        sensor_id=25,
        ordinal=3,
        variant="fd_open",
        pickup_current=480.0,
        max_amps=10000.0,
    )

    assert result.dispatch.solver_path == "ieee_inverse_time"
    assert result.points == [{"amps": 100.0, "seconds": 1.0}]
    assert solver.calls[0]["equation_type"] == "std"


def test_gfd_weg_pickup_exclusion_surfaces_warning_without_solver_call():
    solver = _FakeSolver()

    result = route_delay_curve(
        solver=solver,
        delay_calc_code=2,
        path="gfd",
        sensor_id=25,
        ordinal=1,
        variant="fd_open",
        pickup_current=480.0,
        gf_pickup_calc_code=6,
    )

    assert result.dispatch.supported is False
    assert "WEG OCR Type A" in result.dispatch.unsupported_reason
    assert result.points == []
    assert result.warnings
    assert solver.calls == []
