from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from .extract import extract_workbook


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="ops-intake", description="Estimator .xlsm -> ops.* intake")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="extract .xlsm -> payload JSON (no DB)")
    ex.add_argument("xlsm")
    ex.add_argument("--out", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "extract":
        payload = extract_workbook(args.xlsm)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(dataclasses.asdict(payload), f, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}: contract_value={payload.project.contract_value}, "
              f"scopes={len(payload.scopes)}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
