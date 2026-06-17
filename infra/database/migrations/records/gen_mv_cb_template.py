#!/usr/bin/env python3
"""Generate 011_mvhv_cb_datasheet_template.sql - the MV/HV circuit-breaker composite datasheet.

ONE composite template (ats_mvhv_cb_v1) for the cb_mvhv leaf. An interrupting_medium selector
(air / oil / vacuum / sf6) drives visible_if. Unlike the LV sheet's construction_type, the four
media ARE four NETA procedures (7.6.1.3 air, 7.6.2 oil, 7.6.3 vacuum, 7.6.4 SF6); the composite
covers the UNION of their ATS items and gates each medium-specific delta. Every concept's gate is
AUTO-DERIVED from the media whose NETA procedure lists it (common item -> no gate).

R-A (operator-confirmed for MV/HV): an MV/HV breaker has NO integral trip curve (protection is
external relays, 7.9 / relaytcc), so acceptance windows are sourced from NETA tables + mfr-published
data, NOT lvbreakertcc. tolerance_source.engine is 'neta_table' (IR 100.1, dielectric 100.19,
pickup 100.20, SF6 gas 100.13) or 'mfr' (contact resistance, contact timing - the future mfr-layer
slot). Windows are DECLARED, never valued here; they resolve at provisioning (Chip 5) and ride down
to the device (offline-sync law). Never fabricated.

Coverage invariant (fail-fast here, re-checked in test_011 against records_dev): the union of every
section's neta_covers must cover all 122 NETA ATS visual_mechanical+electrical items across the four
procedures - no silent drops, no phantom refs.

ASCII-only output (NETA trap). Deterministic UUID5 template_id + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_mv_cb_template.py [path-to-json]
"""
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
OUT = os.path.join(HERE, "011_mvhv_cb_datasheet_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")          # same namespace as LV
TEMPLATE_ID = str(uuid.uuid5(NS_TPL, "ats_mvhv_cb_v1"))

MEDIA = {"air": "7.6.1.3", "oil": "7.6.2", "vacuum": "7.6.3", "sf6": "7.6.4"}
ALL_MEDIA = ["air", "oil", "vacuum", "sf6"]
PRIMARY = "7.6.1.3"
COND = ["sat", "unsat", "na"]


