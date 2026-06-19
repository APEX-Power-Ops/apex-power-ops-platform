from __future__ import annotations

from dataclasses import dataclass

from .model import IntakePayload

TOL = 0.01


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
