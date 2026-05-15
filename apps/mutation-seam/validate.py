#!/usr/bin/env python3
"""
APEX Cross-Surface Integration Validation Harness
UI-001d: Proves the full field→lead→PM governed chain.

Requires: mutation seam running on localhost:8000
Usage: python validate.py [--base-url http://localhost:8000]

Scenarios covered:
  1. Full chain: Field capture -> Lead submit -> PM approve (with blocking gate)
  2. Escalation chain: Lead escalate -> PM resolve
  3. Reject cycle: Submit -> Reject -> Resubmit -> Approve
  4. Snapshot review: Approve + transition guard
  5. Authority enforcement: Cross-role boundary checks
  6. Offline rejection: Class C offline queue rejection
  7. Idempotency: Duplicate key replay
  8. Transition guards: Invalid lifecycle transitions rejected
"""
import argparse
import base64
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Any, List

try:
    import httpx
except ImportError:
    print("httpx not installed, falling back to urllib")
    httpx = None
    import urllib.request


def make_token(actor_id: str, role: str) -> str:
    payload = json.dumps({"actor_id": actor_id, "actor_role": role, "project_scope": ["proj-001"]})
    return base64.b64encode(payload.encode()).decode()


TOKENS = {
    "field_tech": make_token("tech-001", "field_tech"),
    "lead": make_token("lead-001", "lead"),
    "pm": make_token("pm-001", "pm"),
}


@dataclass
class StepResult:
    desc: str
    passed: bool
    detail: str


@dataclass
class ScenarioResult:
    name: str
    category: str
    steps: List[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for s in self.steps if s.passed)

    @property
    def failed(self) -> int:
        return sum(1 for s in self.steps if not s.passed)

    @property
    def ok(self) -> bool:
        return self.failed == 0


class HarnessClient:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        if httpx:
            self.client = httpx.Client(timeout=10)
        else:
            self.client = None

    def post(self, token: str, endpoint: str, body: dict) -> dict:
        body["client_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        url = f"{self.base}/api/v1/mutations/{endpoint}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        if self.client:
            response = self.client.post(url, json=body, headers=headers)
            return response.json()
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def get(self, token: str, path: str) -> Any:
        url = f"{self.base}/api/v1/reads/{path}"
        headers = {"Authorization": f"Bearer {token}"}
        if self.client:
            response = self.client.get(url, headers=headers)
            return response.json()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def reset(self):
        url = f"{self.base}/reset"
        if self.client:
            response = self.client.post(url)
            return response.json()
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def health(self) -> bool:
        try:
            url = f"{self.base}/health"
            if self.client:
                response = self.client.get(url)
                return response.json().get("status") == "healthy"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read()).get("status") == "healthy"
        except Exception:
            return False


_counter = [0]


def ukey(prefix: str) -> str:
    _counter[0] += 1
    return f"{prefix}-{int(time.time())}-{_counter[0]}"


