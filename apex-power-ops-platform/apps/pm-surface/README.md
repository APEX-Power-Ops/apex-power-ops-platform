# PM Surface

Status: Merge-target lane

Purpose:
- temporary holding lane for PM-oriented browser concerns
- current folder no longer carries the PM browser artifacts that were re-homed into `apps/operations-web`, and it is not a justified standalone app boundary at the current workspace stage

Current rules:
1. default PM-facing browser work into `apps/operations-web`
2. do not expand this lane as a standalone app unless a hard deployment boundary is later proven
3. treat this folder as merge-planning residue, not as an active app home

Current contents:
1. no local `public/` shell remains after duplicate PM browser artifacts were removed from this lane
2. the canonical active-lane copy of the first re-homed review slice now lives under `apps/operations-web/public/pm-review/`
3. the canonical active-lane copy of the schedule review slice now lives under `apps/operations-web/public/pm-review/schedule.js`
4. the canonical active-lane copy of the tracer review slice now lives under `apps/operations-web/public/pm-review/tracer.js`
5. the canonical active-lane copy of the variance review slice now lives under `apps/operations-web/public/pm-review/variance.js`
6. the canonical active-lane copy of the PM approval prototype shell now lives under `apps/operations-web/public/pm-review/approval-surface.html`
7. this lane should now be treated as a marker-only merge-target residue, not as a fresh app home

Retirement gate:
1. keep this marker while it still helps operators understand that PM-facing browser work now belongs in `apps/operations-web`
2. retire this marker only after the PM review and approval tranche in `apps/operations-web` is stable enough that the historical re-home distinction no longer adds operational value
3. any retirement decision for this lane should be explicit in the workspace architecture docs rather than silent deletion

Authority order:
1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/`
3. root `README.md`
