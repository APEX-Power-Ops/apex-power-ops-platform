"""Declarative (ptm, *, transformer) mapping: PtmModel -> ProposedValue[].

Targets the ats_liquid_xfmr_v1 / ats_dry_xfmr_v1 instrument_import sections (migration 020):
  turns_ratio       (table; rows h_x / h_y / x_y; cols measured_ratio / deviation_pct / nominal_ratio)
  winding_resistance(table; rows h / x / y;       cols ohms / temp)
  power_factor      (table; rows ch / cl / chl / ct / bushing; cols pf_pct / capacitance)
  excitation_current(fields; phase_a / phase_b / phase_c)

Value selection: corrected where the instrument supplies correction; the measured value goes in notes.
Nominal/as-tested measurements only (10a); per-tap row expansion is out of scope (see spec deferred).
Unknown rows are skipped (never invent a phantom target).
"""
from __future__ import annotations

from power_test_converters.model import PtmModel

from records_import.proposal import ProposedValue

# PTM winding-pair / winding / PF-measurement-name -> datasheet row key
_TTR_ROW = {"H-X": "h_x", "H-Y": "h_y", "X-Y": "x_y"}
_WR_ROW = {"H": "h", "X": "x", "Y": "y"}
_PF_ROW = {"ICH": "ch", "ICL": "cl", "ICHL": "chl", "ICT": "ct"}
_EXC_FIELD = {"A": "phase_a", "B": "phase_b", "C": "phase_c"}


def _device(inst) -> str | None:
    if inst is None:
        return None
    name = (inst.test_set_name or "OMICRON").strip()
    if inst.serial_number:
        return f"{name} / SN {inst.serial_number}".strip(" /")
    return name or None


def map_ptm_transformer(model: PtmModel) -> list[ProposedValue]:
    out: list[ProposedValue] = []

    # --- turns ratio ---
    for test in model.turns_ratio_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            row = _TTR_ROW.get((m.name or m.phase or "").upper())
            if not row:
                continue
            for col, val in (("measured_ratio", m.voltage_turns_ratio),
                             ("deviation_pct", m.ratio_deviation),
                             ("nominal_ratio", m.nominal_ratio)):
                if val is not None:
                    out.append(ProposedValue(f"turns_ratio.{row}.{col}", "turns_ratio",
                                             value_numeric=val, measured_at=m.measured_at, origin_device=dev))

    # --- winding resistance (corrected ohms; measured -> notes; reference temp) ---
    for test in model.winding_resistance_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            row = _WR_ROW.get((m.name or m.phase or "").upper())
            if not row:
                continue
            if m.resistance_corrected_ohm is not None:
                notes = None
                if m.resistance_measured_ohm is not None:
                    notes = f"measured={m.resistance_measured_ohm} ohm (corrected to ref temp)"
                out.append(ProposedValue(f"winding_resistance.{row}.ohms", "winding_resistance",
                                         value_numeric=m.resistance_corrected_ohm, unit="ohm",
                                         measured_at=m.measured_at, origin_device=dev, notes=notes))
            if test.reference_temperature_c is not None:
                out.append(ProposedValue(f"winding_resistance.{row}.temp", "winding_resistance",
                                         value_numeric=test.reference_temperature_c, unit="degC",
                                         measured_at=m.measured_at, origin_device=dev))

    # --- power factor (overall + bushing); corrected PF + capacitance ---
    for m in (model.overall_power_factor + model.bushing_power_factor):
        row = _PF_ROW.get((m.measurement_name or "").upper())
        if not row:
            continue
        dev = _device(m.instrument)
        if m.power_factor_corrected is not None:
            out.append(ProposedValue(f"power_factor.{row}.pf_pct", "power_factor",
                                     value_numeric=m.power_factor_corrected, unit="pct",
                                     measured_at=m.measured_at, origin_device=dev))
        if m.capacitance_measured_f is not None:
            out.append(ProposedValue(f"power_factor.{row}.capacitance", "power_factor",
                                     value_numeric=m.capacitance_measured_f, unit="F",
                                     measured_at=m.measured_at, origin_device=dev))

    # --- excitation current (phase fields) ---
    for test in model.exciting_current_tests:
        dev = _device(test.instrument)
        for m in test.measurements:
            field = _EXC_FIELD.get((m.phase or "").upper())
            if field and m.current_corrected_a is not None:
                out.append(ProposedValue(f"excitation_current.{field}", "excitation_current",
                                         value_numeric=m.current_corrected_a, unit="A",
                                         measured_at=m.measured_at, origin_device=dev))

    return out