def gate(media):
    """visible_if for the set of media a concept applies to (None when it spans all four)."""
    s = [m for m in ALL_MEDIA if m in media]
    if len(s) == len(ALL_MEDIA):
        return None
    return "interrupting_medium in [%s]" % ", ".join("'%s'" % m for m in s)


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# ---------------------------------------------------------------- the verified 122-item alignment
# (key, label, cat, {medium: item_number}, optional, section). cat A=visual_mechanical, B=electrical.
# Cross-checked: 72 VM + 50 electrical refs, every NETA item across the 4 procedures assigned once.
CONCEPTS = [
    # --- common + medium-specific VISUAL/MECHANICAL (cat A) -> visual_mechanical checklist
    ("np_drawings",     "Nameplate data compared with drawings",                          "A", {"air": 1, "oil": 1, "vacuum": 1, "sf6": 1}, False, "nameplate"),
    ("phys_mech",       "Physical and mechanical condition",                              "A", {"air": 2, "oil": 2, "vacuum": 2, "sf6": 2}, False, "visual_mechanical"),
    ("anchorage",       "Anchorage, alignment, grounding (and clearances)",               "A", {"air": 3, "oil": 3, "vacuum": 3, "sf6": 3}, False, "visual_mechanical"),
    ("maint_devices",   "Maintenance devices / special tools and gauges available",       "A", {"air": 4, "oil": 4, "vacuum": 4, "sf6": 4}, False, "visual_mechanical"),
    ("clean",           "Unit is clean",                                                  "A", {"air": 5, "oil": 7, "vacuum": 5, "sf6": 5}, False, "visual_mechanical"),
    ("arc_chutes",      "Arc chutes intact",                                              "A", {"air": 6}, False, "visual_mechanical"),
    ("contacts_align",  "Moving/stationary contacts condition and alignment",             "A", {"air": 7}, False, "visual_mechanical"),
    ("slow_close",      "Slow close/open contact-sequence check (IEEE C37.04)",           "A", {"air": 8, "sf6": 10}, False, "visual_mechanical"),
    ("mech_operation",  "Mechanical operation tests on operating mechanism",              "A", {"air": 9, "oil": 10, "vacuum": 6, "sf6": 11}, False, "visual_mechanical"),
    ("torque",          "Bolted connections torqued (calibrated wrench; Table 100.12)",   "A", {"air": 10, "oil": 12, "vacuum": 8, "sf6": 12}, False, "visual_mechanical"),
    ("cell_fit",        "Cell fit and element alignment",                                 "A", {"air": 11, "vacuum": 9}, False, "visual_mechanical"),
    ("racking",         "Racking mechanism operation",                                    "A", {"air": 12, "oil": 13, "vacuum": 10}, False, "visual_mechanical"),
    ("puffer",          "Puffer operation",                                               "A", {"air": 13}, False, "visual_mechanical"),
    ("lubrication",     "Lubrication of moving/sliding current-carrying parts",           "A", {"air": 14, "oil": 17, "vacuum": 11, "sf6": 13}, False, "visual_mechanical"),
    ("mechanism_motion", "Mechanism-motion / travel-velocity analysis",                   "A", {"air": 16, "oil": 15, "vacuum": 14, "sf6": 16}, True, "visual_mechanical"),
    ("coil_signature",  "Trip/close coil current-signature analysis",                     "A", {"air": 17, "oil": 16, "vacuum": 13, "sf6": 15}, True, "visual_mechanical"),
    ("thermography",    "Thermographic survey (Section 9)",                               "A", {"air": 19, "oil": 19, "vacuum": 16, "sf6": 18}, True, "visual_mechanical"),
    ("oil_level",       "Correct oil level in tanks and bushings",                        "A", {"oil": 5}, False, "visual_mechanical"),
    ("breather",        "Breather vents clear",                                           "A", {"oil": 6}, False, "visual_mechanical"),
    ("hydraulic",       "Hydraulic system / air compressor inspected",                    "A", {"oil": 8}, False, "visual_mechanical"),
    ("alarms_oil",      "Alarms / pressure-limit switches (pneumatic/hydraulic) tested",  "A", {"oil": 9}, False, "visual_mechanical"),
    ("internal_insp",   "Internal inspection",                                            "A", {"oil": 11}, True, "visual_mechanical"),
    ("contact_gap",     "Critical distances / contact gap measured",                      "A", {"vacuum": 7}, False, "visual_mechanical"),
    ("sf6_system",      "Operating mechanism / pneumatic-hydraulic / SF6 system inspected", "A", {"sf6": 7}, False, "visual_mechanical"),
    ("sf6_leaks",       "SF6 gas leak test",                                              "A", {"sf6": 8}, False, "visual_mechanical"),
    ("alarms_sf6",      "Alarms / pressure-limit switches (pneumatic/hydraulic/SF6)",     "A", {"sf6": 9}, False, "visual_mechanical"),
    # --- VM items broken out into their own measured sections
    ("contact_timing",  "Contact-timing test (per pole, close/open)",                     "A", {"air": 15, "oil": 14, "vacuum": 12, "sf6": 14}, False, "contact_timing"),
    ("op_counter",      "Operation counter (as-found / as-left)",                         "A", {"air": 18, "oil": 18, "vacuum": 15, "sf6": 17}, False, "operation_counter"),
    ("sf6_gas",         "SF6 gas sample analysis (Table 100.13)",                         "A", {"sf6": 6}, False, "sf6_gas"),
    # --- ELECTRICAL (cat B)
    ("ir_pole",         "Insulation resistance per pole / across open pole (Table 100.1)", "B", {"air": 1, "oil": 2, "vacuum": 1, "sf6": 2}, False, "insulation_resistance"),
    ("ir_control",      "Control-wiring insulation resistance (500/1000 Vdc)",            "B", {"air": 3, "oil": 5, "vacuum": 2, "sf6": 5}, True, "insulation_resistance"),
    ("contact_r",       "Contact / pole resistance",                                      "B", {"air": 2, "vacuum": 3}, False, "contact_resistance"),
    ("static_r",        "Static contact / pole resistance",                               "B", {"oil": 3, "sf6": 3}, False, "contact_resistance"),
    ("dynamic_r",       "Dynamic contact / pole resistance",                              "B", {"oil": 4, "sf6": 4}, True, "contact_resistance"),
    ("bolted_r",        "Bus / bolted-connection resistance (low-resistance ohmmeter)",   "B", {"oil": 1, "sf6": 1}, False, "contact_resistance"),
    ("blowout_r",       "Blowout coil circuit resistance",                                "B", {"air": 9}, False, "contact_resistance"),
    ("dielectric",      "Dielectric withstand (Table 100.19)",                            "B", {"air": 8, "oil": 12, "vacuum": 11, "sf6": 11}, False, "dielectric_withstand"),
    ("vac_bottle",      "Vacuum-bottle integrity (dielectric across open bottle)",        "B", {"vacuum": 10}, False, "dielectric_withstand"),
    ("mac",             "Magnetron atmospheric condition (MAC) test",                     "B", {"vacuum": 9}, True, "dielectric_withstand"),
    ("pf_breaker",      "Power-factor / dissipation-factor, breaker open and closed",     "B", {"air": 6, "oil": 10, "vacuum": 7, "sf6": 9}, False, "power_factor"),
    ("pf_bushing",      "Power-factor on bushings (PF/capacitance tap; hot-collar)",      "B", {"air": 7, "oil": 11, "vacuum": 8, "sf6": 10}, False, "power_factor"),
    ("pickup",          "Minimum pickup voltage, trip and close coils (Table 100.20)",    "B", {"air": 5, "oil": 7, "vacuum": 4, "sf6": 6}, False, "pickup_coils"),
    ("insulating_liquid", "Insulating-liquid sample and test (ASTM D923)",                "B", {"oil": 6}, False, "insulating_liquid"),
    ("aux_features",    "Auxiliary features: electrical close/trip, trip-free, anti-pump", "B", {"oil": 8, "vacuum": 5, "sf6": 7}, False, "auxiliary"),
    ("trip_device",     "Trip breaker by operation of each protective device",            "B", {"oil": 9, "vacuum": 6, "sf6": 8}, False, "auxiliary"),
    ("air_test_position", "Test-position functional checks (close/trip, trip-free, anti-pump)", "B", {"air": 4}, False, "auxiliary"),
    ("heaters",         "Operation of space heaters",                                     "B", {"air": 10, "oil": 13, "vacuum": 12, "sf6": 12}, False, "auxiliary"),
    ("instr_xfmr",      "Instrument transformers tested per Section 7.10 (IT datasheet)", "B", {"oil": 14, "vacuum": 13, "sf6": 13}, False, "instrument_transformers"),
]


