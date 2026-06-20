import argparse
import dataclasses
import json
import sys

from .resolver import resolve


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-resolver",
                                 description="Contextual learning-resource resolver (learning_dev)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rv = sub.add_parser("resolve", help="rank resources for a NETA section")
    rv.add_argument("--section", required=True)
    rv.add_argument("--level", choices=["II", "III", "IV"], default=None)
    rv.add_argument("--limit", type=int, default=20)
    rv.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "resolve":
        items = resolve(args.section, level=args.level, limit=args.limit)
        if args.json:
            json.dump([dataclasses.asdict(r) for r in items], sys.stdout, ensure_ascii=False)
        else:
            for r in items:
                print(f"[{r.source:>13}] {r.score:7.1f}  {r.title}  -- {r.why}")
        return 0
    return 1
