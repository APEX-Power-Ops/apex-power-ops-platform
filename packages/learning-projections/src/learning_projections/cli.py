import argparse
import dataclasses
import json
import sys

from .projections import assessment_summary, cohort_aggregate, competency_rollup, content_progress


def _dump(obj):
    if isinstance(obj, list):
        return [dataclasses.asdict(o) for o in obj]
    return dataclasses.asdict(obj)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-projections",
                                 description="Read-model projections over learning_events (learning_dev); prints JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("progress", "assessments", "competency"):
        p = sub.add_parser(name)
        p.add_argument("--user", required=True)
        if name == "competency":
            p.add_argument("--level", default=None, choices=["I", "II", "III", "IV"])
    pc = sub.add_parser("cohort")
    pc.add_argument("--level", default=None, choices=["I", "II", "III", "IV"])
    args = ap.parse_args(argv)

    if args.cmd == "progress":
        result = content_progress(args.user)
    elif args.cmd == "assessments":
        result = assessment_summary(args.user)
    elif args.cmd == "competency":
        result = competency_rollup(args.user, level=args.level)
    elif args.cmd == "cohort":
        result = cohort_aggregate(level=args.level)
    else:
        return 1
    print(json.dumps(_dump(result), ensure_ascii=False, default=str))
    return 0