def refs_of(c):
    return [f"{MEDIA[m]}.{c[2]}.{n}" for m, n in c[3].items()]


CMAP = {c[0]: c for c in CONCEPTS}
COVERS_BY_SEC = {}
for _c in CONCEPTS:
    COVERS_BY_SEC.setdefault(_c[5], set()).update(refs_of(_c))


def cgate(key):
    return gate(set(CMAP[key][3]))


# ---------------------------------------------------------------- selections
SELECTIONS = [
    {"tag": "interrupting_medium", "label": "Interrupting medium", "value_kind": "selection",
     "options": ["air", "oil", "vacuum", "sf6"], "ties_to": "equipment_model"},
    {"tag": "mounting", "label": "Mounting", "value_kind": "selection",
     "options": ["drawout", "fixed"], "ties_to": "equipment_model"},
    {"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
     "options": ["insulation_resistance", "contact_resistance", "contact_timing",
                 "dielectric_withstand", "power_factor", "minimum_pickup"]},
]

# ---------------------------------------------------------------- 1. nameplate (R-C: inherited)
NAMEPLATE = [
    ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
    ctl("model", "Breaker type / model", "selection", "inherited", ties_to="equipment_model"),
    ctl("serial_no", "Serial no.", "text", "inherited"),
    ctl("catalog_no", "Catalog no.", "text", "inherited"),
    ctl("interrupting_medium", "Interrupting medium", "selection", "inherited",
        options=ALL_MEDIA, ties_to="equipment_model"),
    ctl("voltage_rating", "Rated voltage", "numeric", "inherited", unit="kV"),
    ctl("continuous_current", "Rated continuous current", "numeric", "inherited", unit="A"),
    ctl("interrupting_rating", "Rated interrupting current", "numeric", "inherited", unit="kA"),
    ctl("bil", "BIL", "numeric", "inherited", unit="kV"),
    ctl("op_mechanism", "Operating mechanism", "text", "inherited"),
    ctl("control_voltage", "Control voltage", "numeric", "inherited", unit="V"),
    ctl("mounting", "Mounting", "selection", "inherited", options=["drawout", "fixed"]),
    ctl("poles", "Poles", "numeric", "inherited"),
    ctl("cubicle_code", "Cubicle / location code", "text", "data"),
    ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
        options=COND, neta_ref=refs_of(CMAP["np_drawings"])[0]),
]


