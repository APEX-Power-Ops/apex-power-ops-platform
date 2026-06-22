from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from .extract import extract_workbook
from .envelope import create_run
from .approve import approve_run


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="ops-intake", description="Estimator .xlsm -> ops.* intake")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="extract .xlsm -> payload JSON (no DB)")
    ex.add_argument("xlsm")
    ex.add_argument("--out", required=True)

    it = sub.add_parser("intake", help="upload .xlsm and create intake run")
    it.add_argument("xlsm")
    it.add_argument("--dsn", required=True)
    it.add_argument("--uploaded-by", required=True, metavar="UUID")

    ap_cmd = sub.add_parser("approve", help="approve an intake run")
    ap_cmd.add_argument("run_id")
    ap_cmd.add_argument("--dsn", required=True)
    ap_cmd.add_argument("--approved-by", required=True, metavar="UUID")

    args = ap.parse_args(argv)

    if args.cmd == "extract":
        payload = extract_workbook(args.xlsm)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(dataclasses.asdict(payload), f, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}: contract_value={payload.project.contract_value}, "
              f"scopes={len(payload.scopes)}")
        return 0

    if args.cmd == "intake":
        import pathlib
        xlsm_path = pathlib.Path(args.xlsm)
        raw_bytes = xlsm_path.read_bytes()
        result = create_run(
            args.dsn,
            uploaded_by=args.uploaded_by,
            filename=xlsm_path.name,
            raw_bytes=raw_bytes,
            content_type="xlsm",
        )
        print(f"run_id={result['run_id']} status={result['status']} conflict_kind={result['conflict_kind']}")
        return 0

    if args.cmd == "approve":
        result = approve_run(args.dsn, args.run_id, approved_by=args.approved_by)
        print(f"outcome={result['outcome']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
