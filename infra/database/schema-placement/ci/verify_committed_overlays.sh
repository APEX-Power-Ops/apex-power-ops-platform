#!/usr/bin/env bash
# CI gate: the overlay-evidence contract (design spec 4.2 @ 8f6d41c4).
#  step 0  fail-closed fetch + UNIQUE merge-base (--all; exactly one line)
#  step 1  immutability: --no-renames --name-status over census/overlay/source/sig pathspecs,
#          FAIL unless EVERY entry is status A (rejects M, D, T, R, C, U, B; --no-renames
#          decomposes a rename+modify into A+D -- the empirically-pinned round-2b bypass);
#          plus a non-regular-mode check (120000 symlink / 160000 gitlink under evidence/)
#  step 2+ delegated to overlay_ci_checks.py (kind-sniff, census uniqueness, sig pairing,
#          SOURCE-ORPHAN GUARD (rider, unconditional), added-set per-overlay verification with
#          the non-self-referential census binding, committed-set OV007)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
SP=infra/database/schema-placement

git fetch --quiet origin main    # FAIL-CLOSED: a fetch failure aborts (no '|| true')

BASES=$(git merge-base --all origin/main HEAD)
if [ "$(printf '%s\n' "$BASES" | grep -c .)" -ne 1 ]; then
  echo "FAIL: merge-base of origin/main and HEAD is empty or ambiguous"; exit 1
fi
BASE=$BASES

# step 1a: immutability -- every touched evidence artifact must be status A.
# NO '|| true' anywhere in these pipelines (plan-audit ECMC-4/SPEC-3: it would rescue a FAILING
# git diff/ls-files and pass the step fail-OPEN); awk exits 0 on zero matches, and under
# `set -euo pipefail` a git failure aborts the gate -- the fail-closed posture.
BAD=$(git diff --no-renames --name-status "$BASE" HEAD -- \
        ":(glob)$SP/evidence/census-prod-*.json" \
        ":(glob)$SP/evidence/overlay-*.json" \
        "$SP/evidence/source" \
        ":(glob)$SP/evidence/**/*.sig" \
      | awk '$1 != "A"')
if [ -n "$BAD" ]; then
  echo "FAIL: immutability -- committed evidence was modified/deleted/renamed/typechanged:"
  printf '%s\n' "$BAD"
  exit 1
fi

# step 1b: non-regular modes under evidence/ (symlink/gitlink)
MODES=$(git ls-files -s -- "$SP/evidence" | awk '$1 == "120000" || $1 == "160000"')
if [ -n "$MODES" ]; then
  echo "FAIL: non-regular file mode under $SP/evidence:"
  printf '%s\n' "$MODES"
  exit 1
fi

# steps 2-5: repo-level + per-added-overlay checks (python driver; runs its unconditional
# checks -- incl. the source-orphan guard -- even when zero overlays are added)
uv run --project "$SP" --locked python "$SP/ci/overlay_ci_checks.py" --base "$BASE"
