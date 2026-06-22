from __future__ import annotations

from dataclasses import dataclass

from .model import IntakePayload

TOL = 0.01


# ---------------------------------------------------------------------------
# Legacy types — kept for backward-compat (test_validate.py, cli.py callers)
# ---------------------------------------------------------------------------

class IntakeValidationError(Exception):
    pass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def validate(p: IntakePayload) -> list[Check]:
    cs: list[Check] = []
    for s in p.scopes:
        if s.lines:  # apparatus-bearing scopes only (chiller scopes have no lines)
            lh = round(sum(l.line_hours for l in s.lines), 4)
            cs.append(Check(
                f"{s.scope_name}: sum(line_hours)==J3",
                abs(lh - s.quote.total_quoted_hours) <= TOL,
                f"{lh} vs {s.quote.total_quoted_hours}",
            ))
    csum = round(sum(s.quote.adjusted_total for s in p.scopes), 2)
    cs.append(Check(
        "sum(scope.adjusted_total)==contract_value",
        abs(csum - p.project.contract_value) <= 1.0,
        f"{csum} vs {p.project.contract_value}",
    ))
    names = [s.scope_name for s in p.scopes]
    cs.append(Check("scope names unique", len(names) == len(set(names)),
                    f"{len(names)} names, {len(set(names))} unique"))
    return cs


def assert_valid(p: IntakePayload, **_) -> None:
    bad = [c for c in validate(p) if not c.ok]
    if bad:
        raise IntakeValidationError("; ".join(f"{c.name} [{c.detail}]" for c in bad))


# ---------------------------------------------------------------------------
# New structured Finding model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    code: str
    severity: str
    ok: bool
    message: str
    diagnostic_detail: str | None = None


def validate_payload(
    p: IntakePayload,
    *,
    source_format: str,
    n4_defaulted: bool = False,
) -> list[Finding]:
    """Return a list of Findings.

    message    — PM-safe: descriptive English, NO numeric figures, NO dollar amounts.
    diagnostic_detail — finance-only: the actual numbers for reconciliation.
    """
    findings: list[Finding] = []

    # 1. Unsupported source format (blocking)
    if source_format != "decomposed_scope_sheet":
        findings.append(Finding(
            code="unsupported_format",
            severity="blocking",
            ok=False,
            message="Payload format is not supported for automated intake",
            diagnostic_detail=f"source_format={source_format!r}",
        ))

    # 2. Unique scope names (blocking)
    names = [s.scope_name for s in p.scopes]
    if len(names) != len(set(names)):
        from collections import Counter
        dupes = [n for n, cnt in Counter(names).items() if cnt > 1]
        findings.append(Finding(
            code="duplicate_scope_names",
            severity="blocking",
            ok=False,
            message="Scope names are not unique within this payload",
            diagnostic_detail=f"duplicates={dupes}",
        ))

    # 3. J3 vs sum(line_hours) per scope (blocking)
    for s in p.scopes:
        if s.lines:
            lh = round(sum(l.line_hours for l in s.lines), 4)
            ok = abs(lh - s.quote.total_quoted_hours) <= TOL
            findings.append(Finding(
                code="j3_mismatch",
                severity="blocking",
                ok=ok,
                message=f"Scope {s.scope_name!r} hours do not reconcile",
                diagnostic_detail=f"J3={s.quote.total_quoted_hours} vs Σline={lh}",
            ))

    # 4. Contract total (blocking)
    csum = round(sum(s.quote.adjusted_total for s in p.scopes), 2)
    ok = abs(csum - p.project.contract_value) <= 1.0
    findings.append(Finding(
        code="contract_total",
        severity="blocking",
        ok=ok,
        message="Scope total does not match the contract value",
        diagnostic_detail=f"Σadjusted={csum} vs contract={p.project.contract_value}",
    ))

    # 5. N4 default (info/fidelity — ok=True; if this breaks reconciliation the
    #    j3_mismatch / contract_total checks above already emit blocking findings)
    if n4_defaulted:
        findings.append(Finding(
            code="n4_default",
            severity="info",
            ok=True,
            message="Pct-adjust (N4) was not found and has been defaulted to 1",
            diagnostic_detail="n4_defaulted=True; pct_adjust (N4) defaulted to 1 (M4 is the unit multiplier)",
        ))

    return findings
