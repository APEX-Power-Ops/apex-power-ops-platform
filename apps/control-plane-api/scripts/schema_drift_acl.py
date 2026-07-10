"""Pure ACL/view-posture drift evaluation for the mcp_* control-plane cluster.

Schema-placement packet 01, sections 1b.4 (durable ACL drift assertion) and 1b.5
(definer-view allowlist). After the pure-REVOKE hardening (actions A1/A2), the roles
anon and authenticated must hold NO effective privilege on the six mcp_* tables or the
two SECURITY DEFINER summary views; and the ONLY accepted public SECURITY DEFINER mcp
views are those two summary views.

Kept import-safe on purpose: no config/engine/DB imports, so it is unit-testable without
a live database. check_schema_drift.py performs the live queries (the RETIRED-01b-auth
comment marker, has_table_privilege probes, and the definer-view scan) and feeds the
results to the pure evaluators here.

Timing: the anon/authenticated no-privilege assertion is enforced only once the 01b
boundary is applied (detected by the comment marker) -- pre-apply, anon legitimately
still holds privilege, so gate_acl_failures suppresses it. The definer-view allowlist is
a standing invariant, checked pre- and post-apply.
"""

# The six always-public mcp tables plus the two summary views hardened by A1.
MCP_CORE_OBJECTS = (
    "mcp_job_runs",
    "mcp_lane_priorities",
    "mcp_local_action_queue",
    "mcp_review_decisions",
    "mcp_task_packets",
    "mcp_validation_artifacts",
    "mcp_job_run_summary_v",
    "mcp_task_packet_summary_v",
)

# The seventh table is conditionally present (migration 000009, unapplied on prod).
# The live checker probes it only when it exists; the target posture is identical.
MCP_CONDITIONAL_OBJECTS = ("mcp_external_action_audits",)

# Roles that must hold no privilege after A1 (anon) and A2 (authenticated).
MCP_HARDENED_ROLES = ("anon", "authenticated")

MCP_ACL_VERBS = ("SELECT", "INSERT", "UPDATE", "DELETE")

# The only accepted public SECURITY DEFINER mcp views (DESIGN 1b.5). If a later 6b
# converts them to security_invoker, both drop out together (count 0). Any other count
# (exactly one present) is an inconsistent partial state; any other definer mcp view is
# an unaccounted-for anon leak.
MCP_ACCEPTED_DEFINER_VIEWS = ("mcp_job_run_summary_v", "mcp_task_packet_summary_v")


def evaluate_mcp_acl_posture(rows):
    """Return sorted failure strings for any retained anon/authenticated privilege.

    rows: iterable of (role, obj, verb, has_priv). has_priv is truthy when role holds
    verb on the object. Any truthy value is a leak, reported as
    "<role> retains <verb> on public.<obj>". (Whether a leak is an ERROR depends on
    boundary state -- see gate_acl_failures.)
    """
    failures = []
    for role, obj, verb, has_priv in rows:
        if has_priv:
            failures.append(f"{role} retains {verb} on public.{obj}")
    return sorted(failures)


def gate_acl_failures(acl_failures, boundary_applied):
    """Enforce the anon/authenticated no-privilege assertion only after the 01b boundary
    is applied. Pre-apply (boundary_applied False), anon legitimately still holds
    privilege, so no failure is raised; post-apply, any leak is drift (a silent re-grant).
    """
    return sorted(acl_failures) if boundary_applied else []


def evaluate_definer_view_allowlist(present_definer_views):
    """Standing invariant (DESIGN 1b.5): the only accepted SECURITY DEFINER mcp views are
    the two summary views, present consistently (both, or both converted to invoker).

    present_definer_views: iterable of mcp_* view names that are SECURITY DEFINER.
    Returns sorted failure strings for (a) any definer mcp view outside the allowlist and
    (b) an inconsistent count of the accepted views (exactly one present).
    """
    accepted = set(MCP_ACCEPTED_DEFINER_VIEWS)
    present = set(present_definer_views)
    failures = []

    unexpected = sorted(present - accepted)
    if unexpected:
        failures.append(
            "unexpected SECURITY DEFINER mcp views outside the 01b allowlist "
            f"{{{', '.join(sorted(accepted))}}}: {', '.join(unexpected)}"
        )

    named = present & accepted
    if len(named) not in (0, 2):
        failures.append(
            "mcp summary views in inconsistent security-mode state (partial 6b): "
            f"definer={', '.join(sorted(named))}"
        )
    return failures
