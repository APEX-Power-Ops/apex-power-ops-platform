"""Tests for the cited Eaton Power Defense PXR curve/setting catalog (services.neta.pxr_curves).

Validates the authoritative-data lookups against the Eaton TCC docs (TD012064/065/067/068EN)
+ PXPM (PXR2025MCCB.xml) — STATE §140, reference/tcc/EATON-POWER-DEFENSE-PXR.md.
"""
from services.neta import pxr_curves as pxr


class TestFrameRatings:
    def test_pd3_sensor_ratings(self):
        # PD3 (TD012065EN): 125 / 250 / 400 / 600 A standard frames.
        r = pxr.frame_ratings("PDG3")
        assert 125 in r and 250 in r and 400 in r and 600 in r

    def test_pd6_sensor_ratings(self):
        # PD6 (TD012068EN): 1600 / 2000 / 2500 A.
        assert pxr.frame_ratings("PDG6") == [1600, 2000, 2500]

    def test_unknown_frame_returns_empty(self):
        assert pxr.frame_ratings("nope") == []

    def test_frame_label_normalizes(self):
        # accepts "PDG3-F PXR 400A" style frame labels, not just "PDG3"
        assert pxr.frame_ratings("PDG3-F PXR 400A") == pxr.frame_ratings("PDG3")


class TestCurveModel:
    def test_pxr2025_short_delay_range(self):
        m = pxr.curve_model("PXR20/25")
        assert m["sd"]["isd_min"] == 1.5
        assert m["sd"]["isd_max"] == 12.0
        assert m["sd"]["tsd_min"] == 0.05
        assert m["sd"]["tsd_max"] == 0.5
        # selectable slope: flat OR I2t (the authoritative model — NOT a fixed i2x)
        assert set(m["sd"]["slopes"]) == {"flat", "i2t"}

    def test_pxr2025_long_delay(self):
        m = pxr.curve_model("PXR20/25")
        assert m["ld"]["pickup_pct_of_ir"] == 110
        assert m["ld"]["time_min"] == 0.5
        assert m["ld"]["time_max"] == 24.0
        assert set(m["ld"]["slopes"]) == {"i2t", "i4t"}

    def test_pxr10_is_basic_variant(self):
        # PXR 10: LD time tops out at 7 s; Isd to 10x in 0.5x steps; tsd 50-300 ms.
        m = pxr.curve_model("PXR 10")
        assert m["ld"]["time_max"] == 7.0
        assert m["sd"]["isd_max"] == 10.0
        assert m["sd"]["tsd_max"] == 0.3

    def test_ground_pickup_range(self):
        m = pxr.curve_model("PXR20/25")
        assert m["gf"]["pickup_min_xin"] == 0.2
        assert m["gf"]["pickup_max_xin"] == 1.0


class TestTolerances:
    def test_pickup_tolerances(self):
        t = pxr.tolerances("PXR20/25")
        assert t["ldpu"] == (-5.0, 5.0)
        assert t["sdpu"] == (-5.0, 5.0)
        assert t["inst"] == (-10.0, 10.0)

    def test_ld_time_tolerance_asymmetric(self):
        t = pxr.tolerances("PXR20/25")
        assert t["ld_time"] == (-30.0, 0.0)

    def test_sd_time_graded(self):
        # tsd graded tolerance: tightest at long settings, widest at short.
        assert pxr.sd_time_tolerance(0.5) == (-20.0, 0.0)
        assert pxr.sd_time_tolerance(0.18) == (-30.0, 0.0)
        assert pxr.sd_time_tolerance(0.12) == (-40.0, 0.0)
        assert pxr.sd_time_tolerance(0.07) == (-50.0, 0.0)


class TestSstCorrection:
    def test_pdg5_correct_target(self):
        # the shipped clean fix (migration 009)
        assert pxr.correct_sst_target("PDG5-K PXR 1200") == ("Eaton", "PXR20", "PDG5-LSI")

    def test_pdg3_correct_target(self):
        assert pxr.correct_sst_target("PDG3-F PXR 400A") == ("Eaton", "PXR20", "PDG3-LSI")

    def test_pdg6_correct_target(self):
        assert pxr.correct_sst_target("PDG6-P PXR 2500") == ("Eaton", "PXR20", "PDG6-LSIGM")

    def test_pdg2_already_correct_returns_none(self):
        # PDG2 maps correctly in EasyPower already → no correction
        assert pxr.correct_sst_target("PDG2-F PXR 2/3P") is None