# ---------------------------------------------------------------- 2. visual_mechanical (checklist)
def vm_section():
    rows = []
    for c in CONCEPTS:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_refs": sorted(refs_of(c))}
        g = cgate(c[0])
        if g:
            r["visible_if"] = g
        if c[4]:
            r["optional"] = True
        rows.append(r)
    return {
        "key": "visual_mechanical", "title": "Visual and Mechanical Inspection",
        "kind": "table", "neta_basis": PRIMARY,
        "table": {
            "row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
            "columns": [
                ctl("inspected", "Inspected", "boolean"),
                ctl("condition", "Condition", "selection", options=COND),
                ctl("clean_lube", "Clean / lube", "selection", options=COND + ["not_applicable"]),
                ctl("value", "Value (e.g. torque)", "text"),
                ctl("note", "Note", "text"),
            ],
        },
    }


POLES = [{"key": p, "label": f"Pole {p}"} for p in ("A", "B", "C")]


# ---------------------------------------------------------------- 3. operation_counter
COUNTER = [
    ctl("counter_as_found", "Operation counter - as found", "numeric", "data",
        neta_ref=sorted(refs_of(CMAP["op_counter"]))[0]),
    ctl("counter_as_left", "Operation counter - as left", "numeric", "data"),
]


# ---------------------------------------------------------------- 4. contact_timing (per pole)
def contact_timing_section():
    cols = [
        ctl("close_ms_af", "Close time - as found", "numeric", unit="ms",
            acceptance={"basis": "mfr_tolerance"},
            tolerance_source={"engine": "mfr", "function": "contact_timing",
                              "inputs": ["manufacturer", "model", "interrupting_medium"]}),
        ctl("close_ms_al", "Close time - as left", "numeric", unit="ms"),
        ctl("open_ms_af", "Open time - as found", "numeric", unit="ms",
            acceptance={"basis": "mfr_tolerance"},
            tolerance_source={"engine": "mfr", "function": "contact_timing",
                              "inputs": ["manufacturer", "model", "interrupting_medium"]}),
        ctl("open_ms_al", "Open time - as left", "numeric", unit="ms"),
        ctl("note", "Note", "text"),
    ]
    return {
        "key": "contact_timing", "title": "Contact Timing",
        "kind": "table", "neta_basis": PRIMARY,
        "visible_if": "'contact_timing' in tests_performed",
        "table": {"row_dim": {"tag": "pole", "label": "Pole", "rows": POLES}, "columns": cols},
    }


# ---------------------------------------------------------------- 5. insulation_resistance
def ir_section():
    rows = [
        {"key": "pole_1_2", "label": "Pole 1-2"},
        {"key": "pole_2_3", "label": "Pole 2-3"},
        {"key": "pole_1_3", "label": "Pole 1-3"},
        {"key": "pole_to_ground_closed", "label": "Pole-to-ground (closed)"},
        {"key": "across_open_pole", "label": "Across each open pole"},
        {"key": "control_wiring", "label": "Control wiring",
         "neta_refs": sorted(refs_of(CMAP["ir_control"])), "optional": True},
    ]
    return {
        "key": "insulation_resistance", "title": "Insulation Resistance",
        "kind": "table", "neta_basis": PRIMARY,
        "table": {
            "row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
            "columns": [
                ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                    acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"},
                    tolerance_source={"engine": "neta_table", "table": "100.1",
                                      "inputs": ["voltage_rating"]}),
                ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
                ctl("tcf", "Temp-correction factor", "numeric", "calc"),
                ctl("corrected_mohm", "Corrected to 20degC", "numeric", "calc", unit="Mohm"),
            ],
        },
    }


