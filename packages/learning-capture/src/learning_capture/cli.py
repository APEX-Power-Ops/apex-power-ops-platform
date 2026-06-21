import argparse
import dataclasses
import json
import sys

from .acquisition import record_acquired_event
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

    acq = sub.add_parser("acquire", help="append a learning event with a provenance envelope (Slice 2d)")
    acq.add_argument("--user", required=True)
    acq.add_argument("--type", required=True, dest="event_type")
    acq.add_argument("--content", default=None, dest="study_content_id")
    acq.add_argument("--section", default=None, dest="neta_section")
    acq.add_argument("--run-id", required=True, dest="acquisition_run_id")
    acq.add_argument("--source-surface", default="cli", dest="source_surface")
    acq.add_argument("--observed-by", required=True, dest="observed_by")
    acq.add_argument("--evidence-ref", required=True, dest="evidence_ref")
    acq.add_argument("--fidelity", required=True, dest="data_fidelity")
    acq.add_argument("--score", type=float, default=None, dest="score_percent")
    acq.add_argument("--confidence", type=int, default=None, dest="confidence")

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
    if args.cmd == "acquire":
        ev = record_acquired_event(
            user_id=args.user, event_type=args.event_type, study_content_id=args.study_content_id,
            neta_section=args.neta_section, acquisition_run_id=args.acquisition_run_id,
            source_surface=args.source_surface, observed_by=args.observed_by,
            evidence_ref=args.evidence_ref, data_fidelity=args.data_fidelity,
            score_percent=args.score_percent, confidence=args.confidence)
        print(json.dumps({"event_id": ev.event_id, "event_type": ev.event_type}, ensure_ascii=False))
        return 0
    return 1
