from __future__ import annotations

from ops_intake.model import IntakePayload


def classify(payload: IntakePayload) -> str:
    """Return the source_format label for the parsed payload.

    Rules (in priority order):
    - any scope bears apparatus lines (non-empty) -> 'decomposed_scope_sheet'
    - scopes present but none bear lines          -> 'flat_quote'
    - no scopes at all                            -> 'unsupported'
    """
    if not payload.scopes:
        return "unsupported"
    if any(scope.lines for scope in payload.scopes):
        return "decomposed_scope_sheet"
    return "flat_quote"
