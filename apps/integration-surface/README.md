# Integration Surface

Status: Merge-target lane

Purpose:
- temporary holding lane for cross-surface integration validation material
- current folder is not a justified standalone app boundary; active validation code should be re-homed into active runtime or validation lanes

Current contents:
1. the Python cross-surface validation harness now lives under `apps/mutation-seam/validate.py`
2. the browser dashboard slice now lives under `apps/operations-web/public/integration-dashboard/index.html`
3. no local `public/` shell remains in this lane; the folder is now marker-only retirement residue

Current posture:
1. this lane no longer carries active validation code
2. this lane should now be treated as marker-only retirement residue, not as a new feature home

Retirement gate:
1. keep this marker in place while it still helps operators understand that the validation harness moved to `apps/mutation-seam` and the browser slice moved to `apps/operations-web`
2. retire this marker only after those active-lane homes are stable enough that the historical re-home distinction no longer adds operational value
3. any retirement decision for this lane should be explicit in the workspace architecture docs rather than silent deletion

Current rules:
1. do not treat this lane as architecture authority
2. do not expand this lane as a standalone runtime unless a hard deployment boundary is newly proven
3. prefer bounded re-home into `apps/mutation-seam`, `apps/operations-web`, or other active validation tooling rather than growing this folder in place

Authority order:
1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/README.md`
2. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `C:/APEX Platform/apex-power-ops-platform/README.md`
