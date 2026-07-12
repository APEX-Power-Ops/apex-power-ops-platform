#!/usr/bin/env bash
# CI gate: verify every census snapshot ADDED on this branch (vs origin/main) against the
# source-pinned production signer, and confirm the tooling that produced it is unchanged from the
# snapshot's signed repo_sha. A corrupted snapshot/signature, a foreign signer, an out-of-scope
# census, or evidence produced by drifted tooling all fail here — so the artifact gate travels with
# the same PR that adds the evidence. Verifying only ADDED files (not all history) keeps the
# tooling-unchanged assertion valid across legitimate future tooling evolution.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
SP=infra/database/schema-placement
git fetch --quiet origin main || true
BASE=$(git merge-base origin/main HEAD)
mapfile -t SNAPS < <(git diff --diff-filter=A --name-only "$BASE" HEAD -- "$SP/evidence/census-prod-*.json" || true)
if [ "${#SNAPS[@]}" -eq 0 ]; then
  echo "no census artifacts added on this branch (vs origin/main) — nothing to verify"; exit 0
fi
TOOLING=("$SP/verify_census.py" "$SP/collect_disposition.py" "$SP/disposition_signing.py" "$SP/disposition_trust.py" "$SP/disposition_provenance.py" "$SP/disposition.schema.json" "$SP/keys")
rc=0
for snap in "${SNAPS[@]}"; do
  echo "=== verifying committed census: $snap ==="
  sig="$snap.sig"
  [ -f "$sig" ] || { echo "FAIL: missing sidecar $sig"; rc=1; continue; }
  repo_sha=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['repo_sha'])" "$snap")
  git merge-base --is-ancestor "$repo_sha" HEAD || { echo "FAIL: signed repo_sha $repo_sha is not an ancestor of HEAD"; rc=1; continue; }
  if ! git diff --quiet "$repo_sha" HEAD -- "${TOOLING[@]}"; then
    echo "FAIL: verifier/collector/trust-anchor changed since signed repo_sha $repo_sha — re-run the census at HEAD before merging"; rc=1; continue
  fi
  # tooling unchanged => the collector bundle at HEAD equals the one at repo_sha; use it as the reviewed expected hash (not the snapshot's self-attested value)
  qb=$(cd "$SP" && uv run --project . --locked python -c "import collect_disposition as c;print(c.query_bundle_sha256())")
  if uv run --project "$SP" --locked python "$SP/verify_census.py" \
      --snapshot "$snap" --snapshot-sig "$sig" \
      --key-id prod-disposition-ed25519-2026-07 \
      --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres --expect-schemas public \
      --expect-repo-sha "$repo_sha" \
      --require-role-markers anon,authenticated,service_role \
      --expect-query-bundle-sha256 "$qb"; then
    echo "OK: $snap"
  else
    echo "FAIL: verify_census rejected $snap"; rc=1
  fi
done
[ "$rc" -eq 0 ] && echo "=== ALL COMMITTED CENSUS ARTIFACTS VERIFIED ===" || echo "=== CENSUS ARTIFACT VERIFICATION FAILED ==="
exit $rc
