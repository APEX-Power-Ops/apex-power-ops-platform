#!/usr/bin/env bash
# Mechanical pre-commit redaction guard for Slice 2d committable artifacts. Rejects (1) email-shaped
# PII and (2) any literal term in an OPERATOR-HELD denylist file at $REDACTION_DENYLIST (kept OUT of
# git -- e.g. the real cohort names under .claude/PLATFORM/). The denylist is optional; without it,
# only the email check runs. Usage: [REDACTION_DENYLIST=path] redaction_check.sh FILE...
set -euo pipefail
status=0
for f in "$@"; do
  if grep -InE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$f" | grep -viE '@learning\.invalid'; then
    echo "REDACTION FAIL: email-like PII in $f" >&2
    status=1
  fi
  if [ -n "${REDACTION_DENYLIST:-}" ] && [ -s "${REDACTION_DENYLIST:-}" ]; then
    if grep -Inf "$REDACTION_DENYLIST" "$f"; then
      echo "REDACTION FAIL: denylisted term in $f" >&2
      status=1
    fi
  fi
done
exit $status