# ---------------------------------------------------------------- 6. contact_resistance
def contact_r_section():
    rows = [
        {"key": "contact_pole", "label": "Contact / pole resistance", "visible_if": cgate("contact_r")},
        {"key": "static_r", "label": "Static contact resistance", "visible_if": cgate("static_r")},
        {"key": "dynamic_r", "label": "Dynamic contact resistance", "visible_if": cgate("dynamic_r"), "optional": True},
        {"key": "bolted_r", "label": "Bus / bolted-connection resistance", "visible_if": cgate("bolted_r")},
        {"key": "blowout_r", "label": "Blowout coil circuit resistance", "visible_if": cgate("blowout_r")},
    ]
    return {
        "key": "contact_resistance", "title": "Contact / Pole Resistance",
        "kind": "table", "neta_basis": PRIMARY,
        "table": {
            "row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
            "columns": [
                ctl("pole_a", "Pole A", "numeric", unit="uohm",
                    acceptance={"basis": "mfr_tolerance", "rule": "investigate >50% pole-pole deviation"},
                    tolerance_source={"engine": "mfr", "function": "contact_resistance",
                                      "inputs": ["manufacturer", "model"]}),
                ctl("pole_b", "Pole B", "numeric", unit="uohm"),
                ctl("pole_c", "Pole C", "numeric", unit="uohm"),
                ctl("temp", "Temp", "numeric", unit="degC"),
            ],
        },
    }


# ---------------------------------------------------------------- 7. dielectric_withstand
def dielectric_section():
    rows = [
        {"key": "phase_a", "label": "Phase A (poles not under test grounded)"},
        {"key": "phase_b", "label": "Phase B (poles not under test grounded)"},
        {"key": "phase_c", "label": "Phase C (poles not under test grounded)"},
        {"key": "vac_bottle", "label": "Vacuum-bottle integrity (breaker open)",
         "neta_refs": sorted(refs_of(CMAP["vac_bottle"])), "visible_if": cgate("vac_bottle")},
        {"key": "mac", "label": "Magnetron atmospheric condition (MAC)",
         "neta_refs": sorted(refs_of(CMAP["mac"])), "visible_if": cgate("mac"), "optional": True},
    ]
    return {
        "key": "dielectric_withstand", "title": "Dielectric Withstand (Hipot)",
        "kind": "table", "neta_basis": PRIMARY,
        "visible_if": "'dielectric_withstand' in tests_performed",
        "table": {
            "row_dim": {"tag": "test_point", "label": "Test point", "rows": rows},
            "columns": [
                ctl("test_kv", "Test voltage", "numeric", unit="kV",
                    acceptance={"basis": "mfr_tolerance", "fallback_table": "100.19"},
                    tolerance_source={"engine": "neta_table", "table": "100.19",
                                      "inputs": ["voltage_rating"]}),
                ctl("duration_s", "Duration", "numeric", unit="s"),
                ctl("leakage_ua", "Leakage", "numeric", unit="uA"),
                ctl("result", "Result", "selection", options=["pass", "fail"]),
            ],
        },
    }


# ---------------------------------------------------------------- 8. power_factor
def pf_section():
    rows = [
        {"key": "breaker_open", "label": "Breaker open (each pole)"},
        {"key": "breaker_closed", "label": "Breaker closed (each phase)"},
        {"key": "bushing", "label": "Bushing (PF/cap tap or hot-collar)", "grow": True},
    ]
    return {
        "key": "power_factor", "title": "Power-Factor / Dissipation-Factor",
        "kind": "table", "neta_basis": PRIMARY,
        "visible_if": "'power_factor' in tests_performed",
        "table": {
            "row_dim": {"tag": "test_point", "label": "Test point", "rows": rows},
            "columns": [
                ctl("pf_pct", "Power factor", "numeric", unit="pct",
                    acceptance={"basis": "comparison", "rule": "vs prior/similar units or mfr data"}),
                ctl("capacitance", "Capacitance", "numeric", unit="pF"),
                ctl("watts_loss", "Watts loss", "numeric", unit="W"),
                ctl("temp", "Temp", "numeric", unit="degC"),
            ],
        },
    }


# ---------------------------------------------------------------- 9. pickup_coils
def pickup_section():
    rows = [{"key": "trip_coil", "label": "Trip coil"}, {"key": "close_coil", "label": "Close coil"}]
    return {
        "key": "pickup_coils", "title": "Minimum Pickup Voltage (Trip / Close Coils)",
        "kind": "table", "neta_basis": PRIMARY,
        "visible_if": "'minimum_pickup' in tests_performed",
        "table": {
            "row_dim": {"tag": "coil", "label": "Coil", "rows": rows},
            "columns": [
                ctl("rated_v", "Rated control voltage", "numeric", unit="V"),
                ctl("min_pickup_af", "Min pickup - as found", "numeric", unit="V",
                    acceptance={"basis": "mfr_tolerance", "fallback_table": "100.20"},
                    tolerance_source={"engine": "neta_table", "table": "100.20",
                                      "inputs": ["control_voltage"]}),
                ctl("min_pickup_al", "Min pickup - as left", "numeric", unit="V"),
            ],
        },
    }


