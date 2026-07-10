"""Unit tests for the mcp_* ACL/view-posture drift evaluators (schema-placement 1b.4/1b.5).

Imports ONLY the pure evaluator module (no config/engine, no live DB) so the guard is
testable in any environment. The live queries (comment marker, has_table_privilege,
definer-view scan) live in check_schema_drift.py; this covers the logic they feed.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"),
)

from schema_drift_acl import (  # noqa: E402
    MCP_ACCEPTED_DEFINER_VIEWS,
    MCP_ACL_VERBS,
    MCP_CORE_OBJECTS,
    MCP_HARDENED_ROLES,
    evaluate_definer_view_allowlist,
    evaluate_mcp_acl_posture,
    gate_acl_failures,
)


def _rows(objects, priv_for=lambda role, obj, verb: False):
    for role in MCP_HARDENED_ROLES:
        for obj in objects:
            for verb in MCP_ACL_VERBS:
                yield (role, obj, verb, priv_for(role, obj, verb))


def test_all_revoked_yields_no_failures():
    rows = list(_rows(MCP_CORE_OBJECTS))
    assert evaluate_mcp_acl_posture(rows) == []


def test_any_retained_privilege_is_reported():
    def priv(role, obj, verb):
        return role == "anon" and obj == "mcp_task_packets" and verb == "SELECT"

    rows = list(_rows(MCP_CORE_OBJECTS, priv))
    assert evaluate_mcp_acl_posture(rows) == [
        "anon retains SELECT on public.mcp_task_packets"
    ]


def test_multiple_failures_are_sorted_and_complete():
    def priv(role, obj, verb):
        return obj == "mcp_job_run_summary_v" and verb == "SELECT"

    rows = list(_rows(MCP_CORE_OBJECTS, priv))
    assert evaluate_mcp_acl_posture(rows) == [
        "anon retains SELECT on public.mcp_job_run_summary_v",
        "authenticated retains SELECT on public.mcp_job_run_summary_v",
    ]


def test_truthy_non_bool_priv_flags_are_honored():
    rows = [("anon", "mcp_job_runs", "SELECT", 1)]
    assert evaluate_mcp_acl_posture(rows) == ["anon retains SELECT on public.mcp_job_runs"]


def test_core_object_set_is_exactly_six_tables_and_two_views():
    assert len(MCP_CORE_OBJECTS) == 8
    assert "mcp_job_run_summary_v" in MCP_CORE_OBJECTS
    assert "mcp_task_packet_summary_v" in MCP_CORE_OBJECTS
    views = [o for o in MCP_CORE_OBJECTS if o.endswith("_v")]
    assert len(views) == 2


# --- boundary gating (1b.4 timing) -----------------------------------------

def test_gate_suppresses_leaks_before_boundary_applied():
    leaks = ["anon retains SELECT on public.mcp_task_packets"]
    assert gate_acl_failures(leaks, boundary_applied=False) == []


def test_gate_enforces_leaks_after_boundary_applied():
    leaks = ["anon retains SELECT on public.mcp_task_packets"]
    assert gate_acl_failures(leaks, boundary_applied=True) == leaks


def test_gate_passes_when_no_leaks_and_boundary_applied():
    assert gate_acl_failures([], boundary_applied=True) == []


# --- definer-view allowlist (1b.5) -----------------------------------------

def test_allowlist_accepts_exactly_the_two_summary_views():
    assert evaluate_definer_view_allowlist(MCP_ACCEPTED_DEFINER_VIEWS) == []


def test_allowlist_accepts_zero_definer_views_after_invoker_conversion():
    assert evaluate_definer_view_allowlist([]) == []


def test_allowlist_flags_inconsistent_single_summary_view():
    failures = evaluate_definer_view_allowlist(["mcp_job_run_summary_v"])
    assert len(failures) == 1
    assert "inconsistent security-mode" in failures[0]


def test_allowlist_flags_unexpected_definer_view():
    failures = evaluate_definer_view_allowlist(
        [*MCP_ACCEPTED_DEFINER_VIEWS, "mcp_secret_leak_v"]
    )
    assert any("mcp_secret_leak_v" in f and "outside the 01b allowlist" in f for f in failures)
