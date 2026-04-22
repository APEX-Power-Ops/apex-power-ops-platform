from migrations.full_access_emt_import import filter_valid_emt_graph


def _source_records():
    return {
        "EMT.csv": [
            {"ID": "73", "Mfr_ID": "9", "Type": "EC-1", "Style": "AK-15", "TCCNumber": "", "Note": "", "TripChar": "7", "TripPlug": "0"},
            {"ID": "74", "Mfr_ID": "9", "Type": "EC-1", "Style": "AK-15 LI", "TCCNumber": "", "Note": "", "TripChar": "5", "TripPlug": "0"},
        ],
        "EMT_Frames.csv": [
            {"ID": "1", "StyleID": "1", "FrameSize": "225.00", "FrameDesc": "225A (15-225AT)", "Ordinal": "1"},
            {"ID": "298", "StyleID": "73", "FrameSize": "225.00", "FrameDesc": "225A (15-225AT)", "Ordinal": "1"},
            {"ID": "2", "StyleID": "74", "FrameSize": "225.00", "FrameDesc": "225A (15-225AT)", "Ordinal": "1"},
        ],
        "EMT_FrameAmps.csv": [
            {"FrameID": "1", "TripAmp": "225"},
            {"FrameID": "298", "TripAmp": "225"},
            {"FrameID": "2", "TripAmp": "225"},
        ],
        "EMT_Sections.csv": [
            {"ID": "11", "Name": "LT Pickup", "FrameID": "1", "SecChar": "1", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "12", "Name": "ST Pickup", "FrameID": "1", "SecChar": "2", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "13", "Name": "Instantaneous", "FrameID": "1", "SecChar": "4", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "21", "Name": "LT Pickup", "FrameID": "298", "SecChar": "1", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "22", "Name": "ST Pickup", "FrameID": "298", "SecChar": "2", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "23", "Name": "Instantaneous", "FrameID": "298", "SecChar": "4", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "31", "Name": "LT Pickup", "FrameID": "2", "SecChar": "1", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
            {"ID": "33", "Name": "Instantaneous", "FrameID": "2", "SecChar": "4", "CurveType": "0", "PickupCalc": "0", "PickupTolerLow": "-10", "PickupTolerHigh": "10", "PickupSetting": "0", "StepSize": "", "CurrentCalc": "0", "DelayClrCurve": "", "DelayOpenTime": "", "DelayClearTime": "", "OpenCurveRadius": "", "ClearCurveRadius": ""},
        ],
        "EMT_BandNames.csv": [
            {"ID": "111", "SecID": "11", "BandName": "Min", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "112", "SecID": "12", "BandName": "Max", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "113", "SecID": "13", "BandName": "(Std)", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "211", "SecID": "21", "BandName": "Min", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "212", "SecID": "22", "BandName": "Max", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "213", "SecID": "23", "BandName": "(Std)", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "311", "SecID": "31", "BandName": "Min", "Ordinal": "1", "CurrentAt": "1"},
            {"ID": "313", "SecID": "33", "BandName": "(Std)", "Ordinal": "1", "CurrentAt": "1"},
        ],
        "EMT_Pickups.csv": [
            {"SecID": "11", "Setting": "0.80", "Description": "0.8x"},
            {"SecID": "12", "Setting": "2.00", "Description": "2x"},
            {"SecID": "13", "Setting": "75.00", "Description": "75"},
            {"SecID": "21", "Setting": "0.80", "Description": "0.8x"},
            {"SecID": "22", "Setting": "2.00", "Description": "2x"},
            {"SecID": "23", "Setting": "75.00", "Description": "75"},
            {"SecID": "31", "Setting": "0.80", "Description": "0.8x"},
            {"SecID": "33", "Setting": "75.00", "Description": "75"},
        ],
        "EMT_Curves.csv": [
            {"ParentID": "111", "Class": "0", "Time": "10.0", "Amps": "100.0"},
            {"ParentID": "111", "Class": "1", "Time": "12.0", "Amps": "100.0"},
            {"ParentID": "112", "Class": "0", "Time": "2.5", "Amps": "200.0"},
            {"ParentID": "113", "Class": "1", "Time": "0.1", "Amps": "500.0"},
            {"ParentID": "211", "Class": "0", "Time": "10.0", "Amps": "100.0"},
            {"ParentID": "211", "Class": "1", "Time": "12.0", "Amps": "100.0"},
            {"ParentID": "212", "Class": "0", "Time": "2.5", "Amps": "200.0"},
            {"ParentID": "213", "Class": "1", "Time": "0.1", "Amps": "500.0"},
            {"ParentID": "311", "Class": "0", "Time": "10.0", "Amps": "100.0"},
            {"ParentID": "313", "Class": "1", "Time": "0.1", "Amps": "500.0"},
        ],
    }


def test_filter_valid_emt_graph_reports_exact_duplicate_candidate_for_orphan_style(monkeypatch):
    monkeypatch.delenv("EMT_ENABLE_STYLE_ALIASES", raising=False)

    filtered, anomalies = filter_valid_emt_graph(_source_records())

    assert [record["ID"] for record in filtered["EMT_Frames.csv"]] == ["298", "2"]
    assert anomalies["missing_style_ids"] == [1]
    assert anomalies["orphan_counts"]["frames"] == 1

    candidates = anomalies["orphan_duplicate_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["frame_id"] == 1
    assert candidates[0]["missing_style_id"] == 1
    assert candidates[0]["exact_duplicate_match"] is True
    assert candidates[0]["candidate_style_ids"] == [73]
    assert candidates[0]["candidate_frame_ids"] == [298]


def test_filter_valid_emt_graph_can_apply_opt_in_style_alias(monkeypatch):
    monkeypatch.setenv("EMT_ENABLE_STYLE_ALIASES", "1")

    filtered, anomalies = filter_valid_emt_graph(_source_records())

    assert [record["ID"] for record in filtered["EMT_Frames.csv"]] == ["298", "2"]
    assert anomalies["missing_style_ids"] == []
    assert anomalies["orphan_counts"]["frames"] == 0
    assert anomalies["applied_style_aliases"] == {1: 73}
    assert anomalies["collapsed_aliased_duplicate_frames"] == [
        {
            "frame_id": 1,
            "aliased_style_id": 73,
            "canonical_frame_id": 298,
            "frame_desc": "225A (15-225AT)",
        }
    ]
    assert anomalies["collapsed_alias_counts"] == {
        "frames": 1,
        "frame_amps": 1,
        "sections": 3,
        "bands": 3,
        "pickups": 3,
        "curves": 4,
    }