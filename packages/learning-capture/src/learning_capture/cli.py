import argparse
import dataclasses
import json
import sys

from .capture import list_events, record_event


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-capture",
                                 description="Record / list learning capture events (learning_dev)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="append a learning event")
    rec.add_argument("--user", required=True)
    rec.add_argument("--type", required=True, dest="event_type")
    rec.add_argument("--content", default=None, dest="study_content_id")
    rec.add_argument("--section", default=None, dest="neta_section")
    rec.add_argument("--payload", default=None, help="JSON object string")

    lst = sub.add_parser("list", help="list recent events")
    lst.add_argument("--user", default=None)
    lst.add_argument("--limit", type=int, default=50)
    lst.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "record":
        payload = json.loads(args.payload) if args.payload else None
        ev = record_event(args.user, args.event_type, study_content_id=args.study_content_id,
                          neta_section=args.neta_section, payload=payload)
        print(json.dumps({"event_id": ev.event_id, "event_type": ev.event_type}, ensure_ascii=False))
        return 0
    if args.cmd == "list":
        rows = list_events(user_id=args.user, limit=args.limit)
        dicts = [dataclasses.asdict(r) for r in rows]
        if args.json:
            print(json.dumps(dicts, ensure_ascii=False, default=str))
        else:
            for r in rows:
                print(f"{r.occurred_at}  {r.event_type:>20}  {r.neta_section or '-'}  {r.event_id}")
        return 0
    return 1
