# Olares Dev Residency 096 - Historical Parent-Root Helper And Task Demotion Planning Handoff

Date: 2026-05-07
Status: Complete
Packet: `2026-05-07-olares-dev-residency-096`

## Outcome

The next bounded provenance-routing normalization lane is now selected.

The highest-risk remaining parent-root residue is the repo-root VS Code task surface, not the already-closed historical handoff documents.

Packet 096 therefore opens one smallest follow-on execution slice: relabel or demote the current-looking parent-root bootstrap and scaffold tasks inside `.vscode/tasks.json` so delegated execution is less likely to route through older parent-root packet helpers by mistake.

## Decision Basis

The controlling evidence is the current active repo task surface:

1. `.vscode/tasks.json` still exposes `Preview parent-root bootstrap packet`, `Stage parent-root bootstrap packet`, and `Parent-root bootstrap packet staged diff` directly beside active repo-root and Olares-host tasks.
2. The same task block also still exposes `Preview parent-root Class A scaffold packet`, `Stage parent-root Class A scaffold packet`, and `Parent-root Class A scaffold packet staged diff` with current-looking labels.
3. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` already explains that the bootstrap-packet helpers are historical and not part of routine publication.
4. `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md` is already explicitly closed and historical.

That means the task labels themselves are now the dominant misrouting hazard, because they remain visible as normal runnable options inside the active standalone repo workspace even though the surrounding prose already treats them as provenance-only surfaces.

## Boundary Preserved

This planning packet does not open:

1. runtime mutation,
2. hosting or publication-boundary reversal,
3. package or lockfile mutation,
4. trust-boundary widening,
5. destructive historical cleanup.

## Selected Next Packet

The next truthful follow-on is:

`Olares Dev Residency 097 - Repo-Root Task Surface Historical Relabel And Demotion Execution`

That later packet should:

1. relabel or demote the parent-root bootstrap and Class A scaffold tasks in `.vscode/tasks.json`,
2. update the runbook task list only as needed to match the new task labels and routing posture,
3. preserve the underlying historical packet surfaces as provenance unless a separate later packet explicitly archives them.