# ---------------------------------------------------------------- 10. insulating_liquid (oil)
INSULATING_LIQUID = [
    ctl("dielectric_breakdown_kv", "Dielectric breakdown (ASTM D877 / D1816)", "numeric", unit="kV",
        acceptance={"basis": "standard", "ref": "ASTM D923"}),
    ctl("color", "Color", "text"),
    ctl("neutralization_number", "Neutralization number", "numeric", unit="mgKOH/g"),
    ctl("interfacial_tension", "Interfacial tension", "numeric", unit="dyne/cm"),
    ctl("water_content_ppm", "Water content", "numeric", unit="ppm"),
    ctl("power_factor_pct", "Liquid power factor", "numeric", unit="pct"),
]

# ---------------------------------------------------------------- 11. sf6_gas (sf6)
SF6_GAS = [
    ctl("moisture_ppmv", "Moisture", "numeric", unit="ppmv",
        acceptance={"basis": "table", "table": "100.13"},
        tolerance_source={"engine": "neta_table", "table": "100.13", "inputs": []}),
    ctl("purity_pct", "Purity", "numeric", unit="pct"),
    ctl("decomposition", "Decomposition products", "text"),
    ctl("gas_pressure", "Gas pressure / density", "numeric", unit="kPa"),
    ctl("gas_temp", "Gas temperature", "numeric", unit="degC"),
]

# ---------------------------------------------------------------- 12. auxiliary
AUX = [
    ctl("aux_close_trip", "Electrical close and trip", "selection", "data", options=COND),
    ctl("aux_trip_free", "Trip-free operation", "selection", "data", options=COND),
    ctl("aux_antipump", "Anti-pump function", "selection", "data", options=COND),
    ctl("air_test_position_block", "Test-position functional checks", "selection", "data",
        options=COND, visible_if=cgate("air_test_position")),
    ctl("trip_by_protective_device", "Trip by operation of each protective device", "selection", "data",
        options=COND, visible_if=cgate("trip_device")),
    ctl("heaters", "Space heaters operational", "selection", "data", options=COND),
]

# ---------------------------------------------------------------- 13. instrument_transformers (xref)
INSTR_XFMR = [
    ctl("instrument_transformers_xref",
        "Instrument transformers - test per NETA 7.10 (recorded on the Instrument Transformer datasheet)",
        "text", "reference", visible_if=cgate("instr_xfmr")),
]

# ---------------------------------------------------------------- 14/15. test equipment + comments
TEST_EQUIPMENT = {
    "key": "test_equipment", "title": "Test Equipment Used", "kind": "table",
    "table": {"row_dim": {"tag": "equipment", "label": "Instrument", "rows": [], "grow": True},
              "columns": [
                  ctl("manufacturer", "Manufacturer", "text", "inherited"),
                  ctl("model", "Model", "text", "inherited"),
                  ctl("type", "Type", "text", "inherited"),
                  ctl("serial_id", "Serial / ID", "text", "inherited"),
                  ctl("cal_date", "Cal date", "date", "inherited"),
                  ctl("cal_due", "Cal due", "date", "inherited"),
              ]},
}

COMMENTS = [
    ctl("comments", "Comments", "text", "data", grow=True),
    ctl("deficiencies", "Deficiencies", "text", "data", grow=True),
]


