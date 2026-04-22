"""
Packet 020f — Real XER Host Parser Verification And Golden Fixture Admission

These tests are intentionally infrastructure-free. They validate the fixture
contract document itself and the static invariants it declares, so subsequent
XER-tools packets cannot silently drift away from the contract's required
content.

They do NOT:
    * import the mutation-seam loader (its working copy may be truncated; see
      §5 of HOST_XER_VERIFICATION_RUNBOOK.md),
    * reach a database,
    * require PyP6Xer at import time.

They DO:
    * assert the contract document exists in the authorized location,
    * assert the contract enumerates each required section, negative case,
      and invariant named in packet 020b,
    * assert the host runbook exists and declares exactly three dispositions.

Running:

    python -m pytest apps/mutation-seam/tests/test_fixture_contract_020f.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


# tests/ → mutation-seam/ → apps/ → repo-root, then into the fixtures dir.
MUTATION_SEAM_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = MUTATION_SEAM_ROOT / "app" / "schedule" / "fixtures"
CONTRACT = FIXTURES_DIR / "BASELINE_XER_FIXTURE_CONTRACT.md"
RUNBOOK  = FIXTURES_DIR / "HOST_XER_VERIFICATION_RUNBOOK.md"


# ---------------------------------------------------------------------------
# Contract document existence + structure
# ---------------------------------------------------------------------------

def test_contract_exists_in_authorized_location():
    assert CONTRACT.is_file(), (
        f"fixture contract must live at {CONTRACT!s} so 020g+ can target it"
    )


def test_contract_declares_packet_id():
    body = CONTRACT.read_text(encoding="utf-8")
    assert "2026-04-18-pm-schema-020f" in body, (
        "contract must declare the authorizing packet so later packets can trace it"
    )


@pytest.mark.parametrize(
    "required_section_header",
    [
        "# Baseline-Bearing XER Fixture Contract",
        "## 1. Why this contract exists",
        "## 2. Definitions",
        "## 3. Required content",
        "## 4. Admission process",
        "## 5. Parser-surface prerequisite",
        "## 6. Compliance statement",
    ],
)
def test_contract_carries_required_top_level_section(required_section_header: str):
    body = CONTRACT.read_text(encoding="utf-8")
    assert required_section_header in body, (
        f"fixture contract missing required section: {required_section_header!r}"
    )


@pytest.mark.parametrize(
    "required_xer_section",
    [
        "PROJECT",
        "PROJWBS",
        "TASK",
        "TASKPRED",
        "PROJBASELINE",
        "BASELINEPROJECT",
    ],
)
def test_contract_names_each_required_xer_section(required_xer_section: str):
    body = CONTRACT.read_text(encoding="utf-8")
    assert required_xer_section in body, (
        f"fixture contract must enumerate {required_xer_section!r} as required"
    )


def test_contract_enumerates_all_four_reconciliation_classes():
    """020b §4.3 names four reconciliation classes; the contract must point at
    at least two of them and list all four by description."""
    body = CONTRACT.read_text(encoding="utf-8")
    # All four must be distinguishable in §3.5 of the contract.
    required_phrases = [
        "does **not** exist on the live project",            # class 1
        "no baseline counterpart",                            # class 2
        "no matching baseline `PROJECT` row",                 # class 3
        "`sum_base_proj_id` is NULL",                         # class 4
    ]
    missing = [p for p in required_phrases if p not in body]
    assert not missing, f"contract must name reconciliation classes: {missing}"


def test_contract_repeats_non_overload_invariants():
    body = CONTRACT.read_text(encoding="utf-8")
    required = [
        "No synthetic fabrication",
        "No current-plan overload",
        "No export-lane coupling",
    ]
    missing = [p for p in required if p not in body]
    assert not missing, f"contract must repeat non-overload invariants: {missing}"


# ---------------------------------------------------------------------------
# Contract document content — parser-prerequisite honesty
# ---------------------------------------------------------------------------

def test_contract_records_pyp6xer_parser_gap():
    """020f's sandbox probe found PyP6Xer 1.016.00 does not surface
    PROJBASELINE / BASELINEPROJECT at all. The contract must record this so
    admitters cannot silently assume the loader can consume a compliant
    fixture today."""
    body = CONTRACT.read_text(encoding="utf-8")
    assert "PyP6Xer 1.016.00" in body
    assert "zero" in body.lower() and "baseline entries" in body


def test_contract_names_both_parser_options():
    """Two follow-on paths must be named: a parser-side reader shim (Option A)
    or an out-of-band baseline companion JSON (Option B). Leaving only one
    would pre-authorize that path, which 020f is not allowed to do."""
    body = CONTRACT.read_text(encoding="utf-8")
    assert "Option A" in body
    assert "Option B" in body


# ---------------------------------------------------------------------------
# Host runbook document existence + structure
# ---------------------------------------------------------------------------

def test_runbook_exists_alongside_contract():
    assert RUNBOOK.is_file(), (
        f"host runbook must live at {RUNBOOK!s} so operators find both docs "
        "in the same directory"
    )


@pytest.mark.parametrize(
    "required_disposition",
    [
        "host-validated",
        "sandbox-probed-host-runbook-authored",
        "blocked-no-real-baseline-bearing-xer",
    ],
)
def test_runbook_declares_required_disposition(required_disposition: str):
    body = RUNBOOK.read_text(encoding="utf-8")
    assert required_disposition in body, (
        f"host runbook must declare disposition {required_disposition!r}"
    )


def test_runbook_declares_only_three_dispositions():
    """The prompt explicitly says there are three allowed dispositions; §7
    must not quietly grow a fourth."""
    body = RUNBOOK.read_text(encoding="utf-8")
    section = body.split("## 7. Recording disposition", 1)[1].split("## 8.", 1)[0]
    tags = set(re.findall(r"`([a-z\-]+)`", section))
    expected = {
        "host-validated",
        "sandbox-probed-host-runbook-authored",
        "blocked-no-real-baseline-bearing-xer",
    }
    assert tags == expected, (
        f"runbook §7 dispositions must be exactly {expected}, found {tags}"
    )


def test_runbook_targets_named_default_xer():
    body = RUNBOOK.read_text(encoding="utf-8")
    assert "Baseline Zone 2 Rev.01.xer" in body, (
        "host runbook must target the default sample XER named in the prompt"
    )


def test_runbook_requires_integrity_check_on_loader():
    """020f surfaced a truncated loader.py. The runbook must force the
    operator to ast.parse() loader.py before running regression tests,
    so a silently broken working copy cannot masquerade as a green run."""
    body = RUNBOOK.read_text(encoding="utf-8")
    assert "ast.parse" in body, (
        "runbook must require an ast.parse integrity check on loader.py"
    )
    assert "unterminated triple-quoted string" in body, (
        "runbook must record the specific SyntaxError surfaced in the sandbox"
    )


# ---------------------------------------------------------------------------
# Contract ↔ runbook cross-consistency
# ---------------------------------------------------------------------------

def test_contract_and_runbook_share_packet_id():
    c = CONTRACT.read_text(encoding="utf-8")
    r = RUNBOOK.read_text(encoding="utf-8")
    assert "2026-04-18-pm-schema-020f" in c
    assert "2026-04-18-pm-schema-020f" in r
