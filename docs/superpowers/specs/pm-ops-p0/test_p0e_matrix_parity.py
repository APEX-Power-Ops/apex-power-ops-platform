#!/usr/bin/env python3
"""Static parity test: P0-E readiness matrix (design) <-> migration 012 grant DDL.

rev5.3 task 4. Offline, deterministic, NO live DB. Derives the authoritative column/table/function
sets from infra/database/migrations/ops/012_ops_app_role_boundary.sql and asserts the design's
_OPS_*_CONTRACT_SQL blocks mirror them exactly, and that the correct privilege functions are used
(has_column_privilege for column-scoped grants; has_any_column_privilege for forbidden I/U negatives).

Runs both as a pytest test (`test_p0e_matrix_parity`) and standalone (`python3 test_p0e_matrix_parity.py`).
"""
import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for anc in [p] + list(p.parents):
        if (anc / ".git").exists():
            return anc
    return Path("/home/olares/code/apex/apex-pm-ops-p0")


ROOT = _repo_root()
M012 = (ROOT / "infra/database/migrations/ops/012_ops_app_role_boundary.sql").read_text()
DESIGN = (ROOT / "docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-design.md").read_text()

NINE_FNS = [
    "attest_apparatus_complete", "revoke_completion_attestation", "approve_and_recognize",
    "reverse_recognition", "record_billing_application", "issue_billing_application",
    "discard_draft_billing_application", "void_billing_application",
]
API_TABLES = ["scopes", "scope_quote", "scope_quote_line", "tasks", "projects", "apparatus",
              "revenue_recognition_event", "completion_attestation", "billing_application",
              "billing_application_line", "billing_application_draft"]


def _m012_grant_cols(table: str, role: str, verb: str) -> set[str]:
    """Column list for `<verb> (cols)` in the grant statement `... on ops.<table> to ...<role>...;`."""
    for m in re.finditer(r"grant\s+(.*?)\s+on\s+ops\.(\w+)\s+to\s+([^;]+);", M012, re.I | re.S):
        spec, tbl, roles = m.group(1), m.group(2), m.group(3)
        if tbl != table or role not in roles:
            continue
        vm = re.search(verb + r"\s*\(([^)]*)\)", spec, re.I)
        if vm:
            return {c.strip() for c in vm.group(1).split(",") if c.strip()}
    return set()


def _design_cols(table: str, verb: str) -> set[str]:
    cols: set[str] = set()
    # unnest(ARRAY[...]) c WHERE NOT has_column_privilege(current_user, 'ops.<table>', c, '<verb>')
    for m in re.finditer(
        r"unnest\(ARRAY\[([^\]]*)\]\)\s*c\s*WHERE NOT has_column_privilege\(current_user,\s*'ops\."
        + table + r"',\s*c,\s*'" + verb + r"'\)", DESIGN, re.I | re.S):
        cols |= {c.strip().strip("'") for c in m.group(1).split(",") if c.strip()}
    # literal positive has_column_privilege(current_user, 'ops.<table>', '<col>', '<verb>')
    for m in re.finditer(
        r"(?<!NOT )has_column_privilege\(current_user,\s*'ops\." + table + r"',\s*'(\w+)',\s*'"
        + verb + r"'\)", DESIGN, re.I):
        cols.add(m.group(1))
    return cols


def collect_failures(verbose: bool = False) -> list[str]:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if verbose:
            print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))
        if not cond:
            failures.append(f"{name}: {detail}")

    exp = {
        ("projects", "INSERT"): _m012_grant_cols("projects", "ops_intake_writer", "insert"),
        ("projects", "UPDATE"): _m012_grant_cols("projects", "ops_intake_writer", "update"),
        ("apparatus", "INSERT"): _m012_grant_cols("apparatus", "ops_intake_writer", "insert"),
        ("apparatus", "UPDATE"): _m012_grant_cols("apparatus", "ops_intake_writer", "update"),
        ("scope_quote", "UPDATE"): _m012_grant_cols("scope_quote", "ops_intake_writer", "update"),
    }
    if verbose:
        print("012 authoritative column counts:", {f"{t}.{v}": len(s) for (t, v), s in exp.items()})

    # 1. 012 self-parse sanity (operator-stated cardinalities)
    check("012 projects INSERT = 15 cols", len(exp[("projects", "INSERT")]) == 15, str(sorted(exp[("projects", "INSERT")])))
    check("012 apparatus INSERT = 11 cols", len(exp[("apparatus", "INSERT")]) == 11, str(sorted(exp[("apparatus", "INSERT")])))
    check("012 scope_quote UPDATE = 3 cols", len(exp[("scope_quote", "UPDATE")]) == 3, str(sorted(exp[("scope_quote", "UPDATE")])))

    # 2. design matrix column sets == 012 for each column-scoped grant
    for (table, verb), expected in exp.items():
        got = _design_cols(table, verb)
        check(f"design {table}.{verb} column set == 012", got == expected,
              f"missing={sorted(expected - got)} extra={sorted(got - expected)}")

    # 3. correct-function-usage (the rev5.3 bug class)
    for table in ("projects", "apparatus"):
        bad = re.search(r"has_table_privilege\(current_user,\s*'ops\." + table + r"',\s*'INSERT'\)", DESIGN, re.I)
        check(f"no has_table_privilege INSERT on column-scoped ops.{table}", bad is None, "found table-level INSERT check")
    check("negatives use has_any_column_privilege for INSERT",
          re.search(r"has_any_column_privilege\(current_user, t, 'INSERT'\)", DESIGN) is not None)
    check("negatives use has_any_column_privilege for UPDATE",
          re.search(r"has_any_column_privilege\(current_user, t, 'UPDATE'\)", DESIGN) is not None)

    # 4. function-denial + helper parity
    check("writer no_mutation_exec block present", "AS no_mutation_exec" in DESIGN)
    check("api no_exec_forbidden block present", "AS no_exec_forbidden" in DESIGN)
    for fn in NINE_FNS:
        check(f"mutation fn '{fn}' present", ("ops." + fn) in DESIGN)
    check("both issue_billing_application overloads present",
          "issue_billing_application(uuid,uuid,text)" in DESIGN
          and "issue_billing_application(uuid,uuid,date,text,uuid[],numeric)" in DESIGN)
    check("F-012-1 helper referenced twice (writer holds / api denied)",
          DESIGN.count("_intake_source_format_text(ops.intake_source_format)") >= 2)

    # 5. api forbidden-write covers the full 11-table write surface (all 11 named in the api contract block)
    api_block = DESIGN[DESIGN.index("_OPS_API_CONTRACT_SQL"):DESIGN.index("_OPS_WRITER_CONTRACT_SQL")]
    missing = [t for t in API_TABLES if ("'ops." + t + "'") not in api_block]
    check("api negative names all 11 write tables", not missing, "missing=" + str(missing))

    return failures


def test_p0e_matrix_parity():
    failures = collect_failures(verbose=False)
    assert not failures, "P0-E matrix parity drift vs migration 012:\n  " + "\n  ".join(failures)


if __name__ == "__main__":
    fs = collect_failures(verbose=True)
    print()
    if fs:
        print(f"PARITY FAILED: {len(fs)} check(s)")
        sys.exit(1)
    print("PARITY OK: design P0-E matrix mirrors migration 012 exactly.")
    sys.exit(0)
