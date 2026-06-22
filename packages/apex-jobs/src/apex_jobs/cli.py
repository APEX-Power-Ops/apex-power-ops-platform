"""apex-jobs CLI - thin argparse wrapper over the engine. `apex-jobs <verb> ...`.

Verbs: enqueue, enqueue-review, review-run, queue, claim, start, report, request-gate, approve, reject,
gates, status, ledger, reap, promotions, review, unblock. Returns an int exit
code (3 = gated/refused).
"""
import argparse
import json
import os
import sys
import uuid

from . import engine


def cmd_enqueue(a):
    payload = json.loads(a.payload) if a.payload else {}
    if a.prompt:
        payload["prompt"] = a.prompt
    jid = engine.enqueue(
        dispatch_id=a.dispatch_id, title=a.title, payload=payload, target=a.target,
        priority=a.priority, predecessor_id=a.predecessor, authority=a.authority,
        requires_approval=a.requires_approval, gate_categories=a.gate_category,
        env_required=a.env_required, created_by=a.by, closeout_path=a.closeout,
        kind=a.kind, max_attempts=a.max_attempts, base_ref=a.base_ref)
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
    """Approve a gate. A promotion gate's approval IS the promotion: route it to
    engine.promote (atomic gate-close + merge), else the normal unblock path."""
    gate = engine.get_gate(a.gate)
    if gate and gate["gate_type"] == "promotion":
        try:
            newsha = engine.promote(gate["job_id"], by=a.by)
        except engine.PromoteError as e:
            print(f"PROMOTE-REFUSED: {e}")
            return 3
        print(f"promoted {newsha}")
        return 0
    print(engine.approve(a.gate, by=a.by, note=a.note))
    return 0


def cmd_reject(a):
    """Reject a gate. A promotion gate's rejection routes to discard_promotion
    (recoverable snapshot + base untouched), else the normal reject path."""
    gate = engine.get_gate(a.gate)
    if gate and gate["gate_type"] == "promotion":
        try:
            engine.discard_promotion(gate["job_id"], by=a.by)
        except engine.PromoteError as e:
            print(f"DISCARD-REFUSED: {e}")
            return 3
        print(f"discarded {gate['job_id']}")
        return 0
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


def cmd_reap(a):
    print(engine.reap())
    return 0


def cmd_promotions(a):
    rows = engine.list_promotions()
    if not rows:
        print("(no jobs awaiting promotion)")
    for r in rows:
        print(f"{r['dispatch_id']}\t{r['title']}\tbase={r['base_ref']}\t"
              f"{r['branch']}\t{r['diff_stat']}")
    return 0


def cmd_review(a):
    runs = engine.runs_for(a.ident)
    if not runs:
        print("(no runs)")
        return 1
    r = runs[-1]
    print(f"branch={r['branch']}")
    print(f"worktree={r['worktree_path']}")
    print(f"diff_stat:\n{r['diff_stat']}")
    print(f"result={r['result']}")
    return 0


def cmd_unblock(a):
    r = engine.unblock(a.ident)
    print(r if r is not None else "none")
    return 0


def cmd_enqueue_review(a):
    """Enqueue a cross-engine (Codex) review job: `codex exec review` of review_head
    vs base_ref, captured as findings (no promotion gate). kind=agent + target=codex
    + payload.review_head are fixed here so the IRP cross-engine step cannot
    misconfigure them; the job runs on the host (where codex lives)."""
    payload = json.loads(a.payload) if a.payload else {}
    payload["review_head"] = a.review_head
    if a.prompt:
        payload["prompt"] = a.prompt
    title = a.title or f"codex review: {a.review_head} vs {a.base_ref}"
    jid = engine.enqueue(
        dispatch_id=a.dispatch_id, title=title, payload=payload,
        target="codex", kind="agent", base_ref=a.base_ref,
        env_required=a.env_required, priority=a.priority, created_by=a.by)
    print(jid)
    return 0


def cmd_review_run(a):
    """Synchronous cross-engine review (the IRP front door): enqueue a codex review
    job, RUN it in-process (REAL codex unless APEX_JOBS_AGENT_CMD overrides the CLI,
    for tests), and print the findings. Exit 0 if the review ran (succeeded), 3 if it
    failed. No promotion gate -- a review only reports."""
    from . import agent_runner
    disp = a.dispatch_id or f"review-{uuid.uuid4().hex[:8]}"
    payload = {"review_head": a.review_head}
    if a.prompt:
        payload["prompt"] = a.prompt
    engine.enqueue(dispatch_id=disp,
                   title=a.title or f"codex review: {a.review_head} vs {a.base_ref}",
                   payload=payload, target="codex", kind="agent", base_ref=a.base_ref,
                   env_required="host", created_by=a.by)
    job = engine.get_job(disp)
    seam = os.environ.get("APEX_JOBS_AGENT_CMD")
    agent_cmd = json.loads(seam) if seam else None
    summary = agent_runner.run_review_job(job, env="host", agent_cmd=agent_cmd)
    res = (engine.runs_for(disp)[-1]["result"]) or {}
    if a.json:
        print(json.dumps({"dispatch_id": disp, "status": summary["status"],
                          "review_head": a.review_head, "base_ref": a.base_ref,
                          "findings": res.get("findings", "")}, indent=2))
    else:
        print(f"dispatch_id={disp} status={summary['status']}")
        print("---- findings ----")
        print(res.get("findings", ""))
    return 0 if summary["status"] == "succeeded" else 3


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
    e.add_argument("--kind", default="command", choices=["command", "agent"])
    e.add_argument("--base-ref", default=None, dest="base_ref")
    e.add_argument("--max-attempts", type=int, default=1, dest="max_attempts")
    e.add_argument("--prompt", default=None)
    e.set_defaults(fn=cmd_enqueue)

    er = sub.add_parser("enqueue-review")
    er.add_argument("--dispatch-id", required=True, dest="dispatch_id")
    er.add_argument("--review-head", required=True, dest="review_head")
    er.add_argument("--base-ref", required=True, dest="base_ref")
    er.add_argument("--title", default=None)
    er.add_argument("--payload", default=None)
    er.add_argument("--env-required", default="host", dest="env_required")
    er.add_argument("--priority", type=int, default=100)
    er.add_argument("--prompt", default=None)
    er.add_argument("--by", default=None)
    er.set_defaults(fn=cmd_enqueue_review)

    rr = sub.add_parser("review-run")
    rr.add_argument("--review-head", required=True, dest="review_head")
    rr.add_argument("--base-ref", required=True, dest="base_ref")
    rr.add_argument("--dispatch-id", default=None, dest="dispatch_id")
    rr.add_argument("--title", default=None)
    rr.add_argument("--prompt", default=None)
    rr.add_argument("--json", action="store_true")
    rr.add_argument("--by", default=None)
    rr.set_defaults(fn=cmd_review_run)

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

    rp = sub.add_parser("reap")
    rp.set_defaults(fn=cmd_reap)

    pr = sub.add_parser("promotions")
    pr.set_defaults(fn=cmd_promotions)

    rv = sub.add_parser("review")
    rv.add_argument("ident")
    rv.set_defaults(fn=cmd_review)

    ub = sub.add_parser("unblock")
    ub.add_argument("ident")
    ub.set_defaults(fn=cmd_unblock)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
