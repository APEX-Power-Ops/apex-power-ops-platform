# Lead Surface

Status: Merge-target lane

Purpose:
- temporary holding lane for lead-oriented browser concerns
- current folder no longer carries the lead browser artifact that was re-homed into `apps/operations-web`, and it is not a justified standalone deployable at the current workspace stage

Current rules:
1. default new lead-facing browser work into `apps/operations-web`
2. do not expand this lane as a standalone app unless a hard deployment boundary is later proven
3. treat this folder as merge-planning residue, not as an active app home

Current contents:
1. no local `public/` shell remains after the lead-oriented prototype was re-homed into the active lane
2. the canonical active-lane copy of the lead operations prototype now lives under `apps/operations-web/public/lead-ops/index.html`
3. this lane should now be treated as marker-only merge residue, not extended in place

Retirement gate:
1. keep this marker while it still helps operators understand that lead-facing browser work now belongs in `apps/operations-web`
2. retire this marker only after the lead-facing operations-web surface is stable enough that the old lane no longer adds orientation value
3. any retirement decision for this lane should be recorded in the workspace architecture docs rather than handled as silent cleanup

Authority order:
1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/`
3. root `README.md`