def scenario_full_chain(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Full Chain: Field Capture -> Lead Submit -> PM Approve", "Cross-Surface Chain")

    r = c.post(TOKENS["field_tech"], "apparatus", {
        "entity_id": "app-001", "action_type": "update_status", "mutation_class": "B",
        "idempotency_key": ukey("fc-status"), "source": "online", "payload": {"status": "active"}
    })
    res.steps.append(StepResult("Field updates apparatus status", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["field_tech"], "checklist", {
        "entity_id": "item-001", "action_type": "complete_item", "mutation_class": "A",
        "idempotency_key": ukey("fc-check"), "source": "online", "payload": {"completed": True}
    })
    res.steps.append(StepResult("Field completes checklist item", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["field_tech"], "hours", {
        "action_type": "log_entry", "mutation_class": "A",
        "idempotency_key": ukey("fc-hours"), "source": "online",
        "payload": {"apparatus_id": "app-001", "task_id": "task-001", "project_id": "proj-001", "hours": 4.5, "date": "2026-04-16"}
    })
    res.steps.append(StepResult("Field logs hours", r["status"] == "accepted", f"status={r['status']}"))

    app = c.get(TOKENS["lead"], "apparatus/app-001")
    hrs = c.get(TOKENS["lead"], "hours")
    ok = app.get("status") == "active" and len(hrs) > 0
    res.steps.append(StepResult("Lead reads field-captured data", ok, f"apparatus={app.get('status')}, hours={len(hrs)}"))

    r = c.post(TOKENS["lead"], "tasks", {
        "entity_id": "task-001", "action_type": "start", "mutation_class": "B",
        "idempotency_key": ukey("lead-start"), "source": "online", "payload": {"status": "active"}
    })
    res.steps.append(StepResult("Lead starts task-001", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["lead"], "tasks", {
        "entity_id": "task-001", "action_type": "submit_for_review", "mutation_class": "C",
        "idempotency_key": ukey("lead-submit"), "source": "online", "payload": {"status": "awaiting_review"}
    })
    res.steps.append(StepResult("Lead submits task for review", r["status"] == "accepted", f"status={r['status']}"))

    q = c.get(TOKENS["pm"], "approval-queue")
    found = any(t["id"] == "task-001" for t in q.get("tasks", []))
    res.steps.append(StepResult("PM sees task in approval queue", found, f"total={q['total_count']}, found={found}"))

    r = c.post(TOKENS["pm"], "tasks", {
        "entity_id": "task-001", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("pm-blocked"), "source": "online", "payload": {"status": "complete"}
    })
    blocked = r.get("error", {}).get("code") == "PRECONDITION_FAILED"
    res.steps.append(StepResult("PM approve blocked by issue-002", blocked, f"error={r.get('error', {}).get('code', r['status'])}"))

    c.post(TOKENS["lead"], "issues", {
        "entity_id": "issue-002", "action_type": "begin_review", "mutation_class": "B",
        "idempotency_key": ukey("lead-rev"), "source": "online", "payload": {"status": "in_review"}
    })
    r = c.post(TOKENS["lead"], "issues", {
        "entity_id": "issue-002", "action_type": "resolve", "mutation_class": "B",
        "idempotency_key": ukey("lead-resolve"), "source": "online", "payload": {"status": "resolved"}
    })
    res.steps.append(StepResult("Lead resolves blocking issue", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["pm"], "tasks", {
        "entity_id": "task-001", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("pm-approve"), "source": "online", "payload": {"status": "complete"}
    })
    res.steps.append(StepResult("PM approves task after resolution", r["status"] == "accepted", f"status={r['status']}"))

    h = c.get(TOKENS["pm"], "decision-history")
    has_approve = any(e.get("action_type") == "approve" and e.get("entity_id") == "task-001" for e in h)
    res.steps.append(StepResult("Decision history records approval", has_approve, f"entries={len(h)}"))

    return res


def scenario_escalation(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Escalation: Lead Escalate -> PM Resolve", "Cross-Surface Chain")

    r = c.post(TOKENS["lead"], "issues", {
        "entity_id": "issue-001", "action_type": "escalate_to_pm", "mutation_class": "C",
        "idempotency_key": ukey("esc"), "source": "online", "payload": {"status": "escalated"}
    })
    res.steps.append(StepResult("Lead escalates issue to PM", r["status"] == "accepted", f"status={r['status']}"))

    q = c.get(TOKENS["pm"], "approval-queue")
    found = any(i["id"] == "issue-001" for i in q.get("escalated_issues", []))
    res.steps.append(StepResult("PM sees escalated issue in queue", found, f"found={found}"))

    r = c.post(TOKENS["pm"], "issues", {
        "entity_id": "issue-001", "action_type": "resolve_escalated", "mutation_class": "C",
        "idempotency_key": ukey("pm-res"), "source": "online", "payload": {"status": "resolved"},
        "reason": "PM reviewed and resolved escalated issue"
    })
    res.steps.append(StepResult("PM resolves escalated issue", r["status"] == "accepted", f"status={r['status']}"))

    issues = c.get(TOKENS["lead"], "issues")
    issue = next((i for i in issues if i["id"] == "issue-001"), None)
    res.steps.append(StepResult("Lead sees resolved status", issue and issue["status"] == "resolved", f"status={issue and issue.get('status')}"))

    return res


def scenario_reject_cycle(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Reject Cycle: Submit -> Reject -> Resubmit -> Approve", "Cross-Surface Chain")

    r = c.post(TOKENS["lead"], "workpackages", {
        "entity_id": "wp-002", "action_type": "submit_for_review", "mutation_class": "C",
        "idempotency_key": ukey("wp-sub"), "source": "online", "payload": {"status": "awaiting_review"}
    })
    res.steps.append(StepResult("Lead submits wp-002", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["pm"], "workpackages", {
        "entity_id": "wp-002", "action_type": "reject", "mutation_class": "C",
        "idempotency_key": ukey("wp-rej"), "source": "online", "payload": {"status": "rejected"}
    })
    res.steps.append(StepResult("PM rejects wp-002", r["status"] == "accepted", f"status={r['status']}"))

    wps = c.get(TOKENS["lead"], "workpackages")
    wp = next((w for w in wps if w["id"] == "wp-002"), None)
    res.steps.append(StepResult("Lead sees rejected state", wp and wp["status"] == "rejected", f"status={wp and wp.get('status')}"))

    r = c.post(TOKENS["lead"], "workpackages", {
        "entity_id": "wp-002", "action_type": "submit_for_review", "mutation_class": "C",
        "idempotency_key": ukey("wp-react"), "source": "online", "payload": {"status": "active"}
    })
    res.steps.append(StepResult("Lead reactivates wp-002", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["lead"], "workpackages", {
        "entity_id": "wp-002", "action_type": "submit_for_review", "mutation_class": "C",
        "idempotency_key": ukey("wp-resub"), "source": "online", "payload": {"status": "awaiting_review"}
    })
    res.steps.append(StepResult("Lead resubmits wp-002", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["pm"], "workpackages", {
        "entity_id": "wp-002", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("wp-appr"), "source": "online", "payload": {"status": "complete"}
    })
    res.steps.append(StepResult("PM approves wp-002", r["status"] == "accepted", f"status={r['status']}"))

    return res


def scenario_snapshot(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Snapshot Review", "Cross-Surface Chain")

    r = c.post(TOKENS["pm"], "snapshots", {
        "entity_id": "snap-001", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("snap-appr"), "source": "online", "payload": {"status": "approved"}
    })
    res.steps.append(StepResult("PM approves snap-001", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["pm"], "snapshots", {
        "entity_id": "snap-001", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("snap-re"), "source": "online", "payload": {"status": "approved"}
    })
    res.steps.append(StepResult("Terminal state blocks re-approve", r.get("status") == "rejected", f"error={r.get('error', {}).get('code', r['status'])}"))

    return res


def scenario_authority(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Authority Boundary Enforcement", "Authority Gates")

    r = c.post(TOKENS["field_tech"], "tasks", {
        "entity_id": "task-003", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("auth-tech"), "source": "online", "payload": {"status": "complete"}
    })
    res.steps.append(StepResult("Field tech cannot approve", r.get("error", {}).get("code") == "UNAUTHORIZED_ROLE", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["lead"], "tasks", {
        "entity_id": "task-003", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("auth-lead"), "source": "online", "payload": {"status": "complete"}
    })
    res.steps.append(StepResult("Lead cannot approve", r.get("error", {}).get("code") == "UNAUTHORIZED_ROLE", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["field_tech"], "issues", {
        "entity_id": "issue-001", "action_type": "escalate_to_pm", "mutation_class": "C",
        "idempotency_key": ukey("auth-esc"), "source": "online", "payload": {"status": "escalated"}
    })
    res.steps.append(StepResult("Field tech cannot escalate", r.get("error", {}).get("code") == "UNAUTHORIZED_ROLE", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["pm"], "apparatus", {
        "entity_id": "app-005", "action_type": "update_assessment", "mutation_class": "B",
        "idempotency_key": ukey("auth-pm"), "source": "online", "payload": {"assessment": "test"}
    })
    res.steps.append(StepResult("PM cannot capture field data", r.get("error", {}).get("code") == "UNAUTHORIZED_ROLE", f"error={r.get('error', {}).get('code')}"))

    return res


def scenario_offline(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Class C Offline Rejection", "Offline Rules")

    r = c.post(TOKENS["pm"], "tasks", {
        "entity_id": "task-003", "action_type": "approve", "mutation_class": "C",
        "idempotency_key": ukey("off-pm"), "source": "offline_queue", "payload": {"status": "complete"}
    })
    res.steps.append(StepResult("Offline Class C (PM) rejected", r.get("error", {}).get("code") == "OFFLINE_CLASS_C_REJECTED", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["lead"], "tasks", {
        "entity_id": "task-003", "action_type": "submit_for_review", "mutation_class": "C",
        "idempotency_key": ukey("off-lead"), "source": "offline_queue", "payload": {"status": "awaiting_review"}
    })
    res.steps.append(StepResult("Offline Class C (Lead) rejected", r.get("error", {}).get("code") == "OFFLINE_CLASS_C_REJECTED", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["field_tech"], "checklist", {
        "entity_id": "item-003", "action_type": "complete_item", "mutation_class": "A",
        "idempotency_key": ukey("off-ok"), "source": "offline_queue", "payload": {"completed": True}
    })
    res.steps.append(StepResult("Offline Class A accepted", r["status"] == "accepted", f"status={r['status']}"))

    return res


def scenario_idempotency(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Idempotency Enforcement", "Idempotency")
    key = ukey("idemp")

    r = c.post(TOKENS["field_tech"], "checklist", {
        "entity_id": "item-005", "action_type": "complete_item", "mutation_class": "A",
        "idempotency_key": key, "source": "online", "payload": {"completed": True}
    })
    res.steps.append(StepResult("First call accepted", r["status"] == "accepted", f"status={r['status']}"))

    r = c.post(TOKENS["field_tech"], "checklist", {
        "entity_id": "item-005", "action_type": "complete_item", "mutation_class": "A",
        "idempotency_key": key, "source": "online", "payload": {"completed": True}
    })
    res.steps.append(StepResult("Replay returns idempotent_hit", r["status"] == "idempotent_hit", f"status={r['status']}"))

    return res


def scenario_transitions(c: HarnessClient) -> ScenarioResult:
    res = ScenarioResult("Lifecycle Transition Guards", "Transition Rules")

    c.post(TOKENS["field_tech"], "apparatus", {
        "entity_id": "app-003", "action_type": "update_status", "mutation_class": "B",
        "idempotency_key": ukey("tr-comp"), "source": "online", "payload": {"status": "complete"}
    })
    r = c.post(TOKENS["field_tech"], "apparatus", {
        "entity_id": "app-003", "action_type": "update_status", "mutation_class": "B",
        "idempotency_key": ukey("tr-inv"), "source": "online", "payload": {"status": "active"}
    })
    res.steps.append(StepResult("Invalid transition rejected", r.get("error", {}).get("code") == "TRANSITION_INVALID", f"error={r.get('error', {}).get('code')}"))

    r = c.post(TOKENS["field_tech"], "apparatus", {
        "entity_id": "app-004", "action_type": "update_status", "mutation_class": "B",
        "idempotency_key": ukey("tr-val"), "source": "online", "payload": {"status": "ready"}
    })
    res.steps.append(StepResult("Valid transition accepted", r["status"] == "accepted", f"status={r['status']}"))

    return res


ALL_SCENARIOS = [
    scenario_full_chain,
    scenario_escalation,
    scenario_reject_cycle,
    scenario_snapshot,
    scenario_authority,
    scenario_offline,
    scenario_idempotency,
    scenario_transitions,
]


def main():
    parser = argparse.ArgumentParser(description="APEX Cross-Surface Integration Validation Harness")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Mutation seam base URL")
    parser.add_argument("--no-reset", action="store_true", help="Skip store reset before run")
    args = parser.parse_args()

    c = HarnessClient(args.base_url)

    print("=" * 60)
    print("APEX Cross-Surface Integration Validation Harness")
    print(f"Target: {args.base_url}")
    print("=" * 60)

    if not c.health():
        print("\n[FAIL] Seam not reachable. Start the mutation seam first.")
        sys.exit(1)
    print("[OK] Seam healthy\n")

    if not args.no_reset:
        c.reset()
        print("[OK] Store reset to seed data\n")

    total_pass = 0
    total_fail = 0
    total_steps = 0
    all_results: List[ScenarioResult] = []

    for scenario_fn in ALL_SCENARIOS:
        result = scenario_fn(c)
        all_results.append(result)
        total_pass += result.passed
        total_fail += result.failed
        total_steps += len(result.steps)

        icon = "[OK]" if result.ok else "[FAIL]"
        print(f"{icon} {result.name} [{result.passed}/{len(result.steps)}]")
        for step in result.steps:
            s_icon = "  [OK]" if step.passed else "  [FAIL]"
            print(f"{s_icon} {step.desc} - {step.detail}")
        print()

    print("=" * 60)
    if total_fail == 0:
        print(f"[OK] ALL PASSED: {total_pass}/{total_steps} steps across {len(all_results)} scenarios")
    else:
        print(f"[FAIL] FAILED: {total_pass}/{total_steps} passed, {total_fail} failed")
    print("=" * 60)

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