def build_schema():
    sections = [
        {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": PRIMARY, "fields": NAMEPLATE},
        vm_section(),
        {"key": "operation_counter", "title": "Operation Counter", "kind": "fields",
         "neta_basis": PRIMARY, "fields": COUNTER},
        contact_timing_section(),
        ir_section(),
        contact_r_section(),
        dielectric_section(),
        pf_section(),
        pickup_section(),
        {"key": "insulating_liquid", "title": "Insulating Liquid (Oil)", "kind": "fields",
         "neta_basis": "7.6.2", "visible_if": gate({"oil"}), "fields": INSULATING_LIQUID},
        {"key": "sf6_gas", "title": "SF6 Gas Analysis", "kind": "fields",
         "neta_basis": "7.6.4", "visible_if": gate({"sf6"}), "fields": SF6_GAS},
        {"key": "auxiliary", "title": "Auxiliary Features and Functional Checks", "kind": "fields",
         "neta_basis": PRIMARY, "fields": AUX},
        {"key": "instrument_transformers", "title": "Instrument Transformers (Cross-Reference)",
         "kind": "fields", "neta_basis": "7.10", "visible_if": gate({"oil", "vacuum", "sf6"}),
         "fields": INSTR_XFMR},
        TEST_EQUIPMENT,
        {"key": "comments_deficiencies", "title": "Comments and Deficiencies", "kind": "fields",
         "fields": COMMENTS},
    ]
    # attach the authoritative coverage map (from CONCEPTS) to each section
    for s in sections:
        cov = COVERS_BY_SEC.get(s["key"])
        if cov:
            s["neta_covers"] = sorted(cov)
    return {"version": 1, "family": "mvhv_circuit_breaker",
            "selections": SELECTIONS, "sections": sections}


def required_refs(json_path):
    d = json.load(open(json_path, encoding="utf-8"))
    eqs = d["equipment"]
    req = set()
    for sec in MEDIA.values():
        e = next(x for x in eqs if x.get("section") == sec)
        ats = e.get("ats_data") or {}
        vm = ats.get("visual_mechanical") or []
        el = ats.get("electrical_tests") or []
        req |= {f"{sec}.A.{i + 1}" for i in range(len(vm))}
        req |= {f"{sec}.B.{i + 1}" for i in range(len(el))}
    return req


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    schema = build_schema()

    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src)
    prefixes = tuple(s + "." for s in MEDIA.values())
    missing = required - covered
    phantom = {r for r in covered if r.startswith(prefixes)} - required
    assert not missing, f"coverage gap (silent drop): {sorted(missing)}"
    assert not phantom, f"phantom coverage (no such NETA item): {sorted(phantom)}"
    assert len(required) == 122, f"expected 122 NETA items, got {len(required)}"
    assert len(schema["sections"]) == 15, len(schema["sections"])

    payload = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
    sql_json = payload.replace("'", "''")
    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - MV/HV Circuit-Breaker composite datasheet (ats_mvhv_cb_v1).",
        "-- GENERATED by gen_mv_cb_template.py - do not edit by hand.",
        "-- ONE template; interrupting_medium selector (air/oil/vacuum/sf6) gates the deltas.",
        "-- R-A: MV/HV has no integral trip curve -> tolerance_source = neta_table + mfr",
        "--      (NOT lvbreakertcc); windows DECLARED, resolved at provisioning.",
        f"-- Coverage: all {len(required)} NETA ATS items across 7.6.1.3/7.6.2/7.6.3/7.6.4 mapped.",
        "-- Idempotent (ON CONFLICT); deterministic UUID5 template_id.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "INSERT INTO records.form_templates",
        "  (template_id, template_code, title, form_type, neta_standard, neta_section,",
        "   asset_class_id, version, is_current, field_schema, description, source)",
        "VALUES (",
        f"  '{TEMPLATE_ID}', 'ats_mvhv_cb_v1',",
        "  'Medium/High-Voltage Circuit Breaker - ATS Field Data Sheet',",
        f"  'neta_datasheet', 'ats', '{PRIMARY}',",
        "  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'cb_mvhv'),",
        "  1, true,",
        f"  '{sql_json}'::jsonb,",
        "  'Composite MV/HV circuit-breaker datasheet (air/oil/vacuum/SF6 via interrupting_medium). Chip 2b.',",
        "  'manual'",
        ")",
        "ON CONFLICT (template_code, version) DO UPDATE SET",
        "  field_schema = EXCLUDED.field_schema, title = EXCLUDED.title,",
        "  neta_section = EXCLUDED.neta_section, asset_class_id = EXCLUDED.asset_class_id,",
        "  description = EXCLUDED.description, updated_at = now();",
        "",
        "COMMIT;",
    ]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"sections={len(schema['sections'])}  selections={len(schema['selections'])}  "
          f"neta_covered={len(covered & required)}/{len(required)}  json_bytes={len(payload)}")


if __name__ == "__main__":
    main()
