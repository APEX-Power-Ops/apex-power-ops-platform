# Olares Dev Residency 395 - Copilot Instructions Routing Refresh Handoff

Date: 2026-05-09
Status: Complete
Packet: `2026-05-09-olares-dev-residency-395`

## Purpose

Close the next adjacent post-cutover residue slice after the parent-root decision-log routing refresh by correcting stale startup and schema-reference paths in the Copilot instruction surfaces.

## Execution Result

Packet 395 is complete.

`apex-power-ops-platform/.github/copilot-instructions.md` and its parent-root aligned mirror at `C:/APEX Platform/.github/copilot-instructions.md` now route startup reads to repo-owned authority, handoff, and schema-reference surfaces that actually exist inside the canonical repo boundary.

## Validation Notes

Focused validation stayed bounded to the Copilot-instructions routing refresh, the new Packet 395 routing line in `PROJECT_STATUS.md`, and this handoff.

Checks confirmed:

1. the active Copilot instruction file no longer points readers at missing repo-local `.claude` or `Supabase` paths,
2. both the repo-owned instruction file and the parent-root mirror now route schema and session-start reads through canonical repo surfaces,
3. the parent-root instruction copy remains an aligned mirror rather than a separate source of authority.

All checks passed.

## Boundaries Preserved

This packet does not open:

1. runtime or service mutation,
2. instruction-file rewrites beyond the localized startup and routing references,
3. task or command changes,
4. repo-boundary reversal,
5. strategic-authority changes,
6. broader `.github/` or prompt-surface normalization beyond this specific routing defect.

## Next Candidate

The next truthful repo-foundation work is the next adjacent parent-root mirror, publication, prompt, authority, or operator surface whose routing note, current-path statement, or preserved internal guidance still implies a current bootstrap, umbrella-root publication boundary, or stale non-canonical dependency despite the maintained post-cutover baseline.