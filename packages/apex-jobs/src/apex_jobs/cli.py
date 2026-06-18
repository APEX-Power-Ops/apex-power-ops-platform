"""apex-jobs CLI - thin argparse wrapper over the engine. `apex-jobs <verb> ...`.

Verbs: enqueue, queue, claim, start, report, request-gate, approve, reject,
gates, status, ledger. Returns an int exit code (3 = gated/refused).
"""
import argparse
import json
import sys

from . import engine


def cmd_enqueue(a):
    payload = json.loads(a.payload) if a.payload else {}
    jid = engine.enqueue(
        dispatch_id=a.dispatch_id, title=a.title, payload=payload, target=a.target,
        priority=a.priority, predecessor_id=a.predecessor, authority=a.authority,
        requires_approval=a.requires_approval, gate_categories=a.gate_category,
        env_required=a.env_required, created_by=a.by, closeout_path=a.closeout)
    print(jid)
    return 0


def cmd_queue(a):
    rows = engine.list_eligible()
    if not rows:
        print("(no eligible jobs)")
    for r in rows:
        print(f"{r['priority']:>4}  {r['dispatch_id']}  {r['title']}  -> {r['target']}")
    return 0


def cmd_claim(a):
    job = engine.claim(as_=a.as_, env=a.env)
    if job is None:
        print("none")
        return 0
    print(f"{job['dispatch_id']}\t{job['id']}")
    return 0


def cmd_start(a):
    try:
        run_id = engine.start(a.job, claimed_by=a.as_, run_env=a.env)
    except engine.GateError as e:
        print(f"GATED: {e}")
        return 3
    print(run_id)
    return 0


def cmd_report(a):
    result = json.loads(a.result) if a.result else None
    print(engine.report(a.run, exit_code=a.exit_code, result=result))
    return 0


def cmd_request_gate(a):
    print(engine.request_gate(a.job, a.type, note=a.note))
    return 0


def cmd_approve(a):
    print(engine.approve(a.gate, by=a.by, note=a.note))
    return 0


def cmd_reject(a):
    print(engine.reject(a.gate, by=a.by, note=a.note))
    return 0


def cmd_gates(a):
    for g in engine.gates_for(a.job):
        print(f"{g['id']}\t{g['gate_type']}\t{g['state']}")
    return 0


def cmd_status(a):
    job = engine.get_job(a.ident)
    if job is None:
        print("not found")
        return 1
    print(job["status"])
    return 0


def cmd_ledger(a):
    for r in engine.runs_for(a.ident):
        print(f"attempt {r['attempt']}  env={r['env']}  {r['status']}  "
              f"exit={r['exit_code']}  by={r['claimed_by']}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="apex-jobs", description="APEX orchestration task bus")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enqueue")
    e.add_argument("--dispatch-id", required=True, dest="dispatch_id")
    e.add_argument("--title", required=True)
    e.add_argument("--payload")
    e.add_argument("--target", default="any")
    e.add_argument("--priority", type=int, default=100)
    e.add_argument("--predecessor", default=None)
    e.add_argument("--authority", default="gated")
    e.add_argument("--requires-approval", action="store_true", dest="requires_approval")
    e.add_argument("--gate-category", action="append", default=[], dest="gate_category")
    e.add_argument("--env-required", default="any", dest="env_required")
    e.add_argument("--by", default=None)
    e.add_argument("--closeout", default=None)
    e.set_defaults(fn=cmd_enqueue)

    q = sub.add_parser("queue")
    q.set_defaults(fn=cmd_queue)

    c = sub.add_parser("claim")
    c.add_argument("--as", required=True, dest="as_")
    c.add_argument("--env", default=None)
    c.set_defaults(fn=cmd_claim)

    s = sub.add_parser("start")
    s.add_argument("--job", required=True)
    s.add_argument("--as", required=True, dest="as_")
    s.add_argument("--env", required=True)
    s.set_defaults(fn=cmd_start)

    r = sub.add_parser("report")
    r.add_argument("--run", required=True)
    r.add_argument("--exit-code", type=int, required=True, dest="exit_code")
    r.add_argument("--result")
    r.set_defaults(fn=cmd_report)

    rg = sub.add_parser("request-gate")
    rg.add_argument("--job", required=True)
    rg.add_argument("--type", required=True)
    rg.add_argument("--note", default=None)
    rg.set_defaults(fn=cmd_request_gate)

    ap = sub.add_parser("approve")
    ap.add_argument("--gate", required=True)
    ap.add_argument("--by", required=True)
    ap.add_argument("--note", default=None)
    ap.set_defaults(fn=cmd_approve)

    rj = sub.add_parser("reject")
    rj.add_argument("--gate", required=True)
    rj.add_argument("--by", required=True)
    rj.add_argument("--note", default=None)
    rj.set_defaults(fn=cmd_reject)

    g = sub.add_parser("gates")
    g.add_argument("--job", required=True)
    g.set_defaults(fn=cmd_gates)

    st = sub.add_parser("status")
    st.add_argument("ident")
    st.set_defaults(fn=cmd_status)

    le = sub.add_parser("ledger")
    le.add_argument("ident")
    le.set_defaults(fn=cmd_ledger)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
