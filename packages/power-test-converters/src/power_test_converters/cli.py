from __future__ import annotations

import argparse
from pathlib import Path

from power_test_converters.dtax import write_dtax
from power_test_converters.ptm import read_ptm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert an Omicron PTM transformer package to Doble dtax XML."
    )
    parser.add_argument("input_ptm", type=Path)
    parser.add_argument("output_dtax", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output dtax file if it already exists.",
    )
    parser.add_argument(
        "--template-dtax",
        type=Path,
        help=(
            "Optional known-good Doble dtax file to use as the output skeleton. "
            "This is recommended when importing into Doble software."
        ),
    )
    args = parser.parse_args(argv)

    if args.output_dtax.exists() and not args.overwrite:
        parser.error(f"output already exists: {args.output_dtax}")
    if args.template_dtax is not None and not args.template_dtax.exists():
        parser.error(f"template dtax does not exist: {args.template_dtax}")

    model = read_ptm(args.input_ptm)
    write_dtax(model, args.output_dtax, template_path=args.template_dtax)
    bushing_summary = (
        f"{len(model.bushing_power_factor)} bushing PF rows"
        if args.template_dtax is None
        else f"{len(model.bushing_power_factor)} bushing PF rows parsed"
    )

    print(f"Converted: {args.input_ptm}")
    print(f"Output: {args.output_dtax}")
    print(
        "Summary: "
        f"{model.transformer.apparatus_id or model.transformer.serial_number}; "
        f"{len(model.bushings)} bushings; "
        f"{len(model.overall_power_factor)} overall PF rows; "
        f"{bushing_summary}; "
        f"{sum(len(test.measurements) for test in model.turns_ratio_tests)} TTR measurements; "
        f"{sum(len(test.measurements) for test in model.winding_resistance_tests)} WR measurements; "
        f"{sum(len(test.measurements) for test in model.exciting_current_tests)} excitation measurements"
    )
    if args.template_dtax is not None:
        print(f"Template: {args.template_dtax}")
    return 0
